**본 보고서의 검토자: GLM 5.3 Flash (reasoning max, OpenRouter `z-ai/glm-5.3-flash`) — C5 B0-A 라운드 전용 신규 독립 외부 검토.**

다른 모델·다른 라운드의 검토 결과를 재사용하지 않았다. 아래 판정은 본인이 요청서와 원문 artifact를 직접 열람·재계산한 결과다.

# C5 B0-A 결과 외부 검토 — GLM 5.3 Flash (독립 라운드)

- 작성일: 2026-11-09 (UTC)
- 검토 대상 문서: `reports/EXTERNAL_REVIEW_C5_B0A_2026-11-09.md` (495줄 전체 직접 열람, 발췌·요약·타모델 답변 미사용)
- **검토 기준 HEAD: `1d0e756`** (`docs: add C5 B0-A review prompts and dispatch`)
  - 동기화: `git fetch origin` → `git pull --ff-only origin main` → "Already up to date." (로컬 = origin/main 동일 HEAD)
  - 요청서 표기 기준 `c66f17c`은 본 HEAD의 직전 커밋이며, `git diff --stat c66f17c..1d0e756` 결과는 검토 dispatch 파일 6개 추가(890 insertions)뿐이다. 결과 코드·보고서는 `c66f17c`와 동일하다.
- 준수 사항: consultation-only (본 파일 외 저장소 쓰기 0), 학습·평가 실행 없음, **test 163 미사용**, P1 데이터·외부 API 미사용, subagent·추가 LLM 호출 없음, 결과를 본 뒤 threshold·seed·donor·step 변경 제안 없음, `eval/slot_verify.py` 미수정 (`git log -- eval/slot_verify.py` → 최종 커밋 `4d7f007` 이후 변경 없음 확인), T5Gemma2 D-108 STOP 존중.
- 검증 방법: `reports/provenance/C5_b0a/{aggregate.json,s*_*.json}` 6개 unit에서 수치를 jq로 독립 재계산하고, `runner/c5_mt5_lora_b0.py`(562줄)·`runner/c5_b0a_aggregate.py`(175줄)·`docs/plan_c5_b0_prereg_v0_1.md`(340줄)·`reports/C5_B0A_2026-11-09.md`·`reports/C5_B0_METRIC_IMPL_2026-11-09.md`·`reports/C5_E0_NATIVE_AUDIT_2026-11-09.md`·`reports/C5_LAYER_PLAN_3AI_REVIEW_SYNTHESIS_2026-11-08.md`를 교차 대조했다.
- 한계 선언: 이 체크아웃에는 `data/`(모델 가중치·캐시)가 없다(gitignore). 따라서 재실행·재측정은 불가하며(애초에 금지), 검증은 provenance JSON ↔ 보고서 ↔ 코드 교차 확인 수준이다. 레이블 EOS 포함 여부 등 tokenizer 실행이 필요한 판단은 코드 근거 + T5 계열 표준 동작에 근거하며 별표로 한계를 표기했다.

---

## 0. 최종 판정 요약

### **NARROW**

> mT5 decoder adaptation 트랙을 닫지도(STOP 기각), B0-B로 바로 확대하지도(CONTINUE 기각) 않는다. 다음 실행은 **(0) 무훈련 native-encoder metric sanity → (1) generation 붕괴 진단(소형, 새 사전등록) → (2) P/M 통제 20/20(새 사전등록)** 으로 한정하고, 이 선행 진단이 통과한 뒤에만 B0-B 4-arm 300/95를 새 사전등록·사용자 승인으로 진행한다.

한 줄 근거: B0-A의 **INCONCLUSIVE는 통계적으로 올바르게 도출됐고**(§1 재계산 일치, F8 결정 로직 일치), **트랙 STOP의 근거도 아니다**(F5 전력 분석 — 이 설계는 L−F ≈ 0.068 미만의 효과를 원리적으로 POSITIVE로 만들 수 없었고 관측치는 0.014였다). 반면 LoRA arm의 generation은 2/3 seed에서 루프 토큰이 공백 계열로 붕괴했고(F1), **frozen arm과의 학습-mode dropout 비대칭**(F2)이라는 recipe confound가 남아 "decoder adaptation 효과" 질문의 아답터가 부족하다.

