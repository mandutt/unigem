# C5 Phase 6 v0.2.1-r2 — External Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `308648e` (`docs: pin r2 M preflight hash to committed blob`)
- 대상: `docs/plan_c5_b0a_pm_prereg_v0_2_1_r2.md` (770줄)
- preflight: `reports/provenance/C5_b0a/m_cohort_preflight.json`
- preflight hash: **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`** (committed blob, LF)
- 상태: **r2 review. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. Reviewer instructions

1. 이 문서를 처음부터 끝까지 직접 읽어라. 다른 모델의 답을 재사용하지 말라.
2. 저장소 접근이 가능하면 다음 원문을 확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v0_2_1_r2.md`
   - `docs/plan_c5_b0a_pm_prereg_v0_2_1_r1.md`
   - `reports/C5_B0A_PM_PREREG_V0_2_1_R1_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
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
   `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r2_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q12 판정 표와 Must-fix 요약을 포함하라.

---

## 1. TL;DR

> **r1은 3/3 NARROW였다. r2는 (a) `m_valid`/`M_CONTROL_INVALID`를 factored contract에 연결하고, (b) path flags를 개별 열거하며, (c) L 보존을 L-qualified label로 바꾸고, (d) K_M_L=753 선택 규칙·zero-margin·hash를 고정하고, (e) M builder/cohort/aggregation/replay를 명시하고, (f) D0 0-update·D1 1-update·timing gate를 분리한 text-only repair다. 이 문서는 r2가 r1 3-AI Must-fix를 실제로 닫았는지, 동결·구현·D0를 승인할 수 있는지를 묻는다.**

| 항목 | 상태 |
|---|---|
| v0.1 | NARROW 3/3 |
| v0.2 | NARROW 3/3 |
| v0.2.1 | NARROW 3/3 |
| r1 | NARROW 3/3 |
| **r2** | **작성 완료, 미승인** |
| Phase 6 실행 | **없음** |
| P0 | SENSITIVE_POSITIVE, descriptive |
| test 163 | sealed |

---

## 2. r1 3-AI Must-fix

1. `m_valid_p`/`m_valid_pa`/`M_VALID`가 `control_status`에 슬롯 없음 → P/PA M 실패가 `M_CONTROL_PASS`로 샐 수 있음.
2. path/test flag 미열거; “any path false → ASSAY_INVALID”와 “PA path fail → PA_STEP100_NOT_VALID” 충돌.
3. `l_signal=true` + control `NOT_ASSESSABLE`/`n_signal<15`에서 L 보존 불변식 깨짐.
4. K_M_L=753 선택 규칙 미기재; zero-margin cohort.
5. M builder 결정론/M_VALID cohort/per-variant aggregation/`delta_memfree` 미정의.
6. D0/D1 seed 20261111 미재기술; D0만으로 timing projection 불가; D1 optional vs timing gate 충돌; stale `seeds_positive`.

---

## 3. r2 변경 요약

### 3.1 M preflight

```text
K_M_L = max K such that
  count(train20 h_len >= K) >= 10
  AND count(val20 h_len >= K) >= 15
```

- `K_M_L = 753`; `K=754` → val eligible 14.
- L contributors **16**, L targets **15/20**, native **20/20 at 512**, common **15/20**.
- full-K L **11/20**, secondary only.
- label: `M_CONTROL_PREFIX753_COHORT15`.
- zero-margin: `MARGINAL_SIGNAL_COHORT=true`.
- preflight hash **3ee3f1ca…** (committed blob).

### 3.2 Factored contract

```text
validity_status
control_status
signal_status
flags
headline  # convenience only
```

#### Path precedence

```text
assay_path_ok=false / p0_path_ok=false / test_split_used=true
  -> ASSAY_INVALID
any of assay/p0/p_step100_path not_assessable
  -> NOT_ASSESSABLE
p_step100_path_ok=false
  -> ASSAY_INVALID
p_valid=false -> P_STEP100_NOT_VALID
p_valid=NA -> NOT_ASSESSABLE
pa_step100_path_ok=false -> PA_STEP100_NOT_VALID
pa_valid=false -> PA_STEP100_NOT_VALID
pa_valid=NA -> NOT_ASSESSABLE
m_evaluable=false/NA -> M_NOT_EVALUABLE
else VALID
```

- P path fail은 `ASSAY_INVALID`.
- PA path fail은 `PA_STEP100_NOT_VALID`.
- `pa_step100_path_ok`는 aggregate “any path”에 넣지 않음.

#### Control

```text
m_valid = AND3(
  m_pass_pos_p, m_pass_norm_p,
  m_pass_pos_pa, m_pass_norm_pa
)

m_evaluable = AND3(cohort_ok, seed_ok, replay_ok, p_valid, pa_valid)

if m_evaluable not true -> M_NOT_EVALUABLE
elif p_valid/pa_valid not true -> M_NOT_EVALUABLE
elif m_valid false -> M_CONTROL_INVALID
elif m_valid NA -> NOT_ASSESSABLE
elif m_pass_l true -> M_CONTROL_PASS
elif m_pass_l false -> M_CONTROL_FAIL
else NOT_ASSESSABLE
```

- `M_CONTROL_NOT_VALID` 부활 금지.
- `M_CONTROL_INVALID` = P/PA M calibration fail.

#### Signal

- `l_signal` consensus:
  - both true → true
  - both false → false
  - otherwise NA
- `copy_only` / `full_only` = AND3 with NOT3.
- small-N labels:
  - `INCONCLUSIVE_SMALL_N`
  - `_WITH_L_SIGNAL`
  - `_WITH_COPY_ONLY`
  - `_WITH_FULL_ONLY`
