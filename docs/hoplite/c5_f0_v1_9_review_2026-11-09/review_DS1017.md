# C5 F0 v1.9 — Independent Review (DS1017)

- 검토일: 2026-11-10
- 대상: `docs/plan_c5_f0_v1_9_2026-11-09.md` (655 lines)
- **Reviewed HEAD: `d88d8de1f7641fd44761dadedc8b5d0ffc53498b`**
  (`docs: add C5 F0 v1.9 review request`, 2026-11-10 12:24:16 +0900)
- 동기화: `git fetch origin` → ok (`main -> FETCH_HEAD`); `git pull --ff-only origin main` → **Already up to date.**
- 범위: consultation only. 학습/평가 없음, test 163/P1 없음, subagent 없음, 이 파일 외 repo 수정 없음.
- v1.8 결론 상속 없음. 새 10-round block, round 9.
- 모델: `deepseek-v4.1-flash-1017`

---

## 0. Verbatim paired E01−E11 (mandatory)

§2 (line 61):

```text
- Primary: **E01 vs E11** (LoRA initialization matched).
```

§6.2 (line 208):

```text
delta_c(s,d) = mean_donor( CE_wrong_donor - CE_real )
```

§6.3 (lines 217–221):

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

§6.4 (lines 235–240):

```text
SIGNAL(c,copy) = mean(delta_c) >= .05
                 AND CI.lower > 0
                 AND 2/3 seeds > 0
SIGNAL(c,full) = mean(delta_c) > 0
                 AND CI.lower > 0
                 AND 2/3 seeds > 0
```

§7 (line 301):

```text
| 2 | `PASS_POSITIVE` | `mean_D>0` AND `CI_D.lower > +.05` AND `SIGNAL(E01,copy)` AND 2/3 seeds `D_s>0` |
```

---

## 1. 판정 요약

리뷰 요청의 Q1–Q6(CE formula/dry-run, P/Q per-seed schema, D1 materialization/wall, R mechanics/scope, compute 8 threads, near-threshold)로 답한다. 계획서 §15의 Q1–Q6(init audit, D1 seal, STOP taxonomy, cohort, compute, H3)와 **질문 번호가 다르다** — 이 불일치 자체가 must-fix #7이다.

| Q | 판정 | 핵심 |
|---|---|---|
| Q1 D1 CE formula/dry-run | **disagree** | `expected_real_memory_ce_calls`가 정수로 고정되지 않았고, committed call graph에서 유도하면 `real_memory_ce_calls_ok`가 tautology가 된다. `donor_map_loads:0`과 `per doc×donor`가 상호모순. |
| Q2 P/Q per-seed schema | **disagree** | per-seed 차원은 고쳐졌으나 `p_r_hash_equal`이 P 산출물 안에 있으면서 R 해시를 요구 → 순환. Q의 `wrong_donor_finite`는 §13A.8 "first exercised at R"과 모순. |
| Q3 D1 materialization/wall | **conditional** | wall fallback은 추가됨. 그러나 "counts not persisted"가 §13A.4의 `m_records`/`generation_records` int와 모순. D1 anchor thread 수가 D-156과 불일치. |
| Q4 R mechanics/scope | **disagree** | `r_mechanics_pass`의 **predicate가 정의되지 않았다**. 카운트만 있고 expected/`_ok`가 없다. scope 경계(§14)는 정직. |
| Q5 compute 8 threads | **conditional** | 8 logical threads·900 updates·96 min은 정합. 그러나 D1 25 min의 anchor가 3 threads/arm(D-156)인데 계획은 "2 threads/arm"이라 적었고, Phase 6 실측을 "estimates, not measurements"로 오기. |
| Q6 near-threshold | **conditional** | v1.8의 조작적 정의(b, h, near 조건)를 삭제하고 산문만 남겨 진단이 미정의. EQUIVALENT 도달가능성이 SE 선택에 전적으로 의존하는데 명시 없음. |

**최종 판정: NARROW.**

설계 골격(단일 대조, 15-doc 고정 cohort, doc-level paired bootstrap, 4-state taxonomy, H3 제거, provenance commit 선행)은 v1.8 대비 개선되었고 승인 가능한 수준에 근접했다. 그러나 Q1/Q2/Q4의 세 결함은 **게이트가 실제로 작동하지 않는** 종류다 — 통과/실패를 판정하는 predicate가 순환하거나 미정의이므로, 이 상태로 D1/R을 승인하면 seal이 형식만 남는다. 따라서 CONTINUE가 아니라 NARROW.

