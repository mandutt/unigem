# C5 Phase 6 v1.0.1 — External Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `7ecf973`
- 대상: `docs/plan_c5_b0a_pm_prereg_v1_0_1.md` (1,431줄)
- golden vectors: `docs/hoplite/c5_b0a_pm_prereg_v1_0_2026-11-09/golden_vectors.json`
- preflight: `reports/provenance/C5_b0a/m_cohort_preflight.json`
- preflight hash: **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`**
- 상태: **v1.0.1 review. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. Reviewer instructions

1. 이 문서를 처음부터 끝까지 직접 읽어라. 다른 모델의 답을 재사용하지 말라.
2. 저장소 접근이 가능하면 다음 원문을 확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v1_0_1.md`
   - `docs/hoplite/c5_b0a_pm_prereg_v1_0_2026-11-09/golden_vectors.json`
   - `reports/C5_B0A_PM_PREREG_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0.md` (historical)
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
   `docs/hoplite/c5_b0a_pm_prereg_v1_0_1_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q13 판정 표와 Must-fix 요약을 포함하라.

---

## 1. TL;DR

> **v1.0은 3/3 NARROW였다. v1.0.1은 P/PA cohort를 mixed domain(F/L 15 common, P/PA 20 native)으로 통일하고, measurement semantics·donor rule·shuffled donor·path flags·replay procedure·M control digest·bindings를 추가한 self-contained repair다. 이 문서는 v1.0.1이 freeze 가능한지, 구현·D0를 승인할 수 있는지를 묻는다.**

| 항목 | 상태 |
|---|---|
| r3.4 | 3/3 NARROW |
| v1.0 | 3/3 NARROW |
| **v1.0.1** | **작성 완료, 미승인** |
| Phase 6 실행 | **없음** |
| P0 | SENSITIVE_POSITIVE, descriptive |
| test 163 | sealed |

---

## 2. v1.0.1의 핵심

### 2.1 Mixed M domain

- F/L: **15 common**
- P/PA: **20 native (15 common + 5 native-only)**
- primary records = **1,680**
  - common: 15 × 96 = 1,440
  - native-only: 5 × 48 = 240
- D1 phase 5 = **560**
  - F/L 120 each
  - P/PA 160 each
- phase 7 = 15-common diagnostic **600/arm-seed**
- `m_valid` P/PA 20 native; `m_pass_l` L 15 common.

### 2.2 Measurement semantics

- mT5-small, T5Tokenizer, `summarize: `, source 512, target 256.
- built-in same-position CE; no extra shift.
- copyable mask, copy CE, copy tokens ≥5.
- donor rule: val20 exclude self, `(abs len diff, doc_id)`, 5 donors, donor_id 0..4.
- `shuffled` = wrong-donor memory, mean over 5 donors.
- adapter random init with seed; LoRA A kaiming/B zeros.
- greedy generation 256.

### 2.3 Path flags

- `assay_path_ok`
- `p0_path_ok`
- `p_step100_path_ok`
- `pa_step100_path_ok`
- `test_split_used`

### 2.4 Bindings

```text
P_VALID = ANDn(P_POS_PASS, P_NORM_PASS)
PA_VALID = ANDn(PA_POS_PASS, PA_NORM_PASS)

