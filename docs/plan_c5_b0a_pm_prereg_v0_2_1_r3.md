# C5 Phase 6 P/M Prereg v0.2.1-r3 — Text-only Contract Closure

- 작성일: 2026-11-09
- 상태: **r3 동결 후보. 실행 미승인.**
- 적용 대상: `docs/plan_c5_b0a_pm_prereg_v0_2_1_r2.md` (r2)
- 충돌 시: **r3 > r2 > r1 > v0.2.1 > v0.2**
- 근거:
  - `reports/C5_B0A_PM_PREREG_V0_2_1_R2_3AI_REVIEW_SYNTHESIS_2026-11-09.md` (NARROW 3/3)
  - `reports/provenance/C5_b0a/m_cohort_preflight.json`
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. r3의 목적

r3는 r2 3-AI NARROW의 **Must-fix만** 닫는 text-only errata다.

- threshold/seed/donor/step/LR 변경 없음
- 결과 전에 commit/freeze
- 코드는 r3 승인 후에만 작성
- `M_NOT_EVALUABLE`를 validity에서 제거하고 control에만 둔다
- path NA를 fail-closed로 만든다
- signal cohort(val20)와 M cohort(15 longest)를 분리한다
- 3-seed checklist의 stale hash와 circular M_VALID를 수정한다
- D1 timing을 D1-only로 정의한다

---

## 1. R2 Must-fix closure map

| R2 Must-fix | r3 조치 |
|---|---|
| `test_split_used=NA`, `pa_path=NA` fail-open | §3.3 known failure first + NA fail-closed |
| `M_NOT_EVALUABLE` dead label | §4 validity에서 M 제거; §5 control only |
| signal validity guard 비대칭 | §6.4 validity-invalid labels + valid-only labels |
| signal/M cohort 불명확 | §6.1 signal=val20; §8.2 M=15 longest |
| M copy endpoint zero margin | §8.3 endpoint_ok 15/15 |
| stale hash | §11 item 6 = 3ee3f1ca… |
| circular M_VALID prelaunch | §11 item 9 = computation contract |
| D1 timed phases/seed/projection | §10.3–10.5 |
| P0 256 vs 512 | §12 limitation |
| `m_pass_l` derivation absent | §2.2 inventory + §5.1 derivation |
| mixed false+NA aggregation | §8.5 false-dominant AND3 |

---

## 2. Flag inventory

### 2.1 Raw flags

```text
assay_path_ok
p0_path_ok
p_step100_path_ok
pa_step100_path_ok
test_split_used

p_valid
pa_valid

cohort_ok
endpoint_ok
seed_ok
replay_ok

m_evaluable
m_valid
m_pass_l
m_pass_pos_l
m_pass_norm_l
m_pass_pos_p
m_pass_norm_p
m_pass_pos_pa
m_pass_norm_pa

l_copy_signal
l_full_signal

n_signal
MARGINAL_SIGNAL_COHORT
M_COHORT_MARGIN
control_status
validity_status
signal_status
```

### 2.2 Derived flags

```text
m_pass_l = AND3(m_pass_pos_l, m_pass_norm_l)

m_valid = AND3(
  m_pass_pos_p, m_pass_norm_p,
  m_pass_pos_pa, m_pass_norm_pa
)

m_evaluable = AND3(
  cohort_ok,
  endpoint_ok,
  seed_ok,
  replay_ok
)

l_signal = true   if l_copy_signal=true and l_full_signal=true
           false  if l_copy_signal=false and l_full_signal=false
           not_assessable otherwise

copy_only = AND3(l_copy_signal, NOT3(l_full_signal))
full_only = AND3(l_full_signal, NOT3(l_copy_signal))
```

- `m_evaluable`은 **availability**다.
- `m_valid`는 **P/PA M calibration**이다.
- `m_pass_l`는 **L M contrast**다.
- `m_evaluable`에 `p_valid`/`pa_valid`를 넣지 않는다. control에서 별도 검사한다.

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

- **`M_NOT_EVALUABLE`는 validity에 넣지 않는다.**
- M availability는 control이 담당한다.

