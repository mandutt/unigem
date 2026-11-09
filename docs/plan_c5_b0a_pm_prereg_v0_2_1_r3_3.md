# C5 Phase 6 P/M Prereg v0.2.1-r3.3 — Contract Unification

- 작성일: 2026-11-09
- 상태: **r3.3 동결 후보. 실행 미승인.**
- 적용 대상: `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_2.md` (r3.2)
- 충돌 시: **r3.3 > r3.2 > r3.1 > r3 > r2 > r1 > v0.2.1 > v0.2**
- 근거:
  - `reports/C5_B0A_PM_PREREG_V0_2_1_R3_2_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
  - r3.2 review: GLM CONTINUE conditional / DeepSeek 1017 NARROW / Sol NARROW
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. r3.3의 목적

r3.3은 r3.2의 **freeze blocker**만 닫는 text-only errata다.

- threshold/seed/donor/step/LR 변경 없음
- full threshold는 **`>0`**
- copy threshold는 **`.05`**
- 결과 전에 commit/freeze
- 코드는 r3.3 승인 후에만 작성

---

## 1. R3.2 freeze blocker closure

| Blocker | r3.3 조치 |
|---|---|
| L consensus §2.3 vs §9.2 | §2.3 **단일 authoritative**; §9.2 ANDn alias 삭제 |
| §6.3 unreachable cell | §6.3에서 삭제, fixture 16–18 참조 |
| `tail_driven` criterion 소실 | §9.4 exact `leave_top3_mean<=0 or top3_share>.50` |
| M builder/primary reference | §8.1–8.2 recipe + target prefix K_M |
| arm 표 부재 | §7.4 F/L/P/PA table |
| replay/hash wire format | §10.6 canonical frame + replay key + golden vector |
| D1 initial M CE scoring | §10.3 phase 5 + T_proj |
| `NOT3` 소실 | §2.2 정의 |
| `delta_memfree` 소실 | §8.5 정의 |
| DoD truth-table/PA labels | §13 복원 |
| missing seed 2/3 | §9.2 registered seeds rule |
| legacy stats | §9.3 new module only |
| PA caveat | §7.2 복원 |
| `endpoint_ok` 중복 | §8.4 단일 정의 |
| blob 표현 | §1.1 |

### 1.1 Preflight artifact

- `reports/provenance/C5_b0a/m_cohort_preflight.json`
- **content SHA-256**: `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`
- file content의 SHA-256이며 git blob OID가 아니다.
- frozen preflight hash로 사용한다.

---

## 2. Primitive semantics

### 2.1 Tri-state

```text
true | false | not_assessable
```

### 2.2 ANDn/ORn/NOT3

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

- `m_pass_l`(2), `m_valid`(4), `m_evaluable`(5).
- 2/4/5 operand tests.
- 3-arity 절단 금지.

### 2.3 L consensus (single authoritative)

```text
l_signal = true   if l_copy_signal=true and l_full_signal=true
           false  if l_copy_signal=false and l_full_signal=false
           not_assessable otherwise

copy_only = ANDn(l_copy_signal, NOT3(l_full_signal))
full_only = ANDn(l_full_signal, NOT3(l_copy_signal))
```

- 이 정의가 **유일한** `l_signal`이다.
- §9.2의 ANDn alias는 사용하지 않는다.
- `false+NA`는 `l_signal=NA`; `copy_only/full_only`도 true가 아니다.
- `ANDn`은 `l_signal` consensus에 사용하지 않는다; `m_pass_l`에만 사용한다.

### 2.4 L tri-state table

| l_copy | l_full | l_signal | copy_only | full_only |
|---|---|---|---|---|
| true | true | true | false | false |
| true | false | false | true | false |
| true | NA | NA | NA | false |
| false | true | false | false | true |
| false | false | false | false | false |
| false | NA | NA | false | NA |
| NA | true | NA | false | NA |
| NA | false | NA | NA | false |
| NA | NA | NA | NA | NA |

- 이 표가 §5.3 dispatch의 입력이다.
- `false+NA`는 `NOT_ASSESSABLE`; `MEAN_CONTRAST_ONLY`가 아니다.

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
- `p_step100_path_ok=NA` + `p_valid=false` → `NOT_ASSESSABLE`.
- `pa_step100_path_ok=NA` + `p_valid=false` → `P_STEP100_NOT_VALID`.
- `pa_step100_path_ok=NA` + `pa_valid=false` → `NOT_ASSESSABLE`.
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
endpoint_ok = §8.4 single definition
seed_ok    = 3 registered seeds available
replay_ok  = replay equality
builder_ok = contributors >=10
             AND all M tensors finite
             AND ||M_POS_MEAN||_F > 0
             AND all 15 ||real_prefix_t||_F > 0
```

