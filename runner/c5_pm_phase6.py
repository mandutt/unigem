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
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from transformers.modeling_outputs import BaseModelOutput

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_mt5_layer_probe import Adapter, load_layer_cache, make_labels  # noqa: E402
from runner.c5_mt5_lora_b0 import (  # noqa: E402
    attach_decoder_lora_mt5,
    copy_ce,
    copyable_mask,
    donors_for,
    generation_record,
    load_base,
    native_memory,
    native_source_ids,
    token_losses,
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



D1_OUT = ROOT / "reports/provenance/C5_b0a/d1/d1_report.json"
D1_M_RECORDS = ROOT / "reports/provenance/C5_b0a/d1/m_records.json"
CHECKPOINTS = ROOT / "reports/provenance/C5_b0a/checkpoints"
CONTROL_MANIFEST = ROOT / "reports/provenance/C5_b0a/control_manifest"
D1_SEED = 20261111


def set_arm_training(built: dict[str, Any], train: bool) -> dict[str, Any]:
    model = built["model"]
    adapter = built["adapter"]
    model.eval()
    if adapter is not None:
        adapter.train(train)
    modules = [
        model.get_submodule(name)
        for name in built["lora_names"]
    ]
    for module in modules:
        module.train(train)
        module.base.eval()
    return {
        "base_decoder": "eval",
        "adapter": "train" if (adapter is not None and train) else ("eval" if adapter is not None else "absent"),
        "lora": "train" if (modules and train) else ("eval" if modules else "absent"),
    }


def train_forward_loss(model, memory: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    enc = BaseModelOutput(last_hidden_state=memory.unsqueeze(0))
    mask = torch.ones(1, memory.shape[0], dtype=torch.long)
    out = model(encoder_outputs=enc, attention_mask=mask, labels=labels)
    return out.loss


def optimizer_for(built: dict[str, Any]) -> torch.optim.Optimizer:
    groups = []
    if built["adapter"] is not None:
        groups.append({"params": [p for p in built["adapter"].parameters() if p.requires_grad], "lr": 1e-3})
    lora = [p for name, p in built["model"].named_parameters() if ".lora_" in name and p.requires_grad]
    if lora:
        groups.append({"params": lora, "lr": 1e-4})
    if not groups:
        raise RuntimeError(f"{built['arm']}: no trainable parameters")
    return torch.optim.AdamW(groups, weight_decay=0.01)


def native_cache_for(model, tok, rows: dict[str, dict], ids: list[str]) -> dict[str, torch.Tensor]:
    out: dict[str, torch.Tensor] = {}
    # no_grad, not inference_mode: PA/P use this tensor in a backward pass.
    with torch.no_grad():
        for rid in ids:
            ids_out = native_source_ids(tok, rows[rid]["passage"], SOURCE_MAX_LENGTH)
            if len(ids_out) != SOURCE_MAX_LENGTH:
                raise RuntimeError(f"native source length {rid}: {len(ids_out)}")
            out[rid] = native_memory(model, ids_out)
    return out


def memory_for(
    built: dict[str, Any],
    rid: str,
    cache: dict[str, dict],
    native: dict[str, torch.Tensor],
) -> torch.Tensor:
    if built["spec"]["memory_source"] == "eg2_layer19":
        h = cache[rid]["h"]
        return built["adapter"](h) if built["adapter"] is not None else h
    h = native[rid]
    return built["adapter"](h) if built["adapter"] is not None else h


def donor_map(lengths: dict[str, int], ids: list[str], count: int = 5) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for rid in ids:
        candidates = [x for x in ids if x != rid]
        candidates.sort(key=lambda x: (abs(lengths[x] - lengths[rid]), x))
        out[rid] = candidates[:count]
    return out


def labels_and_copy(
    tok,
    rows: dict[str, dict],
    ids: list[str],
) -> tuple[dict[str, torch.Tensor], dict[str, torch.Tensor]]:
    labels: dict[str, torch.Tensor] = {}
    copies: dict[str, torch.Tensor] = {}
    special = {int(x) for x in tok.all_special_ids}
    for rid in ids:
        lab = make_labels(tok, rows[rid]["summary"], 256)
        labels[rid] = lab
        mask, _ = copyable_mask(rows[rid]["passage"], lab[0].tolist(), tok, special)
        copies[rid] = mask
    return labels, copies


def eval_arm_d1(
    built: dict[str, Any],
    ids: list[str],
    cache: dict[str, dict],
    native: dict[str, torch.Tensor],
    rows: dict[str, dict],
    labels: dict[str, torch.Tensor],
    copies: dict[str, torch.Tensor],
    donors: dict[str, list[str]],
) -> dict[str, Any]:
    set_arm_training(built, False)
    per_doc: dict[str, Any] = {}
    with torch.inference_mode():
        for rid in ids:
            real = memory_for(built, rid, cache, native)
            lab = labels[rid]
            mask = copies[rid]
            real_copy: list[float] = []
            wrong_copy: list[float] = []
            real_full: list[float] = []
            wrong_full: list[float] = []
            for donor in donors[rid]:
                wrong = memory_for(built, donor, cache, native)
                k = min(int(real.shape[0]), int(wrong.shape[0]))
                mem_real = real[:k]
                mem_wrong = wrong[:k]
                fr, tr = token_losses(built["model"], mem_real, lab)
                fw, tw = token_losses(built["model"], mem_wrong, lab)
                rc = copy_ce(tr, lab, mask)
                wc = copy_ce(tw, lab, mask)
                if rc is not None and wc is not None:
                    real_copy.append(rc)
                    wrong_copy.append(wc)
                real_full.append(fr)
                wrong_full.append(fw)
            if not real_copy:
                continue
            per_doc[rid] = {
                "n_donors": len(real_copy),
                "real_ce_copy": float(np.mean(real_copy)),
                "wrong_ce_copy": float(np.mean(wrong_copy)),
                "delta_shuffled_copy": float(np.mean(np.asarray(wrong_copy) - np.asarray(real_copy))),
                "real_ce_full": float(np.mean(real_full)),
                "wrong_ce_full": float(np.mean(wrong_full)),
                "delta_shuffled_full": float(np.mean(np.asarray(wrong_full) - np.asarray(real_full))),
                "copy_tokens": int(mask.sum()),
                "copy_coverage": float(mask.sum()) / max(1, int(mask.numel())),
            }
    values = list(per_doc.values())
    if not values:
        return {"n_docs": 0, "error": "no copyable target token document"}
    return {
        "n_docs": len(values),
        "mean_delta_shuffled_copy": float(np.mean([x["delta_shuffled_copy"] for x in values])),
        "mean_delta_shuffled_full": float(np.mean([x["delta_shuffled_full"] for x in values])),
        "mean_real_ce_copy": float(np.mean([x["real_ce_copy"] for x in values])),
        "mean_wrong_ce_copy": float(np.mean([x["wrong_ce_copy"] for x in values])),
        "mean_copy_coverage": float(np.mean([x["copy_coverage"] for x in values])),
        "median_copy_coverage": float(np.median([x["copy_coverage"] for x in values])),
        "per_doc": per_doc,
    }


def train_one_update(
    built: dict[str, Any],
    rows: dict[str, dict],
    cache: dict[str, dict],
    native: dict[str, torch.Tensor],
    rid: str,
) -> dict[str, Any]:
    set_arm_training(built, True)
    memory = memory_for(built, rid, cache, native)
    labels = make_labels(built["tok"], rows[rid]["summary"], 256)
    opt = optimizer_for(built)
    opt.zero_grad(set_to_none=True)
    loss = train_forward_loss(built["model"], memory, labels)
    if not torch.isfinite(loss):
        raise RuntimeError(f"{built['arm']}: non-finite training loss")
    loss.backward()
    params = [p for p in built["model"].parameters() if p.requires_grad]
    if built["adapter"] is not None:
        params += [p for p in built["adapter"].parameters() if p.requires_grad]
    torch.nn.utils.clip_grad_norm_(params, 1.0)
    opt.step()
    set_arm_training(built, False)
    return {"doc_id": rid, "loss": float(loss.detach()), "updates": 1}



def train_registered(
    built: dict[str, Any],
    rows: dict[str, dict],
    cache: dict[str, dict],
    native: dict[str, torch.Tensor],
    ids: list[str],
    updates: int = 100,
) -> dict[str, Any]:
    """Frozen registered training loop: 100 updates, batch 1, order step % 20."""
    if updates != 100:
        raise ValueError("registered training requires exactly 100 updates")
    opt = optimizer_for(built)
    set_arm_training(built, True)
    losses: list[float] = []
    for step in range(updates):
        rid = ids[step % len(ids)]
        memory = memory_for(built, rid, cache, native)
        labels = make_labels(built["tok"], rows[rid]["summary"], 256)
        opt.zero_grad(set_to_none=True)
        loss = train_forward_loss(built["model"], memory, labels)
        if not torch.isfinite(loss):
            raise RuntimeError(f"{built['arm']}: non-finite loss at step {step}")
        loss.backward()
        params = [p for p in built["model"].parameters() if p.requires_grad]
        if built["adapter"] is not None:
            params += [p for p in built["adapter"].parameters() if p.requires_grad]
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        losses.append(float(loss.detach()))
    set_arm_training(built, False)
    return {
        "updates": updates,
        "loss_first": losses[0],
        "loss_last": losses[-1],
        "loss_mean": float(np.mean(losses)),
        "loss_min": float(np.min(losses)),
        "loss_max": float(np.max(losses)),
        "all_finite": bool(np.all(np.isfinite(losses))),
    }


def build_controls(
    built: dict[str, Any],
    ids: list[str],
    targets: list[str],
    cache: dict[str, dict],
    native: dict[str, torch.Tensor],
) -> dict[str, Any]:
    k_m = built["spec"]["m_k"]
    contributors = [rid for rid in ids if int(memory_for(built, rid, cache, native).shape[0]) >= k_m]
    if len(contributors) < 10:
        raise RuntimeError(f"{built['arm']}: contributor cohort {len(contributors)} < 10")
    with torch.inference_mode():
        pieces = [memory_for(built, rid, cache, native)[:k_m] for rid in contributors]
        pos_mean = torch.stack(pieces, dim=0).mean(dim=0)
        real_prefix = {tid: memory_for(built, tid, cache, native)[:k_m] for tid in targets}
        m_norm: dict[str, torch.Tensor] = {}
        for tid in targets:
            r = real_prefix[tid]
            denom = torch.linalg.norm(pos_mean)
            if float(denom) == 0.0:
                raise RuntimeError("M_POS_MEAN has zero norm")
            scale = torch.linalg.norm(r) / denom
            m_norm[tid] = pos_mean * scale
    return {
        "M_POS_MEAN": pos_mean.detach(),
        "M_NORM": {k: v.detach() for k, v in m_norm.items()},
        "real_prefix": {k: v.detach() for k, v in real_prefix.items()},
        "contributors": contributors,
    }


def tensor_digest(tensors: dict[str, torch.Tensor]) -> str:
    h = hashlib.sha256()
    for key in sorted(tensors):
        h.update(key.encode("utf-8"))
        h.update(b"\0")
        h.update(tensors[key].detach().cpu().numpy().astype("<f4").tobytes())
    return h.hexdigest()


def write_control_manifest(built: dict[str, Any], controls: dict[str, Any], seed: int) -> dict[str, Any]:
    arm = built["arm"]
    root = CONTROL_MANIFEST / arm / str(seed)
    root.mkdir(parents=True, exist_ok=True)
    tensors = {"M_POS_MEAN": controls["M_POS_MEAN"]}
    np.savez_compressed(root / "M_POS_MEAN.npz", tensor=controls["M_POS_MEAN"].numpy())
    norm_dir = root / "M_NORM"
    norm_dir.mkdir(parents=True, exist_ok=True)
    for tid, tensor in controls["M_NORM"].items():
        np.savez_compressed(norm_dir / f"{tid}.npz", tensor=tensor.numpy())
        tensors[f"M_NORM/{tid}"] = tensor
    return {
        "arm": arm,
        "seed": seed,
        "path": str(root.relative_to(ROOT)),
        "M_POS_MEAN_shape": list(controls["M_POS_MEAN"].shape),
        "M_NORM_count": len(controls["M_NORM"]),
        "contributors": controls["contributors"],
        "control_digest": tensor_digest(tensors),
    }


def m_records_for(
    built: dict[str, Any],
    targets: list[str],
    controls: dict[str, Any],
    labels: dict[str, torch.Tensor],
    copies: dict[str, torch.Tensor],
    seed: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    set_arm_training(built, False)
    for tid in targets:
        lab = labels[tid]
        mask = copies[tid]
        real = controls["real_prefix"][tid]
        real_ep = endpoint_values_model(built["model"], real, lab, mask)
        controls_by_variant = {
            "M_POS_MEAN": controls["M_POS_MEAN"],
            "M_NORM": controls["M_NORM"][tid],
        }
        for variant, control in controls_by_variant.items():
            control_ep = endpoint_values_model(built["model"], control, lab, mask)
            for memory_kind, ep in (("control", control_ep), ("real", real_ep)):
                for endpoint in ("copy", "full"):
                    records.append({
                        "arm": built["arm"],
                        "seed": seed,
                        "target_id": tid,
                        "variant": variant,
                        "memory_kind": memory_kind,
                        "endpoint": endpoint,
                        "donor_id": None,
                        "ce": ep[endpoint],
                        "endpoint_ok": ep["endpoint_ok"],
                        "copy_tokens": ep["copy_tokens"],
                        "copy_coverage": ep["copy_coverage"],
                    })
    return records


def endpoint_values_model(model, memory: torch.Tensor, labels: torch.Tensor, copies: torch.Tensor) -> dict[str, Any]:
    with torch.inference_mode():
        full, tok_loss = token_losses(model, memory, labels)
    c = copy_ce(tok_loss, labels, copies)
    return {
        "full": full,
        "copy": c,
        "endpoint_ok": c is not None,
        "copy_tokens": int(copies.sum()),
        "copy_coverage": float(copies.sum()) / max(1, int(copies.numel())),
    }



def phase7_records_for(
    built: dict[str, Any],
    targets: list[str],
    controls: dict[str, Any],
    cache: dict[str, dict],
    native: dict[str, torch.Tensor],
    labels: dict[str, torch.Tensor],
    copies: dict[str, torch.Tensor],
    donors: dict[str, list[str]],
    seed: int,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    k_m = built["spec"]["m_k"]
    set_arm_training(built, False)
    baseline_cache: dict[tuple[str, str, str, int], dict[str, Any]] = {}
    for tid in targets:
        lab = labels[tid]
        mask = copies[tid]
        real_full = controls["real_prefix"][tid]
        for donor in donors[tid]:
            donor_full = memory_for(built, donor, cache, native)
            k_d = min(k_m, int(real_full.shape[0]), int(donor_full.shape[0]))
            if not (1 <= k_d <= k_m):
                raise RuntimeError(f"phase7 K_d out of range: {k_d}")
            real = real_full[:k_d]
            wrong = donor_full[:k_d]
            raw_real = endpoint_values_model(built["model"], real, lab, mask)
            raw_wrong = endpoint_values_model(built["model"], wrong, lab, mask)
            for variant, control in (
                ("M_POS_MEAN", controls["M_POS_MEAN"]),
                ("M_NORM", controls["M_NORM"][tid]),
            ):
                key = (tid, variant, "control", k_d)
                if key not in baseline_cache:
                    baseline_cache[key] = endpoint_values_model(
                        built["model"], control[:k_d], lab, mask
                    )
                baseline = baseline_cache[key]
                for memory_kind, raw in (("real", raw_real), ("donor", raw_wrong)):
                    for endpoint in ("copy", "full"):
                        ce = raw[endpoint]
                        base = baseline[endpoint]
                        ok = raw["endpoint_ok"] and baseline["endpoint_ok"]
                        out.append({
                            "arm": built["arm"],
                            "seed": seed,
                            "target_id": tid,
                            "variant": variant,
                            "memory_kind": memory_kind,
                            "endpoint": endpoint,
                            "donor_id": int(donors[tid].index(donor)),
                            "k_d": int(k_d),
                            "ce": ce,
                            "baseline_ce": base,
                            "delta": (None if ce is None or base is None else base - ce),
                            "endpoint_ok": ok,
                            "copy_tokens": raw["copy_tokens"],
                            "copy_coverage": raw["copy_coverage"],
                        })
    return out


def generate_d1(built: dict[str, Any], ids: list[str], cache: dict[str, dict], native: dict[str, torch.Tensor]) -> list[dict[str, Any]]:
    set_arm_training(built, False)
    out: list[dict[str, Any]] = []
    tok = built["tok"]
    model = built["model"]
    old_cache = bool(model.config.use_cache)
    model.config.use_cache = True
    try:
        for rid in ids:
            mem = memory_for(built, rid, cache, native)
            with torch.inference_mode():
                gen = model.generate(
                    encoder_outputs=BaseModelOutput(last_hidden_state=mem.unsqueeze(0)),
                    attention_mask=torch.ones(1, mem.shape[0], dtype=torch.long),
                    max_new_tokens=256,
                    num_beams=1,
                    do_sample=False,
                    decoder_start_token_id=model.config.decoder_start_token_id or tok.pad_token_id,
                    eos_token_id=tok.eos_token_id,
                    pad_token_id=tok.pad_token_id,
                )
            record = generation_record(gen, tok, 256)
            record["id"] = rid
            out.append(record)
    finally:
        model.config.use_cache = old_cache
    return out


def save_d1_checkpoint(built: dict[str, Any], seed: int) -> str:
    path = CHECKPOINTS / built["arm"] / f"{seed}.pt"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "arm": built["arm"],
        "seed": seed,
        "adapter": built["adapter"].state_dict() if built["adapter"] is not None else None,
        "lora": {name: p.detach().cpu() for name, p in built["model"].named_parameters() if ".lora_" in name},
    }
    torch.save(payload, path)
    return str(path.relative_to(ROOT))


def run_d1() -> dict[str, Any]:
    torch.set_num_threads(6)
    inputs = load_frozen_inputs()
    preflight = inputs["preflight"]
    rows = inputs["rows"]
    train_ids = inputs["train_ids"]
    val_ids = inputs["val_ids"]
    cache = load_layer_cache("train", CACHE)
    cache.update(load_layer_cache("val", CACHE))
    assert_cache_lengths(cache, preflight)

    labels: dict[str, torch.Tensor] | None = None
    copies: dict[str, torch.Tensor] | None = None
    records: dict[str, Any] = {}
    control_entries: list[dict[str, Any]] = []
    m_all: list[dict[str, Any]] = []
    for arm in ARMS:
        started = time.time()
        built = build_arm(arm, D1_SEED)
        if labels is None or copies is None:
            labels, copies = labels_and_copy(built["tok"], rows, val_ids)
        native = native_cache_for(built["model"], built["tok"], rows, train_ids + val_ids)
        if arm in {"F", "L"}:
            donors = donors_for(val_ids, cache)
        else:
            donors = donor_map({rid: int(native[rid].shape[0]) for rid in val_ids}, val_ids)
        step0 = eval_arm_d1(built, val_ids, cache, native, rows, labels, copies, donors)
        train = train_one_update(built, rows, cache, native, train_ids[0])
        final = eval_arm_d1(built, val_ids, cache, native, rows, labels, copies, donors)
        targets = list(preflight["common_ids"]) if arm in {"F", "L"} else val_ids
        controls = build_controls(built, train_ids, targets, cache, native)
        control_entry = write_control_manifest(built, controls, D1_SEED)
        control_entries.append(control_entry)
        m_records = m_records_for(built, targets, controls, labels, copies, D1_SEED)
        m_all.extend(m_records)
        phase7 = phase7_records_for(
            built, list(preflight["common_ids"]), controls, cache, native,
            labels, copies, donors, D1_SEED,
        )
        p7_dir = ROOT / "reports/provenance/C5_b0a/phase7_records" / arm
        p7_dir.mkdir(parents=True, exist_ok=True)
        (p7_dir / f"{D1_SEED}.json").write_text(
            json.dumps(phase7, indent=2) + "\n", encoding="utf-8"
        )
        generation = generate_d1(built, val_ids, cache, native)
        checkpoint = save_d1_checkpoint(built, D1_SEED)
        records[arm] = {
            "arm": arm,
            "seed": D1_SEED,
            "updates": 1,
            "step0": step0,
            "train": train,
            "final": final,
            "control": control_entry,
            "m_records": len(m_records),
            "phase7_records": len(phase7),
            "generation": generation,
            "checkpoint": checkpoint,
            "elapsed_s": time.time() - started,
        }
        partial = {
            "mode": "d1_one_update",
            "complete": False,
            "arms_done": list(records),
            "seed": D1_SEED,
            "arms": records,
            "m_records_total": len(m_all),
            "test_split_used": False,
            "p1_used": False,
            "labels_computed": False,
            "not_a_result": True,
        }
        D1_OUT.parent.mkdir(parents=True, exist_ok=True)
        (D1_OUT.parent / "d1_partial.json").write_text(
            json.dumps(partial, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        del built
        gc.collect()

    D1_OUT.parent.mkdir(parents=True, exist_ok=True)
    D1_M_RECORDS.write_text(json.dumps(m_all, indent=2) + "\n", encoding="utf-8")
    out = {
        "schema_version": 1,
        "experiment": "C5 Phase 6 P/M",
        "mode": "d1_one_update",
        "complete": True,
        "seed": D1_SEED,
        "updates": 1,
        "configs": len(records),
        "registered_seed_used": False,
        "test_split_used": False,
        "p1_used": False,
        "labels_computed": False,
        "not_a_result": True,
        "arms": records,
        "m_records_path": str(D1_M_RECORDS.relative_to(ROOT)),
        "m_records_total": len(m_all),
        "phase7_total": sum(v["phase7_records"] for v in records.values()),
        "control_manifest": {
            "path": str(CONTROL_MANIFEST.relative_to(ROOT)),
            "arms": control_entries,
        },
        "freeze": freeze_record(),
    }
    D1_OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("d0", "d1", "registered"), default="d0")
    args = ap.parse_args()
    if args.mode == "d0":
        out = run_d0()
        print(json.dumps({"mode": out["mode"], "configs": out["configs"], "arms": sorted(out["arms"])}, ensure_ascii=False))
        return 0
    if args.mode == "d1":
        out = run_d1()
        print(json.dumps({"mode": out["mode"], "configs": out["configs"], "m_records": out["m_records_total"]}, ensure_ascii=False))
        return 0
    raise NotApprovedError(
        f"{args.mode} is outside the current approval; D0 only. "
        "D1 and registered execution require separate approval."
    )


if __name__ == "__main__":
    raise SystemExit(main())
