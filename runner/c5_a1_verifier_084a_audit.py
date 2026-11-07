#!/usr/bin/env python3
"""D-084 rev3 / 084a bidirectional audit.

Allowed inputs:
- clean train + val rows (by splits.json allowlist)
- excluded rows (full v3 minus clean)
- saved val predictions for five systems

Never loads test predictions or evaluates test 163.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval.slot_verify import verify_summary  # noqa: E402
from eval.slot_verify_084a import verify_084a  # noqa: E402

CLEAN = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
FULL = ROOT / "data/external/f5_pairs_v3.jsonl"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
RUN = ROOT / "reports/provenance/C5_a1/full_2ep"
PILOT = ROOT / "reports/provenance/C5_a1/pilot300_val161/predictions.jsonl"


def load_jsonl(path: Path, keep_ids: set[str] | None = None, reject_ids: set[str] | None = None) -> list[dict[str, Any]]:
    out = []
    for x in path.read_text(encoding="utf-8").splitlines():
        if not x.strip():
            continue
        row = json.loads(x)
        rid = str(row.get("id"))
        if keep_ids is not None and rid not in keep_ids:
            continue
        if reject_ids is not None and rid in reject_ids:
            continue
        out.append(row)
    return out


def main() -> int:
    splits = json.loads(SPLITS.read_text(encoding="utf-8"))
    train_ids = set(splits["train"])
    val_ids = set(splits["val"])
    test_ids = set(splits["test"])
    allowed_ids = train_ids | val_ids
    assert not (allowed_ids & test_ids), "train/val/test overlap"

    clean_ids = train_ids | val_ids | test_ids
    # Keep only train/val rows in memory; test rows are skipped at parse time.
    data = {str(r["id"]): r for r in load_jsonl(CLEAN, keep_ids=allowed_ids)}
    # Excluded pool = full v3 minus clean; reject every clean/test id.
    excluded = load_jsonl(FULL, reject_ids=clean_ids)

    # Materialize allowlisted inputs only. Test rows are never used.
    train_val = list(data.values())
    assert len(train_val) == len(train_ids) + len(val_ids), (len(train_val), len(train_ids), len(val_ids))
    assert all(str(r["id"]) not in test_ids for r in train_val)

    systems = {
        "pilot300": PILOT,
        "0647": RUN / "eval_step_0647/eval.jsonl",
        "1293": RUN / "eval_step_1293/eval.jsonl",
        "1940": RUN / "eval_step_1940/eval.jsonl",
        "2586": RUN / "eval_step_2586/eval.jsonl",
    }
    out: dict[str, Any] = {
        "scope": "D-084 rev3 084a; train/val + excluded only; test 163 not loaded",
        "allowed": {"train": len(train_ids), "val": len(val_ids), "excluded": len(excluded)},
        "test_loaded": False,
        "systems": {},
        "target_audit": {},
    }

    # Clean train/val targets: strictness can create new failures.
    target_changes = []
    for r in train_val:
        rid = str(r["id"])
        src = str(r["passage"])
        tgt = str(r["summary"])
        v1 = verify_summary(src, tgt)
        a = verify_084a(src, tgt)
        if (not v1.new) != a.grounded:
            target_changes.append({
                "id": rid,
                "v1_grounded": not v1.new,
                "084a_grounded": a.grounded,
                "v1_new": list(v1.new),
                "084a_new": list(a.new),
                "unresolved": [u.__dict__ for u in a.unresolved],
            })
    out["target_audit"]["train_val"] = {
        "n": len(train_val),
        "v1_grounded": sum(1 for r in train_val if not verify_summary(str(r["passage"]), str(r["summary"])).new),
        "a_grounded": sum(1 for r in train_val if verify_084a(str(r["passage"]), str(r["summary"])).grounded),
        "changes": target_changes,
    }

    # Excluded 383: 084a should have zero flips if URL-only.
    ex_changes = []
    for r in excluded:
        rid = str(r["id"])
        src = str(r["passage"])
        tgt = str(r["summary"])
        v1 = verify_summary(src, tgt)
        a = verify_084a(src, tgt)
        if (not v1.new) != a.grounded:
            ex_changes.append({
                "id": rid,
                "v1_grounded": not v1.new,
                "084a_grounded": a.grounded,
                "v1_new": list(v1.new),
                "084a_new": list(a.new),
                "unresolved": [u.__dict__ for u in a.unresolved],
            })
    out["target_audit"]["excluded"] = {
        "n": len(excluded),
        "v1_grounded": sum(1 for r in excluded if not verify_summary(str(r["passage"]), str(r["summary"])).new),
        "a_grounded": sum(1 for r in excluded if verify_084a(str(r["passage"]), str(r["summary"])).grounded),
        "changes": ex_changes,
    }

    for name, path in systems.items():
        rows = load_jsonl(path)
        by_id = {str(r["id"]): r for r in rows}
        assert set(by_id) == val_ids, (name, len(by_id), len(val_ids))
        per = {}
        new_pass: list[str] = []
        new_fail: list[str] = []
        unresolved_docs: list[str] = []
        for rid, r in by_id.items():
            source = str(data[rid]["passage"])
            pred = str(r.get("pred") or r.get("prediction") or "")
            v1 = verify_summary(source, pred)
            a = verify_084a(source, pred)
            v1g = not v1.new
            ag = a.grounded
            per[rid] = {
                "v1_grounded": v1g,
                "a_grounded": ag,
                "v1_new": list(v1.new),
                "a_new": list(a.new),
                "a_new_count": len(a.new),
                "a_missing_count": len(a.missing),
                "a_source_count": len(a.source_slots),
                "a_summary_count": len(a.summary_slots),
                "v1_missing": list(v1.missing),
                "a_missing": list(a.missing),
                "v1_slot_free": v1.summary_count == 0,
                "a_slot_free": a.slot_free,
                "v1_preservation": v1.slot_preservation,
                "a_preservation": a.slot_preservation,
                "url_repairs": [x.__dict__ for x in a.url_repairs],
                "unresolved": [x.__dict__ for x in a.unresolved],
            }
            if not v1g and ag:
                new_pass.append(rid)
            if v1g and not ag:
                new_fail.append(rid)
            if a.unresolved:
                unresolved_docs.append(rid)
        out["systems"][name] = {
            "n": len(rows),
            "v1_grounded": sum(1 for x in per.values() if x["v1_grounded"]),
            "a_grounded": sum(1 for x in per.values() if x["a_grounded"]),
            "new_pass": new_pass,
            "new_fail": new_fail,
            "unresolved_docs": unresolved_docs,
            "changed": {rid: x for rid, x in per.items() if x["v1_grounded"] != x["a_grounded"]},
            "per_doc": per,
        }

    # URL census over allowed source material (no test).
    url_repair_docs = []
    unresolved_docs = []
    for r in train_val + excluded:
        rid = str(r["id"])
        a = verify_084a(str(r["passage"]), str(r["summary"]))
        if a.url_repairs:
            url_repair_docs.append({"id": rid, "count": len(a.url_repairs)})
        if a.unresolved:
            unresolved_docs.append({"id": rid, "reasons": sorted({u.reason for u in a.unresolved})})
    out["url_census"] = {
        "repair_docs": url_repair_docs,
        "unresolved_docs": unresolved_docs,
        "reason_counts": dict(Counter(
            u.reason for r in train_val + excluded
            for u in verify_084a(str(r["passage"]), str(r["summary"])).unresolved
        )),
    }

    path = RUN / "verifier_084a_audit.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "allowed": out["allowed"],
        "systems": {
            k: {kk: v[kk] for kk in ("n", "v1_grounded", "a_grounded", "new_pass", "new_fail", "unresolved_docs")}
            for k, v in out["systems"].items()
        },
        "target_audit": {
            k: {"n": v["n"], "v1_grounded": v["v1_grounded"], "a_grounded": v["a_grounded"], "changes": len(v["changes"])}
            for k, v in out["target_audit"].items()
        },
        "url_census": {"repair_docs": len(url_repair_docs), "unresolved_docs": len(unresolved_docs), "reason_counts": out["url_census"]["reason_counts"]},
    }, ensure_ascii=False, indent=2))
    print("wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
