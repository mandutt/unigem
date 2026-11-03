"""D0-c — 오디오 Q8 카나리 입력/로컬 기준 출력 생성."""
from __future__ import annotations

import json
import os

import numpy as np
import onnxruntime as ort

ROOT = r"C:\code\unigem"
ONNX = os.path.join(ROOT, "onnx", "eg2_audio_q8_layers.onnx")
OUT = os.path.join(ROOT, "cache", "d0c_canary")
T = 1600


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(12345)
    x = rng.normal(size=(1, T, 128)).astype(np.float32)
    m = np.ones((1, T), np.bool_)
    np.savez_compressed(os.path.join(OUT, "input.npz"), input_features=x, input_features_mask=m)
    so = ort.SessionOptions(); so.intra_op_num_threads = 6; so.log_severity_level = 3
    s = ort.InferenceSession(ONNX, so, providers=["CPUExecutionProvider"])
    outs = dict(zip([o.name for o in s.get_outputs()], s.run(None, {"input_features": x, "input_features_mask": m})))
    keep = {k: outs[k] for k in ["audio_features", "aud_h_l06", "aud_h_l08", "aud_h_l10", "aud_h_l11", "aud_out_proj"]}
    np.savez_compressed(os.path.join(OUT, "local.npz"), **keep)
    print("saved", OUT, {k: v.shape for k, v in keep.items()})


if __name__ == "__main__":
    main()
