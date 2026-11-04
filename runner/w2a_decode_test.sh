#!/usr/bin/env bash
# Decode the frozen Wave 2A-lite checkpoint on a sealed test set.
# Usage: runner/w2a_decode_test.sh {kspon|fleurs}
set -euo pipefail
cd "$(dirname "$0")/.."
WHICH="${1:?kspon|fleurs required}"
PY=".venv/Scripts/python.exe"
CKPT="data/wave2a_lite/frozen/w2a_fc_concat_s42.best.pt"
VOCAB="data/wave2a_lite/vocab.json"
case "$WHICH" in
  kspon) FEATS="data/wave2a_lite/feats_kspon_eval_other/fc.npz"; OUT="logs/W2A_lite/decode_kspon_eval_other.json" ;;
  fleurs) FEATS="data/wave2a_lite/feats_fleurs_test/fc.npz"; OUT="logs/W2A_lite/decode_fleurs_test.json" ;;
  *) echo "unknown: $WHICH" >&2; exit 2 ;;
esac
test -f "$CKPT" || { echo "missing frozen checkpoint" >&2; exit 3; }
test -f "$FEATS" || { echo "missing features: $FEATS" >&2; exit 4; }
"$PY" train/d5_reader.py --decode --features "$FEATS" --vocab-file "$VOCAB" \
  --ckpt "$CKPT" --arm "fc_concat_s42_frozen" --out "$OUT" --threads 6 \
  2>&1 | tee "${OUT%.json}.log"
