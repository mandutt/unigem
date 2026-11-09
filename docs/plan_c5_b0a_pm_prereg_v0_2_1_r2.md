# C5 Phase 6 P/M Prereg v0.2.1-r2 — Text-only Contract Repair

- 작성일: 2026-11-09
- 상태: **r2 동결 후보. 실행 미승인.**
- 적용 대상: `docs/plan_c5_b0a_pm_prereg_v0_2_1_r1.md` (r1)
- 충돌 시: **r2 > r1 > v0.2.1 > v0.2**
- 근거:
  - `reports/C5_B0A_PM_PREREG_V0_2_1_R1_3AI_REVIEW_SYNTHESIS_2026-11-09.md` (NARROW 3/3)
  - `reports/provenance/C5_b0a/m_cohort_preflight.json`
  - `reports/provenance/C5_b0a/m_cohort_preflight.sha256`
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. r2의 목적

r2는 r1 3-AI NARROW의 **Must-fix만** 닫는 text-only errata다.

- threshold/seed/donor/step/LR 변경 없음
- 결과 전에 commit/freeze
- 코드는 r2 승인 후에만 작성
- data-only preflight는 r2에서 hash로 고정
- M control cohort는 **15/20, zero-margin**임을 명시
- D0/D1과 registered cap을 분리 회계

---

## 1. M preflight (r2 보강)

### 1.1 K 선택 규칙

r1의 K=753은 결과 전 data-only 선택이지만 규칙이 문자로 고정되지 않았다. r2는 다음을 동결한다.

```text
K_M_L = max K such that
  count(train20 h_len >= K) >= 10
  AND count(val20 h_len >= K) >= 15
```

- `K_M_L = 753`
- `K_M_L + 1 = 754`이면 val eligible이 **14**로 감소
- 따라서 753이 조건을 만족하는 **최대 K**
- 이 규칙은 target outcome을 보지 않은 **length-only** 선택이다.

### 1.2 결과

| 항목 | 값 |
|---|---:|
| train20 h median | 768.5 |
| val20 h median | 766.5 |
| K_M_L | **753** |
| L contributors | **16** |
| L target eligible | **15/20** |
| native source length | **512 all 20** |
| native contributors | 20 |
| native target eligible | 20 |
| common cohort | **15/20** |
| full-K L cohort (secondary) | **11/20** |

### 1.3 Cohort label

```text
M_CONTROL_PREFIX753_COHORT15
```

- M control cohort = val20 중 h>=753인 **15개**
- 이는 “15 longest-of-20”이다.
- excluded 5:
  - `REPORT-news_r-00430-00001`
  - `REPORT-news_r-01127-00001`
  - `REPORT-news_r-02180-00001`
  - `REPORT-news_r-02804-00001`
  - `REPORT-news_r-03445-00001`
- **zero-margin**: 정확히 15/20이며 여유가 없다.
- 한 doc의 copy mask가 빠지면 signal n은 14가 될 수 있다.
- 이 경우 M rule을 바꾸지 않고 `INCONCLUSIVE_SMALL_N`으로 보고한다.

### 1.4 Hash

- frozen preflight: `m_cohort_preflight.json`
- SHA256: **`07c3fe4cc1f0cb7b3c8af89ef0eb2dc9448eb4ec9a09587dba323a800d44617e`**
- hash file: `reports/provenance/C5_b0a/m_cohort_preflight.sha256`
- freeze 후 K/cohort 재산출 금지.

### 1.5 full-K secondary

- full-K L cohort는 **11/20**.
- full-K real CE는 secondary descriptive only.
- full-K는 M gate가 아니다.
- `M_CONTROL_PREFIX753_COHORT15`를 full-real-K control로 부르지 않는다.

---

## 2. Flag inventory and path precedence

### 2.1 Flag inventory

