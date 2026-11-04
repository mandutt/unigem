#!/usr/bin/env bash
# Decode one Wave 2A-lite arm on FLEURS dev. Usage: runner/w2a_decode_dev.sh ARM [SEED]
set -euo pipefail
cd "$(dirname "$0")/.."
ARM="${1:?arm required: fa|fb|fc_softmax|fc_concat}"
SEED="${2:-42}"
PY=".venv/Scripts/python.exe"
VOCAB="data/wave2a_lite/vocab.json"
CKPT="data/wave2a_lite/ckpt/${ARM}_s${SEED}.best.pt"
case "$ARM" in
  fa) DEV="data/wave2a_lite/feats_dev/fa.npz" ;;
  fb) DEV="data/wave2a_lite/feats_dev/fb.npz" ;;
  fc_softmax|fc_concat) DEV="data/wave2a_lite/feats_dev/fc.npz" ;;
  *) echo "unknown arm: $ARM" >&2; exit 2 ;;
esac
test -f "$CKPT" || { echo "missing $CKPT" >&2; exit 3; }
mkdir -p logs/W2A_lite
"$PY" train/d5_reader.py --decode --features "$DEV" --vocab-file "$VOCAB" \
  --ckpt "$CKPT" --arm "${ARM}_s${SEED}" --out "logs/W2A_lite/decode_${ARM}_s${SEED}.json" --threads 6 \
  2>&1 | tee "logs/W2A_lite/decode_${ARM}_s${SEED}.log"
