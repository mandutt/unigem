#!/usr/bin/env bash
set -u

ROOT="C:/code/unigem"
CLI="C:/Users/mandu/hermes-made/hoplite-advisor/hoplite_cli.py"
PROJECT="proj_2e8de5ed594f47c7b851f1d7c5b52c61"
OUTDIR="$ROOT/docs/hoplite/c5_b0a_2026-11-09"
cd "$ROOT" || exit 1

if [ -z "${HOPLITE_SERVICE_KEY:-}" ] || [ "${#HOPLITE_SERVICE_KEY}" -lt 20 ]; then
  export HOPLITE_SERVICE_KEY=$(powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('HOPLITE_SERVICE_KEY','User')" | tr -d '\r')
fi
if [ -z "${HOPLITE_SERVICE_KEY:-}" ] || [ "${#HOPLITE_SERVICE_KEY}" -lt 20 ]; then
  echo "HOPLITE_SERVICE_KEY missing" >&2
  exit 3
fi

for f in prompt_glm.txt prompt_sonnet.txt prompt_sol.txt; do
  if [ ! -s "$OUTDIR/$f" ] || [ "$(wc -c < "$OUTDIR/$f")" -lt 1000 ]; then
    echo "prompt missing or too small: $f" >&2
    exit 1
  fi
done

send_one() {
  local tag="$1" model="$2" reasoning="$3" prompt="$4"
  (timeout 590 python "$CLI" ask "$(cat "$prompt")" \
      --project "$PROJECT" \
      --model "$model" \
      --reasoning "$reasoning" \
      --timeout 570 \
      > "$OUTDIR/${tag}.out" 2> "$OUTDIR/${tag}.err") &
}

send_one glm    "z-ai/glm-5.3-flash" max  "$OUTDIR/prompt_glm.txt"
sleep 10
send_one sonnet "claude-sonnet-5-5"  high "$OUTDIR/prompt_sonnet.txt"
sleep 10
send_one sol    "gpt-6.1-sol"        high "$OUTDIR/prompt_sol.txt"
wait
echo "DISPATCH_DONE"