```text
assay_path_ok
p0_path_ok
p_step100_path_ok
pa_step100_path_ok
test_split_used

p_valid
pa_valid

m_evaluable
m_valid
m_pass_l
m_pass_pos_p
m_pass_norm_p
m_pass_pos_pa
m_pass_norm_pa

l_copy_signal
l_full_signal

n_signal
MARGINAL_SIGNAL_COHORT
control_status
validity_status
signal_status
```

### 2.2 m_evaluable

```text
m_evaluable = AND3(
  cohort_ok,
  seed_ok,
  replay_ok,
  p_valid,
  pa_valid
)
```

- `cohort_ok`: common M cohort >=15/20
- `seed_ok`: 3 seeds available
- `replay_ok`: replay equality pass
- `p_valid`/`pa_valid`: P/PA step100 valid
- `m_evaluable`는 **availability**다. P/PA M calibration 결과(`m_valid`)와 구분한다.
- `m_valid`는 `m_evaluable=true`에서만 의미가 있다.

### 2.3 Path flags

- `assay_path_ok`: shape/finite/64 modules/same-position CE/metric alignment.
- `p0_path_ok`: P0 historical path usable.
- `p_step100_path_ok`: P step100 forward/eval path.
- `pa_step100_path_ok`: PA step100 forward/eval path.
- `test_split_used`: must be false.

### 2.4 Path precedence

```text
if assay_path_ok is false
   or p0_path_ok is false
   or test_split_used is true:
    ASSAY_INVALID

elif any of assay_path_ok, p0_path_ok, p_step100_path_ok is not_assessable:
    NOT_ASSESSABLE

elif p_step100_path_ok is false:
    ASSAY_INVALID

elif p_valid is false:
    P_STEP100_NOT_VALID

elif p_valid is not_assessable:
    NOT_ASSESSABLE

elif pa_step100_path_ok is false:
    PA_STEP100_NOT_VALID

elif pa_valid is false:
    PA_STEP100_NOT_VALID

elif pa_valid is not_assessable:
    NOT_ASSESSABLE

elif m_evaluable is false:
    M_NOT_EVALUABLE

elif m_evaluable is not_assessable:
    M_NOT_EVALUABLE

else:
    VALID
```

- `pa_step100_path_ok`는 “any path” aggregate에 넣지 않는다.
- P path fail은 `ASSAY_INVALID`.
- PA path fail은 `PA_STEP100_NOT_VALID`.
- P valid + PA path fail cell을 명시적으로 포함.
- simultaneous P/PA path fail은 P failure가 우선한다.
- `test_split_used=true`는 무조건 `ASSAY_INVALID`.

---

## 3. Tri-state logic

모든 gated flag는 `true | false | not_assessable`.

```text
AND3: any false -> false; else any NA -> NA; else true
OR3:  any true  -> true;  else any NA -> NA; else false
NOT3: true<->false; NA->NA
```

별도로 signal consensus를 정의한다.

```text
l_signal = true   if l_copy_signal=true and l_full_signal=true
           false  if l_copy_signal=false and l_full_signal=false
           not_assessable otherwise

copy_only = AND3(l_copy_signal, NOT3(l_full_signal))
full_only = AND3(l_full_signal, NOT3(l_copy_signal))
```

- `l_copy=false, l_full=NA`이면 `l_signal=NA`다.
- 한쪽만 false인 경우를 “no signal”로 접지 않는다.
- `copy_only`/`full_only`가 true이려면 반대쪽이 명시적 false여야 한다.

---

## 4. Validity status

§2.3의 precedence를 그대로 사용한다.

```text
ASSAY_INVALID
P_STEP100_NOT_VALID
PA_STEP100_NOT_VALID
M_NOT_EVALUABLE
NOT_ASSESSABLE
VALID
```

- `P_STEP100_NOT_VALID`는 path 실패가 아니라 **P_VALID false**만 뜻한다.
- `PA_STEP100_NOT_VALID`는 path 또는 valid 실패를 모두 포함한다.
- `M_NOT_EVALUABLE`은 cohort/seed/replay/availability 결측이다.
- `M_CONTROL_INVALID`는 validity가 아니라 control에 둔다.

