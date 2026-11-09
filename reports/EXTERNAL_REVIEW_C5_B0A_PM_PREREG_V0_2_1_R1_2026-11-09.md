# C5 Phase 6 v0.2.1-r1 — External Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `0fce2e2` (`docs: add C5 Phase 6 v0.2.1-r1 contract repair`)
- 대상: `docs/plan_c5_b0a_pm_prereg_v0_2_1_r1.md` (552줄)
- data preflight: `reports/provenance/C5_b0a/m_cohort_preflight.json`
- 상태: **r1 review. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. Reviewer instructions

1. 이 문서를 처음부터 끝까지 직접 읽어라. 다른 모델의 답을 재사용하지 말라.
2. 저장소 접근이 가능하면 다음 원문을 확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v0_2_1_r1.md`
   - `docs/plan_c5_b0a_pm_prereg_v0_2_1_errata.md`
   - `reports/C5_B0A_PM_PREREG_V0_2_1_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/provenance/C5_b0a/m_cohort_preflight.json`
   - `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md`
   - `runner/c5_mt5_lora_b0.py`
   - `eval/tests/test_c5_b0_metric.py`
3. **학습·평가를 실행하지 말라.** test 163을 열지 말라. P1 데이터를 사용하지 말라.
4. **서브에이전트/추가 LLM을 호출하지 말고 직접 검토하라.**
5. 각 Q1~Q12에 대해 **판정(agree / disagree / conditional / defer) + 근거 + 다음 단계 1~3개**를 적어라.
6. 최종 판정은 **STOP / NARROW / CONTINUE** 중 하나로 하고, 승인 범위·금지 범위·compute cap을 명시하라.
7. 결과를 본 뒤 threshold·seed·donor·step·LR을 바꾸자는 제안은 하지 말라. 필요하면 **새 사전등록**으로 분리하라.
8. 보고서 파일을 작성하라:
   `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r1_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q12 판정 표와 Must-fix 요약을 포함하라.

---

## 1. TL;DR

> **v0.2.1은 3/3 NARROW였다. r1은 (a) factored decision contract, (b) M cohort data-only preflight/K_M=753, (c) debug/registered cap 분리, (d) PA acquisition label, (e) statistics constants를 추가한 text-only repair다. 이 문서는 r1이 남은 NARROW Must-fix를 실제로 닫았는지, 동결·구현·D0 mechanics debug를 승인할 수 있는지를 묻는다.**

| 항목 | 상태 |
|---|---|
| v0.1 | NARROW 3/3 |
| v0.2 | NARROW 3/3 |
| v0.2.1 | NARROW 3/3 |
| **v0.2.1-r1** | **작성 완료, 미승인** |
| Phase 6 실행 | **없음** |
| P0 | SENSITIVE_POSITIVE, descriptive |
| test 163 | sealed |

---

## 2. v0.2.1 3-AI Must-fix

### 2.1 Decision function

- `not_assessable`가 headline에서 사용되지 않음
- `INCONCLUSIVE_SMALL_N`이 도달 불가능한 dead cell
- P valid + PA path-fail cell 없음
- P path fail이 `P_STEP100_NOT_VALID`와 `ASSAY_INVALID` 사이에서 모순
- `MEAN_CONTRAST_ONLY` 정의 없음
- L_SIGNAL이 headline에서 숨음

### 2.2 M

- full-K `len(h) >= K_real` + contributor≥10이면 target eligible이 대략 train median 이하
- **common cohort ≥15/20이 구조적으로 불가능할 수 있음**
- M seed aggregation 규칙 없음
- M replay equality 없음
- M_NORM scale/qualified 표기

### 2.3 Cap

- 12 units ×100 = **1,200** = cap
- debug 4 arms ×5 = +20 updates, +4 units
- debug 포함 cap 산술 불가능

### 2.4 PA

- PA는 acquisition control이지 retention control이 아님
- `ADAPTER_REGIME_LOSS`는 인과적 이름
- PA_RETENTION null 가능

### 2.5 Statistics / stale

- CI percentile, n_boot, RNG seed, top-3 share, endpoint rule 미고정
- `documents_positive` vs `seeds_positive`
- v0.2 §12의 B0-B 금지 목록이 삭제된 label을 참조

