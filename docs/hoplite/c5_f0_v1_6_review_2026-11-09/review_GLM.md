# C5 F0 v1.6 — GLM Independent Review (New Block Round 6/10)

- 작성일: 2026-11-10
- 모델: `z-ai/glm-5.3-flash`
- 대상: `docs/plan_c5_f0_v1_6_2026-11-09.md`
- 성격: **신규 독립 검토** — v1.5 스레드/결론 상속 없음 (v1.5 = GLM CONTINUE / DS NARROW / Luna NARROW, archive 완료)
- 파일 수정: 이 리포트 1개뿐. 학습/평가, test 163/P1, subagent 없음.

## 0. Reviewed HEAD 및 동기화

```text
git fetch origin   : ok (FETCH_HEAD main)
git pull --ff-only origin main : "Already up to date."
reviewed HEAD      : 1b6e4c52932a557e4f47484b456bb55cbdf91b12
HEAD subject       : docs: add C5 F0 v1.6 review request (2026-11-10 10:54:41 +0900)
```

읽은 파일: `docs/plan_c5_f0_v1_6_2026-11-09.md` 전체, `docs/plan_c5_f0_v1_5_2026-11-09.md`,
`reports/EXTERNAL_REVIEW_C5_F0_V1_6_2026-11-09.md`, `reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`,
`reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`,
`reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md` (§2.5.4–2.5.7, §2.7, §10, §11.5–11.6),
`runner/c5_pm_phase6.py` (`arm_spec`/`build_arm`/`eval_arm_d1`/`run_d0`), `runner/c5_mt5_lora_b0.py:318–326` (`donors_for`),
`runner/c5_pm_stats.py:1–60`, `runner/c5_pm_labels.py:54–90` (`l_predicate`).

## 0.1 Verbatim paired E01−E11

`docs/plan_c5_f0_v1_6_2026-11-09.md` §6.3 Primary contrast, 그대로:

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

§2: "Primary: **E01 vs E11** (LoRA initialization matched)." / §6.2: "delta_c(s,d) = mean_donor( CE_wrong_donor - CE_real )" / §6.3: "`D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary."

## 1. Q1 — Wrong-donor / P / Q / init hashes

**판정: agree**

근거:

- v1.5의 wrong-donor 모순이 해소되었다. §0 변경 1, §5 D1("D1 **no signal persistence**"), §13A.8이 모두 "D1은 wrong-donor CE를 호출하지 않음; `wrong_donor_ce_calls:0` absolute / unit-test only / R-first accepted"로 일치한다. R에서 wrong-donor CE 경로가 처음 실행되는 것이 명시적으로 accept되었고, 완화책(unit-test `donors_for`/crop 1 doc, 값 미저장)이 §13A.8에 있다.
- 소스 검증: `donors_for`(`runner/c5_mt5_lora_b0.py:318–326`)는 EG2 h 길이 기반 deterministic length-nearest이므로 F0의 4 cell 전부 동일 donor map을 얻는다(§6.1 "donor sets identical" 요구와 구조적으로 일치). R에서 처음 실행될 경로는 `eval_arm_d1`(`runner/c5_pm_phase6.py:429–470`)의 wrong-donor CE 루프이며, v1.6은 이를 재사용하지 않고 `c5_pm_f0_mechanics.py`를 새로 만든다(§11).
- Stage P/Q가 v1.0 DS-5(3-seed init audit 부재)를 닫는다: P init-only 12 loads(§13A.1), Q per-R-seed 1-update 12 units ≤15 min, `pre_r_seed_audit_pass[seed]` 필수, Q 실패 seed 배제 + 잔여 ≥2 seeds(§5 Stage R).
- `init_hashes.json` append-only per `{stage,seed,cell}`, no overwrite(§0 변경 6, §13A.1) — P 기록이 D0에 덮어쓰이지 않는다.
- step_seed golden table **재계산 검증 완료**: formula `(seed ^ ((0x9E3779B9 * (step+1)) & 0xffffffff)) & 0xffffffff`로 12개 벡터 전부 일치 —
  20261108 → `0x9f02514d, 0x3d5bdb86, 0xdb9345df`; 20261109 → `0x9f02514c, 0x3d5bdb87, 0xdb9345de`; 20261110 → `0x9f02514f, 0x3d5bdb84, 0xdb9345dd`; 20261111 → `0x9f02514e, 0x3d5bdb85, 0xdb9345dc`. §4 표기와 정확히 일치한다.

다음 단계:

1. Stage R이 `r/init_hashes.json`을 기록하도록 되어 있으나(§13), **R의 fresh-load init hash == P가 기록한 동일 `{seed,cell}` init hash**라는 동등성 assertion이 어디에도 요구되지 않는다. Q는 P 시점 로드를 인증할 뿐 R이 실제로 쓰는 로드를 인증하지 않는다. 구현 시 r↔d0 hash equality assertion을 추가할 것 (must-fix 1).
2. 그 외에는 변경 불요.

## 2. Q2 — D1 mechanics_pass / flags / telemetry / seal

**판정: agree**

근거:

- §13A.4 `mechanics_pass` predicate: `partial==false AND error==null AND checkpoint_absent==true AND all assertions==true AND phase7_records==0 AND wrong_donor_ce_calls==0 AND donor_map_loads==0 AND labels_computed==false AND not_a_result==true AND test_split_used==false AND p1_used==false AND d1_signal_read==false` — 5개 seal flag가 모두 AND로 들어가 v1.5 must-fix 2를 충족한다.
- 신규 `cells_ok / updates_total_ok / e00_steps_zero` + top-level `updates_total:int`(§0 변경 3)는 §5 D1 assertions 1–3(cells==4, per-cell 1 update/total 3, E00 `optimizer_steps==0`)을 schema 차원에서 강제한다. `assertions` 18키가 §5 D1 항목 1–10을 전부 매핑함을 확인했다(예: step0_docs_ok/final_docs_ok↔4, m_count_ok↔5, generation_count_ok↔7, ce_finite_ok↔8, phase6_io_zero↔§4 I/O assert).
- `timings / provenance / parallel` literal object 추가(§0 변경 4)로 T_proj audit이 가능해졌다 — v1.0 DS-7, Luna compute-provenance 지적의 반영.
- Seal 잔여 우회 경로 평가: (a) digest-only checkpoint + 삭제 + `checkpoint_absent` + filesystem negative test(§5 D1, §13A.4)는 "checkpoint를 밖에서 재로드해 signal oracle로 쓰는" 경로를 artifact 수준에서 차단한다. 남는 것은 **committed orchestrator가 실제 실행 경로라는 보장** 문제인데, 이는 Phase 6 MF-1(실행 코드 미커밋)과 동일 클래스이며 v1.6은 `runner/c5_pm_f0*.py` commit + clean-tree SHA + `code_commit/command/input_sha256` 기록(§11 Provenance, §13A.4 provenance)으로 대응한다. (b) `real_memory_ce_calls:int`는 required 값 assertion이 없어 eval을 생략한 evaluator도 count-only artifact를 남길 수 있으나, `m_count_ok`/`generation_count_ok`/`n_docs_*`가 상한을 걸어 실질 리스크는 낮다. (c) `checkpoint_digests`의 E00이 `null`인지는 미규정(사소).
- Crash path(`partial:true`+`error`, checkpoint 삭제, 다른 파일 없음)와 writer/consumer allowlist도 규정되어 있다(§13A.4).

다음 단계: 1) `checkpoint_digests` E00=null 규정 1줄 추가(사소), 2) orchestrator commit을 D0 stage approval의 확인 항목으로 유지.

## 3. Q3 — STOP / MDE / near-threshold

**판정: agree**

근거:

- §7 4-state table은 priority 1–4 순서 평가로 상호배타·전체포괄이다. `PASS_POSITIVE`는 `CI_D.lower > +.05`를 요구하므로 `EQUIVALENT`(§7: `CI_D.lower >= -.05 AND CI_D.upper <= +.05`)와 논리적으로 겹칠 수 없다(lower > +.05이면 upper ≤ +.05 불가). `EQUIVALENT > harm > benefit` precedence로 다중 라벨 충돌도 해소된다.
- `ALL_FAIL`이 정확히 E01/E11 × copy/full로 고정되고(§7), E00/E10 배제, `ROUTE_STOP`가 cell-level `FAIL(c,e)`를 쓴다는 명시 — v1.5 변경 2의 cell CI 소비 규정(§6.4 "no re-bootstrap at decision time")과 정합한다. `ALL_FAIL`+benefit이 `adapter_benefit` STOP이 되는 것은 route-only 정의(§8, §14)와 일관되고 타당하다.
- MDE 재표기(§12): `.019170 = .037573/1.96`는 Phase 6 `labels.json L_COPY_SIGNAL.paired`의 **F−L planning proxy**이며, 50% MDE .0376 / 80% MDE .0537 / `.104` gate mean / `.0876` 50% boundary는 "none is an observed F0 mean"으로 명시되었다. 산술 검증: .037573/1.96=.019170, .019170×2.8≈.0537, .05+.0376=.0876 — 자기정합. v1.0 DS-3의 "single-arm SE를 paired로 오독" 문제가 해소되었다. 실제 지배량은 realized `CI_D`이고 donor graph 조건부(§6.5)다.
- Near-threshold ROUTE_STOP reporting(§0 변경 8, §7): mean/CI/half-width 보고 요구는 적절. 다만 "boundary"가 어느 경계인지(0 vs ±.05) 미규정 — must-fix 3.

