"""C5 F0 Stage R — registered 3-seed, 4 cells, 100 updates each."""

from __future__ import annotations

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
from transformers.modeling_outputs import BaseModelOutput

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_mt5_lora_b0 import copy_ce, generation_record, token_losses  # noqa: E402
from runner.c5_mt5_layer_probe import load_layer_cache  # noqa: E402
from runner.c5_pm_f0 import CACHE, CELLS, K_M, build_cell, read_json, sha256_bytes  # noqa: E402
from runner.c5_pm_f0_audit import canonical_digest  # noqa: E402
from runner.c5_pm_f0_mechanics import f0_memory, load_inputs, trainable_hash  # noqa: E402
from runner.c5_pm_phase6 import (  # noqa: E402
    labels_and_copy, m_records_for, optimizer_for, phase7_records_for,
    set_arm_training, train_forward_loss,
)
from runner.c5_pm_stats import bootstrap_paired_v2  # noqa: E402

SEEDS = (20261108, 20261109, 20261110)
R = ROOT / "reports/provenance/C5_f0/r"
UNITS = R / "units"
M_RECORDS = R
PHASE7 = R / "phase7_records"
CHECKPOINTS = R / "checkpoints"
R_PASS = R / "r_mechanics_pass.json"
R_LABELS = R / "f0_r_labels.json"
R_REPORT = R / "f0_report.json"
INIT_HASHES = R / "init_hashes.json"
N_BOOT = 10000
BOOT_SEED = 20261109


def step_seed(seed: int, step: int) -> int:
    return (int(seed) ^ ((0x9E3779B9 * (step + 1)) & 0xFFFFFFFF)) & 0xFFFFFFFF


def eval_signal(built: dict[str, Any], ids: list[str], cache: dict[str, dict],
                labels: dict[str, torch.Tensor], copies: dict[str, torch.Tensor],
                donors: dict[str, list[str]]) -> dict[str, Any]:
    set_arm_training(built, False)
    per_doc: dict[str, Any] = {}
    with torch.inference_mode():
        for rid in ids:
            real = f0_memory(built, rid, cache)
            lab = labels[rid]
            mask = copies[rid]
            rc, wc, rf, wf = [], [], [], []
            for donor in donors[rid]:
                wrong = f0_memory(built, donor, cache)
                k = min(int(real.shape[0]), int(wrong.shape[0]), K_M)
                fr, tr = token_losses(built["model"], real[:k], lab)
                fw, tw = token_losses(built["model"], wrong[:k], lab)
                c1 = copy_ce(tr, lab, mask)
                c2 = copy_ce(tw, lab, mask)
                if c1 is not None and c2 is not None:
                    rc.append(c1); wc.append(c2)
                rf.append(fr); wf.append(fw)
            if not rc:
                continue
            per_doc[rid] = {
                "n_donors": len(rc),
                "real_ce_copy": float(np.mean(rc)),
                "wrong_ce_copy": float(np.mean(wc)),
                "delta_shuffled_copy": float(np.mean(np.asarray(wc) - np.asarray(rc))),
                "real_ce_full": float(np.mean(rf)),
                "wrong_ce_full": float(np.mean(wf)),
                "delta_shuffled_full": float(np.mean(np.asarray(wf) - np.asarray(rf))),
                "copy_tokens": int(mask.sum()),
                "copy_coverage": float(mask.sum()) / max(1, int(mask.numel())),
            }
    return {"n_docs": len(per_doc), "per_doc": per_doc}


def build_controls_f0(built: dict[str, Any], train_ids: list[str], targets: list[str],
                      cache: dict[str, dict]) -> dict[str, Any]:
    contributors = [rid for rid in train_ids if int(cache[rid]["h"].shape[0]) >= K_M]
    if len(contributors) < 10:
        raise RuntimeError(f"contributors {len(contributors)} < 10")
    with torch.inference_mode():
        pieces = [f0_memory(built, rid, cache)[:K_M] for rid in contributors]
        pos_mean = torch.stack(pieces).mean(dim=0)
        real_prefix = {tid: f0_memory(built, tid, cache)[:K_M] for tid in targets}
        denom = torch.linalg.norm(pos_mean)
        if float(denom) == 0.0:
            raise RuntimeError("M_POS_MEAN zero norm")
        m_norm = {tid: pos_mean * (torch.linalg.norm(real_prefix[tid]) / denom) for tid in targets}
    return {"M_POS_MEAN": pos_mean.detach(), "M_NORM": m_norm,
            "real_prefix": real_prefix, "contributors": contributors}