---

## 3. r1 변경 요약

### 3.1 Data-only M preflight

실제 train20/val20 EG2 hidden length:

| 항목 | 값 |
|---|---:|
| train20 h median | 768.5 |
| val20 h median | 766.5 |
| K_M_L | **753** |
| L contributors | **16** |
| L target eligible | **15/20** |
| native contributors | 20 |
| native target eligible | 20 |
| common cohort | **15/20** |
| full-K L cohort (secondary) | **11/20** |

- full-K는 `M_NOT_EVALUABLE`이므로 **prefix 753**을 primary M으로 고정.
- full-K real CE는 secondary descriptive only.
- excluded 5:
  - `REPORT-news_r-00430-00001`
  - `REPORT-news_r-01127-00001`
  - `REPORT-news_r-02180-00001`
  - `REPORT-news_r-02804-00001`
  - `REPORT-news_r-03445-00001`

### 3.2 Factored decision contract

```text
validity_status
control_status
signal_status
flags
headline  # convenience only
```

Tri-state: true / false / not_assessable; strong Kleene.

#### validity_status

```text
any path/test false -> ASSAY_INVALID
any path/test NA -> NOT_ASSESSABLE
p false -> P_STEP100_NOT_VALID
p NA -> NOT_ASSESSABLE
pa false -> PA_STEP100_NOT_VALID
pa NA -> NOT_ASSESSABLE
m_evaluable false -> M_NOT_EVALUABLE
m_evaluable NA -> M_NOT_EVALUABLE
else VALID
```

P path fail → `ASSAY_INVALID`.
PA path fail → `PA_STEP100_NOT_VALID`.
`ADAPTER_REGIME_LOSS` 삭제.
`M_CONTROL_NOT_VALID` status 삭제.

#### control_status

```text
m_evaluable not true -> M_NOT_EVALUABLE
m_pass_l true -> M_CONTROL_PASS
m_pass_l false -> M_CONTROL_FAIL
else NOT_ASSESSABLE
```

#### signal_status

```text
n_signal NA -> NOT_ASSESSABLE
n_signal <15 -> INCONCLUSIVE_SMALL_N
required signal NA -> NOT_ASSESSABLE
l_signal true + M_CONTROL_PASS -> EXPLORATORY_L_SIGNAL
l_signal true + M_CONTROL_FAIL -> L_SIGNAL_M_CONTROL_FAIL
l_signal true + M_NOT_EVALUABLE -> L_SIGNAL_M_CONTROL_NOT_EVALUABLE
copy_only -> COPY_ONLY_WEAK
full_only -> FULL_ONLY_WEAK
M_CONTROL_PASS -> MEAN_CONTRAST_ONLY
M_CONTROL_FAIL -> NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE
else NOT_ASSESSABLE
```

- L flag는 headline과 별도 보존
- `INCONCLUSIVE_SMALL_N` n_min 15
- `MEAN_CONTRAST_ONLY` = M control pass but no donor signal

### 3.3 M

- L prefix **753**, contributors **16**
- P/PA prefix **512**, contributors 20
- common **15/20**
- seed별 M builder → seed 평균 → document bootstrap
- final checkpoint replay `atol=1e-5`
- M_CONTROL_PASS_L = POS AND NORM
- M_VALID = P and PA both POS and NORM

### 3.4 PA

- `PA_STEP100_NOT_VALID`
- PA = acquisition control
- random adapter step0 별도
- `PA_RETENTION` null 가능
- mT5 final hidden vs EG2 layer19 scale/geometry caveat

### 3.5 Cap

| 항목 | 값 |
|---|---|
| registered | 12 units / 1,200 updates / 2h / 6 threads |
| D0 | **0 optimizer updates**, ≤4 configs, ≤15min, separate |
| D1 optional | 4 arm-seeds × **1 update**, ≤20min, **별도 승인**, separate |
| registered cap과 debug | 분리 회계 |

### 3.6 Statistics

- n_boot 1,000
- percentile 2.5/97.5
- bootstrap seed 20261109
- seed-average before doc bootstrap
- `documents_positive` / `seeds_positive`
- top-3 share, leave-top-3-out
- 3-seed checklist 10항

---

## 4. P0 기준값

