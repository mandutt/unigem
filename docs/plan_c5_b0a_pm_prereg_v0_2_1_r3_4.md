# C5 Phase 6 P/M Prereg v0.2.1-r3.4 — Executable Contract Closure

- 작성일: 2026-11-09
- 상태: **r3.4 동결 후보. 실행 미승인.**
- 적용 대상: `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_3.md` (r3.3)
- 충돌 시: **r3.4 > r3.3 > r3.2 > r3.1 > r3 > r2 > r1 > v0.2.1 > v0.2**
- 근거:
  - `reports/C5_B0A_PM_PREREG_V0_2_1_R3_3_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
  - r3.3 review: GLM CONTINUE conditional / DeepSeek 1017 NARROW / Terra 6.1 NARROW
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. r3.4의 목적

r3.4는 r3.3의 **freeze blocker만** 닫는 text-only errata다.

- threshold/seed/donor/step/LR 변경 없음
- full threshold는 **`>0`**
- copy threshold는 **`.05`**
- 결과 전에 commit/freeze
- 코드는 r3.4 승인 후에만 작성

---

## 1. R3.3 freeze blocker closure

| Blocker | r3.4 조치 |
|---|---|
| §2.4 mixed true/false `false` | §2.4를 **NA**로 수정 |
| F M builder 누락 | §8.2 arm matrix + F recipe |
| P `A=identity` | §8.2 explicit |
| `h_i >= K_M` type | §8.2 `h_len_i >= K_M` |
| `real_prefix_t` space | §8.3 `A(h_t)[:K_M]` |
| `n_signal` 15/20 | §5.1 `{NA,0..15}` |
| `tail_driven` input | §9.4 exact L copy endpoint |
| `top3_share` gate | §9.4 `|delta|`; signed descriptive |
| tail NA precedence | §9.4 ordered |
| `adapter_lr (PA only)` | §7.3 all adapter-bearing |
| T_proj real/control factor | §10.4 120/600 |
| endpoint count | §8.4 1,440 |
| PA veto rationale | §4.2 |
| golden vector self-generated | §10.6 independent vector |
| named-cell prerequisites | §6.3 fixtures 16–18 only |
| ANDn/NOT3 domain | §2.2 scalar predicates |
| zero-margin path | §8.7 |
| P0 OOD caveat | §12 |

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

### 2.2 ANDn/ORn/NOT3 (scalar predicates only)

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

- `ANDn`/`ORn`/`NOT3`는 **scalar tri-state predicate**만 받는다.
- seed axis/endpoint axis를 operator 안에 섞지 않는다.
- `m_pass_l`(2), `m_valid`(4), `m_evaluable`(5).
- `copy_only = ANDn(l_copy_signal, NOT3(l_full_signal))`; `full_only = ANDn(l_full_signal, NOT3(l_copy_signal))`.
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
- `ANDn`은 `l_signal` consensus에 사용하지 않는다; `m_pass_l`에만 사용한다.

### 2.4 L tri-state table (authoritative)

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

- `true/false`와 `false/true`는 **NA**; `copy_only`/`full_only`가 각각 true.
- 이 표가 §5.3 dispatch의 입력이다.
- `false+NA`는 `NOT_ASSESSABLE`; `MEAN_CONTRAST_ONLY`가 아니다.
- `copy_only`/`full_only`가 true이면 `l_signal`보다 먼저 평가한다.

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

### 4.2 m_valid / m_pass_l / PA veto

```text
m_pass_l = ANDn(m_pass_pos_l, m_pass_norm_l)

m_valid = ANDn(
  m_pass_pos_p, m_pass_norm_p,
  m_pass_pos_pa, m_pass_norm_pa
)
```

- false-dominant; mixed false+NA → false.
- missingness-first 구현 금지.
- **PA veto rationale**: PA는 native mT5 512 + random-init adapter + decoder LoRA인 acquisition control이다. PA가 실패하면 native memory regime 자체의 calibration이 무효이므로 L M-control을 해석할 수 없다. 따라서 `m_valid=ANDn(P,PA)`는 의도된 arm-level calibration veto이며, `PA_RETENTION`은 여전히 gate가 아니다.
- PA veto는 L threshold를 변경하지 않는다.

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
signal eligible cohort = 15 L-eligible val docs at K_M=753
val20 = descriptive only
n_signal = number of 15 eligible docs with valid F/L copy and full endpoints
n_signal ∈ {NA, 0..15}
n_min = 15
```

