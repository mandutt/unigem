#!/usr/bin/env python3
"""Analyze existing C5 F5.0 pilot300 val161 predictions without regeneration.

Inputs are fixed artifacts:
  - reports/provenance/C5_a1/pilot300_val161/predictions.jsonl
  - data/external/f5_pairs_v3_clean.jsonl

Outputs:
  - reports/provenance/C5_f5_0/val161_analysis.json
  - reports/provenance/C5_f5_0/val161_per_doc.jsonl
  - reports/provenance/C5_f5_0/val161_review_strata.json

No model load, no generation, no training. Test 163 is not read.
"""
from __future__ import annotations

import hashlib
import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRED = ROOT / "reports/provenance/C5_a1/pilot300_val161/predictions.jsonl"
METRICS = ROOT / "reports/provenance/C5_a1/pilot300_val161/metrics.json"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
OUT = ROOT / "reports/provenance/C5_f5_0"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def ngrams(text: str, n: int) -> set[str]:
    text = norm(text)
    if len(text) < n:
        return set()
    return {text[i : i + n] for i in range(len(text) - n + 1)}


def ratio(num: float, den: float) -> float:
    return float(num) / float(den) if den else 0.0


def quantile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    if len(xs) == 1:
        return float(xs[0])
    pos = (len(xs) - 1) * p
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return float(xs[lo] * (1 - frac) + xs[hi] * frac)


def dist(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "p10": quantile(values, 0.10),
        "p25": quantile(values, 0.25),
        "p75": quantile(values, 0.75),
        "p90": quantile(values, 0.90),
        "min": min(values),
        "max": max(values),
    }