| split | mean Δcopy | CI | mean Δfull | positive docs |
|---|---:|---|---:|---:|
| train | +3.7617 | [1.8917, 5.6050] | +3.5027 | 14/20 |
| val | +5.2375 | [2.5013, 8.0753] | +5.2936 | 18/20 |

한계:

- val median 2.9739, top-3 share .4862
- untrained real CE 12.7/13.2 > ln|V| 12.43
- 20 val은 confirmatory holdout 아님
- P0는 native path sensitivity이지 EG2/decoder adaptation 증거 아님

---

## 5. 검토 질문

### Q1. Factored decision

r1의 `(validity_status, control_status, signal_status)` factored output과 tri-state Kleene이 실제로 total function인가? 빠진 cell, 모순, precedence 잔재가 있는가?

### Q2. Signal labels

`INCONCLUSIVE_SMALL_N`, `MEAN_CONTRAST_ONLY`, `COPY_ONLY_WEAK`, `FULL_ONLY_WEAK`, `L_SIGNAL_M_CONTROL_NOT_EVALUABLE`의 정의/우선순위가 executable한가? L flag가 항상 보존되는가?

### Q3. M preflight

K_M_L=753, 16 contributors, 15/20 targets, full-K 11/20 secondary가 정당한가? `M primary = target prefix`가 full-real-K 원칙을 얼마나 훼손하는가? 대안(`M_NOT_EVALUABLE` 수용)보다 나은가?

### Q4. M aggregation/replay

seed별 builder → seed 평균 → doc bootstrap, P/PA M_VALID, checkpoint replay `atol=1e-5`가 leakage-free이고 충분한가? 빠진 cohort/seed/replay 조건은?

### Q5. PA

PA를 acquisition control로 재정의하고 `PA_STEP100_NOT_VALID`로 바꾼 것이 충분한가? `PA_RETENTION` null/무정보를 gate로 쓰지 않는가?

### Q6. Cap

registered 12/1,200/2h와 D0 0-update, D1 1-update 별도 승인이 산술·승인 경계에서 맞는가? 2h wall-clock이 12 units에 현실적인가?

### Q7. Statistics

n_boot 1,000, CI percentile, bootstrap seed 20261109, seed-average-before-bootstrap, `documents_positive`/`seeds_positive`, top-3 share/leave-top-3-out이 executable한가?

### Q8. 남은 Must-fix

v0.2.1 3-AI Must-fix 중 아직 닫히지 않은 항목을 ranked list로 제시하라. r1이 새로 만든 문제가 있는가?

### Q9. 동결·구현 승인

r1을 동결하고 **구현 + unit tests + D0 zero-update mechanics debug**를 승인할 수 있는가? 구현 전 반드시 있어야 할 test/contract는 무엇인가?

### Q10. D1 / 3-seed

D1 1-update smoke와 3-seed를 별도 gate로 유지하는 경계가 충분한가? 3-seed launch checklist에 빠진 항목은?

### Q11. B0-B

r1 결과가 좋아도 B0-B/B1/B2/Stage C를 자동 승인하지 않는 경계가 유지되는가? B0-B 필요조건을 r1 label에 맞게 재진술하라.

### Q12. 최종 판정

**STOP / NARROW / CONTINUE**와 승인 범위를 제시하라.

- r1 동결
- 구현 + unit tests
- D0
- D1
- 3-seed
- 금지 범위
- 최대 compute
- test 163 지위

---

## 6. 답변 형식

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
r1 동결:
구현+unit tests:
D0:
D1:
3-seed:
금지 범위:
최대 compute:
Must-fix (ranked):
잘못된 전제:
```

---

## 7. Artifacts

| 경로 | 내용 |
|---|---|
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r1.md` | r1 |
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_errata.md` | v0.2.1 |
| `reports/C5_B0A_PM_PREREG_V0_2_1_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | v0.2.1 review |
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

> **r1이 v0.2.1 3-AI Must-fix를 충분히 닫았는가, 그리고 r1 동결·구현·unit tests·D0를 승인할 수 있는가?**

특히 다음을 명시해 달라.

1. factored decision/truth table의 남은 cell/모순
2. K_M_L=753 M preflight와 full-K secondary의 타당성
3. D0/D1/3-seed/B0-B 승인 경계
