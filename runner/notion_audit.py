"""Notion 백업 전체 감사 — 페이지 중복, 파일 블록 중복/누락."""
from __future__ import annotations

import collections
import json
import os
import sys

ROOT = r"C:\code\unigem"
sys.path.insert(0, os.path.join(ROOT, "runner"))
import notion_pages as npg

SNAP = os.path.join(ROOT, "env", "snapshots", "notion_pages.json")
AH = os.path.join(ROOT, "logs", "aihub_backup2.json")

EXPECT = {
    "01_오류교정_71560": ["aihub_error_correction.zip"],
    "02_문서요약_097": ["aihub_docsum_text.zip"],
    "03_요약_022": ["aihub_022_summary_report.zip"],
    "04_논문_018": ["aihub_018_paper_summary.zip"],
    "05_구매도서_029": [f"029_vol0{i}.zip" for i in range(1, 6)],
    "06_전문분야": ["전문분야_vol01.zip", "전문분야_vol03.zip",
                    "전문분야_[라벨]training_특허_part01of03.zip",
                    "전문분야_[라벨]training_특허_part02of03.zip",
                    "전문분야_[라벨]training_특허_part03of03.zip"],
}


def caps(tok, pid):
    out = []
    for b in npg.children(tok, pid):
        if b.get("type") == "file":
            out.append("".join(x.get("plain_text", "") for x in b["file"].get("caption") or []))
    return out


def main():
    tok = npg.token()
    snap = json.load(open(SNAP, encoding="utf-8"))
    ah = json.load(open(AH, encoding="utf-8"))
    root = snap["unigem"]

    # 중복 페이지 제목
    titles = [npg.title_of(b) for b in npg.children(tok, root) if npg.title_of(b)]
    dup_titles = {k: v for k, v in collections.Counter(titles).items() if v > 1}
    print("root pages", titles)
    print("duplicate page titles", dup_titles)

    report = {"duplicate_page_titles": dup_titles, "pages": {}}

    # AI Hub 부모 + 6개 하위
    parent = ah["pages"].get("__parent__") or snap.get("datasets")
    ah_parent = None
    for b in npg.children(tok, snap["datasets"]):
        if npg.title_of(b) == "AI Hub Datasets":
            ah_parent = b["id"]
    for name, pid in [("AI Hub Datasets(부모)", ah_parent)] + list(ah["pages"].items()):
        if not pid:
            continue
        c = caps(tok, pid)
        dup = {k: v for k, v in collections.Counter(c).items() if v > 1}
        missing = []
        if name in EXPECT:
            missing = [x for x in EXPECT[name] if x not in c]
            extra = [x for x in c if x not in EXPECT[name]]
        else:
            extra = []
        report["pages"][name] = {"n": len(c), "dup": dup, "missing": missing, "extra": extra}
        print(name, "n", len(c), "dup", dup, "missing", missing, "extra", extra)

    # ONNX/Manifests 페이지
    for key, label in (("onnx_artifacts", "ONNX Artifacts"), ("manifests", "Manifests & Provenance")):
        pid = snap.get(key)
        if not pid:
            continue
        c = caps(tok, pid)
        dup = {k: v for k, v in collections.Counter(c).items() if v > 1}
        report["pages"][label] = {"n": len(c), "dup": dup}
        print(label, "n", len(c), "dup", dup)

    json.dump(report, open(os.path.join(ROOT, "logs", "notion_audit.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
