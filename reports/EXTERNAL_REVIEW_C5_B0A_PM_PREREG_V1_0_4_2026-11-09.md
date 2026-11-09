# C5 Phase 6 v1.0.4 — External Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `f82b47d`
- 대상: `docs/plan_c5_b0a_pm_prereg_v1_0_4.md` (1,691줄)
- golden: `docs/hoplite/c5_b0a_pm_prereg_v1_0_4_2026-11-09/golden_vectors.json`
- P1: `reports/provenance/C5_b0a/p1_usage.json`, `p1_usage.postrun.json`
- registry: `reports/provenance/C5_b0a/phase6_artifact_registry.json`
- preflight: `reports/provenance/C5_b0a/m_cohort_preflight.json`
- preflight hash: **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`**
- 상태: **v1.0.4 review. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. Reviewer instructions

1. 이 문서를 처음부터 끝까지 직접 읽어라. 다른 모델의 답을 재사용하지 말라.
2. 저장소 접근이 가능하면 다음 원문을 확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v1_0_4.md`
   - `docs/hoplite/c5_b0a_pm_prereg_v1_0_4_2026-11-09/golden_vectors.json`
   - `reports/C5_B0A_PM_PREREG_V1_0_3_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_3.md` (historical)
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
   `docs/hoplite/c5_b0a_pm_prereg_v1_0_4_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q13 판정 표와 Must-fix 요약을 포함하라.

---

## 1. TL;DR

> **v1.0.3은 1 CONTINUE / 2 NARROW였다. v1.0.4는 phase-7 K_d/baseline_ce, null sort, flat 8-field hash, 12-key checkpoint, P1 frozen/postrun, control fixture, module contracts를 닫았다. 이 문서는 v1.0.4가 freeze 가능한지, 구현·unit tests·D0를 승인할 수 있는지를 묻는다.**

| 항목 | 상태 |
|---|---|
| v1.0.3 | 1 CONTINUE / 2 NARROW |
| **v1.0.4** | **작성 완료, 미승인** |
| Phase 6 실행 | **없음** |
| P0 | SENSITIVE_POSITIVE, descriptive |
| test 163 | sealed |

---

## 2. v1.0.4의 핵심 변경

### 2.1 Phase-7 K_d / baseline_ce

```text
K_d = min(len(real_prefix), len(donor_prefix))
assert 1 <= K_d <= min(len(real_prefix), len(donor_prefix))

control_pos = M_POS_MEAN[:K_d]
control_norm = M_NORM(t)[:K_d]
real = real_prefix[:K_d]
wrong = donor_prefix[:K_d]

