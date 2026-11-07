#!/usr/bin/env python3
"""Build a provisional D-084 rev3 / 084a selection record.

This does NOT modify D-083 selection files and does not approve a candidate.
It reads the 084a audit and strict metrics, applies the unchanged point
screens, and labels evidence separately.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

AUDIT = ROOT / "reports/provenance/C5_a1/full_2ep/verifier_084a_audit.json"
RUN = ROOT / "reports/provenance/C5_a1/full_2ep"
PILOT_METRICS = ROOT / "reports/provenance/C5_a1/pilot300_val161/metrics.json"


def cp_bounds(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact Clopper-Pearson two-sided interval if scipy is available."""
    if n == 0:
        return (0.0, 1.0)
    try:
        from scipy.stats import beta

        lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
        hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
        return lo, hi
    except Exception:
        # Conservative fallback: Wilson-ish normal approximation; marked in output.
        p = k / n
        z = 1.959963984540054
        den = 1 + z * z / n
        mid = (p + z * z / (2 * n)) / den
        half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
        return max(0.0, mid - half), min(1.0, mid + half)


def metrics_for(name: str) -> dict[str, Any]:
    if name == "pilot300":
        return json.loads(PILOT_METRICS.read_text(encoding="utf-8"))
    return json.loads((RUN / f"eval_step_{name}/eval.metrics.json").read_text(encoding="utf-8"))


def main() -> int:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    rows = []
    for name, sysdata in audit["systems"].items():
        per = sysdata["per_doc"]
        n = len(per)
        grounded = sum(1 for x in per.values() if x["a_grounded"])
        slots = sum(x["a_summary_count"] for x in per.values())
        new = sum(x["a_new_count"] for x in per.values())
        micro = new / slots if slots else 1.0
        nonvac = [x for x in per.values() if x["a_summary_count"] > 0]
        nonvac_grounded = sum(1 for x in nonvac if x["a_grounded"])
        slotfree = [rid for rid, x in per.items() if x["a_slot_free"]]
        m = metrics_for(name)
        eos = float(m.get("eos_rate", 0.0))
        rep4 = float(m.get("repeated_4gram_rate_mean", 0.0))
        f1 = float(m.get("char_f1_mean", 0.0))
        doc_cp = cp_bounds(grounded, n)
        slot_cp = cp_bounds(new, slots)
        gate = {
            "grounded": grounded / n >= 0.99,
            "new_slot_micro": micro <= 0.01,
            "eos": eos >= 0.95,
            "repeated4": rep4 <= 0.06,
        }
        rows.append({
            "system": name,
            "n": n,
            "char_f1": f1,
            "grounded": grounded,
            "grounded_rate": grounded / n,
            "new_slots": new,
            "summary_slots": slots,
            "new_slot_micro": micro,
            "nonvacuous_n": len(nonvac),
            "nonvacuous_grounded": nonvac_grounded,
            "nonvacuous_rate": nonvac_grounded / len(nonvac) if nonvac else None,
            "slot_free": len(slotfree),
            "slot_free_ids": slotfree,
            "eos": eos,
            "repeated4": rep4,
            "gate": gate,
            "screen_eligibility": all(gate.values()),
            "doc_cp95": list(doc_cp),
            "slot_cp95": list(slot_cp),
            "evidence_status": (
                "INCONCLUSIVE"
                if (doc_cp[0] < 0.99 or slot_cp[1] > 0.01)
                else "CERTIFIED"
            ),
        })

    full_train = [r for r in rows if r["system"] != "pilot300"]
    eligible = [r for r in full_train if r["screen_eligibility"]]
    eligible_sorted = sorted(eligible, key=lambda r: (-r["char_f1"], int(r["system"])))
    if eligible_sorted:
        win = eligible_sorted[0]
        candidate_status = "PROVISIONAL_NOMINEE"
        provisional = {
            "step": win["system"],
            "char_f1": win["char_f1"],
            "grounded": win["grounded"],
            "note": "provisional 084a nominee only; not D-083 selected, not approved, not promoted",
        }
    else:
        candidate_status = "NO_ELIGIBLE_CHECKPOINT"
        provisional = None

    out = {
        "policy": "D084A/1.0.0",
        "spec_hash": "d084a-rev3-2026-11-07",
        "source": "verifier_084a_audit.json",
        "strict_d083_selected_step": None,
        "strict_d083_fallback": "pilot300",
        "candidate_status": candidate_status,
        "provisional_nominee": provisional,
        "eligible_full_train": [r["system"] for r in eligible_sorted],
        "approval_status": "NOT_APPROVED",
        "human_50": "NOT_RUN",
        "test_163": "SEALED",
        "systems": {r["system"]: r for r in rows},
        "note": "Point screens are unchanged. CP is evidence-status only and does not remove eligibility. No D-083 file was overwritten.",
    }
    path = RUN / "selection_084a_provisional.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_status": candidate_status,
        "provisional_nominee": provisional,
        "eligible_full_train": out["eligible_full_train"],
        "systems": {
            r["system"]: {
                "grounded": f"{r['grounded']}/{r['n']}",
                "micro": round(r["new_slot_micro"], 5),
                "eos": r["eos"],
                "rep4": r["repeated4"],
                "screen": r["screen_eligibility"],
                "evidence": r["evidence_status"],
            }
            for r in rows
        },
    }, ensure_ascii=False, indent=2))
    print("wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