---

## 5. Control status

### 5.1 m_valid

```text
m_valid = AND3(
  m_pass_pos_p,
  m_pass_norm_p,
  m_pass_pos_pa,
  m_pass_norm_pa
)
```

- P/PA 각각 POS **and** NORM.
- `m_valid`는 P_VALID와 PA_VALID를 전제로 한다.
- P/PA 중 하나라도 invalid면 `m_valid`를 pass로 계산하지 않는다.

### 5.2 control_status

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

### 5.3 의미

- `M_CONTROL_INVALID`: P/PA M calibration이 fail. L M pass를 신뢰하지 않는다.
- `M_NOT_EVALUABLE`: cohort/seed/replay/P/PA 전제 결측. pass/fail 금지.
- `M_CONTROL_PASS`: P/PA calibration pass **and** L M pass.
- `M_CONTROL_FAIL`: calibration pass **and** L M fail.
- `M_CONTROL_NOT_VALID`는 사용하지 않는다.

---

## 6. Signal status

### 6.1 n_signal

```text
n_signal = number of common target docs with valid copy and full endpoints
n_min = 15
```

- copy/full common subset이 없으면 `n_signal=NA`.
- `n_signal=15`이면 zero margin이며 `MARGINAL_SIGNAL_COHORT=true`.
- `MARGINAL_SIGNAL_COHORT`는 label을 바꾸지 않는 flag다.

### 6.2 signal_status

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

elif copy_only is true:
    COPY_ONLY_WEAK

elif full_only is true:
    FULL_ONLY_WEAK

elif l_signal is not_assessable:
    NOT_ASSESSABLE

elif l_signal is true:
    if validity_status != VALID:
        L_SIGNAL_VALIDITY_INVALID
    elif control_status == M_CONTROL_PASS:
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

### 6.3 label semantics

| label | 의미 |
|---|---|
| `EXPLORATORY_L_SIGNAL` | L copy+full signal, M control pass, **validity VALID** |
| `L_SIGNAL_VALIDITY_INVALID` | L signal, but validity is not VALID |
| `L_SIGNAL_M_CONTROL_FAIL` | L signal, M control fail |
| `L_SIGNAL_M_CONTROL_INVALID` | L signal, P/PA M calibration fail |
| `L_SIGNAL_M_CONTROL_NOT_EVALUABLE` | L signal, M not evaluable |
| `L_SIGNAL_CONTROL_NOT_ASSESSABLE` | L signal, control axis not assessable |
| `COPY_ONLY_WEAK` | copy signal only, full endpoint false |
| `FULL_ONLY_WEAK` | full signal only, copy endpoint false |
| `MEAN_CONTRAST_ONLY` | M pass, but no L donor signal |
| `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE` | no L signal, M control fail |
| `NO_L_SIGNAL_CONTROL_INVALID` | no L signal, P/PA M invalid |
| `NO_L_SIGNAL_CONTROL_NOT_EVALUABLE` | no L signal, M not evaluable |
| `INCONCLUSIVE_SMALL_N` | n_signal<15, no L qualifier |
| `INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL` | n_signal<15, L signal present |
| `INCONCLUSIVE_SMALL_N_WITH_COPY_ONLY` | n_signal<15, copy-only |
| `INCONCLUSIVE_SMALL_N_WITH_FULL_ONLY` | n_signal<15, full-only |
| `NOT_ASSESSABLE` | n≥15 but signal/control unavailable |

### 6.4 L preservation

- raw L flags는 항상 `flags`에 저장한다.
- signal_status는 L을 **가능한 한 label에 명시**한다.
- `INCONCLUSIVE_SMALL_N` 계열은 L flag를 보존하면서 small-N을 표현한다.
- `NOT_ASSESSABLE`도 `signal_reason`과 raw L flags를 함께 저장한다.
- “L flag가 true인 모든 조합에서 signal_status가 L을 포함한다”는 **문자 그대로의** 불변식은 사용하지 않는다. 대신 **flags 보존 + L-qualified label**을 불변식으로 한다.

