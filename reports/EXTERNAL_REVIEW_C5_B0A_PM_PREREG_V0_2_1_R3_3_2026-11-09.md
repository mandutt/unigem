# C5 Phase 6 v0.2.1-r3.3 — External Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `148d5c1` (`docs: add C5 Phase 6 v0.2.1-r3.3 contract unification`)
- 대상: `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_3.md` (1,031줄)
- preflight: `reports/provenance/C5_b0a/m_cohort_preflight.json`
- preflight hash: **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`** (content SHA-256)
- 상태: **r3.3 review. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. Reviewer instructions

1. 이 문서를 처음부터 끝까지 직접 읽어라. 다른 모델의 답을 재사용하지 말라.
2. 저장소 접근이 가능하면 다음 원문을 확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_3.md`
   - `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_2.md`
   - `reports/C5_B0A_PM_PREREG_V0_2_1_R3_2_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
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
   `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r3_3_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q12 판정 표와 Must-fix 요약을 포함하라.

---

## 1. TL;DR

> **r3.2는 1 CONTINUE(조건부) / 2 NARROW였다. r3.3은 L consensus 단일화, §6.3 unreachable cell 제거, tail_driven exact criterion, M builder/arm 표, replay/hash wire format, D1 initial fixed-prefix M CE scoring, NOT3/delta_memfree/DoD, missing-seed 2/3, stats, PA caveat, endpoint_ok, §1.1을 text-only로 닫는 errata다. 이 문서는 r3.3이 실제로 freeze 가능한지, 구현·D0를 승인할 수 있는지를 묻는다.**

| 항목 | 상태 |
|---|---|
| v0.1 | NARROW 3/3 |
| v0.2 | NARROW 3/3 |
| v0.2.1 | NARROW 3/3 |
| r1 | NARROW 3/3 |
| r2 | NARROW 3/3 |
| r3 | 2 CONTINUE 조건부 / 1 NARROW |
| r3.1 | 1 CONTINUE 조건부 / 2 NARROW |
| r3.2 | 1 CONTINUE 조건부 / 2 NARROW |
| **r3.3** | **작성 완료, 미승인** |
| Phase 6 실행 | **없음** |
| P0 | SENSITIVE_POSITIVE, descriptive |
| test 163 | sealed |

---

## 2. r3.2 freeze blockers

1. §2.3 L consensus vs §9.2 `L_SIGNAL=ANDn` 이중 정의.
2. §6.3 “M pass L false + control PASS” unreachable.
3. `tail_driven` exact criterion 소실.
4. `M_POS_MEAN` builder recipe/M primary reference 누락.
5. F/L/P/PA arm 표 부재.
6. replay/hash wire format identity/framing/golden vector.
7. D1 initial fixed-prefix M CE scoring/donor mapping.
8. `NOT3`/`delta_memfree`/DoD items 소실.
9. missing-seed 2/3 rule.
10. legacy stats.
11. PA caveat/`endpoint_ok` 중복.
12. `§1.4` dangling.

---

## 3. r3.3 변경 요약

### 3.1 L consensus

```text
l_signal = true   if l_copy=true and l_full=true
           false  if l_copy=false and l_full=false
           NA     otherwise

copy_only = ANDn(l_copy, NOT3(l_full))
full_only = ANDn(l_full, NOT3(l_copy))
```

- §2.3이 유일한 authoritative 정의.
- §9.2의 ANDn alias 삭제.
- 3×3 tri-state 표 9개.
- `false+NA` → `NOT_ASSESSABLE`; `MEAN_CONTRAST_ONLY` 아님.

### 3.2 Fixtures

- Fixture 16: all m_pass p/pa true, L both true → `EXPLORATORY_L_SIGNAL`
- Fixture 17: all m_pass true, L both false → `MEAN_CONTRAST_ONLY`
- Fixture 18: `m_pass_pos_l=false`, L both false → `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE`
- derived `m_pass_l`/`m_valid` 주입 금지
- §6.3 unreachable cell 삭제

### 3.3 tail_driven

```text
tail_driven = true   if leave_top3_mean <= 0 OR top3_share > .50
              false  if leave_top3_mean > 0 AND top3_share <= .50
              NA     if either null/nonfinite
```

- raw top3/share/leave_top3 artifact 보존.
- B0-B `tail_driven == false`.

### 3.4 M builder

```text
M_POS_MEAN = mean_i A(h_i)[:K_M]   # K_M × 512
```

