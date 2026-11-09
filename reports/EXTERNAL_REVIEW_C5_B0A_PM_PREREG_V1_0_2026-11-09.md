# C5 Phase 6 v1.0 — External Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `631e180`
- 대상: `docs/plan_c5_b0a_pm_prereg_v1_0.md` (1,220줄)
- golden vectors: `docs/hoplite/c5_b0a_pm_prereg_v1_0_2026-11-09/golden_vectors.json`
- preflight: `reports/provenance/C5_b0a/m_cohort_preflight.json`
- preflight hash: **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`**
- 상태: **v1.0 review. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. Reviewer instructions

1. 이 문서를 처음부터 끝까지 직접 읽어라. 다른 모델의 답을 재사용하지 말라.
2. 저장소 접근이 가능하면 다음 원문을 확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v1_0.md`
   - `docs/hoplite/c5_b0a_pm_prereg_v1_0_2026-11-09/golden_vectors.json`
   - `reports/C5_B0A_PM_PREREG_V0_2_1_R3_4_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_4.md` (historical)
   - `reports/provenance/C5_b0a/m_cohort_preflight.json`
   - `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md`
   - `runner/c5_mt5_lora_b0.py`
   - `eval/tests/test_c5_b0_metric.py`
3. **학습·평가를 실행하지 말라.** test 163을 열지 말라. P1 데이터를 사용하지 말라.
4. **서브에이전트/추가 LLM을 호출하지 말고 직접 검토하라.**
5. 각 Q1~Q13에 대해 **판정(agree / disagree / conditional / defer) + 근거 + 다음 단계 1~3개**를 적어라.
6. 최종 판정은 **STOP / NARROW / CONTINUE** 중 하나로 하고, 승인 범위·금지 범위·compute cap을 명시하라.
7. 결과를 본 뒤 threshold·seed·donor·step·LR을 바꾸자는 제안은 하지 말라. 필요하면 **새 사전등록**으로 분리하라.
8. 보고서 파일을 작성하라:
   `docs/hoplite/c5_b0a_pm_prereg_v1_0_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q13 판정 표와 Must-fix 요약을 포함하라.

---

## 1. TL;DR

> **v1.0은 r3.1~r3.4 errata chain을 대체하는 첫 self-contained normative spec이다. r3.4는 3/3 NARROW였고, v1.0은 그 Must-fix(variant×memory_kind, tail variant, P/PA cohort, replay domain/hash, L binding, F/L K scope, PA_VALID, full-K, top3, documents_positive, golden digests)를 통합했다. 이 문서는 v1.0이 실제로 freeze 가능한지, 구현·D0를 승인할 수 있는지를 묻는다.**

| 항목 | 상태 |
|---|---|
| v0.1~r3.4 | NARROW chain |
| r3.4 | **3/3 NARROW** |
| **v1.0** | **작성 완료, 미승인** |
| Phase 6 실행 | **없음** |
| P0 | SENSITIVE_POSITIVE, descriptive |
| test 163 | sealed |

---

## 2. v1.0의 핵심

### 2.1 단일 권위

- v1.0 = 유일한 구현 권위.
- r3.4 및 이전 P/M 문서 = traceability only.
- freeze 후 = v1.0 + numbered ERRATA only.

### 2.2 r3.4 Must-fix 반영

- **variant×memory_kind table**:
  - `M_POS_MEAN`: control = global mean, real = `real_prefix_t`
  - `M_NORM`: control = magnitude-matched mean, real = `real_prefix_t`
- **`tail_driven` = signal tail**:
  - arm L, copy, shuffled donor, variant NA, 15 docs
  - M tails descriptive only
- **P/PA validity = 20 native docs**; L/F = 15 common.
- **replay domains**:
  - phase 5 donor-free 120/arm-seed
  - phase 7 donor diagnostic 600/arm-seed
  - debug hash vs final hash separated
- **L binding**:
  - `l_copy_signal := L_COPY_SIGNAL`
  - `l_full_signal := L_FULL_SIGNAL`
- **F/L K=753 M-only**:
  - training/eval donor-crop
  - generation 20×256
- **PA_VALID** 20 native docs, direct definition.
- **`full_k_secondary`** historical only.
- **top3 absolute** `.4335` gate; signed `.4862` descriptive.
- **`documents_positive`** defined.
- **golden vectors**:
  - state `43ecb58e…d65712`
  - empty `e3b0c442…b7852b855`
  - replay `c43ea35c…f7851667`

---

## 3. P0 기준값

| split | mean Δcopy | CI | mean Δfull | positive docs |
|---|---:|---|---:|---:|
| train | +3.7617 | [1.8917, 5.6050] | +3.5027 | 14/20 |
| val | +5.2375 | [2.5013, 8.0753] | +5.2936 | 18/20 |

한계:

- val median 2.9739
- signed top3 share .4862; absolute .43355
- untrained real CE 12.7/13.2 > ln|V| 12.43
- P0 source_max_length=256; M 512
- trained P/PA/L 증거 아님

---

## 4. 검토 질문

### Q1. Self-containedness

v1.0이 이전 문서 없이 구현 가능한가? 정의/참조 누락, 순환 참조, stale chain 참조가 없는가?

### Q2. Decision contract

validity/control/signal, ANDn, F1–F11, L 9-pair, fixtures 16–18, small-N이 total/executable한가?

### Q3. M variant × memory_kind

`M_POS_MEAN`/`M_NORM` control/real table, `M_PASS_POS/NORM`, endpoint 1,440, target 96회, exact key set이 충분한가?

### Q4. M builder / M_NORM / endpoint / replay

F/L/P/PA builder, P identity, `real_prefix_t`, `M_NORM(t)`, replay phase 5/7, donor_sort, debug/final hash 분리가 충분한가?

### Q5. F/L memory length scope

`K=753` M-only, training/eval donor-crop, generation 20×256이 4 train/5 val short docs를 올바르게 처리하는가?

### Q6. P/PA

P/PA 20 native cohort, `P_VALID`/`PA_VALID`, PA veto, `PA_RETENTION` non-gate, geometry caveat가 충분한가?

### Q7. Statistics / tail

n_boot 1000, seed 20261109, documents_positive, 2/3 registered, signal tail, absolute top3, tie rule, missing seed NA가 executable한가?

### Q8. D0/D1/cap

D0 0-update, D1 4 arms ×1 debug seed, 8 phases, phase 5 120, phase 7 600, T_proj ≤96이 산술·승인 경계에서 맞는가?

### Q9. Hash/golden

state/replay canonical frame, golden digests, donor_sort, tolerance vs exact hash가 충분한가?

### Q10. 남은 Must-fix

v1.0이 r3.4 Must-fix를 실제로 닫았는가? 새로 만든 문제가 있는가? ranked list로 제시하라.

### Q11. 동결·구현 승인

v1.0을 동결하고 **구현 + unit tests + D0 zero-update mechanics debug**를 승인할 수 있는가? 구현 전 필수 test는 무엇인가?

### Q12. B0-B / D1 / 3-seed

D1/3-seed/B0-B/B1/B2/Stage C 경계가 충분한가? B0-B predicate를 v1.0 label에 맞게 재진술하라.

### Q13. 최종 판정 및 v1.0 freeze

**STOP / NARROW / CONTINUE**와 승인 범위를 제시하라.

- v1.0 freeze
- 구현+unit tests
- D0
- D1
- 3-seed
- 금지 범위
- 최대 compute
- test 163 지위
- v1.0이 정말 단일 구현 권위로 충분한가

---

## 5. 답변 형식

각 Q1~Q13:

```text
Qn.
- 판정: agree / disagree / conditional / defer
- 근거: 이 문서·artifact의 구체 수치
- 다음 단계: 1~3개
```

마지막에:

```text
최종 판정: STOP / NARROW / CONTINUE
v1.0 freeze:
구현+unit tests:
D0:
D1:
3-seed:
금지 범위:
최대 compute:
Must-fix (ranked):
v1.0 self-contained:
잘못된 전제:
```

---

## 6. Artifacts

| 경로 | 내용 |
|---|---|
| `docs/plan_c5_b0a_pm_prereg_v1_0.md` | v1.0 |
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_2026-11-09/golden_vectors.json` | golden |
| `reports/C5_B0A_PM_PREREG_V0_2_1_R3_4_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | r3.4 review |
| `reports/provenance/C5_b0a/m_cohort_preflight.json` | preflight |
| `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md` | P0 |
| `runner/c5_mt5_lora_b0.py` | runner |
| `eval/tests/test_c5_b0_metric.py` | tests |

---

## 7. 금지

- 학습·평가 실행 금지
- test 163 열람 금지
- P1 사용 금지
- repository 수정 금지 (지정 report 파일만)
- subagent/추가 LLM 호출 금지
- 결과를 본 뒤 threshold/seed/donor/step/LR 변경 금지
- Phase 6/B0-B/B1/B2/Stage C 자동 진행 금지

---

## 8. 요청하는 최종 판단

> **v1.0이 r3.4 Must-fix를 실제로 닫고 self-contained 구현 권위로 freeze 가능한가, 그리고 구현·unit tests·D0를 승인할 수 있는가?**

특히 다음을 명시해 달라.

1. variant × memory_kind / replay / P/PA cohort의 실행 가능성
2. F/L K scope / L binding / tail 정의의 정합성
3. D0/D1/3-seed/B0-B 승인 경계
