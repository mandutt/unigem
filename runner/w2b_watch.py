"""Periodic health monitor for W2B V2 training.

Checks every 60 seconds:
  - B0-prime process/log progress
  - B3 chain process/log progress
  - checkpoint recency
  - disk headroom

If B0-prime disappears before its final checkpoint and a resumable `.last.pt`
exists, it relaunches `d5_reader.py --resume` once (with a cooldown).
It does not kill healthy processes and does not restart a failed B3 arm from
scratch; those are alerts for human/agent review.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path("C:/code/unigem")
PY = str(ROOT / ".venv/Scripts/python.exe")
W2B = ROOT / "data/wave2b"
CKPT = W2B / "ckpt_v2"
B0_LOG = ROOT / "logs/W2B/b0p_v2_s42.log"
CHAIN_LOG = ROOT / "logs/W2B/b3_chain.log"
STATE = ROOT / "logs/W2B/watch_state.json"
ALERTS = ROOT / "logs/W2B/watch_alerts.log"
LOCK = ROOT / "logs/W2B/watch.lock"
B0_FINAL = CKPT / "b0p_v2_s42.pt"
B0_LAST = CKPT / "b0p_v2_s42.last.pt"
B0_BEST = CKPT / "b0p_v2_s42.best.pt"
CHAIN_DONE = W2B / "B3_CHAIN_DONE.json"


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def append_alert(msg: str) -> None:
    ALERTS.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERTS, "a", encoding="utf-8") as f:
        f.write(f"{now()} {msg}\n")


def tail_lines(p: Path, n: int = 5) -> list[str]:
    if not p.exists():
        return []
    try:
        return p.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
    except Exception:
        return []


def last_epoch(p: Path) -> tuple[int, str]:
    ep = 0
    last = ""
    for line in tail_lines(p, 50):
        if line.startswith("epoch "):
            last = line
            try:
                ep = int(line.split()[1].split("/")[0])
            except Exception:
                pass
    return ep, last


def age(p: Path) -> float:
    return time.time() - p.stat().st_mtime if p.exists() else 1e18


def processes() -> list[str]:
    out = []
    try:
        import psutil
        for pr in psutil.process_iter(["cmdline"]):
            try:
                cmd = " ".join(pr.info.get("cmdline") or [])
            except Exception:
                continue
            if "d5_reader.py" in cmd or "w2b_run_b3_chain.py" in cmd:
                out.append(cmd)
    except Exception:
        pass
    return out


def has_proc(needles: list[str]) -> bool:
    return any(all(n in c for n in needles) for c in processes())


def disk_free_gb(path: str = "C:/") -> float:
    try:
        import shutil
        return shutil.disk_usage(path).free / 1e9
    except Exception:
        return -1.0


def resume_b0() -> None:
    if not B0_LAST.exists():
        append_alert("B0 missing and no .last.pt; cannot resume")
        return
    args = [PY, "train/d5_reader.py",
            "--features", "data/wave1/feats/fc.npz",
            "--dev-features", "data/wave2b/feats_dev/fc.npz",
            "--vocab-file", "data/wave2b/vocab_v2.json",
            "--retarget", "--arch", "base", "--arm", "b0p_v2_s42",
            "--epochs", "12", "--patience", "4",
            "--batch", "2", "--grad-accum", "4",
            "--seed", "42", "--threads", "6", "--device", "cpu",
            "--resume", str(B0_LAST), "--ckpt-dir", str(CKPT)]
    log = ROOT / "logs/W2B/b0p_v2_resume.log"
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"\n{now()} AUTO_RESUME {' '.join(args)}\n")
    subprocess.Popen(args, cwd=str(ROOT), stdout=open(log, "ab"), stderr=subprocess.STDOUT,
                     start_new_session=True)
    append_alert(f"AUTO_RESUME B0 from {B0_LAST}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--max-hours", type=float, default=12)
    a = ap.parse_args()
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists() and not a.once:
        old = LOCK.read_text(encoding="utf-8", errors="replace").strip()
        raise SystemExit(f"watch lock exists: {old}")
    LOCK.write_text(f"{os.getpid()} {now()}", encoding="utf-8")
    deadline = time.time() + a.max_hours * 3600
    last_resume = 0.0
    while time.time() < deadline:
        procs = processes()
        b0_running = has_proc(["d5_reader.py", "b0p_v2_s42"])
        chain_running = has_proc(["w2b_run_b3_chain.py"])
        b3_running = has_proc(["d5_reader.py", "b3_v2_s42"])
        b3nat_running = has_proc(["d5_reader.py", "b3nat_v2_s42"])
        b0_ep, b0_line = last_epoch(B0_LOG)
        b0_age = age(B0_LOG)
        free = disk_free_gb("C:/")
        alert = ""
        if not B0_FINAL.exists() and not b0_running and b0_age > 900 and time.time() - last_resume > 1200:
            alert = f"B0 not running; log age={b0_age:.0f}s; attempting resume"
            resume_b0()
            last_resume = time.time()
        elif not B0_FINAL.exists() and b0_running and b0_age > 1800:
            alert = f"B0 running but log stale {b0_age:.0f}s"
        if B0_FINAL.exists() and not chain_running and not (b3_running or b3nat_running) and age(CHAIN_LOG) > 600:
            alert = "B0 final exists but B3 chain is not running"
        if free >= 0 and free < 5:
            alert = f"LOW DISK C: {free:.1f}GB"
        state = {
            "time": now(),
            "b0_running": b0_running, "chain_running": chain_running,
            "b3_running": b3_running, "b3nat_running": b3nat_running,
            "b0_epoch": b0_ep, "b0_last": b0_line,
            "b0_final": B0_FINAL.exists(), "b0_best": B0_BEST.exists(),
            "b0_log_age_s": round(b0_age, 1), "chain_done": CHAIN_DONE.exists(),
            "disk_free_gb": round(free, 2), "alert": alert,
            "procs": len(procs),
        }
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(state, ensure_ascii=False), flush=True)
        if alert:
            append_alert(alert)
        if CHAIN_DONE.exists() or (B0_FINAL.exists() and B3_FINAL_EXISTS()):
            print("WATCH_DONE", flush=True)
            break
        if a.once:
            break
        time.sleep(a.interval)
    LOCK.unlink(missing_ok=True)


def B3_FINAL_EXISTS() -> bool:
    return (CKPT / "b3_v2_s42.pt").exists() and (CKPT / "b3nat_v2_s42.pt").exists()


if __name__ == "__main__":
    main()
