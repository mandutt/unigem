#!/usr/bin/env python3
"""Read-only audit of candidate verifier-v2 rules for C5 A1.

This does NOT modify eval/slot_verify.py or any production verifier.
It re-scores saved val predictions with a candidate equivalence matcher and
counts rule collisions across the P0 clean corpus.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval.slot_verify import Slot, extract_slots, verify_summary  # noqa: E402

CLEAN = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
FULL = ROOT / "data/external/f5_pairs_v3.jsonl"
RUN = ROOT / "reports/provenance/C5_a1/full_2ep"
PILOT = ROOT / "reports/provenance/C5_a1/pilot300_val161/predictions.jsonl"

URL_WRAP = re.compile(
    r"(https?://[^\s<>\"']*?[./_-])[ \t]*\n[ \t]*"
    r"([a-z0-9][A-Za-z0-9.\-/_%?=&#]*)"
)
TIME_RE = re.compile(r"^(?:(오전|오후))?(\d{1,2})시(?:(\d{1,2})분)?$")
NUM_RE = re.compile(r"^(\d[\d,]*(?:\.\d+)?)(.*)$")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def repair_url_wraps(text: str) -> tuple[str, list[str]]:
    repairs: list[str] = []

    def repl(m: re.Match[str]) -> str:
        joined = m.group(1) + m.group(2)
        repairs.append(joined)
        return joined

    return URL_WRAP.sub(repl, text), repairs


def time_parts(slot: Slot) -> tuple[str | None, str, str] | None:
    s = re.sub(r"\s+", "", slot.value)
    m = TIME_RE.fullmatch(s)
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3) or "0"


def numeric_parts(slot: Slot) -> tuple[str, str] | None:
    if slot.kind != "number":
        return None
    s = slot.value.replace(",", "").strip()
    m = NUM_RE.fullmatch(s)
    if not m:
        return None
    return m.group(1), m.group(2).strip()


def source_numeric_map(slots: list[Slot]) -> dict[str, list[Slot]]:
    out: dict[str, list[Slot]] = defaultdict(list)
    for s in slots:
        p = numeric_parts(s)
        if p:
            out[p[0]].append(s)
    return out


def match_v2(source: str, summary: str, counter_alias: bool = False) -> dict[str, Any]:
    src_text, url_repairs = repair_url_wraps(source)
    sm_text, _sm_repairs = repair_url_wraps(summary)
    src_slots = list(dict.fromkeys(extract_slots(src_text)))
    sm_slots = list(dict.fromkeys(extract_slots(sm_text)))
    src_map = {s.canonical: s for s in src_slots}
    sm_map = {s.canonical: s for s in sm_slots}
    matched_src: set[str] = set()
    matched_sm: set[str] = set()

    # Exact canonical matches.
    for c in src_map.keys() & sm_map.keys():
        matched_src.add(c)
        matched_sm.add(c)

    # URL and time equivalence (one-directional where relevant).
    for sc, s in src_map.items():
        if sc in matched_src:
            continue
        if s.kind == "url":
            for mc, m in sm_map.items():
                if mc not in matched_sm and m.kind == "url" and mc == sc:
                    matched_src.add(sc)
                    matched_sm.add(mc)
                    break
        elif s.kind == "time":
            sp = time_parts(s)
            if not sp or sp[0] is None:
                continue
            qual, hh, mm = sp
            same = [x for x in src_map.values() if x.kind == "time" and time_parts(x)
                    and time_parts(x)[1:] == (hh, mm)]
            if len({time_parts(x)[0] for x in same if time_parts(x)}) > 1:
                continue  # qualifier collision: require human adjudication
            for mc, m in sm_map.items():
                if mc in matched_sm or m.kind != "time":
                    continue
                mp = time_parts(m)
                if mp and mp[0] is None and mp[1:] == (hh, mm):
                    matched_src.add(sc)
                    matched_sm.add(mc)
                    break

    # Bare-number / unit equivalence, with a uniqueness guard by default.
    snum = source_numeric_map(src_slots)
    for sc, s in src_map.items():
        if sc in matched_src:
            continue
        sp = numeric_parts(s)
        if not sp:
            continue
        value, unit = sp
        if not unit:
            continue
        if len(snum[value]) != 1 and not counter_alias:
            continue
        for mc, m in sm_map.items():
            if mc in matched_sm:
                continue
            mp = numeric_parts(m)
            if not mp or mp[1]:
                continue
            if mp[0] != value:
                continue
            if counter_alias:
                after = summary[m.end:m.end + 24]
                if "확진자" not in after:
                    continue
            matched_src.add(sc)
            matched_sm.add(mc)
            break

    missing = [c for c in src_map if c not in matched_src]
    new = [c for c in sm_map if c not in matched_sm]
    return {
        "grounded": not new,
        "new": new,
        "missing": missing,
        "source_count": len(src_slots),
        "summary_count": len(sm_slots),
        "url_repairs": url_repairs,
    }


def main() -> int:
    clean = load_jsonl(CLEAN)
    full = load_jsonl(FULL)
    clean_ids = {str(r["id"]) for r in clean}
    excluded = [r for r in full if str(r["id"]) not in clean_ids]
    data = {str(r["id"]): r for r in clean}

    # Corpus-level collision counts.
    url_docs = 0
    url_occurrences = 0
    qualifier_collision_docs = 0
    numeric_collision_docs = 0
    for r in clean:
        text = str(r["passage"])
        repaired, reps = repair_url_wraps(text)
        if reps:
            url_docs += 1
            url_occurrences += len(reps)
        slots = extract_slots(repaired)
        times = [time_parts(s) for s in slots if s.kind == "time"]
        by_hm: dict[tuple[str, str], set[str | None]] = defaultdict(set)
        for t in times:
            if t:
                by_hm[(t[1], t[2])].add(t[0])
        if any(len(v) > 1 for v in by_hm.values()):
            qualifier_collision_docs += 1
        nums = source_numeric_map(slots)
        if any(len({numeric_parts(s)[1] for s in v if numeric_parts(s)}) > 1 for v in nums.values()):
            numeric_collision_docs += 1

    # Target-side audit: excluded pairs were removed by the v1 clean filter,
    # so every v2 accept here is a candidate false accept and needs human review.
    target_audit: dict[str, Any] = {}
    for label, rows in (("excluded", excluded), ("clean", clean)):
        flips = []
        v1_grounded = 0
        v2_grounded = 0
        for r in rows:
            source = str(r["passage"])
            target = str(r["summary"])
            v1 = verify_summary(source, target)
            v2 = match_v2(source, target, counter_alias=False)
            a = not v1.new
            b = v2["grounded"]
            v1_grounded += int(a)
            v2_grounded += int(b)
            if a != b:
                flips.append({
                    "id": str(r["id"]),
                    "v1_grounded": a,
                    "v2_grounded": b,
                    "v1_new": list(v1.new),
                    "v2_new": v2["new"],
                })
        target_audit[label] = {
            "n": len(rows),
            "v1_grounded": v1_grounded,
            "v2_grounded": v2_grounded,
            "flips": flips,
        }

    # V1/V2 metrics for available predictions.
    checkpoints: dict[str, Any] = {}
    pred_files = {
        "pilot300": PILOT,
        "0647": RUN / "eval_step_0647/eval.jsonl",
        "1293": RUN / "eval_step_1293/eval.jsonl",
        "1940": RUN / "eval_step_1940/eval.jsonl",
        "2586": RUN / "eval_step_2586/eval.jsonl",
    }
    for name, path in pred_files.items():
        rows = load_jsonl(path)
        # normalize pilot predictions schema
        v1 = {}
        v2 = {}
        v2_alias = {}
        for row in rows:
            rid = str(row["id"])
            source = str(data[rid]["passage"])
            pred = str(row.get("pred") or row.get("prediction") or "")
            v1[rid] = verify_summary(source, pred)
            v2[rid] = match_v2(source, pred, counter_alias=False)
            v2_alias[rid] = match_v2(source, pred, counter_alias=True)
        # explicit fields (avoid boolean indexing ambiguity)
        checkpoints[name] = {
            "n": len(rows),
            "v1_grounded": sum(1 for x in v1.values() if not x.new),
            "v2_grounded": sum(1 for x in v2.values() if x["grounded"]),
            "v2_alias_grounded": sum(1 for x in v2_alias.values() if x["grounded"]),
            "v1_fail_ids": [rid for rid, x in v1.items() if x.new],
            "v2_fail_ids": [rid for rid, x in v2.items() if not x["grounded"]],
            "v2_alias_fail_ids": [rid for rid, x in v2_alias.items() if not x["grounded"]],
            "url_repair_docs": sorted({rid for rid, x in v2.items() if x["url_repairs"]}),
            "v2_new_counts": {rid: len(x["new"]) for rid, x in v2.items() if x["new"]},
        }

    out = {
        "scope": "P0 clean, val predictions only; no test, no production verifier changes",
        "clean_n": len(clean),
        "excluded_n": len(excluded),
        "corpus": {
            "url_wrap_docs": url_docs,
            "url_wrap_occurrences": url_occurrences,
            "qualifier_collision_docs": qualifier_collision_docs,
            "numeric_unit_collision_docs": numeric_collision_docs,
        },
        "target_audit": target_audit,
        "checkpoints": checkpoints,
    }
    path = RUN / "verifier_v2_audit.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print("wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