- `n_signal=15` → `MARGINAL_SIGNAL_COHORT=true`.
- signal cohort와 M cohort는 **same 15 IDs**.
- val20의 나머지 5개는 L prefix 부족으로 signal endpoint에서 제외; descriptive table에는 남길 수 있다.
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
- n_signal `{NA,0..15}`

### 6.2 Primitive fixtures 16–18

**중요**: fixture는 primitive에서 derive한다; `control_status`/`m_pass_l`/`m_valid`를 직접 주입하지 않는다.

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

### 6.3 Named cells

- F1–F11.
- §2.4의 9개 L pair.
- §4.3의 control status 5종.
- named cell은 fixture 16–18로만 정의한다.
- generic “M pass L true + control PASS” cell은 **L flags/validity/n_signal prerequisites**를 모두 적을 때만 유효하다; 그렇지 않으면 fixture 16을 참조한다.
- “m_pass_l=false → M_CONTROL_FAIL”은 **m_evaluable=true, P/PA valid/calibrated, m_valid=true** 전제에서만 성립한다; 그 전제가 없으면 `M_NOT_EVALUABLE`/`M_CONTROL_INVALID`가 우선한다.

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
- PA veto rationale는 §4.2.

### 7.3 Hyperparameters

```text
optimizer: AdamW
weight_decay: .01
adapter_lr: 1e-3 for F, L, PA (all adapter-bearing arms)
lora_lr: 1e-4 for L, P, PA (all LoRA-bearing arms)
updates: 100
batch: 1
order: train_ids[step % 20]
clip: 1.0
base decoder: eval
LoRA: 64 modules, r8 alpha16 dropout .05
```

- P has no adapter; adapter_lr not applied.
- `(PA only)` 금지; F/L adapter도 학습한다.

### 7.4 Arm table

| arm | memory | memory K | adapter | trainable | role |
|---|---|---:|---|---|---|
| F | EG2 layer19 | 753 | trained | adapter | reference |
| L | EG2 layer19 | 753 | trained | adapter + decoder LoRA | B0-A 재검증 |
| P | native mT5 encoder | 512 | none (`A=identity`) | decoder LoRA only | positive control |
| PA | native mT5 encoder | 512 | random-init trained | adapter + decoder LoRA | P/F regime 정합 |

- 12 trained units = 4 arms × 3 seeds.
- 100 updates/unit.
- 1,200 registered updates.
- F/L both 753, same adapter geometry.

---

## 8. M

### 8.1 Lengths/cohorts

| arm | K_M | source |
|---|---:|---|
| F | **753** | EG2 layer19 prefix |
| L | **753** | EG2 layer19 prefix |
| P/PA | **512** | native mT5 source prefix |

- M cohort 15/20.
- signal eligible cohort 15/20.
- full-K L 11/20 secondary.
- `M_CONTROL_PREFIX753_COHORT15`.

### 8.2 Builder recipe (all arms)

For each seed and arm:

```text
model.eval()
with torch.no_grad():
    contributors = [i for i in train20 if h_len_i >= K_M]
    if len(contributors) < 10:
        builder_ok = false
    else:
        h_i = A(h_i)[:K_M]          # K_M × 512
        M_POS_MEAN = mean_i h_i      # K_M × 512
```

- `h_len_i` is **scalar source length**, not a tensor comparison.
- `A = adapter` for F/L/PA; `A = identity` for P.
- F and L use `[:753]`; P/PA use `[:512]`.
- adapter `eval()` + `no_grad()`; no dropout.
- seed별 `M_POS_MEAN`; seed-average before doc bootstrap.
- **M primary reference = A(h_t)[:K_M] at target `t`**, not donor-crop.
- donor-crop 금지.
- `M_GLOBAL` is secondary/descriptive only.
- F M exists; §8.4 requires it.

### 8.3 M_NORM fixed formula

```text
real_prefix_t := A(h_t)[:K_M]       # same adapter space as M_POS_MEAN
M_NORM(t) = M_POS_MEAN * ( ||real_prefix_t||_F / ||M_POS_MEAN||_F )
```

- `M_POS_MEAN` = one global train-only mean matrix (K_M×512).
- `real_prefix_t` = **same-arm adapter output**, not raw EG2 embedding.
- `M_NORM(t)` = per-target scalar × one global mean direction.
- target-dependent은 magnitude scalar만; target label/mean direction leakage 없음.
- `builder_ok`는 all 15 `||real_prefix_t||>0`.
- per-target matrix를 만들지 않는다.
- M primary reference와 M CE real memory도 `real_prefix_t`를 사용한다.

### 8.4 Endpoint identity (single definition)