---

## 1. 독립 수치 검증 (요청서·aggregate 대조)

6개 unit JSON에서 문서별 `delta_shuffled_copy`를 다시 집계했다. 문서 값 = seed 3개·donor 5개 평균, 전체 평균 = 문서 평균(aggregate와 동일 정의).

| 항목 | 요청서/aggregate.json | 본 검토 재계산 | 판정 |
|---|---:|---:|---|
| frozen mean `Δshuffled_copy` | +0.007810 | +0.0078099 | 일치 |
| frozen CI | [−0.037997, +0.051194] | normal-approx [−0.0360, +0.0516] | 일치(허용 오차) |
| lora mean | +0.021751 | +0.0217514 | 일치 |
| lora CI | [−0.028004, +0.067209] | normal-approx [−0.0267, +0.0702] | 일치(허용 오차) |
| L−F paired mean | +0.013942 | +0.0139415 | 일치 |
| L−F CI | [−0.052508, +0.078599] | normal-approx [−0.0543, +0.0821] | 일치(허용 오차) |
| positive seeds F / L | 1/3, 2/3 | 1/3, 2/3 | 일치 |
| seed별 F mean | −0.0029 / +0.0334 / −0.0071 | 동일 | 일치 |
| seed별 L mean | +0.0339 / +0.0513 / −0.0199 | 동일 | 일치 |
| copy coverage | 0.8246 | 0.824620 (6개 unit 모두 동일) | 일치 |
| train CE last (L) | 7.1412 / 7.4557 / 7.6252 | 동일 | 일치 |
| generation nonempty F / L | 60/60, 22/60 | F 20+20+20, L 2+20+0 | 일치 |

부가 재계산: L−F 문서별 부호 **12+/8−/0** (부호검정 two-sided p≈0.50), 문서 SD frozen 0.100 / lora 0.110 / paired 0.156, lora seed-mean SD ≈ 0.037, 문서-level SE ≈ 0.022-0.035. 6개 unit 모두 `n_docs=20`(copy token <5로 제외된 문서 없음), `copy_guard_failed=false`, `test_split_used=false` 확인.

**F8 — 판정 로직 구현 일치.** `runner/c5_b0a_aggregate.py`는 prereg §8.1을 그대로 구현한다: POSITIVE_SIGNAL = mean ≥ 0.05 ∧ lora CI lower > 0 ∧ L−F CI lower > 0 ∧ positive seeds ≥ 2, NO_SIGNAL = mean ≤ 0 ∧ CI upper < 0.05, 그 외 INCONCLUSIVE. B0-A 수치는 세 조건 모두 미충족이므로 INCONCLUSIVE는 **유일하게 올바른 분기**다.

---

## 2. 본 라운드 신규 관찰 (F1~F7)

### F1. generation은 양 arm 모두 cap-hit 반복 루프다 — "collapse"의 실체

- 6개 unit × 20문서 = **120/120 전부 gen_len=257**(max_new_tokens 256 전부 소진), **EOS 0/120**.
- 샘플(원문 JSON): frozen = `<extra_id_0> 도 도 도 도 …`(보이는 문자 루프 → nonempty 계수), lora seed09 = `을 고를 도를 도를 도를 …`(nonempty), lora seed08/10 붕괴 엔트리 = **텍스트가 공백 문자만 반복**(gen_len 257, strip하면 빈 문자열 → "empty" 계수).
- 즉 nonempty 60/60 vs 22/60의 차이는 생성 품질 격차가 아니라 **루프 토큰의 표면형 차이**(보이는 문자 vs 공백 계열 piece)에 가깝다. 양 arm 모두 기능적 요약이 전혀 없다(val real_ce_copy ≈ 7.65-8.07 nats ≈ perplexity 2,100-3,200).
- 요청서 §4.4의 "LoRA generation collapse"는 방향은 맞지만 과소 기술이다. 정확한 구조는 **"100-step 공통 underfit 위에, lora arm의 2/3 seed에서 루프 토큰이 공백 계열로 이동"**이다.

### F2. 학습-mode dropout 비대칭이 코드로 확인된다 (recipe confound)

