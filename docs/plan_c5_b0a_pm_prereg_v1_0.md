# C5 Phase 6 P/M Prereg — v1.0 Consolidated Normative Spec

- 작성일: 2026-11-09
- 상태: **v1.0 review candidate. 실행 미승인.**
- 문서 성격: **구현 권위 문서(단일 normative spec)**
- 대체 대상: `v0.2.1-r3.4` 및 그 이전 P/M prereg chain
- 역사 문서: `v0.2`, `v0.2.1`, `r1`, `r2`, `r3`, `r3.1`, `r3.2`, `r3.3`, `r3.4`는 **traceability only**
- 충돌 시: **v1.0 > 모든 이전 P/M 문서**
- freeze 후: **v1.0 + 번호가 붙은 ERRATA만** 유효
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. Authority and scope

### 0.1 Normative status

이 문서는 C5 Phase 6 P/M 실험의 **유일한 구현 계약**이다.

- 구현자는 이 문서만 읽고 코드를 작성할 수 있어야 한다.
- 이전 r3.x 문서를 참조하지 않는다.
- 이전 문서와 충돌하는 문장은 모두 이 문서가 대체한다.
- 리뷰 보고서는 역사 기록이며 구현 권위가 아니다.

### 0.2 Scope

- Phase 6: F/L/P/PA 4-arm, 3 seeds, 100 updates.
- M: eval-only memory control.
- D0: zero-update mechanics.
- D1: separate timing/debug run.
- 3-seed: separate registered run.
- B0-B: separate downstream gate.

### 0.3 Non-goals

- STT/F2 재개 없음.
- T5Gemma2 bridge 재개 없음.
- B0-B/B1/B2/Stage C 자동 승인 없음.
- test 163/P1 사용 없음.
- 결과 후 threshold/seed/donor/step/LR 변경 없음.

### 0.4 Preflight artifact

- `reports/provenance/C5_b0a/m_cohort_preflight.json`
- content SHA-256: **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`**
- git blob OID가 아닌 file content hash.
- frozen preflight hash.

---

## 1. Data, cohorts, identities

### 1.1 Splits

- clean F5: 1,617
- train/val/test: **1,293 / 161 / 163**, seed 42
- Phase 6 uses:
  - train20 = `train[:20]`
  - val20 = `val[5:25]`
  - test 163 = **sealed**

### 1.2 Length cohorts

| cohort | 정의 | n |
|---|---|---:|
| train20 | train[:20] | 20 |
| val20 | val[5:25] | 20 |
| L signal eligible | val20 with `h_len >= 753` | **15** |
| L M targets | common_ids at K=753 | **15** |
| native P/PA | all val20 at 512 | **20** |

- preflight `common_ids` = 15.
- zero-margin: K=753, K=754 → 14 eligible.
- 15→14 substitution 금지.

### 1.3 IDs

- `train20_ids` and `val20_ids` are frozen in preflight.
- `common_ids` = 15 L-eligible val IDs.
- no target replacement.
- no duplicate target.
- no test ID.

### 1.4 Leakage

- test 163 not read.
- P1 not used.
- no external API on P1.
- P0 only external (public/synthetic).
- preflight no model forward.

---

## 2. Arms and training

### 2.1 Arm table

| arm | memory | M K | adapter | trainable | role |
|---|---|---:|---|---|---|
| F | EG2 layer19 | 753 | trained | adapter | reference |
| L | EG2 layer19 | 753 | trained | adapter + decoder LoRA | B0-A 재검증 |
| P | native mT5 encoder | 512 | none (`A=identity`) | decoder LoRA only | positive control |
| PA | native mT5 encoder | 512 | random-init trained | adapter + decoder LoRA | P/F regime 정합 |

- 12 units = 4 arms × 3 seeds.
- M K applies only to M; see §2.3.
- F/L adapter geometry 512; memory prefix 753.

### 2.2 Hyperparameters

```text
optimizer: AdamW
weight_decay: .01
adapter_lr: 1e-3 for F, L, PA
lora_lr: 1e-4 for L, P, PA
updates: 100
batch: 1
order: train20_ids[step % 20]
clip: 1.0
base decoder: eval
LoRA: 64 modules, r8 alpha16 dropout .05
```

- P has no adapter; adapter_lr not applied.
- `adapter_lr` applies to F/L/PA.
- `lora_lr` applies to L/P/PA.

### 2.3 Workload-specific length/crop

**M memory**:

- F/L: `M_POS_MEAN` from `A(h_i)[:753]`
- P/PA: `A(h_i)[:512]`
- donor-crop 금지
- target prefix `A(h_t)[:K_M]`

**Training/eval signal**:

- donor-crop `K = min(len(real), len(donor))` per document.
- all 20 train/val docs.
- 753 not required.
- no padding/drop/order change.

**Generation**:

- 20 val docs.
- `max_new_tokens=256`.
- 753 not required.

**Rule**:

- `K_M=753` is **M-only**.
- training/eval/generation must not require 753.
- 이 규칙은 4 train/5 val short docs를 처리한다.

### 2.4 P/PA initialization

- P: native mT5 encoder, no adapter.
- PA: native mT5 encoder + random-init adapter + decoder LoRA.
- PA adapter seed: same registered seed.
- PA is acquisition control; not retention gate.

---

## 3. Primitive semantics

### 3.1 Tri-state

```text
true | false | not_assessable
```

### 3.2 Operators

```text
ANDn(args):
  any false -> false
  else any NA -> NA
  else true

