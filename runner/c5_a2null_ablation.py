"""Memory-ablation teacher-forced NLL for A2-null adapters.

For each val document, compare the real adapter memory against:
  - shuffled memory from another val document
  - zero memory

A positive ΔNLL means the real memory lowers NLL (is used by the decoder).
No generation, no test split.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from transformers.modeling_outputs import BaseModelOutput

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_a2null_eval import Adapter, load_adapter, load_features, read_jsonl  # noqa: E402
from runner.c5_a2null_full_train import make_batch  # noqa: E402

T5 = ROOT / "data/models/t5gemma-2-270m-270m"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
FEATURES = ROOT / "data/wave2c/a2null"
OUT = ROOT / "reports/provenance/C5_a2null"


def bootstrap_ci(x: list[float], n: int = 2000) -> tuple[float, float]:
    if not x:
        return 0.0, 0.0
    rng = np.random.default_rng(42)
    arr = np.asarray(x, dtype=np.float64)
    means = np.empty(n, dtype=np.float64)
    for i in range(n):
        means[i] = arr[rng.integers(0, len(arr), len(arr))].mean()
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features-dir", type=Path, default=FEATURES)
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--splits", type=Path, default=SPLITS)
    ap.add_argument("--adapters", nargs="+", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-memory", type=int, default=1024)
    ap.add_argument("--max-target", type=int, default=512)
    ap.add_argument("--out", type=Path, default=OUT / "memory_ablation.json")
    args = ap.parse_args()
    torch.set_num_threads(6)
    rows = read_jsonl(args.data)
    by_id = {str(r["id"]): r for r in rows}
    feats = load_features(args.features_dir, "val", args.limit)
    if len(feats) < 2:
        raise SystemExit("need at least 2 val features")
    tok = AutoTokenizer.from_pretrained(str(T5), local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        str(T5), local_files_only=True, dtype=torch.bfloat16, low_cpu_mem_usage=True
    ).eval()
    for p in model.parameters():
        p.requires_grad_(False)

    # Fixed shuffle pairing; excludes self.
    order = list(range(len(feats)))
    random.Random(42).shuffle(order)
    shuffled = {}
    for i in range(len(feats)):
        j = order[(i + 1) % len(feats)]
        shuffled[feats[i]["id"]] = feats[j]

    results = {}
    for adapter_path in args.adapters:
        adapter = load_adapter(Path(adapter_path))
        records = []
        with torch.inference_mode():
            for i, rec in enumerate(feats):
                t = min(rec["length"], args.max_memory)
                z = rec["z"][:t]
                m = torch.ones(t, dtype=torch.bool)
                _, _, labels = make_batch(
                    [{**rec, "z": rec["z"].numpy()}], by_id, tok, args.max_memory, args.max_target
                )
                mem_real = adapter(z.unsqueeze(0)).to(torch.bfloat16)
                real_loss = float(model(
                    encoder_outputs=BaseModelOutput(last_hidden_state=mem_real),
                    attention_mask=m.unsqueeze(0),
                    labels=labels,
                ).loss)
                other = shuffled[rec["id"]]
                t2 = min(other["length"], args.max_memory)
                mem_shuf = adapter(other["z"][:t2].unsqueeze(0)).to(torch.bfloat16)
                shuf_loss = float(model(
                    encoder_outputs=BaseModelOutput(last_hidden_state=mem_shuf),
                    attention_mask=torch.ones(t2, dtype=torch.bool).unsqueeze(0),
                    labels=labels,
                ).loss)
                mem_zero = torch.zeros_like(mem_real)
                zero_loss = float(model(
                    encoder_outputs=BaseModelOutput(last_hidden_state=mem_zero),
                    attention_mask=m.unsqueeze(0),
                    labels=labels,
                ).loss)
                records.append({
                    "id": rec["id"],
                    "real_nll": real_loss,
                    "shuffled_nll": shuf_loss,
                    "zero_nll": zero_loss,
                    "delta_shuffled": shuf_loss - real_loss,
                    "delta_zero": zero_loss - real_loss,
                })
                if (i + 1) % 20 == 0:
                    print(json.dumps({"adapter": Path(adapter_path).name, "done": i + 1, "n": len(feats)}), flush=True)
        ds = [r["delta_shuffled"] for r in records]
        dz = [r["delta_zero"] for r in records]
        summary = {
            "n": len(records),
            "real_nll_mean": float(np.mean([r["real_nll"] for r in records])),
            "shuffled_nll_mean": float(np.mean([r["shuffled_nll"] for r in records])),
            "zero_nll_mean": float(np.mean([r["zero_nll"] for r in records])),
            "delta_shuffled_mean": float(np.mean(ds)),
            "delta_shuffled_ci95": list(bootstrap_ci(ds)),
            "delta_zero_mean": float(np.mean(dz)),
            "delta_zero_ci95": list(bootstrap_ci(dz)),
            "positive_shuffled": int(sum(x > 0 for x in ds)),
            "positive_zero": int(sum(x > 0 for x in dz)),
        }
        results[Path(adapter_path).parent.name] = {"summary": summary, "records": records}
        print(json.dumps({"adapter": Path(adapter_path).parent.name, **summary}, ensure_ascii=False), flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "adapters": list(results)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
