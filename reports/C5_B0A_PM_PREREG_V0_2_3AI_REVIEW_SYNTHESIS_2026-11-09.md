# C5 Phase 6 P/M Prereg v0.2 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v0_2_2026-11-09/`
- 검토 기준 HEAD: `918cfa5`
- 모델:
  - GLM 5.3 Flash **max**
  - Sonnet 5.5 **high**
  - Sol 6.1 **high**
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_2026-11-09.md` (352줄)
- 원문:
  - `review_GLM.md` (17,925 chars)
  - `review_SONNET.md` (32,594 chars)
  - `review_SOL.md` (38,868 chars)
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **3/3 NARROW.** v0.2는 v0.1의 핵심 구조를 개선했지만, **decision table이 total function이 아니고 PA failure cell·M_NORM gate·P/PA step0·debug seed/cap contract가 미완**이다. **v0.2.1 errata를 결과 전에 commit/freeze해야 하며, 3-seed는 별도 승인 없이는 금지**다.

---

## 1. 판정 행렬

| 검토자 | 최종 판정 | v0.2 | 구현·1-seed | 3-seed |
|---|---|---|---|---|
| GLM 5.3 Flash max | **NARROW** | 조건부 승인 (MF-1~5 후) | 승인 (MF 반영/테스트 후) | 미승인 |
| Sonnet 5.5 high | **NARROW** | **v0.2.1 errata 필요** | mechanics debug만 | 미승인 |
| Sol 6.1 high | **NARROW (conditional)** | not frozen as written | 계약 동결 후 조건부 | 미승인 |
| **종합** | **NARROW 3/3** | **v0.2.1 필요** | **별도 승인 전 미실행** | **미승인** |

STOP 0/3, CONTINUE 0/3.

---

## 2. v0.2가 실제로 고친 것

- P gate에 `.05` + full CE + CI 조건 추가
- **PA arm** 추가 (native memory + adapter + LoRA)
- M의 real reference를 full real K로 분리
- M_POS_MEAN / M_GLOBAL / M_NORM
- P/PA M validation
- `REGIME_ERASES_SELECTIVITY`, `M_CONTROL_NOT_VALID`, `L_SIGNAL_M_CONTROL_FAIL` 추가
- aligned full CE co-primary
- heavy-tail reporting
- 12 trained units / 2 CPU-hours cap

검토자들은 이 방향을 **의미 있는 개선**으로 평가했다.

---

## 3. 남은 공통 Must-fix

### MF-1. Decision table을 total function으로

- `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE`가 §6.3에는 있으나 §6.4 표에는 없다.
- **PA가 label table에 없다.**
- `(P_VALID, PA_VALID)` interaction table이 없다.
- precedence가 **L_SIGNAL을 숨길 수 있다**.
- `REGIME_ERASES_SELECTIVITY`는 observational name으로 바꾸고, “erased”는 hypothesis로 제한해야 한다.
- `COPY_ONLY_WEAK`/`FULL_ONLY_WEAK`도 M status를 확인해야 한다.

**요구**: independent flag vector + deterministic headline; 모든 truth-table cell unit test.

### MF-2. P/PA gate meaning

- P floor `.05`는 P0 mean의 약 **1%**; 거의 “학습이 99%를 지웠는가”만 검출.
- PA는 **step0 reference가 없다** (P0는 P의 step0이지만 PA의 random adapter step0은 별개).
- PA_VALID가 M_VALID/decision에 일관되게 연결되지 않는다.
- `P_RETENTION`/`PA_RETENTION`은 descriptive; hidden gate 금지.
- P/PA learning rate, parameter movement, train CE trajectory를 artifact에 기록해야 한다.

**요구**: P+PA conjunction eligibility, PA step0, retention/movement fields, `ADAPTER_...` descriptive cell.

### MF-3. M adequacy

- `M_POS_MEAN`은 LayerNorm rows의 평균이라 **norm-shrunk/OOD**.
- `M_CONTROL_PASS`가 M_POS_MEAN에만 정의되어 가장 약한 variant를 통과시킬 수 있다.
- M_NORM도 strictly target-independent가 아니다 (real norm 사용).
- M_VALID의 P/PA AND/OR, pooling, eligible target cohort, missing CI가 불명확.
- `eligible >= 10`은 train contributor 수이지 analyzable target cohort가 아니다.
- final checkpoint persistence가 필요.

**요구**: M_CONTROL_PASS에 **M_POS_MEAN AND M_NORM**; M_VALID quantifier (P AND PA, pooled); minimum target cohort; `M_NOT_EVALUABLE`; checkpoint hash.

### MF-4. Statistics contract

- bootstrap은 **seed-averaged per-doc Δ**에 문서 단위로.
- `L > F`는 paired per-doc difference로 정의.
- `2/3 seeds`는 seed-level means로 정의 (copy/full 각각).
- `seeds_positive`를 `documents_positive`로 rename.
- full CE missingness/eligibility와 copy mask eligibility 차이를 명시.
- heavy-tail: median, top-3 share, leave-top-3-out; CI-only conclusion 금지.

### MF-5. Debug protocol

- 1-seed debug가 **registered seed 20261108의 outcome**을 노출할 수 있다.
- mechanics-only debug는 unregistered seed 또는 short mechanical prefix; label 계산 금지; commit hash freeze.
- debug를 compute cap에 포함.
- 3-seed 전 acceptance check: shapes, finite, 64 modules, mode, seed reproducibility, metric alignment, artifact completeness, timing.

### MF-6. Cap and artifact contract

- wall-clock vs CPU-hour 정의.
- debug 포함 budget.
- final checkpoint/hash, code/config/input manifest.
- per-doc donor/K/crop, M eligible IDs/norm, m_eligible.
- generation workload cost를 cap에 포함.

---

## 4. v0.2.1 권고

v0.2.1은 **결과 전 errata**로 아래를 고정해야 한다.

1. full label truth table + precedence + all cells + synthetic tests
2. P/PA step0, retention/movement, PA eligibility, adapter-risk cells
3. M_POS_MEAN **AND** M_NORM pass, M_VALID quantifier, target cohort, M_NOT_EVALUABLE
4. statistics/pooling/L>F/2-of-3-seed/documents_positive definitions
5. debug protocol (unregistered seed/short prefix; no labels; commit hash)
6. cap/artifact/checkpoint/timing/manifest

이 항목은 **threshold/seed/donor/step 변경이 아니다.** v0.2.1은 protocol contract tighten이다.

---

## 5. 결정

```text
v0.2 as written = NARROW 3/3, not frozen
v0.2.1 = 필요
Phase 6 구현 = 미승인 (v0.2.1 + explicit approval 후)
1-seed debug = 미승인 (mechanics-only, 별도 승인)
3-seed = 미승인
B0-B/B1/B2/Stage C = 미승인
test 163 = sealed
T5Gemma2 = D-108 STOP
```

### 다음

1. v0.2.1 errata 작성·commit/freeze
2. 사용자 승인
3. 구현 + unit tests
4. non-gating mechanics debug (unregistered seed/short prefix)
5. debug artifact gate 후 3-seed 여부 결정
6. 3-seed 이후에도 B0-B 별도 decision

---

## 6. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v0_2_2026-11-09/review_GLM.md` | GLM |
| `.../review_SONNET.md` | Sonnet |
| `.../review_SOL.md` | Sol |
| `reports/C5_B0A_PM_PREREG_V0_2_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |
| `docs/plan_c5_b0a_pm_prereg_v0_2.md` | v0.2 |
| `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_2026-11-09.md` | 요청서 |

## 7. 제한

- 이 종합은 승인이 아니다.
- v0.2.1 없이 코드를 작성하지 않는다.
- 3/3 NARROW는 bridge STOP이 아니다.
- “54 tests”는 historical evidence이며 P/PA/M tests는 아직 없다.
