"""Combine 6h Wave1 F-C features with short 4h features into a 10h cache.

The output npz carries metadata only; fc.feats.npy is the memmap payload.
Both inputs must use the same 1,101-char V1 vocab.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import numpy.lib.format as nf


def load_meta(path: Path):
    d = np.load(path, allow_pickle=True)
    npy = path.with_suffix(".feats.npy")
    return d, npy


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="data/wave1/feats/fc.npz")
    ap.add_argument("--extra", default="data/wave2b/feats_short/fc.npz")
    ap.add_argument("--out", default="data/wave2b/feats_10h")
    a = ap.parse_args()
    base, base_npy = load_meta(Path(a.base))
    extra, extra_npy = load_meta(Path(a.extra))
    if not base_npy.exists() or not extra_npy.exists():
        raise SystemExit(f"missing memmap: {base_npy} {extra_npy}")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    def cat(key, dtype=None):
        vals = []
        for d in (base, extra):
            if key not in d.files:
                return None
            vals.append(np.asarray(d[key]))
        return np.concatenate(vals, axis=0)

    lens = cat("lens").astype(np.int32)
    target_lens = cat("target_lens").astype(np.int32)
    targets = cat("targets").astype(np.int32)
    ids = cat("ids").astype(str)
    texts = cat("texts").astype(str)
    n = len(lens)
    offsets = np.zeros(n + 1, dtype=np.int64)
    offsets[1:] = np.cumsum(lens)
    dst = out / "fc.feats.npy"
    with open(dst, "wb") as f:
        nf.write_array_header_1_0(f, {"descr": "<f2", "fortran_order": False,
                                      "shape": (int(offsets[-1]), 4096)})
        for p in (base_npy, extra_npy):
            with open(p, "rb") as src:
                # skip the npy header of each source
                version = np.lib.format.read_magic(src)
                shape, fortran, dtype = np.lib.format._read_array_header(src, version)
                while True:
                    b = src.read(1 << 24)
                    if not b:
                        break
                    f.write(b)
    np.savez_compressed(out / "fc.npz", offsets=offsets, lens=lens,
                        targets=targets, target_lens=target_lens,
                        ids=ids, texts=texts)
    summary = {"rows": n, "frames": int(offsets[-1]), "hours_est": float(lens.sum() / 25 / 3600),
               "base": a.base, "extra": a.extra, "out": a.out,
               "vocab": "2A 1,101"}
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
