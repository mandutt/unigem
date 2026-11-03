"""D0-c — VPS 오디오 Q8 카나리 비교 (원격 실행)."""
from __future__ import annotations

import json
import sys

import numpy as np
import onnxruntime as ort

ROOT = "/data/home/unigem"
ONNX = ROOT + "/onnx/eg2_audio_q8_layers.onnx"


def main():
    z = np.load(ROOT + "/onnx/d0c_input.npz")
    x, m = z["input_features"], z["input_features_mask"]
    ref = np.load(ROOT + "/onnx/d0c_local.npz")
    so = ort.SessionOptions(); so.intra_op_num_threads = 4; so.log_severity_level = 3
    s = ort.InferenceSession(ONNX, so, providers=["CPUExecutionProvider"])
    outs = dict(zip([o.name for o in s.get_outputs()], s.run(None, {"input_features": x, "input_features_mask": m})))
    out = {}
    for k in ref.files:
        a, b = ref[k].reshape(-1, ref[k].shape[-1]).astype(np.float64), outs[k].reshape(-1, outs[k].shape[-1]).astype(np.float64)
        n = min(len(a), len(b))
        c = (a[:n] * b[:n]).sum(1) / np.maximum(np.linalg.norm(a[:n], axis=1) * np.linalg.norm(b[:n], axis=1), 1e-12)
        out[k] = {"n": int(n), "cos_mean": float(c.mean()), "cos_min": float(c.min()),
                  "max_abs": float(np.max(np.abs(a[:n] - b[:n])))}
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