- `train_arm()`: frozen arm은 `load_base()`의 eval 상태 그대로 학습(디코더 dropout off), **lora arm만 `model.train()`**(mT5 base dropout 0.1 + LoRA dropout 0.05). 평가(`evaluate_arm`)는 양 arm 모두 `model.eval()`이라 metric 자체는 공정하다.
- 교차 증거: frozen seed08 step-0 train CE **27.43998146057129** == smoke의 zero-LoRA eval-mode loss와 정확히 동일(→ frozen 학습 forward에 dropout이 없었음을 실증). lora arm의 같은 step-0는 37.43/32.15/49.10 — 동일 adapter 초기화·동일 첫 문서인데 frozen 대비 **+10.0/+10.5/+12.1 nats**, 순수하게 train-mode dropout 차이.
- 결과: "L−F"는 순수한 decoder capacity 효과가 아니라 **"LoRA + 학습 드롭아웃" vs "무LoRA + 무드롭아웃 학습"의 bundle**이다. prereg §5의 "학습 시 LoRA dropout, 평가 시 eval"은 base decoder dropout 상태를 특정하지 않은 모호성이 있다(요청서 §7 confound 표와 일치 — 본 검토가 코드·수치로 확정).

### F3. EOS 0/60은 wiring 결함이 아니라 underfit의 예상 결과 (레이블에는 EOS가 있다)

- `make_labels()`는 `add_special_tokens=True`로 요약을 인코딩한다. T5 계열 tokenizer는 이 경우 시퀀스 끝에 EOS(id 1)를 붙인다(표준 동작 — 이 체크아웃에 가중치가 없어 직접 실행 검증은 불가*). 즉 레이블에는 EOS가 포함돼 있고, "EOS 미포함 레이블"이라는 설계 결함 가설은 기각된다.
- 20문서×100 step(시퀀스당 EOS 1토큰)으로 EOS 생성을 학습하기엔 부족하고, mT5의 EOS 회피 성향 + 루프 디코딩(F1)이 겹친다. "EOS 0/60"을 generation 경로 결함의 증거로 쓰면 안 된다.

### F4. copyable mask가 과잉 관대하다 — coverage 0.8246은 과대계수 (MF6)

- `copyable_mask()`: NFKC 후 **source에서 모든 공백을 제거한 문자열**에 piece(공백 제거)가 substring인지 검사. 한국어 1-2음절 piece는 장문 어디든 존재하므로 mask ≈ 전체 content token이 된다.
- mask는 arm·seed 무관(6개 unit 동일 0.824620)이라 F vs L 비교 자체를 편향시키지는 않는다. 그러나 Δshuffled_copy의 "copy" 의미를 희석하고, copy guard(중앙값 ≥ 0.10)를 사실상 무의미한 통과로 만든다. 표본 정밀도 감사가 B0-B 전 Must-fix다. **규칙 변경 자체는 새 사전등록 사항**이다(결과를 본 뒤 무음 변경 금지).

### F5. 전력: B0-A는 δ≈0.05~0.07 이하에서 POSITIVE가 원리적으로 나오기 어려웠다

- paired 문서 SD 0.156, n=20에서 L−F의 CI lower > 0가 되려면 **L−F ≥ 1.96×0.156/√20 ≈ 0.068**(80% power 기준 ≈ 0.098) 필요. 관측치 0.014.
- arm-level: 문서 SD 0.10-0.11, n=20 → mean ≥ 0.045-0.05 필요. **screen threshold 0.05가 관측 분산에서는 n=20의 인지 한계선과 일치**한다.
- 대조: n=95(B0-B val)에서 paired MDE ≈ **0.031(유의) / 0.045(80% power)** — B0-B 규모는 현 사전등록 threshold(0.05)를 검증할 수 있는 최소 규모다. 이는 threshold 변경 제안이 아니라 **현 threshold에 대한 전력 평가**다.

### F6. 통계 단위: 문서 bootstrap은 3 seed를 고정으로 조건화한다

