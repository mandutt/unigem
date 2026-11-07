"""C5 B1d bridge feasibility probe.

Checks token alignment, EG2 -> T5 hidden shapes, a small token-level adapter
distillation, and the decoder-side `encoder_outputs` injection path.

This is an interface probe, not a summarization quality experiment.
No sealed test split is loaded.
"""
from __future__ import annotations

import argparse
import gc
import json
import math
import os
import sys
import time
from pathlib import Path

import psutil
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModel, AutoModelForSeq2SeqLM, AutoTokenizer
from transformers.modeling_outputs import BaseModelOutput

ROOT = Path(__file__).resolve().parents[1]
EG2_PATH = ROOT / "data/models/embeddinggemma-2-f9972ac2"
T5_PATH = ROOT / "data/models/t5gemma-2-270m-270m"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
OUT = ROOT / "reports/provenance/C5_b1d/probe.json"
PROMPT = "summarize: "
MAX_LEN = 1024


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rss_mb() -> float:
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)


def t5_ids(tok, text: str) -> list[int]:
    ids = tok(text, add_special_tokens=True, truncation=True, max_length=MAX_LEN)["input_ids"]
    return [int(x) for x in ids]


def eg2_ids_same(tok, text: str) -> list[int]:
    # EG2 and T5Gemma2 share a tokenizer family; both use BOS=2. EG2's
    # add_special_tokens=True also appends EOS, while T5 does not, so we build
    # the exact T5 sequence: BOS + tokens.
    base = tok(text, add_special_tokens=False, truncation=True, max_length=MAX_LEN - 1)["input_ids"]
    return [int(tok.bos_token_id)] + [int(x) for x in base]