`endpoint_ok` = all of:

- exact 15 target IDs from preflight `common_ids`
- 3 registered seeds
- 4 arms (F/L/P/PA)
- 2 primary variants (M_POS_MEAN, M_NORM)
- 2 endpoints (copy, full)
- 2 memory kinds (real, control)
- **record count = 15 × 3 × 4 × 2 × 2 × 2 = 1,440**
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

### 8.7 Zero-margin failure path

- `K_M=753`은 zero-margin: 754이면 14 eligible.
- cohort 15/15도 zero-margin.
- h-length 재계산이 하나라도 753 미만이면 target이 탈락한다.
- target <15 또는 contributors <10이면 **`M_NOT_EVALUABLE`**, run abort.
- 15→14 substitution 금지; threshold/K 변경 금지.
- report `ZERO_MARGIN_COHORT_FAIL` + missing ID.
- D0에서 h-length 재계산 일치 assert.

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

- canonical signal endpoint keys: F/L × 3 registered seeds × copy/full.
- same retained IDs for copy/full/L−F.
- missing seed → no pooling; excluded ID/reason.
- nonfinite CE → excluded with reason.
- `n_signal` counts only valid endpoints; max 15.
- `tail_driven` input is fixed:

```text
arm = L
endpoint = copy
cohort = 15 signal-eligible docs
delta = control_copy_ce - real_copy_ce
```

- `top3_share` gate uses **absolute** delta:

```text
top3_abs_share = sum(top3 |delta|) / sum(all |delta|)
top3_signed_share = sum(top3 delta) / sum(all delta)
```

- `top3_signed_share` is descriptive only.
- `top3_abs_share` is the gate input.
- `leave_top3_mean` = mean delta excluding top3 by |delta|.
- `top3_share` = `top3_abs_share` by definition; signed variant always named separately.
- denominator 0 → null.
- `leave_top3_mean` n<4 → null.

`tail_driven` ordered:

```text
if leave_top3_mean is not null and leave_top3_mean <= 0:
    true
elif leave_top3_mean is null or top3_abs_share is null:
    NA
elif top3_abs_share > .50:
    true
else:
    false
```

- B0-B requires **false**; NA/true not pass.
- `MARGINAL_SIGNAL_COHORT` non-gating.
- raw top3 sum/denominator/top3 IDs/signed share artifact 보존.

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
- h-length 재계산 assert

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
5. **initial fixed-prefix real/M CE scoring 15 targets × 2 variants × 2 endpoints × 2 memory kinds = 120**
6. **generation 20 docs × max_new_tokens=256**
7. **replay 15 targets × 5 donors × 2 variants × 2 endpoints × 2 memory kinds = 600**
8. **load/checkpoint/process/report overhead**

- 각 arm-run은 8 phase 전부 측정.
- missing phase → no projection.
- step0는 update 전 또는 동일 unupdated state restore에서 측정.
- phase 5는 donor-free primary M scoring; donor factor 없음.
- phase 2/3/7만 donor factor 5.
- phase 5/7은 real/control factor 2 포함.

### 10.4 T_proj

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

- `3` = seeds; `100` = updates.
- phase 5 = **120 records/arm-seed**.
- phase 7 = **600 records/arm-seed**.
- generation 포함.
- M build 20 train 포함.
- donor 5, variants 2, endpoints 2, memory kinds 2 포함.
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
  name_len:u32 little-endian | name_utf8
  dtype_len:u8 | dtype_str
  ndim:u8 | shape:u32×ndim little-endian
  nbytes:u64 little-endian | little_endian_contiguous_bytes
