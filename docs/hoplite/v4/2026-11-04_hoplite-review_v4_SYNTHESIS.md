# EG2 상주 인코더 — 4차 Hoplite 3-AI 검토 종합

- 작성일: 2026-11-04
- 검토 대상: `reports/EXTERNAL_REVIEW_2026-11-04.md` (4차 요청서, 586줄)
- 검토자: GLM 5.3 Flash(max), Claude Sonnet 5.5(medium), GPT-6 Luna(xhigh)
- 스레드: GLM `thr_790930f5f3b449baac37da7b0c113691`, Sonnet `thr_30632cc9c1f149d49c6d05ad21c9ae84`, Luna `thr_303b93161be047fda00498adff4b425a`
- 검토 기준 HEAD: `147d0d1` (스레드 생성 시점). GLM은 이후 `774bdb2`까지 재동기화해 확인.
- 원문:
  - `docs/hoplite/v4/2026-11-04_hoplite-review_v4_GLM.md` (35,930B)
  - `docs/hoplite/v4/2026-11-04_hoplite-review_v4_SONNET.md` (27,009B)
  - `docs/hoplite/v4/2026-11-04_hoplite-review_v4_LUNA.md` (21,710B)
- 이 문서는 3-AI 의견의 **종합·비교**이며, 설계 승인이나 구현 지시가 아니다. 승인은 사용자만 한다.

---

## 0. 한눈에 보는 결론

1. **세 모델 모두 D-β의 정규화 정정(D-063)을 “사후 합리화”가 아니라 “사전등록 지표의 하네스 버그 수정”으로 판정했다.** 정정 후 수치도 독립 재계산과 일치한다.
2. **세 모델 모두 Q1을 “B — 탐색적 유지”로 판정했다.** “256d readout 병목”은 방향성 가설로만 유지되고, 층 선택·구조적 병목·G-C2 통과 가능성은 주장할 수 없다.
3. **세 모델 모두 Wave 2A를 다음 단계로 선택했지만, 현재 설계 그대로는 승인하지 않았다.** 공통 수정 요구는 ① 새 dev 기준선 ② 깨끗한 최종 test 사전등록 ③ Go/No-Go 논리 수정 ④ positive control·다중 seed·진단 ⑤ F-C-concat comparator다.
4. **세 모델 모두 현재 `Go → Wave 2B`, `No-Go → Wave 2B` 규칙이 비판별적이라고 지적했다.** 이는 문서의 실제 결함이다. Go와 No-Go가 같은 행동으로 이어지면 2A는 의사결정 실험이 아니다.
5. **세 모델 모두 5% 기준 자체는 유지 가능하지만, Kspon 기준선 0.3939를 FLEURS dev 결과에 그대로 적용하는 것은 비교 설계 오류라고 판정했다.** FLEURS dev에서 F-A′ 기준선을 다시 학습·측정해야 한다.
6. **세 모델 모두 2A에서는 문자 CTC를 유지하고 wordpiece/13-state/40h/LoRA는 후속으로 미뤘다.** output unit 변경은 원인 분리를 깨뜨리고, 6h 데이터에서 30k head는 과적합 위험이 크다.
7. **최종 test는 합의가 갈렸다.** GLM은 FLEURS test(주) + Kspon eval_other(보조), Sonnet은 Kspon eval_other(봉인 주) + FLEURS test(비교용 1회), Luna는 새 P0 holdout 확보 전 보류(E)다. 이 문서는 **2단 test 구조**를 권고한다(§4.1).
8. **D 트랙은 중단하지 않는다.** 다만 2A는 “2A-lite”로 범위를 좁혀 3~5일 예산으로 하고, 2B/2C는 2A 결과와 CP-D2에서 별도 승인한다.

---

## 1. 3-AI 판정 대조표

