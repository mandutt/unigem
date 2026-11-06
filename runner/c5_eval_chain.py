"""Sequential C5 A2-null evaluation chain.

Steps: A0 val -> A2-null EOS val -> A2-null LN val -> zero-shot T5 -> memory ablation.
Writes a state file for the watchdog; never uses the sealed test split.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs/C5/eval_chain"
STATE = LOG_DIR / "state.json"
REPORT = LOG_DIR / "chain_report.json"
PY = sys.executable

STEPS = [
    ("a0_val161", [PY, "runner/c5_a0_val161.py"]),
    ("a2null_eos_val161", [
        PY, "runner/c5_a2null_eval_batch.py",
        "--adapter", "data/models/f5_a2null_full_eos/adapter.pt",
        "--split", "val", "--batch-size", "8", "--max-new", "448",
        "--out", "reports/provenance/C5_a2null/a2null_eos_val161_predictions.jsonl",
    ]),
    ("a2null_ln_val161", [
        PY, "runner/c5_a2null_eval_batch.py",
        "--adapter", "data/models/f5_a2null_full_ln/adapter.pt",
        "--split", "val", "--batch-size", "8", "--max-new", "448",
        "--out", "reports/provenance/C5_a2null/a2null_ln_val161_predictions.jsonl",
    ]),
    ("zero_shot_t5_val161", [
        PY, "runner/c5_zero_shot_t5.py",
        "--split", "val", "--batch-size", "4", "--max-new", "448",
        "--out", "reports/provenance/C5_a2null/zero_shot_t5_val161.jsonl",
    ]),
    ("memory_ablation_val161", [
        PY, "runner/c5_a2null_ablation.py",
        "--adapters", "data/models/f5_a2null_full_eos/adapter.pt",
        "data/models/f5_a2null_full_ln/adapter.pt",
        "--out", "reports/provenance/C5_a2null/memory_ablation_val161.json",
    ]),
]


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_state(state: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STATE)


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    state = {
        "status": "running",
        "pid": __import__("os").getpid(),
        "started": now(),
        "current": None,
        "current_log": None,
        "steps": [],
        "done": 0,
        "total": len(STEPS),
    }
    write_state(state)
    for name, cmd in STEPS:
        log = LOG_DIR / f"{name}.log"
        state.update({"current": name, "current_log": str(log), "step_started": now()})
        write_state(state)
        t0 = time.time()
        with log.open("w", encoding="utf-8", errors="replace") as f:
            f.write("$ " + " ".join(cmd) + "\n")
            f.flush()
            rc = subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT).returncode
        sec = round(time.time() - t0, 1)
        state["steps"].append({"name": name, "rc": rc, "seconds": sec, "log": str(log)})
        state["done"] += 1
        state["current"] = None
        if rc != 0:
            state.update({"status": "failed", "failed_step": name, "finished": now()})
            write_state(state)
            REPORT.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"status": "failed", "step": name, "rc": rc}), flush=True)
            return rc
        write_state(state)
        print(json.dumps({"step": name, "rc": rc, "seconds": sec}), flush=True)
    state.update({"status": "done", "finished": now()})
    write_state(state)
    REPORT.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "done", "steps": state["steps"]}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