### 3.2 Known failure first

```text
if assay_path_ok is false
   or p0_path_ok is false
   or test_split_used is true
   or p_step100_path_ok is false:
    ASSAY_INVALID
```

- known P path failure는 다른 NA flag보다 **먼저** 평가한다.
- `p_step100_path_ok=false`는 `ASSAY_INVALID`다.
- `test_split_used=true`는 `ASSAY_INVALID`다.

### 3.3 NA fail-closed

```text
elif assay_path_ok is not_assessable
   or p0_path_ok is not_assessable
   or p_step100_path_ok is not_assessable
   or test_split_used is not_assessable:
    NOT_ASSESSABLE
```

- `test_split_used=NA` → `NOT_ASSESSABLE`.
- `assay_path_ok=NA` + known P path fail은 §3.2가 먼저 잡는다.

### 3.4 P status

```text
elif p_valid is false:
    P_STEP100_NOT_VALID
elif p_valid is not_assessable:
    NOT_ASSESSABLE
```

### 3.5 PA status

```text
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

- P valid + PA path NA → `NOT_ASSESSABLE`.
- P valid + PA path false → `PA_STEP100_NOT_VALID`.
- P invalid + PA path false → `P_STEP100_NOT_VALID` (P failure wins).
- P path false는 §3.2에서 `ASSAY_INVALID`.

### 3.6 Validity truth-table requirements

- `test_split_used=NA`가 `VALID`를 낼 수 없다.
- `pa_step100_path_ok=NA`가 `VALID`를 낼 수 없다.
- `assay_path_ok=NA` + `p_step100_path_ok=false` → `ASSAY_INVALID`.
- simultaneous P/PA path fail → `ASSAY_INVALID`.
- P valid + PA path false → `PA_STEP100_NOT_VALID`.
- `validity_status`는 `M_NOT_EVALUABLE`를 절대 반환하지 않는다.

---

## 4. Control status

### 4.1 m_evaluable

```text
cohort_ok  = common M target IDs >= 15/20
endpoint_ok = 15/15 L copy/full endpoints valid
              AND 15/15 P/PA copy/full endpoints valid
seed_ok    = 3 seeds available
replay_ok  = replay CE atol=1e-5, rtol=1e-4

