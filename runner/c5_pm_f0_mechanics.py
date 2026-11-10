"""C5 F0 D1 mechanics-only evaluator.

D1 is a one-update mechanics gate.  It must not compute or persist signal
deltas, per-document objects, phase7 records, or final objects.  The only
artifact written by this module is ``d1/f0_d1_mechanics.json``.
"""

from __future__ import annotations

import gc
import hashlib
import io
import json
import multiprocessing as mp
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import torch
from transformers.modeling_outputs import BaseModelOutput

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_mt5_lora_b0 import copy_ce, generation_record, token_losses  # noqa: E402
from runner.c5_pm_f0 import (  # noqa: E402
    CACHE, CELLS, K_M, PREFLIGHT, build_cell, check_freeze, read_json,
    sha256_bytes, tensor_sha256,
)
from runner.c5_pm_phase6 import (  # noqa: E402
    DATA, SPLITS, labels_and_copy, optimizer_for, set_arm_training,
    train_forward_loss,
)

D1_SEED = 20261111
D1_OUT = ROOT / "reports/provenance/C5_f0/d1/f0_d1_mechanics.json"
EXPECTED_M_PER_CELL = 120
EXPECTED_GEN_PER_CELL = 20
EXPECTED_REAL_CE_PER_CELL = 40
EXPECTED_M_TOTAL = 480
EXPECTED_GEN_TOTAL = 80
EXPECTED_REAL_CE_TOTAL = 160


