# C5 F0 v1.9 — Independent Review (GLM, new block round 9/10)

- 작성일: 2026-11-10
- 검토자: `z-ai/glm-5.3-flash` (Hoplite)
- 대상: `docs/plan_c5_f0_v1_9_2026-11-09.md`
- 성격: **새 독립 검토** — v1.8 스레드 archive 후 신규 10라운드 블록의 9번째 라운드. v1.8 결론을 상속하지 않음(문서만 참조).
- 추가 학습/평가: 없음. test 163: sealed. P1: unused. subagent: 미사용.
- 파일 변경: 이 보고서 1개뿐 (지정 경로 외 수정 없음).

## 0. Workspace 동기화 및 reviewed HEAD

```text
git fetch origin            -> OK (FETCH_EXIT=0)
git pull --ff-only origin main -> "Already up to date." (PULL_EXIT=0)
reviewed HEAD = d88d8de1f7641fd44761dadedc8b5d0ffc53498b
                (2026-11-10 12:24:16 +0900, "docs: add C5 F0 v1.9 review request")
tree = clean
```

읽은 파일(전부): `docs/plan_c5_f0_v1_9_2026-11-09.md`, `docs/plan_c5_f0_v1_8_2026-11-09.md`,
`reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`,
`reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`,
`docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py`.

## 1. Verbatim paired E01−E11 (원문 그대로)

출처: `docs/plan_c5_f0_v1_9_2026-11-09.md` §6.2 (L207–212), §6.3 (L216–226). 수정 없이 그대로 인용한다.

```text
delta_c(s,d) = mean_donor( CE_wrong_donor - CE_real )
```
- copy and full separately.
- per-doc seed average: `delta_c(d) = mean_s delta_c(s,d)`.

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```
- `f0_labels.json` alias is forbidden; canonical is `f0_r_labels.json`.
- `l_predicate` bootstrap is forbidden for F0.

- Primary positive: `mean_D > 0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0`.

frozen 상위 규약(대응 관계 확인용, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md` §3.5 L437–447 원문):

```text
L_COPY_SIGNAL = mean delta_copy >= .05
                AND copy CI lower > 0
                AND paired L>F copy mean > 0
                AND 2/3 registered seed copy means > 0

L_FULL_SIGNAL = mean delta_full > 0
                AND full CI lower > 0
                AND paired L>F full mean > 0
                AND 2/3 registered seed full means > 0
```

F0의 E01−E11은 이 L>F paired 구조를 그대로 이어받되, paired 대상이 E01/E11로 바뀌고
`l_predicate` bootstrap이 금지되며 n_boot이 10000으로 명시 override된다 (§6.3 L219–224). 일관성 확인.

## 2. Q1 — D1 CE formula / dry-run

```text
Q1.
- 판정: conditional agree
- 근거
  (a) v1.8의 순환 오류가 제거되었다. v1.8 §13A.4 L508의 기대값식은 "…+ M CE count from report; exact integer
      frozen in f0_d1_mechanics.json and compared"로, 검증 대상 report에서 기대값을 가져오는 순환이었다.
      v1.9 §13A.4 L498은 "committed mechanics evaluator call graph에서 유도, counted op = real_memory_ce
      per doc×donor×cell×phase, 20-doc mechanics와 15-doc donor-crop 분리, frozen at D1 code commit,
      not from the output report"로 교체되어 순환이 끊겼다.
  (b) dry-run이 계측(instrumented) 기반이고 mismatch → NOT_EVALUABLE(§0 item1 L21–22, §13A.4 L498)이며,
      expected/realized/ok 3키가 스키마에 선언(L485–487)되고 real_memory_ce_calls_ok가 mechanics_pass에
      wiring되었다(L499). D1은 counts만 저장(§5 L161–171, §13A.4 L496)하므로 dry-run이 signal 유출 경로가 아니다.
  (c) 분리된 mechanics evaluator의 필요성이 현行 러너로 실증된다: runner/c5_pm_phase6.py의 eval_arm_d1(L429–489)은
      per-doc delta_shuffled_copy/full을 materialize한다(L466–476). "eval_arm_d1을 재사용하지 않는다"(§11 L356)는
      제약이 v1.0 synthesis DS-1의 근본 원인을 정확히 차단한다.
- 다음 단계
  1) dry-run 자체의 감사 기록을 정의하라: dry-run이 어디에 무엇을 남기는지(최소한 expected count 값 1개와
     dry-run 코드 commit) 명시되지 않았다. provenance 객체(§13A.4 L475)에 dry_run_record 1줄 추가로 충분하다.
  2) expected==realized 대조를 러너 내부 assert(실행 중 단절)로도 수행하라. 현재는 파일 검증에 의존한다.
```

