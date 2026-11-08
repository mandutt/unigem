"""C5 B0 two-arm runner: frozen adapter-only vs adapter + mT5 decoder LoRA.

This runner uses the native EG2 layer19 cache. The mT5 encoder is bypassed by
passing the adapted memory through encoder_outputs. The base decoder is frozen;
Arm F trains only the adapter, Arm L trains the adapter plus q/k/v/o LoRA in
the decoder self- and cross-attention modules.

The current invocation is smoke-only: it attaches LoRA, verifies the 64-module
inventory, checks that zero-output LoRA reproduces the frozen forward, and
checks finite forward losses. No optimizer step or generation is performed.
"""
from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from transformers import MT5ForConditionalGeneration, T5Tokenizer
from transformers.modeling_outputs import BaseModelOutput

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_a1_lora import LoRALinear  # noqa: E402
from runner.c5_mt5_layer_probe import Adapter, load_layer_cache, make_labels  # noqa: E402

MODEL = ROOT / "data/models/mt5-small"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
CACHE = ROOT / "data/wave2c/eg2_native_layer19/layer19"
OUT = ROOT / "reports/provenance/C5_b0/mt5_lora_smoke.json"
EXPECTED_LORA_MODULES = 64


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def attach_decoder_lora_mt5(
    model,
    r: int = 8,
    alpha: int = 16,
    dropout: float = 0.05,
) -> list[str]:
    """Attach LoRA to mT5 decoder self- and cross-attention q/k/v/o."""
    names: list[str] = []
    for name, module in list(model.named_modules()):
        if not name.startswith("decoder."):
            continue
        if not name.endswith((".q", ".k", ".v", ".o")):
            continue
        if not isinstance(module, nn.Linear):
            continue
        parent_name, leaf = name.rsplit(".", 1)
        parent = model.get_submodule(parent_name)
        setattr(parent, leaf, LoRALinear(module, r, alpha, dropout))
        names.append(name)
    if len(names) != EXPECTED_LORA_MODULES:
        raise RuntimeError(
            f"unexpected mT5 LoRA module count: {len(names)} != {EXPECTED_LORA_MODULES}; names={names}"
        )
    return names


def lora_parameters(model) -> list[tuple[str, nn.Parameter]]:
    return [(name, p) for name, p in model.named_parameters() if ".lora_" in name and p.requires_grad]


def make_adapter(seed: int) -> Adapter:
    torch.manual_seed(seed)
    return Adapter(512, 512)


def load_base() -> tuple[Any, Any]:
    tok = T5Tokenizer.from_pretrained(str(MODEL), local_files_only=True, use_fast=False)
    model = MT5ForConditionalGeneration.from_pretrained(
        str(MODEL), local_files_only=True, dtype=torch.float32, low_cpu_mem_usage=True
    ).eval()
    model.config.use_cache = False
    for p in model.parameters():
        p.requires_grad_(False)
    return tok, model


def forward_loss(model, memory: torch.Tensor, labels: torch.Tensor) -> tuple[float, torch.Tensor]:
    """Forward one memory/label pair and return loss and logits."""
    model.eval()
    enc = BaseModelOutput(last_hidden_state=memory.unsqueeze(0))
    mask = torch.ones(1, memory.shape[0], dtype=torch.long)
    out = model(encoder_outputs=enc, attention_mask=mask, labels=labels)
    return float(out.loss.detach()), out.logits.detach()


