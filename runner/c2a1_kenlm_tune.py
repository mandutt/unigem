"""KenLM alpha/beta 소규모 튜닝 — FLEURS 앞 80클립."""
from __future__ import annotations

import csv
import itertools
import json
import os
import sys

ROOT = r"C:\code\unigem"
sys.path.insert(0, os.path.join(ROOT, "vendor", "notesoop"))
sys.path.insert(0, os.path.join(ROOT, "vendor", "notesoop", "src"))

import jiwer  # noqa: E402
from run_inference import EmbeddingGemmaSTT  # noqa: E402
from dataset import normalize_text  # noqa: E402

SRC = r"C:\code\eg2-langidentifier\data\raw\fleurs_cache"
AUD = os.path.join(ROOT, "data", "c2a1", "audio", "fleurs")
OUT = os.path.join(ROOT, "logs", "C2_A1", "kenlm_tune.json")


def main():
    refs = {}
    for row in csv.reader(open(os.path.join(SRC, "ko_kr_test.tsv"), encoding="utf-8"), delimiter="\t"):
        if len(row) >= 3 and row[1].endswith(".wav"):
            refs[row[1]] = row[2]
    files = sorted(f for f in os.listdir(AUD) if f.endswith(".wav") and f in refs)[:80]
    rows = [{"id": f[:-4], "audio": os.path.join(AUD, f), "ref": refs[f]} for f in files]
    res = {}
    for alpha, beta in itertools.product([0.05, 0.12, 0.25, 0.5], [0.0, 0.4, 1.0]):
        m = EmbeddingGemmaSTT(device="cpu", use_kenlm=True, lm_alpha=alpha, lm_beta=beta)
        hs = []
        for r in rows:
            hyp, _ = m.transcribe(r["audio"], batch_size=1)
            hs.append((normalize_text(r["ref"]).strip(), normalize_text(hyp).strip()))
        keep = [(a, b) for a, b in hs if a]
        cer = jiwer.cer([a for a, _ in keep], [b for _, b in keep])
        res[f"a{alpha}_b{beta}"] = {"cer": cer, "n": len(keep)}
        print(alpha, beta, round(cer, 4), flush=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"), indent=2)
    best = min(res.items(), key=lambda kv: kv[1]["cer"])
    print("BEST", best, flush=True)


if __name__ == "__main__":
    main()
