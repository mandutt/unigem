"""InstaBox 계정 B API 최소 클라이언트 (Phase V 러너용).

키는 ~/.instabox-b.env 첫 줄에서만 읽고 절대 출력하지 않는다.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

API = "https://api.instabox.sh"
KEY_FILE = os.path.expanduser("~/.instabox-b.env")


def api_key() -> str:
    with open(KEY_FILE, "r", encoding="utf-8") as f:
        return f.readline().strip()


def _req(method: str, path: str, body=None, idem: str | None = None, timeout: int = 60):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("X-API-Key", api_key())
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if idem:
        req.add_header("Idempotency-Key", idem)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def list_machines():
    status, body = _req("GET", "/v1/machines")
    if status != 200:
        raise RuntimeError(f"list_machines failed: {status} {body}")
    return body.get("machines", body if isinstance(body, list) else [])


def get_machine(mid: str):
    status, body = _req("GET", f"/v1/machines/{mid}")
    if status != 200:
        raise RuntimeError(f"get_machine {mid} failed: {status} {body}")
    return body


def start(mid: str, idem: str | None = None):
    return _req("POST", f"/v1/machines/{mid}/start", body=None,
                idem=idem or f"start-{mid}-{int(time.time())}")


def exec_cmd(mid: str, cmd: str, timeout_s: int = 120, stdin: str | None = None):
    body = {"cmd": cmd, "timeoutSeconds": timeout_s}
    if stdin is not None:
        body["stdin"] = stdin
    status, resp = _req("POST", f"/v1/machines/{mid}/exec", body=body, timeout=timeout_s + 30)
    return status, resp


def wait_state(mid: str, want: str = "running", timeout_s: int = 300, poll_s: int = 5):
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        m = get_machine(mid)
        last = m.get("state")
        if last == want:
            return True, last
        time.sleep(poll_s)
    return False, last
