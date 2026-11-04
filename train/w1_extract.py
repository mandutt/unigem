"""D-β Wave 1 특징 추출 — F-D / F-A′ / F-B / F-C.

입력: data/wave1/manifest.jsonl (16kHz wav, 한 클립 = 한 발화)
출력: data/wave1/feats/{fd,fa,fb,fc}.npz + vocab.json

특징:
  F-D  audio_features [T,512] → 앞 256d
  F-A′ aud_out_proj [1,T,1536]
  F-B  aud_h_l11 [1,T,1024]
  F-C  mean(aud_h_l06,08,10,11) [1,T,1024]

T = ceil(mel_frames/4). 16초 상한 400. 클립은 16초 이하만 사용한다.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
import soundfile as sf
from transformers import Gemma4AudioFeatureExtractor

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "wave1"
FEATS = OUT / "feats"
MODEL = ROOT / "data/models/embeddinggemma-2-f9972ac2"
ONNX = ROOT / "onnx/eg2_audio_q8_layers.onnx"
MAX_FRAMES = 400


def ln(x):
    m = x.mean(axis=-1, keepdims=True)
    s = x.std(axis=-1, keepdims=True)
    return (x - m) / (s + 1e-6)


def l2(x):
    n = np.linalg.norm(x, axis=-1, keepdims=True)
    return x / (n + 1e-6)


def build_vocab(texts):
    chars = sorted({c for t in texts for c in t.replace(" ", "")})
    return {"blank": 0, "chars": chars, "char2id": {c: i + 1 for i, c in enumerate(chars)}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(OUT / "manifest.jsonl"))
    ap.add_argument("--out-dir", default=str(FEATS))
    ap.add_argument("--vocab-in", default="")
    ap.add_argument("--arms", default="fd,fa,fb,fc")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--fc-memmap", action="store_true",
                    help="stream F-C frames to fc.feats.npy + metadata (avoids 8GB RAM)")
    a = ap.parse_args()
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(l) for l in open(a.manifest, encoding="utf-8") if l.strip()]
    if a.limit:
        rows = rows[: a.limit]
    # accept both text (wave1) and ref (c2a1)
    for r in rows:
        if "text" not in r:
            r["text"] = r.get("ref", "")
    # skip >16s and empty; keep order
    rows = [r for r in rows if 0.5 <= r["dur"] <= 16.0 and r.get("text")]
    texts = [r["text"] for r in rows]
    if a.vocab_in:
        vocab = json.load(open(a.vocab_in, encoding="utf-8"))
    else:
        vocab = build_vocab(texts)
    json.dump(vocab, open(out_dir / "vocab.json", "w", encoding="utf-8"), ensure_ascii=False)
    c2i = vocab["char2id"]
    print(f"rows={len(rows)} vocab={len(vocab['chars'])}", flush=True)

    # local-only config: avoid HF repo-id resolution on VPS absolute paths
    cfg = json.load(open(MODEL / "preprocessor_config.json", encoding="utf-8"))
    fe = Gemma4AudioFeatureExtractor.from_dict(cfg)
    so = ort.SessionOptions()
    so.intra_op_num_threads = a.threads
    sess = ort.InferenceSession(str(ONNX), sess_options=so, providers=["CPUExecutionProvider"])
    out_names = [o.name for o in sess.get_outputs()]

    all_arms = {
        "fd": (256, "audio_features"),
        "fa": (1536, "aud_out_proj"),
        "fb": (1024, "aud_h_l11"),
        "fc": (4096, "concat"),
    }
    want = [x.strip() for x in a.arms.split(",") if x.strip()]
    arms = {k: v for k, v in all_arms.items() if k in want}
    if not arms:
        raise SystemExit("no arms selected")
    store = {k: {"feats": np.zeros((len(rows), MAX_FRAMES, d), dtype=np.float16),
                 "lens": np.zeros(len(rows), dtype=np.int32)}
             for k, (d, _) in arms.items() if k != "fc"}
    fc_parts = []
    fc_lens = []
    fc_bin = None
    fc_bin_path = out_dir / "fc.frames.bin"
    fc_frames = 0
    if "fc" in arms and a.fc_memmap:
        fc_bin = open(fc_bin_path, "wb")
    targets = []
    target_lens = []
    kept = []
    t0 = time.time()
    for i, r in enumerate(rows):
        try:
            x, sr = sf.read(str(ROOT / r["audio"]), dtype="float32")
        except Exception as e:
            print("skip read", r["id"], e, file=sys.stderr)
            continue
        if x.ndim > 1:
            x = x.mean(axis=1)
        if sr != 16000:
            print("skip sr", r["id"], sr, file=sys.stderr)
            continue
        inp = fe(x[None, :], sampling_rate=16000, return_tensors="np", return_attention_mask=True)
        f_in = inp["input_features"].astype(np.float32)
        m_in = inp["input_features_mask"].astype(bool)
        outs = sess.run(None, {"input_features": f_in, "input_features_mask": m_in})
        o = dict(zip(out_names, outs))
        # actual valid frames (audio_features is frame-major, hidden is [1,T,d])
        n = min(int(np.asarray(o["audio_features"]).shape[0]),
                int(np.asarray(o["aud_out_proj"]).shape[1]), MAX_FRAMES)
        if n <= 0:
            continue
        fd = l2(np.asarray(o["audio_features"])[:n, :256])
        fa = ln(np.asarray(o["aud_out_proj"])[0, :n, :])
        fb = ln(np.asarray(o["aud_h_l11"])[0, :n, :])
        fc = np.concatenate([ln(np.asarray(o[f"aud_h_l{l:02d}"])[0, :n, :])
                             for l in (6, 8, 10, 11)], axis=-1)
        # text / ctc target
        txt = r["text"].replace(" ", "")
        if not txt or len(txt) > n:
            print("skip target", r["id"], len(txt), n, file=sys.stderr)
            continue
        ids = [c2i[c] for c in txt if c in c2i and c != " "]
        if not ids or len(ids) > n:
            continue
        j = len(kept)
        arrs = {"fd": fd, "fa": fa, "fb": fb, "fc": fc}
        for k in arms:
            arr = arrs[k]
            if k == "fc":
                fc_lens.append(n)
                if a.fc_memmap:
                    fc_bin.write(arr.astype(np.float16).tobytes())
                    fc_frames += len(arr)
                else:
                    fc_parts.append(arr.astype(np.float16))
            else:
                d = arms[k][0]
                store[k]["feats"][j, :n, :d] = arr.astype(np.float16)
                store[k]["lens"][j] = n
        targets.extend(ids)
        target_lens.append(len(ids))
        kept.append(r)
        if (i + 1) % 100 == 0:
            print(f"{i+1}/{len(rows)} kept={len(kept)} {time.time()-t0:.1f}s", flush=True)
    N = len(kept)
    print(f"kept={N}/{len(rows)} elapsed={time.time()-t0:.1f}s", flush=True)
    targets = np.asarray(targets, dtype=np.int32)
    target_lens = np.asarray(target_lens, dtype=np.int32)
    for k, (d, _) in arms.items():
        if k == "fc":
            lens_np = np.asarray(fc_lens, dtype=np.int32)
            off = np.zeros(len(fc_lens) + 1, dtype=np.int64)
            off[1:] = np.cumsum(lens_np)
            if a.fc_memmap:
                fc_bin.close()
                npy = out_dir / "fc.feats.npy"
                import numpy.lib.format as nf
                with open(npy, "wb") as outf:
                    nf.write_array_header_1_0(
                        outf, {"descr": "<f2", "fortran_order": False, "shape": (fc_frames, d)})
                    with open(fc_bin_path, "rb") as inf:
                        shutil.copyfileobj(inf, outf)
                fc_bin_path.unlink(missing_ok=True)
                payload = dict(offsets=off, lens=lens_np)
            else:
                payload = dict(feats=np.concatenate(fc_parts, axis=0) if fc_parts else np.zeros((0, d), np.float16),
                               offsets=off, lens=lens_np)
        else:
            payload = dict(feats=store[k]["feats"][:N], lens=store[k]["lens"][:N])
        np.savez_compressed(
            out_dir / f"{k}.npz",
            **payload,
            targets=targets,
            target_lens=target_lens,
            ids=np.array([r["id"] for r in kept]),
            speakers=np.array([str(r.get("speaker") or "") for r in kept]),
            texts=np.array([r["text"] for r in kept]),
        )
        print("saved", k, (out_dir / f"{k}.npz").stat().st_size / 1e6, "MB", flush=True)
    json.dump({"rows": N, "vocab": len(vocab["chars"]), "arms": {k: v[0] for k, v in arms.items()}},
              open(out_dir / "summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
