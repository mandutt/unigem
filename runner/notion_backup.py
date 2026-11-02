"""Notion 백업 러너 — 저널 기반 재개, 대용량 순차 업로드."""
from __future__ import annotations

import json
import os
import subprocess
import sys

ROOT = r"C:\code\unigem"
PY = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
UP = os.path.join(ROOT, "runner", "notion_upload_vps.py")
JOURNAL = os.path.join(ROOT, "logs", "notion_backup.json")

ONNX_PAGE = "40c1f1de-06e4-81a1-a780-cc064c7eae31"
MANIFEST_PAGE = "40c1f1de-06e4-8163-870e-ee18a57f35d7"

JOBS = [
    ("onnx/eg2_text_research_fp32.onnx", ONNX_PAGE, "eg2_text_research_fp32.onnx"),
    ("onnx/eg2_text_research_fp32.onnx.data", ONNX_PAGE, "eg2_text_research_fp32.onnx.data"),
    ("onnx/eg2_text_research_q8.onnx", ONNX_PAGE, "eg2_text_research_q8.onnx"),
    ("onnx/eg2_text_research_q8.onnx_data", ONNX_PAGE, "eg2_text_research_q8.onnx.data"),
    ("onnx/eg2_audio_research_fp32_t500.onnx", ONNX_PAGE, "eg2_audio_research_fp32_t500.onnx"),
    ("onnx/eg2_audio_research_fp32_t500.onnx.data", ONNX_PAGE, "eg2_audio_research_fp32_t500.onnx.data"),
    ("reports/provenance/ONNX_ARTIFACTS.md", MANIFEST_PAGE, "ONNX_ARTIFACTS.md"),
    ("reports/provenance/corpus_v2.zip", MANIFEST_PAGE, "corpus_v2.zip"),
    ("reports/provenance/docs.zip", MANIFEST_PAGE, "docs.zip"),
    ("reports/provenance/reports.zip", MANIFEST_PAGE, "reports.zip"),
]


def load():
    if os.path.exists(JOURNAL):
        return json.load(open(JOURNAL, encoding="utf-8"))
    return {"done": {}, "failed": {}}


def save(j):
    json.dump(j, open(JOURNAL, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def main():
    j = load()
    for rel, parent, name in JOBS:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            print("MISSING", rel, flush=True)
            continue
        size = os.path.getsize(p)
        key = f"{name}:{size}"
        if key in j["done"]:
            print("SKIP", name, flush=True)
            continue
        print("UPLOAD", name, size, flush=True)
        r = subprocess.run([PY, UP, "--file", p, "--parent", parent, "--name", name],
                           capture_output=True, text=True, timeout=3600)
        ok = r.returncode == 0 and "첨부 완료" in (r.stdout + r.stderr)
        rec = {"size": size, "rc": r.returncode, "out": (r.stdout + r.stderr)[-500:]}
        if ok:
            j["done"][key] = rec
            print("OK", name, flush=True)
        else:
            j["failed"][key] = rec
            print("FAIL", name, r.returncode, (r.stdout + r.stderr)[-300:], flush=True)
        save(j)
    print("DONE", len(j["done"]), "failed", len(j["failed"]), flush=True)


if __name__ == "__main__":
    main()
