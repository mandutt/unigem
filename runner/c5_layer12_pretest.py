"""Layer-12 EG2 feature capacity pretest.

Compares adapter input features:
- final 768 (reference, from previous pretest: MLP768 cosine 0.6998)
- layer12 512
- layer12 512 with MLP768 / MLP1536

Objective: 1 - cosine(adapter(feature), teacher_hidden), decoder not used.
Train 300 / val 100, 2 epochs, scratch, same seed. No test split.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_b1d_full import eval_hidden, load_cache  # noqa: E402
import numpy as np  # noqa: E402

LAYER_DIR = ROOT / "data/wave2c/eg2_layer12"
OUT = ROOT / "reports/provenance/C5_b1d/layer12_pretest.json"


class LinearAdapter(nn.Module):
    def __init__(self, d_in: int = 512, d_out: int = 640):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d_in, d_out), nn.LayerNorm(d_out))
        self.scale = nn.Parameter(torch.tensor(5.0))

    def forward(self, x):
        return self.net(x) * self.scale


class MLPAdapter(nn.Module):
    def __init__(self, d_in: int = 512, d_out: int = 640, hidden: int = 768):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, hidden), nn.GELU(), nn.Linear(hidden, d_out), nn.LayerNorm(d_out)
        )
        self.scale = nn.Parameter(torch.tensor(5.0))

    def forward(self, x):
        return self.net(x) * self.scale


def build(kind: str, d_in: int):
    if kind == "linear":
        return LinearAdapter(d_in=d_in)
    if kind == "mlp768":
        return MLPAdapter(d_in=d_in, hidden=768)
    if kind == "mlp1536":
        return MLPAdapter(d_in=d_in, hidden=1536)
    raise ValueError(kind)


def eval_hidden_min(adapter, student, teacher, ids):
    """Eval on min(student, teacher) token length to tolerate alignment gaps."""
    cos_vals, norm_ratios, mse_vals = [], [], []
    with torch.inference_mode():
        for rid in ids:
            s = student[rid]
            t = teacher[rid]
            n = min(int(s["length"]), int(t["length"]))
            x = s["h"][:n].unsqueeze(0)
            y = t["h"][:n].float().unsqueeze(0)
            p = adapter(x)
            cos_vals.extend((F.normalize(p.float(), dim=-1) * F.normalize(y, dim=-1)).sum(-1).reshape(-1).tolist())
            norm_ratios.append(float((p.norm(dim=-1) / y.norm(dim=-1).clamp_min(1e-6)).mean()))
            mse_vals.append(float(F.mse_loss(F.normalize(p, dim=-1), F.normalize(y, dim=-1))))
    return {
        "n_docs": len(ids),
        "n_tokens": len(cos_vals),
        "cosine_mean": sum(cos_vals) / len(cos_vals) if cos_vals else float("nan"),
        "cosine_min": min(cos_vals) if cos_vals else float("nan"),
        "cosine_p05": float(np.quantile(cos_vals, 0.05)) if cos_vals else float("nan"),
        "norm_ratio_mean": sum(norm_ratios) / len(norm_ratios) if norm_ratios else float("nan"),
        "normalized_mse_mean": sum(mse_vals) / len(mse_vals) if mse_vals else float("nan"),
    }


def load_layer_cache(split: str) -> dict:
    out = {}
    for p in sorted(LAYER_DIR.glob(f"{split}_*.npz")):
        z = np.load(p)
        for i, rid in enumerate(z["ids"]):
            n = int(z["lengths"][i])
            out[str(rid)] = {"h": torch.from_numpy(z["h"][i].astype(np.float32)), "length": n}
    return out


def train_arm(kind: str, d_in: int, train_ids, val_ids, student, teacher, epochs: int, lr: float) -> dict:
    torch.manual_seed(20261108)
    adapter = build(kind, d_in)
    opt = torch.optim.AdamW(adapter.parameters(), lr=lr, weight_decay=0.01)
    before = eval_hidden_min(adapter, {r: student[r] for r in val_ids},
                             {r: teacher[r] for r in val_ids}, val_ids)
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
            x = s["h"][:n].unsqueeze(0)
            y = t["h"][:n].float().unsqueeze(0)
            p = adapter(x)
            cos = (F.normalize(p.float(), dim=-1) * F.normalize(y, dim=-1)).sum(-1).mean()
            loss = 1.0 - cos
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(adapter.parameters(), 1.0)
            opt.step()
            losses.append(float(loss.detach()))
    after = eval_hidden_min(adapter, {r: student[r] for r in val_ids},
                            {r: teacher[r] for r in val_ids}, val_ids)
    return {
        "kind": kind,
        "d_in": d_in,
        "params": sum(p.numel() for p in adapter.parameters()),
        "before": before,
        "after": after,
        "loss_first": losses[0] if losses else None,
        "loss_last": losses[-1] if losses else None,
        "elapsed_sec": round(time.time() - t0, 1),
    }, adapter


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-limit", type=int, default=300)
    ap.add_argument("--val-limit", type=int, default=100)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--save-dir", type=Path, default=None,
                    help="optional directory to save each arm's adapter_final.pt")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    args.out = args.out if args.out.is_absolute() else ROOT / args.out
    if args.save_dir is not None:
        args.save_dir = args.save_dir if args.save_dir.is_absolute() else ROOT / args.save_dir
    torch.set_num_threads(6)
    splits = json.loads((ROOT / "reports/provenance/C5_clean/splits.json").read_text(encoding="utf-8"))
    train_ids = list(splits["train"])[: args.train_limit]
    val_ids = list(splits["val"])[: args.val_limit]
    layer = load_layer_cache("train")
    layer.update(load_layer_cache("val"))
    teacher = load_cache("teacher", "train")
    teacher.update(load_cache("teacher", "val"))
    result = {
        "experiment": "layer12_capacity_pretest",
        "feature": "EG2 hidden_states[12] 512",
        "train_n": len(train_ids),
        "val_n": len(val_ids),
        "epochs": args.epochs,
        "lr": args.lr,
        "init": "scratch; same seed for all arms",
        "final_768_reference": {"kind": "mlp768", "cosine_mean": 0.699763472444729},
        "arms": [],
        "test_split_used": False,
    }
    for kind in ("linear", "mlp768", "mlp1536"):
        print(json.dumps({"arm": kind, "status": "start"}), flush=True)
        arm, adapter = train_arm(kind, 512, train_ids, val_ids, layer, teacher, args.epochs, args.lr)
        result["arms"].append(arm)
        if args.save_dir is not None:
            args.save_dir.mkdir(parents=True, exist_ok=True)
            torch.save({"adapter": adapter.state_dict(), "kind": kind, "d_in": 512,
                        "hidden": {"linear": None, "mlp768": 768, "mlp1536": 1536}[kind]},
                       args.save_dir / f"{kind}_adapter_final.pt")
        print(json.dumps(arm, ensure_ascii=False, indent=2), flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
