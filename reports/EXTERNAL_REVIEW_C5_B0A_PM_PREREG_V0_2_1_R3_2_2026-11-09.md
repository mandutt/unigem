# C5 Phase 6 v0.2.1-r3.2 — External Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `44bbef6` (`docs: add C5 Phase 6 v0.2.1-r3.2 freeze blocker repair`)
- 대상: `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_2.md` (900줄)
- preflight: `reports/provenance/C5_b0a/m_cohort_preflight.json`
- preflight hash: **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`** (content SHA-256)
- 상태: **r3.2 review. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. Reviewer instructions

1. 이 문서를 처음부터 끝까지 직접 읽어라. 다른 모델의 답을 재사용하지 말라.
2. 저장소 접근이 가능하면 다음 원문을 확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_2.md`
   - `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_1.md`
   - `reports/C5_B0A_PM_PREREG_V0_2_1_R3_1_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/provenance/C5_b0a/m_cohort_preflight.json`
   - `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md`
   - `runner/c5_mt5_lora_b0.py`
   - `eval/tests/test_c5_b0_metric.py`
3. **학습·평가를 실행하지 말라.** test 163을 열지 말라. P1 데이터를 사용하지 말라.
4. **서브에이전트/추가 LLM을 호출하지 말고 직접 검토하라.**
5. 각 Q1~Q12에 대해 **판정(agree / disagree / conditional / defer) + 근거 + 다음 단계 1~3개**를 적어라.
6. 최종 판정은 **STOP / NARROW / CONTINUE** 중 하나로 하고, 승인 범위·금지 범위·compute cap을 명시하라.
7. 결과를 본 뒤 threshold·seed·donor·step·LR을 바꾸자는 제안은 하지 말라. 필요하면 **새 사전등록**으로 분리하라.
8. 보고서 파일을 작성하라:
   `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r3_2_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q12 판정 표와 Must-fix 요약을 포함하라.

---

## 1. TL;DR

> **r3.1은 1 CONTINUE(조건부) / 2 NARROW였다. r3.2는 full threshold `>0` 복원, fixture 16~18, D1 generation/20-train M build ledger, M_NORM 고정 공식, canonical hash, B0-B tail_driven hard gate, small-N/validity precedence, F9~F11을 text-only로 닫는 errata다. 이 문서는 r3.2가 실제로 freeze 가능한지, 구현·D0를 승인할 수 있는지를 묻는다.**

| 항목 | 상태 |
|---|---|
| v0.1 | NARROW 3/3 |
| v0.2 | NARROW 3/3 |
| v0.2.1 | NARROW 3/3 |
| r1 | NARROW 3/3 |
| r2 | NARROW 3/3 |
| r3 | 2 CONTINUE 조건부 / 1 NARROW |
| r3.1 | 1 CONTINUE 조건부 / 2 NARROW |
| **r3.2** | **작성 완료, 미승인** |
| Phase 6 실행 | **없음** |
| P0 | SENSITIVE_POSITIVE, descriptive |
| test 163 | sealed |

---

## 2. r3.1 freeze blockers

1. `L_FULL_SIGNAL`이 `.05`로 회귀.
2. fixture 16/17가 `M_CONTROL_PASS`와 불일치.
3. D1 projection에서 generation/20-train M build 누락.
4. `M_NORM` 고정 공식 제거.
5. hash canonicalization 미정의.
6. B0-B `tail_driven` 우회.
7. small-N/validity precedence 미명시.
8. F9/F10 누락.
9. `§6.4` dangling reference.

---

## 3. r3.2 변경 요약

### 3.1 L predicate threshold 복원

```text
L_COPY_SIGNAL = mean delta_copy >= .05
                AND copy CI lower > 0
                AND paired L>F copy > 0
                AND 2/3 seed copy means > 0

L_FULL_SIGNAL = mean delta_full > 0
                AND full CI lower > 0
                AND paired L>F full > 0
                AND 2/3 seed full means > 0

