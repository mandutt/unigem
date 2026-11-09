"""Audit the as-run copyable mask without changing it.

This is a report-only utility. It computes coverage for the existing rule and
for a candidate stricter rule, and emits a 100-token sample for human review.
It never trains, never opens test 163, and never changes the runner rule.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_mt5_lora_b0 import (  # noqa: E402
    DATA,
    SPLITS,
    copyable_mask,
    load_base,
)
from runner.c5_mt5_layer_probe import make_labels  # noqa: E402


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def normalized_piece(piece: str) -> str:
    return unicodedata.normalize("NFKC", piece).strip().replace(" ", "")


def strict_mask(passage: str, target_ids: list[int], tok, special_ids: set[int]) -> tuple[list[bool], int]:
    source_norm = unicodedata.normalize("NFKC", passage).replace(" ", "")
    vals: list[bool] = []
    for tid in target_ids:
        if int(tid) in special_ids:
            vals.append(False)
            continue
        piece = normalized_piece(tok.decode([int(tid)], skip_special_tokens=False))
        if len(piece) < 2 or not re.search(r"[0-9A-Za-z가-힣]", piece):
            vals.append(False)
            continue
        vals.append(piece in source_norm)
    return vals, int(sum(vals))


def audit(rows: dict[str, dict], ids: list[str], split: str, limit: int) -> dict[str, Any]:
    tok, _ = load_base()
    special = {int(x) for x in tok.all_special_ids}
    records: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    for rid in ids[:limit]:
        row = rows[rid]
        labels = make_labels(tok, str(row["summary"]), 256)
        target_ids = labels[0].tolist()
        as_run, as_count = copyable_mask(str(row["passage"]), target_ids, tok, special)
        strict, strict_count = strict_mask(str(row["passage"]), target_ids, tok, special)
        n = len(target_ids)
        source_norm = unicodedata.normalize("NFKC", str(row["passage"])).replace(" ", "")
        records.append({
            "id": rid,
            "target_tokens": n,
            "as_run_copy_tokens": as_count,
            "as_run_coverage": as_count / max(1, n),
            "strict_piece_len_ge2_copy_tokens": strict_count,
            "strict_piece_len_ge2_coverage": strict_count / max(1, n),
        })
        for tid, keep in zip(target_ids, as_run[0].tolist()):
            if not keep or len(samples) >= 100:
                continue
            piece = normalized_piece(tok.decode([int(tid)], skip_special_tokens=False))
            pos = source_norm.find(piece)
            samples.append({
                "doc_id": rid,
                "token_id": int(tid),
                "piece": piece,
                "source_found": pos >= 0,
                "source_context": source_norm[max(0, pos - 30): pos + 70] if pos >= 0 else "",
            })
    def dist(key: str) -> dict[str, float]:
        vals = [float(r[key]) for r in records]
        if not vals:
            return {"mean": 0.0, "median": 0.0, "p05": 0.0, "p95": 0.0}
        vals_sorted = sorted(vals)
        return {
            "mean": float(statistics.mean(vals)),
            "median": float(statistics.median(vals)),
            "p05": float(vals_sorted[max(0, int(0.05 * (len(vals_sorted) - 1)))]),
            "p95": float(vals_sorted[min(len(vals_sorted) - 1, int(0.95 * (len(vals_sorted) - 1)))]),
        }

    return {
        "experiment": "c5_b0_mask_audit",
        "split": split,
        "n_docs": len(records),
        "n_target_tokens": sum(r["target_tokens"] for r in records),
        "as_run": {
            "rule": "NFKC, remove spaces, any non-special piece with a letter/digit substring in source",
            "coverage": dist("as_run_coverage"),
            "total_copy_tokens": sum(r["as_run_copy_tokens"] for r in records),
            "adoption": "as-run; no rule change in runner",
        },
        "candidate_strict_piece_len_ge2": {
            "rule": "same as as-run, but require normalized piece length >= 2",
            "coverage": dist("strict_piece_len_ge2_coverage"),
            "total_copy_tokens": sum(r["strict_piece_len_ge2_copy_tokens"] for r in records),
            "adoption": "candidate only; requires a new preregistration",
        },
        "sample": samples,
        "sample_status": "manual/blind adjudication required; not counted as precision",
        "test_split_used": False,
        "records": records,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "val"], default="val")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--val-start", type=int, default=5)
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--splits", type=Path, default=SPLITS)
    ap.add_argument("--out", type=Path, default=ROOT / "reports/provenance/C5_b0a/mask_audit.json")
    args = ap.parse_args()
    if args.split == "val":
        ids = [str(x) for x in json.loads(args.splits.read_text(encoding="utf-8"))["val"][args.val_start:args.val_start + args.limit]]
    else:
        ids = [str(x) for x in json.loads(args.splits.read_text(encoding="utf-8"))["train"][:args.limit]]
    rows = {str(r["id"]): r for r in read_jsonl(args.data)}
    payload = audit(rows, ids, args.split, args.limit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("split", "n_docs", "n_target_tokens", "as_run", "candidate_strict_piece_len_ge2", "sample_status") if k in payload}, ensure_ascii=False, indent=2))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
