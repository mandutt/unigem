#!/bin/bash
# Phase V1 — VPS 공통 환경 구성 (네이티브 venv, Docker 금지)
# 실행: base64로 주입 후 setsid 백그라운드. 완료 마커 /data/home/unigem/setup.done
set -e
export DEBIAN_FRONTEND=noninteractive
export PIP_DISABLE_PIP_VERSION_CHECK=1

sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv python3-pip >/dev/null

mkdir -p /data/home/unigem
cd /data/home/unigem

if [ "${FORCE_REBUILD:-0}" = "1" ]; then
  rm -rf venv
fi

if [ ! -x venv/bin/python ]; then
  python3 -m venv venv
fi
./venv/bin/pip install -q --upgrade pip wheel

# 공통 의존성 (버전은 lock으로 고정)
./venv/bin/pip install -q numpy onnx onnxruntime onnxscript transformers tokenizers \
    safetensors huggingface-hub psutil
# torch CPU wheel (CUDA 없음)
./venv/bin/pip install -q torch --index-url https://download.pytorch.org/whl/cpu

./venv/bin/python - <<'PY'
import json, platform, sys
import numpy, onnx, onnxruntime, transformers, torch
print(json.dumps({
    "python": sys.version.split()[0],
    "platform": platform.platform(),
    "numpy": numpy.__version__,
    "onnx": onnx.__version__,
    "onnxruntime": onnxruntime.__version__,
    "transformers": transformers.__version__,
    "torch": torch.__version__,
}, ensure_ascii=False))
PY

./venv/bin/pip freeze > lock_linux.txt
echo DONE > setup.done
