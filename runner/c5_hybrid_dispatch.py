#!/usr/bin/env python3
"""D-086 Hoplite dispatch with checkpoint/resume.

- 5 concurrent workers (Hoplite Free concurrent limit)
- one task = one judge/doc prompt
- state.json is updated after every task
- rerunning skips done tasks
- CLI timeout does not imply thread failure: thread id is preserved for recovery
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CLI = Path("C:/Users/mandu/hermes-made/hoplite-advisor/hoplite_cli.py")
PROJECT = "proj_2e8de5ed594f47c7b851f1d7c5b52c61"
TASKS = ROOT / "reports/provenance/C5_hybrid/tasks.json"
STATE = ROOT / "reports/provenance/C5_hybrid/dispatch_state.json"
LOG = ROOT / "reports/provenance/C5_hybrid/dispatch.log"
THREAD_RE = re.compile(r"thr_[0-9a-f]{32}")


class State:
    def __init__(self, tasks: list[dict[str, Any]]) -> None:
        self.lock = threading.Lock()
        if STATE.exists():
            self.data = json.loads(STATE.read_text(encoding="utf-8"))
        else:
            self.data = {"tasks": {t["task_id"]: t for t in tasks}}
            self.save()
        self.tasks = self.data["tasks"]

    def save(self) -> None:
        tmp = STATE.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(STATE)

    def get(self, tid: str) -> dict[str, Any]:
        with self.lock:
            return self.tasks[tid]

    def update(self, tid: str, **kw: Any) -> None:
        with self.lock:
            self.tasks[tid].update(kw)
            self.save()

    def pending(self) -> list[dict[str, Any]]:
        with self.lock:
            return [t for t in self.tasks.values() if t.get("status") not in {"done", "thread_pending", "failed"}]


def log(msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def thread_id_from(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return None
    m = THREAD_RE.search(text)
    return m.group(0) if m else None


def run_one(task: dict[str, Any], state: State) -> bool:
    """Run one task. Return True when it should be retried."""
    tid = task["task_id"]
    if not CLI.exists():
        state.update(tid, status="failed", error=f"missing CLI: {CLI}")
        return False
    prompt = Path(task["prompt_path"]).read_text(encoding="utf-8")
    if len(prompt) < 1000:
        state.update(tid, status="failed", error="prompt too short")
        return False
    out = Path(task["out_path"])
    err = Path(task["err_path"])
    out.parent.mkdir(parents=True, exist_ok=True)
    err.parent.mkdir(parents=True, exist_ok=True)
    state.update(tid, status="running", started_at=datetime.now(timezone.utc).isoformat())
    cmd = [
        sys.executable, str(CLI), "ask", prompt,
        "--project", PROJECT,
        "--model", task["model"],
        "--reasoning", task["reasoning"],
        "--no-sync",
        "--timeout", "1800",
    ]
    try:
        with out.open("w", encoding="utf-8") as fo, err.open("w", encoding="utf-8") as fe:
            proc = subprocess.run(cmd, stdout=fo, stderr=fe, timeout=1900, cwd=str(ROOT))
        rc = proc.returncode
        thread = thread_id_from(err)
        if thread:
            state.update(tid, thread_id=thread)
        if rc == 0 and thread:
            state.update(tid, status="done", exit_code=rc, finished_at=datetime.now(timezone.utc).isoformat())
        elif thread:
            state.update(tid, status="thread_pending", exit_code=rc, finished_at=datetime.now(timezone.utc).isoformat(),
                         note="CLI ended before completion; server thread may still be running")
        else:
            raise RuntimeError(f"no thread id; exit={rc}")
        return False
    except subprocess.TimeoutExpired:
        thread = thread_id_from(err)
        if thread:
            state.update(tid, thread_id=thread, status="thread_pending", exit_code=124,
                         finished_at=datetime.now(timezone.utc).isoformat(),
                         note="CLI timeout; server thread may still be running")
        else:
            state.update(tid, status="failed", exit_code=124, error="timeout without thread id")
        return False
    except Exception as exc:  # noqa: BLE001
        attempts = int(task.get("attempts", 0)) + 1
        task["attempts"] = attempts
        state.update(tid, attempts=attempts, error=str(exc)[:500])
        if attempts < 3:
            state.update(tid, status="pending")
            return True
        state.update(tid, status="failed", finished_at=datetime.now(timezone.utc).isoformat())
        return False


def worker(q: "queue.Queue[dict[str, Any]]", state: State, stop: threading.Event) -> None:
    while not stop.is_set():
        try:
            task = q.get(timeout=1)
        except queue.Empty:
            continue
        try:
            retry = run_one(task, state)
            if retry:
                time.sleep(min(300, 15 * (2 ** int(task.get("attempts", 1)))))
                q.put(task)
        finally:
            q.task_done()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=5)
    args = ap.parse_args()
    if args.workers < 1 or args.workers > 5:
        raise SystemExit("workers must be 1..5")
    if not os.environ.get("HOPLITE_SERVICE_KEY"):
        raise SystemExit("HOPLITE_SERVICE_KEY missing")
    if not TASKS.exists():
        raise SystemExit(f"missing tasks: {TASKS}")
    tasks = json.loads(TASKS.read_text(encoding="utf-8"))["tasks"]
    state = State(tasks)
    q: "queue.Queue[dict[str, Any]]" = queue.Queue()
    pending = state.pending()
    for t in pending:
        q.put(t)
    log(f"START pending={len(pending)} workers={args.workers}")
    stop = threading.Event()
    threads = [threading.Thread(target=worker, args=(q, state, stop), daemon=True) for _ in range(args.workers)]
    for t in threads:
        t.start()
    q.join()
    stop.set()
    with state.lock:
        counts: dict[str, int] = {}
        for t in state.tasks.values():
            counts[t.get("status", "unknown")] = counts.get(t.get("status", "unknown"), 0) + 1
    log(f"DONE {json.dumps(counts, ensure_ascii=False)}")
    print(json.dumps(counts, ensure_ascii=False, indent=2))
    return 0 if counts.get("failed", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
