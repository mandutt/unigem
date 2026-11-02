"""R3 — 접두사 3조건 코퍼스 생성 (base / search query / search document)."""
from __future__ import annotations

import json
import os
import random

ROOT = r"C:\code\unigem"
SRC = os.path.join(ROOT, "data", "b1_5", "corpus_v2", "corpus.jsonl")
OUT = os.path.join(ROOT, "data", "r3")
PREFIX = {
    "query": "task: search result | query: ",
    "doc": "title: none | text: ",
}
N = 800


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = [json.loads(l) for l in open(SRC, encoding="utf-8")]
    rng = random.Random(20261108)
    by = {}
    for r in rows:
        by.setdefault(r["kind"], []).append(r)
    pick = []
    for k, v in by.items():
        rng.shuffle(v)
        pick += v[:max(1, int(N * len(v) / len(rows)))]
    rng.shuffle(pick)
    pick = pick[:N]
    for tag in ("base", "query", "doc"):
        with open(os.path.join(OUT, f"{tag}.jsonl"), "w", encoding="utf-8") as f:
            for i, r in enumerate(pick):
                text = r["text"] if tag == "base" else PREFIX[tag] + r["text"]
                f.write(json.dumps({"id": f"{tag}-{i:04d}", "text": text, "split": r["split"],
                                    "kind": r["kind"], "lang": r["lang"]}, ensure_ascii=False) + "\n")
    print("rows", len(pick), {k: sum(1 for r in pick if r["kind"] == k) for k in by})


if __name__ == "__main__":
    main()
