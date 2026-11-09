# C5 Phase 6 v0.2.1-r3 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r3_2026-11-09/`
- 검토 기준 HEAD: `fc0d973` (요청서 커밋); r3 plan `e779e93`
- 모델:
  - GLM 5.3 Flash **max**
  - DeepSeek 4.1 Flash 1017 **max** — Hoplite 등록 alias `deepseek/deepseek-v4.1-flash`
  - Terra 6.1 **medium**
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_1_R3_2026-11-09.md` (313줄)
- 원문:
  - `review_GLM.md` (25,543 chars)
  - `review_DS41.md` (24,648 chars)
  - `review_TERRA.md` (21,894 chars)
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **2 CONTINUE(조건부) / 1 NARROW.** GLM과 DeepSeek은 r3의 6개 r2 Must-fix가 구조적으로 닫혔다고 보지만, 작은 residual(AND3 arity, validity-NA label, projection eval counts, n_signal domain, stats debt)을 **r3.1**에 붙여 동결·구현·D0를 조건부 승인한다. Terra는 r3가 아직 self-consistent freeze contract가 아니라고 보아 **r4 text repair**를 요구한다. 따라서 **r3 동결·구현·D0는 보류**하고, residual을 닫는 **r3.1 text-only errata** 후 재검토한다.

---

## 1. 판정 행렬

| 검토자 | 모델 | 판정 | r3 동결 | 구현+unit tests | D0 | D1 | 3-seed |
|---|---|---|---|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **CONTINUE(조건부)** | r3.1 후 | 조건부 | 조건부 | 미승인 | 미승인 |
| DeepSeek | `deepseek/deepseek-v4.1-flash` max | **CONTINUE(조건부)** | r3.1 후 | 조건부 | 조건부 | 미승인 | 미승인 |
| Terra | `gpt-6.1-terra` medium | **NARROW** | **아니오** | 아니오 | 아니오 | 미승인 | 미승인 |
| **종합** | — | **보류 / NARROW** | **미승인** | **미승인** | **미승인** | **미승인** | **미승인** |

- STOP 0/3.
- CONTINUE 2/3 conditional.
- NARROW 1/3.
- **만장일치 아님** → freeze하지 않는다.

---

## 2. 실제로 닫힌 것

모든 검토자가 인정한 항목:

- NA path fail-closed (`test_split_used`, `pa_step100_path_ok`)
- known P failure precedence
- `M_NOT_EVALUABLE` control-only
- `M_CONTROL_INVALID` reachable
- dead `L_SIGNAL_M_CONTROL_NOT_EVALUABLE` 복구
- signal validity guard / copy-only/full-only invalid labels
- signal cohort val20 vs M cohort 15 분리
- M endpoint 15/15 fail-closed
- K_M_L=753 max-K rule
- preflight hash `3ee3f1ca…`
- checklist stale hash 수정
- circular `M_VALID=true` 제거
- D1 seed 20261111 / D1-only timing
- P0 256 vs 512 caveat
- `m_pass_l` derivation
- mixed false+NA false-dominant

DeepSeek는 6/6 r2 Must-fix가 구조적으로 닫혔다고 평가했다. GLM도 6개 모두 닫혔다고 본다. Terra는 routing은 좋아졌지만 **executable freeze contract**로는 아직 부족하다고 본다.

---

## 3. 남은 residual

### R-1. `AND3` arity / n-ary semantics

**문제**

- `AND3`가 2/4/5 operand에 사용된다.
- 실제 코드에서 3-arity로 고정되면 4/5 operand가 잘릴 수 있다.

**r3.1 요구**

```text
ANDn: any false -> false; else any NA -> NA; else true
```

- 2/4/5 operand test.
- `m_valid`(4), `m_evaluable`(4), `m_pass_l`(2) 명시.
- n-ary test를 DoD에 추가.

### R-2. validity-NA signal labels

**문제**

- `validity_status=NOT_ASSESSABLE`도 `*_VALIDITY_INVALID`로 라벨링된다.
- unknown을 invalid로 과장한다.

**r3.1 요구**

- `NOT_ASSESSABLE` + L true → `L_SIGNAL_VALIDITY_NOT_ASSESSABLE`
- `NOT_ASSESSABLE` + copy/full → `COPY_ONLY_VALIDITY_NOT_ASSESSABLE` / `FULL_ONLY_VALIDITY_NOT_ASSESSABLE`
- `INVALID` + L → `L_SIGNAL_VALIDITY_INVALID` 유지
- label table 갱신.

### R-3. §6.3 unconditional NA assertions

**문제**

- “`test_split_used=NA` → NOT_ASSESSABLE”가 known P path false와 충돌.
- “`pa_step100_path_ok=NA` → NOT_ASSESSABLE”가 P valid false와 충돌.

**r3.1 요구**

- “known failure precedence를 조건으로” 문구 추가:
```text
test_split_used=NA -> ASSAY_INVALID if known P/assay failure; else NOT_ASSESSABLE
pa_path=NA -> P_STEP100_NOT_VALID if p_valid=false; else NOT_ASSESSABLE
```
- fixtures:
  - test_split NA + p path false → ASSAY_INVALID
  - test_split NA + paths good → NOT_ASSESSABLE
  - pa path NA + p valid false → P_STEP100_NOT_VALID
  - pa path NA + p valid true → NOT_ASSESSABLE

### R-4. M builder availability / zero norms

**문제**

- `m_evaluable`는 cohort/endpoint/seed/replay만 본다.
- M norm zero/nonfinite, contributor 부족, adapter output nonfinite가 `M_NOT_EVALUABLE`로 라우팅되지 않는다.
- `M_NORM`은 target real-prefix norm을 사용하므로 target-dependent magnitude match다.

**r3.1 요구**

- `builder_ok`를 추가:
```text
builder_ok = contributors >= 10
             AND all M tensors finite
             AND ||M_POS_MEAN|| > 0
             AND ||real_prefix|| > 0
