"""C5 F0 post-mortem: descriptive analysis of frozen units only.

No training, no threshold changes, no label recomputation.  This module only
summarizes existing unit artifacts to diagnose whether the F0 negative result
is a clean test or an optimization/measurement confound.
"""

from __future__ import annotations

import glob
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_pm_f0 import read_json  # noqa: E402

UNITS = ROOT / "reports/provenance/C5_f0/r/units"
OUT = ROOT / "reports/provenance/C5_f0/postmortem.json"
CELLS = ("E00", "E10", "E01", "E11")
SEEDS = (20261108, 20261109, 20261110)


def load_units() -> dict[tuple[str, int], dict[str, Any]]:
    out = {}
    for p in glob.glob(str(UNITS / "*.json")):
        u = json.loads(Path(p).read_text(encoding="utf-8"))
        out[(u["cell"], int(u["seed"]))] = u
    if len(out) != 12:
        raise RuntimeError(f"expected 12 units, got {len(out)}")
    return out


def main() -> int:
    units = load_units()
    common = list(read_json(ROOT / "reports/provenance/C5_b0a/m_cohort_preflight.json")["common_ids"])
    cell_stats = {}
    for cell in CELLS:
        cell_stats[cell] = {}
        for ep in ("copy", "full"):
            seed_means = {}
            docs: dict[str, list[float]] = defaultdict(list)
            coverage = []
            for seed in SEEDS:
                u = units[(cell, seed)]
                vals = [float(u["final"]["per_doc"][rid]["delta_shuffled_" + ep]) for rid in common]
                seed_means[str(seed)] = float(np.mean(vals))
                for rid in common:
                    docs[rid].append(float(u["final"]["per_doc"][rid]["delta_shuffled_" + ep]))
                    coverage.append(float(u["final"]["per_doc"][rid]["copy_coverage"]))
            doc_mean = {rid: float(np.mean(v)) for rid, v in docs.items()}
            arr = np.asarray(list(doc_mean.values()))
            cell_stats[cell][ep] = {
                "seed_means": seed_means,
                "doc_mean": doc_mean,
                "mean": float(arr.mean()),
                "sd": float(arr.std(ddof=1)),
                "positive_docs": int((arr > 0).sum()),
                "n_docs": int(arr.size),
                "coverage_mean": float(np.mean(coverage)),
                "coverage_min": float(np.min(coverage)),
                "coverage_max": float(np.max(coverage)),
            }
    loss = {}
    for cell in ("E01", "E10", "E11"):
        loss[cell] = {}
        for seed in SEEDS:
            t = units[(cell, seed)]["train"]
            loss[cell][str(seed)] = {
                "first": float(t["loss_first"]),
                "last": float(t["loss_last"]),
                "mean": float(t["loss_mean"]),
                "last_over_first": float(t["loss_last"] / t["loss_first"]),
            }
    d_seed = {}
    d_docs = []
    for i, rid in enumerate(common):
        e01 = np.mean([units[("E01", s)]["final"]["per_doc"][rid]["delta_shuffled_copy"] for s in SEEDS])
        e11 = np.mean([units[("E11", s)]["final"]["per_doc"][rid]["delta_shuffled_copy"] for s in SEEDS])
        d_docs.append(float(e01 - e11))
    for seed in SEEDS:
        vals = [
            float(units[("E01", seed)]["final"]["per_doc"][rid]["delta_shuffled_copy"]
                  - units[("E11", seed)]["final"]["per_doc"][rid]["delta_shuffled_copy"])
            for rid in common
        ]
        d_seed[str(seed)] = {"mean": float(np.mean(vals)), "sd": float(np.std(vals, ddof=1)),
                             "positive": int(sum(v > 0 for v in vals)), "n": len(vals)}
    out = {
        "schema_version": "1",
        "postmortem_only": True,
        "labels_recomputed": False,
        "units": 12,
        "cells": cell_stats,
        "train_loss": loss,
        "primary_D": {
            "doc_mean": d_docs,
            "mean": float(np.mean(d_docs)),
            "sd": float(np.std(d_docs, ddof=1)),
            "per_seed": d_seed,
            "positive_docs": int(sum(v > 0 for v in d_docs)),
        },
        "flags": {
            "e01_underfit": bool(
                np.mean([loss["E01"][str(s)]["last"] for s in SEEDS]) > 2.0
                * np.mean([loss["E11"][str(s)]["last"] for s in SEEDS])
            ),
            "e01_loss_ratio_mean": float(np.mean([loss["E01"][str(s)]["last_over_first"] for s in SEEDS])),
            "e11_loss_ratio_mean": float(np.mean([loss["E11"][str(s)]["last_over_first"] for s in SEEDS])),
            "coverage_equal": abs(
                cell_stats["E01"]["copy"]["coverage_mean"] - cell_stats["E11"]["copy"]["coverage_mean"]
            ) < 1e-9,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)),
                      "flags": out["flags"],
                      "D_mean": out["primary_D"]["mean"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
