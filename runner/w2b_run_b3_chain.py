"""Run B3 and B3-nat after B0-prime V2 finishes.

The chain waits for the final B0-prime checkpoint only to serialize CPU use;
B3/B3-nat both initialize from the same V2-remapped 2A reader, not from B0-prime.
No GPU is used.
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
CKPT = W2B / "ckpt_v2"
B0_FINAL = CKPT / "b0p_v2_s42.pt"
B0_BEST = CKPT / "b0p_v2_s42.best.pt"
LOG = ROOT / "logs/W2B/b3_chain.log"
DONE = W2B / "B3_CHAIN_DONE.json"
FAILED = W2B / "B3_CHAIN_FAILED.txt"
INIT = W2B / "ckpt_v2/w2a_fc_concat_s42_v2head.pt"
VOCAB = "data/wave2b/vocab_v2.json"
FEATURES = "data/wave2b/feats_10h_v2/fc.npz"
DEV = "data/wave2b/feats_dev/fc.npz"


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


def common(arm: str, sampler: str) -> list[str]:
    return [PY, "train/d5_reader.py",
            "--features", FEATURES,
            "--dev-features", DEV,
            "--vocab-file", VOCAB,
            "--retarget", "--arch", "base",
            "--arm", arm,
            "--init-ckpt", str(INIT),
            "--epochs", "12", "--patience", "4",
            "--batch", "2", "--grad-accum", "4",
            "--seed", "42", "--threads", "6", "--device", "cpu",
            "--sampler", sampler,
            "--ckpt-dir", str(CKPT)]


def main() -> None:
    DONE.unlink(missing_ok=True)
    FAILED.unlink(missing_ok=True)
    log("START B3 chain")
    deadline = time.time() + 3 * 3600
    while time.time() < deadline:
        if B0_FINAL.exists():
            log(f"B0 final checkpoint found: {B0_FINAL}")
            break
        time.sleep(30)
    else:
        raise TimeoutError("B0-prime V2 checkpoint did not appear within 3 hours")
    if not INIT.exists():
        raise FileNotFoundError(INIT)
    run(common("b3_v2_s42", "balanced"))
    run(common("b3nat_v2_s42", "natural"))
    out = {"status": "DONE", "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
           "arms": ["b3_v2_s42", "b3nat_v2_s42"], "init": str(INIT),
           "features": FEATURES, "vocab": VOCAB}
    (ROOT / "reports/provenance/W2B").mkdir(parents=True, exist_ok=True)
    (ROOT / "reports/provenance/W2B/b3_chain.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    DONE.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log("B3_CHAIN_DONE " + json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        log("B3_CHAIN_FAILED " + msg)
        FAILED.write_text(msg + "\n", encoding="utf-8")
        sys.exit(1)
