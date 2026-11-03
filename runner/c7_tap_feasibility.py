"""C-7 — 운영 LID 그래프에 중간 텐서 탭 추가 가능성 확인(복사본)."""
from __future__ import annotations

import glob
import json
import os
import shutil

import numpy as np
import onnx
import onnxruntime as ort

SRC = r"C:\code\eg2-langidentifier\scripts\mmal4\audio_encoder_quantized_al4.onnx"
OUTDIR = r"C:\code\unigem\onnx\tap"
DST = os.path.join(OUTDIR, "audio_encoder_q8_tap.onnx")
FLEURS = r"C:\code\unigem\data\c2a1\audio\fleurs"
OUT = r"C:\code\unigem\logs\C7_tap.json"

TAPS = ["add_8945", "linear_134", "type_as_108"]


def build():
    os.makedirs(OUTDIR, exist_ok=True)
    shutil.copy2(SRC, DST)
    for suf in (".data", "_data"):
        data = SRC + suf
        if os.path.exists(data):
            shutil.copy2(data, os.path.join(OUTDIR, os.path.basename(SRC) + suf))
    m = onnx.load(DST)  # external data 로드
    have = {o.name for o in m.graph.output}
    for t in TAPS:
        if t in have:
            continue
        vi = next((v for v in m.graph.value_info if v.name == t), None)
        if vi is None:
            # shape 추론값이 없으면 타입만 복사
            src = next((v for v in m.graph.value_info if v.name == "audio_features"), None)
            vi = onnx.helper.ValueInfoProto()
            vi.name = t
            if src is not None:
                vi.type.CopyFrom(src.type)
        m.graph.output.append(vi)
    onnx.save(m, DST)
    return m


def preprocess(wav):
    import soundfile as sf
    import sys
    sys.path.insert(0, r"C:\code\eg2-langidentifier")
    from eg2_langid.adapters.gemma2_np import log_mel, frame_mask
    x, sr = sf.read(wav, dtype="float32")
    assert sr == 16000
    n = len(x); longest = -(-n // 128) * 128
    xp = np.pad(x, (0, longest - n)) if longest > n else x
    feats = log_mel(xp)[None]
    fmask = frame_mask(n, feats.shape[1], total=longest)[None]
    return feats, fmask


def main():
    m = build()
    print("outputs", [o.name for o in m.graph.output], flush=True)
    so = ort.SessionOptions(); so.intra_op_num_threads = 6
    orig = ort.InferenceSession(SRC, sess_options=so, providers=["CPUExecutionProvider"])
    tap = ort.InferenceSession(DST, sess_options=so, providers=["CPUExecutionProvider"])
    files = sorted(glob.glob(os.path.join(FLEURS, "*.wav")))[:220]
    diffs = []; tap_stats = []
    for i, w in enumerate(files, 1):
        f, mk = preprocess(w)
        a = orig.run(["audio_features"], {"input_features": f, "input_features_mask": mk})[0]
        outs = tap.run(None, {"input_features": f, "input_features_mask": mk})
        b = outs[0]
        diffs.append(float(np.max(np.abs(a - b))))
        tap_stats.append([o.shape for o in outs[1:]])
        if i % 50 == 0:
            print(i, "/", len(files), "maxdiff", max(diffs), flush=True)
    res = {"clips": len(files), "max_abs_diff": max(diffs),
           "clips_over_1e6": sum(1 for d in diffs if d > 1e-6),
           "tap_shapes_sample": tap_stats[0], "taps": TAPS}
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
