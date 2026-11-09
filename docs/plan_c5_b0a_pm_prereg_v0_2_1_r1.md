# C5 Phase 6 P/M Prereg v0.2.1-r1 — Contract Repair Errata

- 작성일: 2026-11-09
- 상태: **v0.2.1-r1 동결 후보. 실행 미승인.**
- 적용 대상: `docs/plan_c5_b0a_pm_prereg_v0_2_1_errata.md` (v0.2.1)
- 충돌 시: **v0.2.1-r1 > v0.2.1 > v0.2**
- 근거:
  - `reports/C5_B0A_PM_PREREG_V0_2_1_3AI_REVIEW_SYNTHESIS_2026-11-09.md` (NARROW 3/3)
  - `reports/provenance/C5_b0a/m_cohort_preflight.json`
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. r1의 목적

r1은 v0.2.1의 **text-only contract repair**다.

- threshold/seed/donor/step/LR 변경 없음
- 결과 전에 commit/freeze
- 코드는 r1 승인 후에만 작성
- M cohort는 **data-only preflight**로 데이터에 맞게 고정
- cap은 debug와 registered run을 **분리 회계**

---

## 1. Data-only M cohort preflight

### 1.1 결과

| 항목 | 값 |
|---|---:|
| train20 h median | 768.5 |
| val20 h median | 766.5 |
| K_M_L | **753** |
| L contributors at K_M_L | **16** |
| L target eligible at K_M_L | **15/20** |
| native contributors at 512 | 20 |
| native target eligible at 512 | 20 |
| common L/P/PA cohort | **15/20** |
| required | 15/20 |
| full-K L cohort (secondary) | **11/20** |

### 1.2 Excluded at K_M_L

```text
REPORT-news_r-00430-00001
REPORT-news_r-01127-00001
REPORT-news_r-02180-00001
REPORT-news_r-02804-00001
REPORT-news_r-03445-00001
```

### 1.3 결론

- v0.2.1의 `len(h_i) >= K_real` full-K M은 **11/20**으로 `M_NOT_EVALUABLE`이 된다.
- r1은 **prefix K_M_L=753**을 사용해 **15/20 common cohort**를 확보한다.
- full-K 결과는 **secondary descriptive**로만 보고하고 M gate에 사용하지 않는다.
- 이 변경은 결과를 본 뒤 threshold를 바꾸는 것이 아니라, **결과 전 data-only preflight**다.

Artifact: `reports/provenance/C5_b0a/m_cohort_preflight.json`

---

## 2. Factored decision contract

### 2.1 원칙

v0.2.1의 단일 headline precedence는 폐기한다. 대신 **세 개의 독립 status**를 항상 동시에 출력한다.

```text
validity_status
control_status
signal_status
headline  # convenience string: "validity/control/signal"
flags     # raw tri-state values
```

- 어느 status도 다른 status를 숨기지 않는다.
- L_SIGNAL은 `flags`와 `signal_status`에 항상 남는다.
- `headline`은 편의를 위한 문자열이며 판정 근거가 아니다.

### 2.2 Tri-state

모든 gated flag:

```text
true | false | not_assessable
```

AND/OR는 강한 Kleene:

```text
AND3: any false -> false; else any NA -> NA; else true
OR3:  any true  -> true;  else any NA -> NA; else false
NOT3: true<->false; NA->NA
```

`not_assessable`을 `false`로 접지 않는다.

### 2.3 validity_status

```text
if any path/test flag is false:
    ASSAY_INVALID
elif any path/test flag is not_assessable:
    NOT_ASSESSABLE
elif p_valid is false:
    P_STEP100_NOT_VALID
elif p_valid is not_assessable:
    NOT_ASSESSABLE
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

- P step100 **path fail**은 `ASSAY_INVALID`로 통일한다.
- PA path fail은 `PA_STEP100_NOT_VALID`.
- `P_STEP100_NOT_VALID` path 변형은 삭제.
- `ADAPTER_REGIME_LOSS`는 삭제.

### 2.4 control_status

```text
if m_evaluable is not true:
    M_NOT_EVALUABLE
elif m_pass_l is true:
    M_CONTROL_PASS
elif m_pass_l is false:
    M_CONTROL_FAIL
else:
    NOT_ASSESSABLE
