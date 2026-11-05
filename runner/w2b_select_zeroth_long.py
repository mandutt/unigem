"""Select 4h of additional Zeroth long (8-16s) utterances, excluding Wave 1 clips.

Wave 1 uses the first 1,534 accepted Zeroth records (`zeroth_000001` ...).
This script iterates the same parquet order, skips those records, and selects
4h of 8-16s clips for the non-Kspon long-domain control.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/wave2b"
AUDIO = OUT / "audio/long_4h_zeroth"
ZEROTH = ROOT / "data/raw/zeroth/data"
WAVE1 = ROOT / "data/wave1/manifest.jsonl"
VOCAB = ROOT / "data/wave2a_lite/vocab.json"
BINS = [(8, 16, 4.0)]
SEED = 42

_PUNCT = re.compile(r"[?!.,\"~:;()\[\]{}<>@#$%^&*_+=\\/|`·…“”‘’]")
_SPACE = re.compile(r"\s+")
_ALT = re.compile(r"\([^)]*\)")
_SLASH = re.compile(r"\s*/\s*")


def clean_text(s: str) -> str:
    s = _ALT.sub(" ", s)
    s = _SLASH.sub(" ", s)
    s = _PUNCT.sub(" ", s)
    s = _SPACE.sub(" ", s).strip()
    return s


def bin_of(d: float) -> str:
    for lo, hi, _ in BINS:
        if lo <= d < hi:
            return f"{lo}-{hi}"
    return "out"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--vocab", default=str(VOCAB))
    a = ap.parse_args()
    vocab = set(json.loads(Path(a.vocab).read_text(encoding="utf-8"))["char2id"].keys())
    skip = sum(1 for line in WAVE1.read_text(encoding="utf-8").splitlines()
               if line.strip() and json.loads(line).get("source") == "zeroth")
    print(f"wave1_zeroth_skip={skip} vocab={len(vocab)}", flush=True)

    AUDIO.mkdir(parents=True, exist_ok=True)
    rows = []
    oov = 0
    dur_ok = 0
    empty = 0
    APR = 0
    n = 0
    for fp in sorted(ZEROTH.glob("train-*.parquet")):
        pf = pq.ParquetFile(fp)
        file_idx = 0
        for batch in pf.iter_batches(batch_size=64, columns=["audio", "text"]):
            d = batch.to_pydict()
            for rec, text in zip(d["audio"], d["text"]):
                raw = rec["bytes"]
                try:
                    x, sr = sf.read(io.BytesIO(raw), dtype="float32")
                except Exception as e:
                    print("skip flac", e, file=sys.stderr)
                    file_idx += 1
                    continue
                if sr != 16000 or len(x) < 16000 * 0.5:
                    file_idx += 1
                    continue
                text = clean_text(text or "")
                if len(text) < 2:
                    file_idx += 1
                    continue
                dur = len(x) / sr
                if dur > 16.0:
                    file_idx += 1
                    continue
                n += 1
                if n <= skip:
                    file_idx += 1
                    continue
                if not (8.0 <= dur <= 16.0):
                    file_idx += 1
                    continue
                dur_ok += 1
                ref = text
                norm = ref.replace(" ", "")
                if not norm or len(norm) <= 1:
                    empty += 1
                    file_idx += 1
                    continue
                if any(c not in vocab for c in norm):
                    oov += 1
                    file_idx += 1
                    continue
                frames = int(dur * 25)
                repeats = sum(1 for p, q in zip(norm, norm[1:]) if p == q)
                if len(norm) + repeats > frames:
                    file_idx += 1
                    continue
                cid = f"zeroth_short_{n:06d}"
                rows.append({
                    "id": cid,
                    "source": "zeroth_control",
                    "split": "train",
                    "audio": "",
                    "text": ref,
                    "ref": ref,
                    "ref_raw": text,
                    "dur": round(dur, 6),
                    "bin": bin_of(dur),
                    "wave1_index": n,
                    "src_fp": fp.name,
                    "src_i": file_idx,
                })
                file_idx += 1
    print(f"scanned_accepted={n} after_skip_dur_ok={dur_ok} eligible={len(rows)} "
          f"oov={oov} ({oov/max(1,dur_ok):.2%}) empty={empty}", flush=True)

    rng = random.Random(a.seed)
    by_bin = defaultdict(list)
    for r in rows:
        by_bin[r["bin"]].append(r)
    for b in by_bin:
        rng.shuffle(by_bin[b])
    selected = []
    selected_ids = set()
    for lo, hi, hours in BINS:
        b = f"{lo}-{hi}"
        target = hours * 3600.0
        got = 0.0
        for r in by_bin.get(b, []):
            if r["id"] in selected_ids:
                continue
            selected.append(r)
            selected_ids.add(r["id"])
            got += r["dur"]
            if got >= target:
                break
        print(f"bin {b}: target={target:.0f}s got={got:.1f}s n={sum(1 for x in selected if x['bin']==b)}", flush=True)

    selected.sort(key=lambda x: x["id"])
    # Second pass: write only selected audio, using the source parquet index.
    by_file = defaultdict(dict)
    for r in selected:
        by_file[r["src_fp"]][r["src_i"]] = r
    for fp in sorted(ZEROTH.glob("train-*.parquet")):
        wanted = by_file.get(fp.name)
        if not wanted:
            continue
        pf = pq.ParquetFile(fp)
        file_idx = 0
        for batch in pf.iter_batches(batch_size=64, columns=["audio", "text"]):
            d = batch.to_pydict()
            for rec, _text in zip(d["audio"], d["text"]):
                row = wanted.get(file_idx)
                if row is not None:
                    x, sr = sf.read(io.BytesIO(rec["bytes"]), dtype="float32")
                    path = AUDIO / f"{row['id']}.wav"
                    sf.write(path, x, sr, subtype="PCM_16")
                    row["audio"] = str(path.relative_to(ROOT)).replace("\\", "/")
                file_idx += 1
    with open(OUT / "long_4h_zeroth.jsonl", "w", encoding="utf-8") as f:
        for r in selected:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    by_bin = defaultdict(lambda: {"n": 0, "sec": 0.0})
    for r in selected:
        by_bin[r["bin"]]["n"] += 1
        by_bin[r["bin"]]["sec"] += r["dur"]
    summary = {
        "seed": a.seed,
        "source": "zeroth_train_control",
        "wave1_zeroth_skipped": skip,
        "rows": len(selected),
        "hours": round(sum(r["dur"] for r in selected) / 3600, 4),
        "bins": {k: {"n": v["n"], "hours": round(v["sec"] / 3600, 4)} for k, v in sorted(by_bin.items())},
        "scanned_accepted": n,
        "after_skip_dur_ok": dur_ok,
        "oov_clips": oov,
        "oov_rate_pct": round(100 * oov / max(1, dur_ok), 4),
        "empty_refs": empty,
        "policy": f"vocab={Path(a.vocab).name}; Wave1 zeroth skip={skip}; OOV excluded; 8<=dur<=16",
    }
    (OUT / "long_4h_zeroth_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