SHA256 over concatenated frames
```

- frozen base/config/mode identity는 manifest에 별도 기록.
- `final_checkpoint_hash` = post-run adapter/LoRA state.
- empty state_dict → SHA256 of empty byte stream.
- tensor bytes: little-endian, contiguous, no padding.

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
- donor-free records encode `donor_id:null`, not omitted.

**Independent golden vector**:

- fixed synthetic state:
  - tensor `a`: dtype `<f4`, shape `[2]`, values `[1.0, -2.0]`
  - tensor `b`: dtype `<f4`, shape `[1,1]`, values `[0.5]`
  - empty state hash
- frame example (hand-derivable):
```text
name_len=1 | "a" | dtype_len=3 | "<f4" | ndim=1 | shape=[2] |
nbytes=8 | 0000803f 000000c0
```
- expected SHA256 must be computed by an **independent one-off script from this specification**, not by the implementation under test.
- expected digest constants are committed to `docs/hoplite/.../golden_vectors.json`.
- replay golden: three fixed records with explicit `donor_id` and `memory_kind`, expected SHA256.
- permutation/duplicate/missing-key tests.
- `golden_vectors.json` is a test artifact, not a result.

---

## 11. 3-seed checklist

1. r3.4 freeze commit hash
2. code commit hash
3. unit tests all green
4. D0 pass artifact
5. D1 timing artifact
6. preflight hash `3ee3f1ca…` + 15/20
7. debug seed 20261111 ∉ registered 20261108/09/10
8. no threshold/seed/donor/step/LR diff
9. M_VALID computation contract
10. `M_CONTROL_PREFIX753_COHORT15` scope
11. signal eligible 15 vs val20 descriptive separation
12. T_proj ≤96 min (8 phases, 120/600 records)
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
24. F/P/PA M builder existence + identity test green
25. endpoint record count 1,440 test green
26. tail input/precedence test green
27. zero-margin abort path test green

---

## 12. P0 limitation

- P0 source_max_length=256; registered M 512.
- P0 historical native-path sensitivity only.
- no P0 rerun.
- P0 not trained P/PA/L evidence.
- untrained real CE 12.7/13.2 > ln|V| 12.43 → phase 5 OOD caveat.
- P0 never B0-B/gate evidence.

---

## 13. Implementation DoD

- pure decision function
- ANDn 2/4/5
- F1–F11
- §2.4 9 L pairs (mixed true/false → NA)
- validity INVALID vs NOT_ASSESSABLE labels
- m_valid/M_CONTROL_INVALID
- m_pass_l derivation
- PA veto rationale test
- builder_ok zero/nonfinite/contributor/15 norms
- F/L/P/PA M builders; P identity
- `h_len_i >= K_M`
- endpoint identity 1,440
- M builder recipe `[:753]`/`[:512]`
- M primary reference target prefix; donor-crop 금지
- M_NORM fixed formula same adapter space
- M seed aggregation
- canonical hash golden vector independent
- empty state hash
- replay prelaunch/final
- signal eligible 15/M15 separation
- n_signal 0..15
- stats module seed 20261109/documents_positive/2-of-3
- L_COPY/L_FULL predicate tests + boundaries
- fixture 16/17/18
- tail tri-state/partial endpoint/absolute share
- PA acquisition labels
- P/PA mode/init
- adapter_lr all adapter-bearing; lora_lr all LoRA-bearing
- no `ADAPTER_REGIME_LOSS`/`M_CONTROL_NOT_VALID`
- no stale `seeds_positive`
- manifest/checkpoint/replay hash
- truth-table per-axis + named cells
- `test_split_used:false`
- validity enum assertion
- zero-margin abort path

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

## 15. R3.3 closure

| Blocker | 조치 | 상태 |
|---|---|---|
| §2.4 mixed table | §2.4 NA | closed |
| F M builder | §8.2 F | closed |
| P identity | §8.2 | closed |
| `h_i >=` type | `h_len_i` | closed |
| real_prefix_t | `A(h_t)[:K_M]` | closed |
| n_signal 15/20 | §5.1 `{NA,0..15}` | closed |
| tail input | §9.4 L copy | closed |
| top3 gate | `|delta|` | closed |
| tail NA precedence | §9.4 ordered | closed |
| adapter_lr | §7.3 all adapter | closed |
| T_proj factor | §10.4 120/600 | closed |
| endpoint count | §8.4 1,440 | closed |
| PA veto | §4.2 rationale | closed |
| golden vector | §10.6 independent | closed |
| named cell | §6.3 fixtures 16–18 | closed |
| ANDn/NOT3 domain | §2.2 scalar | closed |
| zero-margin | §8.7 | closed |
| P0 caveat | §12 | closed |

---

## 16. 동결 조건

- r3.4 review에서 NARROW가 다시 나오면 MUST-FIX만 수정한 r3.5를 작성한다.
- r3.4 승인 시 commit hash freeze.
- freeze 후 threshold/seed/donor/step/LR 변경 금지.
- 코드는 freeze 후에만 작성.
- 3-seed는 별도 gate.

---

## 17. 승인 요청

> **r3.4를 Phase 6 protocol contract로 동결하고, 구현 + unit tests + D0 zero-update mechanics debug를 진행해도 되는가?**

승인 후에도:
- D1은 별도 승인
- 3-seed는 별도 gate
- B0-B/B1/B2/Stage C는 별도
- test 163/P1 미사용
- T5Gemma2는 D-108 STOP