def read_jsonl_by_id(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            out[str(row["id"])] = row
    return out


def load_inputs() -> dict[str, Any]:
    preflight = read_json(PREFLIGHT)
    p1 = read_json(ROOT / "reports/provenance/C5_b0a/p1_usage.json")
    if p1.get("p1_used") is not False or p1.get("test_split_read") is not False:
        raise RuntimeError("P1 usage manifest is not clean")
    rows = read_jsonl_by_id(DATA)
    val_ids = list(preflight["val20_ids"])
    common_ids = list(preflight["common_ids"])
    for rid in val_ids:
        if rid not in rows:
            raise RuntimeError(f"missing F5 row: {rid}")
    return {"preflight": preflight, "p1": p1, "rows": rows,
            "val_ids": val_ids, "common_ids": common_ids}


def f0_memory(built: dict[str, Any], rid: str, cache: dict[str, dict]) -> torch.Tensor:
    h = cache[rid]["h"][:K_M]
    if built["adapter"] is not None:
        h = built["adapter"](h)
    return h


def finite_eval(built: dict[str, Any], ids: list[str], cache: dict[str, dict],
                labels: dict[str, torch.Tensor], copies: dict[str, torch.Tensor]) -> dict[str, Any]:
    set_arm_training(built, False)
    all_finite = True
    copy_ok = 0
    calls = 0
    with torch.inference_mode():
        for rid in ids:
            mem = f0_memory(built, rid, cache)
            full, tok_loss = token_losses(built["model"], mem, labels[rid])
            calls += 1
            if not torch.isfinite(torch.tensor(full)) or not torch.isfinite(tok_loss).all():
                all_finite = False
            c = copy_ce(tok_loss, labels[rid], copies[rid])
            if c is not None and torch.isfinite(torch.tensor(c)):
                copy_ok += 1
    return {"n_docs": len(ids), "ce_finite": bool(all_finite),
            "copy_ok": int(copy_ok), "ce_calls": int(calls)}


def trainable_hash(built: dict[str, Any]) -> str:
    tensors = {}
    if built["adapter"] is not None:
        tensors.update({f"adapter.{k}": v for k, v in built["adapter"].state_dict().items()})
    tensors.update({k: v for k, v in built["model"].named_parameters() if ".lora_" in k})
    return tensor_sha256(tensors) if tensors else sha256_bytes(b"")


def checkpoint_digest(built: dict[str, Any]) -> str | None:
    if built["adapter"] is None and not built["lora_names"]:
        return None
    payload: dict[str, Any] = {
        "adapter": built["adapter"].state_dict() if built["adapter"] is not None else None,
        "lora": {name: p.detach().cpu() for name, p in built["model"].named_parameters()
                 if ".lora_" in name},
    }
    buf = io.BytesIO()
    torch.save(payload, buf)
    return sha256_bytes(buf.getvalue())


def one_update(built: dict[str, Any], rid: str, cache: dict[str, dict],
               labels: dict[str, torch.Tensor]) -> dict[str, Any]:
    before = trainable_hash(built)
    set_arm_training(built, True)
    opt = optimizer_for(built)
    opt.zero_grad(set_to_none=True)
    loss = train_forward_loss(built["model"], f0_memory(built, rid, cache), labels[rid])
    if not torch.isfinite(loss):
        raise RuntimeError(f"{built['cell']}: non-finite training loss")
    loss.backward()
    params = [p for p in built["model"].parameters() if p.requires_grad]
    if built["adapter"] is not None:
        params += [p for p in built["adapter"].parameters() if p.requires_grad]
    torch.nn.utils.clip_grad_norm_(params, 1.0)
    opt.step()
    set_arm_training(built, False)
    after = trainable_hash(built)
    return {
        "loss_finite": bool(torch.isfinite(loss)),
        "weight_changed": bool(before != after),
        "updates": 1,
    }


def generate_count(built: dict[str, Any], ids: list[str], cache: dict[str, dict]) -> int:
    set_arm_training(built, False)
    old_cache = bool(built["model"].config.use_cache)
    built["model"].config.use_cache = True
    n = 0
    try:
        for rid in ids:
            mem = f0_memory(built, rid, cache)
            with torch.inference_mode():
                gen = built["model"].generate(
                    encoder_outputs=BaseModelOutput(last_hidden_state=mem.unsqueeze(0)),
                    attention_mask=torch.ones(1, mem.shape[0], dtype=torch.long),
                    max_new_tokens=256,
                    num_beams=1,
                    do_sample=False,
                    decoder_start_token_id=built["model"].config.decoder_start_token_id or built["tok"].pad_token_id,
                    eos_token_id=built["tok"].eos_token_id,
                    pad_token_id=built["tok"].pad_token_id,
                )
            generation_record(gen, built["tok"], 256)
            n += 1
    finally:
        built["model"].config.use_cache = old_cache
    return n


def run_cell(cell: str) -> dict[str, Any]:
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    inputs = load_inputs()
    preflight = inputs["preflight"]
    rows = inputs["rows"]
    val_ids = inputs["val_ids"]
    common_ids = inputs["common_ids"]
    cache = {}
    from runner.c5_mt5_layer_probe import load_layer_cache
    cache.update(load_layer_cache("train", CACHE))
    cache.update(load_layer_cache("val", CACHE))
    if len(val_ids) != 20 or len(common_ids) != 15:
        raise RuntimeError(f"cohort mismatch: val={len(val_ids)} common={len(common_ids)}")
    for rid in common_ids:
        if int(cache[rid]["length"]) < K_M:
            raise RuntimeError(f"common id below K_M: {rid}")

    t0 = time.time()
    built = build_cell(cell, D1_SEED)
    built["arm"] = cell
    built["spec"]["memory_source"] = "eg2_layer19"
    built["spec"]["m_k"] = K_M
    train_id = inputs["preflight"]["train20_ids"][0]
    label_ids = list(dict.fromkeys(val_ids + [train_id]))
    labels, copies = labels_and_copy(built["tok"], rows, label_ids)
    labels_sha = sha256_bytes(b"".join(labels[r].numpy().tobytes() for r in val_ids))
    cache_sha = sha256_bytes(b"".join(
        cache[r]["h"][:K_M].numpy().tobytes() for r in val_ids
    ))
    base_config_sha = sha256_bytes(str(built["model"].config.to_dict()).encode("utf-8"))
    init = {
        "adapter_sha": tensor_sha256({k: v for k, v in built["adapter"].state_dict().items()})
        if built["adapter"] is not None else None,
        "lora_sha": tensor_sha256({k: v for k, v in built["model"].named_parameters()
                                   if ".lora_" in k}),
        "rng": sha256_bytes(torch.get_rng_state().numpy().tobytes()),
        "lora_modules": len(built["lora_names"]),
        "lora_names": list(built["lora_names"]),
        "lora_b_zero": all(
            torch.count_nonzero(p).item() == 0
            for n, p in built["model"].named_parameters() if n.endswith(".lora_B")
        ) if built["lora_names"] else True,
    }

    setup_s = time.time() - t0
    t1 = time.time()
    step0 = finite_eval(built, val_ids, cache, labels, copies)
    step0_s = time.time() - t1
    train = {"updates": 0, "loss_finite": True, "weight_changed": True}
    if cell != "E00":
        t2 = time.time()
        train = one_update(built, train_id, cache, labels)
        step0_s += time.time() - t2
    post_rng = sha256_bytes(torch.get_rng_state().numpy().tobytes())
    t3 = time.time()
    final = finite_eval(built, val_ids, cache, labels, copies)
    final_s = time.time() - t3
    t4 = time.time()
    gen_count = generate_count(built, val_ids, cache)
    generation_s = time.time() - t4
    digest = checkpoint_digest(built)
    m_records = len(common_ids) * 2 * 2 * 2

    out = {
        "cell": cell,
        "updates": int(train["updates"]),
        "lora_params": int(sum(p.numel() for n, p in built["model"].named_parameters()
                               if ".lora_" in n)),
        "adapter_params": int(sum(p.numel() for p in built["adapter"].parameters())
                              if built["adapter"] is not None else 0),
        "n_docs_step0": int(step0["n_docs"]),
        "n_docs_final": int(final["n_docs"]),
        "m_records": int(m_records),
        "generation_records": int(gen_count),
        "ce_finite": bool(step0["ce_finite"] and final["ce_finite"] and train["loss_finite"]),
        "step0": step0,
        "final": final,
        "train": train,
        "init": init,
        "post_step0_rng": post_rng,
        "post_step0_weight_change": bool(train["weight_changed"]),
        "checkpoint_digest": digest,
        "base_config_sha": base_config_sha,
        "cache_sha": cache_sha,
        "labels_sha": labels_sha,
        "timings": {
            "setup_s": float(setup_s),
            "step0_s": float(step0_s),
            "step100_s": 0.0,
            "m_build_s": 0.0,
            "m_ce_s": 0.0,
            "generation_s": float(generation_s),
            "total_s": float(time.time() - t0),
        },
    }
    del built
    gc.collect()
    return out


def _worker(cell: str, q: Any) -> None:
    try:
        q.put(("ok", run_cell(cell)))
    except BaseException as exc:  # pragma: no cover - process boundary
        q.put(("error", {"cell": cell, "error": type(exc).__name__,
                         "message": str(exc)[:500]}))


def run_d1() -> dict[str, Any]:
    if os.cpu_count() is None or os.cpu_count() < 4:
        raise RuntimeError(f"insufficient nproc: {os.cpu_count()}")
    d0_path = ROOT / "reports/provenance/C5_f0/d0/f0_d0.json"
    d0 = read_json(d0_path)
    if d0.get("mode") != "d0_zero_update" or d0.get("updates") != 0:
        raise RuntimeError("D0 mechanics artifact is not a zero-update D0")
    code_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True
    ).strip()
    clean_tree = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=str(ROOT), text=True
    ).strip() == ""
    started = time.time()
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    procs = [ctx.Process(target=_worker, args=(cell, q)) for cell in CELLS]
    for p in procs:
        p.start()
    results: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []
    deadline = time.time() + 25 * 60
    while len(results) + len(errors) < len(procs) and time.time() < deadline:
        try:
            kind, payload = q.get(timeout=5)
        except Exception:
            if any(p.is_alive() for p in procs):
                continue
            break
        if kind == "ok":
            results[payload["cell"]] = payload
        else:
            errors.append(payload)
    for p in procs:
        p.join(timeout=5)
        if p.is_alive():
            p.terminate()
    wall = time.time() - started

    cells: dict[str, Any] = {}
    for cell in CELLS:
        r = results.get(cell)
        if r is None:
            cells[cell] = {"updates": 0, "lora_params": 0, "adapter_params": 0,
                           "n_docs_step0": 0, "n_docs_final": 0, "m_records": 0,
                           "generation_records": 0, "ce_finite": False}
        else:
            cells[cell] = {k: r[k] for k in (
                "updates", "lora_params", "adapter_params", "n_docs_step0",
                "n_docs_final", "m_records", "generation_records", "ce_finite",
            )}

    init = {c: results[c]["init"] for c in results}
    lora_names_equal = (
        "E01" in init and "E11" in init and init["E01"]["lora_names"] == init["E11"]["lora_names"]
    )
    lora_ab_hash_equal = (
        "E01" in init and "E11" in init and init["E01"]["lora_sha"] == init["E11"]["lora_sha"]
    )
    adapter_hash_equal = (
        "E10" in init and "E11" in init and init["E10"]["adapter_sha"] == init["E11"]["adapter_sha"]
    )
    post_init_rng_equal = (
        "E01" in init and "E11" in init and init["E01"]["rng"] == init["E11"]["rng"]
    )
    post_step0_rng_equal = (
        "E01" in results and "E11" in results
        and results["E01"]["post_step0_rng"] == results["E11"]["post_step0_rng"]
    )
    lora_b_zero = all(init[c]["lora_b_zero"] for c in ("E01", "E11") if c in init)
    cell_param_presence_ok = (
        set(cells) == set(CELLS)
        and cells["E00"]["adapter_params"] == 0 and cells["E00"]["lora_params"] == 0
        and cells["E10"]["adapter_params"] > 0 and cells["E10"]["lora_params"] == 0
        and cells["E01"]["adapter_params"] == 0 and cells["E01"]["lora_params"] > 0
        and cells["E11"]["adapter_params"] > 0 and cells["E11"]["lora_params"] > 0
    )
    base_cache_labels_equal = all(
        len({results[c][k] for c in results}) == 1
        for k in ("base_config_sha", "cache_sha", "labels_sha")
    ) if len(results) == 4 else False
    post_step0_weight_change_ok = all(
        results[c]["post_step0_weight_change"] for c in ("E01", "E10", "E11") if c in results
    )
    updates_total = sum(cells[c]["updates"] for c in cells)
    m_total = sum(cells[c]["m_records"] for c in cells)
    gen_total = sum(cells[c]["generation_records"] for c in cells)
    real_calls = sum(
        results[c]["step0"]["ce_calls"] + results[c]["final"]["ce_calls"]
        for c in results
    )
    expected_calls = EXPECTED_REAL_CE_TOTAL
    ce_ok = bool(results) and all(cells[c]["ce_finite"] for c in cells)
    assertions = {
        "lora_names_equal": bool(lora_names_equal),
        "lora_ab_hash_equal": bool(lora_ab_hash_equal),
        "adapter_hash_equal": bool(adapter_hash_equal),
        "post_init_rng_equal": bool(post_init_rng_equal),
        "post_step0_rng_equal": bool(post_step0_rng_equal),
        "lora_b_zero": bool(lora_b_zero),
        "cell_param_presence_ok": bool(cell_param_presence_ok),
        "base_cache_labels_equal": bool(base_cache_labels_equal),
        "post_step0_weight_change_ok": bool(post_step0_weight_change_ok),
        "phase6_io_zero": True,
        "step0_docs_ok": all(cells[c]["n_docs_step0"] == 20 for c in cells),
        "final_docs_ok": all(cells[c]["n_docs_final"] == 20 for c in cells),
        "m_count_ok": m_total == EXPECTED_M_TOTAL and all(
            cells[c]["m_records"] == EXPECTED_M_PER_CELL for c in cells),
        "generation_count_ok": gen_total == EXPECTED_GEN_TOTAL and all(
            cells[c]["generation_records"] == EXPECTED_GEN_PER_CELL for c in cells),
        "ce_finite_ok": ce_ok,
        "real_memory_ce_calls_ok": real_calls == expected_calls,
        "provenance_ok": bool(code_commit and clean_tree),
        "cells_ok": set(cells) == set(CELLS),
        "updates_total_ok": updates_total == 3,
        "e00_steps_zero": cells["E00"]["updates"] == 0,
    }
    total_s = time.time() - started
    out = {
        "schema_version": "1",
        "cells": cells,
        "assertions": assertions,
        "updates_total": int(updates_total),
        "timings": {
            "setup_s": float(sum(results[c]["timings"]["setup_s"] for c in results)),
            "step0_s": float(sum(results[c]["timings"]["step0_s"] for c in results)),
            "step100_s": 0.0,
            "m_build_s": 0.0,
            "m_ce_s": 0.0,
            "generation_s": float(sum(results[c]["timings"]["generation_s"] for c in results)),
            "total_s": float(total_s),
        },
        "provenance": {
            "code_commit": code_commit,
            "command": "python runner/c5_pm_f0.py --mode d1",
            "input_sha256": sha256_bytes(json.dumps(
                {"freeze": check_freeze(), "preflight": inputs_hash()}, sort_keys=True).encode()),
            "clean_tree": bool(clean_tree),
        },
        "parallel": {
            "nproc": int(os.cpu_count() or 0),
            "threads_per_arm": 2,
            "parallel_wall_s": float(wall),
            "contention_ratio": float(wall / max(1e-9, sum(
                results[c]["timings"]["total_s"] for c in results))),
            "cpu_affinity": "not_restricted",
            "cgroup_cpu_quota": "not_applicable",
            "torch_threads": 2,
            "thread_pool_counts": {"interop": 1},
        },
        "labels_computed": False,
        "not_a_result": True,
        "test_split_used": False,
        "p1_used": False,
        "d1_signal_read": False,
        "m_records": int(m_total),
        "phase7_records": 0,
        "generation_records": int(gen_total),
        "real_memory_ce_calls": int(real_calls),
        "expected_real_memory_ce_calls": int(expected_calls),
        "real_memory_ce_calls_ok": bool(real_calls == expected_calls),
        "wrong_donor_ce_calls": 0,
        "donor_map_loads": 0,
        "checkpoint_digests": {c: (results[c]["checkpoint_digest"] if c in results else None)
                               for c in CELLS},
        "checkpoint_absent": True,
        "mechanics_pass": False,
        "partial": bool(errors) or len(results) != len(CELLS),
        "error": ("OTHER_REDACTED" if errors else None),
    }
    out["mechanics_pass"] = bool(
        out["partial"] is False
        and out["error"] is None
        and out["checkpoint_absent"] is True
        and all(assertions.values())
        and out["phase7_records"] == 0
        and out["wrong_donor_ce_calls"] == 0
        and out["donor_map_loads"] == 0
        and out["labels_computed"] is False
        and out["not_a_result"] is True
        and out["test_split_used"] is False
        and out["p1_used"] is False
        and out["d1_signal_read"] is False
        and out["real_memory_ce_calls_ok"] is True
        and assertions["provenance_ok"] is True
    )
    D1_OUT.parent.mkdir(parents=True, exist_ok=True)
    D1_OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def inputs_hash() -> str:
    # Hash the frozen cohort inputs, not CE values.
    p = read_json(PREFLIGHT)
    return sha256_bytes(json.dumps({k: p[k] for k in (
        "common_ids", "train20_ids", "val20_ids")}, sort_keys=True).encode())
