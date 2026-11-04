"""Build FLEURS ko dev manifest for Wave 2A-lite.

Input:  data/raw/fleurs_ko_dev/parquet-data/ko_kr/validation-00000-of-00001.parquet
Output: data/wave2a_lite/audio/fleurs_dev/*.wav
        data/wave2a_lite/fleurs_dev.jsonl
        data/wave2a_lite/fleurs_dev_summary.json

The parquet stores audio bytes; this script writes 16 kHz mono WAV files and
keeps the raw transcription. The evaluator applies eval.normalize.normalize_nospace.
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import pyarrow.parquet as pq
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data/raw/fleurs_ko_dev/parquet-data/ko_kr/validation-00000-of-00001.parquet"
OUT = ROOT / "data/wave2a_lite"
AUDIO = OUT / "audio/fleurs_dev"


def main() -> None:
    AUDIO.mkdir(parents=True, exist_ok=True)
    table = pq.read_table(SRC, columns=["id", "audio", "transcription", "raw_transcription", "num_samples"])
    rows = []
    total_sec = 0.0
    sr_set = set()
    for r in table.to_pylist():
        raw = (r.get("audio") or {}).get("bytes")
        if not raw:
            continue
        x, sr = sf.read(io.BytesIO(raw), dtype="float32", always_2d=False)
        if x.ndim > 1:
            x = x.mean(axis=1)
        sr_set.add(int(sr))
        if int(sr) != 16000:
            raise ValueError(f"unexpected sample rate {sr} for id={r['id']}")
        dur = len(x) / float(sr)
        name = f"fleurs_dev_{int(r['id']):08d}.wav"
        sf.write(AUDIO / name, x, sr, subtype="PCM_16")
        rows.append({
            "id": f"fleurs_dev_{int(r['id']):08d}",
            "source": "fleurs_ko",
            "split": "dev",
            "audio": str((AUDIO / name).relative_to(ROOT)).replace("\\", "/"),
            "ref": r.get("transcription") or "",
            "ref_raw": r.get("raw_transcription") or "",
            "dur": round(dur, 6),
            "num_samples": int(r.get("num_samples") or len(x)),
        })
        total_sec += dur
    rows.sort(key=lambda x: x["id"])
    with open(OUT / "fleurs_dev.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {
        "source": "google/fleurs ko_kr validation",
        "rows": len(rows),
        "total_hours": round(total_sec / 3600.0, 4),
        "sample_rates": sorted(sr_set),
        "min_dur": min((r["dur"] for r in rows), default=0),
        "max_dur": max((r["dur"] for r in rows), default=0),
        "le_16s": sum(1 for r in rows if 0.5 <= r["dur"] <= 16.0),
        "gt_16s": sum(1 for r in rows if r["dur"] > 16.0),
        "audio_dir": "data/wave2a_lite/audio/fleurs_dev",
    }
    json.dump(summary, open(OUT / "fleurs_dev_summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