- 문서별 seed/donor 평균 후 문서 resample — prereg §6.3대로 구현됐고 오류는 없다. 다만 lora seed-mean의 표본 SD(≈0.037, 범위 −0.020~+0.051)는 문서-level SE(≈0.025)와 같은 크기다. 계층적(문서×seed) bootstrap이면 CI가 다소 넓어질 것이고, **판정은 불변이며 오히려 INCONCLUSIVE가 강화된다**. 새 사전등록에서 채택 권장.

### F7. prereg §7의 generation 기록 항목이 미구현이다

- JSON generation 엔트리는 id/text/gen_len/eos 4필드뿐이다. prereg이 약속한 **cap hit / repeated-4gram / char F1 / grounded no-new**는 없다. gen_len=257로 cap-hit은 사후 추론 가능하지만 반복·grounded 진단은 불가하다. 학습 없이 구현 완성 가능한 Must-fix다.

---

## 3. Q1~Q12 판정

형식: 판정 / 근거 / 다음 단계(1~3개).

### Q1. E0 tokenizer 결론

- **판정: agree.**
- 근거: content ID 400/400 일치, content token mismatch 0, 문자 0/498,455, digit-span 0/12,538, 유일 차이 = native EOS +1(전 문서), truncation 0/400. hidden cosine mean .99135/.99150, p01 .9275/.9292, **cosine < .95가 2.4-2.5%**. 직전 검토의 "T5Gemma2 ID가 EG2 PLE를 광범위 오염" 우려는 이 400문서(train+val)의 content-ID 기준으로 기각됐다. 그러나 EOS 1토큰만으로 2.4% 토큰의 hidden이 유의미하게 이동한다는 사실은 ID 일치와 무관하게 native cache 필요성을 유지시킨다. 검증 범위가 이 프로젝트 데이터 400문서라는 점도 유지.
- 다음 단계: (1) **native cache는 B0-B에도 필수로 유지**(EOS/sequence semantics + provenance 단일화, legacy cache는 historical screening artifact로만 격리), (2) B0-B 사전등록서에 cache provenance(tokenizer_class, test_split_used=false 등) 복사 기록, (3) 추가 tokenizer 작업은 불요 — 예산을 아래 Must-fix로 이동.

### Q2. B0-A 설계의 적절성

- **판정: conditional.** 설계 오류라기보다 "요구의 절반을 충족한 계획된 screening"이다.
- 근거: prereg §4.1이 P/M 제외를 명시했고 요청서 §5.1이 미이행(native positive 없음, memory-free 없음, role probing 없음, metric audit 없음)을 숨기지 않는다. 즉 승인된 범위 내 staging이며 사기적 구성이 아니다. 그러나 3-AI 종합 MF3는 matched 4-arm을 요구했고, P 없이는 metric 민감성을, M 없이는 "Δ>0이 real memory 사용 때문인지"조차 확인할 수 없다. 결과의 인과 해석 상한이 구조적으로 낮다.
- 다음 단계: (1) P/M을 B0-B가 아니라 **소형 선행 통제로 앞당긴다**(Q6), (2) 이후 모든 문서에서 B0-A를 "F/L 2-arm screening"으로 지칭하고 matched B0으로 부르지 않는다, (3) metric 유효성(P valid)을 B0-B PASS 조건으로 유지(현 prereg §9에 이미 있음).

### Q3. INCONCLUSIVE 판정

- **판정: agree.** 통계·집계 오류 없음.
- 근거: §1 재계산표(평균·CI·seed별 값 전부 일치, bootstrap CI는 normal-approx와 0.003-0.005 내 일치), F8(결정 로직이 prereg 그대로), 부호검정 p≈0.50, donor/label/crop 구현이 prereg §6.1과 일치(`K=min`, 동일 donor 배정, donor 5개, <5 copy token 문서 없음). 유일한 유보는 F6 — CI가 3 seed를 고정 조건화하므로 실제 불확실성은 이보다 약간 크다. 그래도 판정 불변(NO_SIGNAL도 POSITIVE도 아님).
- 다음 단계: (1) B0-A 수치를 확정 기록으로 보존(재계산 불요), (2) 새 사전등록에서 계층적 bootstrap 채택, (3) 이 CI를 threshold 재조정 논의의 근거로 쓰지 않는다.

### Q4. Generation collapse

