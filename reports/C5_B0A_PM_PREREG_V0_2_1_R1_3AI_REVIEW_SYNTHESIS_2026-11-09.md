# C5 Phase 6 v0.2.1-r1 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r1_2026-11-09/`
- 검토 기준 HEAD: `4920953`
- 모델:
  - GLM 5.3 Flash **max**
  - Sonnet 5.5 **medium**
  - Sol 6.1 **medium**
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_1_R1_2026-11-09.md`
- 원문:
  - `review_GLM.md` (19,412 chars)
  - `review_SONNET.md` (21,863 chars)
  - `review_SOL.md` (28,001 chars)
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **3/3 NARROW.** r1은 factored output, M preflight, cap 분리, PA 명명, statistics constants를 실제로 개선했지만, **M_VALID가 status 함수에 연결되지 않았고**, **path flag 열거/PA path 충돌**, **L 보존 불변식**, **K_M_L 선택 규칙**, **D1/timing gate**가 남았다. **r2 text-only repair 후 동결**해야 하며, 구현·D0·D1·3-seed·B0-B는 아직 미승인이다.

---

## 1. 판정 행렬

| 검토자 | 판정 | r2 | 동결 | 구현+unit tests | D0 | D1 | 3-seed |
|---|---|---|---|---|---|---|---|
| GLM max | **NARROW** | 필요 | B-1~B-5 후 | 동결 후 승인 | 승인(동결 후) | 미승인 | 미승인 |
| Sonnet medium | **NARROW** | 필요 | r2 후 | 조건부 | 조건부 | 미승인 | 미승인 |
| Sol medium | **NARROW** | 필요 | not as written | 조건부 | 미승인(현재) | 미승인 | 미승인 |
| **종합** | **NARROW 3/3** | **필요** | **미승인** | **미승인** | **미승인** | **미승인** | **미승인** |

STOP 0/3, CONTINUE 0/3.

---

## 2. 실제로 닫힌 것

- factored `validity/control/signal` output 방향
- tri-state Kleene 도입
- `INCONCLUSIVE_SMALL_N` dead cell 해소
- `MEAN_CONTRAST_ONLY` 도달 가능
- `ADAPTER_REGIME_LOSS` 삭제, `PA_STEP100_NOT_VALID` 도입
- M preflight: K=753, 16 contributors, 15/20 targets, full-K 11/20 secondary
- registered 12×100=1,200와 D0 0-update 분리
- D1 4×1 update 별도 승인
- statistics constants 고정
- L flag를 flags에 보존하는 원칙

세 검토자 모두 r1을 v0.2.1보다 **명확히 개선**됐다고 평가했다.

---

## 3. 남은 Must-fix

### MF-1. `M_VALID` / `m_valid_p` / `m_valid_pa`의 status 슬롯 상실

**문제**

- r1 §4.5는 `M_VALID = P/PA POS AND NORM`을 요구하지만,
- §2.3 validity와 §2.4 control은 `m_evaluable`, `m_pass_l`만 사용한다.
- P/PA M validation이 **계산되어 실패**해도 `m_pass_l=true`이면 `M_CONTROL_PASS`가 가능하다.
- `p_valid/pa_valid=false`여도 control이 pass가 가능하다.
- v0.2.1의 `M_CONTROL_NOT_VALID`를 삭제만 하고 대체 cell을 만들지 않았다.

**r2 요구**

- `m_valid` tri-state를 flag vector에 추가:
```text
m_valid = AND3(
  m_pass_pos_p, m_pass_norm_p,
  m_pass_pos_pa, m_pass_norm_pa
)
```
- `control_status`를 `m_valid`까지 확장:
```text
M_NOT_EVALUABLE
M_CONTROL_INVALID   # P/PA M calibration false
M_CONTROL_PASS
M_CONTROL_FAIL
NOT_ASSESSABLE
```
- `M_CONTROL_INVALID`를 새 label로 사용; `M_CONTROL_NOT_VALID` 부활 금지.
- P_VALID/PA_VALID false 또는 M_VALID false면 L M pass를 주장하지 않는다.
- B0-B predicate에 `m_valid=true`를 명시.

### MF-2. Path/test flag 열거와 PA path 충돌

**문제**

- §2.3 rule 1: “any path/test flag false → ASSAY_INVALID”
- §2.3 각주: “PA path fail → PA_STEP100_NOT_VALID”
- `pa_step100_path_ok`가 “any path”에 포함되면 두 규칙이 충돌.
- §2.8 truth table는 단일 `path`만 사용해 P/PA path 구분을 검증할 수 없다.

**r2 요구**

- named flags:
```text
assay_path_ok
p0_path_ok
p_step100_path_ok
pa_step100_path_ok
test_split_used
```
- 우선순위:
```text
assay_path_ok=false or p0_path_ok=false -> ASSAY_INVALID
p_step100_path_ok=false -> ASSAY_INVALID
pa_step100_path_ok=false and p_valid=true -> PA_STEP100_NOT_VALID
pa_step100_path_ok=false and p_valid!=true -> P_STEP100_NOT_VALID (또는 ASSAY_INVALID)
```
- P path fail을 `ASSAY_INVALID`로 통일.
- simultaneous P/PA path fail cell test.
- truth table input에서 aggregate `path` 제거.

### MF-3. L 보존 불변식과 signal precedence

**문제**

- `l_signal=true`, `m_pass_l=NA`, `n>=15`이면 signal_status가 `NOT_ASSESSABLE`로 L을 잃는다.
- `n_signal<15`와 `l_signal=true`가 동시에 가능한데, §2.8은 “n<15는 항상 INCONCLUSIVE”와 “L true는 signal_status가 L을 잃지 않는다”를 동시에 요구한다.
- `l_copy=F`, `l_full=NA`는 AND3상 l_signal=F이지만, “required NA”가 먼저 `NOT_ASSESSABLE`로 보낸다.
- `l_copy=F`, `l_full=F`, control `M_NOT_EVALUABLE`이 `NOT_ASSESSABLE`로 떨어진다.

**r2 요구**

- L 보존은 **flags에서 보장**, signal_status는 L-qualified label을 추가:
```text
L_SIGNAL_CONTROL_NOT_ASSESSABLE
NO_L_SIGNAL_CONTROL_NOT_EVALUABLE
```
- `INCONCLUSIVE_SMALL_N`은 flags 보존을 전제로 하고, “L을 signal_status에서 항상 보존” 문구를 **정확히 수정**.
- “required signal flags”를 `l_copy`, `l_full`로 명시.
- `l_copy=F, l_full=NA` → `NOT_ASSESSABLE`이 아니라 `l_signal=F` (AND3)로 계산; 단 signal_status에 `NOT_ASSESSABLE` 사유를 별도 기록.
- `l_copy=F, l_full=F, control not evaluable` → `NO_L_SIGNAL_CONTROL_NOT_EVALUABLE`.
- truth table domain에 `n_signal={NA,0,14,15,20}` 및 control NA를 포함.

### MF-4. K_M_L=753 선택 규칙 미기재

**문제**

- 753은 “common cohort ≥15/20 ∧ contributors ≥10을 만족하는 최대 K”로 역산되지만 r1/preflight에 규칙이 없다.
- 정확히 15/20, zero margin.
- K=753은 val 문서 `01331`의 h=753 경계와 일치.
- 15/20은 “the 15 longest-of-20 val docs”이며, length-conditioned cohort다.

**r2 요구**

- 선택 규칙을 문자로 고정:
```text
K_M_L = max K such that
  train contributors >= 10
  and val target eligible >= 15
