#!/usr/bin/env bash
set -u

REPO="$(git rev-parse --show-toplevel)"
cd "$REPO" || exit 1
DIR="docs/hoplite/v4"
CLI="C:/Users/mandu/hermes-made/hoplite-advisor/hoplite_cli.py"
PROJECT="proj_2e8de5ed594f47c7b851f1d7c5b52c61"

for f in "$DIR/prompt_GLM.txt" "$DIR/prompt_SONNET.txt" "$DIR/prompt_LUNA.txt"; do
  [ -s "$f" ] || { echo "missing prompt: $f" >&2; exit 1; }
done
[ ${#HOPLITE_SERVICE_KEY:-0} -ge 20 ] || { echo "HOPLITE_SERVICE_KEY missing" >&2; exit 3; }

[ -d "$DIR" ] || mkdir -p "$DIR"

run_one() {
  local tag="$1" model="$2" reasoning="$3" prompt="$4"
  (
    timeout 590 python "$CLI" ask "$(cat "$prompt")" \
      --project "$PROJECT" \
      --model "$model" \
      --reasoning "$reasoning" \
      --no-readonly \
      --timeout 570 \
      > "$DIR/v4_${tag}.out" 2> "$DIR/v4_${tag}.err"
    echo "EXIT $? $tag $(date -u +%FT%TZ)" >> "$DIR/dispatch_v4.status"
  ) &
}

: > "$DIR/dispatch_v4.status"
run_one glm    "z-ai/glm-5.3-flash" "max"    "$DIR/prompt_GLM.txt"
sleep 10
run_one sonnet "claude-sonnet-5-5"    "medium" "$DIR/prompt_SONNET.txt"
sleep 10
run_one luna   "gpt-6-luna"           "xhigh"  "$DIR/prompt_LUNA.txt"

echo "launched"
