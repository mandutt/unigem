# C5 Phase 6 P/M Prereg v0.2.1-r3.1 — Residual Closure Errata

- 작성일: 2026-11-09
- 상태: **r3.1 동결 후보. 실행 미승인.**
- 적용 대상: `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3.md` (r3)
- 충돌 시: **r3.1 > r3 > r2 > r1 > v0.2.1 > v0.2**
- 근거:
  - `reports/C5_B0A_PM_PREREG_V0_2_1_R3_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
  - r3.1 residual: ANDn, validity-NA labels, §6.3 precedence, builder_ok/M norms, endpoint identity, D1 workload/replay hash, n_signal 0..20, stats module/2-of-3, truth-table strategy
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. r3.1의 목적

r3.1은 r3 검토의 **residual Must-fix만** 닫는 text-only errata다.

- threshold/seed/donor/step/LR 변경 없음
- 결과 전에 commit/freeze
- 코드는 r3.1 승인 후에만 작성
- r3의 **구조적 6/6 closure**는 유지
- r3.1은 **test-contract/operational contract**를 보강

---

## 1. R3 residual closure map

| Residual | r3.1 조치 |
|---|---|
| AND3 arity | §2.2 `ANDn`/`ORn` n-ary |
| validity-NA labels | §5.3 `*_VALIDITY_NOT_ASSESSABLE` |
| §6.3 unconditional NA assertions | §3.6 precedence-aware fixtures |
| M builder zero/nonfinite norm | §8.2 `builder_ok` |
| endpoint identity/finite | §8.3 exact IDs/seeds/arms/CE |
| D1 workload/eval counts/replay hash | §10.3–10.6 |
| n_signal 16~19 | §5.1 `0..20` |
| stats module/2-of-3 | §9.2 |
| truth-table strategy | §6.4 |

---

## 2. Logic primitives

### 2.1 Tri-state

```text
true | false | not_assessable
```

### 2.2 N-ary AND/OR

```text
ANDn(args):
  if any arg is false -> false
  elif any arg is not_assessable -> not_assessable
  else -> true

ORn(args):
  if any arg is true -> true
  elif any arg is not_assessable -> not_assessable
  else -> false

NOT3(x):
  true <-> false
  not_assessable -> not_assessable
```

- `AND3`라는 이름은 **`ANDn` alias**로만 사용한다.
- `m_pass_l`(2), `m_valid`(4), `m_evaluable`(5)는 모두 `ANDn`이다.
- 2/4/5 operand test를 요구한다.
- 3-arity로 조용히 자르는 구현을 금지한다.

### 2.3 Signal consensus

```text
l_signal = true   if l_copy_signal=true and l_full_signal=true
           false  if l_copy_signal=false and l_full_signal=false
           not_assessable otherwise

copy_only = ANDn(l_copy_signal, NOT3(l_full_signal))
full_only = ANDn(l_full_signal, NOT3(l_copy_signal))
```

---

## 3. Validity status

### 3.1 Values

```text
ASSAY_INVALID
P_STEP100_NOT_VALID
PA_STEP100_NOT_VALID
NOT_ASSESSABLE
VALID
```

- `M_NOT_EVALUABLE`는 validity가 아니다.
- `M_CONTROL_INVALID`도 validity가 아니다.

### 3.2 Known failure first

```text
if assay_path_ok is false
   or p0_path_ok is false
   or test_split_used is true
   or p_step100_path_ok is false:
    ASSAY_INVALID
```

### 3.3 NA fail-closed

```text
elif assay_path_ok is not_assessable
   or p0_path_ok is not_assessable
   or p_step100_path_ok is not_assessable
   or test_split_used is not_assessable:
    NOT_ASSESSABLE
```

### 3.4 P/PA

```text
elif p_valid is false:
    P_STEP100_NOT_VALID
elif p_valid is not_assessable:
    NOT_ASSESSABLE
elif pa_step100_path_ok is not_assessable:
    NOT_ASSESSABLE
elif pa_step100_path_ok is false:
    PA_STEP100_NOT_VALID
elif pa_valid is false:
    PA_STEP100_NOT_VALID
elif pa_valid is not_assessable:
    NOT_ASSESSABLE
