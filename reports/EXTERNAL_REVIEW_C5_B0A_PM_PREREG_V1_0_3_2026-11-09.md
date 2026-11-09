# C5 Phase 6 v1.0.3 — External Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `97e9d12`
- 대상: `docs/plan_c5_b0a_pm_prereg_v1_0_3.md` (1,618줄)
- golden: `docs/hoplite/c5_b0a_pm_prereg_v1_0_3_2026-11-09/golden_vectors.json`
- P1 manifest: `reports/provenance/C5_b0a/p1_usage.json`
- preflight: `reports/provenance/C5_b0a/m_cohort_preflight.json`
- preflight hash: **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`**
- 상태: **v1.0.3 review. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. Reviewer instructions

1. 이 문서를 처음부터 끝까지 직접 읽어라. 다른 모델의 답을 재사용하지 말라.
2. 저장소 접근이 가능하면 다음 원문을 확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v1_0_3.md`
   - `docs/hoplite/c5_b0a_pm_prereg_v1_0_3_2026-11-09/golden_vectors.json`
   - `reports/C5_B0A_PM_PREREG_V1_0_2_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_2.md` (historical)
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
   `docs/hoplite/c5_b0a_pm_prereg_v1_0_3_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q13 판정 표와 Must-fix 요약을 포함하라.

---

## 1. TL;DR

> **v1.0.2는 3/3 NARROW였다. v1.0.3은 10개 blocker를 text/golden/schema only로 폐쇄했다. 이 문서는 v1.0.3이 freeze 가능한지, 구현·unit tests·D0를 승인할 수 있는지를 묻는다.**

| 항목 | 상태 |
|---|---|
| v1.0.2 | 3/3 NARROW |
| **v1.0.3** | **작성 완료, 미승인** |
| Phase 6 실행 | **없음** |
| P0 | SENSITIVE_POSITIVE, descriptive |
| test 163 | sealed |

---

## 2. v1.0.3의 핵심 변경

### 2.1 Canonical key

```text
key = (doc_id, arm, seed, variant, endpoint, memory_kind, donor_id)
```

- `donor_id`: `null` phase 5; `0..4` phase 7.
- `donor_sort`는 internal only; serialized/hashed 아님.
- base golden `c43ea…` 보존.
- supplemental golden은 canonical ascending sort 후 **`8277a713…af7a20`**.

### 2.2 Replay scope

- `final_checkpoint_hash` = **12 keys** `(arm,seed)`.
- phase 5 per-unit: F/L 120, P/PA 160.
- registered per arm-seed: F/L 120, P/PA 160.
- registered aggregate: F/L **360**, P/PA **480**, total **1,680**.
- D1 total **560**.
- phase 7 = 600/arm-seed diagnostic.

### 2.3 Phase-7

```text
real_prefix = memory(real doc) in arm space
donor_prefix = memory(donor doc) in arm space
K_d = min(len(real_prefix), len(donor_prefix))

control_pos = M_POS_MEAN[:K_d]
control_norm = M_NORM(t)[:K_d]
real = real_prefix[:K_d]
wrong = donor_prefix[:K_d]

records = 15 ×5 donors ×2 variants ×2 endpoints ×2 memory kinds = 600
memory_kind ∈ {real, donor}
```

- general enum `{control,real,donor}`.
- phase 5 subset `{control,real}`, `donor_id=null`.
- phase 7 subset `{real,donor}`, `donor_id=0..4`.
- record stores `ce` raw, `baseline_ce`, `delta`.
- canonical replay hash uses `{key, ce}` only.

### 2.4 P1

```json
{
  "manifest_version": 1,
  "p1_used": false,
  "test_split_read": false,
  "checked_artifacts": []
}
```

- `assay_path_ok` requires both false, manifest SHA256 match, no test ID, allowlist.
- malformed/missing → NA; contradictory known-use → false.
- attestation only; test 163 remains sealed.

### 2.5 P_VALID tri-state

```text
P_VALID:
  false  if path false OR nonfinite
  NA     if path NA OR artifact missing/unreadable
  true   if path true AND 20 native ×2×2×2 per seed present/finite
