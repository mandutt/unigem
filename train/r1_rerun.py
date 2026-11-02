"""R1 (Addendum B §B-3) — G-B1.5-a 정정 재측정.

- 진단: 층 특징 → 임베딩 테이블 전체(262,144) 코사인 최근접
- 주 측정: 폐쇄형 릿지 회귀 W (H→E_y), λ는 val 선택
- 평가: 전체 어휘 코사인 최근접, 전체 test 토큰
- 지표: 전체/숫자/언어별/seen-unseen 정확도, 식별자·숫자 span exact, 문자 편집거리
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time

import numpy as np
import torch

ROOT = r"C:\code\unigem"
CACHE = os.path.join(ROOT, "cache", "b1_5")
CORPUS = os.path.join(ROOT, "data", "b1_5", "corpus_v2", "corpus.jsonl")
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
SPLITS: list[str] = []

PATTERNS = {
    "sha": re.compile(r"\b[0-9a-f]{40}\b"),
    "url": re.compile(r"https?://\S+"),
    "path": re.compile(r"[\w./-]+/[\w./-]+\.(?:py|json|md|txt|yaml|yml|toml|onnx|cpp|h)"),
    "version": re.compile(r"\bv?\d+\.\d+(?:\.\d+)?\b"),
    "errcode": re.compile(r"\bE\d{4}\b"),
    "number": re.compile(r"\b\d[\d,]*\b"),
}


def load_table():
    from safetensors import safe_open
    with safe_open(os.path.join(CKPT, "model.safetensors"), framework="pt") as f:
        return f.get_tensor("language_model.embed_tokens.weight").float().numpy()


def load_flat(layer: str):
    files = sorted(os.path.join(CACHE, "shards", f) for f in os.listdir(os.path.join(CACHE, "shards")))
    xs, ys, ss, rr = [], [], [], []
    for p in files:
        z = np.load(p)
        h = z[layer]; ids = z["ids"]; m = z["mask"]
        xs.append(h[m].astype(np.float32)); ys.append(ids[m].astype(np.int64))
        ss.append(np.repeat(np.array([SPLITS[int(r)] for r in z["row_idx"]]), m.sum(axis=1)))
        rr.append(np.repeat(z["row_idx"], m.sum(axis=1)))
    return np.concatenate(xs), np.concatenate(ys), np.concatenate(ss), np.concatenate(rr)


def ridge_fit(H, Y, lam):
    # H [N,D], Y [N,E]
    A = H.T @ H + lam * np.eye(H.shape[1], dtype=np.float32)
    B = H.T @ Y
    return np.linalg.solve(A, B).astype(np.float32)


def top1_full(Q, E, chunk=512):
    """Q [N,D] cosine top-1 against E [V,D]."""
    q = Q / np.maximum(1e-9, np.linalg.norm(Q, axis=1, keepdims=True))
    e = E / np.maximum(1e-9, np.linalg.norm(E, axis=1, keepdims=True))
    out = np.empty(len(q), np.int64)
    for i in range(0, len(q), chunk):
        s = q[i:i + chunk] @ e.T
        out[i:i + chunk] = s.argmax(1)
    return out


def wilson(p, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (float(c - h), float(c + h))


def span_metrics(rows, pred_map, tok):
    """rows: list of corpus rows (identifier/number). pred_map: row_idx -> pred ids."""
    import collections
    stats = collections.defaultdict(lambda: [0, 0, 0.0])  # exact, total, editdist
    tokcache = {}
    for ridx in rows:
        r = json.loads(open(CORPUS, encoding="utf-8").readlines()[ridx])
        text = r["text"]
        pred = pred_map.get(ridx)
        if pred is None:
            continue
        enc = tok.encode(text)
        offs = enc.offsets[:len(pred)]
        for name, pat in PATTERNS.items():
            for m in pat.finditer(text):
                s0, s1 = m.span()
                ks = [k for k, (a, b) in enumerate(offs) if a < s1 and s0 < b]
                if not ks:
                    continue
                true_ids = enc.ids[ks[0]:ks[-1] + 1]
                got = pred[ks[0]:ks[-1] + 1]
                ok = bool(np.array_equal(np.array(true_ids), np.array(got)))
                st = stats[name]
                st[1] += 1
                if ok:
                    st[0] += 1
                else:
                    # 문자 편집거리 (디코드 문자열)
                    a = tok.decode([int(x) for x in true_ids]); b = tok.decode([int(x) for x in got])
                    st[2] += levenshtein(a, b)
    return {k: {"exact": v[0], "n": v[1], "rate": (v[0] / v[1] if v[1] else None),
                "mean_edit": (v[2] / v[1] if v[1] else None)} for k, v in stats.items()}


def levenshtein(a, b):
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", nargs="+", default=["tok_h_l00", "tok_h_l04", "combo"])
    ap.add_argument("--lams", nargs="+", type=float, default=[1e-4, 1e-3, 1e-2, 1e-1, 1.0, 10.0])
    ap.add_argument("--out", default=os.path.join(ROOT, "logs", "R1_rerun.json"))
    a = ap.parse_args()

    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    rows = [json.loads(l) for l in open(CORPUS, encoding="utf-8")]
    global SPLITS
    SPLITS = [r["split"] for r in rows]
    E = load_table()
    Ev = torch.from_numpy(E)
    print("E", E.shape, flush=True)

    feats = {}
    Y = None; S = None; R = None
    for layer in a.layers:
        if layer == "combo":
            continue
        X, y, s, r = load_flat(layer)
        feats[layer] = X
        if Y is None:
            Y, S, R = y, s, r
        print(layer, X.shape, flush=True)
    if "combo" in a.layers:
        feats["combo"] = np.concatenate([feats["tok_h_l00"], feats["tok_h_l04"]], axis=1)
        print("combo", feats["combo"].shape, flush=True)

    results = {"n_tokens": int(len(Y)), "splits": {k: int((S == k).sum()) for k in ("train", "val", "test")},
               "layers": {}}
    tr = S == "train"; va = S == "val"; te = S == "test"

    # 언어/유형 메타 (행 단위)
    row_lang = np.array([r["lang"] for r in rows])
    row_kind = np.array([r["kind"] for r in rows])
    tok_lang = row_lang[R]
    tok_kind = row_kind[R]
    seen_vocab = np.unique(Y[tr])

    for layer, X in feats.items():
        t0 = time.time()
        Ytr = E[Y[tr]].astype(np.float32)
        best = None
        for lam in a.lams:
            W = ridge_fit(X[tr], Ytr, lam)
            # val 평가는 부분표본으로 λ 선택 (비용)
            idx = np.where(va)[0]
            sub = idx[::max(1, len(idx) // 20000)]
            pred = top1_full(X[sub] @ W, E)
            acc = float((pred == Y[sub]).mean())
            print(layer, "lam", lam, "val_acc", round(acc, 4), flush=True)
            if best is None or acc > best[1]:
                best = (lam, acc, W)
        lam, val_acc, W = best

        res = {"lambda": lam, "val_acc": val_acc}
        # 진단: raw NN (no ridge)
        idx_te = np.where(te)[0]
        pred_raw = top1_full(X[idx_te], E)
        pred = top1_full(X[idx_te] @ W, E)
        y = Y[idx_te]
        for tag, p in (("raw_nn", pred_raw), ("ridge", pred)):
            acc = float((p == y).mean()); lo, hi = wilson(acc, len(y))
            res[tag] = {"acc": acc, "ci": [lo, hi], "n": int(len(y))}
        # seen/unseen
        seen_mask = np.isin(y, seen_vocab)
        res["ridge_seen"] = float((pred[seen_mask] == y[seen_mask]).mean()) if seen_mask.any() else None
        res["ridge_unseen"] = float((pred[~seen_mask] == y[~seen_mask]).mean()) if (~seen_mask).any() else None
        res["n_unseen"] = int((~seen_mask).sum())
        # 언어별
        res["by_lang"] = {lg: float((pred[tok_lang[idx_te] == lg] == y[tok_lang[idx_te] == lg]).mean())
                          for lg in np.unique(tok_lang[idx_te])}
        # 숫자 토큰
        num_mask = np.array([bool(re.fullmatch(r"\d+", tok.decode([int(t)]))) for t in y])
        res["numeric_acc"] = float((pred[num_mask] == y[num_mask]).mean()) if num_mask.any() else None
        res["n_numeric"] = int(num_mask.sum())

        # span exact: test 식별자/숫자 행
        test_rows = [i for i in np.unique(R[idx_te]) if row_kind[i] in ("identifier", "number_date")]
        pred_map = {}
        order_pos = {int(idx): k for k, idx in enumerate(idx_te)}
        for i in np.unique(R[idx_te]):
            ks = [order_pos[int(j)] for j in np.where((R == i) & te)[0]]
            if ks:
                pred_map[int(i)] = pred[ks]
        res["spans"] = span_metrics([int(i) for i in test_rows], pred_map, tok)
        res["elapsed_s"] = round(time.time() - t0, 1)
        results["layers"][layer] = res
        print(layer, json.dumps({k: res[k] for k in ("lambda", "raw_nn", "ridge")}, ensure_ascii=False), flush=True)
        json.dump(results, open(a.out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("saved", a.out, flush=True)


if __name__ == "__main__":
    main()
