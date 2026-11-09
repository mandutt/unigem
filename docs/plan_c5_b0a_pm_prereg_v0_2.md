# C5 B0-A Phase 6 — P/M Bounded Diagnostic Preregistration v0.2

- 작성일: 2026-11-09
- 상태: **v0.2 초안. 실행 미승인.**
- v0.1: `docs/plan_c5_b0a_pm_prereg_v0_1.md` (preserved, superseded)
- 상위 계획: `docs/plan_c5_b0a_repair_v0_1.md`
- 3-AI review: `reports/C5_B0A_PM_PREREG_3AI_REVIEW_SYNTHESIS_2026-11-09.md` (NARROW 3/3)
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- B0-B / B1 / B2 / Stage C: **미승인**

---

## 0. v0.2 변경 요약

v0.1 review의 공통 Must-fix를 다음과 같이 반영했다.

| Must-fix | v0.2 조치 |
|---|---|
| P gate near-vacuous | P에 `.05` + full CE + CI 조건; step0(P0) vs step100; PA arm 추가 |
| P/F/L regime 불일치 | **PA** = native memory + adapter + LoRA 추가 (12 trained units) |
| P0 heavy-tail | mean/median/top-3 share/leave-top-3-out 병기; mean 단독 금지 |
| M 정의 불확실 | real reference를 full K로 고정; mean builder·eligibility·leakage test 동결 |
| M position-wise 의미 약함 | M_POS_MEAN primary + M_GLOBAL/M_NORM secondary |
| M이 P/PA에서 미검증 | M validation을 P/PA에 먼저 적용; 실패 시 M_NOT_VALID |
| Label overclaim | `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE`, `M_CONTROL_NOT_VALID`, `REGIME_ERASES_SELECTIVITY` 추가 |
| L_SIGNAL + M fail cell 누락 | `L_SIGNAL_M_CONTROL_FAIL` 추가 |
| Copy mask가 copy-specific 아님 | aligned **full CE co-primary**; as-run copy secondary; strict mask exploratory |
| `seeds_positive` mislabel | 문서 positive와 seed positive 분리; pooled + per-seed 표 |
| 2/3 seeds 미구현 | seed별 mean을 코드에서 계산·기록 |
| cap 모호 | 12 trained units, ≤1,200 updates, ≤2 CPU-hours, 6 threads |
| P/PA seed 미고정 | `torch.manual_seed(seed)`를 LoRA init 전에 호출 |
| artifact 누락 | donor ID/K, mean source ID list, m_eligible, checkpoint hash |

---

## 1. 목적

20 train / 20 val에서 다음을 분리한다.

1. **P**: native mT5 encoder + decoder LoRA가 corrected metric에서 selectivity를 유지하는가?
2. **PA**: native memory + adapter + LoRA에서도 selectivity가 유지되는가? — adapter soft-prompt 효과 분리
3. **M**: L의 real memory가 target-independent mean memory보다 나은가?
4. **F/L**: repaired metric·mode에서 EG2 layer19 memory의 signal이 남아 있는가?

Phase 6는 **B0-B 300/95가 아니다.** B0-B/B1/B2/C는 별도 결정이다.

---

## 2. Arms

| arm | memory | adapter | decoder LoRA | trainable | 역할 |
|---|---|---|---|---|---|
| F | EG2 native layer19 | yes | no | adapter | EG2 adapter-only |
| L | EG2 native layer19 | yes | yes (64) | adapter + LoRA | EG2 bridge |
| P | native mT5 encoder | no | yes (64) | LoRA | native path positive control |
| PA | native mT5 encoder | yes | yes (64) | adapter + LoRA | adapter soft-prompt control |
| M | train-only mean | — | — | no training | L checkpoint memory replacement |

- F/L/P/PA: 3 seeds each = **12 trained units**
- M: **evaluation-only**, no optimizer updates

### 2.1 F

- 20 train / 100 updates / seed 20261108/09/10
- EG2 native layer19 512d cache
- adapter 526,336 params
- base decoder eval
- no LoRA

### 2.2 L

- same as F
- decoder self/cross q/k/v/o LoRA, **64 modules**, r8 α16 dropout .05
- base eval; adapter+LoRA train
- same corrected metric

