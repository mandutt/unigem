# C5 Phase 6 v0.2.1-r2 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r2_2026-11-09/`
- 검토 기준 HEAD: `fc5680e` (요청서 커밋), r2 문서 기준 `308648e`
- 모델:
  - GLM 5.3 Flash **max**
  - Sonnet 5.5 **medium**
  - Sol 6.1 **medium**
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_1_R2_2026-11-09.md`
- 원문:
  - `review_GLM.md` (23,049 chars)
  - `review_SONNET.md` (22,694 chars)
  - `review_SOL.md` (27,330 chars)
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **3/3 NARROW.** r2는 r1 Must-fix를 구조적으로 상당 부분 닫았지만, **`test_split_used=NA`/`pa_step100_path_ok=NA`가 VALID로 새는 fail-open**, **`L_SIGNAL_M_CONTROL_NOT_EVALUABLE` dead label**, **signal cohort vs M cohort 불명확**, **M copy endpoint 0-margin**, **checklist stale hash·circular M_VALID**, **D1 timing 미정의**가 남았다. **r3 text-only repair 후 동결**해야 하며, 구현·D0·D1·3-seed·B0-B는 미승인이다.

---

## 1. 판정 행렬

| 검토자 | 판정 | r3 | 동결 | 구현+unit tests | D0 | D1 | 3-seed |
|---|---|---|---|---|---|---|---|
| GLM max | **NARROW** | 필요 | r3 후 | 조건부 | 조건부 | 미승인 | 미승인 |
| Sonnet medium | **NARROW** | 필요 | r3 후 | 조건부 | 조건부 | 미승인 | 미승인 |
| Sol medium | **NARROW** | 필요 | r3 후 | 조건부 | 조건부 | 미승인 | 미승인 |
| **종합** | **NARROW 3/3** | **필요** | **미승인** | **미승인** | **미승인** | **미승인** | **미승인** |

STOP 0/3, CONTINUE 0/3.

---

## 2. 실제로 닫힌 것

- `m_valid` / `M_CONTROL_INVALID` 도입
- path flag 개별 열거 (대부분)
- L-qualified labels
- `K_M_L=753` max-K rule
- `M_CONTROL_PREFIX753_COHORT15`
- zero-margin/length-conditioned cohort 명시
- M builder eval/no_grad
- seed-average-before-bootstrap
- replay `atol=1e-5`
- D0 0-update / D1 1-update / registered cap 분리
- debug seed 20261111 명시
- `documents_positive`/`seeds_positive` 분리 원칙

세 검토자 모두 **r2가 r1보다 실질적으로 개선**됐다고 평가했다.

---

## 3. 남은 Must-fix

### MF-1. NA path fail-open

**문제**

- `test_split_used=NA`가 VALID로 통과한다.
- `pa_step100_path_ok=NA`가 VALID로 통과한다.
- `assay_path_ok=NA` + `p_step100_path_ok=false`에서 NA 분기가 known P failure를 가린다.

**r3 요구**

- known failure를 NA보다 먼저 평가:
```text
if assay_path_ok=false
   or p0_path_ok=false
   or test_split_used=true
   or p_step100_path_ok=false:
    ASSAY_INVALID
elif any of assay_path_ok/p0_path_ok/p_step100_path_ok/
         test_split_used is not_assessable:
    NOT_ASSESSABLE