```

- `M_CONTROL_NOT_VALID`는 **status label로 사용하지 않는다**.
- `M_CONTROL_FAIL`이 그 자리를 대체한다.

### 2.5 signal_status

선행:

```text
n_signal = common copy/full assessable docs
n_min = 15
l_signal = AND3(l_copy_signal, l_full_signal)
copy_only = AND3(l_copy_signal, NOT3(l_full_signal))
full_only = AND3(l_full_signal, NOT3(l_copy_signal))
```

```text
if n_signal is not_assessable:
    NOT_ASSESSABLE
elif n_signal < 15:
    INCONCLUSIVE_SMALL_N
elif any required signal flag is not_assessable:
    NOT_ASSESSABLE
elif l_signal is true and control_status == M_CONTROL_PASS:
    EXPLORATORY_L_SIGNAL
elif l_signal is true and control_status == M_CONTROL_FAIL:
    L_SIGNAL_M_CONTROL_FAIL
elif l_signal is true and control_status == M_NOT_EVALUABLE:
    L_SIGNAL_M_CONTROL_NOT_EVALUABLE
elif copy_only is true:
    COPY_ONLY_WEAK
elif full_only is true:
    FULL_ONLY_WEAK
elif control_status == M_CONTROL_PASS:
    MEAN_CONTRAST_ONLY
elif control_status == M_CONTROL_FAIL:
    NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE
else:
    NOT_ASSESSABLE
```

### 2.6 label 정의

| label | 정의 |
|---|---|
| `EXPLORATORY_L_SIGNAL` | L이 copy+full signal이고 M control pass |
| `L_SIGNAL_M_CONTROL_FAIL` | L signal이지만 M control fail |
| `L_SIGNAL_M_CONTROL_NOT_EVALUABLE` | L signal이지만 M control 평가 불가 |
| `COPY_ONLY_WEAK` | copy signal만, full signal 없음 |
| `FULL_ONLY_WEAK` | full signal만, copy signal 없음 |
| `MEAN_CONTRAST_ONLY` | M control pass, 그러나 L donor signal 없음 |
| `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE` | L signal 없고 M control fail |
| `INCONCLUSIVE_SMALL_N` | n_signal < 15 |
| `NOT_ASSESSABLE` | n≥15이나 required flag/CI 결측 |

### 2.7 L_SIGNAL non-suppression

- `l_copy_signal`, `l_full_signal`, `l_signal`은 `flags`에 항상 저장.
- `signal_status`는 validity/control과 무관하게 계산 가능한 한 항상 계산.
- validity failure 때문에 signal을 `null`로 덮지 않는다.
- artifact와 report 양쪽에 `signal_status`를 별도 표기.

### 2.8 Truth-table test

구현 시 다음을 **exhaustive**로 검증한다.

입력:

```text
path ∈ {T,F,NA}
p_valid ∈ {T,F,NA}
pa_valid ∈ {T,F,NA}
m_evaluable ∈ {T,F,NA}
m_pass_l ∈ {T,F,NA}
l_copy ∈ {T,F,NA}
l_full ∈ {T,F,NA}
n_signal ∈ {NA,0,15,20}
```

- 모든 조합에 대해 `(validity_status, control_status, signal_status)`가 **정확히 하나** 나온다.
- flag 입력이 변형되지 않는다.
- 모든 label이 최소 1회 도달한다.
- `n_signal <15`는 항상 `INCONCLUSIVE_SMALL_N`.
- L flag가 true인 조합은 signal_status가 L을 잃지 않는다.

---

## 3. P/PA contract

### 3.1 P

- P = native mT5 encoder + decoder LoRA only; adapter 없음.
- P_VALID = post-training native-path sensitivity screen.
- `P_VALID`를 “LoRA가 selectivity를 학습했다”는 증거로 부르지 않는다.

```text
P_VALID = delta_copy_step100 >= .05
          AND copy CI lower > 0
          AND delta_full_step100 > 0
          AND full CI lower > 0
