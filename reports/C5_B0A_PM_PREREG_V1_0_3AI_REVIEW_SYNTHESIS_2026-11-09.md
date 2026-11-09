# C5 Phase 6 v1.0 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v1_0_2026-11-09/`
- 검토 기준 HEAD: `78fa7b4` (v1.0 plan은 `63876ce`, consolidation record `631e180`)
- 모델:
  - GLM 5.3 Flash **max** — 29,027 chars
  - Claude Sonnet 5.5 **medium** — 18,062 chars
  - Sol 6.1 **medium** — 30,280 chars
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V1_0_2026-11-09.md`
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **3/3 NARROW.** v1.0은 r3.4 Must-fix 대부분을 실제로 닫고 golden digest까지 재현됐지만, **P/PA M cohort가 20 native와 15 common으로 이중 진술**되어 gate arithmetic/1,440 endpoint가 성립하지 않는다. 추가로 **donor selection rule, "shuffled donor" 정의, path flags, measurement semantics, replay mechanics, M tensor hash binding**이 필요하다. **v1.0 freeze 불가. v1.0.1/ERRATA로 text-only repair 후 재검토.**

---

## 1. 판정 행렬

| 검토자 | 모델 | 판정 | v1.0 freeze | 구현+unit tests | D0 | D1 | 3-seed |
|---|---|---|---|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **NARROW** | 아니오 | 아니오 | 아니오 | 미승인 | 미승인 |
| Sonnet | `claude-sonnet-5-5` medium | **NARROW** | 아니오 | 아니오 | 아니오 | 미승인 | 미승인 |
| Sol | `gpt-6.1-sol` medium | **NARROW** | 아니오 | 아니오 | 아니오 | 미승인 | 미승인 |
| **종합** | — | **NARROW 3/3** | **미승인** | **미승인** | **미승인** | **미승인** | **미승인** |

- STOP 0/3.
- CONTINUE 0/3.
- NARROW 3/3.
- **만장일치 NARROW** → freeze하지 않는다.

---

## 2. 실제로 닫힌 것

세 검토자가 인정한 항목:

- **variant×memory_kind table**: M_POS_MEAN/M_NORM distinct controls
- **L direct binding** `l_copy_signal := L_COPY_SIGNAL`
- **signal-tail variant=NA**, M tails descriptive
- **PA_VALID** direct 20-native definition
- **F/L K=753 M-only**, training/eval donor-crop, generation 20×256
- **top3 absolute `.43355` vs signed `.4862`**
- **documents_positive**
- **golden digests** all three independently verified
- **preflight hash** verified
- **cap arithmetic** 1,200/1,204/155/96
- **endpoint 1,440** arithmetic
- **no stale chain references** in normative sections
- **banned-term scan** only prohibition lists

GLM: 17/18 r3.4 blockers closed at text level. Sonnet/Sol: substantial consolidation, not just precedence.

---

## 3. 남은 Must-fix

### MF-1. P/PA M cohort 이중 진술 (blocker)

**문제**

- §4.5/§5.2/§8.3: P/PA `m_pass_pos/norm` = **20 native docs**.
- §9.1: P/PA M targets = **15 common**.
- §9.5: exact endpoint set `15×3×4×2×2×2 = 1,440`, 15 targets ×96.
- An implementation cannot both reject extra native keys and evaluate missing 5 native targets.
- `m_valid` is a gate input → cohort must be unique.
- Sol: mixed domain needs `(15+15+20+20)×3×2×2×2 = 1,680`; or 1,440 + 240 native calibration.
- D1 phase 5: F/L 120 each + P/PA 160 each = **560**, not 480.

**v1.0.1 요구**

- Choose one:
  - **Option A (mixed)**:
    - F/L: 15 common
    - P/PA: 20 native
    - primary records = **1,680**
    - 15 common targets ×96; 5 native-only targets ×48
    - D1 phase 5 = 560
    - endpoint_ok exact mixed key set
  - **Option B (common-only audit + native calibration)**:
    - primary M 1,440 common records
    - +240 native-only P/PA calibration records
    - both key sets explicitly validated
    - D1 phase 5 = 560
- No silent subset.
- Missing native doc → NA/`M_NOT_EVALUABLE`, not drop.
- Propagate to builder, endpoint_ok, manifest, replay, tests, T_proj.

### MF-2. Donor selection rule (high)

- 5 donors, length-matched nearest, exclude self, deterministic tie-break, donor_id 0..4.
- Only implicit in runner `native_donors_for`; not normative.
- v1.0.1: define function, ordering, tie-break (e.g., `|len diff|`, then doc_id asc), ordinal mapping, donor pool val20, crop `K=min(len_real,len_donor)`.
- donor list artifact.

### MF-3. "Shuffled donor" definition (high)

- Legacy name; must state **wrong-donor memory**, not token shuffling.
- Memory computed from different length-matched donor document; cropped; averaged over 5 donors.
- v1.0.1: define `shuffled_copy_ce/full_ce` aggregation across donors; per-doc mean.

### MF-4. Path flags (medium)

- `assay_path_ok`, `p0_path_ok`, `p_step100_path_ok`, `pa_step100_path_ok` used but undefined.
- v1.0.1: table with computing function, artifact, true/false/NA conditions.
- this is last chain-inherited definition.

### MF-5. Measurement semantics (high; Sonnet/Sol)

- training loss/label format.
- `copyable_mask`/`copy_ce`, copy tokens ≥5 count.
- F/L adapter initialization (only PA random stated).
- source prefix/tokenization (`summarize: `, native 512).
- generation decoding settings.
- v1.0.1 §2.5 "Measurement semantics" normative, not code-by-reference.
- If runner inherited, pin runner commit + function hashes.

### MF-6. Replay mechanics (high; Sol)

- Dimensions/digest defined, but actual replay procedure not:
  - same-state restore/reload.
  - which checkpoint/mode.
  - donor-free vs donor diagnostic.
  - comparison pair and tolerance.
  - debug vs final.
- v1.0.1: define replay as a procedure, not just schema.
- phase 7 scope explicit.
- numeric tolerance vs hash separation.

### MF-7. M tensor hash binding (medium; GLM)

- §12.1 checkpoint hash covers adapter+LoRA, not `M_POS_MEAN`/`M_NORM`.
- Add M tensors or digests to hash domain/manifest.
- exact control tensors re-derivable.

### MF-8. Training vs eval cohort wording (low)

- §2.3 "training/eval signal all 20 docs" reads as training donor-crop; training has no donor.
- split train20@512 vs val20@512.
- training forward uses real memory; donor-crop applies eval endpoints.

### MF-9. Bindings/axis/golden (low)

- `p_valid := P_VALID`, `pa_valid := PA_VALID`, `m_pass_* := M_PASS_*`.
- §7.1 calibration axis count (3^6 including m_pass_l's two operands).
- supplemental replay golden (donor 0..4 / P or PA / M_NORM).

---

## 4. 검토자별 차이

### GLM — NARROW

- 17/18 r3.4 blockers closed.
- MF-V1-1 cohort blocker.
- donor rule, shuffled donor, path flags, M tensor hash, wording, bindings.
- Q13 NARROW; freeze after MF-V1-1..4.

### Sonnet — NARROW

- P/PA cohort/record counts contradiction.
- replay procedure, path flags, measurement semantics.
- training loss/label/copy mask/donor/F-L init/tokenization/generation undefined.
- Q13 NARROW; repair then freeze.

### Sol — NARROW

- native-20 calibration cannot implement with 1,440.
- mixed domain 1,680 or 1,440+240; D1 560.
- training vs eval crop.
- operational identities/path evidence/manifest.
- replay mechanics.
- estimands/missingness/fixtures/launch.
- Q13 NARROW.

**해석**: 3/3 NARROW. P/PA cohort is the common blocker; measurement semantics/replay are next.

---

## 5. 결정

```text
v1.0 = 동결 보류 (3/3 NARROW)
v1.0.1 또는 v1.0 + ERRATA = 필요 (text-only)
r3.5 chain = 사용하지 않는다
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

