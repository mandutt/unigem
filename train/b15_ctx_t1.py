"""B1.5-3 — 문맥 가치 테스트 (T1: 오타 토큰 탐지).

- 데이터: 코퍼스 v2의 typo_clean/typo_noisy 쌍 (그룹 동일)
- 라벨: clean↔noisy 문자 정렬(difflib)로 바뀐 구간에 속한 noisy 토큰 = 1
- 특징: 층별 hidden, BL-0=l00 단일 토큰, BL-1=l00 ±2창 연결
- 지표: 토큰 F1, AUPRC, 문장 단위 탐지 precision@recall0.8, 문장 클러스터 부트스트랩 CI
"""
from __future__ import annotations

import argparse
import difflib
import json
import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from tokenizers import Tokenizer

ROOT = r"C:\code\unigem"
CACHE = os.path.join(ROOT, "cache", "b1_5")
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
CORPUS = os.path.join(ROOT, "data", "b1_5", "corpus_v2", "corpus.jsonl")


def load_shards(layer: str):
    files = sorted(os.path.join(CACHE, "shards", f) for f in os.listdir(os.path.join(CACHE, "shards")))
    out = {}
    for p in files:
        z = np.load(p)
        h = z[layer]
        for k, r in enumerate(z["row_idx"]):
            L = int(z["mask"][k].sum())
            out[int(r)] = h[k, :L].astype(np.float32)
    return out


