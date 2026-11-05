"""Periodic health monitor for the B0-prime matched-budget controls.

Every 60s:
  - detects the b0p_v2_s42_e20 / e38 training process
  - parses the last epoch and dev CER from logs/W2B/b0_matched.log
  - checks .last/.best checkpoint recency
  - checks disk headroom
  - auto-restarts runner/w2b_run_b0_matched.py once per cooldown if the
    chain disappears before B0_MATCHED_DONE.json (the runner resumes .last.pt)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

ROOT = Path("C:/code/unigem")
PY = str(ROOT / ".venv/Scripts/python.exe")
W2B = ROOT / "data/wave2b"
CKPT = W2B / "ckpt_matched"
LOG = ROOT / "logs/W2B/b0_matched.log"
STATE = ROOT / "logs/W2B/b0_matched_watch_state.json"
ALERTS = ROOT / "logs/W2B/b0_matched_watch_alerts.log"
LOCK = ROOT / "logs/W2B/b0_matched_watch.lock"
DONE = W2B / "B0_MATCHED_DONE.json"
FAIL = W2B / "B0_MATCHED_FAILED.txt"
ARMS = ["b0p_v2_s42_e20", "b0p_v2_s42_e38"]


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def append_alert(msg: str) -> None:
    ALERTS.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERTS, "a", encoding="utf-8") as f:
        f.write(f"{now()} {msg}\n")


def tail_lines(p: Path, n: int = 80) -> list[str]:
    if not p.exists():
        return []
    try:
        return p.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
    except Exception:
        return []


def last_epoch() -> tuple[int, int, str]:
    ep = total = 0
    last = ""
    for line in tail_lines(LOG, 120):
        if line.startswith("epoch "):
            last = line
            try:
                a, b = line.split()[1].split("/")
                ep, total = int(a), int(b)
            except Exception:
                pass
    return ep, total, last


def age(p: Path) -> float:
    return time.time() - p.stat().st_mtime if p.exists() else 1e18


def disk_free_gb(path: str = "C:/") -> float:
    try:
        import shutil
        return shutil.disk_usage(path).free / 1e9
    except Exception:
        return -1.0


def procs() -> list[str]:
    out = []
    try:
        import psutil
        for pr in psutil.process_iter(["cmdline"]):
            try:
                cmd = " ".join(pr.info.get("cmdline") or [])
            except Exception:
                continue
            if "d5_reader.py" in cmd or "w2b_run_b0_matched.py" in cmd:
                out.append(cmd)
    except Exception:
        pass
    return out


def arm_running(cmd: str, arm: str) -> bool:
    return "d5_reader.py" in cmd and f"--arm {arm}" in cmd


def resume_chain() -> None:
    log = ROOT / "logs/W2B/b0_matched_resume.log"
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"\n{now()} AUTO_RESUME runner/w2b_run_b0_matched.py\n")
    subprocess.Popen(
        [PY, "runner/w2b_run_b0_matched.py"],
        cwd=str(ROOT),
        stdout=open(log, "ab"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    append_alert("AUTO_RESUME b0 matched chain")


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
        ps = procs()
        running = {arm: any(arm_running(c, arm) for c in ps) for arm in ARMS}
        chain_running = any("w2b_run_b0_matched.py" in c for c in ps)
        ep, total, last = last_epoch()
        log_age = age(LOG)
        ckpt_ages = {arm: min(age(CKPT / f"{arm}.last.pt"), age(CKPT / f"{arm}.best.pt")) for arm in ARMS}
        ckpt_done = {arm: (CKPT / f"{arm}.pt").exists() for arm in ARMS}
        progress_age = min([log_age] + [v for v in ckpt_ages.values()])
        free = disk_free_gb("C:/")

        alert = ""
        if not DONE.exists() and not chain_running and not any(running.values()):
            if log_age > 900 and time.time() - last_resume > 1200:
                alert = f"chain not running; log age={log_age:.0f}s; attempting resume"
                resume_chain()
                last_resume = time.time()
        if any(running.values()) and progress_age > 1800:
            alert = f"training running but progress stale {progress_age:.0f}s: {last[-160:]}"
        if FAIL.exists() and not DONE.exists():
            alert = f"failure sentinel exists: {FAIL.read_text(encoding='utf-8', errors='replace').strip()[:200]}"
        if free >= 0 and free < 5:
            alert = f"LOW DISK C: {free:.1f}GB"

        state = {
            "time": now(),
            "chain_running": chain_running,
            "arm_running": running,
            "epoch": ep,
            "epoch_total": total,
            "last": last,
            "log_age_s": round(log_age, 1),
            "ckpt_age_s": {k: round(v, 1) for k, v in ckpt_ages.items()},
            "ckpt_final": ckpt_done,
            "done": DONE.exists(),
            "failed": FAIL.exists(),
            "disk_free_gb": round(free, 2),
            "alert": alert,
            "procs": len(ps),
        }
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(state, ensure_ascii=False), flush=True)
        if alert:
            append_alert(alert)
        if DONE.exists():
            print("WATCH_DONE", flush=True)
            break
        if a.once:
            break
        time.sleep(a.interval)
    LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
