"""A2-null full adapter training (1 epoch default).

Loads one feature shard at a time to avoid holding the 2.4GB cache in RAM.
T5Gemma2 is frozen; only the adapter trains.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
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
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
FEATURES = ROOT / "data/wave2c/a2null"
OUT = ROOT / "data/models/f5_a2null_full"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rss_mb() -> float:
    return psutil.Process().memory_info().rss / 1e6


class Adapter(nn.Module):
    def __init__(self, d_in: int = 768, d_out: int = 640, hidden: int = 768):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d_in, hidden), nn.GELU(), nn.Linear(hidden, d_out))

    def forward(self, x):
        return self.net(x)


def shard_paths(features_dir: Path, split: str) -> list[Path]:
    return sorted(features_dir.glob(f"{split}_*.npz"))


def load_shard(path: Path) -> list[dict]:
    with np.load(path, allow_pickle=False) as z:
        ids = [str(x) for x in z["ids"].tolist()]
        return [{"id": rid, "z": z["z"][i].copy(), "length": int(z["lengths"][i])} for i, rid in enumerate(ids)]


def make_batch(batch, by_id, tok, max_memory: int, max_target: int):
    zs, masks, labels = [], [], []
    for rec in batch:
        t = min(rec["length"], max_memory)
        zs.append(torch.from_numpy(rec["z"][:t]).float())
        m = torch.zeros(max_memory, dtype=torch.bool)
        m[:t] = True
        masks.append(m)
        target = str(by_id[rec["id"]]["summary"])
        # The tokenizer adds <bos> but not <eos>. Training labels must contain
        # the content followed by <eos>; the model prepends <bos> itself when
        # shifting labels. Including <bos> in labels would teach the decoder to
        # emit <bos> first and would never teach it to stop.
        enc = tok(
            target,
            return_tensors="pt",
            truncation=True,
            max_length=max_target - 1,
            padding=False,
            add_special_tokens=False,
        )
        content = enc["input_ids"].squeeze(0)
        n = int(content.numel())
        lab = torch.full((max_target,), tok.pad_token_id, dtype=torch.long)
        lab[:n] = content
        lab[n] = tok.eos_token_id
        valid = torch.zeros(max_target, dtype=torch.bool)
        valid[: n + 1] = True
        lab[~valid] = -100
        labels.append(lab)
    t_max = max(x.shape[0] for x in zs)
    z_pad = torch.zeros(len(zs), t_max, 768, dtype=torch.float32)
    m_pad = torch.zeros(len(zs), t_max, dtype=torch.bool)
    for i, (z, m) in enumerate(zip(zs, masks)):
        z_pad[i, : z.shape[0]] = z
        m_pad[i, : z.shape[0]] = m[: z.shape[0]]
    return z_pad, m_pad, torch.stack(labels)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features-dir", type=Path, default=FEATURES)
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--splits", type=Path, default=SPLITS)
    ap.add_argument("--t5", type=Path, default=T5)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--max-memory", type=int, default=1024)
    ap.add_argument("--max-target", type=int, default=512)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--checkpoint-every", type=int, default=100)
    ap.add_argument("--val-limit", type=int, default=0)
    ap.add_argument("--max-train", type=int, default=0)
    args = ap.parse_args()
    torch.set_num_threads(6)
    args.out.mkdir(parents=True, exist_ok=True)
    rows = read_jsonl(args.data)
    by_id = {str(r["id"]): r for r in rows}
    split_sizes = json.loads(args.splits.read_text(encoding="utf-8"))["sizes"]
    train_paths = shard_paths(args.features_dir, "train")
    val_paths = shard_paths(args.features_dir, "val")
    if not train_paths:
        raise SystemExit("no train features")
    tok = AutoTokenizer.from_pretrained(str(args.t5), local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        str(args.t5), local_files_only=True, dtype=torch.bfloat16, low_cpu_mem_usage=True
    ).eval()
    for p in model.parameters():
        p.requires_grad_(False)
    adapter = Adapter().float()
    opt = torch.optim.AdamW(adapter.parameters(), lr=args.lr)
    start_epoch = 0
    global_step = 0
    ckpt = args.out / "last.pt"
    if ckpt.exists():
        state = torch.load(ckpt, map_location="cpu")
        adapter.load_state_dict(state["adapter"])
        opt.load_state_dict(state["optimizer"])
        start_epoch = int(state.get("epoch", 0))
        global_step = int(state.get("global_step", 0))
        print(json.dumps({"resume": str(ckpt), "epoch": start_epoch, "step": global_step}), flush=True)

    print(json.dumps({"train": split_sizes["train"], "val": split_sizes["val"],
                      "rss_load_mb": round(rss_mb(), 1)}, ensure_ascii=False), flush=True)
    report = {"train_n": split_sizes["train"], "val_n": split_sizes["val"], "epochs": args.epochs,
              "start_epoch": start_epoch, "steps": []}
    rng = random.Random(42)
    for epoch in range(start_epoch, args.epochs):
        ep_start = time.time()
        losses = []
        seen = 0
        paths = train_paths[:]
        rng.shuffle(paths)
        for path in paths:
            shard = load_shard(path)
            rng.shuffle(shard)
            for rec in shard:
                if args.max_train and seen >= args.max_train:
                    break
                seen += 1
                z, m, labels = make_batch([rec], by_id, tok, args.max_memory, args.max_target)
                st = time.time()
                memory = adapter(z).to(torch.bfloat16)
                out = model(encoder_outputs=BaseModelOutput(last_hidden_state=memory), attention_mask=m, labels=labels)
                loss = out.loss
                opt.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(adapter.parameters(), 1.0)
                opt.step()
                global_step += 1
                losses.append(float(loss.detach()))
                if global_step % 10 == 0:
                    print(json.dumps({"epoch": epoch + 1, "step": global_step, "loss": round(losses[-1], 4),
                                      "sec": round(time.time() - st, 2), "rss_mb": round(rss_mb(), 1)}), flush=True)
                if global_step % args.checkpoint_every == 0:
                    torch.save({"adapter": adapter.state_dict(), "optimizer": opt.state_dict(),
                                "epoch": epoch, "global_step": global_step}, ckpt)
            if args.max_train and seen >= args.max_train:
                break
        # val teacher-forced loss; one shard at a time
        adapter.eval()
        val_losses = []
        val_seen = 0
        with torch.inference_mode():
            for path in val_paths:
                shard = load_shard(path)
                for rec in shard:
                    if args.val_limit and val_seen >= args.val_limit:
                        break
                    val_seen += 1
                    z, m, labels = make_batch([rec], by_id, tok, args.max_memory, args.max_target)
                    memory = adapter(z).to(torch.bfloat16)
                    out = model(encoder_outputs=BaseModelOutput(last_hidden_state=memory), attention_mask=m, labels=labels)
                    val_losses.append(float(out.loss.detach()))
                if args.val_limit and val_seen >= args.val_limit:
                    break
        adapter.train()
        epoch_info = {"epoch": epoch + 1, "steps": len(losses), "train_loss": sum(losses) / len(losses),
                      "val_loss": sum(val_losses) / len(val_losses) if val_losses else None,
                      "elapsed_sec": round(time.time() - ep_start, 1)}
        report["steps"].append(epoch_info)
        print(json.dumps(epoch_info, ensure_ascii=False), flush=True)
        torch.save({"adapter": adapter.state_dict(), "optimizer": opt.state_dict(),
                    "epoch": epoch + 1, "global_step": global_step}, ckpt)
        torch.save({"adapter": adapter.state_dict()}, args.out / "adapter.pt")
    report["final"] = {"global_step": global_step, "rss_mb": round(rss_mb(), 1)}
    (args.out / "train_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