def char_spans(clean: str, noisy: str):
    sm = difflib.SequenceMatcher(None, clean, noisy, autojunk=False)
    spans = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            spans.append((j1, j2))
    return spans


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layer", default="tok_h_l00")
    ap.add_argument("--bl0", action="store_true", help="l00 단일 토큰만 사용")
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--bs", type=int, default=2048)
    ap.add_argument("--out", default=os.path.join(ROOT, "logs", "B1_5_T1.json"))
    ap.add_argument("--save", default="")
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    by_group = {}
    for r in rows:
        by_group.setdefault(r["group"], {})[r["kind"]] = r
    pairs = [(g, d["typo_clean"], d["typo_noisy"]) for g, d in by_group.items()
             if "typo_clean" in d and "typo_noisy" in d]
    print("pairs", len(pairs), flush=True)

    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    H = load_shards(a.layer)
    H0 = load_shards("tok_h_l00") if a.layer != "tok_h_l00" else H

    # row_idx == corpus 인덱스
    idx_of = {id(r): i for i, r in enumerate(rows)}

    X, y, grp, sidx = [], [], [], []
    for g, clean, noisy in pairs:
        i = idx_of[id(noisy)]
        h = H.get(i)
        if h is None:
            continue
        enc = tok.encode(noisy["text"])
        ids, offs = enc.ids, enc.offsets
        spans = char_spans(clean["text"], noisy["text"])
        lab = np.zeros(len(ids), np.int64)
        for t, (a0, a1) in enumerate(offs):
            for s0, s1 in spans:
                if a0 < s1 and s0 < a1:
                    lab[t] = 1
                    break
        h0 = H0.get(i)
        for t in range(len(ids)):
            win = []
            for d in range(-2, 3):
                u = t + d
                win.append(h0[u] if 0 <= u < len(h0) else np.zeros(h0.shape[1], np.float32))
            X.append(h0[t].copy() if a.bl0 else
                     (np.concatenate([np.concatenate(win), h[t]]) if a.layer != "tok_h_l00" else np.concatenate(win)))
            y.append(lab[t])
            grp.append(g)
            sidx.append(noisy["split"])
    X = np.stack(X).astype(np.float32)
    y = np.array(y, np.int64)
    sidx = np.array(sidx)
    print("tokens", X.shape, "pos", int(y.sum()), flush=True)

    def train_eval(tr, te, tag):
        xt = torch.from_numpy(X[tr]); yt = torch.from_numpy(y[tr]).float()
        model = nn.Linear(X.shape[1], 1)
        opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
        pos_weight = torch.tensor([(len(yt) - yt.sum()) / max(1.0, yt.sum())])
        for ep in range(a.epochs):
            perm = torch.randperm(len(xt))
            for st in range(0, len(xt), a.bs):
                j = perm[st:st + a.bs]
                opt.zero_grad()
                logit = model(xt[j]).squeeze(-1)
                loss = F.binary_cross_entropy_with_logits(logit, yt[j], pos_weight=pos_weight)
                loss.backward()
                opt.step()
        with torch.no_grad():
            p = torch.sigmoid(model(torch.from_numpy(X[te])).squeeze(-1)).numpy()
        return p

    tr_m = sidx == "train"
    va_m = sidx == "val"
    te_m = sidx == "test"
    p_va = train_eval(tr_m, va_m, "val")
    p = train_eval(tr_m, te_m, "test")
    yy = y[te_m]
    yv = y[va_m]

    def best_thr(pv, ytrue):
        o = np.argsort(-pv)
        tp = np.cumsum(ytrue[o]); fp = np.cumsum(1 - ytrue[o])
        pr = tp / np.maximum(1, tp + fp); rc = tp / max(1, ytrue.sum())
        f1 = 2 * pr * rc / np.maximum(1e-9, pr + rc)
        return float(pv[o][int(np.argmax(f1))])

    thr = best_thr(p_va, yv)
    pred = p >= thr
    tp = int((pred & (yy == 1)).sum()); fp = int((pred & (yy == 0)).sum()); fn = int((~pred & (yy == 1)).sum())
    prec_b = tp / max(1, tp + fp); rec_b = tp / max(1, tp + fn)
    f1_best = 2 * prec_b * rec_b / max(1e-9, prec_b + rec_b)
    f1 = 2 * prec_b * rec_b / max(1e-9, prec_b + rec_b)
    # AUPRC (threshold-free)
    o = np.argsort(-p)
    tp_c = np.cumsum(yy[o]); fp_c = np.cumsum(1 - yy[o])
    prec = tp_c / np.maximum(1, tp_c + fp_c); rec = tp_c / max(1, yy.sum())
    auprc = float(np.sum((rec - np.concatenate([[0], rec[:-1]])) * prec))
    res = {"task": "T1", "layer": a.layer, "test_tokens": int(len(yy)), "pos": int(yy.sum()),
           "f1": float(f1), "precision": float(prec_b), "recall": float(rec_b), "auprc": auprc,
           "threshold": float(thr), "threshold_source": "val"}
    print(json.dumps(res, indent=1), flush=True)

    # 문장 단위 탐지 precision @ recall 0.8 (문장 내 max prob)
    sent_ids = np.array(grp)[te_m]
    sent_true = np.zeros(len(sent_ids), bool)
    for s in np.unique(sent_ids):
        m = sent_ids == s
        sent_true[m] = yy[m].sum() > 0
    # 문장별 최대 확률
    uniq = {s: i for i, s in enumerate(np.unique(sent_ids))}
    sp = np.zeros(len(uniq)); st = np.zeros(len(uniq), bool)
    for s, i in uniq.items():
        m = sent_ids == s
        sp[i] = p[m].max(); st[i] = sent_true[m][0]
    o = np.argsort(-sp)
    tp2 = np.cumsum(st[o]); fp2 = np.cumsum(~st[o])
    pr2 = tp2 / np.maximum(1, tp2 + fp2); rc2 = tp2 / max(1, st.sum())
    j = int(np.argmin(np.abs(rc2 - 0.8)))
    res["sent_precision_at_recall80"] = float(pr2[j])
    res["sent_recall_at_that_point"] = float(rc2[j])
    if a.save:
        np.savez(a.save, p=p, y=yy, sent=sent_ids)
    json.dump(res, open(a.out, "w", encoding="utf-8"), indent=2)
    print("saved", a.out, flush=True)


if __name__ == "__main__":
    main()
