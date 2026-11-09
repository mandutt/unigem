# C5 Phase 6 v0.2.1-r3 — External Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `e779e93` (`docs: add C5 Phase 6 v0.2.1-r3 contract closure`)
- 대상: `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3.md` (795줄)
- preflight: `reports/provenance/C5_b0a/m_cohort_preflight.json`
- preflight hash: **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`** (committed blob, LF)
- 상태: **r3 review. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. Reviewer instructions

1. 이 문서를 처음부터 끝까지 직접 읽어라. 다른 모델의 답을 재사용하지 말라.
2. 저장소 접근이 가능하면 다음 원문을 확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3.md`
   - `docs/plan_c5_b0a_pm_prereg_v0_2_1_r2.md`
   - `reports/C5_B0A_PM_PREREG_V0_2_1_R2_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
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
   `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r3_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q12 판정 표와 Must-fix 요약을 포함하라.

---

## 1. TL;DR

> **r2는 3/3 NARROW였다. r3는 NA path fail-open, `M_NOT_EVALUABLE` dead label, signal validity guard 비대칭, signal/M cohort 혼동, M copy endpoint, stale hash, circular checklist M_VALID, D1 timing, P0 256/512, `m_pass_l`/mixed false+NA를 text-only로 닫는 r3다. 이 문서는 r3가 남은 Must-fix를 실제로 닫았는지, 동결·구현·D0를 승인할 수 있는지를 묻는다.**

| 항목 | 상태 |
|---|---|
| v0.1 | NARROW 3/3 |
| v0.2 | NARROW 3/3 |
| v0.2.1 | NARROW 3/3 |
| r1 | NARROW 3/3 |
| r2 | NARROW 3/3 |
| **r3** | **작성 완료, 미승인** |
| Phase 6 실행 | **없음** |
| P0 | SENSITIVE_POSITIVE, descriptive |
| test 163 | sealed |

---

## 2. r2 3-AI Must-fix

1. `test_split_used=NA`와 `pa_step100_path_ok=NA`가 VALID로 새는 fail-open.
2. `M_NOT_EVALUABLE`가 validity/control에 중복되어 `L_SIGNAL_M_CONTROL_NOT_EVALUABLE` dead.
3. signal validity guard가 `l_signal`에만 적용되어 copy-only/full-only/mean/no가 invalid assay에서 나옴.
4. signal cohort(val20)와 M cohort(15 longest)가 불명확; M copy endpoint 0-margin.
5. 3-seed checklist stale `07c3...` hash, circular prelaunch `M_VALID=true`.
6. D1 timed phases/seed/projection 미정의; P0 256 vs 512 caveat; `m_pass_l` derivation 없음; mixed false+NA aggregation 충돌.

---

## 3. r3 변경 요약

### 3.1 Validity

- `M_NOT_EVALUABLE`를 validity에서 **삭제**; control에만.
- known failure first:
```text
assay_path_ok=false
or p0_path_ok=false
or test_split_used=true
or p_step100_path_ok=false
  -> ASSAY_INVALID
```
- NA fail-closed:
```text
assay/p0/p_step100/test_split NA -> NOT_ASSESSABLE
```
- PA:
```text
pa_step100_path_ok=NA -> NOT_ASSESSABLE
pa_step100_path_ok=false -> PA_STEP100_NOT_VALID
pa_valid=false -> PA_STEP100_NOT_VALID
```

### 3.2 Control

```text
m_evaluable = AND3(cohort_ok, endpoint_ok, seed_ok, replay_ok)
m_valid = AND3(P/PA POS, P/PA NORM)
m_pass_l = AND3(m_pass_pos_l, m_pass_norm_l)

if m_evaluable not true -> M_NOT_EVALUABLE
elif p_valid/pa_valid not true -> M_NOT_EVALUABLE
elif m_valid false -> M_CONTROL_INVALID
elif m_valid NA -> NOT_ASSESSABLE
elif m_pass_l true -> M_CONTROL_PASS
elif m_pass_l false -> M_CONTROL_FAIL
else NOT_ASSESSABLE
```

- `m_evaluable`에서 p/pa 제거; control에서 별도 검사.
- mixed false+NA = false-dominant AND3.
- `M_CONTROL_NOT_VALID`는 사용하지 않음.

### 3.3 Signal

- signal cohort = **val20**; M cohort = **15 longest-of-20**.
- `n_signal` = val20 copy/full valid docs.
- small-N:
  - `INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL`
  - `_WITH_COPY_ONLY`
  - `_WITH_FULL_ONLY`
  - `INCONCLUSIVE_SMALL_N`
- validity invalid:
  - `L_SIGNAL_VALIDITY_INVALID`
  - `COPY_ONLY_VALIDITY_INVALID`
  - `FULL_ONLY_VALIDITY_INVALID`
  - else `NOT_ASSESSABLE`
