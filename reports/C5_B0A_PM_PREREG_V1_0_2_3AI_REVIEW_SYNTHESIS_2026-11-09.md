# C5 Phase 6 v1.0.2 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v1_0_2_2026-11-09/`
- 검토 기준 HEAD: `ee99fd0`
- 모델:
  - GLM 5.3 Flash **max** — 23,703 chars
  - DeepSeek V4.1 Flash **1017** **high** — 28,333 chars
  - Sol 6.1 **medium** — 31,387 chars
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V1_0_2_2026-11-09.md`
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **3/3 NARROW.** v1.0.2는 15개 v1.0.1 blocker 중 대부분(12 closed, 3 partial)을 실제로 닫았고, `P_VALID`/`PA_VALID` 분리·donor arm-specific·control tensor 저장은 타당하다. 그러나 **golden/replay key가 `donor_sort`와 `donor_id`로 갈라져 mandatory replay test가 불만족**, **단일 `final_checkpoint_hash`로 1,680 records를 재생할 수 없음**, **per-arm replay 420/420 오류(360/480)**, **phase-7 enum/CE binding 미완**, **supplemental golden이 canonical order 위반**이라 freeze할 수 없다. **v1.0.3/ERRATA text-only** 후 재검토.

---

## 1. 판정 행렬

| 검토자 | 모델 | 판정 | v1.0.2 freeze | 구현+unit tests | D0 | D1 | 3-seed |
|---|---|---|---|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **NARROW** | 조건부(수정 후) | freeze 후 | freeze 후 | 미승인 | 미승인 |
| DeepSeek 1017 | `deepseek-v4.1-flash-1017` high | **NARROW** | 아니오(ERRATA 후) | 조건부 | 조건부 | 미승인 | 미승인 |
| Sol | `gpt-6.1-sol` medium | **NARROW** | 아니오 | 아니오 | 아니오 | 미승인 | 미승인 |
| **종합** | — | **NARROW 3/3** | **보류** | **보류** | **보류** | **미승인** | **미승인** |

- STOP 0/3.
- CONTINUE 0/3.
- NARROW 3/3.
- GLM은 “NMF-1/NMF-2 수정 후 freeze 가능”이라는 조건부 표현을 썼지만 최종 category는 NARROW.
- DS/Sol은 명시적 “no freeze as-is”.

---

## 2. 실제로 닫힌 것

세 검토자가 공통 인정한 항목:

- P0 `p0_path_ok` mode-only 호환 — **closed**
- donor arm-specific — **closed**; F/L vs P/PA 분리 정당
- `P_VALID`/`PA_VALID` validity 분리 — **closed**; `M_CONTROL_INVALID` conditional reachable
- `p1_usage.json` 존재와 allowlist — **부분 closed**
- `h_len`/data path §2.6 — **closed**
- P/PA 3-seed aggregation — **closed**
- copy-token `<5` scope — **closed**
- threshold asymmetry — **closed**
- training mode/RNG §2.7 — **closed**
- D1 `not_a_result`/`labels_computed` — **closed**
- 1,680 / 560 / 600 산술 — **closed**
- `M_CONTROL_INVALID` unconditional 아님 — **확인**
- control_manifest ~0.3GB — **수용 가능**
- donor arm-specific이 F/L/P/PA 비교를 해치지 않음 — **확인**

DS 집계: 15개 중 **12 closed, 3 partial**.
Sol: 15개 중 5개 partial (3 replay control tensors, 4 test/P1, 9 phase-7, 13 T_proj, 15 golden).
GLM: 15개 blocker는 대부분 닫혔으나 **NMF-1~5** 신규.

---

## 3. 새 blocker

### MF-1. Golden/replay key: `donor_sort` vs `donor_id` (blocker)

- §12.2 canonical key: `(doc_id, arm, seed, variant, endpoint, memory_kind, donor_sort)`.
- golden base/supplemental records use `donor_id`.
- DS verified divergent hashes:
  - key `donor_sort`: `32db40…` / `1ccdee…`
  - key `donor_id`: `c43ea…` / `38e5e2f…`
- golden constants match `donor_id`, not `donor_sort`.
- mandatory replay test would be unsatisfiable.

**v1.0.3 요구**: canonical key를 **`donor_id`**로 통일하고 `donor_sort`는 internal derived field로만 정의. 기존 base digest `c43ea…` 보존.

### MF-2. 단일 checkpoint로 1,680 replay 불가 (blocker)

- §11.4 step 1: “load `final_checkpoint_hash` state” singular.
- 1,680 M records span **4 arms × 3 seeds = 12 units**.
- one checkpoint cannot produce all 12.

**v1.0.3 요구**:
- `final_checkpoint_hash[arm/seed]` 12개.
- per-unit replay: F/L 120, P/PA 160 D1; registered 360/480.
- aggregation to 1,680.
- no single-checkpoint claim.

### MF-3. Per-arm registered replay 420/420 오류 (high)

- §11.5 says F/L 420, P/PA 420.
- Correct:
  - F/L: 15 docs ×2×2×2 ×3 seeds = **360**
  - P/PA: 20 docs ×2×2×2 ×3 seeds = **480**
  - total **1,680**
- 420 = 1,680/4 is wrong equal split.

**v1.0.3 요구**: 360/480, `t_primary_replay_arm` 동일 수정, D1은 120/160.

### MF-4. Phase-7 enum / CE binding / donor_prefix (high)

- §9.6.1 `memory_kind ∈ {real, donor}`.
- §12.2 `memory_kind ∈ {control, real}`.
- golden supplemental has `donor`.
- `donor_prefix` unbound.
- 600 count correct but **CE quantity** not bound: raw real/donor CE vs contrast vs shared baseline.
- variant axis may duplicate identical CE.

**v1.0.3 요구**:
- general enum `memory_kind ∈ {control, real, donor}`.
- phase 5 subset `{control, real}`, `donor_id=null`.
- phase 7 subset `{real, donor}`, `donor_id=0..4`.
- define `donor_prefix` construction and K.
- define stored `ce` = raw CE for the record’s tensor; no derived contrast.
- define baseline separately.
- phase 7 diagnostic only.

### MF-5. Supplemental golden canonical order (high)

Sol independently computed:

| serialization | SHA256 |
|---|---|
| insertion order | `38e5e2fbbcd30922902e456bb6f16cfca71f6f3b4afedd3806313cb0a08f6695` |
| normative ascending record order | `8277a713fd52b2ba8c5c3c859c83fd78593aa5a381f8640448e2128a97af7a20` |
| base replay normative order | `c43ea35c46c51a0e82cebe5764a989d1b67012b2690246a0f89a94dff7851667` |
| state framing | `43ecb58e197d5789df0a9dbbc67beba11538b8063c3da8ac46f96e1e95d65712` |

- `sort_keys` only sorts object keys, not array records.
- PA rows `real` before `donor` violates ascending string order.
- supplemental digest is not canonical.

**v1.0.3 요구**:
- define `records.sort(key=...)` ascending.
- recompute supplemental digest with independent script; expected `8277a7…` if same records.
- add permutation-invariance test.
- keep base/state unchanged.

### MF-6. P1/test attestation (high)

- §4.0 `assay_path_ok` consumes only `p1_used=false`.
- `test_split_read=false` exists but is not gated.
- malformed/missing field handling unspecified.
- “checked artifacts” unenumerated.
- false declaration is not self-authenticating.

**v1.0.3 요구**:
- strict booleans `p1_used=false` **and** `test_split_read=false`.
- manifest SHA256 + path.
- checked artifact inventory.
- malformed/absent → NA.
- contradictory known-use → false.
- state trust boundary; no claim of forgery detection.

### MF-7. `P_VALID` tri-state / F9 unreachable (medium)

- `P_VALID` includes path validity.
- F9 premise `p_step NA + p_valid false` unreachable.
- missing vs nonfinite tri-state undefined.

**v1.0.3 요구**:
- explicit `P_VALID ∈ {true,false,NA}`:
  - path false → false
  - missing/unreadable → NA
  - nonfinite → false
- F9 rewrite to reachable combination.
- no threshold change.

### MF-8. Control tensor serialization (medium)

- frame requires `name`; control names/order not defined.
- `M_POS_MEAN` no target ID; NPZ `target_id` generic.
- NPZ array key and hash target (framed payload vs archive bytes) unspecified.

**v1.0.3 요구**:
- versioned payload schema.
- canonical names: `arm/seed/M_POS_MEAN`, `arm/seed/M_NORM/{target_id}`.
- array key `tensor`.
- dtype `<f4`, shape, target_id sentinel.
- hash over canonical tensor frame, not ZIP bytes.
- tiny multi-tensor control golden.

### MF-9. P/PA vs L calibration asymmetry (low)

- L uses `2/3 seeds_positive` + paired `L>F`.
- P/PA calibration omits both.

**v1.0.3 요구**: document intentional arm asymmetry or add conjuncts. No threshold change.

### MF-10. D0/cap/artifact (low)

- D0 `≤4 configs` undefined.
- control_manifest ~0.3GB not in artifact list/path/retention.
- native-512 assert missing.

**v1.0.3 요구**: define 4 configs, artifact path/retention, D0 512 assert.

---

## 4. 검토자별 핵심

### GLM — NARROW

- 15 blockers 대부분 closed.
- NMF-1: 420→360/480.
- NMF-2: phase-7 domain mismatch.
- NMF-3: §13.4 supplemental digest test.
- NMF-4: p1 malformed.
- NMF-5: D0 ≤4 configs.
- “NMF-1/NMF-2 수정 후 freeze 가능” but final NARROW.

### DS 1017 — NARROW

- 12 closed / 3 partial.
- MF-1 donor_sort/donor_id blocker; verified divergent hashes.
- MF-2 single checkpoint replay blocker.
- MF-3 420 count; MF-4 phase-7; MF-5 P_VALID/F9; MF-6 P1; MF-7 asymmetry; MF-8 native assert; MF-9 footprint.
- Freeze no.

### Sol — NARROW

- MF-1 supplemental ordering `38e5` vs `8277`.
- MF-2 420 counts/timing mapping.
- MF-3 phase-7 CE/domain.
- MF-4 P1 fail-closed.
- MF-5 control tensor schema.
- Freeze no; text/golden correction only.

---

## 5. 확인된 반론

- **`P_VALID` 약화 → `M_CONTROL_INVALID` unconditional?** 아님.
  - `m_evaluable` + `p_valid` + `pa_valid` + `m_valid=false` 필요.
  - integrity failure → `M_NOT_EVALUABLE`.
- **control_manifest 과중?** 아님. ~0.3GB, 12-unit 규모 수용.
- **donor arm-specific이 비교 훼손?** 아님. arm 내부 비교; cross-arm geometry caveat 존재.

---

## 6. 결정

```text
v1.0.2 = 동결 보류 (3/3 NARROW)
v1.0.3/ERRATA = 필요 (text/golden/schema only)
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

## 7. 다음 단계

1. v1.0.3 text/golden/schema:
   - `donor_id` canonical key
   - 12 checkpoint replay
   - 360/480
   - phase-7 enum/CE
   - supplemental digest `8277a7…`
   - P1 strict both flags
   - P_VALID tri-state/F9
   - control tensor schema
   - P/PA asymmetry
   - D0 config/artifact
2. v1.0.3 review
3. freeze commit + SQLite? no; content SHA256
4. 구현 + unit tests
5. D0
6. D1 separate
7. 3-seed separate

---

## 8. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_2_2026-11-09/review_GLM.md` | GLM |
| `.../review_DS1017.md` | DeepSeek |
| `.../review_SOL.md` | Sol |
| `reports/C5_B0A_PM_PREREG_V1_0_2_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |
| `docs/plan_c5_b0a_pm_prereg_v1_0_2.md` | v1.0.2 |
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_2_2026-11-09/golden_vectors.json` | golden |

## 9. 제한

- 이 종합은 승인이 아니다.
- 3/3 NARROW는 만장일치다.
- v1.0.3 없이 코드를 작성하지 않는다.
- “54 tests”는 historical evidence이며 PM tests는 아직 없다.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아니다.
- golden digests are verified constants, not results.
