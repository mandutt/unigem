"""B1.5-1 — 임베딩 테이블 공유 프로브 v2.

- 각 층 h(512) → W(768) → 임베딩 테이블 E(262144,768)와 내적 → softmax
- 학습은 코퍼스 등장 토큰(어휘 부분집합)에 대해, 평가는 (a) 부분집합 정확도 (b) 전체 어휘 argmax
- 층별·시드별 반복, train/val/test 분리
"""
from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = r"C:\code\unigem"
CACHE = os.path.join(ROOT, "cache", "b1_5")
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
CORPUS = os.path.join(ROOT, "data", "b1_5", "corpus_v2", "corpus.jsonl")
SPLITS: list[str] = []


def load_embedding_table():
    from safetensors import safe_open
    path = os.path.join(CKPT, "model.safetensors")
    with safe_open(path, framework="pt", device="cpu") as f:
        for k in f.keys():
            if "embed_tokens" in k and k.endswith("weight"):
                return f.get_tensor(k).float().numpy(), k
    raise SystemExit("embedding table not found")


def load_layer(layer: str):
    """마스킹된 토큰만 평탄화해 반환한다(메모리 절감)."""
    meta = json.load(open(os.path.join(CACHE, "meta.json"), encoding="utf-8"))
    files = sorted(os.path.join(CACHE, "shards", f) for f in os.listdir(os.path.join(CACHE, "shards")))
    xs, ys, ss = [], [], []
    for p in files:
        z = np.load(p)
        h = z[layer]
        ids = z["ids"]
        m = z["mask"]
        xs.append(h[m].astype(np.float32))
        ys.append(ids[m].astype(np.int64))
        ss.append(np.zeros(0, dtype=object))
        # 행별 split을 row_idx로 매핑해 토큰 단위로 확장
        row_splits = np.array([SPLITS[int(r)] for r in z["row_idx"]])
        ss[-1] = np.repeat(row_splits, m.sum(axis=1))
    return meta, np.concatenate(xs), np.concatenate(ys), np.concatenate(ss)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", nargs="+", default=["tok_h_l00", "tok_h_l04", "tok_h_last"])
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--bs", type=int, default=4096)
    ap.add_argument("--full_tokens", type=int, default=4096)
    ap.add_argument("--out", default=os.path.join(ROOT, "logs", "B1_5_probe.json"))
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    global SPLITS
    SPLITS = [r["split"] for r in rows]
    E, ekey = load_embedding_table()
    print("E", E.shape, ekey, flush=True)

    results = {"embedding_key": ekey, "layers": {}, "seeds": a.seeds, "epochs": a.epochs}
    for layer in a.layers:
        meta, X, Y, S = load_layer(layer)
        tr = S == "train"
        va = S == "val"
        te = S == "test"
        x_tr, y_tr = X[tr], Y[tr]
        vocab = np.unique(y_tr)
        vmap = {int(v): i for i, v in enumerate(vocab)}
        Ev = torch.from_numpy(E[vocab])
        yv_tr = torch.tensor([vmap[int(y)] for y in y_tr], dtype=torch.long)
        print(layer, "train tokens", len(y_tr), "vocab", len(vocab), flush=True)

        accs = []
        for seed in range(a.seeds):
            torch.manual_seed(seed)
            W = nn.Linear(X.shape[-1], E.shape[1], bias=False)
            opt = torch.optim.AdamW(W.parameters(), lr=1e-3)
            ds = torch.utils.data.TensorDataset(torch.from_numpy(x_tr), yv_tr)
            dl = torch.utils.data.DataLoader(ds, batch_size=a.bs, shuffle=True, drop_last=True)
            t0 = time.time()
            for ep in range(a.epochs):
                for xb, yb in dl:
                    opt.zero_grad()
                    logits = (W(xb) @ Ev.T)
                    loss = F.cross_entropy(logits, yb)
                    loss.backward()
                    opt.step()
            # 평가
            W.eval()
            def acc(mask, full=False):
                xs = torch.from_numpy(X[mask]); yy = Y[mask]
                preds = []
                with torch.no_grad():
                    for i in range(0, len(xs), 2048):
                        z = W(xs[i:i + 2048])
                        if full:
                            lg = z @ torch.from_numpy(E).T
                            preds.append(lg.argmax(-1).numpy())
                        else:
                            lg = z @ Ev.T
                            preds.append(vocab[lg.argmax(-1).numpy()])
                p = np.concatenate(preds)
                return float((p == yy).mean()), len(yy)
            va_acc, nva = acc(va)
            te_acc, nte = acc(te)
            te_full = float("nan")
            if seed == 0:
                # 전체 어휘 argmax는 부분표본으로 측정(비용)
                rng = np.random.default_rng(0)
                idx = rng.choice(np.where(te)[0], size=min(a.full_tokens, int(te.sum())), replace=False)
                sub = np.zeros_like(te)
                sub[idx] = True
                te_full, _ = acc(sub, full=True)
            accs.append({"seed": seed, "val": va_acc, "test": te_acc, "test_full": te_full,
                         "train_s": round(time.time() - t0, 1)})
            print(layer, seed, va_acc, te_acc, te_full, f"{time.time()-t0:.0f}s", flush=True)
        results["layers"][layer] = {"n_train_tokens": int(tr.sum()), "vocab": int(len(vocab)),
                                    "runs": accs,
                                    "val_mean": float(np.mean([r["val"] for r in accs])),
                                    "test_mean": float(np.mean([r["test"] for r in accs])),
                                    "test_full_mean": float(np.nanmean([r["test_full"] for r in accs]))}
        json.dump(results, open(a.out, "w", encoding="utf-8"), indent=2)
    print("saved", a.out, flush=True)


if __name__ == "__main__":
    main()
