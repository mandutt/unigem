# Wave 2A-lite — 최종 결과 (2026-11-04)

- 상태: **dev 4-arm + Kspon/FLEURS test 완료. 2B 미착수.**
- dev: FLEURS ko dev 192클립(≤16초), 참조 7,861자.
- 정규화: `normalize_nospace`.

## 1. Seed 42 dev CER

| Arm | CER | errors/ref | pred/ref | 비고 |
|---|---:|---:|---:|---|
| F-A′ | **0.22236** | 1,748 / 7,861 | 0.9875 | best epoch 16 부근 |
| F-B | **0.21931** | 1,724 / 7,861 | 0.9875 | best epoch 15 |
| F-C-softmax | **0.22211** | 1,746 / 7,861 | 0.9805 | best epoch 20 |
| F-C-concat | **0.20913** | 1,644 / 7,861 | 0.9791 | best epoch 18 |

## 2. Pairwise bootstrap (문장 단위, 10,000회, seed 42)

F-A′ 대비 개선량(양수 = F-A′보다 좋음):

| 비교 | 개선 | 95% CI | 판정 |
|---|---:|---|---|
| F-B − F-A′ | **+0.305%p** | **[-0.351, +0.954]%p** | CI가 0 포함 — 유의하지 않음 |
| F-C-softmax − F-A′ | +0.025%p | [-0.686, +0.748]%p | 유의하지 않음 |
| F-C-concat − F-A′ | **+1.323%p (상대 5.95%)** | **[+0.631, +2.028]%p** | CI 하한 > 0 — dev에서 유의 |

- F-C-concat은 dev에서 **상대 5.95% 개선**, paired bootstrap CI 하한 **+0.631%p**로 Go의 dev 조건을 충족했습니다.
- 단, 최종 Go는 seed43 재현과 1h overfit, 동결 후 Kspon eval_other 주 gate까지 확인해야 합니다.
- F-A′/F-B 차이는 0.3%p 수준으로 seed 42에서는 층 선택 우열을 말할 수 없습니다.

## 3. 오류 구성

| Arm | substitution | deletion | insertion |
|---|---:|---:|---:|
| F-A′ | 1,485 | 226 | 139 |
| F-B | 1,533 | 192 | 94 |
| F-C-concat | 1,480 | 127 | 53 |
| F-C-softmax | 1,564 | 189 | 57 |

## 3.1 fbank baseline

| 항목 | 결과 |
|---|---:|
| dev CER | **0.9812** |
| best epoch | 19 |
| 판정 | **실패** — blank plateau |

- log-mel 80 + CTC 최소 대조군이 학습되지 않았습니다. 특징 정규화/프레임 정렬/blank 붕괴 원인을 진단해야 합니다.
- 이 실패는 arm 비교를 중단할 사유는 아니며(4-arm은 정상 수렴), fbank baseline 자체의 구현 문제로 기록합니다.

## 4. Vocab coverage

- dev 참조 7,861자 중 미포함 **49자(0.62%)**, 192문장 중 154문장은 전부 포함.
- `vocab_oracle`(미포함 문자를 양쪽에서 제거한 진단): F-A′ 0.21947, F-B 0.21656, F-C-concat 0.20725 — **모델 결과 아님**.

## 4.1 Seed 43

| Arm | best dev CER | 상태 |
|---|---:|---|
| F-A′ seed43 | **0.2233** | 완료 |
| F-B seed43 | **0.2185** | 완료 |
| F-C-concat seed43 | **0.208116** | 완료·5% 이상 재현 |

## 4.2 Go/No-Go — dev 판정

- **F-C-concat seed42**: F-A′ 대비 상대 **5.95%** 개선, paired bootstrap 95% CI 하한 **+0.631%p** > 0.
- **F-C-concat seed43**: seed43 F-A′ 0.2233 대비 **6.8%** 개선으로 재현.
- **1h overfit positive control**: `pc_fa20n` train=dev 1h subset, epoch 7 CER **0.1161** → PASS.
- 따라서 **dev 기준 Go 조건은 충족**했다. 단, 최종 Go는 동결 후 **Kspon eval_other 주 gate** 결과를 포함해 판정한다.
- seed42를 test에 사용하는 이유: seed42가 사전등록 주 seed이고, seed43은 재현용이다. dev에서 더 좋은 seed를 골라 test에 쓰는 selection bias를 피한다.

## 5. 다음

- Kspon eval_other(2,963 ≤16s) 특징 추출·동결 체크포인트 1회 평가
- FLEURS test 382 1회 평가
- 최종 Go/No-Go·D-065 기록

