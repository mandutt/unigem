# C5 F0 v1.6 — Independent Review (DS1017)

- 검토일: 2026-11-10
- 검토 대상: `docs/plan_c5_f0_v1_6_2026-11-09.md` (DRAFT v1.6, 미승인·미실행)
- **reviewed HEAD: `1b6e4c52932a557e4f47484b456bb55cbdf91b12`**
  - `git fetch origin` → 성공, `git pull --ff-only origin main` → `Already up to date.`
  - HEAD subject: `docs: add C5 F0 v1.6 review request`
- 새 10-round block의 round 6. v1.5 결론 상속 없음. 이전 스레드 미사용.
- 읽은 파일: `reports/EXTERNAL_REVIEW_C5_F0_V1_6_2026-11-09.md`, `docs/plan_c5_f0_v1_6_2026-11-09.md`, `docs/plan_c5_f0_v1_5_2026-11-09.md`, `reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py`, `runner/c5_pm_stats.py`, `reports/C5_B0A_PM_PHASE6_REGISTERED_2026-11-09.md`, `reports/C5_B0A_PM_PHASE6_D1_2026-11-09.md`.
- 추가 학습/평가 없음. test 163/P1 미사용. subagent 미사용. 이 파일 외 수정 없음.

---

## 0. Verbatim paired E01−E11 (reviewed artifact)

§2 Cells (lines 60–63):

```text
| E01 (F0) | EG2 raw | none | 64 modules | 100 | adapter-free + LoRA |
| E11 (L) | EG2 raw | trained | 64 modules | 100 | adapter + LoRA |
```

§2 (line 63):

```text
- Primary: **E01 vs E11** (LoRA initialization matched).
```

§4 (lines 97–98):

```text
- E01/E11 call the LoRA seed reset identically.
- E10/E11 call the adapter seed identically.
```

§6.3 (lines 216–221):

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

§6.3 (line 226):

