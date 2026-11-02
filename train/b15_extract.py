"""B1.5 특징 추출 — 코퍼스 v2, 동적 길이·샤드 체크포인트.

cache/b1_5/shards/shard_0000.npz ...
  row_idx int32 [n], ids int32 [n,L], mask bool [n,L], pooled f32 [n,768],
  h_tok_h_l00 ... f16 [n,L,512]
재개: 기존 shard 파일은 건너뛴다.
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

ROOT = r"C:\code\unigem"
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
ONNX = os.path.join(ROOT, "onnx", "eg2_text_research_fp32.onnx")
CORPUS = os.path.join(ROOT, "data", "b1_5", "corpus_v2", "corpus.jsonl")
OUT = os.path.join(ROOT, "cache", "b1_5")
SHARD = 250
BATCH = 8
MAXLEN = 512


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=CORPUS)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--shard", type=int, default=SHARD)
    a = ap.parse_args()
    sdir = os.path.join(a.out, "shards")
    os.makedirs(sdir, exist_ok=True)
    rows = [json.loads(l) for l in open(a.corpus, encoding="utf-8")]
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    lens = [min(len(tok.encode(r["text"]).ids), MAXLEN) for r in rows]
    order = sorted(range(len(rows)), key=lambda i: lens[i])

    so = ort.SessionOptions()
    so.intra_op_num_threads = 6
    so.log_severity_level = 3
    sess = ort.InferenceSession(ONNX, so, providers=["CPUExecutionProvider"])
    names = [o.name for o in sess.get_outputs()]
    layers = [n for n in names if n.startswith("tok_h_") or n == "tok_emb_768"]
    dims = {o.name: o.shape[-1] for o in sess.get_outputs() if o.name in layers}
    print("layers", dims, flush=True)

    empty = np.zeros((0, 512), np.float32)
    t0 = time.time()
    n_shards = (len(order) + a.shard - 1) // a.shard
    for si in range(n_shards):
        path = os.path.join(sdir, f"shard_{si:04d}.npz")
        if os.path.exists(path):
            continue
        idxs = order[si * a.shard:(si + 1) * a.shard]
        n = len(idxs)
        L = max(1, max(lens[i] for i in idxs))
        ids = np.zeros((n, L), np.int64)
        am = np.zeros((n, L), np.int64)
        for k, i in enumerate(idxs):
            enc = tok.encode(rows[i]["text"])
            seq = enc.ids[:MAXLEN]
            ids[k, :len(seq)] = seq
            am[k, :len(seq)] = 1
        pooled = np.zeros((n, 768), np.float32)
        hs = {name: np.zeros((n, L, dims[name]), np.float16) for name in layers}
        for st in range(0, n, BATCH):
            sl = slice(st, st + BATCH)
            feats = {"input_ids": ids[sl], "attention_mask": am[sl],
                     "image_features": empty, "video_features": empty, "audio_features": empty}
            out = dict(zip(names, sess.run(None, feats)))
            pooled[sl] = out["sentence_embedding"]
            for name in layers:
                hs[name][sl] = out[name].astype(np.float16)
        np.savez_compressed(path, row_idx=np.array(idxs, np.int32), ids=ids.astype(np.int32),
                            mask=am.astype(bool), pooled=pooled, **hs)
        done = si + 1
        print(f"shard {done}/{n_shards} rows={n} L={L} elapsed={time.time()-t0:.1f}s", flush=True)

    json.dump({"n": len(rows), "shards": n_shards, "layers": layers, "dims": dims,
               "corpus": a.corpus, "onnx": ONNX},
              open(os.path.join(a.out, "meta.json"), "w", encoding="utf-8"), indent=2)
    print("done", len(rows), f"{time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