---

## 2. Q1 — D1 CE formula / dry-run

**판정: disagree.**

### 2.1 v1.8 blocker는 "틀린 산식"이었고, v1.9는 "산식 없음"으로 바꿨다

v1.8 §13A.4 (line 508)는 `1 + 3 + 3×15×5 = 229`라는 **틀린 정수**를 명시했다. v1.9 §13A.4 (line 498)는 이를 다음으로 교체했다:

```text
expected_real_memory_ce_calls is derived from the committed mechanics evaluator call graph
(counted op = real_memory_ce per doc×donor×cell×phase); 20-doc mechanics and 15-doc
donor-crop counted separately; frozen at D1 code commit, not from the output report;
instrumented dry-run confirms before D1; mismatch → NOT_EVALUABLE.
```

문제는 세 가지다.

**(a) 정수가 prereg에 없다.** 계획서 어디에도 `expected_real_memory_ce_calls`의 값이 없다. §5 D1 assertion 4 (line 44)는 `n_docs_step0 == 20` / `n_docs_final == 20`을 요구하고, §9 (line 340)는 "E00 step0 = final; one signal eval"이라 하므로, eval 경로만 세면 `20×5×(1+2+2+2) = 700`이다. §5 D1 assertion 5 (line 45)의 M records 480 중 real-memory 절반 240을 포함하면 `940`이다. **700도 940도 문서에 없다.** prereg 단계에서 검증 불가능한 게이트는 게이트가 아니다.

**(b) 유도 방식이 tautological이다.** "committed mechanics evaluator의 call graph에서 유도"하고 "instrumented dry-run으로 확인"하면, expected와 actual이 **같은 코드**에서 나온다. 이 비교는 evaluator가 결정적인지만 검사하고, evaluator가 **옳은 연산을 세는지**는 검사하지 못한다. v1.8의 결함은 "산식이 틀렸다"였는데, v1.9는 산식을 코드에 위임해 결함을 **검출 불가능하게** 만들었다. 올바른 형태는 prereg에 독립 산술 정수(예: `700`, M real CE 포함 시 `940`)를 literal로 고정하고, dry-run은 그 literal과 코드 카운트의 일치만 확인하는 것이다.

**(c) `donor_map_loads:0`과 `per doc×donor`가 동시에 성립할 수 없다.** §13A.4 (line 489)는 `donor_map_loads: int (must 0)`을 요구하고, 같은 절 (line 498)은 counted op를 `real_memory_ce per doc×donor`로 정의한다. D1이 doc×donor 단위 real CE를 계산하려면 donor 신원을 resolve해야 하고, 그것이 `donors_for(val20, cache)` 호출이다 — 즉 donor map load다. 반대로 donor를 로드하지 않으면 카운트는 `20×7 = 140`이고 "doc×donor" 서술이 틀린다. **둘 중 하나는 반드시 거짓이다.** §13A.8 (line 527)의 "D1 does not call wrong-donor CE"는 wrong-donor만 배제할 뿐 이 모순을 해소하지 않는다.

### 2.2 "15-doc donor-crop counted separately"는 D1 절에 있지만 D1 단계가 아니다

line 498의 이 절은 R의 15-doc donor-crop을 가리킨다. §5 D1은 20 docs만 쓰고(assertion 4), §13A.8은 D1이 wrong-donor CE를 호출하지 않는다고 못박는다. D1 schema 절에 R 단계 설명이 섞여 있어 독자가 D1 expected에 15-doc 항을 넣도록 오도한다.

### 2.3 다음 단계

1. §13A.4에 `expected_real_memory_ce_calls`의 **정수 literal**을 prereg에 고정(700 또는 940 중 하나를 명시적으로 선택하고, M real CE 포함 여부를 문장으로 결정).
2. `donor_map_loads`의 의미를 "persisted donor-map artifact 로드"로 한정하거나, D1이 donor를 resolve하지 않도록 카운트 정의를 `per doc×cell×phase`로 수정. 둘 중 하나만 남긴다.
3. dry-run은 literal 대조로만 사용하고, "call graph에서 유도" 문구를 "committed evaluator가 literal과 일치함을 확인"으로 교체.

---

## 3. Q2 — P/Q per-seed schema

