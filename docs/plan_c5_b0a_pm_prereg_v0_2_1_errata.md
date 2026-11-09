# C5 Phase 6 P/M Prereg v0.2.1 — Errata

- 작성일: 2026-11-09
- 상태: **v0.2.1 errata 초안. 실행 미승인.**
- 적용 대상: `docs/plan_c5_b0a_pm_prereg_v0_2.md` (v0.2)
- 충돌 시: **v0.2.1이 우선**
- 근거: `reports/C5_B0A_PM_PREREG_V0_2_3AI_REVIEW_SYNTHESIS_2026-11-09.md` (NARROW 3/3)
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. 목적

v0.2.1은 새로운 실험이 아니다. v0.2의 **protocol contract**를 total·executable하게 만드는 errata다.

- threshold/seed/donor/step 변경 없음
- v0.2의 `.05`, 20/20, 3 seeds, 100 updates 유지
- 결과 전에 commit/freeze
- 코드는 이 errata 승인 후에만 작성

---

## 1. Total decision function

### 1.1 Independent flags

모든 artifact는 headline과 별도로 아래 flag를 저장한다.

```text
assay_path_ok
p0_path_ok
p_step100_path_ok
pa_step100_path_ok
p_valid
pa_valid
m_not_evaluable
m_valid_p
m_valid_pa
m_pass_pos_l
m_pass_norm_l
m_control_pass_l
l_copy_signal
l_full_signal
l_signal
tail_driven
copy_only
full_only
not_assessable
```

- `assay_path_ok`: shape/finite/64 modules/mode/metric alignment 통과
- `p_valid`: P step100 `P_VALID`
- `pa_valid`: PA step100 `PA_VALID`
- `m_valid_p` / `m_valid_pa`: P/PA M validation
- `m_pass_pos_l` / `m_pass_norm_l`: L M_POS_MEAN / M_NORM
- `m_control_pass_l`: 두 M pass의 conjunction
- `tail_driven`: leave-top-3-out mean이 0 이하로 뒤집히거나 top-3 share > .50
- `not_assessable`: missing/CI 불가로 판정 불가

### 1.2 Headline precedence

Headline은 **total deterministic function**이다. 위에서 아래로 첫 일치를 사용한다.

```text
1. ASSAY_INVALID
   if not assay_path_ok or not p0_path_ok

2. P_STEP100_NOT_VALID
   if p0_path_ok and not p_step100_path_ok

3. P_STEP100_NOT_VALID / REGIME_SENSITIVITY_LOST
   if p_step100_path_ok and not p_valid

4. ADAPTER_REGIME_LOSS
   if p_valid and pa_step100_path_ok and not pa_valid

5. M_NOT_EVALUABLE
   if m_not_evaluable

6. M_CONTROL_NOT_VALID
   if not (m_valid_p and m_valid_pa)

7. L_SIGNAL_M_CONTROL_FAIL
   if l_signal and not m_control_pass_l

8. EXPLORATORY_L_SIGNAL
   if l_signal and m_control_pass_l

9. COPY_ONLY_WEAK
   if copy_only and not full_only

10. FULL_ONLY_WEAK
    if full_only and not copy_only

11. MEAN_CONTRAST_ONLY
    if m_control_pass_l and not l_copy_signal and not l_full_signal

12. NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE
    if not l_signal and not m_control_pass_l

13. INCONCLUSIVE_SMALL_N
    otherwise
```

### 1.3 L_SIGNAL suppression 금지

- `L_COPY_SIGNAL` / `L_FULL_SIGNAL` / `L_SIGNAL`은 headline과 **독립 flag**로 항상 저장한다.
- headline이 `P_STEP100_NOT_VALID`, `M_CONTROL_NOT_VALID`, `ADAPTER_REGIME_LOSS`여도 L flag를 지우지 않는다.
- `L_SIGNAL` true인데 headline이 validity failure이면 **artifact와 report 양쪽에 명시**한다.

### 1.4 P/PA interaction

| P_VALID | PA_VALID | headline/field |
|---|---|---|
| T | T | 정상 진행 |
| T | F | **ADAPTER_REGIME_LOSS** |
| F | T | **P_STEP100_NOT_VALID** |
| F | F | **P_STEP100_NOT_VALID** + PA flag |

- `ADAPTER_REGIME_LOSS`는 descriptive label이며 “adapter가 원인”이라는 인과 주장이 아니다.
- `REGIME_ERASES_SELECTIVITY`라는 이름은 사용하지 않는다. 필요하면 narrative의 hypothesis로만 쓴다.

### 1.5 Missingness

- path/finite/shape 실패: `ASSAY_INVALID`
- CI 계산 불가: `NOT_ASSESSABLE`로 기록하고 pass/fail로 바꾸지 않는다.
- target cohort 부족: `M_NOT_EVALUABLE`
- 한 seed 누락: pooled headline 계산 금지; `NOT_ASSESSABLE`
- 문서 수 부족: `INCONCLUSIVE_SMALL_N` (failure 아님)

---

## 2. P/PA contract

### 2.1 Training hyperparameters 고정

