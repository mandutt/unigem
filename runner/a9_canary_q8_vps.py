"""A-9.1 카나리 (Q8) — VPS에서 Q8 텍스트 그래프로 20개 임베딩을 반환."""
import json

import numpy as np
import onnxruntime as ort

ROOT = "/data/home/unigem"
ONNX = f"{ROOT}/onnx/eg2_text_q8_vps.onnx"
IDS = f"{ROOT}/canary_ids.json"

so = ort.SessionOptions()
so.intra_op_num_threads = 4
so.log_severity_level = 3
sess = ort.InferenceSession(ONNX, so, providers=["CPUExecutionProvider"])
out = []
for r in json.load(open(IDS)):
    ids = np.array([r["ids"]], dtype=np.int64)
    v = sess.run(["sentence_embedding"], {
        "input_ids": ids,
        "attention_mask": np.ones_like(ids),
        "image_features": np.zeros((0, 512), np.float32),
        "video_features": np.zeros((0, 512), np.float32),
        "audio_features": np.zeros((0, 512), np.float32),
    })[0][0]
    out.append({"id": r["id"], "v": [float(x) for x in v]})
print(json.dumps({"rows": out}))
