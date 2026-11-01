#!/usr/bin/env python3
"""Notion 페이지에서 파일 블록을 회수한다 (로컬/VPS 공용, requests만 필요).

서명 URL은 만료되므로 **매 실행마다 children을 다시 조회**한다.
다운로드 후 sha256을 출력하며, 기대값을 주면 검증한다.

사용:
  NOTION_TOKEN=... python3 notion_download.py --page <page_id> --name eg2_audio_research_fp32.onnx --out onnx/
  ... --sha256 <expected>
"""
import argparse
import hashlib
import os
import re
import time

import requests

VER = "2026-03-11"
API = "https://api.notion.com/v1"


def load_token(explicit=None):
    if explicit:
        return explicit
    if os.environ.get("NOTION_TOKEN"):
        return os.environ["NOTION_TOKEN"]
    for p in ("/data/home/unigem/notiondrive.toml", os.path.expanduser("~/.notiondrive.toml")):
        if os.path.exists(p):
            m = re.search(r'token\s*=\s*"([^"]+)"', open(p, encoding="utf-8").read())
            if m:
                return m.group(1)
    raise SystemExit("Notion 토큰 없음")


def req(method, path, tok, **kw):
    h = {"Authorization": f"Bearer {tok}", "Notion-Version": VER}
    h.update(kw.pop("headers", {}))
    for attempt in range(6):
        r = requests.request(method, f"{API}{path}", headers=h, timeout=300, **kw)
        if r.status_code == 429 or 500 <= r.status_code < 600:
            time.sleep(int(r.headers.get("Retry-After") or min(2 ** attempt, 30)))
            continue
        return r
    return r


def list_children(tok, page):
    out, cursor = [], None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        r = req("GET", f"/blocks/{page}/children", tok, params=params)
        if r.status_code >= 300:
            raise SystemExit(f"children 실패: {r.status_code} {r.text[:200]}")
        d = r.json()
        out += d.get("results", [])
        if not d.get("has_more"):
            return out
        cursor = d.get("next_cursor")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", required=True)
    ap.add_argument("--name", required=True, help="캡션(표시명)과 일치하는 파일 블록")
    ap.add_argument("--out", required=True, help="저장 디렉터리")
    ap.add_argument("--token")
    ap.add_argument("--sha256", default="")
    a = ap.parse_args()
    tok = load_token(a.token)

    blocks = list_children(tok, a.page)
    hit = None
    for b in blocks:
        if b.get("type") != "file":
            continue
        cap = "".join(x.get("plain_text", "") for x in (b["file"].get("caption") or []))
        if cap == a.name or b["file"].get("name") == a.name:
            hit = b
            break
    if hit is None:
        print("찾은 파일 블록:")
        for b in blocks:
            if b.get("type") == "file":
                cap = "".join(x.get("plain_text", "") for x in (b["file"].get("caption") or []))
                print(" -", cap or b["file"].get("name"))
        raise SystemExit(f"'{a.name}' 블록 없음")

    url = hit["file"]["file"]["url"]
    os.makedirs(a.out, exist_ok=True)
    dest = os.path.join(a.out, a.name)
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                if chunk:
                    f.write(chunk)
    h = hashlib.sha256()
    with open(dest, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    digest = h.hexdigest()
    print(f"저장 {dest} {os.path.getsize(dest)} bytes")
    print("sha256", digest)
    if a.sha256 and digest != a.sha256:
        raise SystemExit("sha256 불일치")


if __name__ == "__main__":
    main()