p_valid := P_VALID
pa_valid := PA_VALID
m_pass_pos_p := P_POS_PASS
m_pass_norm_p := P_NORM_PASS
m_pass_pos_pa := PA_POS_PASS
m_pass_norm_pa := PA_NORM_PASS
```

### 2.5 Replay / hash

- replay procedure 8단계.
- phase 5 primary **1,680 keys**, exact coverage.
- phase 7 diagnostic 600/arm-seed.
- `debug_replay_hash` vs `final_replay_hash` separated.
- `control_digest` includes `M_POS_MEAN` and `M_NORM/t`.
- golden digests unchanged:
  - state `43ecb58e…d65712`
  - empty `e3b0c442…b7852b855`
  - replay `c43ea35c…f7851667`

### 2.6 기타

- training forward real memory only; donor-crop eval only.
- `full_k_secondary` historical only.
- calibration axis 3^6.
- `endpoint_ok = §9.5`.

---

## 3. P0 기준값

| split | mean Δcopy | CI | mean Δfull | positive docs |
|---|---:|---|---:|---:|
| train | +3.7617 | [1.8917, 5.6050] | +3.5027 | 14/20 |
| val | +5.2375 | [2.5013, 8.0753] | +5.2936 | 18/20 |

한계:

- val median 2.9739
- signed top3 .4862; absolute .43355
- untrained real CE 12.7/13.2 > ln|V| 12.43
- P0 source_max_length=256; M 512
- trained P/PA/L 증거 아님

---

## 4. 검토 질문

### Q1. Self-containedness

v1.0.1이 이전 문서 없이 구현 가능한가? measurement semantics, path flags, donor rule, replay procedure가 충분한가?

### Q2. Decision contract

validity/control/signal, ANDn, F1–F11, L 9-pair, fixtures 16–18, small-N이 total/executable한가?

### Q3. Mixed M domain

F/L 15 common + P/PA 20 native = 1,680, 96/48, `m_valid` 20, `m_pass_l` 15가 일관되는가?

### Q4. M builder / M_NORM / endpoint / replay

F/L/P/PA builder, P identity, real_prefix_t, M_NORM, replay procedure, control_digest가 충분한가?

### Q5. F/L memory length scope

K=753 M-only, training real-only, eval donor-crop, generation 20×256이 short docs를 올바르게 처리하는가?

### Q6. P/PA

P/PA 20 native, P_POS/P_NORM/PA_POS/PA_NORM, PA veto, PA_RETENTION non-gate, geometry caveat가 충분한가?

### Q7. Statistics / tail

n_boot 1000, seed 20261109, documents_positive, 2/3 registered, signal tail, absolute top3, tie rule, missing seed NA가 executable한가?

### Q8. D0/D1/cap

D0 0-update, D1 4 arms ×1 debug seed, 8 phases, phase 5 560, phase 7 600, T_proj ≤96이 산술·승인 경계에서 맞는가?

### Q9. Hash/golden

state/replay canonical frame, control_digest, donor_sort, tolerance vs exact hash, golden digests가 충분한가?

### Q10. 남은 Must-fix

v1.0.1이 v1.0 Must-fix를 실제로 닫았는가? 새로 만든 문제가 있는가? ranked list로 제시하라.

### Q11. 동결·구현 승인

v1.0.1을 동결하고 **구현 + unit tests + D0 zero-update mechanics debug**를 승인할 수 있는가? 구현 전 필수 test는 무엇인가?

### Q12. B0-B / D1 / 3-seed

D1/3-seed/B0-B/B1/B2/Stage C 경계가 충분한가? B0-B predicate를 v1.0.1 label에 맞게 재진술하라.

### Q13. 최종 판정 및 freeze

**STOP / NARROW / CONTINUE**와 승인 범위를 제시하라.

- v1.0.1 freeze
- 구현+unit tests
- D0
- D1
- 3-seed
- 금지 범위
- 최대 compute
- test 163 지위
- v1.0.1이 정말 단일 구현 권위로 충분한가

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
v1.0.1 freeze:
구현+unit tests:
D0:
D1:
3-seed:
금지 범위:
최대 compute:
Must-fix (ranked):
v1.0.1 self-contained:
잘못된 전제:
```

---

## 6. Artifacts

| 경로 | 내용 |
|---|---|
| `docs/plan_c5_b0a_pm_prereg_v1_0_1.md` | v1.0.1 |
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_2026-11-09/golden_vectors.json` | golden |
| `reports/C5_B0A_PM_PREREG_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | v1.0 review |
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

> **v1.0.1이 v1.0 Must-fix를 실제로 닫고 self-contained 구현 권위로 freeze 가능한가, 그리고 구현·unit tests·D0를 승인할 수 있는가?**

특히 다음을 명시해 달라.

1. mixed 1,680 / D1 560 / replay 1,680의 실행 가능성
2. measurement semantics / donor rule / path flags의 충분성
3. D0/D1/3-seed/B0-B 승인 경계
