#!/usr/bin/env python3
"""Aggregate D-086 AI panel ratings and report inter-judge agreement.

This does not perform the primary decision: human calibration is still
required by D-086. The output is labelled AI_PANEL_ONLY.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_human50_single_rater_analysis import bootstrap_ci, icc21  # noqa: E402

RAW = ROOT / "reports/provenance/C5_hybrid/ai_ratings.jsonl"
MANIFEST = ROOT / "reports/provenance/C5_hybrid/manifest.json"
AGG = ROOT / "reports/provenance/C5_hybrid/ai_panel_aggregated.jsonl"
SUMMARY = ROOT / "reports/provenance/C5_hybrid/ai_panel_summary.json"
FLAGS = ("critical_unsupported", "critical_omission", "wrong_unit_qualifier", "entity_relation")


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = [json.loads(x) for x in RAW.read_text(encoding="utf-8").splitlines() if x.strip()]
    by: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for r in rows:
        by[(r["doc_id"], r["arm"])][r["judge"]] = r
    judges = [j["id"] for j in manifest["ai_panel"]["judges"]]
    agg_rows = []
    contested = []
    for (doc, arm), js in sorted(by.items()):
        if set(js) != set(judges):
            raise SystemExit(f"missing judge for {doc}/{arm}: {sorted(js)}")
        ad = [int(js[j]["adequacy"]) for j in judges]
        fl = {f: [int(js[j][f]) for j in judges] for f in FLAGS}
        med_flags = {f: int(sum(v) >= 2) for f, v in fl.items()}
        contested_flags = {f: (sum(v) not in (0, 3)) for f, v in fl.items()}
        is_contested = (max(ad) - min(ad)) >= 2 or any(contested_flags.values())
        row = {
            "doc_id": doc,
            "arm": arm,
            "adequacy_median": float(statistics.median(ad)),
            "adequacy_values": ad,
            "adequacy_range": max(ad) - min(ad),
            **{f"{f}_majority": med_flags[f] for f in FLAGS},
            "fluency_median": float(statistics.median([int(js[j]["fluency"]) for j in judges])),
            "utility_median": float(statistics.median([int(js[j]["utility"]) for j in judges])),
            "contested": is_contested,
            "contested_flags": [f for f, v in contested_flags.items() if v],
            "judges": judges,
        }
        agg_rows.append(row)
        if is_contested:
            contested.append({"doc_id": doc, "arm": arm, "adequacy_range": row["adequacy_range"],
                              "contested_flags": row["contested_flags"]})

    AGG.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in agg_rows) + "\n", encoding="utf-8")

    # Inter-judge ICC on 200 doc-arm targets.
    mat = np.array([
        [int(by[(r["doc_id"], r["arm"])][j]["adequacy"]) for j in judges]
        for r in agg_rows
    ], dtype=float)
    icc = float(icc21(mat))
    contested_rate = len(contested) / len(agg_rows) if agg_rows else 0.0
    panel_gate_pass = (icc >= 0.60 and contested_rate <= 0.10)

    # Descriptive AI-only contrast; NOT primary under D-086.
    by_key = {(r["doc_id"], r["arm"]): r for r in agg_rows}
    docs = sorted({r["doc_id"] for r in agg_rows})
    def paired(a: str, b: str) -> dict[str, Any]:
        ad = np.array([by_key[(d, a)]["adequacy_median"] - by_key[(d, b)]["adequacy_median"] for d in docs])
        us = np.array([by_key[(d, a)]["critical_unsupported_majority"] - by_key[(d, b)]["critical_unsupported_majority"] for d in docs])
        om = np.array([by_key[(d, a)]["critical_omission_majority"] - by_key[(d, b)]["critical_omission_majority"] for d in docs])
        return {
            "contrast": f"{a} - {b}", "n_docs": len(docs),
            "adequacy_mean_diff": float(ad.mean()), "adequacy_ci95": list(bootstrap_ci(ad)),
            "critical_unsupported_rate_diff": float(us.mean()), "critical_unsupported_ci95": list(bootstrap_ci(us)),
            "critical_omission_rate_diff": float(om.mean()), "critical_omission_ci95": list(bootstrap_ci(om)),
        }

    summary = {
        "status": "AI_PANEL_READY" if panel_gate_pass else "INCONCLUSIVE",
        "ai_panel_gate_pass": panel_gate_pass,
        "inconclusive_reasons": [] if panel_gate_pass else [
            reason for reason, fail in (
                ("ai_interjudge_icc_below_0.60", icc < 0.60),
                ("contested_rate_above_0.10", contested_rate > 0.10),
            ) if fail
        ],
        "primary_allowed": False,
        "primary_block_reason": (
            "human calibration and calibration gates not run"
            if panel_gate_pass else
            "AI panel gate failed; D-086 requires INCONCLUSIVE"
        ),
        "ratings": len(rows),
        "aggregated_doc_arms": len(agg_rows),
        "judges": judges,
        "ai_interjudge_icc21_adequacy": icc,
        "ai_interjudge_icc21_min": 0.60,
        "ai_interjudge_pass": icc >= 0.60,
        "contested": len(contested),
        "contested_rate": contested_rate,
        "contested_max": 0.10,
        "contested_pass": contested_rate <= 0.10,
        "contested_items": contested,
        "descriptive_ai_only": {
            "2586_vs_pilot300": paired("2586", "pilot300"),
            "2586_vs_1293": paired("2586", "1293"),
            "1940_vs_pilot300": paired("1940", "pilot300"),
        },
        "human_calibration": "NOT_RUN",
        "human_repeat": "NOT_RUN",
        "candidate_status": "NOT_ELIGIBLE" if panel_gate_pass else "NO_APPROVED_CANDIDATE",
        "test_163": "SEALED",
        "note": "AI panel is a proxy, not human ground truth. Do not use this as an approved candidate.",
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