다음 단계: 1) near-threshold 경계 정의 명시, 2) 그 외 변경 불요.

## 4. Q4 — Cohort / cell CI / donor conditional

**판정: agree**

근거:

- §6.1: 15 common = frozen preflight `common_ids`, presence check(15 docs × 4 cells × 3 seeds), per-doc 정확히 5 donors + all-cell donor set 동일성(위 Q1의 `donors_for` 소스 확인으로 구조적으로 성립), `eval_arm_d1`의 silent drop(`if not real_copy: continue`, `runner/c5_pm_phase6.py:470`)에 대해 "missing doc = NOT_EVALUABLE, never a smaller cohort"로 명시 — 실제 코드 행동과 정확히 대응한다.
- §6.2–6.4: per-cell copy/full delta, doc-level seed average, `bootstrap_paired_v2(n_boot=10000, seed=20261109, percentile linear)` + realized n_boot/seed assertion, `CI.lower` = 2.5th percentile. `runner/c5_pm_stats.py:29–31`는 `n_boot/seed`를 파라미터로 받으므로 override가 가능하고, plan의 realized-value assertion이 올바른 통제다.
- `l_predicate` 금지(§6.3)는 소스로 정당하다: `runner/c5_pm_labels.py:66–67`이 `bootstrap_paired_v2(..., 1000, 20261109)`로 hardcode하고 있어 F0가 이를 쓰면 n_boot 10000이 silent revert 된다.
- §6.5: `EQUIVALENT`는 practical-equivalence label일 뿐이고, n=15에서 expected branch undetermined, P−PA(+3.065, 14/15)는 PASS-direction context로만 표기, `±.0124` 등가폐 mean range 주장 없음 — v1.0 DS-3/DS-2 반영이 유지된다. CI_D의 donor-graph 조건부 명시(§12, §6.5)로 donor conditional 요구도 충족.
- 20-doc 일반화 금지 + 20-doc descriptive 병기(§6.1) — length-selected cohort 문제의 정합적 처리.

다음 단계: F0 구현에서 bootstrap 호출부에 realized n_boot/seed assertion을 유지하고 새 default를 추가하지 말 것(이미 plan에 있음 — 변경 불요).

## 5. Q5 — Compute 16-core / setup / contention

**판정: conditional agree**

근거:

- §12 테이블 자체는 정합한다: P 12 loads ≤10 min, Q 12 updates ≤15 min, D0 ≤15 min provisional(측정 기반 final cap), D1 3 updates ≤25 min(Phase 6 D-156 병렬 측정 1,180.6s ≈ 19.7 min이 상한 여유를 지지), R 900 updates ≤96 min(Phase 6 wall anchor 4,939.884s ≈ 82.3 min < 96, 그리고 `T_proj_R = setup_s_effective + 3 × slowest-arm 9-term sum` 규정). 총 updates 900 = 3 trained cells × 100 × 3 seeds — §5 Stage R과 일치.
- `setup_wall_s` vs `sum_process_setup_s` 분리 + `setup_s_effective = setup_wall_s`로 이중 계산 제거(§0 변경 7), `contention_ratio = parallel_wall_s / sum(per_arm_phase_s)` 보고 전용, cap은 wall — v1.0 DS-7 해소.
- `nproc < 16 AND threads_per_arm > 1` hard abort + 4-vCPU workspace 배제(§13A.7) — 16-core 조건이 명시적으로 실행 가능성 요구사항으로 자리했다. orchestrator commit 선행(§11 Provenance, §13A.7) — v1.0 DS-4 해소.
- **조건(사소한 불일치 2건)**:
  1. §0 변경 7 "16 cores, **1 thread/arm**" vs §12 테이블 "3/arm, 4 arms = **12 logical**" vs §5 D1 "4 parallel arm processes × **3 threads/arm**" — 표기 충돌. "1 thread/arm"이 worker당 `torch.set_num_threads(1)`을 뜻한다면 그렇게 명시해야 한다. 기록되는 `nproc`/`threads_per_arm`이 D1에서 실측으로 정리해 주지만, prereg 문구로는 모호하다.
  2. `T_proj_f0`의 9-term sum에서 E00(eval-only, 0 update)의 `t_train`/`t_step100_eval` 처리와 slowest-arm 선정 규칙(§11 "E00/E10/E01/E11 aggregation" vs §12 "slowest arm")이 미규정이다.

