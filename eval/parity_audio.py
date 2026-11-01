"""A3 — 오디오 타워 ONNX FP32 ↔ PyTorch FP32 수치 일치 검증.

전처리는 eg2-langidentifier의 numpy log-mel(`gemma2_np.log_mel`, read-only import)을 그대로 쓴다.
즉 이 비교는 "타워"의 parity만 본다(전처리 parity는 별도).

    .venv/Scripts/python.exe eval/parity_audio.py --mode dump
    .venv/Scripts/python.exe eval/parity_audio.py --mode compare --onnx onnx/eg2_audio_research_fp32.onnx
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time

import numpy as np
import onnxruntime as ort
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "onnx"))
sys.path.insert(0, r"C:\code\eg2-langidentifier")
from export_audio import load_audio_parts  # noqa: E402
from eg2_langid.adapters.gemma2_np import log_mel, frame_mask  # noqa: E402

CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
LAYERS = [0, 4, 8, 11]
SAMPLE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "cache", "scratch",
                      "eg2probe", "fleurs_en_us_sample.npy")


def cos(a: np.ndarray, b: np.ndarray) -> float:
    a = a.reshape(-1).astype(np.float64)
    b = b.reshape(-1).astype(np.float64)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def features(pcm: np.ndarray):
    feats = log_mel(pcm)                      # (frames, 128)
    mask = frame_mask(len(pcm), feats.shape[0])
    return torch.from_numpy(feats)[None], torch.from_numpy(mask)[None]


def make_session(path: str, threads: int = 4) -> ort.InferenceSession:
    so = ort.SessionOptions()
    so.intra_op_num_threads = threads
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(path, so, providers=["CPUExecutionProvider"])


def dump_reference(path: str) -> None:
    pcm = np.load(SAMPLE).astype(np.float32)
    f1, m1 = features(pcm)
    f2, m2 = features(pcm[: 16000 * 3])
    # padded batch: same length, second clip zero-padded
    b_t = max(f1.shape[1], f2.shape[1])
    feats = torch.zeros((2, b_t, 128))
    mask = torch.zeros((2, b_t), dtype=torch.bool)
    for i, (f, m) in enumerate(((f1, m1), (f2, m2))):
        feats[i, : f.shape[1]] = f[0]
        mask[i, : m.shape[1]] = m[0]

    print("loading torch audio tower", flush=True)
    tower, embed = load_audio_parts(CKPT)
    data = {"feats": feats.numpy(), "mask": mask.numpy()}
    caps: dict[int, torch.Tensor] = {}

    def make_hook(index: int):
        def hook(_m, _a, output):
            caps[index] = output[0] if isinstance(output, tuple) else output
        return hook

    handles = [layer.register_forward_hook(make_hook(i)) for i, layer in enumerate(tower.layers)]
    with torch.no_grad():
        single = tower(input_features=f1, attention_mask=m1)
        handles and [h.remove() for h in handles]
        soft = embed(inputs_embeds=single.last_hidden_state)
        data["single|audio_features"] = soft[0][single.attention_mask[0]].numpy()
        data["single|audio_mask"] = single.attention_mask[0].numpy()
        data["single|aud_out_proj"] = single.last_hidden_state[0].numpy()
        for i in LAYERS:
            data[f"single|aud_h_l{i:02d}"] = caps[i][0].numpy()
        batch = tower(input_features=feats, attention_mask=mask)
        bsoft = embed(inputs_embeds=batch.last_hidden_state)
        for i in range(2):
            data[f"batch{i}|aud_out_proj"] = batch.last_hidden_state[i].numpy()
            data[f"batch{i}|audio_features"] = bsoft[i][batch.attention_mask[i]].numpy()
    np.savez_compressed(path, **data)
    print("dumped", path, flush=True)
    del tower, embed
    gc.collect()


def compare(onnx_path: str, ref_path: str, threads: int) -> dict:
    ref = np.load(ref_path)
    sess = make_session(onnx_path, threads)
    names = [o.name for o in sess.get_outputs()]

    out = sess.run(None, {"input_features": ref["feats"], "input_features_mask": ref["mask"]})
    got = dict(zip(names, out))
    rows = []

    n = int(ref["single|audio_mask"].sum())
    valid = ref["single|audio_mask"].astype(bool)
    rec = {"case": "single", "tokens": n, "outputs": {}}
    for name in ("audio_features", "aud_out_proj"):
        a = got[name][:n] if name == "audio_features" else got[name][0][valid]
        b = ref[f"single|{name}"]
        rec["outputs"][name] = {"cos": cos(a, b), "max_abs": float(np.abs(a - b).max())}
    for i in LAYERS:
        name = f"aud_h_l{i:02d}"
        a = got[name][0][valid]
        # torch layer hidden not dumped (only out_proj) — compare skipped if absent
        if f"single|{name}" in ref:
            rec["outputs"][name] = {"cos": cos(a, ref[f"single|{name}"])}
    rows.append(rec)

    # padding invariance: same clip alone vs inside the padded batch
    counts = [int(m.sum()) for m in ref["mask"]]
    offsets = np.cumsum([0] + counts)
    for i in range(2):
        sing = dict(zip(names, sess.run(None, {"input_features": ref["feats"][i:i + 1],
                                              "input_features_mask": ref["mask"][i:i + 1]})))
        valid_i = ref["mask"][i].astype(bool)
        n_i = counts[i]
        rec = {"case": f"padinv:{i}", "tokens": n_i, "outputs": {}}
        for name in ("audio_features", "aud_out_proj"):
            if name == "audio_features":
                a = got[name][offsets[i]:offsets[i + 1]]
                b = sing[name][:n_i]
            else:
                a = got[name][i][valid_i]
                b = sing[name][0][valid_i]
            rec["outputs"][name] = {"cos": cos(a, b), "max_abs": float(np.abs(a - b).max())}
        rows.append(rec)

    summary = {
        "onnx": onnx_path,
        "tokens": n,
        "sin_audio_features_cos": rows[0]["outputs"]["audio_features"]["cos"],
        "sin_out_proj_cos": rows[0]["outputs"]["aud_out_proj"]["cos"],
        "audio_features_max_abs": rows[0]["outputs"]["audio_features"]["max_abs"],
        "gate": "PASS" if rows[0]["outputs"]["audio_features"]["cos"] >= 0.99
                and rows[0]["outputs"]["aud_out_proj"]["cos"] >= 0.99 else "FAIL",
    }
    return {"summary": summary, "rows": rows}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--onnx", default=os.path.join(ROOT, "onnx", "eg2_audio_research_fp32.onnx"))
    ap.add_argument("--ref", default=os.path.join(ROOT, "logs", "A3_audio_ref.npz"))
    ap.add_argument("--out", default=os.path.join(ROOT, "logs", "A3_parity_audio.json"))
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--mode", choices=["all", "dump", "compare"], default="all")
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    if args.mode in ("all", "dump"):
        dump_reference(args.ref)
    if args.mode in ("all", "compare"):
        res = compare(args.onnx, args.ref, args.threads)
        print(json.dumps(res["summary"], ensure_ascii=False, indent=2))
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
