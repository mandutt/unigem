#!/usr/bin/env bash
set -u
REPO=$(git rev-parse --show-toplevel)
cd "$REPO"
ROUND="docs/hoplite/w2b_domain_length"
HOP="C:/Users/mandu/hermes-made/hoplite-advisor/hoplite_cli.py"
export HOPLITE_SERVICE_KEY=$(powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('HOPLITE_SERVICE_KEY','User')" | tr -d '\r')
if [ ${#HOPLITE_SERVICE_KEY} -lt 20 ]; then
  echo "KEY_MISSING" >&2
  exit 3
fi
mkdir -p "$ROUND"
for f in glm opus luna; do
  [ -s "$ROUND/prompts/$f.txt" ] || { echo "PROMPT_MISSING $f" >&2; exit 4; }
done
start_one() {
  local tag="$1" model="$2" reasoning="$3"
  (
    timeout 590 .venv/Scripts/python.exe "$HOP" ask "$(cat "$ROUND/prompts/$tag.txt")" \
      --model "$model" --reasoning "$reasoning" \
      --project proj_2e8de5ed594f47c7b851f1d7c5b52c61 \
      --timeout 570 \
      > "$ROUND/w2b_domain_length_$tag.out" 2> "$ROUND/w2b_domain_length_$tag.err"
  ) &
}
start_one glm z-ai/glm-5.3-flash max
sleep 10
start_one opus claude-opus-5-5 medium
sleep 10
start_one luna gpt-6-luna xhigh
wait
echo "DISPATCH_DONE"
