#!/usr/bin/env python3
"""Analyze the 20-doc x 3-system F5.0 human review export."""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_f5_0_analyze import quantile  # noqa: E402

KEY = ROOT / "reports/provenance/C5_f5_0/human_review_key.json"
OUT = ROOT / "reports/provenance/C5_f5_0"
LABELS = ["pilot300", "full_1940", "full_2586"]
N_BOOT = 10000
BOOT_SEED = 20261110


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def mean(xs: list[float]) -> float:
    return statistics.fmean(xs) if xs else 0.0


def paired_diff(a: list[float], b: list[float]) -> dict:
    diffs = [x - y for x, y in zip(a, b)]
    rng = random.Random(BOOT_SEED)
    boots = []
    n = len(diffs)
    for _ in range(N_BOOT):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        boots.append(mean(sample))
    return {
        "n": n,
        "mean": mean(diffs),
        "ci95": [quantile(boots, 0.025), quantile(boots, 0.975)],
        "wins": sum(d > 0 for d in diffs),
        "ties": sum(d == 0 for d in diffs),
        "losses": sum(d < 0 for d in diffs),
        "per_doc": diffs,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ratings", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=OUT / "human_analysis.json")
    args = ap.parse_args()

    ratings = read_json(args.ratings)
    key = read_json(KEY)
    key_items = {x["doc_key"]: x for x in key["items"]}
    docs = sorted(key_items)

    rows = ratings.get("ratings", [])
    if len(rows) != len(docs) * 3:
        raise SystemExit(f"expected {len(docs) * 3} ratings, got {len(rows)}")
    seen = set()
    by_system: dict[str, list[dict]] = {s: [] for s in LABELS}
    for r in rows:
        dk, code = r["doc_key"], r["system_code"]
        if dk not in key_items:
            raise SystemExit(f"unknown doc_key: {dk}")
        if code not in key_items[dk]["mapping"]:
            raise SystemExit(f"unknown code {code} for {dk}")
        if (dk, code) in seen:
            raise SystemExit(f"duplicate rating: {dk}/{code}")
        seen.add((dk, code))
        if r.get("overall") not in (1, 2, 3):
            raise SystemExit(f"missing/invalid overall: {dk}/{code}")
        sysname = key_items[dk]["mapping"][code]
        if sysname not in by_system:
            raise SystemExit(f"unknown system: {sysname}")
        by_system[sysname].append(r)

    for s in LABELS:
        if len(by_system[s]) != len(docs):
            raise SystemExit(f"{s}: expected {len(docs)} ratings, got {len(by_system[s])}")

    order = {dk: i for i, dk in enumerate(docs)}
    for s in LABELS:
        by_system[s].sort(key=lambda r: order[r["doc_key"]])

    per_system = {}
    for s in LABELS:
        rs = by_system[s]
        flags = {}
        for r in rs:
            for f in r.get("flags", []):
                flags[f] = flags.get(f, 0) + 1
        per_system[s] = {
            "n": len(rs),
            "overall": mean([r["overall"] for r in rs]),
            "abstractness": mean([r["abstractness"] for r in rs]),
            "factual": mean([r["factual"] for r in rs]),
            "flags": flags,
            "flag_rates": {k: v / len(rs) for k, v in flags.items()},
        }

    def series(s: str, field: str) -> list[float]:
        return [float(r[field]) for r in by_system[s]]

    paired = {
        "full_1940_minus_pilot300": {f: paired_diff(series("full_1940", f), series("pilot300", f)) for f in ("overall", "abstractness", "factual")},
        "full_1940_minus_full_2586": {f: paired_diff(series("full_1940", f), series("full_2586", f)) for f in ("overall", "abstractness", "factual")},
        "pilot300_minus_full_2586": {f: paired_diff(series("pilot300", f), series("full_2586", f)) for f in ("overall", "abstractness", "factual")},
    }

    h, p, f = per_system["full_1940"], per_system["pilot300"], per_system["full_2586"]
    hp = paired["full_1940_minus_pilot300"]["overall"]
    hf = paired["full_1940_minus_full_2586"]["overall"]
    supports_1940 = (
        hp["mean"] >= 0.5
        and hf["mean"] >= 0.5
        and h["factual"] >= p["factual"] - 0.3
        and (hp["wins"] + hp["ties"]) >= 12
    )
    supports_pilot = (
        paired["full_1940_minus_pilot300"]["overall"]["mean"] <= -0.5
        and paired["pilot300_minus_full_2586"]["overall"]["mean"] >= 0.5
    )
    decision = "SUPPORTS_1940" if supports_1940 else ("SUPPORTS_PILOT300" if supports_pilot else "INCONCLUSIVE")

    payload = {
        "status": "SINGLE_RATER_EXPLORATORY",
        "rater": ratings.get("rater"),
        "n_docs": len(docs),
        "n_ratings": len(rows),
        "per_system": per_system,
        "paired": paired,
        "decision_rule": {
            "supports_1940": supports_1940,
            "supports_pilot300": supports_pilot,
        },
        "decision": decision,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "per_system": per_system, "paired_overall": {k: v["overall"] for k, v in paired.items()}}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