### 2.3 P

- memory: native mT5 encoder on `summarize: ` + source passage
- adapter: **없음**
- decoder LoRA: 64 modules
- `torch.manual_seed(seed)` before LoRA init
- base eval; LoRA train
- 100 updates
- eval: native val memory vs length-matched native donor source

### 2.4 PA

- memory: native mT5 encoder
- adapter: same architecture/initialization scheme as F/L, `make_adapter(seed)`
- decoder LoRA: 64 modules
- base eval; adapter+LoRA train
- 100 updates
- 목적: adapter가 native memory의 selectivity를 보존/파괴하는지 확인

### 2.5 M — evaluation-only

L checkpoint를 고정하고 memory만 교체한다.

- real reference: **full real memory** `K_real` (donor crop 아님)
- mean source: **train 20 문서의 adapter memory만**
- target val/summary/donor를 mean에 사용하지 않음
- `len(h_i) >= K_real`인 train 문서만 사용
- eligible train 문서 < 10이면 `m_eligible=false`; 해당 doc 제외
- primary: `M_POS_MEAN` = position-wise mean
- secondary: `M_GLOBAL` (global mean vector), `M_NORM` (real memory norm에 맞춘 mean)
- M validation: **P/PA에서도** real vs mean을 먼저 평가한다
  - P/PA M control이 실패하면 **M_NOT_VALID**; L의 M 실패를 content-use 부재로 해석하지 않는다

#### 금지

- val/target label/donor를 mean에 사용
- donor-cropped real CE를 M primary real reference로 사용
- M 결과를 L 외 arm에 소급 적용
- M_NOT_VALID 상태에서 “no content use” 주장

---

## 3. Mean-memory 정의

L adapter `A`, target doc의 real memory length `K_real`.

1. train 20 문서의 `A(h_i)`를 만든다.
2. `len(h_i) >= K_real`인 train 문서만 eligible.
3. `M_POS_MEAN[j] = mean_i A(h_i)[j]` for `j in [0, K_real)`.
4. eligible 수 `<10`이면 `m_eligible=false`; doc 제외.
5. `M_GLOBAL` = eligible train memory의 모든 position 평균을 repeat.
6. `M_NORM` = `M_POS_MEAN * (||real_memory|| / ||M_POS_MEAN||)`.
7. source document IDs, eligible count, K_real, mean norm, real norm을 artifact에 기록.

P/PA M validation은 native train memory(및 PA adapter output)에 같은 규칙을 적용한다.

---

## 4. 데이터·split

| 항목 | 값 |
|---|---|
| train | `split["train"][0:20]` |
| val | `split["val"][5:25]` |
| seeds | 20261108 / 20261109 / 20261110 |
| donors | 5 unique non-self, length-nearest, prefix crop `K=min` |
| donor source duplicates | 제외; duplicate check 결과 기록 |
| target max length | 256 |
| P/PA source max length | 256, target과 독립 flag |
| test 163 | 미사용 |
| P1 | 미사용 |

- F/L: donor length = cache hidden length
- P/PA: donor length = tokenized source length
- M: full real K; donor crop과 다름을 artifact에 명시
- P0 기존 val 20을 재사용; confirmatory holdout으로 부르지 않음

---

## 5. Metrics

### 5.1 Co-primary

1. **aligned full CE**
   - `Δshuffled_full = wrong_full_ce − real_full_ce`
   - mask-free
2. **aligned copy CE**
   - `Δshuffled_copy = wrong_copy_ce − real_copy_ce`
   - as-run mask

`Δ` positive = real memory가 더 좋음.

### 5.2 Secondary

- strict copy mask (`piece_len >= 2`) delta
- `Δshuffled_copy` donor variance
- M:
  - `Δmemfree_full = mean_full_ce − real_full_ce`
  - `Δmemfree_copy = mean_copy_ce − real_copy_ce`
  - M_GLOBAL / M_NORM contrast
- generation telemetry: raw IDs, cap_hit, EOS, rep4, surface_empty
- per-doc distribution: mean, median, p05, p95, top-3 share, leave-top-3-out mean