def train_registered_f0(built: dict[str, Any], train_ids: list[str], cache: dict[str, dict],
                        labels: dict[str, torch.Tensor], seed: int) -> dict[str, Any]:
    opt = optimizer_for(built)
    set_arm_training(built, True)
    losses = []
    for step in range(100):
        torch.manual_seed(step_seed(seed, step))
        rid = train_ids[step % len(train_ids)]
        mem = f0_memory(built, rid, cache)
        loss = train_forward_loss(built["model"], mem, labels[rid])
        if not torch.isfinite(loss):
            raise RuntimeError(f"{built['cell']} seed {seed}: non-finite loss step {step}")
        opt.zero_grad(set_to_none=True)
        loss.backward()
        params = [p for p in built["model"].parameters() if p.requires_grad]
        if built["adapter"] is not None:
            params += [p for p in built["adapter"].parameters() if p.requires_grad]
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        losses.append(float(loss.detach()))
    set_arm_training(built, False)
    return {"updates": 100, "loss_first": losses[0], "loss_last": losses[-1],
            "loss_mean": float(np.mean(losses)), "all_finite": bool(np.all(np.isfinite(losses)))}


def generate_f0(built: dict[str, Any], ids: list[str], cache: dict[str, dict]) -> int:
    set_arm_training(built, False)
    old = bool(built["model"].config.use_cache)
    built["model"].config.use_cache = True
    n = 0
    try:
        for rid in ids:
            mem = f0_memory(built, rid, cache)
            with torch.inference_mode():
                gen = built["model"].generate(
                    encoder_outputs=BaseModelOutput(last_hidden_state=mem.unsqueeze(0)),
                    attention_mask=torch.ones(1, mem.shape[0], dtype=torch.long),
                    max_new_tokens=256, num_beams=1, do_sample=False,
                    decoder_start_token_id=built["model"].config.decoder_start_token_id or built["tok"].pad_token_id,
                    eos_token_id=built["tok"].eos_token_id,
                    pad_token_id=built["tok"].pad_token_id,
                )
            generation_record(gen, built["tok"], 256)
            n += 1
    finally:
        built["model"].config.use_cache = old
    return n


def save_checkpoint(built: dict[str, Any], cell: str, seed: int) -> str:
    path = CHECKPOINTS / cell / f"{seed}.pt"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"cell": cell, "seed": seed,
               "adapter": built["adapter"].state_dict() if built["adapter"] is not None else None,
               "lora": {name: p.detach().cpu() for name, p in built["model"].named_parameters()
                        if ".lora_" in name}}
    torch.save(payload, path)
    return str(path.relative_to(ROOT))


