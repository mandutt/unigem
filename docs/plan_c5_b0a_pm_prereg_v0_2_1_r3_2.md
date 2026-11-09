# C5 Phase 6 P/M Prereg v0.2.1-r3.2 — Freeze Blocker Repair

- 작성일: 2026-11-09
- 상태: **r3.2 동결 후보. 실행 미승인.**
- 적용 대상: `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_1.md` (r3.1)
- 충돌 시: **r3.2 > r3.1 > r3 > r2 > r1 > v0.2.1 > v0.2**
- 근거:
  - `reports/C5_B0A_PM_PREREG_V0_2_1_R3_1_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
  - r3.1 review: GLM CONTINUE conditional / DeepSeek 1017 NARROW / Sol NARROW
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. r3.2의 목적

r3.2는 r3.1의 **freeze blocker만** 닫는 text-only errata다.

- threshold/seed/donor/step/LR 변경 없음
- **full signal threshold는 기존 `>0`으로 복원** (새 threshold 아님)
- 결과 전에 commit/freeze
- 코드는 r3.2 승인 후에만 작성

---

## 1. R3.1 freeze blocker closure

| Blocker | r3.2 조치 |
|---|---|
| `L_FULL_SIGNAL` `.05` 회귀 | §9.2 full `>0` 전문 재기술 |
| fixture 16/17 불일치 | §6.2 primitive fixtures 16~18 |
| D1 generation/20-train M build 누락 | §10.3–10.5 full workload ledger |
| `M_NORM` 공식 제거 | §8.3 fixed formula |
| hash canonicalization 미정의 | §10.6 canonical hash |
| B0-B `tail_driven` 우회 | §14 hard `false` |
| small-N vs validity precedence | §5.5 + F11 |
| F9/F10 누락 | §3.7 |
| `§6.4` dangling ref | §6.1 |
| “committed blob” hash 표현 | §1.1 content SHA-256 |

### 1.1 Preflight artifact

- `reports/provenance/C5_b0a/m_cohort_preflight.json`
- **content SHA-256**: `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`
- 이 값은 **file content**의 SHA-256이며 git blob OID가 아니다.
- frozen preflight hash로 사용한다.

---

## 2. Primitive semantics

### 2.1 Tri-state

```text
true | false | not_assessable
```

### 2.2 ANDn/ORn

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

### 2.3 Signal consensus

```text
l_signal = true   if l_copy_signal=true and l_full_signal=true
           false  if l_copy_signal=false and l_full_signal=false
           not_assessable otherwise

copy_only = ANDn(l_copy_signal, NOT3(l_full_signal))
full_only = ANDn(l_full_signal, NOT3(l_copy_signal))
```

---

## 3. Validity

### 3.1 Values

```text
ASSAY_INVALID
P_STEP100_NOT_VALID
PA_STEP100_NOT_VALID
NOT_ASSESSABLE
VALID
```

- `M_NOT_EVALUABLE`/`M_CONTROL_INVALID`는 validity가 아니다.

### 3.2 Known failure first

```text
if assay_path_ok is false
   or p0_path_ok is false
   or test_split_used is true
   or p_step100_path_ok is false:
    ASSAY_INVALID
```

### 3.3 Assay-tier NA

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

### 3.5 Tier rule

- assay-tier NA(§3.3)는 P/PA validity보다 먼저다.
- `p_step100_path_ok=NA` + `p_valid=false` → `NOT_ASSESSABLE` (assay-tier).
- `pa_step100_path_ok=NA` + `p_valid=false` → `P_STEP100_NOT_VALID` (P validity before PA path).
- `pa_step100_path_ok=NA` + `pa_valid=false` → `NOT_ASSESSABLE` (PA path NA before PA valid).
- 이 tier는 의도된 계약이며 F9/F10으로 고정한다.

### 3.6 Core invariants

- `validity_status`는 M 상태를 반환하지 않는다.
- `test_split_used=true` → `ASSAY_INVALID`.
- `p_step100_path_ok=false` → `ASSAY_INVALID`.
- P valid + PA path false → `PA_STEP100_NOT_VALID`.
- P invalid + PA path false → `P_STEP100_NOT_VALID`.

### 3.7 F1–F11 fixtures

| fixture | flags | expected |
|---|---|---|
| F1 | test_split NA + P path false | `ASSAY_INVALID` |
| F2 | test_split NA + paths good | `NOT_ASSESSABLE` |
| F3 | pa_path NA + P invalid | `P_STEP100_NOT_VALID` |
| F4 | pa_path NA + P valid | `NOT_ASSESSABLE` |
| F5 | assay NA + P path false | `ASSAY_INVALID` |
| F6 | assay NA + paths good | `NOT_ASSESSABLE` |
| F7 | pa_path false + P valid | `PA_STEP100_NOT_VALID` |
| F8 | pa_path false + P invalid | `P_STEP100_NOT_VALID` |
| F9 | p_step NA + p_valid false | `NOT_ASSESSABLE` |
| F10 | pa_path NA + pa_valid false | `NOT_ASSESSABLE` |
| F11 | n<15 + validity INVALID | small-N label + validity INVALID recorded |

---

## 4. Control

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
             AND all 15 ||real_prefix_t||_F > 0
```

