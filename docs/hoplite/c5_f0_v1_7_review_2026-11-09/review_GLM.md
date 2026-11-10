# C5 F0 v1.7 — Independent Review (GLM, New Block Round 7/10)

- 작성일: 2026-11-10
- 검토자: GLM 5.3 Flash (신규 독립 스레드; v1.6 결론 미상속, v1.6 스레드 archive 확인만)
- 대상: `docs/plan_c5_f0_v1_7_2026-11-09.md` (DRAFT v1.7 — 미승인·미실행, plan §18 확인)
- **reviewed HEAD: `e5d69ab3123b8ccc2426a87e672628da99cea080`**
  - `git fetch origin` → 성공; `git pull --ff-only origin main` → "Already up to date."; HEAD 상기 커밋.
- 읽은 파일: `reports/EXTERNAL_REVIEW_C5_F0_V1_7_2026-11-09.md`, `docs/plan_c5_f0_v1_7_2026-11-09.md`, `docs/plan_c5_f0_v1_6_2026-11-09.md`, `reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`(구조/§2.4 P/PA init), `runner/c5_pm_phase6.py`(L142–160 `build_arm`, L779 `torch.set_num_threads(6)`), 등록 아티팩트 2건(§Compute 참조).
- 검증 보조: v1.6↔v1.7 대조 grep, `reports/provenance/C5_b0a/` 등록 JSON 원문 확인, step_seed golden 값 독립 재계산.

## 0. Verbatim paired E01−E11 (plan v1.7 §6.2–§6.3)

```text
delta_c(s,d) = mean_donor( CE_wrong_donor - CE_real )

D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

- §6.3 L233: "`D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary."
- §6.3 L232: "Primary positive: `mean_D > 0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0`."

---

## Q1. Q gate / 3 seeds / init manifest

판정: **conditional** (구조 동의, 명세 2건 누락)

근거:
- v1.6 L184 "R seed excluded if its Q unit fails; remaining seeds continue only if ≥2 remain" → v1.7 §5 L189 / §6.6 L269 "Any Q seed failure → NOT_EVALUABLE; no 2-seed continuation. Primary requires all 3 seeds Q pass." 로 교체 확인. §7 L279–284 `PROTOCOL_VALID`가 E00/E10/E01/E11 × 3 seeds 전건 요구로 일관. PASS의 "2/3 seeds D_s>0"는 3-seed 내부 부호 복제 게이트(L233)이지 표본 축소가 아님 — 모순 없음.
- Init manifest: Stage P 12 loads, `d0/init_hashes.json` append-only per `{stage,seed,cell}`, P 레코드 D0이 덮지 않음(§13A.1 L426). `common_ids_sha256` 추가(§0.7, §4 L121). P/Q/init 단일 writer atomic append+validate(§13A.9 L532). Q는 `pre_r_seed_audit_pass[seed]` per-seed 게이트(§13A.1 L428, §5 L188).
- RNG 계약 검증: v1.7 §4 의사코드 순서 load_base → `manual_seed(seed)` → adapter(seed) → `manual_seed(seed ^ 0x5EED10A5)` → LoRA — adapter는 재시드 전에 생성되므로 E10/E11 adapter 해시 동등성(§4 assertion 3)과 정합. step_seed golden 표(§4 L117) 독립 재계산: `step_seed(20261108,0)=0x9f02514d`, `(20261108,1)=0x3d5bdb86`, seed 20261109/10/11 step0 = `0x9f02514c/0x9f02514f/0x9f02514e` — **전부 일치**. Phase 6 `build_arm`의 frozen RNG order(runner/c5_pm_phase6.py L142–160: load→seed→adapter→LoRA)와 F0 builder가 별도 함수(§4 "must not modify build_arm")로 공존 가능.

다음 단계 (must-fix로 §Must-fix 3에 반영):
1. §13A.1 L429의 Q wrong-donor CE finiteness/shape check **범위 미정의** — 어떤 문서(20 val 전부? 부분?), 몇 명 donor, copy/full 어느 endpoint, 기대 shape 서술이 없음. Q가 R 유일 사전 게이트인 이상 범위가 규범이어야 함.
2. §13 아티팩트 트리(L397–412)에 **Q 레코드 파일 경로·키 allowlist 없음** — `d0/init_hashes.json`, `pre_r/pre_r_init_audit.json`만 존재. Q의 `post_step0_rng` parity / group change / `wrong_donor_finite` 기록 위치와 literal key 목록 명시 필요.

## Q2. D1 predicates / seal / telemetry

