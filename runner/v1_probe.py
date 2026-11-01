"""V1 정합·캘리브레이션 프로브 — 로컬과 VPS에서 동일 실행.

- 고정 시드로 소형 ONNX 그래프를 즉석 생성 (외부 파일 없음)
- 출력 벡터의 sha256 + 첫 8개 값 → 호스트 간 수치 정합 비교
- 스레드 1/2/4별 30회 지연(p50) → 호스트 상대 속도 계수

사용: python v1_probe.py [--json out.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import sys
import time

import numpy as np
import onnx
import onnxruntime as ort
from onnx import helper, TensorProto, numpy_helper


def build_model(path: str, seed: int = 0):
    rng = np.random.default_rng(seed)
    d = 4096
    w1 = rng.standard_normal((128, d), dtype=np.float32) * 0.02
    b1 = rng.standard_normal((d,), dtype=np.float32) * 0.01
    g = np.ones((d,), np.float32)
    b2 = np.zeros((d,), np.float32)
    w2 = rng.standard_normal((d, d), dtype=np.float32) * 0.01
    w3 = rng.standard_normal((d, 128), dtype=np.float32) * 0.05

    inits = [numpy_helper.from_array(a, n) for a, n in [
        (w1, "w1"), (b1, "b1"), (g, "g"), (b2, "b2"), (w2, "w2"), (w3, "w3")]]

    nodes = [
        helper.make_node("MatMul", ["x", "w1"], ["m1"]),
        helper.make_node("Add", ["m1", "b1"], ["a1"]),
        helper.make_node("LayerNormalization", ["a1", "g", "b2"], ["ln"], axis=-1, epsilon=1e-5),
        helper.make_node("MatMul", ["ln", "w2"], ["m2"]),
        helper.make_node("Relu", ["m2"], ["r2"]),
        helper.make_node("MatMul", ["r2", "w3"], ["m3"]),
        helper.make_node("Softmax", ["m3"], ["y"], axis=-1),
    ]
    graph = helper.make_graph(
        nodes, "v1probe",
        [helper.make_tensor_value_info("x", TensorProto.FLOAT, [1, 128])],
        [helper.make_tensor_value_info("y", TensorProto.FLOAT, [1, 128])],
        inits,
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 9
    onnx.checker.check_model(model)
    onnx.save(model, path)


def run(path: str, threads: int, n: int = 30, reps: int = 20):
    so = ort.SessionOptions()
    so.intra_op_num_threads = threads
    so.inter_op_num_threads = 1
    so.log_severity_level = 3
    sess = ort.InferenceSession(path, so, providers=["CPUExecutionProvider"])
    x = np.linspace(-1, 1, 128, dtype=np.float32).reshape(1, 128)
    for _ in range(3):
        sess.run(None, {"x": x})
    times = []
    y = None
    for _ in range(n):
        t0 = time.perf_counter()
        for _ in range(reps):
            y = sess.run(None, {"x": x})[0]
        times.append((time.perf_counter() - t0) * 1000 / reps)
    times.sort()
    p50 = statistics.median(times)
    return {
        "threads": threads,
        "p50_ms": round(p50, 3),
        "p95_ms": round(times[int(len(times) * 0.95) - 1], 3),
        "sha256": hashlib.sha256(y.tobytes()).hexdigest()[:16],
        "y": [float(v) for v in y.ravel()],
        "y_sum": round(float(y.sum()), 8),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="")
    ap.add_argument("--n", type=int, default=30)
    args = ap.parse_args()

    path = "/tmp/v1probe.onnx" if sys.platform != "win32" else "v1probe.onnx"
    build_model(path)
    out = {
        "host": platform.node(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "onnxruntime": ort.__version__,
        "runs": [run(path, t, args.n) for t in (1, 2, 4)],
    }
    text = json.dumps(out, ensure_ascii=False)
    print(text)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            f.write(text)


if __name__ == "__main__":
    main()
