"""B1.5-3 — T2: 한국어 띄어쓰기 오류 탐지 (특징 1회 추출 후 3개 기준선 평가).

원문(공백 있음) → 공백 전부 제거 → 토큰 시작 위치가 원래 단어 경계인지 라벨링.
BL-0=l00 단일, BL-1=l00 ±2창, L=l04(+l00창).
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import onnxruntime as ort
import torch
import torch.nn as nn
import torch.nn.functional as F
from tokenizers import Tokenizer

ROOT = r"C:\code\unigem"
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
ONNX = os.path.join(ROOT, "onnx", "eg2_text_research_fp32.onnx")
CORPUS = os.path.join(ROOT, "data", "b1_5", "corpus_v2", "corpus.jsonl")
CACHE = os.path.join(ROOT, "cache", "b1_5", "t2_feats.npz")
MAXLEN = 192


def extract(texts, tok, sess, names):
    H0 = np.zeros((len(texts), MAXLEN, 512), np.float16)
    HL = np.zeros_like(H0)
    empty = np.zeros((0, 512), np.float32)
    for st in range(0, len(texts), 16):
        batch = texts[st:st + 16]
        ids = np.zeros((len(batch), MAXLEN), np.int64); am = np.zeros_like(ids)
        for i, t in enumerate(batch):
            seq = tok.encode(t).ids[:MAXLEN]
            ids[i, :len(seq)] = seq; am[i, :len(seq)] = 1
        out = dict(zip(names, sess.run(None, {"input_ids": ids, "attention_mask": am,
                                               "image_features": empty, "video_features": empty, "audio_features": empty})))
        H0[st:st + len(batch)] = out["tok_h_l00"].astype(np.float16)
        HL[st:st + len(batch)] = out["tok_h_l04"].astype(np.float16)
        if st % 320 == 0:
            print("extract", st, flush=True)
    return H0, HL


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--bs", type=int, default=2048)
    ap.add_argument("--outdir", default=os.path.join(ROOT, "logs"))
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    ko = [r for r in rows if r["lang"] == "ko_kr" and " " in r["text"] and r["kind"] != "typo_noisy"]
    texts = [r["text"].replace(" ", "") for r in ko]
    print("sentences", len(ko), flush=True)
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    if os.path.exists(CACHE):
        z = np.load(CACHE)
        H0, HL = z["H0"], z["HL"]
    else:
        so = ort.SessionOptions(); so.intra_op_num_threads = 6; so.log_severity_level = 3
        sess = ort.InferenceSession(ONNX, so, providers=["CPUExecutionProvider"])
        names = [o.name for o in sess.get_outputs()]
        H0, HL = extract(texts, tok, sess, names)
        np.savez_compressed(CACHE, H0=H0, HL=HL)

    # 라벨 + 문장 id
    labels, sent_ids = [], []
    for si, (r, t) in enumerate(zip(ko, texts)):
        enc = tok.encode(t); L = int(min(len(enc.ids), MAXLEN))
        nz = [j for j, ch in enumerate(r["text"]) if ch != " "]
        lab = np.zeros(L, np.int64)
        for k, (s0, s1) in enumerate(enc.offsets[:L]):
            if k == 0 or s0 >= len(nz):
                continue
            o = nz[s0]
            lab[k] = 1 if (o > 0 and r["text"][o - 1] == " ") else 0
        labels.append(lab)
        sent_ids.append(np.full(L, si, np.int32))

    for cfg in ("bl0", "bl1", "l04"):
        X, y, sidx, sent = [], [], [], []
        for i, (r, lab) in enumerate(zip(ko, labels)):
            L = len(lab)
            for k in range(L):
                if cfg == "bl0":
                    x = H0[i, k].astype(np.float32)
                else:
                    win = [H0[i, u].astype(np.float32) if 0 <= u < L else np.zeros(512, np.float32)
                           for u in range(k - 2, k + 3)]
                    x = np.concatenate(win + ([HL[i, k].astype(np.float32)] if cfg == "l04" else []))
                X.append(x); y.append(lab[k]); sidx.append(r["split"]); sent.append(sent_ids[i][k])
        X = np.stack(X); y = np.array(y, np.int64); sidx = np.array(sidx); sent = np.array(sent)
        print(cfg, X.shape, "pos", int(y.sum()), flush=True)

        tr = sidx == "train"; va = sidx == "val"; te = sidx == "test"
        xt = torch.from_numpy(X[tr]); yt = torch.from_numpy(y[tr]).float()
        model = nn.Linear(X.shape[1], 1)
        opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
        pw = torch.tensor([(len(yt) - yt.sum()) / max(1.0, yt.sum())])
        for ep in range(a.epochs):
            perm = torch.randperm(len(xt))
            for st in range(0, len(xt), a.bs):
                j = perm[st:st + a.bs]; opt.zero_grad()
                loss = F.binary_cross_entropy_with_logits(model(xt[j]).squeeze(-1), yt[j], pos_weight=pw)
                loss.backward(); opt.step()
        with torch.no_grad():
            p_va = torch.sigmoid(model(torch.from_numpy(X[va])).squeeze(-1)).numpy()
            p = torch.sigmoid(model(torch.from_numpy(X[te])).squeeze(-1)).numpy()
        yv, yy = y[va], y[te]

        def best_thr(pv, ytrue):
            o = np.argsort(-pv); tp = np.cumsum(ytrue[o]); fp = np.cumsum(1 - ytrue[o])
            pr = tp / np.maximum(1, tp + fp); rc = tp / max(1, ytrue.sum())
            f1 = 2 * pr * rc / np.maximum(1e-9, pr + rc)
            return float(pv[o][int(np.argmax(f1))])
        thr = best_thr(p_va, yv)
        pred = p >= thr
        tp = int((pred & (yy == 1)).sum()); fp = int((pred & (yy == 0)).sum()); fn = int((~pred & (yy == 1)).sum())
        pr = tp / max(1, tp + fp); rc = tp / max(1, tp + fn)
        f1 = 2 * pr * rc / max(1e-9, pr + rc)
        o = np.argsort(-p); tp_c = np.cumsum(yy[o]); fp_c = np.cumsum(1 - yy[o])
        prec = tp_c / np.maximum(1, tp_c + fp_c); rec = tp_c / max(1, yy.sum())
        auprc = float(np.sum((rec - np.concatenate([[0], rec[:-1]])) * prec))
        res = {"task": "T2", "cfg": cfg, "test_tokens": int(len(yy)), "pos": int(yy.sum()),
               "f1": float(f1), "precision": float(pr), "recall": float(rc), "auprc": auprc,
               "threshold": float(thr), "threshold_source": "val"}
        json.dump(res, open(os.path.join(a.outdir, f"B1_5_T2_{cfg}.json"), "w", encoding="utf-8"), indent=2)
        np.savez(os.path.join(a.outdir, f"B1_5_T2_{cfg}.npz"), p=p, y=yy, sent=sent[te])
        print(cfg, json.dumps(res), flush=True)


if __name__ == "__main__":
    main()
