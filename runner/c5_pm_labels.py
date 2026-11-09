"""Frozen C5 Phase 6 label/gate primitives (v1.0.11).

Pure decision logic.  No model or data access.  Tri-state values are
True/False/None (None = not_assessable).
"""

from __future__ import annotations

from typing import Any, Iterable

from runner.c5_pm_stats import bootstrap_paired_v2, tail_metrics

NA = None


def and_n(args: Iterable[Any]) -> Any:
    vals = list(args)
    if any(v is False for v in vals):
        return False
    if any(v is None for v in vals):
        return None
    return True


def or_n(args: Iterable[Any]) -> Any:
    vals = list(args)
    if any(v is True for v in vals):
        return True
    if any(v is None for v in vals):
        return None
    return False


def not3(x: Any) -> Any:
    if x is True:
        return False
    if x is False:
        return True
    return None


def l_signal_consensus(l_copy: Any, l_full: Any) -> dict[str, Any]:
    if l_copy is True and l_full is True:
        signal: Any = True
    elif l_copy is False and l_full is False:
        signal = False
    else:
        signal = None
    copy_only = and_n([l_copy, not3(l_full)])
    full_only = and_n([l_full, not3(l_copy)])
    return {"l_signal": signal, "copy_only": copy_only, "full_only": full_only}


def l_predicate(
    per_doc_delta: list[float],
    per_seed_means: list[float],
    paired_contrast: list[float],
    copy: bool,
) -> dict[str, Any]:
    """Compute L_COPY_SIGNAL / L_FULL_SIGNAL with the frozen conjuncts."""
    threshold = 0.05 if copy else 0.0
    d = bootstrap_paired_v2(per_doc_delta, 1000, 20261109)
    p = bootstrap_paired_v2(paired_contrast, 1000, 20261109)
    mean_ok = d["mean"] is not None and d["mean"] >= threshold if copy else d["mean"] is not None and d["mean"] > 0
    ci_ok = d["ci_lower"] is not None and d["ci_lower"] > 0
    paired_ok = p["mean"] is not None and p["mean"] > 0
    seeds_ok = sum(1 for x in per_seed_means if x > 0) >= 2
    return {
        "value": bool(mean_ok and ci_ok and paired_ok and seeds_ok),
        "delta": d,
        "paired": p,
        "threshold": threshold,
        "mean_ok": bool(mean_ok),
        "ci_ok": bool(ci_ok),
        "paired_ok": bool(paired_ok),
        "seeds_positive": int(sum(1 for x in per_seed_means if x > 0)),
        "seed_means": [float(x) for x in per_seed_means],
    }


def m_evaluable(cohort_ok: Any, endpoint_ok: Any, seed_ok: Any, replay_ok: Any, builder_ok: Any) -> Any:
    return and_n([cohort_ok, endpoint_ok, seed_ok, replay_ok, builder_ok])


def m_valid(pass_pos_p: Any, pass_norm_p: Any, pass_pos_pa: Any, pass_norm_pa: Any) -> Any:
    return and_n([pass_pos_p, pass_norm_p, pass_pos_pa, pass_norm_pa])


def control_status(m_evaluable_value: Any, p_valid: Any, pa_valid: Any, m_valid_value: Any, m_pass_l: Any) -> str:
    if m_evaluable_value is not True:
        return "M_NOT_EVALUABLE"
    if p_valid is False or pa_valid is False:
        return "M_NOT_EVALUABLE"
    if p_valid is None or pa_valid is None:
        return "NOT_ASSESSABLE"
    if m_valid_value is False:
        return "M_CONTROL_INVALID"
    if m_valid_value is None:
        return "NOT_ASSESSABLE"
    if m_pass_l is True:
        return "M_CONTROL_PASS"
    if m_pass_l is False:
        return "M_CONTROL_FAIL"
    return "NOT_ASSESSABLE"


def validity_status(
    assay_path_ok: Any,
    p0_path_ok: Any,
    p_step100_path_ok: Any,
    pa_step100_path_ok: Any,
    p_valid: Any,
    pa_valid: Any,
    test_split_used: Any,
) -> str:
    if assay_path_ok is False or p0_path_ok is False or test_split_used is True or p_step100_path_ok is False:
        return "ASSAY_INVALID"
    if assay_path_ok is None or p0_path_ok is None or p_step100_path_ok is None or test_split_used is None:
        return "NOT_ASSESSABLE"
    if p_valid is False:
        return "P_STEP100_NOT_VALID"
    if p_valid is None:
        return "NOT_ASSESSABLE"
    if pa_step100_path_ok is None:
        return "NOT_ASSESSABLE"
    if pa_step100_path_ok is False:
        return "PA_STEP100_NOT_VALID"
    if pa_valid is False:
        return "PA_STEP100_NOT_VALID"
    if pa_valid is None:
        return "NOT_ASSESSABLE"
    return "VALID"


def signal_status(
    n_signal: int | None,
    l_signal: Any,
    copy_only: Any,
    full_only: Any,
    validity: str,
    control: str,
) -> str:
    if n_signal is None:
        return "NOT_ASSESSABLE"
    if n_signal < 15:
        if l_signal is True:
            return "INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL"
        if copy_only is True:
            return "INCONCLUSIVE_SMALL_N_WITH_COPY_ONLY"
        if full_only is True:
            return "INCONCLUSIVE_SMALL_N_WITH_FULL_ONLY"
        return "INCONCLUSIVE_SMALL_N"
    if validity == "NOT_ASSESSABLE":
        if l_signal is True:
            return "L_SIGNAL_VALIDITY_NOT_ASSESSABLE"
        if copy_only is True:
            return "COPY_ONLY_VALIDITY_NOT_ASSESSABLE"
        if full_only is True:
            return "FULL_ONLY_VALIDITY_NOT_ASSESSABLE"
        return "NOT_ASSESSABLE"
    if validity != "VALID":
        if l_signal is True:
            return "L_SIGNAL_VALIDITY_INVALID"
        if copy_only is True:
            return "COPY_ONLY_VALIDITY_INVALID"
        if full_only is True:
            return "FULL_ONLY_VALIDITY_INVALID"
        return "NOT_ASSESSABLE"
    if copy_only is True:
        return "COPY_ONLY_WEAK"
    if full_only is True:
        return "FULL_ONLY_WEAK"
    if l_signal is None:
        return "NOT_ASSESSABLE"
    if l_signal is True:
        if control == "M_CONTROL_PASS":
            return "EXPLORATORY_L_SIGNAL"
        if control == "M_CONTROL_FAIL":
            return "L_SIGNAL_M_CONTROL_FAIL"
        if control == "M_CONTROL_INVALID":
            return "L_SIGNAL_M_CONTROL_INVALID"
        if control == "M_NOT_EVALUABLE":
            return "L_SIGNAL_M_CONTROL_NOT_EVALUABLE"
        return "L_SIGNAL_CONTROL_NOT_ASSESSABLE"
    if control == "M_CONTROL_PASS":
        return "MEAN_CONTRAST_ONLY"
    if control == "M_CONTROL_FAIL":
        return "NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE"
    if control == "M_CONTROL_INVALID":
        return "NO_L_SIGNAL_CONTROL_INVALID"
    if control == "M_NOT_EVALUABLE":
        return "NO_L_SIGNAL_CONTROL_NOT_EVALUABLE"
    return "NOT_ASSESSABLE"


def signal_tail(per_doc_delta: dict[str, float]) -> dict[str, Any]:
    return tail_metrics(per_doc_delta)
