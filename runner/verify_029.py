"""029 5개 볼륨 전수 검증(다운로드→zip 검사) — 업로드 없음."""
from __future__ import annotations

import json
import os
import sys
import time
import zipfile

import requests

ROOT = r"C:\code\unigem"
sys.path.insert(0, os.path.join(ROOT, "runner"))
import notion_pages as npg

PAGE = json.load(open(os.path.join(ROOT, "logs", "aihub_backup2.json"), encoding="utf-8"))["pages"]["05_구매도서_029"]
TMP = os.path.join(ROOT, "cache", "verify")


def main():
    os.makedirs(TMP, exist_ok=True)
    tok = npg.token()
    res = {}
    for b in npg.children(tok, PAGE):
        if b.get("type") != "file":
            continue
        cap = "".join(x.get("plain_text", "") for x in b["file"].get("caption") or [])
        p = os.path.join(TMP, cap)
        with requests.get(b["file"]["file"]["url"], stream=True, timeout=1800) as rr, open(p, "wb") as f:
            for c in rr.iter_content(1 << 24):
                f.write(c)
        try:
            z = zipfile.ZipFile(p)
            res[cap] = {"size": os.path.getsize(p), "test": z.testzip(), "entries": len(z.namelist())}
            z.close()
        except Exception as e:
            res[cap] = {"size": os.path.getsize(p), "error": f"{type(e).__name__}: {e}"}
        print(cap, res[cap], flush=True)
        for _ in range(5):
            try:
                os.remove(p); break
            except PermissionError:
                time.sleep(3)
    json.dump(res, open(os.path.join(ROOT, "logs", "verify_029.json"), "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main()