```

- threshold 변경 없음.
- step0/step100 real/wrong CE, movement, retention을 모두 기록.

### 3.2 PA

PA는 **acquisition control**이다.

- native memory + random adapter + decoder LoRA.
- adapter는 `Linear–GELU–Linear–LayerNorm` 랜덤 초기화.
- step0는 random re-basing; `PA_RETENTION`은 null/무정보일 수 있다.
- PA step0는 P0와 다른 regime이므로 **별도 실행**.
- `PA_VALID`는 P_VALID와 같은 threshold.

### 3.3 PA label

```text
PA_STEP100_NOT_VALID
```

- `ADAPTER_REGIME_LOSS` 삭제.
- artifact interpretation에 다음을 기록:
  - PA input은 mT5 final hidden, L input은 EG2 layer19 hidden.
  - scale/geometry가 다르다.
  - PA validity는 native path acquisition을 보여줄 뿐 L input transfer를 보장하지 않는다.

### 3.4 Hyperparameters

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

## 4. M contract (r1)

### 4.1 Lengths

| arm | K_M | source |
|---|---:|---|
| L | **753** | EG2 layer19 prefix |
| P/PA | **512** | native mT5 source prefix |
| M_NORM | same K_M | whole K_M×512 Frobenius |

- L target는 `h_real_len >= 753` 필요.
- P/PA target은 `native_len >= 512` 필요(전부 512).
- common cohort = **15/20**.
- common IDs: `m_cohort_preflight.json`.

### 4.2 Builder

L:

1. train20 adapter output `A(h_i)`; `len(h_i) >= 753`.
2. contributors = **16**.
3. `M_POS_MEAN[j] = mean_i A(h_i)[:753][j]`.
4. `M_GLOBAL` = eligible position global mean repeat.
5. `M_NORM = M_POS_MEAN * (||real_prefix_753||_F / ||M_POS_MEAN||_F)`.

P/PA:

1. native train20 memory; `len >=512`.
2. contributors = 20.
3. same positionwise mean at 512.
4. M_NORM at 512.

### 4.3 Reference

- M primary real reference: **target prefix K_M** (L 753 / native 512), same positions as M.
- `M_POS_MEAN`과 real prefix는 같은 위치/길이를 사용한다.
- full-K real CE는 **secondary descriptive**로만 보고한다.
- full-K L cohort는 11/20이며 M gate에 사용하지 않는다.
- donor-cropped real CE는 M primary에 사용하지 않는다.

### 4.4 M pass

```text
M_PASS_POS = delta_memfree_full > 0
             AND full CI lower > 0
             AND delta_memfree_copy > 0
             AND copy CI lower > 0

M_PASS_NORM = same with M_NORM

M_CONTROL_PASS_L = M_PASS_POS_L AND M_PASS_NORM_L
```

- M_POS_MEAN-only pass는 pass가 아니다.
- `M_GLOBAL`은 secondary; pass를 rescue할 수 없다.
- `M_PASS_NORM_CONFOUNDED`는 descriptive; pass 아님.

### 4.5 M_VALID

```text
M_VALID = M_PASS_POS(P) AND M_PASS_NORM(P)
          AND M_PASS_POS(PA) AND M_PASS_NORM(PA)
