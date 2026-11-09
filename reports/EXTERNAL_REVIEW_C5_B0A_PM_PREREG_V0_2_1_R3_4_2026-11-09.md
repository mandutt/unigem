# C5 Phase 6 v0.2.1-r3.4 — External Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `30b966d` (`docs: add C5 Phase 6 v0.2.1-r3.4 executable contract closure`)
- 대상: `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_4.md` (1,109줄)
- preflight: `reports/provenance/C5_b0a/m_cohort_preflight.json`
- preflight hash: **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`** (content SHA-256)
- 상태: **r3.4 review. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. Reviewer instructions

1. 이 문서를 처음부터 끝까지 직접 읽어라. 다른 모델의 답을 재사용하지 말라.
2. 저장소 접근이 가능하면 다음 원문을 확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_4.md`
   - `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_3.md`
   - `reports/C5_B0A_PM_PREREG_V0_2_1_R3_3_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/provenance/C5_b0a/m_cohort_preflight.json`
   - `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md`
   - `runner/c5_mt5_lora_b0.py`
   - `eval/tests/test_c5_b0_metric.py`
3. **학습·평가를 실행하지 말라.** test 163을 열지 말라. P1 데이터를 사용하지 말라.
4. **서브에이전트/추가 LLM을 호출하지 말고 직접 검토하라.**
5. 각 Q1~Q13에 대해 **판정(agree / disagree / conditional / defer) + 근거 + 다음 단계 1~3개**를 적어라.
6. 최종 판정은 **STOP / NARROW / CONTINUE** 중 하나로 하고, 승인 범위·금지 범위·compute cap을 명시하라.
7. 결과를 본 뒤 threshold·seed·donor·step·LR을 바꾸자는 제안은 하지 말라. 필요하면 **새 사전등록**으로 분리하라.
8. 보고서 파일을 작성하라:
   `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r3_4_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q13 판정 표와 Must-fix 요약을 포함하라.

---

## 1. TL;DR

> **r3.3은 1 CONTINUE(조건부) / 2 NARROW였다. r3.4는 §2.4 mixed L table, F/P M builder, `real_prefix_t` space, `n_signal 15`, `tail_driven` input, `adapter_lr`, T_proj 120/600, endpoint 1,440, PA veto rationale, independent golden vector를 text-only로 닫는 errata다. 이 문서는 r3.4가 실제로 freeze 가능한지, 구현·D0를 승인할 수 있는지, 그리고 구현 전에 v1.0 consolidated spec이 필요한지를 묻는다.**

| 항목 | 상태 |
|---|---|
| v0.1 | NARROW 3/3 |
| v0.2 | NARROW 3/3 |
| v0.2.1 | NARROW 3/3 |
| r1 | NARROW 3/3 |
| r2 | NARROW 3/3 |
| r3 | 2 CONTINUE 조건부 / 1 NARROW |
| r3.1 | 1 CONTINUE 조건부 / 2 NARROW |
| r3.2 | 1 CONTINUE 조건부 / 2 NARROW |
| r3.3 | 1 CONTINUE 조건부 / 2 NARROW |
| **r3.4** | **작성 완료, 미승인** |
| Phase 6 실행 | **없음** |
| P0 | SENSITIVE_POSITIVE, descriptive |
| test 163 | sealed |

---

## 2. r3.3 freeze blockers

1. §2.4 mixed true/false table이 `false`로 표기; §2.3은 `NA`.
2. §8.4는 F를 요구하지만 §8.1/§8.2 M builder에 F 없음.
3. P에 adapter가 없는데 `A(h_i)` 적용.
4. `h_i >= K_M` type 불명확.
5. `real_prefix_t` space(raw vs adapter output) 미정의.
6. `n_signal val20 / 0..20` vs L eligible 15.
7. `tail_driven` input endpoint/arm/variant 미정의.
8. `top3_share` descriptive-only인데 gate.
9. tail known-positive + null precedence.
10. `adapter_lr (PA only)` vs F/L adapter training.
11. T_proj phases 5/7 real/control factor 누락.
12. endpoint record count variants/copy-full 누락.
13. PA veto rationale 부재.
14. golden vector self-generated.
15. named-cell prerequisites 부족.
16. `ANDn`/`NOT3` domain 불명확.
17. zero-margin failure path.
18. P0 OOD caveat.

---

## 3. r3.4 변경 요약

### 3.1 §2.4 L table

```text
true,false  -> l_signal=NA, copy_only=true,  full_only=false
false,true  -> l_signal=NA, copy_only=false, full_only=true
```

- §2.3과 일치.
- `copy_only`/`full_only`는 `l_signal`보다 먼저 평가.
- `false+NA`는 `NOT_ASSESSABLE`.

### 3.2 F/P M builder

| arm | K_M | A | adapter |
|---|---:|---|---|
| F | 753 | adapter | trained |
| L | 753 | adapter | trained |
| P | 512 | identity | none |
| PA | 512 | adapter | random-init |

- `h_len_i >= K_M` (scalar).
- F M endpoint 존재.

### 3.3 `real_prefix_t`

```text
real_prefix_t := A(h_t)[:K_M]
M_NORM(t) = M_POS_MEAN * (||real_prefix_t||_F / ||M_POS_MEAN||_F)
```

- same adapter space.
- raw EG2 embedding과 adapter output 혼합 금지.

### 3.4 `n_signal`

```text
n_signal ∈ {NA, 0..15}
signal eligible cohort = 15 L-eligible val docs
val20 = descriptive only
n_signal=15 → MARGINAL_SIGNAL_COHORT=true
```

### 3.5 `tail_driven`

```text
arm = L
endpoint = copy
cohort = 15 signal-eligible docs
delta = control_copy_ce - real_copy_ce