m_evaluable = AND3(cohort_ok, endpoint_ok, seed_ok, replay_ok)
```

- `cohort_ok`: `M_CONTROL_PREFIX753_COHORT15`.
- `endpoint_ok`: copy mask 15/15; 하나라도 missing이면 false.
- `seed_ok`: 3 seeds.
- `replay_ok`: separate-process replay equality.
- P/PA validity는 control에서 별도 검사.

### 4.2 control_status

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

### 4.3 의미

- `M_NOT_EVALUABLE`: cohort/endpoint/seed/replay 또는 P/PA 전제 결측.
- `M_CONTROL_INVALID`: P/PA M calibration fail. L M pass를 신뢰하지 않는다.
- `M_CONTROL_PASS`: P/PA calibration pass + L M pass.
- `M_CONTROL_FAIL`: P/PA calibration pass + L M fail.
- `M_CONTROL_NOT_VALID`는 사용하지 않는다.
- `M_NOT_EVALUABLE`는 validity가 아니다.

---

## 5. Signal status

### 5.1 Signal cohort

```text
signal cohort = val20
n_signal = number of val20 docs with valid copy and full endpoints
n_min = 15
```

- signal cohort는 **val20**이다.
- M cohort는 별도로 **15 longest-of-20**이다.
- `n_signal=15`이면 `MARGINAL_SIGNAL_COHORT=true`.
- `M_COHORT_MARGIN=0`은 M cohort에만 적용한다.
- signal n과 M n을 artifact에 별도 기록한다.

### 5.2 n_signal / small N

- `n_signal=NA`: `NOT_ASSESSABLE`.
- `n_signal<15`: small-N labels.
- `l_signal=true` + n<15: `INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL`.
- `copy_only=true` + n<15: `INCONCLUSIVE_SMALL_N_WITH_COPY_ONLY`.
- `full_only=true` + n<15: `INCONCLUSIVE_SMALL_N_WITH_FULL_ONLY`.
- 그 외: `INCONCLUSIVE_SMALL_N`.

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

elif validity_status is not VALID:
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

### 5.4 Label semantics

| label | 의미 |
|---|---|
| `EXPLORATORY_L_SIGNAL` | L signal + control PASS + validity VALID |
| `L_SIGNAL_VALIDITY_INVALID` | L signal + validity invalid |
| `L_SIGNAL_M_CONTROL_FAIL` | L signal + control FAIL |
| `L_SIGNAL_M_CONTROL_INVALID` | L signal + P/PA M calibration fail |
| `L_SIGNAL_M_CONTROL_NOT_EVALUABLE` | L signal + M unavailable |
| `L_SIGNAL_CONTROL_NOT_ASSESSABLE` | L signal + control NA |
| `COPY_ONLY_VALIDITY_INVALID` | copy-only + validity invalid |
| `FULL_ONLY_VALIDITY_INVALID` | full-only + validity invalid |
| `COPY_ONLY_WEAK` | copy-only + validity VALID |
| `FULL_ONLY_WEAK` | full-only + validity VALID |
| `MEAN_CONTRAST_ONLY` | control PASS, no L signal, validity VALID |
| `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE` | control FAIL, no L signal, validity VALID |
| `NO_L_SIGNAL_CONTROL_INVALID` | control INVALID, no L signal |
| `NO_L_SIGNAL_CONTROL_NOT_EVALUABLE` | control M_NOT, no L signal |
| `INCONCLUSIVE_SMALL_N*` | n<15 variants |
| `NOT_ASSESSABLE` | unavailable |

- `EXPLORATORY_L_SIGNAL` only validity VALID.
- `MEAN_CONTRAST_ONLY`/`NO_AFFIRMATIVE` only validity VALID.
- raw L flags are always preserved.

### 5.5 L preservation

- `l_copy_signal`, `l_full_signal`, `l_signal`는 항상 `flags`에 저장.
- signal_status는 L-qualified label 또는 small-N label로 L을 명시.
- `NOT_ASSESSABLE`도 `signal_reason`과 raw flags를 저장.
- universal string invariant 대신 **flags + L-qualified labels**를 불변식으로 사용.

---

## 6. Truth-table contract

### 6.1 Raw inputs

```text
assay_path_ok ∈ {T,F,NA}
p0_path_ok ∈ {T,F,NA}
p_step100_path_ok ∈ {T,F,NA}
pa_step100_path_ok ∈ {T,F,NA}
test_split_used ∈ {T,F,NA}

p_valid ∈ {T,F,NA}
pa_valid ∈ {T,F,NA}

cohort_ok ∈ {T,F,NA}
endpoint_ok ∈ {T,F,NA}
seed_ok ∈ {T,F,NA}
replay_ok ∈ {T,F,NA}

m_pass_pos_l ∈ {T,F,NA}
m_pass_norm_l ∈ {T,F,NA}
m_pass_pos_p ∈ {T,F,NA}
m_pass_norm_p ∈ {T,F,NA}
m_pass_pos_pa ∈ {T,F,NA}
m_pass_norm_pa ∈ {T,F,NA}

l_copy_signal ∈ {T,F,NA}
l_full_signal ∈ {T,F,NA}