P/PA 모두:

```text
optimizer: AdamW
weight_decay: .01
adapter_lr: 1e-3 (PA only)
lora_lr: 1e-4
updates: 100
batch: 1 document/step
example order: train_ids[step % 20]
clip_grad_norm: 1.0
base decoder: eval
LoRA: 64 modules, r8 alpha16 dropout .05
P: adapter 없음, trainable LoRA only
PA: adapter + LoRA trainable
```

- `make_adapter(seed)` 후 **LoRA init 직전** `torch.manual_seed(seed)`를 호출한다.
- P/PA 모두 동일 optimizer/order/clip을 사용한다.
- seed별 LoRA init 재현 test 필수.

### 2.2 Step0 reference

- **P step0**: native memory + zero-LoRA + no adapter; P0와 같은 docs/donors.
- **PA step0**: native memory + random adapter(seed) + zero-LoRA; **별도 실행**.
  - 이는 P0와 다른 regime이므로 P0를 PA step0으로 대체하지 않는다.
- P0는 historical reference로 보존.

### 2.3 Movement fields

모든 P/PA artifact:

```text
real_copy_ce_step0, real_full_ce_step0
wrong_copy_ce_step0, wrong_full_ce_step0
delta_copy_step0, delta_full_step0
real_copy_ce_step100, real_full_ce_step100
wrong_copy_ce_step100, wrong_full_ce_step100
delta_copy_step100, delta_full_step100
train_ce_first, train_ce_last, train_ce_last10_mean
lora_b_norm_start, lora_b_norm_end
adapter_delta_norm (PA only)
lr_adapter, lr_lora
```

- `P_RETENTION = delta_copy_step100 / delta_copy_step0` descriptive.
- denominator 0/불안정이면 `P_RETENTION=null`; gate로 사용하지 않는다.
- `PA_RETENTION` 동일.

### 2.4 P_VALID / PA_VALID

```text
P_VALID = delta_copy_step100 >= .05
          AND copy CI lower > 0
          AND delta_full_step100 > 0
          AND full CI lower > 0
```

PA_VALID same.

- 이 기준은 **post-training native-path sensitivity screen**이다.
- P_VALID를 “LoRA가 selectivity를 학습했다”는 증거로 부르지 않는다.
- P gate `.05`는 v0.2 그대로; 결과 후 변경 금지.

### 2.5 M_VALID 전제

- `M_VALID`는 **P_VALID AND PA_VALID**를 전제로 한다.
- P 또는 PA가 invalid면 M validation은 `M_NOT_EVALUABLE`; L M 실패를 content-use 부재로 해석하지 않는다.

---

## 3. M contract

### 3.1 Reference

- L M primary real reference: **full real K_real**.
- donor-cropped real CE는 M primary에 사용하지 않는다.
- P/PA M validation도 full K를 사용한다.
- M 결과를 F/L/P/PA에 소급 적용하지 않는다.

### 3.2 Mean builder

L adapter `A`, target K_real:

1. train 20 문서의 `A(h_i)` 사용.
2. `len(h_i) >= K_real` only.
3. eligible contributor ≥10.
4. `M_POS_MEAN[j] = mean_i A(h_i)[j]`.
5. `M_GLOBAL` = 모든 eligible position의 global mean vector repeat.
6. `M_NORM` = `M_POS_MEAN * (||real_memory||_F / ||M_POS_MEAN||_F)`.
7. `M_POS_MEAN` 또는 `M_NORM`의 norm이 0/non-finite이면 `M_NOT_EVALUABLE`.

### 3.3 Target cohort

- target document는 `m_eligible=true`이고 `K_real` 유효해야 한다.
- **common M cohort** = L/P/PA 모두 eligible인 target docs의 교집합.
- common cohort **≥15/20** 필요.
- <15이면 `M_NOT_EVALUABLE`; M pass/fail 금지.
- 모든 excluded doc와 이유를 artifact에 기록.

### 3.4 M pass

```text
M_PASS_POS = delta_memfree_full > 0
             AND full CI lower > 0
             AND delta_memfree_copy > 0
             AND copy CI lower > 0

M_PASS_NORM = same with M_NORM
```

- `M_CONTROL_PASS_L = M_PASS_POS_L AND M_PASS_NORM_L`.
- **M_POS_MEAN-only pass는 pass가 아니다.**
- `M_GLOBAL`은 secondary; pass를 rescue할 수 없다.
- M_VALID:

```text
M_VALID = M_PASS_POS(P) AND M_PASS_NORM(P)
          AND M_PASS_POS(PA) AND M_PASS_NORM(PA)
```

P/PA 중 하나라도 missing/CI 불가면 `M_NOT_EVALUABLE`.

### 3.5 M_NORM scale

- **whole K×512 Frobenius norm**을 사용한다.
- per-row norm은 secondary diagnostic으로만 기록한다.
- M_NORM은 real norm을 사용하므로 strictly target-independent가 아니다; magnitude-matched negative control로 표기한다.

### 3.6 M result labels

