#!/usr/bin/env python3
"""Notion 대용량 파일 업로더 (VPS/Linux용, requests만 필요).

프로토콜: create → (멀티파트) send ×N → complete → PATCH blocks children.
함정: .npz/.bin은 확장자 거부 → .zip + application/zip 폴백(내용 바이트 불변, 캡션은 원본명).

사용:
  NOTION_TOKEN=... python3 notion_upload_vps.py --parent <page_id> --file <path> [--name 표시명]
  (토큰은 /data/home/unigem/notiondrive.toml, ~/.notiondrive.toml 에서도 읽는다)
"""
import argparse
import os
import re
import time

import requests

VER = "2026-03-11"
API = "https://api.notion.com/v1"
PART_SIZE = 20 * 1024 * 1024
SINGLE_MAX = 20 * 1024 * 1024


def load_token(explicit=None):
    if explicit:
        return explicit
    if os.environ.get("NOTION_TOKEN"):
        return os.environ["NOTION_TOKEN"]
    for p in ("/data/home/unigem/notiondrive.toml",
              os.path.expanduser("~/.notiondrive.toml"),
              r"C:\code\pimade\notiondrive\notiondrive.toml"):
        if os.path.exists(p):
            m = re.search(r'token\s*=\s*"([^"]+)"', open(p, encoding="utf-8").read())
            if m:
                return m.group(1)
    raise SystemExit("Notion 토큰 없음")


def req(method, path, tok, **kw):
    h = {"Authorization": f"Bearer {tok}", "Notion-Version": VER}
    h.update(kw.pop("headers", {}))
    r = None
    for attempt in range(6):
        r = requests.request(method, f"{API}{path}", headers=h, timeout=300, **kw)
        if r.status_code == 429 or 500 <= r.status_code < 600:
            wait = int(r.headers.get("Retry-After") or min(2 ** attempt, 30))
            print(f"    HTTP {r.status_code} — {wait}s 후 재시도", flush=True)
            time.sleep(wait)
            continue
        return r
    return r


def create_upload(tok, filename, content_type, n_parts=None):
    body = {"mode": "multi_part" if n_parts else "single_part",
            "filename": filename, "content_type": content_type}
    if n_parts:
        body["number_of_parts"] = n_parts
    r = req("POST", "/file_uploads", tok, json=body)
    if r.status_code >= 300:
        return None, r
    return r.json()["id"], r


def upload(path, parent, name, tok):
    size = os.path.getsize(path)
    fn = name or os.path.basename(path)
    display = fn
    used_ct = "application/octet-stream"
    n_parts = 0 if size <= SINGLE_MAX else (size + PART_SIZE - 1) // PART_SIZE

    uid, r = create_upload(tok, fn, used_ct, n_parts or None)
    if uid is None:
        print(f"  ⚠ 확장자 거부({r.status_code}) → .zip 폴백", flush=True)
        fn = fn + ".zip"
        used_ct = "application/zip"
        uid, r = create_upload(tok, fn, used_ct, n_parts or None)
        if uid is None:
            raise SystemExit(f"생성 실패: {r.status_code} {r.text[:200]}")

    with open(path, "rb") as f:
        if n_parts:
            for i in range(1, n_parts + 1):
                chunk = f.read(PART_SIZE)
                rr = req("POST", f"/file_uploads/{uid}/send", tok,
                         data={"part_number": str(i)},
                         files={"file": (fn, chunk, used_ct)})
                if rr.status_code >= 300:
                    raise SystemExit(f"파트 {i}/{n_parts} 실패: {rr.status_code} {rr.text[:200]}")
                print(f"    part {i}/{n_parts} ({len(chunk)//1024}KB)", flush=True)
            rr = req("POST", f"/file_uploads/{uid}/complete", tok, json={})
            if rr.status_code >= 300:
                raise SystemExit(f"complete 실패: {rr.status_code} {rr.text[:200]}")
        else:
            rr = req("POST", f"/file_uploads/{uid}/send", tok,
                     files={"file": (fn, f.read(), used_ct)})
            if rr.status_code >= 300:
                raise SystemExit(f"전송 실패: {rr.status_code} {rr.text[:200]}")

    attach = {"children": [{"object": "block", "type": "file",
                            "file": {"type": "file_upload",
                                     "file_upload": {"id": uid},
                                     "caption": [{"text": {"content": display}}]}}]}
    ra = req("PATCH", f"/blocks/{parent}/children", tok, json=attach)
    if ra.status_code >= 300:
        raise SystemExit(f"첨부 실패: {ra.status_code} {ra.text[:200]}")
    print(f"첨부 완료: {display} (저장명 {fn}, {size/1e6:.1f}MB, upload_id={uid})", flush=True)
    return uid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--name")
    ap.add_argument("--token")
    a = ap.parse_args()
    upload(a.file, a.parent, a.name, load_token(a.token))


if __name__ == "__main__":
    main()