ORn(args):
  any true -> true
  else any NA -> NA
  else false

NOT3(x):
  true -> false
  false -> true
  NA -> NA
```

- scalar tri-state predicates only.
- no seed/endpoint axis inside operator.
- `m_pass_l`(2), `m_valid`(4), `m_evaluable`(5).

### 3.3 L consensus

```text
l_signal = true   if l_copy_signal=true and l_full_signal=true
           false  if l_copy_signal=false and l_full_signal=false
           NA     otherwise

l_copy_signal := L_COPY_SIGNAL
l_full_signal := L_FULL_SIGNAL
```

- **binding is direct**; no alias.
- `l_signal` is not `ANDn`.
- `ANDn` only for `m_pass_l`, `m_valid`, `m_evaluable`, `copy_only`, `full_only`.

```text
copy_only = ANDn(l_copy_signal, NOT3(l_full_signal))
full_only = ANDn(l_full_signal, NOT3(l_copy_signal))
```

### 3.4 L table

| l_copy | l_full | l_signal | copy_only | full_only |
|---|---|---|---|---|
| true | true | true | false | false |
| true | false | **NA** | true | false |
| true | NA | NA | NA | false |
| false | true | **NA** | false | true |
| false | false | false | false | false |
| false | NA | NA | false | NA |
| NA | true | NA | false | NA |
| NA | false | NA | NA | false |
| NA | NA | NA | NA | NA |

- `copy_only`/`full_only` precede `l_signal` in dispatch.
- `false+NA` → `NOT_ASSESSABLE`; not `MEAN_CONTRAST_ONLY`.

### 3.5 L predicates

```text
L_COPY_SIGNAL = mean delta_copy >= .05
                AND copy CI lower > 0
                AND paired L>F copy mean > 0
                AND 2/3 registered seed copy means > 0

L_FULL_SIGNAL = mean delta_full > 0
                AND full CI lower > 0
                AND paired L>F full mean > 0
                AND 2/3 registered seed full means > 0
```

- `delta_copy = shuffled_copy_ce - real_copy_ce`.
- `delta_full = shuffled_full_ce - real_full_ce`.
- positive = real memory better.
- full threshold **`>0`**, copy **`.05`**.
- registered seeds 20261108/09/10.
- missing registered seed → predicate `NA`; 2-of-available 금지.
- existing 2 seeds only → `NA`, not 2/2.

---

## 4. Validity

### 4.1 Values

```text
ASSAY_INVALID
P_STEP100_NOT_VALID
PA_STEP100_NOT_VALID
NOT_ASSESSABLE
VALID
```

### 4.2 Known failure first

```text
if assay_path_ok is false
   or p0_path_ok is false
   or test_split_used is true
   or p_step100_path_ok is false:
    ASSAY_INVALID
```

### 4.3 Assay-tier NA

```text
elif assay_path_ok is not_assessable
   or p0_path_ok is not_assessable
   or p_step100_path_ok is not_assessable
   or test_split_used is not_assessable:
    NOT_ASSESSABLE
