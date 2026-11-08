"""Extract EG2 layer-12 token features (512d) for the F5 clean splits.

Output: data/wave2c/eg2_layer12/{split}_{shard:04d}.npz
  h: [n, maxT, 512] float16
  mask, lengths, ids
No training; no test split is used.
"""
from __future__ import annotations

import argparse
import json
import sys
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
OUT = ROOT / "data/wave2c/eg2_layer12"
PROMPT = "summarize: "


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=MODEL)
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--splits", type=Path, default=SPLITS)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    ap.add_argument("--max-length", type=int, default=1024)
    ap.add_argument("--shard-size", type=int, default=50)
    ap.add_argument("--train-limit", type=int, default=300)
    ap.add_argument("--val-limit", type=int, default=100)
    ap.add_argument("--layer", type=int, default=12)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
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
    for split, limit in (("train", args.train_limit), ("val", args.val_limit)):
        ids = list(split_data[split])[:limit]
        for start in range(0, len(ids), args.shard_size):
            shard = start // args.shard_size
            path = args.out_dir / f"{split}_{shard:04d}.npz"
            if path.exists() and not args.overwrite:
                print(f"SKIP {path}", flush=True)
                continue
            chunk = ids[start : start + args.shard_size]
            hs, masks, lengths = [], [], []
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
                h = out.hidden_states[args.layer].float().reshape(-1, 512)
                n = int(h.shape[0])
                pad = torch.zeros(args.max_length, 512, dtype=h.dtype)
                pad[:n] = h
                hs.append(pad.numpy().astype(np.float16))
                mask = np.zeros(args.max_length, dtype=bool)
                mask[:n] = True
                masks.append(mask)
                lengths.append(n)
            np.savez(path, h=np.stack(hs), mask=np.stack(masks),
                     lengths=np.asarray(lengths, dtype=np.int32), ids=np.asarray(chunk))
            print(json.dumps({"wrote": str(path), "n": len(chunk),
                              "tokens_max": int(max(lengths)),
                              "elapsed": round(time.time() - t0, 1)}), flush=True)
    meta = {
        "model": str(args.model.relative_to(ROOT).as_posix()),
        "layer": args.layer,
        "dim": 512,
        "splits": {"train": args.train_limit, "val": args.val_limit},
        "max_length": args.max_length,
        "elapsed_sec": round(time.time() - t0, 1),
        "test_split_used": False,
    }
    (args.out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
                                            encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
