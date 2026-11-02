"""G-C2a — FLEURS ko 382클립, EG2 Q8 ONNX 오디오 특징으로 교체 후 CER."""
from __future__ import annotations

import csv
import json
import os
import sys
import time

ROOT = r"C:\code\unigem"
sys.path.insert(0, os.path.join(ROOT, "runner"))
sys.path.insert(0, os.path.join(ROOT, "vendor", "notesoop"))
sys.path.insert(0, os.path.join(ROOT, "vendor", "notesoop", "src"))

import jiwer  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from run_inference import EmbeddingGemmaSTT, load_audio  # noqa: E402
from dataset import normalize_text  # noqa: E402
import gc2a_patch  # noqa: E402

SRC = r"C:\code\eg2-langidentifier\data\raw\fleurs_cache"
AUD = os.path.join(ROOT, "data", "c2a1", "audio", "fleurs")
OUT = os.path.join(ROOT, "logs", "C2_A1")
ONNX = os.path.join(ROOT, "onnx", "eg2_audio_q8_layers.onnx")


def main():
    refs = {}
    with open(os.path.join(SRC, "ko_kr_test.tsv"), encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t"):
            if len(row) >= 3 and row[1].endswith(".wav"):
                refs[row[1]] = row[2]
    rows = [{"id": f[:-4], "audio": os.path.join(AUD, f), "ref": refs[f]}
            for f in sorted(os.listdir(AUD)) if f.endswith(".wav") and f in refs]

    stt = EmbeddingGemmaSTT(device="cpu", use_kenlm=False)
    ex = stt.extractor
    # 특징 충실도(처음 30클립)
    cos = []
    patched = False
    for r in rows[:30]:
        wav, _ = load_audio(r["audio"])
        pre = ex.preprocess_audio_cpu(wav)
        with torch.no_grad():
            a = ex.extract_from_preprocessed(*pre).float().numpy()
        if not patched:
            gc2a_patch.patch(stt, ONNX); patched = True
        with torch.no_grad():
            b = ex.extract_from_preprocessed(*pre).float().numpy()
        cos.append(float(np.sum(a * b, axis=1).mean()))
    print("feature_cos mean", round(float(np.mean(cos)), 6), "min", round(float(np.min(cos)), 6), flush=True)

    pred = os.path.join(OUT, "gc2a_pred.jsonl")
    done = set()
    if os.path.exists(pred):
        done = {json.loads(l)["id"] for l in open(pred, encoding="utf-8")}
    todo = [r for r in rows if r["id"] not in done]
    with open(pred, "a", encoding="utf-8") as f:
        for i, r in enumerate(todo, 1):
            hyp, rtf = stt.transcribe(r["audio"], chunk_sec=16.0, overlap_sec=1.0, batch_size=1)
            f.write(json.dumps({"id": r["id"], "ref": r["ref"], "hyp": hyp, "rtf": rtf}, ensure_ascii=False) + "\n")
            f.flush()
            if i % 50 == 0:
                print("progress", i, "/", len(todo), flush=True)
    recs = [json.loads(l) for l in open(pred, encoding="utf-8")]
    keep = [(normalize_text(r["ref"]).strip(), normalize_text(r["hyp"]).strip()) for r in recs]
    keep = [(a, b) for a, b in keep if a]
    res = {"n": len(keep), "cer": jiwer.cer([a for a, _ in keep], [b for _, b in keep]),
           "cer_nospace": jiwer.cer([a.replace(" ", "") for a, _ in keep], [b.replace(" ", "") for _, b in keep]),
           "wer": jiwer.wer([a for a, _ in keep], [b for _, b in keep]),
           "rtf_mean": float(np.mean([r["rtf"] for r in recs])),
           "feature_cos_mean": float(np.mean(cos)), "feature_cos_min": float(np.min(cos))}
    json.dump(res, open(os.path.join(OUT, "gc2a_cer.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(res, ensure_ascii=False, indent=1), flush=True)


if __name__ == "__main__":
    main()