---

## 7. Truth-table test

### 7.1 Inputs

```text
assay_path_ok ∈ {T,F,NA}
p0_path_ok ∈ {T,F,NA}
p_step100_path_ok ∈ {T,F,NA}
pa_step100_path_ok ∈ {T,F,NA}
test_split_used ∈ {T,F,NA}

p_valid ∈ {T,F,NA}
pa_valid ∈ {T,F,NA}
m_evaluable ∈ {T,F,NA}
m_valid ∈ {T,F,NA}
m_pass_l ∈ {T,F,NA}
l_copy_signal ∈ {T,F,NA}
l_full_signal ∈ {T,F,NA}
n_signal ∈ {NA,0,14,15,20}
```

### 7.2 Requirements

- 모든 조합에서 `(validity_status, control_status, signal_status)`가 정확히 하나 나온다.
- 입력 flag가 변형되지 않는다.
- 모든 label이 최소 1회 도달한다.
- `test_split_used=true`는 항상 `ASSAY_INVALID`.
- P path fail은 `ASSAY_INVALID`.
- PA path fail + P valid는 `PA_STEP100_NOT_VALID`.
- `m_valid=false` + P/PA valid는 `M_CONTROL_INVALID`.
- `validity_status != VALID` + L signal은 `L_SIGNAL_VALIDITY_INVALID`이며 `EXPLORATORY`가 아니다.
- `n_signal<15`는 small-N 계열로만 간다.
- L flag는 raw flags에서 보존된다.

### 7.3 Constraint fixtures

- impossible flag combinations은 별도 `constraint_violation` fixture로 표시하되 status는 total해야 한다.
- pure decision function은 model/데이터 없이 실행 가능해야 한다.
- synthetic fixture만 사용; 등록 seed/real data 사용 금지.

---

## 8. P/PA contract

### 8.1 P

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

### 8.2 PA

- PA = native memory + random adapter + decoder LoRA.
- **PA는 acquisition control**이다.
- step0 random re-basing; `PA_RETENTION`은 null/무정보 가능.
- PA step0는 별도 실행.
- `PA_STEP100_NOT_VALID` 사용.
- `ADAPTER_REGIME_LOSS` 사용 금지.
- mT5 final hidden vs EG2 layer19 scale/geometry caveat를 artifact에 기록.

### 8.3 Hyperparameters

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
- seed별 LoRA init 재현 test 필수.

---

## 9. M contract

### 9.1 Lengths

| arm | K_M | source |
|---|---:|---|
| L | **753** | EG2 layer19 prefix |
| P/PA | **512** | native mT5 source prefix |

- L target: `h_len >= 753`.
- P/PA target: `native_len >= 512`.
- common cohort **15/20**.
- full-K L 11/20 secondary only.

### 9.2 Builder determinism

L:

1. `adapter.eval()`, `model.eval()`, `torch.no_grad()`.
2. train20 `A(h_i)`, `len >= 753`.
3. contributors = **16**.
4. `M_POS_MEAN[j] = mean_i A(h_i)[:753][j]`.
5. `M_GLOBAL` = eligible position global mean repeat.
6. `M_NORM = M_POS_MEAN * (||real_prefix_753||_F / ||M_POS_MEAN||_F)`.

P/PA:

1. native train20 memory, `len >=512`.
2. contributors = 20.
3. same positionwise mean at 512.
4. M_NORM at 512.

### 9.3 Reference / cohort

- M primary real = target prefix K_M (L 753 / native 512).
- M control cohort = common **15/20**.
- P/PA variants evaluated on the same 15 target IDs.
- full 20 P/PA M values are descriptive secondary.
- full-K L 11/20 is descriptive secondary.
- donor-cropped real CE는 M primary가 아니다.
- `M_CONTROL_PREFIX753_COHORT15`를 full-real-K control로 부르지 않는다.

