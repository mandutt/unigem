"""R2 T1 확장 — 신규 오타 쌍 1,500개 생성 (코퍼스 v2와 문장 중복 금지).

- FLEURS ko/en에서 코퍼스 v2에 없는 문장만 사용
- 오타 규칙: 자모 변형/전위/삭제/중복/공백 (새 시드)
- split: 그룹(문장) 단위 70/15/15
"""
from __future__ import annotations

import hashlib
import json
import os
import random

from tokenizers import Tokenizer

ROOT = r"C:\code\unigem"
FLEURS_HF = os.path.expanduser(
    r"~/.cache/huggingface/hub/datasets--google--fleurs/snapshots/"
    r"70bb2e84b976b7e960aa89f1c648e09c59f894dd/data")
OUT = os.path.join(ROOT, "data", "r2")
SEED = 20261105

CHO = list("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")
JUNG = list("ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ")
JONG = ["", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ",
        "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]


def read_tsv(lang, split):
    p = os.path.join(FLEURS_HF, lang, f"{split}.tsv")
    if not os.path.exists(p):
        return []
    out = []
    for line in open(p, encoding="utf-8"):
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 4 and parts[3].strip():
            out.append(parts[3].strip())
    return out


def hangul_typo(rng, ch):
    code = ord(ch)
    if not (0xAC00 <= code <= 0xD7A3):
        return ch
    s = code - 0xAC00
    cho, jung, jong = s // 588, (s % 588) // 28, s % 28
    p = rng.random()
    if p < 0.5:
        jung = (jung + rng.choice([-1, 1])) % 21
    elif p < 0.8:
        jong = (jong + rng.choice([-1, 1])) % 28
    else:
        cho = (cho + rng.choice([-1, 1])) % 19
    return chr(0xAC00 + (cho * 21 + jung) * 28 + jong)


KEY_ADJ = {"q": "wa", "w": "qes", "e": "wrd", "r": "etf", "t": "ryg", "y": "tuh", "u": "yij",
           "i": "uok", "o": "ipl", "p": "o", "a": "qsz", "s": "awdx", "d": "sefc", "f": "drgv",
           "g": "fthb", "h": "gyjn", "j": "hukm", "k": "jil", "l": "ko"}


def typo(rng, text, lang):
    chars = list(text)
    n_edit = rng.randint(1, 3)
    for _ in range(n_edit):
        if len(chars) < 8:
            break
        i = rng.randrange(1, len(chars) - 1)
        op = rng.random()
        if lang == "ko_kr" and 0xAC00 <= ord(chars[i]) <= 0xD7A3:
            if op < 0.6:
                chars[i] = hangul_typo(rng, chars[i])
            elif op < 0.8:
                chars[i], chars[i + 1] = chars[i + 1], chars[i]
            else:
                chars.insert(i, chars[i])
        else:
            c = chars[i]
            if op < 0.3 and c.lower() in KEY_ADJ:
                chars[i] = rng.choice(KEY_ADJ[c.lower()])
            elif op < 0.55:
                chars[i] = c.upper() if c.islower() else c.lower()
            elif op < 0.75:
                del chars[i]
            elif op < 0.9:
                chars.insert(i, c)
            else:
                chars[i] = " "
    out = "".join(chars)
    return out if out != text else text + " "


def split_of(key):
    v = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) % 100
    return "train" if v < 70 else ("val" if v < 85 else "test")


def main():
    rng = random.Random(SEED)
    os.makedirs(OUT, exist_ok=True)
    used = {json.loads(l)["text"] for l in open(os.path.join(ROOT, "data", "b1_5", "corpus_v2", "corpus.jsonl"), encoding="utf-8")}
    rows = []
    for lang, n in (("ko_kr", 750), ("en_us", 750)):
        pool = []
        for sp in ("train", "dev", "test"):
            for t in read_tsv(lang, sp):
                if t not in used and t not in pool:
                    pool.append(t)
        rng.shuffle(pool)
        for i, t in enumerate(pool[:n]):
            g = f"{lang}-{i}"
            rows.append({"id": f"{g}-clean", "kind": "typo_clean", "lang": lang, "text": t,
                         "split": split_of(g), "group": g, "source": "fleurs"})
            rows.append({"id": f"{g}-noisy", "kind": "typo_noisy", "lang": lang, "text": typo(rng, t, lang),
                         "split": split_of(g), "group": g, "source": "fleurs+rule"})
    with open(os.path.join(OUT, "t1_corpus.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("pairs", len(rows) // 2, "rows", len(rows),
          "splits", {k: sum(1 for r in rows if r["split"] == k) for k in ("train", "val", "test")})
    # 검증: clean/noisy 동일 비율
    bad = sum(1 for r in rows if r["kind"] == "typo_noisy" and not r["text"])
    print("empty_noisy", bad)


if __name__ == "__main__":
    main()