top3_abs_share = sum(top3 |delta|) / sum(all |delta|)
top3_signed_share = descriptive only

if leave_top3_mean <= 0: true
elif leave_top3_mean is null or top3_abs_share is null: NA
elif top3_abs_share > .50: true
else: false
```

### 3.6 `adapter_lr`

```text
adapter_lr: 1e-3 for F, L, PA
lora_lr: 1e-4 for L, P, PA
P: no adapter
```

### 3.7 T_proj

- phase 5: **120 records/arm-seed**
- phase 7: **600 records/arm-seed**
- `T_proj` includes memory-kind factor 2.
- ≤96 min.

### 3.8 Endpoint identity

```text
15 targets × 3 seeds × 4 arms × 2 variants × 2 endpoints × 2 memory kinds
= 1,440 records
```

### 3.9 기타

- PA veto rationale
- independent golden vector
- named-cell prerequisites
- `ANDn`/`NOT3` scalar domain
- zero-margin `M_NOT_EVALUABLE`
- P0 OOD caveat
- 3-seed checklist 27항목

---

## 4. P0 기준값

| split | mean Δcopy | CI | mean Δfull | positive docs |
|---|---:|---|---:|---:|
| train | +3.7617 | [1.8917, 5.6050] | +3.5027 | 14/20 |
| val | +5.2375 | [2.5013, 8.0753] | +5.2936 | 18/20 |

한계:

- val median 2.9739, top-3 share .4862
- untrained real CE 12.7/13.2 > ln|V| 12.43
- P0 source_max_length=256; registered M 512
- trained P/PA/L 증거 아님

---

## 5. 검토 질문

### Q1. Total factored contract

r3.4의 validity/control/signal, ANDn, F1~F11, L tri-state, small-N precedence가 실제로 total/executable한가?

### Q2. L consensus / fixtures

§2.3, §2.4 9-pair table, fixture 16~18이 서로 일치하는가? mixed true/false가 `NA`로만 가는가?

### Q3. M preflight / cohort

K=753, 15/20 M, signal eligible 15, endpoint 15/15, full-K 11/20 secondary가 정당한가?

### Q4. M builder / M_NORM / endpoint / replay

F/L/P/PA builder, P identity, `real_prefix_t`, `M_NORM(t)`, endpoint 1,440, replay key/framing, golden vector가 충분한가?

### Q5. PA

PA acquisition 명명, `PA_STEP100_NOT_VALID`, `PA_RETENTION` 비gate, scale/geometry caveat, PA veto rationale이 충분한가?

### Q6. Cap / D0 / D1

registered 12×100=1,200, D0 0-update, D1 4×1, 8-phase T_proj, phase 5 120, phase 7 600이 산술·승인 경계에서 맞는가?

### Q7. Statistics

n_boot 1,000, CI percentile, bootstrap seed 20261109, documents_positive, 2/3 registered seeds, tail tri-state가 executable한가?

### Q8. 남은 Must-fix

r3.3 freeze blocker 중 아직 닫히지 않은 항목을 ranked list로 제시하라. r3.4가 새로 만든 문제가 있는가?

### Q9. 동결·구현 승인

r3.4를 동결하고 **구현 + unit tests + D0 zero-update mechanics debug**를 승인할 수 있는가? 구현 전 필수 test/contract는 무엇인가?

### Q10. D1 / 3-seed

D1 timing gate와 3-seed를 별도로 유지하는 경계가 충분한가? 3-seed checklist에 빠진 항목은?

### Q11. B0-B

r3.4 결과가 좋아도 B0-B/B1/B2/Stage C를 자동 승인하지 않는 경계가 유지되는가? B0-B predicate를 r3.4 label에 맞게 재진술하라.

### Q12. 최종 판정

**STOP / NARROW / CONTINUE**와 승인 범위를 제시하라.

- r3.4 동결
- 구현 + unit tests
- D0
- D1
- 3-seed
- 금지 범위
- 최대 compute
- test 163 지위

### Q13. Consolidation

r3.1~r3.4가 errata chain으로 누적되어 있다. 구현 전에 **v1.0 consolidated spec**(self-contained, normative only)을 만들고 그것을 1회 리뷰·freeze하는 것이 필요한가?

- 필요하다면 최소 목차와 traceability 방식
- r3.4를 그대로 구현 권위로 쓸 수 있는지
- errata chain 유지 vs 단일 spec 중 어느 쪽이 구현 오류 위험이 낮은지
- v1.0 review를 별도 round로 둘지

---

## 6. 답변 형식

각 Q1~Q13:

```text
Qn.
- 판정: agree / disagree / conditional / defer
- 근거: 이 문서·artifact의 구체 수치
- 다음 단계: 1~3개
```

마지막에:

```text
최종 판정: STOP / NARROW / CONTINUE
r3.4 동결:
구현+unit tests:
D0:
D1:
3-seed:
금지 범위:
최대 compute:
Must-fix (ranked):
v1.0 consolidation:
잘못된 전제:
```

---

## 7. Artifacts

| 경로 | 내용 |
|---|---|
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_4.md` | r3.4 |
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_3.md` | r3.3 |
| `reports/C5_B0A_PM_PREREG_V0_2_1_R3_3_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | r3.3 review |
| `reports/provenance/C5_b0a/m_cohort_preflight.json` | M preflight |
| `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md` | P0 |
| `runner/c5_mt5_lora_b0.py` | runner |
| `eval/tests/test_c5_b0_metric.py` | tests |

---

## 8. 금지

- 학습·평가 실행 금지
- test 163 열람 금지
- P1 사용 금지
- repository 수정 금지 (지정 report 파일만)
- subagent/추가 LLM 호출 금지
- 결과를 본 뒤 threshold/seed/donor/step/LR 변경 금지
- Phase 6/B0-B/B1/B2/Stage C 자동 진행 금지

---

## 9. 요청하는 최종 판단

> **r3.4가 r3.3 freeze blocker를 충분히 닫았는가, r3.4 동결·구현·unit tests·D0를 승인할 수 있는가, 그리고 구현 전에 v1.0 consolidated spec이 필요한가?**

특히 다음을 명시해 달라.

1. F/L/P/PA builder와 endpoint 1,440의 실행 가능성
2. `n_signal 15`/`tail_driven`/T_proj 120·600의 정합성
3. v1.0 consolidation의 필요성과 최소 목차
