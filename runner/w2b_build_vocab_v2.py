"""Build V2 CTC vocabulary from train-only text.

V2 preserves every V1 character/id and appends new characters found in the
Wave 1 6h train manifest and the KsponSpeech_05 train transcript. Eval/test
text is NOT used to build the vocabulary; it is only measured for coverage.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path("C:/code/unigem")
V1 = ROOT / "data/wave2a_lite/vocab.json"
MANIFEST = ROOT / "data/wave1/manifest.jsonl"
KSPON_TRN = Path("D:/unigem/w2b/train.trn")
OUT = ROOT / "data/wave2b/vocab_v2.json"


def clean_kspon(text: str) -> str:
    import re
    s = text.strip()
    s = re.sub(r"\(([^()]*)\)/\(([^()]*)\)", r"\1", s)
    s = re.sub(r"(^|\s)[A-Za-z]{1,2}/", r"\1", s)
    s = s.replace("+", "")
    s = re.sub(r"\([^()]*\)", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--short", default="", help="short manifest whose refs define V2 (instead of all train.trn)")
    a = ap.parse_args()
    v1 = json.loads(V1.read_text(encoding="utf-8"))
    chars = list(v1["chars"])
    seen = set(chars)
    n_manifest = 0
    n_trn = 0
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        n_manifest += 1
        for c in str(r.get("text", "")).replace(" ", ""):
            if c not in seen:
                seen.add(c)
                chars.append(c)
    if a.short:
        for line in Path(a.short).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            n_trn += 1
            for c in str(r.get("ref", r.get("text", ""))).replace(" ", ""):
                if c not in seen:
                    seen.add(c)
                    chars.append(c)
    else:
        for line in KSPON_TRN.read_text(encoding="utf-8", errors="replace").splitlines():
            if " :: " not in line:
                continue
            _, raw = line.split(" :: ", 1)
            n_trn += 1
            for c in clean_kspon(raw).replace(" ", ""):
                if c not in seen:
                    seen.add(c)
                    chars.append(c)
    # stable: V1 order preserved, new chars appended in first-seen order
    vocab = {"blank": 0, "chars": chars,
             "char2id": {c: i + 1 for i, c in enumerate(chars)}}
    out_path = Path(a.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(vocab, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"v1_chars": len(v1["chars"]), "v2_chars": len(chars),
                      "new_chars": len(chars) - len(v1["chars"]),
                      "manifest_rows": n_manifest, "trn_rows": n_trn,
                      "out": str(out_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