**판정: disagree.**

### 3.1 고쳐진 것

- §13A.10 (line 544): `per_seed:{seed -> {cells:{E00,E10,E01,E11 -> {hash, lora_names,n_params}}, p_r_hash_equal:bool}}` — v1.8의 "3 seeds × 4 cells를 표현 못 함" 결함은 해소됐다.
- §13A.10 (lines 554–555): `units:4`, `trained_updates:3` per seed — v1.8의 12/9 오기를 §12 aggregate로 되돌렸다(line 561). 정확하다.

### 3.2 남은 blocker: `p_r_hash_equal`의 순환

- `pre_r_init_audit.json`은 **Stage P**에서 쓰인다(§13A.1 line 421–422).
- `pre_r_init_audit_pass:true`는 **R 이전**에 요구된다(§13A.6 line 516, §13A.10 line 546).
- 그 pass의 조건이 "each `p_r_hash_equal:true`"다(§13A.10 line 548).
- 그런데 `p_r_hash_equal`은 이름 그대로 **P 해시와 R 해시의 비교**다. R은 아직 실행되지 않았다.
- §13A.1 (line 422)은 "P records not overwritten by D0"라 하여 P 산출물의 append-only를 선언한다.

따라서 P 시점에 `p_r_hash_equal:true`를 쓸 근거가 없고, R 이후에 채우려면 P 산출물을 덮어써야 한다. **게이트가 자기 자신을 선행조건으로 요구하는 순환**이다. v1.8 리뷰가 지적한 "seed 차원 누락"은 고쳤지만, 그 필드를 P 산출물 안에 넣으면서 새로운 순환을 만들었다.

수정 방향은 둘 중 하나다: (i) P 산출물에는 `p_init_hash`만 두고, `p_r_hash_equal`은 `r/r_mechanics_pass.json`으로 옮겨 R 시점에 기록; 또는 (ii) `p_r_hash_equal`을 "P 해시 == committed builder로 P 시점에 재계산한 해시"로 재정의(즉 P vs builder, P vs R이 아님).

### 3.3 Q의 `wrong_donor_finite`는 §13A.8과 모순

- §13A.10 (line 557): Q cell record에 `wrong_donor_finite`가 있고, line 560은 "finite/shape true"를 pass 조건으로 둔다.
- §13A.8 (line 528): "Primary wrong-donor CE numerical path is **first exercised at R**; Q checks finiteness/shape only."

Q가 wrong-donor CE를 계산해 finiteness를 판정한다면, 그 수치 경로는 **Q에서 처음 실행**된다. "first exercised at R"은 거짓이다. 실제 위험은 값 누출이 아니라(§13A.10 line 425가 per-doc/delta 미저장을 선언) **문서 서술의 오류**지만, 이 문장이 "R까지 수치 경로 미검증"이라는 잔여 위험 서사를 뒷받침하고 있으므로 함께 고쳐야 한다.

### 3.4 다음 단계

1. `p_r_hash_equal`을 P 산출물에서 제거하거나 P-vs-builder 의미로 재정의(§3.2).
2. §13A.8 line 528을 "Q exercises wrong-donor CE for finiteness/shape only; R is the first stage that persists or aggregates it"로 수정.
3. `pre_r_seed_audit_pass`가 데이터와 같은 파일에 자기승인 형태로 있는 점은 유지 가능하나, R gate가 그 파일을 **읽기 전용**으로 소비함을 §13A.10에 한 줄 명시.

---

## 4. Q3 — D1 materialization / wall fallback

**판정: conditional.**

### 4.1 wall fallback은 해소됨

§12 (line 380): "Caps: D1 **25 min provisional**; if measured wall exceeds 25 min, repair or re-review; no silent extension. R **96 min binding**." v1.8 must-fix #5가 요구한 fallback이 명시됐다. §5 D1 (line 51)의 "sequential is diagnostic only, not a gate and not a cap claim"도 일관된다. **agree.**

### 4.2 materialization 문장은 여전히 틀렸다

§5 D1 (line 60):

```text
Signal delta values are never materialized in D1; M/generation counts are computed in memory but not persisted.
```

