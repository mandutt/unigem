# C5 F0 v1.4 — Independent Review (DS1017)

- 검토일: 2026-11-09
- **reviewed HEAD: `60c806f95a97e284972a00ba1a0f5b43217e673e`**
- 동기화: `git fetch origin` OK; `git pull --ff-only origin main` → `Already up to date`; HEAD `60c806f` (`docs: add C5 F0 v1.4 review request`).
- 대상: `docs/plan_c5_f0_v1_4_2026-11-09.md`
- 새 독립 검토. v1.3 결론 상속 없음. 학습/평가 없음, test 163 sealed, P1 unused, subagent 없음.
- **최종 판정: NARROW**

## 0. Verbatim paired E01−E11 (plan §2, §6.3)

```text
| E01 (F0) | EG2 raw | none | 64 modules | 100 | adapter-free + LoRA |
| E11 (L) | EG2 raw | trained | 64 modules | 100 | adapter + LoRA |

- Primary: **E01 vs E11** (LoRA initialization matched).

D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
```

---

## Q1. Init / stage P / non-reuse

- **판정: disagree**
- 근거:
  1. **Stage P는 자기가 기록한다고 선언한 assertion을 실행할 수 없다.** §13A.1은 Stage P를 "no updates"로 정의하고 "Records assertions 1–8 + 13A.3 only; assertion 9 (`post_step0_weight_change`) is N/A (no optimizer step)"라고 쓴다. 그런데 §13A.2는 `post_step0_rng_state_sha256`를 "CPU RNG state **immediately after first optimizer step** and before next forward"로 정의하고, §13A.3은 "**First optimizer update** must change: E10 adapter; E01 LoRA; E11 adapter and LoRA"를 요구한다. optimizer step이 없는 Stage P는 assertion 5와 13A.3을 산출할 수 없다. assertion 9만 N/A로 표시하고 5를 그대로 둔 것은 내부 모순이다.
  2. **게이트가 충족 불가.** §13A.6은 `pre_r_init_audit_pass:true`를 R의 선행 조건으로 두고, 그 값의 출처는 Stage P다(§13A.1). Stage P가 13A.3을 낼 수 없으므로, 문면대로면 R은 시작될 수 없다.
  3. **registered seed 커버리지 공백.** §4는 assertion 1–9를 "per registered seed"로 규정하지만, Stage P(registered seeds 20261108/09/10)는 5/9/13A.3을 못 하고, D1은 **non-registered seed 20261111**(§5, D1 report `seed: 20261111 (debug seed, registered seed 아님)`)만 1-update로 검사한다. 따라서 registered seed에 대한 5/9/13A.3 검사가 계획 어디에도 없다.
  4. **init_hashes 경로 모순.** §4는 `init_hashes.json` 캡처 시점을 "immediately after builder returns, before D0 forward"로 두지만, §13 artifact tree는 `r/init_hashes.json`만 두고 `r/`는 "R-only"이며 `pre_r_init_audit_pass` 이후에만 생성된다. D0/P 시점의 init hash가 기록될 경로가 없다.
  5. 긍정적 확인: `step_seed` golden table은 정확히 재현된다(직접 계산: 20261108→`0x9f02514d/0x3d5bdb86/0xdb9345df`, 20261109→`0x9f02514c/0x3d5bdb87/0xdb9345de`, 20261110→`0x9f02514f/0x3d5bdb84/0xdb9345dd`, 20261111→`0x9f02514e/0x3d5bdb85/0xdb9345dc`). `build_arm_f0`의 reseed 구조(`seed` → adapter → `seed^0x5EED10A5` → LoRA)는 E01/E11 LoRA init 일치와 E10/E11 adapter 일치를 구조적으로 만든다. Phase 6 I/O audit(0 checkpoint open)로 hash-inequality를 대체한 판단도 타당하다.
- 다음 단계:
  1. Stage P를 "registered seed별 1 forward + 1 optimizer step" 감사로 재정의해 5/9/13A.3을 실제 산출하거나, Stage P는 1–4·6–8만 기록하고 게이트도 그 부분집합만 요구하도록 명시하고 5/9/13A.3은 별도 per-seed 1-update 감사로 옮긴다.
  2. `init_hashes.json`을 `d0/`(또는 `pre_r/`)에 두고 `r/init_hashes.json`은 R 전용으로 분리한다.

## Q2. D1 schema / §13 stage scope / seal

