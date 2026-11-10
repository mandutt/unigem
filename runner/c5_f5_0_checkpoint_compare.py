#!/usr/bin/env python3
"""Compare existing A1 pilot300 and full2ep checkpoint val161 predictions.

No generation, no training, no test-163 read. All inputs are existing artifacts.
"""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_f5_0_analyze import dist, ngrams, norm, ratio  # noqa: E402

DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
OUT = ROOT / "reports/provenance/C5_f5_0"

CHECKPOINTS = [
    ("pilot300", ROOT / "reports/provenance/C5_a1/pilot300_val161/predictions.jsonl"),
    ("full_0647", ROOT / "reports/provenance/C5_a1/full_2ep/eval_step_0647/eval.jsonl"),
    ("full_1293", ROOT / "reports/provenance/C5_a1/full_2ep/eval_step_1293/eval.jsonl"),
    ("full_1940", ROOT / "reports/provenance/C5_a1/full_2ep/eval_step_1940/eval.jsonl"),
    ("full_2586", ROOT / "reports/provenance/C5_a1/full_2ep/eval_step_2586/eval.jsonl"),
]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    data = {str(r["id"]): r for r in read_jsonl(DATA)}
    val_ids = {str(x) for x in json.loads(SPLITS.read_text(encoding="utf-8"))["val"]}
    src_by_id = {rid: norm(r["passage"]) for rid, r in data.items()}

    rows_by_ckpt: dict[str, list[dict]] = {}
    target_copy8: list[float] = []
    target_novel4: list[float] = []
    for label, path in CHECKPOINTS:
        rows = read_jsonl(path)
        if len(rows) != 161:
            raise SystemExit(f"{label}: expected 161 rows, got {len(rows)}")
        if {str(r["id"]) for r in rows} != val_ids:
            raise SystemExit(f"{label}: id set differs from F5 val split")
        rows_by_ckpt[label] = rows
        if not target_copy8:
            for r in rows:
                tgt, src = norm(r["target"]), src_by_id[str(r["id"])]
                t8, s8 = ngrams(tgt, 8), ngrams(src, 8)
                t4, s4 = ngrams(tgt, 4), ngrams(src, 4)
                target_copy8.append(ratio(len(t8 & s8), len(t8)))
                target_novel4.append(1.0 - ratio(len(t4 & s4), len(t4)))

    target = {
        "copy8": dist(target_copy8),
        "novel4": dist(target_novel4),
    }

    out: dict[str, dict] = {}
    for label, rows in rows_by_ckpt.items():
        vals = {
            "char_f1": [],
            "copy8": [],
            "novel4": [],
            "compression": [],
            "gen_len": [],
            "slot_preservation": [],
            "repeated4": [],
            "distinct2": [],
            "grounded": 0,
            "eos": 0,
            "high_copy8": 0,
            "low_slot": 0,
            "high_rep": 0,
            "low_f1": 0,
        }
        for r in rows:
            rid = str(r["id"])
            pred, src = norm(r["pred"]), src_by_id[rid]
            p8, s8 = ngrams(pred, 8), ngrams(src, 8)
            p4, s4 = ngrams(pred, 4), ngrams(src, 4)
            copy8 = ratio(len(p8 & s8), len(p8))
            novel4 = 1.0 - ratio(len(p4 & s4), len(p4))
            vals["char_f1"].append(float(r["char_f1"]))
            vals["copy8"].append(copy8)
            vals["novel4"].append(novel4)
            vals["compression"].append(ratio(len(pred), len(src)))
            vals["gen_len"].append(float(r.get("gen_len") or len(pred)))
            vals["slot_preservation"].append(float(r.get("slot_preservation", 0.0)))
            vals["repeated4"].append(float(r.get("repeated_4gram_rate", 0.0)))
            vals["distinct2"].append(float(r.get("distinct_2", 0.0)))
            vals["grounded"] += int(bool(r.get("grounded", False)))
            vals["eos"] += int(bool(r.get("ended_eos", False)))
            vals["high_copy8"] += int(copy8 >= 0.80)
            vals["low_slot"] += int(float(r.get("slot_preservation", 0.0)) < 0.20)
            vals["high_rep"] += int(float(r.get("repeated_4gram_rate", 0.0)) >= 0.10)
            vals["low_f1"] += int(float(r["char_f1"]) < 0.55)

        out[label] = {
            "input": str(CHECKPOINTS[[c[0] for c in CHECKPOINTS].index(label)][1].relative_to(ROOT)),
            "input_sha256": sha256(CHECKPOINTS[[c[0] for c in CHECKPOINTS].index(label)][1]),
            "n": len(rows),
            "char_f1": dist(vals["char_f1"]),
            "copy8": dist(vals["copy8"]),
            "novel4": dist(vals["novel4"]),
            "compression": dist(vals["compression"]),
            "gen_len": dist(vals["gen_len"]),
            "slot_preservation": dist(vals["slot_preservation"]),
            "repeated4": dist(vals["repeated4"]),
            "distinct2": dist(vals["distinct2"]),
            "grounded_rate": ratio(vals["grounded"], len(rows)),
            "eos_rate": ratio(vals["eos"], len(rows)),
            "high_copy8": vals["high_copy8"],
            "low_slot": vals["low_slot"],
            "high_rep": vals["high_rep"],
            "low_f1": vals["low_f1"],
            "copy8_minus_target": statistics.fmean(
                c - t for c, t in zip(vals["copy8"], target_copy8)
            ),
            "novel4_minus_target": statistics.fmean(
                n - t for n, t in zip(vals["novel4"], target_novel4)
            ),
        }

    payload = {
        "status": "ANALYSIS_ONLY_NO_REGENERATION",
        "target": target,
        "checkpoints": out,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "checkpoint_compare.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print("checkpoint      n   F1     copy8  novel4  slot   rep4   highCopy lowSlot highRep lowF1")
    for label in out:
        x = out[label]
        print(
            f"{label:12s} {x['n']:3d}  {x['char_f1']['mean']:.4f} "
            f"{x['copy8']['mean']:.4f} {x['novel4']['mean']:.4f} "
            f"{x['slot_preservation']['mean']:.4f} {x['repeated4']['mean']:.4f} "
            f"{x['high_copy8']:8d} {x['low_slot']:7d} {x['high_rep']:7d} {x['low_f1']:5d}"
        )
    print("target copy8", target["copy8"]["mean"], "novel4", target["novel4"]["mean"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
