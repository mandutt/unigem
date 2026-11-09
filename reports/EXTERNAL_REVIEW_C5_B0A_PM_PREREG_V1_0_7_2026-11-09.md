# C5 Phase 6 v1.0.7 — External Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `9613ef6`
- 대상: `docs/plan_c5_b0a_pm_prereg_v1_0_7.md` (1,736줄)
- freeze template: `docs/plan_c5_b0a_pm_prereg_v1_0_7_FREEZE.template.json`
- golden: `docs/hoplite/c5_b0a_pm_prereg_v1_0_7_2026-11-09/golden_vectors.json`
- P1: `reports/provenance/C5_b0a/p1_usage.json`, `p1_usage.postrun.json`
- registry: `reports/provenance/C5_b0a/phase6_artifact_registry.json` (v2)
- preflight: `reports/provenance/C5_b0a/m_cohort_preflight.json`
- preflight hash: **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`**
- 상태: **v1.0.7 review. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

**Reviewer verification requirement (mandatory):**
- Report must include the reviewed HEAD SHA: `9613ef6`.
- Report must include this verbatim quote from §9.6.1:
  `K_d = min(K_M, len(real_prefix), len(donor_prefix))`
- If either is missing, the review is process-invalid and will be re-dispatched.

---

## 0. Reviewer instructions

1. 이 문서를 처음부터 끝까지 직접 읽어라. 다른 모델의 답을 재사용하지 말라.
2. 저장소 접근이 가능하면 다음 원문을 확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v1_0_7.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_7_FREEZE.template.json`
   - `docs/hoplite/c5_b0a_pm_prereg_v1_0_7_2026-11-09/golden_vectors.json`
   - `reports/C5_B0A_PM_PREREG_V1_0_6_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/provenance/C5_b0a/m_cohort_preflight.json`
   - `reports/provenance/C5_b0a/p0_native_sanity.json`
   - `reports/provenance/C5_b0a/p1_usage.json`
   - `reports/provenance/C5_b0a/p1_usage.postrun.json`
   - `reports/provenance/C5_b0a/phase6_artifact_registry.json`
   - `runner/c5_mt5_lora_b0.py`
   - `eval/tests/test_c5_b0_metric.py`
