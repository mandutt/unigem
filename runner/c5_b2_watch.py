"""15-minute watchdog for B2 full training."""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG = ROOT / "reports/provenance/C5_b1d/b2_full_train.log"
DEFAULT_CKPT = ROOT / "data/models/f5_t5gemma2_lora/b2_full"


def iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def tail_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        data = path.read_bytes()[-16384:].decode("utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for line in reversed(data):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "global_step" in obj or "epoch" in obj:
            return obj
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", type=Path, default=DEFAULT_LOG)
    ap.add_argument("--ckpt-dir", type=Path, default=DEFAULT_CKPT)
    ap.add_argument("--pid", type=int, default=0)
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--report-every", type=int, default=900)
    ap.add_argument("--stale-sec", type=int, default=1800)
    ap.add_argument("--max-hours", type=float, default=8.0)
    ap.add_argument("--out", type=Path, default=ROOT / "reports/provenance/C5_b1d/watch_b2.jsonl")
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    last_report = 0.0
    last_alert = 0.0

    def emit(status: str, extra: dict | None = None) -> None:
        nonlocal last_report
        paths = sorted(args.ckpt_dir.glob("adapter_step_*.pt")) if args.ckpt_dir.exists() else []
        final = args.ckpt_dir / "adapter_final.pt"
        last = tail_json(args.log)
        age = (time.time() - args.log.stat().st_mtime) if args.log.exists() else None
        row = {
            "ts": iso(),
            "status": status,
            "elapsed_sec": round(time.time() - start, 1),
            "pid": args.pid,
            "pid_alive": bool(args.pid and psutil.pid_exists(args.pid)),
            "log_age_sec": round(age, 1) if age is not None else None,
            "step_checkpoints": len(paths),
            "latest_checkpoint": paths[-1].name if paths else None,
            "final": final.exists(),
            "last": last,
        }
        if extra:
            row.update(extra)
        line = json.dumps(row, ensure_ascii=False)
        print(line, flush=True)
        with args.out.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        last_report = time.time()

    emit("WATCH_START")
    while True:
        time.sleep(max(10, args.interval))
        final = args.ckpt_dir / "adapter_final.pt"
        if final.exists():
            emit("TRAIN_DONE")
            return 0
        if args.pid and not psutil.pid_exists(args.pid):
            emit("TRAIN_FAIL", {"note": "worker exited before adapter_final.pt"})
            return 2
        if time.time() - start > args.max_hours * 3600:
            emit("WATCH_TIMEOUT")
            return 3
        age = (time.time() - args.log.stat().st_mtime) if args.log.exists() else None
        if age is not None and age >= args.stale_sec and time.time() - last_alert >= args.report_every:
            last_alert = time.time()
            emit("STALL", {"note": f"no log write for {age:.0f}s"})
        elif time.time() - last_report >= args.report_every:
            emit("WATCH_REPORT")


if __name__ == "__main__":
    raise SystemExit(main())
