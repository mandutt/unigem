"""Build concatenated EG2 layer12 512 + final 768 features (1280d)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LAYER = ROOT / "data/wave2c/eg2_layer12"
FINAL = ROOT / "data/wave2c/b1d/student"
OUT = ROOT / "data/wave2c/eg2_concat"


def load_dir(directory: Path, split: str, only: set[str] | None = None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in sorted(directory.glob(f"{split}_*.npz")):
        with np.load(p, mmap_mode="r", allow_pickle=False) as z:
            ids = [str(x) for x in z["ids"].tolist()]
            for i, rid in enumerate(ids):
                if only is not None and rid not in only:
                    continue
                out[rid] = {
                    "h": np.array(z["h"][i], dtype=np.float16, copy=True),
                    "mask": np.array(z["mask"][i], dtype=bool, copy=True),
                    "length": int(z["lengths"][i]),
                }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=OUT)
    ap.add_argument("--shard-size", type=int, default=50)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    meta = {"feature": "EG2 layer12 512 + final 768 concat 1280", "splits": {}}
    for split in ("train", "val"):
        layer = load_dir(LAYER, split)
        final = load_dir(FINAL, split, only=set(layer))
        ids = [rid for rid in layer if rid in final]
        missing = len(layer) - len(ids)
        print(f"{split}: layer={len(layer)} final={len(final)} matched={len(ids)} missing={missing}")
        for start in range(0, len(ids), args.shard_size):
            chunk = ids[start:start + args.shard_size]
            hs, masks, lengths = [], [], []
            for rid in chunk:
                a, b = layer[rid], final[rid]
                if a["length"] != b["length"]:
                    raise SystemExit(f"length mismatch {rid}: {a['length']} vs {b['length']}")
                n = a["h"].shape[0]
                h = np.zeros((n, 1280), dtype=np.float16)
                h[:, :512] = a["h"]
                m = min(n, b["h"].shape[0])
                h[:m, 512:] = b["h"][:m]
                hs.append(h)
                masks.append(a["mask"])
                lengths.append(a["length"])
            path = out_dir / f"{split}_{start // args.shard_size:04d}.npz"
            if path.exists() and not args.overwrite:
                print("skip", path.name)
                continue
            np.savez_compressed(path, h=np.stack(hs), mask=np.stack(masks),
                                lengths=np.asarray(lengths, dtype=np.int32),
                                ids=np.asarray(chunk))
            print("wrote", path.name, len(chunk))
        meta["splits"][split] = {"n": len(ids), "missing": missing}
    (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
