# C5 Hybrid — D-086 workflow

## Status

- Protocol frozen before AI calls and human ratings.
- **AI panel calls: NOT_RUN**
- **Human calibration: NOT_RUN**
- **Human repeat: NOT_RUN**
- test 163: **SEALED**

## Files

- `reports/provenance/C5_hybrid/manifest.json` — 50-doc sample, 3 judge orders, 20-doc calibration, 5-doc repeat, gates
- `reports/provenance/C5_hybrid/ai_inputs/judge_{glm,sonnet,sol}.jsonl` — 50 prompts per judge, no arm names/metrics/targets
- `docs/D-086_hybrid_ai_human_protocol_2026-11-07.md` — protocol
- `runner/c5_hybrid_build_manifest.py`
- `runner/c5_hybrid_build_ai_inputs.py`

## AI panel

3 judges:

| judge | model | reasoning |
|---|---|---|
| glm | `z-ai/glm-5.3-flash` | max |
| sonnet | `claude-sonnet-5-5` | high |
| sol | `gpt-6.1-sol` | xhigh |

150 calls = 3 × 50 docs. Each call returns 4 ratings → 600 AI ratings.

- AI sees source + A–D summaries + rubric + schema.
- AI does **not** see target, arm names, metrics, human ratings, or other judges.
- Each judge has its own A–D order in `manifest.judge_arm_order`.

## Human calibration

- 20 docs × 4 arms = **80 ratings**
- 4 sessions × 5 docs
- BLIND: no AI outputs, no arm identity
- repeat: 5 docs × 4 arms = **20 ratings**, after ≥7 days
- total human: **100 ratings**

## Gates

- AI–human adequacy ICC(2,1) ≥ **0.70**
- AI–human adequacy QWK ≥ **0.60**
- Critical unsupported kappa ≥ **0.60**
- Critical omission kappa ≥ **0.60**
- Human repeat ICC ≥ **0.70**, QWK ≥ **0.60**
- AI inter-judge ICC ≥ **0.60**
- Contested rate ≤ **0.10**
- Primary margins: adequacy lower ≥ **−0.25**, critical upper < **+0.05**
- Any failure → **INCONCLUSIVE**, pilot300 fallback, no approved candidate, test 163 sealed

## Next steps

1. Dispatch 150 AI prompts (after explicit approval).
2. Validate/lock AI outputs.
3. Generate 20-doc human calibration sheet.
4. Collect human calibration + repeat.
5. Run agreement gates.
6. If gates pass, run AI-panel primary analysis.