### 9.4 M pass

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
- `M_GLOBAL` secondary; pass rescue 없음.
- `M_PASS_NORM_CONFOUNDED` descriptive; pass 아님.

### 9.5 M_VALID

```text
M_VALID = m_pass_pos_p AND m_pass_norm_p
          AND m_pass_pos_pa AND m_pass_norm_pa
```

- P/PA 중 하나라도 missing/CI 불가면 `m_valid=NA`.
- P/PA 중 하나라도 false면 `m_valid=false`.
- `m_valid`는 `control_status`에서 `M_CONTROL_INVALID`로 라우팅.

### 9.6 Seed aggregation

- M builder는 **seed별**로 재구성.
- target별 delta를 seed 평균한 뒤 document bootstrap.
- 3 seeds × 15 docs를 45 independent units로 취급하지 않는다.
- per-seed M 표 별도 저장.

### 9.7 Replay

- final adapter/LoRA checkpoint hash를 manifest에 기록.
- replay M builder/eval을 별도 프로세스에서 1회.
- CE 차이 `atol=1e-5`, `rtol=1e-4`.
- 초과 시 `m_evaluable=false` / `M_NOT_EVALUABLE`.
- replay state hash를 artifact에 기록.

### 9.8 Cohort failure

- common cohort <15 → `M_NOT_EVALUABLE`.
- excluded doc/이유 기록.
- M failure를 content-use 부재로 해석하지 않는다.

---

## 10. Statistics constants

```text
n_boot = 1000
ci = percentile 2.5 / 97.5
bootstrap_seed = 20261109
unit = document
seed_average_before_bootstrap = true
n_min_signal = 15
```

- `per_doc_delta[doc] = mean over seeds of delta[doc, seed]`.
- `pooled_mean = mean(per_doc_delta)`.
- `documents_positive = count(per_doc_delta > 0)`.
- `seeds_positive = count(seed_mean > 0)`.
- `seeds_positive`를 문서 수에 쓰지 않는다.
- `L>F`는 paired per-document difference.
- copy/full common subset primary; full-only/copy-only counts 별도.
- common subset <15 → small-N/NA.
- top-3 share = `sum(top3) / sum(all)`.
- leave-top-3-out mean.
- `tail_driven = leave_top3_mean <=0 or top3_share > .50`.
- `tail_driven`는 label을 자동 변경하지 않고 flag로 저장.
- 20-doc bootstrap CI는 anti-conservative일 수 있음.
- `MARGINAL_SIGNAL_COHORT`는 label을 바꾸지 않는 flag.

---

## 11. Debug and cap

### 11.1 Registered Phase 6

| 항목 | 값 |
|---|---|
| trained units | 12 |
| updates | 1,200 |
| wall-clock | 2 hours |
| threads | 6 |
| GPU | none |
| retry | none |

### 11.2 D0 mechanics-only

- **0 optimizer updates**
- F/L/P/PA load/attach/forward/shape/mode/metric
- ≤4 configs
- ≤15 minutes wall
- seed **20261111**
- no labels
- `labels_computed:false`, `not_a_result:true`
- **registered cap과 별도**
- D0는 3-seed timing을 추정하지 않는다.

### 11.3 D1 timing/1-update

- 4 arm-seeds × **1 update**
- seed **20261111**
- ≤20 minutes wall
- **별도 명시 승인**
- registered cap과 별도
- no outcome labels
- D1은 3-seed timing projection의 **측정 근거**다.
- D1 없이 3-seed timing projection을 주장하지 않는다.
- D1은 implementation gate의 필수조건은 아니다.
- D1은 **3-seed launch의 필수조건**이다. 단, 별도 승인된 timing probe로 대체 가능.

### 11.4 Timing projection

- D1 per-phase timing으로 3-seed wall-clock을 외삽.
- projection은 finite finite이고 ≤0.8×2h=**96분**이어야 한다.
- D0-only projection 금지.
- projection 불가/비유한이면 3-seed launch 금지.
- cap 초과 시 중단·보고; 자동 retry/extension 없음.

---