판정: **conditional** (설계 동의, 규범 미배선 1건 + 경로 1건)

근거:
- Predicates: §13A.4 L498 `cells_ok = set(cells)=={E00,E10,E01,E11}`, `updates_total_ok = updates_total==3`, `e00_steps_zero = cells.E00.updates==0` — §5 D1 assertions 2/3(§5 L156–157)와 정합하고 mechanics_pass(L499)에 배선됨.
- Seal: `f0_d1_mechanics.json` 유일 출력 + exact-key allowlist, `d1_report.json` exact-path 금지(§5 L170), digest-only checkpoint + `checkpoint_absent` assertion(§5 L163, L172), negative tests(§5 L171, §13A.4 L502), `wrong_donor_ce_calls:0`·`donor_map_loads:0` absolute(§13A.4 L489–490, §13A.8 L525). Phase 6가 실제로 `d1/d1_report.json`을 썼음이 원문에서 확인됨(`reports/provenance/C5_b0a/d1/d1_report.json:15154`) — v1.7의 exact-path 금지는 실존 아티팩트 클래스를 닫는 조치로 근거 있음.
- Telemetry: D1 schema `parallel{nproc, threads_per_arm, parallel_wall_s, contention_ratio}`(L479)가 §5 L153 "4 parallel arm processes × 1 thread/arm"와 정합.

남는 우회 경로 / 결함:
1. **must-fix 1**: §0 변경 4가 "D1 real-memory CE exact count assertion"을 주장하나, §13A.4 schema L488 `real_memory_ce_calls: int`는 기댓값 없음, `*_ok` flag 없음, mechanics_pass(L499) 공식에 부재. "반영됨"으로 읽으면 안 됨 — 기대 카운트 산식(예: E10/E01/E11 step0+final donor-crop real CE + E00 1회 + M 관련 CE)과 flag를 규범에 배선 필요.
2. **must-fix 2**: D1 `timings`(L477)에 replay 항목이 없고 §12 L391 "T_proj analog from D1 per-phase timing"은 9개 §11.5 항목 중 R-only인 `t_primary_replay`, `t_replay_15x5x2x2x2`(§12 L382)를 만들 수 없음 → Q5 참조.
3. minor: D1/Q가 아티팩트는 통제하지만 **process stdout/log로의 CE 값 출력 금지 조항 없음** — 값은 materialize되지 않아도 로그로 새면 seal 우회. stdout 정책 한 줄 명시 권고(§Must-fix 4).

## Q3. STOP / MDE / near-threshold / harm-benefit

판정: **agree**

근거:
- 4-state 상호배타·전체포괄: §7 L302–309 우선순위 평가(NOT_EVALUABLE > PASS_POSITIVE > ROUTE_STOP > INDETERMINATE)는 first-match로 배타가 구조적으로 성립하고 state 4가 catch-all이므로 포괄. `POST_STEP0_RNG_MISMATCH`/`GROUP_CHANGE_MISSING`/`wrong_donor_finite:false`도 NOT_EVALUABLE로 흡수(§13A.1 L430).
- PASS vs EQUIVALENT 비중첩: PASS `CI_D.lower > +.05`(L307)이면 `upper ≥ lower > .05`이므로 EQUIVALENT(L291, CI⊆[-.05,.05]) 불가. 또한 PASS는 `SIGNAL(E01,copy)`를 요구하므로 `ALL_FAIL`(L289)과도 배타. harm/benefit은 `NOT EQUIVALENT` 조건 내장(L292–293) → reason enum `no_signal_equivalent > adapter_harm > adapter_benefit > no_signal_uncertain`(L308) 서로 배타; ALL_FAIL 하에 4 case 완전분할이고 기본값 `no_signal_uncertain`(L318) 존재.
- harm/benefit vs PASS 비배타 명시(L317, §0.9): 방향 서술자와 positive 1차 라벨의 분리 — v1.6 대비 명확화. 방향 기호도 정합: delta>0 = real이 wrong donor보다 우세 = donor-specific signal이므로 `CI_D.lower>0` = adapter가 signal을 해침 = `adapter_harm`(Phase 6 P−PA +3.065 방향과 일관, cause report §2).
- Near-threshold: b∈{.05,0}, h=(upper−lower)/2, `|mean_D−b|≤h` ⟺ b∈[lower,upper] — CI 내 경계 포함의 결정론적 판정식으로 자기정합(L313). 상태 변경 없음.
- MDE provenance: `.019170 = .037573/1.96`가 F−L planning proxy로 명시, "none is an observed F0 mean"(L389); §6.5 L262 expected branch undetermined, P−PA(+3.065, 14/15)는 PASS-direction context로 한정 — DS-3(C5_F0_V1_0 synthesis §3 DS-3) 해소 확인. 수치 검산: 2.8016×.01917=.0537(80% MDE) ✓.
- note(비블로킹): n=15 paired CI half-width 프록시 ~.117 하에서는 b=.05와 b=0의 "near"가 ALL_FAIL 발생 시 사실상 항상 참 — near-threshold 리포트는 공실화 경향. 이미 서술 전용이므로 현행 유지.

