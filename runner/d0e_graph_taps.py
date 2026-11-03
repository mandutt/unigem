"""D0-e — A2 Q8 다중 출력 그래프의 hidden parity 및 탭 확인.

- FP32 연구 그래프(t1600_l12)와 Q8 운영 그래프를 같은 입력으로 실행
- 6/8/10/11층 hidden cosine 최소/p1/p5, 최대 절대 오차
- audio_features(512d) / aud_out_proj(1536d)도 비교
- 운영 LID 그래프의 출력(탭) 목록 확인
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np
import onnx
import onnxruntime as ort
from safetensors import safe_open

ROOT = r"C:\code\unigem"
sys.path.insert(0, r"C:\code\eg2-langidentifier")
from eg2_langid.adapters.gemma2_np import frame_mask, log_mel  # noqa: E402

FP32 = os.path.join(ROOT, "onnx", "eg2_audio_research_fp32_t1600_l12.onnx")
Q8 = os.path.join(ROOT, "onnx", "eg2_audio_q8_layers.onnx")
FLEURS = os.path.join(ROOT, "data", "c2a1", "audio", "fleurs")
OUT = os.path.join(ROOT, "logs", "D0e_graph_taps.json")
T = 1600
LAYERS = ["aud_h_l06", "aud_h_l08", "aud_h_l10", "aud_h_l11"]


def prep(wav):
    import soundfile as sf

    x, sr = sf.read(wav, dtype="float32")
    assert sr == 16000
    n = len(x)
    longest = -(-n // 128) * 128
    xp = np.pad(x, (0, longest - n)) if longest > n else x
    feats = log_mel(xp)[None]
    fmask = frame_mask(n, feats.shape[1], total=longest)[None]
    # static t1600: crop/pad
    if feats.shape[1] > T:
        feats, fmask = feats[:, :T], fmask[:, :T]
    elif feats.shape[1] < T:
        pad = T - feats.shape[1]
        feats = np.pad(feats, ((0, 0), (0, pad), (0, 0)))
        fmask = np.pad(fmask, ((0, 0), (0, pad)))
    return feats.astype(np.float32), fmask.astype(bool)


def cos_rows(a, b):
    a = a.reshape(-1, a.shape[-1]).astype(np.float64)
    b = b.reshape(-1, b.shape[-1]).astype(np.float64)
    num = (a * b).sum(1)
    den = np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1)
    return num / np.maximum(den, 1e-12)


def stats(v):
    v = np.asarray(v, np.float64)
    return {
        "n": int(v.size),
        "mean": float(v.mean()),
        "min": float(v.min()),
        "p1": float(np.percentile(v, 1)),
        "p5": float(np.percentile(v, 5)),
        "max": float(v.max()),
        "lt_0_98": float((v < 0.98).mean()),
    }


def main():
    so = ort.SessionOptions()
    so.intra_op_num_threads = 6
    fp = ort.InferenceSession(FP32, so, providers=["CPUExecutionProvider"])
    q8 = ort.InferenceSession(Q8, so, providers=["CPUExecutionProvider"])
    files = sorted(glob.glob(os.path.join(FLEURS, "*.wav")))[:20]
    per_layer = {k: [] for k in LAYERS}
    final512, final1536, final256, maxabs = [], [], [], {k: [] for k in LAYERS}
    with safe_open(os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2", "model.safetensors"), framework="pt", device="cpu") as f:
        proj = f.get_tensor("embed_audio.embedding_projection.weight")[:256].float().numpy()
    used = []
    for w in files:
        f, mk = prep(w)
        a = fp.run(None, {"input_features": f, "input_features_mask": mk})
        b = q8.run(None, {"input_features": f, "input_features_mask": mk})
        da = {o.name: v for o, v in zip(fp.get_outputs(), a)}
        db = {o.name: v for o, v in zip(q8.get_outputs(), b)}
        # Q8 audio_features is flattened over valid frames; hidden tensors keep
        # the padded time axis. Restrict every comparison to valid frames.
        n_valid = int(db["audio_features"].shape[0])
        for k in LAYERS:
            ca = cos_rows(da[k][:, :n_valid], db[k][:, :n_valid])
            per_layer[k].extend(ca.tolist())
            maxabs[k].append(float(np.max(np.abs(da[k][:, :n_valid] - db[k][:, :n_valid]))))
        fa = da["audio_soft_tokens"].reshape(-1, 512)[:n_valid]
        fb = db["audio_features"].reshape(-1, 512)[:n_valid]
        final512.extend(cos_rows(fa, fb).tolist())
        # 1536 projection
        pa = da["aud_out_proj"].reshape(-1, 1536)[:n_valid]
        pb = db["aud_out_proj"].reshape(-1, 1536)[:n_valid]
        final1536.extend(cos_rows(pa, pb).tolist())
        qa, qb = pa @ proj.T, pb @ proj.T
        qa /= np.maximum(np.linalg.norm(qa, axis=1, keepdims=True), 1e-12)
        qb /= np.maximum(np.linalg.norm(qb, axis=1, keepdims=True), 1e-12)
        final256.extend(cos_rows(qa, qb).tolist())
        used.append(os.path.basename(w))
    out = {
        "clips": len(files),
        "T": T,
        "layers": {k: {"cos": stats(per_layer[k]), "max_abs": max(maxabs[k])} for k in LAYERS},
        "final512": stats(final512),
        "final1536": stats(final1536),
        "final256": stats(final256),
        "files": used,
    }
    # operating graph outputs
    tap_path = os.path.join(ROOT, "onnx", "tap", "audio_encoder_q8_tap.onnx")
    if os.path.exists(tap_path):
        m = onnx.load(tap_path, load_external_data=False)
        out["operating_tap_outputs"] = [o.name for o in m.graph.output]
    else:
        out["operating_tap_outputs"] = None
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
