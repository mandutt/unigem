# Wave 2B V2 — reader-only dev results

- Finished: 2026-11-05 13:02 KST
- Vocab: V2, 1,329 chars (head 1,330)
- Init: character-remapped 2A reader, 1,101 shared chars
- Data: 10h cache = Wave 1 6h + V2 short 4h (7,463 clips, 10.0221h)
- Dev: Kspon eval_clean dev 500 (7,755 ref chars)
- Seed 42; 12 epochs; CPU; batch 2 / grad accumulation 4

## Results

| Arm | Sampler | Best epoch | Best dev CER | Errors / chars |
|---|---|---:|---:|---:|
| B0′ V2 | natural, 6h | 12 | **0.3701** | 2,870 / 7,755 |
| B3 V2 | balanced, 10h | 12 | **0.2682** | 2,080 / 7,755 |
| B3-nat V2 | natural, 10h | 11 | **0.2633** | 2,042 / 7,755 |

Point differences:

| Comparison | Δ CER | Interpretation |
|---|---:|---|
| B0′ − B3 | **+10.187%p** | short 10h data effect |
| B0′ − B3-nat | **+10.677%p** | short 10h data effect, natural sampler |
| B3 − B3-nat | **+0.490%p** | natural slightly better; not distinguishable |

Paired utterance bootstrap, 20,000 resamples, seed 42:

| Comparison | 95% CI |
|---|---:|
| B0′ − B3 | **[+9.107, +11.328]%p** |
| B0′ − B3-nat | **[+9.624, +11.804]%p** |
| B3 − B3-nat | **[-0.229, +1.205]%p** |

## Interpretation

- Both B3 and B3-nat clear the pre-registered full gate against B0′:
  **Δ ≥ 1.0%p and paired 95% CI lower bound > 0**.
- The B3/B3-nat difference is **not significant** (CI includes 0); the sampler
  effect is negligible at this data scale.
- B3 is the primary candidate under the registered rule; B3-nat is the sampler
  control. The test must use the frozen B3 checkpoint only.
- The 10%p gain is a short-domain effect on Kspon eval_clean dev; it does not
  replace the sealed test.

## Freeze

- Candidate: `data/wave2b/ckpt_v2/b3_v2_s42.best.pt`
- Baseline: `data/wave2b/ckpt_v2/b0p_v2_s42.best.pt`
- Test remains sealed until feature extraction and the one-shot test run.

Raw bootstrap: `reports/provenance/W2B/v2_dev_bootstrap.json`
