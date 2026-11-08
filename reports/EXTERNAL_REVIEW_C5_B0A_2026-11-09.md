# C5 mT5 B0-A — 직전 3-AI 검토 이후 진행 결과 검토요청서

- 작성일: 2026-11-09
- 작성 기준 HEAD: `c66f17c` (`results: record C5 B0-A inconclusive result`)
- 직전 검토 기준: `bb8bf70` (`docs: add C5 layer-plan 3-AI review prompts and dispatch`)
- **검토 기준: Hoplite 스레드 생성 시점의 origin/main HEAD** (이 문서가 포함된 최신 커밋)
- 대상: EG2 layer19 → mT5-small decoder adaptation B0-A
- 상태: **검토용**. B0-A는 실행 완료됐고, B1/B2/Stage C는 미승인·미실행이다.
- test 163: **sealed**, 사용하지 않음. P1 데이터: 사용하지 않음. T5Gemma2: D-108 STOP 유지.

---

## 0. Reviewer instructions

1. 이 문서를 **처음부터 끝까지 직접 읽어라**. 요약·발췌·다른 모델의 답을 근거로 삼지 말라.
2. 저장소 접근이 가능하면 아래 경로의 원문을 확인하라. 불가능하면 이 문서의 표만으로 판단하라.
3. **학습·평가를 실행하지 말라.** test 163을 열지 말라. P1 데이터를 사용하지 말라.
4. **서브에이전트/추가 LLM을 호출하지 말고 직접 검토하라.**
5. 각 질문 Q1~Q12에 대해 **판정(agree / disagree / conditional / defer) + 근거 + 권장 다음 단계 1~3개**를 적어라.
6. 최종 판정은 **STOP / NARROW / CONTINUE** 중 하나로 하고, 승인 범위와 중단 조건을 명시하라.
7. 결과를 본 뒤 threshold를 바꾸자는 제안은 하지 말라. 필요하면 **새 사전등록**으로 분리하라.
8. 보고서 파일을 작성하라:
   `docs/hoplite/c5_b0a_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q12 판정 표와 Must-fix를 요약하라.

---

## 1. TL;DR

### 1.1 지금의 한 줄

> **B0-A는 “decoder LoRA가 EG2 memory의 내용 선택성을 개선하는가”를 20문서/3seed/100update로 screening했지만, 결과는 INCONCLUSIVE였고 LoRA arm의 generation은 크게 붕괴했다.**

### 1.2 직전 검토 이후 변경

| 시점 | 사건 | 결과 |
|---|---|---|
| `bb8bf70` | 3-AI layer plan review | GLM CONTINUE(조건부), Opus NARROW, Sol NARROW → 종합 NARROW |
| `dddb9da` | E0 native tokenizer/wiring audit | content ID 400/400 일치, 차이는 EOS 1개 |
| `58b2bae` | 2-arm LoRA runner smoke | 64/64 modules, zero-LoRA delta 0.0 |
| `07bf9ea` | B0-A metric/donor/bootstrap/generation 구현 | metric smoke PASS |
| `c66f17c` | B0-A 20/20 × 3 seeds 실행 | **INCONCLUSIVE**, LoRA generation collapse |

### 1.3 현재 상태

| 항목 | 상태 |
|---|---|
| B0-A | **실행 완료, INCONCLUSIVE** |
| B1 layer sweep | **미승인·미실행** |
| B2 mT5 vs UMT5 | **미승인·미실행** |
| Stage C 300문서 | **미승인·미실행** |
| test 163 | **sealed** |
| A1 native pilot300 | frozen fallback/reference, 제품 승인 아님 |
| T5Gemma2 bridge | D-108 STOP 유지 |

### 1.5 용어와 지표

| 용어 | 정의 |
|---|---|
| EG2 | EmbeddingGemma 2. 24 layers, hidden 512, 4 heads, output projection 768. B0-A는 layer19의 512d hidden을 사용 |
| F (frozen) | mT5-small decoder를 freeze하고 adapter만 학습 |
| L (LoRA) | F에 decoder self/cross-attention q/k/v/o LoRA를 추가 |
| P (native positive) | native mT5 encoder + LoRA. *B0-A에는 없음* |
| M (memory-free/mean) | memory를 0 또는 평균으로 대체. *B0-A에는 없음* |
| copyable mask | target summary token 중 source passage에 surface-match되는 token |
| `Δshuffled_copy` | copyable target token에서 `loss(shuffled donor prefix) − loss(real prefix)`. **양수 = real prefix가 더 낮은 loss** |
| copy coverage | target token 중 copyable mask가 1인 비율. B0-A 평균 **.8246** |
| document bootstrap | 문서 단위로 1,000회 resample한 평균의 95% percentile CI |
| INCONCLUSIVE | POSITIVE_SIGNAL도 NO_SIGNAL도 아닌 상태 |

B0-A의 사전등록 판정 규칙:

```text
POSITIVE_SIGNAL = mean Δshuffled_copy >= .05
                  AND CI lower > 0
                  AND L > F
                  AND 2/3 seeds > 0
