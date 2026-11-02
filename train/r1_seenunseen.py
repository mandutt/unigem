"""C-3 — seen/unseen 정의 고정 재계산 (토큰 종류 기준)."""
from __future__ import annotations

import json
import os

import numpy as np
from safetensors import safe_open

ROOT = r"C:\code\unigem"
CACHE = os.path.join(ROOT, "cache", "b1_5", "shards")
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")


def load(layer):
    X, Y, S = [], [], []
    for fn in sorted(os.listdir(CACHE)):
        z = np.load(os.path.join(CACHE, fn))
        h = z[layer]; ids = z["ids"]; m = z["mask"]
        for k, r in enumerate(z["row_idx"]):
            L = int(m[k].sum())
            X.append(h[k, :L].astype(np.float32)); Y.append(ids[k, :L].astype(np.int64))
            S.append(np.repeat(int(r), L))
    return np.concatenate(X), np.concatenate(Y), np.concatenate(S)


def wilson(p, n, z=1.96):
    d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [float(c - h), float(c + h)]


def main():
    rows = [json.loads(l) for l in open(os.path.join(ROOT, "data", "b1_5", "corpus_v2", "corpus.jsonl"), encoding="utf-8")]
    split = np.array([r["split"] for r in rows])
    with safe_open(os.path.join(CKPT, "model.safetensors"), framework="pt") as f:
        E = f.get_tensor("language_model.embed_tokens.weight").float().numpy()
    res = {}
    for layer in ("tok_h_l00", "tok_h_l04"):
        X, Y, R = load(layer)
        tr = split[R] == "train"; te = split[R] == "test"
        seen = np.unique(Y[tr])
        W = np.linalg.solve(X[tr].T @ X[tr] + 1e-4 * np.eye(512, dtype=np.float32), X[tr].T @ E[Y[tr]]).astype(np.float32)
        Q = X[te] @ W; Q /= np.maximum(1e-9, np.linalg.norm(Q, axis=1, keepdims=True))
        En = E / np.maximum(1e-9, np.linalg.norm(E, axis=1, keepdims=True))
        pred = np.empty(len(Q), np.int64)
        for s in range(0, len(Q), 512):
            pred[s:s + 512] = (Q[s:s + 512] @ En.T).argmax(1)
        y = Y[te]; seenmask = np.isin(y, seen)
        acc = float((pred == y).mean()); a_s = float((pred[seenmask] == y[seenmask]).mean())
        a_u = float((pred[~seenmask] == y[~seenmask]).mean()) if (~seenmask).any() else None
        res[layer] = {"acc": acc, "ci": wilson(acc, len(y)), "n": int(len(y)),
                      "seen_acc": a_s, "seen_n": int(seenmask.sum()),
                      "unseen_acc": a_u, "unseen_n": int((~seenmask).sum())}
        print(layer, res[layer], flush=True)
    json.dump(res, open(os.path.join(ROOT, "logs", "C3_seen_unseen.json"), "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main()
