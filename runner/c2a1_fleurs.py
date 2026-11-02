"""G-C2 — FLEURS ko test greedy CER (Notesoop, KenLM 없음)."""
from __future__ import annotations

import csv
import json
import os
import sys
import tarfile
import time

ROOT = r"C:\code\unigem"
V = os.path.join(ROOT, "vendor", "notesoop")
sys.path.insert(0, V); sys.path.insert(0, os.path.join(V, "src"))

import jiwer  # noqa: E402
from run_inference import EmbeddingGemmaSTT  # noqa: E402
from dataset import normalize_text  # noqa: E402

SRC = r"C:\code\eg2-langidentifier\data\raw\fleurs_cache"
OUT = os.path.join(ROOT, "logs", "C2_A1")
AUD = os.path.join(ROOT, "data", "c2a1", "audio", "fleurs")


def main():
    os.makedirs(AUD, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    tar = os.path.join(SRC, "ko_kr_test.tar.gz")
    with tarfile.open(tar) as t:
        for m in t.getmembers():
            if m.isfile() and m.name.endswith(".wav"):
                m.name = os.path.basename(m.name)
                t.extract(m, AUD)
    refs = {}
    with open(os.path.join(SRC, "ko_kr_test.tsv"), encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t"):
            if len(row) >= 3 and row[1].endswith(".wav"):
                refs[row[1]] = row[2]
    files = sorted(f for f in os.listdir(AUD) if f.endswith(".wav"))
    rows = [{"id": f[:-4], "audio": os.path.join(AUD, f), "ref": refs.get(f, "")} for f in files]
    rows = [r for r in rows if r["ref"]]
    print("clips", len(rows), "hours", round(sum(os.path.getsize(r["audio"]) / 32000 for r in rows) / 3600, 3), flush=True)

    pred_path = os.path.join(OUT, "fleurs_pred.jsonl")
    done = set()
    if os.path.exists(pred_path):
        done = {json.loads(l)["id"] for l in open(pred_path, encoding="utf-8")}
    todo = [r for r in rows if r["id"] not in done]
    m = EmbeddingGemmaSTT(device="cpu", use_kenlm=False)
    with open(pred_path, "a", encoding="utf-8") as f:
        for i, r in enumerate(todo, 1):
            hyp, rtf = m.transcribe(r["audio"], chunk_sec=16.0, overlap_sec=1.0, batch_size=1)
            f.write(json.dumps({"id": r["id"], "ref": r["ref"], "hyp": hyp, "rtf": rtf}, ensure_ascii=False) + "\n")
            f.flush()
            if i % 50 == 0:
                print("progress", i, "/", len(todo), flush=True)
    recs = [json.loads(l) for l in open(pred_path, encoding="utf-8")]
    refs_n = [normalize_text(r["ref"]).strip() for r in recs]
    hyps_n = [normalize_text(r["hyp"]).strip() for r in recs]
    keep = [(a, b) for a, b in zip(refs_n, hyps_n) if a]
    res = {"n": len(keep), "cer": jiwer.cer([a for a, _ in keep], [b for _, b in keep]),
           "cer_nospace": jiwer.cer([a.replace(" ", "") for a, _ in keep], [b.replace(" ", "") for _, b in keep]),
           "wer": jiwer.wer([a for a, _ in keep], [b for _, b in keep]),
           "rtf_mean": sum(r["rtf"] for r in recs) / len(recs)}
    json.dump(res, open(os.path.join(OUT, "fleurs_cer.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(res, ensure_ascii=False, indent=1), flush=True)


if __name__ == "__main__":
    main()
