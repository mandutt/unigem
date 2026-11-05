#!/usr/bin/env python3
"""Read-only text-level overlap audit for W2B (test/dev vs training manifests)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval.normalize import normalize_nospace

OUT = ROOT / "reports/provenance/W2B/overlap_text_audit.json"
SOURCES = {
    "short_v2": ROOT / "data/wave2b/short_4h_v2.jsonl",
    "short_v1": ROOT / "data/wave2b/short_4h_v1.jsonl",
    "wave1": ROOT / "data/wave1/manifest.jsonl",
    "kspon_long": ROOT / "data/wave2b/long_4h.jsonl",
    "zeroth_long": ROOT / "data/wave2b/long_4h_zeroth.jsonl",
}


def load_manifest(path: Path) -> set[str]:
    if not path.exists():
        return set()
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        text = r.get("ref") or r.get("text") or ""
        n = normalize_nospace(text)
        if n:
            out.add(n)
    return out


def audit(pred_path: Path, label: str, sources: dict[str, set[str]]) -> dict:
    d = json.loads(pred_path.read_text(encoding="utf-8"))
    rows = d["sentences"]
    out = {"n": len(rows), "ref_chars": sum(int(r["ref_chars"]) for r in rows), "sources": {}}
    overlap_all = set()
    chars_all = 0
    for name, refs in sources.items():
        ids = [r["id"] for r in rows if r.get("ref_norm", normalize_nospace(r.get("ref", ""))) in refs]
        chars = sum(int(r["ref_chars"]) for r in rows if r["id"] in set(ids))
        out["sources"][name] = {"rows": len(ids), "chars": chars, "rate_pct": 100.0 * len(ids) / max(1, len(rows))}
        overlap_all.update(ids)
        chars_all += chars
    # deduplicated by utterance: all source overlaps removed
    out["all_sources"] = {"rows": len(overlap_all), "chars": chars_all, "rate_pct": 100.0 * len(overlap_all) / max(1, len(rows))}
    return out


def main() -> None:
    sources = {k: load_manifest(v) for k, v in SOURCES.items()}
    result = {
        "normalizer": "eval.normalize.normalize_nospace",
        "scope": "exact normalized transcript match; no training/decoding",
        "source_sizes": {k: len(v) for k, v in sources.items()},
        "test": audit(ROOT / "reports/provenance/W2B/testpred_b3_v2_s42.json", "test", sources),
        "dev": audit(ROOT / "reports/provenance/W2B/devpred_b3_v2_s42.json", "dev", sources),
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
