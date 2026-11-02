"""AI Hub 매니페스트 갱신 — 전체 15블록 목록·크기·SHA256."""
from __future__ import annotations

import json
import os
import subprocess
import sys

ROOT = r"C:\code\unigem"
sys.path.insert(0, os.path.join(ROOT, "runner"))
import notion_pages as npg
import requests

SNAP = os.path.join(ROOT, "env", "snapshots", "notion_pages.json")
J = json.load(open(os.path.join(ROOT, "logs", "aihub_backup2.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "reports", "provenance", "AIHUB_BACKUP_MANIFEST.md")
UP = os.path.join(ROOT, "runner", "notion_upload_vps.py")
PY = os.path.join(ROOT, ".venv", "Scripts", "python.exe")


def main():
    tok = npg.token()
    snap = json.load(open(SNAP, encoding="utf-8"))
    parent = None
    for b in npg.children(tok, snap["datasets"]):
        if npg.title_of(b) == "AI Hub Datasets":
            parent = b["id"]
    lines = ["# AI Hub 백업 매니페스트", "",
             f"- 백업 페이지: `AI Hub Datasets` (`{parent}`)",
             "- 데이터: AI Hub 이용약관(사용자 확인 완료, 2026-11-02)",
             "- 검증: 029 5볼륨 zip 정상, 전문분야 3분할 SHA256 원본 일치", "",
             "| 분류 페이지 | 파일 | 크기 | SHA256 |", "|---|---|---|---|"]
    for name, pid in J["pages"].items():
        for b in npg.children(tok, pid):
            if b.get("type") != "file":
                continue
            cap = "".join(x.get("plain_text", "") for x in b["file"].get("caption") or [])
            key = f"{cap}:"
            rec = next((v for k, v in J["done"].items() if k.startswith(key)), {})
            size = rec.get("size", "")
            sha = rec.get("sha256", "")
            lines.append(f"| {name} | `{cap}` | {size:,} | `{sha[:16] if sha else ''}` |" if size else
                         f"| {name} | `{cap}` |  |  |")
    lines += ["", "## 복원", "- 029·전문분야는 볼륨/파트를 이름 순으로 이어붙인 뒤 압축 해제한다.",
              "- 전문분야 특허: `cat ...part01of03.zip ...part02of03.zip ...part03of03.zip > 원본.zip`",
              "", "## 재획득", "- AI Hub 로그인 후 동일 데이터셋 재다운로드(승인 유지)."]
    open(OUT, "w", encoding="utf-8").write("\n".join(lines))

    # 기존 매니페스트 삭제 후 새로 업로드
    for b in npg.children(tok, parent):
        if b.get("type") == "file":
            cap = "".join(x.get("plain_text", "") for x in b["file"].get("caption") or [])
            if cap == "AIHUB_BACKUP_MANIFEST.md":
                requests.delete(f"https://api.notion.com/v1/blocks/{b['id']}", headers=npg.h(tok), timeout=30)
                print("deleted old manifest", b["id"][:8], flush=True)
    r = subprocess.run([PY, UP, "--file", OUT, "--parent", parent, "--name", "AIHUB_BACKUP_MANIFEST.md"],
                       capture_output=True, text=True, timeout=600)
    print("upload", r.returncode, (r.stdout + r.stderr)[-200:], flush=True)


if __name__ == "__main__":
    main()
