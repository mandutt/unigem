"""A2-null adapter smoke/training.

Memory features are 768d token sequences; adapter maps to T5Gemma2 decoder 640d.
T5Gemma2 is frozen; only the adapter (and optionally later a decoder LoRA) trains.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import psutil
import torch
from torch import nn
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from transformers.modeling_outputs import BaseModelOutput

ROOT = Path(__file__).resolve().parents[1]
T5 = ROOT / "data/models/t5gemma-2-270m-270m"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
FEATURES = ROOT / "data/wave2c/a2null"
OUT = ROOT / "data/models/f5_a2null"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rss_mb() -> float:
    return psutil.Process().memory_info().rss / 1e6


class Adapter(nn.Module):
    def __init__(self, d_in: int = 768, d_out: int = 640, hidden: int = 768):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, hidden),
            nn.GELU(),
            nn.Linear(hidden, d_out),
        )

    def forward(self, x):
        return self.net(x)


def load_feature_records(features_dir: Path, split: str = "train", limit: int = 0) -> list[dict]:
    paths = sorted(features_dir.glob(f"{split}_*.npz"))
    rows = []
    for path in paths:
        with np.load(path, allow_pickle=False) as z:
            ids = [str(x) for x in z["ids"].tolist()]
            for i, rid in enumerate(ids):
                rows.append(
                    {
                        "id": rid,
                        "z": torch.from_numpy(z["z"][i]).float(),
                        "mask": torch.from_numpy(z["mask"][i]).bool(),
                        "length": int(z["lengths"][i]),
                    }
                )
        if limit and len(rows) >= limit:
            break
    return rows[:limit] if limit else rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features-dir", type=Path, default=FEATURES)
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--t5", type=Path, default=T5)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--steps", type=int, default=5)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--max-target", type=int, default=512)
    ap.add_argument("--max-memory", type=int, default=1024)
    args = ap.parse_args()
    torch.set_num_threads(6)
    args.out.mkdir(parents=True, exist_ok=True)
    rows = read_jsonl(args.data)
    by_id = {str(r["id"]): r for r in rows}
    feats = load_feature_records(args.features_dir, "train", limit=max(args.steps * args.batch_size, 1))
    if not feats:
        raise SystemExit("no feature shards")
    tok = AutoTokenizer.from_pretrained(str(args.t5), local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        str(args.t5), local_files_only=True, dtype=torch.bfloat16, low_cpu_mem_usage=True
    )
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    adapter = Adapter().float()
    opt = torch.optim.AdamW(adapter.parameters(), lr=1e-4)
    print(json.dumps({"rss_after_load_mb": round(rss_mb(), 1), "features": len(feats)}, ensure_ascii=False), flush=True)

    step_times = []
    losses = []
    for step in range(args.steps):
        batch = feats[step * args.batch_size : (step + 1) * args.batch_size]
        zs, masks, labels = [], [], []
        for rec in batch:
            t = min(rec["length"], args.max_memory)
            zs.append(rec["z"][:t])
            m = torch.zeros(args.max_memory, dtype=torch.bool)
            m[:t] = True
            masks.append(m)
            target = by_id[rec["id"]]["summary"]
            enc = tok(
                str(target),
                return_tensors="pt",
                truncation=True,
                max_length=args.max_target,
                padding="max_length",
            )
            lab = enc["input_ids"].squeeze(0)
            lab[enc["attention_mask"].squeeze(0) == 0] = -100
            labels.append(lab)
        # pad z to max length in batch
        t_max = max(x.shape[0] for x in zs)
        z_pad = torch.zeros(len(zs), t_max, 768)
        m_pad = torch.zeros(len(zs), t_max, dtype=torch.bool)
        for i, (z, m) in enumerate(zip(zs, masks)):
            z_pad[i, : z.shape[0]] = z
            m_pad[i, : m.shape[0]] = m[: z.shape[0]]
        labels = torch.stack(labels)
        t0 = torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
        import time
        st = time.time()
        memory = adapter(z_pad).to(torch.bfloat16)
        out = model(
            encoder_outputs=BaseModelOutput(last_hidden_state=memory),
            attention_mask=m_pad,
            labels=labels,
        )
        loss = out.loss
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        step_times.append(time.time() - st)
        losses.append(float(loss.detach()))
        print(json.dumps({"step": step + 1, "loss": round(losses[-1], 4), "sec": round(step_times[-1], 2), "rss_mb": round(rss_mb(), 1)}, ensure_ascii=False), flush=True)
        if not np.isfinite(losses[-1]):
            raise SystemExit("non-finite loss")
    torch.save({"adapter": adapter.state_dict()}, args.out / "adapter_smoke.pt")
    result = {"steps": args.steps, "losses": losses, "step_times": step_times,
              "rss_peak_mb": round(rss_mb(), 1), "adapter_saved": (args.out / "adapter_smoke.pt").resolve().relative_to(ROOT).as_posix()}
    (args.out / "smoke.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
