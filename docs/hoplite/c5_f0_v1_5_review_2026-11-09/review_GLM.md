# C5 F0 v1.5 — Independent Review (GLM, Round 5/10)

- 작성일: 2026-11-10
- 모델: `z-ai/glm-5.3-flash` (새 독립 스레드, v1.4 스레드结论 미상속)
- 대상: `docs/plan_c5_f0_v1_5_2026-11-09.md`
- 성격: consultation only — 이 파일 외 저장소 변경 없음, 학습/평가/test163/P1/subagent 없음
- **reviewed HEAD: `79b5dc772817d68026b7548507d0d6e87927b30e`** ("docs: add C5 F0 v1.5 review request", 2026-11-10 10:41:02 +0900)
- 동기화: `git fetch origin` → `git pull --ff-only origin main` → **Already up to date** (오류 없음)

## 0. Verbatim paired E01−E11 (대상 문서 그대로 인용)

§6.2 Cell delta:

```text
delta_c(s,d) = mean_donor( CE_wrong_donor - CE_real )
```

- copy and full separately.
- per-doc seed average: `delta_c(d) = mean_s delta_c(s,d)`.

§6.3 Primary contrast:

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

- Primary positive: `mean_D > 0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0`.

## 1. 독립 재검증 (v1.4 결론 미상속, 새 블록)

이 스레드에서 직접 계산/확인한 결과:

1. **step_seed golden table 재계산 일치 (12/12).** `(seed ^ ((0x9E3779B9*(step+1)) & 0xffffffff)) & 0xffffffff`로 직접 계산: 20261108 → `0x9f02514d/0x3d5bdb86/0xdb9345df`, 20261109 → `0x9f02514c/0x3d5bdb87/0xdb9345de`, 20261110 → `0x9f02514f/0x3d5bdb84/0xdb9345dd`, 20261111 → `0x9f02514e/0x3d5bdb85/0xdb9345dc`. 문서 §4 표와 전부 일치. 괄호 고정형이 기준임이 확인됨.
2. **MDE 산술 재계산 일치.** `0.037573/1.96 = 0.0191700`(SE) ✓, `1.96×SE = 0.037573`(50% MDE .0376) ✓, `(1.96+0.8416)×SE = 0.05371`(80% MDE .0537) ✓, `.05+.0376 = .0876`(50% boundary) ✓, `.05+.0537 = .1037 ≈ .104`(gate mean) ✓. 즉 `.104`/`.0876`는 "실현된 CI half-width가 각각 80%/50% MDE와 같을 때 `CI_D.lower>.05`를 넘는 mean_D 수준"으로 라벨링하면 자기정합.
3. **출처 확인.** `reports/provenance/C5_b0a/labels/labels.json` `L_COPY_SIGNAL.paired`: mean −0.002639, CI [−0.040845, +0.034302], n=15, n_boot=1000, seed=20261109, ci_method=linear → half-width (0.034302+0.040845)/2 = **0.037573** ✓. `L_COPY_SIGNAL.delta.mean = −0.113506`, `seeds_positive=0` ✓ cause report §1과 일치.
4. **통계 모듈 확인.** `runner/c5_pm_stats.py`: `N_BOOT=1000`, `bootstrap_paired_v2(values, n_boot=N_BOOT, seed=20261109)` — 입력은 "seed 평균 후 per-document 값", 문서 단위 재샘플링, PCG64, `np.percentile(..., method="linear")`. (a) 단일 배열 1-D 입력 → §6.4 cell-level CI(15개 doc 값) 그대로 호출 가능, (b) 반환 dict에 `n_boot`/`seed` 실현값 포함 → §6.3의 realized assertion 구현 가능, (c) `n_boot`/`seed`가 시그니처 파라미터 → 10000 명시 override 가능. `runner/c5_pm_labels.py:54-63`의 `l_predicate`는 n_boot=1000 하드코딩 → v1.5의 `l_predicate` 금지 조항이 실재하는 위험을 정확히 겨냥함 ✓.
5. **eval_arm_d1 확인.** `runner/c5_pm_phase6.py:429` — `if not real_copy: continue`로 non-copyable doc을 **조용히 탈락**시키고 per-doc `delta_shuffled_*`를 materialize함. v1.5의 (a) "missing doc = NOT_EVALUABLE, 축소 cohort 금지"(§6.1), (b) D1 전용 mechanics evaluator(§11, `eval_arm_d1` 미재사용) 근거가 실제 코드로 확인됨 ✓.
6. **donors_for 확인.** `runner/c5_mt5_lora_b0.py:318` — 길이 최근접 결정적 할당, "same for all arms/seeds" → all-cell donor set equality(§6.1)는 구조적으로 성립 ✓. `copy_ce`는 copy token <5면 None → 탈락 경로 실재.
7. **Compute 근거 확인.** decisions.md D-156: Phase 6 D1 병렬 wall **1,180.6s / 1,200s cap**, 4 arms × 3 threads ✓. registered wall **4,939.884s**는 `reports/provenance/C5_b0a/registered/registered_report.json` `wall_estimate_s=4939.884017705917` 및 `C5_B0A_PM_PHASE6_REGISTERED_2026-11-09.md`("4,939.9s / 7,200s = 82.3/120 min")로 provenance 확보 ✓. Phase 6 prereg §11.5의 9개 term이 v1.5 §12와 정확히 일치 ✓. 1.316 multiplier 제거는 v0.4 당시 6,500s 추정의 근거 없는 팽창을 제거한 것으로 올바른 방향.
8. **기타.** `arm_spec`(c5_pm_phase6.py:125)은 F/L/P/PA만 지원 → 신규 runner 근거 ✓. `attach_decoder_lora_mt5`(c5_mt5_lora_b0.py:52)는 `named_modules` 결정적 순회 + 64개 count assert ✓. `L_COPY_SIGNAL`/`L_FULL_SIGNAL` threshold(.05/0)와 v1.5 §6.4의 copy/full threshold 관례 일치 ✓. val 20 중 15 length-eligible(`n_signal: 15`) ✓.

