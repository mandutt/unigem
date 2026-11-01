"""G-A3L — 언어 판정 회귀 (기존 운영 q8-al4 vs 신규 FP32 그래프).

절차(메모리 절약 3단계):
    --mode old      기존 운영 파이프라인(eg2_langidentifier 어댑터, q8-al4)으로 벡터 생성
    --mode new      신규 ONNX(오디오 타워 + 텍스트 백본)로 벡터 생성
    --mode compare  두 벡터를 같은 판정기(eg2_langid.LanguageIdentifier)에 넣어 argmax 일치율 비교

게이트 G-A3L: 기존 대비 argmax 일치율 ≥ 99%, 확신 오판 증가 0.
"""

from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import tarfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGID = r"C:\code\eg2-langidentifier"
FLEURS = os.path.join(LANGID, "data", "raw", "fleurs_cache")
sys.path.insert(0, os.path.join(ROOT, "onnx"))
sys.path.insert(0, LANGID)

LANGS = ["en_us", "ko_kr", "ja_jp", "cmn_hans_cn", "es_419", "pt_br", "fr_fr", "de_de",
         "it_it", "nl_nl", "pl_pl", "ru_ru", "uk_ua", "sv_se", "ar_eg", "hi_in",
         "th_th", "tr_tr", "vi_vn", "fil_ph", "id_id", "ms_my"]
PER_LANG = 2
SR = 16000


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


def load_clips(per_lang: int = PER_LANG) -> list[tuple[str, int, np.ndarray]]:
    out = []
    for lang in LANGS:
        path = os.path.join(FLEURS, f"{lang}_test.tar.gz")
        if not os.path.exists(path):
            print("missing", path, flush=True)
            continue
        got = 0
        with tarfile.open(path, "r:gz") as tf:
            for m in tf:
                if not m.name.endswith(".wav"):
                    continue
                a = read_wav(tf.extractfile(m).read())
                if len(a) < SR:  # 1초 미만 제외
                    continue
                out.append((lang, got, a))
                got += 1
                if got >= per_lang:
                    break
        print(lang, got, flush=True)
    return out


def build_old(clips, out_path):
    from eg2_langid.adapters.gemma2_np import make_embedder
    embed = make_embedder(threads=4)
    vecs, keys = [], []
    for lang, idx, a in clips:
        vecs.append(embed(a).astype(np.float32))
        keys.append(f"{lang}:{idx}")
        print("old", keys[-1], flush=True)
    np.savez_compressed(out_path, vecs=np.stack(vecs), keys=np.array(keys))


def build_new(clips, out_path, audio_onnx, text_onnx, threads=4):
    """기존 운영 오디오 인코더(q8-al4)로 soft token을 만들고, 신규 텍스트 그래프로 임베딩한다.

    이렇게 하면 두 파이프라인의 차이가 '텍스트 그래프 교체' 하나로 통제된다(G-A3L).
    """
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
        print("new", keys[-1], flush=True)
    np.savez_compressed(out_path, vecs=np.stack(vecs), keys=np.array(keys))


def compare(old_path, new_path, out_path):
    from eg2_langid.detector import LanguageIdentifier
    o = np.load(old_path)
    n = np.load(new_path)
    assert list(o["keys"]) == list(n["keys"]), "key 순서 불일치"
    det = LanguageIdentifier()
    rows, agree, cos_sum = [], 0, 0.0
    for k, vo, vn in zip(o["keys"], o["vecs"], n["vecs"]):
        ro, rn = det.detect(vo), det.detect(vn)
        same = ro.label == rn.label
        agree += int(same)
        c = float(np.dot(vo, vn) / (np.linalg.norm(vo) * np.linalg.norm(vn) + 1e-12))
        cos_sum += c
        rows.append({"key": str(k), "old": ro.label, "new": rn.label, "same": same,
                     "old_margin": ro.margin, "new_margin": rn.margin, "cos": c})
    summary = {
        "n": len(rows),
        "argmax_agree": agree / max(1, len(rows)),
        "mean_cos": cos_sum / max(1, len(rows)),
        "gate": "PASS" if agree / max(1, len(rows)) >= 0.99 else "FAIL",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "rows": rows}, f, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["old", "new", "compare"], required=True)
    ap.add_argument("--old", default=os.path.join(ROOT, "logs", "A3L_old.npz"))
    ap.add_argument("--new", default=os.path.join(ROOT, "logs", "A3L_new.npz"))
    ap.add_argument("--out", default=os.path.join(ROOT, "logs", "A3L_langid.json"))
    ap.add_argument("--audio-onnx", default=r"C:\code\eg2-langidentifier\scripts\mmal4\audio_encoder_quantized_al4.onnx",
                    help="G-A3L은 텍스트 그래프 교체만 검증하므로 기존 운영 오디오 인코더를 그대로 쓴다")
    ap.add_argument("--text-onnx", default=os.path.join(ROOT, "onnx", "eg2_text_research_fp32.onnx"))
    ap.add_argument("--per-lang", type=int, default=PER_LANG)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    if args.mode == "compare":
        compare(args.old, args.new, args.out)
        return
    clips = load_clips(args.per_lang)
    print("clips", len(clips), flush=True)
    if args.mode == "old":
        build_old(clips, args.old)
    else:
        build_new(clips, args.new, args.audio_onnx, args.text_onnx)


if __name__ == "__main__":
    main()
