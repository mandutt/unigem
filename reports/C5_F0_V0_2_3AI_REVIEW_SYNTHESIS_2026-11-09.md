# C5 F0 v0.2 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_f0_v0_2_review_2026-11-09/`
- 검토 HEAD: `185d2ff7b2c29aaa10093838335cb15901981657`
- 대상: `docs/plan_c5_f0_v0_2_2026-11-09.md` (DRAFT v0.2)
- 새 독립 스레드 3개
- test 163: sealed
- P1: unused
- 추가 학습/평가: 없음

## 0. 한 줄 결론

> **3/3 NARROW.** v0.1의 Stage D selection bias와 track STOP은 제거됐지만, **E01/E11의 LoRA 초기화가 같지 않고(RNG order)**, **mechanics-pass 술어가 닫혀 있지 않으며**, **primary decision이 paired contrast가 아니라 per-cell significance**다. F0는 여전히 승인 불가.

## 1. 판정

| 검토자 | 모델 | 최종 판정 | 핵심 |
|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **NARROW** | MF-A~MF-E; D1 E00 모순, source ambiguity |
| DeepSeek | `deepseek-v4.1-flash-1017` high | **NARROW** | LoRA RNG, undefined mechanics, per-cell rule, STOP validity, compute |
| Sol | `gpt-6.1-sol` medium | **NARROW** | predicate binding, mechanics contract, runtime, causal scope |
| **종합** | — | **NARROW 3/3** | **F0 미승인** |

## 2. v0.2에서 닫힌 것

- Stage D 1-seed signal gate 제거.
- Stage R 3-seed 기본.
- track STOP 삭제, route-scoped STOP로 한정.
- E00 eval-only baseline 명시.
- H3 별도 prereg.
- F0 code 미구현 명시.

## 3. Must-fix (consensus)

### MF-1. LoRA 초기화가 E01/E11에서 동일하지 않음 (blocker)

- `build_arm`: `torch.manual_seed(seed)` → adapter 생성(E11만) → LoRA attach.
- E11은 adapter가 RNG를 소비한 뒤 LoRA가 초기화되고, E01은 바로 LoRA가 초기화된다.
- 따라서 `lora_A` 초기값이 다르다. “LoRA fixed”가 성립하지 않는다.
- 수정:
  - adapter 생성 후 **LoRA 전용 seed를 명시적으로 재설정**.
  - `set_lora_seed(seed)`를 adapter 유무와 무관하게 호출.
  - E01/E11 LoRA state_dict 초기 hash 동일성 assert.
- 이 수정 없이는 primary contrast가 adapter + LoRA-init 차이이다.

### MF-2. mechanics-pass 술어 미정의

- D0/D1 pass 기준이 닫힌 목록이 아니다.
- D1 signal telemetry를 읽고 중단할 재량이 남아 있다.
- 수정:
  - D0/D1 pass predicate를 enumerated list로 고정.
  - D1 실패 시 코드 수리 + D1 재실행만 허용; signal read 금지.
  - Stage R 진입은 predicate true만.

### MF-3. D1 E00 모순

- E00은 adapter/LoRA 모두 없어 trainable parameter가 0.
- `optimizer_for`가 `no trainable parameters` RuntimeError.
- D1 “4 cells, 1 update”/“4 updates”는 기계적으로 불가능.
- 수정: D1 = E10/E01/E11 각 1 update(총 3) + E00 0-update eval-only.
- D0 adapter vector도 `absent/present/absent/present`로 정정.

### MF-4. Primary decision이 paired contrast가 아님

- §5는 “E01 positive AND E11 negative AND E01−E11 >0”라는 per-cell significance 조합이다.
- Primary endpoint는 paired `E01−E11` CI인데 decision이 그와 다르다.
- 수정:
  - primary decision = paired `E01−E11` copy CI lower >0.
  - per-cell E01/E11 signal은 secondary descriptor.
  - “E01≈E11”의 연산적 정의(CI 0 포함 + |mean|<.05 등) 명시.
  - missing seed/doc → NA; 15→14 대체 금지.

### MF-5. Primary signal source 미지정