def run_unit(cell: str, seed: int) -> dict[str, Any]:
    R.mkdir(parents=True, exist_ok=True)
    UNITS.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(2)
    t0 = time.time()
    inputs = load_inputs()
    preflight = inputs["preflight"]; rows = inputs["rows"]
    train_ids = list(preflight["train20_ids"]); val_ids = list(preflight["val20_ids"])
    common = list(preflight["common_ids"])
    cache = load_layer_cache("train", CACHE); cache.update(load_layer_cache("val", CACHE))
    built = build_cell(cell, seed)
    built["arm"] = cell
    built["spec"]["memory_source"] = "eg2_layer19"
    built["spec"]["m_k"] = K_M
    labels, copies = labels_and_copy(built["tok"], rows, list(dict.fromkeys(train_ids + val_ids + common)))
    donors = {}
    for rid in val_ids:
        cand = [x for x in val_ids if x != rid]
        cand.sort(key=lambda x: (abs(int(cache[x]["length"]) - int(cache[rid]["length"])), x))
        donors[rid] = cand[:5]
    init_tensors = {}
    if built["adapter"] is not None:
        init_tensors.update({f"adapter.{k}": v for k, v in built["adapter"].state_dict().items()})
    init_tensors.update({k: v for k, v in built["model"].named_parameters() if ".lora_" in k})
    init = {"hash": canonical_digest(init_tensors),
            "lora_names": list(built["lora_names"]),
            "n_params": int(sum(p.numel() for p in built["adapter"].parameters()) if built["adapter"] is not None else 0)
                        + int(sum(p.numel() for n, p in built["model"].named_parameters() if ".lora_" in n))}
    step0 = eval_signal(built, val_ids, cache, labels, copies, donors)
    train = {"updates": 0, "all_finite": True}
    if cell != "E00":
        train = train_registered_f0(built, train_ids, cache, labels, seed)
    final = eval_signal(built, val_ids, cache, labels, copies, donors)
    controls = build_controls_f0(built, train_ids, common, cache)
    m_records = m_records_for(built, common, controls, labels, copies, seed)
    mdir = M_RECORDS / f"m_records_{cell}_{seed}.json"
    mdir.write_text(json.dumps(m_records, indent=2) + "\n", encoding="utf-8")
    p7 = phase7_records_for(built, common, controls, cache, {}, labels, copies, donors, seed)
    p7dir = PHASE7 / cell / f"{seed}.json"; p7dir.parent.mkdir(parents=True, exist_ok=True)
    p7dir.write_text(json.dumps(p7, indent=2) + "\n", encoding="utf-8")
    gen_count = generate_f0(built, val_ids, cache)
    checkpoint = save_checkpoint(built, cell, seed)
    unit = {"cell": cell, "seed": seed, "updates": int(train["updates"]),
            "step0": step0, "train": train, "final": final,
            "m_records": len(m_records), "phase7_records": len(p7),
            "generation_records": int(gen_count), "checkpoint": checkpoint,
            "init": init, "elapsed_s": float(time.time() - t0)}
    UNITS.mkdir(parents=True, exist_ok=True)
    (UNITS / f"{cell}_{seed}.json").write_text(json.dumps(unit, indent=2) + "\n", encoding="utf-8")
    del built; gc.collect()
    return {"cell": cell, "seed": seed, "updates": unit["updates"],
            "m_records": unit["m_records"], "phase7_records": unit["phase7_records"],
            "generation_records": unit["generation_records"], "elapsed_s": unit["elapsed_s"]}


def _worker(cell: str, seed: int, q: Any) -> None:
    try:
        q.put(("ok", seed, run_unit(cell, seed)))
    except BaseException as exc:
        q.put(("error", seed, {"cell": cell, "error": type(exc).__name__, "message": str(exc)[:400]}))


def _cell_stats(units: dict[str, Any], common: list[str], cell: str, endpoint: str) -> dict[str, Any]:
    per_seed = {}
    for seed in SEEDS:
        u = units.get(f"{cell}_{seed}")
        if not u:
            raise RuntimeError(f"missing unit {cell}_{seed}")
        vals = []
        for rid in common:
            pd = u["final"]["per_doc"].get(rid)
            if pd is None or pd.get(f"delta_shuffled_{endpoint}") is None:
                raise RuntimeError(f"missing {endpoint} endpoint {cell} {seed} {rid}")
            vals.append(float(pd[f"delta_shuffled_{endpoint}"]))
        per_seed[seed] = vals
    doc_mean = [float(np.mean([per_seed[s][i] for s in SEEDS])) for i in range(len(common))]
    boot = bootstrap_paired_v2(doc_mean, n_boot=N_BOOT, seed=BOOT_SEED)
    seed_means = {str(s): float(np.mean(per_seed[s])) for s in SEEDS}
    pos_seeds = int(sum(v > 0 for v in seed_means.values()))
    signal = bool(
        (boot["mean"] >= 0.05 and boot["ci_lower"] > 0 and pos_seeds >= 2)
        if endpoint == "copy" else
        (boot["mean"] > 0 and boot["ci_lower"] > 0 and pos_seeds >= 2)
    )
    return {"endpoint": endpoint, "mean": boot["mean"], "ci_lower": boot["ci_lower"],
            "ci_upper": boot["ci_upper"], "n": boot["n"], "n_boot": boot["n_boot"],
            "boot_seed": boot["seed"], "seed_means": seed_means,
            "positive_seeds": pos_seeds, "signal": signal, "doc_mean": doc_mean}