## 6. 최종 test (동결 체크포인트)

동결 checkpoint: `data/wave2a_lite/frozen/w2a_fc_concat_s42.best.pt`
SHA-256: `258f6ddf84b3f41afc0e88f832946229b3a1319d28cec11cd4a0da40951cb23d`

### 6.1 Kspon eval_other (주 gate)

| 항목 | 결과 |
|---|---:|
| 평가 발화 | **2,962 / 3,000** (≤16s, 1건 특징 skip) |
| CER | **0.35143** |
| errors/ref | 23,508 / 66,893 |
| prediction/ref 길이비 | 0.9279 |
| blank | **0 / 2,962** |
| taxonomy | substitution 19,816 / deletion 3,309 / insertion 1,157 |
| vocab coverage | 99.43% (378자 miss) |

- 전사 정리·`normalize_nospace`는 사전등록 규칙 그대로 적용했습니다.
- D-β Kspon eval_clean 100의 F-A′ **0.3939**와 직접 비교하지 않습니다(다른 split·다른 표본). 참고 수치로만 둡니다.

### 6.2 FLEURS ko test (비교용)

| 항목 | 결과 |
|---|---:|
| 평가 발화 | **318 / 382** (≤16s) |
| CER | **0.23509** |
| errors/ref | 3,126 / 13,297 |
| prediction/ref 길이비 | 0.9669 |
| blank | **0 / 318** |
| taxonomy | substitution 2,697 / deletion 359 / insertion 114 |

- FLEURS test는 **benchmark comparison**이며 gate 판정에 쓰지 않습니다.
- Notesoop/komix/whisper 수치는 **WER**이고 우리 결과는 **CER**이므로 직접 비교하지 않습니다. WER은 공백 없는 예측이라 **미산출**입니다.

## 7. 판정

- **dev Go 조건:** F-C-concat seed42가 F-A′ 대비 **상대 5.95%** 개선, paired bootstrap 95% CI 하한 **+0.631%p** > 0, 1h overfit PASS → **충족**.
- **seed43 재현:** F-C-concat seed43 **0.208116**, seed43 F-A′ 0.2233 대비 **6.8%** 개선 → **재현**.
- **Kspon eval_other:** CER **0.35143**. 사전등록된 절대 threshold는 없으며, 최종 판정에는 이 수치를 gate 결과로 함께 기록합니다.
- **잠정 결론:** **Go (Wave 2B 후보)**. 단, 2B 착수는 CP 경계 승인 후 진행합니다. 자동 착수하지 않습니다.
- **No-Go 시:** CP-D2에서 구현/vocab/seed·데이터·동결 타워 원인을 진단합니다.

## 8. AM-6 이행

| 요구 | 이행 |
|---|---|
| FLEURS ko dev | 이행 |
| Kspon eval_other 봉인 test | 이행 (2,962평가) |
| FLEURS test 비교 1회 | 이행 (318평가) |
| 4-arm 동일 조건 | 이행 |
| F-C softmax + concat comparator | 이행 |
| seed 반복 | seed42 + seed43 |
| positive control 1h overfit | PASS (0.1161) |
| per-domain/error/blank/vocab/fbank | taxonomy·blank·vocab oracle·fbank 보고 |
| WER/공백 포함 CER | **미산출** (예측 공백 없음) |
| 13-state/wordpiece/40h/LoRA | 미이행(후속) |

## 9. CP-D2-lite — Kspon 35.14% 분해

- 추가 test 평가 없이 기존 decode/manifest만 분석: `docs/STT/reports/W2A_lite_cp_d2_lite.md`
- **오류는 outlier가 아님**: 상위 1% 발화가 전체 오류의 4.2%, 상위 5%가 15.5%.
- **길이 분포 불일치가 주축**: train ≤4초 **4.1%** vs Kspon eval_other ≤4초 **57.2%**.
- Kspon CER: 0–2초 **46.4%** → 12–16초 **28.6%** (duration–CER Pearson −0.265).
- **잡음 마커는 주원인 아님**: noisy 34.7% vs clean 35.4%.
- Kspon ≥12초 28.6% vs FLEURS test ≥12초 23.1% → 잔여 도메인 갭 약 5.5%p.
- 외부: Kspon 원 논문 960h Transformer eval-other CER 9.0%(우리 6h·동결 타워와 직접 비교 불가), 짧은 발화 오류 증가는 ASR 문헌과 일치.
