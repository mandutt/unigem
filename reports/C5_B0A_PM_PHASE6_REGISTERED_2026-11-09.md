# C5 Phase 6 P/M — Registered 3-Seed Report

- 실행일: 2026-11-09
- 동결: `docs/plan_c5_b0a_pm_prereg_v1_0_11_FREEZE.json`
- 모드: `registered_3seed`
- seeds: **20261108 / 20261109 / 20261110**
- units: **12** (4 arms × 3 seeds), **100 updates/arm**, total **1,200 updates**
- 실행 방식: seed별 4-arm wave, 각 arm 2 threads, wave 순차
- wall estimate: **4,939.9s / 7,200s (82.3 / 120 min)** → `cap_ok:true`
- M records: **1,680**
- phase7 diagnostic: **7,200** (600/arm-seed)
- generation: **240** (20/unit)
- checkpoints: **12**
- `labels_computed`: **false** (decision/signal labels 미계산)
- test 163: **sealed**
- P1: **unused**
- T5Gemma2: **D-108 STOP**

## 1. Unit 결과

| arm | seed | loss first | loss last | step0 copy Δ | final copy Δ | step0 full Δ | final full Δ | EOS/20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| F | 20261108 | 27.44 | 6.49 | -0.5391 | -0.0582 | -0.5164 | -0.0515 | 0 |
| L | 20261108 | 27.44 | 6.58 | -0.5391 | -0.0374 | -0.5164 | -0.0349 | 0 |
| P | 20261108 | 11.74 | 12.39 | 7.0555 | 2.7155 | 7.1471 | 2.4995 | 2 |
| PA | 20261108 | 21.81 | 6.79 | -0.1407 | 0.0312 | 0.1083 | 0.0196 | 0 |
| F | 20261109 | 21.68 | 7.24 | -0.3177 | 0.0392 | -0.3139 | 0.0377 | 0 |
| L | 20261109 | 21.68 | 6.78 | -0.3177 | -0.0120 | -0.3139 | -0.0045 | 0 |
| P | 20261109 | 11.74 | 14.70 | 7.0555 | 2.8848 | 7.1471 | 2.6442 | 1 |
| PA | 20261109 | 29.50 | 6.66 | -1.0710 | 0.0057 | -0.8813 | 0.0232 | 0 |
| F | 20261110 | 36.98 | 6.68 | -0.3503 | 0.0195 | -0.3935 | 0.0160 | 0 |
| L | 20261110 | 36.98 | 6.78 | -0.3503 | -0.0171 | -0.3935 | -0.0108 | 0 |
| P | 20261110 | 11.74 | 11.72 | 7.0555 | 2.6905 | 7.1471 | 2.4482 | 3 |
| PA | 20261110 | 36.35 | 6.75 | 0.7163 | -0.0022 | 0.8082 | -0.0042 | 0 |

- F/L의 donor-crop signal Δ는 final에서 **0 근처**입니다.
- P는 native encoder 경로이며 절대 CE를 F/L과 직접 비교하지 않습니다.
- generation은 telemetry이며 gate가 아닙니다.

## 2. M primary — 1,680 records

- F/L: 15 common ×2 variants×2 memory_kinds×2 endpoints = **120/unit**.
- P/PA: 20 native ×2×2×2 = **160/unit**.
- `delta = control CE - real CE`; seed-average before bootstrap; 1,000 resamples, PCG64 seed 20261109.

| arm | variant | endpoint | mean Δ | 95% CI | docs | pass |
|---|---|---|---:|---|---:|---|
| F | M_POS_MEAN | copy | 0.548 | [0.487, 0.623] | 15 | true |
| F | M_POS_MEAN | full | 0.576 | [0.522, 0.644] | 15 | true |
| F | M_NORM | copy | 0.548 | [0.487, 0.622] | 15 | true |
| F | M_NORM | full | 0.576 | [0.522, 0.644] | 15 | true |
| L | M_POS_MEAN | copy | 0.367 | [0.313, 0.427] | 15 | true |
| L | M_POS_MEAN | full | 0.365 | [0.312, 0.423] | 15 | true |
| L | M_NORM | copy | 0.379 | [0.324, 0.439] | 15 | true |
| L | M_NORM | full | 0.378 | [0.324, 0.436] | 15 | true |
| P | M_POS_MEAN | copy | 6.327 | [4.249, 8.533] | 20 | true |
| P | M_POS_MEAN | full | 6.118 | [3.913, 8.644] | 20 | true |
| P | M_NORM | copy | 6.168 | [4.787, 7.820] | 20 | true |
| P | M_NORM | full | 5.774 | [4.387, 7.509] | 20 | true |
| PA | M_POS_MEAN | copy | 0.586 | [0.563, 0.615] | 20 | true |
| PA | M_POS_MEAN | full | 0.576 | [0.554, 0.601] | 20 | true |
| PA | M_NORM | copy | 0.660 | [0.637, 0.689] | 20 | true |
| PA | M_NORM | full | 0.672 | [0.644, 0.700] | 20 | true |

- **M_PASS_POS**: F/L/P/PA 모두 true.
- **M_PASS_NORM**: F/L/P/PA 모두 true.
- **m_pass_l**: **true**.
- 이는 M control 대비 real memory의 CE 우위이며, signal/L gate 또는 B0-B 승인이 아닙니다.

## 3. Artifacts

| 경로 | 내용 |
|---|---|
| `reports/provenance/C5_b0a/registered/registered_report.json` | 12-unit 요약 + M summary |
| `reports/provenance/C5_b0a/registered/registered_m_records.json` | 1,680 M records |
| `reports/provenance/C5_b0a/registered/units/{arm}_{seed}.json` | 12 unit reports |
| `reports/provenance/C5_b0a/phase7_records/{arm}/{seed}.json` | 600/unit, 7,200 |
| `reports/provenance/C5_b0a/control_manifest/control_manifest_registered.json` | 12 arms/seeds |
| `reports/provenance/C5_b0a/final_checkpoint_hash.json` | 12 keys |
| `reports/provenance/C5_b0a/checkpoints/{arm}/{seed}.pt` | 12 checkpoints |

## 4. 경계

```text
registered 3-seed = 완료
decision/signal labels = 미계산
B0-B = 미승인
B1/B2/Stage C = 미승인
test 163 = sealed
P1 = unused
T5Gemma2 = D-108 STOP
```

- `M_PASS`는 M endpoint의 control-vs-real 비교입니다.
- signal/L_SIGNAL, n_signal, tail_driven, m_valid는 **아직 계산하지 않았습니다**.
- 따라서 이 보고서는 **B0-B 판정이 아닙니다**.
