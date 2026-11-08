"""E0 wiring and decoder-LoRA inventory audit.

No training. Three checks:
1. mT5 native encoder forward vs the same hidden states passed through
   encoder_outputs must produce identical logits/loss.
2. A native EG2 layer19 cache can be consumed as an external memory tensor
   with finite loss and the expected [tokens, 512] shape.
3. The decoder exposes q/k/v/o modules for LoRA, while the legacy T5Gemma2
   q_proj/k_proj/v_proj/o_proj target selector matches zero mT5 modules.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn
from transformers import MT5ForConditionalGeneration, T5Tokenizer
from transformers.modeling_outputs import BaseModelOutput

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "data/models/mt5-small"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
CACHE = ROOT / "data/wave2c/eg2_native_layer19/layer19"
OUT = ROOT / "reports/provenance/C5_e0/wiring_audit.json"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def make_labels(tok, text: str, max_length: int = 64) -> torch.Tensor:
    ids = tok(text, add_special_tokens=True, truncation=True, max_length=max_length)["input_ids"]
    out = torch.tensor([ids], dtype=torch.long)
    out[out == tok.pad_token_id] = -100
    return out


def inventory(model) -> dict[str, Any]:
    decoder = []
    for name, module in model.named_modules():
        if not (name.startswith("decoder.") or name.startswith("model.decoder.")):
            continue
        if not isinstance(module, nn.Linear):
            continue
        decoder.append({"name": name, "shape": [int(module.in_features), int(module.out_features)]})
    q = [x for x in decoder if x["name"].endswith(".q")]
    k = [x for x in decoder if x["name"].endswith(".k")]
    v = [x for x in decoder if x["name"].endswith(".v")]
    o = [x for x in decoder if x["name"].endswith(".o")]
    legacy = [x for x in decoder if any(x["name"].endswith("." + t) for t in ("q_proj", "k_proj", "v_proj", "o_proj"))]
    return {
        "decoder_linear_modules": len(decoder),
        "q": len(q),
        "k": len(k),
        "v": len(v),
        "o": len(o),
        "q_k_v_o_total": len(q) + len(k) + len(v) + len(o),
        "legacy_q_proj_style_total": len(legacy),
        "sample_names": [x["name"] for x in decoder[:8]],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", type=Path, default=MODEL)
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--splits", type=Path, default=SPLITS)
    ap.add_argument("--cache", type=Path, default=CACHE)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--max-source-length", type=int, default=256)
    args = ap.parse_args()

    torch.set_num_threads(6)
    rows = {str(r["id"]): r for r in read_jsonl(args.data)}
    split = json.loads(args.splits.read_text(encoding="utf-8"))
    rid = str(split["train"][0])
    row = rows[rid]

    tok = T5Tokenizer.from_pretrained(str(args.model_dir), local_files_only=True, use_fast=False)
    model = MT5ForConditionalGeneration.from_pretrained(
        str(args.model_dir), local_files_only=True, dtype=torch.float32, low_cpu_mem_usage=True
    ).eval()
    model.config.use_cache = False

    src = tok(
        str(row["passage"]),
        add_special_tokens=True,
        truncation=True,
        max_length=args.max_source_length,
        return_tensors="pt",
    )
    labels = make_labels(tok, str(row["summary"]))
    attention = src["attention_mask"]

    with torch.no_grad():
        normal = model(input_ids=src["input_ids"], attention_mask=attention, labels=labels)
        encoder = model.encoder(input_ids=src["input_ids"], attention_mask=attention)
        external = model(
            encoder_outputs=BaseModelOutput(last_hidden_state=encoder.last_hidden_state),
            attention_mask=attention,
            labels=labels,
        )
    logits_delta = float((normal.logits - external.logits).abs().max())
    loss_delta = abs(float(normal.loss) - float(external.loss))
    forward = {
        "normal_loss": float(normal.loss),
        "external_loss": float(external.loss),
        "loss_abs_delta": loss_delta,
        "logits_max_abs_delta": logits_delta,
        "allclose_atol_1e-5": bool(torch.allclose(normal.logits, external.logits, atol=1e-5, rtol=1e-4)),
        "finite": bool(torch.isfinite(normal.loss) and torch.isfinite(external.loss)),
        "encoder_hidden_shape": list(encoder.last_hidden_state.shape),
    }

    cache_check: dict[str, Any] = {"cache": str(args.cache), "exists": args.cache.exists()}
    if args.cache.exists():
        files = sorted(args.cache.glob("train_*.npz"))
        if files:
            with np.load(files[0]) as z:
                h = z["h"]
                mask = z["mask"]
                lengths = z["lengths"]
            cache_check.update({
                "file": str(files[0].relative_to(ROOT).as_posix()),
                "h_shape": list(h.shape),
                "h_dtype": str(h.dtype),
                "mask_shape": list(mask.shape),
                "length_n": int(mask.sum()),
                "lengths_min": int(lengths.min()),
                "lengths_max": int(lengths.max()),
                "finite": bool(np.isfinite(h).all()),
                "dim_512": bool(h.shape[-1] == 512),
            })
            if h.shape[-1] == 512 and h.shape[1] >= 1:
                n = min(int(mask[0].sum()), h.shape[1])
                mem = torch.from_numpy(h[:1, :n, :].astype(np.float32))
                with torch.no_grad():
                    mm = model(
                        encoder_outputs=BaseModelOutput(last_hidden_state=mem),
                        attention_mask=torch.ones(1, n, dtype=torch.long),
                        labels=labels,
                    )
                cache_check.update({
                    "external_memory_loss": float(mm.loss),
                    "external_memory_finite": bool(torch.isfinite(mm.loss)),
                    "external_memory_logits_shape": list(mm.logits.shape),
                })
        else:
            cache_check["error"] = "no train_*.npz"
    else:
        cache_check["error"] = "cache directory absent"

    payload = {
        "experiment": "c5_e0_wiring_audit",
        "model": str(args.model_dir.relative_to(ROOT).as_posix()),
        "doc_id": rid,
        "source_tokens": int(src["input_ids"].shape[1]),
        "target_tokens": int(labels.shape[1]),
        "native_encoder_vs_external": forward,
        "eg2_native_layer19_cache": cache_check,
        "decoder_lora_inventory": inventory(model),
        "test_split_used": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
