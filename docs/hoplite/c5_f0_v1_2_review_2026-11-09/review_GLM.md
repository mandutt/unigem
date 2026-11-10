# C5 F0 v1.2 — Independent Review (GLM)

- 작성일: 2026-11-10
- 블록: 신규 10-round block, round 2/10 (v1.1 스레드 archive 완료, **결론 상속 없음**)
- 검토 대상: `docs/plan_c5_f0_v1_2_2026-11-09.md` (DRAFT v1.2 — 미승인·미실행)
- 참조: v1.1 plan, v1.0/v0.9 synthesis, Phase 6 cause report, Phase 6 results synthesis, prereg v1.0.11, `runner/c5_pm_phase6.py`
- 학습/평가 없음, test 163 sealed, P1 unused, subagent 없음
- 파일 변경: 이 보고서 1개뿐

## 0. Workspace sync / reviewed HEAD

```text
git fetch origin              → ok
git pull --ff-only origin main → "Already up to date."
reviewed HEAD  = f2525253efeb7de49d35a355b25c22b481594178
commit subject = "docs: add C5 F0 v1.2 review request" (2026-11-10 10:00:05 +0900)
tree           = clean (git status --porcelain empty before this report)
```

## 1. Verbatim paired E01−E11 (mandatory)

결정적 사실 먼저: **Phase 6 등록 결과 어디에도 E01−E11에 직접 대응하는 paired contrast는 존재하지 않는다.** prereg v1.0.11 §2.1 기준 Phase 6 arm은 F=(EG2+adapter), L=(EG2+adapter+LoRA), P=(native, LoRA only), PA=(native+adapter+LoRA)이며, "EG2 raw + LoRA only"(=E01) arm은 없다. 대응은 E11=Phase 6 L, E10=Phase 6 F 뿐이다. verbatim 인용 가능한 앵커는 다음 4개이고, E01−E11 paired estimand 자체는 F0에서 처음 계산된다:

Phase 6 L(=E11 analog) 절대 signal — `C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md` §1:

```text
| `L_COPY_SIGNAL` | **false** |
| mean Δ copy | **-0.1135** |
| 95% CI | [-0.2341, -0.0012] |
| positive docs | **6/15** |
| seed means >0 | **0/3** |
| `L_FULL_SIGNAL` | **false** |
| mean Δ full | **-0.1085** |
| positive docs | 6/15 |
```

15-doc vs 20-doc cohort 차이 — `C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md` §3 DS-2:

```text
- 15 common is length-selected: F 15-doc −0.11087 vs 20-doc +0.000195; L −0.11351 vs −0.02218.
- donors reuse val docs.
```

LoRA 효과 (E11−E10 analog, E01−E11 아님) — cause report §2:

```text
- F(adapter only) vs L(adapter+LoRA):
  - 15-doc seed-average paired contrast **-0.0026**
  - 8/15 positive
  - 60 seed-doc pairs mean -0.0224, 30/60 positive
- L−F contrast ~0 → **decoder LoRA가 signal을 만들거나 없애지 않음**.
```

Adapter 효과 (native 경로, 양성 대조) — cause report §2:

```text
- P(native, no adapter) vs PA(native + adapter + LoRA):
  - 15-doc seed-average paired contrast **+3.065**
  - **14/15 positive**
  - P copy Δ mean **3.076** vs PA **0.011**
- P와 PA는 **adapter 유무만 다릅니다**.
```

v1.2가 §6.5에서 인용하는 수치(계산 검증 포함):

```text
paired SE .019170 × 1.96 = .0375732   (= §12 half-width .037573 ✓)
observed boundary .05 + .037573 = .087573 (≈.0876 ✓)
80% power mean .05 + .037573 + 0.8416×.019170 = .10371 (≈.104 ✓)
EQUIVALENT mean band .05 − .037573 = .012427 (≈±.0124 ✓)
```

**그러나 SE .019170의 출처(어느 paired 계열/어느 artifact)는 v1.2 어디에도 기록되어 있지 않다** (must-fix 1). L 절대 CI [−0.2341, −0.0012]의 SE≈.0594(단일 arm)가 아니며, 가장 유력한 후보는 F−L 15-doc paired 계열이지만 문서상 확인 불가.

## 2. Q1. Init — golden table / serialization / post-step0 / all seeds

```text
판정: agree (2 minor)
```

근거:

- **golden table 독립 재계산 12/12 일치.** `step_seed(s,k)=(s ^ ((0x9E3779B9*(k+1)) & 0xffffffff)) & 0xffffffff` (v1.2 §4, L117-118)으로 20261108→`0x9f02514d/0x3d5bdb86/0xdb9345df`, 20261109→`0x9f02514c/0x3d5bdb87/0xdb9345de`, 20261110→`0x9f02514f/0x3d5bdb84/0xdb9345dd`, 20261111→`0x9f02514e/0x3d5bdb85/0xdb9345dc` — 문서 값과 전부 일치. 승수가 홀수이므로 mod 2^32에서 (step+1)∈1..100에 대해 X가 서로 다르고, XOR 후에도 step_seed 충돌 없음.
- **Phase 6 confound 실재 확인.** `runner/c5_pm_phase6.py` `build_arm`(L142-153)은 "RNG order is frozen: load weights first, then seed, then adapter, then LoRA" — LoRA 부착 전 별도 reseed 없음. 즉 Phase 6 L에서는 LoRA 초기화가 adapter draw 뒤에 이어지고, adapter가 없는 E01과 동일 LoRA init을 보장할 수 없었다. v1.2 §4의 `torch.manual_seed(seed ^ 0x5EED10A5)` 항상 실행(§4 L94, "always, adapter-independent")은 이 confound의 정확한 제거이며, E01/E11 post-init RNG state가 seed^X 이후 동일 진행되어 assertion 4(`post_init_rng_state_sha256` E01==E11)가 성립한다.
- per-step reseed(`torch.manual_seed(step_seed)` before each forward, §4 L96-98)는 dropout RNG 동등성을 구조적으로 보장(§4 L105, L124). adapter에 stochastic op이 없고(Linear/GELU/Linear/LayerNorm, §3) LoRA dropout .05만 유일한 RNG 소비자이므로 E01/E11 stream 동일.
- assertion 1-9(§4 L106-115)는 lora_A/B hash, adapter hash(E10==E11), lora_B all-zero 별도 assert(#6), E00/E01 adapter 부재·E00/E10 LoRA 0(#7), base/cache/labels hash cross-cell 동일(#8), post-step0 weight change(#9)를 커버. canonical tensor serialization(`name_len|dtype|ndim|shape|nbytes|LE bytes`, §4 L120)과 capture point(builder 직후, D0 forward 전, §4 L121)도 적절.
- Phase 6 checkpoint I/O assert(§4 L122)는 "F0 E11 ≠ Phase 6 L"이라는 검증 불가 명제를 "F0가 Phase 6 경로를 열지 않았다"는 검증 가능 명제로 치환 — 정확한 수정.

남는 문제 (minor):

1. **등록 seed 3개(20261108/09/10)의 init assertion 실행 위치 미지정.** §5 D0은 seed 20261111만 다루고, §5 Stage R에는 init 재검증 문장이 없다. §4는 "Assertions per registered seed"라만 쓴다. R unit build 시 동일 capture point로 실행한다고 §5 R에 명시해야 함.
2. serialization 헤더 필드(name_len, dtype, ndim, shape, nbytes)의 인코딩/폭 미지정 → `init_hashes.json` 재현성이 구현에 의존. 구현 commit에서 고정 필요. 또한 #9(post_step0_weight_change)의 cell 적용 범위(E00은 0-update라 제외)를 명시.

다음 단계: (1) §5 R에 "R unit build 시 §4 assertion 1-9를 seed 20261108/09/10에 동일 실행" 한 줄 추가. (2) 구현 commit에 헤더 인코딩 명세 + #9 적용 cell 명시.

## 3. Q2. D1 — f0_d1_mechanics / literal allowlist / no wrong-donor CE / filesystem seal

```text
판정: agree (1 medium-minor)
```

근거:

- v1.2 §5 D1(L147-176)은 v1.0 DS-1/Luna 지적을 구조적으로 해소한다: `f0_d1_mechanics.json` exact-key allowlist, `d1_report.json` exact-path 금지, `d1_sealed/` 부재, gate negative test("any `d1_report.json`/`per_doc`/`delta_*` input exits non-zero"), checkpoint digest-only + 삭제 + `checkpoint_absent==true` + loading 금지, checkpoints는 state_dict만 저장(신호 배열 없음). "values are never materialized in D1"(L174)는 seal 이상의 강한 통제이고, `eval_arm_d1` 재사용 금지(§11 L352, `c5_pm_f0_mechanics.py` 신설)로 Phase 6의 `eval_arm_d1`(runner L429)이 `delta_shuffled_*`를 materialize하는 경로를 차단한다.
- assertion 6("phase7 records == 0")과 filesystem assert로 phase7 경로도 봉쇄. assertion 2(`updates_total == 3`)로 1-update mechanics 유지. `labels_computed:false`, `not_a_result:true`(assertion 10) 일관.
- Stage R 시작 조건이 "D0/D1 **mechanics** pass; no signal-based gate"(§5 L187)이고 decision driver는 `f0_d1_mechanics.json`/`f0_r_labels.json`/`init_hashes.json`만 읽음(§5 L188) — 재량 gate 차단 완결.

남는 문제:

1. **D1 M records/generation의 artifact 처분지 미지정.** §5 D1 assertion 5/7은 "M records == 120/cell; total 480", "generation == 20/cell; total 80"을 요구하는데, §13 artifact tree(L384-395)의 `d1/` 아래는 `f0_d1_mechanics.json`뿐이다. 이 파일들이 어디에 쓰이는지(혹은 count 후 폐기되는지) 명시되지 않음. Phase 6의 M은 wrong-real Δ를 포함한다(cause report §1: L wrong-real −0.017, ratio −0.046) — K=753 M 엔드포인트의 wrong-donor 값은 sealed donor-crop signal과 상관하는 약한 side-channel이 될 수 있다. (a) D1에서는 counts만 유지하고 레코드 폐기, 또는 (b) gate 외 경로임을 명시하는 둘 중 하나로 §5/§13을 정합시켜야 함.
2. "no wrong-donor CE"의 범위 문구: donor-crop signal 경로에만 참이고, M wrong-real(K=753, global-mean 대비)은 별개 엔드포인트임을 한 줄로 명확화 권장(cause report §1의 "M은 donor specificity를 요구하지 않습니다"와 정합).

다음 단계: (1) §13에 D1 M/generation 처분 명시(권장: counts-only + 폐기). (2) "no wrong-donor CE" = donor-crop 경로 한정 문구 추가.

## 4. Q3. STOP/MDE — .104/.0876, EQUIVALENT ±.0124, ALL_FAIL 우세

```text
판정: conditional
```

근거:

- **산술 전부 재검증 일치** (§1의 검증 블록): .0375732 / .087573 / .10371 / .012427. §0.1의 "strict `CI_D.lower>.05` gate의 80% power mean ≈.104, observed boundary ≈.0876"과 §12 L375는 내부 정합. `.166/.216` 제거와 "phase6 single-arm SE 전이 금지"(§0.1)는 DS-3("single-arm SE 0.0594") 정확히 반영.
- **taxonomy 상호배타·전체포괄 확인** (§7 L278-312): PASS_POSITIVE는 `CI_D.lower>.05` ⇒ `CI_D.upper>.05` ⇒ EQUIVALENT(upper≤.05)와 논리적으로 겹치지 않음. 4-state 우선순위(NOT_EVALUABLE > PASS_POSITIVE > ROUTE_STOP > INDETERMINATE)는 전체 포괄이며, ALL_FAIL=SIGNAL 부정이므로 PASS와 ROUTE_STOP도 상호배타. reason enum precedence(`no_signal_equivalent` > `adapter_harm` > `adapter_benefit` > `no_signal_uncertain`)와 "ROUTE_STOP uses cell-level FAIL(c,e), not '3/3 seeds'"(L304)도 일관. E01 positive/E11 negative-but-CI≤.05 → INDETERMINATE(L310) 엣지 케이스 명시 확인.
- MDE의 해석 한계 고지("`.05` gate is a lower bound; F0 is underpowered for small effects; report realized CI_D half-width", §12 L375) 적절.

조건 (must-fix 1, 6):

1. **SE .019170 출처 미기재** — 어느 Phase 6 paired 계열(추정: F−L 15-doc paired)·어느 artifact 파일에서 왔는지 v1.2에 명시해야 MDE가 audit 가능. D1 승인 전 필수.
2. **§6.5의 "ALL_FAIL→ROUTE_STOP이 더 우세" 근거가 비논리.** 인용된 "15-common Phase 6 F/L −.111/−.1135"는 **adapter-bearing arm(F=E10, L=E11)**의 절대값이고, ALL_FAIL 성립 여부는 **E01(신규 cell) 실패 여부**에 달려 있다. F/L 수치는 E01에 대한 증거가 아니며, native 양성 대조 P(copy Δ 3.076)는 adapter-free 경로가 signal을 가질 수 있음을 보여준다(EG2 raw에서의 보존 여부가야말로 F0의 미지수, cause report §6 H1). 기대 서술은 "E11 실패 가능성 높음(L −0.11351), E01 미지"로 재서술 필요. taxonomy 자체는 기계적이어서 판정 오염은 없으나, freeze 전 한 줄 수정 권장.

다음 단계: (1) SE .019170 source artifact 명시. (2) §6.5 기대 문장 재서술. (3) 기대치가 registered branch를 선취하지 않는다는 주석(§7 "No post-hoc state changes"와 병기).

## 5. Q4. Cohort — 15 length-eligible / 20 descriptive / donor sha256 + LOO

```text
판정: agree
```

근거:

- 15 common = frozen preflight `common_ids`(§6.1 L196, prereg §1.2: val20=val[5:25], `h_len>=753` → 15, preflight SHA-256 `3ee3f1ca…79837af` frozen) 바인딩 + presence check(§6.1 L200) + "No 15→14 substitution"(§6.6 L260).
- 20-doc은 descriptive 전용, population 일반화 금지(§6.1 L195-197) — DS-2의 length-selection 문제를 estimand 재정의로 정면 처리. "eval_arm_d1 silently drops non-copyable docs; a missing doc means `NOT_EVALUABLE`, never a smaller cohort"(§6.1 L203)도 축소 cohort 차단.
- donor map = `donors_for(val20, cache)` + sha256 기록(§6.1 L198) — `runner/c5_mt5_lora_b0.py` `donors_for(ids, cache, count=5)`(L318)과 서명 일치. donor 재사용 선언, LOO donor-cluster sensitivity(§6.1 L199), doc당 정확히 5 donors + 전 cell 동일 donor set(§6.1 L201, §7 L273), doc-level 3/3 seed completeness(§6.6), n_boot=10000 + seed=20261109 명시적 override(§6.3 L223; runner `bootstrap_paired` 기본 n_boot=1000/seed=20261108과 다름을 정확히 인지하고 명시).
- donor set이 cell 간 자동 동일한 이유도 구조적으로 성립: donor map은 EG2 raw cache에만 의존(memory source가 모든 cell 동일, §2)하기 때문.

다음 단계: 없음(blocking). LOO range 보고 형식은 §6.1대로 descriptive 유지.

## 6. Q5. Compute — t_proj_f0 setup once + 3× per-wave terms, 96 min, nproc≥12

```text
판정: conditional
```

근거:

- `T_proj_R = setup_s + 3×(step0_eval_s + 100×step_s + m_build_s + m_ce_s + phase7_replay_s + primary_replay_s + gen_s + overhead_s)`(§12 L370)의 term 집합은 Phase 6 §11.5 전 단계를 포함하고, "slowest arm; seed waves sequential"(L371)로 파장 구조 정합. 900 updates = 3 seeds × 3 trained cells × 100(§5 L182) 계산 정확. D1 anchor 1,180.6s(D-156, §12 L369) < 25 min cap 정합.
- hard abort(`nproc < 12` or `T_proj_R > 96 min`, §12 L374), `contention_ratio` 기록(L373), "Caps: no cap increase without re-review"(L372), no retry(L378) — DS-7/Luna compute 지적 반영 완료. F0 전용 orchestration commit 선행 조건(§11 L356)은 DS-4/MF-1(provenance gap: Phase 6 `main()`이 `--mode registered` 거부, runner 미커밋)의 정확한 처방이며 선행 조건임에 동의.

조건 (must-fix 2):

- **"setup once, not 3×"(L371)가 실행 모델과 충돌.** §5 D1은 "4 parallel arm **processes** × 3 threads/arm"(L152)으로 프로세스별 실행인데, seed wave마다 4개 arm 프로세스가 다시 spawn되면 base load/cache build는 wave별로 재발한다. 프로세스 모델 유지 시 정확한 식은 `3×(setup_s + terms)`이고, `setup_s + 3×(…)`가 맞으려면 파장 간 base 공유(persistent loaded base, fork/spawn 공유 등) 메커니즘을 명시해야 한다. 현 식은 cap을 최대 2×setup 만큼 과소 산정할 수 있으므로 R 승인 전에 (a) 식 수정 또는 (b) 공유 메커니즘 명시 둘 중 하나 필수. 또한 Phase 6 R의 실측 parallel wall이 문서에 anchor로 없으므로 D1 기반 외삽의 sanity check로 추가 권장.

다음 단계: (1) setup 회수 규정 확정(식 or 메커니즘). (2) `c5_pm_f0_parallel.py` cap accounting에 반영(§11 L353 필드 목록 유지).

## 7. Q6. Scope — route-only / descriptive no-inference / lost controls

```text
판정: agree
```

근거:

- ROUTE_STOP 결과의 범위: "stops only the route as configured … does not stop the EG2 track, does not rescue B0-B, and does not launch H3"(§14 L412) + route 정의를 8개 항목으로 고정(§8) + association-only claim(§14 L411).
- descriptive contrasts no-inference(§14 L413), lost controls 명시: "the earlier MF-4 zero/permuted null and 1-seed signal gate are intentionally out of scope; F0 cannot claim they were replaced"(§14 L414) — MF-4의 정직한 인정.
- H3 완전 제거(§10 L339-345): "No H3 arm, trigger, rank, identity, null, or donor-discrimination endpoint", "F0 results do not automatically launch H3" — H3 세부가 F0 승인을 막거나 negative를 구제하는 경로 차단. D0/D1/R 개별 승인(§11 L359)과 pre-registration 상태(§18 "미승인, 미실행")도 확인.

남는 문제 (minor): MF-4의 마지막 경고("F0 negative는 'EG2 content 부족'과 'decoder-space alignment 부재'를 구분하지 못함")가 §14에 명시적으로 이월되지 않았다. route-only scope가 사실상 포함하지만, ROUTE_STOP 해석 오독 방지를 위해 한 줄 추가 권장(must-fix 6과 함께 freeze 시 처리 가능).

다음 단계: (1) §14에 content-vs-alignment 비판별 문구 한 줄 추가.

## 8. 최종 판정

```text
최종 판정: CONTINUE
Init:       agree   (golden table 12/12 재계산 일치, Phase 6 confound 실재 확인)
D1:         agree   (non-materialization 설계 강함; M/generation 처분지만 미지정)
STOP/MDE:   conditional (산술·taxonomy 검증 통과; SE .019170 출처 미기재)
Cohort:     agree   (estimand 고정 + NOT_EVALUABLE 원칙 + donor 구조적 동일성)
Compute:    conditional (term 집합 정합; setup-once vs per-wave 프로세스 모순)
Scope:      agree   (route-only, no-inference, lost controls, H3 제거 완결)

Must-fix (ranked):
1. [D1 gate] §0.1/§12 paired SE .019170·half-width .037573의 출처 artifact/계열 명시
   (단일-arm SE .0594가 아님을 file level로 입증). MDE auditability.
2. [R gate]  §12 "setup once" vs §5 per-wave arm 프로세스 모순 해소:
   3×(setup_s+terms)로 수정하거나 파장 간 base 공유 메커니즘 명시.
3. [D1 gate] §5 D1 assertion 5/7(M 480, generation 80)과 §13 artifact tree 정합:
   D1 M/generation 처분지 명시(권장 counts-only+폐기) + M wrong-real≠donor-crop
   signal 문구.
4. [D0 gate] §5 R에 등록 seed 20261108/09/10 init assertion 실행 위치 명시.
5. [D0 gate] §4 canonical serialization 헤더 인코딩 명세 + assertion #9 적용
   cell(E00 제외) 명시 — 구현 commit에서 확정.
6. [freeze]  §6.5 "ALL_FAIL→ROUTE_STOP 우세" 근거 재서술(F/L는 adapter-bearing
   arm이라 E01을 bound하지 않음) + §14에 MF-4 content-vs-alignment 비판별 문구.

잘못된 전제:
- "Phase 6에 paired E01−E11 데이터가 있다"는 전제는 거짓. E01(EG2 raw+LoRA
  only) arm은 Phase 6에 없었고, 해당 contrast는 F0가 처음 계산한다. 인용 가능한
  것은 L 절대값(−0.1135/−0.1085), F/L 15 vs 20-doc(−0.11087/+0.000195,
  −0.11351/−0.02218), L−F −0.0026, P−PA +3.065 뿐.
- §6.5의 ALL_FAIL 우세 근거(F/L −.111/−.1135)는 E01에 대한 증거가 아니다. P
  양성 대조(copy Δ 3.076)는 adapter-free 경로의 signal 가능성을 열어둔다.
- "D1에 wrong-donor CE가 전혀 없다"는 문구는 donor-crop signal 경로에만 참.
  M wrong-real(K=753)은 D1에서 계산될 수 있는 별개 엔드포인트다.

승인 경로: F0 구현 commit(c5_pm_f0*.py, clean tree) → must-fix 4-5 반영 →
D0 stage approval → must-fix 1,3 반영 → D1 → must-fix 2 반영 → R. 신규 review
round 재검토 불요(본 조건들이 stage gate에서 확인 가능). v1.2는 이 상태로
D0 승인 심사에 회부 가능.
```

본 검토는 승인이 아니며, 실행(execution)은 D0/D1/R 각각의 별도 stage approval로만 허용된다(§17).