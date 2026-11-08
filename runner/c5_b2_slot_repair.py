"""Offline slot repair / groundability ceiling for B2 val161 outputs.

No model is loaded. For each prediction:
- keep the original if it has no new slots
- otherwise drop sentences that introduce new slots
- optionally choose the best subset of valid sentences (target-aware oracle)
- fallback to the first source sentence if the repaired summary is empty
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval.slot_verify import verify_summary  # noqa: E402
from runner.c5_a2null_eval import char_f1  # noqa: E402

DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
PRED = ROOT / "reports/provenance/C5_b1d/generation_val161_b2.jsonl"
OUT = ROOT / "reports/provenance/C5_b1d/slot_repair_val161.jsonl"
REPORT = ROOT / "reports/provenance/C5_b1d/slot_repair_val161.json"

SENT_RE = re.compile(r"(?<=[.!?。！？])\s+|\n+")


def sentences(text: str) -> list[str]:
    parts = [p.strip() for p in SENT_RE.split(text) if p.strip()]
    return parts or [text.strip()] if text.strip() else []


def valid_sentences(source: str, pred: str) -> tuple[list[str], list[str]]:
    parts = sentences(pred)
    good, bad = [], []
    for s in parts:
        r = verify_summary(source, s)
        (bad if r.new else good).append(s)
    return good, bad


def first_source_sentence(passage: str) -> str:
    parts = sentences(passage)
    return parts[0] if parts else passage[:200]


def choose_best_subset(source: str, target: str, good: list[str]) -> str:
    """Target-aware ceiling: best F1 subset of new-slot-free sentences."""
    if not good:
        return ""
    # Most outputs have a handful of sentences; brute force up to 12.
    if len(good) <= 12:
        best, best_f1 = "", -1.0
        for mask in range(1, 1 << len(good)):
            text = " ".join(good[i] for i in range(len(good)) if mask & (1 << i))
            f1 = char_f1(text, target)
            if f1 > best_f1:
                best, best_f1 = text, f1
        return best
    # Greedy fallback for unusually long outputs.
    chosen: list[str] = []
    best_f1 = -1.0
    remaining = list(good)
    while remaining:
        cand = max(
            remaining,
            key=lambda s: char_f1(" ".join(chosen + [s]), target),
        )
        f1 = char_f1(" ".join(chosen + [cand]), target)
        if f1 <= best_f1:
            break
        chosen.append(cand)
        remaining.remove(cand)
        best_f1 = f1
    return " ".join(chosen)


def repair_one(source: str, target: str, pred: str) -> dict:
    original = verify_summary(source, pred)
    good, bad = valid_sentences(source, pred)
    drop = " ".join(good).strip()
    oracle = choose_best_subset(source, target, good).strip()
    fallback = first_source_sentence(source)

    def finish(text: str, strategy: str) -> dict:
        if not text:
            text = fallback
            strategy = strategy + "+source_first"
        r = verify_summary(source, text)
        return {
            "strategy": strategy,
            "pred": text,
            "grounded": not r.new,
            "new_count": len(r.new),
            "missing_count": len(r.missing),
            "slot_preservation": r.slot_preservation,
            "summary_slot_count": r.summary_count,
            "char_f1": char_f1(text, target),
            "nonempty": bool(text.strip()),
            "gen_len": len(text),
        }

    drop_row = finish(drop, "drop_new_sentences")
    oracle_row = finish(oracle, "oracle_subset")
    original_row = {
        "strategy": "original",
        "pred": pred,
        "grounded": not original.new,
        "new_count": len(original.new),
        "missing_count": len(original.missing),
        "slot_preservation": original.slot_preservation,
        "summary_slot_count": original.summary_count,
        "char_f1": char_f1(pred, target),
        "nonempty": bool(pred.strip()),
        "gen_len": len(pred),
    }
    return {
        "original": original_row,
        "drop_new_sentences": drop_row,
        "oracle_subset": oracle_row,
        "n_sentences": len(sentences(pred)),
        "n_bad_sentences": len(bad),
    }


def aggregate(rows: list[dict], strategy: str) -> dict:
    vals = [r[strategy] for r in rows]
    n = len(vals)
    slots = sum(v["summary_slot_count"] for v in vals)
    new = sum(v["new_count"] for v in vals)
    return {
        "n": n,
        "char_f1_mean": sum(v["char_f1"] for v in vals) / n if n else 0.0,
        "grounded_rate": sum(v["grounded"] for v in vals) / n if n else 0.0,
        "nonempty_rate": sum(v["nonempty"] for v in vals) / n if n else 0.0,
        "new_count": new,
        "new_slot_rate_micro": new / slots if slots else 0.0,
        "missing_count": sum(v["missing_count"] for v in vals),
        "slot_preservation_mean": sum(v["slot_preservation"] for v in vals) / n if n else 0.0,
        "gen_len_mean": sum(v["gen_len"] for v in vals) / n if n else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", type=Path, default=PRED)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--report", type=Path, default=REPORT)
    args = ap.parse_args()
    for name in ("pred", "out", "report"):
        p = getattr(args, name)
        setattr(args, name, p if p.is_absolute() else ROOT / p)
    recs = [json.loads(x) for x in DATA.read_text(encoding="utf-8").splitlines() if x.strip()]
    by_id = {str(r["id"]): r for r in recs}
    preds = [json.loads(x) for x in args.pred.read_text(encoding="utf-8").splitlines() if x.strip()]
    rows = []
    for p in preds:
        rid = str(p["id"])
        rec = by_id[rid]
        row = {"id": rid, **repair_one(str(rec["passage"]), str(rec["summary"]), str(p["pred"]))}
        rows.append(row)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )
    report = {
        "n": len(rows),
        "source": str(args.pred.relative_to(ROOT).as_posix()),
        "original": aggregate(rows, "original"),
        "drop_new_sentences": aggregate(rows, "drop_new_sentences"),
        "oracle_subset": aggregate(rows, "oracle_subset"),
        "n_sentences_mean": sum(r["n_sentences"] for r in rows) / len(rows) if rows else 0.0,
        "n_bad_sentences_mean": sum(r["n_bad_sentences"] for r in rows) / len(rows) if rows else 0.0,
        "note": "oracle_subset uses the target summary for sentence selection; it is a ceiling, not a deployable method.",
        "test_split_used": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