1. **v1.0.1 text-only**:
   - MF-1 cohort resolution (prefer Option A mixed 1,680 or B 1,440+240; no gate relaxation)
   - MF-2 donor rule
   - MF-3 shuffled donor
   - MF-4 path flags
   - MF-5 measurement semantics
   - MF-6 replay procedure
   - MF-7 M tensor hash binding
   - MF-8 training vs eval wording
   - MF-9 bindings/axis/golden
2. v1.0.1 3-AI review
3. freeze commit + content SHA-256
4. 구현 + unit tests
5. D0
6. D1 separate
7. 3-seed separate
8. B0-B separate

---

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_2026-11-09/review_GLM.md` | GLM 29,027 chars |
| `.../review_SONNET.md` | Sonnet 18,062 chars |
| `.../review_SOL.md` | Sol 30,280 chars |
| `reports/C5_B0A_PM_PREREG_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |
| `docs/plan_c5_b0a_pm_prereg_v1_0.md` | v1.0 |
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_2026-11-09/golden_vectors.json` | golden |

## 8. 제한

- 이 종합은 승인이 아니다.
- 3/3 NARROW는 만장일치다.
- v1.0.1 없이 코드를 작성하지 않는다.
- “54 tests”는 historical evidence이며 PM tests는 아직 없다.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아니다.
- golden digests are verified constants, not results.