- L-qualified:
  - `L_SIGNAL_M_CONTROL_FAIL`
  - `L_SIGNAL_M_CONTROL_INVALID`
  - `L_SIGNAL_M_CONTROL_NOT_EVALUABLE`
  - `L_SIGNAL_CONTROL_NOT_ASSESSABLE`
  - `L_SIGNAL_VALIDITY_INVALID`
  - `NO_L_SIGNAL_CONTROL_INVALID`
  - `NO_L_SIGNAL_CONTROL_NOT_EVALUABLE`
- `EXPLORATORY_L_SIGNAL` requires validity VALID + control PASS.

### 3.3 M

- L prefix **753**, P/PA prefix **512**.
- common M cohort **15/20**.
- builder: `adapter.eval()`, `model.eval()`, `torch.no_grad()`.
- M_VALID = P/PA POS and NORM.
- `delta_memfree_full = mean_full_ce − real_full_ce`; copy 동일.
- seed별 builder → seed 평균 → doc bootstrap.
- replay `atol=1e-5`, `rtol=1e-4`.
- full-K 11/20 secondary; not gate.

### 3.4 D0 / D1 / cap

| 항목 | 값 |
|---|---|
| registered | 12 units / 1,200 updates / 2h / 6 threads |
| D0 | 0 optimizer updates, ≤4 configs, ≤15min, seed 20261111 |
| D1 | 4 arm-seeds ×1 update, ≤20min, seed 20261111, 별도 승인 |
| D0 timing | 3-seed projection 금지 |
| D1 | 3-seed timing의 필수조건 (또는 승인된 timing probe) |
| D1 implementation gate | 필수 아님 |

---

## 4. P0 기준값

| split | mean Δcopy | CI | mean Δfull | positive docs |
|---|---:|---|---:|---:|
| train | +3.7617 | [1.8917, 5.6050] | +3.5027 | 14/20 |
| val | +5.2375 | [2.5013, 8.0753] | +5.2936 | 18/20 |

한계:

- val median 2.9739, top-3 share .4862
- untrained real CE 12.7/13.2 > ln|V| 12.43
- 20 val은 confirmatory holdout 아님
- P0는 native path sensitivity

---

## 5. 검토 질문

### Q1. Total factored contract

r2의 `(validity_status, control_status, signal_status)`와 tri-state가 실제로 total function인가? `m_valid`/`M_CONTROL_INVALID`, path precedence, L labels가 all cell을 덮는가?

### Q2. L preservation / small N

`l_signal` consensus, `INCONCLUSIVE_SMALL_N_WITH_*`, `L_SIGNAL_VALIDITY_INVALID`, `L_SIGNAL_CONTROL_NOT_ASSESSABLE`이 L flag를 왜곡 없이 보존하는가? zero-margin n=15가 executable한가?

### Q3. M preflight

K=753 max-K rule, 16 contributors, 15/20 targets, `MARGINAL_SIGNAL_COHORT`, full-K 11/20 secondary가 정당한가? prefix 753이 full-real-K 원칙을 과도하게 훼손하는가?

### Q4. M builder / aggregation / replay

eval/no_grad, common 15 cohort, P/PA same IDs, seed-average-before-bootstrap, `delta_memfree`, replay `atol=1e-5`가 leakage-free이고 충분한가?

### Q5. PA

PA acquisition 명명, `PA_STEP100_NOT_VALID`, `PA_RETENTION` 비gate, scale/geometry caveat가 충분한가?

### Q6. Cap / D0 / D1

registered 12×100=1,200, D0 0-update, D1 4×1, D1 required for 3-seed timing but optional for implementation gate가 산술·승인 경계에서 맞는가?

### Q7. Statistics

n_boot 1,000, CI percentile 2.5/97.5, bootstrap seed 20261109, seed-average-before-bootstrap, `documents_positive`/`seeds_positive`, top-3 share, `MARGINAL_SIGNAL_COHORT`가 executable한가?

### Q8. 남은 Must-fix

r1 3-AI Must-fix 중 아직 닫히지 않은 항목을 ranked list로 제시하라. r2가 새로 만든 문제가 있는가?

### Q9. 동결·구현 승인

r2를 동결하고 **구현 + unit tests + D0 zero-update mechanics debug**를 승인할 수 있는가? 구현 전 필수 test/contract는 무엇인가?

### Q10. D1 / 3-seed

D1 1-update smoke와 3-seed를 별도 gate로 유지하는 경계가 충분한가? 3-seed checklist에 빠진 항목은?

### Q11. B0-B

r2 결과가 좋아도 B0-B/B1/B2/Stage C를 자동 승인하지 않는 경계가 유지되는가? B0-B predicate를 r2 label에 맞게 재진술하라.

### Q12. 최종 판정

**STOP / NARROW / CONTINUE**와 승인 범위를 제시하라.

- r2 동결
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
r2 동결:
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
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r2.md` | r2 |
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r1.md` | r1 |
| `reports/C5_B0A_PM_PREREG_V0_2_1_R1_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | r1 review |
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

> **r2가 r1 3-AI Must-fix를 충분히 닫았는가, 그리고 r2 동결·구현·unit tests·D0를 승인할 수 있는가?**

특히 다음을 명시해 달라.

1. total factored contract에 남은 cell/모순
2. K_M_L=753 / M_CONTROL_PREFIX753_COHORT15의 타당성
3. D0/D1/3-seed/B0-B 승인 경계