else:
    VALID
```

### 3.5 Validity invariants

- `validity_status`는 `M_NOT_EVALUABLE`/`M_CONTROL_INVALID`를 반환하지 않는다.
- `test_split_used=true` → `ASSAY_INVALID`.
- `p_step100_path_ok=false` → `ASSAY_INVALID`.
- P valid + PA path false → `PA_STEP100_NOT_VALID`.
- P invalid + PA path false → `P_STEP100_NOT_VALID`.

### 3.6 Precedence-aware NA fixtures

**중요**: “NA → NOT_ASSESSABLE”은 **선행 known failure가 없을 때만** 성립한다.

| fixture | flags | expected |
|---|---|---|
| F1 | `test_split_used=NA`, P path false | `ASSAY_INVALID` |
| F2 | `test_split_used=NA`, paths good | `NOT_ASSESSABLE` |
| F3 | `pa_path=NA`, `p_valid=false` | `P_STEP100_NOT_VALID` |
| F4 | `pa_path=NA`, `p_valid=true` | `NOT_ASSESSABLE` |
| F5 | `assay_path_ok=NA`, P path false | `ASSAY_INVALID` |
| F6 | `assay_path_ok=NA`, paths good | `NOT_ASSESSABLE` |
| F7 | `pa_path=false`, `p_valid=true` | `PA_STEP100_NOT_VALID` |
| F8 | `pa_path=false`, `p_valid=false` | `P_STEP100_NOT_VALID` |

- F1~F8 전부 test.
- “NA → NOT_ASSESSABLE” unconditional 문장은 사용하지 않는다.
- “known failure first” 문장을 유지한다.

---

## 4. Control status

### 4.1 Availability

```text
cohort_ok  = common M target IDs >= 15/20
endpoint_ok = 15/15 L copy/full endpoints valid
              AND 15/15 P/PA copy/full endpoints valid
seed_ok    = 3 seeds available
replay_ok  = replay equality
builder_ok = contributors >=10
             AND all M tensors finite
             AND ||M_POS_MEAN||_F > 0
             AND ||real_prefix||_F > 0
```

```text
m_evaluable = ANDn(cohort_ok, endpoint_ok, seed_ok, replay_ok, builder_ok)
```

- `builder_ok=false` → `M_NOT_EVALUABLE`.
- zero/nonfinite M norm → `M_NOT_EVALUABLE`.
- contributor <10 → `M_NOT_EVALUABLE`.
- `m_evaluable`는 availability이지 calibration이 아니다.

### 4.2 m_valid / m_pass_l

```text
m_pass_l = ANDn(m_pass_pos_l, m_pass_norm_l)

m_valid = ANDn(
  m_pass_pos_p, m_pass_norm_p,
  m_pass_pos_pa, m_pass_norm_pa
)
```

- false-dominant; mixed false+NA → false.
- missingness-first 구현 금지.

### 4.3 control_status

```text
if m_evaluable is not true:
    M_NOT_EVALUABLE
elif p_valid is not true or pa_valid is not true:
    M_NOT_EVALUABLE
elif m_valid is false:
    M_CONTROL_INVALID
elif m_valid is not_assessable:
    NOT_ASSESSABLE
elif m_pass_l is true:
    M_CONTROL_PASS
elif m_pass_l is false:
    M_CONTROL_FAIL
else:
    NOT_ASSESSABLE
