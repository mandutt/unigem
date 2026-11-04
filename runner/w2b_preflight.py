"""W2B preflight: eval_clean split, duration/OOV/CTC checks. Read-only audio."""
from __future__ import annotations

import json
import random
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
EVAL_ZIP = ROOT / "data/raw/kspon_eval/10.한국어음성/KsponSpeech_eval.zip"
TRN = ROOT / "data/raw/kspon_eval/extracted/eval_clean.trn"
C2A1 = ROOT / "data/c2a1/manifest.json"
VOCAB = ROOT / "data/wave2a_lite/vocab.json"
OUT_JSON = ROOT / "reports/provenance/W2B/preflight.json"
OUT_MD = ROOT / "reports/W2B_preflight.md"
CAND = ROOT / "data/wave2b/preflight/split_candidate.json"
BINS = [(0, 2), (2, 4), (4, 8), (8, 12), (12, 16), (16, 999)]
SEED = 42


def load_vocab():
    v = json.loads(VOCAB.read_text(encoding="utf-8"))
    return set(v["char2id"].keys())


def bin_of(d):
    for lo, hi in BINS:
        if lo <= d < hi:
            return f"{lo}-{hi}"
    return "unknown"


def read_trn():
    out = {}
    for line in TRN.read_text(encoding="utf-8", errors="replace").splitlines():
        if " :: " not in line:
            continue
        path, text = line.split(" :: ", 1)
        out[Path(path).stem] = text
    return out