baseline_ce = CE(control_variant[:K_d], target, endpoint)   # recomputed in phase 7
ce = raw CE(record tensor)
delta = baseline_ce - ce
```

- phase-5 stored CE at `K_M` must not be reused.
- phase 7 diagnostic only; not `m_valid`.

### 2.2 Null total order

- canonical key: `(doc_id, arm, seed, variant, endpoint, memory_kind, donor_id)`.
- sort tuple uses internal `donor_sort=-1` for null, `0..4` for donors.
- null sorts before 0.
- serialized `donor_id=null`.

### 2.3 Flat hash projection

Hash record is a **flat 8-field object**:

```json
{"arm":"L","ce":1.0,"doc_id":"doc_a","donor_id":null,"endpoint":"copy","memory_kind":"control","seed":20261108,"variant":"M_POS_MEAN"}
```

- nested `{key, ce}` is forbidden.
- `baseline_ce`/`delta` are outside hash domain.
- base `c43ea…`, supplemental `8277a7…`.

### 2.4 12-key checkpoint

```json
{
  "F/20261108": "sha256:...",
  "F/20261109": "sha256:...",
  "F/20261110": "sha256:...",
  "L/20261108": "sha256:...",
  "L/20261109": "sha256:...",
  "L/20261110": "sha256:...",
  "P/20261108": "sha256:...",
  "P/20261109": "sha256:...",
  "P/20261110": "sha256:...",
  "PA/20261108": "sha256:...",
  "PA/20261109": "sha256:...",
  "PA/20261110": "sha256:..."
}
```

- checkpoint paths `checkpoints/{arm}/{seed}.pt`.
- per-unit 120/160; aggregate F=360, L=360, P=480, PA=480, total 1,680.

### 2.5 P1 frozen/postrun

- `p1_usage.json` frozen at freeze with empty `checked_artifacts`.
- `p1_usage.postrun.json` separate; does not modify frozen.
- `phase6_artifact_registry.json`.
- `assay_path_ok` uses frozen hash; postrun audit-only.
- unknown `note` key allowed.

### 2.6 Control fixture

- control golden `[1,1]` is synthetic framing fixture.
- real `[K_M,512]` control_digest is postrun-only.
- names `control/{arm}/{seed}/M_POS_MEAN`, `control/{arm}/{seed}/M_NORM/{target_id}`.
- NPZ key `tensor`; hash over tensor frame.

### 2.7 기타

- external module contracts §17.1.
- D0 4 configs; labels/manifest timing.
- `F=360,L=360,P=480,PA=480`.
- `dtype_str=<f4`.
- golden digests `c43ea…`/`8277a7…`/`6b50…`.

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

### Q1. 10 residual closure

v1.0.3 1 CONTINUE/2 NARROW의 잔여 10개가 실제로 닫혔는가? 각각 closed / partial / open.

1. phase-7 `K_d`/`baseline_ce`
2. null total order
3. flat 8-field hash
4. 12-key checkpoint
5. P1 frozen/postrun
6. control fixture shape
7. external module contracts
8. D0 labels/timing
9. per-arm notation
10. dtype/fixture order/note

### Q2. Self-containedness

v1.0.4만 읽고 구현 가능한가? 남은 외부 참조·암묵 지식은 무엇인가?

### Q3. Phase-7 measurement

`K_d` bounds, `control_variant[:K_d]`, `baseline_ce` 재계산, `ce`/`delta`, 600 count가 실제로 실행 가능한가? phase-5 CE 재사용 위험이 제거됐는가?

### Q4. Canonical hash

flat 8-field record, null sort, `sort_keys`, `baseline_ce`/`delta` 제외가 base `c43ea…`/supplemental `8277a7…`와 정합적인가? nested `{key,ce}`가 불가능하게 봉인됐는가?

### Q5. Checkpoint map

12-key `final_checkpoint_hash.json`, `checkpoints/{arm}/{seed}.pt`, per-unit 120/160, aggregate 360/480/1,680이 맞는가?

### Q6. P1

`p1_usage.json` frozen, `p1_usage.postrun.json` separate, artifact registry, unknown note key, malformed/NA, contradictory/false가 fail-closed인가?

### Q7. Control tensors

`[1,1]` synthetic vs `[K_M,512]` real, NPZ key `tensor`, canonical names, `6b50…`, footprint, postrun-only real digest가 정합적인가?

### Q8. External modules

`Adapter`, `make_labels`, `load_layer_cache`, `LoRALinear`, `attach_decoder_lora_mt5`, `native_memory`, `repeated_4gram_rate` 계약이 충분한가? missing → NA가 안전한가?

### Q9. D0/D1/cap

D0 4 configs, D1 4 arms ×1 seed ×1 update, 8 phases, 560/600, T_proj ≤96, 120 hard abort가 맞는가?

### Q10. 남은 Must-fix

v1.0.4가 새로 만든 문제가 있는가? ranked list. 특히 `baseline_ce`가 phase-7 hash와 분리되는지, 12-key map이 실제 runner와 맞는지, P1 frozen/postrun 분리가 감사 가능한지 확인하라.

### Q11. 동결·구현 승인

v1.0.4를 동결하고 **구현 + unit tests + D0 zero-update mechanics debug**를 승인할 수 있는가? 구현 전 필수 test는 무엇인가?

### Q12. B0-B / D1 / 3-seed

D1/3-seed/B0-B/B1/B2/Stage C 경계가 충분한가? B0-B predicate를 v1.0.4 label에 맞게 재진술하라.

### Q13. 최종 판정 및 freeze

**STOP / NARROW / CONTINUE**와 승인 범위를 제시하라.

- v1.0.4 freeze
- 구현+unit tests
- D0
- D1
- 3-seed
- 금지 범위
- 최대 compute
- test 163 지위
- v1.0.4가 정말 단일 구현 권위로 충분한가

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
v1.0.4 freeze:
구현+unit tests:
D0:
D1:
3-seed:
금지 범위:
최대 compute:
Must-fix (ranked):
v1.0.4 self-contained:
잘못된 전제:
```

---

## 6. Artifacts

| 경로 | 내용 |
|---|---|
| `docs/plan_c5_b0a_pm_prereg_v1_0_4.md` | v1.0.4 |
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_4_2026-11-09/golden_vectors.json` | golden |
| `reports/C5_B0A_PM_PREREG_V1_0_3_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | v1.0.3 review |
| `reports/provenance/C5_b0a/m_cohort_preflight.json` | preflight |
| `reports/provenance/C5_b0a/p0_native_sanity.json` | P0 |
| `reports/provenance/C5_b0a/p1_usage.json` | P1 frozen |
| `reports/provenance/C5_b0a/p1_usage.postrun.json` | P1 postrun |
| `reports/provenance/C5_b0a/phase6_artifact_registry.json` | registry |
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

> **v1.0.4가 v1.0.3의 10개 잔여를 실제로 닫고 self-contained 구현 권위로 freeze 가능한가, 그리고 구현·unit tests·D0를 승인할 수 있는가?**

특히 다음을 명시해 달라.

1. phase-7 `baseline_ce`/`delta`와 hash 분리
2. flat 8-field hash와 base/supplemental digest
3. 12-key checkpoint와 360/480 산술
