"""Create a deterministic ~1h training subset for positive-control overfit.

Uses the first clips in Wave 1 manifest order until 3600 s. The same indices are
applied to fa/fb/fc features so the three representations see identical clips.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/wave2a_lite/feats_1h"
TARGET_SEC = 3600.0


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = [json.loads(l) for l in open(ROOT / "data/wave1/manifest.jsonl", encoding="utf-8") if l.strip()]
    ids = [r["id"] for r in manifest]
    durs = [float(r["dur"]) for r in manifest]
    idx = []
    total = 0.0
    for i, dur in enumerate(durs):
        idx.append(i)
        total += dur
        if total >= TARGET_SEC:
            break
    print(f"selected {len(idx)} clips {total/3600:.4f}h")
    for arm in ["fa", "fb", "fc"]:
        out_path = OUT / f"{arm}.npz"
        if out_path.exists():
            print(f"skip existing {arm}")
            continue
        d = np.load(ROOT / f"data/wave1/feats/{arm}.npz", allow_pickle=True)
        lens = d["lens"].astype(np.int64)
        targets = d["targets"].astype(np.int64)
        tl = d["target_lens"].astype(np.int64)
        assert list(d["ids"]) == ids, f"id order mismatch for {arm}"
        feat_ids = np.asarray(idx, dtype=np.int64)
        new_lens = lens[feat_ids]
        # target slices
        t_off = np.zeros(len(lens) + 1, dtype=np.int64); t_off[1:] = np.cumsum(tl)
        new_t = np.concatenate([targets[t_off[i]:t_off[i+1]] for i in feat_ids]) if len(feat_ids) else np.zeros(0, np.int64)
        new_tl = tl[feat_ids]
        base = {
            "lens": new_lens.astype(np.int32),
            "targets": new_t.astype(np.int32),
            "target_lens": new_tl.astype(np.int32),
            "ids": d["ids"][feat_ids],
            "speakers": d["speakers"][feat_ids],
            "texts": d["texts"][feat_ids],
        }
        if "offsets" in d.files:
            off = d["offsets"].astype(np.int64)
            npy = ROOT / f"data/wave1/feats/{arm}.feats.npy"
            if not npy.exists():
                with zipfile.ZipFile(ROOT / f"data/wave1/feats/{arm}.npz") as z:
                    z.extract("feats.npy", ROOT / "data/wave1/feats")
            mem = np.load(npy, mmap_mode="r")
            parts = [np.asarray(mem[off[i]:off[i] + lens[i]], dtype=np.float16) for i in feat_ids]
            new_off = np.zeros(len(parts) + 1, dtype=np.int64); new_off[1:] = np.cumsum([len(p) for p in parts])
            base["feats"] = np.concatenate(parts) if parts else np.zeros((0, 4096), np.float16)
            base["offsets"] = new_off
        else:
            base["feats"] = d["feats"][feat_ids]
        np.savez_compressed(out_path, **base)
        print(f"saved {arm}: {base['feats'].shape} clips={len(new_lens)} chars={len(new_t)}")
    json.dump({"clips": len(idx), "hours": total / 3600.0, "ids": [ids[i] for i in idx]},
              open(OUT / "subset.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
