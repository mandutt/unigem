#!/usr/bin/env python3
"""Analyze dev 500 predictions for the domain/length controls (D-074/D-074a)."""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROV = ROOT / "reports/provenance/W2B"


def load(name: str) -> dict:
    return json.loads((PROV / f"devpred_{name}.json").read_text(encoding="utf-8"))


def corpus(rows: list[dict]) -> tuple[float, int, int]:
    e = sum(int(r["err"]) for r in rows)
    n = sum(int(r["ref_chars"]) for r in rows)
    return e / n if n else 0.0, e, n


def boot(a: list[dict], b: list[dict], B: int = 20000, seed: int = 42) -> dict:
    assert [r["id"] for r in a] == [r["id"] for r in b]
    rng = random.Random(seed)
    ref = np.asarray([int(r["ref_chars"]) for r in a], dtype=np.float64)
    ea = np.asarray([int(r["err"]) for r in a], dtype=np.float64)
    eb = np.asarray([int(r["err"]) for r in b], dtype=np.float64)
    n = len(a)
    vals = []
    for _ in range(B):
        idx = np.asarray([rng.randrange(n) for _ in range(n)], dtype=np.int64)
        den = ref[idx].sum()
        if den > 0:
            vals.append((ea[idx].sum() - eb[idx].sum()) / den)
    vals.sort()
    point = (ea.sum() - eb.sum()) / ref.sum()
    return {
        "point": float(point),
        "ci95": [float(vals[int(0.025 * len(vals))]), float(vals[int(0.975 * len(vals)) - 1])],
        "mean": float(np.mean(vals)),
        "B": B,
        "seed": seed,
        "n": n,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(PROV / "domain_controls_bootstrap.json"))
    ap.add_argument("--bootstrap", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    names = ["b0p_v2_s42", "b3_v2_s42", "b3nat_v2_s42", "b3long_v2_s42", "b3zerothlong_v2_s42"]
    data = {n: load(n) for n in names}
    base = [r["id"] for r in data["b0p_v2_s42"]["sentences"]]
    for n in names:
        ids = [r["id"] for r in data[n]["sentences"]]
        if ids != base:
            raise SystemExit(f"id mismatch {n}")
    out = {"arms": {}, "bootstrap": {}, "B": a.bootstrap, "seed": a.seed}
    for n in names:
        cer, e, ref = corpus(data[n]["sentences"])
        out["arms"][n] = {"cer": cer, "errors": e, "ref_chars": ref, "n": len(data[n]["sentences"])}
    pairs = [
        ("b3nat_minus_b3long", "b3nat_v2_s42", "b3long_v2_s42"),
        ("b3long_minus_b3zerothlong", "b3long_v2_s42", "b3zerothlong_v2_s42"),
        ("b3nat_minus_b3zerothlong", "b3nat_v2_s42", "b3zerothlong_v2_s42"),
        ("b0_minus_b3long", "b0p_v2_s42", "b3long_v2_s42"),
        ("b0_minus_b3zerothlong", "b0p_v2_s42", "b3zerothlong_v2_s42"),
        ("b3_balanced_minus_b3long", "b3_v2_s42", "b3long_v2_s42"),
    ]
    for key, x, y in pairs:
        out["bootstrap"][key] = boot(
            data[x]["sentences"], data[y]["sentences"], B=a.bootstrap, seed=a.seed)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
