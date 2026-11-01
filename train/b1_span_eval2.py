"""B1 보강 v2 — 식별자 span 평가(전용 평가셋).

학습: cache/b1(원 코퍼스)의 train 문장 토큰
평가: cache/b1_id(전용 합성 300문장)의 식별자 span 전체

사용: python train/b1_span_eval2.py --layers tok_h_l00 --epochs 20
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import torch
import torch.nn as nn
from tokenizers import Tokenizer

ROOT = r"C:\code\unigem"
TRAIN_CACHE = os.path.join(ROOT, "cache", "b1")
EVAL_CACHE = os.path.join(ROOT, "cache", "b1_id")
CORPUS = os.path.join(ROOT, "data", "b1", "corpus.jsonl")
EVAL_CORPUS = os.path.join(ROOT, "data", "b1", "id_eval.jsonl")
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
SEED = 20261102
MAXLEN = 64

from b1_span_eval import spans_of  # noqa: E402


def load(cache, corpus):
    meta = json.load(open(os.path.join(cache, "meta.json"), encoding="utf-8"))
    tokens = np.load(os.path.join(cache, "tokens.npy"))
    mask = np.load(os.path.join(cache, "mask.npy"))
    rows = [json.loads(l) for l in open(corpus, encoding="utf-8")]
    hs = {}
    for n in meta["layers"]:
        hs[n] = np.load(os.path.join(cache, f"h_{n}.npy"), mmap_mode="r")
    return meta, tokens, mask, rows, hs


def flat(hs, names, mask):
    xs = []
    for n in names:
        h = hs[n]
        xs.append(np.asarray(h.reshape(-1, h.shape[-1])[mask.reshape(-1)], dtype=np.float32))
    return np.concatenate(xs, axis=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", required=True)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--lr", type=float, default=3e-3)
    args = ap.parse_args()
    names = [x for x in args.layers.split(",") if x]
    torch.manual_seed(SEED)

    tm, ttok, tmask, trows, ths = load(TRAIN_CACHE, CORPUS)
    em, etok, emask, erows, ehs = load(EVAL_CACHE, EVAL_CORPUS)
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))

    ids = sorted({int(t) for t in ttok[tmask]})
    vmap = {t: i for i, t in enumerate(ids)}
    y = np.array([vmap[int(t)] for t in ttok[tmask]], dtype=np.int64)

    groups = [r.get("base_id", r["id"]) for r in trows]
    uniq = sorted(set(groups))
    rng = np.random.default_rng(SEED)
    rng.shuffle(uniq)
    tg = set(uniq[: int(len(uniq) * 0.8)])
    s_train = np.array([g in tg for g in groups])
    sent_of = np.repeat(np.arange(len(trows)), ttok.shape[1])[tmask.reshape(-1)]
    tr = s_train[sent_of]

    X = flat(ths, names, tmask)
    print(f"train dim {X.shape[1]} vocab {len(ids)} tokens {tr.sum()}", flush=True)
    model = nn.Linear(X.shape[1], len(ids))
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)
    lossf = nn.CrossEntropyLoss()
    Xt, yt = torch.from_numpy(X[tr]), torch.from_numpy(y[tr])
    n = len(Xt)
    for ep in range(args.epochs):
        perm = torch.randperm(n)
        for i in range(0, n, 4096):
            idx = perm[i:i + 4096]
            opt.zero_grad()
            loss = lossf(model(Xt[idx]), yt[idx])
            loss.backward()
            opt.step()
        sched.step()

    Xe = flat(ehs, names, emask)
    with torch.no_grad():
        pred = model(torch.from_numpy(Xe)).argmax(1).numpy()

    pred_by_pos = {}
    k = 0
    for si in range(len(erows)):
        for j in range(etok.shape[1]):
            if emask[si, j]:
                pred_by_pos[(si, j)] = ids[int(pred[k])]
                k += 1

    stats, tokstats = {}, {}
    for si, r in enumerate(erows):
        enc = tok.encode(r["text"])
        offs = enc.offsets[:MAXLEN]
        for kind, s, e, val in spans_of(r["text"]):
            idxs = [j for j in range(min(len(offs), MAXLEN))
                    if emask[si, j] and offs[j] != (0, 0) and offs[j][0] < e and offs[j][1] > s]
            if not idxs:
                continue
            ok = all(pred_by_pos.get((si, j)) == int(etok[si, j]) for j in idxs)
            st = stats.setdefault(kind, {"n": 0, "ok": 0})
            st["n"] += 1; st["ok"] += int(ok)
            for j in idxs:
                ts = tokstats.setdefault(kind, {"n": 0, "ok": 0})
                ts["n"] += 1
                ts["ok"] += int(pred_by_pos.get((si, j)) == int(etok[si, j]))

    out = {"layers": names, "epochs": args.epochs, "eval": "id_eval(300문장, 전용)",
           "spans": {k: {"n": v["n"], "exact": v["ok"] / v["n"]} for k, v in sorted(stats.items())},
           "tokens": {k: {"n": v["n"], "acc": v["ok"] / v["n"]} for k, v in sorted(tokstats.items())}}
    tn = sum(v["n"] for v in stats.values()); to = sum(v["ok"] for v in stats.values())
    out["total"] = {"n": tn, "exact": to / tn if tn else None}
    print(json.dumps(out, ensure_ascii=False), flush=True)
    with open(os.path.join(ROOT, "logs", "B1_span.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