## 3. Q2 — P/Q per-seed schema

```text
Q2.
- 판정: conditional agree
- 근거
  (a) P: per_seed {seed -> {cells:{E00,E10,E01,E11 -> {hash, lora_names, n_params}}, p_r_hash_equal}} (§13A.10 L544),
      pass = 3 per-seed blocks × 4 cells + canonical hashes + KAT 참조(L548). v1.8의 aggregate-only 표현을
      per-seed로 승격시킨 것은 v1.9 §0 item2(L23–24) 대로이며, 3 seeds × 4 cells의 완전성 결손을 per-seed로 잡는다.
  (b) Q: per-seed units:4, trained_updates:3, e00_updates:0 + per-cell {post_step0_rng_sha256, group_change_ok,
      wrong_donor_finite, shape_ok} (§13A.10 L551–560). "12/9는 §12 aggregate only"(L561)로 격상 전술 숫자를
      결정에서 분리했다. §13A.3(L442–446) group-specific weight change가 Q의 group_change_ok의 정의를 제공한다.
  (c) Q가 wrong-donor CE finiteness/shape를 수행(§13A.1 L425)하므로 §13A.8의 "first numerical exercise at R"
      잔여 리스크가 실질적으로 축소되었다(단, §13A.8 본문은 미갱신 — must-fix 3).
- 다음 단계
  1) Q의 12 units에 대한 artifact 경로가 §13(L389–407)에 없다. q/q_seed_audit/{seed}.json만 선언되어 있고
     per-unit raw record(그룹 변경 증거, loss, timing)의 저장 위치가 미선언이다. 경로를 선언하거나
     "audit JSON의 hash/bool이 유일 Q artifact"임을 명시하라.
  2) Q per-cell 블록에 updates:int(학습셀 1, E00 0)를 명시 필드로 추가하라. 현재는 units:4/trained_updates:3
     aggregate로만 추론된다.
  3) P/Q cap 초과 시 fallback(D0 L139/D1 L380의 "repair or re-review; no silent extension" 문구)이 없다
     (§12 L369–370, §13A.1 L421/L423) — must-fix 5.
```

## 4. Q3 — D1 materialization / wall fallback

```text
Q3.
- 판정: agree
- 근거
  (a) "signal delta never materialized"가 3중으로 강제된다: (i) 분리 evaluator(§11 L356), (ii) exact-key
      allowlist + denylist("No per_doc/final/delta_*/signal/phase7 objects", §13A.4 L496), (iii) 파일시스템
      음성시험 + crash path partial:true + checkpoint 삭제(§13A.4 L502–503). checkpoint는 digest-only,
      loading forbidden(§5 L166–167)이고 "process non-computation is not artifact non-access"(L167)로
      잔여 리스크가 정직하게 선언되어 있다.
  (b) wall fallback: "measured wall >25 min → repair or re-review; no silent extension"(§12 L380)이 v1.8의
      provisional-only 표현(v1.8 §0 L24)을 보완한다. D0 15 min provisional(§5 L139), D1 25 min(§5 L160,
      §12 L380)으로 provisional/binding 구분이 일관된다.
  (c) R 게이트가 mechanics-only이다: "no signal-based gate"(§5 L182), decision driver는
      f0_d1_mechanics.json/f0_r_labels.json/init_hashes.json만 읽고 d1_sealed/* 를 읽지 않는다(§5 L184,
      §11 L359). signal 유출이 gating 결정에 도달하는 경로가 서술 수준에서 차단된다.
- 남는 우회 경로 (선언된 잔여)
  - stdout/log 채널: §13 L409가 D1/Q stdout CE 출력을 금지하지만 파일 allowlist가 로그를 묶지 않는다.
    절차적 통제로 남는다(수용 가능, 음성시험 권장).
  - D1과 R 사이 orchestrator의 in-memory signal 계산은 기술적으로 가능하나, R 시작/결정 프레디킷이
    mechanics-only이므로 결정 오염은 없다. 잔여는 §5 L167에 이미 명시됨.
- 다음 단계
  1) §11 L359의 gate 음성시험을 구체화하라: "decision driver에 합성 d1_sealed/* 입력 → non-zero exit"을
     시험 목록에 명시(§13A.4 L502의 파일시스템 음성시험과 별개 행으로).
```

