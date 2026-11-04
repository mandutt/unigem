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
from pathlib import Path

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


class FCSoftmaxReader(nn.Module):
    """4-state softmax mix over 4 x 1024 layer features, then the CTC reader.

    Input is the existing F-C concat tensor [B, T, 4096]. The four 1024-d
    slices are LayerNorm'ed and mixed with a learned softmax weight. This is
    the Addendum D-5.4 canonical mix; F-C-concat remains a separate comparator.
    """

    def __init__(self, vocab: int, d: int = 384, layers: int = 4,
                 heads: int = 6, ff: int = 1536, dropout: float = 0.1,
                 max_len: int = 4096):
        super().__init__()
        self.norms = nn.ModuleList([nn.LayerNorm(1024) for _ in range(4)])
        self.w = nn.Parameter(torch.zeros(4))
        self.reader = CTCReader(1024, vocab, d=d, layers=layers, heads=heads,
                                ff=ff, dropout=dropout, max_len=max_len)

    def forward(self, x, lengths):
        # x: [B, T, 4*1024]
        b, t, c = x.shape
        if c != 4096:
            raise ValueError(f"FCSoftmaxReader expects 4096 features, got {c}")
        parts = x.view(b, t, 4, 1024)
        w = torch.softmax(self.w, dim=0)
        h = sum(w[i] * self.norms[i](parts[:, :, i, :]) for i in range(4))
        return self.reader(h, lengths)


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


