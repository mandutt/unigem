# C5 Phase 6 v1.0.2 — External Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `1f6b816`
- 대상: `docs/plan_c5_b0a_pm_prereg_v1_0_2.md` (1,564줄)
- golden: `docs/hoplite/c5_b0a_pm_prereg_v1_0_2_2026-11-09/golden_vectors.json`
- P1 manifest: `reports/provenance/C5_b0a/p1_usage.json`
- preflight: `reports/provenance/C5_b0a/m_cohort_preflight.json`
- preflight hash: **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`**
- 상태: **v1.0.2 review. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. Reviewer instructions

1. 이 문서를 처음부터 끝까지 직접 읽어라. 다른 모델의 답을 재사용하지 말라.
2. 저장소 접근이 가능하면 다음 원문을 확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v1_0_2.md`
   - `docs/hoplite/c5_b0a_pm_prereg_v1_0_2_2026-11-09/golden_vectors.json`
   - `reports/C5_B0A_PM_PREREG_V1_0_1_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_1.md` (historical)
   - `reports/provenance/C5_b0a/m_cohort_preflight.json`
   - `reports/provenance/C5_b0a/p0_native_sanity.json`
   - `reports/provenance/C5_b0a/p1_usage.json`
   - `runner/c5_mt5_lora_b0.py`
   - `eval/tests/test_c5_b0_metric.py`
3. **학습·평가를 실행하지 말라.** test 163을 열지 말라. P1 데이터를 사용하지 말라.
4. **서브에이전트/추가 LLM을 호출하지 말고 직접 검토하라.**
5. 각 Q1~Q13에 대해 **판정(agree / disagree / conditional / defer) + 근거 + 다음 단계 1~3개**를 적어라.
6. 최종 판정은 **STOP / NARROW / CONTINUE** 중 하나로 하고, 승인 범위·금지 범위·compute cap을 명시하라.
7. 결과를 본 뒤 threshold·seed·donor·step·LR을 바꾸자는 제안은 하지 말라. 필요하면 **새 사전등록**으로 분리하라.
8. 보고서 파일을 작성하라:
   `docs/hoplite/c5_b0a_pm_prereg_v1_0_2_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q13 판정 표와 Must-fix 요약을 포함하라.

---

## 1. TL;DR

> **v1.0.1은 3/3 NARROW였다. v1.0.2는 15개 blocker를 text-only로 폐쇄했다. 이 문서는 v1.0.2가 freeze 가능한지, 구현·unit tests·D0를 승인할 수 있는지를 묻는다.**

| 항목 | 상태 |
|---|---|
| v1.0.1 | 3/3 NARROW |
| **v1.0.2** | **작성 완료, 미승인** |
| Phase 6 실행 | **없음** |
| P0 | SENSITIVE_POSITIVE, descriptive |
| test 163 | sealed |

---

## 2. v1.0.2의 핵심 변경

### 2.1 P0 path flag

- `p0_path_ok` = `mode=p0_sanity_no_training` + `test_split_used=false`.
- legacy P0 artifact에 `no_training` 키가 없어도 된다.
- P0 result 수정 없음.

### 2.2 Donor

```text
F/L: EG2 layer19 h_len
P/PA: native source length after "summarize: " truncation 512

donors(rid, arm):
  val20 except rid
  sort (abs(len_arm[c]-len_arm[rid]), c) asc
  first 5
```

- donor list는 **arm-specific**; F/L과 P/PA가 다르다.
- arm 내 seed는 같은 donor list.
- train20 donor 없음.
- `shuffled` = wrong-donor memory.

### 2.3 Replay control tensors

- `control_manifest/arm/seed/M_POS_MEAN.npz`
- `control_manifest/arm/seed/M_NORM/{t}.npz`
- `control_manifest.json` + per-tensor SHA256.
- `control_digest`는 integrity check이며 tensor 대체가 아니다.
- replay는 tensor를 load해 CE를 재계산한다.

### 2.4 Allowlist / P1

- allowlist = train20 ∪ val20.
- `test_split_used`는 allowlist membership으로 판정하며 test 163을 스캔하지 않는다.
- `reports/provenance/C5_b0a/p1_usage.json`에 `p1_used:false`, `test_split_read:false`.

### 2.5 Data paths / h_len

- F5: `data/external/f5_pairs_v3_clean.jsonl`
- splits: `reports/provenance/C5_clean/splits.json`
- EG2 cache: `data/wave2c/eg2_native_layer19/layer19`
- native: `data/models/mt5-small`
- `h_len` = source sequence length
- `copyable_mask`는 raw passage 기준.

### 2.6 P/PA validity와 calibration 분리

```text
P_VALID = P step100 path valid
          AND each registered seed × 20 native ×2 variants ×2 endpoints ×2 memory present/finite
          AND no test/P1 ID

