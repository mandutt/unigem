# C5 Phase 6 v0.2.1-r3.1 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r3_1_2026-11-09/`
- 검토 기준 HEAD: `c4ed30a` (요청서 커밋)
- 모델:
  - GLM 5.3 Flash **max**
  - DeepSeek V4.1 Flash **1017** **high** — Hoplite `deepseek-v4.1-flash-1017`
  - Sol 6.1 **medium**
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_1_R3_1_2026-11-09.md`
- 원문:
  - `review_GLM.md` (17,555 chars)
  - `review_DS1017.md` (25,250 chars)
  - `review_SOL.md` (27,638 chars)
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **1 CONTINUE(조건부) / 2 NARROW.** GLM은 residual 1~5를 text로 반영하면 동결·구현·D0를 조건부 승인하지만, DeepSeek 1017과 Sol은 **r3.1을 그대로 동결하면 안 된다**고 본다. 핵심은 `L_FULL_SIGNAL`의 **full threshold가 `>0`에서 `>=.05`로 몰래 바뀐 것**, D1 projection에서 **generation/20-train M build 누락**, **M_NORM 고정 공식 제거**, **hash canonicalization 미정의**, **B0-B의 tail_driven 우회**다. **r3.2 text-only repair** 후 재검토한다.

---

## 1. 판정 행렬

| 검토자 | 모델 | 판정 | r3.1 동결 | 구현+unit tests | D0 | D1 | 3-seed |
|---|---|---|---|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **CONTINUE(조건부)** | residual 1~5 후 | 조건부 | 조건부 | 미승인 | 미승인 |
| DeepSeek 1017 | `deepseek-v4.1-flash-1017` high | **NARROW** | 아니오 | 미승인 | 미승인 | 미승인 | 미승인 |
| Sol | `gpt-6.1-sol` medium | **NARROW** | 아니오 | 미승인 | 미승인 | 미승인 | 미승인 |
| **종합** | — | **NARROW / 보류** | **미승인** | **미승인** | **미승인** | **미승인** | **미승인** |

- STOP 0/3.
- CONTINUE 1/3 conditional.
- NARROW 2/3.
- **만장일치 아님** → freeze하지 않는다.

---

## 2. 실제로 닫힌 것

세 검토자가 인정한 항목:

- `ANDn`/`ORn`/`NOT3` n-ary (2/4/5)
- validity-NA label 분리
- F1~F8 precedence fixtures
- `builder_ok` zero/nonfinite/contributor routing
- endpoint 15×3×4×variants identity
- `n_signal ∈ {NA,0..20}`
- stats module / `documents_positive` / 2-of-3
- per-axis truth table + named cells
- replay prelaunch vs post-run 분리
- preflight hash `3ee3f1ca…`

DeepSeek/Sol도 residual 9개가 **text 수준에서 모두 메커니즘을 얻었다**고 평가했다. 문제는 새로운/남은 contract 결함이다.

---

## 3. 남은 Must-fix

### MF-1. `L_FULL_SIGNAL` threshold 회귀

**문제**

- r3.1 §9.2:
```text
L_COPY_SIGNAL = mean delta_copy >= .05 ...
L_FULL_SIGNAL = same for full
```
- 상속된 v0.2/v0.2.1 계약:
  - copy: mean delta_copy **>= .05**
  - full: mean delta_full **> 0**
- “same for full”은 full에 `.05`를 적용한 것으로 읽힌다.
- §0의 “threshold 변경 없음”과 모순.

**r3.2 요구**

- 두 predicate를 **전문 재기술**:
```text
L_COPY_SIGNAL = mean delta_copy >= .05
                AND copy CI lower > 0
                AND paired L>F copy > 0
                AND 2/3 seed means > 0

L_FULL_SIGNAL = mean delta_full > 0
                AND full CI lower > 0
                AND paired L>F full > 0
                AND 2/3 seed means > 0