```

### 4.4 P/PA

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

### 4.5 P_VALID / PA_VALID

```text
P_VALID = 20 native docs, 100-step shuffled-vs-real:
          mean delta_copy >= .05
          AND copy CI lower > 0
          AND mean delta_full > 0
          AND full CI lower > 0

PA_VALID = same 20 native docs, 100-step shuffled-vs-real:
           mean delta_copy >= .05
           AND copy CI lower > 0
           AND mean delta_full > 0
           AND full CI lower > 0
```

- P/PA cohort = **20 native docs**, 512.
- L/F cohort = 15 common IDs.
- P/PA `m_pass_pos/norm` use 20 native docs.
- PA_VALID is defined here, not inherited.
- P/PA validity does not use test 163.

### 4.6 Tier precedence

- assay-tier NA before P/PA validity.
- `p_step NA + p_valid=false` → `NOT_ASSESSABLE`.
- `pa_path NA + p_valid=false` → `P_STEP100_NOT_VALID`.
- `pa_path NA + pa_valid=false` → `NOT_ASSESSABLE`.
- F1–F11 in §7.

### 4.7 Core invariants

- validity never returns M status.
- test_split_used=true → ASSAY_INVALID.
- p_step false → ASSAY_INVALID.
- P valid + PA path false → PA_STEP100_NOT_VALID.
- P invalid + PA path false → P_STEP100_NOT_VALID.

---

## 5. Control

### 5.1 Availability

```text
cohort_ok  = common M target IDs >= 15/20
endpoint_ok = §9.4
seed_ok    = 3 registered seeds
replay_ok  = numeric replay pass
builder_ok = contributors >=10
             AND all M tensors finite
             AND ||M_POS_MEAN||_F > 0
             AND all 15 ||real_prefix_t||_F > 0
```

```text
m_evaluable = ANDn(cohort_ok, endpoint_ok, seed_ok, replay_ok, builder_ok)
```

- `m_evaluable` false or NA → `M_NOT_EVALUABLE`.
- availability NA collapse is intentional; no silent true.
- seed_ok only registered seeds; no substitutes.

### 5.2 m_pass

```text
m_pass_l = ANDn(m_pass_pos_l, m_pass_norm_l)

m_valid = ANDn(
  m_pass_pos_p, m_pass_norm_p,
  m_pass_pos_pa, m_pass_norm_pa
)
```

- false-dominant; mixed false+NA → false.
- missingness-first 금지.
- P/PA pass uses 20 native docs.
- M L pass uses 15 common targets.

### 5.3 PA veto

- PA is native 512 + random-init adapter + decoder LoRA.
- PA failure vetoes joint P/PA calibration; it does not prove native memory regime is intrinsically invalid.
- `m_valid` includes PA intentionally.
- `PA_RETENTION` is descriptive/nullable; never a gate.

### 5.4 control_status

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

- `M_CONTROL_NOT_VALID` 금지.
- `M_CONTROL_INVALID` only when P/PA valid but calibration fail.
- `p_valid=false` routes to `M_NOT_EVALUABLE`, not `M_CONTROL_INVALID`.

---

## 6. Signal labels and dispatch

### 6.1 n_signal

```text
n_signal = number of 15 L-eligible docs with valid F/L copy and full endpoints
n_signal ∈ {NA, 0..15}
n_min = 15
```

- `n_signal=15` → `MARGINAL_SIGNAL_COHORT=true`.
- val20 is descriptive only.
- no val20 signal count.
- missing seed no pooling.

### 6.2 Labels

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
- fallback `NOT_ASSESSABLE`.

### 6.3 Dispatch

```text
if n_signal is NA: NOT_ASSESSABLE
elif n_signal < 15:
    if l_signal true: INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL
    elif copy_only true: INCONCLUSIVE_SMALL_N_WITH_COPY_ONLY
    elif full_only true: INCONCLUSIVE_SMALL_N_WITH_FULL_ONLY
    else: INCONCLUSIVE_SMALL_N
elif validity == NOT_ASSESSABLE:
    if l_signal true: L_SIGNAL_VALIDITY_NOT_ASSESSABLE
    elif copy_only true: COPY_ONLY_VALIDITY_NOT_ASSESSABLE
    elif full_only true: FULL_ONLY_VALIDITY_NOT_ASSESSABLE
    else: NOT_ASSESSABLE
