"""G-A3L-R — 언어 판정 회귀 (Q8 운영 경로, 220클립).

개정(Addendum A §A-2): 판정 대상은 교체 후보인 **Q8 운영 경로**. FP32 연구용은 참고.
- 평가 세트: `C:\\code\\eg2-langidentifier\\data\\raw\\fleurs_test` 메타의 22언어 × 10클립 = 220
- 필수 조건: argmax 일치율 ≥ 99%, 확신 오판(margin≥0.05) 증가 0
- PASS-R: 일치율 <99%라도 (신규만 오답 0) + (확신 오판 증가 0) + 건별 보고 → 사용자 확인 시 인정

사용:
  python eval/g_a3l_r.py --mode old|new|compare|all
"""
from __future__ import annotations

import argparse
import json
import math
import os
import struct
import sys
import tarfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGID = r"C:\code\eg2-langidentifier"
FLEURS = os.path.join(LANGID, "data", "raw", "fleurs_cache")
META = os.path.join(LANGID, "data", "raw", "fleurs_test")
sys.path.insert(0, os.path.join(ROOT, "onnx"))
sys.path.insert(0, LANGID)

LANGS = ["en_us", "ko_kr", "ja_jp", "cmn_hans_cn", "es_419", "pt_br", "fr_fr", "de_de",
         "it_it", "nl_nl", "pl_pl", "ru_ru", "uk_ua", "sv_se", "ar_eg", "hi_in",
         "th_th", "tr_tr", "vi_vn", "fil_ph", "id_id", "ms_my"]
SR = 16000
CONF_MARGIN = 0.05      # Addendum A §A-2.2 (보고서 기준)
VERIFY_MARGIN = 0.4     # 코드의 재확인 임계값(engine.verify_margin)


def read_wav(raw: bytes) -> np.ndarray:
    ch = struct.unpack("<H", raw[22:24])[0]
    sr = struct.unpack("<I", raw[24:28])[0]
    pos, data = 12, None
    while pos + 8 <= len(raw):
        cid = raw[pos:pos + 4]
        sz = struct.unpack("<I", raw[pos + 4:pos + 8])[0]
        if cid == b"data":
            data = raw[pos + 8:pos + 8 + sz]
            break
        pos += 8 + sz + (sz & 1)
    if data is None:
        raise ValueError("no data chunk")
    a = np.frombuffer(data, dtype="<f4").astype(np.float32)
    if ch > 1:
        a = a.reshape(-1, ch).mean(1)
    if sr != SR:
        n = int(len(a) * SR / sr)
        a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)
    return a


def load_clips(per_lang: int = 10):
    """운영 평가 세트(meta 파일 목록)와 동일한 클립을 로드한다."""
    out = []
    for lang in LANGS:
        meta_path = os.path.join(META, f"{lang}_meta.json")
        tar_path = os.path.join(FLEURS, f"{lang}_test.tar.gz")
        if not (os.path.exists(meta_path) and os.path.exists(tar_path)):
            print("missing", lang, flush=True)
            continue
        names = [m["file"] for m in json.load(open(meta_path, encoding="utf-8"))][:per_lang]
        want = {n.split("/")[-1]: i for i, n in enumerate(names)}
        got = {}
        with tarfile.open(tar_path, "r:gz") as tf:
            for m in tf:
                base = os.path.basename(m.name)
                if base in want and base not in got:
                    got[base] = read_wav(tf.extractfile(m).read())
                if len(got) == len(want):
                    break
        for i, n in enumerate(names):
            base = n.split("/")[-1]
            if base in got:
                out.append((lang, i, got[base]))
        print(lang, len(got), flush=True)
    return out


def build_old(clips, out_path):
    from eg2_langid.adapters.gemma2_np import make_embedder
    embed = make_embedder(threads=4)
    vecs, keys = [], []
    for lang, idx, a in clips:
        vecs.append(embed(a).astype(np.float32))
        keys.append(f"{lang}:{idx}")
    np.savez_compressed(out_path, vecs=np.stack(vecs), keys=np.array(keys))
    print("saved", out_path, len(vecs), flush=True)


def build_new(clips, out_path, audio_onnx, text_onnx, threads=4):
    import onnxruntime as ort
    from eg2_langid.adapters.gemma2_np import log_mel, frame_mask

    so = ort.SessionOptions()
    so.intra_op_num_threads = threads
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    audio = ort.InferenceSession(audio_onnx, so, providers=["CPUExecutionProvider"])
    text = ort.InferenceSession(text_onnx, so, providers=["CPUExecutionProvider"])
    BOS, BOA, AUDIO_TOK, EOA, EOS = 2, 256000, 258881, 258883, 1

    vecs, keys = [], []
    for lang, idx, a in clips:
        feats = log_mel(a[: SR * 30])
        mask = frame_mask(min(len(a), SR * 30), feats.shape[0])
        soft = audio.run(["audio_features"], {
            "input_features": feats[None].astype(np.float32),
            "input_features_mask": mask[None].astype(bool),
        })[0]
        n = soft.shape[0]
        ids = [BOS, BOA] + [AUDIO_TOK] * n + [EOA, EOS]
        v = text.run(["sentence_embedding"], {
            "input_ids": np.array([ids], dtype=np.int64),
            "attention_mask": np.ones((1, len(ids)), dtype=np.int64),
            "image_features": np.zeros((0, 512), np.float32),
            "video_features": np.zeros((0, 512), np.float32),
            "audio_features": soft.astype(np.float32),
        })[0][0]
        vecs.append(v.astype(np.float32))
        keys.append(f"{lang}:{idx}")
    np.savez_compressed(out_path, vecs=np.stack(vecs), keys=np.array(keys))
    print("saved", out_path, len(vecs), flush=True)


