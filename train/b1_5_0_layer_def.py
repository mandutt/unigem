"""B1.5-0 — 층 정의 확인.

질문: ONNX `tok_h_l00`은 무엇인가? (임베딩 출력 vs 첫 블록 출력)
방법:
  1) PyTorch(bf16)로 embed_tokens 출력과 각 블록 출력을 덤프
  2) ONNX(FP32)로 같은 문장을 실행해 층별 cosine 비교
  3) 동일 토큰의 문맥 간 변동을 임베딩/블록0/ONNX l00에서 비교

사용:
  python train/b1_5_0_layer_def.py --mode torch
  python train/b1_5_0_layer_def.py --mode onnx
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np

ROOT = r"C:\code\unigem"
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
ONNX = os.path.join(ROOT, "onnx", "eg2_text_research_fp32.onnx")
OUT = os.path.join(ROOT, "logs", "B1_5_0")
SENTS = [
    "서버 eg2-1의 api 버전은 v2.15.0이고 2026-11-02 09:30에 배포했습니다.",
    "The worker on node-7 failed with error code E4312 at /var/log/app.log.",
    "회의에서 롤백을 결정했고 커밋 1a2b3c4d에서 12개 파일이 변경되었습니다.",
]
LAYERS = [0, 4, 8, 11]  # 모델이 12층일 때의 대표 층


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["torch", "onnx"], required=True)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    encs = [tok.encode(s) for s in SENTS]
    ids_list = [e.ids[:64] for e in encs]
    np.save(os.path.join(OUT, "ids.npy"), np.array(ids_list, dtype=object), allow_pickle=True)
    print("ids", [len(x) for x in ids_list])
    print("post_processor", tok.post_processor)

    if args.mode == "torch":
        import torch
        from safetensors.torch import load_file
        from transformers import AutoConfig
        from transformers.models.embedding_gemma2.modeling_embedding_gemma2 import (
            EmbeddingGemma2TextModel,
        )

        cfg = AutoConfig.from_pretrained(CKPT)
        tm = EmbeddingGemma2TextModel(cfg.text_config)
        sd = load_file(os.path.join(CKPT, "model.safetensors"))
        sub = {k[len("language_model."):]: v for k, v in sd.items() if k.startswith("language_model.")}
        missing, unexpected = tm.load_state_dict(sub, strict=False)
        tm = tm.to(torch.bfloat16).eval()
        print("layers", len(tm.layers))

        caps = {}

        def mk(i):
            def h(_m, _a, out):
                caps.setdefault(i, []).append(
                    (out[0] if isinstance(out, tuple) else out)[0].float().numpy())
            return h

        handles = [l.register_forward_hook(mk(i)) for i, l in enumerate(tm.layers)]
        emb_list = []
        try:
            for ids in ids_list:
                t = torch.tensor([ids], dtype=torch.long)
                with torch.no_grad():
                    emb = tm.embed_tokens(t)[0].float().numpy()
                    tm(inputs_embeds=tm.embed_tokens(t), attention_mask=torch.ones_like(t))
                emb_list.append(emb)
        finally:
            for h in handles:
                h.remove()

        def stack_pad(arrs):
            m = max(a.shape[0] for a in arrs)
            out = np.zeros((len(arrs), m, arrs[0].shape[1]), np.float32)
            for i, a in enumerate(arrs):
                out[i, :a.shape[0]] = a
            return out

        np.savez_compressed(os.path.join(OUT, "torch.npz"),
                            emb=stack_pad(emb_list),
                            lengths=np.array([len(x) for x in ids_list]),
                            **{f"l{i}": stack_pad(caps[i]) for i in LAYERS},
                            **{f"all{i}": stack_pad(v) for i, v in caps.items()})
        print("saved torch.npz", {k: len(v) for k, v in caps.items() if k in LAYERS})

    else:
        import onnxruntime as ort
        so = ort.SessionOptions()
        so.intra_op_num_threads = 6
        so.log_severity_level = 3
        sess = ort.InferenceSession(ONNX, so, providers=["CPUExecutionProvider"])
        names = [o.name for o in sess.get_outputs()]
        out = {}
        for i, ids in enumerate(ids_list):
            arr = np.array([ids], dtype=np.int64)
            feats = {
                "input_ids": arr,
                "attention_mask": np.ones_like(arr),
                "image_features": np.zeros((0, 512), np.float32),
                "video_features": np.zeros((0, 512), np.float32),
                "audio_features": np.zeros((0, 512), np.float32),
            }
            o = dict(zip(names, sess.run(None, feats)))
            for k, v in o.items():
                out.setdefault(k, []).append(v[0])

        def stack_pad(arrs):
            m = max(a.shape[0] for a in arrs)
            res = np.zeros((len(arrs), m) + arrs[0].shape[1:], np.float32)
            for i, a in enumerate(arrs):
                res[i, :a.shape[0]] = a
            return res

        np.savez_compressed(os.path.join(OUT, "onnx.npz"),
                            **{k: stack_pad(v) for k, v in out.items()})
        print("saved onnx.npz", list(out)[:6])


if __name__ == "__main__":
    main()