L_SIGNAL = ANDn(L_COPY_SIGNAL, L_FULL_SIGNAL)
```

- full은 **`>0`**; copy는 **`.05`**.
- threshold 변경 없음.
- `seed_mean` = arm-L shuffled-minus-real endpoint; L−F와 별개.

### 3.2 Fixture 16–18

- Fixture 16:
  - validity VALID, n=20, L both true, m_evaluable=true, p/pa valid, m_valid=true, m_pass_l=true
  - → `EXPLORATORY_L_SIGNAL`
- Fixture 17:
  - L both false, same prerequisites, m_pass_l=true
  - → `MEAN_CONTRAST_ONLY`
- Fixture 18:
  - L both false, m_pass_l=false
  - → `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE`

### 3.3 D1 ledger

D1 phases:

1. train 1 update
2. step0 eval 20 docs ×5 donors
3. final eval 20 docs ×5 donors
4. M builder 20 train + 15 target ×2 variants
5. generation 20 docs ×256 max_new_tokens
6. replay 15 targets ×5 donors ×2 variants
7. load/checkpoint/process/report overhead

`T_proj` includes all terms, ×3 seeds, ×100 updates; ≤96 min.

### 3.4 M_NORM

```text
M_NORM(t) = M_POS_MEAN * ( ||real_prefix_t||_F / ||M_POS_MEAN||_F )
```

- one global train-only mean matrix.
- per-target scalar magnitude.
- `builder_ok` all 15 `||real_prefix_t|| > 0`.
- no per-target matrix.

### 3.5 canonical hash

- checkpoint: sorted keys, adapter+LoRA A/B, dtype/shape/little-endian/contiguous, SHA256.
- replay: sorted `(doc_id, arm, seed, variant, endpoint)` canonical JSON, CE float64, SHA256.
- debug/final checkpoint/final replay 분리.
- golden-vector test.

### 3.6 B0-B

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

- `tail_driven=NA`/true → B0-B 불가.

### 3.7 small-N/validity

- n<15 small-N label 우선.
- validity/control은 별도 축으로 항상 기록.
- F9: p_step NA + p_valid false → `NOT_ASSESSABLE`.
- F10: pa_path NA + pa_valid false → `NOT_ASSESSABLE`.
- F11: n<15 + validity INVALID → small-N label + validity recorded.

---

## 4. P0 기준값

| split | mean Δcopy | CI | mean Δfull | positive docs |
|---|---:|---|---:|---:|
| train | +3.7617 | [1.8917, 5.6050] | +3.5027 | 14/20 |
| val | +5.2375 | [2.5013, 8.0753] | +5.2936 | 18/20 |

한계:

- val median 2.9739, top-3 share .4862
- untrained real CE 12.7/13.2 > ln|V| 12.43
- P0 source_max_length=256; registered M 512
- trained P/PA/L 증거 아님

---

## 5. 검토 질문

### Q1. Total factored contract

r3.2의 validity/control/signal, ANDn, F1~F11, small-N precedence가 실제로 total/executable한가?

### Q2. L predicates / fixtures

`L_COPY >=.05`, `L_FULL >0`, fixture 16~18이 상속 계약과 일치하는가? threshold 회귀가 완전히 닫혔는가?

### Q3. M preflight / cohort

K=753, 15/20 M, val20 signal, endpoint 15/15, full-K 11/20 secondary가 정당한가?

### Q4. M builder / M_NORM / endpoint / replay

`M_NORM(t)` fixed formula, `builder_ok`, endpoint 15×3×4×2, canonical hash, replay equality가 충분한가?

### Q5. PA

PA acquisition 명명, `PA_STEP100_NOT_VALID`, `PA_RETENTION` 비gate, scale/geometry caveat가 충분한가?

### Q6. Cap / D0 / D1

registered 12×100=1,200, D0 0-update, D1 4×1, generation/M build/donor/variants/overhead 포함 T_proj가 산술·승인 경계에서 맞는가?

### Q7. Statistics

n_boot 1,000, CI percentile, bootstrap seed 20261109, documents_positive/seeds_positive, L predicate, 2-of-3, partial endpoint/tail tri-state가 executable한가?

### Q8. 남은 Must-fix

r3.1 freeze blocker 중 아직 닫히지 않은 항목을 ranked list로 제시하라. r3.2가 새로 만든 문제가 있는가?

### Q9. 동결·구현 승인

r3.2를 동결하고 **구현 + unit tests + D0 zero-update mechanics debug**를 승인할 수 있는가? 구현 전 필수 test/contract는 무엇인가?

### Q10. D1 / 3-seed

D1 timing gate와 3-seed를 별도로 유지하는 경계가 충분한가? 3-seed checklist에 빠진 항목은?

### Q11. B0-B

r3.2 결과가 좋아도 B0-B/B1/B2/Stage C를 자동 승인하지 않는 경계가 유지되는가? B0-B predicate를 r3.2 label에 맞게 재진술하라.

### Q12. 최종 판정

**STOP / NARROW / CONTINUE**와 승인 범위를 제시하라.

- r3.2 동결
- 구현 + unit tests
- D0
- D1
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
r3.2 동결:
구현+unit tests:
D0:
D1:
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
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_2.md` | r3.2 |
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_1.md` | r3.1 |
| `reports/C5_B0A_PM_PREREG_V0_2_1_R3_1_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | r3.1 review |
| `reports/provenance/C5_b0a/m_cohort_preflight.json` | M preflight |
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

> **r3.2가 r3.1 freeze blocker를 충분히 닫았는가, 그리고 r3.2 동결·구현·unit tests·D0를 승인할 수 있는가?**

특히 다음을 명시해 달라.

1. L predicate/fixture/canonical hash의 남은 모순
2. M_NORM/D1 ledger/endpoint의 타당성
3. D0/D1/3-seed/B0-B 승인 경계