```text
m_evaluable = ANDn(cohort_ok, endpoint_ok, seed_ok, replay_ok, builder_ok)
```

- `endpoint_ok`는 §8.4에서만 정의한다; 중복 정의 금지.
- `seed_ok`는 **registered 20261108/09/10** 기준이다; 가용 seed 대체 금지.

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
- endpoint membership: F/L arms × 3 registered seeds × copy/full; same retained IDs.
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

- `l_signal=NA`이면 `MEAN_CONTRAST_ONLY`로 가지 않는다.
- `copy_only`/`full_only`가 true이면 `l_signal`보다 먼저 평가한다.
- raw flags always preserved.

### 5.4 L preservation

- raw flags always in `flags`.
- `NOT_ASSESSABLE` carries `signal_reason` + raw flags.
- `*_VALIDITY_NOT_ASSESSABLE`와 `*_VALIDITY_INVALID`를 구분한다.
- report는 `(validity, control, signal, flags, reason)`을 함께 기록.

### 5.5 Small-N precedence

- `n_signal<15`이면 small-N 계열이 **signal_status의 1차 label**이다.
- validity/control은 별도 축으로 항상 기록한다.
- small-N이 validity failure를 숨기지 않는다: `(validity_status, control_status, signal_status)` triple과 reason을 함께 report.
- F11: n<15 + validity INVALID → small-N label + `validity=ASSAY_INVALID`/P/PA 상태 기록.
- 이 precedence는 의도된 계약이며 테스트로 고정한다.

---

## 6. Truth-table

### 6.1 Per-axis

- validity path axis 3^5
- p/pa validity 3^2
- control availability 3^4 + builder 3^1
- calibration 3^4
- L 3^2 (9 pairs; §2.4)
- n_signal `{NA,0..20}`

### 6.2 Primitive fixtures 16–18

**중요**: fixture는 primitive에서 derive한다; `control_status`/`m_pass_l`/`m_valid`를 직접 주입하지 않는다.

#### Fixture 16 — EXPLORATORY

