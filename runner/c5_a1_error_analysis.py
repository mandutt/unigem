#!/usr/bin/env python3
"""Analyze A1 full-train grounded failures and 1,940-vs-2,586 compression drift."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval.slot_verify import verify_summary

DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
RUN = ROOT / "reports/provenance/C5_a1/full_2ep"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def slot_info(report) -> dict[str, Any]:
    return {
        "source_count": report.source_count,
        "summary_count": report.summary_count,
        "slot_preservation": report.slot_preservation,
        "new_slot_rate": report.new_slot_rate,
        "missing": list(report.missing),
        "new": list(report.new),
        "missing_slots": [
            {"kind": s.kind, "value": s.value}
            for s in report.source_slots
            if s.canonical in set(report.missing)
        ],
        "new_slots": [
            {"kind": s.kind, "value": s.value}
            for s in report.summary_slots
            if s.canonical in set(report.new)
        ],
    }


def main() -> int:
    data = {str(r["id"]): r for r in load_jsonl(DATA)}
    preds = {
        step: {str(r["id"]): r for r in load_jsonl(RUN / f"eval_step_{step:04d}/eval.jsonl")}
        for step in (1940, 2586)
    }
    out: dict[str, Any] = {"run": str(RUN), "checkpoints": {}}

    for step, rows in preds.items():
        enriched = {}
        for rid, row in rows.items():
            source = str(data[rid]["passage"])
            rep = verify_summary(source, str(row["pred"]))
            enriched[rid] = {**row, **slot_info(rep)}
        slotfree = [rid for rid, r in enriched.items() if r["summary_count"] == 0]
        grounded_fail = [rid for rid, r in enriched.items() if not r["grounded"]]
        target_slots = []
        for rid, row in rows.items():
            target_rep = verify_summary(str(data[rid]["passage"]), str(row["target"]))
            target_slots.append(target_rep.summary_count)
        out["checkpoints"][str(step)] = {
            "n": len(enriched),
            "char_f1_mean": sum(float(r["char_f1"]) for r in enriched.values()) / len(enriched),
            "grounded": sum(bool(r["grounded"]) for r in enriched.values()),
            "nonvacuous_n": len(enriched) - len(slotfree),
            "nonvacuous_grounded": sum(bool(r["grounded"]) for r in enriched.values() if r["summary_count"] > 0),
            "slotfree_ids": slotfree,
            "grounded_fail_ids": grounded_fail,
            "sum_slots": sum(int(r["summary_count"]) for r in enriched.values()),
            "slots_per_doc": sum(int(r["summary_count"]) for r in enriched.values()) / len(enriched),
            "target_slots_mean": sum(target_slots) / len(target_slots),
            "slot_preservation_mean": sum(float(r["slot_preservation"]) for r in enriched.values()) / len(enriched),
            "gen_len_mean": sum(float(r["gen_len"]) for r in enriched.values()) / len(enriched),
            "new_slot_count": sum(len(r["new"]) for r in enriched.values()),
            "missing_slot_count": sum(len(r["missing"]) for r in enriched.values()),
            "new_kinds": dict(Counter(s["kind"] for r in enriched.values() for s in r["new_slots"])),
            "missing_kinds": dict(Counter(s["kind"] for r in enriched.values() for s in r["missing_slots"])),
            "slotfree": [
                {
                    "id": rid,
                    "char_f1": enriched[rid]["char_f1"],
                    "gen_len": enriched[rid]["gen_len"],
                    "target_slots": verify_summary(str(data[rid]["passage"]), str(enriched[rid]["target"])).summary_count,
                    "pred_len": len(str(enriched[rid]["pred"])),
                    "pred_prefix": str(enriched[rid]["pred"])[:160],
                    "target_prefix": str(enriched[rid]["target"])[:160],
                }
                for rid in slotfree
            ],
            "grounded_failures": [
                {
                    "id": rid,
                    "char_f1": enriched[rid]["char_f1"],
                    "gen_len": enriched[rid]["gen_len"],
                    "source_count": enriched[rid]["source_count"],
                    "summary_count": enriched[rid]["summary_count"],
                    "slot_preservation": enriched[rid]["slot_preservation"],
                    "missing": enriched[rid]["missing"],
                    "new": enriched[rid]["new"],
                    "new_slots": enriched[rid]["new_slots"],
                    "missing_slots": enriched[rid]["missing_slots"],
                    "pred_prefix": str(enriched[rid]["pred"])[:240],
                    "target_prefix": str(enriched[rid]["target"])[:240],
                }
                for rid in grounded_fail
            ],
        }
        out.setdefault("_enriched", {})[str(step)] = enriched

    a = out["_enriched"]["1940"]
    b = out["_enriched"]["2586"]
    ids = sorted(set(a) & set(b))
    deltas = []
    for rid in ids:
        deltas.append({
            "id": rid,
            "slots_delta": int(b[rid]["summary_count"]) - int(a[rid]["summary_count"]),
            "f1_delta": float(b[rid]["char_f1"]) - float(a[rid]["char_f1"]),
            "len_delta": float(b[rid]["gen_len"]) - float(a[rid]["gen_len"]),
            "preservation_delta": float(b[rid]["slot_preservation"]) - float(a[rid]["slot_preservation"]),
            "from_slotfree": a[rid]["summary_count"] == 0,
            "to_slotfree": b[rid]["summary_count"] == 0,
            "new_1940": len(a[rid]["new"]),
            "new_2586": len(b[rid]["new"]),
        })
    out["delta_1940_to_2586"] = {
        "n": len(ids),
        "slots_delta_sum": sum(d["slots_delta"] for d in deltas),
        "slots_delta_mean": sum(d["slots_delta"] for d in deltas) / len(deltas),
        "slots_loss_docs": sum(d["slots_delta"] < 0 for d in deltas),
        "slots_gain_docs": sum(d["slots_delta"] > 0 for d in deltas),
        "slots_same_docs": sum(d["slots_delta"] == 0 for d in deltas),
        "new_slotfree": sum(d["to_slotfree"] and not d["from_slotfree"] for d in deltas),
        "recovered_slotfree": sum(d["from_slotfree"] and not d["to_slotfree"] for d in deltas),
        "mean_f1_delta": sum(d["f1_delta"] for d in deltas) / len(deltas),
        "mean_len_delta": sum(d["len_delta"] for d in deltas) / len(deltas),
        "mean_preservation_delta": sum(d["preservation_delta"] for d in deltas) / len(deltas),
        "top_slot_losses": sorted(deltas, key=lambda d: (d["slots_delta"], d["f1_delta"]))[:15],
        "new_slotfree_ids": [d["id"] for d in deltas if d["to_slotfree"] and not d["from_slotfree"]],
        "recovered_slotfree_ids": [d["id"] for d in deltas if d["from_slotfree"] and not d["to_slotfree"]],
    }
    out.pop("_enriched", None)
    path = RUN / "error_analysis_1940_vs_2586.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out["checkpoints"], ensure_ascii=False, indent=2))
    print(json.dumps(out["delta_1940_to_2586"], ensure_ascii=False, indent=2))
    print("wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
