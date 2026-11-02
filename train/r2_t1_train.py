"""R2 T1 확장 — BL-0/BL-1/BL-2/l04 동일 용량 비교.

- 라벨: clean↔noisy 문자 정렬로 바뀐 구간에 속한 noisy 토큰
- BL-2: BL-1 + 어휘 특징(토큰 빈도 log, 길이, 숫자/라틴, 문자 n-gram 해시 64)
- 지표: F1/AUPRC, P@R80, 문장 부트스트랩 ΔF1(l04−BL-1)
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from tokenizers import Tokenizer

ROOT = r"C:\code\unigem"
CACHE = os.path.join(ROOT, "cache", "r2_t1")
CORPUS = os.path.join(ROOT, "data", "r2", "t1_corpus.jsonl")
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


def char_spans(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return [(j1, j2) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]


def ngram_feats(s, dim=64):
    v = np.zeros(dim, np.float32)
    for n in (1, 2, 3):
        for i in range(len(s) - n + 1):
            h = int(hashlib.md5(s[i:i + n].encode()).hexdigest()[:8], 16)
            v[h % dim] += 1.0 if (h >> 8) & 1 else -1.0
    return v / max(1.0, np.linalg.norm(v))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--bs", type=int, default=2048)
    ap.add_argument("--out", default=os.path.join(ROOT, "logs", "R2_t1.json"))
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    idx_of = {id(r): i for i, r in enumerate(rows)}
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    H0, H4 = load("tok_h_l00"), load("tok_h_l04")

    by_group = {}
    for r in rows:
        by_group.setdefault(r["group"], {})[r["kind"]] = r

    # 어휘 빈도 (train noisy 토큰)
    freq = {}
    for g, d in by_group.items():
        if "typo_noisy" not in d:
            continue
        r = d["typo_noisy"]
        if r["split"] != "train":
            continue
        for t in tok.encode(r["text"]).ids:
            freq[int(t)] = freq.get(int(t), 0) + 1

    X, y, sent, split = [], [], [], []
    for g, d in by_group.items():
        if "typo_clean" not in d or "typo_noisy" not in d:
            continue
        clean, noisy = d["typo_clean"], d["typo_noisy"]
        i = idx_of[id(noisy)]
        h0, h4 = H0.get(i), H4.get(i)
        if h0 is None:
            continue
        enc = tok.encode(noisy["text"])
        spans = char_spans(clean["text"], noisy["text"])
        lab = np.zeros(len(enc.ids), np.int64)
        for t, (s0, s1) in enumerate(enc.offsets):
            for a0, a1 in spans:
                if a0 < s1 and s0 < a1:
                    lab[t] = 1
                    break
        L = len(enc.ids)
        for t in range(L):
            win = [h0[u] if 0 <= u < L else np.zeros(512, np.float32) for u in range(t - 2, t + 3)]
            base = np.concatenate(win)
            tid = int(enc.ids[t])
            s = tok.decode([tid])
            vocab_feat = np.array([
                np.log1p(freq.get(tid, 0)), len(s), 1.0 if s.isdigit() else 0.0,
                1.0 if any(c.isascii() and c.isalpha() for c in s) else 0.0,
            ], np.float32)
            X.append({
                "bl0": h0[t].copy(),
                "bl1": base,
                "bl2": np.concatenate([base, vocab_feat, ngram_feats(s)]),
                "l04": np.concatenate([base, h4[t]]),
            })
            y.append(lab[t]); sent.append(g); split.append(noisy["split"])

    y = np.array(y); split = np.array(split); sent = np.array(sent)
    print("tokens", len(y), "pos", int(y.sum()), "test", int((split == "test").sum()), flush=True)
    res = {"n_tokens": int(len(y)), "pos": int(y.sum()), "configs": {}}
    tr, va, te = split == "train", split == "val", split == "test"

    def train_eval(x, tag):
        Xa = np.stack(x)
        xt = torch.from_numpy(Xa[tr]); yt = torch.from_numpy(y[tr]).float()
        model = nn.Linear(Xa.shape[1], 1)
        opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
        pw = torch.tensor([(len(yt) - yt.sum()) / max(1.0, yt.sum())])
        for ep in range(a.epochs):
            perm = torch.randperm(len(xt))
            for st in range(0, len(xt), a.bs):
                j = perm[st:st + a.bs]; opt.zero_grad()
                loss = F.binary_cross_entropy_with_logits(model(xt[j]).squeeze(-1), yt[j], pos_weight=pw)
                loss.backward(); opt.step()
        with torch.no_grad():
            pv = torch.sigmoid(model(torch.from_numpy(Xa[va])).squeeze(-1)).numpy()
            pt = torch.sigmoid(model(torch.from_numpy(Xa[te])).squeeze(-1)).numpy()
        yo = np.argsort(-pv); tp = np.cumsum(y[va][yo]); fp = np.cumsum(1 - y[va][yo])
        pr = tp / np.maximum(1, tp + fp); rc = tp / max(1, 1e-9 + y[va].sum())
        f1 = 2 * pr * rc / np.maximum(1e-9, pr + rc)
        thr = float(pv[yo][int(np.argmax(f1))])
        pred = pt >= thr
        yy = y[te]
        f1t = 2 * pred[yy == 1].sum() / max(1e-9, pred.sum() + (yy == 1).sum())
        o = np.argsort(-pt); tp2 = np.cumsum(yy[o]); fp2 = np.cumsum(1 - yy[o])
        auprc = float(np.sum((tp2 / max(1, yy.sum()) - np.concatenate([[0], (tp2 / max(1, yy.sum()))[:-1]])) *
                             (tp2 / np.maximum(1, tp2 + fp2))))
        res["configs"][tag] = {"f1": float(f1t), "auprc": auprc, "thr": thr, "n_test": int(len(yy))}
        print(tag, res["configs"][tag], flush=True)
        return pt

    preds = {}
    for tag in ("bl0", "bl1", "bl2", "l04"):
        preds[tag] = train_eval([x[tag] for x in X], tag)

    # 문장 부트스트랩 ΔF1
    def f1_at(p, yy, thr):
        pr = p >= thr
        tp = (pr & (yy == 1)).sum(); return 2 * tp / max(1e-9, pr.sum() + (yy == 1).sum())
    ids = np.unique(sent[te]); groups = {s: np.where(sent[te] == s)[0] for s in ids}
    rng = np.random.default_rng(0)
    deltas = []
    for _ in range(1000):
        pick = rng.choice(ids, len(ids), replace=True)
        idx = np.concatenate([groups[s] for s in pick])
        deltas.append(f1_at(preds["l04"][idx], y[te][idx], res["configs"]["l04"]["thr"]) -
                      f1_at(preds["bl1"][idx], y[te][idx], res["configs"]["bl1"]["thr"]))
    d = np.array(deltas)
    res["delta_l04_bl1"] = {"point": float(res["configs"]["l04"]["f1"] - res["configs"]["bl1"]["f1"]),
                            "ci_low": float(np.percentile(d, 2.5)), "ci_high": float(np.percentile(d, 97.5))}
    res["delta_l04_bl2"] = float(res["configs"]["l04"]["f1"] - res["configs"]["bl2"]["f1"])
    json.dump(res, open(a.out, "w", encoding="utf-8"), indent=2)
    print(json.dumps(res["delta_l04_bl1"], indent=1))


if __name__ == "__main__":
    main()