def corr(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or not xs:
        return 0.0
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return float(num / (dx * dy)) if dx and dy else 0.0


def main() -> int:
    preds = read_jsonl(PRED)
    data = {str(r["id"]): r for r in read_jsonl(DATA)}
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    if len(preds) != 161:
        raise SystemExit(f"expected 161 predictions, got {len(preds)}")

    docs = []
    for row in preds:
        rid = str(row["id"])
        if rid not in data:
            raise SystemExit(f"missing source record: {rid}")
        src = norm(data[rid]["passage"])
        target = norm(row["target"])
        pred = norm(row["pred"])

        p8, s8, t8 = ngrams(pred, 8), ngrams(src, 8), ngrams(target, 8)
        p4, s4, t4 = ngrams(pred, 4), ngrams(src, 4), ngrams(target, 4)
        copy8 = ratio(len(p8 & s8), len(p8))
        target_copy8 = ratio(len(t8 & s8), len(t8))
        pred_novel4 = 1.0 - ratio(len(p4 & s4), len(p4))
        target_novel4 = 1.0 - ratio(len(t4 & s4), len(t4))
        pred_target_copy8 = ratio(len(p8 & t8), len(p8))

        gen_len = int(row.get("gen_len") or len(pred))
        target_len = len(target)
        source_len = len(src)
        flags = []
        if not row.get("nonempty", bool(pred)):
            flags.append("empty")
        if not row.get("ended_eos", False):
            flags.append("no_eos")
        if float(row.get("char_f1", 0.0)) < 0.55:
            flags.append("low_char_f1")
        if copy8 >= 0.80:
            flags.append("high_copy8")
        if float(row.get("repeated_4gram_rate", 0.0)) >= 0.10:
            flags.append("high_repetition")
        if int(row.get("new_slot_count", 0)) > 0 or not row.get("grounded", False):
            flags.append("slot_grounding")
        if float(row.get("slot_preservation", 1.0)) < 0.20:
            flags.append("low_slot_preservation")
        if target_len and gen_len > 1.5 * target_len:
            flags.append("long_vs_target")
        if target_len and gen_len < 0.5 * target_len:
            flags.append("short_vs_target")

        docs.append(
            {
                "id": rid,
                "char_f1": float(row["char_f1"]),
                "gen_len": gen_len,
                "target_len": target_len,
                "source_len": source_len,
                "pred_compression": ratio(len(pred), source_len),
                "target_compression": ratio(target_len, source_len),
                "pred_copy8": copy8,
                "target_copy8": target_copy8,
                "pred_novel4": pred_novel4,
                "target_novel4": target_novel4,
                "pred_target_copy8": pred_target_copy8,
                "repeated_4gram_rate": float(row.get("repeated_4gram_rate", 0.0)),
                "distinct_2": float(row.get("distinct_2", 0.0)),
                "slot_preservation": float(row.get("slot_preservation", 0.0)),
                "new_slot_count": int(row.get("new_slot_count", 0)),
                "summary_slot_count": int(row.get("summary_slot_count", 0)),
                "grounded": bool(row.get("grounded", False)),
                "ended_eos": bool(row.get("ended_eos", False)),
                "flags": flags,
                "pred": pred,
                "target": target,
            }
        )

    by_id = {d["id"]: d for d in docs}

    def select(key: str, reverse: bool, n: int, pool: list[dict] | None = None) -> list[str]:
        xs = pool if pool is not None else docs
        return [d["id"] for d in sorted(xs, key=lambda d: d[key], reverse=reverse)[:n]]

    low_f1 = select("char_f1", False, 20)
    high_copy = select("pred_copy8", True, 20)
    low_slot = select("slot_preservation", False, 20)
    high_rep = select("repeated_4gram_rate", True, 20)
    # Deterministic "middle" sample: evenly spaced by char_f1 rank.
    ranked = [d["id"] for d in sorted(docs, key=lambda d: (d["char_f1"], d["id"]))]
    middle = ranked[:: max(1, len(ranked) // 20)][:20]

    strata = {
        "lowest_char_f1": low_f1,
        "highest_copy8": high_copy,
        "lowest_slot_preservation": low_slot,
        "highest_repetition": high_rep,
        "middle_char_f1": middle,
    }

    flag_counts: dict[str, int] = {}
    for d in docs:
        for f in d["flags"]:
            flag_counts[f] = flag_counts.get(f, 0) + 1

    summary = {
        "n": len(docs),
        "char_f1": dist([d["char_f1"] for d in docs]),
        "gen_len": dist([float(d["gen_len"]) for d in docs]),
        "target_len": dist([float(d["target_len"]) for d in docs]),
        "pred_compression": dist([d["pred_compression"] for d in docs]),
        "target_compression": dist([d["target_compression"] for d in docs]),
        "pred_copy8": dist([d["pred_copy8"] for d in docs]),
        "target_copy8": dist([d["target_copy8"] for d in docs]),
        "pred_novel4": dist([d["pred_novel4"] for d in docs]),
        "target_novel4": dist([d["target_novel4"] for d in docs]),
        "pred_target_copy8": dist([d["pred_target_copy8"] for d in docs]),
        "slot_preservation": dist([d["slot_preservation"] for d in docs]),
        "repeated4": dist([d["repeated_4gram_rate"] for d in docs]),
        "distinct2": dist([d["distinct_2"] for d in docs]),
        "grounded_rate": ratio(sum(d["grounded"] for d in docs), len(docs)),
        "eos_rate": ratio(sum(d["ended_eos"] for d in docs), len(docs)),
        "new_slot_docs": sum(d["new_slot_count"] > 0 for d in docs),
        "flag_counts": flag_counts,
        "pred_copy8_minus_target": statistics.fmean(d["pred_copy8"] - d["target_copy8"] for d in docs),
        "pred_novel4_minus_target": statistics.fmean(d["pred_novel4"] - d["target_novel4"] for d in docs),
        "pred_compression_minus_target": statistics.fmean(d["pred_compression"] - d["target_compression"] for d in docs),
        "correlations": {
            "char_f1_vs_pred_copy8": corr([d["char_f1"] for d in docs], [d["pred_copy8"] for d in docs]),
            "char_f1_vs_slot_preservation": corr([d["char_f1"] for d in docs], [d["slot_preservation"] for d in docs]),
            "pred_copy8_vs_pred_novel4": corr([d["pred_copy8"] for d in docs], [d["pred_novel4"] for d in docs]),
        },
        "copy_groups": {
            "high_copy8_ge_0_80": {
                "n": sum(d["pred_copy8"] >= 0.80 for d in docs),
                "char_f1_mean": statistics.fmean([d["char_f1"] for d in docs if d["pred_copy8"] >= 0.80] or [0.0]),
                "slot_preservation_mean": statistics.fmean([d["slot_preservation"] for d in docs if d["pred_copy8"] >= 0.80] or [0.0]),
            },
            "lower_copy8_lt_0_80": {
                "n": sum(d["pred_copy8"] < 0.80 for d in docs),
                "char_f1_mean": statistics.fmean([d["char_f1"] for d in docs if d["pred_copy8"] < 0.80] or [0.0]),
                "slot_preservation_mean": statistics.fmean([d["slot_preservation"] for d in docs if d["pred_copy8"] < 0.80] or [0.0]),
            },
        },
    }

    # Keep compact per-doc artifact without source text (source is in DATA).
    per_doc = [{k: v for k, v in d.items() if k not in {"pred", "target"}} for d in docs]
    payload = {
        "status": "ANALYSIS_ONLY_NO_REGENERATION",
        "inputs": {
            "predictions": {"path": str(PRED.relative_to(ROOT)), "sha256": sha256(PRED)},
            "metrics": {"path": str(METRICS.relative_to(ROOT)), "sha256": sha256(METRICS)},
            "data": {"path": str(DATA.relative_to(ROOT)), "sha256": sha256(DATA)},
        },
        "source_metrics": metrics,
        "summary": summary,
        "strata": strata,
        "examples": {
            "lowest_char_f1": [{"id": i, **{k: by_id[i][k] for k in ("char_f1", "pred_copy8", "pred_novel4", "slot_preservation")}} for i in low_f1[:5]],
            "highest_copy8": [{"id": i, **{k: by_id[i][k] for k in ("char_f1", "pred_copy8", "pred_novel4", "slot_preservation")}} for i in high_copy[:5]],
        },
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "val161_analysis.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (OUT / "val161_per_doc.jsonl").open("w", encoding="utf-8") as f:
        for d in per_doc:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    (OUT / "val161_review_strata.json").write_text(
        json.dumps(strata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    print(json.dumps({"strata_sizes": {k: len(v) for k, v in strata.items()}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
