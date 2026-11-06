#!/usr/bin/env bash
set -u

ROOT="C:/code/unigem"
CLI="C:/Users/mandu/hermes-made/hoplite-advisor/hoplite_cli.py"
PROJECT="proj_2e8de5ed594f47c7b851f1d7c5b52c61"
OUTDIR="$ROOT/docs/hoplite/c5_a1_2026-11-06"
cd "$ROOT" || exit 1

if [ -z "${HOPLITE_SERVICE_KEY:-}" ] || [ "${#HOPLITE_SERVICE_KEY}" -lt 20 ]; then
  echo "HOPLITE_SERVICE_KEY missing" >&2
  exit 3
fi

send_one() {
  local tag="$1" model="$2" reasoning="$3" prompt="$4"
  (timeout 590 python "$CLI" ask "$(cat "$prompt")" \
      --project "$PROJECT" \
      --model "$model" \
      --reasoning "$reasoning" \
      --timeout 570 \
      > "$OUTDIR/${tag}.out" 2> "$OUTDIR/${tag}.err") &
}

send_one glm  "z-ai/glm-5.3-flash" max    "$OUTDIR/prompt_glm.txt"
sleep 10
send_one opus "claude-opus-5-5"   medium "$OUTDIR/prompt_opus.txt"
sleep 10
send_one sol  "gpt-6.1-sol"       xhigh  "$OUTDIR/prompt_sol.txt"
wait
echo "DISPATCH_DONE"
