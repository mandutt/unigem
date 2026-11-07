"""Audit teacher-summary bias: 4-gram copy rate and leading-sentence bias.

Compares A1 native teacher outputs with gold summaries on the same document IDs.
No model execution; text-only audit.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_b1d_teacher_fidelity import read_jsonl, teacher_map  # noqa: E402

DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
TRAIN_TEACHER = ROOT / "reports/provenance/C5_b1d/teacher_train100.jsonl"
VAL_TEACHER = ROOT / "reports/provenance/C5_a1/pilot300_val161/predictions.jsonl"
OUT = ROOT / "reports/provenance/C5_b1d/teacher_bias_audit.json"


def norm(s: str) -> str:
    return re.sub(r"\s+", "", str(s))


def ngrams(s: str, n: int = 4) -> list[str]:
    s = norm(s)
    return [s[i : i + n] for i in range(max(0, len(s) - n + 1))]


def copy_rate(summary: str, source: str, n: int = 4) -> float:
    gs = ngrams(summary, n)
    if not gs:
        return 0.0
    src = norm(source)
    return sum(g in src for g in gs) / len(gs)


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。？！])\s*", str(text).strip())
    return [p.strip() for p in parts if p.strip()]


def leading_sentence_rate(summary: str, source: str, frac: float = 0.4) -> tuple[float, int, int]:
    ss = sentences(summary)
    src = sentences(source)
    if not ss or not src:
        return 0.0, 0, len(src)
    k = max(1, int(len(src) * frac))
    leading = 0
    for s in ss:
        best_i, best = 0, -1.0
        for i, t in enumerate(src):
            r = SequenceMatcher(None, norm(s), norm(t)).ratio()
            if r > best:
                best_i, best = i, r
        if best_i < k:
            leading += 1
    return leading / len(ss), leading, len(ss)


def audit(rows: dict[str, str], by_id: dict[str, dict], ids: list[str]) -> dict:
    cr, lr, lens = [], [], []
    for rid in ids:
        if rid not in rows or rid not in by_id:
            continue
        text = rows[rid]
        src = str(by_id[rid]["passage"])
        cr.append(copy_rate(text, src))
        r, _, _ = leading_sentence_rate(text, src)
        lr.append(r)
        lens.append(len(norm(text)))
    n = len(cr)
    return {
        "n": n,
        "copy4_char_mean": sum(cr) / n if n else None,
        "leading40_sentence_mean": sum(lr) / n if n else None,
        "char_len_mean": sum(lens) / n if n else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    args.out = args.out if args.out.is_absolute() else ROOT / args.out

    recs = read_jsonl(DATA)
    by_id = {str(r["id"]): r for r in recs}
    splits = json.loads((ROOT / "reports/provenance/C5_clean/splits.json").read_text(encoding="utf-8"))
    tr = teacher_map(TRAIN_TEACHER, 0)
    va = teacher_map(VAL_TEACHER, 0)
    train_ids = [rid for rid in splits["train"] if rid in tr][:100]
    val_ids = [rid for rid in splits["val"] if rid in va][:100]

    def gold_map(ids):
        return {rid: str(by_id[rid]["summary"]) for rid in ids if rid in by_id}

    result = {
        "audit": "teacher_vs_gold_bias",
        "copy_ngram": 4,
        "copy_unit": "character after whitespace removal",
        "leading_definition": "summary sentence whose best-matching source sentence is in the first 40% of source sentences",
        "train_teacher": audit(tr, by_id, train_ids),
        "train_gold": audit(gold_map(train_ids), by_id, train_ids),
        "val_teacher": audit(va, by_id, val_ids),
        "val_gold": audit(gold_map(val_ids), by_id, val_ids),
        "test_split_used": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
