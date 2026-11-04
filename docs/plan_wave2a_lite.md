# Wave 2A-lite — 승인된 설계·사전등록

- 작성일: 2026-11-04
- 상태: **승인됨(D-064)** — 4-arm·진단 포함. 구현·실행 가능.
- 선행: 4차 Hoplite 3-AI 검토 종합 `docs/hoplite/v4/2026-11-04_hoplite-review_v4_SYNTHESIS.md`
- 대체: `docs/plan_wave2a.md` (검토 대상 원안, 이 문서가 실행 정본)
- 범위: D 연구 트랙. F2 제품 경로(komixv2/whisper, D-057) 변경 없음.

## 1. 목적

D-β Wave 1의 탐색적 결과를 **새 dev에서 재측정**하고, 3-AI 검토가 지적한 측정 타당성 결함을 고친다. 구체적으로:

1. Kspon eval_clean 100 대신 **FLEURS ko dev**를 사용한다.
2. F-C를 **4-state softmax mix**로 구현하되, **F-C-concat comparator**를 함께 둔다.
3. F-A′/F-B/F-C-softmax/F-C-concat을 **같은 6.0008h·같은 seed·같은 dev**로 재학습한다.
4. **Kspon eval_other를 봉인 test**, FLEURS ko test를 **비교용 1회**로 사전등록한다.
5. **Go/No-Go를 비판별적으로 만들지 않는다.** Go는 2B, No-Go는 CP-D2다.
6. positive control·다중 seed·per-domain·error taxonomy·blank·vocab oracle·fbank baseline을 포함한다.

## 2. 승인 범위

| 항목 | 승인 내용 |
|---|---|
| Arms | F-A′, F-B, F-C-softmax(4-state), **F-C-concat** (4개) |
| dev | FLEURS ko dev |
| 최종 test | **Kspon eval_other 주 gate**, FLEURS ko test 비교용 1회 |
| Go/No-Go | **Go → Wave 2B**, **No-Go → CP-D2** (자동 2B 금지) |
| 예산 | **3~5일** (4 arms + seed 반복 + 진단) |
| 제외 | 13-state, wordpiece, 40h/100h, D-γ′/LoRA, Q4/QAT, Jev, MaxSim |

## 3. DoD

| # | DoD | 검증 |
|---|---|---|
| 1 | FLEURS ko dev manifest가 FLEURS test와 분리됨 | split·ID 대조 |
| 2 | Kspon eval_other가 봉인 test로 선언됨 | `docs/gates.md` 사전등록, 사용 로그 |
| 3 | 4-arm 학습 완료 | 체크포인트·로그 |
| 4 | F-C-softmax와 F-C-concat이 같은 dev에서 비교됨 | 예측·CER |
| 5 | F-A′ 기준선이 FLEURS dev에서 재산출됨 | `CER_FA_dev` |
| 6 | Go/No-Go가 새 기준선으로 판정됨 | `reports/W2A_lite_results.md` |
| 7 | positive control 통과 | 1h subset overfit |
| 8 | best arm 1~2 seed 반복 | seed 42 + 43/44 |
| 9 | per-domain·error taxonomy·blank·vocab oracle·fbank 보고 | 결과 표 |
| 10 | Kspon eval_other는 체크포인트 동결 후 1회만 사용 | 사용 로그 |
| 11 | FLEURS test는 비교용 1회만 사용 | 사용 로그 |
| 12 | AM-6 이행 표 포함 | 결과 보고서 |

## 4. 데이터·평가 세트

### 4.1 학습

- Wave 1과 동일: **6.0008h / 2,384클립**
  - Zeroth train 3.9001h / 1,534
  - KconfSpeech 2.1007h / 850 (3화자)
- 65/35 낭독·대화, ≤16초, 동일 코드·시드.
- 2A-lite에서는 데이터 구성을 바꾸지 않는다(단일 변수 원칙).

### 4.2 dev

- **FLEURS ko dev** 전체.
- FLEURS test와 ID·split이 겹치지 않음을 manifest에서 검증한다.
- dev는 arm 선택·조기 종료에만 사용한다.
- dev 문장 수·문자 수·도메인을 결과 보고서에 기록한다.

### 4.3 최종 test

| 세트 | 역할 | 사용 규칙 |
|---|---|---|
| **Kspon eval_other** (3.8h, 3,000발화) | **주 gate** | 체크포인트 동결 후 **1회**. D 학습·dev에 미사용 |
| **FLEURS ko test 382** | 비교용 | 동결 후 **1회**. Notesoop 18.96/komix 5.49/whisper 5.09와 비교만 |
| Kspon eval_clean 100 | **영구 은퇴** | D 평가에 사용 금지 |
| 새 P0 holdout | 선택 | 일반화 주장이 필요할 때 별도 확보·사전등록 |

