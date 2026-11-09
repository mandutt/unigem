# C5 Phase 6 v1.0.1 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v1_0_1_2026-11-09/`
- 검토 기준 HEAD: `30b6219` (v1.0.1 plan은 `7ecf973`)
- 모델:
  - GLM 5.3 Flash **max** — 15,930 chars
  - DeepSeek V4.1 Flash **1017** **high** — 24,166 chars
  - Sol 6.1 **medium** — 26,851 chars
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V1_0_1_2026-11-09.md`
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **3/3 NARROW.** v1.0.1은 mixed 1,680 / D1 560 / phase 7 600 산술과 golden digest를 모두 재현했고, measurement semantics·donor rule·path flags·replay procedure·control digest를 실제로 추가했다. 그러나 **P0 `p0_path_ok` 불일치, donor length authority 모순, replay control tensor 비재생, `test_split_used`/P1 순환, `h_len`/data path 미정의, P/PA seed aggregation 누락, P/PA alias와 `M_CONTROL_INVALID` unreachable** 때문에 freeze할 수 없다. **v1.0.2/ERRATA** 후 재검토.

---

## 1. 판정 행렬

| 검토자 | 모델 | 판정 | v1.0.1 freeze | 구현+unit tests | D0 | D1 | 3-seed |
|---|---|---|---|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **NARROW** | 아니오 | 아니오 | 아니오 | 미승인 | 미승인 |
| DeepSeek 1017 | `deepseek-v4.1-flash-1017` high | **NARROW** | 아니오 | 아니오 | 아니오 | 미승인 | 미승인 |
| Sol | `gpt-6.1-sol` medium | **NARROW** | 아니오 | 아니오 | 아니오 | 미승인 | 미승인 |
| **종합** | — | **NARROW 3/3** | **미승인** | **미승인** | **미승인** | **미승인** | **미승인** |

- STOP 0/3.
- CONTINUE 0/3.
- NARROW 3/3.
- 만장일치 NARROW → freeze하지 않는다.

---

## 2. 실제로 닫힌 것

세 검토자가 인정한 항목:

- mixed M domain **1,680**
  - F/L 15 common
  - P/PA 20 native (15 common + 5 native-only)
  - common ×96, native-only ×48
- D1 phase 5 **560**
- phase 7 **600/arm-seed**
- measurement semantics §2.5
- donor algorithm 기본
- `shuffled` = wrong-donor definition
- path flags §4.0
- replay procedure §11.4
- `control_digest` §12.1
- P/PA 20 native bindings
- training real-only vs eval donor-crop
- full_k historical only
- 3^6 calibration axis
- golden digests 3종 재현
- preflight hash 재현
- cap arithmetic 1,204/155/96

GLM: v1.0 Must-fix 9개가 text-level로 닫힘. DS: v1.0.1이 v1.0 textual Must-fix를 실제로 닫음. Sol: mixed repair는 real.

---

## 3. 남은 Must-fix

### MF-1. P0 `p0_path_ok` 불일치 (blocker)

**문제**

- §4.0 `p0_path_ok`는 `no_training=true` 요구.
- 실제 `p0_native_sanity.json` top-level keys:
  - `experiment, mode, model, source_prefix, source_max_length, donor_count, splits, interpretation, test_split_used`
  - **`no_training` 없음**
- strict: `p0_path_ok=false` → `ASSAY_INVALID` for every run.
- present-but-inconsistent: false; missing: NA; missing field NA도 pass하지 않음.

**v1.0.2 요구**

- Option A: P0 artifact에 `no_training:true`를 추가하는 **versioned integrity attestation** (결과 변경 없음).
- Option B: `p0_path_ok`를 `mode=p0_sanity_no_training` + `test_split_used=false`로 수정.
- legacy P0 compatibility rule 명시.
- P0 result 수정 금지.

### MF-2. Donor basis 모순 (blocker)

**문제**

- §2.5.6: "same donor set for all arms/seeds".
- also: "donor lengths from the same cache as the real document".
- native lengths all 512; EG2 lengths 708–830.
- For `REPORT-news_r-04161-00002`:
  - EG2 nearest: `04798,03991,05258,03271,01058`
  - native nearest: `00020,00430,01058,01127,01331`
- cannot be same donor set under both rules.

**v1.0.2 요구**

- canonical donor length map:
  - F/L: EG2 layer19 h_len
  - P/PA: native source length (all 512)
- **donor lists per arm**, not “same across all arms”.
- if shared donor policy intended, pin one map and use crop lengths separately.
- train20 docs donor pool = val20? Define.
- donor list artifact.

### MF-3. Replay control tensor 비재구성 (blocker)

**문제**

- `control_digest`는 SHA256.
- §11.4 loads “control_digest manifest” and recomputes 1,680 CE.
- hash cannot supply `M_POS_MEAN`/`M_NORM/t`.
- Need store tensors or deterministic rebuild.

**v1.0.2 요구**

- `control_manifest` includes:
  - `M_POS_MEAN` tensor or `npz` path + hash
  - `M_NORM(t)` tensor or norm ratio + base + hash
  - per arm/seed/target.
- replay loads tensors, verifies digest, recomputes CE.
- hash-only manifest insufficient.

### MF-4. `test_split_used`/P1 verification 순환 (high)

**문제**

- §4.0 defines test_split_used by scanning artifacts for test IDs.
- test 163 sealed; no test-ID manifest or P1 usage artifact.
- Can't prove absence by scanning sealed data.
- `assay_path_ok` unknown/failure precedence undefined.

**v1.0.2 요구**

- frozen ID allowlist: train20/val20/common only.
- reject any ID outside allowlist.
- P1 usage manifest with explicit `p1_used=false`.
- missing/unreadable/malformed → NA or false per known-failure rule.
- no test file read.

### MF-5. `h_len`/data path/self-containedness (high)

**문제**

- `h_len` used for cohort/zero-margin/donor/builder but not defined.
- EG2 cache path/format, split file, JSONL schema, record fields not pinned.
- `copyable_mask` source passage vs prefixed source ambiguous.
- runner is implicit authority.

**v1.0.2 요구**

- implementation appendix:
  - `h_len` F/L = EG2 layer19 cache sequence length
  - `h_len` P/PA = native source length after `summarize: ` truncation 512
  - cache path `data/wave2c/eg2_native_layer19/layer19`
  - split path `reports/provenance/C5_clean/splits.json`
  - JSONL fields.
- `copyable_mask` source = raw passage (no prefix).
- runner commit/function hashes or normative aliases.

### MF-6. P/PA seed aggregation (high)

**문제**

- §4.5 doesn't state whether `P_POS_PASS`/`PA_POS_PASS` use 3 seeds, seed-average before bootstrap, or per-seed.
- P/PA 20 native docs; 3 seeds.

**v1.0.2 요구**

- 3 registered seeds.
- seed-average before bootstrap.
- missing seed → NA.
- `seeds_positive` count.
- same as L.
- no 2/3 substitution.

### MF-7. P/PA alias / `M_CONTROL_INVALID` unreachable (blocker/high)

**문제**

- `p_valid = ANDn(P_POS_PASS,P_NORM_PASS)`
- `pa_valid = ANDn(PA_POS_PASS,PA_NORM_PASS)`
- `m_valid = ANDn(p_valid,pa_valid)`.
- Under false-dominant ANDn, p/pa true implies m_valid true.
- §5.4 exits on p/pa false before `m_valid`.
- `M_CONTROL_INVALID` and labels `L_SIGNAL_M_CONTROL_INVALID`/`NO_L_SIGNAL_CONTROL_INVALID` unreachable.
- Conflicts “every label reachable.”
- threshold naming: §4.5 P/PA copy `.05` vs §9.6 M copy `>0`.

**v1.0.2 요구**

- Decide:
  - **Option A**: validity and calibration are same tests; remove `M_CONTROL_INVALID` reachability obligation, mark reserved, adjust labels/tests.
  - **Option B**: distinct validity; define separate pre-outcome gate; review.
- preserve numeric thresholds.
- Write direct L aliases.
- no fabricated label.

### MF-8. Copy-token threshold contradiction (medium)

- §2.5.5: <5 copy tokens → copy endpoint excluded.
- §9.5: exact 1,680, no missing key, copy≥5.
- If any target <5, cannot both.
- v1.0.2: primary M endpoint <5 → `endpoint_ok=false` → `M_NOT_EVALUABLE`; §2.5.5 “exclude” applies only to signal/eval `n_signal`.
- no value change.

### MF-9. Phase-7 tensor recipe (medium)

- 600 count fixed; content undefined.
- define:
  - `K_d=min(len(real),len(donor))`
  - control = variant cropped to K_d
  - real = A(h_t)[:K_d]
  - donor only determines crop
  - variant/endpoint/memory mapping.
- stored baseline.

### MF-10. Threshold asymmetry intent (medium)

- P/PA validity copy `.05`; M_PASS copy `>0`.
- v1.0.2: intentional: validity=acquisition strength; calibration=direction.
- no post-result change.

### MF-11. F11 label undefined (medium)

- §7.2 says small-N + validity INVALID; not §6.2 enum.
- v1.0.2: one of four small-N labels + explicit tuple `(validity=INVALID,...)`.

### MF-12. Training mode / RNG order (medium)

- base decoder eval; adapter/LoRA modes not fully specified.
- RNG construction order adapter vs LoRA not fixed.
- v1.0.2: mode table per arm, fresh state, reseed order, parameter inventory.

### MF-13. T_proj primary replay (high)

- formula includes phase-7 diagnostic, not primary 1,680 replay.
- v1.0.2: include primary replay 560 (D1) / 1,680 registered; debug vs registered.
- no cap relaxation.

### MF-14. D1 `no labels`/`not_a_result` (medium)

- phase 5 computes CE; “no labels” means no decision labels, not no target tokens.
- D1 `not_a_result:true` explicit.
- v1.0.2.

### MF-15. Golden coverage/header (low)

- only one replay vector; no P/PA, M_NORM, donor 0..4.
- golden file says `spec v1.0`.
- v1.0.2: update spec label + add P/PA/M_NORM/donor vector.

---

## 4. 검토자별 차이

### GLM — NARROW

- v1.0 Must-fix 9개 text-level closed.
- R1 copy threshold, R2 phase-7, R3 threshold asymmetry, R4 train donor pool, R5 low.
- freeze after R1–R4.

### DeepSeek 1017 — NARROW

- mixed 1,680 correct.
- MF-1017-1 P0 path; MF-1017-2 donor; MF-1017-3 replay tensors; MF-1017-4 test_split/P1; MF-1017-5 h_len/data; MF-1017-6 P/PA aggregation; plus 7–13.
- v1.0.2/ERRATA.

### Sol — NARROW

- MF-1 P/PA aliases → unreachable; MF-2 donor authority; MF-3 P0 compatibility; MF-4 replay/timing; MF-5 training mode/RNG.
- freeze no.

**해석**: 3/3 NARROW. Structural arithmetic fixed; remaining are contract-binding defects.

---

## 5. 결정

```text
v1.0.1 = 동결 보류 (3/3 NARROW)
v1.0.2/ERRATA = 필요 (text-only)
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

