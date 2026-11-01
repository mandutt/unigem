"""A4 — ONNX CPU 성능 측정 (텍스트/오디오, 스레드 수별).

측정: 세션 로드 시간, 파일 크기, 첫 추론, 워밍업 후 p50/p95 지연, 프로세스 RSS 증가.
VPS 값은 참고(VPS)로만 표기하고 판정에 쓰지 않는다 (문서 §8.2).

사용:
    .venv/Scripts/python.exe eval/perf_onnx.py --kind text --onnx onnx/eg2_text_prod_q8.onnx --threads 6
    .venv/Scripts/python.exe eval/perf_onnx.py --kind audio --onnx onnx/eg2_audio_research_fp32.onnx --threads 6
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time

import numpy as np
import onnxruntime as ort
import psutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rss_mb() -> float:
    return psutil.Process().memory_info().rss / 2**20


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["text", "audio"], required=True)
    ap.add_argument("--onnx", required=True)
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--lengths", default="128,256,512")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    lengths = [int(x) for x in args.lengths.split(",")]
    rss0 = rss_mb()
    so = ort.SessionOptions()
    so.intra_op_num_threads = args.threads
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    t0 = time.perf_counter()
    sess = ort.InferenceSession(args.onnx, so, providers=["CPUExecutionProvider"])
    load_s = time.perf_counter() - t0
    rss1 = rss_mb()
    size = os.path.getsize(args.onnx)
    data_path = args.onnx + "_data"
    if os.path.exists(data_path):
        size += os.path.getsize(data_path)

    results = []
    for L in lengths:
        if args.kind == "text":
            feed = {
                "input_ids": np.random.randint(3, 200000, (1, L), dtype=np.int64),
                "attention_mask": np.ones((1, L), dtype=np.int64),
                "image_features": np.zeros((0, 512), np.float32),
                "video_features": np.zeros((0, 512), np.float32),
                "audio_features": np.zeros((0, 512), np.float32),
            }
        else:
            feed = {
                "input_features": np.zeros((1, L, 128), dtype=np.float32),
                "input_features_mask": np.ones((1, L), dtype=bool),
            }
        for _ in range(args.warmup):
            sess.run(None, feed)
        times, first = [], None
        for i in range(args.reps):
            t = time.perf_counter()
            sess.run(None, feed)
            dt = (time.perf_counter() - t) * 1000
            times.append(dt)
            if i == 0:
                first = dt
        rec = {
            "kind": args.kind,
            "onnx": os.path.basename(args.onnx),
            "threads": args.threads,
            "length": L,
            "unit": "tokens" if args.kind == "text" else "mel_frames",
            "first_ms": round(first, 2),
            "p50_ms": round(statistics.median(times), 2),
            "p95_ms": round(sorted(times)[max(0, int(len(times) * 0.95) - 1)], 2),
            "min_ms": round(min(times), 2),
            "max_ms": round(max(times), 2),
            "n": args.reps,
        }
        results.append(rec)
        print(json.dumps(rec, ensure_ascii=False), flush=True)

    summary = {
        "onnx": args.onnx,
        "kind": args.kind,
        "threads": args.threads,
        "file_bytes": size,
        "load_s": round(load_s, 3),
        "rss_before_mb": round(rss0, 1),
        "rss_after_load_mb": round(rss1, 1),
        "rss_delta_mb": round(rss1 - rss0, 1),
        "rows": results,
    }
    out = args.out or os.path.join(ROOT, "logs", f"perf_{args.kind}_t{args.threads}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
