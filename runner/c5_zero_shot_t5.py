"""Zero-shot T5Gemma2 native encoder-decoder reference on clean val."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval.slot_verify import verify_summary  # noqa: E402
from runner.c5_a2null_eval import char_f1, distinct_2, read_jsonl, repeated_4gram_rate  # noqa: E402

T5 = ROOT / "data/models/t5gemma-2-270m-270m"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
OUT = ROOT / "reports/provenance/C5_a2null"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--splits", type=Path, default=SPLITS)
    ap.add_argument("--split", default="val", choices=["val"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--max-input", type=int, default=1024)
    ap.add_argument("--max-new", type=int, default=448)
    ap.add_argument("--prefix", default="다음 글을 3~5문장으로 요약하세요.\n\n")
    ap.add_argument("--out", type=Path, default=OUT / "zero_shot_t5_val.jsonl")
    args = ap.parse_args()
    torch.set_num_threads(6)
    rows = read_jsonl(args.data)
    by_id = {str(r["id"]): r for r in rows}
    ids = set(json.loads(args.splits.read_text(encoding="utf-8"))[args.split])
    recs = [r for r in rows if str(r["id"]) in ids]
    recs = sorted(recs, key=lambda r: len(str(r["passage"])))
    if args.limit:
        recs = recs[: args.limit]
    tok = AutoTokenizer.from_pretrained(str(T5), local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        str(T5), local_files_only=True, dtype=torch.bfloat16, low_cpu_mem_usage=True
    ).eval()

    outputs = []
    for start in range(0, len(recs), args.batch_size):
        batch = recs[start : start + args.batch_size]
        texts = [args.prefix + str(r["passage"]) for r in batch]
        enc = tok(texts, return_tensors="pt", padding=True, truncation=True, max_length=args.max_input)
        with torch.inference_mode():
            gen = model.generate(
                **enc,
                max_new_tokens=args.max_new,
                num_beams=1,
                do_sample=False,
            )
        for i, rec in enumerate(batch):
            pred = tok.decode(gen[i], skip_special_tokens=True)
            target = str(rec["summary"])
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
    metrics = {
        "n": n,
        "char_f1_mean": sum(x["char_f1"] for x in outputs) / n,
        "grounded_rate": sum(x["grounded"] for x in outputs) / n,
        "new_slot_rate_mean": sum(x["new_slot_rate"] for x in outputs) / n,
        "new_slot_rate_micro": sum_new / sum_slots if sum_slots else 0.0,
        "new_slot_count": sum_new,
        "summary_slot_count": sum_slots,
        "eos_rate": sum(x["ended_eos"] for x in outputs) / n,
        "nonempty_rate": sum(x["nonempty"] for x in outputs) / n,
        "gen_len_mean": sum(x["gen_len"] for x in outputs) / n,
        "repeated_4gram_rate_mean": sum(x["repeated_4gram_rate"] for x in outputs) / n,
        "distinct_2_mean": sum(x["distinct_2"] for x in outputs) / n,
    }
    args.out.with_suffix(".metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"metrics": metrics, "prefix": args.prefix, "out": str(args.out)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
