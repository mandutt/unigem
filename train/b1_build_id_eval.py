"""B1 보강용 식별자 평가 코퍼스 (원 코퍼스와 다른 시드, 300문장).

FLEURS 없이 합성 슬롯만 사용해 식별자 span 밀도를 높인다.
"""
from __future__ import annotations

import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b1_build_corpus import synth  # noqa: E402

OUT = r"C:\code\unigem\data\b1\id_eval.jsonl"

rng = random.Random(7777)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    for i in range(200):
        f.write(json.dumps({"id": f"ideval-ko-{i:03d}", "lang": "ko_kr",
                            "kind": "synthetic", "text": synth(rng, "ko", i)}, ensure_ascii=False) + "\n")
    for i in range(100):
        f.write(json.dumps({"id": f"ideval-en-{i:03d}", "lang": "en_us",
                            "kind": "synthetic", "text": synth(rng, "en", i)}, ensure_ascii=False) + "\n")
print("wrote", OUT)