- Phase 6에서 phase7 records와 unit-final donor-crop signal이 −0.0407 vs −0.1135로 갈렸다.
- F0 §3은 20 docs/5 donors만 정의하고 artifact source를 지정하지 않았다.
- 수정: primary = **final-checkpoint donor-crop eval** (`signal_final_{cell}_{seed}.json`), phase7 = diagnostic으로 고정.
- Stage R에 step0/final signal eval 행을 추가.

### MF-6. STOP가 protocol validity에 gated되지 않음

- mechanics 실패/M 미해석/endpoint NA에서도 negative를 route STOP으로 읽을 수 있다.
- 수정:
  - route STOP은 mechanics valid + endpoints evaluable(15 docs) + M interpretable + both cells fail copy/full 3/3 + paired CI not >0일 때만.
  - 그 외는 `NOT_EVALUABLE`, STOP 아님.
- F0 결과는 Phase 6 negative/B0-B 미승인을 소급 변경하지 않음.

### MF-7. Compute와 D1 병렬성

- Phase 6 D1: parallel 4 arms 1,180.6s; sequential 3,116.5s.
- v0.2 D1 cap 25min은 4-way parallel 전제인데 명시되지 않았다.
- 수정:
  - D1 `parallel_arms:true` (4 processes × 2 threads 또는 3 threads) 명시.
  - sequential fallback cap 55min.
  - R 900 updates ≤120min, T_proj analog + hard abort.
  - E00 step0=final이므로 signal eval 1회.

### MF-8. Interpretation scope

- “adapter as configured” = adapter params + adapter LR 10× + RNG stream + LoRA init (fixed after MF-1).
- “route as configured” = EG2 layer19 raw 753×512, mT5-small base eval, 64×r8 LoRA, 100 updates, 20 docs, donor-crop assay.
- E01+/E11+ 분기: replication/anomaly investigation, not H3.
- F0 positive는 adapter architecture의 유일 인과를 확정하지 않는다.

## 4. 검토자별 요지

### GLM

- Stage D/R 수정은 agree(conditional).
- D1 E00 모순, D0 adapter vector 오탈자.
- primary source ambiguity (Phase 6 −0.1135 vs −0.0407).
- T_proj analog + signal eval budget.
- NARROW.

### DeepSeek

- “LoRA fixed” false at initialization (RNG).
- mechanics pass undefined → discretionary gate.
- per-cell significance ≠ paired contrast.
- STOP not protocol-gated.
- 25min only with unstated 4-way parallel.
- NARROW.

### Sol

- Bind cell predicates and primary contrast; resolve legacy L>F conjunct.
- Correct mechanics contract; E00 no optimizer, 3 D1 updates.
- Runtime/projection/replay/cap accounting.
- Bound causal language to configured regime; explicit RNG/donor/crop/record bindings.
- NARROW.

## 5. 결정

```text
F0 v0.2 = 3/3 NARROW
F0 = 미승인, 미실행
LoRA RNG fix = prerequisite
mechanics predicate = prerequisite
paired CI decision = prerequisite
protocol-valid STOP = prerequisite
B0-B = 미승인 (Phase 6 negative)
```

## 6. 다음 단계

1. F0 v0.3:
   - LoRA 전용 seed 재설정 + 초기 state hash assert.
   - D1 3 updates + E00 eval-only; D0 adapter vector 수정.
   - mechanics pass predicate 열거.
   - primary = paired E01−E11 CI; source = final-checkpoint donor-crop.
   - STOP protocol-valid gate.
   - compute parallel/sequential 명시.
   - interpretation scope.
2. v0.3 3-AI 재검토.
3. 승인 후에만 F0 코드/D0/D1/R.

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_f0_v0_2_review_2026-11-09/review_GLM.md` | GLM NARROW |
| `.../review_DS1017.md` | DeepSeek NARROW |
| `.../review_SOL.md` | Sol NARROW |
| `reports/C5_F0_V0_2_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |

## 8. 제한

- 이 종합은 F0 승인이 아니다.
- 3/3 NARROW: v0.3 수정 후 재검토.
- test 163 sealed; P1 unused; T5Gemma2 D-108 STOP.