| 질문 | GLM | Sonnet | Luna | 종합 |
|---|---|---|---|---|
| Q1. D-β·R-D1의 과학적 지위 | B — 탐색적 유지. D-063은 버그 수정 | B — 탐색적 유지. F-D는 차원·전처리·수렴 교란 | B — 탐색적 유지 | **B. “탐색적 지지”로 문구 하향** |
| Q2. 다음 단계 | A — 2A 먼저, 5개 수정 조건 | 수정 — 2A-lite 먼저, 2C 보류 | A — 2A 먼저, 설계 수정·별도 승인 | **2A-lite. 2B/2C는 CP-D2에서 별도 승인** |
| Q3. 5% Go/No-Go | 수정 — 5% 유지, No-Go 추론 조건부 | 수정 — 기준선 재설정, No-Go 자동 2B 반대 | 수정 — 교차 dev 비교·자동 No-Go 반대 | **5%는 새 dev 기준선에서 재정의. No-Go는 CP-D2로** |
| Q4. F-C softmax state | A 기본, 조건 시 B(13-state) | D에 가까움 — concat을 comparator로 유지 | A 제한 — 4-state 먼저, 13-state 동등 주장 금지 | **4-state + F-C-concat comparator. 13-state는 후속** |
| Q5. 문자 CTC vs wordpiece | 문자 CTC 유지. wordpiece는 factorized 별도 실험 | 문자 CTC 유지. wordpiece 보류, spacing/F6 분리 | 문자 CTC 유지. spacing 보완, wordpiece 후속 | **문자 CTC 유지. wordpiece는 별도 사전등록 실험** |
| Q6. 깨끗한 최종 test | A — FLEURS test(주) + Kspon eval_other(보조) | 수정 — Kspon eval_other(주 봉인) + FLEURS test(비교 1회) | E — 새 P0 holdout 확보 전 보류 | **2단 구조 권고(§4.1). 사용자 결정 필요** |
| Q7. 데이터·R-D2 | 수정 — 2A 후 best arm, FLEURS dev에서 R-D2 | 수정 — 2A 후, seed/곡선 우선 | 수정 — 2A 기준 고정 후 R-D2 | **2A 후 R-D2. 40h는 그 다음** |
| Q8. 진단·positive control | 수정 — ①④⑥ 필수, ② Go 필수, ③ 권장 | 승인 — overfit·seed·per-domain·vocab oracle·fbank | 수정 — overfit·per-domain·error·blank·seed | **공통 필수 항목 채택(§4.2)** |
| Q9. 중단·예산 | 수정 — 예산 봉투·트리거 지금 등록 | 승인 — 지금 예산·중단 기준 | 수정 — 2A 단위 예산만, 전체는 단계별 | **2A 예산만 지금 승인. 전체 D 예산은 CP-D2** |

---

## 2. 공통 합의 사항

### 2.1 D-063 정규화 정정은 타당하다

- 세 모델 모두 `normalize_nospace`가 C-8/G-C2부터 쓰인 사전등록 지표이고, 학습 라벨에 구두점이 없는데 평가 참조에 남아 있던 것이 버그라고 판정했다.
- GLM은 원시 문장별 결과에서 F-D 930/1,574, F-A′ 620/1,574, F-B 616/1,574, F-C 611/1,574를 직접 재계산해 일치시켰다.
- GLM은 F-C를 제외한 F-A′ 기준으로도 R-D1 +33.33%, CI 하한 >0임을 확인했다. 즉 R-D1의 수치 충족은 F-C 프로토콜 편차에 의존하지 않는다.
- Sonnet/Luna도 `normalized_cer.json`과 원시 예측에서 같은 값을 재현했다. Luna는 NumPy 부재로 CI의 완전 bitwise 재현은 못 했지만 범위는 일치했다.
- **결론:** D-063은 유지한다. 단 “형식상 지지”라는 표현은 “탐색적 지지(수치 기준 충족, 사전등록 dev 절차 미이행)”로 바꾼다.

### 2.2 D-β가 말할 수 있는 것과 없는 것

**말할 수 있는 것:**

