# C5 Phase 6 v1.0.7 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v1_0_7_2026-11-09/`
- 검토 기준 HEAD: `359ac36`
- 모델:
  - GLM 5.3 Flash **max** — 12,250 chars, **CONTINUE(조건부)**
  - DeepSeek V4.1 Flash **1017** **high** — 21,949 chars, **NARROW**
  - Sol 6.1 **medium** — 29,144 chars, **NARROW**
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V1_0_7_2026-11-09.md`
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **1 CONTINUE(조건부) / 2 NARROW.** v1.0.7은 §16.2 path, T_proj per-seed, `K_d<=K_M`, legacy bootstrap, key-coverage를 닫았고 golden/preflight/산수는 재현됐다. 그러나 **`_FREEZE.json`이 자신을 추가하는 commit SHA를 담을 수 없는 자기참조**, **legacy `bootstrap_paired`가 `evaluate_arm` 경유로 여전히 도달 가능**, **paired `L>F` cohort/endpoint/seed 정의 부재**가 남아 동결할 수 없다. **v1.0.8/ERRATA text/schema only.**

---

## 1. 판정 행렬

| 검토자 | 모델 | 판정 | 비고 |
|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **CONTINUE(조건부)** | 6개 중 5 closed, MF-A만 partial |
| DeepSeek 1017 | `deepseek-v4.1-flash-1017` high | **NARROW** | MF-1..3 |
| Sol | `gpt-6.1-sol` medium | **NARROW** | MF-1 freeze-blocking |
| **종합** | — | **NARROW (2/3)** | **동결 보류** |

- CONTINUE 1/3.
- NARROW 2/3.
- STOP 0/3.
- GLM은 이번에 유효(HEAD/quote 충족).

---

## 2. 실제로 닫힌 것

- §16.2 `plan_path`/manifest path `v1_0_7` — **closed**
- `t_primary_replay_arm` per-seed 120/160 — **closed**
- 360/480 aggregate — **verified**
- phase-7 `K_d = min(K_M,...)` + assert — **closed**
- legacy `bootstrap_paired` import 금지 test — **partial**
- key-coverage 4-record vs 600 numeric — **closed**
- golden 5종 + preflight — **verified**
- 1,680/560/600 — **verified**

GLM: 5 closed / 1 partial.
DS: 6 closed; 3 material gaps.
Sol: most closed; 1 freeze-blocking.

---

## 3. 남은 Must-fix

### MF-1. `manifest_commit` 자기참조 (blocker)

- `_FREEZE.json` schema contains `manifest_commit`.
- the SHA of the commit that adds the file cannot be known before the file is committed.
- DS/Sol/GLM all flag.
- GLM: set `manifest_commit: null` in file, record actual SHA in D0 report.
- Sol: external manifest identity record.

**v1.0.8 요구**:
- `_FREEZE.json` stores `manifest_commit: null`.
- D0 report records `manifest_commit` + `freeze_manifest_sha256`.
- or use an external `freeze_manifest_commit.txt` created after commit.
- no self-reference.

### MF-2. Legacy `bootstrap_paired` reachable via `evaluate_arm` (high)

- new stats module must not import legacy.
- Phase 6 entrypoint can still call `runner.c5_mt5_lora_b0.evaluate_arm` → legacy `bootstrap_paired`.
- DS MF-2.

**v1.0.8 요구**:
- define Phase 6 entrypoint call graph.
- `evaluate_arm` must use `c5_pm_stats` or be replaced.
- source assertion / monkeypatch test that legacy symbol is unreachable.
- no behavior change.

### MF-3. Paired `L>F` definition (medium)

- §3.5 says paired `L>F` but not cohort/endpoint alignment/seed averaging.
- DS MF-3.

**v1.0.8 요구**:
- cohort = 15 common IDs.
- endpoint = same variant/endpoint/memory kind.
- seed = same registered seed, seed-average before bootstrap.
- missing pair → NA.
- no 15→14.

### MF-4. Template/schema mismatch (low)

- template has `status:template` + `note`.
- schema `status:frozen` no `note`.

**v1.0.8 요구**: allow `note` in frozen schema or remove template-only key.

### MF-5. Cap labels (low)

- §11.1 registered 120 min vs §11.6 aggregate 155 min.
- disambiguate.

### MF-6. P0 tail provenance (low)

- GLM: .4862/.43355/.455 not in `p0_native_sanity.json`.
- derived, not stored.

**v1.0.8 요구**: mark derived or add artifact.

### MF-7. §4.6 bullet (cosmetic)

- `p_step NA + p_valid=false` unreachable; F9 uses `p_valid=NA`.
- fix text.

---

## 4. 검토자별

### GLM — CONTINUE(조건부)

- 5 closed / 1 partial.
- MF-A manifest_commit self-reference (blocker).
- MF-B P0 tail provenance.
- MF-C §4.6 bullet.
- freeze + 구현 + D0 승인 if MF-A in freeze commit.

### DS 1017 — NARROW

- MF-1 manifest_commit; MF-2 legacy bootstrap; MF-3 paired L>F; MF-4 template note; MF-5 cap.
- freeze no.

### Sol — NARROW

- MF-1 freeze-blocking manifest identity.
- no execution authorization.

---

## 5. 결정

```text
v1.0.7 = 동결 보류 (1 CONTINUE / 2 NARROW)
v1.0.8/ERRATA = 필요 (text/schema only)
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

1. v1.0.8:
   - manifest_commit external/null
   - legacy bootstrap call graph
   - paired L>F
   - template note
   - cap labels
   - P0 tail provenance
   - §4.6
2. v1.0.8 review
3. freeze manifest
4. 구현 + unit tests
5. D0
6. D1 separate
7. 3-seed separate

---

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_7_2026-11-09/review_GLM.md` | GLM CONTINUE |
| `.../review_DS1017.md` | DeepSeek NARROW |
| `.../review_SOL.md` | Sol NARROW |
| `reports/C5_B0A_PM_PREREG_V1_0_7_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |

## 8. 제한

- 이 종합은 승인이 아니다.
- NARROW 2/3가 우세하다.
- v1.0.8 없이 코드를 작성하지 않는다.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아니다.
