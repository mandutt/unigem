"""P1 F4 파일럿 — 구성별 단일 프로세스 (메모리 절감).

사용: python train/p1_train_one.py --cfg h1 [--eff]
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


def load_both():
    files = sorted(os.path.join(CACHE, "shards", f) for f in os.listdir(os.path.join(CACHE, "shards")))
    H0, H4 = {}, {}
    for p in files:
        z = np.load(p)
        a0, a4, rw, mk = z["tok_h_l00"], z["tok_h_l04"], z["row_idx"], z["mask"]
        for k, r in enumerate(rw):
            L = int(mk[k].sum())
            H0[int(r)] = a0[k, :L].astype(np.float32)
            H4[int(r)] = a4[k, :L].astype(np.float32)
    return H0, H4


def ngram_feats(s, dim=64):
    v = np.zeros(dim, np.float32)
    for n in (1, 2, 3):
        for i in range(len(s) - n + 1):
            h = int(hashlib.md5(s[i:i + n].encode()).hexdigest()[:8], 16)
            v[h % dim] += 1.0 if (h >> 8) & 1 else -1.0
    return v / max(1.0, np.linalg.norm(v))


def ap_score(y, p):
    o = np.argsort(-p); y = y[o]
    tp = np.cumsum(y); fp = np.cumsum(1 - y)
    prec = tp / np.maximum(1, tp + fp); rec = tp / max(1, y.sum())
    return float(np.sum(np.diff(np.concatenate([[0], rec])) * prec))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cfg", required=True, choices=["h1", "h1b", "h2", "h3"])
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--eff", action="store_true")
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    H0, H4 = load_both()
    print("loaded", len(H0), flush=True)
    freq = {}
    for r in rows:
        if r["split"] != "train":
            continue
        for t in tok.encode(r["text"]).ids:
            freq[int(t)] = freq.get(int(t), 0) + 1

    mats, ys, sps, sents, sidx = [], [], [], [], []
    for i, r in enumerate(rows):
        h0, h4 = H0.get(i), H4.get(i)
        if h0 is None:
            continue
        enc = tok.encode(r["text"]); L = len(enc.ids)
        spans = []
        if r["is_error"]:
            sm = difflib.SequenceMatcher(None, r["clean"], r["text"], autojunk=False)
            spans = [(j1, j2) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]
        lab = np.zeros(L, np.int64)
        for t, (s0, s1) in enumerate(enc.offsets):
            for a0, a1 in spans:
                if a0 < s1 and s0 < a1:
                    lab[t] = 1; break
        pad = np.zeros((L + 4, 512), np.float32); pad[2:2 + L] = h0
        base = np.concatenate([pad[o:o + L] for o in range(5)], axis=1)
        if a.cfg == "h2":
            m = base
        elif a.cfg == "h1":
            m = np.concatenate([base, h4], axis=1)
        elif a.cfg == "h1b":
            m = np.concatenate([base, h4, np.broadcast_to(h4.mean(0), (L, 512))], axis=1)
        else:
            voc = np.zeros((L, 4), np.float32); ng = np.zeros((L, 64), np.float32)
            for t, s in enumerate(enc.tokens):
                voc[t] = (np.log1p(freq.get(int(enc.ids[t]), 0)), len(s),
                          1.0 if s.isdigit() else 0.0, 1.0 if s.isascii() else 0.0)
                ng[t] = ngram_feats(s)
            m = np.concatenate([base, voc, ng], axis=1)
        mats.append(m); ys.append(lab)
        sps.append(np.repeat(r["split"], L)); sents.append(np.repeat(r["group"], L))
        sidx.append(np.repeat(i, L))
    X = np.concatenate(mats, axis=0); y = np.concatenate(ys)
    sp = np.concatenate(sps); sent = np.concatenate(sents); sidx = np.concatenate(sidx)
    del mats, ys
    print("tokens", X.shape, "pos", int(y.sum()), flush=True)
    is_err = np.array([bool(rows[i]["is_error"]) for i in sidx])
    tr, va, te = sp == "train", sp == "val", sp == "test"
    vg = {g for g in np.unique(sent[tr]) if int(hashlib.md5(g.encode()).hexdigest()[:8], 16) % 100 < 15}
    va = tr & np.isin(sent, list(vg)); tr = tr & ~va
    err_of = {r["group"]: r["is_error"] for r in rows}

    def fit_eval(frac=1.0):
        tri = np.where(tr)[0]
        if frac < 1.0:
            gs = np.unique(sent[tri]); keep = set(gs[:max(1, int(len(gs) * frac))])
            tri = np.array([i for i in tri if sent[i] in keep])
        xt = torch.from_numpy(X[tri]); yt = torch.from_numpy(y[tri]).float()
        model = nn.Linear(X.shape[1], 1)
        opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
        pw = torch.tensor([(len(yt) - yt.sum()) / max(1.0, yt.sum())])
        for ep in range(a.epochs):
            perm = torch.randperm(len(xt))
            for st in range(0, len(xt), 2048):
                j = perm[st:st + 2048]; opt.zero_grad()
                loss = F.binary_cross_entropy_with_logits(model(xt[j]).squeeze(-1), yt[j], pos_weight=pw)
                loss.backward(); opt.step()
        with torch.no_grad():
            pv = torch.sigmoid(model(torch.from_numpy(X[va])).squeeze(-1)).numpy()
            pt = torch.sigmoid(model(torch.from_numpy(X[te])).squeeze(-1)).numpy()
        sv = {}
        for g in np.unique(sent[va]):
            sv[g] = float(pv[sent[va] == g].max())
        best = None
        for th in np.linspace(0.05, 0.95, 91):
            tp = sum(1 for g, s in sv.items() if s >= th and err_of[g])
            fp = sum(1 for g, s in sv.items() if s >= th and not err_of[g])
            fn = sum(1 for g, s in sv.items() if s < th and err_of[g])
            rec = tp / max(1, tp + fn); prec = tp / max(1, tp + fp)
            if rec >= 0.8:
                f1 = 2 * prec * rec / max(1e-9, prec + rec)
                if best is None or f1 > best[0]:
                    best = (f1, th, prec, fp)
        _, th, prec, fpnorm = best
        te_idx = np.where(te)[0]; yte = y[te_idx]; ierr = is_err[te_idx]
        st_ = {g: float(pt[sent[te] == g].max()) for g in np.unique(sent[te])}
        return {"auprc": ap_score(yte[ierr], pt[ierr]),
                "f1": float(2 * ((pt >= th) & (yte == 1)).sum() / max(1e-9, (pt >= th).sum() + (yte == 1).sum())),
                "sent_thr": float(th), "sent_prec_at_r80": float(prec),
                "fp_rate_normal": float(fpnorm / max(1, sum(1 for g in sv if not err_of[g])))}, pt, te_idx

    r, pt, te_idx = fit_eval()
    print(a.cfg, r, flush=True)
    np.savez(os.path.join(ROOT, "logs", f"P1_{a.cfg}_pred.npz"), pt=pt, y=y[te_idx],
             ierr=is_err[te_idx], sent=sent[te_idx])
    out = {"cfg": a.cfg, "result": r, "n": int(X.shape[0])}
    if a.eff:
        out["efficiency"] = {}
        for frac in (0.05, 0.10, 0.25, 0.50):
            rr, _, _ = fit_eval(frac)
            out["efficiency"][str(frac)] = rr["auprc"]
            print("eff", frac, rr["auprc"], flush=True)
    json.dump(out, open(os.path.join(ROOT, "logs", f"P1_{a.cfg}.json"), "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main()