- **판정: conditional.** 귀속은 **① underfit + ② LoRA/dropout 불안정의 복합**, **③ 기각**, **④ 미확정**. CE를 전면 해석 불가로 만들 필요는 없지만 L−F의 treatment 해석은 불가.
- 근거: F1 — 120/120 cap 루프, EOS 0/120, nonempty 차이는 루프 토큰 표면형(공백 이동 2/3 seed). F3 — 레이블에 EOS 포함 → EOS 0/60은 100-step underfit의 예상 결과. F2 — lora arm만 train-mode dropout(step-0 CE +10~12 nats). ③ 기각 근거: 6개 unit이 동일한 `generate_arm` 경로를 쓰고 frozen은 60/60 nonempty, metric-smoke에서 generate 경로 동작 확인 → 경로 결함이면 lora에만 선택적으로 나타나지 않는다. ④ 미확정: 100 step에서 "decoder adaptation 자체의 실패"를 말할 증거 없음.
- CE 해석: 평가는 양 arm 모두 eval 모드로 공정하므로 측정값 자체는 유효하다. 그러나 lora 평균 +0.0218은 "정상 학습 1 seed + 붕괴 2 seed"의 혼합이므로 **L−F를 decoder adaptation 효과 추정량으로 읽는 것은 불가**하다. frozen arm 결과(+0.0078, CI 0 포함)는 여전히 유효한 baseline 측정이다. 별도 training-instability 발견으로 분리 보고하는 요청서 §4.4의 처리가 맞다.
- 다음 단계: (1) collapse 원인 분리 진단을 새 사전등록으로 1회 실행(dropout 대칭화 유무, LoRA LR, checkpoint 시점별 평가 — seed 20261110 lora arm 중심, ≤1 CPU-h), (2) generation 기록 필드 구현(F7), (3) 문서 표기를 "lora 고유 실패"가 아닌 "loop-token degeneration(공통 underfit + lora 2/3 seed 공백 이동)"으로 교정.

### Q5. B0-A가 말하는 것

- **판정: agree** — 요청서의 3분법이 정확하며 아래와 같이 고정한다.
- 근거·구분:
  - **"신호 없음"은 성립하지 않는다.** lora CI upper +0.067 > 0 이고 mean > 0 → NO_SIGNAL 조건(mean ≤ 0 ∧ CI upper < 0.05) 미충족. 0.05 수준 효과를 배제할 수 없다.
  - **"underpowered inconclusive"가 primary에 대한 정확한 서술이다.** F5 — 본 설계의 paired 탐지 한계 ≈ 0.068(유의)/0.098(80%), 관측 0.014.
  - **"LoRA 불안정"은 별도 발견으로 확립** — F1/F2(공백 루프 2/3 seed, 학습 dropout 비대칭이 최유력 후보 원인). 단 원인 귀속은 진단 전까지 보류.
  - 확립: metric/donor/bootstrap/native-cache 경로 동작, frozen baseline 측정, 붕괴 관찰. 미확립: decoder LoRA 무효/유효, frozen 병목, layer19 최적성, bridge 불가능성 — 요청서 §6.2 그대로.
- 다음 단계: (1) 위 3분법 문구를 결과 보고서에 보강 기록, (2) L arm 혼합 해석 경고(Q4) 추가, (3) 다음 실험의 판독 대상을 "L−F"에서 "P/M 유효성 확인 후의 L−F"로 명시.

### Q6. 다음 실험

