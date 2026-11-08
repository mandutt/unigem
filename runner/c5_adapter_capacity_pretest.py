"""Adapter capacity pretest on the hidden-matching objective.

Compares linear, MLP768, MLP1536 adapters trained only on EG2 -> teacher hidden
cosine for 300 train docs / 100 val docs, 2 epochs. No decoder, no test split.

This is a cheap gate before spending ~2h on B2 3-arm training.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_b1d_full import eval_hidden, load_cache  # noqa: E402

OUT = ROOT / "reports/provenance/C5_b1d/adapter_capacity_pretest.json"


class LinearAdapter(nn.Module):
    def __init__(self, d_in: int = 768, d_out: int = 640):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d_in, d_out), nn.LayerNorm(d_out))
        self.scale = nn.Parameter(torch.tensor(5.0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x) * self.scale


class MLPAdapter(nn.Module):
    def __init__(self, d_in: int = 768, d_out: int = 640, hidden: int = 768):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, hidden),
            nn.GELU(),
            nn.Linear(hidden, d_out),
            nn.LayerNorm(d_out),
        )
        self.scale = nn.Parameter(torch.tensor(5.0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x) * self.scale


def build(kind: str) -> nn.Module:
    if kind == "linear":
        return LinearAdapter()
    if kind == "mlp768":
        return MLPAdapter(hidden=768)
    if kind == "mlp1536":
        return MLPAdapter(hidden=1536)
    raise ValueError(kind)


def train_arm(kind: str, train_ids, val_ids, student, teacher, epochs: int, lr: float) -> dict:
    torch.manual_seed(20261108)
    adapter = build(kind)
    opt = torch.optim.AdamW(adapter.parameters(), lr=lr, weight_decay=0.01)
    before = eval_hidden(adapter, {r: student[r] for r in val_ids}, {r: teacher[r] for r in val_ids}, val_ids)
    t0 = time.time()
    losses = []
    for epoch in range(epochs):
        order = list(train_ids)
        perm = torch.randperm(len(order), generator=torch.Generator().manual_seed(20261108 + epoch)).tolist()
        order = [order[i] for i in perm]
        for rid in order:
            s = student[rid]
            t = teacher[rid]
            n = min(int(s["length"]), int(t["length"]))
            x = s["h"][:n].float().unsqueeze(0)
            y = t["h"][:n].float().unsqueeze(0)
            p = adapter(x)
            cos = (F.normalize(p.float(), dim=-1) * F.normalize(y, dim=-1)).sum(-1).mean()
            loss = 1.0 - cos
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(adapter.parameters(), 1.0)
            opt.step()
            losses.append(float(loss.detach()))
    after = eval_hidden(adapter, {r: student[r] for r in val_ids}, {r: teacher[r] for r in val_ids}, val_ids)
    return {
        "kind": kind,
        "params": sum(p.numel() for p in adapter.parameters()),
        "before": before,
        "after": after,
        "loss_first": losses[0] if losses else None,
        "loss_last": losses[-1] if losses else None,
        "elapsed_sec": round(time.time() - t0, 1),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-limit", type=int, default=300)
    ap.add_argument("--val-limit", type=int, default=100)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    args.out = args.out if args.out.is_absolute() else ROOT / args.out
    torch.set_num_threads(6)
    splits = json.loads((ROOT / "reports/provenance/C5_clean/splits.json").read_text(encoding="utf-8"))
    train_ids = list(splits["train"])[: args.train_limit]
    val_ids = list(splits["val"])[: args.val_limit]
    student = load_cache("student", "train")
    teacher = load_cache("teacher", "train")
    student_val = load_cache("student", "val")
    teacher_val = load_cache("teacher", "val")
    # use separate val caches via a merged dict
    student = {**student, **student_val}
    teacher = {**teacher, **teacher_val}
    result = {
        "experiment": "adapter_capacity_hidden_pretest",
        "train_n": len(train_ids),
        "val_n": len(val_ids),
        "epochs": args.epochs,
        "lr": args.lr,
        "init": "scratch; same seed for all arms",
        "arms": [],
        "test_split_used": False,
    }
    for kind in ("linear", "mlp768", "mlp1536"):
        print(json.dumps({"arm": kind, "status": "start"}), flush=True)
        arm = train_arm(kind, train_ids, val_ids, student, teacher, args.epochs, args.lr)
        result["arms"].append(arm)
        print(json.dumps(arm, ensure_ascii=False, indent=2), flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
