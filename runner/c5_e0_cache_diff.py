"""Compare legacy T5Gemma2-tokenizer and native-EG2 layer19 caches.

The native cache adds EOS; compare only the shared content prefix. This is a
read-only diagnostic and does not use the test split.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "data/wave2c/eg2_layer19"
NATIVE = ROOT / "data/wave2c/eg2_native_layer19/layer19"
OUT = ROOT / "reports/provenance/C5_e0/legacy_native_hidden_diff.json"


def load(directory: Path, split: str) -> dict[str, tuple[np.ndarray, int]]:
    out: dict[str, tuple[np.ndarray, int]] = {}
    for p in sorted(directory.glob(f"{split}_*.npz")):
        with np.load(p) as z:
            h = z["h"].astype(np.float32)
            mask = z["mask"].astype(bool)
            for i, rid in enumerate(z["ids"].tolist()):
                n = int(mask[i].sum())
                out[str(rid)] = (h[i, :n], n)
    return out


def compare(split: str) -> dict:
    legacy = load(LEGACY, split)
    native = load(NATIVE, split)
    ids = sorted(set(legacy) & set(native))
    cos: list[float] = []
    norm_delta: list[float] = []
    length_delta: list[int] = []
    for rid in ids:
        lh, ln = legacy[rid]
        nh, nn = native[rid]
        k = min(ln, nn - 1)
        a = lh[:k]
        b = nh[:k]
        num = (a * b).sum(axis=-1)
        den = np.linalg.norm(a, axis=-1) * np.linalg.norm(b, axis=-1) + 1e-8
        cos.extend((num / den).tolist())
        norm_delta.append(float(np.abs(np.linalg.norm(a, axis=-1) - np.linalg.norm(b, axis=-1)).mean()))
        length_delta.append(nn - ln)
    return {
        "n_docs": len(ids),
        "n_token_pairs": len(cos),
        "cosine_mean": float(np.mean(cos)),
        "cosine_min": float(np.min(cos)),
        "cosine_p01": float(np.percentile(cos, 1)),
        "cosine_lt_0_99": int(sum(c < 0.99 for c in cos)),
        "cosine_lt_0_95": int(sum(c < 0.95 for c in cos)),
        "mean_abs_norm_delta": float(np.mean(norm_delta)),
        "length_delta_mean": float(np.mean(length_delta)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    payload = {
        "experiment": "c5_e0_legacy_native_hidden_diff",
        "legacy_cache": str(LEGACY.relative_to(ROOT).as_posix()),
        "native_cache": str(NATIVE.relative_to(ROOT).as_posix()),
        "layer": 19,
        "test_split_used": False,
        "splits": {split: compare(split) for split in ("train", "val")},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
