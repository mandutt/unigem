# C5 F0.4 — Fresh-Seed Directional Adapter Confirmation (Prereg v0.1, DRAFT)

- 작성일: 2026-11-10
- 상태: **DRAFT — 승인 전 코드·실행 금지**
- 근거: F0.2 `E11 copy signal +0.1152`, `E01 non-signal`; F0.3 `E10 adapter-only signal +0.1382`
- 목적: **fresh seeds**에서 `E11 − E01` copy benefit direction을 confirmatory하게 검정

## 1. 중요 한계

- 동일한 15 length-eligible docs와 fixed donor graph를 사용한다.
- 따라서 fresh seeds는 **initialization/training replication**이지 population replication이 아니다.
- F0.2와 같은 cohort를 재사용하므로 external validation이 아니다.
- F0.2/F0.3 label을 변경하지 않는다.

## 2. Conditions

| cell | adapter | LoRA | updates | LoRA LR | adapter LR |
|---|---|---|---:|---:|---:|
| E01 | none | 64 | 400 | 3e-4 | — |
| E11 | 512→512 | 64 | 400 | 3e-4 | 1e-3 |

- **fresh seeds**: `20261112`, `20261113`, `20261114`
- 2 cells × 3 seeds = **6 units**
- E00/E10 재실행 없음
- no M/phase7/generation

## 3. Fit gate

```text
fit_ratio = loss_last / loss_first
fit_pass = fit_ratio <= 0.35
```

- E01/E11 × 3 seeds 모두 pass해야 한다.
- 하나라도 실패 → `NOT_EVALUABLE_OPTIMIZATION`; signal을 읽지 않는다.

## 4. Primary endpoint

```text
D(d) = delta_E11(d, copy) − delta_E01(d, copy)
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)
```

- 15 common docs, 5 donors, final checkpoint
- `SIGNAL(E11,copy)` = mean ≥ .05 AND CI.lower > 0 AND 2/3 seeds > 0
- `BENEFIT_POSITIVE` =
  `mean_D >= .05` AND `CI_D.lower > 0` AND `SIGNAL(E11,copy)` AND `2/3 seed D_s > 0`
- `EQUIVALENT` = 95% CI_D entirely within [−.05,+.05]
- `NO_BENEFIT` = otherwise (including null/uncertain)
- full endpoint secondary only; not part of BENEFIT_POSITIVE

## 5. Decision semantics

- This is a **directional benefit confirmation**, not a two-sided adapter-null test.
- `BENEFIT_POSITIVE` supports the directional adapter-benefit hypothesis.
- `EQUIVALENT`/`NO_BENEFIT` do not prove adapter null; report as no directional confirmation.
- No H3/B0-B/EG2 track decision.
- No post-hoc threshold/seed changes.

## 6. Compute

- 6 units, 4 worker slots, 400 updates/unit
- cap **60분**
- unit 완료 즉시 flush

## 7. Artifacts

```text
reports/provenance/C5_f0_4/
  freeze.json
  summary.json
  units/{E01,E11}_{seed}.json
  labels.json
```

## 8. Approval

승인 후:

1. `runner/c5_pm_f0_4_confirm.py` + tests
2. freeze
3. 6 units 실행
4. fit gate → BENEFIT_POSITIVE/EQUIVALENT/NO_BENEFIT 보고