## 2. Q1 — Stage P / init / step_seed

- 판정: **conditional agree**
- 근거:
  - P init-only(assertions 1–4, 6–8; 5/9·13A.3 제외)는 §4 번호 체계와 정확히 일치(5=post_step0 RNG, 9=weight change). post-step0/weight-change를 D1 seed 20261111로 한정하는 것은 P가 update 없이 init 동등성만 보는 설계와 일관 ✓.
  - `LORA_SEED_XOR` 항상 재시드(adapter-independent)로 E01/E11 LoRA 해시 동등성이 구조적 ✓. per-step reseed로 dropout RNG가 "assumed가 아닌 structural" ✓. golden table 12/12 재계산 일치(§1.1).
  - assertion 6(lora_B zero 별도 assert)은 "A 해시 동등 = 전부 동일" 오독을 차단 ✓.
- 다음 단계:
  1. **P/D0 budget 중의 제거**(must-fix 5): "P ≤10 min inside D0 budget"(13A.1)과 D0 cap "≤15 min provisional"(§5)의 관계(포함 vs 가산)를 명시. 포함이면 D0 본체 5분, 가산이면 25분 — 어느 쪽인지 §5 또는 §12에 한 줄로 고정.
  2. **d0 vs r init hash 교차 일치**(must-fix 2): P는 D0 시점에 실행되고 R은 재빌드함. `r/init_hashes.json` canonical digest가 `d0/init_hashes.json`(R seeds)과 seed별로 동일함을 pre-R gate에서 assert하거나, R 진입 시 audit 재실행. 없으면 P의 증거가 R 빌드에 대해 stale.

## 3. Q2 — D1 full schema / signal path / seal

- 판정: **conditional agree — blocker 1건**
- 근거:
  - 설계 방향이 정확함: D1에서 signal 값을 **materialize하지 않음**(seal보다 강함), exact-key allowlist + denylist, digest-only checkpoint + 삭제 + `checkpoint_absent` assert, gate/driver negative test, writer/consumer allowlist, crash path `partial:true` + checkpoint 삭제. v1.0 DS-1의 세 모순("checkpoint 존재 vs 금지", "only output vs M/generation", `eval_arm_d1` materialize)이 모두 해소됨 ✓.
  - signal path: dry run 선택(13A.8) + `donors_for`/crop 1-doc unit test, 값 미저장 ✓. `wrong_donor_ce_calls==0` + `donor_map_loads==0`이 donor-free D1 eval을 행위적으로 강제 ✓.
  - schema에 §5 D1 assertion 4의 "scalar counts, not objects"가 반영됨(`n_docs_step0:int` 등) ✓.
