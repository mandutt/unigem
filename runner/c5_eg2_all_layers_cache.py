"""Extract all EG2 hidden layers in one forward pass.

The prior layer cache script reran the model once per layer. This script runs
the model once per document and writes the same per-layer npz layout for every
requested layer, so a full layer sweep costs roughly one forward pass.

Output:
  <out-root>/<out-prefix><L>/{train,val}_{shard:04d}.npz
  h: [n, max_length, 512] float16
  mask, lengths, ids
No training; test split is never used.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "data/models/embeddinggemma-2-f9972ac2"
T5_PATH = ROOT / "data/models/t5gemma-2-270m-270m"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
OUT_ROOT = ROOT / "data/wave2c"
PROMPT = "summarize: "


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def parse_layers(spec: str) -> list[int]:
    layers: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            layers.update(range(int(a), int(b) + 1))
        else:
            layers.add(int(part))
    return sorted(layers)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=MODEL)
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--splits", type=Path, default=SPLITS)
    ap.add_argument("--out-root", type=Path, default=OUT_ROOT)
    ap.add_argument("--out-prefix", default="eg2_layer")
    ap.add_argument("--layers", default="0-24")
    ap.add_argument("--max-length", type=int, default=1024)
    ap.add_argument("--shard-size", type=int, default=50)
    ap.add_argument("--train-limit", type=int, default=300)
    ap.add_argument("--val-limit", type=int, default=100)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    args.out_root = args.out_root if args.out_root.is_absolute() else ROOT / args.out_root
    layers = parse_layers(args.layers)
    args.out_root.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(6)

    rows = read_jsonl(args.data)
    by_id = {str(r["id"]): r for r in rows}
    split_data = json.loads(args.splits.read_text(encoding="utf-8"))
    tok = AutoTokenizer.from_pretrained(str(args.model), local_files_only=True)
    t5_tok = AutoTokenizer.from_pretrained(str(T5_PATH), local_files_only=True)
    model = AutoModel.from_pretrained(
        str(args.model), local_files_only=True, dtype=torch.float32, low_cpu_mem_usage=True
    ).eval()
    for name in ("vision_tower", "audio_tower", "embed_vision", "embed_audio"):
        if hasattr(model, name):
            setattr(model, name, None)

    t0 = time.time()
    layer_dirs = {L: args.out_root / f"{args.out_prefix}{L}" for L in layers}
    for d in layer_dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    for split, limit in (("train", args.train_limit), ("val", args.val_limit)):
        ids = list(split_data[split])[:limit]
        for start in range(0, len(ids), args.shard_size):
            shard = start // args.shard_size
            chunk = ids[start : start + args.shard_size]
            paths = {L: layer_dirs[L] / f"{split}_{shard:04d}.npz" for L in layers}
            if all(p.exists() for p in paths.values()) and not args.overwrite:
                print(json.dumps({"skip": str(layer_dirs[layers[0]] / f"{split}_{shard:04d}.npz")}), flush=True)
                continue

            per_layer: dict[int, list[np.ndarray]] = {L: [] for L in layers}
            layer_dims: dict[int, int] = {}
            lengths: list[int] = []
            for rid in chunk:
                rec = by_id[rid]
                text = PROMPT + str(rec["passage"])
                ids_t = t5_tok(text, add_special_tokens=True, truncation=True,
                               max_length=args.max_length)["input_ids"]
                enc = {
                    "input_ids": torch.tensor([ids_t], dtype=torch.long),
                    "attention_mask": torch.ones(1, len(ids_t), dtype=torch.long),
                }
                with torch.inference_mode():
                    out = model.language_model(**enc, output_hidden_states=True)
                n = min(int(out.hidden_states[0].shape[1]), args.max_length)
                lengths.append(n)
                for L in layers:
                    hs = out.hidden_states[L].float()
                    dim = int(hs.shape[-1])
                    layer_dims[L] = dim
                    h = hs.reshape(-1, dim)[:n]
                    pad = np.zeros((args.max_length, dim), dtype=np.float16)
                    pad[:n] = h.numpy().astype(np.float16)
                    per_layer[L].append(pad)

            mask = np.zeros((len(chunk), args.max_length), dtype=bool)
            for i, n in enumerate(lengths):
                mask[i, :n] = True
            ids_arr = np.asarray(chunk)
            lengths_arr = np.asarray(lengths, dtype=np.int32)
            for L in layers:
                np.savez(paths[L], h=np.stack(per_layer[L]), mask=mask,
                         lengths=lengths_arr, ids=ids_arr)
            print(json.dumps({
                "split": split, "shard": shard, "n": len(chunk),
                "tokens_max": int(max(lengths)) if lengths else 0,
                "elapsed": round(time.time() - t0, 1),
            }), flush=True)

    elapsed = round(time.time() - t0, 1)
    for L in layers:
        dim = int(per_layer[L][0].shape[-1]) if per_layer.get(L) else 0
        meta = {
            "model": str(args.model.relative_to(ROOT).as_posix()),
            "layer": L,
            "layer_kind": "embedding" if L == 0 else ("projected_output" if dim == 768 else "transformer"),
            "dim": dim if dim else None,
            "splits": {"train": args.train_limit, "val": args.val_limit},
            "max_length": args.max_length,
            "elapsed_sec": elapsed,
            "test_split_used": False,
        }
        (layer_dirs[L] / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps({"layers": layers, "elapsed_sec": elapsed,
                      "out_root": str(args.out_root.relative_to(ROOT).as_posix())},
                     ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
