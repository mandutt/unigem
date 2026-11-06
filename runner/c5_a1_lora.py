"""A1: native T5Gemma2 encoder-decoder + attention LoRA for F5.

Smoke/pilot are approved under D-082; full train needs a separate decision.
The runner can save exact checkpoint steps, evaluate val at each checkpoint,
reshuffle every epoch, and enforce step-time/RSS stops.

Examples:
  python runner/c5_a1_lora.py --mode smoke --steps 1
  python runner/c5_a1_lora.py --mode pilot --steps 50 --eval-limit 5
  python runner/c5_a1_lora.py --mode full --steps 2586 \
      --checkpoint-steps 647,1293,1940,2586 --eval-checkpoints
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval.slot_verify import verify_summary  # noqa: E402
from runner.c5_a2null_eval import char_f1, distinct_2, read_jsonl, repeated_4gram_rate  # noqa: E402

T5 = ROOT / "data/models/t5gemma-2-270m-270m"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
OUT = ROOT / "reports/provenance/C5_a1"
CKPT = ROOT / "data/models/f5_t5gemma2_lora"
TARGETS = ("q_proj", "k_proj", "v_proj", "o_proj")


class LoRALinear(nn.Module):
    """Minimal LoRA wrapper around a frozen Linear layer."""

    def __init__(self, base: nn.Linear, r: int = 8, alpha: int = 16, dropout: float = 0.05):
        super().__init__()
        self.base = base
        for p in self.base.parameters():
            p.requires_grad_(False)
        self.r = r
        self.scale = alpha / r
        self.dropout = nn.Dropout(dropout)
        self.lora_A = nn.Parameter(torch.empty(r, base.in_features))
        self.lora_B = nn.Parameter(torch.zeros(base.out_features, r))
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))

    def forward(self, x):
        base = self.base(x)
        z = F.linear(self.dropout(x).to(torch.float32), self.lora_A)
        z = F.linear(z, self.lora_B) * self.scale
        return base + z.to(base.dtype)


def attach_lora(model, r: int = 8, alpha: int = 16, dropout: float = 0.05) -> list[str]:
    names = []
    for name, module in list(model.named_modules()):
        if not name.endswith(TARGETS):
            continue
        if not (name.startswith("model.encoder.text_model.") or name.startswith("model.decoder.")):
            continue
        if not isinstance(module, nn.Linear):
            continue
        parent_name, leaf = name.rsplit(".", 1)
        parent = model.get_submodule(parent_name)
        setattr(parent, leaf, LoRALinear(module, r, alpha, dropout))
        names.append(name)
    return names


def lora_state(model) -> dict[str, torch.Tensor]:
    return {n: p.detach().cpu() for n, p in model.named_parameters() if ".lora_" in n}


def load_lora_state(model, path: Path) -> None:
    obj = torch.load(path, map_location="cpu")
    sd = obj.get("lora", obj) if isinstance(obj, dict) else obj
    missing, unexpected = model.load_state_dict(sd, strict=False)
    bad = [x for x in missing if ".lora_" in x]
    if bad:
        raise SystemExit(f"missing LoRA keys: {bad[:5]} ... ({len(bad)})")
    print(json.dumps({"loaded_lora": str(path), "missing_nonlora": len(missing), "unexpected": len(unexpected)}))


def build_order(n: int, seed: int, epoch: int) -> list[int]:
    """Fresh permutation per epoch; deterministic from seed+epoch."""
    gen = torch.Generator().manual_seed(seed + epoch)
    return torch.randperm(n, generator=gen).tolist()


def adapter_record(model, args, tok, losses: list[float], step: int) -> dict:
    decoder_start = getattr(model.generation_config, "decoder_start_token_id", None)
    if decoder_start is None:
        decoder_start = getattr(tok, "decoder_start_token_id", None)
    if decoder_start is None:
        # T5Gemma2 has no explicit decoder_start_token_id; generation starts from BOS.
        decoder_start = getattr(tok, "bos_token_id", None)
    return {
        "lora": lora_state(model),
        "format_version": 2,
        "rank": args.rank,
        "alpha": args.alpha,
        "dropout": args.dropout,
        "targets": list(TARGETS),
        "text_only": not args.keep_vision,
        "steps": args.steps,
        "step": step,
        "seed": args.seed,
        "train_loss_last": losses[-1] if losses else None,
        "train_loss_mean": sum(losses) / len(losses) if losses else None,
        "input_contract": {
            "prefix": args.prefix,
            "max_input": args.max_input,
            "max_target": args.max_target,
            "tokenizer_dir": str(T5),
            "tokenizer_eos_id": tok.eos_token_id,
            "tokenizer_pad_id": tok.pad_token_id,
            "decoder_start_token_id": decoder_start,
            "label_format": "summary content + eos; padding=-100",
        },
        "optimizer": {"name": "AdamW", "lr": args.lr, "weight_decay": args.weight_decay},
        "reshuffle": "epoch",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def write_adapter(path: Path, model, args, tok, losses: list[float], step: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(adapter_record(model, args, tok, losses, step), path)
    print(json.dumps({"event": "saved", "adapter": str(path), "step": step, "bytes": path.stat().st_size}), flush=True)


def build_model(
    drop_vision: bool = True,
    dtype=torch.bfloat16,
    rank: int = 8,
    alpha: int = 16,
    dropout: float = 0.05,
):
    model = AutoModelForSeq2SeqLM.from_pretrained(
        str(T5), local_files_only=True, dtype=dtype, low_cpu_mem_usage=True
    )
    if drop_vision:
        enc = model.model.encoder
        if hasattr(enc, "vision_tower"):
            del enc.vision_tower
    names = attach_lora(model, r=rank, alpha=alpha, dropout=dropout)
    for p in model.parameters():
        p.requires_grad_(False)
    for n, p in model.named_parameters():
        if ".lora_" in n:
            p.requires_grad_(True)
    model.train()
    return model, names


def labels_for(tok, text: str, max_target: int = 512) -> torch.Tensor:
    ids = tok(text, add_special_tokens=False, truncation=True, max_length=max_target - 1)["input_ids"]
    lab = torch.full((1, max_target), -100, dtype=torch.long)
    lab[0, : len(ids)] = torch.tensor(ids, dtype=torch.long)
    lab[0, len(ids)] = tok.eos_token_id
    return lab


def encode(tok, passage: str, max_input: int = 1024):
    return tok(passage, return_tensors="pt", truncation=True, max_length=max_input)


def rss_gb() -> float:
    return psutil.Process(os.getpid()).memory_info().rss / 1024**3


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "pilot", "full", "eval"], default="smoke")
    ap.add_argument("--steps", type=int, default=1)
    ap.add_argument("--eval-limit", type=int, default=0)
    ap.add_argument("--eval-max-new", type=int, default=448)
    ap.add_argument("--max-input", type=int, default=1024)
    ap.add_argument("--max-target", type=int, default=512)
    ap.add_argument("--prefix", default="")
    ap.add_argument("--repetition-penalty", type=float, default=1.0)
    ap.add_argument("--no-repeat-ngram", type=int, default=0)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--weight-decay", type=float, default=0.01)
    ap.add_argument("--rank", type=int, default=8)
    ap.add_argument("--alpha", type=int, default=16)
    ap.add_argument("--dropout", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=OUT / "pilot")
    ap.add_argument("--adapter", type=Path, default=CKPT / "adapter.pt")
    ap.add_argument("--checkpoint-dir", type=Path, default=None)
    ap.add_argument("--checkpoint-steps", default="", help="comma-separated exact steps, e.g. 647,1293,1940,2586")
    ap.add_argument("--save-every", type=int, default=0, help="also save at every N steps; 0 disables")
    ap.add_argument("--eval-checkpoints", action="store_true", help="evaluate val at each saved checkpoint")
    ap.add_argument("--step-time-limit", type=float, default=60.0, help="abort if one optimizer step exceeds this many seconds; 0 disables")
    ap.add_argument("--rss-limit-gb", type=float, default=13.0)
    ap.add_argument("--keep-vision", action="store_true")
    ap.add_argument("--grad-checkpoint", action="store_true")
    ap.add_argument("--no-save", action="store_true")
    args = ap.parse_args()
    if args.checkpoint_dir is None:
        args.checkpoint_dir = args.out / "checkpoints"
    checkpoint_steps = {
        int(x.strip()) for x in args.checkpoint_steps.split(",") if x.strip()
    }
    if any(x < 1 or x > args.steps for x in checkpoint_steps):
        raise SystemExit(f"checkpoint step outside 1..{args.steps}: {sorted(checkpoint_steps)}")
    torch.manual_seed(args.seed)
    torch.set_num_threads(6)
    args.out.mkdir(parents=True, exist_ok=True)
    args.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    records = read_jsonl(DATA)
    split = json.loads(SPLITS.read_text(encoding="utf-8"))
    train = [r for r in records if str(r["id"]) in set(split["train"])]
    val = {str(r["id"]): r for r in records if str(r["id"]) in set(split["val"])}
    if args.mode == "eval":
        model, names = build_model(
            drop_vision=not args.keep_vision,
            rank=args.rank,
            alpha=args.alpha,
            dropout=args.dropout,
        )
        load_lora_state(model, args.adapter)
        model.eval()
        return evaluate(model, names, args, list(val.values())[: args.eval_limit or None])

    t0 = time.time()
    model, names = build_model(
        drop_vision=not args.keep_vision,
        rank=args.rank,
        alpha=args.alpha,
        dropout=args.dropout,
    )
    if args.grad_checkpoint:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.config.use_cache = False
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=args.weight_decay)
    tok = AutoTokenizer.from_pretrained(str(T5), local_files_only=True)
    print(json.dumps({
        "event": "load",
        "seconds": round(time.time() - t0, 2),
        "rss_gb": round(rss_gb(), 2),
        "lora_modules": len(names),
        "trainable_params": sum(p.numel() for p in params),
        "total_params": sum(p.numel() for p in model.parameters()),
        "text_only": not args.keep_vision,
        "rank": args.rank,
        "alpha": args.alpha,
        "dropout": args.dropout,
        "weight_decay": args.weight_decay,
        "reshuffle": "epoch",
    }), flush=True)

    if not train:
        raise SystemExit("empty train split")
    order: list[int] = []
    current_epoch = -1
    losses = []
    start = time.time()
    for step in range(1, args.steps + 1):
        epoch = (step - 1) // len(train)
        if epoch != current_epoch:
            order = build_order(len(train), args.seed, epoch)
            current_epoch = epoch
            print(json.dumps({
                "event": "epoch_start",
                "epoch": epoch,
                "step": step,
                "order_seed": args.seed + epoch,
            }), flush=True)
        rec = train[order[(step - 1) % len(train)]]
        step_t0 = time.time()
        enc = encode(tok, args.prefix + str(rec["passage"]), args.max_input)
        labels = labels_for(tok, str(rec["summary"]), args.max_target)
        out = model(**enc, labels=labels)
        loss = out.loss
        if not torch.isfinite(loss):
            print(json.dumps({"event": "nonfinite", "step": step, "loss": str(float(loss))}), flush=True)
            return 2
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        step_seconds = time.time() - step_t0
        losses.append(float(loss.detach()))
        if step == 1 or step % 5 == 0 or step == args.steps:
            print(json.dumps({
                "event": "step",
                "step": step,
                "epoch": epoch,
                "loss": round(float(loss.detach()), 4),
                "step_seconds": round(step_seconds, 2),
                "elapsed_s": round(time.time() - start, 1),
                "rss_gb": round(rss_gb(), 2),
                "input_tokens": int(enc["input_ids"].shape[1]),
                "target_tokens": int((labels != -100).sum()),
            }), flush=True)

        should_save = step in checkpoint_steps or (args.save_every > 0 and step % args.save_every == 0)
        if should_save and not args.no_save:
            ckpt_path = args.checkpoint_dir / f"step_{step:04d}.pt"
            write_adapter(ckpt_path, model, args, tok, losses, step)
            if args.eval_checkpoints:
                evaluate_checkpoint(model, val, args, step)

        if args.step_time_limit > 0 and step_seconds > args.step_time_limit:
            print(json.dumps({
                "event": "step_time_stop",
                "step": step,
                "step_seconds": round(step_seconds, 2),
                "limit": args.step_time_limit,
            }), flush=True)
            return 4
        if rss_gb() > args.rss_limit_gb:
            print(json.dumps({"event": "rss_stop", "rss_gb": round(rss_gb(), 2), "limit": args.rss_limit_gb}), flush=True)
            return 3

    if not args.no_save:
        write_adapter(args.adapter, model, args, tok, losses, args.steps)

    if args.eval_limit:
        model.eval()
        evaluate(model, names, args, list(val.values())[: args.eval_limit])
    return 0


@torch.inference_mode()
def evaluate(model, names, args, recs) -> int:
    tok = AutoTokenizer.from_pretrained(str(T5), local_files_only=True)
    rows = []
    for rec in recs:
        enc = encode(tok, args.prefix + str(rec["passage"]), args.max_input)
        gen_kwargs = {
            "max_new_tokens": args.eval_max_new,
            "num_beams": 1,
            "do_sample": False,
        }
        if args.repetition_penalty != 1.0:
            gen_kwargs["repetition_penalty"] = args.repetition_penalty
        if args.no_repeat_ngram > 0:
            gen_kwargs["no_repeat_ngram_size"] = args.no_repeat_ngram
        gen = model.generate(**enc, **gen_kwargs)
        pred = tok.decode(gen[0], skip_special_tokens=True)
        target = str(rec["summary"])
        rep = verify_summary(str(rec["passage"]), pred)
        rows.append({
            "id": str(rec["id"]),
            "pred": pred,
            "target": target,
            "gen_len": int(gen.shape[1]),
            "ended_eos": bool((gen[0] == tok.eos_token_id).any()),
            "char_f1": char_f1(pred, target),
            "nonempty": bool(pred.strip()),
            "repeated_4gram_rate": repeated_4gram_rate(pred),
            "distinct_2": distinct_2(pred),
            "new_slot_count": len(rep.new),
            "summary_slot_count": rep.summary_count,
            "slot_preservation": rep.slot_preservation,
            "new_slot_rate": rep.new_slot_rate,
            "grounded": not rep.new,
        })
        print(json.dumps({"event": "eval", "id": rec["id"], "char_f1": round(rows[-1]["char_f1"], 4), "eos": rows[-1]["ended_eos"]}), flush=True)
    path = args.out / "eval.jsonl"
    path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n", encoding="utf-8")
    slot_values = [x["slot_preservation"] for x in rows]
    nonvacuous = [x for x in rows if x["summary_slot_count"] > 0]
    metrics = {
        "n": len(rows),
        "char_f1_mean": sum(x["char_f1"] for x in rows) / len(rows),
        "grounded_rate": sum(x["grounded"] for x in rows) / len(rows),
        "grounded_rate_nonvacuous": (
            sum(x["grounded"] for x in nonvacuous) / len(nonvacuous) if nonvacuous else 0.0
        ),
        "new_slot_rate_mean": sum(x["new_slot_rate"] for x in rows) / len(rows),
        "summary_slot_count": sum(x["summary_slot_count"] for x in rows),
        "slots_per_doc": sum(x["summary_slot_count"] for x in rows) / len(rows),
        "slotfree_docs": sum(x["summary_slot_count"] == 0 for x in rows),
        "slot_preservation_mean": sum(slot_values) / len(slot_values),
        "slot_preservation_min": min(slot_values),
        "slot_preservation_missing_docs": sum(x < 1.0 for x in slot_values),
        "eos_rate": sum(x["ended_eos"] for x in rows) / len(rows),
        "gen_len_mean": sum(x["gen_len"] for x in rows) / len(rows),
        "repeated_4gram_rate_mean": sum(x["repeated_4gram_rate"] for x in rows) / len(rows),
        "distinct_2_mean": sum(x["distinct_2"] for x in rows) / len(rows),
    }
    (args.out / "eval.metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"event": "eval_metrics", **metrics, "out": str(path)}, ensure_ascii=False), flush=True)
    return 0


def evaluate_checkpoint(model, val, args, step: int) -> None:
    was_training = model.training
    model.eval()
    old_out = args.out
    args.out = old_out / f"eval_step_{step:04d}"
    args.out.mkdir(parents=True, exist_ok=True)
    try:
        evaluate(model, [], args, list(val.values())[: args.eval_limit or None])
    finally:
        args.out = old_out
        if was_training:
            model.train()


if __name__ == "__main__":
    raise SystemExit(main())