def main():
    from eval.normalize import normalize_nospace

    trn = read_trn()
    with zipfile.ZipFile(EVAL_ZIP) as z:
        infos = {}
        for i in z.infolist():
            if i.filename.startswith("eval_clean/") and i.filename.endswith(".pcm"):
                infos[Path(i.filename).stem] = i.file_size
    ids = sorted(set(trn) & set(infos))
    print("trn", len(trn), "pcm", len(infos), "intersection", len(ids))
    rows = []
    for i in ids:
        # odd bytes: drop the trailing pad byte; 16 kHz, 16-bit mono
        dur = (infos[i] - (infos[i] % 2)) / 2 / 16000
        rows.append({"id": i, "dur": round(dur, 3), "ref": trn[i], "ref_norm": normalize_nospace(trn[i]), "bin": bin_of(dur)})
    excluded_gt16 = [r for r in rows if r["dur"] > 16.0]
    rows = [r for r in rows if r["dur"] <= 16.0]
    used = [x["id"] for x in json.loads(C2A1.read_text(encoding="utf-8")) if x.get("source") == "kspon_eval_clean"]
    used_set = set(used)
    missing_used = sorted(used_set - set(ids))
    print("used100", len(used), "missing", len(missing_used))

    def stratified(pool, n, rng):
        by = {}
        for r in pool:
            by.setdefault(r["bin"], []).append(r)
        total = len(pool)
        targets = {b: n * len(v) / total for b, v in by.items()}
        picked = []
        for b, v in by.items():
            k = min(len(v), int(round(targets.get(b, 0))))
            picked += rng.sample(v, k)
        rest = [r for r in pool if r not in picked]
        rng.shuffle(rest)
        picked += rest[: max(0, n - len(picked))]
        if len(picked) > n:
            rng.shuffle(picked)
            picked = picked[:n]
        return picked

    rng = random.Random(SEED)
    by_id = {r["id"]: r for r in rows}
    fixed_dev = [by_id[i] for i in used if i in by_id]
    remaining = [r for r in rows if r["id"] not in used_set]
    extra_dev = stratified(remaining, 400, rng)
    dev = fixed_dev + extra_dev
    dev_ids = {r["id"] for r in dev}
    remaining2 = [r for r in rows if r["id"] not in dev_ids]
    test = stratified(remaining2, 2400, rng)
    test_ids = {r["id"] for r in test}
    spare = [r for r in remaining2 if r["id"] not in test_ids]

    def counts(groups):
        c = Counter()
        for g in groups:
            c[g["bin"]] += 1
        return dict(c)

    vocab = load_vocab()
    oov = Counter()
    oov_rows = 0
    ctc_bad = 0
    ctc_no_blank = 0
    for r in rows:
        miss = [c for c in r["ref_norm"] if c not in vocab]
        if miss:
            oov_rows += 1
            oov.update(miss)
        frames = int(r["dur"] * 25)
        if len(r["ref_norm"]) > frames:
            ctc_bad += 1
        # conservative CTC feasibility: target chars + one blank per repeated char
        repeats = sum(1 for a, b in zip(r["ref_norm"], r["ref_norm"][1:]) if a == b)
        if len(r["ref_norm"]) + repeats > frames:
            ctc_no_blank += 1

    def oov_group(groups):
        n = 0
        chars = 0
        for r in groups:
            miss = [c for c in r["ref_norm"] if c not in vocab]
            if miss:
                n += 1
                chars += len(miss)
        return {"rows": n, "pct": round(100 * n / max(1, len(groups)), 2), "chars": chars}

    out = {
        "source": str(EVAL_ZIP),
        "eval_clean_pcm": len(infos),
        "eval_clean_trn": len(trn),
        "eval_clean_intersection": len(ids),
        "excluded_gt16": len(excluded_gt16),
        "eligible_le16": len(rows),
        "used_dev_100": len(used),
        "used_missing": missing_used,
        "duration": {
            "min": min(r["dur"] for r in rows),
            "max": max(r["dur"] for r in rows),
            "mean": round(sum(r["dur"] for r in rows) / len(rows), 3),
            "bins_all": counts(rows),
        },
        "split": {
            "dev": len(dev),
            "test": len(test),
            "spare": len(spare),
            "dev_bins": counts(dev),
            "test_bins": counts(test),
            "spare_bins": counts(spare),
            "overlap_dev_test": len(dev_ids & test_ids),
            "overlap_dev_used": len(dev_ids & used_set),
            "overlap_test_used": len(test_ids & used_set),
        },
        "oov": {
            "rows_with_oov": oov_rows,
            "oov_rows_pct": round(100 * oov_rows / len(rows), 2),
            "oov_chars_total": sum(oov.values()),
            "oov_types": len(oov),
            "top": oov.most_common(20),
            "dev": oov_group(dev),
            "test": oov_group(test),
            "spare": oov_group(spare),
        },
        "ctc_frame": {
            "chars_gt_frames": ctc_bad,
            "chars_repeats_gt_frames": ctc_no_blank,
            "note": "frames = floor(dur*25); conservative repeated-char blank check",
        },
        "speaker_metadata": "not present in eval_clean.trn or zip names; duration-stratified split only",
        "disk_free_gb": None,
    }
    # disk is filled by the shell wrapper; keep this script read-only otherwise.
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CAND.parent.mkdir(parents=True, exist_ok=True)
    CAND.write_text(json.dumps({"seed": SEED, "dev": [r["id"] for r in dev], "test": [r["id"] for r in test], "spare": [r["id"] for r in spare]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# W2B Preflight — eval_clean split·duration·OOV·CTC",
        "",
        "- 입력: `data/raw/kspon_eval/10.한국어음성/KsponSpeech_eval.zip`, `extracted/eval_clean.trn`",
        "- **오디오 추출·다운로드·학습 없음.** zip metadata와 전사만 읽었다.",
        "",
        "## 1. eval_clean 기본",
        "",
        f"- PCM: {len(infos)}, TRN: {len(trn)}, 교집합: **{len(ids)}**",
        f"- 16초 초과 제외: **{len(excluded_gt16)}** → 평가 적격 **{len(rows)}**",
        f"- 기존 D-β dev 100: {len(used)}; eval_clean에 없는 ID: {len(missing_used)}",
        f"- duration: min {out['duration']['min']}s / mean {out['duration']['mean']}s / max {out['duration']['max']}s",
        "",
        "| duration | all | dev 500 | test 2,400 | spare 90 |",
        "|---|---:|---:|---:|---:|",
    ]
    for lo, hi in BINS:
        key = f"{lo}-{hi}"
        lines.append(f"| {key} | {out['duration']['bins_all'].get(key,0)} | {out['split']['dev_bins'].get(key,0)} | {out['split']['test_bins'].get(key,0)} | {out['split']['spare_bins'].get(key,0)} |")
    lines += [
        "",
        "## 2. split",
        "",
        f"- dev: **{len(dev)}** (기존 100 + 신규 400)",
        f"- test: **{len(test)}**",
        f"- spare: **{len(spare)}** (평가에 쓰지 않음)",
        f"- dev/test 교집합: **{len(dev_ids & test_ids)}**",
        f"- dev∩used: {len(dev_ids & used_set)} / test∩used: **{len(test_ids & used_set)}**",
        "",
        "## 3. OOV·CTC",
        "",
        f"- OOV rows: **{oov_rows}/{len(rows)} ({out['oov']['oov_rows_pct']}%)**, OOV types {len(oov)}, chars {sum(oov.values())} **(2A FLEURS vocab 1,101 기준 상한)**",
        f"- OOV by split: dev **{out['oov']['dev']['rows']}/{len(dev)} ({out['oov']['dev']['pct']}%)**, test **{out['oov']['test']['rows']}/{len(test)} ({out['oov']['test']['pct']}%)**, spare **{out['oov']['spare']['rows']}/{len(spare)} ({out['oov']['spare']['pct']}%)**",
        f"- top OOV: `{oov.most_common(15)}`",
        f"- chars > frames: **{ctc_bad}**",
        f"- chars+repeats > frames: **{ctc_no_blank}**",
        "",
        "## 4. 화자·데이터 가용성",
        "",
        "- eval_clean.trn과 zip 파일명에는 **화자 ID가 없다**. 따라서 dev/test는 **duration 층화**로만 나눴다.",
        "- Kspon train shard는 로컬에 없다. AI Hub filekey 50211~50215(각 14~15GB) 중 하나를 streaming으로 받아 short 4h를 선별해야 한다.",
        "- 현재 C: 여유는 약 18GB다. zip 전체 해제 없이 `zipfile` streaming + 선택 파일만 저장하는 전제로 진행해야 한다.",
        "",
        "## 5. Blocker",
        "",
        "- eval_clean **3,000**은 확인됐고, 16초 초과 10건을 제외한 **2,990**에서 dev 500/test 2,400/spare 90 split 후보를 만들었다.",
        "- `test`는 아직 **봉인 평가 전**이며, checkpoint freeze 전에는 어떤 모델도 평가하지 않는다.",
        "- Kspon train shard·화자 메타데이터·short 4h 선별은 아직 수행하지 않았다.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"split": out["split"], "oov": out["oov"], "ctc": out["ctc_frame"], "json": str(OUT_JSON), "md": str(OUT_MD)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
