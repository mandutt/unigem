"""A0 extractive baseline on the clean val 161 split (same IDs as A2-null)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_summary_eval import evaluate_a0, read_jsonl, write_json, write_jsonl  # noqa: E402

DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
OUT = ROOT / "reports/provenance/C5_clean/a0_val161.json"
REPORT = ROOT / "reports/C5_a0_val161.md"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--splits", type=Path, default=SPLITS)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--report", type=Path, default=REPORT)
    args = ap.parse_args()
    records = read_jsonl(args.data)
    split = json.loads(args.splits.read_text(encoding="utf-8"))
    val_ids = split["val"]
    metrics, rows = evaluate_a0(records, val_ids)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.out, {"metrics": metrics, "n": len(rows)})
    write_jsonl(args.out.with_suffix(".predictions.jsonl"), rows)
    lines = [
        "# A0 추출형 baseline — clean val 161",
        "",
        f"- data: `{args.data.resolve().relative_to(ROOT).as_posix()}`",
        f"- split: `{args.splits.resolve().relative_to(ROOT).as_posix()}`",
        f"- n: **{len(rows)}**",
        "",
        "| metric | value |",
        "|---|---:|",
    ]
    for k, v in metrics.items():
        lines.append(f"| {k} | {v:.6f} |" if isinstance(v, float) else f"| {k} | {v} |")
    lines += [
        "",
        "A0는 추출형 기준선이며 최종 추상 요약기가 아니다.",
        "같은 val 161 ID에서 A2-null과 paired 비교한다.",
    ]
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"metrics": metrics, "out": str(args.out)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
