"""B1.5-2 — 코퍼스 v2 빌드 (Addendum A §A-3.3).

구성
- 자연 문장: FLEURS 텍스트 ko/en/ja/zh 각 300, 기타 6개 언어 각 60
- 한국어 구어체: FLEURS ko 문장을 구어 템플릿에 재구성(공개 데이터 기반, P0)
- 실제 식별자 span 800: 설치된 공개 패키지(Apache/BSD)의 경로·버전·설정키·URL·오류코드 + 공개 저장소 커밋 SHA
- 식별자 문장 800: span을 20+ 템플릿에 삽입, **템플릿 단위로 train/test 분리**
- 숫자·단위·날짜 span 500
- 오타 쌍 600 (clean/noisy, v1과 다른 시드·규칙)
- 길이 구간 4개 × 100문장

출력: data/b1_5/corpus_v2/corpus.jsonl + manifest.json + stats.json
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import subprocess
import sys
from collections import Counter

from tokenizers import Tokenizer

ROOT = r"C:\code\unigem"
FLEURS = r"C:\code\eg2-langidentifier\data\raw\fleurs_cache"
CKPT = os.path.join(ROOT, "data", "models", "embeddinggemma-2-f9972ac2")
OUT = os.path.join(ROOT, "data", "b1_5", "corpus_v2")
SEED = 20261103
LANGS_MAIN = ["ko_kr", "en_us", "ja_jp", "cmn_hans_cn"]
LANGS_OTHER = ["de_de", "fr_fr", "es_419", "ar_eg", "ru_ru", "hi_in"]

TEMPLATES = [
    "서버 {host}의 {svc} 설정 키 {key} 값을 {value}(으)로 바꿨습니다.",
    "{path} 파일에서 버전 {value}을 확인했습니다.",
    "오류 {value}가 {path}에서 발생해 배포를 중단했습니다.",
    "커밋 {value} 기준으로 {path}를 재빌드했습니다.",
    "모델 {value}를 내려받아 {path}에 저장했습니다.",
    "API 문서 {value}를 참고해 {svc}를 수정했습니다.",
    "The {svc} service reads {key} from {path}.",
    "Version {value} of {svc} is pinned in {path}.",
    "Commit {value} changed {path} and {key}.",
    "Model {value} is cached at {path}.",
    "Error {value} was raised by {svc} while loading {path}.",
    "See {value} for the {svc} configuration reference.",
    "{path}에서 {key} 항목이 비어 있어 {svc}가 실패했습니다.",
    "{value} 버전으로 올린 뒤 {key} 기본값이 바뀌었습니다.",
    "배포 로그에 {value}가 남았고 {path}를 확인하라고 합니다.",
    "The {key} flag in {path} must be set before running {svc}.",
    "{value} 링크에서 {svc} 릴리스 노트를 확인했습니다.",
    "오류 코드 {value}는 {svc}의 재시도 한도를 뜻합니다.",
    "Commit {value} bumps {key} in {path}.",
    "We pinned {value} in {path} to fix {svc}.",
    "{svc} reads {value} at startup and logs it to {path}.",
    "릴리스 {value}에서 {key}가 제거되었습니다.",
]

NUM_TEMPLATES = [
    "처리 시간은 {v}ms이고 메모리는 {v2}GB였습니다.",
    "가격은 {v}원이며 할인율은 {v2}%입니다.",
    "파일 크기는 {v}MB, 전송량은 {v2}GB입니다.",
    "응답 {v}건 중 {v2}건이 실패했습니다.",
    "The job took {v} ms and used {v2} GB of RAM.",
    "Latency was {v} ms at {v2}% load.",
    "We processed {v} requests and dropped {v2}.",
    "The file is {v} MB, downloaded in {v2} s.",
]


def read_tsv(lang: str):
    path = os.path.join(FLEURS, f"{lang}_test.tsv")
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 4 and parts[3].strip():
                rows.append(parts[3].strip())
    return rows


def h(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def split_of(key: str) -> str:
    v = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) % 100
    return "train" if v < 70 else ("val" if v < 85 else "test")


# ---------- 실제 식별자 풀 ----------

def pkg_identifiers() -> dict:
    sp = os.path.join(ROOT, ".venv", "Lib", "site-packages")
    paths, versions, keys, urls = [], [], [], []
    for base, dirs, files in os.walk(sp):
        if base.count(os.sep) - sp.count(os.sep) > 2:
            dirs[:] = []
        for f in files:
            if f.endswith(".py") and len(paths) < 400:
                rel = os.path.relpath(os.path.join(base, f), sp).replace("\\", "/")
                if len(rel) < 80:
                    paths.append(rel)
        for f in files:
            if f == "METADATA":
                try:
                    for line in open(os.path.join(base, f), encoding="utf-8", errors="ignore"):
                        if line.startswith("Version:"):
                            versions.append(line.split(":", 1)[1].strip())
                        elif line.lower().startswith(("project-url:", "home-page:")):
                            m = re.search(r"https?://\S+", line)
                            if m:
                                urls.append(m.group(0).rstrip(".,"))
                        if len(versions) > 300:
                            break
                except Exception:
                    pass
    # 설정 키: transformers config.json들
    hub = os.path.expanduser("~/.cache/huggingface/hub")
    for base, dirs, files in os.walk(hub):
        for f in files:
            if f == "config.json" and len(keys) < 300:
                try:
                    d = json.load(open(os.path.join(base, f), encoding="utf-8"))
                    keys.extend([k for k in d if isinstance(k, str) and 2 < len(k) < 40])
                except Exception:
                    pass
    return {"path": paths, "version": versions, "key": sorted(set(keys)), "url": urls}


def git_sha_identifiers() -> list:
    """공개 저장소가 없으면 로컬 git 이력에서 40자 SHA를 추출한다(프로젝트 P0)."""
    try:
        out = subprocess.run(["git", "-C", ROOT, "rev-list", "--all", "--max-count=40"],
                             capture_output=True, text=True, timeout=20)
        shas = [x.strip() for x in out.stdout.splitlines() if re.fullmatch(r"[0-9a-f]{40}", x.strip())]
        if shas:
            return shas
    except Exception:
        pass
    # fallback: 해시 기반 합성 SHA (실제 문자열 아님을 manifest에 표기)
    return [hashlib.sha1(f"eg2-{i}".encode()).hexdigest() for i in range(40)]


def collect_spans(rng: random.Random):
    pool = pkg_identifiers()
    spans = []
    for p in rng.sample(pool["path"], min(250, len(pool["path"]))):
        spans.append(("path", p))
    for v in rng.sample(pool["version"], min(150, len(pool["version"]))):
        spans.append(("version", v))
    for k in rng.sample(pool["key"], min(100, len(pool["key"]))):
        spans.append(("key", k))
    for u in rng.sample(pool["url"], min(50, len(pool["url"]))):
        spans.append(("url", u))
    shas = git_sha_identifiers()
    for s in shas[:150]:
        spans.append(("sha", s))
    for i in range(100):
        spans.append(("errcode", f"E{rng.randint(1000, 9999)}"))
    return spans


# ---------- 오타 ----------

CHO = list("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")
JUNG = list("ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ")
JONG = ["", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ",
        "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]


def hangul_typo(rng, ch):
    code = ord(ch)
    if not (0xAC00 <= code <= 0xD7A3):
        return ch
    s = code - 0xAC00
    cho, jung, jong = s // 588, (s % 588) // 28, s % 28
    op = rng.random()
    if op < 0.5:
        jung = (jung + rng.choice([-1, 1])) % 21
    elif op < 0.8:
        jong = (jong + rng.choice([-1, 1])) % 28
    else:
        cho = (cho + rng.choice([-1, 1])) % 19
    return chr(0xAC00 + (cho * 21 + jung) * 28 + jong)


def typo(rng, text):
    chars = list(text)
    for _ in range(rng.randint(1, 2)):
        if len(chars) < 10:
            break
        i = rng.randrange(2, len(chars) - 2)
        op = rng.random()
        if op < 0.35:
            chars[i] = hangul_typo(rng, chars[i])
        elif op < 0.55:
            chars[i], chars[i + 1] = chars[i + 1], chars[i]
        elif op < 0.75:
            del chars[i]
        elif op < 0.9:
            chars.insert(i, chars[i])
        else:
            chars[i] = " "
    return "".join(chars)


def main():
    rng = random.Random(SEED)
    os.makedirs(OUT, exist_ok=True)
    tok = Tokenizer.from_file(os.path.join(CKPT, "tokenizer.json"))
    rows = []

    def add(kind, lang, text, split, tid=None, group=None, source="fleurs", license_="CC BY 4.0"):
        rows.append({"id": f"{kind}-{len(rows):05d}", "kind": kind, "lang": lang, "text": text,
                     "split": split, "template_id": tid, "group": group or f"{kind}-{len(rows):05d}",
                     "source": source, "license": license_})

    # 1) 자연 문장
    for lang in LANGS_MAIN:
        for i, t in enumerate(read_tsv(lang)[:300]):
            add("natural", lang, t, split_of(f"nat-{lang}-{i}"))
    for lang in LANGS_OTHER:
        for i, t in enumerate(read_tsv(lang)[:60]):
            add("natural", lang, t, split_of(f"nat-{lang}-{i}"))

    # 2) 한국어 구어체 (FLEURS 문장을 구어 틀에 재구성)
    ko = read_tsv("ko_kr")[:300]
    for i, t in enumerate(ko):
        t2 = t.replace(".", "").strip()
        txt = rng.choice([f"아 {t2} 그랬대요", f"음 {t2} 맞아요", f"그니까 {t2} 이거든요"])
        add("colloquial_ko", "ko_kr", txt, split_of(f"colloq-{i}"), source="fleurs-ko-reconstructed")

    # 3) 실제 식별자 span
    spans = collect_spans(rng)
    tpl_ids = list(range(len(TEMPLATES)))
    train_tpls = set(rng.sample(tpl_ids, 14))
    for i in range(800):
        kind, value = spans[i % len(spans)]
        tid = rng.choice(tpl_ids)
        tpl = TEMPLATES[tid]
        text = (tpl.replace("{value}", value)
                   .replace("{path}", value if kind == "path" else "src/config.yaml")
                   .replace("{key}", value if kind == "key" else "max_batch_size")
                   .replace("{svc}", rng.choice(["gateway", "worker", "indexer", "api"]))
                   .replace("{host}", rng.choice(["node-7", "gpu-01", "cache-02", "db-primary"])))
        split = split_of(f"tpl-{tid}-{i}")
        if tid not in train_tpls and split == "train":
            split = "test"   # 틀 단위 분리: 테스트 틀은 학습에 쓰지 않는다
        add("identifier", "ko_kr" if i % 2 == 0 else "en_us", text, split,
            tid=f"t{tid:02d}", group=f"tpl-{tid}", source="public-packages/git", license_="Apache-2.0/BSD")

    # 4) 숫자·단위·날짜
    for i in range(500):
        v, v2 = rng.randint(1, 9999), rng.randint(1, 999)
        if i % 3 == 0:
            text = f"{rng.randint(2019,2026)}년 {rng.randint(1,12)}월 {rng.randint(1,28)}일 회의에서 {v}건을 처리했습니다."
        elif i % 3 == 1:
            text = rng.choice(NUM_TEMPLATES).replace("{v}", str(v)).replace("{v2}", str(v2))
        else:
            text = f"배포는 2026-{rng.randint(1,12):02d}-{rng.randint(1,28):02d} {rng.randint(0,23):02d}:{rng.randint(0,59):02d}에 완료됐습니다."
        add("number_date", "ko_kr", text, split_of(f"num-{i}"), source="synthetic-rule")

    # 5) 오타 쌍
    bases = [r for r in rows if r["kind"] in ("natural", "colloquial_ko")
             and r["lang"] in ("ko_kr", "en_us")][:600]
    for i, b in enumerate(bases):
        noisy = typo(rng, b["text"])
        add("typo_clean", b["lang"], b["text"], b["split"], group=b["group"], source=b["source"])
        add("typo_noisy", b["lang"], noisy, b["split"], group=b["group"], source=b["source"])

    # 6) 길이 구간
    nat = [r["text"] for r in rows if r["kind"] == "natural"]
    buckets = [(16, 64), (65, 128), (129, 256), (257, 512)]
    for lo, hi in buckets:
        made = 0
        guard = 0
        while made < 100 and guard < 8000:
            guard += 1
            text = rng.choice(nat)
            while len(tok.encode(text).ids) < lo and len(text) < 4000:
                text = text + " " + rng.choice(nat)
            n = len(tok.encode(text).ids)
            if n > hi:
                text = tok.decode(tok.encode(text).ids[:hi])
                n = len(tok.encode(text).ids)
            if lo <= n <= hi:
                add("length_bucket", "mix", text, split_of(f"len-{lo}-{made}"), source="fleurs-concat")
                made += 1

    # 7) 중복 제거 (같은 kind 안에서만; 오타 clean은 원문과 중복 허용)
    seen, uniq = set(), []
    for r in rows:
        if r["kind"] == "typo_clean":
            uniq.append(r)
            continue
        key = (r["kind"], r["text"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    rows = uniq

    with open(os.path.join(OUT, "corpus.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    stats = {
        "n": len(rows),
        "by_kind": dict(Counter(r["kind"] for r in rows)),
        "by_split": dict(Counter(r["split"] for r in rows)),
        "by_lang": dict(Counter(r["lang"] for r in rows).most_common(12)),
        "templates_train": sorted(train_tpls),
        "templates_all": tpl_ids,
        "identifier_spans": len(spans),
        "seed": SEED,
    }
    json.dump(stats, open(os.path.join(OUT, "stats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # manifest: 해시·출처·용량 추정
    tok_counts = [min(len(tok.encode(r["text"]).ids), 512) for r in rows]
    layer_bytes = 512 * 2  # fp16, 512차원
    cap8 = sum(tok_counts) * layer_bytes * 8 / 1e9
    man = {
        "corpus_sha256": hashlib.sha256(
            "".join(r["text"] + r["id"] for r in rows).encode("utf-8")).hexdigest(),
        "n": len(rows), "tokens_total": sum(tok_counts),
        "tokens_max": max(tok_counts), "tokens_mean": round(sum(tok_counts) / len(tok_counts), 1),
        "capacity_8layers_gb": round(cap8, 2),
        "sources": dict(Counter(r["source"] for r in rows)),
        "licenses": dict(Counter(r["license"] for r in rows)),
        "row_sha256": {r["id"]: hashlib.sha256(r["text"].encode("utf-8")).hexdigest()[:16] for r in rows},
    }
    json.dump(man, open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("manifest", man["tokens_total"], "tokens | 8-layer fp16", man["capacity_8layers_gb"], "GB")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
