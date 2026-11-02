"""AI Hub Notion 백업 v2 — 분류별 하위 페이지 + 4GiB 볼륨 분할.

- 기존 4개 파일은 해당 분류 하위 페이지로 재업로드 후 부모의 구 블록 삭제
- 029 구매도서(17G)·전문분야(14G)는 4GiB 이하 볼륨 zip으로 순차 업로드(완료 후 로컬 zip 삭제)
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import zipfile

ROOT = r"C:\code\unigem"
PY = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
UP = os.path.join(ROOT, "runner", "notion_upload_vps.py")
BASE = r"C:\code\dataset\ai_hub"
STAGE = os.path.join(ROOT, "cache", "aihub_backup")
JOURNAL = os.path.join(ROOT, "logs", "aihub_backup2.json")
DATASETS_PAGE = "40c1f1de-06e4-81e2-af3c-e27bd1cbd9d6"
VOL_MAX = 4 * 1024**3

sys.path.insert(0, os.path.join(ROOT, "runner"))
import notion_pages as npg  # noqa: E402

GROUPS = [
    ("01_오류교정_71560", "인터페이스(자판음성)별 고빈도 오류 교정 데이터", "aihub_error_correction.zip"),
    ("02_문서요약_097", "문서요약 텍스트", "aihub_docsum_text.zip"),
    ("03_요약_022", "요약, 기계독해를 위한 말뭉치 데이터/022.요약문 및 레포트 생성 데이터", "aihub_022_summary_report.zip"),
    ("04_논문_018", "요약, 기계독해를 위한 말뭉치 데이터/018.논문자료 요약 데이터", "aihub_018_paper_summary.zip"),
]
BULK = [
    ("05_구매도서_029", "요약, 기계독해를 위한 말뭉치 데이터/029.대규모 구매도서 기반 한국어 말뭉치 데이터", "029"),
    ("06_전문분야", "요약, 기계독해를 위한 말뭉치 데이터/전문분야 말뭉치", "전문분야"),
]


def load():
    return json.load(open(JOURNAL, encoding="utf-8")) if os.path.exists(JOURNAL) else {"done": {}, "pages": {}}


def save(j):
    json.dump(j, open(JOURNAL, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def upload(tok, path, page, name, journal):
    size = os.path.getsize(path)
    key = f"{name}:{size}"
    if key in journal["done"]:
        return True
    for attempt in (1, 2, 3):
        r = subprocess.run([PY, UP, "--file", path, "--parent", page, "--name", name],
                           capture_output=True, text=True, timeout=14400)
        out = (r.stdout + r.stderr)
        if r.returncode == 0 and "첨부 완료" in out:
            journal["done"][key] = {"size": size, "sha256": sha256(path), "page": page}
            save(journal)
            time.sleep(0.5)
            return True
        print("retry", attempt, name, r.returncode, out[-200:], flush=True)
        time.sleep(5 * attempt)
    return False


def ensure_pages(tok, journal):
    existing = {npg.title_of(b): b["id"] for b in npg.children(tok, DATASETS_PAGE) if npg.title_of(b)}
    for title, _, _ in GROUPS + BULK:
        if title in existing:
            journal["pages"][title] = existing[title]
        else:
            pid = npg.create_page(tok, DATASETS_PAGE, title)
            journal["pages"][title] = pid
            print("page", title, pid, flush=True)
            time.sleep(1)
    return journal["pages"]


def zip_files(src_root, files, out):
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for p in files:
            z.write(p, os.path.relpath(p, BASE))
    return out


def bulk_volumes(root):
    files = []
    for dp, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(dp, f)
            files.append((p, os.path.getsize(p)))
    files.sort()
    vols, cur, cursz = [], [], 0
    for p, s in files:
        if s > VOL_MAX:
            raise SystemExit(f"단일 파일이 4GiB 초과: {p} ({s})")
        if cur and cursz + s > VOL_MAX:
            vols.append(cur); cur, cursz = [], 0
        cur.append(p); cursz += s
    if cur:
        vols.append(cur)
    return vols


def main():
    os.makedirs(STAGE, exist_ok=True)
    tok = npg.token()
    j = load()
    pages = ensure_pages(tok, j)
    save(j)

    # 1) 기존 4개 재업로드 → 해당 하위 페이지
    for title, src, zname in GROUPS:
        p = os.path.join(STAGE, zname)
        if not os.path.exists(p):
            print("MISSING zip", zname, flush=True); continue
        ok = upload(tok, p, pages[title], zname, j)
        print("existing", zname, "OK" if ok else "FAIL", flush=True)

    # 2) 부모의 구 파일 블록 삭제(재업로드 성공 후)
    old = [b for b in npg.children(tok, DATASETS_PAGE) if b.get("type") == "file"]
    done_caps = {k.split(":")[0] for k in j["done"]}
    for b in old:
        cap = "".join(x.get("plain_text", "") for x in b["file"].get("caption") or [])
        if cap in done_caps or cap == "AIHUB_BACKUP_MANIFEST.md":
            import requests
            r = requests.delete(f"https://api.notion.com/v1/blocks/{b['id']}", headers=npg.h(tok), timeout=30)
            print("deleted old", cap, r.status_code, flush=True)
            time.sleep(0.4)

    # 3) 대용량 볼륨 업로드
    for title, rel, tag in BULK:
        root = os.path.join(BASE, rel)
        if not os.path.isdir(root):
            print("MISSING dir", rel, flush=True); continue
        vols = bulk_volumes(root)
        print(title, "volumes", len(vols), flush=True)
        for i, vol in enumerate(vols, 1):
            name = f"{tag}_vol{i:02d}.zip"
            out = os.path.join(STAGE, name)
            if not os.path.exists(out):
                print("zip", name, len(vol), "files", flush=True)
                zip_files(root, vol, out)
            ok = upload(tok, out, pages[title], name, j)
            print("bulk", name, "OK" if ok else "FAIL", os.path.getsize(out), flush=True)
            if ok:
                os.remove(out)  # 로컬 zip 즉시 정리

    print("DONE done=", len(j["done"]), flush=True)


if __name__ == "__main__":
    main()
