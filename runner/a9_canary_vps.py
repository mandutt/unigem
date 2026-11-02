"""A-9.1 카나리 — VPS에서 텍스트 그래프를 export하고 20개 입력의 임베딩을 반환.

사용(원격): python a9_canary_vps.py
- /data/home/unigem/onnx/eg2_text_fp32_vps.onnx 가 없으면 export_text.py 실행
- /data/home/unigem/canary_ids.json 을 읽어 pooled 임베딩을 계산해 stdout에 JSON 출력
"""
import json
import os
import subprocess
import sys

ROOT = "/data/home/unigem"
ONNX = os.path.join(ROOT, "onnx", "eg2_text_fp32_vps.onnx")
IDS = os.path.join(ROOT, "canary_ids.json")


def main():
    if not os.path.exists(ONNX):
        subprocess.run([
            os.path.join(ROOT, "venv/bin/python"), os.path.join(ROOT, "onnx/export_text.py"),
            "--ckpt", os.path.join(ROOT, "models/embeddinggemma-2-f9972ac2"),
            "--out", ONNX, "--seq", "16",
        ], check=True)

    import numpy as np
    import onnxruntime as ort

    so = ort.SessionOptions()
    so.intra_op_num_threads = 4
    so.log_severity_level = 3
    sess = ort.InferenceSession(ONNX, so, providers=["CPUExecutionProvider"])
    rows = json.load(open(IDS))
    out = []
    for r in rows:
        ids = np.array([r["ids"]], dtype=np.int64)
        v = sess.run(["sentence_embedding"], {
            "input_ids": ids,
            "attention_mask": np.ones_like(ids),
            "image_features": np.zeros((0, 512), np.float32),
            "video_features": np.zeros((0, 512), np.float32),
            "audio_features": np.zeros((0, 512), np.float32),
        })[0][0]
        out.append({"id": r["id"], "v": [float(x) for x in v]})
    print(json.dumps({"onnx": ONNX, "rows": out}))


if __name__ == "__main__":
    main()
