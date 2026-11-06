#!/usr/bin/env python3
"""Select the best A1 checkpoint from per-step val metrics.

This applies the pre-registered safety gates, then maximizes char F1 and
breaks ties toward the earlier checkpoint. It does not run generation itself.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True, help="training output dir containing eval_step_*")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--min-grounded", type=float, default=0.99)
    ap.add_argument("--max-new-slot-micro", type=float, default=0.01)
    ap.add_argument("--min-eos", type=float, default=0.95)
    ap.add_argument("--max-repeated4", type=float, default=0.06)
    args = ap.parse_args()

    root = args.root.resolve()
    rows = []
    for d in sorted(root.glob("eval_step_*")):
        m = re.search(r"eval_step_(\d+)$", d.name)
        if not m:
            continue
        metrics_path = d / "eval.metrics.json"
        if not metrics_path.exists():
            continue
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        step = int(m.group(1))
        eligible = (
            metrics.get("grounded_rate", 0.0) >= args.min_grounded
            and metrics.get("new_slot_rate_micro", 1.0) <= args.max_new_slot_micro
            and metrics.get("eos_rate", 0.0) >= args.min_eos
            and metrics.get("repeated_4gram_rate_mean", 1.0) <= args.max_repeated4
        )
        rows.append({"step": step, "eligible": eligible, "metrics": metrics})
    if not rows:
        raise SystemExit(f"no eval_step_*/eval.metrics.json under {root}")

    eligible_rows = [r for r in rows if r["eligible"]]
    if eligible_rows:
        # max char F1, ties toward earlier checkpoint
        best = sorted(eligible_rows, key=lambda r: (-r["metrics"]["char_f1_mean"], r["step"]))[0]
    else:
        best = None

    result = {
        "root": str(root),
        "gates": {
            "min_grounded": args.min_grounded,
            "max_new_slot_micro": args.max_new_slot_micro,
            "min_eos": args.min_eos,
            "max_repeated4": args.max_repeated4,
        },
        "candidates": [
            {
                "step": r["step"],
                "eligible": r["eligible"],
                "char_f1": r["metrics"].get("char_f1_mean"),
                "grounded": r["metrics"].get("grounded_rate"),
                "new_slot_micro": r["metrics"].get("new_slot_rate_micro"),
                "eos": r["metrics"].get("eos_rate"),
                "repeated4": r["metrics"].get("repeated_4gram_rate_mean"),
                "slot_preservation": r["metrics"].get("slot_preservation_mean"),
                "slots_per_doc": r["metrics"].get("slots_per_doc"),
            }
            for r in rows
        ],
        "selected_step": best["step"] if best else None,
        "selected_char_f1": best["metrics"].get("char_f1_mean") if best else None,
        "reason": "highest char_f1 among eligible; tie -> earlier step" if best else "no eligible checkpoint",
    }
    out = args.out or (root / "selection.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