- 6시간·동결 타워·4층 reader·Kspon dev 조건에서 `audio_features[:256] + L2` readout(F-D)은 `aud_out_proj`·11층·4층 concat보다 **명확히 나쁘다**.
- F-D와 나머지 세 arm의 차이는 20%p 이상이고, 부트스트랩 구간도 0을 넘는다.
- F-A′/F-B/F-C끼리는 0.57%p 이내이고 pairwise CI가 모두 0을 포함한다.

**말할 수 없는 것:**

- “256d가 구조적 병목이다” — F-D는 **임의 256d 절단 + L2**이며, 256d-L2 vs 1536d-L2 같은 차원 통제가 없다. GLM은 “이 readout 조합의 열위”로 한정하라고 했다.
- “중간층이 필요하다” — F-A′/F-B/F-C가 동률이라 층 선택을 판별할 수 없다.
- “F-C가 최적이다” — 점추정 1위일 뿐, pairwise CI가 모두 0을 포함한다.
- “R-D1 지지 = G-C2 통과 가능” — R-D1 기준은 F-D 0.5909이고, 20% 개선은 0.4727로 15%에 한참 못 미친다.
- “Notesoop 256d 18.96%와 F-D 0.5909는 같은 의미” — Sonnet이 지적했듯 Notesoop 256d는 `projection[:256]+L2`이고, F-D는 `audio_features[:256]+L2`다. 같은 256d라도 위치·전처리·학습 목적이 다르다.

### 2.3 프로토콜 결함

- **AM-9 위반:** Kspon eval_clean 100을 dev로 사용했다. 이 세트는 최종 1회 test로 지정되어 있었고, 이제 D 평가에서 **영구 은퇴**해야 한다.
- **FLEURS dev 미사용:** D-β의 dev는 FLEURS ko dev가 아니다. R-D1의 사전등록 정의는 FLEURS dev를 전제하므로, D-β는 확인적 지위가 없다.
- **1 seed:** 0.57%p 차이를 arm 선택에 쓰기에는 부족하다. 세 모델 모두 반복 seed를 요구했다.
- **WER/공백 포함 CER 미산출:** 예측이 공백을 출력하지 않는다. 제품 F2는 이미 komix/whisper로 닫혔지만, D의 출력 단위 연구에는 이 공백이 남는다.
- **VPS/로컬 판정 규칙 모호:** GLM은 “성능 판정은 로컬만” 규칙이 CER에도 적용되는지 명확히 하라고 했다. D-β 학습은 VPS에서 수행됐다. 하드웨어 의존 지표(지연·RTF·RAM)와 하드웨어 독립 지표(CER)를 분리해 명시해야 한다.

### 2.4 현재 Wave 2A 설계의 결함

- **Go/No-Go가 둘 다 Wave 2B로 간다.** 세 모델 모두 이 규칙이 비판별적이라고 지적했다. 이 상태로는 2A 결과가 다음 행동을 바꾸지 않는다.
- **0.3742 목표가 다른 dev에서 나온 값이다.** 0.3939는 Kspon eval_clean 100 기준이고, 2A는 FLEURS dev를 쓴다. 도메인·표본·난이도가 달라 직접 비교할 수 없다.
- **F-C-concat comparator가 없다.** softmax mix와 dev 교체 효과를 분리할 수 없다. GLM은 4번째 arm으로 F-C-concat을 추가하라고 했다. Sonnet/Luna도 같은 취지로 comparator를 요구했다.
- **positive control이 없다.** 1시간 subset overfit, 다중 seed, per-domain CER, error taxonomy, blank/alignment, vocab oracle, fbank baseline 없이는 No-Go를 “reader/output unit 한계”로 해석할 수 없다.
- **파라미터 표기:** F-C-softmax는 1,024d 입력이므로 약 8.42M이고, F-C-concat은 9.08M이다. softmax가 concat보다 표현력이 낮을 수 있다는 점을 결과 해석에 명시해야 한다.
- **wordpiece factorized head:** 384→128→30k는 약 3.9M이지만 기존 reader 8.4M과 합치면 약 11.4M로 10M을 넘는다. “factorized면 10M 이내”라는 표현은 틀렸다.

