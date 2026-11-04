"""Build the FLEURS ko test comparison manifest (382 clips), sealed until freeze."""
from __future__ import annotations

import json
from pathlib import Path

import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
PRED = ROOT / "logs/C2_A1/fleurs_pred.jsonl"
AUDIO = ROOT / "data/c2a1/audio/fleurs"
OUT = ROOT / "data/wave2a_lite/fleurs_test.jsonl"


def main() -> None:
    rows = []
    for line in open(PRED, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        p = AUDIO / f"{r['id']}.wav"
        if not p.exists():
            raise FileNotFoundError(p)
        info = sf.info(str(p))
        rows.append({
            "id": r["id"],
            "source": "fleurs_ko_test",
            "split": "test",
            "sealed": True,
            "test_role": "benchmark_comparison",
            "audio": str(p.relative_to(ROOT)).replace("\\", "/"),
            "ref": r["ref"],
            "dur": round(info.frames / info.samplerate, 6),
        })
    rows.sort(key=lambda x: x["id"])
    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"rows": len(rows), "hours": round(sum(r["dur"] for r in rows) / 3600, 4),
                      "out": str(OUT)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