```

- `M_CONTROL_NOT_VALID` 사용 금지.
- `M_CONTROL_INVALID` = P/PA calibration fail.
- `M_CONTROL_PASS` = P/PA calibration + L M pass.

---

## 5. Signal status

### 5.1 n_signal

```text
signal cohort = val20
n_signal = number of val20 docs with valid copy and full endpoints
n_signal ∈ {NA, 0..20}
n_min = 15
```

- 16~19도 valid domain이다.
- `n_signal=15`이면 `MARGINAL_SIGNAL_COHORT=true`.
- signal cohort val20과 M cohort 15를 별도 기록.

### 5.2 Label classes

- validity **INVALID**:
  - `L_SIGNAL_VALIDITY_INVALID`
  - `COPY_ONLY_VALIDITY_INVALID`
  - `FULL_ONLY_VALIDITY_INVALID`
- validity **NOT_ASSESSABLE**:
  - `L_SIGNAL_VALIDITY_NOT_ASSESSABLE`
  - `COPY_ONLY_VALIDITY_NOT_ASSESSABLE`
  - `FULL_ONLY_VALIDITY_NOT_ASSESSABLE`
- small N:
  - `INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL`
  - `INCONCLUSIVE_SMALL_N_WITH_COPY_ONLY`
  - `INCONCLUSIVE_SMALL_N_WITH_FULL_ONLY`
  - `INCONCLUSIVE_SMALL_N`
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
  - `NO_L_SIGNAL_CONTROL_INVALID`
  - `NO_L_SIGNAL_CONTROL_NOT_EVALUABLE`
- fallback: `NOT_ASSESSABLE`.

### 5.3 Signal dispatch

```text
if n_signal is not_assessable:
    NOT_ASSESSABLE

elif n_signal < 15:
    if l_signal is true:
        INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL
    elif copy_only is true:
        INCONCLUSIVE_SMALL_N_WITH_COPY_ONLY
    elif full_only is true:
        INCONCLUSIVE_SMALL_N_WITH_FULL_ONLY
    else:
        INCONCLUSIVE_SMALL_N

elif validity_status == NOT_ASSESSABLE:
    if l_signal is true:
        L_SIGNAL_VALIDITY_NOT_ASSESSABLE
    elif copy_only is true:
        COPY_ONLY_VALIDITY_NOT_ASSESSABLE
    elif full_only is true:
        FULL_ONLY_VALIDITY_NOT_ASSESSABLE
    else:
        NOT_ASSESSABLE

elif validity_status != VALID:
    if l_signal is true:
        L_SIGNAL_VALIDITY_INVALID
    elif copy_only is true:
        COPY_ONLY_VALIDITY_INVALID
    elif full_only is true:
        FULL_ONLY_VALIDITY_INVALID
    else:
        NOT_ASSESSABLE

elif copy_only is true:
    COPY_ONLY_WEAK

elif full_only is true:
    FULL_ONLY_WEAK

elif l_signal is not_assessable:
    NOT_ASSESSABLE

elif l_signal is true:
    if control_status == M_CONTROL_PASS:
        EXPLORATORY_L_SIGNAL
    elif control_status == M_CONTROL_FAIL:
        L_SIGNAL_M_CONTROL_FAIL
    elif control_status == M_CONTROL_INVALID:
        L_SIGNAL_M_CONTROL_INVALID
    elif control_status == M_NOT_EVALUABLE:
        L_SIGNAL_M_CONTROL_NOT_EVALUABLE
    else:
        L_SIGNAL_CONTROL_NOT_ASSESSABLE

elif control_status == M_CONTROL_PASS:
    MEAN_CONTRAST_ONLY

elif control_status == M_CONTROL_FAIL:
    NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE

elif control_status == M_CONTROL_INVALID:
    NO_L_SIGNAL_CONTROL_INVALID

elif control_status == M_NOT_EVALUABLE:
    NO_L_SIGNAL_CONTROL_NOT_EVALUABLE

else:
    NOT_ASSESSABLE