elif validity != VALID:
    if l_signal true: L_SIGNAL_VALIDITY_INVALID
    elif copy_only true: COPY_ONLY_VALIDITY_INVALID
    elif full_only true: FULL_ONLY_VALIDITY_INVALID
    else: NOT_ASSESSABLE
elif copy_only true: COPY_ONLY_WEAK
elif full_only true: FULL_ONLY_WEAK
elif l_signal is NA: NOT_ASSESSABLE
elif l_signal true:
    if control == M_CONTROL_PASS: EXPLORATORY_L_SIGNAL
    elif control == M_CONTROL_FAIL: L_SIGNAL_M_CONTROL_FAIL
    elif control == M_CONTROL_INVALID: L_SIGNAL_M_CONTROL_INVALID
    elif control == M_NOT_EVALUABLE: L_SIGNAL_M_CONTROL_NOT_EVALUABLE
    else: L_SIGNAL_CONTROL_NOT_ASSESSABLE
elif control == M_CONTROL_PASS: MEAN_CONTRAST_ONLY
elif control == M_CONTROL_FAIL: NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE
elif control == M_CONTROL_INVALID: NO_L_SIGNAL_CONTROL_INVALID
elif control == M_NOT_EVALUABLE: NO_L_SIGNAL_CONTROL_NOT_EVALUABLE
else: NOT_ASSESSABLE
```

### 6.4 Preservation

- raw flags always in `flags`.
- `(validity, control, signal, reason)` tuple.
- INVALID vs NOT_ASSESSABLE labels distinct.
- 9 L pairs preserved.
- small-N does not hide validity; triple always reported.

---

## 7. Truth-table and fixtures

### 7.1 Per-axis

- validity path 3^5
- P/PA 3^2
- control availability 3^4 + builder 3^1
- calibration 3^4
- L 3^2 (9 pairs; §3.4)
- n_signal `{NA,0..15}`

### 7.2 F1–F11

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
| F11 | n<15 + validity INVALID | small-N + validity INVALID |

### 7.3 Primitive fixtures 16–18

Fixtures use primitive flags; derived `m_pass_l`/`m_valid` are not inputs.

#### Fixture 16 — EXPLORATORY

```text
validity_status = VALID
n_signal = 15
l_copy_signal = true
l_full_signal = true
m_evaluable = true
p_valid = true
pa_valid = true
m_pass_pos_l = true
m_pass_norm_l = true
m_pass_pos_p = true
m_pass_norm_p = true
m_pass_pos_pa = true
m_pass_norm_pa = true
```

Derived:

```text
l_signal = true
m_pass_l = true
m_valid = true
control_status = M_CONTROL_PASS
signal_status = EXPLORATORY_L_SIGNAL
```

#### Fixture 17 — MEAN_CONTRAST_ONLY

```text
validity_status = VALID
n_signal = 15
l_copy_signal = false
l_full_signal = false
m_evaluable = true
p_valid = true
pa_valid = true
m_pass_pos_l = true
m_pass_norm_l = true
m_pass_pos_p = true
m_pass_norm_p = true
m_pass_pos_pa = true
m_pass_norm_pa = true
```

Derived:

```text
l_signal = false
m_pass_l = true
m_valid = true
control_status = M_CONTROL_PASS
signal_status = MEAN_CONTRAST_ONLY
```

#### Fixture 18 — NO_AFFIRMATIVE

```text
validity_status = VALID
n_signal = 15
l_copy_signal = false
l_full_signal = false
m_evaluable = true
p_valid = true
pa_valid = true
m_pass_pos_l = false
m_pass_norm_l = true
m_pass_pos_p = true
m_pass_norm_p = true
m_pass_pos_pa = true
m_pass_norm_pa = true
```

Derived:

```text
l_signal = false
m_pass_l = false
m_valid = true
control_status = M_CONTROL_FAIL
signal_status = NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE
```

### 7.4 Named cells

- F1–F11.
- 9 L pairs.
- control 5 values.
- named cells are fixtures 16–18 only.
- generic “M pass L” text must include validity/availability/calibration/L/n prerequisites.
- `m_pass_l=false` can yield `M_CONTROL_FAIL` only with `m_evaluable=true`, P/PA valid/calibrated, m_valid=true.
- no control PASS + m_pass_l=false cell.

### 7.5 Requirements

- every named cell exact output.
- every label reachable.
- inputs not mutated.
- pure function; no model/data.
- synthetic fixtures.
- no full Cartesian requirement; per-axis + named.

---

## 8. P/PA

### 8.1 P

- native mT5 512, no adapter, decoder LoRA.
- 100 updates.
- 20 native docs.
- `P_VALID` §4.5.

### 8.2 PA

- native mT5 512, random-init adapter, decoder LoRA.
- 100 updates.
- 20 native docs.
- `PA_VALID` §4.5.
- `PA_STEP100_NOT_VALID` is acquisition failure.
- `PA_RETENTION` nullable/descriptive; not gate.
- geometry caveat: 512 vs 753; no direct retention comparison.

### 8.3 P/PA M pass

- `m_pass_pos_p/norm_p`: 20 native docs.
- `m_pass_pos_pa/norm_pa`: 20 native docs.
- M L pass uses 15 common.
- `m_valid` = P/PA calibration.

---

## 9. M

### 9.1 Cohorts

| arm | M K | M targets | contributors |
|---|---:|---:|---:|
| F | 753 | 15 | 16 |
| L | 753 | 15 | 16 |
| P | 512 | 15 common | 20 |
| PA | 512 | 15 common | 20 |

- signal eligible 15.
- val20 descriptive.
- `full_k_secondary` is historical/descriptive only; not in any gate.
- zero-margin: K=753; K=754→14; abort.

### 9.2 Builder

For each seed and arm:

```text
model.eval()
with torch.no_grad():
    contributors = [i for i in train20 if h_len_i >= K_M]
    if len(contributors) < 10: builder_ok=false
    else:
        h_i = A(h_i)[:K_M]       # K_M × 512
        M_POS_MEAN = mean_i h_i   # K_M × 512
