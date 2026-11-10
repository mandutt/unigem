# C5 F0 v1.11 — Independent Review (GLM)

- 작성일: 2026-11-10
- 검토자: GLM (`z-ai/glm-5.3-flash`)
- 대상: `docs/plan_c5_f0_v1_11_2026-11-09.md`
- **reviewed HEAD: `5aa18b1c857a29b3190b683098e3f098f1ce4063`** ("docs: add C5 F0 v1.11 review request", 2026-11-10 13:32:21 +0900)
- 동기화: `git fetch origin` → `git pull --ff-only origin main` → "Already up to date." HEAD = `5aa18b1c`. 이 HEAD에서 읽은 파일: `reports/EXTERNAL_REVIEW_C5_F0_V1_11_2026-11-09.md`, `docs/plan_c5_f0_v1_11_2026-11-09.md`, `docs/plan_c5_f0_v1_10_2026-11-09.md`, `reports/C5_F0_BLOCK2_3AI_REVIEW_SYNTHESIS_2026-11-10.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py` (추가 검증: `runner/c5_pm_stats.py`, `runner/c5_mt5_lora_b0.py`, `reports/provenance/C5_b0a/labels/labels.json`, `reports/provenance/C5_b0a/registered/registered_report.json`, `reports/C5_STATUS_2026-11-06.md` §100–102).
- 새 10라운드 블록 round **1/10**. 새 독립 검토, v1.10 결론 상속 없음.
- 추가 학습/평가 없음. test 163 sealed, P1 unused, T5Gemma2 D-108 STOP 확인. 파일 수정 없음 (지정 report만).

## 0. Verbatim paired E01−E11

v1.11 plan §6.3 인용 (그대로):

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

- Primary positive (§6.3, 그대로): `mean_D > 0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0`.

## 1. Q1 — CPU observability / D1 custody

판정: **conditional agree**

근거:

- CPU: §0 변경 1 + §13A.4 `parallel` 객체에 `cpu_affinity`, `cgroup_cpu_quota`, `torch_threads`, `thread_pool_counts` 추가 확인(478행). v1.10 GLM must-fix 1·Luna must-fix 4의 D1 측 반영. 그러나 **R 측 artifact schema에는 없다** — §0 변경 1은 "parallel/**R provenance**에 추가"라 약속하지만 `r_mechanics_pass.json`(§13A.10)에는 `provenance_ok:bool` 하나뿐이고 CPU 필드를 담는 R 스키마가 어디에도 정의되지 않았다. 또한 필드는 기록 전용이고 gate는 없다 — §12 hard abort는 `nproc < 16`뿐이며, cgroup quota로 16 logical core가 제한된 호스트는 `nproc` gate를 통과한다. D1 25min·R 96min cap이 binding이라 실패는 늦게라도 fail-closed되지만, quota gate(`cgroup_cpu_quota`가 16 core 미만이면 abort)를 hard abort 조건에 추가하는 것이 정직한 구현이다.
- D1 custody: §5 D1 — `f0_d1_mechanics.json` 유일 출력, exact-key allowlist(§13A.4 "Only these keys"), `d1_report.json` exact-path 금지 + `d1_sealed/` 부재, gate negative test non-zero exit, checkpoint digest-only/삭제/`checkpoint_absent:true`, crash path `partial:true`+`error`+checkpoint 삭제+"no other file"(§13A.4) — 실질적 custody. §0 변경 11의 "exact output inventory; checkpoint nonexistent"는 본문과 정합.
- 잔여: §0 변경 11이 "**logs/temp**/crash paths tested"를 약속하는데 본문(§5, §13A.4 filesystem tests)은 checkpoint 부재와 `per_doc`/`delta_*`/`d1_sealed` negative test만 규정하고 **log 파일 inventory와 temp 경로 테스트는 어디에도 없다.** v1.10 본문도 동일 결손(v1.10 507행)이었으므로 변경 요약만으로는 충족되지 않는다.

다음 단계: (1) R artifact에 parallel/provenance CPU 필드 스키마 정의 + quota 기반 hard abort 조건 추가. (2) §5 또는 §13A.4에 log/temp 경로 inventory와 테스트 명시.

## 2. Q2 — Wrong-donor wording / crash error enum

판정: **conditional agree**

근거:

- Wrong-donor: §0 변경 3 + §13A.8 — D1 `wrong_donor_ce_calls:0` absolute, **Q가 first execution(finiteness/shape only, no persist), R이 first persisted/aggregated use**로 일관 정립. v1.10 GLM must-fix 3의 13A.1 vs 13A.8 모순 해소. §13A.1 Q도 "donor-crop/wrong-donor CE finiteness + shape check; no per-doc/delta/signal persisted"로 정합.
- **그러나 §0 변경 3("Q schema에 `wrong_donor_ce_calls` 추가")과 §13A.8("Q schema records `wrong_donor_ce_calls`")이 약속한 필드가 §13A.10 `q/q_seed_audit/{seed}.json` schema에 없다** — cells 필드는 `{post_step0_rng_sha256, group_change_ok, wrong_donor_finite, shape_ok}`뿐. prereg 자체 모순이며, "first execution"의 카운트가 스키마상 감증 불가능하다. 승인 blocker.
- Error enum: §13A.4 `error: enum{TIMEOUT,OOM,CE_NONFINITE,SHAPE_MISMATCH,CHECKPOINT_DIGEST_FAIL,OTHER_REDACTED}|null` — 폐쇄형 enum으로 CE 값이 `error` 경유 유출 불가. §0 변경 4 "CE 값 문자열 금지" + §13 "D1/Q stdout/log must not print CE values; only counts/booleans"(411행)와 합쳐 v1.10 GLM must-fix 4 충족. enum은 D1에만 적용되지만 Q/P/D0 crash는 audit false → `NOT_EVALUABLE`로 fail-closed되므로 허용 가능. `OTHER_REDACTED`는 메시지 sanitize를 함축 — 충분.

다음 단계: §13A.10 Q schema에 `wrong_donor_ce_calls:int`(cell별 또는 seed별) 추가.

## 3. Q3 — Donor-count / overrun / provenance

판정: **conditional agree**

근거:

- Donor-count: §0 변경 5 — `donor_count`는 frozen metadata, `donor_map_loads`는 runtime load count, "Metadata read는 load로 세지 않음", "Frozen table에는 donor 수만 기록하고 load 이벤트와 분리"로 분리. v1.10 DS의 "frozen table donor_count vs `donor_map_loads:0`" 모순은 서로 다른 양의 분리로 논리적으로 해소됨. §13A.4 `mechanics_pass`의 `wrong_donor_ce_calls==0 AND donor_map_loads==0`과 §13A.8 D1 무호출 규칙 정합. 잔여: D1 행의 donor_count 열 값(기록값)과 `real_memory_ce_calls`가 M-real CE(memory_kind=real)를 포함하는지는 테이블 freeze 시점에 행 단위로 확정 필요 — D1 stage approval에서 검증 가능하므로 리뷰 blocker 아님.
- Overrun: **미통일.** §0 변경 6이 단일 규칙(">25 min: hard abort, partial, new code SHA + explicit stage re-approval")을 선언하고 §0/§5/§12 통일을 주장하지만, 실제 본문은 (a) §5 D1에 overrun 시 귀결 문장이 없고, (b) §12는 "if measured wall exceeds 25 min, **repair or re-review**; no silent extension"으로 §0 변경 6과 다른 처분을 기술하며, (c) R의 측정 wall >96min 시 처분이 없다(T_proj_R>96 pre-run hard abort만 존재), (d) P ≤10min·Q ≤15min·D0 ≤15min cap에도 overrun 처분이 없다. v1.10 DS must-fix "overrun 3중 정의"가 선언만으로 남아 있다. 승인 blocker.
- 4,939.884s provenance: 검증 일치. `registered_report.json` `wall_estimate_s = 4939.884017705917`(D-157, C5_STATUS §101 "3 waves(seed별 4 arms 병렬, **2 threads**)"); D-156 = D1 1,180.6s(C5_STATUS §100 "4 arms 병렬(**3 threads each**)"). §12 첫 문장 "D1 1,180.6s = 3 threads/arm measured (D-156); registered 4,939.884s = 2 threads/arm measured (D-157); neither is F0"는 사실과 정확히 일치 — v1.10 DS 지적 해소. 잔여: 같은 §12 wall-anchor 행의 "not a measurement" 무규정 표현은 "measured (D-157)"과 표면적으로 충돌 — "not an F0 measurement"로 수정 권장(1단어, non-blocker).

다음 단계: (1) §5 D1과 §12에 단일 overrun 규칙을 동일 문구로 기술 + R 측정 wall >96min 및 P/Q/D0 overrun 처분 명시. (2) §12 wall-anchor 표현 수정.

## 4. Q4 — Near-threshold / EQUIVALENT

판정: **conditional agree**

근거:

- EQUIVALENT 정의 정합: §6.5 "95% CI_D is entirely within [-.05, +.05]" ↔ §7 `CI_D.lower >= -.05 AND CI_D.upper <= +.05` 동일; "realized CI governs", "nominal only" 병기; §12 `SE_D <= .0255` reachability는 `.05/1.96` 필요조건으로 정합. PASS(`CI_D.lower > +.05`)는 상한도 >+.05를 함축하므로 EQUIVALENT와 수학적으로 비중복 — §7 우선순위 테이블과 무모순.
- MDE proxy 검증: `.037573` = `labels.json L_COPY_SIGNAL.paired` CI half-width(`(0.034302 + 0.040845)/2 = 0.037574`), `.019170 = .037573/1.96` 산술 일치. labels.json은 `n_boot:1000, seed:20261109, rng:PCG64, ci_method:linear`로 frozen N_BOOT=1000 확인 — §6.3의 "explicit override of frozen N_BOOT=1000" 서술과 정합. "F−L LoRA contrast planning proxy, not a validated E01−E11 SE" 격하 유지 + P−PA reference dispersion(+3.0652, SE 0.6209, per-doc SD 2.405)은 원인 보고서 §2(+3.065, 14/15)와 일치.
- 잔여: §7 "Near-threshold **b∈{+0.05,0}**"는 여전히 endpoint별 binding이 없다(copy vs full 어느 쪽이 +.05인지 미정의). v1.10 GLM next-step("§7에 b per endpoint 명시(copy .05 / full 0)")이 set 표기로만 반영됨. `m_mean`/`m_lower` 계산값이 b 선택에 의존하므로 1줄 수정 필요. `m_sign=(#seeds>0)-2`는 3 seeds에서 [-2,+1]로 well-defined — non-blocker 수준이나 승인 전 확정 권장.

다음 단계: §7에 `b(copy)=+0.05, b(full)=0` 명시.

## 5. Q5 — R donor identity / hash

판정: **conditional agree**

근거:

- §6.1: donor map = `donors_for(val20, cache)`(`runner/c5_mt5_lora_b0.py:318`, `count=5` 기본값 확인), sha256을 `init_hashes.json`에 기록, **R report에 `donor_map_sha256` + per-doc donor-ID hash 기록 + equality assert** — v1.10 GLM must-fix(§0 변경 9) 반영. §13A.5 `evaluated_donors == 5 and expected_donors == 5` abort; §7 PROTOCOL_VALID에 "each doc has exactly 5 donors; donor sets identical for E00/E10/E01/E11" 포함 — cell 간 동일성은 게이트화됨.
- 결손 (a): **`r/f0_report.json`과 `r/f0_r_labels.json`의 literal schema가 없다.** D1은 §13A.4 exact-key allowlist로 묶여 있지만 R report는 `donor_map_sha256`, per-doc donor hash(직렬화 형식 미정의), `replay_ok`(§0 변경 2), bootstrap realized 값(n_boot/seed), `mean_D`/`CI_D`/`D_s`, signed margins를 담을 스키마가 정의되지 않았다. prereg 스키마 체인의 D1만 완결.
- 결손 (b): "asserts equality"의 실패 처분 미규정 — donor hash 불일치 시 어떤 게이트가 false가 되는지(NOT_EVALUABLE인지) 명시 필요.
- 결손 (c): donor map은 seed-independent(`donors_for(val20, cache)`)이므로 3 seed의 `donor_map_sha256` 상호 equality assert가 가능하고 cache drift를 잡는다 — 현재 미언급.
- 결손 (d): `replay_ok` 의미 미정의. §0 변경 2가 `r/f0_replay.json`을 삭제하고 "numeric replay는 Phase 6 §11.4를 재사용하지 않고 R report에 `replay_ok`만 기록"이라 하는데, Phase 6 §11.4(prereg 1307–1327행: primary 1,680 coverage + numeric atol=1e-5/rtol=1e-4)를 재사용하지 않는다면 `replay_ok`가 무엇을 검증하는지 정의가 없다. 정의 없는 bool은 감증 불가.

다음 단계: (1) `f0_report.json`/`f0_r_labels.json` literal schema 정의(D1 §13A.4 대응) — donor hash 필드·직렬화·`replay_ok` 정의 포함. (2) donor hash 불일치 → `NOT_EVALUABLE` 게이트 명시. (3) cross-seed `donor_map_sha256` equality assert 추가.

## 6. Q6 — Scope / route

판정: **agree**

근거:

- §8 route as configured 고정 목록; §14 non-goals — association-only("adapter-as-configured"), ROUTE_STOP route-only("does not stop the EG2 track, does not rescue B0-B, does not launch H3"), descriptive contrasts 명시, **lost controls**(MF-4의 zero/permuted null + 1-seed signal gate)를 "intentionally out of scope; F0 cannot claim they were replaced"로 정직 선언 — v1.0 MF-4 재발 차단.
- §10 H3 완전 배제(별도 prereg + 승인, F0 결과가 H3 자동 launch 금지) — v1.10까지 유지.
- §13A.7: 16-core host 요구("current 4-vCPU workspace fails; no F0 run there"), runner/orchestrator committed clean-tree SHA before D0(§11, §13A.6), test163/P1 read-path negative tests("direct open attempts must fail; flags alone are not evidence") — v1.10 Luna must-fix 6·MF-6 방향 정합.
- Confound 표기(§2): E11−E10, E01−E10 "not clean causal" 명시; E00 non-trained unit 명시. Phase 6 negative 종료·B0-B 미승인 전제와 충돌 없음. §4 "F0 must not modify Phase 6 `build_arm`"는 `runner/c5_pm_phase6.py` `build_arm`(142행, RNG order seed→adapter→LoRA, LoRA seed reset 없음)과 대비해 `build_arm_f0`의 `seed ^ 0x5EED10A5` 재설정이 신규 builder임을 정당화.

다음 단계: 없음 (scope는 승인 가능 상태).

## 7. 최종 판정

```text
최종 판정: NARROW
Init: agree — §4 계약 + §13A.2/13A.3 유효. step_seed golden table 12개 벡터 전수 재계산 일치
  (20261108: 0x9f02514d/0x3d5bdb86/0xdb9345df; 09: …4c/…87/…de; 10: …4f/…84/…dd; 11: …4e/…85/…dc).
  serialization grammar + 외부 KAT fixture 설계 양호.
D1: seal 구조 agree. custody 잔여 = logs/temp 테스트 명시 결손 + overrun 규칙 미통일.
STOP/MDE: taxonomy·EQUIVALENT·MDE proxy 산술 검증 일치. b per-endpoint binding 1줄 필요.
Cohort: 15-doc conditional estimand, CI_D doc-level, §6.6 no-substitution agree.
Compute: D-156(3 threads/arm)/D-157(2 threads/arm, 4939.884s artifact 일치) 검증 완료.
  CPU 필드는 R artifact에 바인딩 필요 + quota gate 권장.
Scope: agree — 결손 없음.
Must-fix (ranked):
  1. §13A.10 q/q_seed_audit schema에 wrong_donor_ce_calls 추가 — §0 변경 3/§13A.8과의
     prereg 자체 모순 제거(승인 blocker).
  2. Overrun 단일 규칙 실제 통일 — §5 D1·§12에 동일 문구(">25 min: hard abort, partial,
     new code SHA + explicit stage re-approval") 기술, §12 "repair or re-review" 대체,
     R 측정 wall >96min 및 P/Q/D0 overrun 처분 명시(승인 blocker).
  3. §7 near-threshold b per endpoint 명시: b(copy)=+0.05, b(full)=0.
  4. R-side schema 완결 — f0_report.json/f0_r_labels.json literal schema(donor_map_sha256,
     per-doc donor-ID hash + 직렬화 형식, replay_ok 정의, realized bootstrap 값),
     donor hash 불일치 → NOT_EVALUABLE 게이트, cross-seed donor_map_sha256 equality,
     r_mechanics_pass.json에 expected_* 필드 또는 별도 frozen expected-table artifact,
     R provenance에 CPU 필드 4종(§0 변경 1 이행).
  5. D1 custody logs/temp 경로 inventory + 테스트 명시(§0 변경 11 이행).
잘못된 전제: 없음. D-157 "measured/not-measured" 전제는 v1.11에서 올바르게 재정립됨
  (artifact 값 4939.884s, 2 threads/arm 확인). 단 §12 wall-anchor "not a measurement"
  표현은 "not an F0 measurement"로 수정 권장(non-blocker).
```

NARROW 근거: 설계·게이트 구조·산술·산출물 분리는 v1.10 대비 실질적으로 개선되었고(scope는 승인 가능), 잔여 결함은 전부 상기 5개 항목으로 열거 가능한 스키마/문구 수준이다. 이 prereg는 fail-closed audit chain이 exact schema에 의존하므로, 약속된 필드의 부재(Q `wrong_donor_ce_calls`, R CPU 필드·expected counts)와 규칙 불일치(overrun)는 승인 전 수정이 필요하다. 5항목 반영(v1.12) 시 재검토 없이 승인 단계로 갈 수 있는 수준이다.