- **판정: disagree**
- 근거:
  1. **literal schema가 D1 assertion과 §13 flag를 담지 못한다.** §13A.4는 "Only these keys"로 key 집합을 닫아 놓았는데, 그 목록에 `labels_computed`, `not_a_result`, `test_split_used`, `p1_used`, `d1_signal_read`가 없다. 그러나 §5 D1 assertion 10은 `labels_computed:false`, `not_a_result:true`를 요구하고, §13은 `test_split_used:false`, `p1_used:false`, `d1_signal_read:false`를 요구한다. "exact-key allowlist"가 assertion이 요구하는 필드를 거부하는 자기모순이다.
  2. **`assertions` object가 10개 중 5개만 기록.** §13A.4의 `assertions`는 `step0_docs_ok, final_docs_ok, m_count_ok, generation_count_ok, ce_finite_ok` 5개뿐이다. §5 D1은 10개 assertion이며, `cells==4`(1), `updates_total==3`(2), `E00 optimizer_steps==0`(3), `labels_computed/not_a_result`(10)에 대한 pass/fail boolean이 schema에 없다(6·9는 top-level `phase7_records`/`checkpoint_absent`로 일부 커버).
  3. **signal path가 R 전까지 미검증.** §13A.4는 `wrong_donor_ce_calls: int (must 0)`을 강제하고 §5는 "D1 does not compute ... signal deltas"라고 한다. §11은 `c5_pm_f0_mechanics.py`가 `eval_arm_d1`을 재사용하지 않는다고 하고, §12는 "No retry/extension"이다. 즉 donor-crop/wrong-donor/delta 코드는 R(96분)에서 처음 실행된다. seal을 위해 signal을 materialize하지 않는 것은 타당하나, *mechanics* 검증까지 포기할 필요는 없다.
  4. 긍정적 확인: D1 count 정합성은 맞다. M 480 = 4×120, generation 80 = 4×20, phase7 0, `checkpoint_absent:true`, `donor_map_loads:0`. §13의 stage 분리(D1은 `d1/f0_d1_mechanics.json`만, `r/`는 R 전용)와 `pre_r_init_audit_pass` 선행 조건 방향은 옳다.
- 다음 단계:
  1. §13A.4에 `labels_computed`, `not_a_result`, `test_split_used`, `p1_used`, `d1_signal_read`를 추가하고, `assertions` object를 10개 assertion 전부(또는 top-level로 승격한 항목을 명시)로 확장한다.
  2. D1이 wrong-donor CE를 *finiteness/mechanics 목적*으로만 계산하고 per-doc delta는 저장하지 않도록 허용하거나, R 전에 signal-path mechanics 단위 테스트를 추가한다.

## Q3. STOP / MDE / reference dispersion

- **판정: conditional**
- 근거:
  1. **taxonomy는 상호배타·전체포괄.** §7에서 `PASS_POSITIVE`는 `SIGNAL(E01,copy)`를 요구하므로 `FAIL(E01,copy)`가 false → `ALL_FAIL` false → `ROUTE_STOP`과 배타적이다. `NOT_EVALUABLE`(1) → `PASS_POSITIVE`(2) → `ROUTE_STOP`(3) → `INDETERMINATE`(4) 순서로 전체를 덮는다. `EQUIVALENT`(lower≥−.05, upper≤+.05)와 `PASS_POSITIVE`(lower>+.05)도 배타적이다.
  2. **expected branch 수정은 옳다.** `delta = mean_donor(CE_wrong − CE_real)`이고 P−PA(+3.0652, 14/15)는 adapter-free 쪽이 큰 값이므로 `D=E01−E11>0` = PASS 방향이다. v1.3의 "ROUTE_STOP 쪽" 표기는 오류였고 v1.4가 바로잡았다. §6.5의 "undetermined; both live"와 "P−PA is PASS-direction context, not ROUTE_STOP evidence"는 정합적이다.
  3. **reference dispersion 수치는 정합.** +3.0652, SE 0.6209, 14/15, per-doc SD 2.405는 cause report(+3.065, 14/15, SD 2.405)와 일치하고, 2.405/√15 = 0.6211 ≈ 0.6209다.
  4. **MDE 표기 오류(비차단).** §12는 "MDE: `.019170 = .037573/1.96`"이라 쓰지만 `.019170`은 **SE**이지 MDE가 아니다. 실제 50%/80% MDE는 `.0376`/`.0537`이다. 다만 `.104`와 `.0876`은 각각 `.05+2.8·SE=.10368`과 `.05+1.96·SE=.087573`으로 정확히 재현되므로, 숫자 자체는 일관적이고 라벨만 틀렸다. realized `CI_D`가 지배한다는 §12 문장은 옳다.
- 다음 단계:
  1. `.019170`을 "SE"로 재라벨하고 MDE(50%)=.0376, MDE(80%)=.0537, gate mean=.104, 50% boundary=.0876의 유도를 명시한다.

