"""Aggregate the six B0-A arm/seed JSON results.

Expected files:
  reports/provenance/C5_b0a/s{20261108,20261109,20261110}_{frozen,lora}.json

The aggregate uses document-level paired differences, seed-level means, and a
document bootstrap. It is report-only and does not train or modify models.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "reports/provenance/C5_b0a"
OUT = SRC / "aggregate.json"
REPORT = ROOT / "reports/C5_B0A_2026-11-09.md"
SEEDS = (20261108, 20261109, 20261110)
ARMS = ("frozen", "lora")


def load_unit(seed: int, arm: str) -> dict[str, Any]:
    p = SRC / f"s{seed}_{arm}.json"
    if not p.exists():
        raise FileNotFoundError(p)
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, list):
        data = data[0]
    return data


def mean(xs: list[float]) -> float:
    return float(np.mean(xs)) if xs else float("nan")


def bootstrap(values: list[float], n_boot: int = 1000, seed: int = 20261108) -> dict[str, Any]:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return {"mean": None, "ci_lower": None, "ci_upper": None, "n": 0}
    rng = np.random.default_rng(seed)
    means = np.asarray([rng.choice(arr, size=arr.size, replace=True).mean() for _ in range(n_boot)])
    return {
        "mean": float(arr.mean()),
        "ci_lower": float(np.percentile(means, 2.5)),
        "ci_upper": float(np.percentile(means, 97.5)),
        "n": int(arr.size),
        "n_boot": n_boot,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--report", type=Path, default=REPORT)
    args = ap.parse_args()

    units = {(seed, arm): load_unit(seed, arm) for seed in SEEDS for arm in ARMS}
    docs = sorted(set.intersection(*(set(u["per_doc"]) for u in units.values())))
    if not docs:
        raise RuntimeError("no common documents across all units")

    arm_doc: dict[str, dict[str, float]] = {}
    seed_info: dict[str, dict[str, Any]] = {}
    for arm in ARMS:
        seed_means = {}
        for seed in SEEDS:
            u = units[(seed, arm)]
            vals = [u["per_doc"][d]["delta_shuffled_copy"] for d in docs]
            seed_means[str(seed)] = mean(vals)
            arm_doc.setdefault(arm, {})
        for d in docs:
            arm_doc[arm][d] = mean([
                units[(seed, arm)]["per_doc"][d]["delta_shuffled_copy"] for seed in SEEDS
            ])
        seed_info[arm] = {
            "seed_means": seed_means,
            "positive_seeds": sum(v > 0 for v in seed_means.values()),
            "mean_doc_delta": mean([arm_doc[arm][d] for d in docs]),
            "doc_bootstrap": bootstrap([arm_doc[arm][d] for d in docs]),
        }

    paired = [arm_doc["lora"][d] - arm_doc["frozen"][d] for d in docs]
    lora_minus_frozen = bootstrap(paired)
    lora = seed_info["lora"]
    frozen = seed_info["frozen"]

    # Copy guard and generation summary (not a gate).
    def generation_summary(arm: str) -> dict[str, Any]:
        rows = [g for seed in SEEDS for g in units[(seed, arm)].get("generation", [])]
        nonempty = sum(bool(str(g.get("text", "")).strip()) for g in rows)
        eos = sum(bool(g.get("eos")) for g in rows)
        return {"n": len(rows), "nonempty": nonempty, "eos": eos}

    decision = "INCONCLUSIVE"
    lora_boot = lora["doc_bootstrap"]
    if (
        lora["mean_doc_delta"] >= 0.05
        and lora_boot["ci_lower"] is not None
        and lora_boot["ci_lower"] > 0
        and lora_minus_frozen["ci_lower"] is not None
        and lora_minus_frozen["ci_lower"] > 0
        and lora["positive_seeds"] >= 2
    ):
        decision = "POSITIVE_SIGNAL"
    elif (
        lora["mean_doc_delta"] <= 0
        and lora_boot["ci_upper"] is not None
        and lora_boot["ci_upper"] < 0.05
    ):
        decision = "NO_SIGNAL"

    payload = {
        "experiment": "c5_b0a_aggregate",
        "seeds": list(SEEDS),
        "arms": list(ARMS),
        "n_docs": len(docs),
        "docs": docs,
        "arm_doc": arm_doc,
        "seed_info": seed_info,
        "lora_minus_frozen": lora_minus_frozen,
        "copy_guard": {
            "frozen_failed": units[(SEEDS[0], "frozen")].get("copy_guard_failed"),
            "lora_failed": units[(SEEDS[0], "lora")].get("copy_guard_failed"),
        },
        "generation": {arm: generation_summary(arm) for arm in ARMS},
        "decision": decision,
        "test_split_used": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# C5 B0-A 결과",
        "",
        "- seeds: 20261108 / 09 / 10",
        "- train 20 / val 20 (val[5:25]), 5 donors, 100 updates",
        "- test 163 미사용",
        "",
        "## 판정",
        "",
        f"**{decision}**",
        "",
        "| arm | mean Δshuffled_copy | doc bootstrap 95% CI | positive seeds |",
        "|---|---:|---|---:|",
    ]
    for arm in ARMS:
        s = seed_info[arm]
        b = s["doc_bootstrap"]
        lines.append(f"| {arm} | {s['mean_doc_delta']:.6f} | [{b['ci_lower']:.6f}, {b['ci_upper']:.6f}] | {s['positive_seeds']}/3 |")
    lines += [
        "",
        f"- L − F paired: **{lora_minus_frozen['mean']:.6f}** "
        f"CI [{lora_minus_frozen['ci_lower']:.6f}, {lora_minus_frozen['ci_upper']:.6f}]",
        f"- copy guard: frozen={payload['copy_guard']['frozen_failed']}, lora={payload['copy_guard']['lora_failed']}",
        f"- generation: frozen {payload['generation']['frozen']}, lora {payload['generation']['lora']}",
        "",
        "## 해석 제한",
        "",
        "- B0-A는 20/20 screening이다. 결과를 B1/B2/Stage C 자동 승인으로 확장하지 않는다.",
        "- NO_SIGNAL은 bridge 전체의 영구 STOP이 아니다.",
        "- test 163은 사용하지 않았다.",
    ]
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "frozen": frozen, "lora": lora, "lora_minus_frozen": lora_minus_frozen}, ensure_ascii=False, indent=2))
    print(f"wrote {args.out}")
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