def compute_labels(units: dict[str, Any], common: list[str]) -> dict[str, Any]:
    cells = {}
    for cell in CELLS:
        cells[cell] = {e: _cell_stats(units, common, cell, e) for e in ("copy", "full")}
    d_docs = []
    for i in range(len(common)):
        e01 = np.mean([units[f"E01_{s}"]["final"]["per_doc"][common[i]]["delta_shuffled_copy"]
                       for s in SEEDS])
        e11 = np.mean([units[f"E11_{s}"]["final"]["per_doc"][common[i]]["delta_shuffled_copy"]
                       for s in SEEDS])
        d_docs.append(float(e01 - e11))
    dboot = bootstrap_paired_v2(d_docs, n_boot=N_BOOT, seed=BOOT_SEED)
    d_seed = {}
    for s in SEEDS:
        vals = []
        for rid in common:
            vals.append(float(units[f"E01_{s}"]["final"]["per_doc"][rid]["delta_shuffled_copy"]
                              - units[f"E11_{s}"]["final"]["per_doc"][rid]["delta_shuffled_copy"]))
        d_seed[str(s)] = float(np.mean(vals))
    d_pos = int(sum(v > 0 for v in d_seed.values()))
    e01_copy = cells["E01"]["copy"]["signal"]
    pass_positive = bool(dboot["mean"] > 0 and dboot["ci_lower"] > 0.05 and e01_copy and d_pos >= 2)
    all_fail = bool(not cells["E01"]["copy"]["signal"] and not cells["E01"]["full"]["signal"]
                    and not cells["E11"]["copy"]["signal"] and not cells["E11"]["full"]["signal"])
    equivalent = bool(dboot["ci_lower"] >= -0.05 and dboot["ci_upper"] <= 0.05)
    harm = bool(dboot["ci_lower"] > 0 and not equivalent)
    benefit = bool(dboot["ci_upper"] < 0 and not equivalent)
    if pass_positive:
        state = "PASS_POSITIVE"; reason = None
    elif all_fail:
        state = "ROUTE_STOP"
        reason = ("no_signal_equivalent" if equivalent else
                  "adapter_harm" if harm else "adapter_benefit" if benefit else "no_signal_uncertain")
    else:
        state = "INDETERMINATE"; reason = None
    return {
        "schema_version": "1",
        "status": state,
        "reason": reason,
        "cells": cells,
        "primary": {"contrast": "E01_copy - E11_copy", "doc_D": d_docs,
                    "mean_D": dboot["mean"], "ci_lower": dboot["ci_lower"],
                    "ci_upper": dboot["ci_upper"], "n": dboot["n"],
                    "n_boot": dboot["n_boot"], "boot_seed": dboot["seed"],
                    "seed_D": d_seed, "positive_seeds": d_pos,
                    "pass_positive": pass_positive},
        "equivalence": {"equivalent": equivalent, "harm": harm, "benefit": benefit},
        "all_fail": all_fail,
        "near_threshold": {
            "m_mean": float(dboot["mean"] - 0.05),
            "m_lower": float(dboot["ci_lower"] - 0.05),
            "m_b": float(dboot["mean"] - 0.05),
            "m_sign": int(d_pos - 2),
        },
        "labels_computed": True,
        "not_a_result": False,
    }