```

- F9/F10 now `p_step NA + p_valid NA` / `pa_path NA + pa_valid NA`.
- `M_CONTROL_INVALID` reachable when p/pa valid + calibration fail.
- P/PA calibration intentionally omits L's 2/3 and paired L>F.

### 2.6 Control tensors

```text
control_manifest/{arm}/{seed}/M_POS_MEAN.npz
control_manifest/{arm}/{seed}/M_NORM/{target_id}.npz
control_manifest.json
```

- NPZ array key `tensor`.
- canonical names `control/{arm}/{seed}/M_POS_MEAN`, `.../M_NORM/{target_id}`.
- hash over tensor frame, not ZIP bytes.
- control golden `6b50c226…c1938`.

### 2.7 기타

- D0 ≤4 configs = one 0-update per arm.
- control manifest path/footprint ~0.3GB.
- native-512 assert.
- `t_primary_replay_arm` 360/480.
- golden base `c43ea…`, supplemental `8277a7…`, control `6b50…`.

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

### Q1. 10 blocker closure

v1.0.2 3/3 NARROW의 10개 blocker가 실제로 닫혔는가? 각각 closed / partial / open.

1. `donor_sort` vs `donor_id`
2. 12-checkpoint replay
3. per-arm 420 → 360/480
4. phase-7 enum/CE
5. supplemental golden sort `8277a7…`
6. P1 strict both flags
7. `P_VALID` tri-state/F9
8. control tensor schema
9. P/PA calibration asymmetry
10. D0/artifact/native assert

### Q2. Self-containedness

v1.0.3만 읽고 구현 가능한가? 남은 외부 참조·암묵 지식은 무엇인가?

### Q3. Canonical hash / golden

`donor_id` canonical key, 12-checkpoint map, base `c43ea…`, supplemental `8277a7…`, control `6b50…`가 서로 정합적인가? `sort_keys`와 record sort가 충분한가?

### Q4. Replay arithmetic

1,680 / 560 / 600, per-unit 120/160, per-arm 360/480, `T_proj`가 정확한가? phase 7이 primary `replay_ok`에 영향을 주지 않는가?

### Q5. Phase-7 measurement

`donor_prefix`, `K_d`, control baseline, `ce`/`baseline_ce`/`delta`, variant 중복이 실제로 측정 가능한가? 600 count가 유지되는가?

### Q6. P1 / allowlist

`p1_used=false` AND `test_split_read=false`, manifest SHA256, checked artifacts, malformed→NA, contradictory→false가 fail-closed인가? test 163을 열지 않는가?

### Q7. P_VALID / M_CONTROL_INVALID

tri-state가 `M_CONTROL_INVALID`를 conditional reachable로 유지하는가? F9/F10이 reachable한가? calibration asymmetry가 정당한가?

### Q8. Control tensors

NPZ key `tensor`, canonical names, tensor-frame hash, shared `M_POS_MEAN`/per-target `M_NORM`, `6b50…`가 재현 가능한가? footprint가 cap 안인가?

### Q9. D0/D1/cap

D0 4 configs, D1 4 arms ×1 seed ×1 update, 8 phases, 560/600, T_proj ≤96, 120 hard abort가 맞는가?

### Q10. 남은 Must-fix

v1.0.3이 새로 만든 문제가 있는가? ranked list로 제시하라. 특히 canonical key 변경이 base digest를 깨지 않는지, 12 checkpoint map이 manifest에서 실제로 표현되는지, phase-7 `baseline_ce`가 replay hash와 충돌하지 않는지 확인하라.

### Q11. 동결·구현 승인

v1.0.3을 동결하고 **구현 + unit tests + D0 zero-update mechanics debug**를 승인할 수 있는가? 구현 전 필수 test는 무엇인가?

### Q12. B0-B / D1 / 3-seed

D1/3-seed/B0-B/B1/B2/Stage C 경계가 충분한가? B0-B predicate를 v1.0.3 label에 맞게 재진술하라.

### Q13. 최종 판정 및 freeze

**STOP / NARROW / CONTINUE**와 승인 범위를 제시하라.

- v1.0.3 freeze
- 구현+unit tests
- D0
- D1
- 3-seed
- 금지 범위
- 최대 compute
- test 163 지위
- v1.0.3이 정말 단일 구현 권위로 충분한가

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
v1.0.3 freeze:
구현+unit tests:
D0:
D1:
3-seed:
금지 범위:
최대 compute:
Must-fix (ranked):
v1.0.3 self-contained:
잘못된 전제:
```

---

## 6. Artifacts

| 경로 | 내용 |
|---|---|
| `docs/plan_c5_b0a_pm_prereg_v1_0_3.md` | v1.0.3 |
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_3_2026-11-09/golden_vectors.json` | golden |
| `reports/C5_B0A_PM_PREREG_V1_0_2_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | v1.0.2 review |
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

> **v1.0.3이 v1.0.2의 10개 blocker를 실제로 닫고 self-contained 구현 권위로 freeze 가능한가, 그리고 구현·unit tests·D0를 승인할 수 있는가?**

특히 다음을 명시해 달라.

1. `donor_id` canonical key와 base/supplemental/control digest 정합성
2. 12-checkpoint replay와 360/480 산술
3. phase-7 `ce`/`baseline_ce`/`delta` binding
