# C5 Phase 6 v1.0.9 — 3-AI Final Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v1_0_9_2026-11-09/`
- 검토 기준 HEAD: `b9fd854`
- 모델/스레드:
  - GLM 5.3 Flash max — `thr_a757d209deae4493985cc2731c5af382` — **CONTINUE(조건부)**
  - DeepSeek 1017 high — `thr_b142cc5df03c484ca20d06ba152279e9` — **CONTINUE**
  - Sol 6.1 medium — `thr_3e45b1e757c64204a065c84429d2abed` — **NARROW**
- **same-thread `fup`**: 새 스레드·아카이브 없음.
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V1_0_9_2026-11-09.md`
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **2 CONTINUE / 1 NARROW.** `bootstrap_paired_v2` 단일화, `freeze_manifest_sha256` 정의/custody, evaluate_arm timing은 모두 닫혔다. 그러나 Sol이 **“freeze 전 evaluate_arm 교체”와 “no code before freeze”의 lifecycle 충돌**을 지적했다. 이는 **v1.0.10 text-only**로 닫을 수 있다.

---

## 1. 판정 행렬

| 검토자 | 모델 | 판정 | v1.0.9 freeze | 구현+unit tests | D0 | D1 | 3-seed |
|---|---|---|---|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **CONTINUE(조건부)** | ERRATA-1 포함 시 | 승인 | 승인 | 미승인 | 미승인 |
| DS 1017 | `deepseek-v4.1-flash-1017` high | **CONTINUE** | 승인 | 승인 | 승인 | 미승인 | 미승인 |
| Sol | `gpt-6.1-sol` medium | **NARROW** | lifecycle 수정 후 | 보류 | 보류 | 미승인 | 미승인 |
| **종합** | — | **NARROW (1/3)** | **보류** | **보류** | **보류** | **미승인** | **미승인** |

- CONTINUE 2/3.
- NARROW 1/3.
- STOP 0/3.
- 동결은 3/3 CONTINUE 전까지 보류.

---

## 2. 실제로 닫힌 것

- `bootstrap_paired_v2` 단일 심볼 — **closed** (GLM, DS, Sol)
- legacy `bootstrap_paired` 배제 — **closed**
- `freeze_manifest_sha256` 정의 — **closed**
- external `freeze_manifest_commit.txt` custody — **closed**
- template/schema — **closed**
- golden/preflight/산수 — **verified**

DS: no blocking Must-fix; implementation-time follow-ups only.
GLM: 3 items closed; ERRATA-1 lifecycle.
Sol: symbol/hash closed; lifecycle remains.

---

## 3. 남은 Must-fix

### MF-1. evaluate_arm lifecycle conflict (blocker)

- v1.0.9 §17.3: `evaluate_arm` bootstrap replacement **before the freeze commit**.
- §16.1: **no code before freeze**.
- Sol: cannot both hold.
- GLM: ERRATA-1 §16.1↔§17.3.
- This is a process contradiction, not a scientific issue.

**v1.0.10 options**:
- **Option A (recommended)**: Phase 6 entrypoint `runner/c5_pm_phase6.py` implements its **own** eval wrapper using `c5_pm_stats.bootstrap_paired_v2`; `evaluate_arm` is not reused. No pre-freeze helper edit. This removes the conflict.
- Option B: allow a narrow pre-freeze helper-preparation exception (remove legacy bootstrap only, no training/eval), recorded in freeze manifest. More moving parts.
- Option C: defer helper edit until after freeze, but then implementation cannot reference frozen helper behavior. Not recommended.

**v1.0.10 요구**:
- choose Option A unless user prefers B.
- §17.3: `evaluate_arm` not used by Phase 6.
- no pre-freeze code change.
- test: Phase 6 path does not import `evaluate_arm`.

### MF-2. GLM ERRATA-1

- §16.1 no-code rule and §17.3 helper replacement.
- same as MF-1; fix once.

### MF-3. Minor

- DS implementation-time: `H1 baseline`, helper internals, etc.
- no pre-freeze blocker.

---

## 4. 검토자별

### GLM — CONTINUE(조건부)

- symbol/hash/timing closed.
- ERRATA-1 lifecycle.
- freeze + implementation + D0 conditional.

### DS — CONTINUE

- no blocking Must-fix.
- implementation-time follow-ups.
- phase 6 registered/D1/3-seed not approved.

### Sol — NARROW

- symbol/hash/custody accepted.
- MF-1 lifecycle conflict.
- freeze after text fix.

---

## 5. 결정

```text
v1.0.9 = 동결 보류 (2 CONTINUE / 1 NARROW)
v1.0.10 = lifecycle text-only repair 필요
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

1. v1.0.10:
   - Phase 6 own eval wrapper; `evaluate_arm` not reused.
   - no pre-freeze code.
   - §17.3/§16.1 정합.
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
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_9_2026-11-09/review_GLM.md` | GLM CONTINUE |
| `.../review_DS1017.md` | DeepSeek CONTINUE |
| `.../review_SOL.md` | Sol NARROW |
| `reports/C5_B0A_PM_PREREG_V1_0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |

## 8. 스레드 보존

- 동일 3개 ID 유지.
- 새 `ask`/archive 없음.
- 다음 라운드도 같은 스레드 사용.

## 9. 제한

- 이 종합은 승인이 아니다.
- NARROW 1/3; freeze 보류.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아니다.
