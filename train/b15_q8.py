"""B1.5-5 — Q8 견고성: FP32 학습 헤드를 Q8 특징에 적용 + Q8 재학습.

- 층: l00, l04
- 어휘: 학습 코퍼스 등장 토큰
- 지표: test 정확도, 하락폭(%p)
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = r"C:\code\unigem"
CORPUS = os.path.join(ROOT, "data", "b1_5", "corpus_v2", "corpus.jsonl")
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
SPLITS: list[str] = []


def load_flat(cache: str, layer: str):
    files = sorted(os.path.join(cache, "shards", f) for f in os.listdir(os.path.join(cache, "shards")))
    xs, ys, ss = [], [], []
    for p in files:
        z = np.load(p)
        h = z[layer]; ids = z["ids"]; m = z["mask"]
        xs.append(h[m].astype(np.float32))
        ys.append(ids[m].astype(np.int64))
        row_splits = np.array([SPLITS[int(r)] for r in z["row_idx"]])
        ss.append(np.repeat(row_splits, m.sum(axis=1)))
    return np.concatenate(xs), np.concatenate(ys), np.concatenate(ss)


def train_eval(Xtr, ytr, vocab, E, Xte, yte, epochs=3, seed=0, bs=4096):
    torch.manual_seed(seed)
    Ev = torch.from_numpy(E[vocab])
    vmap = {int(v): i for i, v in enumerate(vocab)}
    yv = torch.tensor([vmap[int(y)] for y in ytr], dtype=torch.long)
    W = nn.Linear(Xtr.shape[1], E.shape[1], bias=False)
    opt = torch.optim.AdamW(W.parameters(), lr=1e-3)
    ds = torch.utils.data.TensorDataset(torch.from_numpy(Xtr), yv)
    dl = torch.utils.data.DataLoader(ds, batch_size=bs, shuffle=True, drop_last=True)
    for ep in range(epochs):
        for xb, yb in dl:
            opt.zero_grad()
            loss = F.cross_entropy(W(xb) @ Ev.T, yb)
            loss.backward(); opt.step()
    W.eval()
    with torch.no_grad():
        z = W(torch.from_numpy(Xte))
        pred = vocab[(z @ Ev.T).argmax(-1).numpy()]
    return float((pred == yte).mean()), len(yte)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", nargs="+", default=["tok_h_l00", "tok_h_l04"])
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--out", default=os.path.join(ROOT, "logs", "B1_5_q8.json"))
    a = ap.parse_args()

    import json as _json
    rows = [_json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    global SPLITS
    SPLITS = [r["split"] for r in rows]
    from safetensors import safe_open
    with safe_open(os.path.join(CKPT, "model.safetensors"), framework="pt") as f:
        E = f.get_tensor("language_model.embed_tokens.weight").float().numpy()

    res = {"layers": {}}
    for layer in a.layers:
        Xf, Yf, Sf = load_flat(os.path.join(ROOT, "cache", "b1_5"), layer)
        Xq, Yq, Sq = load_flat(os.path.join(ROOT, "cache", "b1_5_q8"), layer)
        vocab = np.unique(Yf[Sf == "train"])
        tr_f, te_f = Sf == "train", Sf == "test"
        tr_q, te_q = Sq == "train", Sq == "test"
        r = {}
        for seed in range(a.seeds):
            acc_ff, n = train_eval(Xf[tr_f], Yf[tr_f], vocab, E, Xf[te_f], Yf[te_f], seed=seed)
            acc_fq, _ = train_eval(Xf[tr_f], Yf[tr_f], vocab, E, Xq[te_q], Yq[te_q], seed=seed)
            acc_qq, _ = train_eval(Xq[tr_q], Yq[tr_q], vocab, E, Xq[te_q], Yq[te_q], seed=seed)
            r[seed] = {"fp32_test": acc_ff, "fp32head_on_q8": acc_fq, "q8_retrain": acc_qq,
                       "drop_pp": (acc_ff - acc_fq) * 100, "n_test": n}
            print(layer, seed, r[seed], flush=True)
        res["layers"][layer] = r
    json.dump(res, open(a.out, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main()
