"""15-minute watchdog for the B1d full cache.

Read-only: counts shards, checks progress/staleness, and writes a status line
to stdout and a JSONL log. Exits when the cache is complete or the process dies.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data/wave2c/b1d"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
LOG = ROOT / "reports/provenance/C5_b1d/watch.jsonl"
SHARD = 32


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def count_shards(kind: str, split: str) -> tuple[int, int, float]:
    files = sorted((CACHE / kind).glob(f"{split}_*.npz"))
    files = [p for p in files if p.stat().st_size > 0 and not p.name.endswith(".tmp.npz")]
    if not files:
        return 0, 0, 0.0
    return len(files), sum(p.stat().st_size for p in files), max(p.stat().st_mtime for p in files)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, default=0)
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--report-every", type=int, default=900)
    ap.add_argument("--stall-sec", type=int, default=1200)
    ap.add_argument("--log", type=Path, default=LOG)
    args = ap.parse_args()

    splits = json.loads(SPLITS.read_text(encoding="utf-8"))
    expected = {
        (kind, split): math.ceil(len(splits[split]) / SHARD)
        for kind in ("teacher", "student") for split in ("train", "val")
    }
    args.log.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    last_report = 0.0
    last_alert = 0.0

    def emit(status: str, extra: dict | None = None) -> None:
        nonlocal last_report
        snap = {}
        total_files = total_expected = 0
        newest = 0.0
        for (kind, split), need in expected.items():
            n, nbytes, mt = count_shards(kind, split)
            total_files += n
            total_expected += need
            newest = max(newest, mt)
            snap[f"{kind}_{split}"] = {"shards": n, "expected": need, "bytes": nbytes}
        age = (time.time() - newest) if newest else None
        row = {
            "ts": now_iso(),
            "status": status,
            "elapsed_sec": round(time.time() - start, 1),
            "shards": total_files,
            "expected_shards": total_expected,
            "progress": round(total_files / total_expected, 4) if total_expected else 0.0,
            "last_write_age_sec": round(age, 1) if age is not None else None,
            "pid": args.pid,
            "pid_alive": bool(args.pid and psutil.pid_exists(args.pid)),
            "detail": snap,
        }
        if extra:
            row.update(extra)
        line = json.dumps(row, ensure_ascii=False)
        print(line, flush=True)
        with args.log.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        last_report = time.time()

    emit("WATCH_START", {"note": "B1d cache shard progress; 15-minute reports"})
    while True:
        time.sleep(max(10, args.interval))
        total_files = sum(count_shards(k, s)[0] for (k, s) in expected)
        total_expected = sum(expected.values())
        if total_files >= total_expected:
            emit("CACHE_DONE", {"note": "all teacher/student shards present"})
            return 0
        if args.pid and not psutil.pid_exists(args.pid):
            emit("WATCH_FAIL", {"note": "cache process is gone before completion"})
            return 2
        _, _, newest = count_shards("teacher", "train")
        for k, s in expected:
            _, _, mt = count_shards(k, s)
            newest = max(newest, mt)
        age = (time.time() - newest) if newest else None
        if age is not None and age >= args.stall_sec and time.time() - last_alert >= args.report_every:
            last_alert = time.time()
            emit("STALL", {"note": f"no shard write for {age:.0f}s"})
        elif time.time() - last_report >= args.report_every:
            emit("WATCH_REPORT")


if __name__ == "__main__":
    raise SystemExit(main())