```text
m_evaluable = ANDn(cohort_ok, endpoint_ok, seed_ok, replay_ok, builder_ok)
```

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
elif p_valid is false or pa_valid is false:
    M_NOT_EVALUABLE
elif p_valid is not_assessable or pa_valid is not_assessable:
    NOT_ASSESSABLE
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
- `p/pa` NA를 `M_NOT_EVALUABLE`로 접지 않는다.

---

## 5. Signal

### 5.1 n_signal

```text
signal cohort = val20
n_signal = number of val20 docs with valid copy and full endpoints
n_signal ∈ {NA, 0..20}
n_min = 15
```

- `n_signal=15` → `MARGINAL_SIGNAL_COHORT=true`.
- signal cohort val20; M cohort 15.
- endpoint membership: F/L arms × 3 seeds × copy/full; same retained IDs.
- missing seed는 pooling하지 않는다.

### 5.2 Label classes

- validity INVALID:
  - `L_SIGNAL_VALIDITY_INVALID`
  - `COPY_ONLY_VALIDITY_INVALID`
  - `FULL_ONLY_VALIDITY_INVALID`
- validity NOT_ASSESSABLE:
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

- raw flags always in `flags`.
- `NOT_ASSESSABLE` carries `signal_reason` + raw flags.
- `*_VALIDITY_NOT_ASSESSABLE`와 `*_VALIDITY_INVALID`를 구분한다.
- report는 `(validity, control, signal, flags, reason)`을 함께 기록.

### 5.5 Small-N precedence

- `n_signal<15`이면 small-N 계열이 **signal_status의 1차 label**이다.
- validity/control은 별도 축으로 항상 기록한다.
- small-N이 validity failure를 **숨기지 않는다**: `(validity_status, control_status, signal_status)` triple과 reason을 함께 report.
- F11: n<15 + validity INVALID → small-N label + `validity=ASSAY_INVALID`/P/PA 상태 기록.
- 이 precedence는 의도된 계약이며 테스트로 고정한다.

---

## 6. Truth-table

### 6.1 Per-axis

- validity path axis 3^5
- p/pa validity 3^2
- control availability 3^4 + builder 3^1
- calibration 3^4
- L 3^2
- n_signal `{NA,0..20}`

### 6.2 Primitive fixtures 16–18

**중요**: fixture는 primitive에서 derive한다; `control_status`를 직접 주입하지 않는다.

#### Fixture 16 — EXPLORATORY

```text
validity_status = VALID
n_signal = 20
l_copy_signal = true
l_full_signal = true
m_evaluable = true
p_valid = true
pa_valid = true
m_valid = true
m_pass_l = true
```

Derived:

```text
l_signal = true
control_status = M_CONTROL_PASS
signal_status = EXPLORATORY_L_SIGNAL
```

#### Fixture 17 — MEAN_CONTRAST_ONLY

```text
validity_status = VALID
n_signal = 20
l_copy_signal = false
l_full_signal = false
m_evaluable = true
p_valid = true
pa_valid = true
m_valid = true
m_pass_l = true
```

Derived:

```text
l_signal = false
control_status = M_CONTROL_PASS
signal_status = MEAN_CONTRAST_ONLY
```

#### Fixture 18 — NO_AFFIRMATIVE

