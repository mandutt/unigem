"""Stage A: which EG2 layer gives usable memory for the mT5-small decoder?

For each requested EG2 layer:
  EG2 cached hidden [n,512] -> adapter 512->512 -> mT5 decoder
  (mT5 encoder is bypassed via encoder_outputs)

The mT5 decoder is frozen. Only the adapter is trained on a tiny set of docs.
After training, val CE is measured with real, zero, and shuffled memory.

This is a screening probe, not an F5 quality run. test split is never used.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from transformers import T5Tokenizer, MT5ForConditionalGeneration, UMT5ForConditionalGeneration
from transformers.modeling_outputs import BaseModelOutput

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
MT5 = ROOT / "data/models/mt5-small"
FEATURE_ROOT = ROOT / "data/wave2c"
OUT = ROOT / "reports/provenance/C5_b1d/mt5_layer_probe.json"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def parse_layers(spec: str) -> list[int]:
    out: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return sorted(out)


class Adapter(nn.Module):
    def __init__(self, d_in: int = 512, d_out: int = 512):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, d_out),
            nn.GELU(),
            nn.Linear(d_out, d_out),
            nn.LayerNorm(d_out),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def load_layer_cache(split: str, directory: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in sorted(directory.glob(f"{split}_*.npz")):
        z = np.load(p)
        for i, rid in enumerate(z["ids"]):
            n = int(z["lengths"][i])
            out[str(rid)] = {
                "h": torch.from_numpy(z["h"][i, :n].astype(np.float32)),
                "length": n,
            }
    return out


def make_labels(tok, text: str, max_length: int) -> torch.Tensor:
    ids = tok(text, add_special_tokens=True, truncation=True,
              max_length=max_length)["input_ids"]
    return torch.tensor([ids], dtype=torch.long)


def memory_ce(model, memory: torch.Tensor, labels: torch.Tensor) -> float:
    memory = memory.float()
    enc = BaseModelOutput(last_hidden_state=memory.unsqueeze(0))
    mask = torch.ones(1, memory.shape[0], dtype=torch.long)
    with torch.no_grad():
        out = model(encoder_outputs=enc, attention_mask=mask, labels=labels)
    return float(out.loss.detach())


def eval_ablation(adapter, model, cache, ids, labels_by_id) -> dict:
    adapter.eval()
    real, zero, shuffled = [], [], []
    with torch.no_grad():
        for i, rid in enumerate(ids):
            h = cache[rid]["h"]
            mem = adapter(h.unsqueeze(0)).squeeze(0)
            labels = labels_by_id[rid]
            real.append(memory_ce(model, mem, labels))
            zero.append(memory_ce(model, torch.zeros_like(mem), labels))
            rid2 = ids[(i + 1) % len(ids)]
            h2 = cache[rid2]["h"]
            mem2 = adapter(h2.unsqueeze(0)).squeeze(0)
            shuffled.append(memory_ce(model, mem2, labels))
    n = len(ids)
    real_m = sum(real) / n
    zero_m = sum(zero) / n
    shuf_m = sum(shuffled) / n
    return {
        "val_real_ce": real_m,
        "val_zero_ce": zero_m,
        "val_shuffled_ce": shuf_m,
        "delta_zero": zero_m - real_m,
        "delta_shuffled": shuf_m - real_m,
    }


def probe_layer(layer: int, args, model, tok, rows, split, train_ids, val_ids) -> dict:
    t0 = time.time()
    directory = ROOT / args.feature_root / f"eg2_layer{layer}"
    if not directory.exists():
        raise FileNotFoundError(directory)
    train_cache = load_layer_cache("train", directory)
    val_cache = load_layer_cache("val", directory)
    labels_by_id = {
        rid: make_labels(tok, str(rows[rid]["summary"]), args.target_max_length)
        for rid in set(train_ids + val_ids)
    }

    torch.manual_seed(20261108 + layer)
    adapter = Adapter(512, 512)
    opt = torch.optim.AdamW(adapter.parameters(), lr=args.lr, weight_decay=0.01)
    model.eval()
    adapter.train()
    losses: list[float] = []
    grad_norms: list[float] = []
    for step in range(args.steps):
        rid = train_ids[step % len(train_ids)]
        h = train_cache[rid]["h"]
        mem = adapter(h.unsqueeze(0))
        enc = BaseModelOutput(last_hidden_state=mem)
        mask = torch.ones(1, h.shape[0], dtype=torch.long)
        out = model(encoder_outputs=enc, attention_mask=mask, labels=labels_by_id[rid])
        loss = out.loss
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite loss layer={layer} step={step}")
        opt.zero_grad(set_to_none=True)
        loss.backward()
        gn = float(torch.nn.utils.clip_grad_norm_(adapter.parameters(), 1.0))
        opt.step()
        losses.append(float(loss.detach()))
        grad_norms.append(gn)

    ablation = eval_ablation(adapter, model, val_cache, val_ids, labels_by_id)
    return {
        "layer": layer,
        "train_n": len(train_ids),
        "val_n": len(val_ids),
        "steps": args.steps,
        "adapter": "MLP 512->512->512 + LayerNorm",
        "decoder_frozen": True,
        "train_ce_first": losses[0],
        "train_ce_last": losses[-1],
        "train_ce_last10_mean": sum(losses[-10:]) / min(10, len(losses)),
        "grad_norm_last": grad_norms[-1],
        "grad_norm_mean": sum(grad_norms) / len(grad_norms),
        **ablation,
        "elapsed_sec": round(time.time() - t0, 1),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", default="1-23")
    ap.add_argument("--train-limit", type=int, default=5)
    ap.add_argument("--val-limit", type=int, default=5)
    ap.add_argument("--steps", type=int, default=100)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--target-max-length", type=int, default=256)
    ap.add_argument("--feature-root", default="data/wave2c")
    ap.add_argument("--model-type", choices=["mt5", "umt5"], default="mt5")
    ap.add_argument("--model-dir", default=str(MT5))
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    args.out = args.out if args.out.is_absolute() else ROOT / args.out
    args.feature_root = args.feature_root if Path(args.feature_root).is_absolute() else str(ROOT / args.feature_root)
    args.model_dir = Path(args.model_dir)
    if not args.model_dir.is_absolute():
        args.model_dir = ROOT / args.model_dir

    torch.set_num_threads(6)
    rows_list = read_jsonl(DATA)
    rows = {str(r["id"]): r for r in rows_list}
    split = json.loads(SPLITS.read_text(encoding="utf-8"))
    train_ids = list(split["train"])[: args.train_limit]
    val_ids = list(split["val"])[: args.val_limit]
    layers = parse_layers(args.layers)

    tok = T5Tokenizer.from_pretrained(str(args.model_dir), local_files_only=True, use_fast=False)
    model_cls = MT5ForConditionalGeneration if args.model_type == "mt5" else UMT5ForConditionalGeneration
    model = model_cls.from_pretrained(
        str(args.model_dir), local_files_only=True, dtype=torch.float32, low_cpu_mem_usage=True
    ).eval()
    for p in model.parameters():
        p.requires_grad_(False)
    model.config.use_cache = False

    result = {
        "experiment": f"{args.model_type}_small_layer_probe_stage_a",
        "model": args.model_type,
        "model_dir": str(args.model_dir.relative_to(ROOT).as_posix()),
        "d_model": int(model.config.d_model),
        "train_n": len(train_ids),
        "val_n": len(val_ids),
        "steps": args.steps,
        "lr": args.lr,
        "target_max_length": args.target_max_length,
        "layers": [],
        "test_split_used": False,
    }
    for layer in layers:
        print(json.dumps({"layer": layer, "status": "start"}), flush=True)
        rec = probe_layer(layer, args, model, tok, rows, split, train_ids, val_ids)
        result["layers"].append(rec)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(rec, ensure_ascii=False), flush=True)
    print(json.dumps({"done": True, "out": str(args.out)}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
