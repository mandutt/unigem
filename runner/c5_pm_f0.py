"""C5 F0 runner — D0 mechanics only.

The F0 consolidated spec freezes four cells:
E00 (raw), E10 (adapter), E01 (LoRA), E11 (adapter + LoRA).
This module deliberately implements only the zero-update D0 gate.  D1 and the
registered/R stages remain blocked on separate approvals.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_mt5_layer_probe import Adapter, load_layer_cache  # noqa: E402
from runner.c5_mt5_lora_b0 import attach_decoder_lora_mt5, load_base  # noqa: E402

PREFLIGHT = ROOT / "reports/provenance/C5_b0a/m_cohort_preflight.json"
CACHE = ROOT / "data/wave2c/eg2_native_layer19/layer19"
P1_USAGE = ROOT / "reports/provenance/C5_b0a/p1_usage.json"
FREEZE = ROOT / "docs/plan_c5_f0_CONSOLIDATED_v1_0_FREEZE.json"
PLAN = ROOT / "docs/plan_c5_f0_CONSOLIDATED_v1_0_2026-11-10.md"
ANNEX = ROOT / "docs/plan_c5_f0_v1_13_2026-11-09.md"
OUT = ROOT / "reports/provenance/C5_f0/d0/f0_d0.json"
INIT_HASHES = ROOT / "reports/provenance/C5_f0/d0/init_hashes.json"

CELLS = ("E00", "E10", "E01", "E11")
D0_SEED = 20261111
K_M = 753
EXPECTED_LORA_MODULES = 64
LORA_SEED_XOR = 0x5EED10A5


class NotApprovedError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def cell_spec(cell: str) -> dict[str, Any]:
    if cell not in CELLS:
        raise ValueError(f"unknown F0 cell: {cell}")
    adapter = cell in {"E10", "E11"}
    lora = cell in {"E01", "E11"}
    return {
        "cell": cell,
        "adapter": adapter,
        "lora": lora,
        "updates_d0": 0,
        "updates_d1": 0 if cell == "E00" else 1,
        "trainable": (
            "none" if not adapter and not lora
            else "adapter" if adapter and not lora
            else "lora" if lora and not adapter
            else "adapter+lora"
        ),
    }


def tensor_sha256(tensors: dict[str, torch.Tensor]) -> str:
    h = hashlib.sha256()
    for name in sorted(tensors):
        t = tensors[name].detach().cpu().contiguous()
        h.update(name.encode("utf-8"))
        h.update(b"\0")
        h.update(str(t.dtype).encode("ascii"))
        h.update(b"\0")
        h.update(str(tuple(t.shape)).encode("ascii"))
        h.update(b"\0")
        h.update(t.numpy().tobytes())
        h.update(b"\0")
    return h.hexdigest()


def build_cell(cell: str, seed: int) -> dict[str, Any]:
    spec = cell_spec(cell)
    tok, model = load_base()

    # Frozen RNG order: load base, seed, adapter, optional LoRA reset.
    torch.manual_seed(int(seed))
    adapter = Adapter(512, 512) if spec["adapter"] else None
    lora_names: list[str] = []
    if spec["lora"]:
        torch.manual_seed((int(seed) ^ LORA_SEED_XOR) & 0xFFFFFFFF)
        lora_names = attach_decoder_lora_mt5(model)
    if spec["lora"] and len(lora_names) != EXPECTED_LORA_MODULES:
        raise RuntimeError(f"{cell}: unexpected LoRA module count {len(lora_names)}")

    model.eval()
    if adapter is not None:
        adapter.eval()
    for module in model.modules():
        if module.__class__.__name__ == "LoRALinear":
            module.eval()
            module.base.eval()

    trainable_base = [
        name for name, p in model.named_parameters()
        if p.requires_grad and ".lora_" not in name
    ]
    if trainable_base:
        raise RuntimeError(f"{cell}: frozen base has trainable parameters: {trainable_base[:3]}")
    if adapter is not None and not all(p.requires_grad for p in adapter.parameters()):
        raise RuntimeError(f"{cell}: adapter has frozen parameters")
    if spec["lora"] and not any(
        p.requires_grad for name, p in model.named_parameters() if ".lora_" in name
    ):
        raise RuntimeError(f"{cell}: LoRA has no trainable parameters")

    adapter_tensors = {
        name: p for name, p in (adapter.named_parameters() if adapter is not None else [])
    }
    lora_tensors = {
        name: p for name, p in model.named_parameters() if ".lora_" in name
    }
    return {
        "cell": cell,
        "spec": spec,
        "tok": tok,
        "model": model,
        "adapter": adapter,
        "lora_names": lora_names,
        "adapter_tensors": adapter_tensors,
        "lora_tensors": lora_tensors,
        "rng_after_init": sha256_bytes(torch.get_rng_state().numpy().tobytes()),
        "adapter_sha256": tensor_sha256(adapter_tensors) if adapter_tensors else None,
        "lora_sha256": tensor_sha256(lora_tensors) if lora_tensors else None,
        "trainable_adapter": sum(p.numel() for p in adapter_tensors.values()),
        "trainable_lora": sum(p.numel() for p in lora_tensors.values()),
    }


def memory_probe(built: dict[str, Any], cache: dict[str, dict], common_ids: list[str]) -> dict[str, Any]:
    rid = next((x for x in common_ids if int(cache[x]["length"]) >= K_M), None)
    if rid is None:
        raise RuntimeError("no common document reaches K_M")
    h = cache[rid]["h"]
    if built["adapter"] is not None:
        h = built["adapter"](h)
    memory = h[:K_M]
    if tuple(memory.shape) != (K_M, 512):
        raise RuntimeError(f"{built['cell']}: memory shape {tuple(memory.shape)} != ({K_M},512)")
    if not torch.isfinite(memory).all():
        raise RuntimeError(f"{built['cell']}: non-finite memory")
    return {"doc_id": rid, "shape": list(memory.shape), "finite": True}


def check_freeze() -> dict[str, Any]:
    freeze = read_json(FREEZE)
    if freeze.get("status") != "owner_approved_unreviewed":
        raise RuntimeError("F0 freeze status is not owner_approved_unreviewed")
    for key, path in (("plan_sha256", PLAN), ("annex_sha256", ANNEX)):
        if sha256_bytes(path.read_bytes()) != freeze[key]:
            raise RuntimeError(f"F0 freeze hash mismatch: {key}")
    return freeze


def run_d0() -> dict[str, Any]:
    freeze = check_freeze()
    preflight = read_json(PREFLIGHT)
    p1 = read_json(P1_USAGE)
    if p1.get("p1_used") is not False or p1.get("test_split_read") is not False:
        raise RuntimeError("P1 usage manifest is not clean")
    common_ids = list(preflight["common_ids"])
    if len(common_ids) != 15:
        raise RuntimeError(f"expected 15 common ids, got {len(common_ids)}")

    train_cache = load_layer_cache("train", CACHE)
    val_cache = load_layer_cache("val", CACHE)
    train_cache.update(val_cache)
    for rid in common_ids:
        if rid not in train_cache:
            raise RuntimeError(f"missing cache row for common id: {rid}")
        if int(train_cache[rid]["length"]) < K_M:
            raise RuntimeError(f"common id below K_M: {rid}")

    cells: dict[str, Any] = {}
    init_hashes: dict[str, Any] = {}
    for cell in CELLS:
        built = build_cell(cell, D0_SEED)
        record = {
            "cell": cell,
            "spec": built["spec"],
            "updates": 0,
            "adapter_present": built["adapter"] is not None,
            "lora_modules": len(built["lora_names"]),
            "trainable_adapter_parameters": int(built["trainable_adapter"]),
            "trainable_lora_parameters": int(built["trainable_lora"]),
            "memory_probe": memory_probe(built, train_cache, common_ids),
            "mode": {
                "base_decoder": "eval",
                "adapter": "eval" if built["adapter"] is not None else "absent",
                "lora": "eval" if built["lora_names"] else "absent",
            },
        }
        cells[cell] = record
        init_hashes[cell] = {
            "rng_after_init": built["rng_after_init"],
            "adapter_sha256": built["adapter_sha256"],
            "lora_sha256": built["lora_sha256"],
            "lora_modules": len(built["lora_names"]),
        }
        del built
        gc.collect()

    out = {
        "schema_version": 1,
        "experiment": "C5 F0",
        "mode": "d0_zero_update",
        "updates": 0,
        "seed": D0_SEED,
        "cells_count": len(cells),
        "cells": cells,
        "common_ids_count": len(common_ids),
        "labels_computed": False,
        "not_a_result": True,
        "test_split_used": False,
        "p1_used": False,
        "freeze": {
            "status": freeze["status"],
            "plan_sha256": freeze["plan_sha256"],
            "annex_sha256": freeze["annex_sha256"],
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    INIT_HASHES.write_text(json.dumps(init_hashes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("d0",), required=True)
    args = ap.parse_args()
    if args.mode == "d0":
        out = run_d0()
        print(json.dumps({
            "mode": out["mode"],
            "cells": sorted(out["cells"]),
            "output": str(OUT.relative_to(ROOT)),
        }, ensure_ascii=False))
        return 0
    raise NotApprovedError(f"mode not implemented: {args.mode}")


if __name__ == "__main__":
    raise SystemExit(main())
