# C5 B0-A Phase 6 P/M Prereg v0.2 — External Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `8c4f197` (`docs: add C5 Phase 6 P/M prereg v0.2`)
- 직전 v0.1 검토 기준: `26e334a`
- **검토 기준: Hoplite 스레드 생성 시점의 origin/main HEAD**
- 대상: `docs/plan_c5_b0a_pm_prereg_v0_2.md` (405줄)
- 상태: **v0.2 review request. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6 / B0-B / B1 / B2 / Stage C: **미승인**

---

## 0. Reviewer instructions

1. 이 문서를 처음부터 끝까지 직접 읽어라. 요약·발췌·다른 모델의 답을 근거로 삼지 말라.
2. 저장소 접근이 가능하면 다음 원문을 확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v0_2.md`
   - `docs/plan_c5_b0a_pm_prereg_v0_1.md` (비교용)
   - `reports/C5_B0A_PM_PREREG_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md`
   - `reports/C5_B0A_REPAIR_2026-11-09.md`
   - `runner/c5_mt5_lora_b0.py`
   - `eval/tests/test_c5_b0_metric.py`
3. **학습·평가를 실행하지 말라.** test 163을 열지 말라. P1 데이터를 사용하지 말라.
4. **서브에이전트/추가 LLM을 호출하지 말고 직접 검토하라.**
5. 각 Q1~Q12에 대해 **판정(agree / disagree / conditional / defer) + 근거 + 권장 다음 단계 1~3개**를 적어라.
6. 최종 판정은 **STOP / NARROW / CONTINUE** 중 하나로 하고, 승인 범위·금지 범위·compute cap을 명시하라.
7. 결과를 본 뒤 threshold·seed·donor·step을 바꾸자는 제안은 하지 말라. 필요하면 **새 사전등록**으로 분리하라.
8. 보고서 파일을 작성하라:
   `docs/hoplite/c5_b0a_pm_prereg_v0_2_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q12 판정 표와 Must-fix 요약을 포함하라.

---

## 1. TL;DR

> **v0.1은 3/3 NARROW였다. v0.2는 그 Must-fix를 반영해 P gate를 강화하고 PA arm, M validation, decision label, full CE co-primary, heavy-tail reporting을 추가했다. 이 문서는 v0.2가 구현·1-seed debug를 승인할 만큼 충분한지, 아니면 아직 Must-fix가 남았는지를 묻는다.**

| 항목 | 상태 |
|---|---|
| v0.1 3-AI review | **NARROW 3/3** |
| v0.1 구현 | 미승인 |
| v0.2 | **작성 완료, 미승인** |
| P0 native sanity | SENSITIVE_POSITIVE train/val |
| F/L repair | 완료, 54 tests |
| Phase 6 실행 | **없음** |
| test 163 | sealed |

---

## 2. 직전 v0.1 review의 결론

### 2.1 판정

- GLM 5.3 Flash max: **NARROW**
- Sonnet 5.5 high: **NARROW**
- Sol 6.1 high: **NARROW**
- 공통: P/M/F/L 분리 구조는 수용. v0.1은 구현 준비 미완료.

### 2.2 공통 Must-fix

| # | v0.1 문제 | v0.2 조치 |
|---|---|---|
| 1 | P_POSITIVE near-vacuous; P0 already +3.76/+5.24 | P에 `.05` + full + copy + CI; step0/step100; PA arm |
| 2 | P는 F/L과 다른 regime | **PA** = native memory + adapter + LoRA 추가 |
| 3 | M real reference 불명확 | full real K 고정; donor crop과 분리 |
| 4 | M norm/OOD, eligible bias | M_POS_MEAN/M_GLOBAL/M_NORM, eligible>=10, m_eligible |
| 5 | M position-wise 의미 약함 | M_GLOBAL/M_NORM secondary, position claim 제한 |
| 6 | M이 P/PA에서 미검증 | P/PA M validation, 실패 시 M_NOT_VALID |
| 7 | Label overclaim | `NO_AFFIRMATIVE...`, `M_CONTROL_NOT_VALID`, `REGIME_ERASES_SELECTIVITY`, `L_SIGNAL_M_CONTROL_FAIL` |
| 8 | copy mask가 copy-specific 아님 | aligned full CE co-primary; copy secondary; strict exploratory |
| 9 | `seeds_positive` mislabel | documents vs seeds 분리 |
| 10 | 2/3 seeds 미구현 | seed별 mean 계산·기록 |
| 11 | P/PA seed 미고정 | `torch.manual_seed(seed)` before LoRA init |
| 12 | cap 모호 | 12 trained units, ≤1,200 updates, ≤2 CPU-h |

---

## 3. v0.2 설계

### 3.1 Arms