```

- `h_len_i` scalar.
- `A=adapter` F/L/PA; `A=identity` P.
- F/L `[:753]`; P/PA `[:512]`.
- eval/no_grad; no dropout.
- seed builder; seed-average before bootstrap.
- M primary reference = `A(h_t)[:K_M]`.
- donor-crop 금지.
- `M_GLOBAL` secondary.

### 9.3 M_NORM

```text
real_prefix_t := A(h_t)[:K_M]
M_NORM(t) = M_POS_MEAN * (||real_prefix_t||_F / ||M_POS_MEAN||_F)
```

- one global mean direction.
- per-target magnitude scalar.
- same adapter space.
- no raw EG2 embedding.
- no per-target matrix.
- M primary reference and real memory use `real_prefix_t`.

### 9.4 Variant × memory table

| variant | control tensor | real tensor | delta name |
|---|---|---|---|
| `M_POS_MEAN` | `M_POS_MEAN` | `real_prefix_t` | `delta_pos` |
| `M_NORM` | `M_NORM(t)` | `real_prefix_t` | `delta_norm` |

- `memory_kind ∈ {control, real}`.
- `M_POS_MEAN` and `M_NORM` are distinct controls.
- Both variants pass independently.
- `M_PASS_POS` uses `delta_pos`; `M_PASS_NORM` uses `delta_norm`.
- not the same test twice.
- `M_GLOBAL` descriptive only.

### 9.5 Endpoint identity

`endpoint_ok`:

- exact 15 common target IDs.
- 3 registered seeds.
- 4 arms F/L/P/PA.
- 2 variants M_POS_MEAN/M_NORM.
- 2 endpoints copy/full.
- 2 memory kinds control/real.
- **record count = 15 × 3 × 4 × 2 × 2 × 2 = 1,440**.
- each target appears **96 times**.
- exact key set, not only count.
- real/control CE finite.
- copy_ce != None.
- copy tokens >=5.
- no duplicate full key.
- no missing key.
- no 15→14 substitution.
- no target replacement.
- no donor-crop for primary M.

### 9.6 delta/pass

```text
delta_pos_copy = control_pos_copy_ce - real_copy_ce
delta_pos_full = control_pos_full_ce - real_full_ce
delta_norm_copy = control_norm_copy_ce - real_copy_ce
delta_norm_full = control_norm_full_ce - real_full_ce
```

- positive = real memory better.
- no `delta_memfree` term.

```text
M_PASS_POS = delta_pos_full > 0
             AND full CI lower > 0
             AND delta_pos_copy > 0
             AND copy CI lower > 0

