#!/usr/bin/env python3
"""Run the step-matched B3-long arm (batch2/grad_accum2, 11,136 steps)."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
LOG = ROOT / "logs/W2B/b3long_sm.log"
SENT = ROOT / "data/wave2b/B3LONG_SM_DONE.json"
FAIL = ROOT / "data/wave2b/B3LONG_SM_FAILED.txt"
CKPT = ROOT / "data/wave2b/ckpt_controls"
ARM = "b3long_sm_v2_s42"


def log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')} {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def main() -> int:
    if SENT.exists():
        log(f"SKIP {ARM}: sentinel exists")
        return 0
    if FAIL.exists():
        FAIL.unlink()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    CKPT.mkdir(parents=True, exist_ok=True)
    final = CKPT / f"{ARM}.pt"
    last = CKPT / f"{ARM}.last.pt"
    if final.exists():
        SENT.write_text(json.dumps({"status": "DONE", "arm": ARM, "reason": "final exists",
                                    "finished_at": time.strftime('%Y-%m-%dT%H:%M:%S%z')}, indent=2) + "\n",
                        encoding="utf-8")
        log(f"DONE {ARM}: final exists")
        return 0
    cmd = [
        PY, "train/d5_reader.py",
        "--features", "data/wave2b/feats_10h_kspon_long/fc.npz",
        "--dev-features", "data/wave2b/feats_dev/fc.npz",
        "--vocab-file", "data/wave2b/vocab_v2.json", "--retarget",
        "--arch", "base", "--arm", ARM,
        "--init-ckpt", "data/wave2b/ckpt_v2/w2a_fc_concat_s42_v2head.pt",
        "--epochs", "12", "--patience", "99",
        "--batch", "2", "--grad-accum", "2",
        "--seed", "42", "--threads", "6", "--device", "cpu",
        "--sampler", "natural", "--ckpt-dir", str(CKPT),
    ]
    if last.exists():
        cmd += ["--resume", str(last)]
        log(f"RESUME {ARM} from {last}")
    else:
        log(f"START {ARM}")
    t0 = time.time()
    with LOG.open("a", encoding="utf-8") as f:
        rc = subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT).returncode
    log(f"END {ARM} rc={rc} sec={time.time()-t0:.1f}")
    if rc != 0:
        FAIL.write_text(f"{ARM} rc={rc} at {time.strftime('%Y-%m-%dT%H:%M:%S%z')}\n", encoding="utf-8")
        return rc
    if not final.exists():
        FAIL.write_text(f"{ARM} rc=0 but missing final {final}\n", encoding="utf-8")
        return 5
    SENT.write_text(json.dumps({"status": "DONE", "arm": ARM,
                                "finished_at": time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                                "scope": "dev 500 only; sealed test 2,400 not used"}, indent=2) + "\n",
                   encoding="utf-8")
    log(f"DONE {ARM}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
