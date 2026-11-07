#!/usr/bin/env python3
"""Archive completed D-086 Hoplite threads while dispatch continues.

Reads dispatch_state.json, archives only status=done threads, and records
archived thread IDs in a separate ledger (no write race with the dispatcher).
"""
from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "reports/provenance/C5_hybrid/dispatch_state.json"
LEDGER = ROOT / "reports/provenance/C5_hybrid/archive_ledger.json"
LOG = ROOT / "reports/provenance/C5_hybrid/archive.log"
API = "https://api.hoplite.sh"


def log(msg: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def key() -> str:
    k = os.environ.get("HOPLITE_SERVICE_KEY", "")
    if len(k) < 20:
        raise SystemExit("HOPLITE_SERVICE_KEY missing")
    return k


def api(method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(
        API + path,
        data=data,
        method=method,
        headers={"X-Api-Key": key(), "Content-Type": "application/json"},
    )
    with urlopen(req, timeout=30) as resp:
        return json.load(resp)


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_ledger(ledger: dict[str, Any]) -> None:
    tmp = LEDGER.with_suffix(".tmp")
    tmp.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(LEDGER)


def archive_one(tid: str, ledger: dict[str, Any]) -> bool:
    if tid in ledger.get("archived", {}):
        return False
    try:
        data = api("GET", f"/api/threads/{tid}")
        thread = data.get("thread", data)
        if thread.get("archivedAt"):
            ledger.setdefault("archived", {})[tid] = {
                "archived_at": thread.get("archivedAt"),
                "note": "already archived",
            }
            save_ledger(ledger)
            return False
        status = thread.get("status")
        if status != "ready":
            return False
        version = thread.get("archiveVersion", 0)
        body = {
            "archived": True,
            "expectedArchiveVersion": version,
            "clientOperationId": str(uuid.uuid4()),
        }
        api("PATCH", f"/api/threads/{tid}", body)
        ledger.setdefault("archived", {})[tid] = {
            "archived_at": datetime.now(timezone.utc).isoformat(),
            "archive_version": version,
        }
        save_ledger(ledger)
        log(f"ARCHIVED {tid} ver={version}")
        return True
    except HTTPError as exc:
        log(f"ARCHIVE_FAIL {tid} HTTP {exc.code}")
    except Exception as exc:  # noqa: BLE001
        log(f"ARCHIVE_FAIL {tid} {str(exc)[:300]}")
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=30)
    ap.add_argument("--max-hours", type=float, default=6.0)
    args = ap.parse_args()
    ledger = load_json(LEDGER, {"archived": {}})
    start = time.time()
    while True:
        state = load_json(STATE, {"tasks": {}})
        tasks = state.get("tasks", {})
        done = [
            t for t in tasks.values()
            if t.get("status") == "done" and t.get("thread_id") and t["thread_id"] not in ledger.get("archived", {})
        ]
        for t in done:
            archive_one(t["thread_id"], ledger)
        if time.time() - start > args.max_hours * 3600:
            log("STOP max-hours")
            return 0
        active = [t for t in tasks.values() if t.get("status") in {"pending", "running"}]
        if not done and not active:
            log(f"DONE archived={len(ledger.get('archived', {}))}")
            return 0
        time.sleep(max(5, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
