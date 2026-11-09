# C5 Phase 6 v1.0.5 — External Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `50653b5`
- 대상: `docs/plan_c5_b0a_pm_prereg_v1_0_5.md` (1,721줄)
- freeze template: `docs/plan_c5_b0a_pm_prereg_v1_0_5_FREEZE.template.json`
- golden: `docs/hoplite/c5_b0a_pm_prereg_v1_0_5_2026-11-09/golden_vectors.json`
- P1: `reports/provenance/C5_b0a/p1_usage.json`, `p1_usage.postrun.json`
- registry: `reports/provenance/C5_b0a/phase6_artifact_registry.json` (v2)
- preflight: `reports/provenance/C5_b0a/m_cohort_preflight.json`
- preflight hash: **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`**
- 상태: **v1.0.5 review. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. Reviewer instructions

1. 이 문서를 처음부터 끝까지 직접 읽어라. 다른 모델의 답을 재사용하지 말라.
2. 저장소 접근이 가능하면 다음 원문을 확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v1_0_5.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_5_FREEZE.template.json`
   - `docs/hoplite/c5_b0a_pm_prereg_v1_0_5_2026-11-09/golden_vectors.json`
   - `reports/C5_B0A_PM_PREREG_V1_0_4_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_4.md` (historical)
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
   `docs/hoplite/c5_b0a_pm_prereg_v1_0_5_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q13 판정 표와 Must-fix 요약을 포함하라.

---

## 1. TL;DR

> **v1.0.4는 1 CONTINUE / 2 NARROW였다. v1.0.5는 freeze manifest, phase-7 baseline/delta numeric replay, `registered_seeds_positive`, key-coverage golden, stored/hash record, P1 contradiction/registry를 닫았다. 이 문서는 v1.0.5가 freeze 가능한지, 구현·unit tests·D0를 승인할 수 있는지를 묻는다.**

| 항목 | 상태 |
|---|---|
| v1.0.4 | 1 CONTINUE / 2 NARROW |
| **v1.0.5** | **작성 완료, 미승인** |
| Phase 6 실행 | **없음** |
| P0 | SENSITIVE_POSITIVE, descriptive |
| test 163 | sealed |

---

## 2. v1.0.5의 핵심 변경

### 2.1 Freeze manifest

- path: `docs/plan_c5_b0a_pm_prereg_v1_0_5_FREEZE.json`
- schema:
  ```json
  {
    "status": "frozen",
    "plan_path": "docs/plan_c5_b0a_pm_prereg_v1_0_5.md",
    "plan_sha256": "...",
    "freeze_commit": "...",
    "p1_manifest_sha256": "...",
    "golden_sha256": "...",
    "preflight_sha256": "...",
    "helper_commits": {"runner/...": "..."},
    "registered_seeds": [20261108,20261109,20261110]
  }
  ```
- template exists; not a freeze.

### 2.2 Phase-7 numeric replay

- `baseline_ce = CE(control_variant[:K_d], target, endpoint)` phase-7 재계산.
- `ce`/`baseline_ce`/`delta` numeric replay `atol=1e-5`, `rtol=1e-4`.
- `diagnostic_replay_ok` separate; does not change primary `replay_ok`.
- `hash_record` excludes `baseline_ce`/`delta`.

### 2.3 seeds naming

- `registered_seeds_positive` = registered seed means > 0.
- P0 helper `seeds_positive` is a **document** count.
- no stale `registered_seeds_positive`.

### 2.4 Golden domains

- `replay_base` = 3-record key coverage digest `c43ea…`.
- `key_coverage_golden` = 4-record fixture `8277a7…`; not the 600-record phase-7 domain.
- `phase7_diagnostic` = 600/arm-seed, numeric-only.
- `control_manifest_golden` = synthetic `[1,1]`; real `[K_M,512]` postrun-only.
- `stored_record` nested; `hash_record` flat 8-field.

### 2.5 P1

- `p1_usage.json` frozen; `p1_usage.postrun.json` separate.
- contradiction rule: any `p1_used=true`, any `test_split_read=true`, or any ID outside allowlist → false.
- postrun covers registry; registry v2 includes checkpoints/control/phase7.
- `note` allowed.

### 2.6 기타

- `M_NORM[:K_d]` no renormalization; P/PA `K_d=512=K_M`.
- checkpoint base `reports/provenance/C5_b0a/checkpoints/{arm}/{seed}.pt`.
- `MARGINAL_SIGNAL_COHORT` informational.
- `control/` logical vs `control_manifest/` filesystem prefix.
- `F=360,L=360,P=480,PA=480`.

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

v1.0.4 1 CONTINUE/2 NARROW의 잔여 10개가 실제로 닫혔는가? 각각 closed / partial / open.

1. freeze manifest
2. phase-7 baseline/delta numeric replay
3. `registered_seeds_positive`
4. key-coverage golden
5. stored/hash record
6. P1 contradiction/registry
7. ordering `donor_sort`
8. M_NORM truncation
9. checkpoint base dir
10. MARGINAL_SIGNAL_COHORT/line count/prefix

### Q2. Self-containedness

v1.0.5만 읽고 구현 가능한가? 남은 외부 참조·암묵 지식은 무엇인가?

### Q3. Freeze manifest

schema/path가 D0 `assay_path_ok`를 평가 가능하게 하는가? `plan_sha256`이 manifest 자기참조 없이 계산 가능한가? helper commits/golden/preflight/P1 binding이 충분한가?

### Q4. Phase-7 numeric replay

`baseline_ce`/`delta` numeric replay가 실제로 실행 가능한가? `diagnostic_replay_ok`가 primary `replay_ok`와 분리되는가? `hash_record`에서 제외된 필드가 audit 가능한가?

### Q5. Seeds / stats

`registered_seeds_positive`가 required/forbidden 충돌을 없애는가? P0 `seeds_positive` document count와 구분되는가?

### Q6. Golden domains

`replay_base` 3-record, `key_coverage_golden` 4-record, `phase7_diagnostic` 600 numeric, `control_manifest_golden` synthetic이 서로 혼동 없이 정의됐는가?

### Q7. P1

contradiction rule, frozen/postrun, registry v2, unknown note가 fail-closed인가? postrun이 registry를 실제로 커버하는가?

### Q8. Checkpoint / naming

`reports/provenance/C5_b0a/checkpoints/{arm}/{seed}.pt`, 12-key map, per-unit 120/160, 360/480/1,680이 맞는가?

### Q9. D0/D1/cap

D0 4 configs, D1 4 arms ×1 seed ×1 update, 8 phases, 560/600, T_proj ≤96, 120 hard abort가 맞는가?

### Q10. 남은 Must-fix

v1.0.5가 새로 만든 문제가 있는가? ranked list. 특히 freeze manifest template와 actual freeze, phase-7 numeric vs hash domain, key-coverage naming이 충분한지 확인하라.

### Q11. 동결·구현 승인

v1.0.5를 동결하고 **구현 + unit tests + D0 zero-update mechanics debug**를 승인할 수 있는가? 구현 전 필수 test는 무엇인가?

### Q12. B0-B / D1 / 3-seed

D1/3-seed/B0-B/B1/B2/Stage C 경계가 충분한가? B0-B predicate를 v1.0.5 label에 맞게 재진술하라.

### Q13. 최종 판정 및 freeze

**STOP / NARROW / CONTINUE**와 승인 범위를 제시하라.

- v1.0.5 freeze
- 구현+unit tests
- D0
- D1
- 3-seed
- 금지 범위
- 최대 compute
- test 163 지위
- v1.0.5가 정말 단일 구현 권위로 충분한가

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
v1.0.5 freeze:
구현+unit tests:
D0:
D1:
3-seed:
금지 범위:
최대 compute:
Must-fix (ranked):
v1.0.5 self-contained:
잘못된 전제:
```

---

## 6. Artifacts

| 경로 | 내용 |
|---|---|
| `docs/plan_c5_b0a_pm_prereg_v1_0_5.md` | v1.0.5 |
| `docs/plan_c5_b0a_pm_prereg_v1_0_5_FREEZE.template.json` | freeze template |
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_5_2026-11-09/golden_vectors.json` | golden |
| `reports/C5_B0A_PM_PREREG_V1_0_4_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | v1.0.4 review |
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

> **v1.0.5가 v1.0.4의 10개 잔여를 실제로 닫고 self-contained 구현 권위로 freeze 가능한가, 그리고 구현·unit tests·D0를 승인할 수 있는가?**

특히 다음을 명시해 달라.

1. freeze manifest schema/path와 D0 평가 가능성
2. phase-7 `baseline_ce`/`delta` numeric replay와 hash 분리
3. `registered_seeds_positive`/key-coverage golden의 일관성