### 5.3 Copy claim

- as-run coverage .8246/.8351, strict .2427/.2161.
- **`copy`라는 이름은 as-run mask에만 사용**; full CE와 다르면 copy-specific 주장 금지.
- P0에서 Δcopy ≈ Δfull이므로 v0.2는 full CE를 동등 primary로 둔다.

---

## 6. 판정

### 6.1 P/PA validity

```text
P_VALID = mean Δshuffled_copy >= .05
          AND copy CI lower > 0
          AND mean Δshuffled_full > 0
          AND full CI lower > 0

PA_VALID = same criteria on PA
```

- step0 reference: P0 native / zero-LoRA path (same docs/donors)
- step100: trained P/PA
- **P_RETENTION** = `Δ_step100 / Δ_step0` descriptive; reported, not a hidden gate
- P/PA path/shape/finite/mode fail → **ASSAY_INVALID**
- P0 positive이지만 P step100이 `P_VALID`가 아니면 → **REGIME_ERASES_SELECTIVITY**
- PA가 P보다 selectivity를 크게 잃으면 adapter soft-prompt risk로 기록

### 6.2 L signal

```text
L_COPY_SIGNAL = mean Δcopy >= .05
                AND copy CI lower > 0
                AND L > F on copy
                AND 2/3 seeds > 0 on copy

L_FULL_SIGNAL = mean Δfull > 0
                AND full CI lower > 0
                AND L > F on full
                AND 2/3 seeds > 0 on full

L_SIGNAL = L_COPY_SIGNAL AND L_FULL_SIGNAL
```

- copy만 positive이고 full이 아니면 `COPY_ONLY_WEAK`
- full만 positive이고 copy가 아니면 `FULL_ONLY_WEAK`
- 20문서/100update는 screening; confirmatory 아님

### 6.3 M control

```text
M_VALID = P/PA의 M_POS_MEAN에서 real_full < mean_full
          (mean Δmemfree_full > 0 and CI lower > 0)

M_CONTROL_PASS = L의 M_POS_MEAN에서
                 Δmemfree_full > 0 and CI lower > 0
                 AND Δmemfree_copy > 0 and CI lower > 0
```

- M_VALID false → **M_CONTROL_NOT_VALID**; L M 실패를 content-use 부재로 해석 금지
- M_CONTROL_PASS false + L_SIGNAL true → **L_SIGNAL_M_CONTROL_FAIL**
- M_CONTROL_PASS false + no L signal → **NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE**
  - “content use 없음”이 아니라 “이 diagnostic에서 affirmative evidence 없음”

### 6.4 최종 label

| 조건 | label |
|---|---|
| P/PA path/shape/finite/mode fail | **ASSAY_INVALID** |
| P0 positive but P step100 not valid | **REGIME_ERASES_SELECTIVITY** |
| M_VALID false | **M_CONTROL_NOT_VALID** |
| L_SIGNAL true + M_CONTROL_PASS false | **L_SIGNAL_M_CONTROL_FAIL** |
| L_SIGNAL true + M_CONTROL_PASS true | **EXPLORATORY_L_SIGNAL** |
| L_COPY_SIGNAL xor L_FULL_SIGNAL | **COPY_ONLY_WEAK** / **FULL_ONLY_WEAK** |
| otherwise | **INCONCLUSIVE_SMALL_N** |

어떤 label도 B0-B/B1/B2/C를 자동 승인하지 않는다.

---

## 7. 통계·pooling

- 문서 단위 paired bootstrap 1,000회
- seed별 mean을 먼저 만들고 pooled mean을 별도 보고
- `documents_positive`와 `seeds_positive`를 분리
- bootstrap seed와 RNG를 artifact에 기록
- `2/3 seeds`는 seed별 mean >0으로 계산
- heavy-tail:
  - median
  - top-3 share
  - leave-top-3-out mean
  - per-doc scatter/table
- 20-doc bootstrap은 anti-conservative 가능; CI를 확정적 증거로 사용하지 않음

### P0 참고값

