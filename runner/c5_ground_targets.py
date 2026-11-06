"""Repair or filter F5 targets that contain ungrounded slots.

Policy (CP3-1, 2026-11-06):
- Keep records whose target has no new slot.
- Otherwise, drop target sentences that introduce a new slot; keep the record
  only if at least two sentences remain and the repaired target is grounded.
- Otherwise, exclude the record. The original file is never modified.
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

DEFAULT_INPUT = ROOT / "data/external/f5_pairs_v3.jsonl"
DEFAULT_OUTPUT = ROOT / "data/external/f5_pairs_v3_grounded.jsonl"
DEFAULT_CLEAN = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
DEFAULT_REJECTED = ROOT / "data/external/f5_pairs_v3_grounded_rejected.jsonl"
DEFAULT_REPORT = ROOT / "reports/provenance/C5/repair_report.json"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = [p.strip() for p in re.split(r"(?<=[.!?。！？])\s+|\n+", text) if p.strip()]
    return parts or [text]


def repair_record(rec: dict) -> tuple[dict | None, str, dict]:
    source = str(rec["passage"])
    target = str(rec["summary"])
    before = verify_summary(source, target)
    if not before.new:
        return rec, "clean", {"new_before": 0, "new_after": 0, "dropped_sentences": 0}

    kept: list[str] = []
    dropped = 0
    for sent in split_sentences(target):
        sr = verify_summary(source, sent)
        if sr.new:
            dropped += 1
            continue
        kept.append(sent)

    repaired = " ".join(kept).strip()
    after = verify_summary(source, repaired)
    # At least two sentences are required to avoid turning a summary into a
    # fragment; a sentence can be long, so also require >=40 chars.
    if len(kept) >= 2 and len(repaired) >= 40 and not after.new:
        out = dict(rec)
        out["summary"] = repaired
        return out, "repaired", {
            "new_before": len(before.new),
            "new_after": len(after.new),
            "dropped_sentences": dropped,
        }
    return None, "dropped", {
        "new_before": len(before.new),
        "new_after": len(after.new),
        "dropped_sentences": dropped,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--clean", type=Path, default=DEFAULT_CLEAN)
    ap.add_argument("--rejected", type=Path, default=DEFAULT_REJECTED)
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = ap.parse_args()
    records = read_jsonl(args.input)
    kept: list[dict] = []
    clean_records: list[dict] = []
    rejected: list[dict] = []
    counts = {"clean": 0, "repaired": 0, "dropped": 0}
    new_before = new_after = dropped_sentences = 0
    examples = []
    for rec in records:
        out, status, stats = repair_record(rec)
        counts[status] += 1
        new_before += stats["new_before"]
        new_after += stats["new_after"]
        dropped_sentences += stats["dropped_sentences"]
        if out is not None:
            kept.append(out)
            if status == "clean":
                clean_records.append(out)
        else:
            rejected.append(rec)
        if status != "clean" and len(examples) < 20:
            examples.append({"id": rec["id"], "status": status, **stats})
    write_jsonl(args.output, kept)
    write_jsonl(args.clean, clean_records)
    write_jsonl(args.rejected, rejected)
    report = {
        "input": str(args.input.relative_to(ROOT).as_posix()),
        "input_n": len(records),
        "kept_n": len(kept),
        "clean_n": len(clean_records),
        "rejected_n": len(rejected),
        "counts": counts,
        "new_slots_before": new_before,
        "new_slots_after": new_after,
        "dropped_sentences": dropped_sentences,
        "examples": examples,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