- valid-only:
  - `COPY_ONLY_WEAK`
  - `FULL_ONLY_WEAK`
  - `MEAN_CONTRAST_ONLY`
  - `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE`
- L/control:
  - `EXPLORATORY_L_SIGNAL`
  - `L_SIGNAL_M_CONTROL_FAIL`
  - `L_SIGNAL_M_CONTROL_INVALID`
  - `L_SIGNAL_M_CONTROL_NOT_EVALUABLE`
  - `L_SIGNAL_CONTROL_NOT_ASSESSABLE`
- `EXPLORATORY` requires validity VALID + control PASS.

### 3.4 M

- L prefix **753**, P/PA prefix **512**.
- M cohort **15/20**; signal cohort **val20**.
- `endpoint_ok = 15/15 L copy/full + 15/15 P/PA copy/full`.
- endpoint missing → `m_evaluable=false` / `M_NOT_EVALUABLE`.
- M copy endpoint n을 14로 낮추지 않음.
- full-K 11/20 secondary only.

### 3.5 Checklist

- item 6 hash = **3ee3f1ca…**
- item 9 = `M_VALID` **computation contract** (not prelaunch truth)
- D1 timing artifact, replay hash, projection formula 추가
- signal val20 vs M 15 분리

### 3.6 D1

- 4 arm-seeds ×1 update, seed **20261111 shared**
- timed phases:
  - one train update
  - step0 eval subset
  - final eval subset
  - M builder
  - replay
- projection:
```text
T_proj = 3 * sum_arm(
  100*t_train + t_step0_eval + t_step100_eval + t_M_build + t_replay
)
```
- D0-only projection 금지; D1 없이 3-seed 금지.

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
- P0는 native path sensitivity; 256 source, registered M 512
- trained P/PA/L 증거 아님

---

## 5. 검토 질문

### Q1. Total factored contract

r3의 validity/control/signal이 실제로 total하고 executable한가? NA path fail-closed, `M_NOT_EVALUABLE` control-only, `M_CONTROL_INVALID`가 all cell을 덮는가?

### Q2. L preservation / signal labels

small-N, validity-invalid, copy-only/full-only, mean/no labels가 L flag를 왜곡 없이 보존하는가? dead label이 없는가?

### Q3. M preflight / cohort

K=753, 15/20 M, val20 signal, endpoint 15/15, full-K 11/20 secondary가 정당한가? zero-margin/endpoint 규칙이 executable한가?

### Q4. M builder / aggregation / replay

eval/no_grad, seed-average-before-bootstrap, false-dominant false+NA, replay `atol=1e-5`가 leakage-free이고 충분한가?

### Q5. PA

PA acquisition 명명, `PA_STEP100_NOT_VALID`, `PA_RETENTION` 비gate, scale/geometry caveat가 충분한가?

### Q6. Cap / D0 / D1

registered 12×100=1,200, D0 0-update, D1 4×1, D1 required for 3-seed timing, projection formula가 산술·승인 경계에서 맞는가?

### Q7. Statistics

n_boot 1,000, CI percentile, bootstrap seed 20261109, `documents_positive`/`seeds_positive`, top-3 share, `MARGINAL_SIGNAL_COHORT`가 executable한가?

### Q8. 남은 Must-fix

r2 3-AI Must-fix 중 아직 닫히지 않은 항목을 ranked list로 제시하라. r3가 새로 만든 문제가 있는가?

### Q9. 동결·구현 승인

r3를 동결하고 **구현 + unit tests + D0 zero-update mechanics debug**를 승인할 수 있는가? 구현 전 필수 test/contract는 무엇인가?

### Q10. D1 / 3-seed

D1 timing gate와 3-seed를 별도로 유지하는 경계가 충분한가? 3-seed checklist에 빠진 항목은?

### Q11. B0-B

r3 결과가 좋아도 B0-B/B1/B2/Stage C를 자동 승인하지 않는 경계가 유지되는가? B0-B predicate를 r3 label에 맞게 재진술하라.

### Q12. 최종 판정

**STOP / NARROW / CONTINUE**와 승인 범위를 제시하라.

- r3 동결
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
r3 동결:
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
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3.md` | r3 |
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r2.md` | r2 |
| `reports/C5_B0A_PM_PREREG_V0_2_1_R2_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | r2 review |
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

> **r3가 r2 3-AI Must-fix를 충분히 닫았는가, 그리고 r3 동결·구현·unit tests·D0를 승인할 수 있는가?**

특히 다음을 명시해 달라.

1. total factored contract에 남은 cell/모순
2. K_M_L=753 / M_CONTROL_PREFIX753_COHORT15 / endpoint 15/15의 타당성
3. D0/D1/3-seed/B0-B 승인 경계