| arm | memory | adapter | decoder LoRA | trainable | 역할 |
|---|---|---|---|---|---|
| F | EG2 native layer19 | yes | no | adapter | adapter-only |
| L | EG2 native layer19 | yes | 64 | adapter+LoRA | EG2 bridge |
| P | native mT5 encoder | no | 64 | LoRA | native positive control |
| PA | native mT5 encoder | yes | 64 | adapter+LoRA | adapter soft-prompt control |
| M | train-only mean | — | — | no training | L memory replacement |

- F/L/P/PA = **12 trained units** (4 arms × 3 seeds)
- M = **evaluation-only**
- 20 train / 20 val (`val[5:25]`)
- 100 updates, seeds 20261108/09/10
- ≤2 CPU-hours, 6 threads, no GPU

### 3.2 P/PA

P:

- native mT5 encoder memory
- adapter 없음
- decoder LoRA 64
- `torch.manual_seed(seed)` before LoRA init
- base eval, LoRA train

PA:

- native mT5 encoder memory
- adapter `make_adapter(seed)`
- decoder LoRA 64
- base eval, adapter+LoRA train

P는 native path의 metric/LoRA pipeline validity, PA는 adapter가 selectivity를 보존/파괴하는지 확인한다.

### 3.3 M

L checkpoint 고정.

- real reference: **full real memory K_real**
- mean source: **train 20 문서의 adapter memory만**
- target val/summary/donor 사용 금지
- `len(h_i) >= K_real` eligible; eligible <10 → `m_eligible=false`
- `M_POS_MEAN` primary
- `M_GLOBAL`, `M_NORM` secondary
- **P/PA M validation**; P/PA M 실패 시 `M_NOT_VALID`

### 3.4 Metrics

Co-primary:

1. aligned `Δshuffled_full` (mask-free)
2. aligned `Δshuffled_copy` (as-run mask)

Secondary:

- strict mask
- M `Δmemfree_full`, `Δmemfree_copy`
- M_GLOBAL/M_NORM
- generation telemetry
- per-doc median, p05/p95, top-3 share, leave-top-3-out

### 3.5 P/PA validity

```text
P_VALID = mean Δcopy >= .05
          AND copy CI lower > 0
          AND mean Δfull > 0
          AND full CI lower > 0
```

PA_VALID same.

- P0 is step0 reference.
- step100 trained P/PA.
- P_RETENTION descriptive.
- P0 positive but P step100 invalid → **REGIME_ERASES_SELECTIVITY**.
- path/shape/finite/mode fail → **ASSAY_INVALID**.

### 3.6 L signal

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

- copy-only → `COPY_ONLY_WEAK`
- full-only → `FULL_ONLY_WEAK`

### 3.7 M control

```text
M_VALID = P/PA M_POS_MEAN real < mean
          (Δmemfree_full > 0 and CI lower > 0)

M_CONTROL_PASS = L M_POS_MEAN
                 Δmemfree_full > 0 and CI lower > 0
                 AND Δmemfree_copy > 0 and CI lower > 0
```

- M_VALID false → `M_CONTROL_NOT_VALID`
- L_SIGNAL + M fail → `L_SIGNAL_M_CONTROL_FAIL`
- no L signal + M fail → `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE`

### 3.8 Labels

| 조건 | label |
|---|---|
| path/shape/finite/mode fail | `ASSAY_INVALID` |
| P0 positive but P step100 invalid | `REGIME_ERASES_SELECTIVITY` |
| M_VALID false | `M_CONTROL_NOT_VALID` |
| L_SIGNAL + M fail | `L_SIGNAL_M_CONTROL_FAIL` |
| L_SIGNAL + M pass | `EXPLORATORY_L_SIGNAL` |
| copy xor full | `COPY_ONLY_WEAK` / `FULL_ONLY_WEAK` |
| otherwise | `INCONCLUSIVE_SMALL_N` |

---

## 4. P0 근거와 그 한계

P0 native sanity:

| split | mean Δcopy | 95% CI | mean Δfull | positive docs |
|---|---:|---|---:|---:|
| train | +3.7617 | [1.8917, 5.6050] | +3.5027 | 14/20 |
| val | +5.2375 | [2.5013, 8.0753] | +5.2936 | 18/20 |

하지만:

- val median Δcopy **2.9739** (mean 5.2375)
- top-3/20 share **.4862**
- train top-3 share **.4222**
- untrained real CE **12.7022 / 13.2352** > `ln(250112)=12.43`
- P0는 **graded content use**가 아니라 native path의 거친 sensitivity다.

v0.2는 이 한계를 P gate 강화와 heavy-tail reporting으로 반영했다.

---

## 5. 검토 질문

### Q1. P gate

