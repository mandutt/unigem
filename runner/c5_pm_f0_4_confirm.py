"""C5 F0.4 — fresh-seed directional E11-E01 benefit confirmation."""

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

CELLS = ("E01", "E11")
SEEDS = (20261112, 20261113, 20261114)
UPDATES = 400
LORA_LR = 3e-4
ADAPTER_LR = 1e-3
FIT_RATIO = 0.35
CAP_SECONDS = 3600
N_BOOT = 10000
BOOT_SEED = 20261109
OUT = ROOT / "reports/provenance/C5_f0_4"
UNITS = OUT / "units"
PLAN = ROOT / "docs/plan_c5_f0_4_confirm_v0_1_2026-11-10.md"
FREEZE = ROOT / "docs/plan_c5_f0_4_confirm_v0_1_FREEZE.json"


def step_seed(seed: int, step: int) -> int:
    return (int(seed) ^ ((0x9E3779B9 * (step + 1)) & 0xFFFFFFFF)) & 0xFFFFFFFF


def optimizer_for(built: dict[str, Any]) -> torch.optim.Optimizer:
    groups = []
    if built["adapter"] is not None:
        groups.append({"params": [p for p in built["adapter"].parameters() if p.requires_grad],
                       "lr": ADAPTER_LR})
    groups.append({"params": [p for n, p in built["model"].named_parameters()
                              if ".lora_" in n and p.requires_grad], "lr": LORA_LR})
    return torch.optim.AdamW(groups, weight_decay=0.01)


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
    opt = optimizer_for(built)
    set_arm_training(built, True)
    losses = []
    for step in range(UPDATES):
        torch.manual_seed(step_seed(seed, step))
        rid = train_ids[step % len(train_ids)]
        loss = train_forward_loss(built["model"], f0_memory(built, rid, cache), labels[rid])
        if not torch.isfinite(loss):
            raise RuntimeError(f"{cell} {seed}: non-finite at {step}")
        opt.zero_grad(set_to_none=True)
        loss.backward()
        params = [p for p in built["model"].parameters() if p.requires_grad]
        if built["adapter"] is not None:
            params += [p for p in built["adapter"].parameters() if p.requires_grad]
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        losses.append(float(loss.detach()))
    set_arm_training(built, False)
    ratio = losses[-1] / losses[0]
    final = eval_signal(built, val_ids, cache, labels, copies, donors)
    out = {"cell": cell, "seed": seed, "updates": UPDATES,
           "lora_lr": LORA_LR, "adapter_lr": ADAPTER_LR if cell == "E11" else None,
           "loss_first": float(losses[0]), "loss_last": float(losses[-1]),
           "fit_ratio": float(ratio), "fit_pass": bool(ratio <= FIT_RATIO),
           "weight_change_ok": bool(before != trainable_hash(built)),
           "final": final, "elapsed_s": float(time.time() - started)}
    del built; gc.collect()
    return out


def _worker(cell: str, seed: int, q: Any) -> None:
    try:
        q.put(("ok", cell, seed, run_unit(cell, seed)))
    except BaseException as exc:
        q.put(("error", cell, seed, {"cell": cell, "seed": seed,
                                     "error": type(exc).__name__, "message": str(exc)[:400]}))


def _cell_stats(units: dict[str, Any], common: list[str], cell: str, ep: str) -> dict[str, Any]:
    per_seed = {}
    for seed in SEEDS:
        u = units[f"{cell}_{seed}"]
        per_seed[seed] = [float(u["final"]["per_doc"][rid]["delta_shuffled_" + ep]) for rid in common]
    doc_mean = [float(np.mean([per_seed[s][i] for s in SEEDS])) for i in range(len(common))]
    boot = bootstrap_paired_v2(doc_mean, n_boot=N_BOOT, seed=BOOT_SEED)
    seed_means = {str(s): float(np.mean(per_seed[s])) for s in SEEDS}
    pos = int(sum(v > 0 for v in seed_means.values()))
    signal = bool((boot["mean"] >= .05 and boot["ci_lower"] > 0 and pos >= 2)
                  if ep == "copy" else
                  (boot["mean"] > 0 and boot["ci_lower"] > 0 and pos >= 2))
    return {"endpoint": ep, "mean": boot["mean"], "ci_lower": boot["ci_lower"],
            "ci_upper": boot["ci_upper"], "n": boot["n"], "n_boot": boot["n_boot"],
            "boot_seed": boot["seed"], "seed_means": seed_means,
            "positive_seeds": pos, "signal": signal, "doc_mean": doc_mean}