---

## 3. 모델별 고유 지적

### 3.1 GLM 5.3 Flash

- F-C 제외 민감도: F-A′ 기준 R-D1 **+33.33%**, CI 하한 >0. R-D1이 F-C 편차에 의존하지 않음을 보였다.
- 정정 전 raw 수치로도 R-D1 +27.5% CI [+23.3,+32.0]이 기준을 충족했다. 정정이 결론을 “만들지” 않았다.
- 구두점 분해: 260개 중 비영숫자 기호 **234개**(`/ . ( ) ?` 226 + `+`·`,` 8), 숫자 16, 희귀 한글 10. 요청서의 “226개” 표기는 8개를 누락한 경미한 오류.
- `reports/provenance/W1/*.json` 경로가 요청서의 `logs/W1_decode`보다 실제 저장소와 일치한다고 지적.
- 2A 수정 조건 5개: 새 dev 기준선, F-C-concat 4번째 arm, 최종 test 사전등록, seed 반복, vocab 기대치 명시.
- Q4는 4-state 기본 + 조건 시 13-state 병행; softmax 폐기는 반대.
- Q6은 FLEURS test(주) + Kspon eval_other(보조)를 조건부 채택.

### 3.2 Claude Sonnet 5.5

- **가장 먼저 지적한 구조 결함:** Go/No-Go가 모두 2B로 가므로 2A가 의사결정 실험이 아니다.
- F-D와 Notesoop 256d의 불일치: 문서는 F-D `[:256]`을 “MRL 아님”이라 하고, D-028/C2-A0는 Notesoop 256d를 MRL로 표기한다. R-D1 해석에 직접 영향을 준다.
- `logs/W1_decode`가 shallow checkout에 없고, 실제 예측은 `reports/provenance/W1/*.json`에 있다.
- factorized head도 총 11.4M로 10M을 넘는다.
- Q6은 Kspon eval_other를 **봉인 test**로 선언하고, FLEURS test는 동결 후 1회 비교용으로만 쓰자고 했다.
- Q8에 **fbank baseline**을 추가하라고 했다. EG2 특징이 단순 log-mel CTC보다 나은지 확인해야 한다.
- Q2는 “2A-lite” — 2A를 재구성해 동률 arm 비교의 검출력을 먼저 확보하자고 했다.

### 3.3 GPT-6 Luna

- Q1은 B, Q2는 A(조건부), Q6은 **E(보류)**. 새 P0 holdout의 라이선스·분할·화자 중복·문장 수가 확인되기 전에는 최종 test를 확정하지 말자고 했다.
- Q5에서 factorized head 총량이 약 11.4M임을 독립 계산했다.
- Q9에서 전체 2주/40h/5 VPS를 지금 약정하지 말고, 2A 단계 예산만 승인한 뒤 tranche별로 재승인하자고 했다.
- Q6에서 FLEURS test를 “clean”이라고 부를 수 없다는 점을 강조했다. 비교 가능성은 인정하지만 독립 표본의 대체물은 아니라고 했다.

---

## 4. 권고안 — Wave 2A-lite

현재 `docs/plan_wave2a.md`를 그대로 승인하지 않고, 다음으로 재구성하는 것을 권고한다. **실행 전 사용자 승인 필요.**

### 4.1 최종 test: 2단 구조

**권고:**

