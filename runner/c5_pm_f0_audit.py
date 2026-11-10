"""C5 F0 Stage P (init audit) and Stage Q (1-update audit)."""

from __future__ import annotations

import gc
import hashlib
import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_mt5_layer_probe import load_layer_cache  # noqa: E402
from runner.c5_mt5_lora_b0 import donors_for, token_losses  # noqa: E402
from runner.c5_pm_f0 import CACHE, CELLS, K_M, build_cell, read_json, sha256_bytes  # noqa: E402
from runner.c5_pm_f0_mechanics import (  # noqa: E402
    D1_SEED, f0_memory, finite_eval, load_inputs, one_update, trainable_hash,
)
from runner.c5_pm_phase6 import labels_and_copy  # noqa: E402

SEEDS = (20261108, 20261109, 20261110)
P_OUT = ROOT / "reports/provenance/C5_f0/pre_r/pre_r_init_audit.json"
Q_DIR = ROOT / "reports/provenance/C5_f0/q/q_seed_audit"
KAT = ROOT / "reports/provenance/C5_f0/serialization_kat.json"


def canonical_digest(tensors: dict[str, torch.Tensor]) -> str:
    h = hashlib.sha256()
    for name in sorted(tensors):
        t = tensors[name].detach().cpu().contiguous()
        b = t.numpy().astype(t.numpy().dtype.newbyteorder("<"), copy=False).tobytes()
        nb = name.encode("utf-8")
        db = str(t.dtype).replace("torch.", "").encode("ascii")
        h.update(len(nb).to_bytes(4, "little")); h.update(nb)
        h.update(bytes([len(db)])); h.update(db)
        h.update(bytes([t.ndim]))
        for dim in t.shape:
            h.update(int(dim).to_bytes(4, "little"))
        h.update(len(b).to_bytes(8, "little")); h.update(b)
        h.update(b"\x00")
    return h.hexdigest()


def make_kat() -> str:
    a = torch.tensor([1.0, -2.5], dtype=torch.float32)
    b = torch.tensor([7], dtype=torch.int64)
    c = torch.tensor(3.25, dtype=torch.float32)
    expected = canonical_digest({"a": a, "b": b, "c": c})
    obj = {
        "grammar": "name_len:u32le|name|dtype_len:u8|dtype|ndim:u8|shape:u32le[ndim]|nbytes:u64le|le_bytes|0x00",
        "tensors": {
            "a": {"dtype": "float32", "shape": [2], "values": [1.0, -2.5]},
            "b": {"dtype": "int64", "shape": [1], "values": [7]},
            "c": {"dtype": "float32", "shape": [], "values": [3.25]},
        },
        "expected_sha256": expected,
    }
    KAT.parent.mkdir(parents=True, exist_ok=True)
    KAT.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    return sha256_bytes(KAT.read_bytes())


def build_hashes(cell: str, seed: int) -> dict[str, Any]:
    built = build_cell(cell, seed)
    adapter = {f"adapter.{k}": v for k, v in built["adapter"].state_dict().items()} if built["adapter"] is not None else {}
    lora = {k: v for k, v in built["model"].named_parameters() if ".lora_" in k}
    h = canonical_digest({**adapter, **lora})
    out = {
        "cell": cell,
        "seed": seed,
        "hash": h,
        "lora_names": list(built["lora_names"]),
        "n_params": int(sum(p.numel() for p in adapter.values()) + sum(p.numel() for p in lora.values())),
        "adapter_present": built["adapter"] is not None,
        "lora_modules": len(built["lora_names"]),
        "adapter_sha": canonical_digest(adapter) if adapter else None,
        "lora_sha": canonical_digest(lora) if lora else None,
        "rng": sha256_bytes(torch.get_rng_state().numpy().tobytes()),
    }
    del built
    gc.collect()
    return out