- 주 gate는 Kspon eval_other의 CER(공백 무시, `normalize_nospace`)이다.
- Kspon eval_other 전사는 사전등록 규칙으로 정리한다: `[A-Za-z]{1,2}/` 잡음 마커 제거, `(A)/(B)`는 **첫 번째 대안**, `+`·잔여 괄호 제거. raw는 `ref_raw`로 보존한다.
- FLEURS test 결과는 “benchmark comparison”으로 표기하고 gate 판정에 쓰지 않는다.
- Kspon eval_other가 확보되지 않으면 2A-lite 결과는 **탐색적**으로만 보고하고 gate 판정을 보류한다.
- FLEURS test를 2A-lite의 arm 선택·조기 종료에 사용하지 않는다.

## 5. Arms

| Arm | 입력 | 차원 | 전처리 | 파라미터(목표) |
|---|---|---:|---|---:|
| F-A′ | `aud_out_proj` | 1,536 | 프레임별 LayerNorm | 8.11M |
| F-B | `aud_h_l11` | 1,024 | 프레임별 LayerNorm | 7.92M |
| F-C-softmax | `aud_h_l06/08/10/11` | 1,024 | 층별 LayerNorm → 학습 `w[4]` → softmax → 가중 합 | 7.93M |
| F-C-concat | `aud_h_l06/08/10/11` | 4,096 | 층별 LayerNorm → concat → 선형 투영 | 9.10M |

- F-C-softmax는 Addendum D-5.4의 정본 구현이다. `logits[4]`만 학습하고 temperature는 고정한다.
- F-C-concat은 D-β의 기존 방식을 같은 dev에서 재학습한 **comparator**다. softmax 효과와 dev 교체 효과를 분리한다.
- F-C-softmax가 F-C-concat보다 표현력이 낮을 수 있음을 결과 해석에 명시한다.
- 모든 arm은 동일 reader(4층 d384, 6 head, FF1536, pre-norm, CTC), 동일 vocab, 동일 seed 42, batch 8, threads 4, AdamW lr 1e-3, cosine, grad clip 5.0, 최대 20 epoch, patience 5.

## 6. Vocab

- train-only: 상위 한글 음절 **2,350 상한**. 실제 Wave 1 train 고유 한글은 **1,064자**이므로 2,350은 상한이고, 현재 코퍼스에서는 1,064자가 모두 포함된다.
- 숫자 0~9 + 라틴 소문자 + 공백 + unk.
- **실측 vocab: 1,101자(blank 포함 1,102)** — `data/wave2a_lite/vocab.json`, `vocab_coverage.json`.
- **dev 포함율 ≥95%**를 DoD로 유지한다. 실측 FLEURS dev coverage **99.42%**(60/10,419 미포함)로 이미 충족한다. 남은 결손은 희귀 한글 27종이며, 2,350 확장으로도 train에 없는 문자는 추가되지 않는다.
- dev/test 문자를 vocab에 추가하지 않는다. 포함율은 `normalize_nospace` 기준으로 계산한다.
- vocab oracle(참조 문자를 모두 허용한 상한)을 별도 진단으로 보고한다.

## 7. 진단·positive control

| # | 항목 | 대상 | 필수 |
|---|---|---|---|
| 1 | 1시간 subset overfit positive control | F-A′ 또는 best | 필수 |
| 2 | seed 42 + best arm seed 43/44 | best | 필수(예산 허용 시 2개) |
| 3 | per-domain CER(낭독/대화) | 4 arms | 필수 |
| 4 | error taxonomy(deletion/insertion/substitution) | 4 arms | 필수 |
| 5 | blank 비율·출력 길이·CTC alignment | 4 arms | 필수 |
| 6 | vocab oracle | best | 필수 |
| 7 | fbank baseline(log-mel + CTC) | 1 arm | 필수 |
| 8 | spacing/WER | best | 가능한 경우; 별도 모듈 |

- 1h overfit은 train subset에서 loss가 충분히 내려가고 train CER가 낮아지는지 확인한다. 실패하면 구현·최적화 문제로 분류하고 arm 비교를 중단한다.
- fbank baseline은 EG2 특징이 단순 acoustic feature보다 나은지 확인하는 최소 대조군이다.
- WER/공백 포함 CER은 예측이 공백을 출력하지 않으면 “미산출”로 명시한다. 별도 spacing 모듈을 쓰면 그 결과를 분리 보고한다.

## 8. 분석·판정

### 8.1 주지표

- dev CER(공백 무시, `normalize_nospace`), corpus 누적.
- arm별 오류/참조 문자, 어휘 포함율, 파라미터, epoch 시간, 총 학습 시간.