그런데 §13A.4 (lines 482, 484)는 `m_records: int`, `generation_records: int`를 **파일에 기록되는 키**로 정의하고, §5 D1 assertion 5/7 (lines 45–46)은 `M records == 120/cell; total 480`, `generation == 20/cell; total 80`을 요구한다. 즉 **count는 persist된다.** persist되지 않는 것은 record 배열이다. v1.8 리뷰가 지적한 "values are never materialized" 오기는 절반만 고쳐졌고, "counts ... not persisted"라는 새 오기가 들어갔다. 정확한 문장은 "signal delta values are never materialized; M/generation **records** are computed in memory and only their **counts** are persisted"다.

### 4.3 D1 anchor의 thread 수가 D-156과 불일치

- `docs/decisions.md:216` (D-156): "4 arms 병렬(**3 threads each**), 1 update/arm, ... wall **1,180.6s / 1,200s cap**".
- 계획 §12 (line 375): "D1 anchor used **2 threads/arm**."

같은 문장이 Phase 6 실측을 "**estimates, not measurements**"라고 부르는데, D-156/D-157은 `cap_ok:true`와 함께 기록된 **실측**이다. 두 오류가 겹치면 25 min cap의 근거가 흔들린다: F0 D1은 2 threads/arm(§12 line 372)이므로 3 threads/arm에서 측정된 19.7 min보다 **느릴 수 있고**, 25 min의 27% 여유가 thread 감소분을 덮는다는 보장이 없다. fallback이 있으므로 blocker는 아니지만, cap 근거 문장은 정정해야 한다.

### 4.4 다음 단계

1. §5 D1 line 60을 §4.2의 정확한 문장으로 교체.
2. §12 line 375를 "Phase 6 D1 1,180.6s는 **3 threads/arm 실측**, registered 4,939.884s는 **2 threads/arm 실측**; 둘 다 F0 측정이 아니다"로 정정.
3. D1 25 min이 2 threads/arm 기준임을 명시하고, 3→2 thread 전환의 예상 감속을 `contention_ratio`로 기록하도록 §12에 한 줄 추가.

---

## 5. Q4 — R mechanics / scope

**판정: disagree.**

### 5.1 `r_mechanics_pass`의 predicate가 없다

§13A.10 (lines 564–576)는 다음을 정의한다:

```text
seeds:3
cells:4
updates_total:900
m_records:1440
phase7_records:7200
real_memory_ce_calls:int
wrong_donor_ce_calls:int
donor_map_loads:int
provenance_ok:bool
r_mechanics_pass:bool
```

비교하라: `mechanics_pass`는 §13A.4 (line 499)에서 13개 항의 완전한 boolean 식으로 정의되고, `pre_r_init_audit_pass`는 §13A.10 (line 548)에서 정의된다. **`r_mechanics_pass`만 정의가 없다.** `real_memory_ce_calls`/`wrong_donor_ce_calls`/`donor_map_loads`는 expected 값도 `_ok` boolean도 없이 정수로만 기록된다. 즉 v1.8 must-fix #6("add counts or explicit N/A")을 **문자 그대로만** 충족했고, 게이트로 만들지는 않았다.

구체적으로 미정의인 것:

- R의 `real_memory_ce_calls` expected 값. 20 docs × 5 donors × 7 evals × 3 seeds = **2,100**(eval만), M real CE 4×3×60 = 720 포함 시 **2,820**. 문서에 없다.
- R의 `wrong_donor_ce_calls`는 **0이면 안 된다**(R이 signal을 계산하므로). expected가 없으므로 0과 구분되지 않는다.
- R의 `donor_map_loads`는 F0 전 cell이 EG2 cache를 쓰므로 `donors_for(val20, cache)`만 호출되고 persisted donor-map 로드는 0이어야 하는데, 이를 요구하는 문장이 없다.

### 5.2 scope 경계는 정직하다

§14 (lines 587–591)는 association-only, ROUTE_STOP의 route-only 한정, descriptive contrast, lost controls(MF-4 zero/permuted null, 1-seed gate) 미대체를 명시한다. Phase 6 cause report §9의 MF-3 correction(adapter bottleneck을 native 경로 관찰로 한정)과 정합한다. **agree.**

### 5.3 다음 단계

1. §13A.10에 `r_mechanics_pass`의 완전한 boolean 식을 추가하고, `real_memory_ce_calls_ok`/`wrong_donor_ce_calls_ok`/`donor_map_loads_ok`를 `mechanics_pass`와 같은 형태로 정의.
2. R expected 정수를 prereg에 literal로 고정(2,100 또는 2,820).
3. `wrong_donor_ce_calls > 0`을 R pass 조건에 명시(0이면 signal 미계산).

