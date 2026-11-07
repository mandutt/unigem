"""B2 + usage-contrast pilot.

Adds a usage-enforcing penalty to the B2 CE objective: a token-mean control
hidden must be worse than the real adapter hidden by a margin, otherwise the
adapter is penalized. Decoder base remains frozen; decoder LoRA stays trainable.

No sealed test split is loaded.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from transformers.modeling_outputs import BaseModelOutput

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_b1d_b2 import attach_decoder_lora, labels_for, lora_state  # noqa: E402
from runner.c5_b1d_full import B1dFullAdapter, load_cache  # noqa: E402

T5 = ROOT / "data/models/t5gemma-2-270m-270m"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
INIT = ROOT / "data/models/f5_t5gemma2_lora/b2_pilot/adapter_final.pt"
OUT = ROOT / "data/models/f5_t5gemma2_lora/b2_usage_pilot"
REPORT = ROOT / "reports/provenance/C5_b1d/b2_usage_pilot_metrics.json"


def forward_ce(model, h_s, mask, labels) -> torch.Tensor:
    out = model(
        encoder_outputs=BaseModelOutput(last_hidden_state=h_s.to(torch.bfloat16)),
        attention_mask=mask,
        labels=labels,
    )
    return out.loss


def control_hidden(adapter, student, rid_ctrl: str, T: int) -> torch.Tensor:
    s = student[rid_ctrl]
    h = adapter(s["h"][: s["length"]].float().unsqueeze(0)).detach()
    if h.shape[1] >= T:
        return h[:, :T]
    pad = h[:, -1:].expand(-1, T - h.shape[1], -1)
    return torch.cat([h, pad], dim=1)


def evaluate(model, adapter, student, teacher, by_id, ids, tok, max_target, margin) -> dict:
    ce_vals, ctrl_vals, gaps, penalties = [], [], [], []
    with torch.no_grad():
        for idx, rid in enumerate(ids):
            s = student[rid]
            t = teacher[rid]
            x = s["h"][: s["length"]].float().unsqueeze(0)
            h_s = adapter(x)
            mask = torch.ones(1, s["length"], dtype=torch.bool)
            labels = labels_for(tok, str(by_id[rid]["summary"]), max_target)
            ce = forward_ce(model, h_s, mask, labels)
            rid_ctrl = ids[(idx + 1) % len(ids)]
            ctrl = control_hidden(adapter, student, rid_ctrl, s["length"])
            ce_ctrl = forward_ce(model, ctrl, mask, labels)
            gap = float(ce_ctrl - ce)
            ce_vals.append(float(ce))
            ctrl_vals.append(float(ce_ctrl))
            gaps.append(gap)
            penalties.append(max(0.0, margin - gap))
    n = len(ce_vals)
    return {
        "n_docs": n,
        "ce_mean": sum(ce_vals) / n if n else None,
        "ce_ctrl_mean": sum(ctrl_vals) / n if n else None,
        "usage_gap_mean": sum(gaps) / n if n else None,
        "usage_penalty_mean": sum(penalties) / n if n else None,
        "ce_min": min(ce_vals) if ce_vals else None,
        "ce_max": max(ce_vals) if ce_vals else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-limit", type=int, default=20)
    ap.add_argument("--val-limit", type=int, default=20)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--usage-weight", type=float, default=0.5)
    ap.add_argument("--margin", type=float, default=0.5)
    ap.add_argument("--hidden-weight", type=float, default=0.01)
    ap.add_argument("--max-target", type=int, default=512)
    ap.add_argument("--init", type=Path, default=INIT)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    ap.add_argument("--report", type=Path, default=REPORT)
    args = ap.parse_args()
    for name in ("init", "out_dir", "report"):
        p = getattr(args, name)
        setattr(args, name, p if p.is_absolute() else ROOT / p)

    torch.set_num_threads(6)
    torch.manual_seed(20261107)
    t0 = time.time()
    recs = [json.loads(x) for x in DATA.read_text(encoding="utf-8").splitlines() if x.strip()]
    by_id = {str(r["id"]): r for r in recs}
    splits = json.loads((ROOT / "reports/provenance/C5_clean/splits.json").read_text(encoding="utf-8"))
    train_ids = list(splits["train"])[: args.train_limit]
    val_ids = list(splits["val"])[: args.val_limit]

    student_train = load_cache("student", "train")
    teacher_train = load_cache("teacher", "train")
    student_val = load_cache("student", "val")
    teacher_val = load_cache("teacher", "val")

    tok = AutoTokenizer.from_pretrained(str(T5), local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        str(T5), local_files_only=True, dtype=torch.bfloat16, low_cpu_mem_usage=True
    ).eval()
    for p in model.parameters():
        p.requires_grad_(False)
    init = torch.load(args.init, map_location="cpu")
    if "lora" in init:
        attach_decoder_lora(model, r=int(init.get("rank", 8)), alpha=int(init.get("alpha", 16)),
                            dropout=0.05)
    else:
        attach_decoder_lora(model)
    for n, p in model.named_parameters():
        if ".lora_" in n:
            p.requires_grad_(True)
    if "lora" in init:
        missing, unexpected = model.load_state_dict(init["lora"], strict=False)
        bad = [x for x in missing if ".lora_" in x]
        if bad:
            raise SystemExit(f"missing LoRA keys: {bad[:5]} n={len(bad)}")

    adapter = B1dFullAdapter()
    adapter.load_state_dict(init["adapter"])
    adapter.train()
    params = list(adapter.parameters()) + [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.01)

    before_train = evaluate(model, adapter, student_train, teacher_train, by_id, train_ids,
                            tok, args.max_target, args.margin)
    before_val = evaluate(model, adapter, student_val, teacher_val, by_id, val_ids,
                          tok, args.max_target, args.margin)
    ce_hist, ctrl_hist, penalty_hist = [], [], []
    for epoch in range(args.epochs):
        order = list(train_ids)
        perm = torch.randperm(len(order), generator=torch.Generator().manual_seed(20261107 + epoch)).tolist()
        order = [order[i] for i in perm]
        for step, rid in enumerate(order):
            s = student_train[rid]
            t = teacher_train[rid]
            x = s["h"][: s["length"]].float().unsqueeze(0)
            h_s = adapter(x)
            mask = torch.ones(1, s["length"], dtype=torch.bool)
            labels = labels_for(tok, str(by_id[rid]["summary"]), args.max_target)
            ce = forward_ce(model, h_s, mask, labels)
            with torch.no_grad():
                ctrl_rid = train_ids[(train_ids.index(rid) + 1) % len(train_ids)]
                ctrl = control_hidden(adapter, student_train, ctrl_rid, s["length"])
                ce_ctrl = forward_ce(model, ctrl, mask, labels)
            usage = F.relu(torch.tensor(args.margin) - (ce_ctrl - ce))
            if args.hidden_weight > 0:
                y = t["h"][: t["length"]].float().unsqueeze(0)
                hidden = 1.0 - (F.normalize(h_s.float(), dim=-1) * F.normalize(y, dim=-1)).sum(-1).mean()
            else:
                hidden = ce.new_zeros(())
            loss = ce + args.usage_weight * usage + args.hidden_weight * hidden
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            ce_hist.append(float(ce.detach()))
            ctrl_hist.append(float(ce_ctrl))
            penalty_hist.append(float(usage.detach()))
            print(json.dumps({"epoch": epoch + 1, "step": step, "n": len(order),
                              "ce": ce_hist[-1], "ce_ctrl": ctrl_hist[-1],
                              "usage_penalty": penalty_hist[-1],
                              "elapsed": round(time.time() - t0, 1)}), flush=True)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        torch.save({"adapter": adapter.state_dict(), "lora": lora_state(model),
                    "epoch": epoch + 1, "rank": 8, "alpha": 16,
                    "usage_weight": args.usage_weight, "margin": args.margin},
                   args.out_dir / f"adapter_ep{epoch + 1}.pt")

    after_train = evaluate(model, adapter, student_train, teacher_train, by_id, train_ids,
                           tok, args.max_target, args.margin)
    after_val = evaluate(model, adapter, student_val, teacher_val, by_id, val_ids,
                         tok, args.max_target, args.margin)
    torch.save({"adapter": adapter.state_dict(), "lora": lora_state(model),
                "rank": 8, "alpha": 16,
                "usage_weight": args.usage_weight, "margin": args.margin,
                "epochs": args.epochs,
                "metrics": {"train": after_train, "val": after_val}},
               args.out_dir / "adapter_final.pt")
    report = {
        "experiment": "b2_usage_contrast_pilot",
        "init": str(args.init.relative_to(ROOT).as_posix()),
        "train_n": len(train_ids), "val_n": len(val_ids), "epochs": args.epochs,
        "lr": args.lr, "usage_weight": args.usage_weight, "margin": args.margin,
        "hidden_weight": args.hidden_weight,
        "lora": {"targets": ["q_proj", "k_proj", "v_proj", "o_proj"],
                 "rank": 8, "alpha": 16,
                 "params": sum(p.numel() for p in model.parameters() if p.requires_grad)},
        "adapter_params": sum(p.numel() for p in adapter.parameters()),
        "ce_first": ce_hist[0] if ce_hist else None,
        "ce_last": ce_hist[-1] if ce_hist else None,
        "ce_ctrl_first": ctrl_hist[0] if ctrl_hist else None,
        "ce_ctrl_last": ctrl_hist[-1] if ctrl_hist else None,
        "usage_penalty_first": penalty_hist[0] if penalty_hist else None,
        "usage_penalty_last": penalty_hist[-1] if penalty_hist else None,
        "before": {"train": before_train, "val": before_val},
        "after": {"train": after_train, "val": after_val},
        "elapsed_sec": round(time.time() - t0, 1),
        "checkpoint": str((args.out_dir / "adapter_final.pt").relative_to(ROOT).as_posix()),
        "test_split_used": False,
        "note": "usage-contrast: token-mean control hidden must be worse than real H_s",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
