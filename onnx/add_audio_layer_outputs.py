"""운영 q8 오디오 그래프에 층 hidden/out_proj 출력을 추가한다 (재export 불필요).

배경: Gemma4 audio 타워의 torch.onnx export는 legacy 실패, dynamo 14~17분+ 무출력으로 막혔다.
대신 운영 그래프의 중간 텐서를 출력으로 승격해 다층 hidden을 확보했다(원본 불변, 파생 사본만 수정).

텐서 매핑은 실측으로 찾았다:
  - [B,T,1024] 후보 533개를 임시 출력으로 추가한 probe를 1회 실행
  - PyTorch 타워 12층 출력과 cosine 비교 → layer i = `type_as_{8 + 9*i}` (cos 0.99997~0.999998)
  - [B,T,1536] 후보 중 `linear_133` = output_proj (cos 0.99945)

사용:
  .venv/Scripts/python.exe onnx/add_audio_layer_outputs.py \
      --src C:/code/eg2-langidentifier/scripts/mmal4/audio_encoder_quantized_al4.onnx \
      --out onnx/eg2_audio_q8_layers.onnx
"""
from __future__ import annotations

import argparse
import os

import onnx


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--layers", default=",".join(str(8 + 9 * i) for i in range(12)),
                    help="layer i의 텐서 이름 접미사 숫자 목록 (type_as_N)")
    ap.add_argument("--out-proj", default="linear_133")
    args = ap.parse_args()

    names = [f"type_as_{x}" for x in args.layers.split(",")]
    model = onnx.load(args.src)
    existing = {o.name for o in model.graph.output}

    for i, src_name in enumerate(names):
        out_name = f"aud_h_l{i:02d}"
        if out_name in existing:
            continue
        model.graph.node.append(onnx.helper.make_node("Identity", [src_name], [out_name], name=f"id_{out_name}"))
        model.graph.output.append(onnx.helper.make_tensor_value_info(out_name, onnx.TensorProto.FLOAT, None))

    model.graph.node.append(onnx.helper.make_node("Identity", [args.out_proj], ["aud_out_proj"], name="id_aud_out_proj"))
    model.graph.output.append(onnx.helper.make_tensor_value_info("aud_out_proj", onnx.TensorProto.FLOAT, None))

    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    data_name = os.path.basename(out) + "_data"
    for f in (out, os.path.join(os.path.dirname(out), data_name)):
        if os.path.exists(f):
            os.remove(f)
    onnx.save_model(model, out, save_as_external_data=True, all_tensors_to_one_file=True,
                    location=data_name, size_threshold=1024)
    print("saved", out, os.path.getsize(out), os.path.getsize(os.path.join(os.path.dirname(out), data_name)))
    print("outputs", [o.name for o in model.graph.output])


if __name__ == "__main__":
    main()
