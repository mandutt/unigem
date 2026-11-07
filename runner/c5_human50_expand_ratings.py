#!/usr/bin/env python3
"""Convert blind rating-sheet export (slot) to canonical arm-labelled ratings.

The rating sheet intentionally contains only slots 0-3, never arm names.
This converter uses the frozen manifest to map slot -> arm.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MANIFEST = ROOT / "reports/provenance/C5_human50/manifest.json"
FIELDS = [
    "doc_id", "arm", "pass", "adequacy",
    "critical_unsupported", "critical_omission",
    "wrong_unit_qualifier", "entity_relation", "fluency", "utility", "notes",
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--manifest", default=MANIFEST, type=Path)
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    primary_order = {
        x["id"]: x["arm_order"]
        for x in manifest["targeted"] + manifest["random"]
    }
    repeat_order = {x["id"]: x["arm_order"] for x in manifest["repeat"]}
    rows = load_jsonl(args.input)
    out = []
    seen = set()
    for r in rows:
        rid = str(r["doc_id"])
        slot = int(r["slot"])
        pass_no = int(r.get("pass", 1))
        order = repeat_order.get(rid) if pass_no == 2 else primary_order.get(rid)
        if order is None:
            raise SystemExit(f"unknown doc/pass: {rid} pass={pass_no}")
        if slot not in range(4):
            raise SystemExit(f"slot out of range: {rid} slot={slot}")
        key = (rid, slot, pass_no)
        if key in seen:
            raise SystemExit(f"duplicate: {key}")
        seen.add(key)
        row = {k: r[k] for k in FIELDS if k in r and k not in {"arm"}}
        row["arm"] = order[slot]
        row["doc_id"] = rid
        row["slot"] = slot
        row["pass"] = pass_no
        out.append(row)

    expected = {(d, s, 1) for d, order in primary_order.items() for s in range(4)}
    expected |= {(d, s, 2) for d, order in repeat_order.items() for s in range(4)}
    # Primary sheet currently exports pass 1 only; allow a complete future repeat file.
    if len(rows) == 200:
        expected = {(d, s, 1) for d in primary_order for s in range(4)}
    missing = expected - seen
    extra = seen - expected
    if missing or extra:
        raise SystemExit(json.dumps({"missing": len(missing), "extra": len(extra), "status": "INCONCLUSIVE"}))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.output), "rows": len(out), "pass1": sum(1 for r in out if r["pass"] == 1), "pass2": sum(1 for r in out if r["pass"] == 2)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
