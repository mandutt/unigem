"""Causal H_s ablation for the adapter-only bridge.

Conditions:
- real: adapter output for the document
- zero: zeros with the same shape
- token_shuffle: adapter output with time positions permuted
- other_doc: adapter output from another document, padded/truncated
- teacher: true teacher hidden (upper reference)

Teacher-forced CE/token accuracy on val100. No training. No test split.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from transformers.modeling_outputs import BaseModelOutput

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_b1d_b2 import labels_for  # noqa: E402
from runner.c5_b1d_full import B1dFullAdapter, load_cache  # noqa: E402
from runner.c5_b1d_teacher_fidelity import read_jsonl, teacher_map  # noqa: E402

T5 = ROOT / "data/models/t5gemma-2-270m-270m"
ADAPTER = ROOT / "data/models/f5_t5gemma2_lora/b1d_teacher100/adapter_final.pt"
VAL_TEACHER = ROOT / "reports/provenance/C5_a1/pilot300_val161/predictions.jsonl"
OUT = ROOT / "reports/provenance/C5_b1d/bridge_ablation_val100.json"


def make_other_h(h_other: torch.Tensor, target_len: int) -> torch.Tensor:
    if h_other.shape[0] >= target_len:
        return h_other[:target_len]
    pad = torch.zeros(target_len - h_other.shape[0], h_other.shape[-1], dtype=h_other.dtype)
    return torch.cat([h_other, pad], dim=0)


def score(model, tok, h: torch.Tensor, mask: torch.Tensor, labels: torch.Tensor) -> tuple[float, float]:
    out = model(
        encoder_outputs=BaseModelOutput(last_hidden_state=h.to(torch.bfloat16)),
        attention_mask=mask,
        labels=labels,
    )
    valid = labels != -100
    acc = float((out.logits.argmax(dim=-1)[valid] == labels[valid]).float().mean()) if valid.any() else 0.0
    return float(out.loss), acc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20261107)
    ap.add_argument("--max-target", type=int, default=512)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    args.out = args.out if args.out.is_absolute() else ROOT / args.out
    torch.set_num_threads(6)
    random.seed(args.seed)

    splits = json.loads((ROOT / "reports/provenance/C5_clean/splits.json").read_text(encoding="utf-8"))
    val_teacher = teacher_map(VAL_TEACHER, 0)
    ids = [r for r in splits["val"] if r in val_teacher][: args.limit]
    student = load_cache("student", "val")
    teacher = load_cache("teacher", "val")

    tok = AutoTokenizer.from_pretrained(str(T5), local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        str(T5), local_files_only=True, dtype=torch.bfloat16, low_cpu_mem_usage=True
    ).eval()
    for p in model.parameters():
        p.requires_grad_(False)
    ck = torch.load(ADAPTER, map_location="cpu")
    adapter = B1dFullAdapter()
    adapter.load_state_dict(ck["adapter"])
    adapter.eval()

    conditions = ["real", "zero", "token_shuffle", "other_doc", "teacher", "teacher_shuffle"]
    rows = []
    t0 = time.time()
    for i, rid in enumerate(ids):
        s = student[rid]
        t = teacher[rid]
        n = int(s["length"])
        h_real = adapter(s["h"][:n].float().unsqueeze(0))
        mask = torch.ones(1, n, dtype=torch.bool)
        labels = labels_for(tok, val_teacher[rid], args.max_target)
        other = student[ids[(i + 1) % len(ids)]]
        h_other = adapter(other["h"][: int(other["length"])].float().unsqueeze(0))[0]
        h_other = make_other_h(h_other, n).unsqueeze(0)
        perm = torch.randperm(n, generator=torch.Generator().manual_seed(args.seed + i))
        h_teacher = t["h"][:n].float().unsqueeze(0)
        variants = {
            "real": h_real,
            "zero": torch.zeros_like(h_real),
            "token_shuffle": h_real[:, perm, :],
            "other_doc": h_other,
            "teacher": h_teacher,
            "teacher_shuffle": h_teacher[:, perm, :],
        }
        rec = {"id": rid, "n": n}
        for cond in conditions:
            ce, acc = score(model, tok, variants[cond], mask, labels)
            rec[cond] = {"ce": ce, "acc": acc}
        rows.append(rec)
        if (i + 1) % 10 == 0:
            print(json.dumps({"done": i + 1, "n": len(ids), "elapsed": round(time.time() - t0, 1)}), flush=True)

    summary = {}
    for cond in conditions:
        ces = [r[cond]["ce"] for r in rows]
        accs = [r[cond]["acc"] for r in rows]
        summary[cond] = {
            "n": len(rows),
            "ce_mean": sum(ces) / len(ces),
            "ce_median": sorted(ces)[len(ces) // 2],
            "token_acc_mean": sum(accs) / len(accs),
        }
    for cond in conditions:
        if cond == "real":
            continue
        deltas = [r[cond]["ce"] - r["real"]["ce"] for r in rows]
        summary[cond]["delta_ce_mean_vs_real"] = sum(deltas) / len(deltas)
        summary[cond]["delta_ce_median_vs_real"] = sorted(deltas)[len(deltas) // 2]
        summary[cond]["frac_ce_higher_than_real"] = sum(d > 0 for d in deltas) / len(deltas)

    result = {
        "experiment": "b1d_bridge_hs_ablation",
        "adapter": ADAPTER.relative_to(ROOT).as_posix(),
        "val_n": len(rows),
        "conditions": conditions,
        "summary": summary,
        "rows": rows,
        "elapsed_sec": round(time.time() - t0, 1),
        "test_split_used": False,
        "note": "teacher-forced CE/token accuracy; no training; other_doc uses next val document padded/truncated",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": summary, "elapsed_sec": result["elapsed_sec"]}, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
