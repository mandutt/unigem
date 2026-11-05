# STT 문서 색인

- 최종 갱신: 2026-11-06
- 상태: **FROZEN / HOLD** (D-079)
- 진입점: [`README.md`](README.md) · [`STATUS.md`](STATUS.md)

## 1. 설계·계획

| 문서 | 내용 |
|---|---|
| [`plans/plan_wave2a.md`](plans/plan_wave2a.md) | Wave 2A 설계 |
| [`plans/plan_wave2a_lite.md`](plans/plan_wave2a_lite.md) | Wave 2A-lite 4-arm 설계 |
| [`plans/plan_wave2b_2c_short.md`](plans/plan_wave2b_2c_short.md) | Wave 2B/2C-short v1 (이력) |
| [`plans/plan_wave2b_2c_short_v2.md`](plans/plan_wave2b_2c_short_v2.md) | Wave 2B/2C-short v2 (이력) |
| [`plans/plan_wave2b_2c_short_v3.md`](plans/plan_wave2b_2c_short_v3.md) | Wave 2B/2C-short v3 **정본** |

## 2. 기반·비교 보고서

| 문서 | 내용 |
|---|---|
| [`reports/C2_A0_notesoop.md`](reports/C2_A0_notesoop.md) | Notesoop 구조·특징 재현 분석 |
| [`reports/C2_A1_cer.md`](reports/C2_A1_cer.md) | Notesoop CER 기준선, G-C2 |
| [`reports/C8_c2a1_cer.md`](reports/C8_c2a1_cer.md) | Notesoop vs komixv2 vs whisper 비교 |
| [`reports/G_C2a.md`](reports/G_C2a.md) | Q8 feature 호환성 |
| [`reports/D5_beta_setup.md`](reports/D5_beta_setup.md) | D-β 실험 셋업 |
| [`reports/D5_beta_pilot.md`](reports/D5_beta_pilot.md) | D-β 4-arm 결과, Sténo 비교 |

## 3. Wave 2A-lite

| 문서 | 내용 |
|---|---|
| [`reports/W2A_lite_prep.md`](reports/W2A_lite_prep.md) | 데이터·preflight |
| [`reports/W2A_lite_results.md`](reports/W2A_lite_results.md) | 4-arm 결과 |
| [`reports/W2A_lite_cp_d2_lite.md`](reports/W2A_lite_cp_d2_lite.md) | CP-D2-lite 분석 |
| [`reports/W2A_lite_vps_steal.md`](reports/W2A_lite_vps_steal.md) | VPS steal 영향 |
| `reports/W2A_lite_*.json` | arm별 dev/test 지표 JSON |

## 4. Wave 2B/2C-short

### 데이터·preflight

| 문서 | 내용 |
|---|---|
| [`reports/W2B_data_ready.md`](reports/W2B_data_ready.md) | V1 데이터 준비 |
| [`reports/W2B_v2_data_ready.md`](reports/W2B_v2_data_ready.md) | V2 데이터·vocab |
| [`reports/W2B_preflight.md`](reports/W2B_preflight.md) | split·OOV preflight |
| [`reports/W2B_preflight_addendum.md`](reports/W2B_preflight_addendum.md) | preflight 보강 |
| [`reports/W2B_split_audit.md`](reports/W2B_split_audit.md) | split 감사 |
| [`reports/W2B_2C_SHORT_3AI_SYNTHESIS.md`](reports/W2B_2C_SHORT_3AI_SYNTHESIS.md) | Wave 2B/2C-short v1 3-AI 종합 |
| [`reports/W2B_2C_SHORT_V2_3AI_SYNTHESIS.md`](reports/W2B_2C_SHORT_V2_3AI_SYNTHESIS.md) | Wave 2B/2C-short v2 3-AI 종합 |

### Reader-only arms

| 문서 | 내용 |
|---|---|
| [`reports/W2B_b0p.md`](reports/W2B_b0p.md) | B0′ V1 |
| [`reports/W2B_b0p_v2.md`](reports/W2B_b0p_v2.md) | B0′ V2 |
| [`reports/W2B_b3_v2.md`](reports/W2B_b3_v2.md) | B3 V2 |
| [`reports/W2B_v2_dev_results.md`](reports/W2B_v2_dev_results.md) | V2 dev 결과 |
| [`reports/W2B_v2_gate_results.md`](reports/W2B_v2_gate_results.md) | V2 gate·sealed test |
| [`reports/W2B_V2_GATE_3AI_SYNTHESIS.md`](reports/W2B_V2_GATE_3AI_SYNTHESIS.md) | V2 gate 3-AI 종합 |

### Matched-budget controls