## 12. 3-seed launch checklist

모두 필요조건이며 충분조건이 아니다.

1. r2 freeze commit hash
2. code commit hash
3. unit tests all green
4. D0 pass artifact
5. D1 timing artifact (or separately approved timing probe)
6. M preflight hash `07c3fe4c…` and common cohort 15/20
7. debug seed 20261111 ∉ {20261108,20261109,20261110}
8. freeze 이후 threshold/seed/donor/step/LR diff 없음
9. P/PA M_VALID true
10. `M_CONTROL_PREFIX753_COHORT15` 명시
11. timing projection ≤96분
12. manifest complete
13. explicit user approval
14. test 163/P1 미사용
15. B0-B/B1/B2/Stage C 자동 승인 없음

---

## 13. Implementation DoD

- `pm-diagnostic` 4 arms F/L/P/PA + M eval-only
- 12 trained units / 1,200 updates / 2h cap
- pure decision function with exhaustive truth table
- tri-state propagation test
- `m_valid` / `M_CONTROL_INVALID` test
- path flag enumeration + PA path cell test
- L preservation test (raw flags + L-qualified labels)
- seed-averaged per-doc bootstrap test
- M cohort 15/20 preflight test
- M seed aggregation test
- M replay equality test
- PA step0 random-adapter test
- P step0 zero-LoRA test
- `ADAPTER_REGIME_LOSS` 부재 test
- `M_CONTROL_NOT_VALID` 부재 test
- stale `seeds_positive` 사용 금지 test
- manifest/checkpoint hash test
- `test_split_used:false` assertion

---

## 14. B0-B boundary

어떤 Phase 6 label도 B0-B/B1/B2/Stage C를 자동 승인하지 않는다.

B0-B predicate:

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS
AND signal_status == EXPLORATORY_L_SIGNAL
AND m_valid == true
AND tail_driven == false (or explicitly reported)
AND leakage/mode/metric pass
AND artifact complete
AND separate prereg/approval
```

- `EXPLORATORY_L_SIGNAL`만으로 B0-B를 승인하지 않는다.
- `M_CONTROL_PREFIX753_COHORT15`의 scope를 report에 명시한다.
- full-K 11/20 결과는 B0-B 근거가 아니다.

---

## 15. r1 Must-fix closure

| Must-fix | r2 조치 | 상태 |
|---|---|---|
| m_valid/M_VALID 슬롯 | control_status m_valid, M_CONTROL_INVALID | closed |
| path flag 미열거 | §2 flag inventory/precedence | closed |
| PA path 충돌 | PA_STEP100_NOT_VALID, P path ASSAY_INVALID | closed |
| L 보존 불변식 | L-qualified labels + small-N labels | closed |
| K_M_L 규칙 미기재 | §1.1 max-K rule + hash | closed |
| zero margin | MARGINAL_SIGNAL_COHORT flag | closed |
| M builder 결정론 | eval/no_grad + state hash | closed |
| M_VALID cohort | common 15/20 | closed |
| per-variant aggregation | §9.3/9.6 | closed |
| D0/D1 seed | 20261111 | closed |
| D1/timing gate | D1 required for 3-seed | closed |
| stale `seeds_positive` | DoD | closed |
| stale label | §14 | closed |

---

## 16. 동결 조건

- r2 review에서 NARROW가 다시 나오면 MUST-FIX만 수정한 r3를 작성한다.
- r2가 승인되면 **commit hash를 freeze**한다.
- freeze 후 threshold/seed/donor/step/LR 변경 금지.
- 코드는 freeze 후에만 작성.
- 3-seed는 별도 gate.

---

## 17. 승인 요청

> **r2를 Phase 6 protocol contract로 동결하고, 구현 + unit tests + D0 zero-update mechanics debug를 진행해도 되는가?**

승인 후에도:
- D1은 별도 승인
- 3-seed는 별도 gate
- B0-B/B1/B2/Stage C는 별도
- test 163/P1 미사용
- T5Gemma2는 D-108 STOP
