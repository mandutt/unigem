"""Watch the step-matched B3-long training run."""
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
ARM = "b3long_sm_v2_s42"
CKPT = ROOT / "data/wave2b/ckpt_controls"
LOG = ROOT / "logs/W2B/b3long_sm.log"
STATE = ROOT / "logs/W2B/b3long_sm_watch_state.json"
ALERTS = ROOT / "logs/W2B/b3long_sm_watch_alerts.log"
LOCK = ROOT / "logs/W2B/b3long_sm_watch.lock"
DONE = ROOT / "data/wave2b/B3LONG_SM_DONE.json"
FAIL = ROOT / "data/wave2b/B3LONG_SM_FAILED.txt"


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def age(p: Path) -> float:
    return time.time() - p.stat().st_mtime if p.exists() else 1e18


def tail(p: Path, n: int = 30) -> list[str]:
    if not p.exists():
        return []
    try:
        return p.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
    except Exception:
        return []


def procs() -> list[str]:
    out = []
    try:
        import psutil
        for pr in psutil.process_iter(["cmdline"]):
            try:
                cmd = " ".join(pr.info.get("cmdline") or [])
            except Exception:
                continue
            if "w2b_run_b3long_sm.py" in cmd or ("d5_reader.py" in cmd and f"--arm {ARM}" in cmd):
                out.append(cmd)
    except Exception:
        pass
    return out


def disk_free_gb() -> float:
    try:
        import shutil
        return shutil.disk_usage("C:/").free / 1e9
    except Exception:
        return -1.0


def resume() -> None:
    log = ROOT / "logs/W2B/b3long_sm_resume.log"
    with log.open("a", encoding="utf-8") as f:
        f.write(f"\n{now()} AUTO_RESUME runner/w2b_run_b3long_sm.py\n")
    subprocess.Popen([PY, "runner/w2b_run_b3long_sm.py"], cwd=str(ROOT),
                     stdout=open(log, "ab"), stderr=subprocess.STDOUT,
                     start_new_session=True)
    append_alert("AUTO_RESUME b3long_sm")


def append_alert(msg: str) -> None:
    ALERTS.parent.mkdir(parents=True, exist_ok=True)
    with ALERTS.open("a", encoding="utf-8") as f:
        f.write(f"{now()} {msg}\n")


def last_epoch() -> str:
    for line in reversed(tail(LOG, 80)):
        if "epoch " in line and "dev_cer=" in line:
            return line[-190:]
    return ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--max-hours", type=float, default=6)
    a = ap.parse_args()
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists() and not a.once:
        raise SystemExit(f"watch lock exists: {LOCK.read_text(encoding='utf-8', errors='replace').strip()}")
    LOCK.write_text(f"{os.getpid()} {now()}", encoding="utf-8")
    deadline = time.time() + a.max_hours * 3600
    last_resume = 0.0
    while time.time() < deadline:
        ps = procs()
        running = bool(ps)
        log_age = age(LOG)
        last_age = min(age(CKPT / f"{ARM}.last.pt"), age(CKPT / f"{ARM}.best.pt"))
        final = (CKPT / f"{ARM}.pt").exists()
        free = disk_free_gb()
        alert = ""
        if not DONE.exists() and not FAIL.exists() and not running:
            if log_age > 900 and time.time() - last_resume > 1200:
                alert = f"not running; log age={log_age:.0f}s; auto-resume"
                resume()
                last_resume = time.time()
        if running and min(log_age, last_age) > 1800:
            alert = f"running but progress stale {min(log_age,last_age):.0f}s: {last_epoch()}"
        if FAIL.exists():
            alert = f"failure sentinel: {FAIL.read_text(encoding='utf-8', errors='replace').strip()[:240]}"
        if free >= 0 and free < 5:
            alert = f"LOW DISK C: {free:.1f}GB"
        state = {
            "time": now(), "running": running, "arm": ARM,
            "epoch": last_epoch(), "log_age_s": round(log_age, 1),
            "ckpt_age_s": round(last_age, 1), "ckpt_final": final,
            "done": DONE.exists(), "failed": FAIL.exists(),
            "disk_free_gb": round(free, 2), "alert": alert,
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
