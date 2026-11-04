#!/usr/bin/env python3
"""Watch Hoplite w2b_2c_short_v2 threads and recover reports."""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request

API = "https://api.hoplite.sh"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DIR = os.path.join(ROOT, "docs", "hoplite", "w2b_2c_short_v2")
LOG = os.path.join(DIR, "watch_w2b_2c_short_v2.log")
THREAD_FILE = os.path.join(DIR, "threads.json")
REPORTS = {
    m: os.path.join(DIR, f"2026-11-04_hoplite-review_w2b_2c_short_v2_{m}.md")
    for m in ("GLM", "SONNET", "LUNA")
}
DONE: set[str] = set()
MAX_WAIT = 3 * 3600
POLL = 30


def key() -> str:
    k = os.environ.get("HOPLITE_SERVICE_KEY") or os.environ.get("HOPLITE_API_KEY")
    if not k:
        raise SystemExit("missing HOPLITE_SERVICE_KEY")
    return k


def api(path: str, k: str):
    req = urllib.request.Request(API + path, headers={"X-Api-Key": k})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def patch_text(patch: str) -> str:
    out = []
    for line in patch.splitlines():
        if line.startswith(("+++", "---", "@@", "diff --git", "new file mode", "index ")):
            continue
        if line.startswith("+"):
            out.append(line[1:])
        elif line.startswith(" "):
            out.append(line[1:])
    return "\n".join(out).strip() + "\n"


def save_diff(model: str, tid: str, k: str) -> bool:
    time.sleep(8)
    try:
        d = api(f"/api/threads/{tid}/diff?mode=base", k)
    except Exception as e:
        log(f"{model} diff error: {e}")
        return False
    files = (d.get("diff") or {}).get("files") or []
    candidates = []
    for f in files:
        patch = f.get("patch") or ""
        name = f.get("filename")
        if not name:
            m = re.search(r"^\+\+\+ b/(.+)$", patch, re.M)
            name = m.group(1) if m else ""
        base = os.path.basename(name or "")
        if name and name.endswith(".md") and "w2b_2c_short_v2" in base:
            candidates.append((name, patch))
    if not candidates:
        return False
    path, patch = candidates[0]
    text = patch_text(patch)
    if len(text.strip()) < 500:
        return False
    with open(REPORTS[model], "w", encoding="utf-8") as f:
        f.write(text)
    log(f"DONE {model} diff {path} chars={len(text)}")
    return True


def save_messages(model: str, tid: str, k: str) -> bool:
    try:
        d = api(f"/api/threads/{tid}/messages?limit=100", k)
    except Exception as e:
        log(f"{model} messages error: {e}")
        return False
    msgs = d.get("messages", d.get("results", d.get("data", [])))
    if isinstance(msgs, dict):
        msgs = msgs.get("messages", [])
    if not isinstance(msgs, list):
        msgs = []
    chunks = []
    for m in msgs:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = m.get("content") or ""
        if role == "assistant" and isinstance(content, str) and len(content) >= 500:
            chunks.append(content)
    if not chunks:
        return False
    chunks.sort(key=len, reverse=True)
    text = "\n\n---\n\n".join(chunks[:3])
    path = REPORTS[model].replace(".md", "_fallback.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    log(f"DONE {model} fallback chars={len(text)} path={path}")
    return True


def main() -> int:
    k = key()
    os.makedirs(DIR, exist_ok=True)
    if not os.path.exists(THREAD_FILE):
        raise SystemExit("missing threads.json")
    threads = json.loads(open(THREAD_FILE, encoding="utf-8").read())
    threads = {str(m).upper(): str(t) for m, t in threads.items()}
    log("START w2b_2c_short_v2 watcher")
    last_status: dict[str, str] = {}
    start = time.time()
    while time.time() - start < MAX_WAIT:
        for model, tid in threads.items():
            if model in DONE:
                continue
            try:
                d = api(f"/api/threads/{tid}", k)
                t = d.get("thread", d)
                status = t.get("status")
                if status != last_status.get(model):
                    log(f"{model} status={status} run={t.get('runStatus')}")
                    last_status[model] = status
                if status == "ready":
                    if not save_diff(model, tid, k):
                        if not save_messages(model, tid, k):
                            log(f"{model} ready but no report yet")
                            continue
                    DONE.add(model)
                elif status == "failed":
                    log(f"{model} failed; inspect messages")
                    DONE.add(model)
            except Exception as e:
                log(f"{model} poll error: {e}")
        if len(DONE) == len(threads):
            log("ALL DONE")
            return 0
        time.sleep(POLL)
    log("TIMEOUT")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