- `M_PASS_POS` only: `M_PASS_NORM_CONFOUNDED` (descriptive; not pass)
- `M_NOT_EVALUABLE`: cohort<15, eligible<10, missing CI, non-finite
- `M_CONTROL_PASS_L`: positive + norm both

---

## 4. Statistics contract

### 4.1 Unit

- **document**가 resampling unit.
- seed 평균을 먼저 만든 뒤 document bootstrap.
- 3 seeds × 20 docs를 60 independent units로 취급하지 않는다.

### 4.2 Aggregation

```text
per_doc_delta[doc] = mean over seeds of delta[doc, seed]
pooled_mean = mean(per_doc_delta)
bootstrap 1,000 document resamples
```

- seed별 mean 표를 별도 저장.
- `documents_positive` = per_doc_delta >0 count.
- `seeds_positive` = seed_mean >0 count.
- `seeds_positive`라는 이름을 문서 수에 쓰지 않는다.

### 4.3 L > F

- `L > F`는 **paired per-document difference** (`L_doc_delta − F_doc_delta`)의 mean >0.
- 양쪽 endpoint(copy/full) 각각 계산.
- `L_COPY_SIGNAL`:

```text
mean delta_copy >= .05
AND copy CI lower > 0
AND paired L−F copy mean > 0
AND 2/3 seeds copy mean > 0
```

- `L_FULL_SIGNAL`:

```text
mean delta_full > 0
AND full CI lower > 0
AND paired L−F full mean > 0
AND 2/3 seeds full mean > 0
```

- `L_SIGNAL = both`.

### 4.4 Missingness

- copy mask eligible != full eligible이면 **common-document subset**을 primary로 하고, full-only/copy-only counts를 별도 보고한다.
- common subset <15/20이면 `NOT_ASSESSABLE`.
- copy-only/full-only label은 M status를 함께 표시한다.

### 4.5 Heavy tail

- report mean, median, p05, p95
- top-3 share
- leave-top-3-out mean
- `tail_driven=true` if leave-top-3-out mean <=0 or top-3 share > .50
- `tail_driven`는 label을 자동 변경하지 않고 별도 flag로 저장

---

## 5. Debug protocol

### 5.1 v0.2.1 이후

- v0.2.1 commit hash와 code/test commit hash를 고정한 뒤 debug한다.
- debug는 **unregistered seed 20261111**을 사용한다.
- **maximum 5 updates per arm**, F/L/P/PA, no M outcome labels.
- M은 synthetic fixture와 1회 mechanics probe만; pass/fail label 계산 금지.
- debug 결과로 3-seed 조건·threshold·seed를 바꾸지 않는다.

### 5.2 허용 검사

- path/shape/finite
- 64 modules
- base eval / adapter·LoRA mode
- seed 재현성
- same-position CE == built-in loss (atol 1e-5)
- metric alignment fields
- donor/K/provenance
- M leakage/invariance synthetic tests
- label function on synthetic fixtures
- per-phase timing

### 5.3 금지

- registered seed 20261108/09/10의 100-step 결과를 debug로 사용
- debug label을 headline으로 사용
- debug 결과로 3-seed 실행 자동 승인
- debug 중 seed/donor/step/LR 탐색

---

## 6. Cap and artifacts

### 6.1 Cap

| 항목 | 값 |
|---|---|
| trained units | 12 arm-seed |
| updates | ≤1,200 total |
| wall-clock | **≤2 hours from process start** |
| threads | 6 |
| GPU | none |
| debug | **included** in wall-clock/units/updates |
| retry | automatic extension 없음 |

- wall-clock과 process CPU time을 둘 다 기록한다.
- cap 초과 시 중단·보고한다.

### 6.2 Manifests

- prereg v0.2.1 commit hash
- code commit hash
- data file hash, split hash
- tokenizer/model hash
- seeds, donor policy, LR, max lengths
- final adapter/LoRA checkpoint hash (M replay용)

### 6.3 Required artifacts

`reports/provenance/C5_b0a/pm/{arm}_{seed}.json`:

- flags vector
- headline
- per-doc deltas and eligible counts
- donor IDs/K/crop rule
- metric_alignment
- train_mode_policy
- P/PA movement fields
- M source IDs/eligible/m_eligible/norm
- generation telemetry
- timings
- test_split_used: false

---

## 7. v0.2.1 완료 조건

- [x] total decision function / precedence
- [x] L_SIGNAL non-suppression
- [x] P/PA interaction cells
- [x] P/PA step0 + retention + movement
- [x] M_POS_MEAN AND M_NORM pass
- [x] M_VALID P AND PA
- [x] common cohort ≥15/20
- [x] statistics / pooling / documents_positive
- [x] debug unregistered seed + mechanics-only
- [x] cap includes debug + wall-clock
- [x] artifact/manifests/checkpoint

---

## 8. 승인 요청

> **이 v0.2.1 errata를 v0.2의 protocol contract로 동결하고, 이후 구현·unit tests·unregistered-seed mechanics debug를 진행해도 되는가?**

승인 후에도 3-seed 실행은 별도 gate다. v0.2.1은 threshold/seed/donor/step을 바꾸지 않는다.
