# Wave 2B V2 — reader-only gate results

- Finished: 2026-11-05 13:10 KST
- Vocab: V2 1,329 chars (head 1,330)
- Primary candidate: **B3 V2, balanced sampler, 10h**
  - checkpoint: `data/wave2b/ckpt_v2/b3_v2_s42.best.pt`
  - sha256: `8349159e9b449ed4cd2f60e27fac4f955513423593ff34854772e90356e84328`
- Baseline: **B0′ V2, 6h**
  - checkpoint: `data/wave2b/ckpt_v2/b0p_v2_s42.best.pt`
  - sha256: `c869e66bf205bdf55596f2428aad3452ac813a68f9817bc4eeea77e6b4c27ddd`
- Sampler control: B3-nat V2, natural sampler, same 10h clip set
- Test was run once, after the candidate freeze in `test_freeze.json`.
- No threshold changes after seeing test.

## Dev 500

| Arm | Dev CER | Errors / chars |
|---|---:|---:|
| B0′ | 0.3701 | 2,870 / 7,755 |
| B3 | 0.2682 | 2,080 / 7,755 |
| B3-nat | 0.2633 | 2,042 / 7,755 |

| Comparison | Δ CER | paired 95% CI |
|---|---:|---:|
| B0′ − B3 | **+10.187%p** | **[+9.107, +11.328]** |
| B0′ − B3-nat | +10.677%p | [+9.624, +11.804] |
| B3 − B3-nat | +0.490%p | [−0.229, +1.205] |

The sampler difference is not significant (CI includes 0).

## Sealed test 2,400

Test features: `data/wave2b/feats_test_v2/`  
Decode: `reports/provenance/W2B/testpred_b0p_v2_s42.json`,
`testpred_b3_v2_s42.json`

| Arm | Test CER | Errors / chars | n |
|---|---:|---:|---:|
| B0′ | 0.359643 | 13,747 / 38,224 | 2,400 |
| B3 | **0.262270** | 10,025 / 38,224 | 2,400 |

- **Δ = +9.737%p**
- paired utterance bootstrap 95% CI **[+9.228, +10.258]%p**
  (20,000 resamples, seed 42)

## FLEURS dev guardrail

| Arm | FLEURS dev CER | Errors / chars |
|---|---:|---:|
| B0′ | 0.209770 | 1,649 / 7,861 |
| B3 | **0.207607** | 1,632 / 7,861 |

B3 is **−0.216%p** vs B0′; no regression (guardrail: ≤ +1.0%p).

## Gate decision

| Gate item | Requirement | Result |
|---|---|---|
| Dev Δ | ≥ 1.0%p and CI lower > 0 | **PASS** (+10.187%p, CI +9.107) |
| Test Δ | ≥ 1.0%p and CI lower > 0 | **PASS** (+9.737%p, CI +9.228) |
| FLEURS dev | no regression > +1.0%p | **PASS** (−0.216%p) |
| Test selection | one frozen candidate, no max | **PASS** (B3 frozen before test) |
| B3-nat sampler | reported separately | **no significant sampler effect** |

**V2 reader-only gate: PASS.**

## Interpretation

- The short 4h addition produces a large Kspon eval_clean gain under V2:
  dev +10.19%p, sealed test +9.74%p.
- The balanced vs natural sampler difference is small and not significant at
  12 epochs; the data effect is robust across both.
- V1 B0′ `0.3663` is **not** a V2 baseline and was not used for this gate.
- This is a reader-only result; B1/B2 LoRA remains conditional and was not run.
- 20-epoch extension remains deferred as D-070.

Raw bootstrap:
`reports/provenance/W2B/v2_dev_bootstrap.json`,
`reports/provenance/W2B/v2_test_bootstrap.json`