- **판정: conditional** — **D 우선(무훈련 sanity 포함) + 소형 진단, 그 후 B.** A(동일 config 재실행)와 C(STOP)는 기각.
- 이유: B0-B(6-10h)는 붕괴 원인 미진단 상태에서 같은 recipe 계열을 900 step로 확대하는 위험이 있고, metric 민감성(P)이 확인 전이면 PASS/STOP 어느 결론도 해석 불가하다. C는 underpowered screening + recipe confound 상태에서의 false-negative 일반화라 prereg §8.2가 금지한 확장이다. A는 B0-A 보고서 스스로 금지한 "같은 setting 재실행"이다.
- 권고 순서와 중단 조건:
  1. **(0) 무훈련 P0 sanity** — native mT5 encoder memory(자체 encoder, E0 §3.1에서 external 경로 delta 0.0 확인) + frozen decoder + 학습 없이 val20 Δshuffled_copy만 계산(수 분, 학습 0). **P0조차 양수 방향을 못 만들면 metric 또는 cross-attention 경로 결함 → 트랙 재설계/STOP 상향.**
  2. **(1) collapse 진단**(새 사전등록, ≤1 CPU-h): seed 20261110 lora arm에서 dropout 대칭화·LoRA LR·checkpoint 시점을 소기 변수로 분리. **recipe 내 안정화가 2회 실패하면 lora arm을 B0-B에서 제외하고 F/P/M 3-arm으로 NARROW.**
  3. **(2) P/M 20/20 통제**(새 사전등록, ~1 CPU-h): P-F(native encoder memory 직주입, adapter bypass)와 M(mean-memory). **P의 Δshuffled_copy CI lower > 0이 아니면 metric 민감성 부재 → mT5 트랙 STOP 권고로 상향.**
  4. (0)-(2) 통과 시 → B0-B 사전등록서 작성 → 사용자 승인 → B0-B.

### Q7. B0-B 설계

- **판정: conditional.** 규모·arm 구성 방향은 적정(F5: n=95에서 paired MDE ≈ 0.031/0.045 — 현 threshold 검증 가능), 단 선행 조건과 정의가 필요하다.
- 근거: prereg §9(300/95, F/L/P/M, 3 seeds, ~900 updates, primary Δshuffled_copy, P valid + L CI lower>0 + L ≥ 25% of P + L>F + real<memfree).
- P/M 정의 제안:
  - **P (native positive)**: mT5-small **자체 encoder**를 동일 source·동일 tokenizer로 통과시킨 last hidden을 `encoder_outputs`로 직주입(E0 §3.1에서 native/external 경로 loss·logits delta 0.0 확인). decoder 쪽은 LoRA 학습. P의 역할은 metric 민감성 검증("잘 인코딩된 memory는 양수 Δ를 만들 수 있는가")이며, P-F(무학습 frozen decoder 버전)를 (0)으로 먼저 무상 확인.
  - **M (memory-free/mean)**: **mean-memory = train 문서들의 adapter 출력 memory를 위치별 평균**(동일 경로·동일 길이 crop, on-manifold negative)을 1차로, zero-memory는 OOD(직전 검토 §2.2)라 진단 보조로만. gate: 같은 문서·같은 target에서 `real_ce < memfree_ce`.
- DoD 추가 제안: 계층적 문서×seed bootstrap 병기 + seed 범위 표기(F6), generation 기록 필드 전부(F7), checkpoint 정책 사전 고정(붕괴 진단 결과를 반영해 새 사전등록에서 결정), mask audit 결과 반영(F4 — mask 정의 변경이 필요하면 이 사전등록에서 확정).
- 다음 단계: (1) 위 정의로 B0-B 사전등록서 초안 작성(실행은 별도 승인), (2) threshold는 현 prereg 값 유지, (3) B0-B PASS/STOP 문구에 P0/P/M 선행 조건 명시.

### Q8. Must-fix (B0-B 또는 B0-A 계열 재실행 전, ranked)

- **판정: agree** (요청 형식대로 5개 ranked list 제시).
- **MF-1 (Blocker) 붕괴 진단 + 학습 모드 대칭 고정**: F1/F2. dropout 대칭화 유무·LoRA LR·checkpoint 시점을 새 사전등록으로 고정하고 lora arm 1회 재학습으로 원인 분리. B0-B의 모든 학습 arm에 선행.
- **MF-2 (Blocker) 무훈련 P0 metric sanity**: native encoder memory + frozen decoder로 Δshuffled_copy 양수 방향 확인(학습 0). metric 민감성이 없으면 이후 모든 학습 계획이 무의미. E0 wiring(delta 0.0)이 이미 경로를 보증하므로 비용 극소.
- **MF-3 (High) copyable mask 감사**: 공백 제거 substring 규칙의 표본 정밀도 측정(예: mask=1 토큰 100개 수기 검증)과 coverage 0.8246의 실질 보고. 규칙 변경은 새 사전등록으로. F4.
- **MF-4 (High) generation 기록 완성**: prereg §7 항목(cap hit, repeated-4gram, char F1, grounded no-new) 구현 — 학습 불요. F7.
- **MF-5 (Medium) 계층적 통계 보고**: 문서×seed bootstrap 병기 + seed 분산 명시(판정 규칙·threshold 불변). F6.

