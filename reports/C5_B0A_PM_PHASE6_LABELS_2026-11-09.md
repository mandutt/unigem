# C5 Phase 6 P/M — Label / Replay Report

- 계산일: 2026-11-09
- 입력: registered 3-seed artifacts (`20261108/09/10`)
- 추가 학습: **없음**
- test 163: **sealed**
- P1: **unused**
- replay: **12/12 pass**, `atol=1e-5`, `rtol=1e-4`
- label: `labels_computed:true`

## 1. Replay

| 항목 | 결과 |
|---|---|
| units replay | **12/12** |
| M records | **1,680** key/numeric OK |
| phase7 records | **7,200** key/numeric OK |
| `replay_ok` | **true** |

## 2. Signal — L arm

| predicate | mean Δ | 95% CI | paired L>F | seeds >0 | value |
|---|---:|---|---:|---:|---|
| `L_COPY_SIGNAL` | -0.1135 | [-0.2341, -0.0012] | -0.0026 | 0/3 | **false** |
| `L_FULL_SIGNAL` | -0.1085 | [-0.2234, -0.0057] | -0.0009 | 0/3 | **false** |

- `l_signal = false`
- `copy_only = false`
- `full_only = false`
- `n_signal = 15`
- 실질적으로 real memory가 wrong-donor memory보다 낫지 않았습니다.

## 3. Signal tail

| 항목 | 값 |
|---|---:|
| top3_abs_share | **0.4775** |
| top3_signed_share | 0.8035 |
| leave_top3_mean | **-0.0279** |
| top3 IDs | `REPORT-news_r-01518-00001`, `REPORT-news_r-00020-00001`, `REPORT-news_r-01951-00001` |
| `tail_driven` | **true** |

- `top3_abs_share`는 .50 미만이지만 `leave_top3_mean <= 0`이므로 tail gate는 **true**입니다.
- hard B0-B gate는 signal tail만 사용합니다.

## 4. M / validity / control

| 항목 | 값 |
|---|---|
| `endpoint_ok` | true |
| `cohort_ok` | true |
| `seed_ok` | true |
| `replay_ok` | true |
| `builder_ok` | true |
| `m_evaluable` | **true** |
| `M_PASS_POS` | F/L/P/PA true |
| `M_PASS_NORM` | F/L/P/PA true |
| `m_pass_l` | **true** |
| `m_valid` | **true** |
| `validity_status` | **VALID** |
| `control_status` | **M_CONTROL_PASS** |
| `signal_status` | **MEAN_CONTRAST_ONLY** |
| `b0_b_candidate_gate` | **false** |

## 5. B0-B candidate

```text
validity_status == VALID                      true
control_status == M_CONTROL_PASS              true
signal_status == EXPLORATORY_L_SIGNAL         false  (MEAN_CONTRAST_ONLY)
m_valid == true                               true
n_signal >= 15                                true (15)
tail_driven == false                          false  (true)
leakage/mode/metric pass                      local checks true
artifact complete                             true
separate prereg/approval                      not requested
```

- **B0-B candidate gate: false**
- 주된 실패 사유: **L signal false**, **tail_driven true**
- M control 통과는 **content-use signal 또는 B0-B 승인이 아닙니다**.

## 6. Artifacts

| 경로 | 내용 |
|---|---|
| `reports/provenance/C5_b0a/labels/labels.json` | label/gate 결과 |
| `reports/provenance/C5_b0a/labels/replay_report.json` | 12-unit replay |
| `reports/provenance/C5_b0a/replay/{arm}_{seed}.json` | unit replay |
| `runner/c5_pm_labels.py` | pure tri-state decision module |
| `eval/tests/test_c5_pm_labels.py` | 8 label tests |
| `reports/provenance/C5_b0a/phase6_artifact_registry.json` | registry |

## 7. 경계

```text
B0-B = 미승인 (candidate gate false)
B1/B2/Stage C = 미승인
test 163 = sealed
P1 = unused
T5Gemma2 = D-108 STOP
```

- 이 보고서는 B0-B 승인이 아닙니다.
- B0-B를 재시도하려면 **새 prereg/승인**이 필요합니다.
- 결과 후 threshold/seed/donor/step/LR 변경 금지.