M_PASS_NORM = delta_norm_full > 0
              AND full CI lower > 0
              AND delta_norm_copy > 0
              AND copy CI lower > 0

m_pass_l = ANDn(M_PASS_POS_L, M_PASS_NORM_L)
```

### 9.7 Aggregation

- seed builder; seed-average.
- 3 seeds ×15 docs ≠ 45 independent.
- false-dominant.
- final checkpoint hash.
- replay separate.
- `m_pass_l` 2 operands.
- `m_valid` 4 operands.
- `m_evaluable` 5 operands.

### 9.8 Zero-margin

- K=753; 754→14.
- cohort 15/15.
- target <15 or contributors <10 → `M_NOT_EVALUABLE`.
- report `ZERO_MARGIN_COHORT_FAIL` + missing ID.
- no 15→14.
- no K change.
- D0 h-length assert.

---

## 10. Statistics

### 10.1 Constants

```text
n_boot=1000
ci=percentile 2.5/97.5
bootstrap_seed=20261109
unit=document
seed_average_before_bootstrap=true
n_min_signal=15
```

### 10.2 Stats module

- `runner/c5_pm_stats.py` new.
- `bootstrap_paired(seed=20261109)`.
- `documents_positive(delta)` = count of docs with delta > 0.
- `seeds_positive` = count of registered seed means > 0.
- no P0 helper reuse (`seed=20261108`, mislabeled doc count).
- no legacy `bootstrap_paired`.

### 10.3 Bootstrap

- doc-level paired.
- seed average before bootstrap.
- 1,000 resamples.
- 2.5/97.5 percentile.
- same retained IDs copy/full/L−F.
- no pooling missing seed.
- no 3×15 independence.

### 10.4 Tail

`tail_driven` = **signal tail**:

```text
arm = L
endpoint = copy
control = shuffled donor
variant = NA (not an M variant)
cohort = 15 L-eligible docs
delta = shuffled_copy_ce - real_copy_ce
```

- `M_POS_MEAN`/`M_NORM` tails are descriptive:
  - `tail_driven_M_POS_MEAN`
  - `tail_driven_M_NORM`
- hard B0-B gate uses **signal tail only**.

```text
top3_abs_share = sum(top3 |delta|) / sum(all |delta|)
top3_signed_share = sum(top3 delta) / sum(all delta)
leave_top3_mean = mean(delta excluding top3 by |delta|)
```

- gate uses `top3_abs_share`.
- signed share descriptive.
- ties: sort by `|delta|` desc, then `doc_id` asc; top3 exactly 3.
- n<4 → `leave_top3_mean=NA`.
- denominator 0 → share=NA.

```text
if leave_top3_mean is not NA and leave_top3_mean <= 0: true
elif leave_top3_mean is NA or top3_abs_share is NA: NA
elif top3_abs_share > .50: true
else: false
```

- threshold `.50` unchanged.
- raw top3 IDs/sum/denominator/signed share artifact.
- P0 val:
  - signed share **.4862**
  - absolute share **.43355** (val20), **.455** (15 common)
  - P0 descriptive only; absolute is gate metric if it were used.
- B0-B requires `tail_driven=false`; true/NA not pass.

---

## 11. D0/D1/cap

### 11.1 Registered

| 항목 | 값 |
|---|---:|
| units | 12 |
| updates | 1,200 |
| wall | 120 min |
| threads | 6 |
| GPU | none |
| retry | none |

### 11.2 D0

- 0 optimizer updates.
- ≤4 configs.
- ≤15 min.
- seed 20261111.
- `labels_computed:false`.
- `not_a_result:true`.
- separate from registered cap.
- h-length assert.
- no timing claim.

### 11.3 D1

- **4 arms × 1 debug seed = 4 units**.
- debug seed 20261111.
- 1 update/arm.
- ≤20 min.
- separate approval.
- no labels.
- no registered seed.

Phases:

1. one train update per arm
2. step0 eval 20 docs ×5 donors
3. final eval 20 docs ×5 donors
4. M builder 20 train + 15 target ×2 variants
5. primary M CE: 15×2×2×2 = **120/arm-seed**
6. generation 20×256
7. donor diagnostic replay: 15×5×2×2×2 = **600/arm-seed**
8. load/checkpoint/process/report overhead

- phase 5 donor-free; `donor_id=null`.
- phase 7 donor-level; `donor_id=0..4`.
- phase 7 is **diagnostic**, not primary.
- all 8 measured; missing phase → no projection.
- step0 before update or restored state.

### 11.4 Replay domains

- primary M replay: phase 5, donor-free, 120/arm-seed.
- donor diagnostic: phase 7, donor-level, 600/arm-seed.
- not comparable as same population.
- `debug_replay_hash` = D1 synthetic only.
- `final_replay_hash` = registered postrun.
- **never compare debug hash directly to final hash**.
- numeric replay: `atol=1e-5`, `rtol=1e-4`.
- artifact integrity: exact SHA256, separate field.

### 11.5 T_proj

```text
T_proj = 3 * sum_{arm in F,L,P,PA} (
            100 * t_train_arm
          + t_step0_eval_20x5_arm
          + t_step100_eval_20x5_arm
          + t_M_build_20x15x2_arm
          + t_initial_M_ce_15x2x2x2_arm
          + t_generate_20x256_arm
          + t_replay_15x5x2x2x2_arm
          + t_overhead_arm
        )
