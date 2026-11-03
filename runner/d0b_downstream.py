"""D0-b — 다운스트림 지표: 전사 임베딩 보존과 검색.

FLEURS 382 + Kspon 100에 대해 ref/hyp를 EG2 텍스트 Q8로 임베딩하고,
코사인 분포·검색 R@1/MRR·CER 구간별 코사인을 보고한다.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

ROOT = r"C:\code\unigem"
sys.path.insert(0, ROOT)
from eval.normalize import cer_prepared, normalize  # noqa: E402

CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
ONNX = os.path.join(ROOT, "onnx", "eg2_text_prod_q8.onnx")
OUT = os.path.join(ROOT, "logs", "D0b_downstream.json")
PREFIX = "title: none | text: "


def load_rows():
    fleurs = [json.loads(l) for l in open(os.path.join(ROOT, "logs", "C2_A1", "fleurs_pred.jsonl"), encoding="utf-8")]
    kspon = [json.loads(l) for l in open(os.path.join(ROOT, "logs", "C2_A1", "pred.jsonl"), encoding="utf-8") if json.loads(l).get("source") == "kspon_eval_clean"]
    return fleurs, kspon


def embed(sess, tok, names, texts):
    out = []
    empty = np.zeros((0, 512), np.float32)
    for t in texts:
        enc = tok.encode(PREFIX + t)
        ids = np.array([enc.ids[:512]], np.int64)
        am = np.ones_like(ids, np.int64)
        r = dict(zip(names, sess.run(None, {"input_ids": ids, "attention_mask": am,
                                            "image_features": empty, "video_features": empty, "audio_features": empty})))
        v = r["sentence_embedding"][0].astype(np.float64)
        out.append(v / max(np.linalg.norm(v), 1e-12))
    return np.asarray(out)


def stats(a, b):
    c = np.sum(a * b, axis=1)
    return {"n": int(len(c)), "mean": float(c.mean()), "p5": float(np.percentile(c, 5)),
            "min": float(c.min()), "max": float(c.max())}


def retrieval(q, cand):
    sim = q @ cand.T
    ranks = []
    for i in range(len(q)):
        order = np.argsort(-sim[i])
        ranks.append(int(np.where(order == i)[0][0]) + 1)
    return {"r1": float(np.mean([r == 1 for r in ranks])), "mrr": float(np.mean([1.0 / r for r in ranks])),
            "n": len(ranks)}


def cers(rows):
    return [cer_prepared(normalize(r["ref"]), normalize(r["hyp"]), False) for r in rows]


def main():
    so = ort.SessionOptions(); so.intra_op_num_threads = 6; so.log_severity_level = 3
    sess = ort.InferenceSession(ONNX, so, providers=["CPUExecutionProvider"])
    names = [o.name for o in sess.get_outputs()]
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    fleurs, kspon = load_rows()
    out = {}
    for label, rows in (("fleurs", fleurs), ("kspon", kspon)):
        refs = embed(sess, tok, names, [r["ref"] for r in rows])
        hyps = embed(sess, tok, names, [r["hyp"] for r in rows])
        cs = np.sum(refs * hyps, axis=1)
        c = cers(rows)
        bins = {"0-5": [], "5-10": [], "10-20": [], "20+": []}
        for v, x in zip(cs, c):
            b = "0-5" if x < 0.05 else "5-10" if x < 0.10 else "10-20" if x < 0.20 else "20+"
            bins[b].append(float(v))
        out[label] = {
            "n": len(rows),
            "cos": stats(refs, hyps),
            "retrieval": retrieval(hyps, refs),
            "cer_mean": float(np.mean(c)),
            "bins": {k: {"n": len(v), "cos_mean": float(np.mean(v)) if v else None} for k, v in bins.items()},
        }
        print(label, json.dumps(out[label], ensure_ascii=False), flush=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("saved", OUT)


if __name__ == "__main__":
    main()
