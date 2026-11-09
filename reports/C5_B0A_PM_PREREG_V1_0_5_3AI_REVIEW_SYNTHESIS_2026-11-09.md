# C5 Phase 6 v1.0.5 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v1_0_5_2026-11-09/`
- 검토 기준 HEAD: `dc1264b`
- 모델:
  - GLM 5.3 Flash **max** — 13,218 chars
  - DeepSeek V4.1 Flash **1017** **high** — 19,577 chars
  - Sol 6.1 **medium** — 24,934 chars
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V1_0_5_2026-11-09.md`
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **1 CONTINUE(조건부) / 2 NARROW.** v1.0.5는 freeze manifest schema, phase-7 numeric replay, `registered_seeds_positive`, key-coverage golden, P1 registry를 대부분 닫았고 golden 5종·preflight·P0는 재현됐다. 그러나 **`§13.5`가 required `registered_seeds_positive`를 “no stale”로 다시 금지**, **replay digest의 byte 규칙이 “array canonical JSON”으로 명시되지 않음**, **phase-7 prefix bound/equal-dim assert 없음**, **control golden order**, **bootstrap RNG/percentile**, **actual freeze handoff**가 남아 동결할 수 없다. **v1.0.6/ERRATA text/schema only.**

---

## 1. 판정 행렬

| 검토자 | 모델 | 판정 | v1.0.5 freeze | 구현+unit tests | D0 | D1 | 3-seed |
|---|---|---|---|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **CONTINUE(조건부)** | MF-A/B 후 | 승인 | 승인 | 미승인 | 미승인 |
| DeepSeek 1017 | `deepseek-v4.1-flash-1017` high | **NARROW** | MF-1..4 ERRATA 후 | 보류 | 보류 | 미승인 | 미승인 |
| Sol | `gpt-6.1-sol` medium | **NARROW** | MF-1 후재검토 | 보류 | 보류 | 미승인 | 미승인 |
| **종합** | — | **NARROW (2/3)** | **보류** | **보류** | **보류** | **미승인** | **미승인** |

- CONTINUE 1/3.
- NARROW 2/3.
- STOP 0/3.
- NARROW 우세 → 동결하지 않는다.

---

## 2. 실제로 닫힌 것

- freeze manifest schema/template — **closed**
- phase-7 `baseline_ce`/`delta` numeric replay — **closed**
- `registered_seeds_positive` 도입 — **partial** (§13.5 잔존)
- `key_coverage_golden` 분리 — **closed**
- `stored_record` vs `hash_record` — **closed**
- P1 contradiction/registry v2 — **closed**
- ordering `donor_sort` — **closed**
- `M_NORM[:K_d]` no renormalization — **closed**
- checkpoint base dir — **closed**
- MARGINAL/line/prefix — **closed**
- golden 5종 + preflight + P0 — **verified**
- `c43ea…`/`8277a7…`/`6b50…` — **verified**

GLM: 9 closed / 1 partial (`seeds_positive` token).
DS: 10 closed; 4 material text/schema gaps.
Sol: most closed; phase-7 prefix bound remains.

---

## 3. 남은 Must-fix

### MF-1. `§13.5` `seeds_positive` 자기모순 (required/forbidden)

- §13.3 requires `registered_seeds_positive`.
- §13.5 says “no stale `registered_seeds_positive`” — reads as a ban on the required field.
- P0 helper `seeds_positive` is document count.

**v1.0.6 요구**:
- §13.5: “no legacy `seeds_positive` in registered stats; no stale registered counts.”
- keep `registered_seeds_positive` required.
- no renaming of P0 helper.

### MF-2. Replay digest byte rule

- §12.2 says SHA256 of UTF-8 bytes, but not the array envelope.
- GLM/DS: digest is **SHA256 over the canonical JSON of the sorted record array**, one array; not record-by-record concatenation.
- `c43ea…`/`8277a7…` reproduce only under array rule.

**v1.0.6 요구**:
- one line: `sha256(canonical_json(sorted_records_array))`.
- add negative test: per-record concatenation must not match.

### MF-3. Phase-7 prefix bound / equal dimensions

- Sol MF-1: exact prefix tensors and equal first dimensions for real, donor, and both controls.
- current `K_d = min(...)` but no assert that real/donor/control slices share first dim.

**v1.0.6 요구**:
- `assert real.shape[0] == donor.shape[0] == control_pos.shape[0] == control_norm.shape[0] == K_d`.
- define target/endpoint slicing.
- F/L both >753; donor <753; native512; no renormalization.
- add regression.

### MF-4. Control golden order

- DS MF-3: `6b50…` requires `M_NORM` before `M_POS_MEAN` by canonical name.
- golden file lists M_POS first; digest computed sorted.
- add `ordering` or reorder file.

**v1.0.6 요구**: reorder `control_manifest_golden.tensors` by canonical name; add ordering note.

### MF-5. Bootstrap RNG / percentile

- DS MF-4: `seed=20261109` but RNG algorithm and percentile interpolation undefined.
- `n_boot 1000`.

**v1.0.6 요구**:
- `numpy.random.default_rng(20261109)` or PCG64.
- percentile method `linear`/`midpoint` explicit.
- document CI definition.
- no threshold change.

### MF-6. Freeze handoff

- GLM MF-D, DS MF-5, Sol MF-2.
- template is not a freeze; actual `FREEZE.json` must be created after final plan commit.
- `freeze_commit` must contain final normative bytes + helper sources, but need not contain manifest.
- D0 report records `freeze_manifest_sha256`.

**v1.0.6 요구**:
- freeze order: final plan commit → populate `_FREEZE.json` → manifest commit → D0 report includes manifest sha.
- no code before freeze.

### MF-7. Postrun/P1 coverage

- DS MF-6: postrun coverage over glob registry; P1 self-listing.
- registry v2 has patterns; postrun must expand actual.

**v1.0.6 요구**:
- postrun expands globs; lists actual files; self-lists `p1_usage.postrun.json`.
- missing → NA.

### MF-8. P0/schema/misc

- P0 source length 256 limitation line.
- `schema_version` in freeze manifest.
- `MARGINAL_SIGNAL_COHORT` informational.
- §13.4 wording.

**v1.0.6 요구**: one-line clarifications.

---

## 4. 검토자별 핵심

### GLM — CONTINUE(조건부)

- 9 closed / 1 partial (`§13.5` token).
- MF-A token, MF-B array digest, MF-C step-5 split, MF-D freeze order.
- freeze after MF-A/B; implementation+D0 conditional.
- golden 5종/preflight/P0 independently reproduced.

### DS 1017 — NARROW

- 10 closed.
- MF-1 §13.5 self-contradiction; MF-2 array digest; MF-3 control order; MF-4 bootstrap; MF-5 freeze commit; MF-6 postrun; MF-7 P0/schema.
- freeze after MF-1..4 ERRATA.

### Sol — NARROW

- phase-7 prefix bound (MF-1).
- actual freeze handoff (MF-2).
- no freeze as-is.

---

## 5. 결정

```text
v1.0.5 = 동결 보류 (1 CONTINUE / 2 NARROW)
v1.0.6/ERRATA = 필요 (text/schema only)
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

1. v1.0.6 text/schema:
   - §13.5 token
   - array digest rule
   - phase-7 equal-dim assert
   - control golden order
   - bootstrap RNG/percentile
   - freeze order/manifest sha
   - postrun/P1 coverage
   - P0/schema/misc
2. v1.0.6 review
3. freeze manifest + content SHA
4. 구현 + unit tests
5. D0
6. D1 separate
7. 3-seed separate

---

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_5_2026-11-09/review_GLM.md` | GLM |
| `.../review_DS1017.md` | DeepSeek |
| `.../review_SOL.md` | Sol |
| `reports/C5_B0A_PM_PREREG_V1_0_5_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |
| `docs/plan_c5_b0a_pm_prereg_v1_0_5.md` | v1.0.5 |
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_5_2026-11-09/golden_vectors.json` | golden |

## 8. 제한

- 이 종합은 승인이 아니다.
- NARROW 2/3가 우세하다.
- v1.0.6 없이 코드를 작성하지 않는다.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아니다.
- golden digests are verified constants, not results.
