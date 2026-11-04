"""Build the sealed KsponSpeech eval_other test manifest.

Input:
  data/raw/kspon_eval/10.한국어음성/KsponSpeech_eval.zip (eval_other only)
  data/raw/kspon_eval/extracted/eval_other.trn

Output:
  data/wave2a_lite/audio/kspon_eval_other/*.wav
  data/wave2a_lite/kspon_eval_other.jsonl
  data/wave2a_lite/kspon_eval_other_summary.json

Transcript cleaning is pre-registered in docs/gates.md (Wave 2A-lite):
- remove one/two-letter noise markers obunl/ at token start
- choose the first alternative in (A)/(B) pairs
- normalize_nospace is applied by the evaluator, not baked into ref
The raw transcript is preserved as ref_raw. Do not use this set for training,
dev, arm selection, or early stopping. It is evaluated once after checkpoint freeze.
"""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data/raw/kspon_eval/10.한국어음성/KsponSpeech_eval.zip"
TRN = ROOT / "data/raw/kspon_eval/extracted/eval_other.trn"
OUT = ROOT / "data/wave2a_lite"
AUDIO = OUT / "audio/kspon_eval_other"

# One/two Latin letters followed by '/', only at a token boundary.
_NOISE = re.compile(r"(^|\s)[A-Za-z]{1,2}/")
_ALT = re.compile(r"\(([^()]*)\)/\(([^()]*)\)")


def clean_kspon(text: str) -> str:
    s = text.strip()
    # (A)/(B) -> A; repeat for nested/adjacent pairs.
    for _ in range(3):
        s2 = _ALT.sub(r"\1", s)
        if s2 == s:
            break
        s = s2
    s = _NOISE.sub(r"\1", s)
    s = s.replace("+", "")
    # Remaining parentheses are not part of the spoken reference.
    s = re.sub(r"\([^()]*\)", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def main() -> None:
    AUDIO.mkdir(parents=True, exist_ok=True)
    trn = {}
    for line in open(TRN, encoding="utf-8"):
        if " :: " not in line:
            continue
        k, v = line.rstrip("\n").split(" :: ", 1)
        trn[Path(k).name] = v
    rows = []
    total = 0.0
    missing_ref = 0
    empty_clean = 0
    with zipfile.ZipFile(SRC) as z:
        names = sorted(n for n in z.namelist() if n.startswith("eval_other/") and n.endswith(".pcm"))
        print(f"eval_other pcm={len(names)}", flush=True)
        for n in names:
            raw = z.read(n)
            if len(raw) % 2:
                raw = raw[:-1]  # Kspon PCM has a trailing pad byte
            x = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
            name = Path(n).stem + ".wav"
            out = AUDIO / name
            sf.write(out, x, 16000, subtype="PCM_16")
            raw_ref = trn.get(Path(n).name, "")
            clean = clean_kspon(raw_ref)
            if not raw_ref:
                missing_ref += 1
            if not clean:
                empty_clean += 1
            dur = len(x) / 16000.0
            total += dur
            rows.append({
                "id": Path(n).stem,
                "source": "kspon_eval_other",
                "split": "test",
                "sealed": True,
                "test_role": "primary_gate",
                "audio": str(out.relative_to(ROOT)).replace("\\", "/"),
                "ref": clean,
                "ref_raw": raw_ref,
                "dur": round(dur, 6),
            })
    rows.sort(key=lambda r: r["id"])
    with open(OUT / "kspon_eval_other.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {
        "source": "KsponSpeech_eval.zip eval_other",
        "rows": len(rows),
        "total_hours": round(total / 3600.0, 4),
        "empty_raw_ref": missing_ref,
        "empty_clean_ref": empty_clean,
        "le_16s": sum(1 for r in rows if 0.5 <= r["dur"] <= 16.0),
        "gt_16s": sum(1 for r in rows if r["dur"] > 16.0),
        "min_dur": min((r["dur"] for r in rows), default=0),
        "max_dur": max((r["dur"] for r in rows), default=0),
        "clean_policy": "remove [A-Za-z]{1,2}/ noise markers; choose first of (A)/(B); remove + and remaining parentheses; evaluator applies normalize_nospace",
        "sealed": True,
    }
    json.dump(summary, open(OUT / "kspon_eval_other_summary.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
