"""B1.5-6(부분) — 길이 구간별 토큰 복원 정확도."""
from __future__ import annotations

import json
import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = r"C:\code\unigem"
CACHE = os.path.join(ROOT, "cache", "b1_5")
CORPUS = os.path.join(ROOT, "data", "b1_5", "corpus_v2", "corpus.jsonl")
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
BUCKETS = [(16, 64), (65, 128), (129, 256), (257, 512)]


def main():
    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    splits = [r["split"] for r in rows]
    from safetensors import safe_open
    with safe_open(os.path.join(CKPT, "model.safetensors"), framework="pt") as f:
        E = f.get_tensor("language_model.embed_tokens.weight").float().numpy()

    files = sorted(os.path.join(CACHE, "shards", f) for f in os.listdir(os.path.join(CACHE, "shards")))
    out = {}
    for layer in ("tok_h_l00", "tok_h_l04"):
        xs, ys, ls, ss = [], [], [], []
        for p in files:
            z = np.load(p)
            h = z[layer]; ids = z["ids"]; m = z["mask"]
            for k, ridx in enumerate(z["row_idx"]):
                L = int(m[k].sum())
                if L == 0:
                    continue
                xs.append(h[k, :L].astype(np.float32)); ys.append(ids[k, :L].astype(np.int64))
                ls.append(np.full(L, L, np.int32)); ss.append(np.full(L, splits[int(ridx)], dtype=object))
        X = np.concatenate(xs); Y = np.concatenate(ys); L = np.concatenate(ls); S = np.concatenate(ss)
        vocab = np.unique(Y[S == "train"])
        vmap = {int(v): i for i, v in enumerate(vocab)}
        Ev = torch.from_numpy(E[vocab])
        tr = S == "train"; te = S == "test"
        yt = torch.tensor([vmap[int(y)] for y in Y[tr]], dtype=torch.long)
        W = nn.Linear(X.shape[1], E.shape[1], bias=False)
        opt = torch.optim.AdamW(W.parameters(), lr=1e-3)
        for ep in range(3):
            perm = torch.randperm(tr.sum())
            xt = torch.from_numpy(X[tr])
            for st in range(0, len(perm), 4096):
                idx = perm[st:st + 4096]; opt.zero_grad()
                F.cross_entropy(W(xt[idx]) @ Ev.T, yt[idx]).backward(); opt.step()
        with torch.no_grad():
            z = W(torch.from_numpy(X[te])); pred = vocab[(z @ Ev.T).argmax(-1).numpy()]
        yy = Y[te]; ll = L[te]
        res = {}
        for lo, hi in BUCKETS:
            m = (ll >= lo) & (ll <= hi)
            res[f"{lo}-{hi}"] = {"n": int(m.sum()), "acc": float((pred[m] == yy[m]).mean()) if m.sum() else None}
        res["all"] = {"n": int(len(yy)), "acc": float((pred == yy).mean())}
        out[layer] = res
        print(layer, res, flush=True)
    json.dump(out, open(os.path.join(ROOT, "logs", "B1_5_length.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
