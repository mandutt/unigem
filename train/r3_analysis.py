"""R3 — 접두사 영향 (토큰 문자열 정렬, 본문만)."""
from __future__ import annotations

import json
import os

import numpy as np
from tokenizers import Tokenizer

ROOT = r"C:\code\unigem"
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
CORP = os.path.join(ROOT, "data", "r3")
PREFIX = {"query": "task: search result | query: ", "doc": "title: none | text: "}


def load(tag):
    d = os.path.join(ROOT, "cache", f"r3_{tag}", "shards")
    rows = {}
    for fn in sorted(os.listdir(d)):
        z = np.load(os.path.join(d, fn))
        for k, r in enumerate(z["row_idx"]):
            L = int(z["mask"][k].sum())
            rows[int(r)] = {"ids": z["ids"][k, :L].astype(np.int64),
                            "l00": z["tok_h_l00"][k, :L].astype(np.float32),
                            "l04": z["tok_h_l04"][k, :L].astype(np.float32)}
    return rows


def align(tok, text, pref):
    b = tok.encode(text); v = tok.encode(pref + text)
    bi0 = 1 if b.tokens and b.tokens[0] == "<bos>" else 0
    vi0 = 1 if v.tokens and v.tokens[0] == "<bos>" else 0
    for k in range(vi0, len(v.tokens)):
        if len(v.tokens) - k == len(b.tokens) - bi0:
            if (v.tokens[k + 1:] == b.tokens[bi0 + 1:] and
                    v.tokens[k].lstrip("▁") == b.tokens[bi0].lstrip("▁")):
                return list(range(bi0, len(b.tokens))), list(range(k, len(v.tokens)))
    return None, None


def main():
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    rows = [json.loads(l) for l in open(os.path.join(CORP, "base.jsonl"), encoding="utf-8")]
    base = load("base")
    res = {"n_rows": len(rows), "variants": {}}
    for tag, pref in PREFIX.items():
        var = load(tag)
        cos = {"l00": [], "l04": [], "l00_pool": [], "l04_pool": []}
        aligned = 0
        for i, r in enumerate(rows):
            b, v = base.get(i), var.get(i)
            if b is None or v is None:
                continue
            bi, vi = align(tok, r["text"], pref)
            if bi is None:
                continue
            bi, vi = bi[1:], vi[1:]  # 경계 병합 토큰 제외
            if b["ids"][bi].shape != v["ids"][vi].shape or not np.array_equal(b["ids"][bi], v["ids"][vi]):
                continue
            aligned += 1
            for k in ("l00", "l04"):
                a, c = b[k][bi], v[k][vi]
                cos[k].append(np.sum(a * c, 1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(c, axis=1) + 1e-9))
                cos[f"{k}_pool"].append(float(np.dot(a.mean(0), c.mean(0)) /
                                              (np.linalg.norm(a.mean(0)) * np.linalg.norm(c.mean(0)) + 1e-9)))
        out = {"prefix_tokens": len(tok.encode(pref).ids), "rows_aligned": aligned, "rows_total": len(rows)}
        for k in ("l00", "l04"):
            arr = np.concatenate(cos[k]) if cos[k] else np.array([np.nan])
            out[k] = {"cos_mean": float(arr.mean()), "cos_p5": float(np.percentile(arr, 5)), "cos_min": float(arr.min())}
            out[f"{k}_pool_mean"] = float(np.mean(cos[f"{k}_pool"])) if cos[f"{k}_pool"] else None
        res["variants"][tag] = out
        print(tag, out, flush=True)

    from safetensors import safe_open
    with safe_open(os.path.join(CKPT, "model.safetensors"), framework="pt") as f:
        E = f.get_tensor("language_model.embed_tokens.weight").float().numpy()
    En = E / np.maximum(1e-9, np.linalg.norm(E, axis=1, keepdims=True))
    splits = np.array([r["split"] for r in rows])
    for tag, pref in (("base", None), ("query", PREFIX["query"]), ("doc", PREFIX["doc"])):
        d = load(tag)
        Xtr, Ytr, Xte, Yte = [], [], [], []
        for i, r in enumerate(rows):
            if i not in d:
                continue
            if pref:
                bi, vi = align(tok, r["text"], pref)
                if bi is None:
                    continue
                idx = vi[1:]; ids = d[i]["ids"][vi[1:]]
            else:
                idx = list(range(len(d[i]["ids"]))); ids = d[i]["ids"]
            if splits[i] == "train":
                Xtr.append(d[i]["l00"][idx]); Ytr.append(ids)
            elif splits[i] == "test":
                Xte.append(d[i]["l00"][idx]); Yte.append(ids)
        X = np.concatenate(Xtr); Y = np.concatenate(Ytr)
        W = np.linalg.solve(X.T @ X + 1e-4 * np.eye(512, dtype=np.float32), X.T @ E[Y]).astype(np.float32)
        Xt = np.concatenate(Xte); Yt = np.concatenate(Yte)
        Q = Xt @ W; Q /= np.maximum(1e-9, np.linalg.norm(Q, axis=1, keepdims=True))
        pred = np.empty(len(Q), np.int64)
        for s in range(0, len(Q), 512):
            pred[s:s + 512] = (Q[s:s + 512] @ En.T).argmax(1)
        res["variants"].setdefault(tag, {})["probe_acc"] = float((pred == Yt).mean())
        res["variants"][tag]["probe_n"] = int(len(Yt))
        print(tag, "probe", round(float((pred == Yt).mean()), 4), len(Yt), flush=True)
    json.dump(res, open(os.path.join(ROOT, "logs", "R3_prefix.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
