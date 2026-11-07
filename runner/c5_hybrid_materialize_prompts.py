#!/usr/bin/env python3
"""Materialize D-086 AI prompts into individual files and a dispatch manifest."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "reports/provenance/C5_hybrid/ai_inputs"
OUTDIR = ROOT / "docs/hoplite/c5_hybrid_2026-11-07"
TASKS = ROOT / "reports/provenance/C5_hybrid/tasks.json"


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    tasks = []
    for path in sorted(INPUTS.glob("judge_*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            judge = row["judge"]
            doc = row["doc_id"]
            pdir = OUTDIR / "prompts" / judge
            pdir.mkdir(parents=True, exist_ok=True)
            prompt_path = pdir / f"{doc}.txt"
            prompt_path.write_text(row["prompt"], encoding="utf-8")
            outdir = ROOT / "reports/provenance/C5_hybrid/ai_outputs" / judge
            outdir.mkdir(parents=True, exist_ok=True)
            tasks.append({
                "task_id": f"{judge}:{doc}",
                "judge": judge,
                "model": row["model"],
                "reasoning": row["reasoning"],
                "doc_id": doc,
                "prompt_path": str(prompt_path),
                "out_path": str(outdir / f"{doc}.out"),
                "err_path": str(outdir / f"{doc}.err"),
                "status": "pending",
                "attempts": 0,
                "thread_id": None,
            })
    if len(tasks) != 150:
        raise SystemExit(f"expected 150 tasks, got {len(tasks)}")
    TASKS.write_text(json.dumps({"tasks": tasks}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"tasks": len(tasks), "outdir": str(OUTDIR), "manifest": str(TASKS)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
