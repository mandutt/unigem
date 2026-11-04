#!/usr/bin/env bash
# Extract sealed test features AFTER checkpoint freeze only.
# Usage: runner/w2a_extract_test.sh {kspon|fleurs|both}
set -euo pipefail
cd "$(dirname "$0")/.."
WHICH="${1:-both}"
PY=".venv/Scripts/python.exe"
VOCAB="data/wave2a_lite/vocab.json"

extract() {
  local manifest="$1" out="$2"
  test -f "$manifest" || { echo "missing $manifest" >&2; exit 2; }
  echo "EXTRACT $manifest -> $out"
  "$PY" train/w1_extract.py --manifest "$manifest" --vocab-in "$VOCAB" \
    --out-dir "$out" --arms fa,fb,fc --threads 6 \
    2>&1 | tee "logs/W2A_lite/extract_$(basename "$manifest" .jsonl).log"
}

case "$WHICH" in
  kspon) extract data/wave2a_lite/kspon_eval_other.jsonl data/wave2a_lite/feats_kspon_other ;;
  fleurs) extract data/wave2a_lite/fleurs_test.jsonl data/wave2a_lite/feats_fleurs_test ;;
  both)
    extract data/wave2a_lite/kspon_eval_other.jsonl data/wave2a_lite/feats_kspon_other
    extract data/wave2a_lite/fleurs_test.jsonl data/wave2a_lite/feats_fleurs_test
    ;;
  *) echo "unknown: $WHICH" >&2; exit 2 ;;
esac
