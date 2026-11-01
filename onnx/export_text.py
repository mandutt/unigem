"""EG2 텍스트 백본 → ONNX (다층 hidden + pooled) export.

설계 근거: docs/phase_a_plan.md §3 (ONNX I/O 계약 초안), docs/plan_v0_5.md §9 A2.

입력 (기존 운영 그래프와 동일 인터페이스):
    input_ids        int64   [B, S]
    attention_mask   int64   [B, S]
    image_features   f32     [N_i, 512]   (soft token, 없으면 [0,512])
    video_features   f32     [N_v, 512]
    audio_features   f32     [N_a, 512]   (오디오 타워 soft token, 투영 후 512)

출력:
    sentence_embedding f32 [B, 768]  mean-pool(attention_mask) + L2 normalize
    tok_h_l{NN}        f32 [B, S, 512]  encoder layer NN 출력 (pre-final-norm)
    tok_h_last         f32 [B, S, 512]  final RMSNorm 이후 (pre-projection)
    tok_emb_768        f32 [B, S, 768]  embedding_projection 이후 (= 기존 last_hidden_state)

주의:
    - FP16 사용 금지. 체크포인트는 bf16이지만 export는 float32로 한다.
    - vision/audio 타워는 이 그래프에 포함하지 않는다(soft token을 입력으로 받는다).
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Iterable

import torch
import torch.nn as nn
from safetensors.torch import load_file
from transformers import AutoConfig
from transformers.models.embedding_gemma2.modeling_embedding_gemma2 import (
    EmbeddingGemma2TextModel,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TextGraph(nn.Module):
    def __init__(self, text_model: EmbeddingGemma2TextModel, layers: Iterable[int],
                 special_token_ids: dict[str, int]):
        super().__init__()
        self.tm = text_model
        self.layers = tuple(layers)
        self.image_token_id = int(special_token_ids["image_token_id"])
        self.video_token_id = int(special_token_ids["video_token_id"])
        self.audio_token_id = int(special_token_ids["audio_token_id"])
        self.pad_token_id = int(special_token_ids["pad_token_id"])

    @staticmethod
    def _scatter(emb: torch.Tensor, mask: torch.Tensor, feats: torch.Tensor) -> torch.Tensor:
        m = mask.unsqueeze(-1).expand_as(emb)
        return emb.masked_scatter(m, feats.to(emb.dtype))

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        image_features: torch.Tensor,
        video_features: torch.Tensor,
        audio_features: torch.Tensor,
    ):
        tm = self.tm
        image_mask = input_ids == self.image_token_id
        video_mask = input_ids == self.video_token_id
        audio_mask = input_ids == self.audio_token_id
        multimodal = image_mask | video_mask | audio_mask

        llm_ids = torch.where(
            multimodal, torch.full_like(input_ids, self.pad_token_id), input_ids
        )
        emb = tm.embed_tokens(llm_ids)
        emb = self._scatter(emb, image_mask, image_features)
        emb = self._scatter(emb, video_mask, video_features)
        emb = self._scatter(emb, audio_mask, audio_features)

        captured: dict[int, torch.Tensor] = {}

        def make_hook(index: int):
            def hook(_module, _args, output):
                captured[index] = output[0] if isinstance(output, tuple) else output
            return hook

        handles = [layer.register_forward_hook(make_hook(i)) for i, layer in enumerate(tm.layers)]
        try:
            tm(inputs_embeds=emb, attention_mask=attention_mask)
        finally:
            for h in handles:
                h.remove()

        last_pre = captured[len(tm.layers) - 1]
        last_norm = tm.norm(last_pre)
        proj = tm.embedding_projection(last_norm)
        selected = [captured[i] for i in self.layers]


        mask = attention_mask.unsqueeze(-1).to(proj.dtype)
        pooled = (proj * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1.0)
        sentence = torch.nn.functional.normalize(pooled, p=2, dim=-1)

        outs = [sentence]
        outs.extend(selected)          # tok_h_l{NN}
        outs.append(last_norm)         # tok_h_last
        outs.append(proj)              # tok_emb_768
        return tuple(outs)

    def output_names(self) -> list[str]:
        names = ["sentence_embedding"]
        names += [f"tok_h_l{i:02d}" for i in self.layers]
        names += ["tok_h_last", "tok_emb_768"]
        return names


def special_token_ids(ckpt_dir: str) -> dict[str, int]:
    cfg = AutoConfig.from_pretrained(ckpt_dir)
    return {
        "image_token_id": cfg.image_token_id,
        "video_token_id": cfg.video_token_id,
        "audio_token_id": cfg.audio_token_id,
        "pad_token_id": cfg.text_config.pad_token_id,
    }


def load_text_model(ckpt_dir: str, dtype: torch.dtype = torch.float32) -> EmbeddingGemma2TextModel:
    cfg = AutoConfig.from_pretrained(ckpt_dir)
    tm = EmbeddingGemma2TextModel(cfg.text_config)
    sd = load_file(os.path.join(ckpt_dir, "model.safetensors"))
    sub = {k[len("language_model."):]: v for k, v in sd.items() if k.startswith("language_model.")}
    if not sub:
        raise RuntimeError("language_model.* 가중치를 찾지 못했습니다")
    missing, unexpected = tm.load_state_dict(sub, strict=False)
    real_missing = [k for k in missing if "rotary" not in k and "inv_freq" not in k]
    if real_missing or unexpected:
        raise RuntimeError(f"state_dict 불일치: missing={real_missing[:8]} unexpected={unexpected[:8]}")
    tm = tm.to(dtype).eval()
    return tm


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default=os.path.join(PROJECT_ROOT, "data", "models",
                                                   "embeddinggemma-2-f9972ac2"))
    ap.add_argument("--out", default=os.path.join(PROJECT_ROOT, "onnx", "eg2_text_research_fp32.onnx"))
    ap.add_argument("--layers", default="0,4,8,12,16,20")
    ap.add_argument("--seq", type=int, default=16)
    ap.add_argument("--opset", type=int, default=21)
    args = ap.parse_args()

    layers = [int(x) for x in args.layers.split(",") if x != ""]
    print(f"loading text model from {args.ckpt}", flush=True)
    tm = load_text_model(args.ckpt)
    graph = TextGraph(tm, layers, special_token_ids(args.ckpt)).eval()

    b, s = 1, args.seq
    ids = torch.randint(3, 200000, (b, s), dtype=torch.long)
    am = torch.ones((b, s), dtype=torch.long)
    empty = torch.zeros((0, 512), dtype=torch.float32)

    print("dry-run forward", flush=True)
    with torch.no_grad():
        outs = graph(ids, am, empty, empty, empty)
    for n, t in zip(graph.output_names(), outs):
        print(f"  {n}: {tuple(t.shape)} {t.dtype}")

    print("exporting", flush=True)
    torch.onnx.export(
        graph,
        (ids, am, empty, empty, empty),
        args.out,
        input_names=["input_ids", "attention_mask", "image_features", "video_features", "audio_features"],
        output_names=graph.output_names(),
        opset_version=args.opset,
        dynamo=True,
        dynamic_axes={
            "input_ids": {0: "batch", 1: "sequence"},
            "attention_mask": {0: "batch", 1: "sequence"},
            "image_features": {0: "num_image_tokens"},
            "video_features": {0: "num_video_tokens"},
            "audio_features": {0: "num_audio_tokens"},
            "sentence_embedding": {0: "batch"},
            **{f"tok_h_l{i:02d}": {0: "batch", 1: "sequence"} for i in layers},
            "tok_h_last": {0: "batch", 1: "sequence"},
            "tok_emb_768": {0: "batch", 1: "sequence"},
        },
    )
    print("saved", args.out, os.path.getsize(args.out))

    meta = {
        "ckpt": args.ckpt,
        "layers": layers,
        "opset": args.opset,
        "outputs": graph.output_names(),
        "dtype": "float32",
    }
    with open(args.out + ".meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