```
- threshold 변경 없음.
- `seed_mean`은 해당 endpoint의 L shuffled-minus-real contrast; L−F와 구분.

### MF-2. Truth-table fixture 16/17 불일치

**문제**

- §4.3 `M_CONTROL_PASS`는 `m_pass_l=true`를 요구.
- §6.2 fixture 17: “M pass L false + control PASS → MEAN_CONTRAST_ONLY”는 **도달 불가능**.
- fixture 16: “M pass L true + control PASS → EXPLORATORY”는 validity/n/L flags 전제가 부족.

**r3.2 요구**

- fixture 16:
  - validity VALID
  - n_signal >=15
  - l_copy=true, l_full=true
  - m_pass_l=true
  - m_evaluable=true, p/pa valid, m_valid=true
  - expected `EXPLORATORY_L_SIGNAL`
- fixture 17:
  - validity VALID
  - n_signal >=15
  - l_copy=false, l_full=false
  - m_pass_l=true
  - control PASS
  - expected `MEAN_CONTRAST_ONLY`
- `m_pass_l=false` fixture:
  - control FAIL
  - expected `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE`
- 모든 fixture는 primitive input에서 derive.

### MF-3. D1 projection 누락

**문제**

- D1 phases:
  - train 1
  - step0 eval 20
  - final eval 20
  - M builder 20/15
  - replay 15
- **generation 20 docs × max_new_tokens**가 빠짐.
- **20-train M build**가 `t_M_build_15`에 포함되는지 불명확.
- donor multiplicity, variants, replay coverage, load/checkpoint overhead도 ledger에 없음.
- `T_proj ≤96`이 실제 2h cap을 넘길 수 있음.

**r3.2 요구**

- D1 phase ledger에 다음을 명시:
  - generation 20 docs × exact max_new_tokens
  - 20-train M builder + 15-target M scoring
  - donor multiplicity (5 donors)
  - variants (M_POS_MEAN, M_NORM)
  - replay 15 targets
  - load/checkpoint/process/report overhead
- `T_proj`에 `t_generate_20` 추가.
- subset normalization은 fixed subset + per-doc scaling; fixed overhead는 별도.
- 96분 launch screen / 120분 hard cap / no retry.

### MF-4. `M_NORM` 고정 공식 제거

**문제**

- r3/r2/r1/errata의 고정 공식:
```text
M_NORM = M_POS_MEAN * (||real_prefix_753||_F / ||M_POS_MEAN||_F)
```
- r3.1 §8.2는 “magnitude-matched with target real-prefix norm; target-dependent”로만 기술.
- one matrix vs per-target matrix가 불명확.
- `builder_ok`의 `||real_prefix||_F`가 어떤 aggregate인지 불명확.
- control statistic이 달라질 수 있음.

**r3.2 요구**

- 고정 공식 복원:
  - **one global M matrix** (train-only mean) × **single scalar** from target-set real prefix norm.
  - per-target matrix가 아니면 “target-dependent” 문구 삭제.
- `builder_ok`는 **single global scalar** `||real_prefix_set||_F`를 검사.
- one-matrix vs per-target을 명시.
- M_NORM은 magnitude-matched, target-set-norm-dependent; target-label leakage 없음.

### MF-5. hash canonicalization 미정의

**문제**

- `debug_replay_hash`, `final_checkpoint_hash`, `final_replay_hash` 이름만 있음.
- key ordering, dtype, byte order, contiguous/view, fp32/bf16, LoRA A/B, adapter state order 미정의.
- “exact endpoint identity”와 replay equality가 재현 불가.

**r3.2 요구**

- canonical serialization:
  - sorted keys
  - dtype string
  - little-endian
  - contiguous
  - state_dict key order sorted
  - LoRA A/B + adapter + base mode 포함
  - SHA256 over canonical bytes
- golden-vector test.
- prelaunch debug hash와 postrun final hash 모두 같은 canonicalizer.

### MF-6. B0-B `tail_driven` 우회

**문제**

- r3.1 §14:
```text
tail_driven == false (or explicitly reported)
```
- `tail_driven=true`도 “reported”로 통과 가능.
- B0-B hard gate가 reporting requirement로 약화.

**r3.2 요구**

- B0-B predicate:
```text
tail_driven == false
```
- `tail_driven=NA`도 B0-B 불가.
- 보고는 별도; gate는 hard false.

### MF-7. signal validity / small-N precedence

**문제**

- `n_signal<15` 분기가 validity보다 앞서므로 validity invalid가 small-N label로 가려짐.
- 결정적/fail-closed이지만 의도된 계약인지 문장이 없음.
- F9/F10:
  - `p_step100_path_ok=NA` + `p_valid=false` → 현재 NOT_ASSESSABLE (assay tier NA)
  - `pa_path=NA` + `pa_valid=false` → NOT_ASSESSABLE
- “known failure first”의 tier를 명시해야.

**r3.2 요구**

- small-N precedence를 명시:
  - n<15이면 small-N label 우선; validity/control은 별도 축으로 기록.
  - 또는 validity INVALID 우선으로 순서 변경.
  - 어느 쪽이든 fixture로 고정.
- F9/F10/F11:
  - p path NA + p_valid false
  - pa path NA + pa_valid false
  - n<15 + validity INVALID
- expected label 명시.

### MF-8. statistics partial endpoint / undefined tail

**문제**

- n_signal endpoint membership이 arm/seed intersection으로 명시되지 않음.
- partial endpoint/missing seed/nonfinite CE 처리.
- zero-sum delta, top3 denominator 0, `tail_driven=NA`.
- `tail_driven=NA`가 false로 접힐 위험.

**r3.2 요구**

- canonical endpoint key set: F/L arms × 3 seeds × copy/full.
- missing seed는 pooling하지 않음.
- excluded ID/reason 기록.
- `tail_driven` tri-state:
  - known positive criterion → true
  - both known false → false
  - otherwise NA
- B0-B requires false (not NA).
- top3 denominator 0 → null.

---

## 4. 검토자별 차이

### GLM

- 9 residual 모두 닫힘.
- Must-fix 1~5:
  - signal small-N vs validity precedence
  - D1 generation/M build completeness
  - `§6.4` dangling reference
  - hash 표현 (“committed blob” vs content SHA)
  - signal endpoint length rule
- 조건부 CONTINUE.

### DeepSeek 1017

- 9 residual 모두 text mechanism.
- NARROW:
  - L_FULL_SIGNAL threshold 회귀
  - M_NORM formula 제거
  - D1 generation/20-train M build 누락
  - hash canonicalization
  - B0-B tail_driven 우회
- r3.2 Must-fix 1~5.

### Sol

- NARROW:
  - L_FULL_SIGNAL threshold
  - fixture 16/17 impossible
  - D1 workload ledger incomplete
  - partial endpoint/tail NA
- r3.2 text-only.

**해석**: GLM은 작은 micro-errata로 충분하다고 보지만, DS1017/Sol은 **threshold 변경·M_NORM·D1·hash**를 freeze blocker로 본다. r3.2에서 모두 닫아야 한다.

---

## 5. 결정

```text
r3.1 = 동결 보류 (1 CONTINUE conditional / 2 NARROW)
r3.2 = 필요 (text-only)
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

1. r3.2 text-only errata:
   - L_COPY/L_FULL predicates 전문 재기술
   - fixture 16/17/18 수정
   - D1 generation + 20-train M build + ledger
   - M_NORM fixed formula
   - canonical hash + golden vector
   - B0-B `tail_driven == false`
   - small-N/validity precedence + F9/F10/F11
   - partial endpoint/tail tri-state
   - `§6.4` → `§6`, hash 표현 교정
2. r3.2 3-AI 재검토
3. freeze commit
4. 구현 + unit tests
5. D0
6. D1 separate
7. 3-seed separate
8. B0-B separate

---

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r3_1_2026-11-09/review_GLM.md` | GLM |
| `.../review_DS1017.md` | DeepSeek 1017 |
| `.../review_SOL.md` | Sol |
| `reports/C5_B0A_PM_PREREG_V0_2_1_R3_1_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_1.md` | r3.1 |
| `reports/provenance/C5_b0a/m_cohort_preflight.json` | M preflight |

## 8. 제한

- 이 종합은 승인이 아니다.
- 1 CONTINUE / 2 NARROW는 만장일치가 아니다.
- r3.2 없이 코드를 작성하지 않는다.
- “54 tests”는 historical evidence이며 PM tests는 아직 없다.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아니다.
