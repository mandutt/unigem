"""EG2 오디오 타워 → ONNX (soft token + 층별 hidden) export.

입력 (기존 운영 그래프와 동일):
    input_features       f32  [B, T_mel, 128]
    input_features_mask  bool [B, T_mel]

출력:
    audio_features  f32 [N, 512]     유효 토큰만 평탄화 (기존 소비자 호환)
    audio_mask      bool [B, T]      타워 출력 기준 유효 마스크
    aud_h_l{NN}     f32 [B, T, 1024] 타워 encoder layer 출력 (pre output_proj)
    aud_out_proj    f32 [B, T, 1536] output_proj 이후 (embed_audio 입력)
    aud_last_hidden f32 [B, T, 1536] = aud_out_proj (별칭, 계약 명시용)

주의:
    - audio_features 는 embed_audio(1536→512) 투영 후 값이다 (텍스트 백본의 audio_features 입력과 동일 공간).
    - FP16 금지. export는 float32.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Iterable

import torch
import torch.nn as nn
import torch.nn.functional as F
from safetensors.torch import load_file
from transformers import AutoConfig
from transformers.models.embedding_gemma2.modeling_embedding_gemma2 import (
    EmbeddingGemma2MultimodalEmbedder,
)
from transformers.models.gemma4.modeling_gemma4 import Gemma4AudioModel

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Gemma4AudioAttention._convert_to_block / _extract_block_context 는 F.pad(..., value 생략)을 쓴다.
# PyTorch tracer는 value=None을 NoneType 상수로 굳혀 ONNX Pad 노드를 무효화한다
# (legacy export 실패 원인). export 동안만 기본값 0.0을 명시한다.
_ORIG_PAD = F.pad


def _pad_with_default(input, pad, mode="constant", value=None):
    if value is None:
        value = 0.0
    return _ORIG_PAD(input, pad, mode, value)


F.pad = _pad_with_default


class AudioGraph(nn.Module):
    def __init__(self, tower: Gemma4AudioModel, embed: EmbeddingGemma2MultimodalEmbedder,
                 layers: Iterable[int]):
        super().__init__()
        self.tower = tower
        self.embed = embed
        self.layers = tuple(layers)

    def forward(self, input_features: torch.Tensor, input_features_mask: torch.Tensor):
        captured: dict[int, torch.Tensor] = {}

        def make_hook(index: int):
            def hook(_module, _args, output):
                captured[index] = output[0] if isinstance(output, tuple) else output
            return hook

        handles = [layer.register_forward_hook(make_hook(i)) for i, layer in enumerate(self.tower.layers)]
        try:
            out = self.tower(input_features=input_features, attention_mask=input_features_mask)
        finally:
            for h in handles:
                h.remove()

        last = out.last_hidden_state              # [B, T, 1536]
        mask = out.attention_mask                 # [B, T] bool
        soft = self.embed(inputs_embeds=last)     # [B, T, 512]

        selected = [captured[i] for i in self.layers]
        return tuple([soft, mask] + selected + [last])

    def output_names(self) -> list[str]:
        names = ["audio_soft_tokens", "audio_mask"]
        names += [f"aud_h_l{i:02d}" for i in self.layers]
        names += ["aud_out_proj"]
        return names


def load_audio_parts(ckpt_dir: str, dtype: torch.dtype = torch.float32):
    cfg = AutoConfig.from_pretrained(ckpt_dir)
    tower = Gemma4AudioModel(cfg.audio_config)
    embed = EmbeddingGemma2MultimodalEmbedder(cfg.audio_config, cfg.text_config)
    sd = load_file(os.path.join(ckpt_dir, "model.safetensors"))
    tower_sd = {k[len("audio_tower."):]: v for k, v in sd.items() if k.startswith("audio_tower.")}
    embed_sd = {k[len("embed_audio."):]: v for k, v in sd.items() if k.startswith("embed_audio.")}
    if not tower_sd or not embed_sd:
        raise RuntimeError("audio_tower.* / embed_audio.* 가중치를 찾지 못했습니다")
    m1 = tower.load_state_dict(tower_sd, strict=False)
    m2 = embed.load_state_dict(embed_sd, strict=False)
    for name, res in (("tower", m1), ("embed", m2)):
        bad = [k for k in res.missing_keys if "rotary" not in k and "inv_freq" not in k]
        if bad or res.unexpected_keys:
            raise RuntimeError(f"{name} state_dict 불일치: missing={bad[:8]} unexpected={list(res.unexpected_keys)[:8]}")
    return tower.to(dtype).eval(), embed.to(dtype).eval()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default=os.path.join(PROJECT_ROOT, "data", "models",
                                                   "embeddinggemma-2-f9972ac2"))
    ap.add_argument("--out", default=os.path.join(PROJECT_ROOT, "onnx", "eg2_audio_research_fp32.onnx"))
    ap.add_argument("--layers", default="0,4,8,11")
    ap.add_argument("--mel", type=int, default=500)
    ap.add_argument("--opset", type=int, default=21)
    ap.add_argument("--exporter", choices=["legacy", "dynamo"], default="legacy")
    ap.add_argument("--static", action="store_true",
                    help="정적 shape으로 export (Unfold가 dynamic size를 지원하지 않는 legacy 경로용)")
    args = ap.parse_args()

    layers = [int(x) for x in args.layers.split(",") if x != ""]
    print(f"loading audio tower from {args.ckpt}", flush=True)
    tower, embed = load_audio_parts(args.ckpt)
    graph = AudioGraph(tower, embed, layers).eval()

    b, t = 1, args.mel
    feats = torch.zeros((b, t, 128), dtype=torch.float32)
    mask = torch.ones((b, t), dtype=torch.bool)

    print("dry-run forward", flush=True)
    with torch.no_grad():
        outs = graph(feats, mask)
    for n, tensor in zip(graph.output_names(), outs):
        print(f"  {n}: {tuple(tensor.shape)} {tensor.dtype}")

    print("exporting", flush=True)
    export_kwargs = dict(
        input_names=["input_features", "input_features_mask"],
        output_names=graph.output_names(),
        opset_version=args.opset,
        dynamo=(args.exporter == "dynamo"),
    )
    if args.exporter == "dynamo":
        # 정적 그래프에서 ONNX optimize 단계가 Clip min 상수를 지워 invalid 모델을 만든다(실측).
        export_kwargs["optimize"] = False
    if not args.static:
        export_kwargs["dynamic_axes"] = {
            "input_features": {0: "batch", 1: "mel_frames"},
            "input_features_mask": {0: "batch", 1: "mel_frames"},
            "audio_soft_tokens": {0: "batch", 1: "audio_tokens"},
            "audio_mask": {0: "batch", 1: "audio_tokens"},
            **{f"aud_h_l{i:02d}": {0: "batch", 1: "audio_tokens"} for i in layers},
            "aud_out_proj": {0: "batch", 1: "audio_tokens"},
        }
    if args.exporter == "legacy":
        # PyTorch #104067: autograd.Function inlining이 IndexError(invalid unordered_map)를 유발한다.
        export_kwargs["autograd_inlining"] = False
    torch.onnx.export(graph, (feats, mask), args.out, **export_kwargs)
    print("saved", args.out, os.path.getsize(args.out))

    meta = {"ckpt": args.ckpt, "layers": layers, "opset": args.opset,
            "outputs": graph.output_names(), "dtype": "float32"}
    with open(args.out + ".meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
