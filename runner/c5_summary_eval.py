"""F5 memory-summary audit and A0 extractive baseline.

Outputs are P0-only: F5 passages, target summaries, A0 drafts, and slot
metrics. No memory-store (P1) content is read.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import html
import json
import math
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval.slot_verify import extract_slots, verify_summary  # noqa: E402

DEFAULT_INPUT = ROOT / "data/external/f5_pairs_v3.jsonl"
DEFAULT_OUT = ROOT / "reports/provenance/C5"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def split_records(records: list[dict], seed: int = 42) -> dict:
    ids = [str(r["id"]) for r in records]
    shuffled = ids[:]
    random.Random(seed).shuffle(shuffled)
    n = len(shuffled)
    n_train = int(n * 0.8)
    n_val = int(n * 0.1)
    train = shuffled[:n_train]
    val = shuffled[n_train : n_train + n_val]
    test = shuffled[n_train + n_val :]
    return {
        "seed": seed,
        "sizes": {"train": len(train), "val": len(val), "test": len(test)},
        "train": train,
        "val": val,
        "test": test,
        "sha256": hashlib.sha256(("\n".join(shuffled)).encode()).hexdigest(),
    }


def audit_targets(records: list[dict], max_examples: int = 20) -> dict:
    totals = {
        "records": len(records),
        "source_slots": 0,
        "summary_slots": 0,
        "preserved": 0,
        "missing": 0,
        "new": 0,
        "records_with_missing": 0,
        "records_with_new": 0,
    }
    by_kind: dict[str, dict[str, int]] = collections.defaultdict(
        lambda: {"source": 0, "summary": 0, "missing": 0, "new": 0}
    )
    examples = {"missing": [], "new": []}
    for rec in records:
        rep = verify_summary(str(rec["passage"]), str(rec["summary"]))
        totals["source_slots"] += rep.source_count
        totals["summary_slots"] += rep.summary_count
        totals["preserved"] += len(rep.preserved)
        totals["missing"] += len(rep.missing)
        totals["new"] += len(rep.new)
        totals["records_with_missing"] += int(bool(rep.missing))
        totals["records_with_new"] += int(bool(rep.new))
        for s in rep.source_slots:
            by_kind[s.kind]["source"] += 1
        for s in rep.summary_slots:
            by_kind[s.kind]["summary"] += 1
        src_kind = {s.canonical: s.kind for s in rep.source_slots}
        sum_kind = {s.canonical: s.kind for s in rep.summary_slots}
        for canonical in rep.missing:
            by_kind[src_kind[canonical]]["missing"] += 1
        for canonical in rep.new:
            by_kind[sum_kind[canonical]]["new"] += 1
        for key, field in (("missing", "missing"), ("new", "new")):
            for canonical in getattr(rep, field):
                if len(examples[key]) >= max_examples:
                    break
                examples[key].append({"id": rec["id"], "slot": canonical})
    n_src = totals["source_slots"]
    n_sum = totals["summary_slots"]
    totals["slot_preservation"] = totals["preserved"] / n_src if n_src else 1.0
    totals["new_slot_rate"] = totals["new"] / n_sum if n_sum else 0.0
    totals["grounding_rate"] = 1.0 - totals["new_slot_rate"]
    return {
        "totals": totals,
        "by_kind": dict(sorted(by_kind.items())),
        "examples": examples,
    }


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?。！？])\s+|\n+", text)
    out = []
    for part in parts:
        part = part.strip()
        if len(part) < 8:
            continue
        # A very long run-on sentence is still one sentence; keep it.
        out.append(part)
    return out or [text]


def content_tokens(text: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[가-힣]{2,}|[A-Za-z][A-Za-z0-9_.-]*|\d[\d,.]*", text)]


def a0_summary(passage: str, max_sentences: int = 4, max_chars: int = 500) -> str:
    """Slot-aware extractive baseline, no model and no decoder."""
    sents = split_sentences(passage)
    if not sents:
        return ""
    freq = collections.Counter(content_tokens(passage))
    scores: list[float] = []
    slots_by_sent: list[set[str]] = []
    for i, sent in enumerate(sents):
        toks = content_tokens(sent)
        base = sum(freq[t] for t in toks) / math.sqrt(max(1, len(toks)))
        base += 0.3 if i == 0 else 0.0
        scores.append(base)
        slots_by_sent.append({s.canonical for s in extract_slots(sent)})
    selected: list[int] = []
    covered: set[str] = set()
    total_chars = 0
    remaining = set(range(len(sents)))
    while remaining and len(selected) < max_sentences:
        def rank(i: int) -> float:
            new_slots = len(slots_by_sent[i] - covered)
            # Prioritize slot coverage; then content score; then brevity.
            return new_slots * 100.0 + scores[i] - 0.01 * len(sents[i])
        best = max(remaining, key=rank)
        add = len(sents[best]) + (1 if selected else 0)
        if selected and total_chars + add > max_chars:
            break
        selected.append(best)
        remaining.remove(best)
        covered |= slots_by_sent[best]
        total_chars += add
    return " ".join(sents[i] for i in sorted(selected))


def char_f1(pred: str, ref: str) -> float:
    def bag(s: str) -> collections.Counter:
        return collections.Counter(re.sub(r"\s+", "", s))

    a, b = bag(pred), bag(ref)
    common = sum((a & b).values())
    p = common / sum(a.values()) if a else 0.0
    r = common / sum(b.values()) if b else 0.0
    return 2 * p * r / (p + r) if p + r else 0.0


def evaluate_a0(records: list[dict], test_ids: list[str]) -> tuple[dict, list[dict]]:
    by_id = {str(r["id"]): r for r in records}
    rows = []
    for rid in test_ids:
        rec = by_id[rid]
        pred = a0_summary(str(rec["passage"]))
        rep = verify_summary(str(rec["passage"]), pred)
        rows.append(
            {
                "id": rid,
                "pred": pred,
                "target": str(rec["summary"]),
                "source_count": rep.source_count,
                "summary_count": rep.summary_count,
                "slot_preservation": rep.slot_preservation,
                "new_slot_rate": rep.new_slot_rate,
                "rejected": rep.rejected,
                "rejected_strict": rep.rejected,
                "rejected_grounding": bool(rep.new),
                "missing": list(rep.missing),
                "new": list(rep.new),
                "compression": len(re.sub(r"\s+", "", pred)) / max(1, len(re.sub(r"\s+", "", str(rec["passage"])))),
                "char_f1": char_f1(pred, str(rec["summary"])),
            }
        )
    n = len(rows)
    metrics = {
        "n": n,
        "records_rejected": sum(int(r["rejected"]) for r in rows),
        "rejected_rate": sum(int(r["rejected"]) for r in rows) / n if n else 0.0,
        "records_rejected_grounding": sum(int(r["rejected_grounding"]) for r in rows),
        "rejected_grounding_rate": sum(int(r["rejected_grounding"]) for r in rows) / n if n else 0.0,
        "slot_preservation_mean": sum(r["slot_preservation"] for r in rows) / n if n else 0.0,
        "new_slot_rate_mean": sum(r["new_slot_rate"] for r in rows) / n if n else 0.0,
        "compression_mean": sum(r["compression"] for r in rows) / n if n else 0.0,
        "char_f1_mean": sum(r["char_f1"] for r in rows) / n if n else 0.0,
    }
    return metrics, rows


def write_review_html(rows: list[dict], records: list[dict], path: Path, limit: int = 50) -> None:
    by_id = {str(r["id"]): r for r in records}
    parts = [
        "<!doctype html><html lang='ko'><meta charset='utf-8'>",
        "<title>F5 A0 요약 검토</title>",
        "<style>body{font-family:system-ui,sans-serif;max-width:1200px;margin:2rem auto;line-height:1.5}"
        "table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccc;padding:.5rem;vertical-align:top}"
        "th{background:#eee}small{color:#555}</style>",
        "<h1>F5 A0 추출형 요약 — 사람 검토 50건</h1>",
        "<p>각 행의 A0 요약이 원문의 핵심 사실을 보존하는지, 슬롯 누락/신규가 있는지 확인한다. "
        "A0는 추출형 baseline이며 최종 요약기가 아니다.</p>",
        "<table><thead><tr><th>#</th><th>ID</th><th>원문(발췌)</th><th>LLM target</th><th>A0</th><th>슬롯</th></tr></thead><tbody>",
    ]
    for i, row in enumerate(rows[:limit], 1):
        passage = str(by_id[row["id"]]["passage"])
        parts.append("<tr>")
        parts.append(f"<td>{i}</td><td><code>{html.escape(row['id'])}</code></td>")
        parts.append(f"<td><small>{html.escape(passage[:700])}</small></td>")
        parts.append(f"<td><small>{html.escape(row['target'][:700])}</small></td>")
        parts.append(f"<td><small>{html.escape(row['pred'][:700])}</small></td>")
        slot = (
            f"preserve={row['slot_preservation']:.3f}<br>new={row['new_slot_rate']:.3f}<br>"
            f"reject_strict={row['rejected_strict']}<br>reject_grounding={row['rejected_grounding']}<br>"
            f"char_f1={row['char_f1']:.3f}"
        )
        if row["missing"]:
            slot += "<br>missing: " + html.escape(", ".join(row["missing"][:8]))
        if row["new"]:
            slot += "<br>new: " + html.escape(", ".join(row["new"][:8]))
        parts.append(f"<td><small>{slot}</small></td></tr>")
    parts.append("</tbody></table></html>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(parts), encoding="utf-8")


def write_report(path: Path, audit: dict, split: dict, a0: dict, input_path: Path) -> None:
    t = audit["totals"]
    lines = [
        "# C5 — F5 메모리 요약: target 감사 + A0 추출형 baseline",
        "",
        "- 작성: 2026-11-06",
        "- 상태: **A0·슬롯 검증기 1차 완료, 사람 검토 대기**",
        "- 데이터: `" + input_path.resolve().relative_to(ROOT).as_posix() + "`",
        "- 범위: P0 F5 데이터만 사용. JEV/메모리 코어 미수정.",
        "",
        f"## 1. Target 슬롯 감사 ({t['records']:,}쌍)",
        "",
        "| 항목 | 값 |",
        "|---|---:|",
        f"| 레코드 | {t['records']:,} |",
        f"| 원문 슬롯 | {t['source_slots']:,} |",
        f"| 요약 슬롯 | {t['summary_slots']:,} |",
        f"| 보존 | {t['preserved']:,} |",
        f"| 누락 | {t['missing']:,} |",
        f"| 신규 | {t['new']:,} |",
        f"| 슬롯 보존율(원문 대비) | **{t['slot_preservation']:.4%}** |",
        f"| 신규 슬롯률 | **{t['new_slot_rate']:.4%}** |",
        f"| grounding rate (요약 슬롯 중 원문 존재) | **{t['grounding_rate']:.4%}** |",
        f"| 누락 레코드 | {t['records_with_missing']:,} |",
        f"| 신규 레코드 | {t['records_with_new']:,} |",
        "",
        "**G-C5 기준:** 슬롯 보존율 ≥99%, 신규 슬롯률 ≤1%.",
        "",
        "> **교정 발견:** 위 두 지표는 같은 분모가 아니다. `슬롯 보존율`은 원문 슬롯 대비 요약에 남은 비율(정보 손실), "
        "`grounding rate`는 요약에 등장한 슬롯이 원문에 있는 비율(환각)이다. F5 news target은 요약 과정에서 "
        "원문 숫자를 의도적으로 생략하므로 **원문 대비 99% 보존은 현실적으로 불가능**하다. "
        "G-C5의 '보존'을 grounding으로 해석할지, 중요 슬롯만 엄격히 요구할지 **사용자 결정이 필요**하다. "
        "이 보고서는 두 값을 모두 제공하며, 게이트 임계값을 임의로 바꾸지 않는다.",
        "",
        "### 유형별",
        "",
        "| kind | 원문 | 요약 | 누락 | 신규 |",
        "|---|---:|---:|---:|---:|",
    ]
    for kind, d in audit["by_kind"].items():
        lines.append(f"| {kind} | {d['source']:,} | {d['summary']:,} | {d['missing']:,} | {d['new']:,} |")
    lines += [
        "",
        "## 2. Split",
        "",
        "| split | n |",
        "|---|---:|",
        f"| train | {split['sizes']['train']:,} |",
        f"| val | {split['sizes']['val']:,} |",
        f"| test | {split['sizes']['test']:,} |",
        "",
        f"seed={split['seed']}, id-sha256=`{split['sha256'][:16]}…`",
        "",
        "## 3. A0 추출형 baseline (test 200)",
        "",
        "| 항목 | 값 |",
        "|---|---:|",
        f"| n | {a0['n']} |",
        f"| strict reject (누락 또는 신규) | {a0['records_rejected']} ({a0['rejected_rate']:.2%}) |",
        f"| grounding reject (신규만) | {a0['records_rejected_grounding']} ({a0['rejected_grounding_rate']:.2%}) |",
        f"| 슬롯 보존율 평균(원문 대비) | {a0['slot_preservation_mean']:.4f} |",
        f"| 신규 슬롯률 평균 | {a0['new_slot_rate_mean']:.4f} |",
        f"| 압축률 평균 | {a0['compression_mean']:.4f} |",
        f"| char F1 평균(target 대비) | {a0['char_f1_mean']:.4f} |",
        "",
        "**해석:** A0는 디코더 없는 추출형 baseline이다. 원문 대비 보존율이 낮아도 추출형 특성상 "
        "원문 문장을 그대로 쓰므로 **신규 슬롯(환각)은 거의 0**이다. strict reject는 모든 원문 숫자를 "
        "보존하라는 뜻이므로 요약 압축과 충돌한다. G-C5 판정은 별도 결정이 필요하다. "
        "char F1은 참고용이며 ROUGE 단독 판정이 아니다.",
        "",
        "## 4. 산출물",
        "",
        "- `reports/provenance/C5/target_slot_audit.json`",
        "- `reports/provenance/C5/splits.json`",
        "- `reports/provenance/C5/a0_eval.json`",
        "- `reports/provenance/C5/a0_test_predictions.jsonl`",
        "- `reports/C5_summary_review.html`",
        "",
        "## 5. 다음",
        "",
        "1. 사람 표본 50건 검토(`C5_summary_review.html`).",
        "2. target 자체의 신규 슬롯률이 1%를 넘으면 **target repair/filter 정책**을 먼저 결정.",
        "3. A0 결과와 사람 검토를 보고 CP3-1에서 A0 채택/보류 결정.",
        "4. 디코더는 C3 A1(T5Gemma 2 LoRA)을 **별도 승인 후** 비교.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--report", type=Path, default=ROOT / "reports/C5_summary.md")
    ap.add_argument("--review", type=Path, default=ROOT / "reports/C5_summary_review.html")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    records = read_jsonl(args.input)
    if len(records) < 50:
        raise SystemExit(f"too few F5 records: {len(records)}")
    ids = [str(r["id"]) for r in records]
    if len(set(ids)) != len(ids):
        raise SystemExit("duplicate ids")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    split = split_records(records, seed=args.seed)
    audit = audit_targets(records)
    a0, pred_rows = evaluate_a0(records, split["test"])
    write_json(args.out_dir / "target_slot_audit.json", audit)
    write_json(args.out_dir / "splits.json", split)
    write_json(args.out_dir / "a0_eval.json", a0)
    write_jsonl(args.out_dir / "a0_test_predictions.jsonl", pred_rows)
    write_review_html(pred_rows, records, args.review)
    write_report(args.report, audit, split, a0, args.input)
    print(json.dumps({"audit": audit["totals"], "a0": a0, "split": split["sizes"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