```

- phase 5 120; phase 7 600.
- `T_proj` finite/nonnegative/≤96 min.
- D1 없이 3-seed 금지.
- D0 projection 금지.
- no timing probe substitute.
- 120-min hard abort.

### 11.6 Cap

- D0/D1 separate.
- prospective max 1,204 updates / 155 min (not grant).
- no retry/extension.

---

## 12. Canonical hash / golden vectors

### 12.1 Checkpoint state hash

```text
sorted state_dict keys
include adapter parameters + LoRA A/B
exclude frozen base
frame:
  name_len:u32 LE | name_utf8
  dtype_len:u8 | dtype_str
  ndim:u8 | shape:u32×ndim LE
  nbytes:u64 LE | little_endian_contiguous_bytes
SHA256 over concatenated frames
```

- no padding.
- empty state → SHA256 empty bytes.
- frozen base/config/mode in manifest.
- `final_checkpoint_hash` postrun.

### 12.2 Replay record

```text
key = (doc_id, arm, seed, variant, endpoint, memory_kind, donor_sort)
```

- `doc_id` only; not `id`.
- `arm ∈ {F,L,P,PA}`.
- `seed ∈ {20261108,20261109,20261110}`; debug 20261111.
- `variant ∈ {M_POS_MEAN,M_NORM}`.
- `endpoint ∈ {copy,full}`.
- `memory_kind ∈ {control,real}`.
- `donor_sort = -1` for null; `0..4` for donor.
- `ce` float64 finite; nonfinite reject.
- sort ascending; canonical JSON `sort_keys=true,separators=(',',':')`.
- SHA256 of UTF-8 bytes.
- `debug_replay_hash` D1 only.
- `final_replay_hash` postrun only.
- numeric replay tolerance; hash exact.

### 12.3 Golden vectors

State vector:

```text
a: dtype <f4, shape [2], bytes 0000803f 000000c0
b: dtype <f4, shape [1,1], bytes 0000003f
```

Expected SHA256:

```text
state_full = 43ecb58e197d5789df0a9dbbc67beba11538b8063c3da8ac46f96e1e95d65712
state_empty = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

Replay vector records:

```json
[
  {"arm":"L","ce":1.0,"doc_id":"doc_a","donor_id":null,"endpoint":"copy","memory_kind":"control","seed":20261108,"variant":"M_POS_MEAN"},
  {"arm":"L","ce":2.0,"doc_id":"doc_a","donor_id":null,"endpoint":"copy","memory_kind":"real","seed":20261108,"variant":"M_POS_MEAN"},
  {"arm":"L","ce":3.5,"doc_id":"doc_b","donor_id":0,"endpoint":"full","memory_kind":"real","seed":20261108,"variant":"M_POS_MEAN"}
]
```

Expected SHA256:

```text
replay_three = c43ea35c46c51a0e82cebe5764a989d1b67012b2690246a0f89a94dff7851667
```

- Expected digests are independent constants; implementation must not compute and overwrite them.
- `docs/hoplite/c5_b0a_pm_prereg_v1_0_2026-11-09/golden_vectors.json` stores these.
- permutation/duplicate/missing-key tests.

