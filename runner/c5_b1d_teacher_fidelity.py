"""Adapter-only teacher-fidelity pilot.

Teacher: A1 native T5Gemma2 pilot300 outputs
Student: EG2 -> adapter -> frozen T5Gemma2 decoder
Trainable: adapter only

Primary metric: teacher-forced CE / token accuracy against teacher outputs.
Secondary: free-running agreement on a small val subset.
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

from eval.slot_verify import verify_summary  # noqa: E402
from runner.c5_a2null_eval import char_f1  # noqa: E402
from runner.c5_b1d_b2 import labels_for  # noqa: E402
from runner.c5_b1d_full import B1dFullAdapter, load_cache  # noqa: E402

T5 = ROOT / "data/models/t5gemma-2-270m-270m"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
INIT = ROOT / "data/models/f5_t5gemma2_lora/b1d_ce_pilot/adapter_final.pt"
TRAIN_TEACHER = ROOT / "reports/provenance/C5_b1d/teacher_train100.jsonl"
VAL_TEACHER = ROOT / "reports/provenance/C5_a1/pilot300_val161/predictions.jsonl"
OUT = ROOT / "data/models/f5_t5gemma2_lora/b1d_teacher100"
REPORT = ROOT / "reports/provenance/C5_b1d/b1d_teacher100_metrics.json"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def teacher_map(path: Path, limit: int = 0) -> dict[str, str]:
    rows = read_jsonl(path)
    if limit:
        rows = rows[:limit]
    return {str(r["id"]): str(r["pred"]) for r in rows}


def eval_fidelity(model, adapter, student, teacher_hidden, by_id, ids, teacher, tok,
                  max_target: int, hidden_weight: float) -> dict:
    ce_vals, accs, cos_vals = [], [], []
    with torch.no_grad():
        for rid in ids:
            s = student[rid]
            t = teacher_hidden[rid]
            text = teacher[rid]
            x = s["h"][: s["length"]].float().unsqueeze(0)
            h_s = adapter(x)
            mask = torch.ones(1, s["length"], dtype=torch.bool)
            labels = labels_for(tok, text, max_target)
            out = model(
                encoder_outputs=BaseModelOutput(last_hidden_state=h_s.to(torch.bfloat16)),
                attention_mask=mask,
                labels=labels,
            )
            ce_vals.append(float(out.loss))
            logits = out.logits
            valid = labels != -100
            if valid.any():
                accs.append(float((logits.argmax(dim=-1)[valid] == labels[valid]).float().mean()))
            y = t["h"][: t["length"]].float().unsqueeze(0)
            cos_vals.append(float((F.normalize(h_s.float(), dim=-1) * F.normalize(y, dim=-1)).sum(-1).mean()))
    n = len(ce_vals)
    return {
        "n": n,
        "teacher_ce_mean": sum(ce_vals) / n if n else None,
        "teacher_token_acc_mean": sum(accs) / len(accs) if accs else None,
        "hidden_cos_mean": sum(cos_vals) / n if n else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-limit", type=int, default=100)
    ap.add_argument("--val-limit", type=int, default=100)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--hidden-weight", type=float, default=0.05)
    ap.add_argument("--max-target", type=int, default=512)
    ap.add_argument("--gen-limit", type=int, default=20)
    ap.add_argument("--init", type=Path, default=INIT)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    ap.add_argument("--report", type=Path, default=REPORT)
    args = ap.parse_args()
    for name in ("init", "out_dir", "report"):
        p = getattr(args, name)
        setattr(args, name, p if p.is_absolute() else ROOT / p)

    torch.set_num_threads(6)
    torch.manual_seed(20261107)
    t0 = time.time()
    recs = read_jsonl(DATA)
    by_id = {str(r["id"]): r for r in recs}
    splits = json.loads((ROOT / "reports/provenance/C5_clean/splits.json").read_text(encoding="utf-8"))
    train_teacher_all = teacher_map(TRAIN_TEACHER, 0)
    val_teacher_all = teacher_map(VAL_TEACHER, 0)

    # Keep only teacher outputs that are grounded against the source.
    train_ids, skipped_train = [], []
    for rid in splits["train"]:
        if rid not in train_teacher_all:
            continue
        if verify_summary(str(by_id[rid]["passage"]), train_teacher_all[rid]).new:
            skipped_train.append(rid)
            continue
        train_ids.append(rid)
    val_ids = [r for r in splits["val"] if r in val_teacher_all]
    train_ids = train_ids[: args.train_limit]
    val_ids = val_ids[: args.val_limit]

    student_train = load_cache("student", "train")
    teacher_hidden_train = load_cache("teacher", "train")
    student_val = load_cache("student", "val")
    teacher_hidden_val = load_cache("teacher", "val")

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
    params = [p for p in adapter.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.01)

    before_train = eval_fidelity(model, adapter, student_train, teacher_hidden_train, by_id,
                                 train_ids, train_teacher_all, tok, args.max_target, args.hidden_weight)
    before_val = eval_fidelity(model, adapter, student_val, teacher_hidden_val, by_id,
                               val_ids, val_teacher_all, tok, args.max_target, args.hidden_weight)
    losses, ce_hist, acc_hist = [], [], []
    for epoch in range(args.epochs):
        order = list(train_ids)
        perm = torch.randperm(len(order), generator=torch.Generator().manual_seed(20261107 + epoch)).tolist()
        order = [order[i] for i in perm]
        for step, rid in enumerate(order):
            s = student_train[rid]
            t = teacher_hidden_train[rid]
            x = s["h"][: s["length"]].float().unsqueeze(0)
            h_s = adapter(x)
            mask = torch.ones(1, s["length"], dtype=torch.bool)
            labels = labels_for(tok, train_teacher_all[rid], args.max_target)
            out = model(
                encoder_outputs=BaseModelOutput(last_hidden_state=h_s.to(torch.bfloat16)),
                attention_mask=mask,
                labels=labels,
            )
            ce = out.loss
            y = t["h"][: t["length"]].float().unsqueeze(0)
            hidden = 1.0 - (F.normalize(h_s.float(), dim=-1) * F.normalize(y, dim=-1)).sum(-1).mean()
            loss = ce + args.hidden_weight * hidden
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            losses.append(float(loss.detach()))
            ce_hist.append(float(ce.detach()))
            with torch.no_grad():
                logits = out.logits
                valid = labels != -100
                acc = float((logits.argmax(dim=-1)[valid] == labels[valid]).float().mean()) if valid.any() else 0.0
                acc_hist.append(acc)
            print(json.dumps({"epoch": epoch + 1, "step": step, "n": len(order),
                              "ce": ce_hist[-1], "tok_acc": acc_hist[-1],
                              "hidden_cos": float(hidden.detach()),
                              "elapsed": round(time.time() - t0, 1)}), flush=True)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        torch.save({"adapter": adapter.state_dict(), "epoch": epoch + 1,
                    "metrics": {"train": before_train, "val": before_val}},
                   args.out_dir / f"adapter_ep{epoch + 1}.pt")

    after_train = eval_fidelity(model, adapter, student_train, teacher_hidden_train, by_id,
                                train_ids, train_teacher_all, tok, args.max_target, args.hidden_weight)
    after_val = eval_fidelity(model, adapter, student_val, teacher_hidden_val, by_id,
                              val_ids, val_teacher_all, tok, args.max_target, args.hidden_weight)
    torch.save({"adapter": adapter.state_dict(), "epochs": args.epochs,
                "metrics": {"train": after_train, "val": after_val}},
               args.out_dir / "adapter_final.pt")

    # Small free-running agreement check; teacher-forced is the primary gate.
    gen_ids = val_ids[: args.gen_limit] if args.gen_limit else val_ids
    gen_rows = []
    with torch.inference_mode():
        for rid in gen_ids:
            s = student_val[rid]
            x = s["h"][: s["length"]].float().unsqueeze(0)
            h_s = adapter(x).to(torch.bfloat16)
            mask = torch.ones(1, s["length"], dtype=torch.bool)
            gen = model.generate(
                encoder_outputs=BaseModelOutput(last_hidden_state=h_s),
                attention_mask=mask,
                max_new_tokens=448,
                num_beams=1,
                do_sample=False,
            )
            pred = tok.decode(gen[0], skip_special_tokens=True)
            teacher = val_teacher_all[rid]
            rep = verify_summary(str(by_id[rid]["passage"]), pred)
            gen_rows.append({
                "id": rid, "pred": pred, "teacher": teacher,
                "teacher_char_f1": char_f1(pred, teacher),
                "gold_char_f1": char_f1(pred, str(by_id[rid]["summary"])),
                "eos": bool((gen[0] == tok.eos_token_id).any()),
                "grounded": not rep.new,
                "gen_len": int(gen[0].shape[0]),
            })

    def agg(rows, key):
        return sum(r[key] for r in rows) / len(rows) if rows else None

    report = {
        "experiment": "b1d_adapter_only_teacher_fidelity",
        "init": str(args.init.relative_to(ROOT).as_posix()),
        "train_n": len(train_ids), "val_n": len(val_ids),
        "skipped_ungrounded_teacher": len(skipped_train),
        "epochs": args.epochs, "lr": args.lr,
        "hidden_weight": args.hidden_weight,
        "adapter_params": sum(p.numel() for p in adapter.parameters()),
        "before": {"train": before_train, "val": before_val},
        "after": {"train": after_train, "val": after_val},
        "loss_first": losses[0] if losses else None,
        "loss_last": losses[-1] if losses else None,
        "ce_first": ce_hist[0] if ce_hist else None,
        "ce_last": ce_hist[-1] if ce_hist else None,
        "tok_acc_first": acc_hist[0] if acc_hist else None,
        "tok_acc_last": acc_hist[-1] if acc_hist else None,
        "free_running": {
            "n": len(gen_rows),
            "teacher_f1_mean": agg(gen_rows, "teacher_char_f1"),
            "gold_f1_mean": agg(gen_rows, "gold_char_f1"),
            "eos_rate": sum(r["eos"] for r in gen_rows) / len(gen_rows) if gen_rows else None,
            "grounded_rate": sum(r["grounded"] for r in gen_rows) / len(gen_rows) if gen_rows else None,
            "gen_len_mean": agg(gen_rows, "gen_len"),
        },
        "elapsed_sec": round(time.time() - t0, 1),
        "checkpoint": str((args.out_dir / "adapter_final.pt").relative_to(ROOT).as_posix()),
        "test_split_used": False,
        "note": "adapter-only; decoder frozen; teacher-forced fidelity is primary; free-running is a small screen",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
