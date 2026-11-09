# C5 Phase 6 P/M Prereg v0.2.1 Errata — External Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `672db63` (`docs: add C5 Phase 6 v0.2.1 errata`)
- 직전 v0.2 검토 기준: `918cfa5`
- **검토 기준: Hoplite 스레드 생성 시점의 origin/main HEAD**
- 대상: `docs/plan_c5_b0a_pm_prereg_v0_2_1_errata.md` (434줄)
- 상태: **v0.2.1 errata review. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. Reviewer instructions

1. 이 문서를 처음부터 끝까지 직접 읽어라. 요약·발췌·다른 모델의 답을 근거로 삼지 말라.
2. 저장소 접근이 가능하면 다음 원문을 확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v0_2_1_errata.md`
   - `docs/plan_c5_b0a_pm_prereg_v0_2.md`
   - `reports/C5_B0A_PM_PREREG_V0_2_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_B0A_PM_PREREG_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md`
   - `reports/C5_B0A_REPAIR_2026-11-09.md`
   - `runner/c5_mt5_lora_b0.py`
   - `eval/tests/test_c5_b0_metric.py`
3. **학습·평가를 실행하지 말라.** test 163을 열지 말라. P1 데이터를 사용하지 말라.
4. **서브에이전트/추가 LLM을 호출하지 말고 직접 검토하라.**
5. 각 Q1~Q12에 대해 **판정(agree / disagree / conditional / defer) + 근거 + 권장 다음 단계 1~3개**를 적어라.
6. 최종 판정은 **STOP / NARROW / CONTINUE** 중 하나로 하고, 승인 범위·금지 범위·compute cap을 명시하라.
7. 결과를 본 뒤 threshold·seed·donor·step·LR을 바꾸자는 제안은 하지 말라. 필요하면 **새 사전등록**으로 분리하라.
8. 보고서 파일을 작성하라:
   `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q12 판정 표와 Must-fix 요약을 포함하라.

---

## 1. TL;DR

> **v0.2는 3/3 NARROW였고, v0.2.1은 total decision function, P/PA step0·retention, M_POS_MEAN AND M_NORM, common cohort, statistics, unregistered-seed mechanics debug, cap/artifact를 추가한 errata다. 이 문서는 v0.2.1이 남은 Must-fix를 실제로 닫았는지, 그리고 구현·unit tests·mechanics debug를 승인할 수 있는지를 묻는다.**

| 항목 | 상태 |
|---|---|
| v0.1 | NARROW 3/3 |
| v0.2 | NARROW 3/3, not frozen |
| v0.2.1 | **작성 완료, 미승인** |
| Phase 6 실행 | **없음** |
| P0 | SENSITIVE_POSITIVE, descriptive |
| test 163 | sealed |

---

## 2. v0.2 review의 남은 Must-fix

v0.2 3-AI review의 공통 지적:

1. **Decision table이 total function이 아님**
   - `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE`가 §6.3에만 있고 §6.4 표에는 없음
   - PA가 label table에 없음
   - P/PA interaction cell 없음
   - precedence가 L_SIGNAL을 숨길 수 있음
   - `REGIME_ERASES_SELECTIVITY`가 인과적 이름

2. **P/PA 경계**
   - P floor `.05`는 P0 mean의 약 1%
   - PA step0 reference 없음
   - PA_VALID가 M_VALID/decision에 일관되게 연결되지 않음
   - P/PA LR·movement·retention contract 없음

3. **M 경계**
   - M_POS_MEAN이 norm-shrunk/OOD
   - M_CONTROL_PASS가 M_POS_MEAN만 사용
   - M_VALID quantifier/eligible target cohort/checkpoint persistence 불명확
   - `eligible >= 10`은 train contributor 수; target cohort와 다름

4. **통계**
   - seed-averaged per-doc Δ에 document bootstrap
   - L>F paired, 2/3 seeds, `documents_positive` vs `seeds_positive`
   - copy/full missingness

