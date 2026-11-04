"""Build log-mel filterbank features for the Wave 2A-lite fbank baseline.

80 mel bands, 25 ms window / 10 ms hop, 512-point FFT, per-utterance CMVN.
This is a diagnostic baseline, not a replacement for EG2 features.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
SR = 16000
N_FFT = 512
WIN = 400
HOP = 640  # 40 ms hop = 25 Hz, same frame rate as EG2 audio features
N_MELS = 80
MAX_FRAMES = 400


def mel_filterbank(n_mels: int = N_MELS, n_fft: int = N_FFT, sr: int = SR) -> np.ndarray:
    def hz_to_mel(hz):
        return 2595.0 * np.log10(1.0 + hz / 700.0)

    def mel_to_hz(mel):
        return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

    mels = np.linspace(hz_to_mel(0.0), hz_to_mel(sr / 2), n_mels + 2)
    hz = mel_to_hz(mels)
    bins = np.floor((n_fft + 1) * hz / sr).astype(int)
    fb = np.zeros((n_mels, n_fft // 2 + 1), dtype=np.float32)
    for m in range(1, n_mels + 1):
        l, c, r = bins[m - 1], bins[m], bins[m + 1]
        if c > l:
            fb[m - 1, l:c] = (np.arange(l, c) - l) / (c - l)
        if r > c:
            fb[m - 1, c:r] = (r - np.arange(c, r)) / (r - c)
    return fb


def logmel(path: Path, fb: np.ndarray) -> np.ndarray:
    x, sr = sf.read(path, dtype="float32", always_2d=False)
    if sr != SR:
        raise ValueError(f"expected 16k, got {sr}: {path}")
    if x.ndim > 1:
        x = x.mean(axis=1)
    if len(x) < WIN:
        x = np.pad(x, (0, WIN - len(x)))
    n = 1 + (len(x) - WIN) // HOP
    idx = np.arange(WIN)[None, :] + HOP * np.arange(n)[:, None]
    frames = x[idx] * np.hamming(WIN)[None, :]
    spec = np.fft.rfft(frames, n=N_FFT, axis=1)
    power = (np.abs(spec) ** 2).astype(np.float32)
    mel = power @ fb.T
    logmel = np.log(np.maximum(mel, 1e-8))
    logmel = (logmel - logmel.mean(axis=0, keepdims=True)) / (logmel.std(axis=0, keepdims=True) + 1e-5)
    return logmel[:MAX_FRAMES].astype(np.float16)


def build(manifest: str, vocab: dict, out: str) -> None:
    rows = [json.loads(l) for l in open(manifest, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if 0.5 <= float(r.get("dur", 0)) <= 16.0]
    fb = mel_filterbank()
    c2i = vocab["char2id"]
    feats = np.zeros((len(rows), MAX_FRAMES, N_MELS), dtype=np.float16)
    lens = np.zeros(len(rows), dtype=np.int32)
    targets = []
    target_lens = np.zeros(len(rows), dtype=np.int32)
    ids, texts, speakers = [], [], []
    for i, r in enumerate(rows):
        f = logmel(ROOT / r["audio"], fb)
        feats[i, :len(f)] = f
        lens[i] = len(f)
        text = r.get("text") or r.get("ref") or ""
        ids_ = [c2i[c] for c in text if c in c2i and c != " "]
        targets.extend(ids_)
        target_lens[i] = len(ids_)
        ids.append(r["id"])
        texts.append(text)
        speakers.append(r.get("speaker") or r.get("source") or "")
    np.savez_compressed(out, feats=feats, lens=lens, targets=np.asarray(targets, np.int32),
                        target_lens=target_lens, ids=np.asarray(ids), texts=np.asarray(texts),
                        speakers=np.asarray(speakers))
    print(f"saved {out} feats={feats.shape} clips={len(rows)} chars={len(targets)}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-manifest", default=str(ROOT / "data/wave1/manifest.jsonl"))
    ap.add_argument("--dev-manifest", default=str(ROOT / "data/wave2a_lite/fleurs_dev.jsonl"))
    ap.add_argument("--vocab", default=str(ROOT / "data/wave2a_lite/vocab.json"))
    ap.add_argument("--out-dir", default=str(ROOT / "data/wave2a_lite/feats_fbank"))
    a = ap.parse_args()
    vocab = json.load(open(a.vocab, encoding="utf-8"))
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    build(a.train_manifest, vocab, str(out / "train.npz"))
    build(a.dev_manifest, vocab, str(out / "dev.npz"))
    json.dump({"n_mels": N_MELS, "win": WIN, "hop": HOP, "n_fft": N_FFT, "cmvn": "per-utterance"},
              open(out / "config.json", "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main()