- **Blocker — mechanics_pass 술어가 값 수준 검증을 누락** (must-fix 1):
  - 13A.4의 `mechanics_pass = partial==false AND error==null AND checkpoint_absent==true AND all assertions==true AND phase7_records==0 AND wrong_donor_ce_calls==0 AND donor_map_loads==0`.
  - 그러나 §5 D1 assertions 1–4·10에 해당하는 값 검증이 assertions object에도 술어에도 없음: cells key set == {E00,E10,E01,E11}, `cells.E00.updates==0`, E10/E01/E11 `updates==1`, **`updates_total==3`(스키마 필드 자체가 없음 — §5 D1 assertion 2가 요구)**, cell별 `n_docs_step0==n_docs_final==20`, `m_records==120`(합 480), `generation_records==20`(합 80), `labels_computed==false`, `not_a_result==true`, `test_split_used==false`, `p1_used==false`, `d1_signal_read==false`, trained cells의 `checkpoint_digests` non-null.
  - 결과: 스키마-valid이지만 §5 위반 파일(예: E10 updates=5, n_docs=18, flags true)이 `mechanics_pass:true`로 R을 개시할 수 있음. D1 gate의 존재 이유가 무너지는 경로이므로 승인 blocker.
- 다음 단계:
  1. must-fix 1 반영(술어 확장 + `updates_total` 필드 추가).
  2. §5 D1에 "step0/final eval은 real-memory CE만, donor loop 없음"을 명시(현재는 카운터로만 암시) (must-fix 6).
  3. E00 D1 eval 장부 명시(§9 "E00 step0 = final; one signal eval" vs n_docs_step0/final 각 20 요구 — 단일 eval이 두 필드에 how 매핑되는지) (must-fix 3).
  4. 잔여 우로 경로 기록: file allowlist는 **stdout/log에 출력되는 CE 수치**는 못 막음. 수용 가능한 residual이지만 13A.4에 "accepted residual: process logs"로 명기하거나 log numeric-scrub assert 추가.

## 4. Q3 — STOP / MDE labels

- 판정: **agree**
- 근거:
  - 4-state 표는 우선순위 평가 순서(NOT_EVALUABLE → PASS → ROUTE_STOP → INDETERMINATE)로 상호배타·전체포괄 ✓. `EQUIVALENT`는 state가 아니라 ROUTE_STOP reason/harm/benefit의修飾자이므로 "PASS lower>.05 vs EQUIVALENT" 겹침 자체가 성립하지 않음. 또한 `lower>+.05`이면 `upper≥lower>.05` → ¬EQUIVALENT이므로 PASS와 EQUIVALE밴드는 논리적으로 배타 ✓.
  - harm = `lower>0 ∧ ¬EQUIVALENT` ⟺ CI 전체가 양수이고 upper>.05; benefit = `upper<0 ∧ ¬EQUIVALENT` ⟺ CI 전체가 음수이고 lower<−.05. `EQUIVALENT>harm>benefit` reason 선행순위와 ALL_FAIL 4종 reason 매핑(no_signal_equivalent/adapter_harm/adapter_benefit/no_signal_uncertain)은 타당하며, benefit=adapter_benefit 네이밍 semantics(D<0 = adapter가 기여) 정확 ✓.
  - PASS에 cell signal + seed gate가 conjunct로 요구되어 "paired contrast만 큰" 오표본 경로가 차단됨 ✓.
  - MDE 라벨 5개 모두 재계산 일치(§1.2), 출처(labels.json paired) 확인(§1.3), "not a validated E01−E11 SE / none is an observed F0 mean" 한정 유지 ✓. EQUIVALENT 도달 가능성이 실현 분산에 좌우되는 점은 INDETERMINATE가 흡수 — 설계 변경 불요.