## Q4. Cohort / donor CI conditional / LOO

- **판정: agree (조건부)**
- 근거:
  1. §6.1은 estimand를 "15 length-eligible docs + fixed donor graph"로 고정하고 20-doc 일반화를 금지하며, 15 common이 length-selected(5/20 제외)임을 명시한다. donor reuse도 선언했다. 이는 DS-2에 대한 정당한 축소다.
  2. `n_boot=10000` override는 실행 가능하다. `runner/c5_pm_stats.py`의 `bootstrap_paired_v2(values, n_boot=N_BOOT, seed=BOOTSTRAP_SEED)`가 `n_boot`/`seed`를 인자로 받고 반환 dict에 `n_boot`/`seed`를 기록하므로 §6.3의 `assert realized.n_boot == 10000 and realized.seed == 20261109`가 성립한다. `l_predicate` 금지, `f0_labels.json` alias 금지도 명시됐다.
  3. donor 조건(문서당 정확히 5, E00/E10/E01/E11 donor set 동일, doc-level 3/3 seed)은 §6.1·§13A.5에 있다.
  4. 잔여: LOO "report range"의 정의(문서 간 공유 donor를 전 문서에서 제거하는지)와, LOO가 state를 뒤집을 수 있는지(descriptive only)가 문면에 없다. CI가 fixed donor graph 조건부라는 한계는 선언됐다.
- 다음 단계:
  1. LOO 절차(공유 donor cluster 제거 규칙)와 "descriptive only, state 변경 불가"를 한 줄로 고정한다.

## Q5. Compute 9-term / setup / execution host

- **판정: conditional**
- 근거:
  1. **term/카운트 정합.** §12의 9 term은 Phase 6 §11.5와 1:1이고(`100*t_train`, `t_step0_eval_20x5`, `t_step100_eval_20x5`, `t_M_build`, `t_initial_M_ce`, `t_generate_20x256`, `t_primary_replay`, `t_replay_15x5x2x2x2`, `t_overhead`), 900 updates = 3 trained cells × 100 × 3 seeds, M 1,440 = 4×3×120, phase7 7,200 = 4×3×600, generation 240 = 4×3×20으로 모두 맞는다. D1 25분은 Phase 6 D1 실측 1,180.6s/1,200s cap 아래다.
  2. **`nproc>=12` + 12 logical threads는 headroom 0.** §12는 "3/arm, 4 arms = 12 logical"이고 §13A.7은 `nproc>=12`를 요구한다. 12 thread를 12 core에 정확히 채우면 orchestrator/OS 몫이 없어 `contention_ratio>1`이 구조적으로 예상된다. 그런데 §12는 "no 1.316 multiplier"로 contention factor를 제거했다.
  3. **4,939.884s는 end-to-end wall이 아니다.** `registered_report.json`의 `wall_estimate_s = 4939.884`는 wave-max unit elapsed의 합(1,661.098 + 1,751.427 + 1,527.358 = 4,939.883)이며, setup/replay를 포함한 실측 wall이 아니다(동일 지적: `docs/hoplite/c5_pm_results_review_2026-11-09/review_SOL.md`). §12가 `setup_s_effective`를 별도로 더하는 것은 옳지만, anchor를 "wall"로 부르는 것은 부정확하다.
  4. 긍정적 확인: `T_proj_R = setup_s_effective + 3 × (slowest arm 9-term sum)`은 4-arm 병렬 wave 구조와 정합적이고, `nproc<12` 또는 `T_proj_R>96min` hard abort, `contention_ratio` 기록, D1 per-phase timing 기반 final cap은 방향이 옳다.
- 다음 단계:
  1. `nproc>=16`(또는 threads/arm 축소)으로 headroom을 두고, final cap을 Phase 6 anchor가 아니라 F0 D1/R 실측 `contention_ratio`에서 유도한다.
  2. 4,939.884s를 "sum of wave-max unit elapsed (setup/replay 제외)"로 재라벨한다.

## Q6. Scope / route-only

- **판정: agree**
- 근거:
  1. §10은 H3를 F0에서 완전히 제거하고 "F0 results do not automatically launch H3", "separate prereg and approval"를 명시한다. §14는 ROUTE_STOP이 "route as configured"만 멈추고 EG2 track/B0-B/H3를 건드리지 않는다고 못박는다.
  2. §14는 E00/E10/E01 vs E00을 descriptive로, association-only claim을 명시하고, "lost controls"(MF-4 zero/permuted null, 1-seed gate)가 대체되지 않았음을 인정한다. §9는 M_PASS ≠ donor-specific content-use를 재확인한다.
  3. 이는 Phase 6 synthesis MF-3/MF-5의 과대 일반화 축소와 일치한다.