PA_VALID = same for PA
```

- `p_valid := P_VALID`; `pa_valid := PA_VALID`.
- `P_POS_PASS`/`P_NORM_PASS`는 calibration이며 validity와 별개.
- `m_valid = ANDn(m_pass_pos_p, m_pass_norm_p, m_pass_pos_pa, m_pass_norm_pa)`.
- P/PA validity true + calibration fail → `M_CONTROL_INVALID` reachable.
- P/PA 3 seeds; seed mean → bootstrap; missing seed NA.

### 2.7 Copy-token scope

- signal/eval: `<5` copy tokens → document excluded from copy endpoint and `n_signal`.
- primary M: `<5` → `endpoint_ok=false` → `M_NOT_EVALUABLE`; no silent omission.
- exact 1,680 if evaluable.

### 2.8 Phase-7

```text
docs 15 common
donors 5
K_d = min(len(real_prefix), len(donor_prefix))
control_pos = M_POS_MEAN[:K_d]
control_norm = M_NORM(t)[:K_d]
real = real_prefix[:K_d]
wrong = donor_prefix[:K_d]
15×5×2×2×2 = 600/arm-seed
```

- donor는 `K_d`만 결정; content 혼합 없음.
- phase 7 diagnostic, not gate.

### 2.9 기타

- training mode/RNG §2.7: base decoder eval, adapter/LoRA train, seed→adapter→LoRA.
- `T_proj`에 `t_primary_replay_arm` 추가.
- D1 `not_a_result:true`; `labels_computed:false` = decision/signal labels, target-token labels는 CE용.
- F11 = `INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL` + validity triple.
- golden supplemental digest `38e5e2f…f6695`.
- `P_VALID` 20 native; `m_pass_l` 15 common.

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

### Q1. 15 blocker closure

v1.0.1 3/3 NARROW의 15개 blocker가 실제로 닫혔는가? 각 blocker별로 closed / partial / open을 판정하라.

1. P0 `no_training`
2. donor basis
3. replay control tensors
4. `test_split_used`/P1
5. `h_len`/data paths
6. P/PA seed aggregation
7. P/PA alias/`M_CONTROL_INVALID`
8. copy-token `<5`
9. phase-7 recipe
10. threshold asymmetry
11. F11 label
12. training mode/RNG
13. T_proj primary replay
14. D1 no-labels/`not_a_result`
15. golden coverage

### Q2. Self-containedness

v1.0.2만 읽고 구현 가능한가? 남은 외부 참조·암묵 지식은 무엇인가?

### Q3. Validity/calibration

`P_VALID`/`PA_VALID`를 artifact-validity로 분리한 것이 `M_CONTROL_INVALID` 도달성을 회복하는가? `p_valid`/`pa_valid` 의미가 §5.4와 일관되는가? `P_POS_PASS`/`P_NORM_PASS`와 threshold `.05` vs `>0`가 정합적인가?

### Q4. Donor

arm-specific donor list가 F/L과 P/PA의 length basis를 올바르게 분리하는가? arm 내 seed 공유, train20 donor 없음, `donor_id 0..4`, `shuffled` 정의가 실행 가능한가?

### Q5. Control tensors / replay

`control_manifest`의 `.npz` + SHA256이 replay를 실제로 재구성하는가? phase 5 1,680 / phase 7 600, `atol=1e-5`/`rtol=1e-4`, debug vs final hash 분리가 충분한가?

### Q6. Allowlist / P1

allowlist membership이 sealed test 163을 열지 않고 `test_split_used`를 판정하는가? `p1_usage.json`이 충분한가? 누락/위조 시 path flag가 올바르게 NA/false가 되는가?

### Q7. Data paths / h_len

§2.6의 F5/JSONL/EG2/splits/native path와 `h_len` 정의가 구현 가능한가? `copyable_mask` raw passage가 맞는가? P/PA all-512 가정이 데이터와 맞는가?

### Q8. M arithmetic

1,680 / 560 / 600 / 96 / 48 / 15+5가 여전히 맞는가? `M_POS_MEAN`/`M_NORM` tensor shape, `K_M` 753/512, `endpoint_ok`가 정합적인가?

### Q9. D0/D1/cap

D0 0-update, D1 4 arms ×1 debug seed, 8 phases, phase 5 560, phase 7 600, T_proj primary replay 포함 ≤96 min이 맞는가?

### Q10. 남은 Must-fix

v1.0.2가 새로 만든 문제가 있는가? ranked list로 제시하라. 특히 `P_VALID`가 너무 약해져 `M_CONTROL_INVALID`가 오히려 unconditional해지는지, `control_manifest`가 너무 무거운지, donor arm-specific이 F/L/P/PA 비교를 해치는지 확인하라.

### Q11. 동결·구현 승인

v1.0.2를 동결하고 **구현 + unit tests + D0 zero-update mechanics debug**를 승인할 수 있는가? 구현 전 필수 test는 무엇인가?

### Q12. B0-B / D1 / 3-seed

D1/3-seed/B0-B/B1/B2/Stage C 경계가 충분한가? B0-B predicate를 v1.0.2 label에 맞게 재진술하라.

### Q13. 최종 판정 및 freeze

**STOP / NARROW / CONTINUE**와 승인 범위를 제시하라.

- v1.0.2 freeze
- 구현+unit tests
- D0
- D1
- 3-seed
- 금지 범위
- 최대 compute
- test 163 지위
- v1.0.2가 정말 단일 구현 권위로 충분한가

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
v1.0.2 freeze:
구현+unit tests:
D0:
D1:
3-seed:
금지 범위:
최대 compute:
Must-fix (ranked):
v1.0.2 self-contained:
잘못된 전제:
```

---

## 6. Artifacts

| 경로 | 내용 |
|---|---|
| `docs/plan_c5_b0a_pm_prereg_v1_0_2.md` | v1.0.2 |
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_2_2026-11-09/golden_vectors.json` | golden |
| `reports/C5_B0A_PM_PREREG_V1_0_1_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | v1.0.1 review |
| `reports/provenance/C5_b0a/m_cohort_preflight.json` | preflight |
| `reports/provenance/C5_b0a/p0_native_sanity.json` | P0 |
| `reports/provenance/C5_b0a/p1_usage.json` | P1 |
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

> **v1.0.2가 v1.0.1의 15개 blocker를 실제로 닫고 self-contained 구현 권위로 freeze 가능한가, 그리고 구현·unit tests·D0를 승인할 수 있는가?**

특히 다음을 명시해 달라.

1. validity/calibration 분리와 `M_CONTROL_INVALID` 도달성
2. donor arm-specific과 control tensor replay의 실행 가능성
3. D0/D1/3-seed/B0-B 승인 경계