1. **주 gate:** `Kspon eval_other` (3.8h, 3,000발화)를 **봉인 test**로 사전등록한다. D-β 학습·dev에 사용되지 않았고, Kspon eval_clean과 다른 split이다. 단, 같은 코퍼스·낭독체라는 한계를 명시한다.
2. **비교용:** `FLEURS ko test` 382클립은 **체크포인트 동결 후 1회**만 실행해 Notesoop 18.96/komix 5.49/whisper 5.09와 비교한다. 이 값은 gate가 아니라 “benchmark comparison”으로 표기한다.
3. **보강:** 새 P0 한국어 holdout(AI Hub 등)은 라이선스·P0·분할·화자 중복·문장 수를 확인한 뒤 **최종 일반화 주장**이 필요할 때만 추가한다. 지금 확보하지 못하면 2A 결과는 “탐색적”으로 유지한다.
4. `Kspon eval_clean 100`은 D 평가에서 **영구 은퇴**한다.

이 구조는 GLM의 “FLEURS 주 + Kspon 보조”와 Sonnet의 “Kspon 주 + FLEURS 비교”를 절충한 것이다. Luna의 E(보류)보다는 실행 가능하지만, 새 P0 holdout 없이는 “일반화” 주장을 하지 않는다.

**사용자 결정 필요:** 주 gate를 FLEURS test로 할지, Kspon eval_other로 할지. 이 문서는 Kspon eval_other 주 gate를 권고한다.

### 4.2 2A-lite 범위

| 항목 | 현재 2A | 2A-lite 권고 |
|---|---|---|
| dev | FLEURS ko dev | FLEURS ko dev |
| arms | F-A′/F-B/F-C-softmax | **F-A′/F-B/F-C-softmax/F-C-concat** (4개) |
| F-C-concat | 없음 | **추가** — softmax 효과와 dev 교체 효과 분리 |
| seed | 42 하나 | 42 + best arm 1~2 seed 반복 |
| test | 미정 | Kspon eval_other 봉인 + FLEURS test 비교 1회 |
| 진단 | CER·coverage·bootstrap | + overfit·per-domain·error taxonomy·blank/alignment·vocab oracle·fbank |
| Go/No-Go | 둘 다 2B | Go → 2B; No-Go → **CP-D2**에서 2B/2C/중단 결정 |
| 예산 | 1~2일 | **3~5일** (4 arms + seed + 진단) |

### 4.3 수정된 Go/No-Go

- **기준선:** FLEURS dev에서 F-A′를 같은 manifest·vocab·seed로 다시 학습해 `CER_FA_dev`를 만든다. Kspon 0.3939를 쓰지 않는다.
- **Go:** best arm이 `CER_FA_dev` 대비 상대 5% 이상 개선되고, 문장 단위 대응 부트스트랩 95% CI 하한 >0이고, positive control(1h overfit)이 통과할 때.
- **No-Go:** 위 조건 미충족. 이때 “reader/output unit 병목 아님”이라고 단정하지 않는다. **CP-D2**에서 ① 구현/vocab/seed 문제인지 ② 데이터 문제인지 ③ 동결 타워 문제인지 진단한 뒤 2B/2C/중단을 결정한다.
- **금지:** No-Go를 이유로 자동 2B로 가는 것. Go와 No-Go가 같은 행동으로 이어지면 2A는 실험이 아니다.

### 4.4 진단·positive control (필수)

세 모델의 공통 요구를 합치면:

1. **1시간 subset overfit positive control** — reader가 작은 데이터를 외울 수 있는지 확인. 실패하면 구현/최적화 문제다.
2. **2~3 seed** — 최소한 best arm은 반복. 0.57%p 차이를 선택에 쓰지 않는다.
3. **Per-domain CER** — 낭독(Zeroth) vs 대화(Kconf)를 분리 보고.
4. **Error taxonomy** — deletion/insertion/substitution, 숫자·영문·띄어쓰기별.
5. **Blank/alignment 진단** — blank 비율, 출력 길이, CTC alignment.
6. **Vocab oracle** — 참조 문자를 모두 허용한 상한; vocab 결손과 모델 오류를 분리.
7. **fbank baseline** — log-mel + CTC. EG2 특징이 단순 acoustic feature보다 나은지 확인(Sonnet 제안).
8. **Spacing/WER** — 별도 spacing 모듈 또는 공백 포함 라벨로 측정. 2A의 주지표는 CER(공백 무시) 유지.

