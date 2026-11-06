"""A2-null feasibility probe: EG2 text final projection null space.

This does NOT train a summarizer. It verifies:
- W is 768x512 and has a 256d left null space
- W.T @ P ~= 0 for the null basis P
- EG2 final text hidden at layer 24 equals W @ hidden[23]
- PCA of intermediate text layers into 256d is well-defined
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModel, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "data/models/embeddinggemma-2-f9972ac2"
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
OUT = ROOT / "reports/provenance/C5_a2null/nullspace_probe.json"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def pca_explained(hidden: torch.Tensor, k: int = 256) -> dict:
    """hidden: [N, 512], rows are tokens; returns PCA variance stats."""
    x = hidden.float()
    x = x - x.mean(dim=0, keepdim=True)
    # covariance; 512x512 is cheap
    cov = (x.T @ x) / max(1, x.shape[0] - 1)
    evals = torch.linalg.eigvalsh(cov).clamp_min(0).flip(0)
    total = float(evals.sum())
    k = min(k, evals.numel())
    explained = float(evals[:k].sum() / total) if total > 0 else 0.0
    return {
        "tokens": int(x.shape[0]),
        "k": k,
        "explained_variance": explained,
        "top1": float(evals[0] / total) if total > 0 else 0.0,
        "top_min": float(evals[k - 1] / total) if total > 0 else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=MODEL)
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--max-records", type=int, default=50)
    ap.add_argument("--max-length", type=int, default=1024)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    torch.set_num_threads(6)
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(str(args.model), local_files_only=True)
    model = AutoModel.from_pretrained(
        str(args.model), local_files_only=True, dtype=torch.float32, low_cpu_mem_usage=True
    )
    model.eval()
    # Text-only path: drop the audio/vision towers to reduce memory.
    for name in ("vision_tower", "audio_tower", "embed_vision", "embed_audio"):
        if hasattr(model, name):
            setattr(model, name, None)

    w = model.language_model.embedding_projection.weight.detach().float()
    u, s, vh = torch.linalg.svd(w, full_matrices=True)
    tol = max(w.shape) * torch.finfo(torch.float32).eps * float(s[0])
    rank = int((s > tol).sum().item())
    nullity = int(w.shape[0] - rank)
    p = u[:, rank:]  # [768, nullity], left null space of W
    wtp = w.T @ p
    ptp = p.T @ p - torch.eye(nullity)
    result = {
        "model": str(args.model.relative_to(ROOT).as_posix()),
        "load_sec": round(time.time() - t0, 2),
        "W_shape": list(w.shape),
        "rank": rank,
        "nullity": nullity,
        "singular_min": float(s.min()),
        "singular_max": float(s.max()),
        "WTP_max_abs": float(wtp.abs().max()),
        "PTP_identity_max_abs": float(ptp.abs().max()),
    }

    rows = read_jsonl(args.data)[: args.max_records]
    layer_ids = (2, 6, 12, 18, 23)
    layer_hidden: dict[int, list[torch.Tensor]] = {i: [] for i in layer_ids}
    projection_errors = []
    injection_dot = []
    pooled_cos = []
    captured: dict[str, torch.Tensor] = {}

    def capture_projection(module, inputs, output):
        captured["input"] = inputs[0].detach()
        captured["output"] = output.detach()

    hook = model.language_model.embedding_projection.register_forward_hook(capture_projection)
    for i, rec in enumerate(rows):
        enc = tok(
            str(rec["passage"]),
            return_tensors="pt",
            truncation=True,
            max_length=args.max_length,
        )
        with torch.inference_mode():
            out = model.language_model(**enc, output_hidden_states=True)
        hs = out.hidden_states
        # The projection input is the post-norm 512d hidden; the final
        # last_hidden_state is the 768d projection output.
        h512 = captured["input"].float().reshape(-1, w.shape[1])
        final = out.last_hidden_state.float().reshape(-1, w.shape[0])
        proj_err = (final - h512 @ w.T).abs().max().item()
        projection_errors.append(proj_err)
        # Injection is orthogonal to the original 768d output.
        x = torch.randn(h512.shape[0], nullity, generator=torch.Generator().manual_seed(1234 + i))
        injected = x @ p.T  # [T, 768]
        injection_dot.append(float(torch.einsum("td,td->t", final, injected).abs().max()))
        # Pooled cosine is expected to change for text because we inject text
        # features; this is not the audio "text unchanged" guarantee.
        pooled_orig = final.mean(dim=0)
        pooled_new = (final + injected).mean(dim=0)
        pooled_cos.append(float(torch.nn.functional.cosine_similarity(pooled_orig, pooled_new, dim=0)))
        for lid in layer_ids:
            layer_hidden[lid].append(hs[lid].float().reshape(-1, hs[lid].shape[-1]))
        if i == 0:
            result["sample_tokens"] = int(h512.shape[0])
            result["hidden_shapes"] = [list(x.shape) for x in hs]
    hook.remove()

    result["projection_max_error"] = max(projection_errors) if projection_errors else None
    result["injection_dot_max"] = max(injection_dot) if injection_dot else None
    result["pooled_text_cosine_mean"] = sum(pooled_cos) / len(pooled_cos) if pooled_cos else None
    result["pca"] = {
        str(lid): pca_explained(torch.cat(layer_hidden[lid], dim=0), k=min(256, nullity))
        for lid in layer_ids
    }
    result["elapsed_sec"] = round(time.time() - t0, 2)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
