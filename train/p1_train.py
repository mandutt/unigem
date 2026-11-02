"""P1 F4 파일럿 — 선형 모델 비교 (H1/H1b/H2/H3) + H5 규칙.

H1  = l00 ±2창 ⊕ l04
H1b = H1 ⊕ 문장 평균(l04)
H2  = l00 ±2창
H3  = H2 ⊕ 어휘 특징
H5  = 혼동쌍 사전 규칙
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
CACHE = os.path.join(ROOT, "cache", "p1")
CORPUS = os.path.join(ROOT, "data", "p1", "p1_corpus.jsonl")
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
SUSPECT = {"돼었", "돼면", "돼고", "되요", "되서", "안고", "안아", "안았", "안는", "로써", "로서", "던", "든", "낫", "낳", "났"}


def load(layer):
    files = sorted(os.path.join(CACHE, "shards", f) for f in os.listdir(os.path.join(CACHE, "shards")))
    out = {}
    for p in files:
        z = np.load(p)
        h = z[layer]; ids = z["ids"]; m = z["mask"]; rw = z["row_idx"]
        for k, r in enumerate(rw):
            L = int(m[k].sum())
            out[int(r)] = h[k, :L].astype(np.float32)
    return out


def ngram_feats(s, dim=64):
    v = np.zeros(dim, np.float32)
    for n in (1, 2, 3):
        for i in range(len(s) - n + 1):
            h = int(hashlib.md5(s[i:i + n].encode()).hexdigest()[:8], 16)
            v[h % dim] += 1.0 if (h >> 8) & 1 else -1.0
    return v / max(1.0, np.linalg.norm(v))


def ap_score(y, p):
    o = np.argsort(-p)
    y = y[o]
    tp = np.cumsum(y); fp = np.cumsum(1 - y)
    prec = tp / np.maximum(1, tp + fp); rec = tp / max(1, y.sum())
    return float(np.sum(np.diff(np.concatenate([[0], rec])) * prec))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--out", default=os.path.join(ROOT, "logs", "P1_linear.json"))
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    H0, H4 = load("tok_h_l00"), load("tok_h_l04")
    print("loaded", len(H0), len(H4), flush=True)
    freq = {}
    for i, r in enumerate(rows):
        if r["split"] != "train":
            continue
        for t in tok.encode(r["text"]).ids:
            freq[int(t)] = freq.get(int(t), 0) + 1

    X, y, sp, sent, sidx, texts = {k: [] for k in ("h1", "h1b", "h2", "h3")}, [], [], [], [], []
    for i, r in enumerate(rows):
        h0, h4 = H0.get(i), H4.get(i)
        if h0 is None:
            continue
        enc = tok.encode(r["text"]); L = len(enc.ids); toks = enc.tokens
        spans = []
        if r["is_error"]:
            sm = difflib.SequenceMatcher(None, r["clean"], r["text"], autojunk=False)
            spans = [(j1, j2) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]
        lab = np.zeros(L, np.int64)
        for t, (s0, s1) in enumerate(enc.offsets):
            for a0, a1 in spans:
                if a0 < s1 and s0 < a1:
                    lab[t] = 1; break
        pooled = h4.mean(0)
        pad = np.zeros((L + 4, 512), np.float32)
        pad[2:2 + L] = h0
        base = np.concatenate([pad[o:o + L] for o in range(5)], axis=1)  # [L,2560]
        h1 = np.concatenate([base, h4], axis=1)
        h1b = np.concatenate([h1, np.broadcast_to(pooled, (L, 512))], axis=1)
        voc = np.zeros((L, 4), np.float32)
        ng = np.zeros((L, 64), np.float32)
        for t in range(L):
            s = toks[t]
            voc[t] = (np.log1p(freq.get(int(enc.ids[t]), 0)), len(s),
                      1.0 if s.isdigit() else 0.0, 1.0 if s.isascii() else 0.0)
            ng[t] = ngram_feats(s)
        h3 = np.concatenate([base, voc, ng], axis=1)
        for t in range(L):
            X["h2"].append(base[t]); X["h1"].append(h1[t]); X["h1b"].append(h1b[t]); X["h3"].append(h3[t])
            y.append(lab[t]); sp.append(r["split"]); sent.append(r["group"]); sidx.append(i); texts.append(r["text"])
    y = np.array(y); sp = np.array(sp); sent = np.array(sent); sidx = np.array(sidx); texts = np.array(texts)
    is_err_sent = np.array([rows[i]["is_error"] for i in sidx])
    tr, va, te = sp == "train", sp == "val", sp == "test"
    if not va.any():
        vg = {g for g in np.unique(sent[tr]) if int(hashlib.md5(g.encode()).hexdigest()[:8], 16) % 100 < 15}
        va = tr & np.array([g in vg for g in sent])
        tr = tr & ~va
    res = {"n_tokens": int(len(y)), "pos": int(y.sum()), "test_tokens": int(te.sum()), "models": {}}

    def fit_eval(cfg, frac=1.0):
        Xa = np.stack(X[cfg])
        tri = np.where(tr)[0]
        if frac < 1.0:
            gs = np.unique(sent[tri]); keep = set(gs[:max(1, int(len(gs) * frac))])
            tri = np.array([i for i in tri if sent[i] in keep])
        xt = torch.from_numpy(Xa[tri]); yt = torch.from_numpy(y[tri]).float()
        model = nn.Linear(Xa.shape[1], 1)
        opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
        pw = torch.tensor([(len(yt) - yt.sum()) / max(1.0, yt.sum())])
        for ep in range(a.epochs):
            perm = torch.randperm(len(xt))
            for st in range(0, len(xt), 2048):
                j = perm[st:st + 2048]; opt.zero_grad()
                loss = F.binary_cross_entropy_with_logits(model(xt[j]).squeeze(-1), yt[j], pos_weight=pw)
                loss.backward(); opt.step()
        with torch.no_grad():
            pv = torch.sigmoid(model(torch.from_numpy(Xa[va])).squeeze(-1)).numpy()
            pt = torch.sigmoid(model(torch.from_numpy(Xa[te])).squeeze(-1)).numpy()
        # 문장 점수 = 최대 토큰 확률
        def sent_scores(p, sarr):
            out = {}
            for g in np.unique(sarr):
                out[g] = float(p[sarr == g].max())
            return out
        sv = sent_scores(pv, sent[va]); st_ = sent_scores(pt, sent[te])
        err_of = {r["group"]: r["is_error"] for r in rows}
        yv = {g: int(err_of[g]) for g in sv}
        thrs = np.linspace(0.05, 0.95, 91)
        best = None
        for th in thrs:
            tp = sum(1 for g, s in sv.items() if s >= th and yv[g] == 1)
            fp = sum(1 for g, s in sv.items() if s >= th and yv[g] == 0)
            fn = sum(1 for g, s in sv.items() if s < th and yv[g] == 1)
            rec = tp / max(1, tp + fn); prec = tp / max(1, tp + fp)
            if rec >= 0.8:
                f1 = 2 * prec * rec / max(1e-9, prec + rec)
                if best is None or f1 > best[0]:
                    best = (f1, th, prec, fp)
        _, th, prec, fpnorm = best
        te_idx = np.where(te)[0]
        yte = y[te_idx]; ierr = is_err_sent[te_idx]
        r = {"auprc": ap_score(yte[ierr], pt[ierr]),
             "f1": float(2 * ((pt >= th) & (yte == 1)).sum() / max(1e-9, (pt >= th).sum() + (yte == 1).sum())),
             "sent_thr": float(th), "sent_prec_at_r80": float(prec),
             "fp_rate_normal": float(fpnorm / max(1, sum(1 for g in st_ if yv.get(g) == 0)))}
        full = np.zeros(len(y), np.float32); full[te_idx] = pt
        return r, full

    preds = {}
    for cfg in ("h1", "h1b", "h2", "h3"):
        r, p = fit_eval(cfg)
        res["models"][cfg] = r; preds[cfg] = p
        print(cfg, r, flush=True)

    # H5 규칙 점수
    te_idx_g = np.where(te)[0]; yte_g = y[te_idx_g]; ierr_g = is_err_sent[te_idx_g]
    pt = np.zeros(len(te_idx_g), np.float32)
    for k, txt in enumerate(texts[te]):
        pt[k] = 1.0 if any(s in txt for s in SUSPECT) else 0.0
    res["models"]["h5"] = {"auprc": ap_score(yte_g[ierr_g], pt[ierr_g]),
                           "note": "혼동쌍 사전만"}

    # 데이터 효율 (H1, H2)
    eff = {}
    for cfg in ("h1", "h2"):
        eff[cfg] = {}
        for frac in (0.05, 0.10, 0.25, 0.50):
            r, _ = fit_eval(cfg, frac)
            eff[cfg][str(frac)] = r["auprc"]
    res["data_efficiency"] = eff

    # 부트스트랩 ΔAUPRC (H1 - 최선 기준선)
    base = max(("h2", "h3"), key=lambda k: res["models"][k]["auprc"])
    ids = np.unique(sent[te & is_err_sent]); rng = np.random.default_rng(0)
    mask_err = te & is_err_sent
    groups = {g: np.where(mask_err & (sent == g))[0] for g in ids}
    d = []
    for _ in range(1000):
        pick = rng.choice(ids, len(ids), replace=True)
        idx = np.concatenate([groups[g] for g in pick])
        d.append(ap_score(y[idx], preds["h1"][idx]) - ap_score(y[idx], preds[base][idx]))
    res["delta_h1_vs"] = base
    res["delta_h1"] = {"point": res["models"]["h1"]["auprc"] - res["models"][base]["auprc"],
                       "ci_low": float(np.percentile(d, 2.5)), "ci_high": float(np.percentile(d, 97.5))}
    json.dump(res, open(a.out, "w", encoding="utf-8"), indent=2)
    print(json.dumps(res["delta_h1"], indent=1))


if __name__ == "__main__":
    main()
