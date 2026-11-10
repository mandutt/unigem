# C5 F0 v1.4 — New Block Round 4/10 Review (GLM)

- 작성일: 2026-11-10
- 검토 대상: `docs/plan_c5_f0_v1_4_2026-11-09.md` (DRAFT v1.4, 미승인·미실행)
- **reviewed HEAD: `60c806f95a97e284972a00ba1a0f5b43217e673e`**
- 동기화: `git fetch origin` + `git pull --ff-only origin main` → "Already up to date", HEAD = `60c806f95a97e284972a00ba1a0f5b43217e673e`
- 모델: `z-ai/glm-5.3-flash` (신규 독립 스레드; v1.3 및 이전 라운드 결론 미상속, archive된 v1.3 스레드 미열람)
- 열람: 요청 문서 8종 전부 + `runner/c5_pm_stats.py` + `runner/c5_pm_labels.py` + `runner/c5_pm_gate.py` + provenance artifact (`m_cohort_preflight.json`, `registered/registered_report.json`, `phase6_artifact_registry.json`) + `docs/decisions.md` D-156. step_seed golden table 12 vector과 MDE/SE 산술은 Python으로 직접 재계산해 검증. **학습/평가 실행 없음, test 163/P1 미사용, subagent 없음, repository 수정 없음 (이 파일 1개만 작성).**

---

## 0. Verbatim paired E01−E11 (대상 문서에서 그대로 인용)

v1.4 §2 Cells 표, E01/E11 행:

```text
| E01 (F0) | EG2 raw | none | 64 modules | 100 | adapter-free + LoRA |
| E11 (L) | EG2 raw | trained | 64 modules | 100 | adapter + LoRA |
```

v1.4 §6.3 Primary contrast (전문):

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

v1.4 §6.3 (전문):