```text
validity_status = VALID
n_signal = 20
l_copy_signal = false
l_full_signal = false
m_evaluable = true
p_valid = true
pa_valid = true
m_valid = true
m_pass_l = false
```

Derived:

```text
l_signal = false
control_status = M_CONTROL_FAIL
signal_status = NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE
```

### 6.3 Other named cells

- F1–F11.
- m_valid=false + P/PA valid → `M_CONTROL_INVALID`.
- m_evaluable=false + L true → `L_SIGNAL_M_CONTROL_NOT_EVALUABLE`.
- validity invalid + L → `L_SIGNAL_VALIDITY_INVALID`.
- validity NA + L → `L_SIGNAL_VALIDITY_NOT_ASSESSABLE`.
- copy-only + invalid/NA.
- n=14 + L.
- n=16 + L + control PASS.
- endpoint_ok=false / builder_ok=false / M norm zero → `M_NOT_EVALUABLE`.
- M pass L true + control PASS → `EXPLORATORY`.
- M pass L false + control PASS → `MEAN_CONTRAST_ONLY`.

### 6.4 Requirements

- every named cell exact output.
- every label reachable.
- inputs not mutated.
- pure function; no model/data.
- synthetic fixtures only.
- `ANDn` 2/4/5.
- full Cartesian 요구하지 않음; per-axis + named.

---

## 7. P/PA

### 7.1 P

```text
P_VALID = delta_copy_step100 >= .05
          AND copy CI lower > 0
          AND delta_full_step100 > 0
          AND full CI lower > 0
```

### 7.2 PA

- PA = native memory + random adapter + decoder LoRA.
- acquisition control.
- `PA_STEP100_NOT_VALID`.
- `ADAPTER_REGIME_LOSS` 금지.
- `PA_RETENTION` null 가능; gate 아님.
- PA step0는 별도 실행.

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

## 8. M

### 8.1 Lengths/cohorts

| arm | K_M | source |
|---|---:|---|
| L | **753** | EG2 layer19 prefix |
| P/PA | **512** | native mT5 source prefix |

- M cohort 15/20.
- signal cohort val20.
- full-K L 11/20 secondary.
- `M_CONTROL_PREFIX753_COHORT15`.

### 8.2 builder_ok

```text
builder_ok = contributors >= 10
             AND all M tensors finite
             AND ||M_POS_MEAN||_F > 0
             AND all 15 ||real_prefix_t||_F > 0
```

- L contributors 16; P/PA 20.
- zero/nonfinite → `M_NOT_EVALUABLE`.

### 8.3 M_NORM fixed formula

```text
M_NORM(t) = M_POS_MEAN * ( ||real_prefix_t||_F / ||M_POS_MEAN||_F )
```

- `M_POS_MEAN` = **one global train-only mean matrix**.
- `real_prefix_t` = target `t`의 real prefix (L 753 / native 512).
- `M_NORM(t)` = **per-target scalar × one global mean direction**.
- target-dependent은 **magnitude scalar만**; target label/mean direction leakage 없음.
- `builder_ok`는 all 15 `||real_prefix_t||>0`.
- per-target matrix를 만들지 않는다.
- `M_NORM`은 magnitude-matched, target-set-norm-dependent control.

### 8.4 Endpoint identity

`endpoint_ok`:

- exact 15 IDs from preflight hash
- 3 seeds
- 4 arms (F/L/P/PA)
- primary variants (M_POS_MEAN, M_NORM)
- real/control CE finite
- `copy_ce != None`
- copy tokens >=5
- no duplicate/missing
- no 15→14 substitution
- no target replacement

하나라도 실패 → `M_NOT_EVALUABLE`.

### 8.5 Pass

```text
M_PASS_POS = delta_memfree_full > 0
             AND full CI lower > 0
             AND delta_memfree_copy > 0
             AND copy CI lower > 0

M_PASS_NORM = same with M_NORM

M_CONTROL_PASS_L = M_PASS_POS_L AND M_PASS_NORM_L
```

- M_POS_MEAN-only pass 아님.
- `M_GLOBAL` secondary.
- `M_PASS_NORM_CONFOUNDED` descriptive.

### 8.6 Aggregation/replay

