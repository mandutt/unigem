"""Evaluate an A2-null adapter with T5Gemma2 generation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from transformers.modeling_outputs import BaseModelOutput

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval.slot_verify import verify_summary  # noqa: E402

T5 = ROOT / "data/models/t5gemma-2-270m-270m"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
FEATURES = ROOT / "data/wave2c/a2null"
OUT = ROOT / "reports/provenance/C5_a2null"


class Adapter(nn.Module):
    def __init__(self, d_in: int = 768, d_out: int = 640, hidden: int = 768):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d_in, hidden), nn.GELU(), nn.Linear(hidden, d_out))

    def forward(self, x):
        return self.net(x)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_features(features_dir: Path, split: str, limit: int = 0) -> list[dict]:
    rows = []
    for path in sorted(features_dir.glob(f"{split}_*.npz")):
        with np.load(path, allow_pickle=False) as z:
            for i, rid in enumerate([str(x) for x in z["ids"].tolist()]):
                rows.append({"id": rid, "z": torch.from_numpy(z["z"][i]).float(),
                             "mask": torch.from_numpy(z["mask"][i]).bool(),
                             "length": int(z["lengths"][i])})
    return rows[:limit] if limit else rows


def char_f1(pred: str, ref: str) -> float:
    def bag(s):
        import collections
        return collections.Counter(s.replace(" ", ""))
    a, b = bag(pred), bag(ref)
    common = sum((a & b).values())
    p = common / max(1, sum(a.values()))
    r = common / max(1, sum(b.values()))
    return 2 * p * r / (p + r) if p + r else 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features-dir", type=Path, default=FEATURES)
    ap.add_argument("--adapter", type=Path, required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-memory", type=int, default=1024)
    ap.add_argument("--max-new", type=int, default=256)
    ap.add_argument("--out", type=Path, default=OUT / "predictions.jsonl")
    args = ap.parse_args()
    torch.set_num_threads(6)
    rows = read_jsonl(DATA)
    by_id = {str(r["id"]): r for r in rows}
    feats = load_features(args.features_dir, args.split, args.limit)
    if not feats:
        raise SystemExit("no features")
    tok = AutoTokenizer.from_pretrained(str(T5), local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        str(T5), local_files_only=True, dtype=torch.bfloat16, low_cpu_mem_usage=True
    ).eval()
    adapter = Adapter().float()
    state = torch.load(args.adapter, map_location="cpu")
    adapter.load_state_dict(state["adapter"])
    adapter.eval()
    outputs = []
    for rec in feats:
        t = min(rec["length"], args.max_memory)
        z = rec["z"][:t]
        mask = torch.zeros(args.max_memory, dtype=torch.bool)
        mask[:t] = True
        with torch.inference_mode():
            memory = adapter(z.unsqueeze(0)).to(torch.bfloat16)
            gen = model.generate(
                encoder_outputs=BaseModelOutput(last_hidden_state=memory),
                attention_mask=mask.unsqueeze(0),
                max_new_tokens=args.max_new,
                num_beams=1,
                do_sample=False,
            )
        pred = tok.decode(gen[0], skip_special_tokens=True)
        target = str(by_id[rec["id"]]["summary"])
        rep = verify_summary(str(by_id[rec["id"]]["passage"]), pred)
        outputs.append({
            "id": rec["id"],
            "pred": pred,
            "target": target,
            "char_f1": char_f1(pred, target),
            "slot_preservation": rep.slot_preservation,
            "new_slot_rate": rep.new_slot_rate,
            "grounded": not rep.new,
        })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in outputs) + "\n", encoding="utf-8")
    n = len(outputs)
    metrics = {
        "n": n,
        "char_f1_mean": sum(x["char_f1"] for x in outputs) / n,
        "grounded_rate": sum(x["grounded"] for x in outputs) / n,
        "new_slot_rate_mean": sum(x["new_slot_rate"] for x in outputs) / n,
    }
    print(json.dumps({"metrics": metrics, "out": str(args.out)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
