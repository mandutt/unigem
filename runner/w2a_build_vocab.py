"""Build train-only vocab for Wave 2A-lite.

- top N Hangul syllables by frequency in Wave 1 training text
- digits 0-9, Latin a-z, space, and an explicit unk marker
- evaluate coverage on FLEURS ko dev refs with normalize_nospace
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from eval.normalize import normalize_nospace


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-manifest", default=str(ROOT / "data/wave1/manifest.jsonl"))
    ap.add_argument("--dev-manifest", default=str(ROOT / "data/wave2a_lite/fleurs_dev.jsonl"))
    ap.add_argument("--out", default=str(ROOT / "data/wave2a_lite/vocab.json"))
    ap.add_argument("--top-syllables", type=int, default=2350)
    a = ap.parse_args()

    counts = collections.Counter()
    for line in open(a.train_manifest, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        text = r.get("text") or r.get("ref") or ""
        for ch in text:
            if "\uac00" <= ch <= "\ud7a3":
                counts[ch] += 1
    top = [ch for ch, _ in counts.most_common(a.top_syllables)]
    chars = []
    for ch in top + list("0123456789") + list("abcdefghijklmnopqrstuvwxyz") + [" "]:
        if ch not in chars:
            chars.append(ch)
    vocab = {"blank": 0, "chars": chars, "char2id": {c: i + 1 for i, c in enumerate(chars)}}

    dev_chars = collections.Counter()
    dev_rows = [json.loads(l) for l in open(a.dev_manifest, encoding="utf-8") if l.strip()]
    for r in dev_rows:
        dev_chars.update(normalize_nospace(r["ref"]))
    missing = {c: n for c, n in dev_chars.items() if c not in vocab["char2id"]}
    cov = 1.0 - sum(missing.values()) / max(1, sum(dev_chars.values()))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(vocab, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    summary = {
        "train_hangul_types": len(counts),
        "top_syllables": a.top_syllables,
        "vocab_chars": len(chars),
        "vocab_with_blank": len(chars) + 1,
        "dev_rows": len(dev_rows),
        "dev_chars": sum(dev_chars.values()),
        "dev_missing_types": len(missing),
        "dev_missing_tokens": sum(missing.values()),
        "dev_coverage": cov,
        "dev_missing_top": collections.Counter(missing).most_common(30),
    }
    json.dump(summary, open(str(a.out).replace(".json", "_coverage.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
