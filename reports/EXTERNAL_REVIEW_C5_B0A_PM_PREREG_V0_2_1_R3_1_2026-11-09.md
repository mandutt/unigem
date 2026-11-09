# C5 Phase 6 v0.2.1-r3.1 — External Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `7264c55` (`docs: add C5 Phase 6 v0.2.1-r3.1 residual closure`)
- 대상: `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_1.md` (771줄)
- preflight: `reports/provenance/C5_b0a/m_cohort_preflight.json`
- preflight hash: **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`** (committed blob, LF)
- 상태: **r3.1 review. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. Reviewer instructions

1. 이 문서를 처음부터 끝까지 직접 읽어라. 다른 모델의 답을 재사용하지 말라.
2. 저장소 접근이 가능하면 다음 원문을 확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_1.md`
   - `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3.md`
   - `reports/C5_B0A_PM_PREREG_V0_2_1_R3_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
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
   `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r3_1_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q12 판정 표와 Must-fix 요약을 포함하라.

---

## 1. TL;DR

> **r3는 2 CONTINUE(조건부) / 1 NARROW였다. r3.1은 residual 9개(ANDn arity, validity-NA labels, precedence-aware NA assertions, M builder zero/norm routing, endpoint identity/finite, D1 workload/replay hash, n_signal 0..20, stats module/2-of-3, truth-table strategy)를 text-only로 닫는 errata다. 이 문서는 r3.1이 실제로 freeze 가능한지, 구현·D0를 승인할 수 있는지를 묻는다.**

| 항목 | 상태 |
|---|---|
| v0.1 | NARROW 3/3 |
| v0.2 | NARROW 3/3 |
| v0.2.1 | NARROW 3/3 |
| r1 | NARROW 3/3 |
| r2 | NARROW 3/3 |
| r3 | 2 CONTINUE 조건부 / 1 NARROW |
| **r3.1** | **작성 완료, 미승인** |
| Phase 6 실행 | **없음** |
| P0 | SENSITIVE_POSITIVE, descriptive |
| test 163 | sealed |

---

## 2. r3 residual

1. `AND3`가 2/4/5 operand에 사용됨.
2. validity `NOT_ASSESSABLE`을 `*_VALIDITY_INVALID`로 과장.
3. §6.3의 unconditional NA 문구가 precedence와 충돌.
4. M builder zero/nonfinite norm/contributor 부족이 `M_NOT_EVALUABLE`로 라우팅되지 않음.
5. endpoint identity/finite/15 IDs/3 seeds/4 arms 미고정.
6. D1 workload/eval counts/replay hash prelaunch vs post-run 미분리.
7. `n_signal` 16~19 누락.
8. stats module/`bootstrap_seed=20261109`/2-of-3 rule 미고정.
9. truth-table “exhaustive” 전략 미정의.

---

## 3. r3.1 변경 요약

### 3.1 ANDn

```text
ANDn(args):
  any false -> false
  else any NA -> NA
  else true

ORn(args):
  any true -> true
  else any NA -> NA
  else false
```

- `m_pass_l`(2), `m_valid`(4), `m_evaluable`(5).
- 2/4/5 operand tests.
- 3-arity 절단 금지.

### 3.2 validity-NA labels

- validity `NOT_ASSESSABLE`:
  - `L_SIGNAL_VALIDITY_NOT_ASSESSABLE`
  - `COPY_ONLY_VALIDITY_NOT_ASSESSABLE`
  - `FULL_ONLY_VALIDITY_NOT_ASSESSABLE`
- validity known invalid:
  - `*_VALIDITY_INVALID`
- small-N labels 그대로.
- raw flags always preserved.

### 3.3 precedence-aware NA

| fixture | expected |
|---|---|
| test_split NA + P path false | `ASSAY_INVALID` |
| test_split NA + paths good | `NOT_ASSESSABLE` |
| pa_path NA + P invalid | `P_STEP100_NOT_VALID` |
| pa_path NA + P valid | `NOT_ASSESSABLE` |
| assay NA + P path false | `ASSAY_INVALID` |
| assay NA + paths good | `NOT_ASSESSABLE` |
| pa_path false + P valid | `PA_STEP100_NOT_VALID` |
| pa_path false + P invalid | `P_STEP100_NOT_VALID` |

- F1~F8 test.

### 3.4 M builder

