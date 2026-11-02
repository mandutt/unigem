"""Notion 프로젝트 페이지 관리 — unigem 하위 페이지 생성/조회."""
from __future__ import annotations

import json
import os
import re

import requests

VER = "2026-03-11"
SNAP = r"C:\code\unigem\env\snapshots\notion_pages.json"
TOKEN_PATHS = [
    os.path.expanduser("~/.notiondrive.toml"),
    r"C:\code\pimade\notiondrive\notiondrive.toml",
    "/data/home/unigem/notiondrive.toml",
]


def token():
    if os.environ.get("NOTION_TOKEN"):
        return os.environ["NOTION_TOKEN"]
    for p in TOKEN_PATHS:
        if os.path.exists(p):
            m = re.search(r'token\s*=\s*"([^"]+)"', open(p, encoding="utf-8").read())
            if m:
                return m.group(1)
    raise SystemExit("Notion 토큰 없음")


def h(tok):
    return {"Authorization": f"Bearer {tok}", "Notion-Version": VER, "Content-Type": "application/json"}


def children(tok, pid):
    out, cursor = [], None
    while True:
        p = {"page_size": 100}
        if cursor:
            p["start_cursor"] = cursor
        r = requests.get(f"https://api.notion.com/v1/blocks/{pid}/children", headers=h(tok), params=p, timeout=30)
        r.raise_for_status()
        d = r.json()
        out += d["results"]
        if not d.get("has_more"):
            return out
        cursor = d["next_cursor"]


def title_of(block):
    t = block.get("type")
    if t == "child_page":
        return block["child_page"]["title"]
    return None


def create_page(tok, parent, title):
    r = requests.post("https://api.notion.com/v1/pages", headers=h(tok), timeout=30,
                      json={"parent": {"page_id": parent},
                            "properties": {"title": {"title": [{"text": {"content": title}}]}}})
    r.raise_for_status()
    return r.json()["id"]


def main():
    tok = token()
    snap = json.load(open(SNAP, encoding="utf-8"))
    root = snap["unigem"]
    existing = {title_of(b): b["id"] for b in children(tok, root) if title_of(b)}
    print("existing:", existing)

    wanted = ["Datasets", "ONNX Artifacts", "Manifests & Provenance"]
    for w in wanted:
        if w in existing:
            print("skip", w, existing[w])
            continue
        pid = create_page(tok, root, w)
        existing[w] = pid
        print("created", w, pid)

    snap["datasets"] = existing.get("Datasets")
    snap["onnx_artifacts"] = existing.get("ONNX Artifacts")
    snap["manifests"] = existing.get("Manifests & Provenance")
    json.dump(snap, open(SNAP, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(snap, indent=2))


if __name__ == "__main__":
    main()
