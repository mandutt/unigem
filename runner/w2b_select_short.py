"""Select 4h of KsponSpeech train short utterances and extract WAV.

Input:
  D:/unigem/kspon_train/10.한국어음성/KsponSpeech_05.zip
  D:/unigem/w2b/train.trn
  data/wave2a_lite/vocab.json

Output:
  data/wave2b/short_4h.jsonl
  data/wave2b/short_4h_summary.json
  data/wave2b/audio/short_4h/*.wav

Policy (v3):
- 0-2s 25%, 2-4s 35%, 4-6s 20%, 6-8s 20% (4.0h total)
- V1: exclude clips containing chars outside the 2A 1,101-char vocab
- exclude empty/1-char refs, <0.5s, >8s, CTC len>frames
- deterministic seed 42
- folder proxy cap: 10% of total 4h (1440s) per KsponSpeech_XXXXXX directory
"""
from __future__ import annotations

import argparse
import json
import random
import re
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/wave2b"
AUDIO = OUT / "audio/short_4h"
TRAIN_TRN = Path("D:/unigem/w2b/train.trn")
VOCAB = ROOT / "data/wave2a_lite/vocab.json"
BINS = [(0, 2, 1.0), (2, 4, 1.4), (4, 6, 0.8), (6, 8, 0.8)]
SEED = 42
FOLDER_CAP_SEC = 1440.0  # 10% of 4h

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


