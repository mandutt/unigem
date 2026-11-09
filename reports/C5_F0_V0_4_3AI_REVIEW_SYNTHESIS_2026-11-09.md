# C5 F0 v0.4 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_f0_v0_4_review_2026-11-09/`
- 대상: `docs/plan_c5_f0_v0_4_2026-11-09.md`
- 모델: GLM 5.3 Flash high, DeepSeek 1017 high, Luna 6 xhigh
- 이전 v0.3 스레드: archive 완료
- 추가 학습/평가: 없음

## 1. 판정

| 검토자 | 판정 | 핵심 |
|---|---|---|
| GLM | **CONTINUE** | `ROUTE_STOP` all-four FAIL 열거, orchestrator/gate, RNG 문구 |
| DeepSeek | **NARROW** | STOP 부호 역전, D1 seal 우회, R cap, cohort, RNG |
| Luna | **NARROW** | equivalence/STOP truth table, D1 gate, init manifest, cap |
| **종합** | **1 CONTINUE / 2 NARROW** | **F0 미승인** |

## 2. 닫힌 것

- compute 기본 회계 / orchestrator 필요성.
- D1 allowlist / sealed signal 방향.
- 4-state taxonomy 골격.
- 15 common binding.
- init hash / H3 분리.

## 3. Must-fix

### MF-1. ROUTE_STOP 부호 역전 (DS blocker)

- v0.4: `CI_D.upper<0` → `adapter_associated_harm`.
- 실제: `CI_D.lower>0`가 E01 우세 = adapter harm.
- `CI_D.upper<0`는 E11 우세 = adapter benefit.
- v0.5: harm/benefit 분리, STOP은 harm 또는 EQUIVALENT.

### MF-2. `all four FAIL` 해석 (GLM/DS)

- E01/E11 × copy/full인지, E00/E10 포함 4-cell인지 불명.
- v0.5: `ALL_FAIL = FAIL(E01,copy)&FAIL(E01,full)&FAIL(E11,copy)&FAIL(E11,full)`; E00/E10 제외.

### MF-3. Equivalence (Luna/DS)

- `|mean_D|<.05 + CI contains 0`은 equivalence가 아니다.
- v0.5: `EQUIVALENT = 95% CI within [-.05,.05]`; `E01≈E11` descriptive only.

### MF-4. PASS_POSITIVE 정합 (DS)

- “no per-cell conjunction” vs `SIGNAL(E01,copy)` 요구.
- v0.5: primary paired + E01 signal guard 명시.

### MF-5. D1 seal schema (DS/Luna)

- allowlist만으로는 `d1_partial`/logs/checkpoint 우회.
- v0.5: denylist + negative test + state_dict-only checkpoints + no plaintext signal.

### MF-6. R cap (DS/GLM)

- registered 4,939.88s ×1.316 ≈ 6,500s (108.3min); 120min margin 11.7min.
- v0.5: R cap 150min, margin ≈2,500s; nproc/threads/contention recorded.
- sequential 3,116.5s는 committed artifact 아님 → scratch telemetry로 한정.

### MF-7. Cohort 완전성 (DS/GLM)

- doc 3/3 seed, n_donors=5, E01/E11 donor set identical.
- v0.5 반영.

### MF-8. RNG 문구 (DS/GLM)

- “dropout/optimizer diverges”는 과도/사실 반대.
- v0.5: post-step0 RNG hash E01==E11 assert; LoRA fixed=init, not trained equality.

### MF-9. H3 (DS/Luna)

- projection spec, identity threshold, trigger direction.
- v0.5: QR seed/rank/hash, mean≤1e-6/max≤1e-5, CI-excluding-0 trigger.

## 4. 결정

```text
F0 v0.4 = 1 CONTINUE / 2 NARROW
F0 = 미승인, 미실행
v0.5 = sign/taxonomy/equivalence/seal/cohort/RNG/cap/H3 수정
```

## 5. 다음

- v0.5 3-AI 재검토 (새 스레드, v0.4 스레드 archive).
- 3/3 CONTINUE까지 또는 최대 10라운드.