---

## 6. Q5 — compute 8 threads / affinity

**판정: conditional.**

### 6.1 정합하는 부분

- §12 (lines 369–373): P/Q/D1/R 모두 `2/arm, 4 arms = 8 logical`. D0만 `1/arm`.
- §5 D1 (line 38): "4 parallel arm processes × 2 threads/arm (16-core host)".
- §13A.7 (line 520): `nproc>=16` 필수, 4-vCPU workspace 비해당.
- §12 (line 382): `nproc < 16` 또는 `T_proj_R > 96 min`에서 hard abort.
- 900 updates = 3 seeds × 3 trained cells × 100 (§5 line 68) — 산술 정확.
- 96 min vs Phase 6 registered 4,939.884s(82.3 min, 1,200 updates) — F0는 300 updates 적으므로 여유 있음. **agree.**

### 6.2 남는 문제

**(a) D1 anchor thread 불일치** — §4.3 참조. D-156은 3 threads/arm, 계획은 2 threads/arm이라 적었다.

**(b) Phase 6 실측을 "estimates"로 오기** — §12 line 375. D-156/D-157은 `cap_ok:true`로 기록된 실측이다. "F0 측정이 아니다"가 의도라면 그렇게 써야 한다.

**(c) 8 logical threads의 근거 부재** — 16 core에서 8 threads만 쓰는 이유(메모리 대역폭, mT5-small decoder 병목 등)가 없다. D0는 1/arm인데 D1은 2/arm인 것도 설명이 없다. blocker는 아니나 `contention_ratio`(line 381)가 이 선택을 사후 정당화하는 유일한 장치이므로, 4/arm 대비 2/arm을 택한 이유를 한 줄 남겨야 한다.

### 6.3 다음 단계

1. §12 line 375 정정(§4.3).
2. 2 threads/arm 선택 근거와 D0 1/arm과의 차이를 §12에 명시.

---

## 7. Q6 — near-threshold / scope

**판정: conditional.**

### 7.1 v1.8의 조작적 정의가 삭제됐다

v1.8 §7 (line 307)은 다음을 정의했다:

```text
boundary b∈{.05,0}, h=(CI.upper-CI.lower)/2, near if |mean-b|<=h
```

v1.9 §7 (line 307)는 이를 다음 산문으로 교체했다:

```text
Near-threshold diagnostic: separate mean margin, CI-lower margin, and seed-sign margin
for each cell-level SIGNAL; diagnostics are non-decisional and do not alter gates.
```

"margin"이 무엇인지, "near"의 임계가 무엇인지, 세 margin을 어떻게 보고하는지가 모두 미정의다. 진단이 non-decisional이므로 **blocker는 아니지만**, 미정의 진단은 사후 해석의 여지를 남긴다 — 정확히 v1.8이 막으려던 것이다. v1.8의 b/h 정의를 복원하고 세 margin을 그 위에 얹는 것이 옳다.

### 7.2 EQUIVALENT 도달가능성이 SE 선택에 전적으로 의존한다

§6.5 (line 251): `EQUIVALENT iff 95% CI_D entirely within [-.05, +.05]`. 도달 조건은 `1.96×SE_D ≤ .05`, 즉 `SE_D ≤ .0255`다.

- F−L proxy SE `.019170` (line 383) → 도달 가능.
- P−PA reference SE `.6209` (line 383) → **도달 불가**(1.96×.6209 = 1.22 ≫ .05).

계획은 두 SE를 나란히 제시하면서(line 383) 어느 것이 E01−E11에 적용되는지 결정하지 않는다. §6.5 (line 256)는 "expected branch is undetermined; PASS and ROUTE_STOP are both live"라고만 쓴다. 실제로는 **EQUIVALENT의 도달가능성이 F−L 규모 SE를 가정할 때만 성립**하며, P−PA 규모라면 EQUIVALENT는 장식적 상태가 된다. 이 조건을 명시해야 한다.

### 7.3 MDE 산술은 맞지만 proxy 선택이 낙관적이다

