"""CP-D2-lite: decompose the sealed Kspon eval_other CER without new model runs.

Uses only the already-produced decode JSON and manifest metadata.
No test-set retuning, no additional checkpoint evaluation.
"""
from __future__ import annotations

import json
import math
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "reports/W2A_lite_cp_d2_lite.json"
OUT_MD = ROOT / "reports/W2A_lite_cp_d2_lite.md"

DUR_BINS = [(0, 2), (2, 4), (4, 6), (6, 8), (8, 10), (10, 12), (12, 16), (16, 99)]
LEN_BINS = [(0, 10), (10, 20), (20, 30), (30, 40), (40, 60), (60, 999)]
NOISE_RE = re.compile(r"([A-Za-z]{1,2})/")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def boot_ci(rows: list[dict], n: int = 2000, seed: int = 42) -> list[float] | None:
    if not rows:
        return None
    rng = random.Random(seed)
    vals = []
    for _ in range(n):
        e = c = 0
        for _ in range(len(rows)):
            r = rows[rng.randrange(len(rows))]
            e += r["err"]
            c += r["ref_chars"]
        if c:
            vals.append(e / c)
    vals.sort()
    if not vals:
        return None
    return [round(vals[int(0.025 * len(vals))], 6), round(vals[int(0.975 * len(vals)) - 1], 6)]


def summary(rows: list[dict], label: str) -> dict:
    e = sum(r["err"] for r in rows)
    c = sum(r["ref_chars"] for r in rows)
    return {
        "label": label,
        "n": len(rows),
        "errors": e,
        "ref_chars": c,
        "cer": round(e / c, 6) if c else None,
        "cer_ci95": boot_ci(rows),
        "mean_utt_cer": round(sum(r["cer"] for r in rows) / len(rows), 6) if rows else None,
        "blank": sum(1 for r in rows if not r.get("pred_norm")),
    }


def group_by(rows: list[dict], key, bins) -> list[dict]:
    out = []
    for lo, hi in bins:
        g = [r for r in rows if lo <= r[key] < hi]
        if not g:
            continue
        s = summary(g, f"{lo}-{hi}" if hi < 99 else f">={lo}")
        s["lo"] = lo
        s["hi"] = hi
        out.append(s)
    return out


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3:
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    dx = sum((x - mx) ** 2 for x in xs)
    dy = sum((y - my) ** 2 for y in ys)
    if dx <= 0 or dy <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(dx * dy)


def build(manifest_path: Path, decode_path: Path, label: str) -> dict:
    manifest = {r["id"]: r for r in load_jsonl(manifest_path)}
    dec = json.loads(decode_path.read_text(encoding="utf-8"))
    rows = []
    missing = []
    skipped = []
    for s in dec["sentences"]:
        m = manifest.get(s["id"])
        if m is None:
            missing.append(s["id"])
            continue
        row = dict(s)
        row["dur"] = float(m.get("dur") or 0.0)
        row["ref_raw"] = m.get("ref_raw", m.get("ref", ""))
        row["ref_len"] = len(s.get("ref_norm", ""))
        markers = sorted(set(NOISE_RE.findall(row["ref_raw"])))
        row["noise_markers"] = markers
        row["noisy"] = bool(markers)
        rows.append(row)
    for mid, m in manifest.items():
        if mid not in {s["id"] for s in dec["sentences"]}:
            skipped.append({"id": mid, "dur": m.get("dur"), "reason": "decode_missing_or_gt_16s"})

    noisy = [r for r in rows if r["noisy"]]
    clean = [r for r in rows if not r["noisy"]]
    marker_counts: dict[str, int] = {}
    for r in rows:
        for m in r["noise_markers"]:
            marker_counts[m] = marker_counts.get(m, 0) + 1

    total_err = sum(r["err"] for r in rows)
    by_err = sorted(rows, key=lambda r: r["err"], reverse=True)
    concentration = {}
    for pct in (1, 5, 10):
        k = max(1, round(len(rows) * pct / 100))
        top = by_err[:k]
        concentration[f"top_{pct}pct"] = {
            "k": k,
            "errors": sum(r["err"] for r in top),
            "share_of_errors": round(sum(r["err"] for r in top) / total_err, 4) if total_err else None,
            "ref_chars": sum(r["ref_chars"] for r in top),
            "cer": round(sum(r["err"] for r in top) / max(1, sum(r["ref_chars"] for r in top)), 6),
        }
    for thr in (0.5, 0.8, 1.0):
        g = [r for r in rows if r["cer"] >= thr]
        concentration[f"cer_ge_{thr}"] = {
            "n": len(g),
            "pct": round(100 * len(g) / len(rows), 2),
            "errors": sum(r["err"] for r in g),
            "share_of_errors": round(sum(r["err"] for r in g) / total_err, 4) if total_err else None,
        }

    worst = [
        {
            "id": r["id"],
            "dur": round(r["dur"], 3),
            "markers": r["noise_markers"],
            "cer": round(r["cer"], 4),
            "errors": r["err"],
            "ref_chars": r["ref_chars"],
            "ref": r.get("ref", "")[:140],
            "pred": r.get("pred", "")[:140],
        }
        for r in by_err[:8]
    ]

    cumulative = []
    for lo in (0, 2, 4, 6, 8, 10, 12):
        g = [r for r in rows if r["dur"] >= lo]
        e = sum(r["err"] for r in g)
        c = sum(r["ref_chars"] for r in g)
        cumulative.append({
            "min_dur": lo,
            "n": len(g),
            "errors": e,
            "ref_chars": c,
            "cer": round(e / c, 6) if c else None,
        })

    return {
        "label": label,
        "manifest_rows": len(manifest),
        "decoded_rows": len(rows),
        "decoded_n": dec.get("n"),
        "missing_in_decode": missing[:20],
        "manifest_not_decoded": skipped[:100],
        "skipped_gt_16s": sum(1 for x in skipped if (x.get("dur") or 0) > 16),
        "all": summary(rows, "all"),
        "by_duration": group_by(rows, "dur", DUR_BINS),
        "cumulative_duration": cumulative,
        "by_ref_len": group_by(rows, "ref_len", LEN_BINS),
        "noise": {
            "clean": summary(clean, "clean"),
            "noisy": summary(noisy, "noisy"),
            "noise_rows": len(noisy),
            "noise_pct": round(100 * len(noisy) / len(rows), 2) if rows else None,
            "marker_counts": dict(sorted(marker_counts.items(), key=lambda kv: -kv[1])),
        },
        "concentration": concentration,
        "worst": worst,
        "pearson_dur_cer": round(pearson([r["dur"] for r in rows], [r["cer"] for r in rows]), 4) if pearson([r["dur"] for r in rows], [r["cer"] for r in rows]) is not None else None,
        "pearson_reflen_cer": round(pearson([r["ref_len"] for r in rows], [r["cer"] for r in rows]), 4) if pearson([r["ref_len"] for r in rows], [r["cer"] for r in rows]) is not None else None,
    }