v0.2의 P_VALID(`Δcopy ≥ .05`, copy/full CI lower>0)가 v0.1의 near-vacuous gate를 충분히 고쳤는가? 여전히 약한가?

### Q2. PA arm

PA(native memory + adapter + LoRA)가 P와 F/L 사이의 adapter soft-prompt confound를 분리하기에 충분한가? PA를 P/PA gate에 어떻게 포함해야 하는가?

### Q3. M real reference

M의 real reference를 full real K로 고정하고 donor crop을 secondary로 분리한 것이 타당한가? 기존 `evaluate_arm`의 donor-cropped real CE와 어떻게 비교해야 하는가?

### Q4. Mean-memory 정의

train-only, len>=K, eligible>=10, M_POS_MEAN/M_GLOBAL/M_NORM, P/PA validation이 leakage-free이고 negative control로 충분한가? 빠진 invariant가 있는가?

### Q5. Decision label

v0.2의 label table(`REGIME_ERASES_SELECTIVITY`, `M_CONTROL_NOT_VALID`, `L_SIGNAL_M_CONTROL_FAIL`, `NO_AFFIRMATIVE...`)이 overclaim 없이 일관적인가? 빠진 cell/모순이 있는가?

### Q6. Copy vs full

aligned full CE co-primary와 as-run copy secondary가 v0.1의 “copy-specific” overclaim을 충분히 제한하는가? `L_SIGNAL`이 copy+full 둘 다를 요구하는 것이 과도한가?

### Q7. Heavy-tail / power

P0 median 2.97, val top-3 share .486, n=20, 12 trained units, 3 seeds를 볼 때 v0.2의 diagnostic이 검출 가능한 결론과 금지해야 할 결론을 구분해 달라.

### Q8. Compute·implementation

12 trained units × 100 updates, M eval-only, ≤2 CPU-hours, 6 threads가 현실적인가? `pm-diagnostic` 코드가 아직 없다는 전제에서 Must-fix를 ranked list로 제시하라.

### Q9. P/PA/M tests

P/PA 64 modules, seed, mode, M leakage, row-permutation/perturbation invariance, `documents_positive` vs `seeds_positive` 중 구현 전 반드시 필요한 test는 무엇인가?

### Q10. 1-seed debug

v0.2 승인 후 non-gating 1-seed debug를 어디까지 허용해야 하는가? 3-seed gate로 넘어가기 위한 artifact/판정 조건은 무엇인가?

### Q11. B0-B 경계

v0.2 결과가 L_SIGNAL + M pass여도 B0-B 300/95를 자동 승인하지 않는 것이 맞는가? B0-B proposal의 필요조건을 명시하라.

### Q12. 최종 판정

**STOP / NARROW / CONTINUE**와 승인 범위를 제시하라.

- v0.2 승인 여부
- 구현·1-seed debug 승인 여부
- 3-seed 승인 여부
- 금지 범위
- 최대 compute
- 다음 decision gate
- test 163 지위

---

## 6. 답변 형식

각 Q1~Q12:

```text
Qn.
- 판정: agree / disagree / conditional / defer
- 근거: 이 문서·artifact의 구체 수치
- 다음 단계: 1~3개
```

마지막에:

```text
최종 판정: STOP / NARROW / CONTINUE
v0.2:
구현·1-seed debug:
3-seed:
금지 범위:
최대 compute:
Must-fix (ranked):
잘못된 전제:
```

---

## 7. Artifacts

| 경로 | 내용 |
|---|---|
| `docs/plan_c5_b0a_pm_prereg_v0_2.md` | v0.2 |
| `docs/plan_c5_b0a_pm_prereg_v0_1.md` | v0.1 |
| `reports/C5_B0A_PM_PREREG_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | v0.1 3-AI 종합 |
| `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md` | P0 |
| `reports/C5_B0A_REPAIR_2026-11-09.md` | repair |
| `runner/c5_mt5_lora_b0.py` | runner |
| `eval/tests/test_c5_b0_metric.py` | tests |

---

## 8. 금지

- 학습·평가 실행 금지
- test 163 열람 금지
- P1 데이터 사용 금지
- repository 수정 금지 (지정 report 파일만)
- subagent/추가 LLM 호출 금지
- 결과를 본 뒤 threshold/seed/donor/step 변경 금지
- Phase 6/B0-B/B1/B2/Stage C 자동 진행 금지

---

## 9. 요청하는 최종 판단

> **v0.2가 v0.1 3-AI review의 Must-fix를 충분히 닫았는가, 그리고 구현·non-gating 1-seed debug를 승인할 수 있는가?**

특히 다음을 명시해 달라.

1. P gate와 PA arm이 충분한가.
2. M full-reference/mean/P·PA validation이 충분한가.
3. 아직 남은 Must-fix와 3-seed 금지 조건은 무엇인가.