5. **Debug**
   - registered seed 100-step 결과가 3-seed gate 전에 노출될 수 있음
   - mechanics-only protocol/commit hash/timing 필요

6. **Cap/artifact**
   - wall-clock vs CPU-hour, debug 포함, checkpoint/manifest.

---

## 3. v0.2.1 변경 요약

### 3.1 Total decision function

독립 flag vector:

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

Precedence:

```text
1 ASSAY_INVALID
2 P_STEP100_NOT_VALID (path fail)
3 P_STEP100_NOT_VALID (stat fail)
4 ADAPTER_REGIME_LOSS
5 M_NOT_EVALUABLE
6 M_CONTROL_NOT_VALID
7 L_SIGNAL_M_CONTROL_FAIL
8 EXPLORATORY_L_SIGNAL
9 COPY_ONLY_WEAK
10 FULL_ONLY_WEAK
11 MEAN_CONTRAST_ONLY
12 NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE
13 INCONCLUSIVE_SMALL_N
```

- L flag는 headline이 validity failure여도 보존
- `REGIME_ERASES_SELECTIVITY` 삭제; `P_STEP100_NOT_VALID` 사용
- P/PA interaction table:
  - T/T 정상
  - T/F ADAPTER_REGIME_LOSS
  - F/T P_STEP100_NOT_VALID
  - F/F P_STEP100_NOT_VALID

### 3.2 P/PA

- optimizer AdamW, wd .01
- adapter LR 1e-3 (PA), LoRA LR 1e-4
- 100 updates, batch 1, cyclic train order, clip 1.0
- `make_adapter(seed)` 후 LoRA init 직전 `torch.manual_seed(seed)`
- P step0: native + zero-LoRA
- **PA step0: native + random adapter + zero-LoRA, 별도 실행**
- movement fields: step0/step100 real/wrong CE, train CE first/last/last10, LoRA B norm, adapter delta norm, LR
- P_RETENTION/PA_RETENTION descriptive; denominator null guard

### 3.3 M

- L real reference: full real K
- M_POS_MEAN primary, M_NORM **pass condition**, M_GLOBAL secondary
- M_NORM scale: whole K×512 Frobenius norm
- M_CONTROL_PASS_L = M_PASS_POS_L **AND** M_PASS_NORM_L
- M_VALID = P and PA both pass POS and NORM
- eligible contributor ≥10
- common M cohort ≥15/20
- `M_NOT_EVALUABLE` / `M_PASS_NORM_CONFOUNDED`
- checkpoint hash

### 3.4 Statistics

- document-level bootstrap on seed-averaged per-doc Δ
- L>F paired per-document
- 2/3 seeds seed-level means
- `documents_positive` separate
- copy/full common subset
- heavy-tail median/top-3/leave-top-3-out

### 3.5 Debug

- unregistered seed **20261111**
- F/L/P/PA max **5 updates**
- mechanics only
- no M pass/fail labels
- no registered seed 100-step result
- commit hash freeze
- debug included in cap

### 3.6 Cap

- 12 trained units
- ≤1,200 updates
- wall-clock **≤2h**, 6 threads, no GPU
- debug included
- manifests/checkpoint/timing

---

## 4. P0 기준값

| split | mean Δcopy | CI | mean Δfull | positive docs |
|---|---:|---|---:|---:|
| train | +3.7617 | [1.8917, 5.6050] | +3.5027 | 14/20 |
| val | +5.2375 | [2.5013, 8.0753] | +5.2936 | 18/20 |

한계:

- val median 2.9739, top-3 share .4862
- untrained real CE 12.7/13.2 > ln|V| 12.43
- P0는 graded content use가 아니라 native path sensitivity
- 20 val은 confirmatory holdout 아님

---

## 5. 검토 질문

### Q1. Total decision function

v0.2.1의 flag vector/precedence/13-label table이 total function이며, L_SIGNAL을 숨기지 않는가? 빠진 cell/모순은 무엇인가?

