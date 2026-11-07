#!/usr/bin/env python3
"""Build the D-086 hybrid AI-panel + human-calibration manifest.

D-085 is not modified. D-086 reuses its frozen 50-doc sample and adds:
- 3 AI judges x 50 docs x 4 summaries = 600 AI ratings
- 20 docs x 4 summaries = 80 human calibration ratings
- 5 docs x 4 summaries = 20 human repeat ratings

No AI call and no human rating is performed by this script.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
D085 = ROOT / "reports/provenance/C5_human50/manifest.json"
OUT = ROOT / "reports/provenance/C5_hybrid/manifest.json"

SEED = 20261107
ARMS = ["pilot300", "1293", "1940", "2586"]
JUDGES = [
    {"id": "glm", "model": "z-ai/glm-5.3-flash", "reasoning": "max"},
    {"id": "sonnet", "model": "claude-sonnet-5-5", "reasoning": "high"},
    {"id": "sol", "model": "gpt-6.1-sol", "reasoning": "xhigh"},
]


def main() -> int:
    d085 = json.loads(D085.read_text(encoding="utf-8"))
    sample = [x["id"] for x in d085["targeted"] + d085["random"]]
    targeted = [x["id"] for x in d085["targeted"]]
    random30 = [x["id"] for x in d085["random"]]
    assert len(sample) == 50 and len(set(sample)) == 50

    # Human calibration: 10 targeted + 10 random.
    calib_targeted = targeted[:10]
    calib_random = random30[:10]
    calibration = calib_targeted + calib_random
    assert len(calibration) == 20 and len(set(calibration)) == 20

    # Human repeat: first 3 targeted + first 2 random.
    repeat_ids = targeted[:3] + random30[:2]
    assert len(repeat_ids) == 5 and len(set(repeat_ids)) == 5

    # Independent A-D order per judge/doc.
    judge_arm_order: dict[str, dict[str, list[str]]] = {}
    for judge in JUDGES:
        judge_arm_order[judge["id"]] = {}
        for rid in sample:
            order = list(ARMS)
            random.Random(f"{SEED}:{judge['id']}:{rid}").shuffle(order)
            judge_arm_order[judge["id"]][rid] = order

    # Human sessions: 4 calibration sessions x 5 docs; 1 repeat session x 5 docs.
    calib_order = list(calibration)
    random.Random(SEED + 11).shuffle(calib_order)
    calibration_sessions = {
        str(i): calib_order[(i - 1) * 5:i * 5] for i in range(1, 5)
    }
    repeat_sessions = {"1": list(repeat_ids)}

    cats = {x["id"]: x["category"] for x in d085["targeted"]}
    manifest = {
        "protocol": "D-086 hybrid AI-panel + human-calibration v1.0.0",
        "status": "FROZEN",
        "frozen_before_ai_calls": True,
        "frozen_before_human_ratings": True,
        "created": "2026-11-07",
        "supersedes": "D-085 human50 single-rater protocol (before any human rating)",
        "base_sample": "D-085 frozen 50-doc sample",
        "seed": SEED,
        "arms": ARMS,
        "sample_n": 50,
        "ai_panel": {
            "judges": JUDGES,
            "docs": 50,
            "summaries_per_doc": 4,
            "ratings_per_judge": 200,
            "total_ratings": 600,
            "blind": True,
            "target_hidden": True,
            "metrics_hidden": True,
            "independent_arm_order": True,
        },
        "human_calibration": {
            "n_docs": 20,
            "targeted": 10,
            "random": 10,
            "ratings": 80,
            "sessions": calibration_sessions,
            "status": "NOT_RUN",
        },
        "human_repeat": {
            "n_docs": 5,
            "targeted": 3,
            "random": 2,
            "ratings": 20,
            "gap_days_min": 7,
            "sessions": repeat_sessions,
            "status": "NOT_RUN",
        },
        "human_total_ratings": 100,
        "calibration_ids": calibration,
        "calibration_categories": [
            {"id": rid, "category": cats.get(rid, "random30")} for rid in calibration
        ],
        "repeat_ids": repeat_ids,
        "judge_arm_order": judge_arm_order,
        "hashes": d085["hashes"],
        "train_prefix_ids": d085["train_prefix_ids"],
        "decision_rule": {
            "primary_contrast": "2586 - pilot300",
            "adequacy_lower_95_margin": -0.25,
            "critical_unsupported_upper_95_margin": 0.05,
            "critical_omission_upper_95_margin": 0.05,
            "ai_human_calibration": {
                "adequacy_icc21_min": 0.70,
                "adequacy_qwk_min": 0.60,
                "critical_unsupported_kappa_min": 0.60,
                "critical_omission_kappa_min": 0.60,
            },
            "human_repeat": {
                "adequacy_icc21_min": 0.70,
                "adequacy_qwk_min": 0.60,
            },
            "ai_interjudge": {
                "adequacy_icc21_min": 0.60,
            },
            "contested": {
                "adequacy_range_cutoff": 2,
                "critical_vote_split": True,
                "max_rate": 0.10,
                "sensitivity_required": True,
            },
            "bootstrap_resamples": 10000,
            "bootstrap_seed": 20261107,
        },
        "test_163": "SEALED",
        "human_inter_rater_reliability": "NOT_AVAILABLE",
        "ai_independence_claim": "NOT_INDEPENDENT",
        "note": "AI panel is a proxy, not a human population. Human calibration is required before AI-panel primary evidence.",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(OUT),
        "sample": len(sample),
        "calibration": len(calibration),
        "repeat": len(repeat_ids),
        "ai_ratings": 600,
        "human_calibration_ratings": 80,
        "human_repeat_ratings": 20,
        "human_total": 100,
        "calibration_targeted": calib_targeted,
        "calibration_random": calib_random,
        "repeat_ids": repeat_ids,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
