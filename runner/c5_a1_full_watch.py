#!/usr/bin/env python3
"""Watch a long A1 full-train run and report every N seconds.

Unlike c5_a1_watch.py, this watcher does not treat a checkpoint eval_metrics
event as final completion. It waits for the training PID to exit (or for the
expected final step plus a later eval_metrics line).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

ROOT = Path(__file__).resolve().parents[1]


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def find_training_pid(match: str) -> int:
    if psutil is None:
        return 0
    candidates = []
    for p in psutil.process_iter(["pid", "cmdline", "memory_info"]):
        try:
            if p.info["pid"] in {os.getpid(), os.getppid()}:
                continue
            cmd = " ".join(p.info.get("cmdline") or [])
            # Do not match this watcher's own --match argument.
            if "c5_a1_full_watch.py" in cmd:
                continue
            if match in cmd and "c5_a1_lora.py" in cmd and "--mode full" in cmd:
                rss = p.info.get("memory_info").rss if p.info.get("memory_info") else 0
                candidates.append((rss, p.info["pid"]))
        except Exception:
            continue
    if not candidates:
        return 0
    # The venv launcher and the uv child share a cmdline; choose the real worker
    # by RSS instead of the small launcher process.
    return max(candidates)[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--pid", type=int, default=0)
    ap.add_argument("--match", default="runner/c5_a1_lora.py")
    ap.add_argument("--expected-steps", type=int, default=0)
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--report-every", type=int, default=1800)
    ap.add_argument("--max-hours", type=float, default=8.0)
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    start = time.time()
    last_report = 0.0
    seen_process = False
    while True:
        elapsed = time.time() - start
        if elapsed > args.max_hours * 3600:
            print(json.dumps({"time": now(), "status": "timeout", "elapsed_s": round(elapsed, 1)}), flush=True)
            return 2

        text = ""
        age = None
        if args.log.exists():
            try:
                text = args.log.read_text(encoding="utf-8", errors="replace")
                age = round(time.time() - args.log.stat().st_mtime, 1)
            except OSError:
                pass

        lines = [x for x in text.splitlines() if x.startswith("{")]
        steps = [int(x) for x in re.findall(r'"step":\s*(\d+)', text)]
        last_step = max(steps) if steps else None
        pid = args.pid or find_training_pid(args.match)
        if pid:
            seen_process = True
        alive = bool(psutil and pid and psutil.pid_exists(pid))
        if psutil is None:
            # Conservative fallback: do not declare completion without psutil.
            alive = True

        failed = any(k in text for k in ("Traceback", '"event": "nonfinite"', '"event": "rss_stop"', '"event": "step_time_stop"'))
        final_eval = False
        if args.expected_steps:
            final_eval = (
                f'"step": {args.expected_steps}' in text
                and text.rfind('"event": "eval_metrics"') > text.rfind(f'"step": {args.expected_steps}')
            )
        done = seen_process and not alive
        if not seen_process and not failed:
            status = "waiting"
        elif not alive and not failed and not final_eval and args.expected_steps and (last_step or 0) < args.expected_steps:
            status = "exited"
        elif failed:
            status = "failed"
        elif done:
            status = "done"
        elif age is not None and age > 1800:
            status = "stalled"
        else:
            status = "running"

        if args.report_every and (time.time() - last_report >= args.report_every or status in {"done", "failed", "exited", "timeout"}):
            payload = {
                "time": now(),
                "status": status,
                "elapsed_s": round(elapsed, 1),
                "log_age_s": age,
                "last_step": last_step,
                "lines": len(lines),
                "pid": pid or None,
                "alive": alive,
                "tail": lines[-3:],
            }
            line = json.dumps(payload, ensure_ascii=False)
            print(line, flush=True)
            with args.out.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
            last_report = time.time()

        if status in {"done", "failed", "exited"}:
            return 0 if status == "done" else 1
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
