"""D-084 rev3 / 084a: URL-only verifier.

This module is deliberately separate from eval/slot_verify.py (v1).
It implements only the 084a measurement baseline:

- ASCII URL spans with Hangul-particle and delimiter boundaries
- source-side deterministic URL soft-wrap candidates
- summary-side joins only when the joined URL matches a source URL
- strict URL canonicalization (scheme/host lowercase; path/query preserved)
- no time/unit/alias equivalence

It must not be used for 084b diagnostics or selection unless the caller
checks verifier_version/spec_hash.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from eval.slot_verify import Slot, _canonical, _normalize, _unique, extract_slots

VERIFIER_VERSION = "084a/1.0.0"
SPEC_HASH = "d084a-rev3-2026-11-07"

# ASCII URL grammar; Hangul and whitespace terminate a URL span.
URL_CHARS = r"A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%"
_URL_RE = re.compile(rf"https?://[{URL_CHARS}]+", re.IGNORECASE)
_WRAP_RE = re.compile(
    rf"(https?://[{URL_CHARS}]*?[./_-])[ \t]*\r?\n[ \t]*"
    rf"([A-Za-z0-9][{URL_CHARS}]*)"
)


@dataclass(frozen=True)
class UrlSpan:
    raw: str
    canonical: str
    start: int
    end: int


@dataclass(frozen=True)
class UrlRepair:
    original: str
    joined: str
    start: int
    end: int
    reason: str


@dataclass(frozen=True)
class Unresolved:
    text: str
    reason: str
    start: int
    end: int


@dataclass(frozen=True)
class Report084A:
    verifier_version: str
    spec_hash: str
    source_urls: tuple[UrlSpan, ...]
    summary_urls: tuple[UrlSpan, ...]
    url_repairs: tuple[UrlRepair, ...]
    unresolved: tuple[Unresolved, ...]
    source_slots: tuple[Slot, ...]
    summary_slots: tuple[Slot, ...]
    new: tuple[str, ...]
    missing: tuple[str, ...]
    grounded: bool
    slot_free: bool
    slot_preservation: float
    new_slot_rate: float

    def to_dict(self) -> dict:
        return {
            "verifier_version": self.verifier_version,
            "spec_hash": self.spec_hash,
            "source_urls": [u.__dict__ for u in self.source_urls],
            "summary_urls": [u.__dict__ for u in self.summary_urls],
            "url_repairs": [r.__dict__ for r in self.url_repairs],
            "unresolved": [u.__dict__ for u in self.unresolved],
            "source_slots": [s.to_dict() for s in self.source_slots],
            "summary_slots": [s.to_dict() for s in self.summary_slots],
            "new": list(self.new),
            "missing": list(self.missing),
            "grounded": self.grounded,
            "slot_free": self.slot_free,
            "slot_preservation": self.slot_preservation,
            "new_slot_rate": self.new_slot_rate,
        }


def _canonical_url(raw: str) -> str:
    """Strict-enough URL identity for 084a.

    Scheme and host are case-insensitive. Path/query/fragment case, comma,
    escape and trailing slash are preserved. Percent-escape hex case is
    normalized only for comparison; no decoding is performed.
    """
    m = re.match(r"(?i)^(https?)://([^/?#]+)(.*)$", raw, re.S)
    if not m:
        return raw
    scheme = m.group(1).lower()
    host = m.group(2).lower()
    rest = m.group(3)
    rest = re.sub(r"%[0-9A-Fa-f]{2}", lambda x: x.group(0).upper(), rest)
    return f"{scheme}://{host}{rest}"


def _trim_closing_delimiters(raw: str) -> tuple[str, bool]:
    """Remove unmatched closing quotes/brackets; keep ambiguous punctuation."""
    ambiguous = False
    while raw:
        ch = raw[-1]
        if ch in ")]}":
            opener = {")": "(", "]": "[", "}": "{"}[ch]
            if raw.count(ch) > raw.count(opener):
                raw = raw[:-1]
                continue
        if ch in ".,;:!?":
            # A terminal punctuation lookalike is ambiguous. Leave it in
            # the span and let the caller record "unresolved"; do not guess.
            ambiguous = True
        break
    return raw, ambiguous


def _url_spans(text: str) -> tuple[list[UrlSpan], list[Unresolved]]:
    spans: list[UrlSpan] = []
    unresolved: list[Unresolved] = []
    for m in _URL_RE.finditer(text):
        raw, ambiguous = _trim_closing_delimiters(m.group(0))
        start, end = m.start(), m.start() + len(raw)
        if not raw or len(raw) <= len("https://"):
            continue
        if ambiguous:
            unresolved.append(Unresolved(raw, "terminal_punctuation", start, end))
            continue
        spans.append(UrlSpan(raw, _canonical_url(raw), start, end))
    return spans, unresolved


def _join_wraps(
    text: str,
    *,
    source_urls: set[str] | None = None,
    allow_unattested_source: bool = True,
) -> tuple[str, list[UrlRepair], list[Unresolved]]:
    """Join URL soft wraps.

    Source side (source_urls is None): deterministic grammar candidate.
    Summary side (source_urls is a set): only join when the joined URL is
    already a resolved source URL; otherwise record unresolved.
    """
    repairs: list[UrlRepair] = []
    unresolved: list[Unresolved] = []
    out: list[str] = []
    pos = 0
    for m in _WRAP_RE.finditer(text):
        out.append(text[pos:m.start()])
        original = m.group(0)
        joined_raw = m.group(1) + m.group(2)
        joined, _ = _trim_closing_delimiters(joined_raw)
        canonical = _canonical_url(joined)
        host = canonical.split("://", 1)[-1].split("/", 1)[0]
        # A bare, incomplete host such as fine.fss. is intentionally
        # unresolved rather than guessed into a suffix.
        pre_host = _canonical_url(m.group(1)).split("://", 1)[-1].split("/", 1)[0].rstrip(".")
        if host.endswith(".fss") or pre_host.endswith(".fss"):
            unresolved.append(Unresolved(original, "ambiguous_host_wrap", m.start(), m.end()))
            out.append(original)
        elif source_urls is not None and canonical not in source_urls:
            unresolved.append(Unresolved(original, "summary_wrap_not_in_source", m.start(), m.end()))
            out.append(original)
        else:
            out.append(joined)
            repairs.append(UrlRepair(original, joined, m.start(), m.end(), "source_wrap" if source_urls is None else "summary_source_match"))
        pos = m.end()
    out.append(text[pos:])
    return "".join(out), repairs, unresolved


def _mask_urls(text: str, spans: Iterable[UrlSpan]) -> str:
    chars = list(text)
    for s in spans:
        for i in range(max(0, s.start), min(len(chars), s.end)):
            chars[i] = " "
    return "".join(chars)


def _slots_with_urls(text: str, urls: list[UrlSpan]) -> list[Slot]:
    """v1 non-URL slots on masked text + explicit 084a URL slots."""
    masked = _mask_urls(text, urls)
    non_url = extract_slots(masked)
    url_slots = [
        Slot("url", u.raw, u.canonical, u.start, u.end)
        for u in urls
    ]
    # Keep v1's deterministic order; URL spans replace their masked regions.
    return sorted([*non_url, *url_slots], key=lambda s: (s.start, s.end))


def verify_084a(source: str, summary: str) -> Report084A:
    # Source side: deterministic wrap candidates.
    src_text, src_repairs, src_unresolved = _join_wraps(source, allow_unattested_source=True)
    src_urls, src_url_unresolved = _url_spans(src_text)
    src_unresolved.extend(src_url_unresolved)
    src_canon = {u.canonical for u in src_urls}

    # Summary side: only source-attested joins.
    sm_text, sm_repairs, sm_unresolved = _join_wraps(
        summary, source_urls=src_canon, allow_unattested_source=False
    )
    sm_urls, sm_url_unresolved = _url_spans(sm_text)
    sm_unresolved.extend(sm_url_unresolved)

    src_slots = _unique(_slots_with_urls(src_text, src_urls))
    sm_slots = _unique(_slots_with_urls(sm_text, sm_urls))
    src_map = {s.canonical: s for s in src_slots}
    sm_map = {s.canonical: s for s in sm_slots}
    preserved = tuple(s.canonical for s in src_slots if s.canonical in sm_map)
    missing = tuple(s.canonical for s in src_slots if s.canonical not in sm_map)
    new = tuple(s.canonical for s in sm_slots if s.canonical not in src_map)
    source_count = len(src_slots)
    summary_count = len(sm_slots)
    unresolved = tuple(src_unresolved + sm_unresolved)
    # Source-side unresolved URL is a missing/measurement caveat; it does not
    # create a new slot. Summary-side unresolved URL is material and blocks a
    # silent grounded pass. Missing slots remain separate from `grounded`.
    grounded = not new and not sm_unresolved
    return Report084A(
        verifier_version=VERIFIER_VERSION,
        spec_hash=SPEC_HASH,
        source_urls=tuple(src_urls),
        summary_urls=tuple(sm_urls),
        url_repairs=tuple(src_repairs + sm_repairs),
        unresolved=unresolved,
        source_slots=tuple(src_slots),
        summary_slots=tuple(sm_slots),
        new=new,
        missing=missing,
        grounded=grounded,
        slot_free=summary_count == 0,
        slot_preservation=(len(preserved) / source_count) if source_count else 1.0,
        new_slot_rate=(len(new) / summary_count) if summary_count else 0.0,
    )