def duration_dist(rows: list[dict]) -> dict:
    total = len(rows)
    bins = []
    for lo, hi in DUR_BINS:
        g = [r for r in rows if lo <= float(r.get("dur") or 0) < hi]
        bins.append({
            "lo": lo,
            "hi": hi,
            "n": len(g),
            "pct": round(100 * len(g) / total, 2) if total else None,
        })
    return {"n": total, "mean_dur": round(sum(float(r.get("dur") or 0) for r in rows) / total, 4) if total else None, "bins": bins}


def fmt(x, nd=4):
    return "—" if x is None else f"{x:.{nd}f}"


def write_md(k: dict, f: dict, t: dict) -> None:
    lines = [
        "# CP-D2-lite — Kspon eval_other 35.14% CER 분해",
        "",
        "- 목적: Wave 2B 전에 Kspon 오류가 **길이·잡음·소수 outlier·도메인** 중 어디에 몰리는지 진단",
        "- 입력: 이미 생성된 decode JSON과 manifest만 사용. **추가 test 평가·재학습 없음.**",
        "- 주의: Kspon eval_other은 이미 gate에 1회 사용됐다. 이 분석은 사후 진단이며, 임계값·모델 선택에 재사용하지 않는다.",
        "",
        "## 1. Kspon eval_other",
        "",
        "| 항목 | 값 |",
        "|---|---:|",
        f"| manifest | {k['manifest_rows']} |",
        f"| decode | {k['decoded_rows']} |",
        f"| 16초 초과 제외 | {k['skipped_gt_16s']} |",
        f"| 기타 제외(0.4~1.1초 등 특징 부족) | {len(k['manifest_not_decoded']) - k['skipped_gt_16s']} |",
        f"| CER | **{fmt(k['all']['cer'])}** |",
        f"| 95% CI (문장 bootstrap) | {k['all']['cer_ci95']} |",
        f"| blank | {k['all']['blank']} |",
        f"| duration–CER Pearson | {fmt(k['pearson_dur_cer'], 3)} |",
        f"| ref length–CER Pearson | {fmt(k['pearson_reflen_cer'], 3)} |",
        "",
        "### 길이 구간별",
        "",
        "| duration(s) | n | CER | errors/ref |",
        "|---|---:|---:|---:|",
    ]
    for g in k["by_duration"]:
        lines.append(f"| {g['lo']}–{g['hi']} | {g['n']} | {fmt(g['cer'])} | {g['errors']}/{g['ref_chars']} |")
    lines += [
        "",
        "### 참조 길이 구간별",
        "",
        "| ref chars | n | CER |",
        "|---|---:|---:|",
    ]
    for g in k["by_ref_len"]:
        lines.append(f"| {g['lo']}–{g['hi']} | {g['n']} | {fmt(g['cer'])} |")
    lines += [
        "",
        "### 학습 데이터와 길이 분포",
        "",
        f"- train manifest: **{t['n']}클립**, 평균 **{t['mean_dur']}초**",
        "",
        "| duration(s) | train | Kspon eval_other |",
        "|---|---:|---:|",
    ]
    kd = {b["lo"]: b for b in k["by_duration"]}
    for b in t["bins"]:
        if b["lo"] >= 16:
            continue
        kk = kd.get(b["lo"])
        lines.append(f"| {b['lo']}–{b['hi']} | {b['n']} ({b['pct']}%) | {(kk['n'] if kk else 0)} |")
    lines += [
        "",
        "**핵심:** train은 ≤4초가 4.1%인데 Kspon eval_other은 57.2%다. **길이 분포가 크게 어긋난다.**",
        "",
        "### 누적 길이별 Kspon CER",
        "",
        "| 최소 길이 | n | CER |",
        "|---|---:|---:|",
    ]
    for c in k["cumulative_duration"]:
        lines.append(f"| ≥{c['min_dur']}s | {c['n']} | {fmt(c['cer'])} |")
    lines += [
        "",
        "### 잡음 마커",
        "",
        "| 구분 | n | 비율 | CER |",
        "|---|---:|---:|---:|",
        f"| clean | {k['noise']['clean']['n']} | {100 - (k['noise']['noise_pct'] or 0):.1f}% | {fmt(k['noise']['clean']['cer'])} |",
        f"| noisy | {k['noise']['noisy']['n']} | {k['noise']['noise_pct']}% | {fmt(k['noise']['noisy']['cer'])} |",
        "",
        f"- 마커별: `{k['noise']['marker_counts']}`",
        "",
        "### 오류 집중도",
        "",
        "| 구간 | n | 오류 비중 | 해당 CER |",
        "|---|---:|---:|---:|",
    ]
    for pct in (1, 5, 10):
        c = k["concentration"][f"top_{pct}pct"]
        lines.append(f"| 상위 {pct}% 발화 | {c['k']} | {100*c['share_of_errors']:.1f}% | {fmt(c['cer'])} |")
    for thr in (0.5, 0.8, 1.0):
        c = k["concentration"][f"cer_ge_{thr}"]
        lines.append(f"| CER ≥ {thr} | {c['n']} ({c['pct']}%) | {100*c['share_of_errors']:.1f}% | — |")
    lines += [
        "",
        "### 최악 발화 예시",
        "",
        "| id | dur | marker | CER | ref | pred |",
        "|---|---:|---|---:|---|---|",
    ]
    for w in k["worst"]:
        lines.append(f"| {w['id']} | {w['dur']} | {','.join(w['markers']) or '-'} | {w['cer']:.2f} | {w['ref'][:45]} | {w['pred'][:45]} |")
    lines += [
        "",
        "## 2. FLEURS test 비교",
        "",
        "| 항목 | Kspon eval_other | FLEURS test |",
        "|---|---:|---:|",
        f"| 평가 수 | {k['decoded_rows']} | {f['decoded_rows']} |",
        f"| CER | {fmt(k['all']['cer'])} | {fmt(f['all']['cer'])} |",
        f"| duration–CER Pearson | {fmt(k['pearson_dur_cer'], 3)} | {fmt(f['pearson_dur_cer'], 3)} |",
        f"| 상위 1% 오류 비중 | {100*k['concentration']['top_1pct']['share_of_errors']:.1f}% | {100*f['concentration']['top_1pct']['share_of_errors']:.1f}% |",
        f"| 상위 5% 오류 비중 | {100*k['concentration']['top_5pct']['share_of_errors']:.1f}% | {100*f['concentration']['top_5pct']['share_of_errors']:.1f}% |",
        "",
        "### FLEURS test 길이 구간",
        "",
        "| duration(s) | n | CER |",
        "|---|---:|---:|",
    ]
    for g in f["by_duration"]:
        lines.append(f"| {g['lo']}–{g['hi']} | {g['n']} | {fmt(g['cer'])} |")
    lines += [
        "",
        "## 3. 해석",
        "",
        "### 3.1 오류는 outlier가 아니라 전반적 음향 혼동",
        "",
        "- Kspon은 substitution이 84%(19,816/23,508)이고 blank는 0이다. **blank 붕괴가 아니라 음향 혼동**이다.",
        "- 상위 1% 발화가 전체 오류의 **4.2%**, 상위 5%가 **15.5%**뿐이다. 소수 잡음/이상 발화가 CER를 지배하지 않는다.",
        "- 따라서 “이상 발화 몇 개를 제거하면 해결”되는 문제가 아니다.",
        "",
        "### 3.2 주된 축은 길이 분포 불일치",
        "",
        "- Kspon CER: 0–2초 **46.4%** → 12–16초 **28.6%**로 단조 감소. duration–CER Pearson **-0.265**.",
        "- train은 ≤4초가 **4.1%**(4+93/2,384)인데, Kspon eval_other은 ≤4초가 **57.2%**(1,693/2,962)다.",
        "- 즉 **학습 분포에 없는 짧은 발화가 test의 절반 이상**이다. 이는 모델 용량 문제 이전에 **데이터 선택 문제**다.",
        "",
        "### 3.3 잡음 마커는 주원인이 아니다",
        "",
        "- noisy 34.7% vs clean 35.4% — **잡음 마커 발화가 더 나쁘지 않다.**",
        "- `b/`(호흡), `o/`(겹침), `l/`(웃음), `n/`(주변 잡음), `u/`(불명) 모두 소수이며, CER 차이를 만들지 않는다.",
        "- 따라서 2B에 noise augmentation을 넣는 것은 우선순위가 낮다.",
        "",
        "### 3.4 FLEURS test와의 비교",
        "",
        "- Kspon 35.1% vs FLEURS test 23.5%. Kspon ≥12초만 보면 **28.6% vs 23.1%**로 격차가 **5.5%p**로 줄어든다.",
        "- 즉 Kspon의 높은 CER 중 상당 부분은 **짧은 발화 비중**이고, 남는 5%p가 도메인/화자/발화 스타일 차이다.",
        "- FLEURS test는 4초 미만이 0개라 이 효과가 드러나지 않았다.",
        "",
        "### 3.5 외부 기준",
        "",
        "- KsponSpeech 원 논문은 960h급 Transformer에서 eval-other CER **9.0%**를 보고한다(우리와 데이터·모델 규모가 다름). [KsponSpeech paper](https://www.mdpi.com/2076-3417/10/19/6936)",
        "- ASR 문헌은 짧은 발화에서 substitution/insertion이 늘고 오류가 커진다고 보고한다. [Chan 2016](https://doi.org/10.1184/r1/6716237), [ESPnet issue #2893](https://github.com/espnet/espnet/issues/2893)",
        "- Kspon 전사 규칙의 `b/ l/ o/ n/ u/` 정의와 전처리 관행은 원 논문·KoSpeech와 일치한다. [KoSpeech preprocess](https://sooftware.github.io/kospeech/notes/Preparation.html)",
        "",
        "## 4. 2B 설계에 주는 결론",
        "",
        "1. **상위 conformer LoRA/fine-tune만으로는 부족할 가능성이 높다.** 오류는 전반적이지만, test의 57%가 학습에 거의 없는 ≤4초 발화다.",
        "2. 2B에는 **길이 균형 샘플러/커리큘럼**을 반드시 포함한다. 다만 train에 ≤4초가 100클립 미만이므로, 같은 4개를 반복하면 과적합한다.",
        "3. 따라서 **2B와 2C(짧은 발화 데이터 확보)를 분리하지 말고**, 2B 설계에 “Kspon train에서 eval-other 길이 분포에 맞춘 short-clip subset 확보”를 선행 조건으로 넣는다.",
        "4. noise augmentation은 우선순위가 낮다. 잡음 마커 CER가 clean보다 낮았다.",
        "5. 2B의 1차 비교는 **F-A′ 동결 vs 상위층 적응**으로 하고, 길이 bin별 CER를 반드시 보고한다. 전체 CER만 보면 짧은 발화 개선을 놓친다.",
        "",
        "이 분석은 gate 재판정이나 test 재사용이 아니다. 2B/2C 설계 입력으로만 쓴다.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    k = build(
        ROOT / "data/wave2a_lite/kspon_eval_other.jsonl",
        ROOT / "logs/W2A_lite/decode_kspon_eval_other.json",
        "kspon_eval_other",
    )
    f = build(
        ROOT / "data/wave2a_lite/fleurs_test.jsonl",
        ROOT / "logs/W2A_lite/decode_fleurs_test.json",
        "fleurs_test",
    )
    train_rows = load_jsonl(ROOT / "data/wave1/manifest.jsonl")
    t = duration_dist(train_rows)
    out = {"kspon": k, "fleurs": f, "train_duration": t}
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_md(k, f, t)
    print(json.dumps({
        "kspon": {x: k["all"][x] for x in ("n", "cer", "errors", "ref_chars")},
        "fleurs": {x: f["all"][x] for x in ("n", "cer", "errors", "ref_chars")},
        "kspon_top1_share": k["concentration"]["top_1pct"]["share_of_errors"],
        "kspon_noise_pct": k["noise"]["noise_pct"],
        "out": str(OUT_JSON),
        "md": str(OUT_MD),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
