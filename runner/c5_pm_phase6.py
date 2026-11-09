"""C5 Phase 6 entrypoint (frozen v1.0.11).

The Phase 6 path is deliberately self-contained: it owns training and
evaluation loops and never imports ``train_arm`` or ``evaluate_arm`` from the
B0 runner.  This file currently implements the approved D0 zero-update
mechanics gate.  D1 and the registered run remain gated on separate approval.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_mt5_layer_probe import Adapter, load_layer_cache  # noqa: E402
from runner.c5_mt5_lora_b0 import (  # noqa: E402
    attach_decoder_lora_mt5,
    load_base,
    native_memory,
    native_source_ids,
)

MODEL = ROOT / "data/models/mt5-small"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
CACHE = ROOT / "data/wave2c/eg2_native_layer19/layer19"
PREFLIGHT = ROOT / "reports/provenance/C5_b0a/m_cohort_preflight.json"
P1_USAGE = ROOT / "reports/provenance/C5_b0a/p1_usage.json"
FREEZE = ROOT / "docs/plan_c5_b0a_pm_prereg_v1_0_11_FREEZE.json"
FREEZE_COMMIT_TXT = ROOT / "reports/provenance/C5_b0a/freeze_manifest_commit.txt"
D0_OUT = ROOT / "reports/provenance/C5_b0a/d0/d0_report.json"

D0_SEED = 20261111
REGISTERED_SEEDS = (20261108, 20261109, 20261110)
EXPECTED_LORA_MODULES = 64
SOURCE_PREFIX = "summarize: "
SOURCE_MAX_LENGTH = 512
K_M_L = 753
K_M_NATIVE = 512
ARMS = ("F", "L", "P", "PA")


class NotApprovedError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl_by_id(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        out[str(row["id"])] = row
    return out


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def committed_blob_sha256(commit: str, path: str) -> str:
    data = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=str(ROOT))
    return sha256_bytes(data)


def load_frozen_inputs() -> dict[str, Any]:
    preflight = read_json(PREFLIGHT)
    splits = read_json(SPLITS)
    p1 = read_json(P1_USAGE)
    freeze = read_json(FREEZE)
    rows = read_jsonl_by_id(DATA)
    train_ids = list(preflight["train20_ids"])
    val_ids = list(preflight["val20_ids"])
    allowed = set(train_ids) | set(val_ids)
    missing = [rid for rid in allowed if rid not in rows]
    if missing:
        raise RuntimeError(f"missing F5 rows for preflight IDs: {missing[:5]}")
    if p1.get("p1_used") is not False or p1.get("test_split_read") is not False:
        raise RuntimeError("P1 usage manifest is not clean")
    if freeze.get("status") != "frozen":
        raise RuntimeError("freeze manifest is not frozen")
    if freeze.get("plan_path") != "docs/plan_c5_b0a_pm_prereg_v1_0_11.md":
        raise RuntimeError("freeze manifest plan path mismatch")
    return {
        "preflight": preflight,
        "splits": splits,
        "p1": p1,
        "freeze": freeze,
        "rows": rows,
        "train_ids": train_ids,
        "val_ids": val_ids,
        "allowed_ids": allowed,
    }


def assert_allowed_ids(ids: list[str], allowed: set[str]) -> None:
    bad = sorted(set(ids) - allowed)
    if bad:
        raise RuntimeError(f"IDs outside frozen train20/val20 allowlist: {bad[:5]}")


def arm_spec(arm: str) -> dict[str, Any]:
    if arm not in ARMS:
        raise ValueError(f"unknown arm: {arm}")
    return {
        "arm": arm,
        "memory_source": "eg2_layer19" if arm in {"F", "L"} else "native_mt5",
        "m_k": K_M_L if arm in {"F", "L"} else K_M_NATIVE,
        "adapter": arm != "P",
        "lora": arm in {"L", "P", "PA"},
        "trainable": (
            "adapter" if arm == "F"
            else "adapter+lora" if arm in {"L", "PA"}
            else "lora"
        ),
    }


def build_arm(arm: str, seed: int) -> dict[str, Any]:
    """Build one fresh arm.  RNG order: seed, adapter, then LoRA."""
    spec = arm_spec(arm)
    tok, model = load_base()
    # RNG order is frozen: load weights first, then seed, then adapter, then LoRA.
    torch.manual_seed(int(seed))
    adapter = None
    if spec["adapter"]:
        adapter = Adapter(512, 512)
    lora_names: list[str] = []
    if spec["lora"]:
        lora_names = attach_decoder_lora_mt5(model)
    if spec["lora"] and len(lora_names) != EXPECTED_LORA_MODULES:
        raise RuntimeError(f"{arm}: unexpected LoRA module count {len(lora_names)}")

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
        raise RuntimeError(f"{arm}: frozen base has trainable parameters: {trainable_base[:3]}")
    if adapter is not None and not all(p.requires_grad for p in adapter.parameters()):
        raise RuntimeError(f"{arm}: adapter has frozen parameters")
    if spec["lora"] and not any(p.requires_grad for _, p in model.named_parameters() if ".lora_" in _):
        raise RuntimeError(f"{arm}: LoRA has no trainable parameters")

    return {
        "arm": arm,
        "spec": spec,
        "tok": tok,
        "model": model,
        "adapter": adapter,
        "lora_names": lora_names,
        "trainable_adapter": sum(
            p.numel() for p in adapter.parameters() if p.requires_grad
        ) if adapter is not None else 0,
        "trainable_lora": sum(
            p.numel() for name, p in model.named_parameters()
            if ".lora_" in name and p.requires_grad
        ),
        "mode": {
            "base_decoder": "eval",
            "adapter": "eval" if adapter is not None else "absent",
            "lora": "eval" if spec["lora"] else "absent",
        },
    }


def assert_cache_lengths(cache: dict[str, dict], preflight: dict[str, Any]) -> None:
    for split, ids_key, len_key in (
        ("train", "train20_ids", "train_h_lengths"),
        ("val", "val20_ids", "val_h_lengths"),
    ):
        for rid in preflight[ids_key]:
            if rid not in cache:
                raise RuntimeError(f"missing EG2 cache row: {split}/{rid}")
            expected = int(preflight[len_key][rid])
            actual = int(cache[rid]["length"])
            if actual != expected:
                raise RuntimeError(
                    f"EG2 h_len mismatch {split}/{rid}: {actual} != {expected}"
                )


def assert_native_lengths(tok, rows: dict[str, dict], ids: list[str]) -> None:
    for rid in ids:
        ids_out = native_source_ids(tok, rows[rid]["passage"], SOURCE_MAX_LENGTH)
        if len(ids_out) != SOURCE_MAX_LENGTH:
            raise RuntimeError(f"native source length {rid}: {len(ids_out)} != {SOURCE_MAX_LENGTH}")


def memory_probe(arm: str, built: dict[str, Any], cache: dict[str, dict], rows: dict[str, dict], preflight: dict[str, Any]) -> dict[str, Any]:
    spec = built["spec"]
    if spec["memory_source"] == "eg2_layer19":
        rid = next(
            rid for rid in preflight["train20_ids"]
            if int(preflight["train_h_lengths"][rid]) >= K_M_L
        )
        h = cache[rid]["h"]
        memory = built["adapter"](h) if built["adapter"] is not None else h
        memory = memory[:K_M_L]
    else:
        rid = preflight["train20_ids"][0]
        ids_out = native_source_ids(built["tok"], rows[rid]["passage"], SOURCE_MAX_LENGTH)
        memory = native_memory(built["model"], ids_out)
        if len(ids_out) != K_M_NATIVE:
            raise RuntimeError(f"native probe length {len(ids_out)} != {K_M_NATIVE}")
        if built["adapter"] is not None:
            memory = built["adapter"](memory)
        memory = memory[:K_M_NATIVE]
    if tuple(memory.shape) != (spec["m_k"], 512):
        raise RuntimeError(f"{arm}: memory probe shape {tuple(memory.shape)} != ({spec['m_k']}, 512)")
    if not torch.isfinite(memory).all():
        raise RuntimeError(f"{arm}: non-finite memory probe")
    return {"doc_id": rid, "shape": list(memory.shape)}


def freeze_record() -> dict[str, Any]:
    freeze = read_json(FREEZE)
    commit = FREEZE_COMMIT_TXT.read_text(encoding="utf-8").strip()
    if not commit:
        raise RuntimeError("freeze_manifest_commit.txt is empty")
    manifest_sha = committed_blob_sha256(commit, "docs/plan_c5_b0a_pm_prereg_v1_0_11_FREEZE.json")
    return {
        "manifest_path": "docs/plan_c5_b0a_pm_prereg_v1_0_11_FREEZE.json",
        "freeze_commit": freeze["freeze_commit"],
        "manifest_commit": commit,
        "freeze_manifest_sha256": manifest_sha,
        "plan_sha256": freeze["plan_sha256"],
        "p1_manifest_sha256": freeze["p1_manifest_sha256"],
        "golden_sha256": freeze["golden_sha256"],
        "preflight_sha256": freeze["preflight_sha256"],
    }


def d0_flags() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "experiment": "C5 Phase 6 P/M",
        "mode": "d0_zero_update",
        "updates": 0,
        "seed": D0_SEED,
        "registered_seed_used": False,
        "labels_computed": False,
        "not_a_result": True,
        "test_split_used": False,
        "p1_used": False,
    }


def run_d0() -> dict[str, Any]:
    inputs = load_frozen_inputs()
    preflight = inputs["preflight"]
    rows = inputs["rows"]
    assert_allowed_ids(inputs["train_ids"] + inputs["val_ids"], inputs["allowed_ids"])

    if inputs["freeze"]["plan_sha256"] != committed_blob_sha256(
        inputs["freeze"]["freeze_commit"],
        "docs/plan_c5_b0a_pm_prereg_v1_0_11.md",
    ):
        raise RuntimeError("plan SHA mismatch against freeze commit")

    cache = load_layer_cache("train", CACHE)
    val_cache = load_layer_cache("val", CACHE)
    cache.update(val_cache)
    assert_cache_lengths(cache, preflight)

    records: dict[str, Any] = {}
    tok = None
    for arm in ARMS:
        built = build_arm(arm, D0_SEED)
        tok = built["tok"]
        assert_native_lengths(tok, rows, inputs["train_ids"])
        assert_native_lengths(tok, rows, inputs["val_ids"])
        record = {
            "arm": arm,
            "spec": built["spec"],
            "updates": 0,
            "adapter_present": built["adapter"] is not None,
            "lora_modules": len(built["lora_names"]),
            "trainable_adapter_parameters": int(built["trainable_adapter"]),
            "trainable_lora_parameters": int(built["trainable_lora"]),
            "mode": built["mode"],
            "memory_probe": memory_probe(arm, built, cache, rows, preflight),
            "cache_h_length_ok": True,
            "native_length_ok": True,
        }
        records[arm] = record
        del built
        gc.collect()

    out = {
        **d0_flags(),
        "configs": len(records),
        "arms": records,
        "freeze": freeze_record(),
    }
    D0_OUT.parent.mkdir(parents=True, exist_ok=True)
    D0_OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("d0", "d1", "registered"), default="d0")
    args = ap.parse_args()
    if args.mode == "d0":
        out = run_d0()
        print(json.dumps({"mode": out["mode"], "configs": out["configs"], "arms": sorted(out["arms"])}, ensure_ascii=False))
        return 0
    raise NotApprovedError(
        f"{args.mode} is outside the current approval; D0 only. "
        "D1 and registered execution require separate approval."
    )


if __name__ == "__main__":
    raise SystemExit(main())