| split | mean Δcopy | median | top3 share | real CE | wrong CE |
|---|---:|---:|---:|---:|---:|
| train | 3.7617 | 4.0680 | .4222 | 12.7022 | 16.4639 |
| val | 5.2375 | 2.9739 | .4862 | 13.2352 | 18.4727 |

`ln(250112)=12.43`; P0 real CE는 uniform보다 높다. P0는 **graded content use** 증거가 아니라 native path의 거친 sensitivity 증거다.

---

## 8. DoD

### D1. Code path

- `--mode pm-diagnostic`와 `--pm-arm {f,l,p,pa,mean}` 구현
- P/PA: 64 LoRA modules, base eval, `torch.manual_seed(seed)`
- M: full real K, train-only mean, `m_eligible`, leakage assert
- F/L: prior repair invariants 유지

### D2. Artifacts

`reports/provenance/C5_b0a/pm/{arm}_{seed}.json`:

- arm, seed, train/val IDs
- donor IDs, length, K, crop rule
- `train_mode_policy`
- metric_alignment (built-in vs same-position, atol 1e-5)
- per-doc copy/full
- M: real/mean, eligible IDs, m_eligible, M_GLOBAL/M_NORM
- generation telemetry
- `test_split_used:false`

### D3. Tests

- 기존 54 + PM tests
- P/PA 64 modules/mode/seed
- M no val/target/donor leakage
- M row-permutation/perturbation invariance
- `seeds_positive` vs `documents_positive`
- full CE = built-in loss

### D4. Run integrity

- 12 trained units (F/L/P/PA ×3 seeds), 100 updates
- M eval-only for L, plus P/PA validation
- no test/P1
- no threshold/seed/donor/step change after results
- no B0-B launch

---

## 9. Compute cap

| 항목 | 상한 |
|---|---:|
| F/L/P/PA training | **12 arm-seed**, <=1,200 updates |
| M | eval-only, no training |
| wall time | **<=2 CPU-hours** |
| threads | 6 |
| GPU | 없음 |
| retry/extension | 자동 없음 |

P0와 repair는 이미 완료되어 cap에 포함하지 않는다.

---

## 10. Implementation order

| 단계 | 작업 | 승인 |
|---:|---|---|
| G0 | v0.2 사전등록 승인 | **필요** |
| 1 | PM runner + P/PA/M tests | G0 후 |
| 2 | P/PA smoke + M leakage/invariance tests | G0 후 |
| 3 | 1-seed debug (non-gating) | G0 후 |
| 4 | 3-seed F/L/P/PA run | **별도 gate** |
| 5 | M probe + report | 4 후 |
| 6 | B0-B 여부 decision | **별도 승인** |

1-seed debug는 3-seed 결과가 아니며 gate가 아니다.

---

## 11. Stop conditions

즉시 중단:

- P/PA path/shape/64 modules/mode/seed fail
- M leakage (val/target/donor 사용)
- same-position CE != built-in loss (atol 1e-5)
- non-finite loss
- test 163/P1 접근
- 2 CPU-hour cap 초과
- artifact/donor/K 누락
- P0 positive인데 P step100이 path failure (report; not B0-B)

중단 시 자동으로 다른 arm/B0-B를 진행하지 않는다.

---

## 12. B0-B 경계

Phase 6 결과가 좋아도 B0-B는 자동 승인되지 않는다.

B0-B **검토 조건** (필요조건, 충분조건 아님):

- P/PA valid
- M valid + L M pass
- L_SIGNAL (copy+full)
- heavy-tail robustness (top-3 제거 후에도 방향 유지)
- no leakage/mode/metric failure
- artifact 완전성

B0-B **금지 조건**:

- ASSAY_INVALID
- REGIME_ERASES_SELECTIVITY
- M_CONTROL_NOT_VALID
- L_SIGNAL_M_CONTROL_FAIL
- INCONCLUSIVE_SMALL_N에서 “scale하면 해결”이라는 정당화 없음

test 163/P1/T5Gemma2 상태는 그대로다.

---

## 13. 승인 요청

> **이 v0.2 사전등록으로 `pm-diagnostic` 구현과 non-gating 1-seed debug까지 진행해도 되는가?**

승인 후에도 3-seed 실행은 1-seed debug 결과와 별도 gate에서 확인한다.
