#!/usr/bin/env bash
set -u

ROOT="C:/code/unigem"
CLI="C:/Users/mandu/hermes-made/hoplite-advisor/hoplite_cli.py"
OUTDIR="$ROOT/docs/hoplite/c5_b0a_pm_prereg_v1_0_8_2026-11-09"
cd "$ROOT" || exit 1

if [ -z "${HOPLITE_SERVICE_KEY:-}" ] || [ "${#HOPLITE_SERVICE_KEY}" -lt 20 ]; then
  export HOPLITE_SERVICE_KEY=$(powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('HOPLITE_SERVICE_KEY','User')" | tr -d '\r')
fi
if [ -z "${HOPLITE_SERVICE_KEY:-}" ] || [ "${#HOPLITE_SERVICE_KEY}" -lt 20 ]; then
  echo "HOPLITE_SERVICE_KEY missing" >&2
  exit 3
fi

for f in fup_glm.txt fup_ds1017.txt fup_sol.txt; do
  if [ ! -s "$OUTDIR/$f" ] || [ "$(wc -c < "$OUTDIR/$f")" -lt 500 ]; then
    echo "prompt missing or too small: $f" >&2
    exit 1
  fi
done

# Same-thread continuation: no archive, no new ask.
(timeout 590 python "$CLI" fup thr_a757d209deae4493985cc2731c5af382 "$(cat "$OUTDIR/fup_glm.txt")" \
  --model "z-ai/glm-5.3-flash" --timeout 570 \
  > "$OUTDIR/glm_fup_v108.out" 2> "$OUTDIR/glm_fup_v108.err") &
sleep 10
(timeout 590 python "$CLI" fup thr_b142cc5df03c484ca20d06ba152279e9 "$(cat "$OUTDIR/fup_ds1017.txt")" \
  --model "deepseek-v4.1-flash-1017" --timeout 570 \
  > "$OUTDIR/ds1017_fup_v108.out" 2> "$OUTDIR/ds1017_fup_v108.err") &
sleep 10
(timeout 590 python "$CLI" fup thr_3e45b1e757c64204a065c84429d2abed "$(cat "$OUTDIR/fup_sol.txt")" \
  --model "gpt-6.1-sol" --timeout 570 \
  > "$OUTDIR/sol_fup_v108.out" 2> "$OUTDIR/sol_fup_v108.err") &
wait
echo "FUP_DISPATCH_DONE"
