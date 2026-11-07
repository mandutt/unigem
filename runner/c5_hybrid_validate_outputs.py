#!/usr/bin/env python3
"""Validate D-086 AI panel outputs and emit canonical judge ratings.

The model output is expected to be JSON, but markdown fences or leading prose
are tolerated. Every summary label is mapped back to the frozen arm order.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reports/provenance/C5_hybrid/manifest.json"
OUTDIR = ROOT / "reports/provenance/C5_hybrid/ai_outputs"
RAW = ROOT / "reports/provenance/C5_hybrid/ai_ratings.jsonl"
VALID = ROOT / "reports/provenance/C5_hybrid/ai_output_validation.json"
HASH = ROOT / "reports/provenance/C5_hybrid/ai_outputs.sha256"

FIELDS = ("adequacy", "critical_unsupported", "critical_omission", "wrong_unit_qualifier", "entity_relation", "fluency", "utility")


def extract_json(text: str) -> dict[str, Any]:
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.I)
        s = re.sub(r"\s*```$", "", s)
    start, end = s.find("{"), s.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object")
    return json.loads(s[start:end + 1])


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    judges = manifest["ai_panel"]["judges"]
    sample = {x["id"] for x in json.loads((ROOT / "reports/provenance/C5_human50/manifest.json").read_text(encoding="utf-8"))["targeted"]}
    d085 = json.loads((ROOT / "reports/provenance/C5_human50/manifest.json").read_text(encoding="utf-8"))
    sample = {x["id"] for x in d085["targeted"] + d085["random"]}
    rows = []
    errors = []
    file_hashes = {}
    for judge in judges:
        jid = judge["id"]
        for doc in sorted(sample):
            path = OUTDIR / jid / f"{doc}.out"
            if not path.exists():
                errors.append({"judge": jid, "doc": doc, "error": "missing output"})
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            file_hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
            try:
                obj = extract_json(text)
                if str(obj.get("doc_id")) != doc:
                    raise ValueError(f"doc_id mismatch {obj.get('doc_id')}")
                summaries = obj["summaries"]
                order = manifest["judge_arm_order"][jid][doc]
                for i, label in enumerate(["A", "B", "C", "D"]):
                    s = summaries[label]
                    for f in FIELDS:
                        if f not in s:
                            raise ValueError(f"missing {f} in {label}")
                    if int(s["adequacy"]) not in range(5):
                        raise ValueError(f"bad adequacy {label}")
                    for f in ("critical_unsupported", "critical_omission", "wrong_unit_qualifier", "entity_relation"):
                        if int(s[f]) not in (0, 1):
                            raise ValueError(f"bad {f} {label}")
                    if int(s["fluency"]) not in range(1, 6) or int(s["utility"]) not in range(1, 6):
                        raise ValueError(f"bad fluency/utility {label}")
                    rows.append({
                        "judge": jid,
                        "doc_id": doc,
                        "arm": order[i],
                        "slot": i,
                        **{f: int(s[f]) for f in FIELDS},
                        "evidence": s.get("evidence", []),
                        "reason": s.get("reason", ""),
                    })
            except Exception as exc:  # noqa: BLE001
                errors.append({"judge": jid, "doc": doc, "error": str(exc)[:300]})

    RAW.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    HASH.write_text("\n".join(f"{h}  {p}" for p, h in sorted(file_hashes.items())) + "\n", encoding="utf-8")
    validation = {
        "expected": 600,
        "parsed": len(rows),
        "errors": errors,
        "error_count": len(errors),
        "judges": [j["id"] for j in judges],
        "docs": len(sample),
        "per_judge": {j["id"]: sum(1 for r in rows if r["judge"] == j["id"]) for j in judges},
        "hash_manifest": str(HASH.relative_to(ROOT)),
    }
    VALID.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(validation, ensure_ascii=False, indent=2))
    return 0 if not errors and len(rows) == 600 else 1


if __name__ == "__main__":
    raise SystemExit(main())
