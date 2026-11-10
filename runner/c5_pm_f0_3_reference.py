"""C5 F0.3 — E00/E10 reference decomposition.

Descriptive only: no PASS_POSITIVE or ROUTE_STOP.  E11 from F0.2 is used as an
external reference and is never retrained here.
"""

from __future__ import annotations

import argparse
import gc
import json
import multiprocessing as mp
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_mt5_lora_b0 import donors_for  # noqa: E402
from runner.c5_mt5_layer_probe import load_layer_cache  # noqa: E402
from runner.c5_pm_f0 import CACHE, K_M, build_cell, read_json, sha256_bytes  # noqa: E402
from runner.c5_pm_f0_mechanics import f0_memory, trainable_hash  # noqa: E402
from runner.c5_pm_f0_registered import eval_signal  # noqa: E402
from runner.c5_pm_phase6 import labels_and_copy, set_arm_training, train_forward_loss  # noqa: E402
from runner.c5_pm_stats import bootstrap_paired_v2  # noqa: E402

CELLS = ("E00", "E10")
SEEDS = (20261108, 20261109, 20261110)
UPDATES = {"E00": 0, "E10": 400}
ADAPTER_LR = 1e-3
FIT_RATIO = 0.35
CAP_SECONDS = 3600
N_BOOT = 10000
BOOT_SEED = 20261109
OUT = ROOT / "reports/provenance/C5_f0_3"
UNITS = OUT / "units"
F02 = ROOT / "reports/provenance/C5_f0_2"
PLAN = ROOT / "docs/plan_c5_f0_3_reference_v0_1_2026-11-10.md"
FREEZE = ROOT / "docs/plan_c5_f0_3_reference_v0_1_FREEZE.json"


def step_seed(seed: int, step: int) -> int:
    return (int(seed) ^ ((0x9E3779B9 * (step + 1)) & 0xFFFFFFFF)) & 0xFFFFFFFF


def adapter_optimizer(built: dict[str, Any]) -> torch.optim.Optimizer:
    params = [p for p in built["adapter"].parameters() if p.requires_grad]
    if not params:
        raise RuntimeError("E10 has no adapter parameters")
    return torch.optim.AdamW([{"params": params, "lr": ADAPTER_LR}], weight_decay=0.01)


