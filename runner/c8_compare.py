"""C-8 마무리 — komixv2·whisper-turbo 비교, 청크 경계 점검."""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import re
import subprocess
import sys
import time

import jiwer

ROOT = r"C:\code\unigem"
FLEURS = os.path.join(ROOT, "data", "c2a1", "audio", "fleurs")
NOTESOOP = os.path.join(ROOT, "logs", "C2_A1", "fleurs_pred.jsonl")
OUT = os.path.join(ROOT, "logs", "C8")
KOMIX = r"C:\Users\mandu\AppData\Local\jev-mem\bench\run-20261024-embedgemma2ko\komixv2-ct2"
ASRB = r"C:\Users\mandu\AppData\Local\jev-mem\bench\run-20261024-embedgemma2ko\asr_bench"
WCLI = os.path.join(ASRB, "whispercpp", "Release", "whisper-cli.exe")
WGGML = os.path.join(ASRB, "ggml-large-v3-turbo-q4_k.bin")


def norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^\w\s가-힣]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def load_refs():
    rows = [json.loads(l) for l in open(NOTESOOP, encoding="utf-8")]
    return {r["id"]: r for r in rows}


def done_ids(path):
    if not os.path.exists(path):
        return set()
    return {json.loads(l)["id"] for l in open(path, encoding="utf-8")}


def run_komix(limit=None):
    from faster_whisper import WhisperModel
    import soundfile as sf
    refs = load_refs()
    out = os.path.join(OUT, "komix_pred.jsonl")
    os.makedirs(OUT, exist_ok=True)
    done = done_ids(out)
    ids = sorted(refs)[:limit] if limit else sorted(refs)
    todo = [i for i in ids if i not in done]
    print("komix todo", len(todo), flush=True)
    m = WhisperModel(KOMIX, device="cpu", compute_type="int8", cpu_threads=6)
    with open(out, "a", encoding="utf-8") as f:
        for n, i in enumerate(todo, 1):
            w = os.path.join(FLEURS, i + ".wav")
            a, sr = sf.read(w, dtype="float32")
            t0 = time.time()
            segs, info = m.transcribe(a, language="ko", beam_size=5, vad_filter=False,
                                      condition_on_previous_text=False)
            text = " ".join(s.text for s in segs).strip()
            dt = time.time() - t0
            f.write(json.dumps({"id": i, "hyp": text,
                                "rtf": dt / max(1e-9, info.duration)}, ensure_ascii=False) + "\n")
            f.flush()
            if n % 50 == 0:
                print("komix", n, "/", len(todo), flush=True)


def run_whisper(limit=None):
    refs = load_refs()
    out = os.path.join(OUT, "whisper_pred.jsonl")
    os.makedirs(OUT, exist_ok=True)
    done = done_ids(out)
    ids = sorted(refs)[:limit] if limit else sorted(refs)
    todo = [i for i in ids if i not in done]
    print("whisper todo", len(todo), flush=True)
    tmp = os.path.join(OUT, "wtmp")
    os.makedirs(tmp, exist_ok=True)
    with open(out, "a", encoding="utf-8") as f:
        for n, i in enumerate(todo, 1):
            w = os.path.join(FLEURS, i + ".wav")
            of = os.path.join(tmp, i)
            t0 = time.time()
            p = subprocess.run([WCLI, "-m", WGGML, "-f", w, "-l", "ko", "-t", "6", "-bs", "5",
                                "-otxt", "-of", of, "-np"], capture_output=True, text=True)
            dt = time.time() - t0
            txt = ""
            if os.path.exists(of + ".txt"):
                txt = open(of + ".txt", encoding="utf-8").read().strip()
                os.remove(of + ".txt")
            if p.returncode != 0:
                print("fail", i, p.returncode, flush=True)
                continue
            f.write(json.dumps({"id": i, "hyp": txt, "sec": dt}, ensure_ascii=False) + "\n")
            f.flush()
            if n % 25 == 0:
                print("whisper", n, "/", len(todo), flush=True)


def cer_pair(refs, hyp_map, ids):
    keep = [i for i in ids if norm(refs[i]["ref"])]
    a = [norm(refs[i]["ref"]) for i in keep]
    b = [norm(hyp_map[i]) for i in keep]
    return (jiwer.cer([x.replace(" ", "") for x in a], [y.replace(" ", "") for y in b]),
            jiwer.cer(a, b), jiwer.wer(a, b), keep)


def boot_ci(a, b, iters=1000, seed=0):
    rng = random.Random(seed)
    n = len(a)
    vals = []
    for _ in range(iters):
        idx = [rng.randrange(n) for _ in range(n)]
        vals.append(jiwer.cer([a[i].replace(" ", "") for i in idx], [b[i].replace(" ", "") for i in idx]))
    vals.sort()
    return vals[int(0.025 * iters)], vals[int(0.975 * iters)]


def stats():
    refs = load_refs()
    systems = {}
    npath = NOTESOOP
    systems["notesoop"] = {r["id"]: r["hyp"] for r in map(json.loads, open(npath, encoding="utf-8"))}
    for name in ("komix", "whisper"):
        p = os.path.join(OUT, f"{name}_pred.jsonl")
        if os.path.exists(p):
            systems[name] = {r["id"]: r["hyp"] for r in map(json.loads, open(p, encoding="utf-8"))}
    ids = sorted(set.intersection(*[set(v) for v in systems.values()]))
    print("common ids", len(ids), "systems", list(systems))
    res = {}
    for name, hyps in systems.items():
        ns, sp, w, keep = cer_pair(refs, hyps, ids)
        lo, hi = boot_ci([norm(refs[i]["ref"]) for i in keep], [norm(hyps[i]) for i in keep])
        res[name] = {"n": len(keep), "cer_nospace": ns, "cer_space": sp, "wer": w,
                     "ci95": [lo, hi]}
        print(name, res[name], flush=True)
    if "notesoop" in systems:
        base = [norm(systems["notesoop"][i]) for i in ids]
        for name in systems:
            if name == "notesoop":
                continue
            other = [norm(systems[name][i]) for i in ids]
            rng = random.Random(1)
            diffs = []
            for _ in range(1000):
                idx = [rng.randrange(len(ids)) for _ in range(len(ids))]
                diffs.append(jiwer.cer([base[i].replace(" ", "") for i in idx], [other[i].replace(" ", "") for i in idx]))
            diffs.sort()
            res[name]["diff_vs_notesoop"] = [diffs[25], diffs[975]]
            print(name, "diff CI", res[name]["diff_vs_notesoop"], flush=True)
    json.dump(res, open(os.path.join(OUT, "compare.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["komix", "whisper", "stats"])
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    {"komix": run_komix, "whisper": run_whisper, "stats": stats}[a.mode](a.limit) if a.mode != "stats" else stats()