1. v1.0.2 text-only:
   - P0 path flag
   - donor basis
   - control tensors
   - test_split/P1 manifest
   - h_len/data paths
   - P/PA seed aggregation
   - P/PA alias/`M_CONTROL_INVALID`
   - copy-token threshold scope
   - phase-7 tensor recipe
   - F11 label
   - training mode/RNG
   - primary replay in T_proj
   - D1 no labels/not_a_result
   - golden coverage
2. v1.0.2 review
3. freeze commit + content SHA256
4. 구현 + unit tests
5. D0
6. D1 separate
7. 3-seed separate
8. B0-B separate

---

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_1_2026-11-09/review_GLM.md` | GLM |
| `.../review_DS1017.md` | DeepSeek |
| `.../review_SOL.md` | Sol |
| `reports/C5_B0A_PM_PREREG_V1_0_1_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |
| `docs/plan_c5_b0a_pm_prereg_v1_0_1.md` | v1.0.1 |
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_2026-11-09/golden_vectors.json` | golden |

## 8. 제한

- 이 종합은 승인이 아니다.
- 3/3 NARROW는 만장일치다.
- v1.0.2 없이 코드를 작성하지 않는다.
- “54 tests”는 historical evidence이며 PM tests는 아직 없다.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아니다.
- golden digests are verified constants, not results.