n_signal ∈ {NA,0,14,15,20}
```

### 6.2 Derived flag tests

- `m_pass_l = AND3(m_pass_pos_l, m_pass_norm_l)`.
- `m_valid = AND3(P/PA POS/NORM)`.
- `m_evaluable = AND3(cohort,endpoint,seed,replay)`.
- `l_signal` consensus.
- `copy_only`/`full_only` AND3/NOT3.
- mixed false+NA는 **false-dominant**: any false → false; else any NA → NA.

### 6.3 Requirements

- 모든 combination이 정확히 하나의 `(validity, control, signal)` triple을 낸다.
- `validity_status`는 `M_NOT_EVALUABLE`를 반환하지 않는다.
- `test_split_used=NA` → `NOT_ASSESSABLE`.
- `pa_step100_path_ok=NA` → `NOT_ASSESSABLE`.
- `assay_path_ok=NA` + p path false → `ASSAY_INVALID`.
- `M_CONTROL_INVALID`는 p/pa valid + m_valid false에서 reachable.
- `M_CONTROL_PASS`는 m_evaluable true, p/pa valid, m_valid true, m_pass_l true에서만.
- `L_SIGNAL_M_CONTROL_NOT_EVALUABLE` reachable: validity VALID + control M_NOT + l true.
- `L_SIGNAL_VALIDITY_INVALID` reachable: validity invalid + l true.
- `COPY_ONLY_VALIDITY_INVALID`/`FULL_ONLY_VALIDITY_INVALID` reachable.
- every label reachable at least once.
- raw inputs not mutated.
- pure function test without model/data.
- synthetic fixtures only; no registered seed/real data.

---

## 7. P/PA contract

### 7.1 P

- P = native mT5 encoder + decoder LoRA only; adapter 없음.
- P_VALID = post-training native-path sensitivity screen.

```text
P_VALID = delta_copy_step100 >= .05
          AND copy CI lower > 0
          AND delta_full_step100 > 0
          AND full CI lower > 0
```

- threshold 변경 없음.
- `P_VALID`를 “selectivity learned”로 부르지 않는다.

### 7.2 PA

- PA = native memory + random adapter + decoder LoRA.
- **PA는 acquisition control**이다.
- step0 random re-basing; `PA_RETENTION`은 null/무정보 가능.
- PA step0는 별도 실행.
- `PA_STEP100_NOT_VALID` 사용.
- `ADAPTER_REGIME_LOSS` 사용 금지.
- mT5 final hidden vs EG2 layer19 scale/geometry caveat.

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

- `make_adapter(seed)` 후 LoRA init 직전 `torch.manual_seed(seed)`.
- seed별 LoRA init 재현 test.

---

## 8. M contract

### 8.1 Lengths

| arm | K_M | source |
|---|---:|---|
| L | **753** | EG2 layer19 prefix |
| P/PA | **512** | native mT5 source prefix |

- L target: `h_len >= 753`.
- P/PA target: `native_len >= 512`.
- M cohort: **15/20**.
- signal cohort: **val20** (separate).
- full-K L 11/20 secondary only.

### 8.2 Cohort/endpoint

```text
M_CONTROL_PREFIX753_COHORT15
cohort_ok = 15/20
endpoint_ok = 15/15 L copy/full valid
              AND 15/15 P/PA copy/full valid
```

- endpoint 하나라도 missing → `m_evaluable=false`, `M_NOT_EVALUABLE`.
- M copy endpoint n을 14로 낮추지 않는다.
- signal n=15/20은 M n=15/15와 별도.
- excluded 5 shortest docs reported.

### 8.3 Builder

L:

1. `adapter.eval()`, `model.eval()`, `torch.no_grad()`.
2. train20 `A(h_i)`, `len >= 753`.
3. contributors = 16.
4. `M_POS_MEAN[j] = mean_i A(h_i)[:753][j]`.
5. `M_GLOBAL` = eligible position global mean repeat.
6. `M_NORM = M_POS_MEAN * (||real_prefix_753||_F / ||M_POS_MEAN||_F)`.

P/PA:

1. native train20 memory, `len >=512`.
2. contributors = 20.
3. same positionwise mean at 512.
4. M_NORM at 512.

### 8.4 Pass

```text
M_PASS_POS = delta_memfree_full > 0
             AND full CI lower > 0
             AND delta_memfree_copy > 0
             AND copy CI lower > 0

M_PASS_NORM = same with M_NORM

