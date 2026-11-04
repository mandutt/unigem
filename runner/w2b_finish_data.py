"""Finish Wave 2B data preparation after the Kspon 50215 download.

This is intentionally a single background job so the long download/merge and
CPU feature extraction survive the interactive session. It never uses a GPU.

Success sentinel: data/wave2b/DATA_READY.json
Failure sentinel: data/wave2b/DATA_FAILED.txt
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import traceback
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("C:/code/unigem")
PY = str(ROOT / ".venv/Scripts/python.exe")
KSPON = Path("D:/unigem/kspon_train")
ZIP = KSPON / "10.한국어음성/KsponSpeech_05.zip"
TAR = KSPON / "download.tar"
W2B = ROOT / "data/wave2b"
LOG = ROOT / "logs/W2B/data_finish.log"
READY = W2B / "DATA_READY.json"
FAILED = W2B / "DATA_FAILED.txt"


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


def wait_for_zip(timeout_sec: int = 7200) -> None:
    deadline = time.time() + timeout_sec
    last = -1
    stable = 0
    while time.time() < deadline:
        if ZIP.exists() and not TAR.exists():
            n = ZIP.stat().st_size
            if n > 1_000_000_000 and n == last:
                stable += 1
            else:
                stable = 0
            last = n
            log(f"wait zip size={n} stable={stable}")
            if stable >= 2:
                return
        else:
            log(f"wait zip exists={ZIP.exists()} tar_exists={TAR.exists()}")
        time.sleep(10)
    raise TimeoutError("KsponSpeech_05.zip did not become stable")


def validate_zip() -> dict:
    with zipfile.ZipFile(ZIP) as z:
        infos = [i for i in z.infolist() if i.filename.endswith(".pcm")]
        if not infos:
            raise RuntimeError("zip has no .pcm entries")
        # Do not call testzip(): it reads all ~15 GB. The central directory and
        # a handful of member headers are enough to catch a partial merge.
        sample = []
        for i in infos[:1] + infos[-1:]:
            with z.open(i) as f:
                sample.append(len(f.read(4096)))
    return {"zip_bytes": ZIP.stat().st_size, "pcm_entries": len(infos),
            "sample_reads": sample}


def validate_outputs() -> dict:
    short_manifest = W2B / "short_4h.jsonl"
    short_summary = W2B / "short_4h_summary.json"
    short_feat = W2B / "feats_short/fc.npz"
    short_npy = W2B / "feats_short/fc.feats.npy"
    ten_meta = W2B / "feats_10h/fc.npz"
    ten_npy = W2B / "feats_10h/fc.feats.npy"
    ten_summary = W2B / "feats_10h/summary.json"
    for p in (short_manifest, short_summary, short_feat, short_npy, ten_meta, ten_npy, ten_summary):
        if not p.exists() or p.stat().st_size == 0:
            raise RuntimeError(f"missing/empty output: {p}")
    import numpy as np
    rows = [json.loads(line) for line in short_manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise RuntimeError("short_4h.jsonl is empty")
    audio_missing = [r["id"] for r in rows if not (ROOT / r["audio"]).exists()]
    if audio_missing:
        raise RuntimeError(f"missing short audio: {audio_missing[:5]} ({len(audio_missing)})")
    s = json.loads(short_summary.read_text(encoding="utf-8"))
    t = json.loads(ten_summary.read_text(encoding="utf-8"))
    short_d = np.load(short_feat, allow_pickle=True)
    ten_d = np.load(ten_meta, allow_pickle=True)
    if "offsets" not in short_d.files or "offsets" not in ten_d.files:
        raise RuntimeError("flat offsets missing from feature metadata")
    return {"short_rows": len(rows), "short_hours": s.get("hours"),
            "short_oov": s.get("oov"), "short_bins": s.get("bins"),
            "short_frames": int(short_d["offsets"][-1]),
            "short_feat_bytes": short_npy.stat().st_size,
            "ten_rows": int(t.get("rows", len(ten_d["lens"]))),
            "ten_hours_est": t.get("hours_est"),
            "ten_frames": int(ten_d["offsets"][-1]),
            "ten_feat_bytes": ten_npy.stat().st_size}


def main() -> None:
    FAILED.unlink(missing_ok=True)
    READY.unlink(missing_ok=True)
    log("START data preparation")
    wait_for_zip()
    z = validate_zip()
    log("ZIP " + json.dumps(z, ensure_ascii=False))

    short_manifest = W2B / "short_4h.jsonl"
    if not short_manifest.exists():
        run([PY, "runner/w2b_select_short.py", "--zip", str(ZIP)])
    else:
        log("skip short selection: manifest exists")

    short_feat = W2B / "feats_short/fc.npz"
    if not short_feat.exists():
        run([PY, "train/w1_extract.py",
             "--manifest", "data/wave2b/short_4h.jsonl",
             "--out-dir", "data/wave2b/feats_short",
             "--vocab-in", "data/wave2a_lite/vocab.json",
             "--arms", "fc", "--fc-memmap", "--threads", "6", "--min-dur", "0.28"])
    else:
        log("skip short features: fc.npz exists")

    ten_meta = W2B / "feats_10h/fc.npz"
    if not ten_meta.exists():
        run([PY, "runner/w2b_combine_feats.py",
             "--base", "data/wave1/feats/fc.npz",
             "--extra", "data/wave2b/feats_short/fc.npz",
             "--out", "data/wave2b/feats_10h"])
    else:
        log("skip 10h combine: metadata exists")

    out = validate_outputs()
    ready = {
        "status": "READY",
        "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "zip": str(ZIP), "zip_check": z, "outputs": out,
    }
    (ROOT / "reports/provenance/W2B").mkdir(parents=True, exist_ok=True)
    (ROOT / "reports/provenance/W2B/data_ready.json").write_text(
        json.dumps(ready, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    READY.write_text(json.dumps(ready, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log("DATA_READY " + json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        log("DATA_FAILED " + msg)
        FAILED.write_text(msg + "\n", encoding="utf-8")
        sys.exit(1)
