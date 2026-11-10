"""C5 F0.1 — E01 LoRA-only optimization diagnostic.

No signal evaluation, no generation, no M/phase7.  The only question is
whether E01 can reach the preregistered fit ratio under a tested update/LR
condition.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import multiprocessing as mp
import os
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

from runner.c5_mt5_lora_b0 import token_losses  # noqa: E402
from runner.c5_mt5_layer_probe import load_layer_cache  # noqa: E402
from runner.c5_pm_f0 import CACHE, K_M, build_cell, read_json, sha256_bytes  # noqa: E402
from runner.c5_pm_f0_mechanics import f0_memory, trainable_hash  # noqa: E402
from runner.c5_pm_phase6 import (  # noqa: E402
    labels_and_copy, set_arm_training, train_forward_loss,
)

CONDITIONS = (
    {"id": "C1", "updates": 100, "lr": 1e-4},
    {"id": "C2", "updates": 400, "lr": 1e-4},
    {"id": "C3", "updates": 1000, "lr": 1e-4},
    {"id": "C4", "updates": 400, "lr": 3e-4},
    {"id": "C5", "updates": 1000, "lr": 3e-4},
)
SEEDS = (20261108, 20261109, 20261110)
FIT_RATIO = 0.35
CAP_SECONDS = 60 * 60
OUT = ROOT / "reports/provenance/C5_f0_1"
UNITS = OUT / "units"
PLAN = ROOT / "docs/plan_c5_f0_1_opt_v0_1_2026-11-10.md"
FREEZE = ROOT / "docs/plan_c5_f0_1_opt_v0_1_FREEZE.json"


def step_seed(seed: int, step: int) -> int:
    return (int(seed) ^ ((0x9E3779B9 * (step + 1)) & 0xFFFFFFFF)) & 0xFFFFFFFF


def lora_optimizer(built: dict[str, Any], lr: float) -> torch.optim.Optimizer:
    params = [p for n, p in built["model"].named_parameters() if ".lora_" in n and p.requires_grad]
    if not params:
        raise RuntimeError("E01 has no trainable LoRA parameters")
    return torch.optim.AdamW([{"params": params, "lr": float(lr)}], weight_decay=0.01)


def run_unit(condition: dict[str, Any], seed: int) -> dict[str, Any]:
    torch.set_num_threads(2)
    started = time.time()
    preflight = read_json(ROOT / "reports/provenance/C5_b0a/m_cohort_preflight.json")
    rows = {}
    data = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
    for line in data.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line); rows[str(row["id"])] = row
    train_ids = list(preflight["train20_ids"])
    cache = load_layer_cache("train", CACHE)
    cache.update(load_layer_cache("val", CACHE))
    built = build_cell("E01", seed)
    built["arm"] = "E01"
    built["spec"]["memory_source"] = "eg2_layer19"
    built["spec"]["m_k"] = K_M
    labels, _ = labels_and_copy(built["tok"], rows, train_ids)
    before = trainable_hash(built)
    opt = lora_optimizer(built, condition["lr"])
    set_arm_training(built, True)
    curve = []
    losses = []
    for step in range(int(condition["updates"])):
        torch.manual_seed(step_seed(seed, step))
        rid = train_ids[step % len(train_ids)]
        loss = train_forward_loss(built["model"], f0_memory(built, rid, cache), labels[rid])
        if not torch.isfinite(loss):
            raise RuntimeError(f"{condition['id']} seed {seed}: non-finite loss at {step}")
        opt.zero_grad(set_to_none=True)
        loss.backward()
        params = [p for n, p in built["model"].named_parameters() if ".lora_" in n and p.requires_grad]
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        losses.append(float(loss.detach()))
        if step % 25 == 0 or step == int(condition["updates"]) - 1:
            curve.append({"step": step + 1, "loss": float(loss.detach())})
    set_arm_training(built, False)
    after = trainable_hash(built)
    ratio = losses[-1] / losses[0] if losses[0] else None
    out = {
        "condition": condition["id"],
        "updates": int(condition["updates"]),
        "lr": float(condition["lr"]),
        "seed": int(seed),
        "loss_first": float(losses[0]),
        "loss_last": float(losses[-1]),
        "loss_mean": float(np.mean(losses)),
        "loss_min": float(np.min(losses)),
        "loss_max": float(np.max(losses)),
        "loss_curve": curve,
        "fit_ratio": float(ratio) if ratio is not None else None,
        "fit_pass": bool(ratio is not None and ratio <= FIT_RATIO),
        "weight_change_ok": bool(before != after),
        "elapsed_s": float(time.time() - started),
    }
    del built
    gc.collect()
    return out


def _worker(condition: dict[str, Any], seed: int, q: Any) -> None:
    try:
        q.put(("ok", condition["id"], seed, run_unit(condition, seed)))
    except BaseException as exc:
        q.put(("error", condition["id"], seed,
               {"condition": condition["id"], "seed": seed,
                "error": type(exc).__name__, "message": str(exc)[:400]}))


def run() -> dict[str, Any]:
    FREEZE.parent.mkdir(parents=True, exist_ok=True)
    plan_hash = sha256_bytes(PLAN.read_bytes())
    if not FREEZE.exists():
        raise RuntimeError("F0.1 freeze manifest is missing")
    freeze = read_json(FREEZE)
    if freeze.get("plan_sha256") != plan_hash:
        raise RuntimeError("F0.1 plan hash mismatch")
    if freeze.get("status") != "owner_approved":
        raise RuntimeError("F0.1 is not owner-approved")
    started = time.time()
    ctx = mp.get_context("spawn")
    results = {}
    errors = []
    tasks = [(c, s) for c in CONDITIONS for s in SEEDS]
    for offset in range(0, len(tasks), 4):
        if time.time() - started >= CAP_SECONDS:
            break
        batch = tasks[offset:offset + 4]
        q = ctx.Queue()
        procs = [ctx.Process(target=_worker, args=(c, s, q)) for c, s in batch]
        for p in procs:
            p.start()
        got = 0
        while got < len(batch) and time.time() - started < CAP_SECONDS:
            try:
                kind, cid, seed, payload = q.get(timeout=10)
            except Exception:
                if all(not p.is_alive() for p in procs):
                    break
                continue
            got += 1
            if kind == "ok":
                results[(cid, seed)] = payload
            else:
                errors.append(payload)
        for p in procs:
            p.join(timeout=5)
            if p.is_alive():
                p.terminate()
    wall = time.time() - started
    UNITS.mkdir(parents=True, exist_ok=True)
    summaries = {}
    for c in CONDITIONS:
        vals = [results.get((c["id"], s)) for s in SEEDS]
        present = [v for v in vals if v]
        ratios = [float(v["fit_ratio"]) for v in present]
        passes = sum(bool(v["fit_pass"]) for v in present)
        condition_fit = bool(len(present) == 3 and passes >= 2 and np.median(ratios) <= FIT_RATIO)
        summaries[c["id"]] = {
            "updates": c["updates"], "lr": c["lr"],
            "n": len(present), "fit_passes": passes,
            "median_fit_ratio": float(np.median(ratios)) if ratios else None,
            "condition_fit": condition_fit,
            "seeds": {str(v["seed"]): v for v in present},
        }
    for cid, s in results:
        (UNITS / f"{cid}_{s}.json").write_text(
            json.dumps(results[(cid, s)], indent=2) + "\n", encoding="utf-8")
    any_fit = any(v["condition_fit"] for v in summaries.values())
    diagnosis = ("E01_UNDERFIT_RESCUED" if any_fit
                 else "E01_UNDERFIT_NOT_RESCUED_IN_TESTED_RANGE")
    out = {
        "schema_version": "1",
        "experiment": "C5 F0.1 E01 optimization diagnostic",
        "status": diagnosis,
        "fit_ratio_gate": FIT_RATIO,
        "conditions": summaries,
        "n_units": len(results),
        "n_errors": len(errors),
        "wall_s": wall,
        "cap_s": CAP_SECONDS,
        "partial": bool(errors) or len(results) != 15,
        "error": "OTHER_REDACTED" if errors else None,
        "freeze": {"status": freeze["status"], "plan_sha256": plan_hash,
                   "code_commit": freeze.get("code_commit")},
        "no_signal": True,
        "labels_computed": False,
        "not_a_result": True,
        "test_split_used": False,
        "p1_used": False,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    if not ap.run:
        raise SystemExit("pass --run to execute")
    out = run()
    print(json.dumps({"status": out["status"], "n_units": out["n_units"],
                      "n_errors": out["n_errors"], "wall_s": out["wall_s"]}, ensure_ascii=False))
    return 0 if not out["partial"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
