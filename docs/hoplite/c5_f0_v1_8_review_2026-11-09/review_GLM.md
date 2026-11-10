# C5 F0 v1.8 — Independent Review (GLM 5.3 Flash, New Block Round 8/10)

- 검토일: 2026-11-09 기준 문서, 작성 2026-11-10
- reviewed HEAD: **`ac1ee40da32427d452bd5d89bb339f034b2b7c9c`** ("docs: add C5 F0 v1.8 review request"), `git fetch origin` + `git pull --ff-only origin main` = Already up to date
- 대상: `docs/plan_c5_f0_v1_8_2026-11-09.md` (DRAFT v1.8, 미승인·미실행)
- 참조: `docs/plan_c5_f0_v1_7_2026-11-09.md` (SUPERSEDED), `reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py`
- 새 독립 검토. v1.7 결론(3/3 NARROW) 상속 없음. 학습/평가·test163/P1·subagent 없음. 본 파일 외 수정 없음.

## 0. Verbatim paired E01−E11 (plan §6.3 Primary contrast, lines 227–238, 무변경 인용)

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
- `D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary.
- Copy primary; full secondary.
- **CI_D is doc-level only.** Seed-level `D_s` is a gate/descriptor, not a doc-level interval.
- `PASS_POSITIVE` requires the paired contrast, E01 absolute copy signal, and seed replication; this is not a per-cell significance conjunction.

## Q1. P/Q/R gates/schema/hash — 충분한가?

- 판정: **conditional**
- 근거:
  - Fail-closed 골격은 전달됨. §13A.10: `pre_r_init_audit_pass` = 3 seeds × 4 cells + canonical hashes + `p_r_hash_equal:true` + KAT referenced, "Missing/duplicate/malformed/stale/partial → false". Q: "Any false → `NOT_EVALUABLE`; no R" (§13A.1). R: `r_mechanics_pass` 필드 수준 완비 (§13A.10: seeds:3, cells:4, updates_total:900, m_records:1440, phase7_records:7200, provenance_ok).
  - Hash 층은 견고: train20/val20/common ordered sha256 + sorted vs preflight order 분리 기록 + `post_step0_rng_state_sha256` `device=cpu` (§4), canonical serialization grammar + dtype whitelist + 고정폭 LE + KAT fixture(2 tensors + 1 scalar) D0 전 commit (§13A.2), `step_seed` golden table(§4: `(20261108,0)=0x9f02514d` 등 6 seed 벡터).
  - **결함 1 — Q per-seed schema 산술 오류**: §13A.10 `q/q_seed_audit/{seed}.json`는 `units:12`, `trained_updates:9`. 그러나 §13A.1에서 Q = "3 seeds × 4 cells = 12 units, 9 trained updates"는 **전체 합계**이고, per-seed 파일은 4 units / 3 trained updates여야 한다. per-seed 파일에 전체 합계 12/9를 기록하면 units 필드의 의미가 모호해지고, `units==12`를 per-seed로 검증하는 fail-closed validator는 영구 실패(전체 NOT_EVALUABLE deadlock), 4를 기록하는 writer는 schema와 불일치.
  - **결함 2 — `p_r_hash_equal` 순환**: §13 "`pre_r_init_audit_pass:true` required before `r/` creation"인데 `pre_r_init_audit_pass`는 `p_r_hash_equal:true`(R 시점 init hash와 P hash 비교, §13A.10)를 요구. R의 init hash는 `r/init_hashes.json`이 생성된 후에야 존재하므로, "r/ creation"이 무엇을 가리키는지(r/ 결과물 vs r/init_hashes.json) 명시 없이는 순환. R 시작 시 R init hash 기록 → audit 확정 → 학습 write 허용 순서를 규정해야 함.
  - 보통: `p_r_hash_equal` 검증 시점은 R 시작뿐이라 P 단계에서는 결정 불가 — 이는 구조상 불가피하나 문서에 명시 없음.
- 다음 단계: (1) per-seed Q schema를 `units:4, trained_updates:3`(파일당)로 수정하거나 `units_total_all_seeds` 별도 필드로 분리. (2) `p_r_hash_equal` 산출 순서 규정(§13 게이트 문구를 "r/ 학습 결과물 생성 전"으로 정밀화).

## Q2. D1 real CE/seal/telemetry — 충분한가?

- 판정: **conditional** (real_memory_ce_calls 기대값 정의가 실행 불가 수준의 모순 — 승인 blocker)
- 근거:
  - **결함 3 — expected count formula가 eval scope와 충돌**: §13A.4 "Expected `real_memory_ce_calls` = E00 step0 1 + E10/E01/E11 step0 1 each + E10/E01/E11 final donor-crop **15 docs × 5 donors** each + M CE count from report". 그러나 §5 Stage D1 assertion 4는 "`n_docs_step0 == 20` and `n_docs_final == 20`", §3 Definitions는 "Signal: donor-crop K=min(len(real),len(donor)), **20 val docs**, 5 donors", §6.1은 "20 val docs are descriptive"라며 per-doc eval을 20 docs로 규정. final donor-crop이 20 docs면 실제 real CE 호출은 cell당 20×5=100회이고 formula의 15×5=75회는 과소 계산 → `real_memory_ce_calls_ok:false` → `mechanics_pass:false`(§13A.4 mechanics_pass 정의에 `real_memory_ce_calls_ok==true` 포함) → **D1이 구조적으로 통과 불가**. 15-doc 제한이 의도라면 `n_docs_final==20` 및 §3과 정면 모순.
  - 같은 formula의 "M CE count from report"는 매핑 미정의(M records 480 ≠ CE 호출 수 보장; M_POS_MEAN/M_NORM × endpoint × doc 구조 명시 필요), generation CE(20/cell, 총 80 — §5 D1 assertion 7; prereg §2.5.6 "generation is telemetry only")의 real_memory_ce_calls 포함 여부도 미규정. "exact integer frozen"이 있으므로 정합만 하면 안전하지만 현재 정의로는 정합 불가.
  - Seal은 강함: checkpoint digest 후 삭제 + `checkpoint_absent==true` + loading 금지(§5 D1 assertion 9), "D1 checkpoints are digest-only … loading a D1 checkpoint is forbidden … stronger than a seal: values are never materialized"(§5), exact-key allowlist + "No `per_doc`, `final`, `delta_*`"(§13A.4), gate negative test "any `d1_report.json`/`per_doc`/`delta_*` input exits non-zero"(§5), filesystem tests(§13A.4), `wrong_donor_ce_calls:0` absolute(§13A.8), stdout/log CE 금지(§13), crash path partial+error+checkpoint 삭제(§13A.4).
  - 잔여 우회: `error:string|null`에 CE 수치 유출 가능 — error 문자열 내 수치 금지 문구 없음. `timings`/`parallel` float를 이용한 은닉은 allowlist가 shape을 제한하므로 허용 가능 수준.
  - Telemetry: §13A.4 provenance{code_commit, command, input_sha256, clean_tree} + parallel{nproc, threads_per_arm, parallel_wall_s, contention_ratio} 기록. v1.0 DS-4(실행 코드 provenance)는 §11 "must be committed at a recorded SHA with clean tree before D0"로 반영. `parallel_wall_s`는 self-reported telemetry라는 본질은 유지되나 R binding이 measured wall(§12)이므로 허용.
- 다음 단계: (1) final donor-crop scope를 15/20 중 하나로 확정하고 formula·`n_docs_final`·§3을 일치. (2) M CE 매핑과 generation CE 포함 여부를 정수로 규정. (3) error 문자열 수치 금지 추가.

## Q3. STOP/MDE/near-threshold — 정합하는가?

- 판정: **agree**
- 근거:
  - Taxonomy(§7)는 4-state(1 NOT_EVALUABLE > 2 PASS_POSITIVE > 3 ROUTE_STOP > 4 INDETERMINATE)로 상호배타·전체 포괄. PASS_POSITIVE는 `SIGNAL(E01,copy)`를 요구하고 ALL_FAIL은 `FAIL(E01,copy)`를 요구하므로 state 2/3 동시 충족 불가. PASS의 `CI_D.lower > +.05`는 EQUIVALENT(`CI_D.lower >= -.05 AND CI_D.upper <= +.05`)와 논리적으로 겹침 없음(upper>+.05 보장). Precedence `EQUIVALENT > harm > benefit`(§7)로 harm/benefit 정의(`NOT EQUIVALENT` 포함)와 일관.
  - Near-threshold(v1.8 변경 4): cell-level `SIGNAL` 통계(mean, boundary b∈{.05,0}, h=(CI.upper−CI.lower)/2, near if |mean−b|≤h)로 ALL_FAIL 구동 통계 기준 진단, paired `mean_D/CI_D`는 "paired-contrast diagnostic"으로 relabel — v1.0 DS-3(cell gate vs paired 혼동) 재발 방지 설계로 정합. b=0 근방은 percentile CI의 비대칭으로 근사 진단이나 diagnostic-only라 허용.
  - MDE(§12): `.019170 = .037573/1.96` (Phase 6 `labels.json L_COPY_SIGNAL.paired`, F−L planning proxy, "not a validated E01−E11 SE" 명시), 50% MDE .0376 = 1.96×SE, 80% MDE .0537 ≈ (1.96+0.84)×SE — 산술 검산 일치. `.104`/`.0876` 제거("untraceable") + `.037573`/`.019170` verified proxy 유지는 v1.0 DS-3의 요구(단일-arm SE .0594 기반 수치 철회)를 충실히 반영.
  - 정합성 경고(차단 아님): P−PA per-doc SD 2.405(§12) 체감의 E01−E11 변동이라면 CI_D half-width ≈ t(.975,14)×2.405/√15 ≈ 1.3 수준 → EQUIVALENT 사실상 도달 불가, PASS도 낮음 → INDETERMINATE/ROUTE_STOP 지배. §6.5 "expected branch is undetermined; PASS and ROUTE_STOP are both live"와 "no `±.0124` equivalence mean range"는 이를 정직하게 서술하나, `no_signal_equivalent` reason이 사실상 발생하지 않을 것임을 리포트 템플릿에 반영할 것.
- 다음 단계: (1) 리포트 양식에 "EQUIVALENT 도달 가능성 낮음(분산 근거)" 사전 고지 추가. (2) 근사가 아닌 percentile 기반 near 판정은 diagnostic로 유지(변경 불요).

## Q4. Cohort/cell CI/donor conditional — 충분한가?

- 판정: **agree**
- 근거:
  - §6.1: primary estimand = "15 length-eligible docs + fixed donor graph", "15 common = frozen preflight `common_ids`; it is length-selected (5 of 20 excluded at K=753)" 명시 + "Generalization to the 20-doc val population is forbidden; report 20-doc F/L descriptively" — v1.0 DS-2(length-selected cohort) 요구를 정확히 소화.
  - Donor: "Each doc must have exactly 5 donors; donor sets identical for E00/E10/E01/E11 per doc"(§6.1) + `donors_for(val20, cache)` sha256 기록 + leave-one-donor-out sensitivity + "Donor reuse from val docs is declared" — conditional estimand의 민감도 경계 완비.
  - Cell CI(§6.4): 15 docs × 5 donors, seed mean(20261108/09/10), `bootstrap_paired_v2(n_boot=10000, seed=20261109, percentile linear)`, `CI.lower` = 2.5th percentile, realized n_boot/seed assert, "no re-bootstrap at decision time" — 결정 시점 재샘플링 차단. `n_boot=10000`은 §6.3 "explicit override of frozen N_BOOT=1000" + `assert not used_l_predicate` — v1.0 DS-6(l_predicate 하드코딩 1000) 재발 차단.
  - Missing data(§6.6): "No 15→14 substitution; no '2 of available'", "If <15 or <3 seeds: `NOT_EVALUABLE`" + §6.1 "`eval_arm_d1` silently drops non-copyable docs; a missing doc means `NOT_EVALUABLE`, never a smaller cohort" — silent-drop 위험을 predicate으로 전환.
- 다음 단계: (1) LOO donor sensitivity의 보고 범위(range) 형식을 리포트 스키마에 고정. (2) 20-doc descriptive 표를 secondary로 한정하는 문구 유지.

## Q5. Compute 2/arm/caps/lower-bound — 충분한가?

- 판정: **conditional**
- 근거:
  - v1.7 must-fix의 정수(ratio)·측정 기반 전환은 반영됨: §12 "Phase 6 D1 and registered wall values (1,180.6s, 4,939.884s) are estimates, not measurements; Final cap requires measured `parallel_wall_s`", "no 1.316 multiplier", D1 cap 25 min provisional, R 96 min binding, "Hard abort if `nproc < 16` or `T_proj_R > 96 min`", `contention_ratio = parallel_wall_s / sum(per_arm_phase_s)` 기록.
  - T_proj 하한 명시(v1.8 변경 1): §13A.7 "D1-derived T_proj is a lower bound (R-only replay terms absent); R binding gate is measured wall ≤96 min" — D1에는 phase7 7,200 record·primary replay가 없으므로(§5 D1 assertion 6: "phase7 records == 0 (D1 does not write phase7; Stage R only)") 하한 성립. §12 9-term 목록(100*t_train … t_overhead)과 `T_proj_R = setup_s_effective + 3 × sum(slowest arm)` + "no double count" 규정은 v1.0 DS-7(Phase 6 t_proj 용어 비호환) 해소.
  - **결함 4 — §12 D0 row `1/arm`이 normative와 모순**: v1.8 변경 1은 "Normative host 16 cores, 2 threads/arm, 8 worker threads"인데 §12 테이블 D0만 "1/arm". D0을 1/arm로 두면 provisional cap 산출의 contention 모델이 D1/R(2/arm)과 불일치하고, v1.7이 제거한 1/arm 혼용이 D0에 잔존하는 형태.
  - **결함 5 — P/Q cap 초과 시 규정 부재**: P ≤10 min, Q ≤15 min(§12, §13A.1)은 "separate"라고만 명시; D0에는 "If measured >15 min, repair first"(§5)가 있으나 P/Q에는 초과 시 repair/NOT_EVALUABLE 중 무엇인지 없음.
  - 산술 검산: R = 900 updates(3 seeds × 3 trained cells × 100), M 1,440(4 cells × 3 seeds × 120), phase7 7,200, generation 240(§5 Stage R) — §13A.10 `r_mechanics_pass.json`과 일치. P = 12 loads(3 seeds × 4 cells), Q = 12 units / 9 trained updates(§13A.1) 일치.
- 다음 단계: (1) D0을 2/arm로 통일하거나 예외 근거 명시. (2) P/Q cap 초과 시 fail-closed 규정 추가.

## Q6. Scope/negative reads — 충분한가?

- 판정: **agree** (소규모 정합화 1건)
- 근거:
  - §14 Non-goals는 포괄: association-only("does not identify an architecture-only bottleneck"), ROUTE_STOP route-only("stops only the route as configured … does not stop the EG2 track, does not rescue B0-B, and does not launch H3"), descriptive contrasts, "lost controls: the earlier MF-4 zero/permuted null and 1-seed signal gate are intentionally out of scope; F0 cannot claim they were replaced", "M_PASS is not donor-specific content-use evidence" — Phase 6 cause report MF-4/MF-5의 축소 요구가 그대로 유지됨.
  - H3(§10): "No H3 arm, trigger, rank, identity, null, or donor-discrimination endpoint is registered here", "F0 results do not automatically launch H3", 별도 prereg — v1.7 질문 Q6에 대한 답으로 타당(제거 사유까지 명시: H3 상세가 F0 승인을 막는 것과 음성 F0이 H3로 구제되는 것 모두 방지).
  - Negative reads(v1.8 변경 10): §13A.7 "test163/P1 read-path negative tests: direct open attempts must fail; flags alone are not evidence" — v1.0 DS/Luna의 "attestation은 proof가 아니다" 지적을 read-path로 강화. §13A.6 forbidden-read probe + Phase 6 protected paths(`checkpoints/**`, `registered/checkpoints/**`, `d1/checkpoints/**`) 전 `open`/`torch.load`/`numpy.load` 감사 + "count of protected-path opens must be 0".
  - **결함 6 — probe와 감사 카운트 충돌**: §13A.6 "a probe open of one protected path must raise/flag and be recorded"인데 감사 대상이 "every `open`, `torch.load`, `numpy.load` path under F0 audit"이면, 감사 프로세스 내 probe 실행 시 protected-path opens = 1이 되어 "must be 0"과 충돌. probe는 감사 runner 프로세스 외부(테스트 코드)에서 실행함을 명시해야 함.
  - 13A.1 "Q also runs donor-crop/wrong-donor CE finiteness + shape check" vs 13A.8 "Primary wrong-donor CE numerical path is first exercised at R; Q checks finiteness/shape only" — Q가 CE를 계산하면 첫 수치 exercise가 Q가 되어 13A.8과 모순. Q의 `wrong_donor_finite`는 CE 없이 tensor finiteness/shape만 검사함을 문구로 확정 필요(결함 3과 별개, 사소).
- 다음 단계: (1) probe를 감사 프로세스 밖으로 명시. (2) Q wrong-donor 검사의 "no CE computation" 문구 확정.

## 최종 판정

```text
최종 판정: NARROW

Init:      P/Q/R fail-closed 골격·hash 층(KAT, ordered IDs, device=cpu)은 충분하나
           Q per-seed units/trained_updates 산술(12/9 vs 4/3)과 p_r_hash_equal
           순환(§13 게이트 문구)을 수정해야 함 (결함 1, 2)
D1:        seal은 전단계 대비 강화됨(digest-only, exact-key, negative tests,
           wrong_donor_ce_calls:0). 단 real_memory_ce_calls 기대값 formula가
           15 docs(§13A.4) vs 20 docs(§5 assert 4, §3)로 충돌 — fail-closed가
           오히려 D1을 구조적으로 통과 불가로 만듦 (결함 3, blocker)
STOP/MDE:  4-state taxonomy 상호배타·전체 포괄, PASS/EQUIVALENT 비중복, near-threshold
           cell-level relabel 정합, MDE 산술 검산 일치(.019170/.0376/.0537),
           .104/.0876 제거 적정. EQUIVALENT 도달성 경고만 리포트 반영 (agree)
Cohort:    15 length-eligible + fixed donor graph conditional estimand, LOO sensitivity,
           n_boot=10000 override + l_predicate 금지, missing data fail-closed (agree)
Compute:   2/arm anchor, provisional→binding measured wall, T_proj lower bound 정확,
           900/1440/7200 검산 일치. §12 D0 1/arm 모순과 P/Q cap 규정 보완 필요
           (결함 4, 5)
Scope:     §14 non-goals 포괄, H3 완전 분리, test163/P1 read-path negative tests.
           protected-path probe의 감사 프로세스 외부 실행 명시만 필요 (결함 6)

Must-fix (ranked):
1. [blocker] real_memory_ce_calls 기대값: §13A.4 formula "final donor-crop 15 docs × 5
   donors"를 §5 Stage D1 assertion 4 `n_docs_final == 20` / §3 "20 val docs"와 정합.
   final donor-crop scope를 확정하고(15 또는 20), "M CE count from report"의
   record→CE 호출 매핑과 generation CE(80회) 포함 여부를 정수로 규정한 뒤 freeze.
   미해결 시 D1 mechanics_pass는 항상 false → 전체 NOT_EVALUABLE.
2. [high] Q per-seed schema(§13A.10): `units:12`, `trained_updates:9`는 3-seed 총합.
   per-seed 파일은 units:4 / trained_updates:3으로 수정하거나 필드 의미를 분리.
3. [high] p_r_hash_equal 순환(§13 vs §13A.10): R 시작 시 r/init_hashes.json 기록 →
   audit 확정 → 학습 출력 허용 순서를 규정하고 "before r/ creation" 문구를
   "before any R training output"으로 정밀화.
4. [medium] §12 D0 row 1/arm → normative 2/arm 통일 또는 예외 근거 명시.
5. [medium] §13A.1 "wrong-donor CE finiteness" 문구를 §13A.8과 정합: Q는 CE를
   계산하지 않고 tensor finiteness/shape만 검사(첫 수치 exercise는 R).
6. [low] protected-path negative probe를 감사 runner 프로세스 외부 실행으로 명시;
   P/Q cap 초과 시 fail-closed 규정; D1/Q error 문자열 내 CE 수치 금지.

잘못된 전제:
- 요청서 "normative 16 cores, 2/arm"는 §12 D0 row(1/arm)와 불일치 — normative는
  D0에 적용되지 않음(결함 4).
- 요청서 변경 요약 "real_memory_ce_calls expected count + flag"가 완결된 것처럼
  서술되었으나 formula 자체가 eval scope와 모순 — flag 존재가 아니라 정합성이
  승인 조건(결함 3).
- "Wrong-donor residual risk explicit"는 달성됨(§13A.8), 그러나 §13A.1 문구가
  Q에서 CE를 계산하는 것처럼 읽히는 잔여 모호성 존재(결함 5).
```

## 판정 근거 요약

NARROW. v1.8은 v1.7 must-fix(게이트 schema, real CE count, provenance_ok, near-threshold relabel, ID hash, Q update 수, proxy MDE, residual risk, Q artifact ban, negative read tests)를 구조적으로 반영했고 STOP taxonomy·cohort·scope 층에서는 이견 없음. 그러나 must-fix 1–3은 승인 시 실행을 막거나 게이트 의미를 무효화하는 수준의 내부 모순이며, 특히 결함 3은 fail-closed 설계 특성상 D1 전체를 NOT_EVALUABLE로 고정한다. 정의 수정만으로 해결 가능한 단계이므로 STOP이 아니라 NARROW이며, must-fix 1–3 반영 후 소규모 재검토(전체 라운드 재소모 불요)로 CONTINUE 판정이 가능하다. 승인·실행은 이 검토 기준으로 불가.
