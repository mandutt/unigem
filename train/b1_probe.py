"""B1 프로빙 — 층별 선형 토큰 복원 + 오타 민감도.

- 각 층 hidden(512/768)에서 토큰 id를 복원하는 선형 헤드를 학습
- 문장 단위 80/20 분할(오타-원문 그룹은 같은 쪽에 둔다)
- 지표: 전체 정확도, 숫자 토큰, 식별자 토큰
- 오타 민감도: 오타 문장과 원문의 pooled cosine, 그리고 같은 위치 토큰 hidden cosine
"""
from __future__ import annotations

import json
import os
import re
import sys

import numpy as np
import torch
import torch.nn as nn
from tokenizers import Tokenizer

ROOT = r"C:\code\unigem"
CACHE = os.path.join(ROOT, "cache", "b1")
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
CORPUS = os.path.join(ROOT, "data", "b1", "corpus.jsonl")
OUT_JSON = os.path.join(ROOT, "logs", "B1_probe.json")

SEED = 20261102
EPOCHS = 6
BATCH = 4096
LR = 2e-3


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
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    meta = json.load(open(os.path.join(CACHE, "meta.json"), encoding="utf-8"))
    tokens = np.load(os.path.join(CACHE, "tokens.npy"))
    mask = np.load(os.path.join(CACHE, "mask.npy"))
    pooled = np.load(os.path.join(CACHE, "pooled.npy"))
    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]

    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    inv = {v: k for k, v in tok.get_vocab().items()}
    id_str = {i: inv.get(i, "[UNK]") for i in np.unique(tokens[mask])}

    ids = sorted(id_str)
    vmap = {tid: i for i, tid in enumerate(ids)}
    V = len(ids)
    print("vocab", V)

    # 문장 그룹: 오타는 원문과 같은 그룹
    groups = []
    for r in rows:
        groups.append(r.get("base_id", r["id"]))
    uniq = sorted(set(groups))
    rng = np.random.default_rng(SEED)
    rng.shuffle(uniq)
    n_train = int(len(uniq) * 0.8)
    train_groups = set(uniq[:n_train])
    train_sent = np.array([g in train_groups for g in groups])

    tok_cls = np.array([token_class(id_str.get(int(t), "")) for t in tokens.reshape(-1)])
    flat_tok = tokens.reshape(-1)
    flat_mask = mask.reshape(-1)
    sent_of = np.repeat(np.arange(len(rows)), tokens.shape[1])

    results = {}
    for name in meta["layers"]:
        h = np.load(os.path.join(CACHE, f"h_{name}.npy"), mmap_mode="r")
        X = np.asarray(h.reshape(-1, h.shape[-1])[flat_mask], dtype=np.float32)
        y = np.array([vmap[int(t)] for t in flat_tok[flat_mask]], dtype=np.int64)
        s = sent_of[flat_mask]
        tr = np.isin(s, np.where(train_sent)[0])
        te = ~tr

        model = nn.Linear(X.shape[1], V)
        opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
        lossf = nn.CrossEntropyLoss()
        Xt = torch.from_numpy(X[tr]); yt = torch.from_numpy(y[tr])
        n = len(Xt)
        for ep in range(EPOCHS):
            perm = torch.randperm(n)
            tot = 0.0
            for i in range(0, n, BATCH):
                idx = perm[i:i + BATCH]
                opt.zero_grad()
                out = model(Xt[idx])
                loss = lossf(out, yt[idx])
                loss.backward()
                opt.step()
                tot += float(loss) * len(idx)
            if ep == EPOCHS - 1:
                print(f"  {name} ep{ep} loss {tot/n:.4f}", flush=True)

        with torch.no_grad():
            pred = model(torch.from_numpy(X[te])).argmax(1).numpy()
        ytrue = y[te]
        cls = tok_cls[flat_mask][te]
        acc = float((pred == ytrue).mean())
        per = {}
        for c in ("number", "identifier", "other"):
            m = cls == c
            per[c] = {"n": int(m.sum()), "acc": float((pred[m] == ytrue[m]).mean()) if m.any() else None}
        results[name] = {"dim": int(X.shape[1]), "overall": acc, "classes": per}
        print(f"{name}: overall {acc:.4f} number {per['number']['acc']} id {per['identifier']['acc']}", flush=True)
        del X, y, Xt, yt, s, tr, te, model
        import gc; gc.collect()

    # 오타 민감도: pooled cosine(오타 vs 원문)
    idx = {r["id"]: i for i, r in enumerate(rows)}
    cos_typo, cos_rand = [], []
    for r in rows:
        if r["kind"] == "typo" and r.get("base_id") in idx:
            a, b = pooled[idx[r["id"]]], pooled[idx[r["base_id"]]]
            cos_typo.append(float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12)))
    rr = np.random.default_rng(SEED)
    for _ in range(len(cos_typo)):
        a, b = pooled[rr.integers(0, len(pooled))], pooled[rr.integers(0, len(pooled))]
        cos_rand.append(float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12)))

    out = {"vocab": V, "layers": results,
           "typo_pooled_cosine": {"mean": float(np.mean(cos_typo)), "n": len(cos_typo)},
           "random_pooled_cosine": {"mean": float(np.mean(cos_rand)), "n": len(cos_rand)}}
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    json.dump(out, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(out["typo_pooled_cosine"]))


if __name__ == "__main__":
    main()