def smoke(args) -> int:
    rows = {str(r["id"]): r for r in read_jsonl(args.data)}
    split = json.loads(args.splits.read_text(encoding="utf-8"))
    train_ids = [str(x) for x in split["train"][: args.train_limit]]
    cache = load_layer_cache("train", args.cache_dir)
    if not train_ids or train_ids[0] not in cache:
        raise RuntimeError("no training document in native cache")

    tok, model = load_base()
    rid = train_ids[0]
    h = cache[rid]["h"]
    labels = make_labels(tok, str(rows[rid]["summary"]), args.target_max_length)
    seed = args.seed

    # Frozen arm: adapter-only, decoder untouched.
    adapter_f = make_adapter(seed)
    adapter_f.eval()
    with torch.no_grad():
        mem_f = adapter_f(h.unsqueeze(0)).squeeze(0)
        loss_f, logits_f = forward_loss(model, mem_f, labels)

    # LoRA arm: same adapter state, zero-output LoRA must reproduce frozen arm.
    adapter_l = make_adapter(seed)
    adapter_l.load_state_dict(deepcopy(adapter_f.state_dict()))
    adapter_l.eval()
    attached = attach_decoder_lora_mt5(model, args.lora_r, args.lora_alpha, args.lora_dropout)
    lora_params = lora_parameters(model)
    with torch.no_grad():
        mem_l = adapter_l(h.unsqueeze(0)).squeeze(0)
        loss_l, logits_l = forward_loss(model, mem_l, labels)

    delta_loss = abs(loss_f - loss_l)
    delta_logits = float((logits_f - logits_l).abs().max())
    finite = bool(torch.isfinite(torch.tensor(loss_f)) and torch.isfinite(torch.tensor(loss_l)))

    payload = {
        "experiment": "c5_b0_two_arm_runner_smoke",
        "mode": "smoke_no_training",
        "model": str(MODEL.relative_to(ROOT).as_posix()),
        "cache": str(args.cache_dir.relative_to(ROOT).as_posix()),
        "layer": 19,
        "doc_id": rid,
        "source_tokens": int(h.shape[0]),
        "label_tokens": int(labels.shape[1]),
        "seed": seed,
        "lora": {
            "r": args.lora_r,
            "alpha": args.lora_alpha,
            "dropout": args.lora_dropout,
            "attached_modules": len(attached),
            "expected_modules": EXPECTED_LORA_MODULES,
            "module_names_head": attached[:8],
            "trainable_lora_parameters": sum(p.numel() for _, p in lora_params),
        },
        "adapter_parameters": sum(p.numel() for p in adapter_f.parameters()),
        "frozen_arm": {
            "loss": loss_f,
            "trainable_adapter_parameters": sum(p.numel() for p in adapter_f.parameters()),
        },
        "lora_arm": {
            "loss": loss_l,
            "trainable_parameters": sum(p.numel() for p in adapter_l.parameters()) + sum(p.numel() for _, p in lora_params),
        },
        "zero_lora_equivalence": {
            "loss_abs_delta": delta_loss,
            "logits_max_abs_delta": delta_logits,
            "allclose_atol_1e-5": bool(torch.allclose(logits_f, logits_l, atol=1e-5, rtol=1e-4)),
            "finite": finite,
        },
        "base_encoder_frozen": all(not p.requires_grad for p in model.encoder.parameters()),
        "test_split_used": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"wrote {args.out}")
    return 0 if (payload["zero_lora_equivalence"]["allclose_atol_1e-5"] and finite) else 2