- 다음 단계:
  1. 없음(범위는 충분). 단, Q1/Q2 수정이 scope 문구를 바꾸지 않도록 유지.

---

## 최종 판정: **NARROW**

```text
Initialization: disagree — Stage P가 assertion 5/13A.3을 실행 불가(no updates), registered-seed 커버리지 공백, init_hashes 경로 모순
D1 seal:        disagree — §13A.4 literal schema가 §5 assertion 10과 §13 flag를 누락, assertions object 5/10, signal path R 전 미검증
STOP taxonomy:  conditional — 상호배타·전체포괄·expected branch 정합; MDE 라벨(.019170=SE)만 오류
Cohort/CI:      agree(조건부) — 15-doc+fixed donor graph 고정, n_boot=10000 실행 가능; LOO 절차 미정의
Compute:        conditional — term/카운트 정합; nproc=12 headroom 0, 4,939.884s는 wave-max 합
Scope:          agree — H3 제거, route-only, descriptive no-inference 충분
```

## Must-fix (ranked)

1. **[blocker, Q1/Q2] Stage P 실행 불가능성.** §13A.1 "no updates" vs §13A.2 `post_step0_rng_state_sha256`("after first optimizer step") vs §13A.3("First optimizer update must change"). Stage P는 5/13A.3을 낼 수 없고, `pre_r_init_audit_pass`(§13A.6) 게이트가 충족 불가다. Stage P를 registered-seed 1-update 감사로 바꾸거나, 5/9/13A.3을 별도 per-seed 1-update 감사로 분리하고 게이트 요구를 명시하라.
2. **[blocker, Q2] D1 literal schema 불완전.** §13A.4 "Only these keys"에 `labels_computed`, `not_a_result`, `test_split_used`, `p1_used`, `d1_signal_read`가 없고, `assertions` object가 §5의 10개 중 5개만 담는다. schema를 assertion/§13 flag와 일치시켜라.
3. **[high, Q2] signal path가 R 전까지 미검증.** `wrong_donor_ce_calls must 0`(§13A.4) + "does not compute signal deltas"(§5) + `c5_pm_f0_mechanics.py`가 `eval_arm_d1` 미재사용(§11) + "No retry/extension"(§12) → donor-crop/delta 버그가 96분 R에서 처음 드러난다. D1에서 wrong-donor CE finiteness만 검사(per-doc 미저장)하거나 R 전 mechanics 단위 테스트를 추가하라.
4. **[medium, Q5] nproc headroom 0 + contention 미반영.** `nproc>=12`에 12 threads(§12, §13A.7), "no 1.316 multiplier"(§12). `nproc>=16` 또는 threads/arm 축소, final cap을 F0 실측 `contention_ratio`에서 유도하라.
5. **[medium, Q2] `init_hashes.json` 경로 모순.** §4 캡처 시점("before D0 forward") vs §13 `r/init_hashes.json`(R-only, `pre_r_init_audit_pass` 이후 생성). D0/P용 경로를 추가하라.
6. **[low, Q3] MDE 라벨.** `.019170`은 SE다. MDE(50%)=.0376, MDE(80%)=.0537, gate mean=.104, 50% boundary=.0876으로 재라벨하라.
7. **[low, Q1] step_seed 코드 주석의 precedence.** §4 주석 `seed ^ (0x9E3779B9 * (step+1)) & 0xffffffff`는 C(`^`>`&`)와 Python(`&`>`^`)에서 다르게 파싱된다. 명시적 괄호형 `(seed ^ ((0x9E3779B9*(step+1)) & 0xffffffff)) & 0xffffffff`로 통일하라(공식·golden table은 이미 정확).

## 잘못된 전제

- "Stage P는 optimizer step 없이 assertion 5/9/13A.3을 기록할 수 있다" — 거짓. 5/9/13A.3은 step을 요구한다.
- "§13A.4의 'Only these keys'가 D1 assertion과 §13 flag를 모두 담는다" — 거짓. 5개 key와 5개 assertion boolean이 빠졌다.
- "4,939.884s는 end-to-end wall이다" — 거짓. wave-max unit elapsed의 합이다.
- "v1.3의 P−PA는 ROUTE_STOP 방향" — 거짓. v1.4가 PASS 방향으로 바로잡은 것이 옳다.
- "`.019170`은 MDE다" — 거짓. SE다(단, `.104`/`.0876`은 정확).

## 경계

```text
F0 v1.4 = NARROW (미승인, 미실행)
Phase 6 = negative 종료 불변
B0-B = 미승인
test 163 = sealed; P1 = unused; T5Gemma2 = D-108 STOP
```