```

### 5.4 L preservation

- raw L flags always in `flags`.
- `NOT_ASSESSABLE` carries `signal_reason` + raw flags.
- `*_VALIDITY_NOT_ASSESSABLE`와 `*_VALIDITY_INVALID`를 구분한다.
- 모든 report는 `(validity, control, signal, flags, reason)`을 함께 기록.

---

## 6. Truth-table strategy

### 6.1 Per-axis exhaustive

- validity path axis: `3^5` (assay, p0, p_step, pa_step, test_split)
- p/pa validity axis: `3^2`
- control availability: `3^4` (cohort, endpoint, seed, replay)
- builder axis: `3^1` (builder_ok)
- calibration axis: `3^4` P/PA POS/NORM
- L/control/pass axis: `3^2` (l_copy/l_full)
- `n_signal`: 21 values + NA

### 6.2 Named cross-axis fixtures

필수 named cells:

1. `test_split_used=NA` + P path false → `ASSAY_INVALID`
2. `test_split_used=NA` + paths good → `NOT_ASSESSABLE`
3. `pa_path=NA` + P invalid → `P_STEP100_NOT_VALID`
4. `pa_path=NA` + P valid → `NOT_ASSESSABLE`
5. `m_valid=false` + P/PA valid → `M_CONTROL_INVALID`
6. `m_evaluable=false` + L true → `L_SIGNAL_M_CONTROL_NOT_EVALUABLE`
7. validity invalid + L true → `L_SIGNAL_VALIDITY_INVALID`
8. validity NA + L true → `L_SIGNAL_VALIDITY_NOT_ASSESSABLE`
9. copy-only + validity invalid → `COPY_ONLY_VALIDITY_INVALID`
10. full-only + validity NA → `FULL_ONLY_VALIDITY_NOT_ASSESSABLE`
11. n=14 + L true → `INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL`
12. n=16 + L true + control PASS → `EXPLORATORY_L_SIGNAL`
13. endpoint_ok=false → `M_NOT_EVALUABLE`
14. builder_ok=false → `M_NOT_EVALUABLE`
15. M norm zero → `M_NOT_EVALUABLE`
16. M pass L true + control PASS → `EXPLORATORY_L_SIGNAL`
17. M pass L false + control PASS → `MEAN_CONTRAST_ONLY`

### 6.3 Requirements

- every named cell exact output.
- every label reachable at least once.
- inputs not mutated.
- pure function; no model/data.
- synthetic fixtures only.
- no registered seed/real data.
- `ANDn` 2/4/5 operand tests.
- full Cartesian은 요구하지 않는다; per-axis + named cells로 정의.

---

## 7. P/PA contract

### 7.1 P

```text
P_VALID = delta_copy_step100 >= .05
          AND copy CI lower > 0
          AND delta_full_step100 > 0
          AND full CI lower > 0
```

- post-training native-path sensitivity screen.
- “selectivity learned”로 부르지 않는다.

### 7.2 PA

- PA = native memory + random adapter + decoder LoRA.
- **acquisition control**.
- `PA_STEP100_NOT_VALID`.
- `ADAPTER_REGIME_LOSS` 금지.
- `PA_RETENTION` null 가능; gate 아님.
- scale/geometry caveat 기록.

### 7.3 Hyperparameters

```text
optimizer: AdamW
weight_decay: .01
adapter_lr: 1e-3 (PA only)
lora_lr: 1e-4
updates: 100
batch: 1
order: train_ids[step % 20]
clip: 1.0
base decoder: eval
LoRA: 64 modules, r8 alpha16 dropout .05
```

---

## 8. M contract

### 8.1 Lengths / cohorts

| arm | K_M | source |
|---|---:|---|
| L | **753** | EG2 layer19 prefix |
| P/PA | **512** | native mT5 source prefix |

- M cohort: **15/20**.
- signal cohort: **val20**.
- full-K L: 11/20 secondary only.
- `M_CONTROL_PREFIX753_COHORT15`.

### 8.2 builder_ok

```text
builder_ok = contributors >= 10
             AND all M tensors finite
             AND ||M_POS_MEAN||_F > 0
             AND ||real_prefix||_F > 0
```

- L contributors 16; P/PA 20.
- zero/nonfinite → `M_NOT_EVALUABLE`.
- `m_evaluable` includes builder_ok.
- M_NORM is **magnitude-matched with target real-prefix norm**; target-dependent; no target labels.
- `M_NORM` leakage is norm-only; report `M_PASS_NORM_CONFOUNDED` if only POS passes.

### 8.3 Endpoint identity

`endpoint_ok`는 다음을 모두 요구한다.

- exact 15 IDs from preflight hash
- 3 seeds
- 4 arms (F/L/P/PA)
- each primary variant (M_POS_MEAN, M_NORM)
- each real/control CE
- all CE finite
- `copy_ce != None`
- copy tokens >=5
- no duplicate/missing ID
- no cohort substitution 15→14
- no target replacement

하나라도 실패 → `M_NOT_EVALUABLE`.

### 8.4 Builder

L:

1. `adapter.eval()`, `model.eval()`, `torch.no_grad()`.
2. train20 `A(h_i)`, `len >=753`.
3. contributors 16.
4. `M_POS_MEAN`.
5. `M_GLOBAL`.
6. `M_NORM`.

P/PA:

1. native train20, `len >=512`.
2. contributors 20.
3. same positionwise mean.
4. M_NORM.

### 8.5 Pass

```text
M_PASS_POS = delta_memfree_full > 0
             AND full CI lower > 0
             AND delta_memfree_copy > 0
             AND copy CI lower > 0

