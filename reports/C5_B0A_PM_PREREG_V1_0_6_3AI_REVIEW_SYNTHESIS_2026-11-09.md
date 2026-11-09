# C5 Phase 6 v1.0.6 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v1_0_6_2026-11-09/`
- 검토 기준 HEAD: `4a97c21`
- 모델:
  - GLM 5.3 Flash **max** — 8,651 chars, **process-level invalid**
  - DeepSeek V4.1 Flash **1017** **high** — 9,260 chars, **NARROW**
  - Sol 6.1 **medium** — 18,158 chars, **NARROW**
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V1_0_6_2026-11-09.md`
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **2/2 실질 NARROW + GLM invalid.** v1.0.6은 array digest, equal-dim assert, control order, bootstrap RNG, postrun coverage를 닫았지만, **§16.2 freeze schema의 `plan_path`가 여전히 `v1_0_5.md`**, **`T_proj`가 arm-seed 120/160과 360/480을 혼용해 triple-count 위험**, **phase-7 prefix가 `K_M` bounded라는 보장이 없음**, **`freeze_commit` 정의와 key-coverage wording**이 남아 동결할 수 없다. **v1.0.7/ERRATA text/schema only.**

---

## 1. 판정 행렬

| 검토자 | 모델 | 판정 | 비고 |
|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **NARROW (process)** | HEAD/verbatim quote 부재를 이유로 내용 검증 없음; 유효 표로 사용하지 않음 |
| DeepSeek 1017 | `deepseek-v4.1-flash-1017` high | **NARROW** | MF-1..5 |
| Sol | `gpt-6.1-sol` medium | **NARROW** | MF-1..2 |
| **종합** | — | **NARROW** | **동결 보류** |

- 실질 NARROW 2/2.
- GLM은 process-level invalid; 재디스패치 없이 content verdict로 쓰지 않는다.
- STOP 0.

---

## 2. 실제로 닫힌 것

- array digest 규칙 — **closed**
- phase-7 equal-dim assert — **partial**
- control golden canonical order — **closed**
- bootstrap RNG/percentile — **closed**
- §13.5 문구 — **closed**
- P1/postrun glob — **closed**
- P0 256/schema_version — **closed**
- golden `c43ea…`/`8277a7…`/`6b50…` — **verified**
- 1,680/560/600 — **verified**

---

## 3. 남은 Must-fix

### MF-1. §16.2 freeze 경로가 v1.0.5 (blocker)

- `docs/plan_c5_b0a_pm_prereg_v1_0_6.md` §16.2 schema:
  - `plan_path` still `docs/plan_c5_b0a_pm_prereg_v1_0_5.md`
  - freeze manifest path still `..._v1_0_5_FREEZE.json`
- template is v1_0_6.
- implementer can faithfully hash/freeze the superseded plan.

**v1.0.7 요구**:
- all §16.2 paths → `v1_0_6` (or `v1_0_7`).
- template and schema identical.
- add path assertion.

### MF-2. `T_proj` 120/160 vs 360/480 (high)

- `t_primary_replay_arm` says “D1 120/160; registered 120/160 per seed; 360/480 per arm across 3 seeds”.
- formula already multiplies by 3 outside.
- reading 360/480 as input triple-counts.

**v1.0.7 요구**:
- term is **per-seed 120/160 only**.
- 360/480 is descriptive aggregate, not an input.
- add arithmetic unit test: `3 * sum(120/160)`.

### MF-3. key-coverage wording (medium)

- §11.4 step 5 “verify key-coverage golden” can be misread as 600-record phase-7 domain.
- fixture is 4 records.

**v1.0.7 요구**: “4-record key-coverage fixture” + “600-record numeric only”.

### MF-4. `freeze_commit` definition (medium)

- is it final plan commit or manifest commit?
- DS/Sol.

**v1.0.7 요구**:
- `freeze_commit` = final plan commit (contains normative bytes/helpers).
- `manifest_commit` separate.
- `freeze_manifest_sha256` in D0 report.

### MF-5. legacy bootstrap assert (low)

- old `bootstrap_paired(seed=20261108, seeds_positive)` remains in helper.
- new stats module must not import it.

**v1.0.7 요구**: unit test `no import legacy bootstrap_paired`; no behavior change.

### MF-6. phase-7 `K_M` bound (Sol)

- `K_d=min(real,donor)` but not bounded by `K_M`.
- F/L real_prefix may be 753; donor >753? memory prefix 753; but P/PA K_M 512.
- concrete preflight cases need `K_d <= K_M`.

**v1.0.7 요구**:
- `K_d = min(K_M, len(real_prefix), len(donor_prefix))`.
- assert `K_d <= K_M`.
- slice controls/real/donor to K_d.
- no renormalization.

---

## 4. 검토자별

### GLM — process invalid

- report lacks HEAD SHA/verbatim quote; no content findings.
- NARROW process-level, not a substantive verdict.
- re-dispatch needed for a valid third opinion.

### DS 1017 — NARROW

- MF-1 §16.2 v1.0.5 path; MF-2 T_proj; MF-3 key-coverage; MF-4 freeze_commit; MF-5 legacy bootstrap.
- freeze after MF-1..4.

### Sol — NARROW

- MF-1 phase-7 K_M bound.
- MF-2 freeze/plan path.
- no freeze as-is.

---

## 5. 결정

```text
v1.0.6 = 동결 보류 (2/2 substantive NARROW; GLM invalid)
v1.0.7/ERRATA = 필요 (text/schema only)
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

1. v1.0.7:
   - §16.2 paths
   - T_proj per-seed
   - key-coverage wording
   - freeze_commit/manifest_commit
   - legacy bootstrap assert
   - K_M bound
2. v1.0.7 review (GLM 재디스패치 포함)
3. freeze manifest
4. 구현 + unit tests
5. D0
6. D1 separate
7. 3-seed separate

---

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_6_2026-11-09/review_GLM.md` | GLM process invalid |
| `.../review_DS1017.md` | DeepSeek NARROW |
| `.../review_SOL.md` | Sol NARROW |
| `reports/C5_B0A_PM_PREREG_V1_0_6_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |

## 8. 제한

- 이 종합은 승인이 아니다.
- GLM은 process-level invalid; 3-AI substantive quorum은 2/3.
- v1.0.7 없이 코드를 작성하지 않는다.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아니다.