### Q9. 100-step / 20-doc 문제

- **판정: conditional.** 확장 금지는 **절차(rule)로** 시행하고, 표본 수치는 참고치로 제시한다.
- 근거: prereg §8.2는 NO_SIGNAL조차 "bridge 전체 영구 STOP으로 일반화하지 않는다"고 못박았고, INCONCLUSIVE는 더욱 그렇다. 수치로는 F5 — paired 기준 유의 탐지에 약 68문서, 80% power에 약 76문서(δ=0.05, SD 0.156 가정), arm 기준 약 35-40문서. 즉 20문서는 δ=0.05 스크린에 구조적으로 부족했고, B0-B의 95 eval 문서는 적정이다. update 수도 100(=5 epoch)에서 루프 디코딩 + real CE 7.7-8.1로 underfit이 명백하며, 900 update(3 epoch/300문서)가 최소 출발점이다. 단 이 변경은 B0-A에 소급되지 않는다 — 모두 새 사전등록 사항이다.
- 다음 단계: (1) "B0-A는 decoder LoRA 효과 부재의 증거가 아니다"를 후속 문서의 고정 문구로 채택, (2) 표본 확장은 B0-B 사전등록에서만, (3) 100-step 결과를 recipe 진단의 입력으로만 사용.

### Q10. Role probing

- **판정: defer.**
- 근거: MF5는 원래 "B0 이후"였다. B0-A의 INCONCLUSIVE는 probing 우선순위를 올리지 않는다 — 오히려 decoder adaptation이 작동 상태가 아니고, P/M으로 metric 유효성도 확인 전이므로 "역할" probing의 해석 기반이 아직 없다. F4(mask 과잉 관대)는 probing 설계의 token-type baseline 요구(직전 검토 §2.7)를 오히려 강화한다.
- 다음 단계: (1) 현행 보류 유지(B0-B 이후 별도 예산), (2) probing 재설계 요구사항(직전 검토 §2.7: native offset, token-type baseline, BH-FDR, 문서 bootstrap)을 결정 문서에 보존, (3) 이번 라운드에서 probing 자원 배정 없음.

### Q11. Metric audit

- **판정: conditional.**
- 근거: B0-B 최소 요건은 (a) MF-3 mask 정밀도 감사, (b) MF-4 generation 기록, (c) primary 유지 조건 = P arm 유효 동시 충족(현 B0-B PASS 규칙에 이미 포함 — 유지). Δshuffled_copy를 B0-B primary로 유지하는 것은 conditional yes — mask 정의 확정이 선행이고, 보조(Δshuffled_full, real/memfree) 병기 유지. Stage C/B2 전에는 preservation·required-slot recall·entity audit 전체(MF6 전항)와 no-new/preservation 분리 표기가 필요하며 production `eval/slot_verify.py` 미수정 원칙은 유지된다(본 검토가 git log로 미수정 재확인).
- 다음 단계: (1) mask 감사 결과를 새 사전등록에 첨부, (2) B0-B 보고서 템플릿에 secondary/exploratory 구분 필드 추가, (3) Stage C 이전 metric audit을 별도 사전등록 항목으로 고정.

### Q12. 최종 판정