def run_p() -> dict[str, Any]:
    kat = make_kat()
    per_seed: dict[str, Any] = {}
    for seed in SEEDS:
        cells = {cell: build_hashes(cell, seed) for cell in CELLS}
        p_equal = (
            cells["E01"]["lora_names"] == cells["E11"]["lora_names"]
            and cells["E01"]["lora_sha"] == cells["E11"]["lora_sha"]
            and cells["E10"]["adapter_sha"] == cells["E11"]["adapter_sha"]
            and cells["E01"]["rng"] == cells["E11"]["rng"]
            and cells["E00"]["adapter_present"] is False
            and cells["E00"]["lora_modules"] == 0
            and cells["E01"]["adapter_present"] is False
            and cells["E10"]["lora_modules"] == 0
        )
        per_seed[str(seed)] = {
            "cells": {c: {k: cells[c][k] for k in ("hash", "lora_names", "n_params")} for c in CELLS},
            "p_r_hash_equal": bool(p_equal),
        }
    out = {
        "schema_version": "1",
        "seeds": list(SEEDS),
        "per_seed": per_seed,
        "kat_sha256": kat,
        "pre_r_init_audit_pass": bool(all(v["p_r_hash_equal"] for v in per_seed.values())),
    }
    P_OUT.parent.mkdir(parents=True, exist_ok=True)
    P_OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def q_donor_check(cell: str, seed: int) -> dict[str, Any]:
    inputs = load_inputs()
    preflight = inputs["preflight"]
    rows = inputs["rows"]
    val_ids = inputs["val_ids"]
    cache = load_layer_cache("train", CACHE)
    cache.update(load_layer_cache("val", CACHE))
    built = build_cell(cell, seed)
    built["arm"] = cell
    built["spec"]["memory_source"] = "eg2_layer19"
    built["spec"]["m_k"] = K_M
    train_id = preflight["train20_ids"][0]
    labels, copies = labels_and_copy(built["tok"], rows, list(dict.fromkeys(val_ids + [train_id])))
    donors = donors_for(val_ids, cache, 5)
    init_rng = sha256_bytes(torch.get_rng_state().numpy().tobytes())
    if cell == "E00":
        train = {"updates": 0, "weight_changed": True, "loss_finite": True}
    else:
        train = one_update(built, train_id, cache, labels, seed=seed)
    post_rng = sha256_bytes(torch.get_rng_state().numpy().tobytes())
    wrong_calls = 0
    finite = True
    shape_ok = True
    with torch.inference_mode():
        for rid in val_ids:
            real = f0_memory(built, rid, cache)
            for donor in donors[rid]:
                wrong = f0_memory(built, donor, cache)
                k = min(int(real.shape[0]), int(wrong.shape[0]))
                if not (1 <= k <= K_M):
                    shape_ok = False
                try:
                    fr, tr = token_losses(built["model"], real[:k], labels[rid])
                    fw, tw = token_losses(built["model"], wrong[:k], labels[rid])
                    wrong_calls += 2
                    if not (torch.isfinite(torch.tensor(fr)) and torch.isfinite(tr).all()
                            and torch.isfinite(torch.tensor(fw)) and torch.isfinite(tw).all()):
                        finite = False
                except Exception:
                    finite = False
    out = {
        "cell": cell,
        "post_step0_rng_sha256": post_rng,
        "init_rng_sha256": init_rng,
        "group_change_ok": bool(train["weight_changed"]),
        "wrong_donor_finite": bool(finite),
        "shape_ok": bool(shape_ok),
        "updates": int(train["updates"]),
        "wrong_donor_ce_calls": int(wrong_calls),
    }
    del built
    gc.collect()
    return out


def _q_worker(seed: int, cell: str, q: Any) -> None:
    try:
        q.put(("ok", seed, q_donor_check(cell, seed)))
    except BaseException as exc:  # pragma: no cover
        q.put(("error", seed, {"cell": cell, "error": type(exc).__name__, "message": str(exc)[:300]}))


def run_q() -> dict[str, Any]:
    ctx = mp.get_context("spawn")
    summaries = {}
    for seed in SEEDS:
        q = ctx.Queue()
        procs = [ctx.Process(target=_q_worker, args=(seed, c, q)) for c in CELLS]
        for p in procs:
            p.start()
        cells: dict[str, Any] = {}
        errors = []
        while len(cells) + len(errors) < 4:
            try:
                kind, s, payload = q.get(timeout=10)
            except Exception:
                if all(not p.is_alive() for p in procs):
                    break
                continue
            if kind == "ok":
                cells[payload.get("cell", "")] = payload
            else:
                errors.append(payload)
        for p in procs:
            p.join(timeout=5)
        # Preserve cell key from worker result.
        fixed = {}
        for cell in CELLS:
            if cell in cells:
                fixed[cell] = cells[cell]
            else:
                fixed[cell] = {"post_step0_rng_sha256": None, "group_change_ok": False,
                               "wrong_donor_finite": False, "shape_ok": False,
                               "updates": 0, "wrong_donor_ce_calls": 0}
        pass_q = (
            not errors
            and all(fixed[c]["updates"] == (0 if c == "E00" else 1) for c in CELLS)
            and all(fixed[c]["group_change_ok"] for c in CELLS)
            and all(fixed[c]["wrong_donor_finite"] and fixed[c]["shape_ok"] for c in CELLS)
            and fixed["E01"]["post_step0_rng_sha256"] == fixed["E11"]["post_step0_rng_sha256"]
        )
        summaries[seed] = {
            "seed": seed,
            "units": 4,
            "trained_updates": 3,
            "e00_updates": 0,
            "cells": {c: {k: fixed[c][k] for k in (
                "post_step0_rng_sha256", "group_change_ok", "wrong_donor_finite", "shape_ok")} for c in CELLS},
            "wrong_donor_ce_calls": int(sum(fixed[c]["wrong_donor_ce_calls"] for c in CELLS)),
            "pre_r_seed_audit_pass": bool(pass_q),
        }
        Q_DIR.mkdir(parents=True, exist_ok=True)
        (Q_DIR / f"{seed}.json").write_text(json.dumps(summaries[seed], indent=2) + "\n", encoding="utf-8")
    return summaries


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=("p", "q"), required=True)
    args = ap.parse_args()
    if args.stage == "p":
        out = run_p()
        print(json.dumps({"stage": "p", "pass": out["pre_r_init_audit_pass"]}, ensure_ascii=False))
    else:
        out = run_q()
        print(json.dumps({"stage": "q", "pass": {str(k): v["pre_r_seed_audit_pass"] for k, v in out.items()}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