## 5. Q4 — R mechanics / scope boundary

```text
Q4.
- 판정: conditional agree (여기서 approval blocker 1건)
- 근거
  (a) r_mechanics_pass.json에 real_memory_ce_calls / wrong_donor_ce_calls / donor_map_loads / provenance_ok가
      추가되었다(§13A.10 L564–576, v1.9 §0 item6 L31–32). v1.8 스키마는 R의 CE 계수가 없었다(v1.8 §0 item2 L31).
  (b) scope: loader가 full-split 파싱 전에 allowlist 적용(§13A.9 L535), transitive test163/P1 read-path
      음성시험(§13A.7 L523, §13A.9 L535), data_scope.json(L536), init non-reuse I/O 감사 — protected path
      opens == 0 + probe 음성시험 + committed clean-tree SHA(§13A.6 L509–516). v1.0 DS-8/MF-6의 "attestation이
      아니라 read-path proof" 요구에 부합한다.
- 차단 근거 (blocker)
  - R 스키마의 CE 필드가 bare int이다: expected 값, ok 프레디킷, r_mechanics_pass의 합성 규칙이 어디에도 없다
    (§13A.10 L564–576). v1.8 §0 item2 L31은 "r_mechanics_pass = 3 seeds, 4 cells, updates 900, M/phase7 counts,
    provenance"로 합성 규칙이 있었는데 v1.9는 스키마만 남기고 합성 규칙을 떨궜다. D1은
    expected_real_memory_ce_calls + real_memory_ce_calls_ok(§13A.4 L485–487, L499)을 갖는 반면 R에는 없으므로,
    wrong_donor_ce_calls == 0(= 주 endpoint 미계산, silent no-op)인 R도 r_mechanics_pass:true를 통과할 수 있다.
  - §5 R L181이 요구하는 nproc/threads_per_arm/parallel_wall_s/contention_ratio의 저장 위치가 §13 artifact
    목록에 없다(§11 L357의 c5_pm_f0_parallel.py가 쓴다는 것만 있고 대상 파일 미선언).
- 다음 단계
  1) (필수) r_mechanics_pass 합성 규칙 + expected_real_memory_ce_calls/wrong_donor_ce_calls 기대값(커밋된 R call
     graph에서 D1과 동일 counted-op 정의로 유도) + *_ok 플래그 + wrong_donor_ce_calls > 0 단언을 추가하라.
  2) R wall/parallel 기록의 artifact 경로를 선언하거나 r_mechanics_pass.json 스키마에 parallel 객체를 추가하라.
```

## 6. Q5 — Compute 8 threads / affinity / orchestrator commit

```text
Q5.
- 판정: conditional agree
- 근거
  (a) 8 logical = 4 arms × 2 threads/arm이 P/Q/D1/R 전 단계에서 일관된다(§12 L369–373). 이는 frozen anchor
      2 threads/arm(v1.8 §0 L22–23, D-157)과 정합하고, Phase 6 walls(1,180.6s / 4,939.884s)는 estimate로
      강등 표기되었다(§12 L375, L379) — v1.0 DS-7 후속으로 정확하다.
  (b) 산술 검증(모두 §5/§12 수치와 합치): R 900 = 3 cells × 3 seeds × 100; M 1,440 = 15 targets × 8 records
      (2 variants × 2 kinds × 2 endpoints) × 4 cells × 3 seeds; phase7 7,200 = 15 × 5 donors × 2 × 2 × 2
      (=40/doc) × 4 × 3; generation 240 = 20 × 4 × 3; D1 M 480 = 15 × 8 × 4, generation 80 = 20 × 4.
      러너의 m_records_for(L621–657)와 phase7_records_for(L674 이하)의 레코드 구조와 일치한다.
  (c) orchestrator commit이 선행 조건인가 — 예. §13A.7 L521 "F0 runner/orchestrator must be committed before
      D0" + §11 L360 provenance commit. T_proj는 D1 유도 하한이고 R 구속 게이트는 measured wall ≤96 min
      (§13A.7 L522, §12 L380–382). nproc<16 또는 T_proj_R>96 min hard abort(§12 L382).
- 차단 근거 아님, 단 미완결
  - CPU affinity/quota가 §0 item8(L36)에 "변경 사항"으로 선언되었지만 전 문서에서 유일 출처가 L36 한 줄이다.
    메커니즘(core pinning, torch.set_num_threads, OMP/MKL env)도, 기록 필드(§13A.4 L476 parallel 객체에는
    nproc/threads_per_arm/parallel_wall_s/contention_ratio만 있음)도 없다. 현재 상태로는 구현 불가능한 주장이다.
- 다음 단계
  1) affinity/quota 메커니즘과 기록 필드를 §12/§13A.4에 명시하라(must-fix 2).
  2) P ≤10 min, Q ≤15 min(§12 L369–370)은 미측정 cap이다. D0/D1처럼 provisional + 초과 시 repair/re-review
     문구를 붙여라(must-fix 5).
```