- 다음 단계: `.104`/`.0876`의 의미(위 문장)를 §12에 각주 1줄로 고정(현재는 수식 나열이라 오독 여지).

## 5. Q4 — Cohort / cell CI / donor conditional

- 판정: **agree**
- 근거:
  - 15 common = frozen preflight binding, 20-doc은 descriptive only + 일반화 금지(§6.1) → v1.0 DS-2(length-selected cohort)의 처방 그대로 ✓.
  - doc 3/3 seed 필수, missing = NA, 15→14 대체 금지, `<15 or <3 seeds → NOT_EVALUABLE`(§6.6) → `eval_arm_d1`의 silent drop(§1.5 확인)에 대한 정확한 방어 ✓.
  - n_donors=5 + all-cell equality는 `donors_for`의 결정적 구현으로 구조적 성립(§1.6) + `evaluated_donors==5` abort(13A.5) 이중 방어 ✓. leave-one-donor-out은 descriptive로 한정 ✓.
  - cell CI: seed-mean(3 seeds) 후 15-doc bootstrap — `bootstrap_paired_v2`의 문서화된 입력 규약("per-document value after any seed averaging")과 정확히 일치(§1.4) ✓. `n_boot=10000, seed=20261109, percentile linear` + realized assert + `ALL_FAIL`/`ROUTE_STOP`의 frozen CI 소비(재-bootstrap 금지) ✓.
  - CI_D donor-graph conditional 명시 + population inference 금지 ✓.
- 다음 단계: 없음 (심각한 gap 발견 안 됨). 참고로 CI_D와 4개 cell CI가 같은 seed 20261109를 쓰지만 호출마다 fresh PCG64라 결합 없음 — 기록 수준으로 충분.

## 6. Q5 — Compute / nproc / setup / T_proj

- 판정: **agree**
- 근거:
  - D1 cap 25 min vs D-156 1,180.6s(≈19.7 min) — 그리고 F0 D1은 Phase 6 D1보다 **적게** 일함(phase7 0, donor eval 없음) → cap 여유는 안전 방향 ✓.
  - R cap 96 min vs wall anchor 4,939.884s(82.3 min, provenance §1.7) → ~17% margin. F0 진단 부하(480 M + 7,200 phase7/12 units) ≤ Phase 6(560 + 7,200) → anchor 타당 ✓. 900 updates = 3 trained cells × 100 × 3 seeds ✓.
  - 9 terms = prereg §11.5와 정확히 동일, slowest-arm 집계는 DS-7(Phase 6 T_proj의 전-arm 합산 호환성) 해소 ✓. `setup_s_effective` = 3 waves × 4 processes 총합, amortization 금지 ✓. `contention_ratio` 기록 + 측정 기반 cap ✓.
  - `nproc>=16 or threads_per_arm<=1` + hard abort, 12-thread no-headroom 제거, 4-vCPU workspace no-run(13A.7) ✓. 12 logical threads + overhead에 16 logical CPU 요구는 합리적 headroom.
  - F0 orchestrator/runner 사전 commit + code_commit/command/input SHA(§11) → v1.0 DS-4/MF-1 provenance blocker 반영 ✓.
- 다음 단계: §12 표에 P 행(또는 각주) 추가 — P가 D0 행에 흡수된 것이 표상으로는 보이지 않음 (must-fix 5와 동일 수정).

## 7. Q6 — Scope / route-only

- 판정: **agree**
- 근거:
  - Primary E01−E11은 MF-4가 요구한 clean contrast("F0 vs L, LoRA 고정, adapter만 차이")의 정확한 구현이며, LoRA init matched로 "capacity/LR 동시 변경" confound 중 LoRA 쪽은 제거됨. adapter 쪽(params + lr 1e-3)은 `adapter-as-configured`(§4 마지막 문장)로 선언 — association-only 한계와 정합 ✓.
  - E00 = 0-update EG2-raw usability probe(v1.0 GLM 제안) 흡수 ✓. E10/E11 및 E00 대비 contrast는 전부 descriptive로 강등 ✓.
  - H3 완전 제거 + "F0 결과가 H3를 자동 개시하지 않음" + INDETERMINATE에서도 "no automatic H3; new prereg required" ✓. ROUTE_STOP consequence가 route-as-configured로 한정됨(§8/§14) ✓.
  - lost controls(MF-4의 zero/permuted null, donor-discrimination probe, 1-seed gate)를 §14에서 의도적 제외로 선언 — F0가 이들을 대체한다는 주장 차단 ✓. 잔여 한계(E01−E11 negative가 EG2 content 부족과 decoder 정렬 부재를 구분 못 함)는 이미 선언된 진단 범위로 수용 가능.