다음 단계: 1) threads 표기 정리(must-fix 2), 2) E00 term=0 + slowest arm 규칙 명시(must-fix 4). 둘 다 문구 수정이며 실행 가능성을 바꾸지 않는다.

## 6. Q6 — Scope / route-only

**판정: agree**

근거:

- §14 Non-goals가 v1.0 DS-8 전부를 흡수했다: ROUTE_STOP은 "route as configured"(§8의 10개 요소)만 중단, EG2 track 중단·B0-B 구제·H3 자동 개시 없음(§10). descriptive contrast(E00/E10/E01 vs E00) 인과 금지. **lost controls**(MF-4 zero/permuted null, 1-seed signal gate)가 의도적 out-of-scope로 명시되고 "F0 cannot claim they were replaced"라고 선언 — 사후 구제 경로를 차단한다.
- §9: M_PASS ≠ donor-specific content-use evidence, M은 F0 primary gate 아님 — Phase 6 cause report §1(M table, L −0.1135 / P−PA +3.065) 및 results synthesis MF-5와 정합.
- H3 완전 제거(§10): "F0 results do not automatically launch H3", H3 별도 prereg — negative F0가 H3로 구제되거나 positive F0가 H3를 자동 개시하지 않는 경계가 문서 레벨에서 충분하다.
- `adapter-as-configured` 인과 요소 정의(§4 마지막 bullet)와 E01 vs E10 "not clean causal" 표기(§2)로 association-only 주장의 경계가 명확하다.

다음 단계: 없음 (scope는 v1.6에서 완결).

## 7. 최종 판정

```text
최종 판정: CONTINUE
Init:        P/Q 분리 + append-only init_hashes + golden table(재계산 일치) 충분.
             R↔d0 init hash equality assertion 1건 구현 시 추가.
D1:          mechanics_pass + 5 seal flags + literal schema + telemetry 충분.
             잔여 우회는 orchestrator provenance(MF-1 클래스)로 commit으로 통제.
STOP/MDE:    4-state taxonomy 정합, MDE planning-proxy 재표기 해소,
             near-threshold 경계 정의만 보강.
Cohort:      15 common frozen + 5 donors all-cell + n_boot=10000 + l_predicate 금지 충분.
Compute:     16-core hard abort + setup_wall/contention 분리 충분.
             threads 표기 모호성 1건 정리 필요.
Scope:       route-only + H3 제외 + lost controls 선언 충분.
잘못된 전제: 없음. Q1–Q6 어느 것도 허위 전제 위에 있지 않다;
             유일한 전제 수준 유의점(MDE 수치는 planning proxy)은 v1.6 §12가 이미 자기 규정하고 있다.
```

**승인 blocker: 없음.** v1.5 must-fix(1 CONTINUE / 2 NARROW 유발 항목)는 전부 반영되었고, 잔여 지적은 문구/구현 시 검증 항목이다.

## 8. Must-fix (ranked)

1. **R↔P init hash 동등성 assertion**: Stage R decision이 `r/init_hashes.json`을 소비하기 전에, R fresh-load의 init hashes가 `d0/init_hashes.json`의 동일 `{stage=P,seed,cell}` 기록과 전부 일치함을 assert하도록 §13A.1/§13에 추가. (Q gate가 인증하는 로드와 R이 쓰는 로드의 연결 보장; 구현 비용 극소, D0 stage approval 시점 확인 가능)
2. **threads 표기 정리**: §0 변경 7의 "1 thread/arm"을 "worker process당 1 CPU thread (`torch.set_num_threads(1)`), arm당 3 worker"로 명확화하거나 §12 테이블과 일치시킬 것. 기록 필드 `nproc`/`threads_per_arm`은 유지.
3. **near-threshold "boundary" 정의**: §7 near-threshold 조건의 경계를 reason별로 고정 — `no_signal_equivalent` → ±.05, `adapter_harm`/`adapter_benefit` → 0.
4. **T_proj_f0 E00 term 규정**: E00은 `t_train=0`, `t_step100_eval=0`(step0=final 단일 eval)로 처리하고 slowest-arm 선정을 E10/E01/E11(및 E00 포함 시 0-term 처리 명시)로 규정.

1–4는 모두 신규 3-AI 라운드 없이 D0 stage approval 시점 확인 가능한 문서/구현 보강이다. v1.6 설계 자체는 승인 가능 상태다.