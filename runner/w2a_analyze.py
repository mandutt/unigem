"""Wave 2A-lite dev/test analysis: CER, paired bootstrap, taxonomy, coverage.

Usage:
  python runner/w2a_analyze.py --label dev_read \
    --arm fa=logs/W2A_lite/decode_fa.json \
    --arm fb=logs/W2A_lite/decode_fb.json \
    --arm fc_softmax=logs/W2A_lite/decode_fc_softmax.json \
    --arm fc_concat=logs/W2A_lite/decode_fc_concat.json \
    --vocab data/wave2a_lite/vocab.json --out reports/W2A_lite_dev_analysis.json

The decode JSON contract is from train/d5_reader.py --decode:
  {n, cer, errors, ref_chars, sentences:[{id, ref_norm, pred_norm, err, ref_chars}]}
"""
from __future__ import annotations

import argparse
import collections
import difflib
import json
import random
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys_path = str(ROOT)


def load_json(path: str) -> dict:
    return json.load(open(path, encoding="utf-8"))


def corpus_cer(rows: list[dict]) -> tuple[float, int, int]:
    e = sum(int(r["err"]) for r in rows)
    n = sum(int(r["ref_chars"]) for r in rows)
    return (e / n if n else 0.0), e, n


def paired_bootstrap(a: list[dict], b: list[dict], n_boot: int = 10000, seed: int = 42) -> dict:
    assert len(a) == len(b)
    rng = random.Random(seed)
    ref = np.asarray([int(r["ref_chars"]) for r in a], dtype=np.float64)
    ea = np.asarray([int(r["err"]) for r in a], dtype=np.float64)
    eb = np.asarray([int(r["err"]) for r in b], dtype=np.float64)
    diffs = []
    n = len(a)
    for _ in range(n_boot):
        idx = np.asarray([rng.randrange(n) for _ in range(n)], dtype=np.int64)
        den = ref[idx].sum()
        if den <= 0:
            continue
        diffs.append((ea[idx].sum() - eb[idx].sum()) / den)
    diffs.sort()
    lo = diffs[int(0.025 * len(diffs))]
    hi = diffs[int(0.975 * len(diffs)) - 1]
    point = (ea.sum() - eb.sum()) / ref.sum() if ref.sum() else 0.0
    return {"improvement": float(point), "ci95": [float(lo), float(hi)], "n_boot": len(diffs), "seed": seed}


def taxonomy(rows: list[dict]) -> dict:
    c = collections.Counter()
    for r in rows:
        ref, pred = r["ref_norm"], r["pred_norm"]
        sm = difflib.SequenceMatcher(None, ref, pred, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            if tag == "replace":
                c["substitution"] += max(i2 - i1, j2 - j1)
            elif tag == "delete":
                c["deletion"] += i2 - i1
            elif tag == "insert":
                c["insertion"] += j2 - j1
    return dict(c)


def coverage(rows: list[dict], vocab: dict) -> dict:
    known = set(vocab["char2id"])
    miss = collections.Counter()
    all_known = 0
    for r in rows:
        m = [c for c in r["ref_norm"] if c not in known]
        miss.update(m)
        if not m:
            all_known += 1
    total = sum(len(r["ref_norm"]) for r in rows)
    return {
        "ref_chars": total,
        "missing_types": len(miss),
        "missing_tokens": sum(miss.values()),
        "coverage": 1.0 - sum(miss.values()) / total if total else 0.0,
        "missing_top": miss.most_common(20),
        "sentences_all_known": all_known,
        "sentences": len(rows),
    }


def vocab_oracle(rows: list[dict], vocab: dict) -> dict:
    """Best-case diagnostic: drop reference chars outside train vocab from both sides.

    This is not a trained oracle; it is a lower-bound diagnostic for the residual
    coverage gap. Report it with that label, never as a model result.
    """
    known = set(vocab["char2id"])
    e = n = 0
    for r in rows:
        ref = "".join(c for c in r["ref_norm"] if c in known)
        pred = "".join(c for c in r["pred_norm"] if c in known)
        # Levenshtein
        if len(ref) < len(pred):
            ref, pred = pred, ref
        prev = list(range(len(pred) + 1))
        for i, rc in enumerate(ref, 1):
            cur = [i]
            for j, pc in enumerate(pred, 1):
                cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (rc != pc)))
            prev = cur
        e += prev[-1]
        n += len(ref)
    return {"cer_known_only": e / n if n else 0.0, "errors": e, "ref_chars": n,
            "note": "diagnostic lower bound; not a model result"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--arm", action="append", default=[], help="name=json")
    ap.add_argument("--vocab", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bootstrap", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    vocab = json.load(open(a.vocab, encoding="utf-8"))
    arms = {}
    for spec in a.arm:
        name, path = spec.split("=", 1)
        d = load_json(path)
        arms[name] = d
    if not arms:
        raise SystemExit("no --arm")
    ref_name = "fa" if "fa" in arms else next(iter(arms))
    ref_rows = arms[ref_name]["sentences"]
    out = {"label": a.label, "reference_arm": ref_name, "arms": {}, "pairwise": {}, "taxonomy": {},
           "coverage": {}, "vocab_oracle": {}}
    for name, d in arms.items():
        rows = d["sentences"]
        cer, e, n = corpus_cer(rows)
        out["arms"][name] = {
            "n": len(rows),
            "cer": cer,
            "errors": e,
            "ref_chars": n,
            "decode_file_cer": d.get("cer"),
            "pred_chars": sum(len(r["pred_norm"]) for r in rows),
            "pred_ref_ratio": sum(len(r["pred_norm"]) for r in rows) / max(1, n),
        }
        out["taxonomy"][name] = taxonomy(rows)
        out["coverage"][name] = coverage(rows, vocab)
        out["vocab_oracle"][name] = vocab_oracle(rows, vocab)
        if len(rows) != len(ref_rows):
            raise SystemExit(f"row count mismatch {name}: {len(rows)} vs {len(ref_rows)}")
        out["pairwise"][name] = paired_bootstrap(ref_rows, rows, n_boot=a.bootstrap, seed=a.seed)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