def run_unit(cell: str, seed: int) -> dict[str, Any]:
    torch.set_num_threads(2)
    started = time.time()
    preflight = read_json(ROOT / "reports/provenance/C5_b0a/m_cohort_preflight.json")
    rows = {}
    for line in (ROOT / "data/external/f5_pairs_v3_clean.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line); rows[str(row["id"])] = row
    train_ids = list(preflight["train20_ids"])
    val_ids = list(preflight["val20_ids"])
    common = list(preflight["common_ids"])
    cache = load_layer_cache("train", CACHE); cache.update(load_layer_cache("val", CACHE))
    built = build_cell(cell, seed)
    built["arm"] = cell
    built["spec"]["memory_source"] = "eg2_layer19"
    built["spec"]["m_k"] = K_M
    labels, copies = labels_and_copy(built["tok"], rows, list(dict.fromkeys(train_ids + val_ids + common)))
    donors = donors_for(val_ids, cache, 5)
    before = trainable_hash(built)
    losses = []
    if UPDATES[cell]:
        opt = adapter_optimizer(built)
        set_arm_training(built, True)
        for step in range(UPDATES[cell]):
            torch.manual_seed(step_seed(seed, step))
            rid = train_ids[step % len(train_ids)]
            loss = train_forward_loss(built["model"], f0_memory(built, rid, cache), labels[rid])
            if not torch.isfinite(loss):
                raise RuntimeError(f"{cell} {seed}: non-finite at {step}")
            opt.zero_grad(set_to_none=True)
            loss.backward()
            params = [p for p in built["adapter"].parameters() if p.requires_grad]
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            losses.append(float(loss.detach()))
        set_arm_training(built, False)
    ratio = (losses[-1] / losses[0]) if losses else None
    fit = True if not losses else bool(ratio <= FIT_RATIO)
    final = eval_signal(built, val_ids, cache, labels, copies, donors)
    out = {
        "cell": cell, "seed": seed, "updates": UPDATES[cell],
        "adapter_lr": ADAPTER_LR if cell == "E10" else None,
        "loss_first": float(losses[0]) if losses else None,
        "loss_last": float(losses[-1]) if losses else None,
        "fit_ratio": float(ratio) if ratio is not None else None,
        "fit_pass": fit,
        "weight_change_ok": bool(before != trainable_hash(built)),
        "final": final, "elapsed_s": float(time.time() - started),
    }
    del built; gc.collect()
    return out


def _worker(cell: str, seed: int, q: Any) -> None:
    try:
        q.put(("ok", cell, seed, run_unit(cell, seed)))
    except BaseException as exc:
        q.put(("error", cell, seed, {"cell": cell, "seed": seed,
                                     "error": type(exc).__name__, "message": str(exc)[:400]}))


def _stats(units: dict[str, Any], common: list[str], cell: str, endpoint: str) -> dict[str, Any]:
    per_seed = {}
    for seed in SEEDS:
        u = units[f"{cell}_{seed}"]
        vals = [float(u["final"]["per_doc"][rid]["delta_shuffled_" + endpoint]) for rid in common]
        per_seed[seed] = vals
    doc_mean = [float(np.mean([per_seed[s][i] for s in SEEDS])) for i in range(len(common))]
    boot = bootstrap_paired_v2(doc_mean, n_boot=N_BOOT, seed=BOOT_SEED)
    seed_means = {str(s): float(np.mean(per_seed[s])) for s in SEEDS}
    pos = int(sum(v > 0 for v in seed_means.values()))
    return {"endpoint": endpoint, "mean": boot["mean"], "ci_lower": boot["ci_lower"],
            "ci_upper": boot["ci_upper"], "n": boot["n"], "n_boot": boot["n_boot"],
            "boot_seed": boot["seed"], "seed_means": seed_means,
            "positive_seeds": pos, "doc_mean": doc_mean}


def _paired(units_a: dict[str, Any], units_b: dict[str, Any], common: list[str], ep: str) -> dict[str, Any]:
    docs = []
    per_seed = {}
    for seed in SEEDS:
        vals = []
        for rid in common:
            a = units_a[f"{seed}"]["final"]["per_doc"][rid]["delta_shuffled_" + ep]
            b = units_b[f"{seed}"]["final"]["per_doc"][rid]["delta_shuffled_" + ep]
            vals.append(float(a - b))
        per_seed[str(seed)] = float(np.mean(vals))
        if seed == SEEDS[0]:
            docs = vals
    # doc mean across seeds
    doc_means = []
    for rid in common:
        a = np.mean([units_a[str(s)]["final"]["per_doc"][rid]["delta_shuffled_" + ep] for s in SEEDS])
        b = np.mean([units_b[str(s)]["final"]["per_doc"][rid]["delta_shuffled_" + ep] for s in SEEDS])
        doc_means.append(float(a - b))
    boot = bootstrap_paired_v2(doc_means, n_boot=N_BOOT, seed=BOOT_SEED)
    return {"endpoint": ep, "mean": boot["mean"], "ci_lower": boot["ci_lower"],
            "ci_upper": boot["ci_upper"], "n": boot["n"], "n_boot": boot["n_boot"],
            "boot_seed": boot["seed"], "seed_means": per_seed, "doc_mean": doc_means}


def run() -> dict[str, Any]:
    plan_hash = sha256_bytes(PLAN.read_bytes())
    if not FREEZE.exists():
        raise RuntimeError("F0.3 freeze missing")
    freeze = read_json(FREEZE)
    if freeze.get("plan_sha256") != plan_hash:
        raise RuntimeError("F0.3 plan hash mismatch")
    if freeze.get("status") != "owner_approved":
        raise RuntimeError("F0.3 not approved")
    preflight = read_json(ROOT / "reports/provenance/C5_b0a/m_cohort_preflight.json")
    common = list(preflight["common_ids"])
    started = time.time()
    UNITS.mkdir(parents=True, exist_ok=True)
    ctx = mp.get_context("spawn")
    results = {}; errors = []
    tasks = [(c, s) for c in CELLS for s in SEEDS]
    for off in range(0, len(tasks), 4):
        if time.time() - started >= CAP_SECONDS: break
        batch = tasks[off:off + 4]
        q = ctx.Queue()
        procs = [ctx.Process(target=_worker, args=(c, s, q)) for c, s in batch]
        for p in procs: p.start()
        got = 0
        while got < len(batch) and time.time() - started < CAP_SECONDS:
            try:
                kind, c, s, payload = q.get(timeout=10)
            except Exception:
                if all(not p.is_alive() for p in procs): break
                continue
            got += 1
            if kind == "ok":
                results[(c, s)] = payload
                (UNITS / f"{c}_{s}.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            else:
                errors.append(payload)
        for p in procs:
            p.join(timeout=5)
            if p.is_alive(): p.terminate()
        for c, s in batch:
            if (c, s) not in results and not any(e.get("cell") == c and e.get("seed") == s for e in errors):
                errors.append({"cell": c, "seed": s, "error": "MISSING_RESULT"})
    wall = time.time() - started
    units = {f"{c}_{s}": results[(c, s)] for c, s in results}
    e10_fit = len(units) == 6 and all(
        units[f"E10_{s}"]["fit_pass"] for s in SEEDS
    )
    if e10_fit:
        cells = {c: {e: _stats(units, common, c, e) for e in ("copy", "full")} for c in CELLS}
        d = {e: _paired({str(s): units[f"E10_{s}"] for s in SEEDS},
                        {str(s): units[f"E00_{s}"] for s in SEEDS}, common, e)
             for e in ("copy", "full")}
        ext = {}
        if (F02 / "labels.json").exists():
            ext_labels = read_json(F02 / "labels.json")
            ext["e11_reference"] = ext_labels
            if all((F02 / f"units/E11_{s}.json").exists() for s in SEEDS):
                e11_units = {str(s): read_json(F02 / f"units/E11_{s}.json") for s in SEEDS}
                ext["E11_E10"] = {
                    e: _paired(e11_units, {str(s): units[f"E10_{s}"] for s in SEEDS}, common, e)
                    for e in ("copy", "full")}
        labels = {
            "schema_version": "1",
            "status": "REFERENCE_DECOMPOSITION",
            "cells": cells,
            "E10_minus_E00": d,
            "external_E11": ext,
            "fit_gate": {"ratio": FIT_RATIO, "pass": bool(e10_fit)},
            "labels_computed": True,
            "not_a_result": False,
            "confirmatory": False,
            "population_inference": False,
        }
    else:
        labels = {"schema_version": "1", "status": "NOT_EVALUABLE_OPTIMIZATION",
                  "reason": "E10_fit_gate_failed", "labels_computed": False,
                  "not_a_result": True, "fit_gate": {"ratio": FIT_RATIO, "pass": False}}
    out = {
        "schema_version": "1", "experiment": "C5 F0.3 E00/E10 reference decomposition",
        "cells": list(CELLS), "seeds": list(SEEDS), "updates": UPDATES,
        "n_units": len(units), "n_errors": len(errors), "wall_s": wall, "cap_s": CAP_SECONDS,
        "fit_gate": {"ratio": FIT_RATIO, "pass": bool(e10_fit)},
        "labels": labels, "partial": bool(errors) or len(units) != 6,
        "error": "OTHER_REDACTED" if errors else None,
        "no_signal_values_in_logs": True,
        "labels_computed": labels["labels_computed"], "not_a_result": labels["not_a_result"],
        "test_split_used": False, "p1_used": False,
        "provenance": {"code_commit": freeze.get("code_commit"),
                       "command": "python runner/c5_pm_f0_3_reference.py --run",
                       "input_sha256": sha256_bytes(json.dumps(common, sort_keys=True).encode()),
                       "clean_tree": subprocess.check_output(["git", "status", "--porcelain"], cwd=str(ROOT), text=True).strip() == ""},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    (OUT / "labels.json").write_text(json.dumps(labels, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if not args.run: raise SystemExit("pass --run")
    out = run()
    print(json.dumps({"status": out["labels"]["status"], "fit_pass": out["fit_gate"]["pass"],
                      "n_units": out["n_units"], "n_errors": out["n_errors"],
                      "wall_s": out["wall_s"]}, ensure_ascii=False))
    return 0 if not out["partial"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
