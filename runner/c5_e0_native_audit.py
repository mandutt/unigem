"""E0 native-tokenizer audit for the C5 EG2 -> mT5 plan.

No model forward, no training. Compares the legacy T5Gemma2 tokenizer (used by
the existing EG2 layer cache) with the EG2-native tokenizer on the same 300
train / 100 val F5 documents.

Outputs a JSON summary only. Test split is never read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
EG2 = ROOT / "data/models/embeddinggemma-2-f9972ac2"
T5 = ROOT / "data/models/t5gemma-2-270m-270m"
OUT = ROOT / "reports/provenance/C5_e0/native_tokenizer_audit.json"
PROMPT = "summarize: "
MAX_LENGTH = 1024


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint(path: Path, tok) -> dict[str, Any]:
    files = {}
    for name in ("tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"):
        p = path / name
        if p.exists():
            files[name] = {"bytes": p.stat().st_size, "sha256": digest(p)}
    return {
        "path": str(path.relative_to(ROOT).as_posix()),
        "class": type(tok).__name__,
        "vocab_size": len(tok),
        "bos_token_id": tok.bos_token_id,
        "eos_token_id": tok.eos_token_id,
        "pad_token_id": tok.pad_token_id,
        "all_special_ids": sorted(int(x) for x in tok.all_special_ids),
        "files": files,
    }


def strip_special(ids: list[int], special: set[int]) -> list[int]:
    return [int(x) for x in ids if int(x) not in special]


def char_id_map(ids: list[int], offsets: list[tuple[int, int]], text_len: int) -> list[int | None]:
    out: list[int | None] = [None] * text_len
    for tid, span in zip(ids, offsets):
        start, end = int(span[0]), int(span[1])
        if start == 0 and end == 0:
            continue
        for pos in range(max(0, start), min(text_len, end)):
            if out[pos] is None:
                out[pos] = int(tid)
    return out


def compare_doc(
    rid: str,
    passage: str,
    native,
    legacy,
    special_native: set[int],
    special_legacy: set[int],
) -> dict[str, Any]:
    text = PROMPT + passage
    native_full = native(text, add_special_tokens=True, truncation=False)
    legacy_full = legacy(text, add_special_tokens=True, truncation=False)
    native_enc = native(
        text,
        add_special_tokens=True,
        truncation=True,
        max_length=MAX_LENGTH,
        return_offsets_mapping=True,
    )
    legacy_enc = legacy(
        text,
        add_special_tokens=True,
        truncation=True,
        max_length=MAX_LENGTH,
        return_offsets_mapping=True,
    )
    n_ids = [int(x) for x in native_enc["input_ids"]]
    l_ids = [int(x) for x in legacy_enc["input_ids"]]
    n_content = strip_special(n_ids, special_native)
    l_content = strip_special(l_ids, special_legacy)
    mismatch = sum(1 for a, b in zip(n_content, l_content) if a != b) + abs(len(n_content) - len(l_content))
    n_map = char_id_map(n_ids, native_enc["offset_mapping"], len(text))
    l_map = char_id_map(l_ids, legacy_enc["offset_mapping"], len(text))
    common = [(a, b) for a, b in zip(n_map, l_map) if a is not None and b is not None]
    char_mismatch = sum(1 for a, b in common if a != b)
    digit_positions = [m.start() for m in re.finditer(r"\d", text)]
    digit_pairs = [(n_map[p], l_map[p]) for p in digit_positions if n_map[p] is not None and l_map[p] is not None]
    digit_mismatch = sum(1 for a, b in digit_pairs if a != b)
    return {
        "id": rid,
        "native_len": len(n_ids),
        "legacy_len": len(l_ids),
        "full_len_native": len(native_full["input_ids"]),
        "full_len_legacy": len(legacy_full["input_ids"]),
        "truncated_native": len(native_full["input_ids"]) > MAX_LENGTH,
        "truncated_legacy": len(legacy_full["input_ids"]) > MAX_LENGTH,
        "exact_sequence_match": n_ids == l_ids,
        "content_sequence_match": n_content == l_content,
        "content_token_mismatch": mismatch,
        "native_has_eos": bool(n_ids and n_ids[-1] == native.eos_token_id),
        "legacy_has_eos": bool(l_ids and l_ids[-1] == legacy.eos_token_id),
        "native_special_count": len(n_ids) - len(n_content),
        "legacy_special_count": len(l_ids) - len(l_content),
        "char_pairs": len(common),
        "char_mismatch": char_mismatch,
        "digit_pairs": len(digit_pairs),
        "digit_mismatch": digit_mismatch,
        "native_tail": n_ids[-5:],
        "legacy_tail": l_ids[-5:],
    }


def summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    char_pairs = sum(r["char_pairs"] for r in rows)
    char_mismatch = sum(r["char_mismatch"] for r in rows)
    digit_pairs = sum(r["digit_pairs"] for r in rows)
    digit_mismatch = sum(r["digit_mismatch"] for r in rows)
    return {
        "n_docs": n,
        "exact_sequence_match": sum(r["exact_sequence_match"] for r in rows),
        "content_sequence_match": sum(r["content_sequence_match"] for r in rows),
        "docs_with_content_mismatch": sum(r["content_token_mismatch"] > 0 for r in rows),
        "content_token_mismatch_total": sum(r["content_token_mismatch"] for r in rows),
        "docs_native_has_eos": sum(r["native_has_eos"] for r in rows),
        "docs_legacy_has_eos": sum(r["legacy_has_eos"] for r in rows),
        "docs_native_truncated": sum(r["truncated_native"] for r in rows),
        "docs_legacy_truncated": sum(r["truncated_legacy"] for r in rows),
        "length_diff_native_minus_legacy": {
            "mean": (sum(r["native_len"] - r["legacy_len"] for r in rows) / n) if n else 0.0,
            "min": min((r["native_len"] - r["legacy_len"] for r in rows), default=0),
            "max": max((r["native_len"] - r["legacy_len"] for r in rows), default=0),
        },
        "char_pairs": char_pairs,
        "char_mismatch": char_mismatch,
        "char_mismatch_rate": (char_mismatch / char_pairs) if char_pairs else 0.0,
        "digit_pairs": digit_pairs,
        "digit_mismatch": digit_mismatch,
        "digit_mismatch_rate": (digit_mismatch / digit_pairs) if digit_pairs else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--splits", type=Path, default=SPLITS)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--train-limit", type=int, default=300)
    ap.add_argument("--val-limit", type=int, default=100)
    args = ap.parse_args()

    rows = {str(r["id"]): r for r in read_jsonl(args.data)}
    split_data = json.loads(args.splits.read_text(encoding="utf-8"))
    native = AutoTokenizer.from_pretrained(str(EG2), local_files_only=True)
    legacy = AutoTokenizer.from_pretrained(str(T5), local_files_only=True)
    special_native = {int(x) for x in native.all_special_ids}
    special_legacy = {int(x) for x in legacy.all_special_ids}

    results: dict[str, Any] = {}
    all_rows: list[dict[str, Any]] = []
    for split, limit in (("train", args.train_limit), ("val", args.val_limit)):
        ids = list(split_data[split])[:limit]
        docs = [compare_doc(rid, str(rows[rid]["passage"]), native, legacy, special_native, special_legacy) for rid in ids]
        all_rows.extend(docs)
        results[split] = {"summary": summary(docs), "examples": docs[:3]}

    payload = {
        "experiment": "c5_e0_native_tokenizer_audit",
        "data": str(args.data.relative_to(ROOT).as_posix()),
        "splits": str(args.splits.relative_to(ROOT).as_posix()),
        "prompt": PROMPT,
        "max_length": MAX_LENGTH,
        "train_limit": args.train_limit,
        "val_limit": args.val_limit,
        "test_split_used": False,
        "native": fingerprint(EG2, native),
        "legacy": fingerprint(T5, legacy),
        "splits_result": results,
        "overall": summary(all_rows),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["overall"], ensure_ascii=False, indent=2))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