## Q4. Cohort / cell CI / donor conditional

판정: **agree**

근거:
- 15 length-eligible frozen: preflight `common_ids` + `common_ids_sha256`(§6.1 L198, §4 L121), 20→15 length 선택 공개(L198), 20-doc 일반화 금지·서술 전용(L199) — DS-2 해소.
- Donor 조건부: donor map sha256 기록(L200), LOO donor sensitivity + reuse 선언(L201), doc당 정확히 5 donors·전 셀 동일 donor set·위반 시 abort(L203, §13A.5 L507), CI_D는 fixed donor graph 조건부 명시(L389).
- 결측: 15×3 전건, NA 없음, 15→14 대체 금지, 미달 시 NOT_EVALUABLE(L266–269); `eval_arm_d1`의 silent drop 위험을 명명하고 mechanics evaluator 비재사용(§11 L362) + presence check(L202)로 차단.
- CI: cell CI와 paired CI_D 모두 doc-level bootstrap, n_boot=10000 explicit override + realized assert + `l_predicate` 금지(L225–230, L251 — DS-6 해소), 결정 시점 재부트스트랩 금지(L252). percentile linear + CI.lower=2.5th 명시(L251). seed-sign gate는 복제 서술자로 1차 검정 아님(L233–235) — 이중검정 오류 없음.

## Q5. Compute 16-core / 1-thread / estimate provenance

판정: **conditional** (단일화·provenance 동의, T_proj 규범 1건)

근거:
- Thread 단일화 실재 확인: v1.6 L181 "final cap from D1 T_proj and nproc≥16 **(or threads_per_arm≤1)**", L382 "Hard abort if `nproc < 16` **and** `threads_per_arm > 1`"(AND라 1-thread 4-vCPU 호스트가 통과하는 결함), §13A.7 v1.6 L512 "nproc>=16 (or threads_per_arm<=1)", §15 Q5 v1.6 L556 "nproc≥12" → v1.7 §0.2 L24 "nproc>=16 only; 4-vCPU host fails", L388 "Hard abort if `nproc < 16`", §12 전 행 "1/arm, 4 arms = 4 logical". 3 threads/arm 잔재(v1.6 L148/180) 제거 확인.
- Estimate provenance 원문 확인: `reports/provenance/C5_b0a/d1/d1_report.json:15154` `"wall_estimate_s": 1180.577`, `reports/provenance/C5_b0a/phase6_artifact_registry.json:146` `"wall_estimate_s": 4939.884` — **두 값 모두 레코드 필드명이 문자 그대로 `wall_estimate_s`**이므로 v1.7 §12 L381 "estimates, not measurements" 재분류는 사실이고, final cap = measured `parallel_wall_s`(§0.3, §11 L363, §5 L186) 원칙은 정당. `contention_ratio`/`nproc`/`threads_per_arm` 기록(L387) 유지. Phase 6 runner는 프로세스당 `torch.set_num_threads(6)`(c5_pm_phase6.py L779)으로 anchor 3 threads/arm 서술(§12 L381)과 모순 없음(호스트 구성 별개).
- 900 updates = 3 cells × 100 × 3 seeds(§5 L183) ✓; D1 25 min / R 96 min 캡 재검토 원칙(L386) ✓; committed-runner 선행조건 = F0 전용 orchestration commit이 D0 전 제약(§11 L366, §13A.7 L521) — DS-4 해소이며 전제조건 답변은 **yes**.

결함:
- **must-fix 2**: `T_proj_R = setup_s_effective + 3 × Σ9 terms(최느린 arm)`(L383–385)의 9항목 중 `t_primary_replay`, `t_replay_15x5x2x2x2`는 R에서만 발생하므로 D1 기반 T_proj는 **하한**이며, L391 "T_proj analog from D1 per-phase timing; hard abort at cap"은 불완전 프로젝션으로 R 사전 abort를 유발할 수 있음. 규범 문언 필요: (i) D1-derived T_proj를 lower bound로 명시, (ii) 구속력 있는 게이트는 R **측정** `parallel_wall_s ≤ 96 min`과 in-run hard abort, (iii) 사전 추정이 필요하면 replay 항목에 명시적 allowance 또는 §12에서 사전 abort 조건에서 replay 제외.

