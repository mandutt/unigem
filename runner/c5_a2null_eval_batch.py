"""Batched val evaluation for A2-null adapters (generation)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from transformers.modeling_outputs import BaseModelOutput

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval.slot_verify import verify_summary  # noqa: E402
from runner.c5_a2null_eval import (  # noqa: E402
    char_f1, distinct_2, load_adapter, load_features, read_jsonl, repeated_4gram_rate,
)

T5 = ROOT / "data/models/t5gemma-2-270m-270m"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
FEATURES = ROOT / "data/wave2c/a2null"
OUT = ROOT / "reports/provenance/C5_a2null"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features-dir", type=Path, default=FEATURES)
    ap.add_argument("--adapter", type=Path, required=True)
    ap.add_argument("--split", default="val", choices=["train", "val"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--max-new", type=int, default=448)
    ap.add_argument("--max-memory", type=int, default=1024)
    ap.add_argument("--out", type=Path, default=OUT / "predictions_batch.jsonl")
    args = ap.parse_args()
    torch.set_num_threads(6)
    rows = read_jsonl(DATA)
    by_id = {str(r["id"]): r for r in rows}
    feats = load_features(args.features_dir, args.split, 0)
    if args.limit:
        feats = feats[: args.limit]
    feats = sorted(feats, key=lambda x: int(x["length"]))
    tok = AutoTokenizer.from_pretrained(str(T5), local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        str(T5), local_files_only=True, dtype=torch.bfloat16, low_cpu_mem_usage=True
    ).eval()
    adapter = load_adapter(args.adapter)

    outputs = []
    for start in range(0, len(feats), args.batch_size):
        batch = feats[start : start + args.batch_size]
        max_t = max(min(int(r["length"]), args.max_memory) for r in batch)
        memory = torch.zeros(len(batch), max_t, 640, dtype=torch.bfloat16)
        mask = torch.zeros(len(batch), max_t, dtype=torch.bool)
        for i, rec in enumerate(batch):
            t = min(int(rec["length"]), args.max_memory)
            if not bool(rec["mask"][:t].all()):
                raise SystemExit(f"non-contiguous feature mask: {rec['id']}")
            m = adapter(rec["z"][:t].unsqueeze(0)).to(torch.bfloat16)
            memory[i, :t] = m[0]
            mask[i, :t] = True
        with torch.inference_mode():
            gen = model.generate(
                encoder_outputs=BaseModelOutput(last_hidden_state=memory),
                attention_mask=mask,
                max_new_tokens=args.max_new,
                num_beams=1,
                do_sample=False,
            )
        for i, rec in enumerate(batch):
            pred = tok.decode(gen[i], skip_special_tokens=True)
            target = str(by_id[rec["id"]]["summary"])
            rep = verify_summary(str(by_id[rec["id"]]["passage"]), pred)
            outputs.append({
                "id": rec["id"],
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
        print(json.dumps({"done": len(outputs), "n": len(feats)}), flush=True)

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
    print(json.dumps({"metrics": metrics, "out": str(args.out)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
