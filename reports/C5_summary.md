# C5 — F5 메모리 요약: target 감사 · repair/filter · A0 baseline

- 작성: 2026-11-06
- 상태: **CP3-1 완료 (grounding 기준 채택, clean 1,617 primary), 사람 검토 대기**
- 범위: P0 F5 데이터만 사용. JEV/메모리 코어 미수정.
- 원본: `data/external/f5_pairs_v3.jsonl` (2,000쌍, 변경 없음)

## 1. CP3-1 결정

G-C5의 `슬롯 보존`은 **grounding rate**로 확정한다.

- **grounding rate** = 요약에 등장한 슬롯이 원문에 존재하는 비율 (환각 통제)
- **원문 대비 coverage** = 원문 슬롯이 요약에 남은 비율 (정보 손실 참고 지표)
- 게이트: **grounding ≥99%, 신규 슬롯 ≤1%**, 검증기 통과분의 신규 슬롯 0
- 원문 대비 coverage는 뉴스 요약의 숫자 생략 때문에 게이트로 쓰지 않는다.

## 2. Target 감사

| 데이터 | n | 원문 슬롯 | 요약 슬롯 | 원문 대비 coverage | grounding | 신규 슬롯률 |
|---|---:|---:|---:|---:|---:|---:|
| 원본 v3 | 2,000 | 28,252 | 14,454 | 47.6922% | 93.2199% | **6.7801%** (980) |
| **clean (filter)** | **1,617** | 19,934 | 10,174 | 51.0384% | **100%** | **0** |
| repaired (secondary) | 1,953 | 26,831 | 11,864 | 44.2175% | **100%** | **0** |

- 원본 target은 신규 슬롯 6.78%로 G-C5 ≤1%를 위반했다.
- **clean**: 신규 슬롯이 있는 383건을 제외한 1,617건. target 문장을 수정하지 않아 보존적이다.
- **repaired**: 336건은 신규 슬롯이 포함된 문장만 제거(총 525문장), 47건은 2문장 미만이 되어 제외. 데이터는 늘지만 요약 품질·coverage 손실 위험이 있어 **secondary**로만 둔다.
- repaired의 원문 대비 coverage가 clean보다 낮아진 이유는 신규 슬롯 문장을 지우면서 원문 슬롯도 함께 사라졌기 때문이다.

## 3. A0 추출형 baseline

A0는 디코더 없이 문장을 선택하는 추출형 baseline이다. `max_sentences=4`, `max_chars=500`.

| 데이터 | test n | strict reject | grounding reject | 원문 대비 coverage 평균 | 신규 슬롯률 평균 | 압축률 | char F1(target 대비) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 원본 v3 | 200 | 152 (76.00%) | 1 (0.50%) | 0.7462 | 0.0004 | 0.2450 | 0.5962 |
| **clean** | **163** | 119 (73.01%) | **1 (0.61%)** | 0.7740 | 0.00038 | 0.2496 | **0.6074** |
| repaired | 196 | 158 (80.61%) | 0 (0.00%) | 0.7433 | 0.0000 | 0.2620 | 0.6060 |

**해석**

- A0는 추출형이라 **신규 슬롯(환각)이 거의 0**이다. clean test에서 163건 중 1건만 grounding reject.
- clean test의 신규 슬롯률 평균은 0.0383%로 ≤1%를 만족하지만, **검증기 통과분 0** 조건은 1건 때문에 엄밀히는 미충족이다.
- strict reject 73.01%는 원문의 모든 숫자를 보존하지 못해서다. grounding 기준에서는 게이트가 아니다.
- char F1 0.6074는 target 대비 참고치이며, ROUGE 단독 판정이 아니다.
- A0는 **추상 요약기가 아니며**, 최종 F5 후보가 아니라 기준선이다.

## 4. 데이터 선택

**primary = clean 1,617쌍.**

- 이유: target 문장을 변형하지 않아 사람이 검토한 원문 요약 품질을 보존한다.
- split: train 1,293 / val 161 / test 163, seed 42 deterministic.
- repaired 1,953쌍은 **민감도 분석용**으로만 보존한다. 학습 primary로 쓰려면 별도 승인과 사람 검토가 필요하다.

## 5. 산출물

- `data/external/f5_pairs_v3_clean.jsonl` — **primary 1,617**
- `data/external/f5_pairs_v3_grounded.jsonl` — repaired 포함 1,953
- `data/external/f5_pairs_v3_grounded_rejected.jsonl` — 47
- `reports/provenance/C5/target_slot_audit.json` — 원본 감사
- `reports/provenance/C5/repair_report.json` — repair/filter 원장
- `reports/provenance/C5_clean/{splits,target_slot_audit,a0_eval}.json`
- `reports/provenance/C5_grounded/{splits,target_slot_audit,a0_eval}.json`
- `reports/C5_summary_clean.md`, `reports/C5_summary_grounded.md`
- `reports/C5_summary_clean_review.html` — 사람 검토 50건

## 6. 판정과 다음

| 항목 | 상태 |
|---|---|
| G-C5 target grounding | **PASS** (clean: 100%, 신규 0) |
| G-C5 A0 | **경계** — 신규 슬롯률 0.0383%이나 위반 1/163 |
| 사람 표본 50 | **대기** (`reports/C5_summary_clean_review.html`) |
| C3 A1 T5Gemma 2 LoRA | **미착수, 별도 승인 필요** |

1. clean 50건을 사람이 검토해 핵심 사실·과압축·누락을 확인한다.
2. A0를 기준선으로 채택할지 CP3-2에서 결정한다.
3. 추상 요약이 필요하면 C3 A1을 별도 사전등록 후 진행한다.
4. repaired 데이터는 primary로 쓰지 않는다.
