"""Notion 백업 무결성 검증 — 029_vol01 zip, 전문분야 분할 3파트 해시."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile

import requests

ROOT = r"C:\code\unigem"
sys.path.insert(0, os.path.join(ROOT, "runner"))
import notion_pages as npg  # noqa: E402

TMP = os.path.join(ROOT, "cache", "verify")
J = json.load(open(os.path.join(ROOT, "logs", "aihub_backup2.json"), encoding="utf-8"))
PAGES = J["pages"]
SRC = os.path.join(r"C:\code\dataset\ai_hub", "요약, 기계독해를 위한 말뭉치 데이터", "전문분야 말뭉치",
                   "Training", "[라벨]training_특허.zip")


def blocks(tok, pid):
    out = []
    for b in npg.children(tok, pid):
        if b.get("type") == "file":
            cap = "".join(x.get("plain_text", "") for x in b["file"].get("caption") or [])
            out.append((cap, b["file"]["file"]["url"]))
    return out


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 24), b""):
            h.update(c)
    return h.hexdigest()


def main():
    os.makedirs(TMP, exist_ok=True)
    tok = npg.token()
    res = {}
    # 1) 029_vol01
    for cap, url in blocks(tok, PAGES["05_구매도서_029"]):
        r = requests.head(url, timeout=60)
        size = int(r.headers.get("Content-Length", 0))
        res[cap] = {"head_size": size}
        if cap == "029_vol01.zip":
            p = os.path.join(TMP, cap)
            with requests.get(url, stream=True, timeout=300) as rr, open(p, "wb") as f:
                for c in rr.iter_content(1 << 24):
                    f.write(c)
            res[cap]["down_size"] = os.path.getsize(p)
            res[cap]["sha256"] = sha_file(p)
            try:
                z = zipfile.ZipFile(p)
                res[cap]["zip_test"] = z.testzip()
                res[cap]["entries"] = len(z.namelist())
            except Exception as e:
                res[cap]["zip_error"] = f"{type(e).__name__}: {e}"
            os.remove(p)
    # 2) 전문분야 parts
    parts = sorted([(c, u) for c, u in blocks(tok, PAGES["06_전문분야"]) if "part" in c])
    h = hashlib.sha256(); total = 0
    for cap, url in parts:
        p = os.path.join(TMP, cap)
        with requests.get(url, stream=True, timeout=600) as rr, open(p, "wb") as f:
            for c in rr.iter_content(1 << 24):
                f.write(c); h.update(c)
        n = os.path.getsize(p); total += n
        res[cap] = {"size": n}
        os.remove(p)
    res["parts_concat_sha256"] = h.hexdigest()
    res["parts_total"] = total
    if os.path.exists(SRC):
        res["source_size"] = os.path.getsize(SRC)
        res["source_sha256"] = sha_file(SRC)
        res["match"] = (res["source_sha256"] == res["parts_concat_sha256"] and res["source_size"] == total)
    json.dump(res, open(os.path.join(ROOT, "logs", "notion_verify.json"), "w", encoding="utf-8"), indent=2)
    print(json.dumps(res, ensure_ascii=False, indent=1), flush=True)


if __name__ == "__main__":
    main()
