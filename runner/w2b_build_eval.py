"""Build W2B dev/test/spare manifests and WAV files from eval_clean.

The split is the audited duration-stratified candidate (D-068):
dev 500 / test 2,400 / spare 90. No model evaluation is performed here.
"""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
EVAL_ZIP = ROOT / "data/raw/kspon_eval/10.한국어음성/KsponSpeech_eval.zip"
TRN = ROOT / "data/raw/kspon_eval/extracted/eval_clean.trn"
CAND = ROOT / "data/wave2b/preflight/split_candidate.json"
OUT = ROOT / "data/wave2b"

_NOISE = re.compile(r"(^|\s)[A-Za-z]{1,2}/")
_ALT = re.compile(r"\(([^()]*)\)/\(([^()]*)\)")


def clean_kspon(text: str) -> str:
    s = text.strip()
    for _ in range(3):
        s2 = _ALT.sub(r"\1", s)
        if s2 == s:
            break
        s = s2
    s = _NOISE.sub(r"\1", s)
    s = s.replace("+", "")
    s = re.sub(r"\([^()]*\)", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def main() -> None:
    cand = json.loads(CAND.read_text(encoding="utf-8"))
    trn = {}
    for line in TRN.read_text(encoding="utf-8", errors="replace").splitlines():
        if " :: " not in line:
            continue
        p, t = line.split(" :: ", 1)
        trn[Path(p).stem] = t
    with zipfile.ZipFile(EVAL_ZIP) as z:
        infos = {Path(i.filename).stem: i for i in z.infolist()
                 if i.filename.startswith("eval_clean/") and i.filename.endswith(".pcm")}
        for split in ("dev", "test", "spare"):
            ids = cand[split]
            audio_dir = OUT / f"audio/kspon_eval_clean/{split}"
            audio_dir.mkdir(parents=True, exist_ok=True)
            rows = []
            for sid in ids:
                info = infos[sid]
                raw = z.read(info.filename)
                if len(raw) % 2:
                    raw = raw[:-1]
                x = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
                out = audio_dir / f"{sid}.wav"
                if not out.exists():
                    sf.write(out, x, 16000, subtype="PCM_16")
                raw_ref = trn[sid]
                ref = clean_kspon(raw_ref)
                rows.append({
                    "id": sid,
                    "source": "kspon_eval_clean",
                    "split": split,
                    "sealed": split == "test",
                    "audio": str(out.relative_to(ROOT)).replace("\\", "/"),
                    "ref": ref,
                    "text": ref,
                    "ref_raw": raw_ref,
                    "dur": round(len(x) / 16000.0, 6),
                })
            rows.sort(key=lambda r: r["id"])
            with open(OUT / f"{split}_{len(rows)}.jsonl", "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(split, len(rows), "hours", round(sum(r["dur"] for r in rows) / 3600, 4),
                  "lt0.5", sum(r["dur"] < 0.5 for r in rows), flush=True)


if __name__ == "__main__":
    main()
