"""B1 특징 추출 — 텍스트 연구용 FP32 그래프의 층별 hidden 캐시.

출력(cache/b1/):
- tokens.npy   int32 [N, 64]  (패딩 0)
- mask.npy     bool  [N, 64]
- pooled.npy   float32 [N, 768]
- h_<name>.npy float16 [N, 64, D]  (l00,l04,l08,l12,l16,l20,last,emb768)
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

ROOT = r"C:\code\unigem"
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
ONNX = os.path.join(ROOT, "onnx", "eg2_text_research_fp32.onnx")
CORPUS = os.path.join(ROOT, "data", "b1", "corpus.jsonl")
OUT = os.path.join(ROOT, "cache", "b1")
MAXLEN = 64
BATCH = 8


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=CORPUS)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rows = [json.loads(l) for l in open(a.corpus, encoding="utf-8")]
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))

    so = ort.SessionOptions()
    so.intra_op_num_threads = 6
    so.log_severity_level = 3
    sess = ort.InferenceSession(ONNX, so, providers=["CPUExecutionProvider"])
    names = [o.name for o in sess.get_outputs()]
    layer_names = [n for n in names if n.startswith("tok_h_") or n == "tok_emb_768"]
    dims = {}
    for o in sess.get_outputs():
        if o.name in layer_names:
            dims[o.name] = o.shape[-1]
    print("layers", layer_names, dims, flush=True)

    n = len(rows)
    tokens = np.zeros((n, MAXLEN), np.int32)
    mask = np.zeros((n, MAXLEN), bool)
    pooled = np.zeros((n, 768), np.float32)
    hs = {name: np.zeros((n, MAXLEN, dims[name]), np.float16) for name in layer_names}

    empty = np.zeros((0, 512), np.float32)
    t0 = time.time()
    for start in range(0, n, BATCH):
        batch = rows[start:start + BATCH]
        ids = np.zeros((len(batch), MAXLEN), np.int64)
        am = np.zeros((len(batch), MAXLEN), np.int64)
        for i, r in enumerate(batch):
            enc = tok.encode(r["text"])
            seq = enc.ids[:MAXLEN]
            ids[i, :len(seq)] = seq
            am[i, :len(seq)] = 1
        feats = {
            "input_ids": ids,
            "attention_mask": am,
            "image_features": empty,
            "video_features": empty,
            "audio_features": empty,
        }
        out = dict(zip(names, sess.run(None, feats)))
        sl = slice(start, start + len(batch))
        tokens[sl] = ids.astype(np.int32)
        mask[sl] = am.astype(bool)
        pooled[sl] = out["sentence_embedding"]
        for name in layer_names:
            hs[name][sl] = out[name].astype(np.float16)
        if start % 160 == 0:
            print(f"{start}/{n} {time.time()-t0:.1f}s", flush=True)

    np.save(os.path.join(a.out, "tokens.npy"), tokens)
    np.save(os.path.join(a.out, "mask.npy"), mask)
    np.save(os.path.join(a.out, "pooled.npy"), pooled)
    for name in layer_names:
        np.save(os.path.join(a.out, f"h_{name}.npy"), hs[name])
    json.dump({"n": n, "maxlen": MAXLEN, "layers": layer_names, "dims": dims,
               "onnx": ONNX, "ckpt": CKPT, "corpus": a.corpus},
              open(os.path.join(a.out, "meta.json"), "w", encoding="utf-8"), indent=2)
    print("done", n, f"{time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