## Q6. Scope / route-only

판정: **agree**

근거:
- H3 완전 제거(§10 L349–355): H3 arm/trigger/rank/identity/null/donor-discrimination endpoint 미등록, 별도 prereg+승인 요구, "F0 results do not automatically launch H3"(L354) — v1.0 synthesis DS-8 및 results synthesis §3 MF 항목(Phase 6 음성을 H3로 구제 금지)과 정합.
- Non-goals(§14 L535–548): association-only(L544), ROUTE_STOP route-only(§8, L545 — EG2 track STOP 아님, B0-B 구제 아님, H3 개시 아님), descriptive contrasts 무인과(L546), lost controls 명시(L547 — MF-4 zero/permuted null과 1-seed gate가 대체되지 않음을 스스로 선언), M_PASS ≠ donor-specific content-use(L342, L548 — cause report §5 "M_PASS ≠ content-use signal"과 일치).
- test 163 sealed / P1 unused 불변(header, §13A.9, `data_scope.json`).

---

## 최종 판정: **NARROW**

```text
Init:        conditional — Q 검사 범위 + Q 레코드 아티팩트 경로/allowlist 명시 필요
D1:          must-fix — real_memory_ce_calls exact-count 미배선, T_proj/timings 정합
STOP/MDE:    agree — 배타/포괄/비중첩 검증 통과, near-threshold 결정론적
Cohort/CI:   agree — DS-2/DS-6 해소 확인
Compute:     must-fix — D1-derived T_proj 하한 선언 + 측정 wall 구속 게이트 문언
Scope:       agree — H3 제거·route-only·lost controls 선언 적정
```

v1.0 블로커(DS-1~DS-8)는 v1.7 §0/§4/§6/§11/§12/§13A에서 실제로 해소됨을 대조로 확인했다. 잔존 결함은 재설계가 아니라 규범 문언 4건이며, v1.7.1 패치로 해소 가능하다.

### Must-fix (ranked)

1. **§13A.4 + §0 변경 4**: `real_memory_ce_calls` 기댓값 산식과 `real_memory_ce_calls_ok` flag를 정의하고 mechanics_pass(L499)에 배선. 현재는 schema 필드만 존재 — v1.7이 주장한 "exact count assertion"이 규범상 미구현.
2. **§12/§11**: D1-derived `T_proj_R`은 R-only replay 항목(`t_primary_replay`, `t_replay_15x5x2x2x2`) 결여로 하한임을 명시하고, 구속 게이트를 측정 `parallel_wall_s ≤ 96 min` + in-R hard abort로 문언 확정(L391 수정). 사전 abort를 하한 프로젝션으로 수행하지 않도록.
3. **§13A.1 + §13**: Q wrong-donor CE finiteness/shape check의 규범 범위(문서 수 × donor 수 × copy/full × 기대 shape) 명시, Q 레코드 파일 경로와 literal key allowlist를 §13 트리에 추가.
4. **§5 D1 / §13A.1**: D1·Q 프로세스 stdout/log에 CE 값 출력 금지 조항 추가(아티팩트 외 잔여 seal 우회 경로 차단).

(비블로킹) 5. near-threshold 지표의 n=15 CI 하반 공실화 — 서술 전용 유지. 6. §12에 1,180.6/4,939.884의 출처 포인터(d1_report.json:15154, phase6_artifact_registry.json:146) 인용 권장.

### 잘못된 전제

- 확인된 오류 전제 없음. v1.7 §0 변경 목록은 v1.6 원문(L181, L184, L382, L512)과의 대조에서 모두 실재 확인됨.
- 단, §0 변경 4("D1 real-memory CE exact count assertion")와 변경 3의 T_proj 문언은 **주장만 존재하고 규범 배선이 없음**(must-fix 1, 2) — "반영 완료"로 전제하고 승인 진행하면 안 됨.

### 다음 단계

1. v1.7.1 패치(must-fix 1–4, 문언 수준).
2. 패치 후 diff-scope 재확인 1회(신규 10-round 소모 없이 승인 가능 수준).
3. 승인 후 D0 stage approval → D1 → R 순 개별 승인(§11 L369), 16-core 자격 호스트에서만 실행(§13A.7).