```
- `pa_step100_path_ok=NA` → `NOT_ASSESSABLE`.
- `test_split_used=NA` → `NOT_ASSESSABLE`.
- truth-table에 두 NA cell을 명시.

### MF-2. `M_NOT_EVALUABLE` 이중 축 / dead label

**문제**

- `M_NOT_EVALUABLE`가 validity와 control 양쪽에 있다.
- validity가 `M_NOT_EVALUABLE`이면 `L_SIGNAL_M_CONTROL_NOT_EVALUABLE`가 선행 `validity != VALID` 분기에 먹혀 도달 불가.
- M 실패가 `L_SIGNAL_VALIDITY_INVALID`로 오표기된다.

**r3 요구**

- `validity_status`에서 `M_NOT_EVALUABLE` 제거.
- validity = assay/P/PA 상태만.
- `M_NOT_EVALUABLE`는 control에만.
- `m_evaluable`에서 p/pa를 제거하고 control에서 별도 검사:
```text
m_evaluable = AND3(cohort_ok, endpoint_ok, seed_ok, replay_ok)
if m_evaluable not true -> M_NOT_EVALUABLE
elif p_valid not true or pa_valid not true -> M_NOT_EVALUABLE
elif m_valid false -> M_CONTROL_INVALID
...
```
- `L_SIGNAL_M_CONTROL_NOT_EVALUABLE`가 실제 도달 가능해야 한다.
- truth table에서 dead label 0.

### MF-3. Signal validity guard 비대칭 / small-N precedence

**문제**

- `l_signal=true`만 validity를 검사하고 `COPY_ONLY_WEAK`/`FULL_ONLY_WEAK`/`MEAN_CONTRAST_ONLY`/`NO_AFFIRMATIVE`는 무시.
- `n_signal<15` + L true + invalid validity가 `L_SIGNAL_VALIDITY_INVALID`와 충돌.
- partial NA (copy T, full NA)가 generic NOT_ASSESSABLE로 간다.

**r3 요구**

- signal status 우선순위를 명시:
```text
n_signal NA/ <15 -> small-N/NA
validity != VALID -> L/COPY/FULL validity-invalid labels (or NOT_ASSESSABLE)
then copy_only/full_only
then l_signal/control
```
- `COPY_ONLY_VALIDITY_INVALID` / `FULL_ONLY_VALIDITY_INVALID` 추가 또는 valid-only labels로 제한.
- `MEAN_CONTRAST_ONLY`/`NO_AFFIRMATIVE`는 validity VALID에서만.
- partial NA rule를 명시: consensus `l_signal=NA`; `copy_only/full_only`도 NA.

### MF-4. Signal cohort vs M cohort / copy endpoint

**문제**

- `n_signal`이 val20인지 M 15인지 불명확.
- M copy endpoint에 copy mask 유효성 규칙이 없다.
- zero margin 15/20; 한 doc missing이면 M copy n=14.

**r3 요구**

- `signal cohort = val20`으로 고정.
- `M control cohort = 15 longest-of-20`으로 고정.
- `endpoint_ok = 15/15 copy mask valid`; 아니면 `m_evaluable=false`.
- signal n과 M n을 별도 필드로 기록.
- `M_CONTROL_PREFIX753_COHORT15` label 유지.

### MF-5. Checklist stale hash / circular M_VALID

**문제**

- §12 item 6이 `07c3fe4c…`를 참조하지만 frozen hash는 `3ee3f1ca…`.
- §12 item 9 “P/PA M_VALID true”는 3-seed 실행 **전**에 요구할 수 없는 post-run 결과다.

**r3 요구**

- item 6 → `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`.
- item 9를 launch checklist에서 제거.
- M_VALID는 **report/interpretation gate**로 이동.
- 3-seed checklist에는 “M_VALID computation contract”만.
- replay hash, projection formula, D1 labels fields 추가.

### MF-6. D1 timing / M endpoint / P0 256-512 caveat

**문제**

- D1 timed phases가 정의되지 않았다.
- “separately approved timing probe”가 정의되지 않은 loophole.
- D1 seed 20261111이 shared인지 derived인지 불명확.
- P0는 `source_max_length=256`에서 측정됐고 registered P/PA M path는 512 prefix다.
- `m_pass_l`의 deriving flags(`m_pass_pos_l`, `m_pass_norm_l`)가 inventory/truth table에 없다.
- mixed false+NA M aggregation 규칙이 §5.1 AND3와 §9.5 missingness-first 사이에서 충돌.

**r3 요구**

- D1 timed phases:
  - 1 train update
  - step0 eval on one doc subset
  - final eval on one doc subset
  - M builder pass
  - replay
  - projection formula `sum(phase_time * count_scale)`.
- timing probe 옵션 삭제 또는 D1과 동일 계약으로 정의.
- D1 seed = **20261111** (모든 4 arm-seeds에 shared; run-specific derived 아님).
- P0 256 vs 512 caveat를 report/limitation에 기록.
- `m_pass_l = AND3(m_pass_pos_l, m_pass_norm_l)`를 inventory/test에 추가.
- mixed false+NA는 **false-dominant AND3**로 통일; missingness-first 금지.

---

## 4. M / preflight

검토자들은 다음을 독립 재계산해 일치를 확인했다.

- max-K=753
- train contributors 16
- val targets 15
- K=754 → 14
- common IDs exact
- preflight SHA256 `3ee3f1ca…`
- full-K 11/20

결론:

- 753은 outcome-blind, length-only, zero-margin.
- `M_CONTROL_PREFIX753_COHORT15`는 full-real-K가 아니다.
- full-K 11/20은 secondary descriptive only.
- 이 선택은 **defensible but narrow**; report마다 label 필요.

---

## 5. D0 / D1 / 3-seed

```text
D0 = 0 updates, ≤4 configs, ≤15 min, seed 20261111, labels_computed:false, not_a_result:true
D1 = 4 arm-seeds ×1 update, ≤20 min, seed 20261111, separate approval
registered = 12 units ×100 = 1,200 updates, 2h, 6 threads, no retry
```

- D0는 implementation gate; timing 근거 아님.
- D1은 implementation gate 필수 아님; **3-seed timing 필수**.
- D1 없이 3-seed 금지.
- 3-seed는 separate approval.
- B0-B/B1/B2/Stage C는 별도.

---

## 6. 결정

```text
r2 = NARROW 3/3, not frozen
r3 = 필요 (text-only)
Phase 6 구현 = 미승인
unit tests = 미승인
D0 = 미승인
D1 = 미승인
3-seed = 미승인
B0-B/B1/B2/Stage C = 미승인
test 163 = sealed
T5Gemma2 = D-108 STOP
```

---

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r2_2026-11-09/review_GLM.md` | GLM |
| `.../review_SONNET.md` | Sonnet |
| `.../review_SOL.md` | Sol |
| `reports/C5_B0A_PM_PREREG_V0_2_1_R2_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r2.md` | r2 |
| `reports/provenance/C5_b0a/m_cohort_preflight.json` | M preflight |

## 8. 제한

- 이 종합은 승인이 아니다.
- 3/3 NARROW는 bridge STOP이 아니다.
- r3 없이 코드를 작성하지 않는다.
- “54 tests”는 historical evidence이며 PM tests는 아직 없다.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아니다.
