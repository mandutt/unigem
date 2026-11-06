"""Batch evaluation for A1 native T5Gemma2 + LoRA on the clean val 161."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval.slot_verify import verify_summary  # noqa: E402
from runner.c5_a1_lora import build_model, load_lora_state  # noqa: E402
from runner.c5_a2null_eval import char_f1, distinct_2, read_jsonl, repeated_4gram_rate  # noqa: E402

T5 = ROOT / "data/models/t5gemma-2-270m-270m"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
OUT = ROOT / "reports/provenance/C5_a1/pilot300_val161"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", type=Path, required=True)
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--splits", type=Path, default=SPLITS)
    ap.add_argument("--split", default="val", choices=["val"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--max-input", type=int, default=1024)
    ap.add_argument("--max-new", type=int, default=448)
    ap.add_argument("--prefix", default="summarize: ")
    ap.add_argument("--out", type=Path, default=OUT / "predictions.jsonl")
    ap.add_argument("--metrics", type=Path, default=OUT / "metrics.json")
    args = ap.parse_args()
    torch.set_num_threads(6)
    rows = read_jsonl(args.data)
    by_id = {str(r["id"]): r for r in rows}
    ids = set(json.loads(args.splits.read_text(encoding="utf-8"))[args.split])
    recs = [r for r in rows if str(r["id"]) in ids]
    recs.sort(key=lambda r: len(str(r["passage"])))
    if args.limit:
        recs = recs[: args.limit]
    tok = AutoTokenizer.from_pretrained(str(T5), local_files_only=True)
    model, names = build_model(drop_vision=True)
    load_lora_state(model, args.adapter)
    model.eval()
    print(json.dumps({"event": "loaded", "lora_modules": len(names), "n": len(recs)}), flush=True)

    outputs = []
    for start in range(0, len(recs), args.batch_size):
        batch = recs[start : start + args.batch_size]
        texts = [args.prefix + str(r["passage"]) for r in batch]
        enc = tok(texts, return_tensors="pt", padding=True, truncation=True, max_length=args.max_input)
        with torch.inference_mode():
            gen = model.generate(**enc, max_new_tokens=args.max_new, num_beams=1, do_sample=False)
        for i, rec in enumerate(batch):
            pred = tok.decode(gen[i], skip_special_tokens=True)
            target = str(by_id[rec["id"]]["summary"])
            rep = verify_summary(str(rec["passage"]), pred)
            outputs.append({
                "id": str(rec["id"]),
                "pred": pred,
                "target": target,
                "gen_len": int(gen[i].shape[0]),
                "ended_eos": bool((gen[i] == tok.eos_token_id).any()),
                "char_f1": char_f1(pred, target),
                "nonempty": bool(pred.strip()),
                "repeated_4gram_rate": repeated_4gram_rate(pred),
                "distinct_2": distinct_2(pred),
                "new_slot_count": len(rep.new),
                "summary_slot_count": rep.summary_count,
                "slot_preservation": rep.slot_preservation,
                "new_slot_rate": rep.new_slot_rate,
                "grounded": not rep.new,
            })
        print(json.dumps({"done": len(outputs), "n": len(recs)}), flush=True)

    outputs.sort(key=lambda x: x["id"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in outputs) + "\n", encoding="utf-8")
    n = len(outputs)
    sum_slots = sum(x["summary_slot_count"] for x in outputs)
    sum_new = sum(x["new_slot_count"] for x in outputs)
    slot_values = [x["slot_preservation"] for x in outputs]
    nonvacuous = [x for x in outputs if x["summary_slot_count"] > 0]
    metrics = {
        "n": n,
        "char_f1_mean": sum(x["char_f1"] for x in outputs) / n,
        "grounded_rate": sum(x["grounded"] for x in outputs) / n,
        "grounded_rate_nonvacuous": (
            sum(x["grounded"] for x in nonvacuous) / len(nonvacuous) if nonvacuous else 0.0
        ),
        "new_slot_rate_mean": sum(x["new_slot_rate"] for x in outputs) / n,
        "new_slot_rate_micro": sum_new / sum_slots if sum_slots else 0.0,
        "new_slot_count": sum_new,
        "summary_slot_count": sum_slots,
        "slots_per_doc": sum_slots / n,
        "slotfree_docs": sum(x["summary_slot_count"] == 0 for x in outputs),
        "slot_preservation_mean": sum(slot_values) / n,
        "slot_preservation_min": min(slot_values),
        "slot_preservation_missing_docs": sum(x < 1.0 for x in slot_values),
        "slot_preservation_zero_docs": sum(x == 0.0 for x in slot_values),
        "eos_rate": sum(x["ended_eos"] for x in outputs) / n,
        "nonempty_rate": sum(x["nonempty"] for x in outputs) / n,
        "gen_len_mean": sum(x["gen_len"] for x in outputs) / n,
        "repeated_4gram_rate_mean": sum(x["repeated_4gram_rate"] for x in outputs) / n,
        "distinct_2_mean": sum(x["distinct_2"] for x in outputs) / n,
        "prefix": args.prefix,
        "max_input": args.max_input,
        "max_new": args.max_new,
        "adapter": str(args.adapter),
    }
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    args.metrics.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"event": "metrics", **metrics, "out": str(args.out), "adapter": str(args.adapter)}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
