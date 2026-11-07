"""Teacher-forced fidelity eval for B2 checkpoints (adapter + decoder LoRA).

Reports CE and token accuracy against either teacher or gold targets.
No training. No test split.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from transformers.modeling_outputs import BaseModelOutput

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_b1d_b2 import attach_decoder_lora, labels_for  # noqa: E402
from runner.c5_b1d_full import B1dFullAdapter, load_cache  # noqa: E402

T5 = ROOT / "data/models/t5gemma-2-270m-270m"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
VAL_TEACHER = ROOT / "reports/provenance/C5_a1/pilot300_val161/predictions.jsonl"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", type=Path, required=True)
    ap.add_argument("--lora", type=Path, required=True)
    ap.add_argument("--target", choices=["gold", "teacher"], default="teacher")
    ap.add_argument("--teacher-preds", type=Path, default=VAL_TEACHER)
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--max-target", type=int, default=512)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    for n in ("adapter", "lora", "teacher_preds", "out"):
        p = getattr(args, n)
        setattr(args, n, p if p.is_absolute() else ROOT / p)
    torch.set_num_threads(6)

    rows = [json.loads(x) for x in DATA.read_text(encoding="utf-8").splitlines() if x.strip()]
    by_id = {str(r["id"]): r for r in rows}
    teacher = {
        str(r["id"]): str(r["pred"])
        for r in [json.loads(x) for x in args.teacher_preds.read_text(encoding="utf-8").splitlines() if x.strip()]
    }
    splits = json.loads((ROOT / "reports/provenance/C5_clean/splits.json").read_text(encoding="utf-8"))
    ids = [rid for rid in splits["val"] if rid in teacher][: args.limit]

    student = load_cache("student", "val")
    t_hidden = load_cache("teacher", "val")
    tok = AutoTokenizer.from_pretrained(str(T5), local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        str(T5), local_files_only=True, dtype=torch.bfloat16, low_cpu_mem_usage=True
    ).eval()
    for p in model.parameters():
        p.requires_grad_(False)
    lora = torch.load(args.lora, map_location="cpu")
    attach_decoder_lora(model, r=int(lora.get("rank", 8)), alpha=int(lora.get("alpha", 16)), dropout=0.0)
    missing, _ = model.load_state_dict(lora["lora"], strict=False)
    bad = [x for x in missing if ".lora_" in x]
    if bad:
        raise SystemExit(f"missing LoRA keys: {bad[:5]}")
    ck = torch.load(args.adapter, map_location="cpu")
    adapter = B1dFullAdapter()
    adapter.load_state_dict(ck["adapter"])
    adapter.eval()

    ces, accs = [], []
    with torch.no_grad():
        for i, rid in enumerate(ids):
            s = student[rid]
            h_s = adapter(s["h"][: s["length"]].float().unsqueeze(0))
            mask = torch.ones(1, s["length"], dtype=torch.bool)
            text = teacher[rid] if args.target == "teacher" else str(by_id[rid]["summary"])
            labels = labels_for(tok, text, args.max_target)
            out = model(
                encoder_outputs=BaseModelOutput(last_hidden_state=h_s.to(torch.bfloat16)),
                attention_mask=mask,
                labels=labels,
            )
            valid = labels != -100
            acc = float((out.logits.argmax(dim=-1)[valid] == labels[valid]).float().mean())
            ces.append(float(out.loss))
            accs.append(acc)
            if (i + 1) % 20 == 0:
                print(json.dumps({"done": i + 1, "n": len(ids)}), flush=True)
    result = {
        "adapter": args.adapter.relative_to(ROOT).as_posix(),
        "lora": args.lora.relative_to(ROOT).as_posix(),
        "target": args.target,
        "n": len(ces),
        "ce_mean": sum(ces) / len(ces),
        "token_acc_mean": sum(accs) / len(accs),
        "test_split_used": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