def bin_of(d: float) -> str:
    for lo, hi, _ in BINS:
        if lo <= d < hi:
            return f"{lo}-{hi}"
    return "out"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default="D:/unigem/kspon_train/10.한국어음성/KsponSpeech_05.zip")
    ap.add_argument("--vocab", default=str(VOCAB), help="char2id vocab JSON")
    ap.add_argument("--tag", default="", help="suffix for output files, e.g. _v2")
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args()
    zp = Path(a.zip)
    if not zp.exists():
        raise SystemExit(f"missing zip: {zp}")

    vocab_path = Path(a.vocab)
    vocab = set(json.loads(vocab_path.read_text(encoding="utf-8"))["char2id"].keys())
    tag = a.tag
    audio_dir = OUT / f"audio/short_4h{tag}"
    trn = {}
    for line in TRAIN_TRN.read_text(encoding="utf-8", errors="replace").splitlines():
        if " :: " not in line:
            continue
        p, t = line.split(" :: ", 1)
        trn[Path(p).stem] = t
    print(f"trn={len(trn)} vocab={len(vocab)} tag={tag}", flush=True)

    with zipfile.ZipFile(zp) as z:
        infos = {Path(i.filename).stem: i for i in z.infolist()
                 if i.filename.endswith(".pcm") and "/KsponSpeech_" in i.filename}
        print(f"pcm={len(infos)}", flush=True)
        rows = []
        miss_ref = 0
        empty = 0
        dur_ok = 0
        oov = 0
        oov_by_bin = defaultdict(int)
        dur_ok_by_bin = defaultdict(int)
        for sid, info in infos.items():
            raw = trn.get(sid, "")
            if not raw:
                miss_ref += 1
                continue
            d = (info.file_size - (info.file_size % 2)) / 2 / 16000
            if not (0.5 <= d <= 8.0):
                continue
            dur_ok += 1
            dur_ok_by_bin[bin_of(d)] += 1
            ref = clean_kspon(raw)
            if not ref or len(ref.replace(" ", "")) <= 1:
                empty += 1
                continue
            norm = ref.replace(" ", "")
            if any(c not in vocab for c in norm):
                oov += 1
                oov_by_bin[bin_of(d)] += 1
                continue
            frames = int(d * 25)
            repeats = sum(1 for x, y in zip(norm, norm[1:]) if x == y)
            if len(norm) + repeats > frames:
                continue
            folder = Path(info.filename).parent.name
            rows.append({
                "id": sid,
                "source": "kspon_train",
                "split": "train",
                "zip_name": info.filename,
                "folder": folder,
                "dur": round(d, 6),
                "ref": ref,
                "ref_raw": raw,
                "bin": bin_of(d),
            })
        print(f"eligible={len(rows)} miss_ref={miss_ref} empty={empty} "
              f"dur_ok={dur_ok} oov={oov} ({oov/max(1,dur_ok):.2%})", flush=True)

        rng = random.Random(a.seed)
        by_bin = defaultdict(list)
        for r in rows:
            by_bin[r["bin"]].append(r)
        for b in by_bin:
            rng.shuffle(by_bin[b])

        selected = []
        selected_ids = set()
        used_folder = defaultdict(float)
        for lo, hi, hours in BINS:
            b = f"{lo}-{hi}"
            target = hours * 3600.0
            got = 0.0
            for r in by_bin.get(b, []):
                if r["id"] in selected_ids:
                    continue
                if used_folder[r["folder"]] + r["dur"] > FOLDER_CAP_SEC:
                    continue
                selected.append(r)
                selected_ids.add(r["id"])
                got += r["dur"]
                used_folder[r["folder"]] += r["dur"]
                if got >= target:
                    break
            print(f"bin {b}: target={target:.0f}s got={got:.1f}s n={sum(1 for x in selected if x['bin']==b)}", flush=True)

        audio_dir.mkdir(parents=True, exist_ok=True)
        out_rows = []
        for r in selected:
            out = audio_dir / f"{r['id']}.wav"
            if not out.exists():
                raw = z.read(r["zip_name"])
                if len(raw) % 2:
                    raw = raw[:-1]
                x = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
                sf.write(out, x, 16000, subtype="PCM_16")
            out_rows.append({
                "id": r["id"],
                "source": r["source"],
                "split": "train",
                "audio": str(out.relative_to(ROOT)).replace("\\", "/"),
                "text": r["ref"],
                "ref": r["ref"],
                "ref_raw": r["ref_raw"],
                "dur": r["dur"],
                "bin": r["bin"],
                "folder": r["folder"],
            })

    out_rows.sort(key=lambda x: x["id"])
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / f"short_4h{tag}.jsonl", "w", encoding="utf-8") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    actual_h = sum(r["dur"] for r in out_rows) / 3600
    by_bin = defaultdict(lambda: {"n": 0, "sec": 0.0})
    for r in out_rows:
        by_bin[r["bin"]]["n"] += 1
        by_bin[r["bin"]]["sec"] += r["dur"]
    summary = {
        "seed": a.seed,
        "zip": str(zp),
        "vocab": str(vocab_path),
        "tag": tag,
        "rows": len(out_rows),
        "hours": round(actual_h, 4),
        "target_hours": 4.0,
        "bins": {k: {"n": v["n"], "hours": round(v["sec"] / 3600, 4)} for k, v in sorted(by_bin.items())},
        "eligible_rows": len(rows),
        "miss_ref": miss_ref,
        "empty_ref": empty,
        "dur_ok_rows": dur_ok,
        "oov": {
            "clips": oov,
            "rate_of_dur_ok": round(oov / max(1, dur_ok), 6),
            "rate_of_dur_ok_pct": round(100.0 * oov / max(1, dur_ok), 4),
            "by_bin": {
                k: {
                    "oov": oov_by_bin.get(k, 0),
                    "dur_ok": dur_ok_by_bin.get(k, 0),
                    "rate_pct": round(100.0 * oov_by_bin.get(k, 0) / max(1, dur_ok_by_bin.get(k, 0)), 4),
                }
                for k in sorted(dur_ok_by_bin)
            },
        },
        "folder_cap_sec": FOLDER_CAP_SEC,
        "folder_count": len({r["folder"] for r in out_rows}),
        "policy": f"vocab={vocab_path.name}; OOV clip excluded; 0.5<=dur<=8; CTC len+repeats<=frames",
    }
    (OUT / f"short_4h{tag}_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
