"""R2 T3′ — 자연문장 최소쌍(5유형) 판별.

BL-0(l00 단일) / BL-1(l00 ±2) / l04(BL-1+l04) 동일 용량 비교.
라벨: 정답 형태=1, 오답 형태=0. target_char 위치의 토큰 특징 사용.
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from tokenizers import Tokenizer

ROOT = r"C:\code\unigem"
CACHE = os.path.join(ROOT, "cache", "r2_t3")
CORPUS = os.path.join(ROOT, "data", "r2", "t3_corpus.jsonl")
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")


def load(layer):
    files = sorted(os.path.join(CACHE, "shards", f) for f in os.listdir(os.path.join(CACHE, "shards")))
    out = {}
    for p in files:
        z = np.load(p)
        for k, r in enumerate(z["row_idx"]):
            L = int(z["mask"][k].sum())
            out[int(r)] = z[layer][k, :L].astype(np.float32)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--bs", type=int, default=512)
    ap.add_argument("--out", default=os.path.join(ROOT, "logs", "R2_t3.json"))
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    H0, H4 = load("tok_h_l00"), load("tok_h_l04")

    X, y, split, typ, sent = [], [], [], [], []
    for i, r in enumerate(rows):
        h0, h4 = H0.get(i), H4.get(i)
        if h0 is None:
            continue
        enc = tok.encode(r["text"])
        pos = r["target_char"]
        k = next((t for t, (s0, s1) in enumerate(enc.offsets) if s0 <= pos < s1), None)
        if k is None:
            continue
        L = len(enc.ids)
        win = [h0[u] if 0 <= u < L else np.zeros(512, np.float32) for u in range(k - 2, k + 3)]
        base = np.concatenate(win)
        X.append({"bl0": h0[k].copy(), "bl1": base, "l04": np.concatenate([base, h4[k]])})
        y.append(r["label"]); split.append(r["split"]); typ.append(r["kind"]); sent.append(r["group"])
    y = np.array(y); split = np.array(split); typ = np.array(typ); sent = np.array(sent)
    tr, va, te = split == "train", split == "val", split == "test"
    print("rows", len(y), "test", int(te.sum()), "types", sorted(set(typ)), flush=True)

    res = {"n": int(len(y)), "n_test": int(te.sum())}
    preds = {}
    for cfg in ("bl0", "bl1", "l04"):
        Xa = np.stack([x[cfg] for x in X])
        xt = torch.from_numpy(Xa[tr]); yt = torch.from_numpy(y[tr]).float()
        model = nn.Linear(Xa.shape[1], 1)
        opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
        for ep in range(a.epochs):
            perm = torch.randperm(len(xt))
            for st in range(0, len(xt), a.bs):
                j = perm[st:st + a.bs]; opt.zero_grad()
                loss = F.binary_cross_entropy_with_logits(model(xt[j]).squeeze(-1), yt[j])
                loss.backward(); opt.step()
        with torch.no_grad():
            pv = torch.sigmoid(model(torch.from_numpy(Xa[va])).squeeze(-1)).numpy()
            pt = torch.sigmoid(model(torch.from_numpy(Xa[te])).squeeze(-1)).numpy()
        thrs = np.linspace(0.05, 0.95, 91)
        thr = max((np.mean((pv >= t) == y[va]), t) for t in thrs)[1]
        acc = float(np.mean((pt >= thr) == y[te]))
        per = {k: float(np.mean((pt[typ[te] == k] >= thr) == y[te][typ[te] == k])) for k in sorted(set(typ))}
        res[cfg] = {"acc": acc, "thr": float(thr), "per_type": per}
        preds[cfg] = (pt, thr)
        print(cfg, res[cfg], flush=True)

    # 부트스트랩 Δ정확도 (l04 - bl1)
    ids = np.unique(sent[te]); groups = {s: np.where(sent[te] == s)[0] for s in ids}
    rng = np.random.default_rng(0)
    d = []
    for _ in range(1000):
        pick = rng.choice(ids, len(ids), replace=True)
        idx = np.concatenate([groups[s] for s in pick])
        acc4 = np.mean((preds["l04"][0][idx] >= preds["l04"][1]) == y[te][idx])
        acc1 = np.mean((preds["bl1"][0][idx] >= preds["bl1"][1]) == y[te][idx])
        d.append(acc4 - acc1)
    res["delta_l04_bl1"] = {"point": res["l04"]["acc"] - res["bl1"]["acc"],
                            "ci_low": float(np.percentile(d, 2.5)), "ci_high": float(np.percentile(d, 97.5))}
    json.dump(res, open(a.out, "w", encoding="utf-8"), indent=2)
    print(json.dumps(res["delta_l04_bl1"], indent=1))


if __name__ == "__main__":
    main()
