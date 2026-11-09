# C5 Phase 6 v0.2.1 Errata — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_2026-11-09/`
- 검토 기준 HEAD: `0756215`
- 모델:
  - GLM 5.3 Flash **max**
  - Sonnet 5.5 **high**
  - Sol 6.1 **high**
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_1_2026-11-09.md` (334줄)
- 원문:
  - `review_GLM.md` (18,222 chars)
  - `review_SONNET.md` (37,053 chars)
  - `review_SOL.md` (37,095 chars)
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **3/3 NARROW.** v0.2.1은 v0.2 Must-fix 대부분을 닫았지만, **decision function이 total하지 않고**, **M common cohort ≥15/20이 구조적으로 불가능할 수 있으며**, **debug를 포함한 cap 산술이 1,200 updates를 초과**한다. **v0.2.1-r1 text-only errata를 동결 전에 작성해야 하며, 3-seed/B0-B는 미승인**이다.

---

## 1. 판정 행렬

| 검토자 | 판정 | 동결 | 구현+unit tests | mechanics debug | 3-seed |
|---|---|---|---|---|---|
| GLM max | **NARROW** | Must-fix 1~4 후 조건부 | 동결 후 승인 | unit tests 후 승인 | 미승인 |
| Sonnet high | **NARROW** | v0.2.1-r1 필요 | 조건부, freeze 후 | 조건부, unit tests 후 | 미승인 |
| Sol high | **NARROW conditional** | not frozen as written | 조건부 | 별도 authorization | 미승인 |
| **종합** | **NARROW 3/3** | **v0.2.1-r1 필요** | **미승인** | **미승인** | **미승인** |

STOP 0/3, CONTINUE 0/3.

---

## 2. 실제로 닫힌 것

- 독립 flag vector 도입
- `REGIME_ERASES_SELECTIVITY` 제거
- P/PA interaction table
- PA random-adapter step0 별도 실행
- M_POS_MEAN AND M_NORM pass
- M_VALID P AND PA
- common M cohort 개념
- seed-averaged per-doc bootstrap
- L>F paired
- `documents_positive` vs `seeds_positive`
- unregistered debug seed 20261111
- manifest/checkpoint/timing 요구

검토자들은 방향과 구조가 **v0.2보다 뚜렷하게 개선**됐다고 평가했다.

---

## 3. 남은 Must-fix

### MF-1. Decision function totality

**문제**

- `not_assessable` flag가 headline에서 사용되지 않는다.
- `INCONCLUSIVE_SMALL_N`은 rule 13까지 도달할 수 없는 dead cell이다.
- P valid + PA **path fail** cell이 없다.
- P path fail이 rule 2와 `ASSAY_INVALID`/stop 조건 사이에서 모순된다.
- `copy_only`/`full_only` flag 정의가 precedence와 완전히 맞물리지 않는다.
- `MEAN_CONTRAST_ONLY`가 다른 문서에 정의되어 있지 않다.
- L_SIGNAL이 headline에서 6/13 cell 동안 숨는다.

**요구**

- **factored output**: `validity_status` + `signal_status`를 항상 둘 다 출력
- tri-state flags (true/false/not_assessable)
- PA path-fail cell
- `INCONCLUSIVE_SMALL_N`에 n-min을 정의하거나 삭제
- `MEAN_CONTRAST_ONLY` 의미 정의
- P path fail을 `ASSAY_INVALID`로 통일
- 모든 truth-table combination unit test
- L flag는 headline과 별도로 항상 보존

### MF-2. M cohort / aggregation / replay

**문제**

- `len(h_i) >= K_real` + contributor≥10이면 target eligible이 대략 train median 이하로 제한된다.
- common L∩P∩PA cohort ≥15/20이 **구조적으로 불가능할 수 있다**.
- M seed aggregation 규칙이 없다.
- M replay가 별도 프로세스일 때 in-process와 동일한지 검증이 없다.
- M_NORM은 real norm을 쓰므로 strictly target-independent가 아니다.

**요구**

- 동결 전 **data-only M cohort preflight**: L/P/PA common eligible target count.
- <15이면 **v0.2.1-r1에서 M 설계를 수정**하거나 `M_NOT_EVALUABLE`을 기본으로 수용.
- seed-averaged per-doc M aggregation 명시.
- replay-equals-in-process test.
- M_NORM secondary/qualified 표기 유지.

### MF-3. Cap arithmetic

**문제**

- 12 units × 100 updates = **1,200** = cap.
- debug 4 arms × 5 updates를 더하면 **1,220 updates**, ≥16 units.
- §6.1은 debug가 cap에 포함된다고 하지만 산술적으로 불가능하다.

**요구**

- debug를 **별도 budget**으로 분리하고 3-seed cap과 합산하지 않거나,
- zero-update mechanics-only로 바꾸거나,
- cap을 **16 units / 1,220 updates**로 명시적으로 늘리되 새 승인 필요.
- 현재는 **debug 포함 1,200 cap**을 그대로 둘 수 없다.

### MF-4. PA semantics

**문제**

- PA는 random adapter + LoRA **acquisition** control이지 retention control이 아니다.
- `ADAPTER_REGIME_LOSS`는 “잃었다”는 인과적 함의.
- PA step0는 random adapter 때문에 P0와 다른 regime이며 `PA_RETENTION`이 null일 수 있다.

**요구**

- `ADAPTER_REGIME_LOSS` → `PA_STEP100_NOT_VALID` (또는 `PA_ACQUISITION_FAILURE`)
- PA를 acquisition control로 명시
- scale/geometry caveat를 artifact interpretation에 기록
- PA step0 expected null/무정보를 명시

### MF-5. Statistics / stale references

- CI percentile, n_boot, RNG seed, top-3 share formula, endpoint rule을 **statistical constants block**으로 고정.
- `INCONCLUSIVE_SMALL_N` n-min 정의.
- v0.2 §12 B0-B 금지 목록이 삭제된 `REGIME_ERASES_SELECTIVITY`를 아직 참조한다.
- 3-seed launch checklist (a)~(h)를 artifact로 추가.
- P gate `.05`는 P0 mean의 약 1%로 weak; threshold 변경이 아니라 **post-training sensitivity screen**이라는 제한을 더 명확히.

---

## 4. v0.2.1-r1 권고

v0.2.1-r1은 **text-only**여야 한다.

1. factored `(validity_status, signal_status)` output
2. tri-state flags + exhaustive truth-table tests
3. PA path-fail cell + `PA_STEP100_NOT_VALID`
4. M cohort data-only preflight + seed aggregation + replay test
5. debug/cap arithmetic 수정
6. statistical constants block
7. stale B0-B references/rules 정리
8. 3-seed launch checklist

이 변경은 threshold/seed/donor/step/LR 변경이 아니다. 결과 전 contract tighten이다.

---

## 5. 결정

```text
v0.2.1 = NARROW 3/3, not frozen
v0.2.1-r1 = 필요
Phase 6 구현 = 미승인
unit tests = 미승인
mechanics debug = 미승인
3-seed = 미승인
B0-B/B1/B2/Stage C = 미승인
test 163 = sealed
T5Gemma2 = D-108 STOP
```

### 다음

1. v0.2.1-r1 text errata 작성
2. data-only M cohort preflight
3. commit/freeze
4. 사용자 승인
5. 구현 + unit tests
6. non-gating mechanics debug (별도 budget)
7. 3-seed 별도 gate
8. B0-B 별도 decision

---

## 6. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_2026-11-09/review_GLM.md` | GLM |
| `.../review_SONNET.md` | Sonnet |
| `.../review_SOL.md` | Sol |
| `reports/C5_B0A_PM_PREREG_V0_2_1_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_errata.md` | v0.2.1 |
| `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_1_2026-11-09.md` | 요청서 |

## 7. 제한

- 이 종합은 승인이 아니다.
- 3/3 NARROW는 bridge STOP이 아니다.
- v0.2.1-r1 없이 코드를 작성하지 않는다.
- “54 tests”는 historical evidence이며 PM tests는 아직 없다.