### 4.5 F-C와 출력 단위

- **F-C-softmax 4-state**를 먼저 구현하되, **F-C-concat을 같은 dev의 comparator**로 둔다.
- 13-state는 2A에서 하지 않는다. 4-state 결과가 나쁘다고 13-state의 성패를 예측하지 않는다. 13-state는 별도 사전등록·예산·승인으로 미룬다.
- **문자 CTC 유지.** wordpiece는 2A에서 하지 않는다. 6h 데이터에서 30k head는 과적합 위험이 크고, 10M 상한도 넘는다. wordpiece는 별도 소-wave(문자 best vs wordpiece-factorized, 같은 dev·seed, Gemma 임베딩 초기화 포함)로 2B 이후에 검토한다.
- 띄어쓰기는 F6 또는 별도 spacing 모듈로 분리한다. D의 제품 요구 정렬은 F2가 이미 komix/whisper로 닫혀 있으므로 긴급하지 않다.

### 4.6 데이터·R-D2

- 2A는 6.0008h, 65/35를 유지한다(단일 변수 원칙).
- 2A 종료 후 best arm으로 **R-D2**: H/3, 2H/3, H 학습곡선을 FLEURS dev에서 측정하고 40h를 로그-시간 외삽한다. 예측 구간을 반드시 병기한다.
- 40h는 “다음 증분”이지 2A의 전제가 아니다. 40h/100h 확장은 R-D2 예측 구간과 CP-D2 승인 후에만.
- Zeroth는 유지하되 화자 ID 부재를 명시하고, speaker-disjoint가 필요한 결론은 화자 ID가 있는 P0 소스로 별도 검증한다.

---

## 5. 문서 정정 사항

이번 검토에서 확인된 요청서·설계 문서의 결함이다. 2A 승인 전에 반영해야 한다.

| # | 위치 | 문제 | 수정 |
|---|---|---|---|
| 1 | `docs/plan_wave2a.md` §8, 요청서 §4.5 | Go와 No-Go가 모두 Wave 2B로 감 | No-Go는 CP-D2로; 자동 2B 금지 |
| 2 | `docs/plan_wave2a.md` §8, 요청서 Q3 | 0.3742가 Kspon 0.3939에서 계산됨 | FLEURS dev에서 F-A′ 기준선 재산출 후 5% 적용 |
| 3 | `docs/plan_wave2a.md` §4.3 | F-C-concat comparator 없음 | 4번째 arm 추가 |
| 4 | 요청서 §7.1, §3.3 | `logs/W1_decode` 경로가 저장소에 없음 | `reports/provenance/W1/{fd,fa,fb,fc}.json` |
| 5 | 요청서 §3.3, D5 보고서 | 260개 중 “226개 구두점”은 8개 누락 | 비영숫자 기호 234개(226+8), 숫자 16, 희귀 한글 10 |
| 6 | 요청서 §3.7, Q1 | F-D 256d와 Notesoop 256d MRL 혼동 | “임의 256d+L2 readout”으로 한정; Notesoop projection도 MRL과 동일하지 않음 |
| 7 | 요청서 Q5 | factorized head가 10M 이내인 것처럼 읽힘 | 3.9M head + 8.4M reader ≈ 11.4M; 상한 lift 또는 reader 축소 필요 |
| 8 | 요청서 §3.4, D5 보고서 | “형식상 지지”가 확인적 지위를 암시 | “탐색적 지지(수치 기준 충족, FLEURS dev 미이행)” |
| 9 | 요청서 §1.2 | “성능 판정 로컬만”이 CER에도 적용되는지 모호 | 하드웨어 의존 지표(지연·RTF·RAM)와 CER를 분리 명시 |
| 10 | `docs/plan_wave2a.md` §4.4 | F-C-softmax 파라미터 8.42M, F-C-concat 9.08M | 두 arm의 파라미터 차이를 결과 해석에 명시 |

