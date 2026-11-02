"""C2-A1 — Notesoop-STT-Ko-v1 기준선 CER (Zeroth 457 + Kspon eval_clean 100)."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

ROOT = r"C:\code\unigem"
V = os.path.join(ROOT, "vendor", "notesoop")
sys.path.insert(0, V)
sys.path.insert(0, os.path.join(V, "src"))

import numpy as np  # noqa: E402
import jiwer  # noqa: E402
from run_inference import EmbeddingGemmaSTT  # noqa: E402
from dataset import normalize_text  # noqa: E402

OUT = os.path.join(ROOT, "logs", "C2_A1")
MANIFEST = os.path.join(ROOT, "data", "c2a1", "manifest.json")


def norm(s):
    return normalize_text(s).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rows = json.load(open(MANIFEST, encoding="utf-8"))
    if a.limit:
        rows = rows[:a.limit]
    pred_path = os.path.join(a.out, "pred.jsonl")
    done = set()
    if os.path.exists(pred_path):
        for line in open(pred_path, encoding="utf-8"):
            done.add(json.loads(line)["id"])
    todo = [r for r in rows if r["id"] not in done]
    print("todo", len(todo), "done", len(done), flush=True)

    m = EmbeddingGemmaSTT(device="cpu", use_kenlm=False)
    print("model loaded", flush=True)
    with open(pred_path, "a", encoding="utf-8") as f:
        for i, r in enumerate(todo, 1):
            t0 = time.time()
            try:
                hyp, rtf = m.transcribe(r["audio"], chunk_sec=16.0, overlap_sec=1.0, batch_size=1)
            except Exception as e:
                hyp, rtf = "", -1.0
                print("ERR", r["id"], type(e).__name__, str(e)[:120], flush=True)
            rec = {"id": r["id"], "source": r["source"], "ref": r["ref"], "hyp": hyp,
                   "dur": r["dur"], "rtf": rtf, "elapsed": round(time.time() - t0, 2)}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
            if i % 20 == 0:
                print("progress", i, "/", len(todo), flush=True)

    recs = [json.loads(l) for l in open(pred_path, encoding="utf-8")]
    by = {}
    for s in sorted({r["source"] for r in recs}):
        rs = [r for r in recs if r["source"] == s]
        refs = [norm(r["ref"]) for r in rs]
        hyps = [norm(r["hyp"]) for r in rs]
        keep = [(a, b) for a, b in zip(refs, hyps) if a]
        cer = jiwer.cer([a for a, _ in keep], [b for _, b in keep])
        cer_ns = jiwer.cer([a.replace(" ", "") for a, _ in keep], [b.replace(" ", "") for _, b in keep])
        wer = jiwer.wer([a for a, _ in keep], [b for _, b in keep])
        by[s] = {"n": len(keep), "cer": cer, "cer_nospace": cer_ns, "wer": wer,
                 "rtf_mean": float(np.mean([r["rtf"] for r in rs if r["rtf"] > 0])) if rs else None}
    all_ref = [norm(r["ref"]) for r in recs]
    all_hyp = [norm(r["hyp"]) for r in recs]
    keep = [(a, b) for a, b in zip(all_ref, all_hyp) if a]
    res = {"n": len(keep), "by_source": by,
           "cer": jiwer.cer([a for a, _ in keep], [b for _, b in keep]),
           "cer_nospace": jiwer.cer([a.replace(" ", "") for a, _ in keep], [b.replace(" ", "") for _, b in keep]),
           "wer": jiwer.wer([a for a, _ in keep], [b for _, b in keep]),
           "rtf_mean": float(np.mean([r["rtf"] for r in recs if r["rtf"] > 0]))}
    json.dump(res, open(os.path.join(a.out, "cer.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(res, ensure_ascii=False, indent=1), flush=True)


if __name__ == "__main__":
    main()