```text
validity_status = VALID
n_signal = 20
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
n_signal = 20
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
n_signal = 20
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

### 6.3 Named cells

- F1–F11.
- §2.4의 9개 L pair.
- §4.3의 control status 5종.
- m_valid=false + P/PA valid → `M_CONTROL_INVALID`.
- m_evaluable=false + L true → `L_SIGNAL_M_CONTROL_NOT_EVALUABLE`.
- validity invalid + L → `L_SIGNAL_VALIDITY_INVALID`.
- validity NA + L → `L_SIGNAL_VALIDITY_NOT_ASSESSABLE`.
- copy-only + invalid/NA.
- full-only + invalid/NA.
- n=14 + L.
- n=16 + L + control PASS.
- endpoint_ok=false / builder_ok=false / M norm zero → `M_NOT_EVALUABLE`.
- M pass L true + control PASS → `EXPLORATORY_L_SIGNAL`.
- M pass L false → `M_CONTROL_FAIL`; `MEAN_CONTRAST_ONLY`는 `m_pass_l=true` + L both false인 경우에만.

**금지**: control PASS와 `m_pass_l=false`를 함께 요구하는 cell은 존재하지 않는다.

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
- **scale/geometry caveat**: PA memory는 native mT5 512, L memory는 EG2 layer19 prefix 753; hidden geometry/scale이 다르므로 PA는 **acquisition control**이며 L의 retention 직접 비교가 아니다. `PA_RETENTION`은 descriptive/nullable이다.

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

### 7.4 Arm table

| arm | memory | memory K | trainable | role |
|---|---|---:|---|---|
| F | EG2 layer19 | 753 | adapter | reference |
| L | EG2 layer19 | 753 | adapter + decoder LoRA | B0-A 재검증 |
| P | native mT5 encoder | 512 | decoder LoRA only | positive control |
| PA | native mT5 encoder | 512 | adapter + decoder LoRA | P/F regime 정합 |

- 12 trained units = 4 arms × 3 seeds.
- 100 updates/unit.
- 1,200 registered updates.
- adapter only for F/P? F adapter; P decoder LoRA only; PA adapter+LoRA.
- PA adapter is random-init; F/L adapter is trained? F adapter trained; yes.
- `F` adapter trained; `L` adapter+LoRA trained.

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

### 8.2 Builder recipe

For each seed:

```text
model.eval()
with torch.no_grad():
    for each contributor i in train20 with h_i >= K_M:
        h_i = A(h_i)[:K_M]          # K_M × 512
        M_POS_MEAN = mean_i h_i      # K_M × 512
```

- adapter `A` evaluation only; no dropout.
- contributors >=10.
- L uses `[:753]`; P/PA use `[:512]`.
- seed별 `M_POS_MEAN`; seed-average before doc bootstrap.
- **M primary reference = target prefix at K_M**, not donor-crop.
- donor-crop 금지.
- `M_GLOBAL` is secondary/descriptive only.

### 8.3 M_NORM fixed formula

```text
M_NORM(t) = M_POS_MEAN * ( ||real_prefix_t||_F / ||M_POS_MEAN||_F )
```

- `M_POS_MEAN` = one global train-only mean matrix (K_M×512).
- `real_prefix_t` = target `t`의 real prefix at K_M.
- `M_NORM(t)` = per-target scalar × one global mean direction.
- target-dependent은 magnitude scalar만; target label/mean direction leakage 없음.
- `builder_ok`는 all 15 `||real_prefix_t||>0`.
- per-target matrix를 만들지 않는다.

### 8.4 Endpoint identity (single definition)

`endpoint_ok` = all of:

- exact 15 target IDs from preflight `common_ids`
- 3 registered seeds
- 4 arms (F/L/P/PA)
- primary variants (M_POS_MEAN, M_NORM)
- real/control CE finite
- `copy_ce != None`
- copy tokens >=5
- no duplicate/missing target
- no 15→14 substitution
- no target replacement
- no donor-crop for primary M

하나라도 실패 → `M_NOT_EVALUABLE`.

### 8.5 Pass / delta definitions

```text
delta_memfree_copy = mean_copy_ce(control) - real_copy_ce
delta_memfree_full = mean_full_ce(control) - real_full_ce
```

- 양수 = real memory 우수.

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
                AND 2/3 registered seed copy means > 0

L_FULL_SIGNAL = mean delta_full > 0
                AND full CI lower > 0
                AND paired L>F full mean > 0
                AND 2/3 registered seed full means > 0
```

- full threshold는 **`>0`**; `.05` 아님.
- copy threshold는 **`.05`**.
- `2/3 registered seeds` = 20261108/09/10.
- 등록 seed 결측 시 해당 predicate = `not_assessable`; 2-of-available 대체 금지.
- `seed_mean` = arm-L shuffled-minus-real endpoint mean; L−F와 별개.
- L−F는 paired per-document.

### 9.3 Stats module

