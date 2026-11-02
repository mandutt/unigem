"""B1.5-3 — T3: 최소쌍 구분 (되/돼, 안/않) — 규칙 합성.

각 쌍은 동일 길이의 정답/오답 형태를 같은 위치에 넣어 만든다.
형태 위치의 hidden으로 이진 분류(정답=1, 오답=0).
"""
from __future__ import annotations

import argparse
import json
import os
import random

import numpy as np
import onnxruntime as ort
import torch
import torch.nn as nn
import torch.nn.functional as F
from tokenizers import Tokenizer

ROOT = r"C:\code\unigem"
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
ONNX = os.path.join(ROOT, "onnx", "eg2_text_research_fp32.onnx")
MAXLEN = 96
SEED = 20261103

SUBJ = ["회의", "배포", "빌드", "테스트", "설정", "작업", "요청", "응답", "서버", "모델",
        "문서", "결과", "일정", "점검", "업로드", "다운로드", "학습", "평가", "리뷰", "릴리스"]

TPL_DOE = [
    ("{s} 작업이 모두 ", "되었습니다", "돼었습니다", "."),
    ("{s}가 완료", "되면", "돼면", " 알려 주세요."),
    ("지금은 {s} 업로드가 안 ", "돼요", "되요", "."),
    ("{s} 일정이 잘 ", "돼서", "되서", " 다행입니다."),
    ("{s} 작업이 모두 ", "됐습니다", "됬습니다", "."),
]
TPL_AN = [
    ("{s} 작업이 아직 끝나지 ", "않았습니다", "안았습니다", "."),
    ("오늘은 {s} 진행이 ", "안 됩니다", "않 됩니다", "."),
    ("{s} 결과가 좋지 ", "않아요", "안아요", "."),
    ("{s} 상태가 ", "안 좋아요", "않 좋아요", "."),
]


def gen_pairs(n_per_type=500, seed=SEED):
    rng = random.Random(seed)
    pairs = []
    for i in range(n_per_type):
        tpl = TPL_DOE[i % len(TPL_DOE)]
        pre, good, bad, suf = tpl[0].format(s=rng.choice(SUBJ)), tpl[1], tpl[2], tpl[3]
        pairs.append((pre + good + suf, pre + bad + suf, len(pre), "doe"))
    for i in range(n_per_type):
        tpl = TPL_AN[i % len(TPL_AN)]
        pre, good, bad, suf = tpl[0].format(s=rng.choice(SUBJ)), tpl[1], tpl[2], tpl[3]
        pairs.append((pre + good + suf, pre + bad + suf, len(pre), "an"))
    rng.shuffle(pairs)
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--bs", type=int, default=1024)
    ap.add_argument("--out", default=os.path.join(ROOT, "logs", "B1_5_T3.json"))
    a = ap.parse_args()

    pairs = gen_pairs()
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    so = ort.SessionOptions(); so.intra_op_num_threads = 6; so.log_severity_level = 3
    sess = ort.InferenceSession(ONNX, so, providers=["CPUExecutionProvider"])
    names = [o.name for o in sess.get_outputs()]
    empty = np.zeros((0, 512), np.float32)

    flat = []
    for pi, (g, b, pos, typ) in enumerate(pairs):
        flat.append((pi, 1, g, pos, typ))
        flat.append((pi, 0, b, pos, typ))

    feats = {"bl0": [], "bl1": [], "l04": []}
    labels, splits = [], []
    for st in range(0, len(flat), 16):
        chunk = flat[st:st + 16]
        ids = np.zeros((len(chunk), MAXLEN), np.int64); am = np.zeros_like(ids)
        for j, (_, _, t, _, _) in enumerate(chunk):
            seq = tok.encode(t).ids[:MAXLEN]
            ids[j, :len(seq)] = seq; am[j, :len(seq)] = 1
        out = dict(zip(names, sess.run(None, {"input_ids": ids, "attention_mask": am,
                                               "image_features": empty, "video_features": empty, "audio_features": empty})))
        H0, HL = out["tok_h_l00"], out["tok_h_l04"]
        for j, (pi, lab, text, pos, typ) in enumerate(chunk):
            enc = tok.encode(text)
            k = next((t for t, (s0, s1) in enumerate(enc.offsets) if s0 <= pos < s1), None)
            if k is None or k >= MAXLEN:
                continue
            L = min(len(enc.ids), MAXLEN)
            win = [H0[j, u].astype(np.float32) if 0 <= u < L else np.zeros(512, np.float32) for u in range(k - 2, k + 3)]
            feats["bl0"].append(H0[j, k].astype(np.float32))
            feats["bl1"].append(np.concatenate(win))
            feats["l04"].append(np.concatenate(win + [HL[j, k].astype(np.float32)]))
            labels.append(lab)
            splits.append("train" if pi % 100 < 70 else ("val" if pi % 100 < 85 else "test"))

    y = np.array(labels); splits = np.array(splits)
    print("samples", len(y), "pos", int(y.sum()), flush=True)
    out = {"n_pairs": len(pairs), "n_samples": int(len(y))}
    for cfg in ("bl0", "bl1", "l04"):
        X = np.stack(feats[cfg])
        tr = splits == "train"; va = splits == "val"; te = splits == "test"
        xt = torch.from_numpy(X[tr]); yt = torch.from_numpy(y[tr]).float()
        model = nn.Linear(X.shape[1], 1)
        opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
        for ep in range(a.epochs):
            perm = torch.randperm(len(xt))
            for s in range(0, len(xt), a.bs):
                idx = perm[s:s + a.bs]; opt.zero_grad()
                loss = F.binary_cross_entropy_with_logits(model(xt[idx]).squeeze(-1), yt[idx])
                loss.backward(); opt.step()
        with torch.no_grad():
            pv = torch.sigmoid(model(torch.from_numpy(X[va])).squeeze(-1)).numpy()
            pt = torch.sigmoid(model(torch.from_numpy(X[te])).squeeze(-1)).numpy()
        thrs = np.linspace(0.05, 0.95, 91)
        thr = max((np.mean((pv >= t) == y[va]), t) for t in thrs)[1]
        acc = float(np.mean((pt >= thr) == y[te]))
        out[cfg] = {"acc": acc, "threshold": float(thr), "n_test": int(te.sum())}
        print(cfg, out[cfg], flush=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main()