| 문서 | 내용 |
|---|---|
| [`reports/W2B_b0_matched_controls_plan.md`](reports/W2B_b0_matched_controls_plan.md) | B0′-20/38 사전등록 |
| [`reports/W2B_b0_matched_controls.md`](reports/W2B_b0_matched_controls.md) | 결과 |

### Domain/length controls

| 문서 | 내용 |
|---|---|
| [`reports/W2B_domain_length_controls_plan.md`](reports/W2B_domain_length_controls_plan.md) | 사전등록 |
| [`reports/W2B_domain_length_controls.md`](reports/W2B_domain_length_controls.md) | 결과 |
| [`reports/W2B_DOMAIN_LENGTH_3AI_SYNTHESIS.md`](reports/W2B_DOMAIN_LENGTH_3AI_SYNTHESIS.md) | 3-AI 종합 |

### Step-matched B3-long

| 문서 | 내용 |
|---|---|
| [`reports/W2B_b3long_stepmatched_plan.md`](reports/W2B_b3long_stepmatched_plan.md) | D-077 사전등록 |
| [`reports/W2B_b3long_stepmatched.md`](reports/W2B_b3long_stepmatched.md) | D-078 결과 |

### 3-AI 검토 요청서

| 문서 | 내용 |
|---|---|
| [`reports/EXTERNAL_REVIEW_W2B_2C_SHORT_2026-11-04.md`](reports/EXTERNAL_REVIEW_W2B_2C_SHORT_2026-11-04.md) | v1 검토 요청 |
| [`reports/EXTERNAL_REVIEW_W2B_2C_SHORT_V2_2026-11-04.md`](reports/EXTERNAL_REVIEW_W2B_2C_SHORT_V2_2026-11-04.md) | v2 검토 요청 |
| [`reports/EXTERNAL_REVIEW_W2B_V2_GATE_2026-11-05.md`](reports/EXTERNAL_REVIEW_W2B_V2_GATE_2026-11-05.md) | V2 gate 검토 요청 |
| [`reports/EXTERNAL_REVIEW_W2B_DOMAIN_LENGTH_2026-11-05.md`](reports/EXTERNAL_REVIEW_W2B_DOMAIN_LENGTH_2026-11-05.md) | domain/length 검토 요청 |
| [`reports/STT_LARGE_SCALE_TRAINING_ASSESSMENT_2026-11-05.md`](reports/STT_LARGE_SCALE_TRAINING_ASSESSMENT_2026-11-05.md) | **대규모 학습 타당성·동결 근거** |

## 5. Hoplite 3-AI 검토 원문

| 디렉터리 | 내용 |
|---|---|
| [`hoplite/v4/`](hoplite/v4/) | 4차 검토(3-AI 원문·종합·threads) |
| [`hoplite/w2b_2c_short/`](hoplite/w2b_2c_short/) | Wave 2B/2C-short v1 검토 |
| [`hoplite/w2b_2c_short_v2/`](hoplite/w2b_2c_short_v2/) | v2 검토 |
| [`hoplite/w2b_v2_gate/`](hoplite/w2b_v2_gate/) | V2 gate 검토 |
| [`hoplite/w2b_domain_length/`](hoplite/w2b_domain_length/) | domain/length 검토 |

각 디렉터리에 prompt·dispatch·watchdog·threads·원문이 포함된다.

## 6. Provenance·로그 (이동하지 않음)

| 위치 | 내용 |
|---|---|
| `reports/provenance/W2A_lite/` | 2A-lite 예측·freeze·test 원장 |
| `reports/provenance/W2B/` | V2 예측·bootstrap·test freeze·overlap·control 원장 |
| `reports/provenance/W1/` | D-β Wave 1 원장 |
| `logs/W2A_lite/`, `logs/W2B/` | 학습·decode·watchdog 로그 |
| `data/wave2b/ckpt_controls/` | control 체크포인트 |
| `data/wave2b/feats_*` | control feature cache (D-074b 보존) |

Provenance와 로그는 재현 근거이므로 **문서 폴더로 이동하지 않고 원래 위치에 보존**했다.

## 7. 전역 결정·리뷰

- [`../decisions.md`](../decisions.md) — D-057, D-067, D-069, D-071, D-073, D-075, D-076, D-077, D-078, **D-079(동결)**
- [`../gates.md`](../gates.md) — G-C2, G-C2a 등 STT gate
- [`../plan_v0_5.md`](../plan_v0_5.md) — 전체 프로젝트 계획(STT 외 트랙 포함)
- `../../reports/EXTERNAL_REVIEW_2026-11-03.md`, `../../reports/EXTERNAL_REVIEW_2026-11-04.md` — STT를 포함한 전역 리뷰(이동하지 않음)
- `../../reports/Addendum_C_review.md`, `../../reports/Addendum_D_review.md` — 전역 Addendum 리뷰(이동하지 않음)