```text
- Primary positive: `mean_D > 0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0`.
- `D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary.
- Copy primary; full secondary.
- **CI_D is doc-level only.** Seed-level `D_s` is a gate/descriptor, not a doc-level interval.
- `PASS_POSITIVE` requires the paired contrast, E01 absolute copy signal, and seed replication; this is not a per-cell significance conjunction.
```

---

## Q1. Init / Stage P / non-reuse — **conditional agree (1개 규격 모순은 must-fix)**

근거:

- §4 pseudocode (L87–95): `manual_seed(seed)` → adapter(조건부) → **항상** `manual_seed(seed ^ 0x5EED10A5)` → LoRA attach. LoRA 시드가 adapter 존재와 무관하게 재설정되므로 E01/E11 LoRA init 동일성은 구조적이고, post-init RNG state 동일(assertion 4)도 이 순서에서 도출된다. E10/E11 adapter 동일성(assertion 3)도 첫 RNG 소비가 `manual_seed(seed)` 직후이므로 성립. Phase 6 `build_arm`(`runner/c5_pm_phase6.py:143`, "RNG order: seed, adapter, then LoRA")를 수정하지 않고 `build_arm_f0`를 새로 두는 것도 정합.
- step_seed golden table(§4 L113–115)을 재계산해 **12/12 vector 전부 일치**를 확인: `step_seed(20261108,·)` = `0x9f02514d/0x3d5bdb86/0xdb9345df`, 20261109 = `...4c/87/de`, 20261110 = `...4f/84/dd`, 20261111 = `...4e/85/dc`. 괄호 고정 공식 `(seed ^ ((0x9E3779B9*(step+1)) & 0xffffffff)) & 0xffffffff`과 정확히 일치 — v1.3 must-fix(step_seed golden) 해소.
- **Stage P 신설(13A.1)은 방향이 맞다**: R 직전 등록 seed 3종(20261108/09/10) 전체에 대한 no-update init audit + `pre_r_init_audit_pass` gate(§13 L406)는 D0(20261111 단일 seed)만으로는 못 잡는 등록-seed init 문제를 닫는다. 시간 cap ≤10 min, no signal/M/phase7 경계도 명확.
- **Non-reuse (13A.6)**: hash-inequality 삭제 판단은 옳다. `build_arm_f0`에서 fresh random init이면 Phase 6 L과 hash가 다른 것은 tautology이고, 실제 비-reuse 증거는 I/O audit(`open`/`torch.load` path 기록 = Phase 6 경로 0)이 맞다. v1.3의 "F0 E11 init/final hash != Phase 6 L hash"(불가검 claim)를 "테스트 불가 → 프로세스 비-computation 감사"로 치환한 것은 v1.0 DS-5/Luna 지적에 대한 정당한 응답.

남는 문제:

1. **(blocker, must-fix 1) Stage P 기록 목록이 no-update stage와 모순된다.** 13A.1(L415)은 "Records assertions 1–8 + 13A.3 only; assertion 9 N/A (no optimizer step)"라 한다. 그러나 (a) 13A.3(L433) "First optimizer update must change…"는 정의상 optimizer step이 필요하고, (b) assertion 5(L108) `post_step0_rng_state_sha256`는 13A.2(L429)에서 "CPU RNG state **immediately after first optimizer step** and before next forward"로 정의되어 stage P(업데이트 없음)에서 계산 불가능하다. 즉 stage P가 실제로 기록할 수 있는 집합은 {1,2,3,4,6,7,8}이며, 13A.3은 D1 소관이다. 외부 검토 요청서 §1의 "stage P assertions 1–8; assertion 9 N/A"도 13A.3을 누락해 문서와 어긋난다. 해결은 기계적이지만 prereg가 gate 정의를 스스로 모순하는 상태로 승인될 수는 없다.
2. (소) §12 compute 표(D0/D1/R 3행)에 Stage P 행이 없다. 13A.1은 "Time counted in D0/compute, cap ≤10 min"이라 하나 표에는 반영 안 됨.
3. (소) §4 pseudocode 주석(L94)은 여전히 우선순위 모호한 `seed ^ (0x9E3779B9 * (step+1)) & 0xffffffff` 형태. L115 공식 + golden table이 진식체를 고정하므로 결과 위험은 없지만 pseudocode도 괄호 버전으로 맞춰야 오독이 없다.

다음 단계: (1) stage P 기록 집합을 no-update 계산 가능 집합으로 고정(13A.3은 D1로 이동, assertion 5는 D0/D1 정의 또는 재정의), (2) §12 표에 Stage P 행 추가, (3) pseudocode 괄호 정합 — 모두 구현 commit 이전 해결 가능.

## Q2. D1 schema / §13 stage scope / seal — **agree**

근거:

- **13A.4 literal schema**는 v1.0 DS-1(D1 seal 모순)에 대한 유효한 해법이다. key 집합을 열거하고(`schema_version`, `cells{...}`, `assertions{...}`, `m_records`, `phase7_records(must 0)`, `generation_records`, `real_memory_ce_calls`, `wrong_donor_ce_calls(must 0)`, `donor_map_loads(must 0)`, `checkpoint_digests`, `checkpoint_absent(must true)`, `mechanics_pass`, `partial`, `error`), nested value까지 literal로 고정했고 `No per_doc/final/delta_*/signal/phase7 objects`를 명시했다.
- **값 자체를 materialize하지 않는 설계가 seal보다 강하다**(§5 L171): D1 mechanics evaluator는 donor 평가를 아예 수행하지 않는다(`wrong_donor_ce_calls must 0`, `donor_map_loads must 0`) — 스키마에 수치가 없으므로 유출 경로가 원천 차단된다. "process non-computation is not artifact non-access"(L169)라는 v1.0 지적도 digest-only + 삭제 + 로드 금지로 응답했다.
- **§13 stage scope 분리가 이제 일관적이다**: D1은 `d1/f0_d1_mechanics.json`만 write(L405), `units/`·`checkpoints/`는 `r/` 아래 R-only, `pre_r_init_audit_pass:true`가 `r/` 생성 선행조건(L406), gate negative test(`d1_report.json`/`per_doc`/`delta_*` 입력 → non-zero, L167), decision driver가 `d1_sealed/*`를 읽지 않음(§5 L185). v1.3의 "3 trained checkpoints exist vs digest-only/discarded" 모순은 checkpoint가 `r/checkpoints/`(R 전용)로 이동되면서 해소되었다.
- 실존 코드 대교도 정확하다: `eval_arm_d1`은 `if not real_copy: continue`(`runner/c5_pm_phase6.py:464`)로 non-copyable doc을 **조용히 탈락**시키며, §6.1 L200 "silently drops … a missing doc means NOT_EVALUABLE, never a smaller cohort"는 이 사실의 정확한 기술이고 `c5_pm_f0_mechanics.py`가 `eval_arm_d1`을 재사용하지 않는다는 §11 L353 규정이 필요충분이다.
- crash path(`partial:true` + `error` + checkpoint 삭제, L472)도 스키마 내에 있다.

남는 우회 경로 (차단 필요 수준은 아님):

1. `error: string|null`은 자유 텍스트 — arm process가 in-memory로 계산한 값을 error 문자열로 밀어넣는 경로가 이론적으로 남는다. error를 closed enum으로 제한하면 닫인다.
2. negative test는 특정 파일명/키를 검사하지만, D1 종료 후 `reports/provenance/C5_f0/d1/`에 정확히 1개 파일만 존재한다는 directory-diff assert가 명문화되어 있지 않다(§13 L405가 규정이나 자동 검사는 아님).
3. stdout 로그를 통한 수치 출력 — 프로세스 표준 출력의 artifact성은 본 검토 범위 밖이지만, seal claim이 "process가 아무것도 계산하지 않음"(wrong_donor_ce_calls=0)에 기반하므로 실질 위험은 낮다.

## Q3. STOP taxonomy / MDE / reference dispersion — **agree**

근거:

- **4-state table(§7 L295–313)은 상호배타·전체포괄이다**: 우선순위 1 NOT_EVALUABLE → 2 PASS_POSITIVE → 3 ROUTE_STOP(ALL_FAIL) → 4 INDETERMINATE(else)로 순차 평가하므로 교집합이 없고 else 절이 전체를 닫는다. `PASS`(`CI_D.lower > +.05`)와 `EQUIVALENT`(`CI_D.lower >= -.05 AND CI_D.upper <= +.05`, L284)의 중복은 수학적으로 불가능(EQUIVALENT면 lower < upper ≤ .05라 PASS의 lower > +.05와 충돌). `harm/benefit`은 ROUTE_STOP 사유 enum으로만 사용되고 상태가 아니므로 taxonomy를 오염시키지 않는다.
- `ALL_FAIL`이 정확히 E01/E11 × copy/full(L304, L282–283)로 고정되고 `ROUTE_STOP`이 cell-level `FAIL(c,e)` 기준(L305)인 점, `ALL_FAIL`+EQUIVALENT/harm/benefit/else → `no_signal_equivalent > adapter_harm > adapter_benefit > no_signal_uncertain` 사유 우선순위(L301, L306–309)도 v1.3 must-fix("ALL_FAIL+benefit STOP과 default reason")에 부합한다. `benefit`(CI_D.upper<0, 즉 adapter가 contrast를 돕지만 두 셀 모두 signal 실패) 상황에서 route-as-configured를 stop하는 판단은 §8 route 정의와 일관적이다.
- **MDE provenance가 이제 정직하다**: §12 L378 "`.019170 = .037573/1.96` from Phase 6 `labels.json L_COPY_SIGNAL.paired`, an **F−L LoRA contrast planning proxy**, not a validated E01−E11 SE" — 산술 재계산 결과 .037573/1.96 = 0.0191699 ✓. 이는 v1.0 DS-3(MDE 산술 blocker: .166/.216이 단일-팔 SE 기반)의 완전한 철회·재표기다. `±.0124` equivalence range 삭제, `.104`(gate-only 80% power)/`.0876`(analytic 50% boundary)가 "neither is an observed F0 mean"으로 규정된 것도 정확하다.
- **"P−PA reference dispersion" 재명명이 정확하다**: mean +3.0652, SE 0.6209, 14/15 positive, per-doc SD 2.405 — 재계산상 2.405/√15 = 0.620968 ✓. 이 수치는 native 경로의 P−PA paired contrast로서 E01−E11(EG2 경로)의 upper bound가 될 수 없으며, v1.3에서 "upper bound"였던 표현을 "reference dispersion"(§0 변경 8, L255 "Realized `CI_D` governs EQUIVALENT/harm/benefit and is conditional on the fixed donor graph; no population inference")으로 하향한 것은 올바른 방향이다.
- **Expected branch 수정(v1.3→v1.4)은 논리적으로 개선이다**: v1.3은 "P−PA(+3.065, 14/15)는 ROUTE_STOP 쪽"이라 했으나 이는 방향을 반대로 읽은 것이다. cause report(`reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md` §2)에서 P(no adapter) copy Δ 3.076 vs PA 0.011은 **adapter 제거가 signal을 살린다**, 즉 E01>E11 방향(D>0, PASS 방향)의 문맥이다. v1.4의 "PASS-direction context, not ROUTE_STOP"(§0 변경 3) + §6.5 "expected branch is **undetermined**; PASS and ROUTE_STOP are both live"(L255) 유지는 과대주장 없는 정확한 상태다. PASS가 여전히 `CI_D.lower>.05` + `SIGNAL(E01,copy)` + 2/3 seeds를 요구하므로 이 문맥이 gate를 약화시키지 않는다.

다음 단계: 없음 (선택) INDETERMINATE 도달 시 사유 필드(enum: discordant 등)를 두면 해석 편의가 올라감.

## Q4. Cohort / donor CI — **agree**

근거:

- **estimand 고정은 v1.0 DS-2(length-selected cohort blocker)의 요청대로다**: §6.1 L191–194 "20 val docs are descriptive; primary estimand is **15 length-eligible docs + fixed donor graph**", "15 common = frozen preflight `common_ids`", "Generalization to the 20-doc val population is forbidden". `m_cohort_preflight.json`의 `common_ids` = 15 실측 확인. 20-doc descriptive 보고 의무(L194)도 유지.
- **donor CI 조건부화**: `CI_D` conditional on fixed donor graph, LOO(donor-cluster) 재계산은 descriptive range만(§6.1 L196), donor의 val-doc 재사용 명시 선언(L196) — cohort가 length-selected라는 사실을 숨기지 않고 inference 범위를 제한하는 정합적 설계. donor graph가 사전 고정이므로 사후 선택(post-treatment selection) 문제는 없다.
- **donor 무결성 assert가 충분하다**: 문서당 정확히 5 donors + all-cell donor set 동일성(§6.1 L198, PROTOCOL_VALID 조건 L274, 13A.5 `evaluated_donors==5 and expected_donors==5` abort, L476), donor map sha256 in `init_hashes.json`(L195). `donors_for(val_ids, cache)`는 EG2 cache만 사용해 cell-independent이므로 all-cell 동일성은 구조적으로도 성립.
- **n_boot=10000**: frozen `N_BOOT=1000`(`runner/c5_pm_stats.py:15`, prereg v1.0.11 §10.1 L1172)에 대한 explicit override + `assert realized.n_boot == 10000 and realized.seed == 20261109`(§6.3). `bootstrap_paired_v2`는 `n_boot`/`seed`를 반환 필드로 기록하므로(`c5_pm_stats.py:48,66–67`) 이 assert는 구현 가능하다.
- **l_predicate 금지가 필요·충분하다**: 실제로 `runner/c5_pm_labels.py:62–63`의 `l_predicate`는 `bootstrap_paired_v2(per_doc_delta, 1000, 20261109)`로 **1000을 하드코딩**하고 `c5_pm_gate.py:37–38`이 이를 사용한다 — F0이 이 함수를 쓰면 n_boot override가 묵살된다. `l_predicate forbidden`(§6.3, §0 변경 6)은 DS-6(n_boot silent revert)에 대한 정확한 차단이다.
- missing data(§6.6): 15 docs × 3 seeds 강제, NA 허용 없음, `<15 or <3 seeds → NOT_EVALUABLE`, no 15→14 substitution — `eval_arm_d1`의 조용한 탈락(위 Q2)과 결합해 cohort 축소 경로가 닫여 있다.
- seed-sign gate: `D_s`는 paired contrast per seed, 2/3 seeds는 replication gate일 뿐 second primary가 아님(§6.3) — CI가 doc-level only임과 함께 이중 추론 오류를 막는다.

다음 단계: 없음.

## Q5. Compute 9-term / setup / execution host — **agree**

근거:

- **9-term 대응이 정확하다**: §12 L371의 9 terms(`100*t_train`, `t_step0_eval_20x5`, `t_step100_eval_20x5`, `t_M_build`, `t_initial_M_ce`, `t_generate_20x256`, `t_primary_replay`, `t_replay_15x5x2x2x2`, `t_overhead`)은 prereg v1.0.11 §11.5(`runner/c5_pm_stats.py` `t_proj_seconds`의 required 집합과 정확히 일치)의 1:1 복사다. v1.0 DS-7(T_proj) 해소.
- **wall anchor 실측 검증**: `registered_report.json`의 `wall_estimate_s = 4939.884017705917` — §12의 4,939.884s와 일치하며, 이는 wave maxima 1,661.1+1,751.4+1,527.4 ≈ 4,939.9의 합(parallel wave-max 합산)이다. 따라서 F0의 `T_proj_R = setup_s_effective + 3 × sum(9 terms for slowest arm)`(L372)은 frozen Phase 6 공식(모든 arm 합산)과 **aggregation semantics가 다르지만** anchor의 wave-max 의미론과는 더 정합하는 선택이다. `contention_ratio = parallel_wall_s / sum(per_arm_phase_s)` + `nproc`/`threads_per_arm` 기록(L376)과 `nproc<12 or T_proj_R>96min` hard abort(L377)가 이 선택의 위험을 덮는다. `setup_s_effective` per-process/wave 정의와 "amortization must be proven in orchestrator commit"(L373)도 v1.3 must-fix(3) 응답으로 충분.
- **D1 cap 정합**: D-156(`docs/decisions.md:216`) 실측 parallel 1,180.6s/1,200s(19.7 min) 대비 F0 D1 cap 25 min은 여유가 있고, F0 D1은 Phase 6 D1보다 phase7(2,400→0)·donor CE(0)가 가벼우므로 방향이 옳다.
- **R cap 정합**: F0 R = 900 updates(E00 eval-only), M 1,440 = 120×12, phase7 7,200 = 600×12, generation 240(§5 L180) — Phase 6 registered(1,200 updates, 4,939.884s = 82.3 min, cap 120 min) 대비 업데이트 수와 phase 부하가 같거나 가벼우므로 96 min cap은 근거 있는 여유. "no 1.316 multiplier"(L182) 제거와 "final cap from D1 T_proj and nproc≥12"(L182)의 2단계 확정도 정합.
- **Execution host(13A.7)**: `nproc>=12` required, 4-vCPU workspace no-run 명시는 honest한 전제 선언이고, "F0 runner/orchestrator must be committed before D0"(L487) + provenance 요구(§11 L357: committed SHA, clean tree, `code_commit`/command/input SHA 기록)는 v1.0 DS-4(provenance blocker)의 prereg-level 응답으로 충분하다.

남는 문제 (차단 아님):

1. D1 cap 25 min은 frozen prereg §11.3 D1 ≤20 min의 완화인데 문서에 그 사실이 명시되지 않았다(v1.0 GLM 지적이 v1.4에서도 미반영). 한 줄 annotation 권장.
2. `t_train`의 100× 선형 외삽(D1 1-update 실측 → R 100 updates)은 가정이지만, D1이 동일 4-arm×3-thread 구조에서 측정되므로 contention이 포함된 실측 기반이고 cap abort가 있어 수용 가능.

## Q6. Scope / route-only — **agree**

근거:

- **§8 route definition(L317–329)**이 route-as-configured를 11개 요소로 완전 열거한다(EG2 layer19 raw 512, M prefix 753, adapter 유무, mT5-small base eval, 64 q/k/v/o LoRA r8 alpha16 dropout .05, 100 updates batch 1 train20 AdamW wd .01, lr 1e-3/1e-4, donor-crop 20 val/5 donors/15 common, frozen thresholds).
- **§14 Non-goals가 v1.0 DS-8을 전부 반영한다**: association-only 한정(L498: "does not identify an architecture-only bottleneck"), ROUTE_STOP route-only(L499: EG2 track stop 아님, B0-B 구제 아님, H3 개시 아님), descriptive contrasts no-inference(L500), **lost controls 명시**(L501: MF-4 zero/permuted null과 1-seed signal gate가 scope-out이며 F0이 대체했다고 주장 불가) — 마지막 항은 이전 라운드에서 반복 지적된 "잃어버린 통제"를 부정하지 않고 남겨두는 정직한 처리다.
- **H3 완전 제거(§10)**: "No H3 arm, trigger, rank, identity, null, or donor-discrimination endpoint is registered here"(L343), 별도 prereg+승인 요구(L344–345), "F0 results do not automatically launch H3"(L345) — F0 결과가 H3를 자동 개시하지 않는 경계가 규정 수준에서 충분하다. negative F0가 H3로 구제되는 경로도 L346이 차단한다.
- **F0 negative의 해석 한계도 선언되어 있다**: cause report §6 H1 예상 분기("F0 ~0 → EG2 layer19 feature 자체가 부족")를 F0 prereg는 §14 association-only로 규약화해, "EG2 content 부족 vs decoder-space alignment 부재"(MF-4)를 F0 하나로 구분하지 못한다는 한계를 claim과 분리했다.
- test 163 sealed / P1 unused / T5Gemma2 D-108 STOP 유지, Phase 6 negative 종료 불변, B0-B 미승인 — 문서 헤더와 §18 상태가 일관적이다.

다음 단계: 없음.

---

## 검증 요약 (이 검토가 직접 확인한 사실)

| 항목 | 검증 방법 | 결과 |
|---|---|---|
| step_seed golden 12 vector | Python 재계산 | 12/12 일치 (§4 L114) |
| MDE .019170 | .037573/1.96 재계산 | 0.0191699 일치 |
| P−PA SE 0.6209 | 2.405/√15 재계산 | 0.620968 일치(0.6210 반올림과 1e-4 차이, 무의미) |
| wall anchor 4,939.884s | `registered_report.json` 열람 | 4939.884017705917 일치, wave-max 합 4,939.9와 정합 |
| D1 실측 1,180.6s | `docs/decisions.md` D-156 | 일치 |
| common_ids = 15 | `m_cohort_preflight.json` | 일치 |
| frozen N_BOOT=1000 | `c5_pm_stats.py:15`, prereg §10.1 | 일치 → n_boot=10000 explicit override 정당 |
| l_predicate 하드코딩 | `c5_pm_labels.py:62–63` | 1000 하드코딩 확인 → 금지 조항 필요·충분 |
| eval_arm_d1 조용한 탈락 | `c5_pm_phase6.py:464` | `if not real_copy: continue` 확인 → NOT_EVALUABLE 규정 정당 |
| 9 terms | `c5_pm_stats.py` `t_proj_seconds` required set | §12 9 terms와 1:1 일치 |

---

## 최종 판정

```text
최종 판정: CONTINUE

Initialization: conditional agree — 계약·golden table·non-reuse 치환은 충분하나, stage P 기록 집합이
  no-update stage와 모순(13A.1 "1–8 + 13A.3" vs 13A.3/assertion 5가 optimizer step 요구). 승인 전 수정 필요.
D1 seal: agree — 값 미-materialize + literal schema + stage-scope 분리로 v1.0 DS-1 봉쇄. 잔여 우회(error 문자열,
  directory-diff 부재)는 enum/assert 한 줄 수준.
STOP/MDE: agree — 4-state 상호배타·전체포괄, PASS/EQUIVALENT 비중복, MDE provenance 철회·재표기 완료,
  reference dispersion 하향과 expected branch 방향 수정 모두 논리적 개선.
Cohort/CI: agree — estimand 고정 + CI_D 조건부 + LOO descriptive + donor asserts + n_boot=10000 assert +
  l_predicate 금지(실코드 하드코딩 확인)로 DS-2/DS-6 해소.
Compute: agree — 9-term 1:1, anchor/duration 실측 검증, slowest-arm aggregation은 wave-max 의미론과 정합,
  provenance commit 선행조건 충분. D1 cap 완화 annotation 권장.
Scope: agree — route 열거, association-only, ROUTE_STOP route-only, lost controls 선언, H3 완전 분리.

Must-fix (ranked):
1. (blocker, D0/stage-P 구현 commit 이전) 13A.1 모순 해소: stage P 기록 집합을 no-update 계산 가능 집합
   {1,2,3,4,6,7,8}로 고정, 13A.3(group-specific weight change)은 D1 소관으로 이동, assertion 5의
   post_step0_rng_state 정의(13A.2 L429 "after first optimizer step")를 stage P 문맥과 일치시킬 것.
   외부 요청서 §1의 "assertions 1–8; assertion 9 N/A" 요약도 동기화.
2. (high, 동일 시점) §12 compute 표에 Stage P 행 추가(cap ≤10 min, 시간 계수 위치 명시).
3. (medium) 13A.6 I/O audit의 감시 대상 loader 열거(open/torch.load + 존재 시 safetensors/np.load) 또는
   "authoritative" 주장을 audited loader 범위로 한정.
4. (medium) D1 crash-path `error`를 closed enum으로 제한 + D1 종료 후 `d1/`에 정확히 1개 파일 존재
   directory-diff assert 추가.
5. (low) §4 pseudocode 주석을 괄호 고정 공식으로 교체; D1 cap 25 min이 frozen §11.3 20 min의 완화임을 명시.

잘못된 전제:
- 요청서 §1 "Stage P는 assertions 1–8; assertion 9 N/A"는 실제 plan(13A.1: "1–8 + 13A.3")과 어긋나며,
  어느 쪽도 no-update stage에서 실행 불가능한 항목(assertion 5, 13A.3)을 걸러내지 못한다 — 이것이 must-fix 1이다.
- v1.4 자체의 전제는 발견된 범위에서 성립: P−PA를 PASS-direction context로 재분류한 것(§0 변경 3)은
  cause report §2 수치(3.076 vs 0.011)와 방향이 일치하고, ROUTE_STOP/PASS 양쪽을 live로 유지하는 §6.5는
  과대주장이 아니다.
```

---

## 결정 경계

```text
F0 v1.4 = CONTINUE (조건부 승인 경로)
must-fix 1–2는 stage-P/D0 구현 commit 이전 해결 필수; 3–5는 동일 commit에서 병행 권장.
must-fix 1은 기계적 수정이므로 신규 review round를 요구하지 않는다 — 다음 stage gate(D0/stage-P 승인)에서 확인.
그 외 수치·산술·실코드 대응은 본 검토에서 직접 재계산/열람으로 검증 완료.
금지 사항 유지: 승인 전 실행 금지, test 163 sealed, P1 unused, subagent 없음, 본 파일 외 repository 수정 없음.
```