- seed별 builder; seed-average before doc bootstrap.
- `m_pass_l = ANDn`.
- `m_valid = ANDn`.
- false-dominant.
- 3 seeds ×15 docs ≠ 45 independent.
- final checkpoint/state hash.
- replay separate; `atol=1e-5`, `rtol=1e-4`.
- prelaunch debug replay hash vs postrun final replay hash.

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

### 9.2 L predicates (threshold restore)

```text
L_COPY_SIGNAL = mean delta_copy >= .05
                AND copy CI lower > 0
                AND paired L>F copy mean > 0
                AND 2/3 seed copy means > 0

L_FULL_SIGNAL = mean delta_full > 0
                AND full CI lower > 0
                AND paired L>F full mean > 0
                AND 2/3 seed full means > 0

L_SIGNAL = ANDn(L_COPY_SIGNAL, L_FULL_SIGNAL)
```

- full threshold는 **`>0`**; `.05` 아님.
- copy threshold는 **`.05`**.
- `seed_mean` = 해당 endpoint의 arm-L shuffled-minus-real mean; L−F와 별개.
- L−F는 paired per-document.
- threshold 변경 없음.

### 9.3 Stats module

- `runner/c5_pm_stats.py` (new)
- `bootstrap_paired(seed=20261109)`
- `documents_positive`
- `seeds_positive` = seed mean only
- P0 helper 재사용 금지 (`seed=20261108`, 문서 수 mislabel)
- 2/3 seed rule above.

### 9.4 Partial endpoint / tail

- canonical endpoint keys: F/L × 3 seeds × copy/full.
- same retained IDs for copy/full/L−F.
- missing seed → no pooling; excluded ID/reason.
- nonfinite CE → excluded with reason.
- `n_signal` counts only valid endpoints.
- `top3_share = sum(top3)/sum(all)`:
  - denominator 0 → null.
  - signed sum may fall outside [0,1]; descriptive only.
- `leave_top3_mean`:
  - n<4 → null.
- `tail_driven` tri-state:
  - known positive criterion → true
  - both known false → false
  - otherwise NA
- B0-B requires **false**; NA not pass.
- `MARGINAL_SIGNAL_COHORT` non-gating.

---

## 10. D0/D1/cap

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

### 10.3 D1 phases

- 4 arm-seeds ×1 update
- seed **20261111 shared**
- ≤20 min
- separate approval
- no labels
- `not_a_result:true`

Timed phases (full workload, no subset):

1. **one train update** per arm
2. **step0 eval 20 docs × 5 donors** before update
3. **final eval 20 docs × 5 donors** after update
4. **M builder 20 train + 15 target × 2 variants**
5. **generation 20 docs × max_new_tokens=256**
6. **replay 15 targets × 5 donors × 2 variants**
7. **load/checkpoint/process/report overhead**

- 각 arm-run은 7 phase 전부 측정.
- missing phase → no projection.
- step0는 update 전 또는 동일 unupdated state restore에서 측정.

### 10.4 T_proj

```text
T_proj = 3 * sum_{arm in F,L,P,PA} (
            100 * t_train_arm
          + t_step0_eval_20x5_arm
          + t_step100_eval_20x5_arm
          + t_M_build_20x15x2_arm
          + t_generate_20x256_arm
          + t_replay_15x5x2_arm
          + t_overhead_arm
        )
```

- `3` = seeds; `100` = updates.
- generation 포함.
- M build 20 train 포함.
- donor multiplicity 5 포함.
- variants 2 포함.
- overhead 포함.
- `T_proj` finite, nonnegative, ≤**96 min**.
- D1 없이 3-seed 금지.
- D0-only projection 금지.
- “timing probe” 대체 금지.

### 10.5 Cap accounting

- D0/D1 separate.
- prospective combined max = 1,204 updates / 155 min (not a grant).
- cap abort/no retry/no extension.

### 10.6 Canonical hash

**Checkpoint hash**:

```text
state_dict keys sorted
include adapter parameters + LoRA A/B
exclude frozen base
for each key: name | dtype.str | shape | little-endian contiguous bytes
SHA256 over canonical byte stream
```

**Replay hash**:

```text
records sorted by (doc_id, arm, seed, variant, endpoint)
each record: id, arm, seed, variant, endpoint, CE float64
canonical JSON (sorted keys, separators=(',',':'))
SHA256
```

