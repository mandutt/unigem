"""G-C2 재측정 — FLEURS ko 382클립, KenLM 빔서치 디코더."""
from __future__ import annotations

import csv
import json
import os
import sys

ROOT = r"C:\code\unigem"
sys.path.insert(0, os.path.join(ROOT, "vendor", "notesoop"))
sys.path.insert(0, os.path.join(ROOT, "vendor", "notesoop", "src"))

import jiwer  # noqa: E402
import numpy as np  # noqa: E402
from run_inference import EmbeddingGemmaSTT  # noqa: E402
from dataset import normalize_text  # noqa: E402

SRC = r"C:\code\eg2-langidentifier\data\raw\fleurs_cache"
AUD = os.path.join(ROOT, "data", "c2a1", "audio", "fleurs")
OUT = os.path.join(ROOT, "logs", "C2_A1")


def main():
    refs = {}
    with open(os.path.join(SRC, "ko_kr_test.tsv"), encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t"):
            if len(row) >= 3 and row[1].endswith(".wav"):
                refs[row[1]] = row[2]
    rows = [{"id": f[:-4], "audio": os.path.join(AUD, f), "ref": refs[f]}
            for f in sorted(os.listdir(AUD)) if f.endswith(".wav") and f in refs]
    pred = os.path.join(OUT, "fleurs_kenlm_tuned_pred.jsonl")
    done = {json.loads(l)["id"] for l in open(pred, encoding="utf-8")} if os.path.exists(pred) else set()
    todo = [r for r in rows if r["id"] not in done]
    m = EmbeddingGemmaSTT(device="cpu", use_kenlm=True, lm_alpha=0.5, lm_beta=1.0)
    with open(pred, "a", encoding="utf-8") as f:
        for i, r in enumerate(todo, 1):
            hyp, rtf = m.transcribe(r["audio"], chunk_sec=16.0, overlap_sec=1.0, batch_size=1)
            f.write(json.dumps({"id": r["id"], "ref": r["ref"], "hyp": hyp, "rtf": rtf}, ensure_ascii=False) + "\n")
            f.flush()
            if i % 25 == 0:
                print("progress", i, "/", len(todo), flush=True)
    recs = [json.loads(l) for l in open(pred, encoding="utf-8")]
    keep = [(normalize_text(r["ref"]).strip(), normalize_text(r["hyp"]).strip()) for r in recs]
    keep = [(a, b) for a, b in keep if a]
    res = {"n": len(keep), "decoder": "kenlm_beam8_alpha0.5_beta1.0",
           "cer": jiwer.cer([a for a, _ in keep], [b for _, b in keep]),
           "cer_nospace": jiwer.cer([a.replace(" ", "") for a, _ in keep], [b.replace(" ", "") for _, b in keep]),
           "wer": jiwer.wer([a for a, _ in keep], [b for _, b in keep]),
           "rtf_mean": float(np.mean([r["rtf"] for r in recs]))}
    json.dump(res, open(os.path.join(OUT, "fleurs_kenlm_tuned_cer.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(res, ensure_ascii=False, indent=1), flush=True)


if __name__ == "__main__":
    main()
