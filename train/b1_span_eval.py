"""B1 보강 — 식별자 span 단위 복원 평가.

문제: Gemma 토크나이저는 `eg2-q8` 같은 식별자를 문자/숫자 서브워드로 분해하므로
"식별자 토큰" 클래스가 존재하지 않는다.

해결: 문자 오프셋으로 식별자 구간(span)을 잡고, 그 구간을 덮는 **모든 토큰이 정확히
복원됐는지**(span exact match)를 측정한다. 문장 단위 분할(80/20)로 학습/평가를 나눈다.

사용: python train/b1_span_eval.py --layers tok_h_l00,tok_h_l04,tok_h_last --epochs 20
"""
from __future__ import annotations

import argparse
import json
import os
import re

import numpy as np
import torch
import torch.nn as nn
from tokenizers import Tokenizer

ROOT = r"C:\code\unigem"
CACHE = os.path.join(ROOT, "cache", "b1")
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
CORPUS = os.path.join(ROOT, "data", "b1", "corpus.jsonl")
SEED = 20261102
MAXLEN = 64

PATTERNS = [
    ("token", re.compile(r"tok_[0-9a-f]{6}")),
    ("sha", re.compile(r"\b[0-9a-f]{8}\b")),
    ("version", re.compile(r"v\d+\.\d+\.\d+")),
    ("path", re.compile(r"(?:[A-Za-z]:)?(?:/[\w.\-]+){2,}")),
    ("errcode", re.compile(r"\bE\d{4}\b")),
    ("host", re.compile(r"\b(?:gpu|node|db|cache|eg2)-[a-z0-9]+\b")),
    ("model", re.compile(r"\b(?:eg2-q8|komixv2|whisper-turbo|qwen3-vl-2b)\b")),
    ("date", re.compile(r"\d{4}-\d{2}-\d{2}")),
]


def spans_of(text: str):
    spans = []
    for kind, pat in PATTERNS:
        for m in pat.finditer(text):
            s, e = m.span()
            if any(not (e <= a or s >= b) for _, a, b, _ in spans):
                continue
            spans.append((kind, s, e, m.group(0)))
    return spans


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", required=True)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--lr", type=float, default=3e-3)
    args = ap.parse_args()
    names = [x for x in args.layers.split(",") if x]

    torch.manual_seed(SEED)
    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    tokens = np.load(os.path.join(CACHE, "tokens.npy"))
    mask = np.load(os.path.join(CACHE, "mask.npy"))
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    inv = {v: k for k, v in tok.get_vocab().items()}

    # 토큰 오프셋 재계산
    offsets = []
    for r in rows:
        enc = tok.encode(r["text"])
        offsets.append(enc.offsets[:MAXLEN])

    # 문장 그룹 분할 (오타-원문 동일 그룹)
    groups = [r.get("base_id", r["id"]) for r in rows]
    uniq = sorted(set(groups))
    rng = np.random.default_rng(SEED)
    rng.shuffle(uniq)
    train_groups = set(uniq[: int(len(uniq) * 0.8)])
    sent_train = np.array([g in train_groups for g in groups])

    ids = sorted({int(t) for t in tokens[mask]})
    vmap = {t: i for i, t in enumerate(ids)}
    flat_tok = tokens.reshape(-1)
    flat_mask = mask.reshape(-1)
    sent_of = np.repeat(np.arange(len(rows)), tokens.shape[1])
    y = np.array([vmap[int(t)] for t in flat_tok[flat_mask]], dtype=np.int64)

    Xs = []
    for n in names:
        h = np.load(os.path.join(CACHE, f"h_{n}.npy"), mmap_mode="r")
        Xs.append(np.asarray(h.reshape(-1, h.shape[-1])[flat_mask], dtype=np.float32))
    X = np.concatenate(Xs, axis=1)

    tr = sent_train[sent_of[flat_mask]]
    print(f"layers {names} dim {X.shape[1]} vocab {len(ids)} train {tr.sum()} eval_sent {int((~sent_train).sum())}", flush=True)

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
    with torch.no_grad():
        pred = model(torch.from_numpy(X)).argmax(1).numpy()

    # 토큰 위치 → 예측
    pred_by_pos = {}
    k = 0
    for si in range(len(rows)):
        for j in range(tokens.shape[1]):
            if mask[si, j]:
                pred_by_pos[(si, j)] = ids[int(pred[k])]
                k += 1

    # span 평가
    stats = {}
    tok_stats = {}
    for si, r in enumerate(rows):
        if sent_train[si]:
            continue
        for kind, s, e, val in spans_of(r["text"]):
            idxs = []
            for j, (a, b) in enumerate(offsets[si]):
                if j >= MAXLEN or not mask[si, j]:
                    continue
                if a == b == 0:
                    continue
                if a < e and b > s:
                    idxs.append(j)
            if not idxs:
                continue
            ok_all = all(pred_by_pos.get((si, j)) == int(tokens[si, j]) for j in idxs)
            st = stats.setdefault(kind, {"n": 0, "ok": 0})
            st["n"] += 1
            st["ok"] += int(ok_all)
            for j in idxs:
                ts = tok_stats.setdefault(kind, {"n": 0, "ok": 0})
                ts["n"] += 1
                ts["ok"] += int(pred_by_pos.get((si, j)) == int(tokens[si, j]))

    out = {"layers": names, "dim": int(X.shape[1]), "epochs": args.epochs, "split": "sentence",
           "spans": {k: {"n": v["n"], "exact": v["ok"] / v["n"]} for k, v in sorted(stats.items())},
           "tokens": {k: {"n": v["n"], "acc": v["ok"] / v["n"]} for k, v in sorted(tok_stats.items())}}
    total = {"n": sum(v["n"] for v in stats.values()), "ok": sum(v["ok"] for v in stats.values())}
    out["total"] = {"n": total["n"], "exact": total["ok"] / total["n"] if total["n"] else None}
    print(json.dumps(out, ensure_ascii=False), flush=True)
    with open(os.path.join(ROOT, "logs", "B1_span.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
