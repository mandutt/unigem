# C5 Phase 6 v1.0.8 — 3-AI Review Synthesis (same-thread round)

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v1_0_8_2026-11-09/`
- 검토 기준 HEAD: `d4e9dfa`
- 모델/스레드:
  - GLM 5.3 Flash **max** — `thr_a757d209deae4493985cc2731c5af382` — **CONTINUE**
  - DeepSeek V4.1 Flash **1017** **high** — `thr_b142cc5df03c484ca20d06ba152279e9` — **NARROW**
  - Sol 6.1 **medium** — `thr_3e45b1e757c64204a065c84429d2abed` — **CONTINUE**
- **same-thread `fup` 라운드**: 새 스레드 생성·아카이브 없음. 캐시/컨텍스트 보존.
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V1_0_8_2026-11-09.md`
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **2 CONTINUE / 1 NARROW.** GLM과 Sol은 v1.0.7의 7개 잔여가 모두 프로토콜 수준에서 닫혔고 pre-freeze blocker가 없다고 판정했다. DeepSeek만 **§10.2의 `bootstrap_paired`와 §17.3의 `bootstrap_paired_v2` 심볼 충돌**, **`freeze_manifest_sha256` 미정의**를 남겼다. 두 항목 모두 text-only이며, **v1.0.9/ERRATA 후 동결 가능**하다.

---

## 1. 판정 행렬

| 검토자 | 모델 | 판정 | v1.0.8 freeze | 구현+unit tests | D0 | D1 | 3-seed |
|---|---|---|---|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **CONTINUE** | 승인 | 승인 | 승인 | 미승인 | 미승인 |
| DeepSeek 1017 | `deepseek-v4.1-flash-1017` high | **NARROW** | MF-1/MF-2 후 | 보류 | 보류 | 미승인 | 미승인 |
| Sol | `gpt-6.1-sol` medium | **CONTINUE** | 승인 | 승인 | 승인 | 미승인 | 미승인 |
| **종합** | — | **NARROW (1/3)** | **보류** | **보류** | **보류** | **미승인** | **미승인** |

- CONTINUE 2/3.
- NARROW 1/3.
- STOP 0/3.
- 동결은 3/3 CONTINUE가 아니므로 보류하되, **잔여가 단일 텍스트 심볼/해시 정의**이므로 v1.0.9에서 닫을 수 있다.

---

## 2. 실제로 닫힌 것

- `manifest_commit` 자기참조 — **closed** (GLM/Sol/DS)
  - `_FREEZE.json` 내 `null`, external `freeze_manifest_commit.txt`, D0 report.
- legacy `bootstrap_paired` 도달 — **partial**
  - call graph §17.3은 추가됐지만 심볼 이름이 §10.2와 충돌.
- paired `L>F` — **closed**
- template `note` vs frozen schema — **closed**
- cap 120 vs 155 — **closed**
- P0 tail provenance — **closed**
- §4.6 `p_valid=NA` — **closed**
- golden/preflight/산수 — **verified**

GLM: 7/7 closed, 2 implementation-time recommendations.
Sol: 7/7 protocol requirements closed, no pre-freeze Must-fix.
DS: 2 material text defects.

---

## 3. 남은 Must-fix

### MF-1. `bootstrap_paired` vs `bootstrap_paired_v2` 심볼 충돌 (material)

- §10.2 new stats module: `bootstrap_paired(seed=20261109)`.
- §17.3 entrypoint: `c5_pm_stats.bootstrap_paired_v2`.
- implementer must guess which symbol exists.
- DS MF-1.

**v1.0.9 요구**:
- choose one name everywhere: `bootstrap_paired_v2` (recommended, avoids legacy confusion).
- §10.2, §17.3, §13.5 test all same.
- legacy `bootstrap_paired` explicitly forbidden.

### MF-2. `freeze_manifest_sha256` 미정의 (low)

- §16.2 step (5) uses it; no definition.
- DS MF-2.

**v1.0.9 요구**:
- `freeze_manifest_sha256 = SHA256(committed _FREEZE.json bytes)`.
- state whether `freeze_manifest_commit.txt` is committed; if yes, D0 also records its hash.
- custody chain explicit.

### MF-3. `evaluate_arm` replacement timing (clarity)

- DS MF-3: state the replacement lands before freeze.
- Add one line.

### MF-4. v1.0.7 split wording (cosmetic)

- DS says v1.0.7 substantive split was 1 CONTINUE / 2 NARROW (correct), not 2/2.
- v1.0.8 request correctly says 1 CONTINUE / 2 NARROW; synthesis should not repeat "2/2" for v1.0.7.
- no spec change.

---

## 4. 검토자별

### GLM — CONTINUE

- 7/7 closed.
- freeze + implementation + D0 승인.
- recommendations: §17.3 transitive source, freeze txt commit timing, §13 test item.

### DeepSeek 1017 — NARROW

- MF-1 symbol contradiction (material).
- MF-2 `freeze_manifest_sha256` undefined.
- MF-3 evaluate_arm timing.
- freeze after text repair.

### Sol — CONTINUE

- 7/7 protocol requirements closed.
- freeze → implementation + unit tests → D0 bounded.
- legacy/paired still need implementation evidence, not pre-freeze text.

---

## 5. 결정

```text
v1.0.8 = 동결 보류 (2 CONTINUE / 1 NARROW)
v1.0.9/ERRATA = 필요 (text-only; 2 material items)
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

1. v1.0.9:
   - `bootstrap_paired_v2` 단일화
   - `freeze_manifest_sha256` 정의/custody
   - evaluate_arm timing
2. v1.0.9 same-thread review (기존 3 스레드 유지)
3. freeze
4. 구현 + unit tests
5. D0
6. D1 separate
7. 3-seed separate

---

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_8_2026-11-09/review_GLM.md` | GLM CONTINUE |
| `.../review_DS1017.md` | DeepSeek NARROW |
| `.../review_SOL.md` | Sol CONTINUE |
| `reports/C5_B0A_PM_PREREG_V1_0_8_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |

## 8. 스레드 보존

- 3개 스레드 모두 **동일 ID 유지**.
- 새 `ask`/archive 없음.
- `fup` delta 프롬프트만 전송.
- 다음 라운드도 같은 스레드 사용 가능.

## 9. 제한

- 이 종합은 승인이 아니다.
- NARROW 1/3이지만 동결은 만장일치 CONTINUE 전까지 보류.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아니다.
- golden digests are verified constants, not results.