```

- P/PA 중 하나라도 missing/CI 불가면 `M_NOT_EVALUABLE`.
- M_VALID는 P_VALID와 PA_VALID를 전제로 한다.

### 4.6 Seed aggregation

- M은 **seed별로 builder를 재구성**한다.
- target별 `delta_memfree`를 seed 평균한 뒤 document bootstrap.
- 3 seeds × 15 docs를 45 independent units로 취급하지 않는다.
- per-seed M 표를 별도 저장한다.

### 4.7 Replay

- final adapter/LoRA checkpoint hash를 manifest에 기록.
- replay M builder/eval을 별도 프로세스에서 1회 수행.
- in-process와 replay의 CE 차이 `atol=1e-5`, `rtol=1e-4` 이내여야 한다.
- 초과 시 `M_NOT_EVALUABLE`, pass/fail 금지.

### 4.8 Cohort failure

- common cohort <15 → `M_NOT_EVALUABLE`.
- excluded doc/이유를 artifact에 기록.
- M failure를 content-use 부재로 해석하지 않는다.

---

## 5. Statistics constants

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
- common subset <15 → `NOT_ASSESSABLE`/`INCONCLUSIVE_SMALL_N`.
- top-3 share = `sum(top3) / sum(all)`.
- leave-top-3-out mean.
- `tail_driven = leave_top3_mean <=0 or top3_share > .50`.
- `tail_driven`는 label을 자동 변경하지 않고 flag로 저장.
- 20-doc bootstrap CI는 anti-conservative일 수 있음을 report에 명시.

---

## 6. Debug and cap

### 6.1 Registered Phase 6 cap

| 항목 | 값 |
|---|---|
| trained units | 12 |
| updates | 1,200 |
| wall-clock | 2 hours |
| threads | 6 |
| GPU | none |
| retry | none |

### 6.2 D0 mechanics-only

- **0 optimizer updates**
- F/L/P/PA config load/attach/forward only
- ≤4 configs
- ≤15 minutes wall
- no labels
- no seed 20261108/09/10 training
- **registered cap과 별도**
- D0 결과는 3-seed gate가 아니다

### 6.3 D1 optional 1-update smoke

- 4 arm-seeds × **1 update**
- ≤20 minutes wall
- **별도 명시 승인 필요**
- registered cap과 별도
- no result labels
- D1 없이도 D0 + unit tests로 implementation gate 통과 가능

### 6.4 Debug artifact

- commit hash
- config
- per-phase timing
- seed
- `labels_computed: false`
- `not_a_result: true`
- output hash

### 6.5 Timing projection

- D0/D1 timing으로 3-seed wall-clock을 외삽.
- projection > 0.8 × 2h이면 3-seed launch 금지, 별도 승인 필요.

---

## 7. 3-seed launch checklist

모두 필요조건이며 충분조건이 아니다.

1. r1 freeze commit hash
2. code commit hash
3. unit tests all green (decision truth table, M, seed, replay, stats constants)
4. D0 pass artifact
5. M preflight common cohort 15/20
6. timing projection ≤0.8 × cap
7. manifest complete
8. explicit user approval
9. test 163/P1 미사용
10. B0-B/B1/B2/Stage C 자동 승인 없음

---

## 8. Implementation DoD

- `pm-diagnostic`는 4 arms F/L/P/PA + M eval-only를 지원
- 12 trained units / 1,200 updates / 2h cap
- decision truth table exhaustive test
- tri-state propagation test
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

## 9. B0-B boundary

어떤 Phase 6 label도 B0-B/B1/B2/Stage C를 자동 승인하지 않는다.

B0-B는 별도 사전등록·별도 승인이다.

필요조건:

- P/PA valid
- M valid + L M pass
- L_SIGNAL(copy+full)
- heavy-tail robustness
- leakage/mode/metric 실패 없음
- artifact 완전성
- 별도 review/approval

`EXPLORATORY_L_SIGNAL`은 exploratory이며 B0-B 승인이 아니다.

---

## 10. v0.2.1 Must-fix closure

| Must-fix | r1 조치 | 상태 |
|---|---|---|
| decision function total | factored 3-status + tri-state + truth table | closed |
| `not_assessable` headline | `NOT_ASSESSABLE` in validity/control/signal | closed |
| `INCONCLUSIVE_SMALL_N` dead cell | n_signal<15 rule | closed |
| PA path-fail | `PA_STEP100_NOT_VALID` | closed |
| P path-fail | `ASSAY_INVALID` | closed |
| L_SIGNAL suppression | separate signal_status + flags | closed |
| `MEAN_CONTRAST_ONLY` undefined | §2.6 정의 | closed |
| M cohort unreachable | K_M_L=753, 15/20 preflight | closed |
| M seed aggregation | §4.6 | closed |
| M replay | §4.7 | closed |
| cap 1,200+debug | D0 zero-update separate; D1 separate approval | closed |
| PA acquisition naming | PA_STEP100_NOT_VALID + caveat | closed |
| stats constants | §5 | closed |
| stale B0-B references | §9 | closed |

---

## 11. 동결 조건

- r1 review에서 NARROW가 다시 나오면 MUST-FIX만 수정한 r2를 작성한다.
- r1이 승인되면 **commit hash를 freeze**한다.
- freeze 후 threshold/seed/donor/step/LR 변경 금지.
- 구현 전 code 작성 금지.
- 3-seed는 별도 gate.

---

## 12. 승인 요청

> **v0.2.1-r1을 Phase 6 protocol contract로 동결하고, 구현 + unit tests + D0 zero-update mechanics debug를 진행해도 되는가?**

승인 후에도:
- 3-seed 실행은 별도
- B0-B/B1/B2/Stage C는 별도
- test 163/P1은 미사용
- T5Gemma2는 D-108 STOP
