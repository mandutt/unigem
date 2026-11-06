"""Extract A2-null token features: EG2 final 768 + layer-12 PCA 256 injection.

Output shards:
  data/wave2c/a2null/{split}_{shard:04d}.npz
    z:      [n, maxT, 768] float16
    mask:   [n, maxT] bool
    lengths:[n] int32
    ids:    [n] unicode
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
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
OUT = ROOT / "data/wave2c/a2null"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_model(model_path: Path):
    torch.set_num_threads(6)
    tok = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
    model = AutoModel.from_pretrained(
        str(model_path), local_files_only=True, dtype=torch.float32, low_cpu_mem_usage=True
    ).eval()
    for name in ("vision_tower", "audio_tower", "embed_vision", "embed_audio"):
        if hasattr(model, name):
            setattr(model, name, None)
    return tok, model


def null_basis(w: torch.Tensor) -> tuple[torch.Tensor, dict]:
    u, s, _ = torch.linalg.svd(w, full_matrices=True)
    tol = max(w.shape) * torch.finfo(torch.float32).eps * float(s[0])
    rank = int((s > tol).sum().item())
    p = u[:, rank:]
    return p, {"rank": rank, "nullity": int(w.shape[0] - rank), "singular_min": float(s.min())}


def fit_pca(model, tok, records: list[dict], layer: int, max_length: int, n_records: int) -> dict:
    cov = torch.zeros(512, 512, dtype=torch.float64)
    sums = torch.zeros(512, dtype=torch.float64)
    total = 0
    for rec in records[:n_records]:
        enc = tok(str(rec["passage"]), return_tensors="pt", truncation=True, max_length=max_length)
        with torch.inference_mode():
            out = model.language_model(**enc, output_hidden_states=True)
        h = out.hidden_states[layer].float().reshape(-1, 512).double()
        cov += h.T @ h
        sums += h.sum(dim=0)
        total += h.shape[0]
    mean = sums / max(1, total)
    cov = cov / max(1, total) - torch.outer(mean, mean)
    evals, evecs = torch.linalg.eigh(cov)
    order = torch.argsort(evals, descending=True)
    evals = evals[order]
    evecs = evecs[:, order]
    k = 256
    comps = evecs[:, :k].T.float()  # [256, 512]
    explained = float(evals[:k].sum() / evals.clamp_min(0).sum())
    return {
        "layer": layer,
        "n_records": min(n_records, len(records)),
        "tokens": total,
        "k": k,
        "mean": mean.float(),
        "components": comps,
        "explained_variance": explained,
        "top1": float(evals[0] / evals.clamp_min(0).sum()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=MODEL)
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--splits", type=Path, default=SPLITS)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    ap.add_argument("--max-length", type=int, default=1024)
    ap.add_argument("--shard-size", type=int, default=100)
    ap.add_argument("--pca-records", type=int, default=200)
    ap.add_argument("--limit", type=int, default=0, help="debug: limit records per split")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = read_jsonl(args.data)
    by_id = {str(r["id"]): r for r in rows}
    split_data = json.loads(args.splits.read_text(encoding="utf-8"))
    tok, model = load_model(args.model)
    w = model.language_model.embedding_projection.weight.detach().float()
    p, winfo = null_basis(w)
    t0 = time.time()
    pca = fit_pca(model, tok, [by_id[i] for i in split_data["train"]], layer=12,
                  max_length=args.max_length, n_records=args.pca_records)
    meta = {
        "model": str(args.model.relative_to(ROOT).as_posix()),
        "max_length": args.max_length,
        "W": {"shape": list(w.shape), **winfo, "WTP_max_abs": float((w.T @ p).abs().max())},
        "pca": {k: v for k, v in pca.items() if k not in {"mean", "components"}},
        "pca_sec": round(time.time() - t0, 1),
    }
    torch.save({"mean": pca["mean"], "components": pca["components"]}, args.out_dir / "pca_layer12.pt")
    torch.save({"P": p}, args.out_dir / "null_basis.pt")

    for split in ("train", "val", "test"):
        ids = split_data[split]
        if args.limit:
            ids = ids[: args.limit]
        for start in range(0, len(ids), args.shard_size):
            shard = start // args.shard_size
            path = args.out_dir / f"{split}_{shard:04d}.npz"
            if path.exists():
                continue
            chunk = ids[start : start + args.shard_size]
            zs, masks, lengths = [], [], []
            for rid in chunk:
                rec = by_id[rid]
                enc = tok(str(rec["passage"]), return_tensors="pt", truncation=True, max_length=args.max_length)
                with torch.inference_mode():
                    out = model.language_model(**enc, output_hidden_states=True)
                final = out.last_hidden_state.float().reshape(-1, 768)
                h12 = out.hidden_states[12].float().reshape(-1, 512)
                x = (h12 - pca["mean"]) @ pca["components"].T
                z = final + x @ p.T
                n = z.shape[0]
                pad = torch.zeros(args.max_length, 768, dtype=z.dtype)
                pad[:n] = z
                zs.append(pad.numpy().astype(np.float16))
                mask = np.zeros(args.max_length, dtype=bool)
                mask[:n] = True
                masks.append(mask)
                lengths.append(n)
            np.savez(
                path,
                z=np.stack(zs),
                mask=np.stack(masks),
                lengths=np.asarray(lengths, dtype=np.int32),
                ids=np.asarray(chunk),
            )
            print(f"WROTE {path.name} n={len(chunk)} tokens_max={max(lengths)}", flush=True)
    meta["elapsed_sec"] = round(time.time() - t0, 1)
    (args.out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
