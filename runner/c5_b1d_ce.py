"""B1d-CE pilot: adapter-only training through a frozen T5Gemma2 decoder.

The adapter is initialized from the B1d full hidden-distillation checkpoint.
The decoder stays frozen; gradients flow through the decoder cross-attention
into the adapter. The objective is teacher-forced CE on gold summaries.

No sealed test split is loaded.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from transformers.modeling_outputs import BaseModelOutput

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_b1d_full import B1dFullAdapter, load_cache  # noqa: E402

T5 = ROOT / "data/models/t5gemma-2-270m-270m"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
INIT = ROOT / "data/models/f5_t5gemma2_lora/b1d_full/adapter_final.pt"
OUT = ROOT / "data/models/f5_t5gemma2_lora/b1d_ce_pilot"
REPORT = ROOT / "reports/provenance/C5_b1d/b1d_ce_pilot_metrics.json"
PROMPT = "summarize: "


def labels_for(tok, text: str, max_target: int = 512) -> torch.Tensor:
    ids = tok(text, add_special_tokens=False, truncation=True, max_length=max_target - 1)["input_ids"]
    lab = torch.full((1, max_target), -100, dtype=torch.long)
    lab[0, : len(ids)] = torch.tensor(ids, dtype=torch.long)
    lab[0, len(ids)] = tok.eos_token_id
    return lab


def ce_loss(model, adapter, student, teacher, rid: str, tok, max_target: int) -> tuple[torch.Tensor, torch.Tensor]:
    s = student[rid]
    x = s["h"][: s["length"]].float().unsqueeze(0)
    h_s = adapter(x).to(torch.bfloat16)
    mask = torch.ones(1, s["length"], dtype=torch.bool)
    labels = labels_for(tok, str(teacher[rid]["summary"]), max_target)
    out = model(
        encoder_outputs=BaseModelOutput(last_hidden_state=h_s),
        attention_mask=mask,
        labels=labels,
    )
    return out.loss, h_s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-limit", type=int, default=20)
    ap.add_argument("--val-limit", type=int, default=20)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--max-target", type=int, default=512)
    ap.add_argument("--init", type=Path, default=INIT)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    ap.add_argument("--report", type=Path, default=REPORT)
    args = ap.parse_args()
    args.init = args.init if args.init.is_absolute() else ROOT / args.init
    args.out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    args.report = args.report if args.report.is_absolute() else ROOT / args.report

    torch.set_num_threads(6)
    torch.manual_seed(20261107)
    t0 = time.time()
    recs = [json.loads(x) for x in DATA.read_text(encoding="utf-8").splitlines() if x.strip()]
    by_id = {str(r["id"]): r for r in recs}
    splits = json.loads((ROOT / "reports/provenance/C5_clean/splits.json").read_text(encoding="utf-8"))
    train_ids = list(splits["train"])[: args.train_limit]
    val_ids = list(splits["val"])[: args.val_limit]

    student_train = load_cache("student", "train")
    student_val = load_cache("student", "val")
    tok = AutoTokenizer.from_pretrained(str(T5), local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        str(T5), local_files_only=True, dtype=torch.bfloat16, low_cpu_mem_usage=True
    ).eval()
    for p in model.parameters():
        p.requires_grad_(False)

    ckpt = torch.load(args.init, map_location="cpu")
    adapter = B1dFullAdapter()
    adapter.load_state_dict(ckpt["adapter"])
    adapter.train()
    params = list(adapter.parameters())
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.01)

    def eval_ce(ids: list[str], student: dict) -> dict:
        vals = []
        with torch.no_grad():
            for rid in ids:
                s = student[rid]
                loss, _ = ce_loss(model, adapter, student, by_id, rid, tok, args.max_target)
                vals.append(float(loss))
        return {"n_docs": len(vals), "ce_mean": sum(vals) / len(vals) if vals else None,
                "ce_min": min(vals) if vals else None, "ce_max": max(vals) if vals else None}

    before_train = eval_ce(train_ids, student_train)
    before_val = eval_ce(val_ids, student_val)
    losses = []
    for epoch in range(args.epochs):
        order = list(train_ids)
        perm = torch.randperm(len(order), generator=torch.Generator().manual_seed(20261107 + epoch)).tolist()
        order = [order[i] for i in perm]
        for step, rid in enumerate(order):
            loss, _ = ce_loss(model, adapter, student_train, by_id, rid, tok, args.max_target)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            losses.append(float(loss.detach()))
            print(json.dumps({"epoch": epoch + 1, "step": step, "n": len(order),
                              "loss": losses[-1], "elapsed": round(time.time() - t0, 1)}), flush=True)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        torch.save({"adapter": adapter.state_dict(), "epoch": epoch + 1,
                    "loss_mean": sum(losses[-len(order):]) / len(order)},
                   args.out_dir / f"adapter_ep{epoch + 1}.pt")

    after_train = eval_ce(train_ids, student_train)
    after_val = eval_ce(val_ids, student_val)
    torch.save({"adapter": adapter.state_dict(), "epochs": args.epochs,
                "metrics": {"train": after_train, "val": after_val}},
               args.out_dir / "adapter_final.pt")
    report = {
        "experiment": "b1d_ce_pilot",
        "init": str(args.init.relative_to(ROOT).as_posix()),
        "train_n": len(train_ids),
        "val_n": len(val_ids),
        "epochs": args.epochs,
        "lr": args.lr,
        "max_target": args.max_target,
        "adapter_params": sum(p.numel() for p in adapter.parameters()),
        "loss_first": losses[0] if losses else None,
        "loss_last": losses[-1] if losses else None,
        "loss_min": min(losses) if losses else None,
        "before": {"train": before_train, "val": before_val},
        "after": {"train": after_train, "val": after_val},
        "elapsed_sec": round(time.time() - t0, 1),
        "checkpoint": str((args.out_dir / "adapter_final.pt").relative_to(ROOT).as_posix()),
        "test_split_used": False,
        "note": "adapter-only CE through frozen decoder; no decoder LoRA",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
