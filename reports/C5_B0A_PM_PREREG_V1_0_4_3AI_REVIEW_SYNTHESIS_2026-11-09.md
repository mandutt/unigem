# C5 Phase 6 v1.0.4 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v1_0_4_2026-11-09/`
- 검토 기준 HEAD: `5d4c9f5`
- 모델:
  - GLM 5.3 Flash **max** — 19,545 chars
  - DeepSeek V4.1 Flash **1017** **high** — 25,596 chars
  - Sol 6.1 **medium** — 27,992 chars
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V1_0_4_2026-11-09.md`
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **1 CONTINUE(조건부) / 2 NARROW.** v1.0.4는 v1.0.3의 10개 잔여를 문서 수준에서 닫았고, golden 5종·preflight hash·1,680/560/600·360/480은 재현됐다. 그러나 **freeze manifest가 어디에도 정의되지 않았고, phase-7 `baseline_ce`/`delta`는 hash에서 빠진 채 numeric replay도 없으며, `seeds_positive`가 required/forbidden으로 동시에 등장**해 동결할 수 없다. **v1.0.5/ERRATA text/schema only.**

---

## 1. 판정 행렬

| 검토자 | 모델 | 판정 | v1.0.4 freeze | 구현+unit tests | D0 | D1 | 3-seed |
|---|---|---|---|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **CONTINUE(조건부)** | MF-1..5 흡수 후 | 승인 | 승인 | 미승인 | 미승인 |
| DeepSeek 1017 | `deepseek-v4.1-flash-1017` high | **NARROW** | ERRATA MF-1..3 후 | 보류 | 보류 | 미승인 | 미승인 |
| Sol | `gpt-6.1-sol` medium | **NARROW** | repair+re-review 후 | 보류 | 보류 | 미승인 | 미승인 |
| **종합** | — | **NARROW (2/3)** | **보류** | **보류** | **보류** | **미승인** | **미승인** |

- CONTINUE 1/3.
- NARROW 2/3.
- STOP 0/3.
- NARROW 우세 → 동결하지 않는다.

---

## 2. 실제로 닫힌 것

- phase-7 `K_d` bounds / `baseline_ce` phase-7 재계산 — **closed**
- `donor_id=null` internal `donor_sort=-1` — **closed**
- flat 8-field hash — **closed**
- `final_checkpoint_hash.json` 12-key object — **closed**
- 12 unit replay / 360/480/1,680 — **verified**
- P1 `p1_usage.json` + `p1_usage.postrun.json` 분리 — **closed**
- control `[1,1]` synthetic, real `[K_M,512]` postrun-only — **closed**
- external module contracts §17.1 — **closed, source-bound**
- D0 labels/manifest timing — **closed**
- `F=360,L=360,P=480,PA=480` — **closed**
- dtype `<f4`, note key — **closed**
- base `c43ea…`, supplemental `8277a7…`, control `6b50…` — **verified**
- preflight hash — **verified**

GLM: 10/10 closed.
DS: 10 closed; 3 material gaps are new contract-level.
Sol: 7 closed / 3 partial, remaining docs.

---

## 3. 남은 Must-fix

### MF-1. Freeze manifest 미정의 (medium, D0 blocker)

- §4.0/§1.5/§16.2/§17.1 reference:
  - `p1_manifest_sha256`
  - freeze commit/content SHA
  - helper commit hashes
- no path/schema for the freeze manifest.
- `assay_path_ok` is in D0 report, so D0 cannot be evaluated.

**v1.0.5 요구**:
- `docs/plan_c5_b0a_pm_prereg_v1_0_5_FREEZE.json`:
  ```json
  {
    "plan_path": "...",
    "plan_sha256": "...",
    "p1_manifest_sha256": "...",
    "golden_sha256": "...",
    "preflight_sha256": "...",
    "helper_commits": {"runner/c5_mt5_layer_probe.py": "..."},
    "registered_seeds": [20261108,20261109,20261110]
  }
  ```
- path and schema normative.

### MF-2. phase-7 `baseline_ce`/`delta` numeric replay (medium)

- `baseline_ce`/`delta` are hash-excluded (correct).
- §11.4 step 5 only verifies `ce`-only supplemental digest.
- corrupted baseline/delta passes.

**v1.0.5 요구**:
- numeric replay of `baseline_ce` and `delta` at `atol=1e-5`, `rtol=1e-4`.
- keep them out of hash.
- report separately; phase-7 failure still does not affect primary `replay_ok`.

### MF-3. `seeds_positive` naming collision (medium-low)

- §10.2/§13.3 require `seeds_positive`.
- §13.5 forbids “stale `seeds_positive`”.
- P0 helper returns same name meaning **document** count.

**v1.0.5 요구**:
- rename registered field `registered_seeds_positive`.
- state P0 `seeds_positive` = document count.
- update tests.

### MF-4. Supplemental digest domain (low)

- §11.4 “supplemental replay digest” singular.
- golden supplemental is 4-record key-coverage fixture, mixes phase-5 `control` and phase-7 `donor`.
- phase-7 600-record domain has no digest.

**v1.0.5 요구**:
- rename `key_coverage_golden`.
- if phase-7 digest: define per arm-seed 600 vs pooled 7,200.
- if not: numeric only.
- no conflation.

### MF-5. Stored vs hash record schema (low)

- §9.6.1 stores `{key, ce, baseline_ce, delta}` nested.
- §12.2 hash record is flat 8-field.
- not labeled.

**v1.0.5 요구**:
- label `stored_record` vs `hash_record`.
- stored may be nested; hash flat.
- no ambiguity.

### MF-6. P1 contradiction/registry (low)

- “contradictory known-use” undefined.
- postrun completeness vs registry unstated.
- registry omits per-unit tensors/phase-7 artifacts.

**v1.0.5 요구**:
- contradiction rule: any `p1_used=true` or `test_split_read=true`, or any ID outside allowlist → false.
- postrun must cover registry.
- registry extends to checkpoints/control/phase-7.

### MF-7. Ordering wording (low)

- golden `ordering` says `donor_id`.
- §12.2 sort uses internal `donor_sort` (null -1).

**v1.0.5 요구**: align wording or state authority.

### MF-8. M_NORM truncation (low)

- `M_NORM(t)[:K_d]` is K_M-scaled vector truncated; no renormalization.
- P/PA K_d=K_M=512 always; F/L donors h_len<753 affected.

**v1.0.5 요구**: one line.

### MF-9. Checkpoint base dir (low)

- §17.2 says no artifact outside `reports/provenance/C5_b0a/`.
- §12.1 uses relative `checkpoints/{arm}/{seed}.pt`.

**v1.0.5 요구**: base path explicit.

### MF-10. Misc (cosmetic)

- `MARGINAL_SIGNAL_COHORT` defined but unused.
- `C5_STATUS` 1,690 vs 1,691 line count.
- canonical name `control/` vs path `control_manifest/`.

---

## 4. 검토자별 핵심

### GLM — CONTINUE(조건부)

- 10/10 closed.
- MF-1 supplemental digest population; MF-2 checkpoint base dir; MF-3 M_NORM truncation; MF-4 null-vs-0 test; MF-5 ordering note.
- freeze after MF-1..5; implementation+D0 conditional.

### DS 1017 — NARROW

- 10 closed.
- MF-1 freeze manifest undefined (blocks D0); MF-2 baseline/delta replay; MF-3 seeds_positive collision; MF-4 supplemental vs phase-7; MF-5 stored vs hash; MF-6 P1 contradiction; MF-7 ordering; MF-8 misc.
- freeze after ERRATA.

### Sol — NARROW

- 7 closed / 3 partial.
- freeze manifest; phase-7 diagnostic audit; text/schema.
- no freeze as-is.

---

## 5. 결정

```text
v1.0.4 = 동결 보류 (1 CONTINUE / 2 NARROW)
v1.0.5/ERRATA = 필요 (text/schema only)
Phase 6 구현 = 미승인
unit tests = 미승인
D0 = 미승인
D1 = 미승인
3-seed = 미승인
B0-B/B1/B2/Stage C = 미승인
test 163 = sealed
T5Gemma2 = D-108 STOP
```

---

## 6. 다음 단계

1. v1.0.5 text/schema:
   - freeze manifest
   - phase-7 baseline/delta numeric replay
   - `registered_seeds_positive`
   - key-coverage golden naming
   - stored vs hash record
   - P1 contradiction/registry
   - ordering/M_NORM/base dir/misc
2. v1.0.5 review
3. freeze manifest + content SHA
4. 구현 + unit tests
5. D0
6. D1 separate
7. 3-seed separate

---

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_4_2026-11-09/review_GLM.md` | GLM |
| `.../review_DS1017.md` | DeepSeek |
| `.../review_SOL.md` | Sol |
| `reports/C5_B0A_PM_PREREG_V1_0_4_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |
| `docs/plan_c5_b0a_pm_prereg_v1_0_4.md` | v1.0.4 |
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_4_2026-11-09/golden_vectors.json` | golden |

## 8. 제한

- 이 종합은 승인이 아니다.
- NARROW 2/3가 우세하다.
- v1.0.5 없이 코드를 작성하지 않는다.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아니다.
- golden digests are verified constants, not results.