- 다음 단계: 없음.

## 8. 최종 판정

```text
최종 판정: CONTINUE
Init:      conditional agree — P/D0 cap 중의성, d0↔r init hash 교차 assert 필요
D1:        conditional agree — mechanics_pass 술어 불완전 = 승인 blocker 1건
STOP/MDE:  agree — 4-state 배타·포괄, MDE 라벨 5개 산술·출처 검증 일치
Cohort:    agree — frozen 15, 3/3, donors_for 구조적 동등성, n_boot override 검증
Compute:   agree — D-156/4,939.884s provenance 확인, nproc≥16, setup explicit
Scope:     agree — MF-4 clean contrast 구현, H3/non-goal 경계 명확
```

## 9. Must-fix (ranked)

1. **(blocker, D0 stage approval 전 필수)** 13A.4: `updates_total:int` 필드 추가 + `mechanics_pass` 술어를 §5 D1 assertions 1–4·10 전체를 검증하도록 확장(cells key set, E00.updates==0, trained updates==1/total 3, n_docs 20/20, m_records 120/480, generation 20/80, flags 5종, trained checkpoint_digests non-null). 현재 술어로는 §5-위반 파일이 gate를 통과함.
2. **(high)** `r/init_hashes.json` canonical digest == `d0/init_hashes.json` (R seeds) 교차 일치 assert를 pre-R gate에 추가, 또는 R 진입 시 P audit 재실행. P가 D0 시점 실행이므로 무교차 시 R 빌드 drift 미검출.
3. **(medium)** E00 D1 eval 장부 명시: 단일 eval이 `n_docs_step0`/`n_docs_final` 두 필드에 어떻게 기록되는지(또는 E00도 두 번 eval) 정의.
4. **(medium)** §5 R의 `phase7 7,200`은 E00이 seed당 600 records를 생산할 때만 성립 — E00 phase7 생산 여부를 명시(없으면 5,400으로 assertion 설계 불일치).
5. **(low)** P ≤10 min과 D0 ≤15 min provisional의 관계(포함/가산) 명시 + §12 표에 P 표기.
6. **(low)** §5 D1에 "step0/final eval = real-memory CE only, donor loop 없음" 명시(카운터 강제만으로는 불명시).
7. **(note, 수정 선택)** residual: process stdout/log의 CE 수치는 file allowlist로 차단 불가 — accepted residual로 기록 또는 log assert.

## 10. 잘못된 전제

없음. 검증 대상 수치 전부(step_seed 12 vectors, SE .019170, 50% .0376, 80% .0537, gate mean .104, 50% boundary .0876, D-156 1,180.6s, wall 4,939.884s, paired half-width .037573)를 저장소 artifact와 독립 재계산으로 확인했고 불일치 0건. 부가 확인: v1.4의 무괄호 step_seed 식은 Python/C 연산자 우선순위(& > ^)에서 우연히 동일 값이었으나, v1.5의 괄호 고정은 올바른 문서화이며 golden table은 고정형과 일치함을 확인함.

## 11. 판정 의미

**CONTINUE** = 설계 원칙 승인. 단, must-fix 1은 **F0 구현 commit 및 D0 stage approval 이전에** plan에 반영되어야 하는 승인 blocker이며, must-fix 2–6은 동일 패치(v1.6 editorial)로 흡수 후 D0 gate에서 확인 가능. 이 범위의 기계적 패치에 대해 별도 전체 재검토 라운드는 불요 — 다음 라운드는 v1.6 패치 diff가 must-fix 1–6에 한정될 때 본 리뷰를 조건부 승인으로 취급할 수 있음. 승인 전 실행·test 163/P1 사용·임계값 변경은 여전히 금지.