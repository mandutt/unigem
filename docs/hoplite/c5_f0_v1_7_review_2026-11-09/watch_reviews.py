#!/usr/bin/env python3
"""Poll the C5 Phase 6 v1.0.1 review threads and save reports."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs" / "hoplite" / "c5_f0_v1_7_review_2026-11-09"
API = "https://api.hoplite.sh"
TAGS = {
    "glm": ("GLM", "z-ai/glm-5.3-flash"),
    "ds1017": ("DS1017", "deepseek-v4.1-flash-1017"),
    "sol": ("SOL", "gpt-6.1-sol"),
    "luna": ("LUNA", "gpt-6-luna"),
}


def read_key() -> str:
    key = os.environ.get("HOPLITE_SERVICE_KEY", "")
    if len(key) < 20:
        raise SystemExit("HOPLITE_SERVICE_KEY missing")
    return key


def get_json(path: str, key: str):
    req = urllib.request.Request(API + path, headers={"X-Api-Key": key, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def unwrap_thread(obj):
    return obj.get("thread", obj) if isinstance(obj, dict) else {}


def get_messages(thread_id: str, key: str) -> list[dict]:
    data = get_json(f"/api/threads/{thread_id}/messages?limit=100", key)
    if isinstance(data, dict):
        for k in ("messages", "results", "data"):
            if isinstance(data.get(k), list):
                return data[k]
        return []
    return data if isinstance(data, list) else []


def get_diff_files(thread_id: str, key: str) -> list[dict]:
    data = get_json(f"/api/threads/{thread_id}/diff?mode=base", key)
    if isinstance(data, dict):
        diff = data.get("diff", data)
        files = diff.get("files", []) if isinstance(diff, dict) else []
        return files if isinstance(files, list) else []
    return []


def patch_to_text(patch: str) -> str:
    out = []
    for line in patch.splitlines():
        if line.startswith(("+++", "---", "diff --git", "@@")):
            continue
        if line.startswith("+"):
            out.append(line[1:])
    return "\n".join(out).strip()


def filename_of(f: dict, patch: str) -> str:
    name = f.get("path") or f.get("filename")
    if not name:
        m = re.search(r"^\+\+\+ b/(.+)$", patch, re.M)
        name = m.group(1) if m else ""
    return str(name or "")


def save_from_diff(tag: str, thread_id: str, key: str) -> int:
    saved = 0
    for f in get_diff_files(thread_id, key):
        patch = f.get("patch") or ""
        name = filename_of(f, patch)
        if not name.lower().endswith(".md"):
            continue
        text = patch_to_text(patch)
        if len(text) < 500:
            continue
        target = OUT / f"review_{TAGS[tag][0]}.md"
        if target.exists() and target.stat().st_size > len(text.encode("utf-8")):
            continue
        target.write_text(text, encoding="utf-8")
        print(f"SAVED {tag} {target.name} {len(text)} chars from {name}", flush=True)
        saved += 1
    return saved


def save_from_messages(tag: str, thread_id: str, key: str) -> int:
    parts = []
    for m in get_messages(thread_id, key):
        if not isinstance(m, dict) or m.get("role") != "assistant":
            continue
        content = m.get("content")
        if isinstance(content, str) and len(content) >= 500:
            parts.append(content)
    if not parts:
        return 0
    text = "\n\n".join(parts)
    target = OUT / f"review_{TAGS[tag][0]}.md"
    if target.exists() and target.stat().st_size > len(text.encode("utf-8")):
        return 0
    target.write_text(text, encoding="utf-8")
    print(f"SAVED {tag} {target.name} {len(text)} chars from messages", flush=True)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-hours", type=float, default=5.0)
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--report-every", type=int, default=900)
    args = ap.parse_args()

    key = read_key()
    tfile = OUT / "threads.json"
    if not tfile.exists():
        print("MISSING threads.json", flush=True)
        return 3
    threads = json.loads(tfile.read_text(encoding="utf-8"))
    if isinstance(threads, dict):
        threads = [{"tag": k, "id": v} for k, v in threads.items()]
    for row in threads:
        row.setdefault("tag", "")
        row.setdefault("id", "")

    deadline = time.time() + args.max_hours * 3600
    last_report = 0.0
    done: set[str] = set()
    for row in threads:
        tag = row.get("tag", "")
        if tag in TAGS and (OUT / f"review_{TAGS[tag][0]}.md").exists():
            done.add(tag)

    while time.time() < deadline:
        states = []
        for row in threads:
            tag = row.get("tag", "")
            tid = row.get("id", "")
            if tag not in TAGS or not tid:
                continue
            try:
                t = unwrap_thread(get_json(f"/api/threads/{tid}", key))
                status = t.get("status") or t.get("runStatus") or "unknown"
                states.append(f"{tag}:{status}")
                if status in {"ready", "done", "completed", "failed"}:
                    n = save_from_diff(tag, tid, key)
                    if n == 0:
                        n = save_from_messages(tag, tid, key)
                    if n > 0 or (OUT / f"review_{TAGS[tag][0]}.md").exists():
                        done.add(tag)
            except Exception as e:
                states.append(f"{tag}:ERR({type(e).__name__})")
        print("STATUS " + " ".join(states) + f" done={len(done)}/3", flush=True)
        if len(done) >= 3:
            print("DONE 3/3", flush=True)
            return 0
        now = time.time()
        if now - last_report >= args.report_every:
            print(f"REPORT {time.strftime('%Y-%m-%dT%H:%M:%S%z')} {states} done={sorted(done)}", flush=True)
            last_report = now
        time.sleep(args.interval)
    print("TIMEOUT", flush=True)
    return 3


if __name__ == "__main__":
    sys.exit(main())