M_PASS_NORM = same with M_NORM

M_CONTROL_PASS_L = M_PASS_POS_L AND M_PASS_NORM_L
```

- M_POS_MEAN-only pass는 pass 아님.
- M_GLOBAL secondary; rescue 없음.

### 8.6 Aggregation/replay

- seed별 builder, seed-average before doc bootstrap.
- `m_pass_l = ANDn(...)`.
- `m_valid = ANDn(...)`.
- false-dominant.
- 3 seeds ×15 docs ≠ 45 independent.
- final checkpoint/state hash.
- replay separate process; `atol=1e-5`, `rtol=1e-4`.
- **prelaunch debug replay hash**와 **post-run final replay hash**를 구분.

---

## 9. Statistics

### 9.1 Constants

```text
n_boot = 1000
ci = percentile 2.5 / 97.5
bootstrap_seed = 20261109
unit = document
seed_average_before_bootstrap = true
n_min_signal = 15
```

### 9.2 New stats module

구현 시 **새 모듈**(예: `runner/c5_pm_stats.py`)을 사용한다.

- `bootstrap_paired(..., seed=20261109)`.
- `documents_positive`.
- `seeds_positive`는 seed mean에만.
- P0 helper의 `seed=20261108`/`seeds_positive` mislabel 재사용 금지.
- 2/3 seed rule:
```text
L_COPY_SIGNAL = mean delta_copy >= .05
                AND CI lower > 0
                AND paired L>F > 0
                AND 2/3 seed means >0
L_FULL_SIGNAL = same for full
L_SIGNAL = both
```
- `L>F` paired per-document.
- signal cohort val20; M cohort 15.
- top-3 share `sum(top3)/sum(all)`; denominator 0/비유한 → null.
- leave-top-3-out mean.
- `tail_driven = leave_top3_mean <=0 or top3_share > .50`.
- `MARGINAL_SIGNAL_COHORT` non-gating.

---

## 10. D0 / D1 / cap

### 10.1 Registered

| 항목 | 값 |
|---|---|
| units | 12 |
| updates | 1,200 |
| wall | 2 hours |
| threads | 6 |
| GPU | none |
| retry | none |

### 10.2 D0

- 0 optimizer updates
- ≤4 configs
- ≤15 min
- seed 20261111
- `labels_computed:false`, `not_a_result:true`
- separate from registered cap
- no timing claim

### 10.3 D1

- 4 arm-seeds ×1 update
- seed **20261111 shared**
- ≤20 min
- separate approval
- no labels
- `not_a_result:true`
- timed phases:
  1. 1 train update
  2. step0 eval **20 docs**
  3. final eval **20 docs**
  4. M builder **20 train / 15 target**
  5. replay **15 targets**
- each of 4 runs measures all five phases; missing phase → no projection.

### 10.4 Projection

```text
T_proj = 3 * sum_{arm in F,L,P,PA} (
            100 * t_train_arm
          + t_step0_eval_20_arm
          + t_step100_eval_20_arm
          + t_M_build_15_arm
          + t_replay_15_arm
        )
