"""Watch the A2-null EOS-corrected full adapter training run."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

ROOT = Path("C:/code/unigem")
PY = str(ROOT / ".venv/Scripts/python.exe")
ARM = "a2null_full_eos"
OUT = ROOT / "data/models/f5_a2null_full_eos"
LOG = ROOT / "logs/C5/a2null_full_eos.log"
STATE = ROOT / "logs/C5/a2null_full_eos_watch_state.json"
ALERTS = ROOT / "logs/C5/a2null_full_eos_watch_alerts.log"
WATCH_LOG = ROOT / "logs/C5/a2null_full_eos_watch.log"
LOCK = ROOT / "logs/C5/a2null_full_eos_watch.lock"
DONE = OUT / "train_report.json"
ADAPTER = OUT / "adapter.pt"
LAST = OUT / "last.pt"
FAIL = OUT / "FAILED.txt"
CMD = [
    PY,
    "runner/c5_a2null_full_train.py",
    "--out", str(OUT),
    "--epochs", "1",
    "--max-memory", "1024",
    "--max-target", "512",
    "--checkpoint-every", "100",
]


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def age(p: Path) -> float:
    return time.time() - p.stat().st_mtime if p.exists() else 1e18


def tail(p: Path, n: int = 60) -> list[str]:
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
            if "c5_a2null_full_train.py" in cmd and "f5_a2null_full_eos" in cmd:
                out.append(cmd)
    except Exception:
        pass
    return out


def disk_free_gb() -> float:
    try:
        return shutil.disk_usage("C:/").free / 1e9
    except Exception:
        return -1.0


def append_alert(msg: str) -> None:
    ALERTS.parent.mkdir(parents=True, exist_ok=True)
    with ALERTS.open("a", encoding="utf-8") as f:
        f.write(f"{now()} {msg}\n")


def resume() -> None:
    WATCH_LOG.parent.mkdir(parents=True, exist_ok=True)
    with WATCH_LOG.open("a", encoding="utf-8") as f:
        f.write(f"\n{now()} AUTO_RESUME {' '.join(CMD)}\n")
    subprocess.Popen(
        CMD,
        cwd=str(ROOT),
        stdout=open(LOG, "ab"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    append_alert("AUTO_RESUME a2null_full_eos")


def last_progress() -> str:
    for line in reversed(tail(LOG, 120)):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if "step" in obj:
            return f"epoch {obj.get('epoch')} step {obj.get('step')} loss {obj.get('loss')}"
        if "epoch" in obj and "train_loss" in obj:
            return f"epoch {obj.get('epoch')} train_loss {obj.get('train_loss')} val_loss {obj.get('val_loss')}"
    return ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--report-every", type=int, default=900)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--no-resume", action="store_true")
    ap.add_argument("--max-hours", type=float, default=3.0)
    a = ap.parse_args()
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists() and not a.once:
        raise SystemExit(f"watch lock exists: {LOCK.read_text(encoding='utf-8', errors='replace').strip()}")
    LOCK.write_text(f"{os.getpid()} {now()}", encoding="utf-8")
    deadline = time.time() + a.max_hours * 3600
    last_resume = 0.0
    last_report = 0.0
    resumes = 0
    while time.time() < deadline:
        ps = procs()
        running = bool(ps)
        log_age = age(LOG)
        ckpt_age = min(age(LAST), age(ADAPTER))
        done = DONE.exists()
        failed = FAIL.exists()
        free = disk_free_gb()
        alert = ""
        if not done and not failed and not running and not a.no_resume:
            if log_age > 900 and time.time() - last_resume > 1200 and resumes < 3:
                alert = f"not running; log age={log_age:.0f}s; auto-resume #{resumes + 1}"
                resume()
                last_resume = time.time()
                resumes += 1
        if running and min(log_age, ckpt_age) > 1800:
            alert = f"running but progress stale {min(log_age, ckpt_age):.0f}s: {last_progress()}"
        if failed:
            alert = f"failure sentinel: {FAIL.read_text(encoding='utf-8', errors='replace').strip()[:240]}"
        if free >= 0 and free < 5:
            alert = f"LOW DISK C: {free:.1f}GB"
        state = {
            "time": now(),
            "running": running,
            "arm": ARM,
            "progress": last_progress(),
            "log_age_s": round(log_age, 1),
            "ckpt_age_s": round(ckpt_age, 1),
            "ckpt_final": ADAPTER.exists(),
            "done": done,
            "failed": failed,
            "disk_free_gb": round(free, 2),
            "resumes": resumes,
            "alert": alert,
            "procs": len(ps),
        }
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report_due = a.once or done or bool(alert) or (time.time() - last_report >= a.report_every)
        if report_due:
            line = json.dumps(state, ensure_ascii=False)
            print(line, flush=True)
            WATCH_LOG.parent.mkdir(parents=True, exist_ok=True)
            with WATCH_LOG.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
            last_report = time.time()
        if alert:
            append_alert(alert)
        if done:
            print("WATCH_DONE", flush=True)
            with WATCH_LOG.open("a", encoding="utf-8") as f:
                f.write(f"{now()} WATCH_DONE\n")
            break
        if a.once:
            break
        time.sleep(a.interval)
    LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