def train_arm(args, arm: str) -> dict[str, Any]:
    """Train one arm. Not invoked by smoke; kept for the approved B0 run."""
    rows = {str(r["id"]): r for r in read_jsonl(args.data)}
    split = json.loads(args.splits.read_text(encoding="utf-8"))
    train_ids = [str(x) for x in split["train"][: args.train_limit]]
    val_ids = [str(x) for x in split["val"][: args.val_limit]]
    cache = load_layer_cache("train", args.cache_dir)
    val_cache = load_layer_cache("val", args.cache_dir)
    missing = [x for x in train_ids + val_ids if x not in cache and x not in val_cache]
    if missing:
        raise RuntimeError(f"missing cache ids: {missing[:3]}")

    tok, model = load_base()
    adapter = make_adapter(args.seed)
    if arm == "lora":
        attach_decoder_lora_mt5(model, args.lora_r, args.lora_alpha, args.lora_dropout)
        params = list(adapter.parameters()) + [p for _, p in lora_parameters(model)]
        groups = [
            {"params": list(adapter.parameters()), "lr": args.adapter_lr},
            {"params": [p for _, p in lora_parameters(model)], "lr": args.lora_lr},
        ]
    elif arm == "frozen":
        params = list(adapter.parameters())
        groups = [{"params": params, "lr": args.adapter_lr}]
    else:
        raise ValueError(arm)

    labels_by_id = {
        rid: make_labels(tok, str(rows[rid]["summary"]), args.target_max_length)
        for rid in set(train_ids + val_ids)
    }
    opt = torch.optim.AdamW(groups, weight_decay=0.01)
    adapter.train()
    if arm == "lora":
        model.train()
        # Keep the base frozen; LoRALinear only exposes lora_A/lora_B.
    losses: list[float] = []
    for step in range(args.steps):
        rid = train_ids[step % len(train_ids)]
        h = cache[rid]["h"]
        mem = adapter(h.unsqueeze(0)).squeeze(0)
        enc = BaseModelOutput(last_hidden_state=mem.unsqueeze(0))
        mask = torch.ones(1, mem.shape[0], dtype=torch.long)
        out = model(encoder_outputs=enc, attention_mask=mask, labels=labels_by_id[rid])
        loss = out.loss
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite loss arm={arm} step={step}")
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        losses.append(float(loss.detach()))

    # Evaluation uses the same real/zero/shuffled protocol as Stage A.
    adapter.eval()
    model.eval()
    real: list[float] = []
    zero: list[float] = []
    shuffled: list[float] = []
    with torch.no_grad():
        for i, rid in enumerate(val_ids):
            h = val_cache[rid]["h"]
            mem = adapter(h.unsqueeze(0)).squeeze(0)
            labels = labels_by_id[rid]
            lr, _ = forward_loss(model, mem, labels)
            lz, _ = forward_loss(model, torch.zeros_like(mem), labels)
            rid2 = val_ids[(i + 1) % len(val_ids)]
            mem2 = adapter(val_cache[rid2]["h"].unsqueeze(0)).squeeze(0)
            ls, _ = forward_loss(model, mem2, labels)
            real.append(lr)
            zero.append(lz)
            shuffled.append(ls)

    n = len(val_ids)
    result = {
        "experiment": "c5_b0_two_arm_runner",
        "arm": arm,
        "model": str(MODEL.relative_to(ROOT).as_posix()),
        "cache": str(args.cache_dir.relative_to(ROOT).as_posix()),
        "layer": 19,
        "train_n": len(train_ids),
        "val_n": len(val_ids),
        "steps": args.steps,
        "seed": args.seed,
        "lora": {
            "r": args.lora_r,
            "alpha": args.lora_alpha,
            "dropout": args.lora_dropout,
            "modules": EXPECTED_LORA_MODULES if arm == "lora" else 0,
        },
        "train_ce_first": losses[0],
        "train_ce_last": losses[-1],
        "train_ce_last10_mean": sum(losses[-10:]) / min(10, len(losses)),
        "val_real_ce": sum(real) / n,
        "val_zero_ce": sum(zero) / n,
        "val_shuffled_ce": sum(shuffled) / n,
        "delta_zero": (sum(zero) - sum(real)) / n,
        "delta_shuffled": (sum(shuffled) - sum(real)) / n,
        "test_split_used": False,
    }
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "train"], default="smoke")
    ap.add_argument("--arm", choices=["frozen", "lora", "both"], default="both")
    ap.add_argument("--model-dir", type=Path, default=MODEL)
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--splits", type=Path, default=SPLITS)
    ap.add_argument("--cache-dir", type=Path, default=CACHE)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--train-limit", type=int, default=20)
    ap.add_argument("--val-limit", type=int, default=20)
    ap.add_argument("--steps", type=int, default=100)
    ap.add_argument("--target-max-length", type=int, default=256)
    ap.add_argument("--seed", type=int, default=20261108)
    ap.add_argument("--lora-r", type=int, default=8)
    ap.add_argument("--lora-alpha", type=int, default=16)
    ap.add_argument("--lora-dropout", type=float, default=0.05)
    ap.add_argument("--adapter-lr", type=float, default=1e-3)
    ap.add_argument("--lora-lr", type=float, default=1e-4)
    args = ap.parse_args()
    args.cache_dir = args.cache_dir if args.cache_dir.is_absolute() else ROOT / args.cache_dir
    args.out = args.out if args.out.is_absolute() else ROOT / args.out
    torch.set_num_threads(6)
    if args.mode == "smoke":
        return smoke(args)

    arms = ["frozen", "lora"] if args.arm == "both" else [args.arm]
    results = [train_arm(args, arm) for arm in arms]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
