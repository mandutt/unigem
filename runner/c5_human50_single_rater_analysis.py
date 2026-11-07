#!/usr/bin/env python3
"""D-085 single-rater human-50 analysis.

The protocol, manifest, sample and decision rule must be frozen before ratings.
This script reads a ratings JSONL and writes a result JSON. It does not modify
the manifest or any model/verifier artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ARMS = ["pilot300", "1293", "1940", "2586"]
PRIMARY = ["2586", "pilot300"]
SECONDARY = ["2586", "1293"]
EXPLORATORY = ["1940", "pilot300"]
REQUIRED_FIELDS = {
    "doc_id", "arm", "pass", "adequacy",
    "critical_unsupported", "critical_omission",
    "wrong_unit_qualifier", "entity_relation", "fluency", "utility",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def bootstrap_ci(values: np.ndarray, *, n_boot: int = 10000, seed: int = 20261107) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    n = len(values)
    idx = rng.integers(0, n, size=(n_boot, n))
    means = values[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(lo), float(hi)


def icc21(matrix: np.ndarray) -> float:
    """Two-way random effects, single measurement ICC(2,1)."""
    n, k = matrix.shape
    grand = float(matrix.mean())
    row_mean = matrix.mean(axis=1)
    col_mean = matrix.mean(axis=0)
    ssr = k * float(((row_mean - grand) ** 2).sum())
    ssc = n * float(((col_mean - grand) ** 2).sum())
    sse = float(((matrix - row_mean[:, None] - col_mean[None, :] + grand) ** 2).sum())
    msr = ssr / (n - 1)
    msc = ssc / (k - 1)
    mse = sse / ((n - 1) * (k - 1))
    denom = msr + (k - 1) * mse + k * (msc - mse) / n
    return (msr - mse) / denom if denom else float("nan")


def quadratic_weighted_kappa(y1: list[int], y2: list[int], n_classes: int = 5) -> float:
    n = len(y1)
    observed = np.zeros((n_classes, n_classes), dtype=float)
    for a, b in zip(y1, y2):
        observed[a, b] += 1
    row = observed.sum(axis=1)
    col = observed.sum(axis=0)
    expected = np.outer(row, col) / n
    weights = np.array([[(i - j) ** 2 / (n_classes - 1) ** 2 for j in range(n_classes)] for i in range(n_classes)])
    denom = float((weights * expected).sum())
    return 1.0 - float((weights * observed).sum()) / denom if denom else float("nan")


def cohen_kappa(y1: list[int], y2: list[int]) -> float:
    n = len(y1)
    observed = sum(1 for a, b in zip(y1, y2) if a == b) / n
    p1 = sum(y1) / n
    p2 = sum(y2) / n
    expected = p1 * p2 + (1 - p1) * (1 - p2)
    return (observed - expected) / (1 - expected) if expected != 1 else float("nan")


def paired_metrics(rows: dict[tuple[str, str, int], dict[str, Any]], docs: list[str], a: str, b: str) -> dict[str, Any]:
    diff = np.array([
        rows[(d, a, 1)]["adequacy"] - rows[(d, b, 1)]["adequacy"]
        for d in docs
    ], dtype=float)
    crit_us = np.array([
        rows[(d, a, 1)]["critical_unsupported"] - rows[(d, b, 1)]["critical_unsupported"]
        for d in docs
    ], dtype=float)
    crit_om = np.array([
        rows[(d, a, 1)]["critical_omission"] - rows[(d, b, 1)]["critical_omission"]
        for d in docs
    ], dtype=float)
    ad_lo, ad_hi = bootstrap_ci(diff)
    us_lo, us_hi = bootstrap_ci(crit_us)
    om_lo, om_hi = bootstrap_ci(crit_om)
    return {
        "contrast": f"{a} - {b}",
        "n_docs": len(docs),
        "adequacy_mean_diff": float(diff.mean()),
        "adequacy_ci95": [ad_lo, ad_hi],
        "critical_unsupported_rate_diff": float(crit_us.mean()),
        "critical_unsupported_ci95": [us_lo, us_hi],
        "critical_omission_rate_diff": float(crit_om.mean()),
        "critical_omission_ci95": [om_lo, om_hi],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ratings", required=True, type=Path)
    ap.add_argument("--manifest", default=ROOT / "reports/provenance/C5_human50/manifest.json", type=Path)
    ap.add_argument("--out", default=ROOT / "reports/provenance/C5_human50/human50_result.json", type=Path)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    sample = [x["id"] for x in manifest["targeted"] + manifest["random"]]
    repeat = [x["id"] for x in manifest["repeat"]]
    prefix_ids = set(manifest.get("train_prefix_ids", []))
    expected_primary = {(d, arm, 1) for d in sample for arm in ARMS}
    expected_repeat = {(d, arm, 2) for d in repeat for arm in ARMS}

    raw = load_jsonl(args.ratings)
    rows: dict[tuple[str, str, int], dict[str, Any]] = {}
    for r in raw:
        missing = REQUIRED_FIELDS - set(r)
        if missing:
            raise SystemExit(f"rating missing fields: {sorted(missing)}")
        key = (str(r["doc_id"]), str(r["arm"]), int(r["pass"]))
        if key in rows:
            raise SystemExit(f"duplicate rating: {key}")
        if key[1] not in ARMS:
            raise SystemExit(f"unknown arm: {key[1]}")
        if int(r["adequacy"]) not in range(5):
            raise SystemExit(f"adequacy out of range: {key}")
        for f in ("critical_unsupported", "critical_omission", "wrong_unit_qualifier", "entity_relation"):
            if int(r[f]) not in (0, 1):
                raise SystemExit(f"{f} must be 0/1: {key}")
        if int(r["fluency"]) not in range(1, 6) or int(r["utility"]) not in range(1, 6):
            raise SystemExit(f"fluency/utility out of range: {key}")
        rows[key] = r

    got_primary = {k for k in rows if k[2] == 1}
    got_repeat = {k for k in rows if k[2] == 2}
    missing_primary = expected_primary - got_primary
    missing_repeat = expected_repeat - got_repeat
    extra = (got_primary - expected_primary) | (got_repeat - expected_repeat)
    if missing_primary or missing_repeat or extra:
        raise SystemExit(json.dumps({
            "missing_primary": len(missing_primary),
            "missing_repeat": len(missing_repeat),
            "extra": len(extra),
            "status": "INCONCLUSIVE",
        }, ensure_ascii=False))

    primary = paired_metrics(rows, sample, "2586", "pilot300")
    secondary = paired_metrics(rows, sample, "2586", "1293")
    exploratory = paired_metrics(rows, sample, "1940", "pilot300")
    sensitivity_docs = [d for d in sample if d not in prefix_ids]
    sensitivity = paired_metrics(rows, sensitivity_docs, "2586", "pilot300")

    # Reliability: repeat docs x 4 arms, pass1 vs pass2.
    rel_docs = repeat
    rel_arms = ARMS
    mat = np.array([
        [rows[(d, arm, 1)]["adequacy"], rows[(d, arm, 2)]["adequacy"]]
        for d in rel_docs for arm in rel_arms
    ], dtype=float)
    y1 = [int(rows[(d, arm, 1)]["adequacy"]) for d in rel_docs for arm in rel_arms]
    y2 = [int(rows[(d, arm, 2)]["adequacy"]) for d in rel_docs for arm in rel_arms]
    icc = float(icc21(mat))
    qwk = float(quadratic_weighted_kappa(y1, y2))
    us1 = [int(rows[(d, arm, 1)]["critical_unsupported"]) for d in rel_docs for arm in rel_arms]
    us2 = [int(rows[(d, arm, 2)]["critical_unsupported"]) for d in rel_docs for arm in rel_arms]
    om1 = [int(rows[(d, arm, 1)]["critical_omission"]) for d in rel_docs for arm in rel_arms]
    om2 = [int(rows[(d, arm, 2)]["critical_omission"]) for d in rel_docs for arm in rel_arms]
    reliability = {
        "n_targets": len(mat),
        "icc21_adequacy": icc,
        "quadratic_weighted_kappa_adequacy": qwk,
        "critical_unsupported_kappa": float(cohen_kappa(us1, us2)),
        "critical_omission_kappa": float(cohen_kappa(om1, om2)),
    }

    primary_ok = (
        primary["adequacy_ci95"][0] >= -0.25
        and primary["critical_unsupported_ci95"][1] < 0.05
        and primary["critical_omission_ci95"][1] < 0.05
    )
    reliability_ok = icc >= 0.70 and qwk >= 0.60
    sensitivity_ok = (
        sensitivity["adequacy_ci95"][0] >= -0.25
        and sensitivity["critical_unsupported_ci95"][1] < 0.05
        and sensitivity["critical_omission_ci95"][1] < 0.05
    )
    if not primary_ok:
        status = "FAIL"
    elif not reliability_ok or not sensitivity_ok:
        status = "INCONCLUSIVE"
    else:
        status = "SINGLE_RATER_SUPPORTED"

    result = {
        "protocol": manifest.get("protocol"),
        "status": status,
        "candidate_status": "PROVISIONAL_NOMINEE" if status == "SINGLE_RATER_SUPPORTED" else "NO_APPROVED_CANDIDATE",
        "approval_status": "NOT_APPROVED",
        "test_163": "SEALED",
        "rater_count": 1,
        "inter_rater_reliability": "NOT_AVAILABLE",
        "primary": primary,
        "secondary": secondary,
        "exploratory": exploratory,
        "train_prefix_sensitivity": sensitivity,
        "reliability": reliability,
        "gates": {
            "adequacy": primary["adequacy_ci95"][0] >= -0.25,
            "critical_unsupported": primary["critical_unsupported_ci95"][1] < 0.05,
            "critical_omission": primary["critical_omission_ci95"][1] < 0.05,
            "icc": icc >= 0.70,
            "weighted_kappa": qwk >= 0.60,
            "train_prefix_sensitivity": sensitivity_ok,
        },
        "counts": {"primary": len(got_primary), "repeat": len(got_repeat), "total": len(rows)},
        "hashes": {
            "ratings_sha256": sha256_file(args.ratings),
            "manifest_sha256": sha256_file(args.manifest),
        },
        "note": "Single-rater evidence only. No inter-rater reliability claim. No test 163 use.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