- **판정: NARROW.**
- 허용할 실험: (a) 무훈련 P0 native-encoder metric sanity, (b) collapse 진단 1회(새 사전등록, lora arm 1 seed 중심), (c) P/M 20/20 통제(새 사전등록), (d) 구현 완성·문서화(MF-3/4/5), (e) B0-B 사전등록서 작성(실행은 별도 승인).
- 금지할 실험: B0-B 즉시 실행, B1/B2/Stage C, T5Gemma2 재개(D-108 STOP 유지), test 163 사용(어떤 경로로도), P1 데이터, B0-A 결과를 본 뒤 threshold/seed/donor/step 변경, 동일 config B0-A 재실행, B0-A를 bridge STOP 또는 제품 품질의 근거로 사용.
- 최대 compute: (a)-(d) 합산 **≤ 약 3 CPU-h**(P0 sanity ~0.2h, 진단 ≤1h, P/M 20/20 ~1h, 문서화 포함). B0-B는 별도 승인 시 6-10h(CPU only, 현 요청서 §11.4 기준 유지).
- 다음 decision gate: (a)-(c) 결과 보고서 + 새 B0-B 사전등록서 → **사용자 승인**. 게이트 통과 조건(예시): P0/P에서 Δshuffled_copy 양수 CI, 진단으로 안정 recipe 확정, M에서 real<memfree.
- test 163의 지위: **sealed 유지.** 본 검토에서도 어떤 형태로도 사용하지 않았다.

---

## 4. 요청서 §13에 대한 직접 답변

1. **B0-A를 신뢰할 수 있는가?** — 기록으로서는 신뢰한다: 수치·provenance·판정 로직이 독립 재계산으로 재현됐고(§1, F8), 사전등록 준수도 확인된다. 다만 **"treatment 효과 추정"으로서의 L arm은 신뢰할 수 없다** — F1(2/3 seed 공백 루프)과 F2(dropout 비대칭)가 해석을 제한한다. 폐기 불요, 동일 config 재실행 불요. frozen arm 결과와 붕괴 관찰은 진단의 입력으로 보존한다.
2. **다음 실험은?** — **native positive/memory-free only(D) + 무훈련 P0 sanity + collapse 진단**을 먼저, B0-B는 그 후(Q6). STOP은 근거 부족으로 기각, B0-B 즉시 실행도 기각.
3. **사전등록 조건과 중단 조건?** — 각 단계(Q6 1-4)에 명시: P0/P 실패 → 트랙 STOP 상향, 진단 2회 실패 → lora arm 제외 3-arm NARROW, 전부 통과 → B0-B 새 사전등록 + 사용자 승인. 모든 단계에서 threshold·seed·donor·step 무변경, test 163·P1·T5Gemma2 금지 유지.

### 잘못된 전제 (교정 권장)

1. "LoRA generation collapse"를 lora 고유의 실패로 읽은 것 — 실제로는 양 arm 120/120이 cap 루프이고, lora 고유 부분은 2/3 seed의 루프 토큰 공백 이동이다(F1).
2. copy coverage 0.8246을 "guard 통과 = metric 건강"으로 읽은 것 — mask가 과잉 관대해 coverage 자체가 과대계수다(F4).
3. "EOS 0/60"을 결함 신호로 읽은 것 — 레이블에는 EOS가 있고 100 step로 부족한 것이다(F3, *tokenizer 표준 동작 근거).
4. frozen vs lora train CE 비교 가능성 — 학습 dropout 모드가 달라 비교 불가다(F2).

---

## 5. 최종 판정 (요청 형식)

```text
최종 판정: NARROW
승인 범위: 무훈련 P0 metric sanity / collapse 진단 1회(새 사전등록) / P·M 20/20 통제(새 사전등록)
           / 구현·문서화(MF-3,4,5) / B0-B 사전등록서 작성(실행 별도 승인)
금지 범위: B0-B 즉시 실행, B1/B2/Stage C, T5Gemma2 재개(D-108), test 163, P1,
           B0-A 이후 threshold·seed·donor·step 변경, 동일 config B0-A 재실행
최대 compute: 선행 진단·통제 합산 ≤ ~3 CPU-h (CPU only) / B0-B는 승인 시 6-10h
Must-fix (ranked):
  1. 붕괴 진단 + 학습 모드(dropout) 대칭 고정 (Blocker)
  2. 무훈련 native-encoder P0 metric sanity (Blocker)
  3. copyable mask 감사 — 공백 제거 substring 규칙 정밀도 (High)
  4. generation 기록 필드 완성 — cap hit/4gram/char F1/grounded (High)
  5. 계층적 문서×seed bootstrap 병기 (Medium)
잘못된 전제: collapse=lora 고유 실패 아님(F1) / coverage 0.8246=metric 건강 아님(F4)
             / EOS 0/60=wiring 결함 아님(F3) / train CE cross-arm 비교 불가(F2)
```