def compute_labels(units: dict[str, Any], common: list[str]) -> dict[str, Any]:
    cells = {c: {e: _cell_stats(units, common, c, e) for e in ("copy", "full")} for c in CELLS}
    docs = []
    for rid in common:
        a = np.mean([units[f"E11_{s}"]["final"]["per_doc"][rid]["delta_shuffled_copy"] for s in SEEDS])
        b = np.mean([units[f"E01_{s}"]["final"]["per_doc"][rid]["delta_shuffled_copy"] for s in SEEDS])
        docs.append(float(a - b))
    boot = bootstrap_paired_v2(docs, n_boot=N_BOOT, seed=BOOT_SEED)
    d_seed = {}
    for s in SEEDS:
        vals = [float(units[f"E11_{s}"]["final"]["per_doc"][r]["delta_shuffled_copy"]
                      - units[f"E01_{s}"]["final"]["per_doc"][r]["delta_shuffled_copy"]) for r in common]
        d_seed[str(s)] = float(np.mean(vals))
    pos = int(sum(v > 0 for v in d_seed.values()))
    e11_signal = cells["E11"]["copy"]["signal"]
    benefit = bool(boot["mean"] >= .05 and boot["ci_lower"] > 0 and e11_signal and pos >= 2)
    equiv = bool(boot["ci_lower"] >= -.05 and boot["ci_upper"] <= .05)
    status = "BENEFIT_POSITIVE" if benefit else ("EQUIVALENT" if equiv else "NO_BENEFIT")
    return {"schema_version": "1", "status": status, "cells": cells,
            "primary": {"contrast": "E11_copy - E01_copy", "mean_D": boot["mean"],
                        "ci_lower": boot["ci_lower"], "ci_upper": boot["ci_upper"],
                        "n": boot["n"], "n_boot": boot["n_boot"], "boot_seed": boot["seed"],
                        "seed_D": d_seed, "positive_seeds": pos,
                        "e11_copy_signal": e11_signal, "benefit_positive": benefit},
            "equivalence": {"equivalent": equiv},
            "labels_computed": True, "not_a_result": False,
            "confirmatory_direction": "E11-E01"}


def run() -> dict[str, Any]:
    plan_hash = sha256_bytes(PLAN.read_bytes())
    if not FREEZE.exists():
        raise RuntimeError("F0.4 freeze missing")
    freeze = read_json(FREEZE)
    if freeze.get("plan_sha256") != plan_hash:
        raise RuntimeError("F0.4 plan hash mismatch")
    if freeze.get("status") != "owner_approved":
        raise RuntimeError("F0.4 not approved")
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
    fit_ok = len(units) == 6 and all(units[f"{c}_{s}"]["fit_pass"] for c in CELLS for s in SEEDS)
    labels = compute_labels(units, common) if fit_ok else {
        "schema_version": "1", "status": "NOT_EVALUABLE_OPTIMIZATION",
        "reason": "fit_gate_failed", "labels_computed": False, "not_a_result": True}
    out = {"schema_version": "1", "experiment": "C5 F0.4 fresh-seed directional confirmation",
           "cells": list(CELLS), "seeds": list(SEEDS), "updates": UPDATES,
           "lora_lr": LORA_LR, "adapter_lr": ADAPTER_LR,
           "n_units": len(units), "n_errors": len(errors), "wall_s": wall, "cap_s": CAP_SECONDS,
           "fit_gate": {"ratio": FIT_RATIO, "pass": bool(fit_ok)},
           "labels": labels, "partial": bool(errors) or len(units) != 6,
           "error": "OTHER_REDACTED" if errors else None,
           "labels_computed": labels["labels_computed"], "not_a_result": labels["not_a_result"],
           "test_split_used": False, "p1_used": False,
           "provenance": {"code_commit": freeze.get("code_commit"),
                          "command": "python runner/c5_pm_f0_4_confirm.py --run",
                          "input_sha256": sha256_bytes(json.dumps(common, sort_keys=True).encode()),
                          "clean_tree": subprocess.check_output(["git", "status", "--porcelain"], cwd=str(ROOT), text=True).strip() == ""}}
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
                      "n_units": out["n_units"], "n_errors": out["n_errors"], "wall_s": out["wall_s"]}, ensure_ascii=False))
    return 0 if not out["partial"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
