"""B1 코퍼스 생성 (P0 전용).

- FLEURS 텍스트: 공개 다국어 문장 10개 언어 × 60
- 합성 슬롯 문장: 숫자·날짜·버전·경로·식별자 (ko 200 / en 100)
- 오타 주입: FLEURS 문장에 자모/문자 편집 (ko 100 / en 50)

출력: data/b1/corpus.jsonl  {id, lang, kind, text, base_id?}
"""
from __future__ import annotations

import json
import os
import random
import re

FLEURS = r"C:\code\eg2-langidentifier\data\raw\fleurs_cache"
OUT = r"C:\code\unigem\data\b1\corpus.jsonl"
LANGS = ["ko_kr", "en_us", "ja_jp", "cmn_hans_cn", "de_de",
         "fr_fr", "es_419", "ar_eg", "ru_ru", "hi_in"]
PER_LANG = 60

KO_TEMPLATES = [
    "서버 {host}의 {svc} 버전은 v{maj}.{min}.{pat}입니다.",
    "{y}년 {m}월 {d}일 {hh}:{mm}에 {person}이 {file}을 수정했습니다.",
    "오류 코드 {code}가 {path}에서 발생했습니다.",
    "모델 {model}의 정확도는 {pct}%이고 처리량은 {qps}입니다.",
    "커밋 {sha}에서 {n}개 파일이 변경되었습니다.",
    "가격은 {amount}원이며 할인율은 {pct}%입니다.",
    "포트 {port}에서 {proto} 요청을 받았습니다.",
    "{y}년 {m}월 {d}일 회의에서 {decision}을 결정했습니다.",
    "사용자 {user}의 토큰은 {token}이고 만료일은 {y}-{m}-{d}입니다.",
    "경로 {path}의 파일 크기는 {size}MB입니다.",
]
EN_TEMPLATES = [
    "The {svc} service on host {host} is running version v{maj}.{min}.{pat}.",
    "On {y}-{m}-{d} at {hh}:{mm}, {person} edited {file}.",
    "Error code {code} occurred at {path}.",
    "Model {model} reached {pct}% accuracy at {qps} queries per second.",
    "Commit {sha} changed {n} files.",
    "The price is {amount} KRW with a {pct}% discount.",
    "Port {port} received a {proto} request.",
    "The meeting on {y}-{m}-{d} decided {decision}.",
    "User {user} has token {token} expiring on {y}-{m}-{d}.",
    "The file at {path} is {size} MB.",
]

HOSTS = ["gpu-01", "node-7", "eg2-1", "db-primary", "cache-02"]
SVCS = ["api", "worker", "gateway", "indexer", "scheduler"]
PEOPLE = ["김민수", "이서연", "박준호", "최지우", "mandu"]
FILES = ["config.yaml", "main.py", "README.md", "deploy.sh", "schema.sql"]
MODELS = ["eg2-q8", "komixv2", "whisper-turbo", "qwen3-vl-2b"]
DECISIONS = ["재배포", "롤백", "일정 연기", "추가 실측"]
PROTOS = ["HTTP", "gRPC", "WebSocket", "TCP"]
PATHS = ["/var/log/app.log", "C:/code/unigem/runner", "/data/home/unigem",
         "src/models/gemma4.py", "/etc/nginx/conf.d"]


def synth(rng: random.Random, lang: str, i: int) -> str:
    tpl = rng.choice(KO_TEMPLATES if lang == "ko" else EN_TEMPLATES)
    vals = {
        "host": rng.choice(HOSTS), "svc": rng.choice(SVCS),
        "maj": rng.randint(0, 9), "min": rng.randint(0, 20), "pat": rng.randint(0, 30),
        "y": rng.randint(2019, 2026), "m": rng.randint(1, 12), "d": rng.randint(1, 28),
        "hh": f"{rng.randint(0,23):02d}", "mm": f"{rng.randint(0,59):02d}",
        "person": rng.choice(PEOPLE), "file": rng.choice(FILES),
        "code": f"E{rng.randint(1000,9999)}", "path": rng.choice(PATHS),
        "model": rng.choice(MODELS), "pct": f"{rng.uniform(50,99.9):.1f}",
        "qps": rng.randint(10, 5000), "sha": f"{rng.getrandbits(32):08x}",
        "n": rng.randint(1, 40), "amount": f"{rng.randint(1000,900000):,}",
        "port": rng.randint(1024, 65535), "proto": rng.choice(PROTOS),
        "decision": rng.choice(DECISIONS), "user": rng.choice(PEOPLE),
        "token": f"tok_{rng.getrandbits(24):06x}",
        "size": f"{rng.uniform(0.1, 900):.1f}",
    }
    return tpl.format(**vals)


def typo(rng: random.Random, text: str) -> str:
    chars = list(text)
    for _ in range(rng.randint(1, 2)):
        if len(chars) < 8:
            break
        i = rng.randrange(1, len(chars) - 2)
        op = rng.random()
        if op < 0.4:                     # 인접 자리 바꿈
            chars[i], chars[i + 1] = chars[i + 1], chars[i]
        elif op < 0.7:                   # 삭제
            del chars[i]
        else:                            # 중복 삽입
            chars.insert(i, chars[i])
    return "".join(chars)


def read_fleurs(lang: str, n: int, rng: random.Random):
    path = os.path.join(FLEURS, f"{lang}_test.tsv")
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 4 and parts[3].strip():
                rows.append(parts[3].strip())
    rng.shuffle(rows)
    return rows[:n]


def main():
    rng = random.Random(20261102)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out = []

    for lang in LANGS:
        for i, text in enumerate(read_fleurs(lang, PER_LANG, rng)):
            out.append({"id": f"fleurs-{lang}-{i:03d}", "lang": lang, "kind": "fleurs", "text": text})

    for i in range(200):
        out.append({"id": f"syn-ko-{i:03d}", "lang": "ko_kr", "kind": "synthetic", "text": synth(rng, "ko", i)})
    for i in range(100):
        out.append({"id": f"syn-en-{i:03d}", "lang": "en_us", "kind": "synthetic", "text": synth(rng, "en", i)})

    bases = [r for r in out if r["kind"] == "fleurs" and r["lang"] in ("ko_kr", "en_us")]
    rng.shuffle(bases)
    for i, base in enumerate(bases[:100]):
        out.append({"id": f"typo-ko-{i:03d}", "lang": "ko_kr", "kind": "typo",
                    "text": typo(rng, base["text"]), "base_id": base["id"]})
    en_bases = [r for r in bases if r["lang"] == "en_us"]
    for i, base in enumerate(en_bases[:50]):
        out.append({"id": f"typo-en-{i:03d}", "lang": "en_us", "kind": "typo",
                    "text": typo(rng, base["text"]), "base_id": base["id"]})

    with open(OUT, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    from collections import Counter
    print("total", len(out), Counter((r["kind"], r["lang"]) for r in out).most_common(8))
    print("avg chars", sum(len(r["text"]) for r in out) / len(out))


if __name__ == "__main__":
    main()
