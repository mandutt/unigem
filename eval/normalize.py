"""CER/WER 정규화 단일 구현 (Addendum D E-1).

C-8에서 사용한 규칙을 코드 상수 한 곳에 고정한다.
- 소문자화
- 한글 음절/영숫자/공백 외 문자 제거 (구두점은 공백으로 대체하지 않고 삭제)
- 연속 공백 축약
- 공백 무시 CER은 비교 직전에 공백만 제거

이 모듈은 외부 패키지에 의존하지 않는다.
"""
from __future__ import annotations

import re
import unicodedata

_WORD_KEEP = re.compile(r"[^\w\s가-힣]", re.UNICODE)
_SPACE = re.compile(r"\s+", re.UNICODE)


def normalize(text: str) -> str:
    """C-8 통일 정규화. 공백은 보존한다."""
    text = unicodedata.normalize("NFC", text)
    text = text.lower()
    text = _WORD_KEEP.sub("", text)
    return _SPACE.sub(" ", text).strip()


def normalize_nospace(text: str) -> str:
    return _SPACE.sub("", normalize(text))


def _edit_distance(ref: str, hyp: str) -> int:
    if len(ref) < len(hyp):
        ref, hyp = hyp, ref
    prev = list(range(len(hyp) + 1))
    for i, rc in enumerate(ref, 1):
        cur = [i]
        for j, hc in enumerate(hyp, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (rc != hc)))
        prev = cur
    return prev[-1]


def cer_prepared(ref: str, hyp: str, ignore_space: bool = False) -> float:
    """이미 정규화된 문자열의 CER. (정규화를 다시 적용하지 않는다.)"""
    if ignore_space:
        ref, hyp = _SPACE.sub("", ref), _SPACE.sub("", hyp)
    if not ref:
        return 0.0 if not hyp else 1.0
    return _edit_distance(ref, hyp) / len(ref)


def cer(ref: str, hyp: str, ignore_space: bool = False) -> float:
    if ignore_space:
        ref, hyp = normalize_nospace(ref), normalize_nospace(hyp)
    else:
        ref, hyp = normalize(ref), normalize(hyp)
    return cer_prepared(ref, hyp, ignore_space=False)


def wer(ref: str, hyp: str) -> float:
    r, h = normalize(ref).split(), normalize(hyp).split()
    if not r:
        return 0.0 if not h else 1.0
    # word-level Levenshtein
    prev = list(range(len(h) + 1))
    for i, rw in enumerate(r, 1):
        cur = [i]
        for j, hw in enumerate(h, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (rw != hw)))
        prev = cur
    return prev[-1] / len(r)


def corpus_cer(pairs, ignore_space: bool = False) -> float:
    """pairs: iterable of (ref, hyp). 문자 단위 누적 CER."""
    import sys

    edits = total = 0
    for ref, hyp in pairs:
        r = normalize_nospace(ref) if ignore_space else normalize(ref)
        h = normalize_nospace(hyp) if ignore_space else normalize(hyp)
        edits += _edit_distance(r, h)
        total += len(r)
    return edits / total if total else 0.0


if __name__ == "__main__":
    print("normalize:", normalize("예를 들어, 15미터이며 2011년 8월입니다!"))
    print("cer:", cer("예를 들어 15미터", "예를들어 15 미터", ignore_space=True))