## 7. Q6 — Near-threshold / scope

```text
Q6.
- 판정: agree
- 근거
  (a) §7 L307: cell-level SIGNAL의 mean margin / CI-lower margin / seed-sign margin을 분리 기록하고
      "diagnostics are non-decisional and do not alter gates". v1.8 §0 item4(L35–36)의 요구를 충족하며
      재량 게이트를 만들지 않는다.
  (b) PASS와 EQUIVALENT의 무결합 검증: PASS_POSITIVE는 CI_D.lower > +.05(§7 L301)를 요구하므로 상한도 +.05를
      초과하고, EQUIVALENT는 CI 전체가 [−.05, +.05] 내(§7 L285)이므로 두 상태는 수학적으로 배타적이다.
      근접 사례("E01 positive/E11 negative but CI not >.05 → INDETERMINATE (discordant), not PASS", §7 L314)도
      명시되어 임계선 게임이 불가능하다.
  (c) §6.5 L256은 ±.0124 평균 동치 구간 주장을 명시적으로 거부하고 expected branch를 undetermined로 유지한다 —
      v1.0 DS-3/MDE 재계산(.019170 = .037573/1.96, 50% .0376, 80% .0537 = 2.8×SE, §12 L383)과 모순 없음.
      산술 재확인: .037573/1.96 = .019170, (1.96+0.84)×.019170 = .05368.
  (d) state 우선순위 NOT_EVALUABLE > PASS_POSITIVE > ROUTE_STOP > INDETERMINATE(§7 L296–304)는 상호배타·전체
      포괄이며, ALL_FAIL 정의가 E01/E11 × copy/full로 정확히 고정되어 있다(L305). reason 우선순위
      EQUIVALENT > harm > benefit은 ROUTE_STOP 사유에만 적용됨이 분리되어 있다(L290–294, L308–311).
- 다음 단계
  1) margin 계산식(mean − .05, CI.lower − 0, seed 부호 개수)을 R 리포트 스키마에 명시하고, margin이
     f0_r_labels.json의 결정 필드로 유입되지 않음을 문장으로 고정하라.
```

## 8. v1.8 must-fix 반영 검증 (상속 아님, 독립 대조)

| v1.8 요구(출처) | v1.9 반영 | 판정 |
|---|---|---|
| D1 CE count formula 애매(v1.8 §13A.4 L508) | call-graph 유도 + dry-run + 코드 commit freeze(§13A.4 L498) | 반영 |
| P per-seed schema(v1.8 §0 L27) | per_seed + p_r_hash_equal + KAT(§13A.10 L540–549) | 반영 |
| Q per-seed 4 units/3 updates(v1.8 §0 L39–40) | per-seed units:4/trained_updates:3(§13A.10 L551–562) | 반영 |
| D1 materialization(v1.0 DS-1) | never materialized + allowlist + digest-only + FS tests(§5 L161–171, §13A.4 L496–503) | 반영 |
| D1 wall fallback(v1.8 §0 L24 provisional) | >25 min → repair/re-review, no silent extension(§12 L380) | 반영 |
| R mechanics counts(v1.8 §0 L31) | 스키마에 count 필드 추가(§13A.10 L564–576) | **부분** — 기대값/ok/합성규칙 누락 |
| scope allowlist/read test(v1.8 §0 L47–48) | loader boundary + transitive read test(§13A.9 L535) | 반영 |
| 8 threads/affinity(v1.8 §0 L22–23) | 8 logical 명시(§12) / affinity·quota는 L36 언급뿐 | **부분** |
| near-threshold(v1.8 §0 L35–36) | 3 margin 분리, non-decisional(§7 L307) | 반영 |

## 9. 최종 판정

