"""A4 — 동적 INT8 (MatMulNBits bits=8, accuracy_level=4) 양자화.

운영 ONNX(q8-al4)와 같은 형식: MatMulNBits + bits=8 + accuracy_level=4.
가중치는 외부 데이터 파일로 저장한다(_data).

사용:
    .venv/Scripts/python.exe onnx/quantize_q8.py --input onnx/eg2_text_research_fp32.onnx \
        --output onnx/eg2_text_prod_q8.onnx
"""

from __future__ import annotations

import argparse
import json
import os
import time

import onnx
from onnxruntime.quantization.matmul_nbits_quantizer import MatMulNBitsQuantizer


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--bits", type=int, default=8)
    ap.add_argument("--block-size", type=int, default=128)
    ap.add_argument("--symmetric", action="store_true")
    ap.add_argument("--accuracy-level", type=int, default=4)
    ap.add_argument("--op-types", default="MatMul,MatMulNBits,Gather")
    args = ap.parse_args()

    t0 = time.time()
    print("quantizing", args.input, flush=True)
    quantizer = MatMulNBitsQuantizer(
        args.input,
        bits=args.bits,
        block_size=args.block_size,
        is_symmetric=args.symmetric,
        accuracy_level=args.accuracy_level,
        op_types_to_quantize=tuple(args.op_types.split(",")),
    )
    quantizer.process()
    model = quantizer.model.model

    out = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    data_name = os.path.basename(out) + "_data"
    for f in (out, os.path.join(os.path.dirname(out), data_name)):
        if os.path.exists(f):
            os.remove(f)
    onnx.save_model(
        model,
        out,
        save_as_external_data=True,
        all_tensors_to_one_file=True,
        location=data_name,
        size_threshold=1024,
    )
    size = os.path.getsize(out) + (os.path.getsize(os.path.join(os.path.dirname(out), data_name))
                                   if os.path.exists(os.path.join(os.path.dirname(out), data_name)) else 0)
    meta = {
        "input": args.input,
        "output": out,
        "bits": args.bits,
        "block_size": args.block_size,
        "symmetric": args.symmetric,
        "accuracy_level": args.accuracy_level,
        "size_bytes": size,
        "elapsed_s": round(time.time() - t0, 1),
    }
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    with open(out + ".meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