NO_SIGNAL       = mean <= 0 AND CI upper < .05
INCONCLUSIVE    = otherwise
```

### 1.6 검토에서 가장 중요한 질문

1. B0-A의 **INCONCLUSIVE가 올바른 해석**인가?
2. LoRA generation collapse 때문에 B0-A의 CE 결과를 **해석 불가**로 봐야 하는가?
3. 다음은 **B0-A 수리**, **B0-B 4-arm**, **mT5 track 중단** 중 무엇인가?

---

## 2. 직전 3-AI 검토의 결론과 Must-fix

### 2.1 판정

| 검토자 | 판정 | 승인 범위 |
|---|---|---|
| GLM 5.3 Flash max | CONTINUE — 조건부 | M1/M2 후 B0 |
| Opus 5.5 medium | NARROW | 통제된 단일 B0 |
| Sol 6.1 xhigh | NARROW | E0 + matched B0 |
| **종합** | **NARROW** | E0 + 단일 B0만 |

### 2.2 공통 Must-fix

| # | 지적 | 요구 |
|---|---|---|
| MF1 | native tokenizer provenance | EG2 native vs legacy 비교, native cache |
| MF2 | mT5 LoRA attach | `q/k/v/o`, 64 modules assert, zero-LoRA 확인 |
| MF3 | B0 matched arms | frozen / LoRA / native positive / memory-free·mean |
| MF4 | B0 DoD | `Δshuffled_copy`, 복수 length-matched donor, 문서×seed bootstrap, inconclusive branch |
| MF5 | role probing | native offset, shortcut baseline, FDR, B0 이후 |
| MF6 | metric audit | no-new와 preservation 분리, entity audit |
| MF7 | scope | Stage C 제외, B1/B2 새 decision, A1/T5Gemma2 분리 |

### 2.3 직전 검토의 핵심 경고

- Stage A는 **underfit**이므로 “frozen decoder 병목”의 인과 증거가 아니다.
- B0는 decoder LoRA·문서 수·tokenizer를 동시에 바꾸면 원인 귀속 불가.
- 20문서/100 step/3 seeds는 underpowered이며, 실패 시 bridge 전체 STOP으로 일반화하면 안 된다.
- layer19는 “best”가 아니라 fixed anchor다.
- `Δzero`는 **out-of-distribution**이므로 memory-use 증거가 아니다.

---

## 3. 직전 검토 이후 실제로 한 일

### 3.1 E0 — native tokenizer / wiring audit (`dddb9da`)

#### Tokenizer

- 대상: `data/models/embeddinggemma-2-f9972ac2` (native) vs `data/models/t5gemma-2-270m-270m` (legacy)
- 둘 다 `GemmaTokenizer`, vocab **262,144**
- 300 train + 100 val, 총 **400문서**
- prompt `summarize: `, max 1,024

| 항목 | 결과 |
|---|---:|
| full ID sequence 일치 | 0 / 400 |
| **content ID sequence 일치** | **400 / 400** |
| content token mismatch | **0** |
| character mismatch | **0 / 498,455** |
| digit-span mismatch | **0 / 12,538** |
| native 길이 − legacy | **+1 token (모든 문서)** |
| native EOS | **400 / 400** |
| legacy EOS | 0 / 400 |
| truncation | 0 / 400 both |

**해석**: 직전 검토에서 우려한 “T5Gemma2 tokenizer ID가 EG2 PLE를 광범위하게 오염시킨다”는 **content ID 기준으로는 재현되지 않았다**. 실제 차이는 **native EOS 1 token**이다.

#### native layer19 cache

- 경로: `data/wave2c/eg2_native_layer19/layer19`
- train 300 / val 100, layer19, **512d**, **401MB**
- 추출 **386.9초**
- `tokenizer_class: GemmaTokenizer`, `test_split_used: false`

#### legacy vs native hidden

| split | cosine mean | p01 | cosine < .95 |
|---|---:|---:|---:|
| train | **.991352** | .927518 | 2.5% |
| val | **.991501** | .929249 | 2.4% |

EOS 하나가 추가되어도 **약 2.4% token은 cosine < .95**로 달라진다. native cache를 쓰는 이유는 남아 있다.

#### mT5 wiring

| 항목 | 결과 |
|---|---:|
| native encoder vs external `encoder_outputs` loss | 12.603192 both |
| loss delta | **0.0** |
| logits max delta | **0.0** |
| allclose(atol 1e-5) | **true** |
| encoder hidden shape | `[1, 256, 512]` |

#### mT5 decoder LoRA inventory

- decoder linear modules **88**
- `q` 16 / `k` 16 / `v` 16 / `o` 16 → **64**
- legacy `q_proj/k_proj/v_proj/o_proj` matches **0**
- 실제 이름: `decoder.block.0.layer.0.SelfAttention.q`, `...EncDecAttention.q` 등

**해석**: T5Gemma2용 `q_proj` naming과 `model.decoder` prefix를 mT5에 그대로 쓰면 **0 modules**가 붙는다. 이 blocker는 runner에서 교체했다.

### 3.2 2-arm runner smoke (`58b2bae`)

- `runner/c5_mt5_lora_b0.py`
- mT5 decoder q/k/v/o **64/64** attach
- LoRA **458,752** params, adapter **526,336**
- zero-output LoRA가 frozen forward를 정확히 재현:
  - loss **27.43998146057129** both
  - loss/logits delta **0.0**
  - allclose true, finite
- training/generation은 이 단계에서 **실행하지 않음**

### 3.3 B0-A 사전등록 (`2d2b581`)

- `docs/plan_c5_b0_prereg_v0_1.md`
- B0-A: train 20 / val 20 `val[5:25]`, F vs L, 3 seeds, 100 updates, 5 donors
- primary `Δshuffled_copy`
- copy coverage guard, 문서 단위 bootstrap
- B0-B: 300/95, 4 arms, 3 seeds, ~900 updates — **별도 승인**

### 3.4 Metric 구현 (`07bf9ea`)

구현 완료:

- copyable target token mask
- 5 length-matched donors
- real/wrong prefix crop `K=min`
- `Δshuffled_copy` / `Δshuffled_full`
- 문서 단위 bootstrap 1,000회
- copy coverage guard
- val20 greedy generation
- B0-A train path

metric smoke(2문서/2donor)에서 frozen=LoRA(zero-init), `mean_delta_shuffled_copy -0.14960`, copy coverage .78427; **성능 결과 아님**.

---

## 4. B0-A 실행 결과

### 4.1 설정

| 항목 | 값 |
|---|---|
| train / val | **20 / 20** |
| val | `split["val"][5:25]` — Stage A val 5개 제외 |
| arms | **F** adapter-only, **L** adapter + decoder LoRA |
| seeds | 20261108 / 20261109 / 20261110 |
| updates | **100** |
| donors | **5** length-matched |
| LoRA | r8 α16 dropout .05, 64 modules |
| test | 미사용 |

### 4.2 핵심 수치

| arm | mean `Δshuffled_copy` | document bootstrap 95% CI | positive seeds |
|---|---:|---|---:|
| **F (frozen)** | **+0.007810** | [-0.037997, +0.051194] | 1 / 3 |
| **L (LoRA)** | **+0.021751** | [-0.028004, +0.067209] | 2 / 3 |

| 비교 | mean | 95% CI |
|---|---:|---|
| **L − F** | **+0.013942** | [-0.052508, +0.078599] |

- copy coverage: **.8246** both
- copy guard failed: **false** both
- **B0-A 판정: INCONCLUSIVE**
  - LoRA mean은 `.05` screen threshold에 미달
  - CI가 0 포함
  - L−F도 CI가 0 포함

### 4.3 seed별

| seed | F `Δshuffled_copy` | L `Δshuffled_copy` | L train CE last |
|---|---:|---:|---:|
| 20261108 | -0.002855 | +0.033865 | 7.1412 |
| 20261109 | +0.033376 | +0.051284 | 7.4557 |
| 20261110 | -0.007092 | -0.019894 | 7.6252 |

F train CE last: 6.5401 / 7.1140 / 6.8337.

### 4.4 Generation

| arm | n | nonempty | EOS |
|---|---:|---:|---:|
| F | 60 | **60 / 60** | 0 / 60 |
| L | 60 | **22 / 60** | 0 / 60 |

LoRA seed별 nonempty:

- 20261108: **2 / 20**
- 20261109: **20 / 20**
- 20261110: **0 / 20**

**LoRA generation collapse**가 관찰됐다. frozen도 EOS 0/60으로, 100-step 학습에서는 EOS가 나오지 않았다. 이 generation은 B0-A의 quality gate가 아니지만, CE metric 해석을 제한하는 **추가 실패 신호**다.

---

## 5. 직전 Must-fix 대응표

| Must-fix | 현재 상태 | 근거 |
|---|---|---|
| MF1 native tokenizer | **부분 완료** | E0 audit + native layer19 cache. content ID는 일치, EOS만 차이. B0-B native cache는 준비됨 |
| MF2 LoRA attach | **완료** | 64/64 modules, zero-LoRA delta 0.0 |
| MF3 matched arms | **부분** | F/L은 matched. native positive(P), memory-free/mean(M) 없음 |
| MF4 DoD | **부분** | copyable mask, 5 donors, docs bootstrap, guard 구현. P/M과 300/95 confirmatory 없음 |
| MF5 role probing | **미완** | B0 이후로 연기. native offset/FDR 미실행 |
| MF6 metric audit | **미완** | preservation/entity audit, production verifier 미수정 |
| MF7 scope | **유지** | Stage C/B1/B2 미실행, test sealed, T5Gemma2 STOP |

### 5.1 명시적 미이행

- B0-A에는 **native encoder positive control**이 없다.
- B0-A에는 **memory-free/mean-memory arm**이 없다.
- B0-A는 **20/20, 100 update, 3 seeds**로 underpowered하다.
- **role probing**은 실행하지 않았다.
- **metric/entity audit**는 실행하지 않았다.

이 문서는 이 미이행을 숨기지 않는다. 검토자는 B0-A를 “완전한 matched B0”로 간주하면 안 된다.

---

## 6. 무엇이 확립됐고, 무엇이 아닌가

### 6.1 확립

- EG2 native와 T5Gemma2 tokenizer의 content ID는 이 400문서에서 동일하다.
- native EOS 차이는 hidden state를 약 2.4% token에서 cosine < .95로 바꾼다.
- mT5 encoder와 external `encoder_outputs` wiring은 수치적으로 일치한다.
- mT5 decoder q/k/v/o LoRA는 64 modules에 정확히 붙고, zero-init에서 frozen forward와 동일하다.
- B0-A F/L 학습·copy metric·donor·bootstrap·generation 경로는 실제로 실행됐다.
- B0-A 결과는 **INCONCLUSIVE**이며, LoRA generation은 붕괴했다.

### 6.2 확립되지 않음

- decoder LoRA가 content selectivity를 개선했다는 인과 결론
- frozen decoder가 병목이라는 확정 결론
- layer19가 최적 layer라는 결론
- mT5 bridge가 불가능하다는 결론
- B0-A가 제품 품질 또는 A1 native와 비교 가능하다는 주장

특히 **B0-A는 P/M control이 없고 20문서/100 step**이므로, “LoRA가 안 됐다”는 결과를 **bridge 전체 STOP**으로 일반화하면 안 된다.

---

## 7. 현재 남은 confound

| confound | 영향 |
|---|---|
| 20 train / 20 val, 100 updates | 전력 부족, false negative 가능 |
| P/M control 부재 | LoRA 효과와 metric validity를 분리 불가 |
| 100-step LoRA generation collapse | CE와 generation 불일치 |
| dropout/train mode | frozen arm은 decoder eval, LoRA arm은 train mode; base dropout 차이 |
| single fixed layer19 | layer 일반화 불가 |
| validation 재사용 | Stage A와 B0-A가 같은 val 풀을 공유한다; B0-A는 `val[5:25]`만 사용 |
| copyable mask | surface substring 기반; 한국어 subword/정규화 한계 |
| 단일 seed별 20문서 | seed variance와 문서 variance 분리 제한 |
| metric audit 부재 | grounded/preservation/entity 미검증 |

---

## 8. 다음 선택지

| 안 | 내용 | 장점 | 단점 |
|---|---|---|---|
| **A. B0-A 수리** | 100 step 대신 더 많은 step/LR 안정화, generation collapse 원인 분리 | 저렴, 원인 분리 | 결과를 본 뒤 수정이므로 새 사전등록 필요 |
| **B. B0-B** | 300/95, F/L/P/M 4-arm, 3 seeds, ~900 updates | native positive·memory-free 포함, 전력 개선 | 6~10시간, 구현 추가 |
| **C. mT5 track 중단** | D-108과 유사하게 종료 | 비용 절감 | B0-A가 underpowered라 성급 |
| **D. narrower diagnostic** | native positive + memory-free만 20/20로 추가 | P/M 분리, 상대적으로 저렴 | decoding/generation collapse는 남음 |

**검토자가 판정할 것**: A/B/C/D 중 무엇이 맞는가, 그리고 그 판정의 **사전등록 조건**은 무엇인가.

---

## 9. 검토 질문

### Q1. E0 tokenizer 결론

E0에서 content ID 400/400 일치, native EOS만 차이를 확인했다. 이 결론이 직전 검토의 tokenizer 우려를 **어느 정도까지** 해소하는가? native cache를 B0-B에 쓰는 것이 여전히 필수인가?

### Q2. B0-A 설계의 적절성

B0-A는 20/20, F/L 2-arm, 3 seeds, 100 updates로 실행됐다. 직전 검토의 “matched control” 요구에 비추어 이 설계는 **screening으로 허용 가능**한가, 아니면 P/M 없이 실행한 것 자체가 설계 오류인가?

### Q3. INCONCLUSIVE 판정

F +.00781 CI [-.0380,+.0512], L +.02175 CI [-.0280,+.0672], L−F +.01394 CI [-.0525,+.0786]를 **INCONCLUSIVE**로 판정한 것이 맞는가? 통계·집계 오류가 있는가?

### Q4. Generation collapse

LoRA nonempty 22/60, seed10 0/20, EOS 0/60 both. 이 collapse는 ① 100-step underfit, ② LoRA/LR/dropout 불안정, ③ generation/eval 경로 문제, ④ decoder adaptation 자체의 실패 중 무엇으로 봐야 하는가? B0-A의 CE 결과를 해석 불가로 만들어야 하는가?

### Q5. B0-A가 말하는 것

B0-A는 decoder adaptation에 대해 어떤 결론을 허용하는가? “신호 없음”, “underpowered inconclusive”, “LoRA 불안정”을 구분해 달라.

### Q6. 다음 실험

A 수리 / B B0-B 4-arm / C stop / D native positive+memory-free only 중 무엇을 권고하는가? 이유와 중단 조건을 적어라.

### Q7. B0-B 설계

B0-B가 300/95, F/L/P/M, 3 seeds, ~900 updates라면 적절한가? P(native encoder + LoRA)와 M(memory-free/mean-memory)의 정확한 정의와 DoD를 제안하라.

### Q8. Must-fix

B0-B 또는 B0-A 수리 전에 반드시 고쳐야 할 항목을 1~5개로 ranked list로 제시하라.

### Q9. 100-step / 20-doc 문제

B0-A의 실패를 “decoder LoRA는 효과 없다”로 확장하지 않으려면, 최소 몇 문서·몇 update가 필요한가? 또는 그러한 확장 자체를 금지해야 하는가?

### Q10. Role probing

현 시점에서 layer role probing을 다시 꺼내야 하는가, 아니면 B0-B 이후까지 계속 보류해야 하는가? B0-A 결과가 role probing의 우선순위를 바꾸는가?

### Q11. Metric audit

Stage C/B2 이전에 preservation/entity audit를 어디까지 해야 하는가? B0-B의 primary metric을 `Δshuffled_copy`로 유지해도 되는가?

### Q12. 최종 판정

**STOP / NARROW / CONTINUE** 중 하나와 승인 범위를 제시하라. 다음을 명시하라.

- 허용할 실험
- 금지할 실험
- 최대 compute
- 다음 decision gate
- test 163의 지위

---

## 10. 답변 형식

각 Q1~Q12:

```text
Qn.
- 판정: agree / disagree / conditional / defer
- 근거: 이 문서·artifact의 구체 수치
- 다음 단계: 1~3개
```

마지막에:

```text
최종 판정: STOP / NARROW / CONTINUE
승인 범위:
금지 범위:
최대 compute:
Must-fix (ranked):
잘못된 전제:
```

---

## 11. 재현·산출물

### 11.1 주요 파일

| 경로 | 내용 |
|---|---|
| `docs/plan_c5_b0_prereg_v0_1.md` | B0-A/B0-B 사전등록 |
| `reports/C5_LAYER_PLAN_3AI_REVIEW_SYNTHESIS_2026-11-08.md` | 직전 3-AI 종합 |
| `reports/C5_E0_NATIVE_AUDIT_2026-11-09.md` | E0 audit |
| `reports/C5_B0_METRIC_IMPL_2026-11-09.md` | metric 구현 smoke |
| `reports/C5_B0A_2026-11-09.md` | B0-A 결과 |
| `reports/provenance/C5_b0a/aggregate.json` | B0-A 집계 |
| `reports/provenance/C5_b0a/s{seed}_{arm}.json` | 6개 individual 결과 |
| `runner/c5_mt5_lora_b0.py` | 2-arm runner |
| `runner/c5_b0a_aggregate.py` | 집계 |
| `data/wave2c/eg2_native_layer19/layer19` | native cache 401MB |

### 11.2 재현 명령

```bash
cd C:/code/unigem
.venv/Scripts/python.exe runner/c5_b0a_aggregate.py
```

### 11.3 사용하지 않은 것

- test 163: **미사용**
- P1 데이터: **미사용**
- T5Gemma2 bridge: **재개하지 않음**
- B1/B2/Stage C: **미실행**

### 11.4 compute

- CPU only, `torch.set_num_threads(6)`
- B0-A 6 unit: 각 약 5~6분, 총 약 32분
- GPU 미사용

---

## 12. Reviewer prohibition

- 학습·평가 실행 금지
- test 163 열람 금지
- P1 데이터 사용 금지
- repository 수정 금지 (지정 report 파일만)
- subagent/추가 LLM 호출 금지
- 결과를 본 뒤 threshold·seed·donor 변경 제안 금지

---

## 13. 요청하는 최종 판정

> **B0-A INCONCLUSIVE와 LoRA generation collapse를 확인한 지금, mT5 decoder adaptation 트랙을 STOP / NARROW / CONTINUE 중 어떻게 처리해야 하는가?**

특히 다음을 명시해 달라.

1. B0-A를 **신뢰할 수 있는가**, 아니면 **재실행 전 폐기**해야 하는가?
2. 다음 실험은 **B0-A 수리**, **B0-B 4-arm**, **native positive/memory-free only**, **stop** 중 무엇인가?
3. 그 실험의 **사전등록 조건과 중단 조건**은 무엇인가?