3. **학습·평가를 실행하지 말라.** test 163을 열지 말라. P1 데이터를 사용하지 말라.
4. **서브에이전트/추가 LLM을 호출하지 말고 직접 검토하라.**
5. 각 Q1~Q13에 대해 **판정(agree / disagree / conditional / defer) + 근거 + 다음 단계 1~3개**를 적어라.
6. 최종 판정은 **STOP / NARROW / CONTINUE** 중 하나로 하고, 승인 범위·금지 범위·compute cap을 명시하라.
7. 결과를 본 뒤 threshold·seed·donor·step·LR을 바꾸자는 제안은 하지 말라. 필요하면 **새 사전등록**으로 분리하라.
8. 보고서 파일을 작성하라:
   `docs/hoplite/c5_b0a_pm_prereg_v1_0_7_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q13 판정 표와 Must-fix 요약을 포함하라.

---

## 1. TL;DR

> **v1.0.6은 실질 2/2 NARROW + GLM process-invalid였다. v1.0.7은 §16.2 freeze 경로, `T_proj` per-seed, phase-7 `K_M` bound, freeze/manifest commit, key-coverage wording을 닫았다. 이 문서는 v1.0.7이 freeze 가능한지, 구현·unit tests·D0를 승인할 수 있는지를 묻는다.**

| 항목 | 상태 |
|---|---|
| v1.0.6 | 2/2 substantive NARROW; GLM invalid |
| **v1.0.7** | **작성 완료, 미승인** |
| Phase 6 실행 | **없음** |
| P0 | SENSITIVE_POSITIVE, descriptive |
| test 163 | sealed |

---

## 2. v1.0.7의 핵심 변경

### 2.1 Freeze paths/commit

- `docs/plan_c5_b0a_pm_prereg_v1_0_7.md` §16.2:
  - manifest `docs/plan_c5_b0a_pm_prereg_v1_0_7_FREEZE.json`
  - `plan_path` v1_0_7
- `freeze_commit` = final plan commit.
- `manifest_commit` = `_FREEZE.json` commit.
- D0 report records `freeze_manifest_sha256`.

### 2.2 T_proj

- `t_primary_replay_arm` = per-seed 120/160 only.
- outer `3 *` produces 360/480 per arm.
- do not pass 360/480 into the term.
- unit test `3 * sum(per-seed 120/160)`.

### 2.3 Phase-7 K_M bound

```text
K_d = min(K_M, len(real_prefix), len(donor_prefix))
assert 1 <= K_d <= K_M
assert K_d <= len(real_prefix) and K_d <= len(donor_prefix)
```

- real/donor/control all sliced to K_d.
- no M_NORM renormalization.
- 600/arm-seed numeric replay.

### 2.4 Key coverage

- `key_coverage_golden` 4-record fixture.
- phase-7 600 numeric-only.
- no conflation.

### 2.5 Legacy bootstrap

- `runner/c5_pm_stats.py` must not import legacy `bootstrap_paired`.
- unit assertion.

### 2.6 Golden

| vector | digest |
|---|---|
| state | `43ecb58e…d65712` |
| base replay | `c43ea35c…f7851667` |
| key coverage | `8277a713…af7a20` |
| control | `6b50c226…c1938` |

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

### Q1. 6 residual closure

v1.0.6 실질 NARROW의 잔여 6개가 실제로 닫혔는가? 각각 closed / partial / open.

1. §16.2 freeze paths
2. `T_proj` per-seed vs aggregate
3. phase-7 `K_d <= K_M`
4. `freeze_commit`/`manifest_commit`
5. key-coverage wording
6. legacy bootstrap assert

### Q2. Self-containedness

v1.0.7만 읽고 구현 가능한가? 남은 외부 참조·암묵 지식은 무엇인가?

### Q3. Freeze

§16.2 path가 v1_0_7로 일치하는가? `freeze_commit`/`manifest_commit`/`freeze_manifest_sha256` chain이 self-reference 없이 가능한가? template와 schema가 일치하는가?

### Q4. T_proj

per-seed 120/160, outer 3*, 360/480 aggregate, 1,680 total이 정확한가? triple-count 위험이 제거됐는가?

### Q5. Phase-7

`K_d` bound/assert, slicing, `baseline_ce`/`delta`, 600 numeric replay가 실행 가능한가? `K_M` 753/512와 정합적인가?

### Q6. Key coverage

4-record golden vs 600 numeric이 혼동 없이 분리됐는가?

### Q7. Legacy bootstrap

`runner/c5_pm_stats.py`가 legacy `bootstrap_paired`를 import하지 않는다는 test가 충분한가?

### Q8. Hash/golden

array digest, flat 8-field, `donor_sort`, control order, golden 5종이 정합적인가?

### Q9. D0/D1/cap

D0 4 configs, D1 4 arms ×1 seed ×1 update, 8 phases, 560/600, T_proj ≤96, 120 hard abort가 맞는가?

### Q10. 남은 Must-fix

v1.0.7이 새로 만든 문제가 있는가? ranked list.

### Q11. 동결·구현 승인

v1.0.7을 동결하고 **구현 + unit tests + D0 zero-update mechanics debug**를 승인할 수 있는가? 구현 전 필수 test는 무엇인가?

### Q12. B0-B / D1 / 3-seed

D1/3-seed/B0-B/B1/B2/Stage C 경계가 충분한가? B0-B predicate를 v1.0.7 label에 맞게 재진술하라.

### Q13. 최종 판정 및 freeze

**STOP / NARROW / CONTINUE**와 승인 범위를 제시하라.

- v1.0.7 freeze
- 구현+unit tests
- D0
- D1
- 3-seed
- 금지 범위
- 최대 compute
- test 163 지위
- v1.0.7이 정말 단일 구현 권위로 충분한가

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
v1.0.7 freeze:
구현+unit tests:
D0:
D1:
3-seed:
금지 범위:
최대 compute:
Must-fix (ranked):
v1.0.7 self-contained:
잘못된 전제:
```

---

## 6. Artifacts

| 경로 | 내용 |
|---|---|
| `docs/plan_c5_b0a_pm_prereg_v1_0_7.md` | v1.0.7 |
| `docs/plan_c5_b0a_pm_prereg_v1_0_7_FREEZE.template.json` | freeze template |
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_7_2026-11-09/golden_vectors.json` | golden |
| `reports/C5_B0A_PM_PREREG_V1_0_6_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | v1.0.6 review |
| `reports/provenance/C5_b0a/m_cohort_preflight.json` | preflight |
| `reports/provenance/C5_b0a/p0_native_sanity.json` | P0 |
| `reports/provenance/C5_b0a/p1_usage.json` | P1 frozen |
| `reports/provenance/C5_b0a/p1_usage.postrun.json` | P1 postrun |
| `reports/provenance/C5_b0a/phase6_artifact_registry.json` | registry v2 |
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

> **v1.0.7이 v1.0.6의 6개 잔여를 실제로 닫고 self-contained 구현 권위로 freeze 가능한가, 그리고 구현·unit tests·D0를 승인할 수 있는가?**

특히 다음을 명시해 달라.

1. §16.2 freeze path/commit chain
2. T_proj per-seed 120/160
3. phase-7 `K_d <= K_M`