class B1dAdapter(nn.Module):
    def __init__(self, d_in: int = 768, d_out: int = 640, hidden: int = 768):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, hidden),
            nn.GELU(),
            nn.Linear(hidden, d_out),
            nn.LayerNorm(d_out),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def direction_cosine(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    p = F.normalize(pred.float(), dim=-1)
    t = F.normalize(target.float(), dim=-1)
    return (p * t).sum(dim=-1)


def extract_eg2(records: list[dict], tok, model) -> list[dict]:
    out = []
    for rec in records:
        ids = eg2_ids_same(tok, PROMPT + str(rec["passage"]))
        enc = {
            "input_ids": torch.tensor([ids], dtype=torch.long),
            "attention_mask": torch.ones(1, len(ids), dtype=torch.long),
        }
        with torch.no_grad():
            z = model.language_model(**enc).last_hidden_state[0].float()
        out.append({
            "id": str(rec["id"]),
            "ids": ids,
            "student": z,
            "student_norm_mean": float(z.norm(dim=-1).mean()),
        })
    return out


def extract_t5_teacher(records: list[dict], tok, model) -> list[dict]:
    out = []
    enc_model = model.get_encoder()
    for rec in records:
        ids = t5_ids(tok, PROMPT + str(rec["passage"]))
        enc = {
            "input_ids": torch.tensor([ids], dtype=torch.long),
            "attention_mask": torch.ones(1, len(ids), dtype=torch.long),
        }
        with torch.no_grad():
            h = enc_model(**enc).last_hidden_state[0].float()
        out.append({
            "id": str(rec["id"]),
            "ids": ids,
            "teacher": h,
            "teacher_norm_mean": float(h.norm(dim=-1).mean()),
        })
    return out


def align(eg2_rows: list[dict], t5_rows: list[dict]) -> dict:
    n = min(len(eg2_rows), len(t5_rows))
    exact = 0
    mismatches = []
    for i in range(n):
        a, b = eg2_rows[i], t5_rows[i]
        if a["id"] != b["id"]:
            mismatches.append({"i": i, "reason": "id_order", "a": a["id"], "b": b["id"]})
            continue
        if a["ids"] != b["ids"]:
            first = next((j for j, (x, y) in enumerate(zip(a["ids"], b["ids"])) if x != y), None)
            mismatches.append({
                "i": i, "id": a["id"], "reason": "token_ids",
                "len_a": len(a["ids"]), "len_b": len(b["ids"]), "first_diff": first,
            })
            continue
        exact += 1
    return {"n": n, "exact": exact, "rate": exact / n if n else 0.0, "mismatches": mismatches}


def eval_cos(adapter: B1dAdapter, eg2_rows: list[dict], t5_rows: list[dict]) -> float:
    vals = []
    with torch.inference_mode():
        for r, t in zip(eg2_rows, t5_rows):
            pred = adapter(r["student"].unsqueeze(0))[0]
            vals.extend(direction_cosine(pred, t["teacher"]).tolist())
    return sum(vals) / len(vals) if vals else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-docs", type=int, default=5)
    ap.add_argument("--val-docs", type=int, default=2)
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--max-new", type=int, default=16)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    torch.set_num_threads(6)
    t0 = time.time()
    rows = read_jsonl(DATA)
    by_id = {str(r["id"]): r for r in rows}
    splits = json.loads(SPLITS.read_text(encoding="utf-8"))
    train_ids = splits["train"][: args.train_docs]
    val_ids = splits["val"][: args.val_docs]
    train_recs = [by_id[i] for i in train_ids]
    val_recs = [by_id[i] for i in val_ids]

    eg2_tok = AutoTokenizer.from_pretrained(str(EG2_PATH), local_files_only=True)
    t5_tok = AutoTokenizer.from_pretrained(str(T5_PATH), local_files_only=True)

    # 1. Token alignment on exactly the documents used by the probe.
    ids_audit = []
    for rec in train_recs + val_recs:
        text = PROMPT + str(rec["passage"])
        a = eg2_ids_same(eg2_tok, text)
        b = t5_ids(t5_tok, text)
        ids_audit.append({
            "id": str(rec["id"]),
            "eg2_len": len(a),
            "t5_len": len(b),
            "exact": a == b,
            "first_diff": next((j for j, (x, y) in enumerate(zip(a, b)) if x != y), None),
        })

    # 2. EG2 student features, then free the model.
    t_eg2 = time.time()
    eg2_model = AutoModel.from_pretrained(
        str(EG2_PATH), local_files_only=True, dtype=torch.float32, low_cpu_mem_usage=True
    ).eval()
    for name in ("vision_tower", "audio_tower", "embed_vision", "embed_audio"):
        if hasattr(eg2_model, name):
            setattr(eg2_model, name, None)
    eg2_train = extract_eg2(train_recs, eg2_tok, eg2_model)
    eg2_val = extract_eg2(val_recs, eg2_tok, eg2_model)
    eg2_sec = time.time() - t_eg2
    del eg2_model
    gc.collect()
    rss_after_eg2 = rss_mb()

    # 3. T5 teacher features; keep the model for the generate smoke.
    t_t5 = time.time()
    t5_model = AutoModelForSeq2SeqLM.from_pretrained(
        str(T5_PATH), local_files_only=True, dtype=torch.bfloat16, low_cpu_mem_usage=True
    ).eval()
    t5_train = extract_t5_teacher(train_recs, t5_tok, t5_model)
    t5_val = extract_t5_teacher(val_recs, t5_tok, t5_model)
    t5_sec = time.time() - t_t5

    alignment = align(eg2_train, t5_train)
    alignment_val = align(eg2_val, t5_val)
    shapes = {
        "teacher": list(t5_train[0]["teacher"].shape),
        "student": list(eg2_train[0]["student"].shape),
        "teacher_norm_mean": sum(x["teacher_norm_mean"] for x in t5_train) / len(t5_train),
        "student_norm_mean": sum(x["student_norm_mean"] for x in eg2_train) / len(eg2_train),
    }

    # 4. Adapter distillation (direction only).
    t_fit = time.time()
    adapter = B1dAdapter()
    torch.manual_seed(20261107)
    opt = torch.optim.AdamW(adapter.parameters(), lr=args.lr, weight_decay=0.01)
    train_before = eval_cos(adapter, eg2_train, t5_train)
    val_before = eval_cos(adapter, eg2_val, t5_val)
    losses = []
    for step in range(args.steps):
        i = step % len(eg2_train)
        r = eg2_train[i]
        t = t5_train[i]
        pred = adapter(r["student"].unsqueeze(0))[0]
        cos = direction_cosine(pred, t["teacher"])
        loss = 1.0 - cos.mean() + 0.05 * F.mse_loss(
            F.normalize(pred, dim=-1), F.normalize(t["teacher"], dim=-1)
        )
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        losses.append(float(loss.detach()))
    train_after = eval_cos(adapter, eg2_train, t5_train)
    val_after = eval_cos(adapter, eg2_val, t5_val)
    fit_sec = time.time() - t_fit

    # 5. Decoder-side injection smoke: adapter -> H_s -> encoder_outputs.
    # Scale to the teacher's mean hidden norm; the adapter was trained on
    # direction only.
    r = eg2_val[0] if eg2_val else eg2_train[0]
    with torch.inference_mode():
        pred = adapter(r["student"].unsqueeze(0))[0]
        pred = F.normalize(pred, dim=-1) * shapes["teacher_norm_mean"]
        h_s = pred.unsqueeze(0).to(torch.bfloat16)
        mask = torch.ones(1, h_s.shape[1], dtype=torch.bool)
        gen_error = None
        gen_ids = []
        gen_text = ""
        try:
            gen = t5_model.generate(
                encoder_outputs=BaseModelOutput(last_hidden_state=h_s),
                attention_mask=mask,
                max_new_tokens=args.max_new,
                num_beams=1,
                do_sample=False,
            )
            gen_ids = gen[0].tolist()
            gen_text = t5_tok.decode(gen, skip_special_tokens=True)
        except Exception as exc:  # noqa: BLE001
            gen_error = f"{type(exc).__name__}: {exc}"

    rss_peak = rss_mb()
    duration = time.time() - t0

    # 6. Teacher-hidden control: if the decoder accepts the native T5 encoder
    # hidden, the `encoder_outputs` path is valid independently of adapter
    # quality. This should reproduce a normal native-encoder generation.
    with torch.inference_mode():
        th = t5_val[0]["teacher"].to(torch.bfloat16).unsqueeze(0)
        tmask = torch.ones(1, th.shape[1], dtype=torch.bool)
        teacher_error = None
        teacher_ids = []
        teacher_text = ""
        try:
            tgen = t5_model.generate(
                encoder_outputs=BaseModelOutput(last_hidden_state=th),
                attention_mask=tmask,
                max_new_tokens=args.max_new,
                num_beams=1,
                do_sample=False,
            )
            teacher_ids = tgen[0].tolist()
            teacher_text = t5_tok.decode(tgen, skip_special_tokens=True)
        except Exception as exc:  # noqa: BLE001
            teacher_error = f"{type(exc).__name__}: {exc}"

    result = {
        "probe_version": "b1d-probe/0.1.0",
        "status": "PASS_INTERFACE" if (
            alignment["rate"] == 1.0 and alignment_val["rate"] == 1.0
            and not gen_error and len(gen_ids) > 1
            and not teacher_error and len(teacher_ids) > 1
        ) else "FAIL",
        "train_docs": train_ids,
        "val_docs": val_ids,
        "test_split_used": False,
        "prompt": PROMPT,
        "token_alignment": {
            "train": alignment,
            "val": alignment_val,
            "per_doc": ids_audit,
        },
        "shapes": shapes,
        "adapter": {
            "params": sum(p.numel() for p in adapter.parameters()),
            "steps": args.steps,
            "lr": args.lr,
            "loss_first": losses[0] if losses else None,
            "loss_last": losses[-1] if losses else None,
            "loss_min": min(losses) if losses else None,
            "train_cosine_before": train_before,
            "train_cosine_after": train_after,
            "val_cosine_before": val_before,
            "val_cosine_after": val_after,
        },
        "generate": {
            "ok": gen_error is None,
            "error": gen_error,
            "n_tokens": len(gen_ids),
            "text": gen_text,
            "max_new": args.max_new,
        },
        "generate_teacher_control": {
            "ok": teacher_error is None,
            "error": teacher_error,
            "n_tokens": len(teacher_ids),
            "text": teacher_text,
            "max_new": args.max_new,
            "note": "native T5 encoder hidden passed back through encoder_outputs",
        },
        "timing_sec": {
            "eg2": round(eg2_sec, 2),
            "t5": round(t5_sec, 2),
            "adapter_fit": round(fit_sec, 2),
            "total": round(duration, 2),
        },
        "rss_mb": {"after_eg2": round(rss_after_eg2, 1), "peak": round(rss_peak, 1)},
        "limitations": [
            "5 train / 2 val documents; not a quality result.",
            "adapter is direction-only; scale is fixed at teacher mean norm for generation.",
            "no decoder LoRA; frozen decoder may ignore or misuse H_s.",
            "no full teacher cache; no full distillation.",
            "test 163 remained sealed.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "alignment": {"train": alignment["rate"], "val": alignment_val["rate"]},
        "shapes": shapes,
        "loss": [result["adapter"]["loss_first"], result["adapter"]["loss_last"]],
        "cosine": {
            "train": [train_before, train_after],
            "val": [val_before, val_after],
        },
        "generate": result["generate"],
        "generate_teacher_control": result["generate_teacher_control"],
        "timing_sec": result["timing_sec"],
        "rss_mb": result["rss_mb"],
        "out": str(args.out),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