```text
- `D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary.
```

---

## 1. Q1 — Wrong-donor / P / Q / init hashes

**판정: conditional**

**근거**

1. v1.5의 wrong-donor 모순은 실제로 닫혔다. §0-1 (lines 19–21)이 “D1은 wrong-donor CE를 호출하지 않음; `wrong_donor_ce_calls:0` absolute”로 통일되었고, §13A.8 (lines 515–517)과 일치한다. §13A.4 schema의 `wrong_donor_ce_calls: int (must 0)` (line 480)와 `mechanics_pass` 조건 (line 489)도 같은 방향이다. 이전 라운드의 “D1 dry run vs R-first” 이중 서술은 제거되었다.
2. Init 계약은 강하다. `build_arm_f0` (lines 84–93)가 adapter 유무와 무관하게 `torch.manual_seed(seed ^ 0x5EED10A5)`를 호출하므로 E01/E11 LoRA init이 구조적으로 같고, per-step reseed (line 99)로 dropout RNG도 같다. Assertion 1–9 (lines 100–109)가 names/hash/RNG/base/cache/labels/weight-change를 모두 덮는다.
3. **step_seed golden table을 직접 재계산해 검증했다.** `(seed ^ ((0x9E3779B9*(step+1)) & 0xffffffff)) & 0xffffffff`로 20261108 → `0x9f02514d/0x3d5bdb86/0xdb9345df`, 20261109 → `0x9f02514c/0x3d5bdb87/0xdb9345de`, 20261110 → `0x9f02514f/0x3d5bdb84/0xdb9345dd`, 20261111 → `0x9f02514e/0x3d5bdb85/0xdb9345dc`. §4 line 111의 표와 **완전히 일치**한다. 산술 오류 없음.
4. 그러나 **primary signal path가 R 전에 한 번도 실행되지 않는다.** §13A.8 (line 516)이 “Primary wrong-donor CE path is first exercised at R; explicitly accepted”라고 명시하고, mitigation은 “unit-test `donors_for`/crop on 1 doc before D1; no values persisted” (line 517)뿐이며 **gate가 아니다**. §5 D1 assertion 8 “all CE finite” (line 155)는 이제 real/M CE만 덮으므로 primary CE의 finiteness를 보증하지 않는다. R은 “No retry/extension” (line 382)이므로 donor-crop/wrong-donor 경로의 버그는 96분 R 전체를 낭비시킨다. 이는 v1.5가 택했던 non-persisting dry run보다 후퇴다.
5. **Q의 update 수가 틀렸다.** §12 table Q row는 “trained updates 12” (line 369)이지만, Q는 3 seeds × 4 cells = 12 units이고 E00은 0 updates이므로 실제 trained updates는 **9**다. §5 D1이 4 cells에서 `updates_total == 3` (line 149)이라고 쓴 것과 같은 규칙을 Q에 적용하면 9여야 한다.
6. **`common_ids` hash가 기록되지 않는다.** §6.1은 donor map sha256만 `init_hashes.json`에 기록한다 (line 193). cohort binding의 핵심인 15 `common_ids`의 sha256·개수·preflight 일치 assert가 없다.
7. §15 Q1 (line 538)은 아직 “F0≠Phase6 L”을 질문에 넣지만, §4 (line 116)와 §13A.6 (line 511)은 해당 hash-inequality assertion을 “tautological”이라며 제거했다. 질문 텍스트가 stale하다.

**다음 단계**

1. Q stage에 donor-crop/wrong-donor CE의 **non-persisting** finiteness/shape check를 추가하라(per-doc/delta 값은 쓰지 않고 `ce_finite`만). 이는 oracle을 만들지 않으면서 R-first 위험을 제거한다.
2. Q row를 9 updates로 고치고, `updates_total_ok`의 기대값을 stage별로 명시하라.
3. `common_ids_sha256`, `n_common=15`, uniqueness, preflight 일치를 `init_hashes.json`에 기록·assert하라.
4. §15 Q1의 “F0≠Phase6 L”을 I/O assert 문구로 교체하라.

---

## 2. Q2 — D1 mechanics_pass / flags / telemetry / seal

**판정: conditional**

**근거**

1. v1.5 must-fix 2–4는 실제로 반영되었다. `mechanics_pass` (line 489)가 `labels_computed==false`, `not_a_result==true`, `test_split_used==false`, `p1_used==false`, `d1_signal_read==false`를 AND한다. `timings`/`provenance`/`parallel` literal object도 추가되었다 (lines 468–470). T_proj audit이 가능해진 것은 개선이다.
2. **그러나 새 assertion 3개의 predicate가 정의되지 않았다.** §13A.4는 `cells_ok`, `updates_total_ok`, `e00_steps_zero`를 key로만 나열하고 (line 465), `mechanics_pass`는 “all assertions==true” (line 489)에 의존한다. `cells_ok`가 §5 assertion 1–4(cells list, adapter flags, LoRA counts)를 모두 포함하는지, `updates_total_ok`가 `updates_total==3`인지, `e00_steps_zero`가 `optimizer_steps==0`인지 문서에 없다. 정의가 없으면 seal predicate가 vacuous하게 true가 될 수 있다.
3. **seal은 여전히 자기신고다.** `labels_computed:false` 등은 같은 프로세스가 쓰는 값이고, negative test는 “any `d1_report.json`/`per_doc`/`delta_*` **input** exits non-zero” (line 54)로 입력만 막는다. `c5_pm_f0_mechanics.py`가 signal/delta 모듈을 import하지 못하게 하는 static import/AST test가 없다. §11 (line 350)의 “does not reuse `eval_arm_d1`”은 서술이지 강제가 아니다.
4. `real_memory_ce_calls: int` (line 479)에는 기대값·assert가 없다. D1이 M CE를 계산한다면 480, real eval만 한다면 80 등 stage별 기대값이 있어야 telemetry가 검증된다.
5. `timings.step100_s` (line 468)는 1-update D1에서 이름이 틀렸다(`final_s`가 맞다). 사소하지만 artifact 소비자가 오독할 수 있다.
6. checkpoint digest-only/`checkpoint_absent`/crash path (lines 482–486)는 v1.0 DS-1 지적을 잘 닫았다. 이 부분은 agree.

**다음 단계**

1. `cells_ok`를 `cells_list_ok`/`adapter_flags_ok`/`lora_counts_ok`로 분해하거나, 각 boolean의 정확한 predicate를 §13A.4에 명시하라.
2. `updates_total_ok := updates_total == 3`, `e00_steps_zero := cells.E00.updates == 0`을 명문화하라.
3. mechanics 모듈의 import allowlist를 AST test로 강제하라(signal/delta 함수 도달 불가).
4. `real_memory_ce_calls` 기대값을 stage별로 assert하고, `step100_s`를 `final_s`로 rename하라.

---

## 3. Q3 — STOP / MDE / near-threshold

**판정: conditional**

**근거**

1. 4-state table (lines 300–303)은 top-level에서 상호배타·전체포괄이다. `PASS_POSITIVE`는 `SIGNAL(E01,copy)`를 요구하므로 `ALL_FAIL`과 공존할 수 없고, `INDETERMINATE`는 “not ALL_FAIL and not PASS”로 나머지를 덮는다. 이 구조는 agree.
2. **MDE 산술은 검증되었다.** `.037573/1.96 = .0191699` → `.019170` (line 381), 50% MDE `.0376`, 80% MDE `2.802*.019170 = .05371` → `.0537`, `.05+.0537 = .1037` → `.104`, `.05+.0376 = .0876`. 모두 맞다. F−L proxy임을 명시한 것도 정확하다.
3. **그러나 `harm`/`benefit` label이 PASS와 배타적이지 않다.** `harm = CI_D.lower > 0 AND NOT EQUIVALENT` (line 313)인데, PASS는 `CI_D.lower > .05`를 요구하므로 PASS이면 `harm`도 true다. state table의 priority 2가 3을 이기므로 state 결정은 모호하지 않지만, label 정의는 “mutually exclusive”라는 §7 서술과 어긋난다. `harm`/`benefit`을 ROUTE_STOP reason 전용으로 한정하거나 `AND NOT PASS_POSITIVE`를 붙여야 한다.
4. **near-threshold 규칙이 정의되지 않았고 위치가 틀렸다.** §7 line 306은 “|mean_D| within one half-width of the boundary”라고만 쓰고 “the boundary”가 무엇인지(.05인지 ±.05인지) 정의하지 않는다. 더 중요하게, 이 규칙은 `ROUTE_STOP`에만 붙는데 ROUTE_STOP은 `mean_D`가 아니라 cell `FAIL`로 구동된다. 실제로 취약한 분기는 (a) `CI_D.lower`가 .05 바로 위인 PASS, (b) .05 바로 아래인 near-miss INDETERMINATE, (c) CI edge가 ±.05에 붙은 EQUIVALENT다. 이 세 경우에 보고 의무가 없다.
5. `ALL_FAIL + benefit → adapter_benefit` (line 310)의 방향은 맞다(E01−E11<0 ⇒ E11 우세 ⇒ adapter benefit). 다만 ALL_FAIL과 benefit의 공존 가능성은 문서화되어 있지 않다.

**다음 단계**

1. boundary를 `.05`로 명시하고, near-threshold 보고를 `PASS_POSITIVE`(lower가 .05±half-width), `INDETERMINATE`(near-miss), `EQUIVALENT`(CI edge가 ±.05±half-width)에 적용하라. ROUTE_STOP에는 descriptive로만 남겨라.
2. `harm`/`benefit`에 `AND NOT PASS_POSITIVE`를 추가하거나 ROUTE_STOP reason 전용으로 재정의하라.
3. `ALL_FAIL`과 `benefit`/`harm` 공존 시 reason 선택 예시를 §7에 추가하라.

---

## 4. Q4 — Cohort / cell CI / donor conditional

**판정: disagree**

**근거**

1. Cohort binding 자체는 개선되었다. §6.1 (lines 190–198)이 15 `common_ids`를 frozen preflight로 고정하고, 20-doc은 descriptive로 제한하며, donor map을 `donors_for(val20, cache)`로 고정하고, `eval_arm_d1`의 silent drop을 `NOT_EVALUABLE`로 처리한다. §6.6 (lines 150–153)의 “no 15→14 substitution”도 명확하다. 이 부분은 agree.
2. **치명적 내부 모순: 2-seed continuation이 3-seed 요구와 충돌한다.** §5 Stage R (line 181)은 “R seed excluded if its Q unit fails; remaining seeds continue only if ≥2 remain”이라고 한다. 그러나 §6.6 (line 150)은 “Exactly 15 common docs and **3 seeds** required”, line 153은 “If <15 or **<3 seeds**: `NOT_EVALUABLE`”, §7 `PROTOCOL_VALID` (line 163)은 “15 common_ids ... × **3 seeds**”다. 즉 Q failure로 seed가 하나 빠지면 2 seeds로는 **어떤 경우에도 evaluable하지 않다**. “≥2 remain이면 계속”은 dead rule이며, 96분 R을 돌리고 NOT_EVALUABLE을 받는 경로다. 이는 승인 blocker다.
3. **cell CI가 donor clustering을 무시한다.** §6.4 (line 135)는 doc-level bootstrap이고, donor는 val20에서 length-nearest로 재사용된다(§6.1 line 193). 15 docs × 5 donors에서 donor overlap이 크므로 doc independence 가정은 anti-conservative할 수 있다. §6.1 line 194의 LODO “report range”는 완화책이지만 **artifact/gate 요구가 아니다**. estimand를 fixed donor graph에 conditional로 한정한 것은 타당하나, LODO range가 `f0_r_labels.json`에 필수로 기록되어야 conditional claim이 성립한다.
4. `n_boot=10000` override는 실행 가능하다. `runner/c5_pm_stats.py`의 `bootstrap_paired_v2(values, n_boot=N_BOOT, seed=...)`가 `n_boot` 인자를 받고 (lines 29–31), `N_BOOT=1000`은 default일 뿐이다. `l_predicate` 금지도 유효하다.
5. `donors_for`는 `cache[rid]["h"].shape[0]` 기반으로 모든 cell이 같은 EG2 cache를 쓰므로 donor set equality가 구조적으로 보장된다. §13A.5의 `evaluated_donors == expected_donors == 5`도 적절하다.

**다음 단계**

1. **Q failure 시 R을 시작하지 말고 즉시 `NOT_EVALUABLE`로 종료하라.** “≥2 remain” 문장을 삭제하거나, 2-seed 평가를 허용하려면 §6.6/§7의 3-seed 요구를 명시적으로 바꿔야 한다(현재는 둘 다 불가).
2. LODO range를 `f0_r_labels.json` 필수 field로 만들고 `CI_D`와 함께 보고하라.
3. `common_ids_sha256`를 cohort artifact에 기록하라(Q1-3과 동일).

---

## 5. Q5 — Compute 16-core / setup / contention

**판정: disagree**

**근거**

1. **thread 수가 문서 내에서 4번 다르게 서술된다.** §0-7 (line 36)은 “16 cores, **1 thread/arm**; 4-vCPU excluded”, §12 table (lines 367–372)은 P/Q/D1/R 모두 “**3/arm**, 4 arms = 12 logical”, §5 Stage R (line 178)은 “4 arms × **3 threads/arm**”, §13A.7 (line 510)은 “`nproc>=16` (**or `threads_per_arm<=1`**)”. 어느 것이 승인 대상인지 결정할 수 없다.
2. **host gate에 구멍이 있다.** hard abort는 “`nproc < 16` **and** `threads_per_arm > 1`” (line 380)이다. §0/§13A.7의 “1 thread/arm” 설정에서는 4-vCPU host가 `nproc<16`이지만 `threads_per_arm==1`이라 **abort되지 않는다**. 그런데 §13A.7 (line 510)은 “current 4-vCPU workspace is not a qualifying host; no F0 run there”라고 명시한다. 즉 gate가 문서의 금지를 강제하지 못한다. 승인 blocker다.
3. **wall anchor가 measurement가 아니라 estimate다.** §12 line 373은 “Phase 6 D1 **recorded parallel measurement** (D-156): 1,180.6s”라고 하지만, `reports/C5_B0A_PM_PHASE6_D1_2026-11-09.md` line 13은 “D1 **wall estimate**: 1,180.6s / 1,200s cap”이다. §12 line 377의 “Wall anchor: Phase 6 registered 4,939.884s”도 `reports/C5_B0A_PM_PHASE6_REGISTERED_2026-11-09.md` line 9의 “**wall estimate**: 4,939.9s / 7,200s”와 다르다. estimate를 measurement로 승격한 것은 provenance 오류다.
4. **anchor의 thread config가 F0와 다르다.** registered report line 8은 “seed별 4-arm wave, 각 arm **2 threads**”라고 하고, D1 report line 13은 “4 processes × **3 threads**”다. F0 table은 3/arm이다. 96분 cap의 근거가 서로 다른 thread config의 estimate에 걸쳐 있다.
5. **`setup_s_effective`가 3 seed wave를 한 번만 센다.** `T_proj_R = setup_s_effective + 3 × sum(9 terms for slowest arm)` (line 373)에서 `setup_s_effective = setup_wall_s` (line 374)다. R은 3 seed wave마다 4 cells를 fresh build하므로 setup이 wave마다 발생한다. `setup_wall_s`가 “전체 3 wave의 first-start→last-ready span”으로 정의되지 않으면 setup을 최대 2/3 과소계상한다. v1.5 must-fix 10의 “total setup for 3 waves × 4 processes; explicit sum”이 v1.6에서 약화되었다.
6. `contention_ratio = parallel_wall_s / sum(per_arm_phase_s)` (line 379)를 cap에 곱하지 않고 보고만 하는 것은 타당하다. `T_proj_R`이 slowest arm 기준인 것도 parallel wall에 맞다.

**다음 단계**

1. thread config를 하나로 확정하라. 3/arm이면 §0-7과 §13A.7의 “1 thread/arm”을 삭제하고, 1/arm이면 §12 table과 §5 line 178을 고치고 T_proj를 1-thread 측정으로 재산출하라.
2. host gate를 `nproc >= 16` **단독 conjunct**로 만들거나, 1 thread/arm을 허용하려면 “4-vCPU no F0” 문장을 삭제하고 cap 근거를 다시 제시하라.
3. D1/R artifact에서 `wall_estimate_s`가 아니라 **measured `parallel_wall_s`**로 cap을 확정하고, anchor가 estimate임을 명시하라.
4. `setup_wall_s`를 “3 wave 전체의 setup span”으로 정의하고 `sum_process_setup_s`와의 관계를 assert하라.

---

## 6. Q6 — Scope / route-only

**판정: agree**

**근거**

1. H3는 §10 (lines 330–336)에서 arm/trigger/rank/identity/null/donor-discrimination endpoint 없이 완전히 제거되었고, “requires a separate prereg and approval after F0 is complete and reviewed”로 경계가 명확하다. F0 결과가 H3를 자동 개시하지 않는다는 문장도 있다.
2. §14 (lines 528–532)의 ROUTE_STOP consequence는 “stops only the route as configured ... does not stop the EG2 track, does not rescue B0-B, and does not launch H3”로 충분히 좁혀졌다. association-only, descriptive contrasts, lost controls(MF-4 null/1-seed gate)도 명시되어 과대 주장 경로가 닫혀 있다.
3. Phase 6 P/PA native-path evidence를 EG2 mechanism claim으로 쓰지 않는다는 경계(line 532)도 cause report §9의 MF-3 correction과 일치한다.
4. 남는 scope 위험은 없다고 판단한다. 다만 F0가 native no-adapter control(P)을 포함하지 않으므로 “EG2 feature 부족”과 “adapter 효과”를 F0 단독으로 분리하지 못한다는 점은 §14의 association-only로 이미 커버된다.

**다음 단계**

1. 없음. H3/route-only 경계는 그대로 유지하라.

---

## 7. 최종 판정

```text
최종 판정: NARROW
```

**이유**: v1.5 must-fix의 상당 부분이 실제로 닫혔고(특히 wrong-donor 모순, seal flags, telemetry/provenance, golden table, MDE 산술), core estimand(E01−E11, LoRA init matched)와 cohort/H3 경계는 수용 가능하다. 그러나 **프로토콜 자체의 gate가 두 곳에서 자기모순**이다: (a) 2-seed continuation vs 3-seed requirement, (b) 1-thread/arm vs 3-thread/arm 및 4-vCPU host gate hole. 또한 compute cap의 근거가 estimate를 measurement로 승격한 것이다. 이 세 가지는 승인 전에 반드시 고쳐야 하므로 CONTINUE가 아니고, 설계를 폐기할 이유는 없으므로 STOP도 아니다.

```text
Init:      conditional — 계약·golden table은 강함. primary path pre-R 미실행, Q 9 vs 12, common_ids hash 누락.
D1:        conditional — seal flags/telemetry 추가됨. cells_ok/updates_total_ok/e00_steps_zero predicate 미정의, import ban 없음.
STOP/MDE:  conditional — 산술 정확. near-threshold 정의·위치 오류, harm/benefit이 PASS와 비배타.
Cohort:    disagree — 2-seed continuation이 3-seed 요구와 충돌(blocker). LODO는 artifact화 필요.
Compute:   disagree — thread 수 4중 서술, host gate hole, estimate→measurement 승격(blocker).
Scope:     agree — H3 제거·route-only 경계 충분.
```

### Must-fix (ranked)

1. **[blocker] 3-seed 요구와 2-seed continuation의 모순 제거.** §5 line 181(“remaining seeds continue only if ≥2 remain”) vs §6.6 lines 150–153(“<3 seeds → NOT_EVALUABLE”) vs §7 line 163(“× 3 seeds”). Q failure 시 R을 시작하지 말고 즉시 NOT_EVALUABLE로 종료하라.
2. **[blocker] thread config 단일화 + host gate 수정.** §0-7 line 36(1/arm) vs §12 lines 367–372(3/arm) vs §5 line 178(3/arm) vs §13A.7 line 510(or ≤1). hard abort line 380이 4-vCPU/1-thread host를 통과시키므로 `nproc>=16`을 단독 조건으로 만들거나 1-thread 허용을 명시하고 cap을 재산출하라.
3. **[blocker] compute anchor의 provenance 수정.** §12 line 373 “recorded parallel measurement 1,180.6s”와 line 377 “Wall anchor 4,939.884s”는 각각 D1 report line 13, registered report line 9의 **estimate**다. measured `parallel_wall_s`로 cap을 확정하고, anchor의 thread config(2/arm vs 3/arm)를 명시하라.
4. **[high] primary signal path를 R 전에 non-persisting으로 검증.** §13A.8 line 517의 1-doc unit test는 gate가 아니다. Q stage에 donor-crop/wrong-donor CE finiteness/shape check를 추가하되 per-doc/delta 값은 쓰지 마라.
5. **[high] D1 assertion predicate 정의.** §13A.4 line 465의 `cells_ok`/`updates_total_ok`/`e00_steps_zero`가 무엇을 검사하는지 명시하고, `mechanics_pass`(line 489)가 vacuous true가 되지 않게 하라. `real_memory_ce_calls` 기대값도 assert하라.
6. **[high] `setup_wall_s`를 3-wave total로 정의.** line 373–374의 `setup_s_effective = setup_wall_s`가 wave별 setup을 한 번만 세지 않도록 “first-start→last-ready across 3 waves”로 정의·assert하라.
7. **[medium] near-threshold 규칙 재정의.** line 306의 “boundary”를 `.05`로 명시하고, ROUTE_STOP이 아니라 PASS/INDETERMINATE/EQUIVALENT의 경계 근접에 적용하라.
8. **[medium] Q trained updates 12 → 9.** §12 line 369. E00은 0 updates이므로 3 seeds × 3 trained cells = 9.
9. **[medium] `common_ids_sha256` 기록·assert.** §6.1 line 193은 donor map hash만 기록한다. 15개 cohort binding의 hash/개수/uniqueness/preflight 일치를 `init_hashes.json`에 넣어라.
10. **[medium] LODO range를 artifact로 승격.** §6.1 line 194의 “report range”를 `f0_r_labels.json` 필수 field로 만들고 `CI_D`와 함께 보고하라.
11. **[low] `harm`/`benefit`을 PASS와 배타적으로.** line 313–315에 `AND NOT PASS_POSITIVE`를 추가하거나 ROUTE_STOP reason 전용으로 재정의하라.
12. **[low] stale 질문/이름 정리.** §15 Q1 line 538의 “F0≠Phase6 L”(§4 line 116에서 제거됨), §15 Q5 line 554의 “nproc≥12”(§13A.7은 ≥16), §13A.4 line 468의 `step100_s`(1-update D1에서는 `final_s`).

### 잘못된 전제

1. “Phase 6 D1 recorded parallel measurement 1,180.6s” — 실제로는 `D1 wall estimate`다(`reports/C5_B0A_PM_PHASE6_D1_2026-11-09.md` line 13).
2. “Wall anchor: Phase 6 registered 4,939.884s” — 실제로는 `wall estimate: 4,939.9s`이고, registered run은 “각 arm 2 threads”였다(`reports/C5_B0A_PM_PHASE6_REGISTERED_2026-11-09.md` lines 8–9).
3. “16 cores, 1 thread/arm” — 같은 문서 §12 table과 §5 line 178은 3 threads/arm이다.
4. “Q trained updates 12” — E00이 0 updates이므로 9다.
5. “F0≠Phase6 L”이 Q1의 검토 항목이라는 전제 — §4 line 116과 §13A.6 line 511에서 이미 제거되었다.
6. “nproc≥12” (§15 Q5 line 554) — 본문 §13A.7 line 510은 `nproc>=16`이다.

---

## 8. 경계

```text
F0 v1.6 = NARROW (미승인)
Phase 6 = negative 종료 불변
B0-B = 미승인
test 163 = sealed
P1 = unused
T5Gemma2 = D-108 STOP
추가 학습/평가 = 없음
```

- 이 review는 승인이 아니다. D0/D1/R은 각각 별도 승인이 필요하다.
- 수정 파일: 이 파일 하나뿐이다.