```text
Q1. conditional agree — call-graph 유도/dry-run/mismatch→NOT_EVALUABLE로 v1.8 순환 오류 제거 확인.
    dry-run 감사 기록만 보강 필요.
Q2. conditional agree — per-seed 스키마 승격 확인. Q unit artifact 경로 미선언, cap fallback 없음.
Q3. agree — never-materialized 3중 강제 + wall fallback 확인. 잔여(stdout/log, in-memory)는 선언됨.
Q4. conditional agree — R CE count 필드는 추가되었으나 기대값/ok/합성규칙/parallel 기록 경로 부재로
    R silent no-op 통과 가능. approval blocker.
Q5. conditional agree — 8 logical/산술/orchestrator 선행 commit 확인. affinity·quota는 선언만 있고
    메커니즘·기록 필드 없음.
Q6. agree — 3-margin 분리, PASS/EQUIVALENT 배타성 수학적 확인, INDETERMINATE 봉쇄 확인.

최종 판정: NARROW
Init: agree
D1: conditional agree
STOP/MDE: agree
Cohort: agree
Compute: conditional agree
Scope: agree
Must-fix (ranked):
  1. (blocker) r_mechanics_pass 합성 규칙 + R 기대 CE 계수 정의: expected_real_memory_ce_calls /
     wrong_donor_ce_calls 기대값(커밋된 R call graph, D1과 동일 counted-op)과 *_ok 플래그,
     wrong_donor_ce_calls > 0 단언을 §13A.10에 추가하라. 없으면 주 endpoint가 전혀 계산되지 않은 R도
     r_mechanics_pass:true로 통과한다. (§13A.10 L564–576)
  2. (blocker) R wall/parallel 기록 위치 선언: §5 L181의 nproc/threads_per_arm/parallel_wall_s/contention_ratio를
     저장할 artifact 경로를 §13에 추가하거나 r_mechanics_pass.json에 parallel 객체를 추가하라.
  3. (high) §13A.8 갱신: "Primary wrong-donor CE numerical path is first exercised at R"(L528)는
     §13A.1 L425의 Q wrong-donor CE finiteness/shape 검사와 모순된다. "finiteness/shape는 Q에서 최초,
     전체 수치 exercise는 R에서 최초"로 정정하라.
  4. (medium) CPU affinity/quota 메커니즘과 기록 필드를 명시하라(§0 item8 L36은 선언뿐). 예: per-arm core
     pinning, torch.set_num_threads(2), OMP/MKL env, parallel 객체에 quota 필드.
  5. (medium) Q 12 units의 artifact 경로를 §13에 선언하고, Q per-cell에 updates:int를 명시하라.
  6. (low) P/Q cap 초과 시 "repair or re-review; no silent extension" 문구를 D0/D1과 동일하게 추가하고
     (§12 L369–370), near-threshold margin 계산식을 R 리포트에 명시하라.
잘못된 전제:
  - §13A.8 L528 "first exercised at R"은 §13A.1 L425가 있는 현재 문서에서 거짓이다.
  - §0 item8 L36은 affinity/quota를 채택된 변경으로 서술하지만 실제로는 메커니즘이 정의되지 않은 미완성 항목이다.
  - §5 R L180 "final cap from D1 T_proj"은 §13A.7 L522의 "T_proj는 하한, 구속은 measured wall ≤96 min"과
    읽기에 따라 충돌할 수 있다 — §5 문구를 하한/구속 구분에 맞게 정정하라.
```

## 10. 판정 근거 요약 (decisive)

NARROW이다. v1.9는 v1.8/v1.0의 구조적 결함(D1 순환 기대값, per-seed 스키마 부재, signal materialization,
wall 무연장 원칙, scope read-path)을 실제로 제거했고, 신규 설계 모순은 없다. 그러나 승인을 막는 결함 2건이
남는다: (i) R mechanics 프레디킷의 기대값·합성 규칙 부재 — D1에는 있고 R에는 없어, 주 endpoint 미계산 R을
통과시킬 수 있는 비대칭(§13A.4 L485–487/L499 vs §13A.10 L564–576); (ii) affinity/quota가 전문에서 정의 없이
선언만 된 상태(§0 L36). 둘 다 텍스트 수정으로 해결되며 재설계는 불필요하다. must-fix 1–2 반영 후 별도 재검토
없이 승인 판정이 가능한 수준이다(신규 라운드 1회로 충분).

test 163 sealed, P1 unused, T5Gemma2 D-108 STOP, Phase 6 negative 종료, B0-B 미승인 — 모두 불변 확인.

EXIT:0