M_CONTROL_PASS_L = M_PASS_POS_L AND M_PASS_NORM_L
```

`delta_memfree_full = mean_full_ce - real_full_ce`; copy 동일.

- M_POS_MEAN-only pass는 pass 아님.
- `M_GLOBAL` secondary; rescue 없음.
- `M_PASS_NORM_CONFOUNDED` descriptive; pass 아님.

### 8.5 Aggregation

- `m_pass_l = AND3(m_pass_pos_l, m_pass_norm_l)`.
- `m_valid = AND3(P/PA POS/NORM)`.
- mixed false+NA → **false-dominant** (any false → false; else NA).
- missingness-first 구현 금지.
- P/PA 각 variant는 common 15 target IDs에서 평가.
- full 20 P/PA M은 descriptive secondary.

### 8.6 Seed aggregation / replay

- M builder는 seed별 재구성.
- target별 delta를 seed 평균 후 document bootstrap.
- 3 seeds ×15 docs를 45 independent units로 취급하지 않는다.
- final adapter/LoRA checkpoint hash 기록.
- replay separate process; CE `atol=1e-5`, `rtol=1e-4`.
- replay state hash 기록.
- 초과 시 `m_evaluable=false` / `M_NOT_EVALUABLE`.

---

## 9. Statistics constants

```text
n_boot = 1000
ci = percentile 2.5 / 97.5
bootstrap_seed = 20261109
unit = document
seed_average_before_bootstrap = true
n_min_signal = 15
```

- `per_doc_delta[doc] = mean over seeds of delta[doc, seed]`.
- `documents_positive = count(per_doc_delta > 0)`.
- `seeds_positive = count(seed_mean > 0)`.
- `seeds_positive`를 문서 수에 쓰지 않는다.
- `L>F`는 paired per-document difference.
- signal cohort val20; M cohort 15; 둘을 혼동하지 않는다.
- `sum(top3)/sum(all)`; denominator 0/비유한이면 null.
- leave-top3-out mean.
- `tail_driven = leave_top3_mean <=0 or top3_share > .50`.
- 20-doc bootstrap CI는 anti-conservative일 수 있음.
- `MARGINAL_SIGNAL_COHORT`는 label을 바꾸지 않는 flag.

---

## 10. D0 / D1 / cap

### 10.1 Registered Phase 6

| 항목 | 값 |
|---|---|
| trained units | 12 |
| updates | 1,200 |
| wall-clock | 2 hours |
| threads | 6 |
| GPU | none |
| retry | none |

### 10.2 D0 mechanics-only

- 0 optimizer updates
- F/L/P/PA load/attach/forward/shape/mode/metric
- ≤4 configs
- ≤15 minutes wall
- seed **20261111**
- no labels
- `labels_computed:false`, `not_a_result:true`
- registered cap과 별도
- D0는 timing projection 근거가 아니다.

### 10.3 D1 timing

- 4 arm-seeds × **1 update**
- seed **20261111** (shared; run-specific derived 아님)
- ≤20 minutes wall
- 별도 명시 승인
- registered cap과 별도
- no outcome labels
- `labels_computed:false`, `not_a_result:true`

D1 timed phases:

1. one train update
2. step0 eval on one doc subset
3. final eval on one doc subset
4. M builder pass (15 docs)
5. replay pass

### 10.4 Projection formula

```text
T_proj = 3 * sum_{arm in F,L,P,PA} (
            100 * t_train_arm
          + t_step0_eval_arm
          + t_step100_eval_arm
          + t_M_build_arm
          + t_replay_arm
        )
```

- `t_*`는 D1 measured seconds.
- `100`은 registered updates.
- `3`은 registered seeds.
- projection은 finite이고 ≤0.8×2h=**96분**이어야 한다.
- D0-only projection 금지.
- D1 없이 3-seed 금지.
- “separately approved timing probe”는 사용하지 않는다; D1만 인정.

### 10.5 Cap-abort

- cap 초과 시 중단·보고.
- 자동 retry/extension 없음.
- D1/D0 결과는 3-seed 결과가 아니다.

---

## 11. 3-seed launch checklist

모두 필요조건이며 충분조건이 아니다.

1. r3 freeze commit hash
2. code commit hash
3. unit tests all green
4. D0 pass artifact
5. D1 timing artifact
6. M preflight hash **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`** and common cohort 15/20
7. debug seed 20261111 ∉ {20261108,20261109,20261110}
8. freeze 이후 threshold/seed/donor/step/LR diff 없음
9. `M_VALID` **computation contract** present (not a prelaunch truth value)
10. `M_CONTROL_PREFIX753_COHORT15` scope 명시
11. signal cohort val20 vs M cohort 15 분리
12. timing projection ≤96분
13. manifest complete
14. replay hash complete
15. explicit user approval
16. test 163/P1 미사용
17. B0-B/B1/B2/Stage C 자동 승인 없음

