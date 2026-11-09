# C5 B0-A Phase 6 P/M Prereg — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_2026-11-09/`
- 검토 기준 HEAD: `26e334a`
- 검토 모델:
  - GLM 5.3 Flash **max**
  - Sonnet 5.5 **high**
  - Sol 6.1 **high**
- 검토요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_2026-11-09.md` (356줄)
- 원문:
  - `docs/hoplite/c5_b0a_pm_prereg_2026-11-09/review_GLM.md` (14,659 chars)
  - `docs/hoplite/c5_b0a_pm_prereg_2026-11-09/review_SONNET.md` (39,150 chars)
  - `docs/hoplite/c5_b0a_pm_prereg_2026-11-09/review_SOL.md` (34,862 chars)
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**
- B0-B/B1/B2/Stage C: **미승인**

---

## 0. 한 줄 결론

> **3/3 NARROW.** P/M/F/L 분리 구조는 채택 가능하지만, **P positive gate가 near-vacuous**하고 **P0의 Δ가 catastrophic wrong-memory에 민감한 heavy-tail**이며, **M 정의·decision label·copy mask**에 Must-fix가 있다. **v0.2 사전등록 개정 전에는 구현·1-seed debug도 승인되지 않는다.** Phase 6/B0-B 자동 진행 없음.

---

## 1. 판정 행렬

| 검토자 | 최종 판정 | 구현·1-seed debug | 3-seed |
|---|---|---|---|
| GLM 5.3 Flash max | **NARROW** | MF-1~MF-3 구현·테스트 후 조건부 | 별도 gate |
| Sonnet 5.5 high | **NARROW** | v0.2 개정 후 non-gating mechanics debug만 | 미승인 |
| Sol 6.1 high | **NARROW (conditional)** | 실행 승인 없음; Must-fix 계약 동결 후 | 미승인 |
| **종합** | **NARROW 3/3** | **현 v0.1로는 미승인** | **미승인** |

STOP 0/3, CONTINUE 0/3.

---

## 2. 검토자별 핵심

### GLM

- P/M/F/L 분리는 타당.
- eval-only M은 Phase 6 질문에 직접적인 paired 검증.
- P_POSITIVE는 **약한 통제**이며, 정보 가치는 주로 decoder-LoRA 학습이 경로를 파괴하는지의 실패 검출.
- Must-fix:
  1. P-arm path/mode assert
  2. M leakage assert + provenance
  3. metric_alignment hard assert
  4. donor/K provenance
  5. pooling/mask warning/cap 정의

### Sonnet

- **P_POSITIVE는 거의 vacuous**: P0가 이미 +3.76/+5.24이므로, P가 경로를 파괴하지 않으면 거의 통과.
- P0의 untrained CE 12.7/13.2는 `ln|V|=12.43`보다 높다. Δ는 **graded content use가 아니라 catastrophic wrong-memory 민감도**.
- val Δ 평균의 약 **49%가 3/20 문서**에서 나오는 heavy-tail.
- P는 adapter bypass로 F/L과 다른 regime; **PA (native memory + adapter + LoRA)**가 필요.
- M은 eval-only가 맞지만, real reference 고정·norm·eligibility·position-wise 의미·P/PA에서의 validation이 필요.
- `NO_CONTENT_USE_EVIDENCE`는 absence of evidence를 evidence of absence로 오독할 수 있다.
- `L_SIGNAL true + M fail` cell이 label 표에 없다.
- as-run copy mask coverage 82~84%는 **copy-specific이 아니다.** P0 Δcopy ≈ Δfull. strict mask가 유일하게 copy-specific.
- v0.2를 결과 전에 commit/freeze해야 한다.

### Sol

- P adapter bypass는 native path assay control로 타당; EG2 bridge control은 아니다.
- eval-only M은 같은 checkpoint input intervention으로 타당; trained M은 다른 질문.
- mean은 length-conditional로 leakage-free일 수 있으나, cohort/missingness/EOS/crop 규칙을 동결해야 한다.
- M_CONTROL_PASS만으로 semantic content use를 주장할 수 없다.
- P 실패는 **ASSAY_INVALID**보다 **REGIME_ERASES_SELECTIVITY**가 더 정확할 수 있다.
- `NO_CONTENT_USE_EVIDENCE`도 “no affirmative evidence”로 제한해야 한다.
- 20/20/100/3 seeds는 screening envelope; confirmatory/generalization 아님.
- Must-fix 5개:
  1. mean builder/leakage/eligible cohort
  2. same-position CE + P mode invariants
  3. donor/K semantics + M baseline
  4. pooling/decision/missingness executable
  5. artifacts/checkpoints/approval/compute cap
- B0-B는 별도 사전등록·승인.

---

## 3. 공통 결함

### 3.1 P gate가 약하다

```text
P_POSITIVE = mean Δcopy > 0 and CI lower > 0
```

- P0가 이미 positive.
- P가 학습 중 경로를 파괴하지 않으면 거의 통과.
- F/L의 CE ≈ 6.5~7.7 operating point와 P의 CE regime이 다르다.
- P0 real CE 12.7/13.2 > uniform 12.43.
- **P는 “metric이 catastrophic wrong memory를 구분한다”는 것만 보여준다.**

### 3.2 P0 heavy-tail

- val Δcopy 범위 −5.8 ~ +19.1.
- 상위 3개 문서가 평균의 약 49%.
- per-doc real CE 5.5~20.9.
- 20-doc bootstrap은 heavy-tail에서 anti-conservative.

### 3.3 P arm과 F/L의 regime 불일치

- P: native encoder, adapter 없음, LoRA only.
- F/L: EG2 memory, adapter + LoRA.
- P가 통과해도 **F/L의 adapter-as-soft-prompt 문제**를 분리하지 못한다.
- **PA (native memory + adapter + LoRA)**가 필요하다는 지적.

### 3.4 M 정의

- eval-only 자체는 3/3 수용.
- 그러나:
  - real reference가 donor별 crop인지 full인지 고정되지 않음
  - mean의 norm이 OOD일 수 있음
  - `len>=K` / eligible>=10이 survivorship bias를 만든다
  - “position-wise”는 T5 cross-attention position bias가 없어 의미가 약하다
  - P/PA에서 M을 validate해야 한다
  - M-norm, M-global, row-permutation, perturbation invariance가 필요

### 3.5 Label semantics

- `NO_CONTENT_USE_EVIDENCE`는 **no affirmative evidence**로 제한.
- `P fail → ASSAY_INVALID`는 P0 pass 때문에 **REGIME_ERASES_SELECTIVITY**가 더 정확.
- `L_SIGNAL true + M_CONTROL_FAIL` cell이 없다.
- `L > F`, `2/3 seeds`의 정의·pooling이 코드에 없다.
- `bootstrap_paired.seeds_positive`는 **문서 수**인데 이름이 seed 수처럼 보인다.

### 3.6 Copy mask

- coverage .8246/.8351.
- P0 Δcopy ≈ Δfull (3.76 vs 3.50; 5.24 vs 5.29).
- **copy-specific metric으로 부르기 어렵다.**
- aligned full CE를 co-primary, strict mask를 secondary/exploratory로 두는 것이 안전.

### 3.7 구현 전 상태

- `--mode pm-diagnostic` 미구현.
- `set_training_mode`는 F/L만 지원.
- P/PA/M tests 없음.
- `torch.manual_seed`가 P LoRA 초기화 전에 없으면 seed 재현성 문제.
- 54 tests는 historical evidence; 검토자가 재실행하지 않음.

---

## 4. v0.2 Must-fix (ranked)

| 순위 | Must-fix | 완료 조건 |
|---:|---|---|
| 1 | **P gate 강화 + PA arm** | P Δ ≥ .05? / step0 vs step100 / native PA(adapter+LoRA) 결과; P0와 다른 regime 명시 |
| 2 | **M definition 동결** | real reference, crop/EOS, norm, eligible cohort, M-norm/M-global, P/PA validation |
| 3 | **leakage·seed·mode tests** | val/target/donor leakage assert, P seed, 64 modules, mode invariant |
| 4 | **decision/label 재작성** | L_SIGNAL+M fail cell, no-evidence semantics, `REGIME_ERASES_SELECTIVITY`, pooling/2-of-3 seeds |
| 5 | **metric co-primary** | aligned full CE + strict mask secondary, copy claim 제한 |
| 6 | **artifact/cap contract** | per-doc donor/K, `m_eligible`, checkpoint hash, timing, 2 CPU-h 정의 |

이 Must-fix는 **v0.2 사전등록 개정**으로 닫아야 하며, 결과 전에 commit hash를 고정해야 한다.

---

## 5. 결정

```text
Phase 6 v0.1 = NARROW 3/3
Phase 6 구현 = 미승인
1-seed debug = 미승인 (v0.2 이후 별도)
3-seed 실행 = 미승인
B0-B = 미승인
B1/B2/Stage C = 미승인
test 163 = sealed
P1 = 미사용
T5Gemma2 = D-108 STOP
```

### 다음

1. v0.2 사전등록 작성:
   - P/PA/P0 gate 재정의
   - M real reference·norm·eligible·validation
   - label table 수정
   - aligned full CE co-primary / strict mask secondary
   - pooling·seed·cap·artifact contract
2. v0.2 commit/freeze
3. 사용자 승인 후 **구현 + non-gating 1-seed debug**
4. 1-seed debug 결과 gate에서 3-seed 여부 결정
5. 3-seed 결과 후에도 B0-B는 별도 decision

---

## 6. 원문·산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_2026-11-09/review_GLM.md` | GLM 원문 |
| `docs/hoplite/c5_b0a_pm_prereg_2026-11-09/review_SONNET.md` | Sonnet 원문 |
| `docs/hoplite/c5_b0a_pm_prereg_2026-11-09/review_SOL.md` | Sol 원문 |
| `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_2026-11-09.md` | 검토요청서 |
| `docs/plan_c5_b0a_pm_prereg_v0_1.md` | v0.1 사전등록 (개정 대상) |
| `docs/plan_c5_b0a_repair_v0_1.md` | repair 계획 |
| `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md` | P0 결과 |

## 7. 해석 제한

- 이 종합은 Phase 6/B0-B 실행 승인이 아니다.
- 3/3 NARROW는 bridge 전체 STOP이 아니다.
- P0의 SENSITIVE_POSITIVE는 graded content use 증거가 아니다.
- v0.1의 threshold·seed·donor·step을 결과 후 변경하지 않는다.