- L `[:753]`, P/PA `[:512]`
- adapter `eval()` + `no_grad()`
- contributors >=10
- seed별 builder → seed-average
- M primary reference = target prefix at K_M
- donor-crop 금지

### 3.5 Arm table

| arm | memory | K | trainable |
|---|---|---:|---|
| F | EG2 layer19 | 753 | adapter |
| L | EG2 layer19 | 753 | adapter + decoder LoRA |
| P | native mT5 | 512 | decoder LoRA |
| PA | native mT5 | 512 | adapter + decoder LoRA |

### 3.6 Replay/hash

- checkpoint frame: `name_len|name|dtype|ndim|shape|nbytes|bytes`
- replay key: `(doc_id, arm, seed, variant, endpoint, memory_kind, donor_id)`
- `memory_kind ∈ {real, control}`
- donor-free primary M vs donor-level replay 분리
- canonical JSON + SHA256
- golden-vector expected digest
- permutation/duplicate/missing-key tests

### 3.7 D1

Phases:

1. train 1 update
2. step0 eval 20×5 donors
3. final eval 20×5 donors
4. M builder 20 train + 15 target ×2
5. **initial fixed-prefix real/M CE scoring 15×2×copy/full**
6. generation 20×256
7. replay 15×5×2×copy/full
8. overhead

- T_proj includes phase 5.
- donor factor only phases 2/3/7.
- ≤96 min.

### 3.8 기타

- `NOT3` 정의
- `delta_memfree` 정의
- DoD truth-table/PA labels
- missing registered seed → predicate NA
- new stats module seed 20261109
- PA scale/geometry caveat
- `endpoint_ok` single definition
- `§1.1`

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

r3.3의 validity/control/signal, ANDn, F1~F11, L tri-state, small-N precedence가 실제로 total/executable한가?

### Q2. L consensus / fixtures

§2.3 consensus, §2.4 9-pair table, fixture 16~18이 서로 일치하는가? false+NA가 `NOT_ASSESSABLE`로만 가는가?

### Q3. M preflight / cohort

K=753, 15/20 M, val20 signal, endpoint 15/15, full-K 11/20 secondary가 정당한가?

### Q4. M builder / M_NORM / endpoint / replay

`M_POS_MEAN` recipe/shape, M primary reference, `M_NORM(t)`, `builder_ok`, endpoint 15×3×4×2, replay key/framing, golden vector가 충분한가?

### Q5. PA

PA acquisition 명명, `PA_STEP100_NOT_VALID`, `PA_RETENTION` 비gate, scale/geometry caveat가 충분한가?

### Q6. Cap / D0 / D1

registered 12×100=1,200, D0 0-update, D1 4×1, 8-phase T_proj, initial M CE scoring이 산술·승인 경계에서 맞는가?

### Q7. Statistics

n_boot 1,000, CI percentile, bootstrap seed 20261109, documents_positive, 2/3 registered seeds, partial endpoint/tail tri-state가 executable한가?

### Q8. 남은 Must-fix

r3.2 freeze blocker 중 아직 닫히지 않은 항목을 ranked list로 제시하라. r3.3이 새로 만든 문제가 있는가?

### Q9. 동결·구현 승인

r3.3을 동결하고 **구현 + unit tests + D0 zero-update mechanics debug**를 승인할 수 있는가? 구현 전 필수 test/contract는 무엇인가?

### Q10. D1 / 3-seed

D1 timing gate와 3-seed를 별도로 유지하는 경계가 충분한가? 3-seed checklist에 빠진 항목은?

### Q11. B0-B

r3.3 결과가 좋아도 B0-B/B1/B2/Stage C를 자동 승인하지 않는 경계가 유지되는가? B0-B predicate를 r3.3 label에 맞게 재진술하라.

### Q12. 최종 판정

**STOP / NARROW / CONTINUE**와 승인 범위를 제시하라.

- r3.3 동결
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
r3.3 동결:
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
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_3.md` | r3.3 |
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_2.md` | r3.2 |
| `reports/C5_B0A_PM_PREREG_V0_2_1_R3_2_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | r3.2 review |
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

> **r3.3이 r3.2 freeze blocker를 충분히 닫았는가, 그리고 r3.3 동결·구현·unit tests·D0를 승인할 수 있는가?**

특히 다음을 명시해 달라.

1. L consensus/fixture/tail의 남은 모순
2. M builder/replay/hash/D1 phase 5의 타당성
3. D0/D1/3-seed/B0-B 승인 경계
