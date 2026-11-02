"""P1 F4 파일럿 — 정상/오류 문장 생성 (Addendum B §B-6.1).

- 정상: FLEURS ko 중 코퍼스 v2에 없는 문장
- 오류: 규칙 합성 1~3개 (띄어쓰기 부분, 자모, 어미 혼동, 식별자, 다중)
- 어미 혼동(되/돼, 안/않)은 **테스트 전용 홀드아웃**
"""
from __future__ import annotations

import hashlib
import json
import os
import random

ROOT = r"C:\code\unigem"
FLEURS_HF = os.path.expanduser(
    r"~/.cache/huggingface/hub/datasets--google--fleurs/snapshots/"
    r"70bb2e84b976b7e960aa89f1c648e09c59f894dd/data")
OUT = os.path.join(ROOT, "data", "p1")
SEED = 20261107

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


def split_of(k):
    v = int(hashlib.sha256(k.encode()).hexdigest()[:8], 16) % 100
    return "train" if v < 70 else ("val" if v < 85 else "test")


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


def edit_spacing(rng, text):
    spaces = [i for i, c in enumerate(text) if c == " "]
    if not spaces:
        return text, []
    i = rng.choice(spaces)
    if rng.random() < 0.5:
        return text[:i] + text[i + 1:], [(i, i + 1, "spacing_del")]
    j = rng.randrange(1, len(text) - 1)
    return text[:j] + " " + text[j:], [(j, j + 1, "spacing_ins")]


def edit_jamo(rng, text):
    idx = [i for i, c in enumerate(text) if 0xAC00 <= ord(c) <= 0xD7A3]
    if not idx:
        return text, []
    i = rng.choice(idx)
    return text[:i] + hangul_typo(rng, text[i]) + text[i + 1:], [(i, i + 1, "jamo")]


def edit_ending(rng, text):
    for good, bad in (("되었", "돼었"), ("되면", "돼면"), ("돼요", "되요"), ("않", "안")):
        p = text.find(good)
        if p >= 0:
            return text[:p] + bad + text[p + len(good):], [(p, p + len(good), "ending")]
    return text, []


def edit_ident(rng, text):
    idx = [i for i, c in enumerate(text) if c.isdigit() or (c.isascii() and c.isalpha())]
    if not idx:
        return text, []
    i = rng.choice(idx)
    c = text[i]
    rep = str((int(c) + 1) % 10) if c.isdigit() else ("x" if c.lower() != "x" else "y")
    return text[:i] + rep + text[i + 1:], [(i, i + 1, "ident")]


def make_error(rng, text, allowed, n_edit, tries=8):
    for _ in range(tries):
        out = text; edits = []
        for _ in range(n_edit):
            t = rng.choice(allowed)
            f = {"spacing": edit_spacing, "jamo": edit_jamo, "ending": edit_ending, "ident": edit_ident}[t]
            cand, ed = f(rng, out)
            if ed:
                out = cand; edits += ed
        if out != text and edits:
            return out, edits
    return None


def load_c4(limit=6000):
    """AI Hub C4 교정문에서 자연 문장 추가."""
    import zipfile, ijson
    base = (r"C:\code\dataset\ai_hub\인터페이스(자판음성)별 고빈도 오류 교정 데이터"
            r"\143.인터페이스(자판-음성)별 고빈도 오류 교정 데이터\01-1.정식개방데이터\Training\02.라벨링데이터")
    out = []
    for fn in sorted(os.listdir(base)):
        if not fn.endswith(".zip") or len(out) >= limit:
            continue
        with zipfile.ZipFile(os.path.join(base, fn)) as zf:
            with zf.open(zf.namelist()[0]) as f:
                for rec in ijson.items(f, "data.item"):
                    s = rec.get("annotation", {}).get("cor_sentence", "").strip()
                    if 20 <= len(s) <= 150 and s not in out:
                        out.append(s)
                        if len(out) >= limit:
                            break
    return out


def main():
    rng = random.Random(SEED)
    os.makedirs(OUT, exist_ok=True)
    used = {json.loads(l)["text"] for l in open(os.path.join(ROOT, "data", "b1_5", "corpus_v2", "corpus.jsonl"), encoding="utf-8")}
    pool = []
    for sp in ("train", "dev", "test"):
        for t in read_tsv("ko_kr", sp):
            if t not in used and t not in pool:
                pool.append(t)
    for t in load_c4(6000):
        if t not in used and t not in pool:
            pool.append(t)
    rng.shuffle(pool)
    print("pool", len(pool), flush=True)

    # 정상: train 1,600 / test 700 (그룹 분할)
    normals = {"train": pool[:1600], "test": pool[1600:2300]}
    rows = []
    for sp, texts in normals.items():
        for i, t in enumerate(texts):
            g = f"n-{sp}-{i}"
            rows.append({"id": g, "text": t, "clean": t, "split": sp, "group": g,
                         "is_error": 0, "edits": [], "source": "fleurs"})
    # 오류: train 2,400 (spacing/jamo/ident/multi) / test 1,000 (ending 포함)
    for sp, n_err, allowed in (("train", 2400, ["spacing", "jamo", "ident"]),
                               ("test", 1000, ["spacing", "jamo", "ident", "ending"])):
        texts = normals[sp]
        made = 0; i = 0
        while made < n_err and i < n_err * 20:
            base = texts[i % len(texts)]
            i += 1
            g = f"e-{sp}-{made}"
            res = make_error(rng, base, allowed, rng.randint(1, 3))
            if res is None:
                continue
            out, edits = res
            rows.append({"id": g, "text": out, "clean": base, "split": sp, "group": g,
                         "is_error": 1, "edits": edits, "source": "rule:" + ",".join(sorted({e[2] for e in edits}))})
            made += 1
    with open(os.path.join(OUT, "p1_corpus.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    print("rows", len(rows), "by_split", Counter((r["split"], r["is_error"]) for r in rows),
          "types", Counter(r["source"] for r in rows if r["is_error"]).most_common(8))


if __name__ == "__main__":
    main()