def evaluate_cer(model, d, vocab, batch=8, features_path=None, device="cpu"):
    """Greedy CTC CER on a feature npz; returns (cer, err, ref)."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    device = torch.device(device)
    feats = _load_feats(d, features_path) if features_path else d["feats"]
    lens = d["lens"].astype(np.int64)
    flat = "offsets" in d.files
    off = d["offsets"].astype(np.int64) if flat else None
    from eval.normalize import _edit_distance, normalize_nospace
    texts = [normalize_nospace(str(x)) for x in d["texts"]]
    chars = vocab["chars"]
    was_training = model.training
    model.eval()
    preds = []
    with torch.no_grad():
        for b in range(0, len(lens), batch):
            ids = np.arange(b, min(b + batch, len(lens)))
            maxlen = int(lens[ids].max())
            if flat:
                rows = [np.asarray(feats[off[i]:off[i] + lens[i]], dtype=np.float32) for i in ids]
                rows = [np.pad(r, ((0, maxlen - len(r)), (0, 0))) if len(r) < maxlen else r for r in rows]
            else:
                rows = [np.asarray(feats[i, :maxlen, :], dtype=np.float32) for i in ids]
            x = torch.from_numpy(np.stack(rows, axis=0)).to(device)
            il = torch.from_numpy(lens[ids]).to(device)
            am = model(x, il).argmax(-1).cpu().numpy()
            for row, n in zip(am, lens[ids]):
                out = []
                prev = -1
                for v in row[:n]:
                    v = int(v)
                    if v != 0 and v != prev:
                        out.append(chars[v - 1])
                    prev = v
                preds.append("".join(out))
    model.train(was_training)
    err = sum(_edit_distance(normalize_nospace(p), t) for p, t in zip(preds, texts))
    ref = sum(len(t) for t in texts)
    return err / max(1, ref), err, ref


def _load_feats(d, features_path):
    """Prefer a sibling .feats.npy memmap for large flat feature files.

    The F-C npz stores ~4.1 GB of float16 rows. np.load(path)['feats'] copies the
    whole array into RAM; a sibling fc.feats.npy lets training slice it lazily.
    """
    p = Path(features_path)
    npy = p.with_suffix(".feats.npy")
    if npy.exists():
        return np.load(npy, mmap_mode="r")
    return d["feats"]


def train_from_npz(args):
    import sys
    from pathlib import Path
    torch.set_num_threads(args.threads)
    torch.manual_seed(args.seed)
    device = torch.device(args.device if args.device == "cuda" and torch.cuda.is_available() else "cpu")
    if args.device == "cuda" and device.type != "cuda":
        print("WARNING: --device cuda requested but CUDA is unavailable; using CPU", flush=True)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)
    print(f"device={device}", flush=True)
    d = np.load(args.features, allow_pickle=True)
    feats = _load_feats(d, args.features)
    lens = d["lens"].astype(np.int64)
    flat = "offsets" in d.files
    offsets_f = d["offsets"].astype(np.int64) if flat else None
    vocab = json.load(open(args.vocab_file, encoding="utf-8"))
    n_chars = len(vocab["chars"])
    if args.retarget:
        c2i = vocab["char2id"]
        tlist = [[c2i[c] for c in str(t) if c in c2i and c != " "] for t in d["texts"]]
        target_lens = np.asarray([len(t) for t in tlist], dtype=np.int64)
        targets_all = np.asarray([i for t in tlist for i in t], dtype=np.int64)
        print(f"retargeted {len(tlist)} clips chars={len(targets_all)}", flush=True)
    else:
        targets_all = d["targets"].astype(np.int64)
        target_lens = d["target_lens"].astype(np.int64)
    print(f"features={feats.shape} clips={len(lens)} chars={n_chars} flat={flat}", flush=True)
    in_dim = int(feats.shape[1] if flat else feats.shape[2])
    arch = getattr(args, "arch", "base")
    if arch == "softmax":
        if in_dim != 4096:
            raise ValueError(f"softmax arch expects 4096 features, got {in_dim}")
        model = FCSoftmaxReader(n_chars + 1, d=args.d_model, layers=args.layers,
                                heads=args.heads, ff=args.ff, dropout=args.dropout)
    else:
        model = CTCReader(in_dim, n_chars + 1, d=args.d_model, layers=args.layers,
                          heads=args.heads, ff=args.ff, dropout=args.dropout)
    print(f"arch={arch} params={count_params(model)}", flush=True)
    model.to(device)
    if args.init_ckpt:
        ck = torch.load(args.init_ckpt, map_location="cpu", weights_only=False)
        state = ck["model"] if isinstance(ck, dict) and "model" in ck else ck
        missing, unexpected = model.load_state_dict(state, strict=False)
        print(f"init_ckpt={args.init_ckpt} missing={len(missing)} unexpected={len(unexpected)}", flush=True)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(1, args.epochs * max(1, len(lens) // (args.batch * args.grad_accum))))
    start_epoch = 1
    best = 1e9
    patience = 0
    if args.resume:
        ck = torch.load(args.resume, map_location="cpu", weights_only=False)
        model.load_state_dict(ck["model"])
        if "optimizer" in ck:
            opt.load_state_dict(ck["optimizer"])
            for state in opt.state.values():
                for k, v in state.items():
                    if torch.is_tensor(v):
                        state[k] = v.to(device)
        if "scheduler" in ck:
            sched.load_state_dict(ck["scheduler"])
        start_epoch = int(ck.get("epoch", 0)) + 1
        best = float(ck.get("best", best))
        patience = int(ck.get("patience", patience))
        if "torch_rng" in ck:
            torch.set_rng_state(ck["torch_rng"])
            if device.type == "cuda" and "cuda_rng" in ck:
                torch.cuda.set_rng_state_all(ck["cuda_rng"])
        if "numpy_rng" in ck:
            np.random.set_state(ck["numpy_rng"])
        print(f"resume={args.resume} start_epoch={start_epoch} best={best:.4f} patience={patience}", flush=True)
    # target offsets
    offsets = np.zeros(len(lens) + 1, dtype=np.int64)
    offsets[1:] = np.cumsum(target_lens)
    if not args.resume:
        np.random.seed(args.seed)
    dev = np.load(args.dev_features, allow_pickle=True) if args.dev_features else None
    ckdir = Path(args.ckpt_dir)
    ckdir.mkdir(parents=True, exist_ok=True)
    for ep in range(start_epoch, args.epochs + 1):
        if args.sampler == "balanced":
            secs = lens.astype(np.float32) / 25.0
            b4 = secs <= 4.0
            b8 = (secs > 4.0) & (secs <= 8.0)
            b16 = secs > 8.0
            probs = np.zeros(len(lens), dtype=np.float64)
            for mask, target in ((b4, args.balanced_4), (b8, args.balanced_8), (b16, args.balanced_16)):
                n = int(mask.sum())
                if n:
                    probs[mask] = target / n
            probs /= probs.sum()
            idx = np.random.choice(len(lens), size=len(lens), replace=True, p=probs)
            print(f"sampler=balanced idx_counts b4={int(b4[idx].sum())} b8={int(b8[idx].sum())} b16={int(b16[idx].sum())}", flush=True)
        else:
            idx = np.arange(len(lens))
            np.random.shuffle(idx)
        model.train()
        tot_loss = 0.0
        nb = 0
        micro = 0
        t0 = time.time()
        opt.zero_grad(set_to_none=True)
        for b in range(0, len(idx), args.batch):
            if args.max_batches and micro >= args.max_batches:
                break
            ids = idx[b:b + args.batch]
            maxlen = int(lens[ids].max())
            if flat:
                rows = [np.asarray(feats[offsets_f[i]:offsets_f[i] + lens[i]], dtype=np.float32) for i in ids]
                rows = [np.pad(r, ((0, maxlen - len(r)), (0, 0))) if len(r) < maxlen else r for r in rows]
            else:
                rows = [np.asarray(feats[i, :maxlen, :], dtype=np.float32) for i in ids]
            x = torch.from_numpy(np.stack(rows, axis=0)).to(device)
            il = torch.from_numpy(lens[ids]).to(device)
            tgt = []
            tl = []
            for i in ids:
                t = targets_all[offsets[i]:offsets[i + 1]]
                tgt.append(t)
                tl.append(len(t))
            tgt = torch.from_numpy(np.concatenate(tgt).astype(np.int64)).to(device)
            tl = torch.from_numpy(np.asarray(tl, dtype=np.int64)).to(device)
            logits = model(x, il)
            loss = F.ctc_loss(logits.log_softmax(-1).transpose(0, 1), tgt, il, tl,
                              blank=0, zero_infinity=True)
            (loss / args.grad_accum).backward()
            tot_loss += float(loss.detach())
            micro += 1
            if micro % args.grad_accum == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
                opt.step()
                sched.step()
                opt.zero_grad(set_to_none=True)
                nb += 1
        if micro % args.grad_accum != 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            sched.step()
            opt.zero_grad(set_to_none=True)
            nb += 1
        line = f"epoch {ep}/{args.epochs} loss={tot_loss/max(1,micro):.4f} steps={nb} micro={micro} sec={time.time()-t0:.1f}"
        if dev is not None:
            cer, err, ref = evaluate_cer(model, dev, vocab, batch=args.batch,
                                         features_path=args.dev_features, device=device)
            line += f" dev_cer={cer:.4f} ({err}/{ref})"
            if cer < best - 1e-6:
                best = cer
                patience = 0
                torch.save({"model": model.state_dict(), "in_dim": in_dim, "vocab": n_chars + 1,
                            "d_model": args.d_model, "layers": args.layers, "heads": args.heads,
                            "ff": args.ff, "arm": args.arm, "arch": arch, "dev_cer": cer}, ckdir / (args.arm + ".best.pt"))
            else:
                patience += 1
        print(line, flush=True)
        torch.save({"model": model.state_dict(), "optimizer": opt.state_dict(),
                    "scheduler": sched.state_dict(), "epoch": ep, "best": best,
                    "patience": patience, "torch_rng": torch.get_rng_state(),
                    "cuda_rng": torch.cuda.get_rng_state_all() if device.type == "cuda" else None,
                    "numpy_rng": np.random.get_state(),
                    "in_dim": in_dim, "vocab": n_chars + 1, "d_model": args.d_model,
                    "layers": args.layers, "heads": args.heads, "ff": args.ff,
                    "arm": args.arm, "arch": arch}, ckdir / (args.arm + ".last.pt"))
        if dev is not None and patience >= args.patience:
            print(f"early stop patience={args.patience} best={best:.4f}", flush=True)
            break
    out = ckdir / (args.arm + ".pt")
    torch.save({"model": model.state_dict(), "in_dim": in_dim, "vocab": n_chars + 1,
                "d_model": args.d_model, "layers": args.layers, "heads": args.heads,
                "ff": args.ff, "arm": args.arm, "arch": arch}, out)
    print("saved", out, flush=True)


def decode_npz(args):
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
    from eval.normalize import _edit_distance, normalize_nospace
    torch.set_num_threads(args.threads)
    d = np.load(args.features, allow_pickle=True)
    feats = _load_feats(d, args.features)
    lens = d["lens"].astype(np.int64)
    flat = "offsets" in d.files
    offsets_f = d["offsets"].astype(np.int64) if flat else None
    texts = [str(x) for x in d["texts"]]
    vocab = json.load(open(args.vocab_file, encoding="utf-8"))
    chars = vocab["chars"]
    ck = torch.load(args.ckpt, map_location="cpu", weights_only=False)
    arch = ck.get("arch", "base")
    if arch == "softmax":
        model = FCSoftmaxReader(ck["vocab"], d=ck["d_model"], layers=ck["layers"],
                                heads=ck["heads"], ff=ck["ff"], dropout=0.0)
    else:
        model = CTCReader(ck["in_dim"], ck["vocab"], d=ck["d_model"], layers=ck["layers"],
                          heads=ck["heads"], ff=ck["ff"], dropout=0.0)
    model.load_state_dict(ck["model"])
    was_training = model.training
    model.eval()
    preds = []
    with torch.no_grad():
        for b in range(0, len(lens), args.batch):
            ids = np.arange(b, min(b + args.batch, len(lens)))
            maxlen = int(lens[ids].max())
            if flat:
                rows = [np.asarray(feats[offsets_f[i]:offsets_f[i] + lens[i]], dtype=np.float32) for i in ids]
                rows = [np.pad(r, ((0, maxlen - len(r)), (0, 0))) if len(r) < maxlen else r for r in rows]
            else:
                rows = [np.asarray(feats[i, :maxlen, :], dtype=np.float32) for i in ids]
            x = torch.from_numpy(np.stack(rows, axis=0))
            il = torch.from_numpy(lens[ids])
            logits = model(x, il)
            am = logits.argmax(-1).cpu().numpy()
            for row, n in zip(am, lens[ids]):
                out = []
                prev = -1
                for v in row[:n]:
                    v = int(v)
                    if v != 0 and v != prev:
                        out.append(chars[v - 1])
                    prev = v
                preds.append("".join(out))
    ids = [str(x) for x in d["ids"]]
    refs_norm = [normalize_nospace(t) for t in texts]
    preds_norm = [normalize_nospace(p) for p in preds]
    err = sum(_edit_distance(p, t) for p, t in zip(preds_norm, refs_norm))
    ref = sum(len(t) for t in refs_norm)
    raw_err = sum(_edit_distance(p.replace(" ", ""), t.replace(" ", "")) for p, t in zip(preds, texts))
    raw_ref = sum(len(t.replace(" ", "")) for t in texts)
    sents = []
    for i, p, t in zip(ids, preds, texts):
        pp, tt = normalize_nospace(p), normalize_nospace(t)
        e = _edit_distance(pp, tt)
        sents.append({"id": i, "ref": t, "pred": p, "ref_norm": tt, "pred_norm": pp,
                      "err": e, "ref_chars": len(tt), "cer": e / max(1, len(tt))})
    out = {"n": len(texts), "cer": err / max(1, ref), "errors": err, "ref_chars": ref,
           "cer_raw": raw_err / max(1, raw_ref), "raw_errors": raw_err, "raw_ref_chars": raw_ref,
           "normalization": "normalize_nospace", "sentences": sents}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if args.out:
        json.dump(out, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--features", default="")
    ap.add_argument("--dev-features", default="")
    ap.add_argument("--vocab-file", default="")
    ap.add_argument("--arm", default="fd")
    ap.add_argument("--arch", default="base", choices=["base", "softmax"])
    ap.add_argument("--retarget", action="store_true", help="re-encode d['texts'] with --vocab-file")
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--patience", type=int, default=5)
    ap.add_argument("--max-batches", type=int, default=0)
    ap.add_argument("--in-dim", type=int, default=1024)
    ap.add_argument("--vocab", type=int, default=3000)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--grad-accum", type=int, default=1)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--d-model", type=int, default=384)
    ap.add_argument("--layers", type=int, default=4)
    ap.add_argument("--heads", type=int, default=6)
    ap.add_argument("--ff", type=int, default=1536)
    ap.add_argument("--dropout", type=float, default=0.1)
    ap.add_argument("--ckpt-dir", default="train/ckpt")
    ap.add_argument("--ckpt", default="")
    ap.add_argument("--init-ckpt", default="", help="initialize model weights from a 2A checkpoint (B0-prime warm start)")
    ap.add_argument("--resume", default="", help="full checkpoint (model+optimizer+scheduler+epoch+RNG) to resume")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="training/eval device")
    ap.add_argument("--sampler", default="natural", choices=["natural", "balanced"],
                    help="B3 uses balanced; B0-prime/B3-nat use natural")
    ap.add_argument("--balanced-4", type=float, default=0.40)
    ap.add_argument("--balanced-8", type=float, default=0.30)
    ap.add_argument("--balanced-16", type=float, default=0.30)
    ap.add_argument("--decode", action="store_true")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    if a.decode:
        decode_npz(a)
        return
    if a.features:
        train_from_npz(a)
        return
    if not a.probe:
        ap.error("choose --probe or --features")
    out = probe(a)
    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