- `runner/c5_pm_stats.py` (new)
- `bootstrap_paired(seed=20261109)`
- `documents_positive`
- `seeds_positive` = seed mean only
- P0 helper 재사용 금지 (`seed=20261108`, 문서 수 mislabel)
- legacy `bootstrap_paired`/`seeds_positive` 사용 금지.

### 9.4 Partial endpoint / tail

- canonical endpoint keys: F/L × 3 registered seeds × copy/full.
- same retained IDs for copy/full/L−F.
- missing seed → no pooling; excluded ID/reason.
- nonfinite CE → excluded with reason.
- `n_signal` counts only valid endpoints.
- `top3_share = sum(top3)/sum(all)`:
  - denominator 0 → null.
  - signed sum may fall outside [0,1]; descriptive only.
- `leave_top3_mean`:
  - n<4 → null.
- `tail_driven` exact:

```text
tail_driven = true   if leave_top3_mean <= 0 OR top3_share > .50
              false  if leave_top3_mean > 0 AND top3_share <= .50
              NA     if either input is null or nonfinite
```

- B0-B requires **false**; NA not pass.
- `MARGINAL_SIGNAL_COHORT` non-gating.
- top3/share/leave_top3 raw values를 artifact에 보존.

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
5. **initial fixed-prefix real/M CE scoring 15 targets × 2 variants × copy/full**
6. **generation 20 docs × max_new_tokens=256**
7. **replay 15 targets × 5 donors × 2 variants × copy/full**
8. **load/checkpoint/process/report overhead**

- 각 arm-run은 8 phase 전부 측정.
- missing phase → no projection.
- step0는 update 전 또는 동일 unupdated state restore에서 측정.
- phase 5는 donor-free primary M scoring; donor factor 없음.
- phase 2/3/7만 donor factor 5.

### 10.4 T_proj

```text
T_proj = 3 * sum_{arm in F,L,P,PA} (
            100 * t_train_arm
          + t_step0_eval_20x5_arm
          + t_step100_eval_20x5_arm
          + t_M_build_20x15x2_arm
          + t_initial_M_ce_15x2x2_arm
          + t_generate_20x256_arm
          + t_replay_15x5x2x2_arm
          + t_overhead_arm
        )
```

- `3` = seeds; `100` = updates.
- generation 포함.
- M build 20 train 포함.
- initial M CE scoring 포함.
- donor multiplicity 5 포함.
- variants 2 포함.
- copy/full 2 포함.
- `T_proj` finite, nonnegative, ≤**96 min**.
- D1 없이 3-seed 금지.
- D0-only projection 금지.
- “timing probe” 대체 금지.

### 10.5 Cap accounting

- D0/D1 separate.
- prospective combined max = 1,204 updates / 155 min (not a grant).
- cap abort/no retry/no extension.

### 10.6 Canonical hash

**Checkpoint state hash**:

```text
sorted state_dict keys
include adapter parameters + LoRA A/B
exclude frozen base
frame per tensor:
  name_len:u32 | name_utf8
  dtype_len:u8 | dtype_str
  ndim:u8 | shape:u32×ndim
  nbytes:u64 | little_endian_contiguous_bytes
SHA256 over concatenated frames
```

- frozen base/config/mode identity는 manifest에 별도 기록.
- `final_checkpoint_hash` = post-run adapter/LoRA state.

**Replay record**:

```text
key = (doc_id, arm, seed, variant, endpoint, memory_kind, donor_id)
```

- `memory_kind ∈ {real, control}`.
- `donor_id ∈ {0..4}` for donor-level; `null` for donor-free primary M.
- `endpoint ∈ {copy, full}`.
- `variant ∈ {M_POS_MEAN, M_NORM}`.
- `doc_id` only (not `id`).
- CE float64 finite only; nonfinite reject.
- sort keys ascending; canonical JSON `sort_keys=true, separators=(',',':')`.
- SHA256 over UTF-8 JSON bytes.
- `debug_replay_hash` = D1 synthetic/debug.
- `final_replay_hash` = post-run.
- prelaunch debug hash와 final hash를 구분한다.

