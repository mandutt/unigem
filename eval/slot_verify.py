"""Slot extraction and summary verification for F5.

The verifier is intentionally conservative: a summary is rejected when it
drops a source slot or introduces a slot that is not present in the source.
It is a safety gate, not a summary-quality metric.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class Slot:
    kind: str
    value: str
    canonical: str
    start: int
    end: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SlotReport:
    source_slots: tuple[Slot, ...]
    summary_slots: tuple[Slot, ...]
    preserved: tuple[str, ...]
    missing: tuple[str, ...]
    new: tuple[str, ...]
    rejected: bool
    source_count: int
    summary_count: int
    slot_preservation: float
    new_slot_rate: float

    def to_dict(self) -> dict:
        return {
            "source_slots": [s.to_dict() for s in self.source_slots],
            "summary_slots": [s.to_dict() for s in self.summary_slots],
            "preserved": list(self.preserved),
            "missing": list(self.missing),
            "new": list(self.new),
            "rejected": self.rejected,
            "source_count": self.source_count,
            "summary_count": self.summary_count,
            "slot_preservation": self.slot_preservation,
            "new_slot_rate": self.new_slot_rate,
        }


# Order matters: earlier patterns consume their spans and later patterns
# skip overlaps. URLs/paths must precede generic numbers; dates precede
# versions and plain numbers.
_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("url", re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)),
    ("path", re.compile(r"(?<![\w])(?:[A-Za-z]:\\|/)[^\s<>\"']+")),
    (
        "date",
        re.compile(
            r"(?<!\d)(?:(?:19|20)\d{2}\s*[-./년]\s*\d{1,2}\s*[-./월]\s*\d{1,2}\s*일?"
            r"|\d{1,2}\s*월\s*\d{1,2}\s*일)"
        ),
    ),
    (
        "time",
        re.compile(
            r"(?<!\d)(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?(?!\d)"
            r"|(?<![가-힣])(?:오전|오후)?\s*\d{1,2}\s*시(?:\s*\d{1,2}\s*분)?"
        ),
    ),
    ("version", re.compile(r"(?<![A-Za-z0-9])v?\d+(?:\.\d+){2,3}(?![A-Za-z0-9])", re.IGNORECASE)),
    (
        "identifier",
        re.compile(
            r"(?<![A-Za-z0-9])[A-Za-z][A-Za-z0-9]*(?:[._-][A-Za-z0-9]+)+(?![A-Za-z0-9])"
            r"|(?<![A-Za-z0-9])[A-Za-z]+[0-9][A-Za-z0-9]*(?![A-Za-z0-9])"
        ),
    ),
    (
        "number",
        re.compile(
            r"(?<![A-Za-z0-9])\d[\d,]*(?:\.\d+)?\s*"
            r"(?:(?:조|억|만|천|백|십)+\s*)?"
            r"(?:원|달러|유로|엔|위안|%|명|개|건|년|월|일|시간|분|초|"
            r"GB|MB|TB|KB|km|위|등)?"
        ),
    ),
)


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def _canonical(kind: str, value: str) -> str:
    s = _normalize(value).strip().lower()
    s = re.sub(r"\s+", "", s)
    s = s.replace(",", "")
    s = s.strip(".,;:!?()[]{}<>\"'")
    if kind == "date":
        s = re.sub(r"[년월일./]", "-", s)
        s = re.sub(r"-+", "-", s).strip("-")
        m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
        if m:
            s = f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return s


def extract_slots(text: str) -> list[Slot]:
    """Extract typed slots from text.

    Longest/priority patterns win; overlapping lower-priority matches are
    discarded. Positions refer to the NFKC-normalized text.
    """
    norm = _normalize(text)
    occupied: list[tuple[int, int]] = []
    found: list[Slot] = []
    for kind, pattern in _PATTERNS:
        for match in pattern.finditer(norm):
            start, end = match.span()
            if end <= start:
                continue
            if any(start < e and end > s for s, e in occupied):
                continue
            value = match.group(0).strip()
            if not value:
                continue
            # Keep URL/path punctuation meaningful; trim sentence punctuation
            # only for the non-URL/path kinds.
            if kind not in {"url", "path"}:
                value = value.rstrip(".,;:!?")
                end = start + len(value)
            if not value:
                continue
            occupied.append((start, end))
            found.append(
                Slot(
                    kind=kind,
                    value=value,
                    canonical=_canonical(kind, value),
                    start=start,
                    end=end,
                )
            )
    found.sort(key=lambda s: (s.start, s.end))
    return found


def _unique(slots: Iterable[Slot]) -> list[Slot]:
    seen: set[str] = set()
    out: list[Slot] = []
    for slot in slots:
        if slot.canonical in seen:
            continue
        seen.add(slot.canonical)
        out.append(slot)
    return out


def verify_summary(source: str, summary: str) -> SlotReport:
    """Verify that summary preserves every source slot and invents none."""
    src = _unique(extract_slots(source))
    sm = _unique(extract_slots(summary))
    src_map = {s.canonical: s for s in src}
    sm_map = {s.canonical: s for s in sm}
    preserved = tuple(s.canonical for s in src if s.canonical in sm_map)
    missing = tuple(s.canonical for s in src if s.canonical not in sm_map)
    new = tuple(s.canonical for s in sm if s.canonical not in src_map)
    source_count = len(src)
    summary_count = len(sm)
    slot_preservation = len(preserved) / source_count if source_count else 1.0
    new_slot_rate = len(new) / summary_count if summary_count else 0.0
    return SlotReport(
        source_slots=tuple(src),
        summary_slots=tuple(sm),
        preserved=preserved,
        missing=missing,
        new=new,
        rejected=bool(missing or new),
        source_count=source_count,
        summary_count=summary_count,
        slot_preservation=slot_preservation,
        new_slot_rate=new_slot_rate,
    )
