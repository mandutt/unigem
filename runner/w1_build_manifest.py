"""D-β Wave 1 데이터 선정 — 6시간(낭독 65% + 대화 35%).

소스:
  - 낭독: Bingsu/zeroth-korean parquet (16kHz FLAC, 화자 ID 없음)
  - 대화: KconfSpeech sample zip (16kHz WAV, 화자 ID = S000012 등)

출력:
  data/wave1/audio/*.wav (16kHz mono PCM16)
  data/wave1/manifest.jsonl
  data/wave1/summary.json

주의: Zeroth에는 화자 ID가 없어 낭독 구간의 speaker-disjoint holdout은
만들 수 없다. 대화 구간은 Kconf 화자 ID로 분리 가능. 이 한계는 summary에 기록한다.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "wave1"
AUDIO = OUT / "audio"

ZEROTH = ROOT / "data/raw/zeroth/data"
KCONF_ZIP = Path(r"C:\code\dataset\audio\한국어_회의_음성_sample\한국어_회의_음성_sample.zip")

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


def stable_id(prefix: str, key: str) -> str:
    return prefix + "_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]


def write_wav(path: Path, x: np.ndarray, sr: int) -> float:
    if x.ndim > 1:
        x = x.mean(axis=1)
    x = np.asarray(x, dtype=np.float32)
    # peak normalize lightly, avoid clipping
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    if peak > 1.0:
        x = x / peak
    sf.write(path, x, sr, subtype="PCM_16")
    return len(x) / sr


def build_kconf(target_s: float, rows: list[dict]) -> float:
    have = 0.0
    with zipfile.ZipFile(KCONF_ZIP) as z:
        names = z.namelist()
        wavs = sorted(n for n in names if n.startswith("원천데이터/") and n.endswith(".wav"))
        for i, wname in enumerate(wavs):
            if have >= target_s:
                break
            # mirrored label path
            rel = wname.split("/", 1)[1]
            label_rel = rel.replace("_wav_", "_label_")
            lname = "라벨링데이터/" + label_rel.rsplit(".", 1)[0] + ".txt"
            try:
                raw = z.read(wname)
                x, sr = sf.read(io.BytesIO(raw), dtype="float32")
            except Exception as e:
                print("skip wav", wname, e, file=sys.stderr)
                continue
            if sr != 16000:
                print("skip sr", wname, sr, file=sys.stderr)
                continue
            try:
                text = z.read(lname).decode("utf-8", "ignore")
            except KeyError:
                continue
            text = clean_text(text)
            if len(text) < 2:
                continue
            # speaker from path: .../G02/S000012/000020.wav
            parts = rel.split("/")
            speaker = parts[-2] if len(parts) >= 2 else "unknown"
            cid = stable_id("kconf", rel)
            if len(x) / sr > 16.0:
                continue
            dur = write_wav(AUDIO / (cid + ".wav"), x, sr)
            rows.append({
                "id": cid,
                "source": "kconf",
                "speaker": speaker,
                "audio": str((AUDIO / (cid + ".wav")).relative_to(ROOT)).replace("\\", "/"),
                "text": text,
                "dur": round(dur, 3),
                "chars": len(text),
            })
            have += dur
    return have


def build_zeroth(target_s: float, rows: list[dict]) -> float:
    have = 0.0
    n = 0
    files = sorted(ZEROTH.glob("train-*.parquet"))
    for fp in files:
        if have >= target_s:
            break
        pf = pq.ParquetFile(fp)
        for batch in pf.iter_batches(batch_size=64, columns=["audio", "text"]):
            if have >= target_s:
                break
            d = batch.to_pydict()
            for rec, text in zip(d["audio"], d["text"]):
                if have >= target_s:
                    break
                raw = rec["bytes"]
                try:
                    x, sr = sf.read(io.BytesIO(raw), dtype="float32")
                except Exception as e:
                    print("skip flac", e, file=sys.stderr)
                    continue
                if sr != 16000 or len(x) < 16000 * 0.5:
                    continue
                text = clean_text(text or "")
                if len(text) < 2:
                    continue
                if len(x) / sr > 16.0:
                    continue
                n += 1
                cid = f"zeroth_{n:06d}"
                dur = write_wav(AUDIO / (cid + ".wav"), x, sr)
                rows.append({
                    "id": cid,
                    "source": "zeroth",
                    "speaker": None,
                    "audio": str((AUDIO / (cid + ".wav")).relative_to(ROOT)).replace("\\", "/"),
                    "text": text,
                    "dur": round(dur, 3),
                    "chars": len(text),
                })
                have += dur
    return have


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--read-hours", type=float, default=3.9)
    ap.add_argument("--conv-hours", type=float, default=2.1)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    AUDIO.mkdir(parents=True, exist_ok=True)
    for p in AUDIO.glob("*.wav"):
        p.unlink()
    rows: list[dict] = []
    print("building kconf...", flush=True)
    conv = build_kconf(a.conv_hours * 3600, rows)
    print("conv", conv / 3600, "h", len(rows), flush=True)
    print("building zeroth...", flush=True)
    read = build_zeroth(a.read_hours * 3600, rows)
    print("read", read / 3600, "h", len(rows), flush=True)
    total = conv + read
    summary = {
        "target_hours": a.read_hours + a.conv_hours,
        "read_hours": round(read / 3600, 4),
        "conv_hours": round(conv / 3600, 4),
        "total_hours": round(total / 3600, 4),
        "clips": len(rows),
        "sources": {s: sum(1 for r in rows if r["source"] == s) for s in ("zeroth", "kconf")},
        "speaker_disjoint": {
            "kconf": "가능(S000012 등 화자 ID)",
            "zeroth": "불가(화자 ID 없음)",
            "dev": "Kspon eval 100화자 — 학습과 분리",
        },
        "normalization": "Kconf 주석 제거 + 문장부호/슬래시 제거, 공백 정리",
        "note": "Zeroth 낭독 구간은 화자 ID가 없어 speaker-disjoint holdout을 보장하지 못한다.",
    }
    with open(OUT / "manifest.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    json.dump(summary, open(OUT / "summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
