"""B1 프로빙 v2 — 에폭/층 조합 스윕 (선형 헤드).

사용:
  python train/b1_probe2.py --layers tok_h_l00,tok_h_last --epochs 30
  python train/b1_probe2.py --combo tok_h_l00,tok_h_l04,tok_h_l08,tok_h_l12,tok_h_l16,tok_h_l20 --epochs 15
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time

import numpy as np
import torch
import torch.nn as nn
from tokenizers import Tokenizer

ROOT = r"C:\code\unigem"
CACHE = os.path.join(ROOT, "cache", "b1")
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
CORPUS = os.path.join(ROOT, "data", "b1", "corpus.jsonl")
SEED = 20261102


def token_class(s: str) -> str:
    core = s.replace("▁", "").strip()
    if not core:
        return "other"
    if re.fullmatch(r"[\d.,:/\-]+", core) and any(c.isdigit() for c in core):
        return "number"
    if re.fullmatch(r"[A-Za-z0-9_./\-]+", core) and any(c.isdigit() for c in core):
        return "identifier"
    return "other"


def load_xy(names):
    meta = json.load(open(os.path.join(CACHE, "meta.json"), encoding="utf-8"))
    tokens = np.load(os.path.join(CACHE, "tokens.npy"))
    mask = np.load(os.path.join(CACHE, "mask.npy"))
    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    inv = {v: k for k, v in tok.get_vocab().items()}
    ids = sorted({int(t) for t in tokens[mask]})
    vmap = {t: i for i, t in enumerate(ids)}
    Xs = []
    for n in names:
        h = np.load(os.path.join(CACHE, f"h_{n}.npy"), mmap_mode="r")
        Xs.append(np.asarray(h.reshape(-1, h.shape[-1])[mask.reshape(-1)], dtype=np.float32))
    X = np.concatenate(Xs, axis=1)
    y = np.array([vmap[int(t)] for t in tokens[mask]], dtype=np.int64)
    cls = np.array([token_class(inv.get(int(t), "")) for t in tokens[mask]])
    sent = np.repeat(np.arange(len(rows)), tokens.shape[1])[mask.reshape(-1)]
    groups = np.array([r.get("base_id", r["id"]) for r in rows])
    uniq = sorted(set(groups))
    rng = np.random.default_rng(SEED)
    rng.shuffle(uniq)
    train_groups = set(uniq[: int(len(uniq) * 0.8)])
    sent_train = np.array([g in train_groups for g in groups])
    tr = sent_train[sent]
    return X, y, cls, tr, len(ids), rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", default="")
    ap.add_argument("--combo", default="")
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--lr", type=float, default=3e-3)
    args = ap.parse_args()

    names = [x for x in (args.combo or args.layers).split(",") if x]
    label = "+".join(names)
    torch.manual_seed(SEED)
    X, y, cls, tr, V, rows = load_xy(names)
    print(f"combo {label} dim {X.shape[1]} vocab {V} tokens {len(y)} train {tr.sum()}", flush=True)

    model = nn.Linear(X.shape[1], V)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)
    lossf = nn.CrossEntropyLoss()
    Xt, yt = torch.from_numpy(X[tr]), torch.from_numpy(y[tr])
    Xe, ye = torch.from_numpy(X[~tr]), torch.from_numpy(y[~tr])
    n = len(Xt)

    t0 = time.time()
    for ep in range(args.epochs):
        perm = torch.randperm(n)
        tot = 0.0
        for i in range(0, n, 4096):
            idx = perm[i:i + 4096]
            opt.zero_grad()
            loss = lossf(model(Xt[idx]), yt[idx])
            loss.backward()
            opt.step()
            tot += loss.item() * len(idx)
        sched.step()
        if ep % 5 == 4 or ep == args.epochs - 1:
            with torch.no_grad():
                pred = model(Xe).argmax(1).numpy()
            acc = float((pred == ye.numpy()).mean())
            print(f"  ep{ep+1} loss {tot/n:.4f} test_acc {acc:.4f} ({time.time()-t0:.0f}s)", flush=True)

    with torch.no_grad():
        pred = model(Xe).argmax(1).numpy()
    ytrue = ye.numpy()
    ce = cls[~tr]
    out = {"layers": names, "dim": int(X.shape[1]), "vocab": V, "epochs": args.epochs,
           "overall": float((pred == ytrue).mean()), "classes": {}}
    for c in ("number", "identifier", "other"):
        m = ce == c
        out["classes"][c] = {"n": int(m.sum()),
                             "acc": float((pred[m] == ytrue[m]).mean()) if m.any() else None}
    print(json.dumps(out, ensure_ascii=False), flush=True)
    path = os.path.join(ROOT, "logs", "B1_sweep.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
