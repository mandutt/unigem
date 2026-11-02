"""029 볼륨 복구 — vol01 재생성·재업로드 후 5개 볼륨 전수 zip 검증."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile

import requests

ROOT = r"C:\code\unigem"
sys.path.insert(0, os.path.join(ROOT, "runner"))
import notion_pages as npg  # noqa: E402
import aihub_backup2 as B  # noqa: E402

PAGE = json.load(open(os.path.join(ROOT, "logs", "aihub_backup2.json"), encoding="utf-8"))["pages"]["05_구매도서_029"]
SRC = os.path.join(B.BASE, "요약, 기계독해를 위한 말뭉치 데이터", "029.대규모 구매도서 기반 한국어 말뭉치 데이터")
TMP = os.path.join(ROOT, "cache", "verify")


def main():
    os.makedirs(TMP, exist_ok=True)
    tok = npg.token()
    vols = B.bulk_volumes(SRC)
    print("volumes", [len(v) for v in vols], flush=True)
    out = os.path.join(B.STAGE, "029_vol01.zip")
    if not os.path.exists(out) or os.path.getsize(out) < 3000000000:
        if os.path.exists(out):
            os.remove(out)
        print("zip vol01", len(vols[0]), flush=True)
        B.zip_files(SRC, vols[0], out)
    print("size", os.path.getsize(out), flush=True)
    r = subprocess.run([B.PY, B.UP, "--file", out, "--parent", PAGE, "--name", "029_vol01.zip"],
                       capture_output=True, text=True, timeout=7200)
    print("upload", r.returncode, (r.stdout + r.stderr)[-200:], flush=True)
    # 오래된 손상 블록 삭제(가장 최근 것만 유지)
    blocks = []
    for b in npg.children(tok, PAGE):
        if b.get("type") == "file":
            cap = "".join(x.get("plain_text", "") for x in b["file"].get("caption") or [])
            if cap == "029_vol01.zip":
                blocks.append(b)
    blocks.sort(key=lambda b: b["created_time"])
    for b in blocks[:-1]:
        requests.delete(f"https://api.notion.com/v1/blocks/{b['id']}", headers=npg.h(tok), timeout=30)
        print("deleted old", b["created_time"], flush=True)
    os.remove(out)

    # 전수 검증
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
            z = zipfile.ZipFile(p); res[cap] = {"size": os.path.getsize(p), "test": z.testzip(), "entries": len(z.namelist())}
        except Exception as e:
            res[cap] = {"size": os.path.getsize(p), "error": f"{type(e).__name__}: {e}"}
        os.remove(p)
        print(cap, res[cap], flush=True)
    json.dump(res, open(os.path.join(ROOT, "logs", "verify_029.json"), "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main()
