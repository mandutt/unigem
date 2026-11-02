"""C0 — EG2 vs T5Gemma 2 토크나이저 비교 + 디코더 구성 확인.

- tokenizer.json 해시·어휘 크기·토큰 집합 일치율
- 샘플 문장 분할 일치율(ko/en/ja/zh)
- T5Gemma 2 config에서 decoder 차원·층·LM head 크기 확인
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer

ROOT = r"C:\code\unigem"
OUT = os.path.join(ROOT, "logs", "C0_tokenizer.json")
EG2 = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2", "tokenizer.json")
T5G = "google/t5gemma-2-270m-270m"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    t5_tok = hf_hub_download(T5G, "tokenizer.json")
    t5_cfg = hf_hub_download(T5G, "config.json")
    a = Tokenizer.from_file(EG2)
    b = Tokenizer.from_file(t5_tok)
    va, vb = a.get_vocab(), b.get_vocab()
    sa, sb = set(va), set(vb)
    inter = len(sa & sb)

    sents = [
        "서버 eg2-1의 api 버전은 v2.15.0입니다.",
        "The quick brown fox jumps over the lazy dog.",
        "東京都の天気は晴れです。",
        "今天的会议决定回滚部署。",
        "사용자 김민수는 2026-11-02에 로그인했습니다.",
        "error code E4312 at /var/log/app.log",
    ]
    agree = 0
    for s in sents:
        ia = a.encode(s).tokens
        ib = b.encode(s).tokens
        if ia == ib:
            agree += 1

    cfg = json.load(open(t5_cfg, encoding="utf-8"))
    out = {
        "eg2": {"path": EG2, "sha256": sha(EG2), "vocab": len(va)},
        "t5gemma2": {"repo": T5G, "path": t5_tok, "sha256": sha(t5_tok), "vocab": len(vb)},
        "vocab_intersection": inter,
        "vocab_jaccard": inter / len(sa | sb),
        "segmentation_agreement": f"{agree}/{len(sents)}",
        "sample_segmentation": [{"text": s, "eg2": a.encode(s).tokens[:12],
                                "t5": b.encode(s).tokens[:12]} for s in sents],
        "t5_config_keys": {k: cfg[k] for k in cfg if "d_model" in k or "decoder" in k and "num" in k
                           or k in ("vocab_size", "d_kv", "num_layers", "num_decoder_layers")},
    }
    print(json.dumps({k: v for k, v in out.items() if k != "sample_segmentation"}, ensure_ascii=False, indent=2))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
