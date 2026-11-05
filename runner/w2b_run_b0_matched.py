#!/usr/bin/env python3
"""Run the pre-registered B0-prime matched-budget controls sequentially."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "logs" / "W2B" / "b0_matched.log"
SENT = ROOT / "data" / "wave2b" / "B0_MATCHED_DONE.json"
FAIL = ROOT / "data" / "wave2b" / "B0_MATCHED_FAILED.txt"
CKPT = ROOT / "data" / "wave2b" / "ckpt_matched"
TRAIN = ROOT / "train" / "d5_reader.py"
PY = sys.executable


def log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')} {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_arm(arm: str, epochs: int) -> None:
    final = CKPT / f"{arm}.pt"
    last = CKPT / f"{arm}.last.pt"
    if final.exists():
        log(f"SKIP {arm}: final checkpoint exists")
        return
    CKPT.mkdir(parents=True, exist_ok=True)
    cmd = [
        PY, str(TRAIN),
        "--features", "data/wave1/feats/fc.npz",
        "--dev-features", "data/wave2b/feats_dev/fc.npz",
        "--vocab-file", "data/wave2b/vocab_v2.json",
        "--retarget",
        "--arch", "base",
        "--arm", arm,
        "--init-ckpt", "data/wave2b/ckpt_v2/w2a_fc_concat_s42_v2head.pt",
        "--epochs", str(epochs),
        "--patience", "99",
        "--batch", "2",
        "--grad-accum", "4",
        "--seed", "42",
        "--threads", "6",
        "--device", "cpu",
        "--sampler", "natural",
        "--ckpt-dir", str(CKPT),
    ]
    if last.exists():
        cmd += ["--resume", str(last)]
        log(f"RESUME {arm} from {last}")
    else:
        log(f"START {arm} epochs={epochs}")
    log("CMD " + " ".join(cmd))
    t0 = time.time()
    with LOG.open("a", encoding="utf-8") as f:
        rc = subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT).returncode
    dt = time.time() - t0
    log(f"END {arm} rc={rc} sec={dt:.1f}")
    if rc != 0:
        FAIL.write_text(f"{arm} rc={rc} at {time.strftime('%Y-%m-%dT%H:%M:%S%z')}\n", encoding="utf-8")
        raise SystemExit(rc)
    if not final.exists():
        FAIL.write_text(f"{arm} finished rc=0 but final missing\n", encoding="utf-8")
        raise SystemExit(5)


def main() -> int:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    if FAIL.exists():
        FAIL.unlink()
    log("START B0 matched controls")
    run_arm("b0p_v2_s42_e20", 20)
    run_arm("b0p_v2_s42_e38", 38)
    SENT.write_text(json.dumps({
        "status": "DONE",
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "arms": [
            {"arm": "b0p_v2_s42_e20", "epochs": 20, "steps": 5960, "audio_hours": 120.016},
            {"arm": "b0p_v2_s42_e38", "epochs": 38, "steps": 11324, "audio_hours": 228.030},
        ],
        "scope": "dev 500 only; sealed test not used",
    }, indent=2) + "\n", encoding="utf-8")
    log(f"DONE {SENT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