```

- subset 사용 시 per-doc normalize; omission 금지.
- `T_proj` finite, nonnegative, ≤**96 min**.
- D1 없이 3-seed 금지.
- D0-only projection 금지.
- “timing probe” substitute 금지.

### 10.5 Prelaunch vs post-run replay hash

- **prelaunch**: D1 `debug_replay_hash` (synthetic/debug state).
- **post-run**: final adapter/LoRA `final_checkpoint_hash` + `final_replay_hash`.
- 3-seed checklist item 14은 **prelaunch debug replay hash**만 요구한다.
- post-run final hash는 결과 report gate다.

### 10.6 Cap accounting

- D0/D1 separate; registered cap unchanged.
- combined prospective maximum = 1,204 updates / 155 min if all separately approved; not a grant.
- cap abort/no retry/no extension.

---

## 11. 3-seed launch checklist

1. r3.1 freeze commit hash
2. code commit hash
3. unit tests all green
4. D0 pass artifact
5. D1 timing artifact
6. preflight hash `3ee3f1ca…` + 15/20
7. debug seed 20261111 ∉ registered seeds
8. no threshold/seed/donor/step/LR diff
9. M_VALID **computation contract**
10. `M_CONTROL_PREFIX753_COHORT15` scope
11. signal val20 vs M 15 separation
12. T_proj ≤96 min
13. manifest complete
14. **prelaunch debug replay hash**
15. explicit user approval
16. test 163/P1 미사용
17. no B0-B/B1/B2/Stage C auto
18. post-run final checkpoint/replay hash validation plan

- item 14 ≠ final trained hash.
- item 18 is post-run, not prelaunch.

---

## 12. P0 limitation

- P0 source_max_length=256; registered M path 512.
- P0 historical native-path sensitivity only.
- 256/512 mismatch caveat; no P0 rerun.
- P0 is not trained P/PA/L or EG2 adaptation evidence.

---

## 13. Implementation DoD

- pure decision function
- ANDn 2/4/5 operand tests
- validity NA fixture F1–F8
- validity-INVALID vs NOT_ASSESSABLE labels
- m_valid/M_CONTROL_INVALID
- m_pass_l derivation
- builder_ok zero/nonfinite/contributor
- endpoint identity 15×3×4×variants
- M norm zero/nonfinite
- M seed aggregation
- M replay prelaunch debug/final post-run
- signal val20/M15 separation
- n_signal 0..20
- stats module seed 20261109/documents_positive/2-of-3
- truth-table per-axis + named cells
- P/PA mode/init tests
- PA acquisition labels
- no `ADAPTER_REGIME_LOSS`/`M_CONTROL_NOT_VALID`
- no stale `seeds_positive`
- manifest/checkpoint/replay hash
- `test_split_used:false`

---

## 14. B0-B boundary

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS
AND signal_status == EXPLORATORY_L_SIGNAL
AND m_valid == true (implied; consistency check)
AND tail_driven == false (or explicitly reported)
AND leakage/mode/metric pass
AND artifact complete
AND separate prereg/approval
```

- `EXPLORATORY_L_SIGNAL` alone does not approve B0-B.
- `M_CONTROL_PREFIX753_COHORT15` scope must be quoted.
- full-K 11/20, P0, PA_RETENTION are not B0-B evidence.
- B0-B/B1/B2/Stage C separate.

---

## 15. R3 residual closure

| Residual | r3.1 조치 | 상태 |
|---|---|---|
| AND3 arity | §2.2 ANDn/ORn 2/4/5 | closed |
| validity-NA labels | §5.2–5.3 split | closed |
| §6.3 unconditional NA | §3.6 F1–F8 | closed |
| builder zero/norm | §4.1/§8.2 builder_ok | closed |
| endpoint identity | §8.3 exact | closed |
| D1 workload/replay | §10.3–10.6 | closed |
| n_signal 16–19 | §5.1/§6.1 | closed |
| stats module/2-of-3 | §9.2 | closed |
| truth-table strategy | §6 | closed |

---

## 16. 동결 조건

- r3.1 review에서 NARROW가 다시 나오면 MUST-FIX만 수정한 r3.2를 작성한다.
- r3.1 승인 시 commit hash freeze.
- freeze 후 threshold/seed/donor/step/LR 변경 금지.
- 코드는 freeze 후에만 작성.
- 3-seed는 별도 gate.

---

## 17. 승인 요청

> **r3.1을 Phase 6 protocol contract로 동결하고, 구현 + unit tests + D0 zero-update mechanics debug를 진행해도 되는가?**

승인 후에도:
- D1은 별도 승인
- 3-seed는 별도 gate
- B0-B/B1/B2/Stage C는 별도
- test 163/P1 미사용
- T5Gemma2는 D-108 STOP