def clopper_pearson(k, n, alpha=0.05):
    from scipy.stats import beta
    lo = 0.0 if k == 0 else beta.ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - alpha / 2, k + 1, n - k)
    return float(lo), float(hi)


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, p)


def compare(old_path, new_path, out_path):
    from eg2_langid.detector import LanguageIdentifier
    o = np.load(old_path)
    n = np.load(new_path)
    assert list(o["keys"]) == list(n["keys"]), "key 순서 불일치"
    det = LanguageIdentifier()

    rows = []
    agree = 0
    for k, vo, vn in zip(o["keys"], n["vecs"]):
        truth = str(k).split(":")[0]
        ro, rn = det.detect(vo), det.detect(vn)
        lo = "unknown" if ro.unknown else ro.label
        ln = "unknown" if rn.unknown else rn.label
        same = lo == ln
        agree += int(same)
        rows.append({
            "key": str(k), "truth": truth,
            "old": lo, "new": ln, "same": same,
            "old_margin": float(ro.margin), "new_margin": float(rn.margin),
            "old_correct": lo == truth, "new_correct": ln == truth,
            "cos": float(np.dot(vo, vn) / (np.linalg.norm(vo) * np.linalg.norm(vn) + 1e-12)),
        })

    N = len(rows)
    ci = clopper_pearson(agree, N)
    old_ok = sum(r["old_correct"] for r in rows)
    new_ok = sum(r["new_correct"] for r in rows)
    new_only_wrong = sum(1 for r in rows if r["old_correct"] and not r["new_correct"])
    old_only_wrong = sum(1 for r in rows if not r["old_correct"] and r["new_correct"])
    both_wrong = sum(1 for r in rows if not r["old_correct"] and not r["new_correct"])

    def conf_err(key_m, ok_key):
        sel = [r for r in rows if r[key_m] >= 0.05]
        return sum(1 for r in sel if not r[ok_key]), len(sel)

    old_conf_err, old_conf_n = conf_err("old_margin", "old_correct")
    new_conf_err, new_conf_n = conf_err("new_margin", "new_correct")

    mismatches = [r for r in rows if not r["same"]]
    pair_counts = {}
    for r in mismatches:
        pair_counts[f"{r['old']}->{r['new']}"] = pair_counts.get(f"{r['old']}->{r['new']}", 0) + 1

    summary = {
        "n": N,
        "argmax_agree": agree / N,
        "agree_ci95": ci,
        "correct_old": old_ok, "correct_new": new_ok,
        "accuracy_old": old_ok / N, "accuracy_new": new_ok / N,
        "direction": {"new_only_correct": old_only_wrong, "old_only_correct": new_only_wrong,
                      "both_wrong": both_wrong},
        "confident_errors": {"margin_ge_0.05": {"old": old_conf_err, "new": new_conf_err,
                                                "n_conf_old": old_conf_n, "n_conf_new": new_conf_n}},
        "mcnemar_exact_p": mcnemar_exact(new_only_wrong, old_only_wrong),
        "mean_cos": float(np.mean([r["cos"] for r in rows])),
        "mismatch_pairs": pair_counts,
        "mismatches": mismatches,
        "gate": {
            "g_a3l_r": "PASS" if (agree / N >= 0.99 and new_conf_err <= old_conf_err)
            else ("PASS-R_candidate" if (new_only_wrong == 0 and new_conf_err <= old_conf_err)
                  else "FAIL")
        },
    }
    print(json.dumps({k: v for k, v in summary.items() if k != "mismatches"}, ensure_ascii=False, indent=2))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "rows": rows}, f, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["old", "new", "compare", "all"], required=True)
    ap.add_argument("--per-lang", type=int, default=10)
    ap.add_argument("--old", default=os.path.join(ROOT, "logs", "A3LR_old.npz"))
    ap.add_argument("--new", default=os.path.join(ROOT, "logs", "A3LR_new_q8.npz"))
    ap.add_argument("--out", default=os.path.join(ROOT, "logs", "A3LR.json"))
    ap.add_argument("--audio-onnx",
                    default=os.path.join(LANGID, "scripts", "mmal4", "audio_encoder_quantized_al4.onnx"))
    ap.add_argument("--text-onnx", default=os.path.join(ROOT, "onnx", "eg2_text_prod_q8.onnx"))
    args = ap.parse_args()

    if args.mode == "compare":
        compare(args.old, args.new, args.out)
        return
    clips = load_clips(args.per_lang)
    print("clips", len(clips), flush=True)
    if args.mode in ("old", "all"):
        build_old(clips, args.old)
    if args.mode in ("new", "all"):
        build_new(clips, args.new, args.audio_onnx, args.text_onnx)
    if args.mode == "all":
        compare(args.old, args.new, args.out)


if __name__ == "__main__":
    main()