```
- preflight artifact hash를 freeze manifest에 포함.
- `M_CONTROL_PREFIX753_COHORT15` label/설명 추가.
- excluded shortest-5와 length bias를 report template에 명시.
- K 재산출 금지; artifact에 고정.
- native lengths를 preflight JSON에 추가해 20/20 at 512를 재검증 가능하게 한다.

### MF-5. M builder 결정론 / M_VALID cohort / per-variant 집계

**문제**

- builder가 eval mode인지, adapter/LoRA state가 고정인지 명시 부족.
- M_VALID cohort가 L/P/PA에서 동일 target set인지, 각 variant별인지 불명확.
- `delta_memfree_full/copy` 정의가 r1에 재기술되지 않았다(v0.2 상속).
- P/PA M_VALID와 L M_CONTROL_PASS의 cohort가 다를 수 있다.

**r2 요구**

- builder는 `adapter.eval()`, `model.eval()`, `torch.no_grad()` 고정.
- M_VALID cohort = common 15/20; 각 variant는 같은 target ID에서 평가.
- per-variant M table + pooled seed-average table.
- `delta_memfree_full = mean_full_ce - real_full_ce`; copy 동일.
- M_NORM scale/qualified 표기 유지.
- replay test에 builder state hash 포함.

### MF-6. D0/D1 seed / timing projection / stale naming

**문제**

- r1은 D0/D1 debug seed를 재기술하지 않는다. v0.2.1의 **20261111**을 상속해야 한다.
- D0는 zero-update라 backward/optimizer timing을 측정하지 못한다.
- checklist item 6 “timing projection ≤0.8×cap”은 실질적으로 D1을 요구하지만, §6.3은 D1 없이 implementation gate 통과 가능이라고 한다.
- `bootstrap_paired`의 `seeds_positive`에 문서 수를 저장하는 stale naming.
- v0.2의 `REGIME_ERASES_SELECTIVITY` 참조가 남아 있다.

**r2 요구**

- D0/D1 seed = **20261111** 명시.
- D0-only projection은 **허용하지 않는다**; D1 1-update timing 또는 별도 timing probe 없으면 3-seed launch 금지.
- D1을 timing gate의 필요조건으로 명시하거나, D1 없이 3-seed를 금지.
- `not_a_result:true`, `labels_computed:false`.
- `seeds_positive` → `documents_positive` 구현 DoD.
- stale label grep/fix.

---

## 4. 3-seed / B0-B 경계

3-seed checklist 추가:

- preflight JSON hash
- debug seed 20261111 ∉ registered seeds
- D1 timing projection (or explicit timing probe)
- freeze commit 이후 threshold/seed/donor/step/LR diff 없음
- P/PA M_VALID true
- `M_CONTROL_PREFIX753_COHORT15` 명시

B0-B predicate:

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS
AND signal_status == EXPLORATORY_L_SIGNAL
AND m_valid == true
AND tail_driven == false (or reported)
AND leakage/mode/metric pass
AND artifact complete
AND separate prereg/approval
```

`EXPLORATORY_L_SIGNAL`만으로 B0-B를 승인하지 않는다.

---

## 5. 결정

```text
r1 = NARROW 3/3, not frozen
r2 = 필요 (text-only)
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

## 6. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r1_2026-11-09/review_GLM.md` | GLM |
| `.../review_SONNET.md` | Sonnet |
| `.../review_SOL.md` | Sol |
| `reports/C5_B0A_PM_PREREG_V0_2_1_R1_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r1.md` | r1 |
| `reports/provenance/C5_b0a/m_cohort_preflight.json` | M preflight |

## 7. 제한

- 이 종합은 승인이 아니다.
- 3/3 NARROW는 bridge STOP이 아니다.
- r2 없이 코드를 작성하지 않는다.
- “54 tests”는 historical evidence이며 PM tests는 아직 없다.
