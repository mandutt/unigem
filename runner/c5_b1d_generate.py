"""Generate and score B1d-full val summaries (adapter only, decoder frozen).

Uses the B1d adapter output directly as `encoder_outputs.last_hidden_state`.
No test split is loaded.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from transformers.modeling_outputs import BaseModelOutput

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval.slot_verify import verify_summary  # noqa: E402
from runner.c5_a2null_eval import char_f1, distinct_2, repeated_4gram_rate  # noqa: E402
from runner.c5_b1d_full import B1dFullAdapter, load_cache  # noqa: E402

T5 = ROOT / "data/models/t5gemma-2-270m-270m"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
ADAPTER = ROOT / "data/models/f5_t5gemma2_lora/b1d_full/adapter_final.pt"
OUT = ROOT / "reports/provenance/C5_b1d/generation_val.jsonl"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", type=Path, default=ADAPTER)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-new", type=int, default=448)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    torch.set_num_threads(6)
    t0 = time.time()
    rows = [
        json.loads(line)
        for line in DATA.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_id = {str(r["id"]): r for r in rows}
    splits = json.loads((ROOT / "reports/provenance/C5_clean/splits.json").read_text(encoding="utf-8"))
    ids = list(splits["val"])
    if args.limit:
        ids = ids[: args.limit]

    ckpt = torch.load(args.adapter, map_location="cpu")
    adapter = B1dFullAdapter()
    adapter.load_state_dict(ckpt["adapter"])
    adapter.eval()
    student = load_cache("student", "val")
    tok = AutoTokenizer.from_pretrained(str(T5), local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        str(T5), local_files_only=True, dtype=torch.bfloat16, low_cpu_mem_usage=True
    ).eval()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    done_ids = set()
    if args.out.exists():
        for line in args.out.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done_ids.add(str(json.loads(line)["id"]))
    outputs = []
    if args.out.exists():
        outputs = [json.loads(x) for x in args.out.read_text(encoding="utf-8").splitlines() if x.strip()]

    with args.out.open("a", encoding="utf-8") as fh:
        for rid in ids:
            if rid in done_ids:
                continue
            rec = by_id[rid]
            s = student[rid]
            T = s["length"]
            with torch.inference_mode():
                h_s = adapter(s["h"][:T].float().unsqueeze(0)).to(torch.bfloat16)
                mask = torch.ones(1, T, dtype=torch.bool)
                gen = model.generate(
                    encoder_outputs=BaseModelOutput(last_hidden_state=h_s),
                    attention_mask=mask,
                    max_new_tokens=args.max_new,
                    num_beams=1,
                    do_sample=False,
                )
            pred = tok.decode(gen[0], skip_special_tokens=True)
            target = str(rec["summary"])
            rep = verify_summary(str(rec["passage"]), pred)
            row = {
                "id": rid,
                "pred": pred,
                "target": target,
                "gen_len": int(gen[0].shape[0]),
                "h_norm_mean": float(h_s.float().norm(dim=-1).mean()),
                "ended_eos": bool((gen[0] == tok.eos_token_id).any()),
                "nonempty": bool(pred.strip()),
                "char_f1": char_f1(pred, target),
                "repeated_4gram_rate": repeated_4gram_rate(pred),
                "distinct_2": distinct_2(pred),
                "new_slot_count": len(rep.new),
                "summary_slot_count": rep.summary_count,
                "slot_preservation": rep.slot_preservation,
                "new_slot_rate": rep.new_slot_rate,
                "grounded": not rep.new,
            }
            outputs.append(row)
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            print(json.dumps({"done": len(outputs), "n": len(ids), "id": rid,
                              "char_f1": row["char_f1"], "grounded": row["grounded"],
                              "gen_len": row["gen_len"], "elapsed": round(time.time() - t0, 1)}),
                  flush=True)

    n = len(outputs)
    sum_slots = sum(x["summary_slot_count"] for x in outputs)
    sum_new = sum(x["new_slot_count"] for x in outputs)
    metrics = {
        "n": n,
        "adapter": str(args.adapter.relative_to(ROOT).as_posix()),
        "max_new": args.max_new,
        "char_f1_mean": sum(x["char_f1"] for x in outputs) / n if n else 0.0,
        "grounded_rate": sum(x["grounded"] for x in outputs) / n if n else 0.0,
        "new_slot_rate_micro": sum_new / sum_slots if sum_slots else 0.0,
        "new_slot_rate_mean": sum(x["new_slot_rate"] for x in outputs) / n if n else 0.0,
        "new_slot_count": sum_new,
        "summary_slot_count": sum_slots,
        "eos_rate": sum(x["ended_eos"] for x in outputs) / n if n else 0.0,
        "nonempty_rate": sum(x["nonempty"] for x in outputs) / n if n else 0.0,
        "gen_len_mean": sum(x["gen_len"] for x in outputs) / n if n else 0.0,
        "repeated_4gram_rate_mean": sum(x["repeated_4gram_rate"] for x in outputs) / n if n else 0.0,
        "distinct_2_mean": sum(x["distinct_2"] for x in outputs) / n if n else 0.0,
        "elapsed_sec": round(time.time() - t0, 1),
        "test_split_used": False,
    }
    args.out.with_suffix(".metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
