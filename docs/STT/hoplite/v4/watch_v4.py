#!/usr/bin/env python3
"""Watch Hoplite v4 review threads and recover report files.

Uses only the standard library. The service key must be in
HOPLITE_SERVICE_KEY (or HOPLITE_API_KEY). Never prints the key.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

API = "https://api.hoplite.sh"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DIR = os.path.join(ROOT, "docs", "hoplite", "v4")
LOG = os.path.join(DIR, "watch_v4.log")
THREADS = {
    "GLM": "thr_790930f5f3b449baac37da7b0c113691",
    "SONNET": "thr_30632cc9c1f149d49c6d05ad21c9ae84",
    "LUNA": "thr_303b93161be047fda00498adff4b425a",
}
REPORTS = {
    "GLM": os.path.join(DIR, "2026-11-04_hoplite-review_v4_GLM.md"),
    "SONNET": os.path.join(DIR, "2026-11-04_hoplite-review_v4_SONNET.md"),
    "LUNA": os.path.join(DIR, "2026-11-04_hoplite-review_v4_LUNA.md"),
}
DONE = set()
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
        if name and name.endswith(".md") and "_v4_" in os.path.basename(name):
            candidates.append((name, patch))
    if not candidates:
        return False
    # Prefer the exact expected filename, but write whatever the model produced.
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
    # Keep the longest assistant message(s); final/narration variants should both survive.
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
    start = time.time()
    log("START v4 watcher")
    last_status = {}
    while time.time() - start < MAX_WAIT:
        for model, tid in THREADS.items():
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
        if len(DONE) == len(THREADS):
            log("ALL DONE")
            return 0
        time.sleep(POLL)
    log("TIMEOUT")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