**Golden vector**:

- fixed synthetic state: two tensors + adapter scalar + LoRA A/B.
- expected SHA256 상수를 test에 동결.
- replay: three fixed records, expected SHA256 상수.
- permutation/duplicate/missing-key tests.

---

## 11. 3-seed checklist

1. r3.3 freeze commit hash
2. code commit hash
3. unit tests all green
4. D0 pass artifact
5. D1 timing artifact
6. preflight hash `3ee3f1ca…` + 15/20
7. debug seed 20261111 ∉ registered 20261108/09/10
8. no threshold/seed/donor/step/LR diff
9. M_VALID computation contract
10. `M_CONTROL_PREFIX753_COHORT15` scope
11. signal val20 vs M 15 separation
12. T_proj ≤96 min (8 phases)
13. manifest complete
14. prelaunch debug replay hash
15. explicit user approval
16. test 163/P1 미사용
17. no B0-B/B1/B2/Stage C auto
18. post-run final checkpoint/replay hash validation plan
19. canonical hash golden-vector test green
20. stats module seed/documents_positive/2-of-3 tests green
21. missing registered seed → predicate NA test green
22. replay record variant/memory_kind/donor_id coverage test green
23. `test_split_used:false` in every artifact

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
- §2.4 9 L pairs
- validity INVALID vs NOT_ASSESSABLE labels
- m_valid/M_CONTROL_INVALID
- m_pass_l derivation
- builder_ok zero/nonfinite/contributor/15 norms
- endpoint identity 15×3×4×2
- M builder recipe `[:753]`/`[:512]`
- M primary reference target prefix; donor-crop 금지
- M_NORM fixed formula
- M seed aggregation
- canonical hash golden vector
- replay prelaunch/final
- signal val20/M15 separation
- n_signal 0..20
- stats module seed 20261109/documents_positive/2-of-3
- L_COPY/L_FULL predicate tests + boundaries
- fixture 16/17/18
- tail tri-state/partial endpoint
- PA acquisition labels
- P/PA mode/init
- no `ADAPTER_REGIME_LOSS`/`M_CONTROL_NOT_VALID`
- no stale `seeds_positive`
- manifest/checkpoint/replay hash
- truth-table per-axis + named cells
- `test_split_used:false`
- validity enum assertion

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

## 15. R3.2 closure

| Blocker | 조치 | 상태 |
|---|---|---|
| L consensus 이중 정의 | §2.3 single; §9.2 ANDn 삭제 | closed |
| §6.3 unreachable | §6.3 삭제/교체 | closed |
| tail_driven criterion | §9.4 exact | closed |
| M builder/reference | §8.2 | closed |
| arm 표 | §7.4 | closed |
| replay/hash wire | §10.6 | closed |
| D1 initial M CE | §10.3 phase 5/T_proj | closed |
| NOT3 | §2.2 | closed |
| delta_memfree | §8.5 | closed |
| DoD truth-table/PA | §13 | closed |
| missing-seed 2/3 | §9.2 | closed |
| legacy stats | §9.3 | closed |
| PA caveat | §7.2 | closed |
| endpoint_ok 중복 | §8.4 single | closed |
| blob 표현 | §1.1 | closed |

---

## 16. 동결 조건

- r3.3 review에서 NARROW가 다시 나오면 MUST-FIX만 수정한 r3.4를 작성한다.
- r3.3 승인 시 commit hash freeze.
- freeze 후 threshold/seed/donor/step/LR 변경 금지.
- 코드는 freeze 후에만 작성.
- 3-seed는 별도 gate.

---

## 17. 승인 요청

> **r3.3을 Phase 6 protocol contract로 동결하고, 구현 + unit tests + D0 zero-update mechanics debug를 진행해도 되는가?**

승인 후에도:
- D1은 별도 승인
- 3-seed는 별도 gate
- B0-B/B1/B2/Stage C는 별도
- test 163/P1 미사용
- T5Gemma2는 D-108 STOP