- `.037573/1.96 = .019170` ✓
- 50% MDE `.0376` ✓, 80% MDE `2.802×.01917 = .0537` ✓
- 그러나 이 SE는 **F−L LoRA 대조**의 것이고, estimand는 **E01−E11 adapter 대조**다. 계획 스스로 "not a validated E01−E11 SE"라 인정한다(line 383). P−PA SE `.6209`로 계산하면 80% MDE는 **1.74**로, `.0537`의 32배다. 큰 adapter 효과(Phase 6에서 3.08→0.01)를 탐지하는 데는 충분하지만, "MDE .0537"을 인용해 소효과 탐지력을 주장하면 안 된다. §12에 두 SE의 불일치와 그 함의를 한 문장으로 명시할 것.

### 7.4 scope는 적절

§10 (lines 345–349) H3 완전 제거, §14 (line 588) ROUTE_STOP route-only, §14 (line 590) lost controls 미대체 선언 — Phase 6 results synthesis MF-4/MF-5와 정합. **agree.**

### 7.5 다음 단계

1. v1.8의 b/h near-threshold 정의를 복원하고 세 margin을 그 위에 정의.
2. §6.5에 "EQUIVALENT는 `SE_D ≤ .0255`일 때만 도달 가능"을 명시하고, F−L proxy와 P−PA reference 중 어느 것이 E01−E11에 적용되는지 결정.
3. §12에 두 SE의 32배 불일치와 MDE 해석 한계를 명시.

---

## 8. Ranked must-fix

| rank | severity | must-fix | 위치 |
|---:|---|---|---|
| 1 | **blocker** | `expected_real_memory_ce_calls`를 prereg에 **정수 literal**로 고정(700 또는 940, M real CE 포함 여부 결정). "committed call graph에서 유도"는 tautology이므로 literal 대조로 교체. | §13A.4 line 498; §5 D1 lines 44–45 |
| 2 | **blocker** | `donor_map_loads:0`과 "counted op = real_memory_ce per doc×donor"의 모순 해소. D1이 donor를 resolve하면 `donor_map_loads`는 0이 아니고, resolve하지 않으면 카운트는 per-doc(140)이다. | §13A.4 lines 489, 498 |
| 3 | **blocker** | `p_r_hash_equal`의 순환 제거. P 산출물에서 빼서 `r_mechanics_pass.json`으로 옮기거나, "P hash == committed builder 재계산 hash"로 재정의. | §13A.10 lines 544, 548; §13A.6 line 516 |
| 4 | **blocker** | `r_mechanics_pass`의 완전한 boolean predicate 정의 + R expected 정수(2,100 또는 2,820) + `wrong_donor_ce_calls > 0` 조건. | §13A.10 lines 564–576 |
| 5 | high | §5 D1 line 60을 "signal delta values are never materialized; M/generation **records** are computed in memory and only their **counts** are persisted"로 정정. | §5 D1 line 60 vs §13A.4 lines 482, 484 |
| 6 | high | §12 line 375 정정: Phase 6 D1 1,180.6s는 **3 threads/arm 실측**(D-156), registered 4,939.884s는 **2 threads/arm 실측**(D-157); 둘 다 F0 측정이 아니다. D1 25 min이 2 threads/arm 기준임을 명시. | §12 line 375; `docs/decisions.md:216,218` |
| 7 | high | 리뷰 요청 Q1–Q6와 계획 §15 Q1–Q6의 불일치 해소(계획 §15를 CE/schema/materialization/R/compute/near-threshold로 재작성하거나, 리뷰 요청에 계획 §15 번호를 명시). | §15 lines 595–617 vs review request §3 |
| 8 | medium | v1.8의 near-threshold 조작적 정의(b∈{.05,0}, h=(CI.upper−CI.lower)/2, near if \|mean−b\|≤h) 복원 + 세 margin 정의. | §7 line 307 |
| 9 | medium | §6.5에 EQUIVALENT 도달 조건 `SE_D ≤ .0255` 명시, F−L proxy vs P−PA reference 중 적용 SE 결정. | §6.5 lines 251–256; §12 line 383 |
| 10 | medium | §13A.8 line 528 "first exercised at R"을 "Q exercises wrong-donor CE for finiteness/shape only; R is the first stage that persists or aggregates it"로 정정. | §13A.8 line 528 vs §13A.10 line 557 |
| 11 | low | §12에 2 threads/arm 선택 근거와 D0 1/arm과의 차이를 한 줄 명시. | §12 lines 369–373 |

---

## 9. 잘못된 전제

