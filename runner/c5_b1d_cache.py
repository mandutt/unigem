"""Cache B1d teacher (T5Gemma2 encoder) and student (EG2) token hidden.

Cache layout:
  <out-dir>/<kind>/<split>_<shard:04d>.npz
    h:      [n, T, D] float16
    mask:   [n, T] bool
    lengths:[n] int32
    ids:    [n] unicode

The script is shard-resumable: existing shards are skipped. Test is never
loaded.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import time
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModel, AutoModelForSeq2SeqLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
EG2_PATH = ROOT / "data/models/embeddinggemma-2-f9972ac2"
T5_PATH = ROOT / "data/models/t5gemma-2-270m-270m"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
OUT = ROOT / "data/wave2c/b1d"
PROMPT = "summarize: "
MAX_LEN = 1024


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def t5_ids(tok, text: str) -> list[int]:
    ids = tok(text, add_special_tokens=True, truncation=True, max_length=MAX_LEN)["input_ids"]
    return [int(x) for x in ids]


def eg2_ids_same(tok, text: str) -> list[int]:
    base = tok(text, add_special_tokens=False, truncation=True, max_length=MAX_LEN - 1)["input_ids"]
    return [int(tok.bos_token_id)] + [int(x) for x in base]


def load_model(kind: str):
    if kind == "teacher":
        model = AutoModelForSeq2SeqLM.from_pretrained(
            str(T5_PATH), local_files_only=True, dtype=torch.bfloat16, low_cpu_mem_usage=True
        ).eval()
        return model.get_encoder()
    if kind == "student":
        model = AutoModel.from_pretrained(
            str(EG2_PATH), local_files_only=True, dtype=torch.float32, low_cpu_mem_usage=True
        ).eval()
        for name in ("vision_tower", "audio_tower", "embed_vision", "embed_audio"):
            if hasattr(model, name):
                setattr(model, name, None)
        return model.language_model
    raise ValueError(kind)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", required=True, choices=["teacher", "student"])
    ap.add_argument("--splits", nargs="+", default=["train", "val"], choices=["train", "val"])
    ap.add_argument("--shard-size", type=int, default=32)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    torch.set_num_threads(6)
    t0 = time.time()
    rows = read_jsonl(DATA)
    by_id = {str(r["id"]): r for r in rows}
    split_ids = json.loads(SPLITS.read_text(encoding="utf-8"))
    out_dir = args.out_dir / args.kind
    out_dir.mkdir(parents=True, exist_ok=True)

    t5_tok = AutoTokenizer.from_pretrained(str(T5_PATH), local_files_only=True)
    tok = AutoTokenizer.from_pretrained(
        str(T5_PATH if args.kind == "teacher" else EG2_PATH), local_files_only=True
    )
    model = load_model(args.kind)
    rss0 = None
    try:
        import psutil
        rss0 = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except Exception:
        pass

    meta = {
        "kind": args.kind,
        "prompt": PROMPT,
        "max_len": MAX_LEN,
        "shard_size": args.shard_size,
        "model": str((T5_PATH if args.kind == "teacher" else EG2_PATH).relative_to(ROOT).as_posix()),
        "splits": {},
        "rss_mb_start": round(rss0, 1) if rss0 else None,
    }
    total_done = 0
    for split in args.splits:
        ids = list(split_ids[split])
        if args.limit:
            ids = ids[: args.limit]
        n_shards = (len(ids) + args.shard_size - 1) // args.shard_size
        aligned = 0
        for start in range(0, len(ids), args.shard_size):
            shard = start // args.shard_size
            path = out_dir / f"{split}_{shard:04d}.npz"
            if path.exists() and path.stat().st_size > 0:
                print(f"SKIP {path.name}", flush=True)
                continue
            chunk = ids[start : start + args.shard_size]
            h_list = []
            masks = []
            lengths = []
            for rid in chunk:
                rec = by_id[rid]
                text = PROMPT + str(rec["passage"])
                a = eg2_ids_same(tok, text) if args.kind == "student" else t5_ids(t5_tok, text)
                b = t5_ids(t5_tok, text)
                if a != b:
                    raise SystemExit(f"TOKEN_ALIGNMENT_FAIL {rid} kind={args.kind}")
                aligned += 1
                enc = {
                    "input_ids": torch.tensor([b], dtype=torch.long),
                    "attention_mask": torch.ones(1, len(b), dtype=torch.long),
                }
                with torch.no_grad():
                    h = model(**enc).last_hidden_state[0].float().cpu().numpy()
                h_list.append(h.astype(np.float16))
                lengths.append(int(h.shape[0]))
            max_t = max(lengths)
            d = h_list[0].shape[1]
            arr = np.zeros((len(h_list), max_t, d), dtype=np.float16)
            mask = np.zeros((len(h_list), max_t), dtype=bool)
            for i, h in enumerate(h_list):
                arr[i, : h.shape[0]] = h
                mask[i, : h.shape[0]] = True
            tmp = path.with_suffix(".tmp.npz")
            np.savez(
                tmp,
                h=arr,
                mask=mask,
                lengths=np.asarray(lengths, dtype=np.int32),
                ids=np.asarray(chunk),
            )
            os.replace(tmp, path)
            total_done += len(chunk)
            print(
                f"WROTE {path.name} n={len(chunk)} maxT={max_t} D={d} "
                f"elapsed={time.time()-t0:.1f}s",
                flush=True,
            )
        meta["splits"][split] = {
            "n": len(ids),
            "shards": n_shards,
            "aligned": aligned,
            "alignment_rate": aligned / len(ids) if ids else 0.0,
        }
    meta["elapsed_sec"] = round(time.time() - t0, 1)
    meta["total_docs_written_this_run"] = total_done
    (out_dir / "cache_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(meta, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
