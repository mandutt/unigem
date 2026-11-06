"""Watch an A1 pilot log and report every 15 minutes."""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--report-every", type=int, default=900)
    ap.add_argument("--max-hours", type=float, default=2.0)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    last = 0.0
    while True:
        elapsed = time.time() - start
        if elapsed > args.max_hours * 3600:
            print(json.dumps({"time": now(), "status": "timeout"}), flush=True)
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
        done = "eval_metrics" in text or '"event": "metrics"' in text
        failed = "Traceback" in text or "nonfinite" in text or "rss_stop" in text
        if args.report_every and (time.time() - last >= args.report_every or done or failed):
            payload = {
                "time": now(), "status": "done" if done else ("failed" if failed else "running"),
                "log_age_s": age, "lines": len(lines), "tail": lines[-3:],
            }
            line = json.dumps(payload, ensure_ascii=False)
            print(line, flush=True)
            with args.out.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
            last = time.time()
        if done or failed:
            return 0 if done else 1
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
