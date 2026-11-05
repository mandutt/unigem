#!/usr/bin/env python3
"""Run domain/length controls sequentially: Kspon long, then Zeroth short."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
W2B = ROOT / "data/wave2b"
LOG = ROOT / "logs/W2B/domain_controls.log"
SENT = W2B / "DOMAIN_CONTROLS_DONE.json"
FAIL = W2B / "DOMAIN_CONTROLS_FAILED.txt"
CKPT = W2B / "ckpt_controls"
LONG_MAN = W2B / "long_4h.jsonl"
ZER_MAN = W2B / "long_4h_zeroth.jsonl"
LONG_FEAT = W2B / "feats_kspon_long"
ZER_FEAT = W2B / "feats_zeroth_long"
LONG_10H = W2B / "feats_10h_kspon_long"
ZER_10H = W2B / "feats_10h_zeroth_long"


def log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')} {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(name: str, cmd: list[str], check_output: Path | None = None) -> None:
    log(f"START {name}")
    t0 = time.time()
    with LOG.open("a", encoding="utf-8") as f:
        rc = subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT).returncode
    log(f"END {name} rc={rc} sec={time.time()-t0:.1f}")
    if rc != 0:
        FAIL.write_text(f"{name} rc={rc} at {time.strftime('%Y-%m-%dT%H:%M:%S%z')}\n", encoding="utf-8")
        raise SystemExit(rc)
    if check_output is not None and not check_output.exists():
        FAIL.write_text(f"{name} rc=0 but missing {check_output}\n", encoding="utf-8")
        raise SystemExit(5)


def validate_manifest(path: Path, min_hours: float) -> float:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    hours = sum(float(r["dur"]) for r in rows) / 3600
    empty_audio = sum(1 for r in rows if not r.get("audio"))
    log(f"VALIDATE {path.name} rows={len(rows)} hours={hours:.4f} empty_audio={empty_audio}")
    if hours < min_hours or empty_audio:
        FAIL.write_text(f"invalid manifest {path}: hours={hours} empty_audio={empty_audio}\n", encoding="utf-8")
        raise SystemExit(6)
    return hours


def run_arm(arm: str, feat_path: Path) -> None:
    final = CKPT / f"{arm}.pt"
    last = CKPT / f"{arm}.last.pt"
    if final.exists():
        log(f"SKIP {arm}: final exists")
        return
    CKPT.mkdir(parents=True, exist_ok=True)
    cmd = [
        PY, "train/d5_reader.py",
        "--features", f"data/wave2b/{feat_path.name}/fc.npz",
        "--dev-features", "data/wave2b/feats_dev/fc.npz",
        "--vocab-file", "data/wave2b/vocab_v2.json",
        "--retarget", "--arch", "base", "--arm", arm,
        "--init-ckpt", "data/wave2b/ckpt_v2/w2a_fc_concat_s42_v2head.pt",
        "--epochs", "12", "--patience", "4", "--batch", "2", "--grad-accum", "4",
        "--seed", "42", "--threads", "6", "--device", "cpu",
        "--sampler", "natural", "--ckpt-dir", str(CKPT),
    ]
    if last.exists():
        cmd += ["--resume", str(last)]
        log(f"RESUME {arm} from {last}")
    run(f"TRAIN {arm}", cmd, final)


def main() -> int:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    if FAIL.exists():
        FAIL.unlink()
    log("START domain/length controls")
    if not LONG_MAN.exists():
        run("SELECT Kspon long 4h", [
            PY, "runner/w2b_select_kspon_long.py",
            "--vocab", "data/wave2b/vocab_v2.json",
        ])
    validate_manifest(LONG_MAN, 3.8)
    if not ZER_MAN.exists():
        run("SELECT Zeroth long 4h", [
            PY, "runner/w2b_select_zeroth_long.py",
            "--vocab", "data/wave2b/vocab_v2.json",
        ])
    validate_manifest(ZER_MAN, 3.8)

    if not (LONG_FEAT / "fc.npz").exists():
        run("FEATURE Kspon long", [
            PY, "train/w1_extract.py", "--manifest", str(LONG_MAN),
            "--out-dir", str(LONG_FEAT), "--vocab-in", "data/wave2b/vocab_v2.json",
            "--arms", "fc", "--fc-memmap", "--threads", "6", "--min-dur", "0.5",
        ], LONG_FEAT / "fc.npz")
    if not (ZER_FEAT / "fc.npz").exists():
        run("FEATURE Zeroth long", [
            PY, "train/w1_extract.py", "--manifest", str(ZER_MAN),
            "--out-dir", str(ZER_FEAT), "--vocab-in", "data/wave2b/vocab_v2.json",
            "--arms", "fc", "--fc-memmap", "--threads", "6", "--min-dur", "0.5",
        ], ZER_FEAT / "fc.npz")

    if not (LONG_10H / "fc.npz").exists():
        run("COMBINE Kspon long 10h", [
            PY, "runner/w2b_combine_feats.py",
            "--base", "data/wave1/feats/fc.npz",
            "--extra", str(LONG_FEAT / "fc.npz"),
            "--out", str(LONG_10H),
        ], LONG_10H / "fc.npz")
    if not (ZER_10H / "fc.npz").exists():
        run("COMBINE Zeroth long 10h", [
            PY, "runner/w2b_combine_feats.py",
            "--base", "data/wave1/feats/fc.npz",
            "--extra", str(ZER_FEAT / "fc.npz"),
            "--out", str(ZER_10H),
        ], ZER_10H / "fc.npz")

    run_arm("b3long_v2_s42", LONG_10H)
    run_arm("b3zerothlong_v2_s42", ZER_10H)
    SENT.write_text(json.dumps({
        "status": "DONE",
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "arms": ["b3long_v2_s42", "b3zerothlong_v2_s42"],
        "scope": "dev 500 only; sealed test 2,400 not used",
    }, indent=2) + "\n", encoding="utf-8")
    log(f"DONE {SENT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