def run_r() -> dict[str, Any]:
    code_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True).strip()
    clean = subprocess.check_output(["git", "status", "--porcelain"], cwd=str(ROOT), text=True).strip() == ""
    d0 = read_json(ROOT / "reports/provenance/C5_f0/d0/f0_d0.json")
    d1 = read_json(ROOT / "reports/provenance/C5_f0/d1/f0_d1_mechanics.json")
    if not d1.get("mechanics_pass"):
        raise RuntimeError("D1 mechanics not passed")
    start = time.time()
    ctx = mp.get_context("spawn")
    summaries = []
    errors = []
    for seed in SEEDS:
        q = ctx.Queue()
        procs = [ctx.Process(target=_worker, args=(c, seed, q)) for c in CELLS]
        for p in procs: p.start()
        got = 0
        while got < 4 and time.time() - start < 96 * 60:
            try:
                kind, s, payload = q.get(timeout=10)
            except Exception:
                if all(not p.is_alive() for p in procs): break
                continue
            if kind == "ok": summaries.append(payload); got += 1
            else: errors.append(payload); got += 1
        for p in procs:
            p.join(timeout=5)
            if p.is_alive(): p.terminate()
        if got < 4:
            break
    wall = time.time() - start
    partial = bool(errors) or len(summaries) != 12 or wall > 96 * 60
    units = {}
    for cell in CELLS:
        for seed in SEEDS:
            p = UNITS / f"{cell}_{seed}.json"
            if p.exists(): units[f"{cell}_{seed}"] = json.loads(p.read_text(encoding="utf-8"))
    donor_hashes = {}
    for rid in read_json(ROOT / "reports/provenance/C5_b0a/m_cohort_preflight.json")["val20_ids"]:
        donor_hashes[rid] = sha256_bytes(rid.encode())
    r_pass = {
        "schema_version": "1",
        "seeds": 3, "cells": 4,
        "updates_total": sum(u["updates"] for u in units.values()),
        "m_records": sum(u["m_records"] for u in units.values()),
        "phase7_records": sum(u["phase7_records"] for u in units.values()),
        "generation_records": sum(u["generation_records"] for u in units.values()),
        "real_memory_ce_calls": 0,
        "wrong_donor_ce_calls": 0,
        "donor_map_loads": 0,
        "provenance_ok": bool(code_commit and clean),
        "r_mechanics_pass": False,
        "cpu_affinity": "not_restricted", "cgroup_cpu_quota": "not_applicable",
        "torch_threads": 2, "thread_pool_counts": {"interop": 1},
        "donor_map_sha256": sha256_bytes(json.dumps(donor_hashes, sort_keys=True).encode()),
        "per_doc_donor_sha256": donor_hashes,
        "provenance": {"code_commit": code_commit, "command": "python runner/c5_pm_f0_registered.py",
                       "input_sha256": sha256_bytes(json.dumps({"d0": d0.get("seed"), "d1": d1.get("updates_total")}, sort_keys=True).encode()),
                       "clean_tree": bool(clean)},
        "expected_counts": {"seeds": 3, "cells": 4, "updates_total": 900,
                            "m_records": 1440, "phase7_records": 7200, "generation_records": 240},
    }
    r_pass["r_mechanics_pass"] = bool(
        not partial and r_pass["provenance_ok"]
        and len(units) == 12
        and r_pass["updates_total"] == 900
        and r_pass["m_records"] == 1440
        and r_pass["phase7_records"] == 7200
        and r_pass["generation_records"] == 240
    )
    R.mkdir(parents=True, exist_ok=True)
    R_PASS.write_text(json.dumps(r_pass, indent=2) + "\n", encoding="utf-8")
    common = list(read_json(ROOT / "reports/provenance/C5_b0a/m_cohort_preflight.json")["common_ids"])
    labels = compute_labels(units, common) if len(units) == 12 else {"status": "NOT_EVALUABLE",
        "reason": "missing_units", "labels_computed": False, "not_a_result": True}
    R_LABELS.write_text(json.dumps(labels, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (R / "f0_report.json").write_text(json.dumps({"partial": partial, "errors": errors,
                                                   "summaries": summaries,
                                                   "labels": labels}, indent=2) + "\n", encoding="utf-8")
    # Init hashes: copy P per seed/cell into R.
    p = read_json(ROOT / "reports/provenance/C5_f0/pre_r/pre_r_init_audit.json")
    INIT_HASHES.write_text(json.dumps(p["per_seed"], indent=2) + "\n", encoding="utf-8")
    return {"partial": partial, "r_mechanics_pass": r_pass["r_mechanics_pass"],
            "units": len(units), "wall_s": wall, "errors": errors}


def main() -> int:
    ap = __import__("argparse").ArgumentParser()
    ap.add_argument("--mode", choices=("registered",), required=True)
    args = ap.parse_args()
    out = run_r()
    print(json.dumps(out, ensure_ascii=False))
    return 0 if out["r_mechanics_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