> 1~3은 설계 승인 전에 반드시 고쳐야 한다. 4~10은 문서 정합성 수정이며, 2A 실행 전에 반영한다.

---

## 6. 지금 결정할 것 / 미룰 것

### 지금 결정

1. **F2 제품 경로 유지:** komixv2/whisper(D-057). D는 연구 트랙.
2. **D-β 문구 하향:** “탐색적 지지”로 통일. D-063 정규화 정정은 유지.
3. **2A-lite 승인 여부:** 4-arm, FLEURS dev, Kspon eval_other 봉인 test, FLEURS test 비교 1회, 3~5일 예산.
4. **Go/No-Go 수정:** Go → 2B, No-Go → CP-D2. 5%는 새 dev 기준선에서 재정의.
5. **필수 진단:** overfit, seed, per-domain, error taxonomy, blank, vocab oracle, fbank, spacing.
6. **Kspon eval_clean 영구 은퇴.**

### 미룰 것

- 13-state mix
- wordpiece/factorized head와 10M 상한 변경
- 40h/100h 데이터 확장
- D-γ′/LoRA와 Q8 parity
- 2B/2C 전체 예산
- 최종 test에서의 성능 판정(2A/2B 결과 전)
- Q4/QAT, Jev head, MaxSim

---

## 7. 권고 결론

**D-β의 방향성 결론은 살아 있다. 그러나 확인적 지위는 없다.** “256d readout이 이 조건에서 불리했다”까지만 말하고, “256d 구조적 병목”, “중간층 필요”, “F-C 최적”은 주장하지 않는다.

**다음 단계는 2A-lite다.** 현재 2A는 ① 다른 dev 기준선 ② 비판별적 Go/No-Go ③ comparator 부재 ④ 진단 부재 때문에 그대로 승인할 수 없다. 2A-lite는 이 네 가지를 고치고, Kspon eval_other를 봉인 test로 두고, FLEURS test는 비교용으로만 쓴다.

**2B/2C는 2A 결과와 CP-D2 없이 승인하지 않는다.** 2A가 No-Go여도 자동으로 2B로 가지 않는다. No-Go는 “이 구성에서 5% 근거 없음”이며, 원인 진단 후 2B/2C/중단을 결정한다.

**사용자 승인이 필요한 핵심 3건:**

1. 2A-lite의 4-arm·3~5일 예산 승인.
2. 최종 test를 Kspon eval_other(주) + FLEURS test(비교)로 사전등록하는 안 승인.
3. Go/No-Go를 “Go → 2B, No-Go → CP-D2”로 바꾸는 안 승인.

이 3건이 승인되기 전에는 구현·학습·VPS 재기동을 하지 않는다.

---

## 8. 원문·재현

| 항목 | 경로 |
|---|---|
| 4차 요청서 | `reports/EXTERNAL_REVIEW_2026-11-04.md` |
| GLM 원문 | `docs/hoplite/v4/2026-11-04_hoplite-review_v4_GLM.md` |
| Sonnet 원문 | `docs/hoplite/v4/2026-11-04_hoplite-review_v4_SONNET.md` |
| Luna 원문 | `docs/hoplite/v4/2026-11-04_hoplite-review_v4_LUNA.md` |
| 스레드 매니페스트 | `docs/hoplite/v4/threads.json` |
| D-β 정정 | `reports/provenance/W1/normalized_cer.json` |
| 워처 로그 | `docs/hoplite/v4/watch_v4.log` |

- 세 검토 모두 P0만 사용했고, P1·시크릿·서브에이전트·추가 모델 호출은 없었다.
- 검토 시점 HEAD는 `147d0d1`이며, GLM은 `774bdb2`까지 재동기화했다. 이후 문서 정정은 검토 원문에 반영되지 않았으므로, 원문과 이 종합의 차이는 §5에 명시했다.
