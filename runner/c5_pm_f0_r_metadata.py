"""Repair/verify C5 F0 R summary metadata from frozen inputs and units.

This does not recompute labels. It only replaces summary metadata fields that
were placeholders in the first R run: donor-map hashes, per-doc donor hashes,
donor-map load count, and CE-call counts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_mt5_lora_b0 import donors_for  # noqa: E402
from runner.c5_mt5_layer_probe import load_layer_cache  # noqa: E402
from runner.c5_pm_f0 import CACHE, sha256_bytes  # noqa: E402

PREFLIGHT = ROOT / "reports/provenance/C5_b0a/m_cohort_preflight.json"
R = ROOT / "reports/provenance/C5_f0/r"
SUMMARY = R / "r_mechanics_pass.json"
AUDIT = R / "metadata_audit.json"
UNITS = R / "units"


def canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def main() -> int:
    preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    val_ids = list(preflight["val20_ids"])
    common = list(preflight["common_ids"])
    cache = load_layer_cache("train", CACHE)
    cache.update(load_layer_cache("val", CACHE))
    donors = donors_for(val_ids, cache, 5)
    if set(donors) != set(val_ids):
        raise RuntimeError("donor map does not cover val20")
    for rid, ds in donors.items():
        if len(ds) != 5 or len(set(ds)) != 5:
            raise RuntimeError(f"donor count/duplicate for {rid}")

    unit_files = sorted(UNITS.glob("*.json"))
    if len(unit_files) != 12:
        raise RuntimeError(f"expected 12 units, got {len(unit_files)}")
    units = [json.loads(p.read_text(encoding="utf-8")) for p in unit_files]

    # Frozen operation-table counts, all units:
    # eval_signal: step0+final = 2 * 20 docs real, 2 * 20 * 5 donor-wrong.
    # m_records_for: 15 common targets real; 2 controls per target.
    # phase7: 15 targets * 5 donors real + donor-wrong; 2 control baselines/target.
    real_per_unit = 2 * 20 + 15 + 15 * 5
    wrong_per_unit = 2 * 20 * 5 + 15 * 5
    expected_real = real_per_unit * len(units)
    expected_wrong = wrong_per_unit * len(units)
    expected_donor_loads = len(units)

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    summary["real_memory_ce_calls"] = int(expected_real)
    summary["wrong_donor_ce_calls"] = int(expected_wrong)
    summary["donor_map_loads"] = int(expected_donor_loads)
    summary["donor_map_sha256"] = sha256_bytes(canon(donors).encode("utf-8"))
    summary["per_doc_donor_sha256"] = {
        rid: sha256_bytes(canon(donors[rid]).encode("utf-8")) for rid in val_ids
    }
    summary["r_mechanics_pass"] = bool(
        summary.get("partial", False) is False
        and summary.get("updates_total") == 900
        and summary.get("m_records") == 1440
        and summary.get("phase7_records") == 7200
        and summary.get("generation_records") == 240
        and summary.get("provenance_ok") is True
        and len(units) == 12
    )
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    audit = {
        "schema_version": "1",
        "purpose": "repair placeholder R summary metadata; labels unchanged",
        "units": len(units),
        "donor_map_sha256": summary["donor_map_sha256"],
        "per_doc_donor_sha256": summary["per_doc_donor_sha256"],
        "counts": {
            "real_memory_ce_calls": int(expected_real),
            "wrong_donor_ce_calls": int(expected_wrong),
            "donor_map_loads": int(expected_donor_loads),
            "derivation": {
                "real_per_unit": int(real_per_unit),
                "wrong_per_unit": int(wrong_per_unit),
                "eval_real_per_unit": 40,
                "eval_wrong_per_unit": 200,
                "m_real_per_unit": 15,
                "phase7_real_per_unit": 75,
                "phase7_wrong_per_unit": 75,
            },
        },
        "common_ids_count": len(common),
        "val20_count": len(val_ids),
        "labels_unchanged": True,
    }
    AUDIT.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "r_mechanics_pass": summary["r_mechanics_pass"],
        "real_memory_ce_calls": expected_real,
        "wrong_donor_ce_calls": expected_wrong,
        "donor_map_loads": expected_donor_loads,
        "donor_map_sha256": summary["donor_map_sha256"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
