"""Finish V2 data preparation: short features and 10h cache only.

No model training and no GPU. V2 vocabulary has already been built and the
V2 short subset selected. Success sentinel: data/wave2b/V2_READY.json.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path("C:/code/unigem")
PY = str(ROOT / ".venv/Scripts/python.exe")
W2B = ROOT / "data/wave2b"
LOG = ROOT / "logs/W2B/v2_finish.log"
READY = W2B / "V2_READY.json"
FAILED = W2B / "V2_FAILED.txt"


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now().astimezone().isoformat(timespec='seconds')} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(args: list[str]) -> None:
    log("RUN " + " ".join(args))
    env = dict(os.environ)
    env["PYTHONUNBUFFERED"] = "1"
    p = subprocess.run(args, cwd=str(ROOT), env=env)
    if p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(args)}")


def main() -> None:
    FAILED.unlink(missing_ok=True)
    READY.unlink(missing_ok=True)
    log("START V2 data preparation")
    short = W2B / "short_4h_v2.jsonl"
    if not short.exists():
        raise RuntimeError(f"missing V2 short manifest: {short}")
    short_feat = W2B / "feats_short_v2/fc.npz"
    if not short_feat.exists():
        run([PY, "train/w1_extract.py",
             "--manifest", "data/wave2b/short_4h_v2.jsonl",
             "--out-dir", "data/wave2b/feats_short_v2",
             "--vocab-in", "data/wave2b/vocab_v2.json",
             "--arms", "fc", "--fc-memmap", "--threads", "6", "--min-dur", "0.28"])
    else:
        log("skip V2 short features: fc.npz exists")
    ten_meta = W2B / "feats_10h_v2/fc.npz"
    if not ten_meta.exists():
        run([PY, "runner/w2b_combine_feats.py",
             "--base", "data/wave1/feats/fc.npz",
             "--extra", "data/wave2b/feats_short_v2/fc.npz",
             "--out", "data/wave2b/feats_10h_v2"])
    else:
        log("skip V2 10h combine: metadata exists")

    import numpy as np
    rows = [json.loads(l) for l in open(short, encoding="utf-8") if l.strip()]
    short_d = np.load(short_feat, allow_pickle=True)
    ten_d = np.load(ten_meta, allow_pickle=True)
    ten_summary = json.loads((W2B / "feats_10h_v2/summary.json").read_text(encoding="utf-8"))
    ready = {
        "status": "READY",
        "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "vocab": "data/wave2b/vocab_v2.json",
        "vocab_chars": len(json.loads((W2B / "vocab_v2.json").read_text(encoding="utf-8"))["chars"]),
        "short_rows": len(rows),
        "short_hours": round(sum(r["dur"] for r in rows) / 3600, 4),
        "short_frames": int(short_d["offsets"][-1]),
        "short_feat_bytes": (W2B / "feats_short_v2/fc.feats.npy").stat().st_size,
        "ten_rows": int(ten_summary["rows"]),
        "ten_hours_est": ten_summary["hours_est"],
        "ten_frames": int(ten_d["offsets"][-1]),
        "ten_feat_bytes": (W2B / "feats_10h_v2/fc.feats.npy").stat().st_size,
        "training": "not started",
        "note": "V2 head is vocab_chars+1 rows; the 2A head must be remapped by character before warm start.",
    }
    (ROOT / "reports/provenance/W2B").mkdir(parents=True, exist_ok=True)
    (ROOT / "reports/provenance/W2B/v2_data_ready.json").write_text(
        json.dumps(ready, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    READY.write_text(json.dumps(ready, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log("V2_READY " + json.dumps(ready, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        log("V2_FAILED " + msg)
        FAILED.write_text(msg + "\n", encoding="utf-8")
        sys.exit(1)
