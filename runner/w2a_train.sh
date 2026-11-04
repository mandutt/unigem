#!/usr/bin/env bash
# Train one Wave 2A-lite arm. Usage: runner/w2a_train.sh {fa|fb|fc_softmax|fc_concat} [seed]
set -euo pipefail
cd "$(dirname "$0")/.."
ARM="${1:?arm required: fa|fb|fc_softmax|fc_concat}"
SEED="${2:-42}"
PY=".venv/Scripts/python.exe"
VOCAB="data/wave2a_lite/vocab.json"
CKPT="data/wave2a_lite/ckpt"
LOG="logs/W2A_lite"
mkdir -p "$CKPT" "$LOG"

case "$ARM" in
  fa)
    FEATURES="data/wave1/feats/fa.npz"
    DEV="data/wave2a_lite/feats_dev/fa.npz"
    ARCH="base"
    ;;
  fb)
    FEATURES="data/wave1/feats/fb.npz"
    DEV="data/wave2a_lite/feats_dev/fb.npz"
    ARCH="base"
    ;;
  fc_softmax)
    FEATURES="data/wave1/feats/fc.npz"
    DEV="data/wave2a_lite/feats_dev/fc.npz"
    ARCH="softmax"
    ;;
  fc_concat)
    FEATURES="data/wave1/feats/fc.npz"
    DEV="data/wave2a_lite/feats_dev/fc.npz"
    ARCH="base"
    ;;
  *)
    echo "unknown arm: $ARM" >&2
    exit 2
    ;;
esac

echo "arm=$ARM seed=$SEED features=$FEATURES dev=$DEV arch=$ARCH"
"$PY" train/d5_reader.py \
  --features "$FEATURES" --dev-features "$DEV" --vocab-file "$VOCAB" \
  --arm "${ARM}_s${SEED}" --arch "$ARCH" --epochs 20 --patience 5 \
  --seed "$SEED" --ckpt-dir "$CKPT" --threads 6 --retarget \
  2>&1 | tee "$LOG/train_${ARM}_s${SEED}.log"
