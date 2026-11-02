"""A-7.2 — 오디오 q8(동적, 12층) 지연·RTF 측정.

입력 길이 5/16/30초에 대해 p50/p95, RTF, peak RSS, 로드 시간을 측정한다.
"""
from __future__ import annotations

import json
import os
import statistics
import time

import numpy as np
import onnxruntime as ort
import psutil

ROOT = r"C:\code\unigem"
ONNX = os.path.join(ROOT, "onnx", "eg2_audio_q8_layers.onnx")
OUT = os.path.join(ROOT, "logs", "A7_audio_q8_latency.json")
SECONDS = [5, 16, 30]
REPEAT = 15


def main():
    proc = psutil.Process()
    rss0 = proc.memory_info().rss
    so = ort.SessionOptions()
    so.intra_op_num_threads = 6
    so.log_severity_level = 3
    t0 = time.perf_counter()
    sess = ort.InferenceSession(ONNX, so, providers=["CPUExecutionProvider"])
    load_s = time.perf_counter() - t0
    rss_load = proc.memory_info().rss
    names = [o.name for o in sess.get_outputs()]
    print("load", round(load_s, 2), "s | outputs", len(names), "| rss MB",
          round((rss_load - rss0) / 1e6, 1), flush=True)

    rows = []
    for sec in SECONDS:
        frames = sec * 100  # 10ms hop
        feats = np.random.default_rng(0).standard_normal((1, frames, 128)).astype(np.float32) * 0.1
        mask = np.ones((1, frames), bool)
        feed = {"input_features": feats, "input_features_mask": mask}
        for _ in range(3):
            sess.run(None, feed)
        ts = []
        peak = 0
        for _ in range(REPEAT):
            t = time.perf_counter()
            sess.run(None, feed)
            ts.append((time.perf_counter() - t) * 1000)
            peak = max(peak, proc.memory_info().rss)
        ts.sort()
        row = {"seconds": sec, "p50_ms": round(statistics.median(ts), 1),
               "p95_ms": round(ts[int(len(ts) * 0.95) - 1], 1),
               "rtf": round(statistics.median(ts) / (sec * 1000), 4),
               "rss_peak_mb": round((peak - rss0) / 1e6, 1)}
        rows.append(row)
        print(row, flush=True)

    out = {"onnx": ONNX, "threads": 6, "repeat": REPEAT, "load_s": round(load_s, 2),
           "rss_load_mb": round((rss_load - rss0) / 1e6, 1), "rows": rows}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("saved", OUT)


if __name__ == "__main__":
    main()
