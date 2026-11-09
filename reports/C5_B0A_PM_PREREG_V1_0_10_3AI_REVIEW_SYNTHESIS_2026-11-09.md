# C5 Phase 6 v1.0.10 — 3-AI Final Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v1_0_10_2026-11-09/`
- 검토 기준 HEAD: `206117b`
- 모델/스레드:
  - GLM 5.3 Flash max — **NARROW**
  - DeepSeek 1017 high — **NARROW**
  - Sol 6.1 medium — **NARROW**
- **same-thread `fup`**: 새 스레드·아카이브 없음.
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **3/3 NARROW.** Option A는 pre-freeze helper edit 충돌을 제거했지만, **`train_arm`이 내부에서 무조건 `evaluate_arm`을 호출**하므로 “training only” 재사용이 성립하지 않는다. `train_arm`을 재사용하면 legacy `bootstrap_paired` 경로가 다시 열린다. **Phase 6가 training loop까지 직접 소유**하는 v1.0.11이 필요하다.

---

## 1. 판정 행렬

| 검토자 | 모델 | 판정 | 근거 |
|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **NARROW** | `train_arm` line 665→723 `evaluate_arm`; test scope |
| DeepSeek | `deepseek-v4.1-flash-1017` high | **NARROW** | train_arm reuse vs evaluate_arm exclusion; P/PA |
| Sol | `gpt-6.1-sol` medium | **NARROW** | composite train_arm mislabeled training-only |
| **종합** | — | **NARROW 3/3** | **동결 보류** |

- STOP 0/3.
- CONTINUE 0/3.
- NARROW 3/3.

---

## 2. 실제로 닫힌 것

- pre-freeze helper edit 충돌 — **closed**
- `bootstrap_paired_v2` — **closed**
- `freeze_manifest_sha256` — **closed**
- external txt custody — **closed**
- evaluate_arm direct import/call 금지 — **closed** (직접만)
- golden/preflight/산수 — **verified**

---

## 3. 남은 Must-fix

### MF-1. `train_arm`은 training-only가 아니다 (blocker)

`runner/c5_mt5_lora_b0.py`:
- `train_arm` (line 665)은 training loop 후 **무조건** `evaluate_arm(...)` (line 723)과 `generate_arm(...)` (line 724)를 호출.
- `evaluate_arm`은 legacy `bootstrap_paired` (line 460, seed 20261108)를 호출.
- 따라서 `train_arm` 재사용은 **런타임에서 legacy bootstrap 경로에 도달**.
- §17.3 “train_arm may be reused for training”과 “must not import/call evaluate_arm”이 동시에 성립 불가.

**v1.0.11 요구**:
- **Phase 6 owns training loop too.**
- `runner/c5_pm_phase6.py` implements training + evaluation.
- no `train_arm` reuse.
- no `evaluate_arm` reuse.
- no legacy `bootstrap_paired`.
- §17.3 call graph:

```text
runner/c5_pm_phase6.py
  -> own training loop
  -> own eval loop
  -> c5_pm_stats.bootstrap_paired_v2
```

- §17.1 helper list: do not list train_arm.
- §13.5: Phase 6 path does not import train_arm or evaluate_arm.

### MF-2. “Phase 6 path” 정의

- direct entrypoint source vs transitive call graph ambiguous.
- define: **transitive call graph rooted at `runner/c5_pm_phase6.py`**.
- assertion covers all reachable imports/definitions.

### MF-3. `train_arm` not in §17.1

- if any helper reused, add to §17.1; or reference none.
- Option: no train helper reuse, simplest.

### MF-4. P0 unaffected

- P0 uses `p0_eval_split`, not `evaluate_arm`.
- state one line.

---

## 4. 검토자별

### GLM — NARROW

- Option A lifecycle closed.
- `train_arm` composite issue.
- ERRATA-A train_arm; ERRATA-B test scope.
- no STOP.

### DS — NARROW

- MF-1 train_arm reuse; MF-2 Phase 6 path; MF-3 §17.1; MF-4 P0.
- freeze after text fix.

### Sol — NARROW

- MF-1 composite train_arm.
- no second Must-fix.
- freeze after coherent training-only route.

---

## 5. 결정

```text
v1.0.10 = 동결 보류 (3/3 NARROW)
v1.0.11 = Phase 6 owns train+eval loops (text-only)
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

1. v1.0.11:
   - own training loop
   - no train_arm/evaluate_arm
   - transitive Phase 6 path
   - P0 unaffected line
2. same-thread review.
3. freeze.
4. 구현 + unit tests.
5. D0.
6. D1 separate.
7. 3-seed separate.

---

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_10_2026-11-09/review_GLM.md` | GLM NARROW |
| `.../review_DS1017.md` | DeepSeek NARROW |
| `.../review_SOL.md` | Sol NARROW |
| `reports/C5_B0A_PM_PREREG_V1_0_10_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |

## 8. 스레드 보존

- 동일 3개 ID 유지.
- 새 `ask`/archive 없음.
- 다음 라운드도 같은 스레드 사용.

## 9. 제한

- 이 종합은 승인이 아니다.
- 3/3 NARROW; freeze 보류.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아니다.