---

## 13. Test matrix / DoD

### 13.1 Decision tests

- ANDn 2/4/5.
- F1–F11.
- §3.4 9 L pairs.
- fixtures 16–18.
- all labels reachable.
- validity INVALID vs NOT_ASSESSABLE.
- small-N triple.
- `m_valid`/`M_CONTROL_INVALID`.
- availability NA → `M_NOT_EVALUABLE`.
- `m_pass_l` derivation.
- no `M_CONTROL_NOT_VALID`.

### 13.2 M tests

- F/L/P/PA builder.
- P identity.
- `h_len_i`.
- `M_POS_MEAN` shape.
- `M_NORM` same adapter.
- endpoint 1,440 exact key set.
- duplicate/missing target.
- target appears 96 times.
- zero/nonfinite norm.
- seed aggregation.
- M_PASS_POS/NORM independent.
- no delta_memfree.
- zero-margin abort.

### 13.3 Stats tests

- n_boot 1000.
- seed 20261109.
- documents_positive.
- seeds_positive.
- 2/3 registered.
- missing seed NA.
- tail signal; variant NA.
- top3 absolute/signed.
- tie rule.
- partial endpoint.

### 13.4 Hash/replay tests

- state golden 43ecb…
- empty golden e3b0…
- replay golden c43ea…
- canonical JSON.
- donor_sort -1/0..4.
- numeric tolerance vs exact hash.
- debug vs final separation.

### 13.5 Implementation DoD

- pure decision function.
- no model/data in decision.
- `test_split_used:false`.
- validity enum assertion.
- manifest/checkpoint/replay hash.
- D0/D1 gates.
- no B0-B auto.
- no test 163/P1.
- no stale `seeds_positive`.
- no `ADAPTER_REGIME_LOSS`.
- no `PA only`.
- no 0..20.
- no 753 training requirement.

---

## 14. B0-B boundary

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS
AND signal_status == EXPLORATORY_L_SIGNAL
AND m_valid == true
AND n_signal >= 15
AND tail_driven == false
AND leakage/mode/metric pass
AND artifact complete
AND separate prereg/approval
```

- n_signal max 15; `>=15` means exactly 15.
- tail true/NA blocks.
- `EXPLORATORY_L_SIGNAL` alone not approval.
- full_k_secondary/P0/PA_RETENTION not evidence.
- M scope `M_CONTROL_PREFIX753_COHORT15`.
- no B1/B2/Stage C auto.

---

## 15. Traceability appendix

Historical only; not implementation authority.

| v1.0 area | source chain |
|---|---|
| arms | r3.4 §7.4 |
| L table | r3.4 §2.4; r3.3 §2.3 |
| F/P builder | r3.4 §8.2 |
| real_prefix_t | r3.4 §8.3 |
| n_signal 15 | r3.4 §5.1 |
| M endpoints 1,440 | r3.4 §8.4 |
| tail | r3.4 §9.4 + v1.0 signal-tail disambiguation |
| P/PA cohort 20 | v1.0 MF-3 |
| replay domains | v1.0 MF-4 |
| L binding | v1.0 MF-5 |
| F/L memory scope | v1.0 MF-6 |
| PA_VALID | v1.0 §4.5 |
| golden vectors | v1.0 §12.3 |
| full_k_secondary | historical only; not normative |

Superseded:

- r3.4 and all earlier P/M docs.
- any statement `n_signal 0..20`.
- any statement `PA only`.
- any statement `M pass L false + control PASS`.
- any `delta_memfree`.
- any 753 training/generation requirement.
- any replay debug/final direct comparison.

---

## 16. Freeze / review

### 16.1 Review

- v1.0 review required.
- If NARROW: must-fix only; no new scientific choices.
- No code before freeze.

### 16.2 Freeze

- freeze commit hash.
- freeze content SHA-256.
- implementation references only freeze hash.
- post-freeze corrections only numbered ERRATA.

### 16.3 Approval

> **v1.0을 Phase 6 protocol contract로 동결하고, 구현 + unit tests + D0 zero-update mechanics debug를 진행해도 되는가?**

Approval does not include:
- D1
- 3-seed
- B0-B/B1/B2/Stage C
- test 163/P1
- T5Gemma2 (D-108 STOP)
