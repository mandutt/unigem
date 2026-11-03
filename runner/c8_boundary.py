"""C-8 — 청크 경계(16s/1s vs 8s/0.5s) 중복·누락 점검."""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

import numpy as np
import soundfile as sf

ROOT = r"C:\code\unigem"
V = os.path.join(ROOT, "vendor", "notesoop")
sys.path.insert(0, V)
sys.path.insert(0, os.path.join(V, "src"))

import jiwer  # noqa: E402
from run_inference import EmbeddingGemmaSTT  # noqa: E402

OUT = os.path.join(ROOT, "logs", "C8", "boundary.json")


def norm(s: str) -> str:
    import re
    s = s.lower()
    s = re.sub(r"[^\w\s가-힣]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def grams(s: str, n=4):
    s = s.replace(" ", "")
    return Counter(s[i:i + n] for i in range(max(0, len(s) - n + 1)))


def main():
    man = json.load(open(os.path.join(ROOT, "data", "c2a1", "manifest.json"), encoding="utf-8"))
    rows = sorted(man, key=lambda r: -r.get("dur", 0))[:15]
    groups = [rows[i:i + 3] for i in range(0, 15, 3)]
    m = EmbeddingGemmaSTT(device="cpu", use_kenlm=False)
    res = []
    tmpdir = os.path.join(ROOT, "cache", "c8_boundary")
    os.makedirs(tmpdir, exist_ok=True)
    for gi, g in enumerate(groups, 1):
        pcm = []
        for r in g:
            x, sr = sf.read(r["audio"], dtype="float32")
            pcm.append(np.asarray(x, np.float32))
        audio = np.concatenate(pcm)
        path = os.path.join(tmpdir, f"g{gi}.wav")
        sf.write(path, audio, 16000)
        ref = norm(" ".join(r["ref"] for r in g))
        h1, rtf1 = m.transcribe(path, chunk_sec=16.0, overlap_sec=1.0, batch_size=1)
        h2, rtf2 = m.transcribe(path, chunk_sec=8.0, overlap_sec=0.5, batch_size=1)
        a, b = norm(h1), norm(h2)
        c1 = jiwer.cer(ref.replace(" ", ""), a.replace(" ", ""))
        c2 = jiwer.cer(ref.replace(" ", ""), b.replace(" ", ""))
        g1, g2 = grams(a), grams(b)
        inter = sum((g1 & g2).values())
        dup = sum(v - 1 for v in g2.values() if v > 1) / max(1, sum(g2.values()))
        res.append({"id": f"g{gi}", "dur": round(len(audio) / 16000, 1), "cer_16_1": round(c1, 4),
                    "cer_8_0.5": round(c2, 4), "char_16": len(a), "char_8": len(b),
                    "gram_overlap": round(inter / max(1, sum(g2.values())), 3),
                    "repeat_rate_8": round(dup, 3), "rtf_16": round(rtf1, 3), "rtf_8": round(rtf2, 3)})
        print(res[-1], flush=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
