"""AI Hub 데이터셋 Notion 백업 — 선별 업로드 + 인벤토리.

업로드: 오류교정(45M), 문서요약(402M), 022 요약문·레포트(473M), 018 논문(1.7G)
제외: 029 구매도서(17G), 전문분야(14G) — 인벤토리·재획득 절차만 기록
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import zipfile

ROOT = r"C:\code\unigem"
PY = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
UP = os.path.join(ROOT, "runner", "notion_upload_vps.py")
BASE = r"C:\code\dataset\ai_hub"
STAGE = os.path.join(ROOT, "cache", "aihub_backup")
JOURNAL = os.path.join(ROOT, "logs", "aihub_backup.json")
DATASETS_PAGE = "40c1f1de-06e4-81e2-af3c-e27bd1cbd9d6"

sys.path.insert(0, os.path.join(ROOT, "runner"))
import notion_pages as npg  # noqa: E402

JOBS = [
    ("인터페이스(자판음성)별 고빈도 오류 교정 데이터",
     "aihub_error_correction.zip", "AI Hub 71560 인터페이스별 고빈도 오류 교정"),
    ("문서요약 텍스트",
     "aihub_docsum_text.zip", "AI Hub 097 문서요약 텍스트"),
    ("요약, 기계독해를 위한 말뭉치 데이터/022.요약문 및 레포트 생성 데이터",
     "aihub_022_summary_report.zip", "AI Hub 022 요약문·레포트 생성"),
    ("요약, 기계독해를 위한 말뭉치 데이터/018.논문자료 요약 데이터",
     "aihub_018_paper_summary.zip", "AI Hub 018 논문자료 요약"),
]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def make_zip(src, out):
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return out
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for dirpath, _, files in os.walk(src):
            for fn in files:
                p = os.path.join(dirpath, fn)
                z.write(p, os.path.relpath(p, BASE))
    return out


def inventory():
    lines = ["# AI Hub 인벤토리", "", "| 경로 | 파일 수 | 바이트 |", "|---|---|---|"]
    for dirpath, _, files in os.walk(BASE):
        if not files:
            continue
        size = sum(os.path.getsize(os.path.join(dirpath, f)) for f in files)
        lines.append(f"| `{os.path.relpath(dirpath, BASE)}` | {len(files)} | {size:,} |")
    return "\n".join(lines) + "\n"


def main():
    os.makedirs(STAGE, exist_ok=True)
    tok = npg.token()
    snap = json.load(open(r"C:\code\unigem\env\snapshots\notion_pages.json", encoding="utf-8"))
    existing = {npg.title_of(b): b["id"] for b in npg.children(tok, DATASETS_PAGE) if npg.title_of(b)}
    if "AI Hub Datasets" in existing:
        page = existing["AI Hub Datasets"]
    else:
        page = npg.create_page(tok, DATASETS_PAGE, "AI Hub Datasets")
    print("page", page, flush=True)

    j = json.load(open(JOURNAL, encoding="utf-8")) if os.path.exists(JOURNAL) else {"done": {}}
    records = []
    for src, zname, caption in JOBS:
        srcp = os.path.join(BASE, src)
        if not os.path.isdir(srcp):
            print("MISSING", srcp, flush=True)
            continue
        out = os.path.join(STAGE, zname)
        print("zip", zname, flush=True)
        make_zip(srcp, out)
        size = os.path.getsize(out)
        digest = sha256(out)
        key = f"{zname}:{size}"
        if key not in j["done"]:
            print("upload", zname, size, flush=True)
            r = subprocess.run([PY, UP, "--file", out, "--parent", page, "--name", zname],
                               capture_output=True, text=True, timeout=7200)
            ok = r.returncode == 0 and "첨부 완료" in (r.stdout + r.stderr)
            print(("OK " if ok else "FAIL ") + zname, (r.stdout + r.stderr)[-200:], flush=True)
            if not ok:
                continue
            j["done"][key] = {"sha256": digest, "size": size}
            json.dump(j, open(JOURNAL, "w", encoding="utf-8"), indent=2)
        records.append({"file": zname, "caption": caption, "size": size, "sha256": digest})

    manifest = ["# AI Hub 백업 매니페스트", "",
                f"- 백업 페이지: `{page}`",
                f"- 업로드 {len(records)}건 / 제외: 029 구매도서(17G), 전문분야(14G), 기타 소형",
                "", "| 파일 | 원본 | 바이트 | SHA256 |", "|---|---|---|---|"]
    for r in records:
        manifest.append(f"| `{r['file']}` | {r['caption']} | {r['size']:,} | `{r['sha256']}` |")
    manifest.append("")
    manifest.append(inventory())
    mp = os.path.join(STAGE, "AIHUB_BACKUP_MANIFEST.md")
    open(mp, "w", encoding="utf-8").write("\n".join(manifest))
    subprocess.run([PY, UP, "--file", mp, "--parent", page, "--name", "AIHUB_BACKUP_MANIFEST.md"],
                   capture_output=True, text=True, timeout=1200)
    print("manifest uploaded", mp, flush=True)

    # 감사: 페이지 캡션 대조
    caps = []
    for b in npg.children(tok, page):
        if b.get("type") == "file":
            cap = b["file"].get("caption") or []
            caps.append("".join(x.get("plain_text", "") for x in cap))
    want = [r["file"] for r in records] + ["AIHUB_BACKUP_MANIFEST.md"]
    print("AUDIT want", len(want), "have", len(caps), "missing", [w for w in want if w not in caps], flush=True)
    json.dump({"page": page, "caps": caps}, open(os.path.join(ROOT, "env", "snapshots", "aihub_page.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
