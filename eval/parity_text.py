"""A3 — 텍스트 백본 ONNX FP32 ↔ PyTorch(FP32) 수치 일치 검증.

게이트 G-A3: 층별 cosine ≥ 0.99, NaN 0, 패딩 불변, batch 1/N 일치.

메모리 절약을 위해 두 단계로 나눠 실행할 수 있다:
    .venv/Scripts/python.exe eval/parity_text.py --mode dump     # PyTorch 기준값 → npz
    .venv/Scripts/python.exe eval/parity_text.py --mode compare  # ONNX 와 비교
    --mode all (기본)은 한 프로세스에서 순차 실행하되 모델을 먼저 해제한다.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time

import numpy as np
import onnxruntime as ort
import torch
from tokenizers import Tokenizer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "onnx"))
from export_text import TextGraph, load_text_model, special_token_ids  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
PREFIX = "task: search result | query: "
TEXTS = {
    "short": PREFIX + "hello world",
    "mid": PREFIX + " ".join(["the quick brown fox jumps over the lazy dog"] * 14),
    "long": PREFIX + " ".join(["embedding models map text into a shared vector space"] * 60),
    "numeric": PREFIX + "version 2.14.1 build 2026-11-02 file C:/code/unigem/onnx/eg2.onnx id A1B2C3",
    "korean": PREFIX + "안녕하세요. 이 문장은 한국어 토큰 복원 프로빙의 예시입니다.",
}
LAYERS = [0, 4, 8, 12, 16, 20]


def cos(a: np.ndarray, b: np.ndarray) -> float:
    a = a.reshape(-1).astype(np.float64)
    b = b.reshape(-1).astype(np.float64)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def make_session(path: str, threads: int = 4) -> ort.InferenceSession:
    so = ort.SessionOptions()
    so.intra_op_num_threads = threads
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(path, so, providers=["CPUExecutionProvider"])


def onnx_run(sess, ids_list: list[list[int]], pad_id: int):
    b = len(ids_list)
    s = max(len(x) for x in ids_list)
    ids = np.full((b, s), pad_id, dtype=np.int64)
    am = np.zeros((b, s), dtype=np.int64)
    for i, row in enumerate(ids_list):
        ids[i, : len(row)] = row
        am[i, : len(row)] = 1
    empty = np.zeros((0, 512), dtype=np.float32)
    names = [o.name for o in sess.get_outputs()]
    outs = sess.run(None, {
        "input_ids": ids, "attention_mask": am,
        "image_features": empty, "video_features": empty, "audio_features": empty,
    })
    return dict(zip(names, outs)), am


def dump_reference(path: str) -> None:
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    ids = {k: tok.encode(v, add_special_tokens=True).ids for k, v in TEXTS.items()}
    print("loading torch reference", flush=True)
    tm = load_text_model(CKPT)
    graph = TextGraph(tm, LAYERS, special_token_ids(CKPT)).eval()
    data = {f"ids|{k}": np.array(v, dtype=np.int64) for k, v in ids.items()}
    t0 = time.time()
    with torch.no_grad():
        for name, row in ids.items():
            outs = graph(torch.tensor([row]), torch.ones((1, len(row)), dtype=torch.long),
                         torch.zeros((0, 512)), torch.zeros((0, 512)), torch.zeros((0, 512)))
            for n, t in zip(graph.output_names(), outs):
                data[f"{name}|{n}"] = t.numpy()
    np.savez_compressed(path, **data)
    print("dumped", path, "in", round(time.time() - t0, 1), "s", flush=True)
    del tm, graph
    gc.collect()


def compare(onnx_path: str, ref_path: str, threads: int) -> dict:
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    ids = {k: tok.encode(v, add_special_tokens=True).ids for k, v in TEXTS.items()}
    ref = np.load(ref_path)
    sess = make_session(onnx_path, threads)
    names = [o.name for o in sess.get_outputs()]
    pad_id = int(special_token_ids(CKPT)["pad_token_id"])

    rows = []
    for name, row in ids.items():
        out, am = onnx_run(sess, [row], pad_id)
        valid = am[0].astype(bool)
        rec = {"case": name, "tokens": len(row), "outputs": {}}
        for n in names:
            a, b = out[n], ref[f"{name}|{n}"]
            if a.ndim == 3:
                a, b = a[0][valid], b[0][valid]
            else:
                a, b = a[0], b[0]
            rec["outputs"][n] = {
                "shape": list(out[n].shape),
                "cos": cos(a, b),
                "max_abs": float(np.abs(a.astype(np.float64) - b.astype(np.float64)).max()),
                "nan": int(np.isnan(a).sum()),
            }
        rows.append(rec)
        print(name, len(row), "min cos", round(min(v["cos"] for v in rec["outputs"].values()), 6), flush=True)

    batch_keys = ["short", "mid", "korean"]
    bout, bam = onnx_run(sess, [ids[k] for k in batch_keys], pad_id)
    for i, k in enumerate(batch_keys):
        sout, _ = onnx_run(sess, [ids[k]], pad_id)
        valid = bam[i].astype(bool)
        rec = {"case": f"padinv:{k}", "tokens": len(ids[k]), "outputs": {}}
        for n in names:
            a, b = bout[n], sout[n]
            if a.ndim == 3:
                a, b = a[i][valid], b[0][: len(ids[k])]
            else:
                a, b = a[i], b[0]
            rec["outputs"][n] = {"cos": cos(a, b), "max_abs": float(np.abs(a - b).max())}
        rows.append(rec)
        print("padinv", k, round(min(v["cos"] for v in rec["outputs"].values()), 6), flush=True)

    layer_cos = [r["outputs"][f"tok_h_l{l:02d}"]["cos"] for r in rows[:5] for l in LAYERS]
    sent_cos = [r["outputs"]["sentence_embedding"]["cos"] for r in rows[:5]]
    pad_cos = [min(v["cos"] for v in r["outputs"].values()) for r in rows[5:]]
    summary = {
        "onnx": onnx_path,
        "cases": len(rows),
        "min_layer_cos": float(min(layer_cos)),
        "min_sentence_cos": float(min(sent_cos)),
        "min_padinv_cos": float(min(pad_cos)),
        "max_layer_abs": float(max(
            r["outputs"][f"tok_h_l{l:02d}"]["max_abs"] for r in rows[:5] for l in LAYERS)),
        "nan_total": int(sum(v.get("nan", 0) for r in rows for v in r["outputs"].values())),
        "gate": "PASS" if min(layer_cos) >= 0.99 and min(sent_cos) >= 0.99 and min(pad_cos) >= 0.99 else "FAIL",
    }
    return {"summary": summary, "rows": rows}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--onnx", default=os.path.join(ROOT, "onnx", "eg2_text_research_fp32.onnx"))
    ap.add_argument("--ref", default=os.path.join(ROOT, "logs", "A3_text_ref.npz"))
    ap.add_argument("--out", default=os.path.join(ROOT, "logs", "A3_parity_text.jsonl"))
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--mode", choices=["all", "dump", "compare"], default="all")
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    if args.mode in ("all", "dump"):
        dump_reference(args.ref)
    if args.mode in ("all", "compare"):
        res = compare(args.onnx, args.ref, args.threads)
        with open(args.out, "w", encoding="utf-8") as f:
            for r in res["rows"]:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(json.dumps(res["summary"], ensure_ascii=False, indent=2))
        with open(args.out.replace(".jsonl", "_summary.json"), "w", encoding="utf-8") as f:
            json.dump(res["summary"], f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
