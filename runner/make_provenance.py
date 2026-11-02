"""산출물 provenance 생성 — 크기·SHA256·재생성 명령."""
from __future__ import annotations

import hashlib
import json
import os

ROOT = r"C:\code\unigem"
OUT = os.path.join(ROOT, "reports", "provenance")
os.makedirs(OUT, exist_ok=True)

FILES = {
    "eg2_text_research_fp32.onnx": {
        "path": "onnx/eg2_text_research_fp32.onnx",
        "origin": "PyTorch dynamo export (opset 21), 9 outputs",
        "regen": ".venv/Scripts/python.exe onnx/export_text.py --out onnx/eg2_text_research_fp32.onnx --seq 16",
    },
    "eg2_text_research_fp32.onnx.data": {
        "path": "onnx/eg2_text_research_fp32.onnx.data",
        "origin": "external data of eg2_text_research_fp32.onnx",
        "regen": "same as eg2_text_research_fp32.onnx",
    },
    "eg2_text_research_q8.onnx": {
        "path": "onnx/eg2_text_research_q8.onnx",
        "origin": "MatMulNBits 8bit/block128/acc4 quantization of research FP32",
        "regen": ".venv/Scripts/python.exe onnx/quantize_q8.py --input onnx/eg2_text_research_fp32.onnx --output onnx/eg2_text_research_q8.onnx",
    },
    "eg2_text_research_q8.onnx.data": {
        "path": "onnx/eg2_text_research_q8.onnx_data",
        "origin": "external data of eg2_text_research_q8.onnx",
        "regen": "same as eg2_text_research_q8.onnx",
    },
    "eg2_audio_research_fp32_t500.onnx": {
        "path": "onnx/eg2_audio_research_fp32_t500.onnx",
        "origin": "PyTorch dynamo export static/optimize=False, T=500",
        "regen": ".venv/Scripts/python.exe onnx/export_audio.py --mel 500 --static --out onnx/eg2_audio_research_fp32_t500.onnx",
    },
    "eg2_audio_research_fp32_t500.onnx.data": {
        "path": "onnx/eg2_audio_research_fp32_t500.onnx.data",
        "origin": "external data of audio t500",
        "regen": "same as eg2_audio_research_fp32_t500.onnx",
    },
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


rows = []
for name, meta in FILES.items():
    p = os.path.join(ROOT, meta["path"])
    if not os.path.exists(p):
        rows.append({"name": name, "missing": True, "path": meta["path"]})
        continue
    rows.append({"name": name, "path": meta["path"], "size": os.path.getsize(p),
                 "sha256": sha256(p), "origin": meta["origin"], "regen": meta["regen"]})

md = ["# ONNX 산출물 Provenance", "",
      "- 체크포인트: `google/embeddinggemma-2` rev `f9972ac2e696a105c482202646979e33e4b5a1e`",
      "- `model.safetensors` SHA256 `197a32965d4b1105faf060417baa899e193fb73cd401f42ec9295234d5553d79`",
      "- 런타임: onnxruntime 1.31.1 CPU EP, Python 3.12", "",
      "| 파일 | 크기 | SHA256 | 재생성 |", "|---|---|---|---|"]
for r in rows:
    if r.get("missing"):
        md.append(f"| {r['name']} | 없음 | — | {r['path']} |")
    else:
        md.append(f"| {r['name']} | {r['size']:,} | `{r['sha256'][:16]}…` | `{r['regen']}` |")
md += ["", "## 전체 SHA256", ""]
for r in rows:
    if not r.get("missing"):
        md.append(f"- `{r['name']}`: `{r['sha256']}`")

open(os.path.join(OUT, "ONNX_ARTIFACTS.md"), "w", encoding="utf-8").write("\n".join(md))
json.dump(rows, open(os.path.join(OUT, "onnx_artifacts.json"), "w", encoding="utf-8"), indent=2)
print("\n".join(md[:12]))