```text
builder_ok = contributors >= 10
             AND all M tensors finite
             AND ||M_POS_MEAN||_F > 0
             AND ||real_prefix||_F > 0

m_evaluable = ANDn(cohort_ok, endpoint_ok, seed_ok, replay_ok, builder_ok)
```

- zero/nonfinite/contributor 부족 → `M_NOT_EVALUABLE`.
- `M_NORM`은 target real-prefix norm을 사용하는 **magnitude-matched, target-dependent** control.
- target label leakage 금지.

### 3.5 endpoint identity

- exact 15 IDs
- 15 × 3 seeds × 4 arms × primary variants
- real/control CE finite
- `copy_ce != None`
- copy tokens ≥5
- duplicate/missing 없음
- 15→14 substitution 금지
- 하나라도 실패 → `M_NOT_EVALUABLE`.

### 3.6 D1

- D1 4 arm-seeds ×1 update, seed 20261111 shared
- timed phases:
  - train 1 update
  - step0 eval 20 docs
  - final eval 20 docs
  - M builder 20 train / 15 target
  - replay 15 targets
- `T_proj = 3 * sum_arm(100*t_train + t_step0_eval_20 + t_step100_eval_20 + t_M_build_15 + t_replay_15)`
- prelaunch `debug_replay_hash` vs post-run `final_checkpoint_hash`/`final_replay_hash`
- D1 없이 3-seed 금지; D0-only projection 금지.

### 3.7 n_signal / stats / truth table

- `n_signal ∈ {NA, 0..20}`.
- new stats module:
  - `bootstrap_seed=20261109`
  - `documents_positive`
  - 2/3 seed rule
  - P0 helper 재사용 금지
- truth table:
  - per-axis exhaustive
  - named cross-axis fixtures 17개
  - full Cartesian 강제하지 않음
  - every label reachable
  - pure function/synthetic only.

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

r3.1의 validity/control/signal과 ANDn, validity-NA labels, precedence-aware NA가 실제로 total/executable한가?

### Q2. L preservation

small-N, validity-invalid, validity-NA, copy-only/full-only labels가 L flag를 왜곡 없이 보존하는가?

### Q3. M preflight / cohort

K=753, 15/20 M, val20 signal, endpoint 15/15, full-K 11/20 secondary가 정당한가?

### Q4. M builder / endpoint / replay

builder_ok, zero/nonfinite norm, exact 15×3×4×variants, finite/copy tokens, replay prelaunch/post-run 분리가 충분한가?

### Q5. PA

PA acquisition 명명, `PA_STEP100_NOT_VALID`, `PA_RETENTION` 비gate, scale/geometry caveat가 충분한가?

### Q6. Cap / D0 / D1

registered 12×100=1,200, D0 0-update, D1 4×1, D1 workload/projection/seed가 산술·승인 경계에서 맞는가?

### Q7. Statistics

n_boot 1,000, CI percentile, bootstrap seed 20261109, documents_positive/seeds_positive, 2-of-3 seed rule, top-3 share가 executable한가?

### Q8. 남은 Must-fix

r3 residual 중 아직 닫히지 않은 항목을 ranked list로 제시하라. r3.1이 새로 만든 문제가 있는가?

### Q9. 동결·구현 승인

r3.1을 동결하고 **구현 + unit tests + D0 zero-update mechanics debug**를 승인할 수 있는가? 구현 전 필수 test/contract는 무엇인가?

### Q10. D1 / 3-seed

D1 timing gate와 3-seed를 별도로 유지하는 경계가 충분한가? 3-seed checklist에 빠진 항목은?

### Q11. B0-B

r3.1 결과가 좋아도 B0-B/B1/B2/Stage C를 자동 승인하지 않는 경계가 유지되는가? B0-B predicate를 r3.1 label에 맞게 재진술하라.

### Q12. 최종 판정

**STOP / NARROW / CONTINUE**와 승인 범위를 제시하라.

- r3.1 동결
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
r3.1 동결:
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
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_1.md` | r3.1 |
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3.md` | r3 |
| `reports/C5_B0A_PM_PREREG_V0_2_1_R3_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | r3 review |
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

> **r3.1이 r3 residual을 충분히 닫았는가, 그리고 r3.1 동결·구현·unit tests·D0를 승인할 수 있는가?**

특히 다음을 명시해 달라.

1. factored contract에 남은 cell/모순
2. M builder/endpoint/replay의 타당성
3. D0/D1/3-seed/B0-B 승인 경계