### Q2. P/PA contract

P/PA step0, PA random-adapter baseline, retention/movement fields, `ADAPTER_REGIME_LOSS`가 adapter-regime confound를 충분히 다루는가? PA_VALID를 M_VALID/decision에 연결한 방식이 맞는가?

### Q3. P gate

`.05` + full/copy CI 조건이 v0.2.1에서도 약한가? P_VALID를 “post-training sensitivity retention”으로 제한한 것이 충분한가?

### Q4. M contract

M_POS_MEAN AND M_NORM, M_VALID(P AND PA), common cohort ≥15/20, eligible≥10, checkpoint persistence가 leakage-free이고 충분한가? M_NORM scale/결측 처리가 맞는가?

### Q5. Statistics

seed-averaged per-doc bootstrap, L>F paired, 2/3 seeds, documents_positive/seeds_positive 분리, copy/full common subset이 executable한가? 빠진 missingness/threshold가 있는가?

### Q6. Debug

unregistered seed 20261111, max 5 updates, mechanics-only, no labels, commit hash, cap 포함이 registered-seed 결과 노출을 막는가? debug 허용 범위가 적절한가?

### Q7. Cap/artifact

12 units, 1200 updates, wall-clock 2h, 6 threads, manifests/checkpoint/timing이 현실적이고 검증 가능한가? generation/M 비용이 cap에 충분히 반영됐는가?

### Q8. 남은 Must-fix

v0.2 3-AI Must-fix 중 아직 닫히지 않은 항목을 ranked list로 제시하라. v0.2.1이 새로 만든 문제가 있는가?

### Q9. 구현 승인

v0.2.1 동결 후 **구현 + unit tests**를 승인할 수 있는가? 구현 전 반드시 있어야 할 test/contract는 무엇인가?

### Q10. 1-seed mechanics debug

구현·unit tests 후 **unregistered-seed mechanics debug**를 승인할 수 있는가? debug 결과를 3-seed gate로 오인하지 않도록 어떤 artifact가 필요한가?

### Q11. 3-seed / B0-B

3-seed 실행 조건과 B0-B proposal 조건을 구분해 달라. v0.2.1 결과가 좋아도 B0-B를 자동 승인하지 않는 경계가 유지되는가?

### Q12. 최종 판정

**STOP / NARROW / CONTINUE**와 승인 범위를 제시하라.

- v0.2.1 동결
- 구현 + unit tests
- mechanics debug
- 3-seed
- 금지 범위
- 최대 compute
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
v0.2.1 동결:
구현+unit tests:
mechanics debug:
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
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_errata.md` | v0.2.1 |
| `docs/plan_c5_b0a_pm_prereg_v0_2.md` | v0.2 |
| `reports/C5_B0A_PM_PREREG_V0_2_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | v0.2 review |
| `reports/C5_B0A_PM_PREREG_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | v0.1 review |
| `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md` | P0 |
| `runner/c5_mt5_lora_b0.py` | runner |
| `eval/tests/test_c5_b0_metric.py` | tests |

---

## 8. 금지

- 학습·평가 실행 금지
- test 163 열람 금지
- P1 사용 금지
- repository 수정 금지 (지정 report 파일만)
- subagent/추가 LLM 호출 금지
- 결과를 본 뒤 threshold/seed/donor/step/LR 변경 금지
- Phase 6/B0-B/B1/B2/Stage C 자동 진행 금지

---

## 9. 요청하는 최종 판단

> **v0.2.1이 v0.2 3-AI Must-fix를 충분히 닫았는가, 그리고 v0.2.1 동결·구현·unit tests·unregistered-seed mechanics debug를 승인할 수 있는가?**

특히 다음을 명시해 달라.

1. total decision function에 남은 cell/모순
2. P/PA step0·M_POS_MEAN+M_NORM·common cohort의 충분성
3. 3-seed와 B0-B를 자동 승인하지 않는 경계
