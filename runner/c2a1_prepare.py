"""C2-A1 데이터 준비 — Zeroth test 457 + Kspon eval_clean 100 → wav 16k mono."""
from __future__ import annotations

import glob
import io
import json
import os
import random

import numpy as np
import pyarrow.parquet as pq
import soundfile as sf

ROOT = r"C:\code\unigem"
OUT = os.path.join(ROOT, "data", "c2a1")
KSPON = r"C:\code\dataset\kspon_eval\10.한국어음성"
KSPON_TRN = r"C:\code\dataset\kspon_scripts\10.한국어음성\eval_clean.trn"


def zeroth():
    p = glob.glob(os.path.join(ROOT, "data", "raw", "zeroth", "data", "test-*.parquet"))[0]
    t = pq.read_table(p)
    d = os.path.join(OUT, "audio", "zeroth")
    os.makedirs(d, exist_ok=True)
    rows = []
    for i, (text, audio) in enumerate(zip(t["text"].to_pylist(), t["audio"].to_pylist())):
        wav, sr = sf.read(io.BytesIO(audio["bytes"]), dtype="float32")
        assert sr == 16000 and wav.ndim == 1, (sr, wav.shape)
        fp = os.path.join(d, f"z{i:04d}.wav")
        sf.write(fp, wav, 16000, subtype="PCM_16")
        rows.append({"id": f"zeroth-{i:04d}", "source": "zeroth", "audio": fp, "ref": text, "dur": len(wav) / 16000})
    return rows


def kspon(n=100, seed=0):
    trn = {}
    for line in open(KSPON_TRN, encoding="utf-8"):
        if " :: " in line:
            k, v = line.rstrip("\n").split(" :: ", 1)
            trn[os.path.basename(k)] = v
    files = sorted(glob.glob(os.path.join(KSPON, "eval_clean", "*.pcm")))
    random.Random(seed).shuffle(files)
    files = sorted(files[:n])
    d = os.path.join(OUT, "audio", "kspon")
    os.makedirs(d, exist_ok=True)
    rows = []
    for fp in files:
        raw = open(fp, "rb").read()
        if len(raw) % 2:
            raw = raw[:-1]  # 후행 1바이트 패딩
        wav = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
        name = os.path.splitext(os.path.basename(fp))[0] + ".wav"
        out = os.path.join(d, name)
        sf.write(out, wav, 16000, subtype="PCM_16")
        rows.append({"id": name.replace(".wav", ""), "source": "kspon_eval_clean", "audio": out,
                     "ref": trn.get(os.path.basename(fp), ""), "dur": len(wav) / 16000})
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = zeroth() + kspon()
    json.dump(rows, open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import collections
    print("rows", len(rows), collections.Counter(r["source"] for r in rows),
          "hours", round(sum(r["dur"] for r in rows) / 3600, 3),
          "empty_ref", sum(1 for r in rows if not r["ref"]))


if __name__ == "__main__":
    main()
