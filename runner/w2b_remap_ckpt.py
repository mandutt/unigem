"""Remap a V1 CTC checkpoint to a V2 vocabulary by character identity.

The existing d5_reader.py --init-ckpt path requires matching tensor shapes.
This utility copies blank and shared character rows, initializes new V2 rows
with a small normal distribution, and writes a checkpoint that can be loaded
by d5_reader.py --vocab-file data/wave2b/vocab_v2.json.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="data/wave2a_lite/frozen/w2a_fc_concat_s42.best.pt")
    ap.add_argument("--old-vocab", default="data/wave2a_lite/vocab.json")
    ap.add_argument("--new-vocab", default="data/wave2b/vocab_v2.json")
    ap.add_argument("--out", default="data/wave2b/ckpt_v2/w2a_fc_concat_s42_v2head.pt")
    a = ap.parse_args()
    ck = torch.load(a.ckpt, map_location="cpu", weights_only=False)
    state = ck["model"] if isinstance(ck, dict) and "model" in ck else ck
    old_v = json.load(open(a.old_vocab, encoding="utf-8"))
    new_v = json.load(open(a.new_vocab, encoding="utf-8"))
    old_chars = old_v["chars"]
    new_chars = new_v["chars"]
    n_old = len(old_chars) + 1
    n_new = len(new_chars) + 1
    head_keys = [k for k in state if k.endswith("head.weight")]
    bias_keys = [k for k in state if k.endswith("head.bias")]
    if len(head_keys) != 1:
        raise SystemExit(f"expected one head.weight, got {head_keys}")
    hk = head_keys[0]
    bk = bias_keys[0] if bias_keys else None
    old_head = state[hk]
    if old_head.shape[0] != n_old:
        raise SystemExit(f"old head rows {old_head.shape[0]} != old vocab {n_old}")
    new_head = torch.empty(n_new, old_head.shape[1], dtype=old_head.dtype)
    torch.nn.init.normal_(new_head, mean=0.0, std=0.02)
    new_head[0].copy_(old_head[0])
    shared = 0
    for i, c in enumerate(old_chars):
        j = new_v["char2id"].get(c)
        if j is None:
            continue
        new_head[j].copy_(old_head[i + 1])
        shared += 1
    state = dict(state)
    state[hk] = new_head
    if bk is not None:
        old_bias = state[bk]
        new_bias = torch.zeros(n_new, dtype=old_bias.dtype)
        new_bias[0].copy_(old_bias[0])
        for i, c in enumerate(old_chars):
            j = new_v["char2id"].get(c)
            if j is not None:
                new_bias[j].copy_(old_bias[i + 1])
        state[bk] = new_bias
    out = {
        "model": state,
        "in_dim": ck.get("in_dim"),
        "vocab": n_new,
        "d_model": ck.get("d_model"),
        "layers": ck.get("layers"),
        "heads": ck.get("heads"),
        "ff": ck.get("ff"),
        "arch": ck.get("arch", "base"),
        "arm": ck.get("arm", "w2a_fc_concat_s42") + "_v2head",
        "remap": {"from": a.old_vocab, "to": a.new_vocab,
                  "old_rows": n_old, "new_rows": n_new, "shared_chars": shared,
                  "source_ckpt": a.ckpt},
    }
    out_path = Path(a.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(out, out_path)
    print(json.dumps({"out": str(out_path), "old_rows": n_old, "new_rows": n_new,
                      "shared_chars": shared, "new_chars": n_new - n_old}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