- `debug_replay_hash` = D1 synthetic/debug state.
- `final_checkpoint_hash` = post-run adapter/LoRA.
- `final_replay_hash` = post-run endpoint CE records.
- golden-vector test: fixed synthetic state/tensors → expected SHA256.
- prelaunch checklist uses debug hash only; final hashes are post-run.

---

## 11. 3-seed checklist

1. r3.2 freeze commit hash
2. code commit hash
3. unit tests all green
4. D0 pass artifact
5. D1 timing artifact
6. preflight hash `3ee3f1ca…` + 15/20
7. debug seed 20261111 ∉ registered seeds
8. no threshold/seed/donor/step/LR diff
9. M_VALID computation contract
10. `M_CONTROL_PREFIX753_COHORT15` scope
11. signal val20 vs M 15 separation
12. T_proj ≤96 min (generation/M build/overhead 포함)
13. manifest complete
14. prelaunch debug replay hash
15. explicit user approval
16. test 163/P1 미사용
17. no B0-B/B1/B2/Stage C auto
18. post-run final checkpoint/replay hash validation plan
19. canonical hash golden-vector test green
20. stats module seed/documents_positive/2-of-3 tests green

- item 14 ≠ final hash.
- item 18 post-run only.

---

## 12. P0 limitation

- P0 source_max_length=256; registered M 512.
- P0 historical native-path sensitivity only.
- no P0 rerun.
- P0 not trained P/PA/L evidence.

---

## 13. Implementation DoD

- pure decision function
- ANDn 2/4/5
- F1–F11
- validity INVALID vs NOT_ASSESSABLE labels
- m_valid/M_CONTROL_INVALID
- m_pass_l derivation
- builder_ok zero/nonfinite/contributor
- endpoint identity 15×3×4×2
- M_NORM fixed formula
- M seed aggregation
- canonical hash golden vector
- replay prelaunch/final
- signal val20/M15 separation
- n_signal 0..20
- stats module seed 20261109/documents_positive/2-of-3
- L_COPY/L_FULL predicate tests
- fixture 16/17/18
- tail tri-state/partial endpoint
- P/PA mode/init
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
AND m_valid == true (consistency check)
AND n_signal >= 15
AND tail_driven == false
AND leakage/mode/metric pass
AND artifact complete
AND separate prereg/approval
```

- `tail_driven=NA`는 B0-B 불가.
- `tail_driven=true`는 B0-B 불가; “reported”로 통과하지 않는다.
- `EXPLORATORY_L_SIGNAL` alone은 B0-B 승인 아님.
- `M_CONTROL_PREFIX753_COHORT15` scope 명시.
- full-K 11/20/P0/PA_RETENTION은 B0-B 근거 아님.

---

## 15. R3.1 closure

| Blocker | 조치 | 상태 |
|---|---|---|
| L_FULL_SIGNAL `.05` | §9.2 `>0` 복원 | closed |
| fixture 16/17 | §6.2 primitive 16–18 | closed |
| D1 generation/M build | §10.3–10.4 | closed |
| M_NORM formula | §8.3 fixed | closed |
| hash canonicalization | §10.6 | closed |
| B0-B tail_driven | §14 hard false | closed |
| small-N/validity | §5.5/F11 | closed |
| F9/F10 | §3.7 | closed |
| `§6.4` | §6.1 | closed |
| blob 표현 | §1.4 content SHA-256 | closed |

---

## 16. 동결 조건

- r3.2 review에서 NARROW가 다시 나오면 MUST-FIX만 수정한 r3.3을 작성한다.
- r3.2 승인 시 commit hash freeze.
- freeze 후 threshold/seed/donor/step/LR 변경 금지.
- 코드는 freeze 후에만 작성.
- 3-seed는 별도 gate.

---

## 17. 승인 요청

> **r3.2를 Phase 6 protocol contract로 동결하고, 구현 + unit tests + D0 zero-update mechanics debug를 진행해도 되는가?**

승인 후에도:
- D1은 별도 승인
- 3-seed는 별도 gate
- B0-B/B1/B2/Stage C는 별도
- test 163/P1 미사용
- T5Gemma2는 D-108 STOP