```
- `m_evaluable = ANDn(cohort_ok, endpoint_ok, seed_ok, replay_ok, builder_ok)`.
- zero/nonfinite → `M_NOT_EVALUABLE`.
- `M_NORM`은 **magnitude-matched, target-norm-dependent**로 표기; target label leakage는 금지.

### R-5. Endpoint identity / finite checks

**문제**

- 15 IDs, arms, variants, seeds, real/control CE, copy_ce min 5, finite check가 실행 계약으로 충분히 고정되지 않았다.
- `endpoint_ok`가 mask count만 보고 CE finite를 보지 않을 수 있다.

**r3.1 요구**

- `endpoint_ok`는 **15 IDs × 3 seeds × 4 arms × primary variants**에 대해:
  - real/control CE finite
  - copy_ce not None
  - copy tokens >=5
  - no duplicate/missing ID
- exact 15 IDs를 preflight hash에 bind.
- 실패 시 `M_NOT_EVALUABLE`; cohort 14로 낮추지 않는다.

### R-6. D1 projection workload

**문제**

- D1 “one doc subset”과 registered 20/15 cohort의 scaling이 불명확.
- replay hash/D1 phases가 full workload를 대표하지 않을 수 있다.
- D1 projection formula는 있으나 eval doc count가 없다.

**r3.1 요구**

- D1 timed phases에 exact counts:
  - train 1 update
  - step0 eval 20 docs
  - final eval 20 docs
  - M builder 20 train/15 target
  - replay 15 targets
- projection:
```text
T_proj = 3 * sum_arm(
  100*t_train
  + t_step0_eval_20
  + t_step100_eval_20
  + t_M_build_15
  + t_replay_15
)
```
- subset 사용 시 per-doc normalize.
- replay hash:
  - **prelaunch debug replay hash**는 D1 artifact
  - **final trained checkpoint/replay hash**는 post-run
  - 둘을 혼동하지 않는다.

### R-7. `n_signal` domain

**문제**

- `{NA,0,14,15,20}` domain이 16~19를 빠뜨린다.

**r3.1 요구**

- `n_signal ∈ {NA,0..20}`.
- 16~19 fixtures 추가.

### R-8. Statistics wiring

**문제**

- 현재 runner `bootstrap_paired`는 seed 20261108, `seeds_positive`에 문서 수.
- r3 constants와 다르다.
- 2/3 seed rule이 r3에 재기술되지 않았다.

**r3.1 요구**

- new stats module:
  - `bootstrap_seed=20261109`
  - `documents_positive`
  - `n_boot=1000`
  - percentile 2.5/97.5
- 2/3 seed L>F rule 재기술.
- P0 helper 재사용 금지.

### R-9. Truth-table strategy

**문제**

- “exhaustive”가 full Cartesian 3^17-scale로 비현실적.
- per-axis exhaustive + named cells 전략이 필요하다.

**r3.1 요구**

- per-axis exhaustive:
  - validity paths 3^5
  - control 3^4
  - signal labels
  - n_signal 0..20
- named cross-axis fixtures:
  - NA fail-open
  - dead label
  - M_INVALID
  - L validity invalid
  - endpoint 14/15
  - mixed false+NA
- 모든 label reachable test.
- pure function + synthetic only.

---

## 4. 검토자별 차이

### GLM

- 6/6 r2 Must-fix closed.
- r3.1 residual 6개를 붙이면 freeze + implementation + D0 승인 가능.
- D1/3-seed/B0-B 미승인.

### DeepSeek

- 6/6 closed, **CONTINUE**.
- residual: endpoint-valid criterion, stats wiring, D1 per-arm phases, n_signal domain, D1/registered accounting.
- implementation + D0 after r3.1; D1/3-seed 미승인.

### Terra

- routing은 좋아졌으나 **NARROW**.
- §6.3 unconditional assertions, M builder zero norms, endpoint identity, D1 workload, prelaunch replay hash, n_signal domain, truth-table strategy.
- r4 text repair 요구; freeze/implementation/D0 미승인.

**해석**: GLM/DS41은 “작은 r3.1”로 충분하다고 보고, Terra는 “r4”라는 이름을 요구한다. 내용상 residual은 겹친다. r3.1에서 모두 닫고 재검토하는 것이 합의 경로다.

---

## 5. 결정

```text
r3 = 동결 보류 (2 CONTINUE conditional / 1 NARROW)
r3.1 = 필요 (text-only)
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

## 6. 다음 단계

1. r3.1 text-only errata 작성
   - ANDn
   - validity NA labels
   - §6.3 precedence-aware fixtures
   - builder_ok / M zero norms
   - endpoint identity/finite
   - D1 workload/replay hash
   - n_signal 0..20
   - stats module/2-of-3
   - truth-table strategy
2. r3.1 3-AI 재검토
3. 동결 commit
4. 구현 + unit tests
5. D0 (0 updates)
6. D1 separate approval
7. 3-seed separate gate
8. B0-B separate

---

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r3_2026-11-09/review_GLM.md` | GLM |
| `.../review_DS41.md` | DeepSeek |
| `.../review_TERRA.md` | Terra |
| `reports/C5_B0A_PM_PREREG_V0_2_1_R3_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3.md` | r3 |
| `reports/provenance/C5_b0a/m_cohort_preflight.json` | M preflight |

## 8. 제한

- 이 종합은 승인이 아니다.
- 2 CONTINUE / 1 NARROW는 만장일치가 아니다.
- r3.1 없이 코드를 작성하지 않는다.
- “54 tests”는 historical evidence이며 PM tests는 아직 없다.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아니다.