- item 9는 **prelaunch `M_VALID=true`가 아니다**.
- `M_VALID`는 registered outputs에서 계산되는 report/interpretation gate다.
- item 6 hash는 stale `07c3...`가 아니다.

---

## 12. P0 limitation

- P0는 `source_max_length=256`에서 측정됐다.
- registered P/PA M path는 prefix 512다.
- P0는 historical native-path sensitivity이며 512 M path의 직접 검증이 아니다.
- P0 재실행은 하지 않는다.
- P0 수치를 trained P/PA/L 또는 EG2 적응 증거로 사용하지 않는다.

---

## 13. Implementation DoD

- `pm-diagnostic` 4 arms F/L/PA + M eval-only
- 12 trained units / 1,200 updates / 2h cap
- pure decision function + exhaustive truth table
- validity NA fail-closed tests
- m_valid/M_CONTROL_INVALID tests
- `m_pass_l` derivation test
- signal validity guard tests
- L preservation tests
- signal val20 / M 15 separation test
- M endpoint 15/15 test
- M cohort 15/20 test
- M seed aggregation test
- M replay equality test
- PA step0 random-adapter test
- P step0 zero-LoRA test
- `ADAPTER_REGIME_LOSS` 부재 test
- `M_CONTROL_NOT_VALID` 부재 test
- stale `seeds_positive` 사용 금지 test
- manifest/checkpoint/replay hash test
- `test_split_used:false` assertion

---

## 14. B0-B boundary

어떤 Phase 6 label도 B0-B/B1/B2/Stage C를 자동 승인하지 않는다.

B0-B predicate:

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS
AND signal_status == EXPLORATORY_L_SIGNAL
AND tail_driven == false (or explicitly reported)
AND leakage/mode/metric pass
AND artifact complete
AND separate prereg/approval
```

- `EXPLORATORY_L_SIGNAL`만으로 B0-B를 승인하지 않는다.
- `M_CONTROL_PREFIX753_COHORT15`의 scope를 report에 명시한다.
- full-K 11/20은 B0-B 근거가 아니다.
- P0/PA_RETENTION은 B0-B 근거가 아니다.

---

## 15. R2 Must-fix closure

| Must-fix | r3 조치 | 상태 |
|---|---|---|
| NA path fail-open | §3.2 known failure first + §3.3 NA | closed |
| `M_NOT_EVALUABLE` dead label | §3.1 remove from validity; §4 control only | closed |
| signal validity guard | §5.3 invalid labels + valid-only labels | closed |
| signal/M cohort | §5.1 val20; §8.2 M 15 | closed |
| M copy endpoint | §8.2 endpoint_ok 15/15 | closed |
| stale hash | §11 item 6 3ee3f1ca… | closed |
| circular M_VALID | §11 item 9 computation contract | closed |
| D1 timing | §10.3–10.5 | closed |
| P0 256/512 | §12 | closed |
| `m_pass_l` derivation | §2.2/§8.5 | closed |
| mixed false+NA | §8.5 false-dominant | closed |

---

## 16. 동결 조건

- r3 review에서 NARROW가 다시 나오면 MUST-FIX만 수정한 r4를 작성한다.
- r3가 승인되면 **commit hash를 freeze**한다.
- freeze 후 threshold/seed/donor/step/LR 변경 금지.
- 코드는 freeze 후에만 작성.
- 3-seed는 별도 gate.

---

## 17. 승인 요청

> **r3를 Phase 6 protocol contract로 동결하고, 구현 + unit tests + D0 zero-update mechanics debug를 진행해도 되는가?**

승인 후에도:
- D1은 별도 승인
- 3-seed는 별도 gate
- B0-B/B1/B2/Stage C는 별도
- test 163/P1 미사용
- T5Gemma2는 D-108 STOP
