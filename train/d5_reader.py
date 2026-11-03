"""D-5.5 CTC reader — 구현 및 비용 probe.

구조(Addendum D D-5.5):
  입력 투영(→384) → 4층 Transformer(6 head, FF 1536) → CTC head
  프레임률 25Hz, blank=0, 학습 파라미터 ≤10M

이 파일은 두 가지 모드를 제공한다.
  --probe : 합성 특징으로 step 시간·피크 RSS를 측정 (D0-d)
  --features <npz> : 실제 특징 shard로 1 epoch 학습 (D-β 후속)
"""
from __future__ import annotations

import argparse
import json
import math
import os
import threading
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class PositionalEncoding(nn.Module):
    def __init__(self, d: int, max_len: int = 4096):
        super().__init__()
        pe = torch.zeros(max_len, d)
        pos = torch.arange(0, max_len, dtype=torch.float32).unsqueeze(1)
        div = torch.exp(torch.arange(0, d, 2, dtype=torch.float32) * (-math.log(10000.0) / d))
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div)
        self.register_buffer("pe", pe.unsqueeze(0), persistent=False)

    def forward(self, x):
        return x + self.pe[:, : x.size(1)]


class CTCReader(nn.Module):
    def __init__(self, in_dim: int, vocab: int, d: int = 384, layers: int = 4,
                 heads: int = 6, ff: int = 1536, dropout: float = 0.1, max_len: int = 4096):
        super().__init__()
        self.proj = nn.Linear(in_dim, d)
        self.pos = PositionalEncoding(d, max_len)
        enc = nn.TransformerEncoderLayer(
            d_model=d, nhead=heads, dim_feedforward=ff, dropout=dropout,
            activation="gelu", batch_first=True, norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(enc, num_layers=layers)
        self.norm = nn.LayerNorm(d)
        self.head = nn.Linear(d, vocab)

    def forward(self, x, lengths):
        # x: [B,T,in_dim], lengths: [B] (frames)
        h = self.pos(self.proj(x))
        # key padding mask: True = ignore
        T = x.size(1)
        pad = torch.arange(T, device=x.device)[None, :] >= lengths[:, None]
        h = self.encoder(h, src_key_padding_mask=pad)
        return self.head(self.norm(h))


def count_params(m):
    return sum(p.numel() for p in m.parameters() if p.requires_grad)


def probe(args):
    torch.set_num_threads(args.threads)
    torch.manual_seed(42)
    model = CTCReader(args.in_dim, args.vocab)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    B, T, D = args.batch, 400, args.in_dim
    x = torch.randn(B, T, D)
    # target lengths < T/4; random token ids 1..vocab-1
    tl = torch.randint(40, 100, (B,))
    targets = torch.randint(1, args.vocab, (int(tl.sum()),))
    in_len = torch.full((B,), T, dtype=torch.long)

    peak = {"rss": 0}
    stop = threading.Event()

    def watch():
        try:
            import psutil
            p = psutil.Process()
            while not stop.is_set():
                peak["rss"] = max(peak["rss"], p.memory_info().rss)
                time.sleep(0.02)
        except Exception:
            pass

    th = threading.Thread(target=watch, daemon=True)
    th.start()
    model.train()
    for _ in range(args.warmup):
        opt.zero_grad(set_to_none=True)
        logits = model(x, in_len)
        loss = F.ctc_loss(logits.log_softmax(-1).transpose(0, 1), targets, in_len, tl,
                          blank=0, zero_infinity=True)
        loss.backward()
        opt.step()
    t0 = time.time()
    for _ in range(args.steps):
        opt.zero_grad(set_to_none=True)
        logits = model(x, in_len)
        loss = F.ctc_loss(logits.log_softmax(-1).transpose(0, 1), targets, in_len, tl,
                          blank=0, zero_infinity=True)
        loss.backward()
        opt.step()
    dt = (time.time() - t0) / args.steps
    stop.set()
    # 6h = 1350 windows of 16s; batch steps
    windows = int(6 * 3600 / 16)
    steps_per_epoch = math.ceil(windows / args.batch)
    out = {
        "params": count_params(model),
        "batch": args.batch,
        "T": T,
        "in_dim": args.in_dim,
        "vocab": args.vocab,
        "threads": args.threads,
        "sec_per_step": dt,
        "steps_per_epoch_6h": steps_per_epoch,
        "epoch_sec_6h": dt * steps_per_epoch,
        "epoch_min_6h": dt * steps_per_epoch / 60,
        "peak_rss_mb": peak["rss"] / (1024 * 1024),
        "loss": float(loss.detach()),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--in-dim", type=int, default=1024)
    ap.add_argument("--vocab", type=int, default=3000)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    if not a.probe:
        ap.error("only --probe is implemented in this step")
    out = probe(a)
    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