### 8.2 기준선

- **`CER_FA_dev`**: FLEURS dev에서 F-A′를 학습·평가한 CER.
- Kspon 0.3939나 F-D 0.5909를 2A-lite 기준선으로 쓰지 않는다.
- 4-arm 중 best가 F-A′이면 “개선 없음”으로 처리한다.

### 8.3 Go/No-Go (사전등록)

**Go (Wave 2B):**

- best arm이 `CER_FA_dev` 대비 **상대 5% 이상 개선**, 그리고
- 문장 단위 대응 부트스트랩 95% CI 하한 >0, 그리고
- 1h subset overfit positive control 통과.

**No-Go (CP-D2):**

- 위 조건 미충족.
- **“reader/output unit 병목 아님”이라고 단정하지 않는다.**
- CP-D2에서 ① 구현/vocab/seed ② 데이터 ③ 동결 타워 중 어디가 원인인지 진단한 뒤 2B/2C/중단을 결정한다.
- **No-Go를 이유로 자동 2B로 가지 않는다.**

### 8.4 최종 test

- Go/No-Go와 무관하게, 체크포인트를 동결한 뒤 Kspon eval_other를 1회 실행한다.
- FLEURS test는 비교용 1회만 실행한다.
- 최종 test 결과는 “gate”와 “benchmark comparison”을 분리해 표기한다.

## 9. 구현 순서

1. FLEURS ko dev 다운로드·manifest·test 미포함 검증.
2. Kspon eval_other 확보·manifest·전사 검증(봉인).
3. train-only vocab 생성, dev 포함율 계산.
4. FLEURS dev 특징 추출(F-A′/F-B/F-C 4층).
5. `FCSoftmaxReader` 구현 + 단위 테스트(softmax 합=1, shape, param count).
6. F-C-concat comparator 학습 경로 확인(기존 `CTCReader(in_dim=4096)`).
7. 1시간 subset overfit positive control.
8. 4-arm 학습(seed 42), best arm seed 43/44.
9. dev decode·CER·pairwise bootstrap·per-domain·error taxonomy·blank.
10. vocab oracle·fbank baseline.
11. 체크포인트 동결 → Kspon eval_other 1회, FLEURS test 1회.
12. `reports/W2A_lite_results.md`, `docs/decisions.md` 기록.
13. CP-D2: Go/No-Go 결과와 다음 단계 승인 요청.

## 10. 산출물 계약

- `data/wave2a_lite/fleurs_dev.jsonl`
- `data/wave2a_lite/vocab.json`
- `data/wave2a_lite/coverage.json`
- `data/wave2a_lite/kspon_eval_other.jsonl` (봉인 test manifest)
- `data/wave2a_lite/feats_dev/{fa,fb,fc}.npz`
- `train/w2a_lite_softmax.py` (또는 `train/d5_reader.py` 확장)
- `train/w2a_lite_ckpt/{fa,fb,fc_softmax,fc_concat}.best.pt`
- `logs/W2A_lite/{train,decode,diagnostics}`
- `reports/W2A_lite_results.md`
- `reports/provenance/W2A_lite/`

## 11. 예산·중단

- **2A-lite만 3~5일** 승인. 2B/2C는 별도.
- 1h overfit 실패 시 즉시 중단·원인 보고.
- Kspon eval_other 미확보 시 gate 판정 보류, 탐색적 결과만 보고.
- 4-arm 중 2개 이상이 수렴 실패하면 학습 설정 재검토 후 1회 재실행. 그 후에도 실패하면 No-Go로 CP-D2.
- VPS를 쓰는 경우 호스트당 무거운 job 1개, 완료 후 stop. P0만 사용.

## 12. AM-6 이행 표

| 요구 | 이행 |
|---|---|
| FLEURS ko dev | 이행 |
| Kspon eval_other 봉인 test | 이행(확보 후) |
| FLEURS test 비교 1회 | 이행 |
| 4-arm 동일 조건 | 이행 |
| F-C softmax + concat comparator | 이행 |
| seed 반복 | best arm 1~2회 |
| positive control | 1h overfit |
| per-domain/error/blank/vocab oracle/fbank | 이행 |
| WER/공백 포함 CER | 가능한 경우; 아니면 미산출 명시 |
| 13-state/wordpiece/40h/LoRA | **미이행(후속)** |

## 13. 승인 기록

- D-064 (2026-11-04): 3-AI 검토 종합 후 **2A-lite 4-arm·진단 포함 승인**. 최종 test는 **Kspon eval_other 주 gate + FLEURS test 비교 1회**. Go/No-Go는 **Go → 2B, No-Go → CP-D2**.
- 이 문서는 그 승인 범위를 실행하기 위한 사전등록이다.
