#!/usr/bin/env python3
"""Build the deterministic D-085 human-50 single-rater manifest.

The manifest is frozen before any human ratings. It uses only:
- val split IDs
- the 084a audit (already completed)
- deterministic seeds

It never selects test IDs and never reads test predictions.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
AUDIT = ROOT / "reports/provenance/C5_a1/full_2ep/verifier_084a_audit.json"
CLEAN = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
OUT = ROOT / "reports/provenance/C5_human50/manifest.json"

SEED = 20261107
ARMS = ["pilot300", "1293", "1940", "2586"]
KNOWN_RESIDUAL = [
    "REPORT-news_r-02742-00001",  # URL wrap new pass
    "REPORT-news_r-03978-00001",  # time-type residual
    "REPORT-news_r-04709-00001",  # bare 18 unit
    "REPORT-news_r-04951-00002",  # genuine negative control
    "REPORT-news_r-01518-00001",  # source URL truncated
    "REPORT-news_r-03801-00001",  # 1293 identifier residual
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def main() -> int:
    splits = json.loads(SPLITS.read_text(encoding="utf-8"))
    val = set(splits["val"])
    test = set(splits["test"])
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    per = audit["systems"]["2586"]["per_doc"]
    per647 = audit["systems"]["0647"]["per_doc"]
    assert not (val & test)

    def article_prefix(rid: str) -> str:
        return "-".join(rid.split("-")[:3])

    train_prefixes = {article_prefix(rid) for rid in splits["train"]}
    train_prefix_ids = sorted(rid for rid in val if article_prefix(rid) in train_prefixes)

    for rid in KNOWN_RESIDUAL:
        if rid not in val:
            raise SystemExit(f"known residual not in val: {rid}")

    selected: list[str] = []
    categories: dict[str, str] = {}

    def add(rid: str, category: str) -> None:
        if rid not in val:
            raise SystemExit(f"targeted id not in val: {rid}")
        if rid in categories:
            return
        selected.append(rid)
        categories[rid] = category

    # A. Known residuals, fixed order.
    for rid in KNOWN_RESIDUAL:
        add(rid, "known_residual")

    # B. 2586 slot-free docs, sorted ID, first six not already selected.
    slotfree = sorted(rid for rid, x in per.items() if x["a_slot_free"])
    for rid in slotfree:
        if len([r for r in selected if categories.get(r) == "2586_slot_free"]) >= 6:
            break
        add(rid, "2586_slot_free")

    # C. Lowest preservation among non-slot-free docs, sorted by (value, id).
    low = sorted(
        ((x["a_preservation"], rid) for rid, x in per.items() if not x["a_slot_free"]),
    )
    for _, rid in low:
        if len([r for r in selected if categories.get(r) == "2586_low_preservation"]) >= 4:
            break
        if rid not in categories:
            add(rid, "2586_low_preservation")

    # D. 647 residual failures, sorted ID, up to two not already selected.
    d647 = sorted(rid for rid, x in per647.items() if not x["a_grounded"])
    for rid in d647:
        if len([r for r in selected if categories.get(r) == "647_residual"]) >= 2:
            break
        if rid not in categories:
            add(rid, "647_residual")

    # E. Seeded fill to 20.
    if len(selected) < 20:
        remaining = sorted(val - set(selected))
        fill = random.Random(SEED).sample(remaining, 20 - len(selected))
        for rid in fill:
            add(rid, "seeded_fill")
    if len(selected) != 20:
        raise SystemExit(f"targeted count {len(selected)} != 20")
    targeted = list(selected)

    # F. Random 30 from remaining val, fixed seed.
    remaining = sorted(val - set(targeted))
    random30 = random.Random(SEED).sample(remaining, 30)
    if len(set(targeted) & set(random30)) or len(set(targeted) | set(random30)) != 50:
        raise SystemExit("sample construction error")

    # G. Repeat 10: six targeted (first four known + first two slot-free) + four random.
    repeat_targeted = [rid for rid in targeted if categories[rid] == "known_residual"][:4]
    repeat_slotfree = [rid for rid in targeted if categories[rid] == "2586_slot_free"][:2]
    repeat_ids = repeat_targeted + repeat_slotfree + random30[:4]
    if len(repeat_ids) != 10 or len(set(repeat_ids)) != 10:
        raise SystemExit(f"repeat count {len(repeat_ids)} / unique {len(set(repeat_ids))}")

    all50 = targeted + random30
    if len(set(all50)) != 50:
        raise SystemExit("50 sample not unique")

    # H. Session assignment: 5 primary sessions of 10 docs; 2 repeat sessions of 5.
    session_rng = random.Random(SEED + 1)
    primary_order = list(all50)
    session_rng.shuffle(primary_order)
    session_of = {rid: i // 10 + 1 for i, rid in enumerate(primary_order)}
    repeat_order = list(repeat_ids)
    random.Random(SEED + 2).shuffle(repeat_order)
    repeat_session_of = {rid: i // 5 + 1 for i, rid in enumerate(repeat_order)}

    # I. Per-document arm order, fixed before ratings.
    arm_order = {}
    for rid in all50:
        order = list(ARMS)
        random.Random(f"{SEED}:{rid}").shuffle(order)
        arm_order[rid] = order

    # Repeat pass has a separate randomized arm order.
    repeat_arm_order = {}
    for rid in repeat_ids:
        order = list(ARMS)
        random.Random(f"{SEED}:repeat:{rid}").shuffle(order)
        repeat_arm_order[rid] = order

    # J. Source/target hashes (no text in manifest).
    data = {str(r["id"]): r for r in load_jsonl(CLEAN) if str(r["id"]) in set(all50)}
    if set(data) != set(all50):
        raise SystemExit("missing rows for sample")
    hashes = {
        rid: {
            "source_sha256": sha256_text(str(data[rid]["passage"])),
            "target_sha256": sha256_text(str(data[rid]["summary"])),
        }
        for rid in all50
    }

    manifest = {
        "protocol": "D-085 human50 single-rater v1.0.0",
        "status": "FROZEN",
        "frozen_before_ratings": True,
        "created": "2026-11-07",
        "seed": SEED,
        "val_n": len(val),
        "targeted_n": len(targeted),
        "random_n": len(random30),
        "sample_n": len(all50),
        "repeat_n": len(repeat_ids),
        "primary_ratings": len(all50) * len(ARMS),
        "repeat_ratings": len(repeat_ids) * len(ARMS),
        "total_ratings": len(all50) * len(ARMS) + len(repeat_ids) * len(ARMS),
        "arms": ARMS,
        "selection_rule": {
            "targeted": [
                "6 known residual IDs",
                "6 lowest-ID 2586 slot-free docs not already selected",
                "4 lowest-preservation non-slot-free 2586 docs",
                "2 lowest-ID 647 residual failures not already selected",
                "seeded fill to 20",
            ],
            "random": "30 from remaining val, seed 20261107",
            "repeat": "4 known residual + 2 2586 slot-free targeted + first 4 random30",
        },
        "targeted": [
            {"id": rid, "category": categories[rid], "session": session_of[rid], "arm_order": arm_order[rid], "train_prefix_shared": rid in set(train_prefix_ids)}
            for rid in targeted
        ],
        "random": [
            {"id": rid, "category": "random30", "session": session_of[rid], "arm_order": arm_order[rid], "train_prefix_shared": rid in set(train_prefix_ids)}
            for rid in random30
        ],
        "repeat": [
            {
                "id": rid,
                "stratum": "targeted" if rid in targeted else "random30",
                "repeat_session": repeat_session_of[rid],
                "arm_order": repeat_arm_order[rid],
            }
            for rid in repeat_ids
        ],
        "sessions": {
            "primary": {str(i): [rid for rid in primary_order if session_of[rid] == i] for i in range(1, 6)},
            "repeat": {str(i): [rid for rid in repeat_order if repeat_session_of[rid] == i] for i in range(1, 3)},
        },
        "repeat_gap_days_min": 7,
        "ratings_per_session_max": 40,
        "train_prefix_article_rule": "first three hyphen-separated components of id",
        "train_prefix_ids": train_prefix_ids,
        "train_prefix_n": len(train_prefix_ids),
        "hashes": hashes,
        "decision_rule": {
            "primary_contrast": "2586 - pilot300",
            "adequacy_scale": [0, 4],
            "adequacy_lower_95_margin": -0.25,
            "critical_unsupported_upper_95_margin": 0.05,
            "critical_omission_upper_95_margin": 0.05,
            "train_prefix_sensitivity": {
                "exclude_train_prefix_ids": True,
                "adequacy_lower_95_margin": -0.25,
                "critical_unsupported_upper_95_margin": 0.05,
                "critical_omission_upper_95_margin": 0.05,
            },
            "intra_rater_icc_min": 0.70,
            "intra_rater_weighted_kappa_min": 0.60,
            "bootstrap_resamples": 10000,
            "bootstrap_seed": 20261107,
        },
        "test_163": "SEALED",
        "rater_count": 1,
        "inter_rater_reliability": "NOT_AVAILABLE",
        "note": "No ratings were collected before this manifest was frozen. Test 163 is not in the sample.",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(OUT),
        "targeted": len(targeted),
        "random": len(random30),
        "repeat": len(repeat_ids),
        "primary_ratings": manifest["primary_ratings"],
        "repeat_ratings": manifest["repeat_ratings"],
        "total_ratings": manifest["total_ratings"],
        "categories": {c: sum(1 for x in categories.values() if x == c) for c in sorted(set(categories.values()))},
        "targeted_ids": targeted,
        "repeat_ids": repeat_ids,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