1. **"expected count를 committed call graph에서 유도하면 seal이 강해진다"** — 반대다. expected와 actual이 같은 코드에서 나오면 비교는 결정성 검사일 뿐이고, evaluator가 틀린 연산을 세도 통과한다. v1.8의 "틀린 산식" 결함이 "검출 불가능한 산식"으로 바뀌었다. (§13A.4 line 498)
2. **"D1은 donor map을 로드하지 않는다"** — D1이 doc×donor 단위 real CE를 계산한다면 donor 신원 resolve가 필요하다. `donor_map_loads:0`과 `per doc×donor`는 동시에 참일 수 없다. (§13A.4 lines 489, 498)
3. **"P 단계에서 `p_r_hash_equal`을 판정할 수 있다"** — R은 P 이후에 실행된다. P 산출물에 R 해시를 요구하는 필드를 넣으면 게이트가 순환한다. (§13A.10 lines 544, 548)
4. **"M/generation counts는 persist되지 않는다"** — `m_records`와 `generation_records`는 §13A.4의 파일 키다. persist되지 않는 것은 record 배열이다. (§5 D1 line 60)
5. **"Phase 6 D1/registered wall은 estimates다"** — D-156/D-157은 `cap_ok:true`로 기록된 실측이다. F0 측정이 아니라는 뜻이어야 한다. (§12 line 375)
6. **"wrong-donor CE 수치 경로는 R에서 처음 실행된다"** — Q가 `wrong_donor_finite`를 판정하므로 Q에서 실행된다. (§13A.8 line 528 vs §13A.10 line 557)
7. **"MDE .0537이 E01−E11의 80% MDE다"** — .0537은 F−L LoRA 대조 SE에서 나온 값이다. P−PA reference SE .6209로는 80% MDE가 1.74다. (§12 line 383)

---

## 10. 최종 판정

```text
최종 판정: NARROW

Init:      v1.9 §4 init contract는 v1.8 대비 변경 없음; step_seed golden table 재계산 일치
           (20261108 → 0x9f02514d/0x3d5bdb86/0xdb9345df; 20261109/10/11 → 0x9f02514c/4f/4e,
           0x3d5bdb87/84/85, 0xdb9345de/dd/dc). 이 항목은 승인 가능.
D1:        NARROW — expected CE count literal 부재 + tautological 유도 + donor_map_loads 모순
           (must-fix 1, 2). materialization 문장 오기(must-fix 5).
STOP/MDE:  taxonomy는 상호배타·전체포괄 유지(§7 lines 296–316). MDE 산술은 정확하나
           proxy 선택이 낙관적이고 EQUIVALENT 도달 조건 미명시(must-fix 9).
Cohort:    15 common frozen, doc 3/3, n_donors=5, n_boot=10000 — v1.8과 동일, 승인 가능.
Compute:   8 logical threads / 900 updates / 96 min 정합. D1 anchor thread 오기와
           "estimates" 오기 정정 필요(must-fix 6).
Scope:     H3 제거, ROUTE_STOP route-only, lost controls 미대체 — 승인 가능.

Must-fix (ranked): 1–11 (§8)
잘못된 전제: 1–7 (§9)
```

**승인 차단 사유(결정적):** must-fix 1–4. 이 넷은 모두 "게이트가 실제로 판정하지 못하는" 결함이다 — expected CE count는 코드에 위임되어 검증 불가하고, `donor_map_loads:0`은 카운트 정의와 모순이며, `p_r_hash_equal`은 R 이전에 판정될 수 없고, `r_mechanics_pass`는 predicate 자체가 없다. 이 상태로 D1/R을 승인하면 seal과 mechanics gate가 형식만 남는다.

**승인 가능한 부분:** init contract(§4), cohort/CI(§6.1, §6.4), STOP taxonomy(§7), scope 경계(§10, §14), provenance 선행 조건(§11 line 360), H3 제거. v1.8 대비 실질 개선이며, must-fix 1–4를 반영하면 CONTINUE로 전환 가능한 거리에 있다.

**다음 단계:** must-fix 1–4를 v1.10에 반영하고, 5–11을 함께 정정한 뒤 새 라운드에서 재검토. D0/D1/R 실행 승인은 그 이후.

```text
F0 v1.9 = NARROW (DS1017)
F0 = 미승인, 미실행
Phase 6 = negative 종료 불변
B0-B = 미승인
test 163 = sealed; P1 = unused; T5Gemma2 = D-108 STOP
```