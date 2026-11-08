"""B2 pilot: B1d adapter + decoder-only LoRA, trained with teacher-forced CE.

The T5Gemma2 base is frozen. Only the B1d adapter and decoder q/k/v/o LoRA
parameters are trainable. The adapter is initialized from the B1d-CE pilot.

No sealed test split is loaded.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from transformers.modeling_outputs import BaseModelOutput

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_a1_lora import LoRALinear  # noqa: E402
from runner.c5_b1d_full import B1dFullAdapter, load_cache  # noqa: E402
from eval.slot_verify import verify_summary  # noqa: E402

T5 = ROOT / "data/models/t5gemma-2-270m-270m"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
INIT = ROOT / "data/models/f5_t5gemma2_lora/b1d_ce_pilot/adapter_final.pt"
OUT = ROOT / "data/models/f5_t5gemma2_lora/b2_pilot"
REPORT = ROOT / "reports/provenance/C5_b1d/b2_pilot_metrics.json"
TRAIN_TEACHER = ROOT / "reports/provenance/C5_b1d/teacher_train100.jsonl"
VAL_TEACHER = ROOT / "reports/provenance/C5_a1/pilot300_val161/predictions.jsonl"
TARGETS = ("q_proj", "k_proj", "v_proj", "o_proj")


def attach_decoder_lora(model, r: int = 8, alpha: int = 16, dropout: float = 0.05) -> list[str]:
    names = []
    for name, module in list(model.named_modules()):
        if not name.startswith("model.decoder."):
            continue
        if not name.endswith(TARGETS):
            continue
        if not isinstance(module, nn.Linear):
            continue
        parent_name, leaf = name.rsplit(".", 1)
        parent = model.get_submodule(parent_name)
        setattr(parent, leaf, LoRALinear(module, r, alpha, dropout))
        names.append(name)
    return names


def lora_state(model) -> dict[str, torch.Tensor]:
    return {n: p.detach().cpu() for n, p in model.named_parameters() if ".lora_" in n}


def labels_for(tok, text: str, max_target: int = 512) -> torch.Tensor:
    ids = tok(text, add_special_tokens=False, truncation=True, max_length=max_target - 1)["input_ids"]
    lab = torch.full((1, max_target), -100, dtype=torch.long)
    lab[0, : len(ids)] = torch.tensor(ids, dtype=torch.long)
    lab[0, len(ids)] = tok.eos_token_id
    return lab


def load_npz_cache(directory: Path, split: str) -> dict:
    out = {}
    for p in sorted(directory.glob(f"{split}_*.npz")):
        z = np.load(p)
        for i, rid in enumerate(z["ids"]):
            out[str(rid)] = {
                "h": torch.from_numpy(z["h"][i]).float(),
                "length": int(z["lengths"][i]),
            }
    return out


def ce_plus_hidden(model, adapter, student, teacher, rid: str, target_text: str, tok,
                   max_target: int, hidden_weight: float) -> tuple[torch.Tensor, torch.Tensor]:
    s = student[rid]
    t = teacher[rid]
    x = s["h"][: s["length"]].float().unsqueeze(0)
    h_s = adapter(x)
    mask = torch.ones(1, s["length"], dtype=torch.bool)
    labels = labels_for(tok, target_text, max_target)
    out = model(
        encoder_outputs=BaseModelOutput(last_hidden_state=h_s.to(torch.bfloat16)),
        attention_mask=mask,
        labels=labels,
    )
    ce = out.loss
    if hidden_weight > 0:
        y = t["h"][: t["length"]].float().unsqueeze(0)
        hc = 1.0 - (F.normalize(h_s.float(), dim=-1) * F.normalize(y, dim=-1)).sum(-1).mean()
    else:
        hc = ce.new_zeros(())
    return ce + hidden_weight * hc, ce


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-limit", type=int, default=0,
                    help="0 = all train docs")
    ap.add_argument("--val-limit", type=int, default=0,
                    help="0 = all val docs")
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--checkpoint-every", type=int, default=100)
    ap.add_argument("--experiment", default="b2_decoder_lora")
    ap.add_argument("--target", default="gold", choices=["gold", "teacher"],
                    help="training target: gold summary or teacher-generated summary")
    ap.add_argument("--teacher-preds", type=Path, default=TRAIN_TEACHER)
    ap.add_argument("--teacher-val-preds", type=Path, default=VAL_TEACHER)
    ap.add_argument("--require-teacher", action="store_true",
                    help="restrict train/val ids to teacher outputs; use for matched B2 arms")
    ap.add_argument("--no-resume", action="store_true",
                    help="ignore existing adapter_step_*.pt in out-dir")
    ap.add_argument("--rank", type=int, default=8)
    ap.add_argument("--alpha", type=int, default=16)
    ap.add_argument("--lora-dropout", type=float, default=0.05)
    ap.add_argument("--hidden-weight", type=float, default=0.01)
    ap.add_argument("--max-target", type=int, default=512)
    ap.add_argument("--input-dim", type=int, default=768)
    ap.add_argument("--adapter-hidden", type=int, default=768)
    ap.add_argument("--feature-dir", type=Path, default=None,
                    help="optional layer12 feature cache dir; uses h/lengths/ids npz")
    ap.add_argument("--scratch", action="store_true",
                    help="random adapter init; required for input-dim !=768")
    ap.add_argument("--init", type=Path, default=INIT)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    ap.add_argument("--report", type=Path, default=REPORT)
    args = ap.parse_args()
    for name in ("init", "out_dir", "report", "teacher_preds", "teacher_val_preds", "feature_dir"):
        p = getattr(args, name)
        setattr(args, name, p if p is None or p.is_absolute() else ROOT / p)

    torch.set_num_threads(6)
    torch.manual_seed(20261107)
    t0 = time.time()
    recs = [json.loads(x) for x in DATA.read_text(encoding="utf-8").splitlines() if x.strip()]
    by_id = {str(r["id"]): r for r in recs}
    splits = json.loads((ROOT / "reports/provenance/C5_clean/splits.json").read_text(encoding="utf-8"))
    train_ids = list(splits["train"])
    val_ids = list(splits["val"])

    teacher_preds_train = {}
    teacher_preds_val = {}
    if args.target == "teacher" or args.require_teacher:
        for path, dst in ((args.teacher_preds, "train"), (args.teacher_val_preds, "val")):
            rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
            m = {str(r["id"]): str(r["pred"]) for r in rows}
            if dst == "train":
                teacher_preds_train = m
            else:
                teacher_preds_val = m
        train_ids = [rid for rid in train_ids
                     if rid in teacher_preds_train
                     and not verify_summary(str(by_id[rid]["passage"]), teacher_preds_train[rid]).new]
        val_ids = [rid for rid in val_ids if rid in teacher_preds_val]

    if args.train_limit:
        train_ids = train_ids[: args.train_limit]
    if args.val_limit:
        val_ids = val_ids[: args.val_limit]

    def target_for(rid: str, split: str) -> str:
        if args.target == "teacher":
            m = teacher_preds_train if split == "train" else teacher_preds_val
            return m[rid]
        return str(by_id[rid]["summary"])

    student_train = load_cache("student", "train")
    teacher_train = load_cache("teacher", "train")
    student_val = load_cache("student", "val")
    teacher_val = load_cache("teacher", "val")
    if args.feature_dir is not None:
        student_train = load_npz_cache(args.feature_dir, "train")
        student_val = load_npz_cache(args.feature_dir, "val")

    tok = AutoTokenizer.from_pretrained(str(T5), local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        str(T5), local_files_only=True, dtype=torch.bfloat16, low_cpu_mem_usage=True
    ).eval()
    for p in model.parameters():
        p.requires_grad_(False)
    lora_names = attach_decoder_lora(model, args.rank, args.alpha, args.lora_dropout)
    for n, p in model.named_parameters():
        if ".lora_" in n:
            p.requires_grad_(True)

    adapter = B1dFullAdapter(d_in=args.input_dim, hidden=args.adapter_hidden)
    resume = None
    if args.scratch:
        print(json.dumps({"init": "scratch", "input_dim": args.input_dim,
                          "adapter_hidden": args.adapter_hidden}), flush=True)
    elif not args.no_resume:
        candidates = []
        for p in args.out_dir.glob("adapter_step_*.pt"):
            try:
                gs = int(p.stem.rsplit("_", 1)[1])
            except ValueError:
                continue
            candidates.append((gs, p))
        if candidates:
            candidates.sort()
            resume = torch.load(candidates[-1][1], map_location="cpu")
            print(json.dumps({"resumed_from": str(candidates[-1][1]),
                              "global_step": candidates[-1][0]}), flush=True)
    if resume is not None:
        adapter.load_state_dict(resume["adapter"])
        if "lora" in resume:
            missing, unexpected = model.load_state_dict(resume["lora"], strict=False)
            bad = [x for x in missing if ".lora_" in x]
            if bad:
                raise SystemExit(f"missing resumed LoRA keys: {bad[:5]}")
        start_epoch = int(resume.get("epoch_index", max(0, int(resume.get("epoch", 1)) - 1)))
        start_step = int(resume.get("step_in_epoch", 0))
    else:
        if args.scratch:
            start_epoch, start_step = 0, 0
        else:
            ckpt = torch.load(args.init, map_location="cpu")
            adapter.load_state_dict(ckpt["adapter"])
            if "lora" in ckpt:
                missing, unexpected = model.load_state_dict(ckpt["lora"], strict=False)
                bad = [x for x in missing if ".lora_" in x]
                if bad:
                    raise SystemExit(f"missing init LoRA keys: {bad[:5]}")
            start_epoch, start_step = 0, 0
    adapter.train()
    params = list(adapter.parameters()) + [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.01)

    def eval_ce(ids, student, teacher, split: str) -> dict:
        vals = []
        with torch.no_grad():
            for rid in ids:
                loss, ce = ce_plus_hidden(model, adapter, student, teacher, rid,
                                          target_for(rid, split), tok,
                                          args.max_target, args.hidden_weight)
                vals.append(float(ce))
        return {"n_docs": len(vals), "ce_mean": sum(vals) / len(vals) if vals else None,
                "ce_min": min(vals) if vals else None, "ce_max": max(vals) if vals else None}

    before_train = eval_ce(train_ids, student_train, teacher_train, "train")
    before_val = eval_ce(val_ids, student_val, teacher_val, "val")
    losses = []
    for epoch in range(start_epoch, args.epochs):
        order = list(train_ids)
        perm = torch.randperm(len(order), generator=torch.Generator().manual_seed(20261107 + epoch)).tolist()
        order = [order[i] for i in perm]
        begin = start_step if epoch == start_epoch else 0
        for step0, rid in enumerate(order[begin:], start=begin):
            loss, ce = ce_plus_hidden(model, adapter, student_train, teacher_train, rid,
                                      target_for(rid, "train"), tok,
                                      args.max_target, args.hidden_weight)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            losses.append(float(ce.detach()))
            global_step = epoch * len(train_ids) + step0 + 1
            print(json.dumps({"epoch": epoch + 1, "step": step0, "n": len(order),
                              "global_step": global_step,
                              "ce": losses[-1], "loss": float(loss.detach()),
                              "elapsed": round(time.time() - t0, 1)}), flush=True)
            if args.checkpoint_every and global_step % args.checkpoint_every == 0:
                args.out_dir.mkdir(parents=True, exist_ok=True)
                torch.save({"adapter": adapter.state_dict(), "lora": lora_state(model),
                            "epoch": epoch + 1, "epoch_index": epoch,
                            "step_in_epoch": step0 + 1,
                            "global_step": global_step,
                            "targets": list(TARGETS), "rank": args.rank, "alpha": args.alpha},
                           args.out_dir / f"adapter_step_{global_step:06d}.pt")
        args.out_dir.mkdir(parents=True, exist_ok=True)
        torch.save({"adapter": adapter.state_dict(), "lora": lora_state(model),
                    "epoch": epoch + 1, "epoch_index": epoch,
                    "step_in_epoch": len(order),
                    "global_step": (epoch + 1) * len(train_ids),
                    "targets": list(TARGETS),
                    "rank": args.rank, "alpha": args.alpha},
                   args.out_dir / f"adapter_ep{epoch + 1}.pt")
        torch.save({"adapter": adapter.state_dict(), "lora": lora_state(model),
                    "epoch": epoch + 1, "epoch_index": epoch,
                    "step_in_epoch": len(order),
                    "global_step": (epoch + 1) * len(train_ids),
                    "targets": list(TARGETS),
                    "rank": args.rank, "alpha": args.alpha},
                   args.out_dir / f"adapter_step_{(epoch + 1) * len(train_ids):06d}.pt")

    after_train = eval_ce(train_ids, student_train, teacher_train, "train")
    after_val = eval_ce(val_ids, student_val, teacher_val, "val")
    torch.save({"adapter": adapter.state_dict(), "lora": lora_state(model),
                "targets": list(TARGETS), "rank": args.rank, "alpha": args.alpha,
                "epochs": args.epochs,
                "metrics": {"train": after_train, "val": after_val}},
               args.out_dir / "adapter_final.pt")
    report = {
        "experiment": args.experiment,
        "init": str(args.init.relative_to(ROOT).as_posix()),
        "target": args.target,
        "input_dim": args.input_dim,
        "adapter_hidden": args.adapter_hidden,
        "feature_dir": str(args.feature_dir.relative_to(ROOT).as_posix()) if args.feature_dir is not None else None,
        "scratch": bool(args.scratch),
        "teacher_preds": str(args.teacher_preds.relative_to(ROOT).as_posix()),
        "teacher_val_preds": str(args.teacher_val_preds.relative_to(ROOT).as_posix()),
        "require_teacher": bool(args.require_teacher),
        "train_n": len(train_ids), "val_n": len(val_ids),
        "epochs": args.epochs, "lr": args.lr,
        "lora": {"targets": list(TARGETS), "rank": args.rank, "alpha": args.alpha,
                 "dropout": args.lora_dropout, "modules": len(lora_names),
                 "params": sum(p.numel() for p in model.parameters() if p.requires_grad)},
        "adapter_params": sum(p.numel() for p in adapter.parameters()),
        "hidden_weight": args.hidden_weight,
        "loss_first": losses[0] if losses else None,
        "loss_last": losses[-1] if losses else None,
        "loss_min": min(losses) if losses else None,
        "before": {"train": before_train, "val": before_val},
        "after": {"train": after_train, "val": after_val},
        "elapsed_sec": round(time.time() - t0, 1),
        "checkpoint": str((args.out_dir / "adapter_final.pt").relative_to(ROOT).as_posix()),
        "test_split_used": False,
        "note": "adapter + decoder q/k/v/o LoRA; base decoder frozen",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
