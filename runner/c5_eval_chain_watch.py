"""Watchdog for the C5 evaluation chain. Reports every 15 minutes."""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs/C5/eval_chain"
STATE = LOG_DIR / "state.json"
WATCH_LOG = LOG_DIR / "watch.log"


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def tail(path: Path, n: int = 3) -> list[str]:
    if not path.exists():
        return []
    try:
        return [x.rstrip() for x in path.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]]
    except OSError:
        return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--report-every", type=int, default=900)
    ap.add_argument("--max-hours", type=float, default=4.0)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    start = time.time()
    last_report = 0.0
    while True:
        elapsed = time.time() - start
        if elapsed > args.max_hours * 3600:
            print(json.dumps({"time": now(), "status": "watchdog_timeout"}), flush=True)
            return 2
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            state = {"status": "starting"}
        status = state.get("status", "unknown")
        current = state.get("current")
        log_path = Path(state.get("current_log", "")) if state.get("current_log") else None
        due = args.once or status in {"done", "failed"} or (time.time() - last_report >= args.report_every)
        if due:
            payload = {
                "time": now(),
                "status": status,
                "current": current,
                "done": state.get("done", 0),
                "total": state.get("total"),
                "steps": state.get("steps", []),
                "tail": tail(log_path, 3) if log_path else [],
            }
            line = json.dumps(payload, ensure_ascii=False)
            print(line, flush=True)
            with WATCH_LOG.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
            last_report = time.time()
        if status in {"done", "failed"}:
            return 0 if status == "done" else 1
        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
