"""P1 F4 파일럿 — H4 BiGRU (문자 단위, 2×128, ≤2M)."""
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
CORPUS = os.path.join(ROOT, "data", "p1", "p1_corpus.jsonl")
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")


def ap_score(y, p):
    o = np.argsort(-p); y = y[o]
    tp = np.cumsum(y); fp = np.cumsum(1 - y)
    prec = tp / np.maximum(1, tp + fp); rec = tp / max(1, y.sum())
    return float(np.sum(np.diff(np.concatenate([[0], rec])) * prec))


class Net(nn.Module):
    def __init__(self, vocab, emb=96, hid=128):
        super().__init__()
        self.emb = nn.Embedding(vocab, emb, padding_idx=0)
        self.gru = nn.GRU(emb, hid, num_layers=1, bidirectional=True, batch_first=True)
        self.out = nn.Linear(2 * hid, 1)

    def forward(self, x):
        h, _ = self.gru(self.emb(x))
        return self.out(h).squeeze(-1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--out", default=os.path.join(ROOT, "logs", "P1_bigru.json"))
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    chars = ["<pad>"] + sorted({c for r in rows for c in r["text"]})
    c2i = {c: i for i, c in enumerate(chars)}

    samples = []
    for r in rows:
        enc = tok.encode(r["text"])
        spans = []
        if r["is_error"]:
            sm = difflib.SequenceMatcher(None, r["clean"], r["text"], autojunk=False)
            spans = [(j1, j2) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]
        clab = np.zeros(len(r["text"]), np.float32)
        for j in range(len(r["text"])):
            for a0, a1 in spans:
                if a0 <= j < a1:
                    clab[j] = 1; break
        ids = [c2i[c] for c in r["text"]]
        # 토큰별 문자 인덱스
        tidx = []
        for s0, s1 in enc.offsets:
            tidx.append(list(range(s0, min(s1, len(r["text"])))))
        samples.append({"ids": ids, "clab": clab, "tidx": tidx, "split": r["split"], "group": r["group"],
                        "is_err": r["is_error"], "ntok": len(enc.ids)})

    tr = [s for s in samples if s["split"] == "train"]
    te = [s for s in samples if s["split"] == "test"]
    import hashlib
    def is_val(s):
        return int(hashlib.md5(s["group"].encode()).hexdigest()[:8], 16) % 100 < 15
    va = [s for s in tr if is_val(s)]
    tr = [s for s in tr if not is_val(s)]
    model = Net(len(chars))
    print("params", sum(p.numel() for p in model.parameters()), flush=True)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-2)
    pw = torch.tensor([5.0])
    for ep in range(a.epochs):
        model.train(); order = np.random.permutation(len(tr)); tot = 0.0
        for k in order:
            s = tr[k]
            x = torch.tensor([s["ids"]]); y = torch.tensor(s["clab"]).unsqueeze(0)
            opt.zero_grad()
            loss = F.binary_cross_entropy_with_logits(model(x), y, pos_weight=pw)
            loss.backward(); opt.step(); tot += float(loss)
        print("ep", ep, round(tot / len(tr), 4), flush=True)

    def infer(data):
        model.eval(); outs = []
        with torch.no_grad():
            for s in data:
                if not s["ids"]:
                    outs.append(np.zeros(s["ntok"])); continue
                cp = torch.sigmoid(model(torch.tensor([s["ids"]]))).squeeze(0).numpy()
                tp = np.array([cp[ix].max() if ix else 0.0 for ix in s["tidx"]])
                outs.append(tp)
        return outs

    def eval_split(data):
        ps = infer(data); ys = []
        for s, p in zip(data, ps):
            y = np.zeros(len(p), np.int64)
            for t, ix in enumerate(s["tidx"]):
                if any(s["clab"][j] > 0 for j in ix):
                    y[t] = 1
            ys.append(y)
        return ps, ys

    pv, yv = eval_split(va); pt, yt = eval_split(te)
    # 문장 임계값
    best = None
    for th in np.linspace(0.05, 0.95, 91):
        tp = sum(1 for s, p in zip(va, pv) if p.max() >= th and s["is_err"])
        fp = sum(1 for s, p in zip(va, pv) if p.max() >= th and not s["is_err"])
        fn = sum(1 for s, p in zip(va, pv) if p.max() < th and s["is_err"])
        rec = tp / max(1, tp + fn); prec = tp / max(1, tp + fp)
        if rec >= 0.8:
            f1 = 2 * prec * rec / max(1e-9, prec + rec)
            if best is None or f1 > best[0]:
                best = (f1, th, prec, fp)
    _, th, prec, fpnorm = best
    flat_p = np.concatenate([p for s, p in zip(te, pt) if s["is_err"]])
    flat_y = np.concatenate([y for s, y in zip(te, yt) if s["is_err"]])
    res = {"params": sum(p.numel() for p in model.parameters()),
           "auprc": ap_score(flat_y, flat_p), "sent_thr": float(th),
           "sent_prec_at_r80": float(prec),
           "fp_rate_normal": float(fpnorm / max(1, sum(1 for s in va if not s["is_err"])))}
    json.dump(res, open(a.out, "w", encoding="utf-8"), indent=2)
    print(res)


if __name__ == "__main__":
    main()
