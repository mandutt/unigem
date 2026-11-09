"""C5 Phase 6 statistics primitives (frozen by v1.0.11).

This module is intentionally free of the legacy P0 bootstrap.  The only
bootstrap entry point used by Phase 6 is bootstrap_paired_v2, whose RNG and
percentile semantics are fixed by the frozen preregistration.
"""

from __future__ import annotations

import math
from typing import Any, Iterable

import numpy as np

N_BOOT = 1000
BOOTSTRAP_SEED = 20261109
CI_PERCENTILES = (2.5, 97.5)


def _as_float_array(values: Iterable[float]) -> np.ndarray:
    arr = np.asarray(list(values), dtype=np.float64)
    if arr.ndim != 1:
        raise ValueError(f"expected 1-D values, got shape {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError("bootstrap input contains non-finite values")
    return arr


def bootstrap_paired_v2(
    values: Iterable[float],
    n_boot: int = N_BOOT,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """Paired document bootstrap with the frozen Phase 6 semantics.

    The input is already the per-document value after any seed averaging.
    A fresh PCG64 generator is created for every call.  Resampling is
    document-level with replacement; the returned CI uses linear percentile
    interpolation.
    """
    arr = _as_float_array(values)
    if arr.size == 0:
        return {
            "mean": None,
            "ci_lower": None,
            "ci_upper": None,
            "n": 0,
            "n_boot": int(n_boot),
            "seed": int(seed),
            "rng": "PCG64",
            "ci_method": "linear",
        }
    if n_boot < 1:
        raise ValueError("n_boot must be >= 1")
    rng = np.random.default_rng(int(seed))
    means = np.empty(int(n_boot), dtype=np.float64)
    n = arr.size
    for i in range(int(n_boot)):
        idx = rng.integers(0, n, size=n)
        means[i] = arr[idx].mean()
    lo, hi = np.percentile(means, CI_PERCENTILES, method="linear")
    return {
        "mean": float(arr.mean()),
        "ci_lower": float(lo),
        "ci_upper": float(hi),
        "n": int(n),
        "n_boot": int(n_boot),
        "seed": int(seed),
        "rng": "PCG64",
        "ci_method": "linear",
    }


def documents_positive(values: Iterable[float]) -> int:
    arr = _as_float_array(values)
    return int((arr > 0).sum())


def registered_seeds_positive(seed_means: Iterable[float]) -> int:
    arr = _as_float_array(seed_means)
    return int((arr > 0).sum())


def tail_metrics(deltas: dict[str, float]) -> dict[str, Any]:
    """Compute the frozen signal-tail diagnostics.

    ``deltas`` maps doc_id -> delta.  Top-3 is ordered by |delta| desc then
    doc_id asc.  A non-positive denominator produces NA shares; fewer than
    four documents produces an NA leave-top-3 mean.
    """
    items = [(str(k), float(v)) for k, v in deltas.items()]
    if not items:
        return {
            "top3_abs_share": None,
            "top3_signed_share": None,
            "leave_top3_mean": None,
            "top3_ids": [],
            "top3_abs_sum": None,
            "abs_sum": None,
            "top3_signed_sum": None,
            "signed_sum": None,
        }
    values = np.asarray([v for _, v in items], dtype=np.float64)
    if not np.all(np.isfinite(values)):
        raise ValueError("tail input contains non-finite values")
    order = sorted(items, key=lambda kv: (-abs(kv[1]), kv[0]))
    top3 = order[:3]
    top3_ids = [k for k, _ in top3]
    abs_sum = float(np.abs(values).sum())
    signed_sum = float(values.sum())
    top3_abs_sum = float(sum(abs(v) for _, v in top3))
    top3_signed_sum = float(sum(v for _, v in top3))
    abs_share = None if abs_sum == 0.0 else top3_abs_sum / abs_sum
    signed_share = None if signed_sum == 0.0 else top3_signed_sum / signed_sum
    leave_mean = None
    if len(items) >= 4:
        leave_mean = float(np.mean([v for _, v in order[3:]]))
    if leave_mean is not None and leave_mean <= 0.0:
        tail = True
    elif leave_mean is None or abs_share is None:
        tail = None
    elif abs_share > 0.50:
        tail = True
    else:
        tail = False
    return {
        "top3_abs_share": abs_share,
        "top3_signed_share": signed_share,
        "leave_top3_mean": leave_mean,
        "top3_ids": top3_ids,
        "top3_abs_sum": top3_abs_sum,
        "abs_sum": abs_sum,
        "top3_signed_sum": top3_signed_sum,
        "signed_sum": signed_sum,
        "tail_driven": tail,
    }


def t_proj_seconds(
    per_arm: dict[str, dict[str, float]],
    outer_multiplier: int = 3,
) -> float:
    """Frozen T_proj arithmetic.

    ``per_arm[arm]`` contains the per-seed terms.  The caller must pass
    per-seed primary replay counts (F/L 120, P/PA 160); the outer multiplier
    is the only place that introduces the three registered seeds.
    """
    required = {
        "t_train_arm",
        "t_step0_eval_20x5_arm",
        "t_step100_eval_20x5_arm",
        "t_M_build_arm",
        "t_initial_M_ce_arm",
        "t_generate_20x256_arm",
        "t_primary_replay_arm",
        "t_replay_15x5x2x2x2_arm",
        "t_overhead_arm",
    }
    total = 0.0
    for arm in ("F", "L", "P", "PA"):
        if arm not in per_arm:
            raise ValueError(f"missing T_proj arm: {arm}")
        terms = per_arm[arm]
        missing = required - set(terms)
        if missing:
            raise ValueError(f"missing T_proj terms for {arm}: {sorted(missing)}")
        total += sum(float(terms[k]) for k in required)
    value = float(outer_multiplier) * total
    if not math.isfinite(value) or value < 0.0:
        raise ValueError("T_proj must be finite and nonnegative")
    return value
