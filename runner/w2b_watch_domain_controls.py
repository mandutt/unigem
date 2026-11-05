"""Periodic monitor for the domain/length control chain."""
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
CKPT = W2B / "ckpt_controls"
LOG = ROOT / "logs/W2B/domain_controls.log"
STATE = ROOT / "logs/W2B/domain_controls_watch_state.json"
ALERTS = ROOT / "logs/W2B/domain_controls_watch_alerts.log"
LOCK = ROOT / "logs/W2B/domain_controls_watch.lock"
DONE = W2B / "DOMAIN_CONTROLS_DONE.json"
FAIL = W2B / "DOMAIN_CONTROLS_FAILED.txt"
ARMS = ["b3long_v2_s42", "b3zeroth_v2_s42"]


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def append_alert(msg: str) -> None:
    ALERTS.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERTS, "a", encoding="utf-8") as f:
        f.write(f"{now()} {msg}\n")


def tail_lines(p: Path, n: int = 120) -> list[str]:
    if not p.exists():
        return []
    try:
        return p.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
    except Exception:
        return []


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
            if "w2b_run_domain_controls.py" in cmd or "d5_reader.py" in cmd or "w1_extract.py" in cmd:
                out.append(cmd)
    except Exception:
        pass
    return out


def last_stage() -> str:
    lines = tail_lines(LOG, 200)
    for line in reversed(lines):
        if " START " in line or " END " in line or " TRAIN " in line:
            return line[-180:]
    return ""


def resume_chain() -> None:
    log = ROOT / "logs/W2B/domain_controls_resume.log"
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"\n{now()} AUTO_RESUME runner/w2b_run_domain_controls.py\n")
    subprocess.Popen(
        [PY, "runner/w2b_run_domain_controls.py"], cwd=str(ROOT),
        stdout=open(log, "ab"), stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    append_alert("AUTO_RESUME domain controls chain")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--max-hours", type=float, default=12)
    a = ap.parse_args()
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists() and not a.once:
        raise SystemExit(f"watch lock exists: {LOCK.read_text(encoding='utf-8', errors='replace').strip()}")
    LOCK.write_text(f"{os.getpid()} {now()}", encoding="utf-8")
    deadline = time.time() + a.max_hours * 3600
    last_resume = 0.0
    while time.time() < deadline:
        ps = procs()
        chain = any("w2b_run_domain_controls.py" in c for c in ps)
        training = {arm: any("d5_reader.py" in c and f"--arm {arm}" in c for c in ps) for arm in ARMS}
        log_age = age(LOG)
        ckpt_age = {arm: min(age(CKPT / f"{arm}.last.pt"), age(CKPT / f"{arm}.best.pt")) for arm in ARMS}
        final = {arm: (CKPT / f"{arm}.pt").exists() for arm in ARMS}
        progress_age = min([log_age] + [v for v in ckpt_age.values()])
        free = disk_free_gb("C:/")
        alert = ""
        if not DONE.exists() and not FAIL.exists() and not chain and not any(training.values()):
            if log_age > 900 and time.time() - last_resume > 1200:
                alert = f"chain not running; log age={log_age:.0f}s; attempting resume"
                resume_chain()
                last_resume = time.time()
        if chain and progress_age > 1800:
            alert = f"chain running but progress stale {progress_age:.0f}s: {last_stage()}"
        if FAIL.exists():
            alert = f"failure sentinel: {FAIL.read_text(encoding='utf-8', errors='replace').strip()[:240]}"
        if free >= 0 and free < 5:
            alert = f"LOW DISK C: {free:.1f}GB"
        state = {
            "time": now(),
            "chain_running": chain,
            "training": training,
            "stage": last_stage(),
            "log_age_s": round(log_age, 1),
            "ckpt_age_s": {k: round(v, 1) for k, v in ckpt_age.items()},
            "ckpt_final": final,
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
