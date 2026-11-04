#!/usr/bin/env bash
# Dispatch the w2b_2c_short review to GLM, Sonnet, and Luna.
set -u
REPO=$(git rev-parse --show-toplevel)
cd "$REPO"
D="docs/hoplite/w2b_2c_short"
P="$D/prompts"
CLI="C:/Users/mandu/hermes-made/hoplite-advisor/hoplite_cli.py"
PROJECT="proj_2e8de5ed594f47c7b851f1d7c5b52c61"
mkdir -p "$D"

export HOPLITE_API_KEY=$(powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('HOPLITE_API_KEY','User')" | tr -d '\r')
export HOPLITE_SERVICE_KEY=$(powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('HOPLITE_SERVICE_KEY','User')" | tr -d '\r')
[ ${#HOPLITE_API_KEY} -lt 20 ] && { echo "missing HOPLITE_API_KEY" >&2; exit 3; }
[ ${#HOPLITE_SERVICE_KEY} -lt 20 ] && { echo "missing HOPLITE_SERVICE_KEY" >&2; exit 3; }

for m in glm sonnet luna; do
  [ -s "$P/$m.txt" ] || { echo "missing prompt $P/$m.txt" >&2; exit 1; }
  [ "$(wc -c < "$P/$m.txt")" -ge 1000 ] || { echo "prompt too small $m" >&2; exit 1; }
done

# Thread creation: deliberately staggered 10s, each ask in its own subshell.
(timeout 590 python "$CLI" ask "$(cat "$P/glm.txt")" --project "$PROJECT" \
  --model z-ai/glm-5.3-flash --reasoning max --timeout 570 \
  > "$D/glm.out" 2> "$D/glm.err") &
sleep 10
(timeout 590 python "$CLI" ask "$(cat "$P/sonnet.txt")" --project "$PROJECT" \
  --model claude-sonnet-5-5 --reasoning medium --timeout 570 \
  > "$D/sonnet.out" 2> "$D/sonnet.err") &
sleep 10
(timeout 590 python "$CLI" ask "$(cat "$P/luna.txt")" --project "$PROJECT" \
  --model gpt-6-luna --reasoning xhigh --timeout 570 \
  > "$D/luna.out" 2> "$D/luna.err") &
wait
echo "DISPATCH_WAIT_DONE"
