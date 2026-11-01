"""B1 프로빙 v3 — 토큰 단위 층화 분할(클래스별 20% 홀드아웃).

목적: hidden→토큰 id 매핑의 복원 가능성(가역성)을 측정한다.
- 클래스별로 인스턴스를 나눠 학습/평가에 모두 등장시킨다(미등장 클래스 문제 제거).
- 평가는 인스턴스 5개 이상인 클래스로 제한하고, 커버리지를 함께 보고한다.
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", required=True)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--min-count", type=int, default=5)
    args = ap.parse_args()

    names = [x for x in args.layers.split(",") if x]
    torch.manual_seed(SEED)
    tokens = np.load(os.path.join(CACHE, "tokens.npy"))
    mask = np.load(os.path.join(CACHE, "mask.npy"))
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    inv = {v: k for k, v in tok.get_vocab().items()}

    Xs = []
    for n in names:
        h = np.load(os.path.join(CACHE, f"h_{n}.npy"), mmap_mode="r")
        Xs.append(np.asarray(h.reshape(-1, h.shape[-1])[mask.reshape(-1)], dtype=np.float32))
    X = np.concatenate(Xs, axis=1)
    raw = tokens[mask]
    cls = np.array([token_class(inv.get(int(t), "")) for t in raw])

    ids = sorted(set(int(t) for t in raw))
    vmap = {t: i for i, t in enumerate(ids)}
    y = np.array([vmap[int(t)] for t in raw], dtype=np.int64)

    rng = np.random.default_rng(SEED)
    test_mask = np.zeros(len(y), bool)
    counts = np.bincount(y, minlength=len(ids))
    for c in range(len(ids)):
        idx = np.where(y == c)[0]
        if counts[c] >= args.min_count:
            k = max(1, int(round(len(idx) * 0.2)))
            test_mask[rng.choice(idx, size=k, replace=False)] = True

    tr = ~test_mask
    print(f"layers {names} dim {X.shape[1]} vocab {len(ids)} tokens {len(y)} "
          f"train {tr.sum()} test {test_mask.sum()}", flush=True)

    model = nn.Linear(X.shape[1], len(ids))
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)
    lossf = nn.CrossEntropyLoss()
    Xt, yt = torch.from_numpy(X[tr]), torch.from_numpy(y[tr])
    Xe, ye = torch.from_numpy(X[test_mask]), torch.from_numpy(y[test_mask])
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
    ce = cls[test_mask]
    out = {"layers": names, "dim": int(X.shape[1]), "vocab": len(ids), "epochs": args.epochs,
           "split": "token_stratified", "min_count": args.min_count,
           "overall": float((pred == ytrue).mean()), "classes": {}}
    for c in ("number", "identifier", "other"):
        m = ce == c
        out["classes"][c] = {"n": int(m.sum()),
                             "acc": float((pred[m] == ytrue[m]).mean()) if m.any() else None}
    print(json.dumps(out, ensure_ascii=False), flush=True)
    with open(os.path.join(ROOT, "logs", "B1_sweep.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
