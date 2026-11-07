"""B1d full teacher-hidden distillation (adapter only, decoder frozen).

Loads cached T5Gemma2 teacher hidden and EG2 student hidden, trains a
token-level 768->640 adapter for 2 epochs, and evaluates val hidden cosine.
No sealed test split is loaded.
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
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data/wave2c/b1d"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
OUT = ROOT / "data/models/f5_t5gemma2_lora/b1d_full"
REPORT = ROOT / "reports/provenance/C5_b1d/full_metrics.json"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_cache(kind: str, split: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted((CACHE / kind).glob(f"{split}_*.npz")):
        if path.name.endswith(".tmp.npz"):
            continue
        with np.load(path, allow_pickle=False) as z:
            ids = [str(x) for x in z["ids"].tolist()]
            h = z["h"]
            mask = z["mask"]
            lengths = z["lengths"]
            for i, rid in enumerate(ids):
                out[rid] = {
                    "h": torch.from_numpy(h[i].copy()).to(torch.float16),
                    "mask": torch.from_numpy(mask[i].copy()).to(torch.bool),
                    "length": int(lengths[i]),
                }
    return out


class B1dFullAdapter(nn.Module):
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


def direction_cosine(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    return (F.normalize(pred.float(), dim=-1) * F.normalize(target.float(), dim=-1)).sum(dim=-1)


def eval_hidden(adapter: B1dFullAdapter, student: dict, teacher: dict, ids: list[str]) -> dict:
    cos_vals = []
    norm_ratios = []
    mse_vals = []
    with torch.inference_mode():
        for rid in ids:
            x = student[rid]["h"][: student[rid]["length"]].float().unsqueeze(0)
            t = teacher[rid]["h"][: teacher[rid]["length"]].float().unsqueeze(0)
            p = adapter(x)
            cos_vals.extend(direction_cosine(p, t)[0].tolist())
            norm_ratios.append(float((p.norm(dim=-1) / t.norm(dim=-1).clamp_min(1e-6)).mean()))
            mse_vals.append(float(F.mse_loss(F.normalize(p, dim=-1), F.normalize(t, dim=-1))))
    return {
        "n_docs": len(ids),
        "n_tokens": len(cos_vals),
        "cosine_mean": sum(cos_vals) / len(cos_vals) if cos_vals else float("nan"),
        "cosine_min": min(cos_vals) if cos_vals else float("nan"),
        "cosine_p05": float(np.quantile(cos_vals, 0.05)) if cos_vals else float("nan"),
        "norm_ratio_mean": sum(norm_ratios) / len(norm_ratios) if norm_ratios else float("nan"),
        "normalized_mse_mean": sum(mse_vals) / len(mse_vals) if mse_vals else float("nan"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--train-limit", type=int, default=0)
    ap.add_argument("--val-limit", type=int, default=0)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    ap.add_argument("--report", type=Path, default=REPORT)
    args = ap.parse_args()

    args.out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    args.report = args.report if args.report.is_absolute() else ROOT / args.report

    torch.set_num_threads(6)
    torch.manual_seed(20261107)
    t0 = time.time()
    rows = read_jsonl(DATA)
    by_id = {str(r["id"]): r for r in rows}
    splits = json.loads((ROOT / "reports/provenance/C5_clean/splits.json").read_text(encoding="utf-8"))
    train_ids = list(splits["train"])
    val_ids = list(splits["val"])
    if args.train_limit:
        train_ids = train_ids[: args.train_limit]
    if args.val_limit:
        val_ids = val_ids[: args.val_limit]

    student_train = load_cache("student", "train")
    teacher_train = load_cache("teacher", "train")
    student_val = load_cache("student", "val")
    teacher_val = load_cache("teacher", "val")
    missing_train = [x for x in train_ids if x not in student_train or x not in teacher_train]
    missing_val = [x for x in val_ids if x not in student_val or x not in teacher_val]
    if missing_train or missing_val:
        raise SystemExit(f"missing cache ids: train={missing_train[:3]} n={len(missing_train)} "
                         f"val={missing_val[:3]} n={len(missing_val)}")
    for rid in train_ids + val_ids:
        s = student_train[rid] if rid in student_train else student_val[rid]
        t = teacher_train[rid] if rid in teacher_train else teacher_val[rid]
        if s["length"] != t["length"]:
            raise SystemExit(f"length mismatch {rid}: {s['length']} vs {t['length']}")
        if not bool(s["mask"][: s["length"]].all()) or not bool(t["mask"][: t["length"]].all()):
            raise SystemExit(f"bad mask {rid}")

    adapter = B1dFullAdapter()
    opt = torch.optim.AdamW(adapter.parameters(), lr=args.lr, weight_decay=0.01)
    before_train = eval_hidden(adapter, student_train, teacher_train, train_ids)
    before_val = eval_hidden(adapter, student_val, teacher_val, val_ids)
    losses = []
    steps_per_epoch = len(train_ids)
    for epoch in range(args.epochs):
        order = list(train_ids)
        perm = torch.randperm(len(order), generator=torch.Generator().manual_seed(20261107 + epoch)).tolist()
        order = [order[i] for i in perm]
        for step, rid in enumerate(order):
            s = student_train[rid]
            t = teacher_train[rid]
            x = s["h"][: s["length"]].float().unsqueeze(0)
            y = t["h"][: t["length"]].float().unsqueeze(0)
            pred = adapter(x)
            cos = direction_cosine(pred, y)
            loss = (
                1.0 - cos.mean()
                + 0.05 * F.mse_loss(F.normalize(pred, dim=-1), F.normalize(y, dim=-1))
                + 0.05 * ((pred.norm(dim=-1) / y.norm(dim=-1).clamp_min(1e-6)).log() ** 2).mean()
            )
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(adapter.parameters(), 1.0)
            opt.step()
            losses.append(float(loss.detach()))
            if step % 100 == 0:
                print(json.dumps({"epoch": epoch + 1, "step": step, "n": steps_per_epoch,
                                  "loss": losses[-1], "elapsed": round(time.time() - t0, 1)}), flush=True)
        metrics = {
            "epoch": epoch + 1,
            "train": eval_hidden(adapter, student_train, teacher_train, train_ids),
            "val": eval_hidden(adapter, student_val, teacher_val, val_ids),
            "loss_mean": sum(losses[-steps_per_epoch:]) / steps_per_epoch,
            "elapsed_sec": round(time.time() - t0, 1),
        }
        args.out_dir.mkdir(parents=True, exist_ok=True)
        torch.save({"adapter": adapter.state_dict(), "epoch": epoch + 1, "metrics": metrics},
                   args.out_dir / f"adapter_ep{epoch + 1}.pt")
        print(json.dumps({"epoch_done": epoch + 1, "metrics": metrics}, ensure_ascii=False, indent=2), flush=True)

    after_train = eval_hidden(adapter, student_train, teacher_train, train_ids)
    after_val = eval_hidden(adapter, student_val, teacher_val, val_ids)
    torch.save({"adapter": adapter.state_dict(), "epochs": args.epochs,
                "metrics": {"train": after_train, "val": after_val}},
               args.out_dir / "adapter_final.pt")
    report = {
        "experiment": "b1d_full_distillation",
        "train_n": len(train_ids),
        "val_n": len(val_ids),
        "epochs": args.epochs,
        "lr": args.lr,
        "adapter_params": sum(p.numel() for p in adapter.parameters()),
        "teacher": "T5Gemma2 native encoder hidden [T,640]",
        "student": "EG2 text final hidden [T,768], prompt included",
        "prompt": "summarize: ",
        "before": {"train": before_train, "val": before_val},
        "after": {"train": after_train, "val": after_val},
        "loss_first": losses[0] if losses else None,
        "loss_last": losses[-1] if losses else None,
        "loss_min": min(losses) if losses else None,
        "elapsed_sec": round(time.time() - t0, 1),
        "checkpoint": str((args.out_dir / "adapter_final.pt").relative_to(ROOT).as_posix()),
        "test_split_used": False,
        "note": "adapter only; decoder frozen; hidden cosine is not summary quality",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
