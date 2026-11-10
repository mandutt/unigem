# C5 F0 v1.3 — GLM 독립 검토 (신규 10라운드 블록, Round 3/10)

- 작성일: 2026-11-10
- 모델: GLM (z-ai/glm-5.3-flash, high)
- 대상: `docs/plan_c5_f0_v1_3_2026-11-09.md`
- reviewed HEAD: `f5cc44b1bbe733523a3c66913eb5a719ebaa5872` ("docs: add C5 F0 v1.3 review request 2026-11-10 10:14:43 +0900")
- 동기화: `git fetch origin` → `git pull --ff-only origin main` = "Already up to date", 오류 없음, tree clean
- 독립성: v1.2 스레드 archive 완료, v1.2 결론 미상속, 신규 판정
- 상태 확인: 미승인·미실행, test 163 sealed, P1 unused, T5Gemma2 D-108 STOP, Phase 6 negative 종료 불변

## 0. Verbatim paired E01−E11 (대상 문서에서 그대로 인용)

v1.3 §2 Cells 표, E01/E11 행:

```text
| E01 (F0) | EG2 raw | none | 64 modules | 100 | adapter-free + LoRA |
| E11 (L) | EG2 raw | trained | 64 modules | 100 | adapter + LoRA |
```

v1.3 §6.2 (전문):

```text
For cell c, seed s, doc d:

delta_c(s,d) = mean_donor( CE_wrong_donor - CE_real )
```

v1.3 §6.3 (전문):

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
```

- Primary positive: `mean_D > 0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0`.
- `D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary.
- Copy primary; full secondary.
- **CI_D is doc-level only.** Seed-level `D_s` is a gate/descriptor, not a doc-level interval.

v1.3 §6.5 (전문):

```text
EQUIVALENT  iff  95% CI_D is entirely within [-.05, +.05]
```

- With n=15, `.0376` F−L proxy and P−PA SD 2.405: expected branch is **undetermined**; PASS and ROUTE_STOP are both live. No `±.0124` equivalence mean range is asserted.

### 0.1 레포 산출물 재계산 검증 (본 검토에서 독립 수행)

- `reports/provenance/C5_b0a/labels/labels.json` `L_COPY_SIGNAL.paired` = {mean −0.002639355129665797, ci_lower −0.040844837294684515, ci_upper 0.034302208052741166, n 15, n_boot 1000, seed 20261109, rng PCG64, ci_method linear} → half-width .0375735 → **.019170 = .037573/1.96 산술 확인** (1.96×.019170=.0375732). `delta.mean` −0.11350624932183163, seed_means [−0.13308, −0.10433, −0.10311] = cause report §1 표와 일치.
- `reports/provenance/C5_b0a/registered/units/{P,PA}_2026110{8,9,10}.json`의 `unit.final.per_doc.delta_shuffled_copy`를 15-common에서 seed-평균 후 P−PA paired 재계산: **mean +3.065202, SD 2.404764, SE 0.620907, positive 14/15** → v1.3 §12 표기(+3.0652 / SE .6209 / 14 of 15 / SD 2.405)와 **4개 수치 전부 일치**. 20-doc 전체는 mean +2.752/19 of 20 → 15-common 선택 효과 실재 확인.
- F−L 15-common 재계산: mean +0.002639(labels는 L−F 부호), SD 0.077534 → 직접 SE .020019로 proxy .019170과 일관.

---

## Q1. Initialization / serialization / pre-R audit — **conditional agree**

- 판정: conditional
- 근거:
  - §4 재배치가 핵심 결함을 제거한다. Phase 6 `build_arm`(`runner/c5_pm_phase6.py:142-151`)의 RNG 순서는 seed→adapter→LoRA로, LoRA 초기화가 adapter draw에 종속된다. F0 §4는 `torch.manual_seed(seed ^ 0x5EED10A5)`를 adapter 이후 **무조건** 실행하므로 E01(무adapter)/E11(adapter) 모두 동일 RNG 상태에서 LoRA를 draw → LoRA init 등가는 가정이 아니라 구조이다(assertion 2/4 자동 충족). E10/E11 adapter는 동일 seed 상태에서 draw → assertion 3 충족.
  - **step_seed golden table 12/12 재현 검증**: `(seed ^ ((0x9E3779B9*(step+1)) & 0xffffffff)) & 0xffffffff`로 seeds 20261108/09/10/20261111 × step 0/1/2 전부 일치(20261108: 0x9f02514d/0x3d5bdb86/0xdb9345df 등). 괄호 고정 표기도 확인.
  - 13A.1 stage P: v1.2까지 D0/D1(debug 20261111)만 검사하고 등록 seed 20261108/09/10의 init이 R 직전까지 미검증이던 공백을 전수 no-update audit으로 봉합. artifact `pre_r_init_audit.json`, gate, D0/compute 시간 반영 명시 ✓.
  - 13A.2 serialization grammar(name_len|dtype|ndim|shape|nbytes|le_bytes, sorted-name SHA-256, test vectors), capture point "builder 반환 직후, D0 forward 이전", post_step0 정의(첫 optimizer step 직후, 다음 forward 전 CPU RNG state) ✓.
  - RNG 모호성 해소 확인: eval CE는 eval-mode(무dropout)로 결정적이고 generation은 `runner/c5_pm_phase6.py:752` `do_sample=False`(greedy) → per-step reseed는 학습 forward에만 영향, Phase 6 결정성과 충돌 없음.
  - 감점 1: 13A.6 "F0 E11 **init** hash != frozen Phase 6 L hash"는 비교 대상이 없다. Phase 6는 init 가중치 hash를 기록한 적이 없다(`d0_report.json`에 hash 없음, `runner:590` `tensor_digest`는 M 컨트롤 텐서 전용, frozen artifact는 최종 checkpoint hash(`registered_checkpoint_hash.json`)뿐). 불일치 자체는 reseed로 구조적 보장이지만 frozen-artifact 비교로는 실행 불가.
  - 감점 2: stage P 감사와 R 빌드의 결합 장치 부재 — P 통과 후 코드 변경이 R 빌드에 반영될 경로를 artifact 수준에서 차단하지 않음.
- 다음 단계: (1) 13A.6 비교 근거 명시 — (a) stage P 내 Phase 6 RNG-order rebuild로 init hash를 새로 기록해 비교, 또는 (b) frozen 비교를 final-hash 불일치로 한정 + zero-Phase-6-I/O audit(v1.2 §0.6 계승)을 init non-reuse 주 증거로 유지. (2) R `units/{cell}_{seed}.json`에 per-seed §4 init assertion 기록 추가 또는 R 게이트가 stage P와 동일 code_commit 요구.

## Q2. D1 literal schema — **conditional agree (blocker 1건)**

- 판정: conditional
- 근거:
  - 봉합 구조는 강하다. 13A.4 전체 키 literal + nested literal, `wrong_donor_ce_calls` must 0, `donor_map_loads` must 0 → D1에서 donor 대조(delta)의 재료가 원천적으로 계산되지 않는다. v1.0 DS-1의 materialization 경로(`eval_arm_d1`이 `runner:429-490`에서 per_doc에 `delta_shuffled_copy/full` 기록, silent drop `if not real_copy: continue` 포함)를 mechanics evaluator 분리(§11, `eval_arm_d1` 비재사용)+ never-materialized 원칙으로 차단. checkpoint digest-only + 삭제 + `checkpoint_absent` + negative test + `d1_report.json` 금지 유지 ✓. E00 null checkpoint 허용 ✓.
  - **블로커**: §5 Stage D1 assertion 4/5/7/8이 13A.4 literal schema와 불일치한다. assertion 4는 `n_docs_step0==20`, `n_docs_final==20` "(scalar counts, not objects)", assertion 5는 M 120/cell, assertion 7은 generation 20/cell, assertion 8은 CE finiteness를 요구하는데, 13A.4 `cells` 객체는 `{updates, lora_params, adapter_params}`만 허용하고 상위 키는 총량 `m_records`/`generation_records` int뿐이다(총량 480/80은 기록 가능하나 per-cell 120/20, n_docs_step0/final, finiteness는 불가). §5 D1이 `f0_d1_mechanics.json`을 **유일한 D1 출력**으로 규정하므로 이 assertion들은 artifact에 기록될 수 없다 → 구현 시 allowlist writer가 실패하거나, assertion이 기록 없이 조용히 통과하는 구멍이 된다. "(scalar counts, not objects)" 문구는 작성자가 이 수치들을 artifact에 넣을 의도였음을 시사하므로 누락은 착오로 판단된다.
  - 부수 확인: assertion 3(E00 optimizer_steps 0)은 `cells.E00.updates:0`으로 커버, assertion 2의 `updates_total==3`은 cells 합으로 유도 가능 — 문제는 4/5(per-cell)/7(per-cell)/8뿐이다.
- 다음 단계: (1) 13A.4 `cells`에 `m_records`, `generation_records`, `n_docs_step0`, `n_docs_final`, `finite_ce:bool` 추가(또는 assertion 4/5/7/8을 "위반 시 `mechanics_pass:false` + `partial:true` + `error`" in-process 게이트로 재정의), (2) gate negative test가 mechanics_pass 위반을 뒤집는지 명시.

## Q3. STOP taxonomy / MDE proxy / P−PA — **agree**

- 판정: agree
- 근거:
  - §7 우선순위 NOT_EVALUABLE > PASS_POSITIVE > ROUTE_STOP > INDETERMINATE는 상호배타·전체포괄. PASS(`CI_D.lower>.05`)와 EQUIVALENT(CI ⊂ [−.05,+.05])는 수학적으로 겹치지 않는다(lower>.05면 upper>.05). harm/benefit의 `NOT EQUIVALENT` 조건으로 EQUIVALENT와 분리되고, harm(lower>0)=E01 우위=adapter harm, benefit(upper<0)=E11 우위로 방향 명명이 D=delta_E01−delta_E11과 정합. ALL_FAIL+benefit→`adapter_benefit` reason은 방향 정보 보존 + route-only 정지 유지로 타당.
  - MDE 재유도 전수 재검증(§0.1): .037573/.019170(labels.json paired CI), P−PA 4개 수치(mean +3.0652, SE .6209, 14/15, SD 2.405) 모두 registered artifacts와 정확히 일치. `.104`(gate-only 80%: .087573+0.84×.019170≈.1037)와 `.0876`(analytic 50%: .05+.037573=.087573) 재분류 산술 정합. `±.0124` 삭제 ✓.
  - Expected branch 철회 논리가 옳다: Phase 6 F−L(−.0026 paired, mean −.111/−.1135 delta)은 "adapter 하에서의 LoRA" 대조이고 E01−E11은 "LoRA 하에서의 adapter" 대조 → 위치 정보 없음. P−PA는 native memory + K=512 고정이라 방향 전이 불가, 분산 상한으로만 사용(§12) → §6.5 "undetermined; PASS와 ROUTE_STOP both live"가 유일하게 정직한 분기.
  - 유보(비블로커): P−PA 분산 상한(SD 2.405)에서는 EQUIVALENT 도달이 사실상 불가능하고 PASS도 큰 평균 없이는 불가하다. 계획이 분기를 단정하지 않은 것은 오류가 아니며, realized `CI_D` 지배 원칙(§12)으로 처리된다.
- 다음 단계: 없음(설계 변경 불요). 결과 보고 시 realized CI_D half-width + MDE 기입(§12 이미 규정) 상기.

## Q4. Cohort / donor count — **agree**

- 판정: agree
- 근거:
  - §6.1: frozen preflight `common_ids` 바인딩(labels.json `cohort.common_ids` 15 검증), 20-doc은 기술 보고만, presence check 전 cell×seed, donor map `donors_for(val20, cache)`+sha256, donor sets cell 간 동일, doc당 정확히 5 donors, doc 3/3 seed, `eval_arm_d1`의 silent drop을 `NOT_EVALUABLE`로 전환(15→14 대체 금지), `n_boot=10000` 명시 override, donor-cluster LOO sensitivity + donor 재사용 선언.
  - override 구현 가능 확인: `runner/c5_pm_stats.py:28-33` `bootstrap_paired_v2(values, n_boot=N_BOOT, seed=BOOTSTRAP_SEED)` — n_boot 인자 허용, 기본값 1000(15행). `l_predicate`(`runner/c5_pm_labels.py:54`) 미사용 → DS-6 재발 없음.
  - 13A.5: doc/cell마다 `evaluated_donors==5` ∧ `expected_donors==5`, 위반 abort — v1.0 DS-2/Luna n_donors 지적의 봉합. donor_map 결정성 확인: (|Δlen|, doc_id) 정렬(`runner:404-411`)로 tie 결정적.
- 다음 단계: 없음. CI를 "doc-level resampling interval"로 해석 한정하는 문구 유지 상기.

## Q5. Compute 9-term / execution host — **agree (conditional: T_proj 증명은 commit 시점)**

- 판정: conditional
- 근거:
  - `T_proj_R = setup_s + 3 × (step0_eval_s + 100×step_s + 20×5_step100_eval_s + m_build_s + m_ce_s + phase7_replay_s + primary_replay_s + gen_s + overhead_s)` — ×3 내부 9항은 Phase 6 v1.0.11 §11.5의 9항(100×t_train, t_step0_eval_20x5, t_step100_eval_20x5, t_M_build, t_initial_M_ce, t_generate_20x256, t_primary_replay, t_replay_15x5x2x2x2, t_overhead)과 1:1. setup을 ×3 밖으로 꺼내 per-process/wave 회계 + amortization을 orchestrator commit에서 증명 — v1.2 §0.5 "setup once" 가정의 올바른 수정(DS-7).
  - 총량 정합: D1 M 480=4×120, generation 80=4×20, updates 3 ✓. R M 1,440=4×3×120(전 cell EG2 → Phase 6 F/L 120과 동일, P/PA 160 없음), phase7 7,200=4×3×600, generation 240, 900 updates=3 cells×3 seeds×100, E00 0 ✓.
  - D1 cap 25 min: D-156 병렬 실측 1,180.6s/1,200s cap(`reports/C5_STATUS_2026-11-06.md:1565,1571`) → 여유 있음. R cap 96 min + `T_proj_R>96` hard abort + `nproc<12` abort + no 1.316 multiplier(측정 `contention_ratio`로 대체) ✓. 13A.7 nproc≥12 필수, 4-vCPU workspace 비해당 호스트 명시, orchestrator commit 선행 ✓.
  - 유보(계획 스스로 규정): 100×step_s 외삽 선형성과 contention/setup 회계는 commit 시점 T_proj에서만 확정 — "measured parallel timings determine final R cap"(§13A.7)으로 이미 규정되어 설계 결함 아님.
  - 표기 오류(비블로커): §12 산문의 "9 terms" 열거는 setup을 포함하고 20×5 step-100 eval을 누락(공식은 9항에 step-100 eval 포함, setup은 ×3 밖) — must-fix 4.
- 다음 단계: orchestrator commit에 per-phase timing + `contention_ratio` + setup 회계 증명 포함(§11/§12 이미 요구).

## Q6. Scope / route-only — **agree**

- 판정: agree
- 근거:
  - §8 route 정의 열거 + §14: ROUTE_STOP은 "EG2 layer19 raw + 이 LoRA/adapter 구성" 라우트만 정지, EG2 track STOP/keep·B0-B 구제·H3 개시 아님 ✓. association-only, descriptive contrasts 무추론, lost controls(MF-4 zero/permuted null, 1-seed signal gate) 미대체 선언 ✓ — B0A cause MF-4/MF-5 반영 확인.
  - §10 H3 완전 제거: arm/trigger/rank/identity/null/probe 미등록, 별도 prereg+승인, "F0 results do not automatically launch H3", negative F0의 H3 구제 경로 차단 ✓.
  - §9 M 격리: M_PASS ≠ donor-specificity 증거(cause §1 "M_PASS와 L_SIGNAL false는 모순이 아님"과 일관), M evaluability는 PROTOCOL_VALID 조건이나 ROUTE_STOP에는 불요, E00 baseline 비-trained 명시 ✓.
- 다음 단계: 없음.

---

## 최종 판정

```text
최종 판정: NARROW
Init: conditional — 구조적 등가 + golden table(12/12 검증) + stage P 충분; 13A.6 비교 근거와 P↔R 결합 장치 보강 필요
D1: conditional — never-materialized 봉합 강함; §5 assertion 4/5/7/8 ↔ 13A.4 literal schema 불일치는 승인 전 제거 필요 (blocker)
STOP/MDE: agree — .019170/.037573/P−PA 4수치/.0876/.104 전부 재검증 일치, expected branch 철회 논리 옳음
Cohort: agree — frozen 15, 5-donors/doc + 13A.5 count assertion, n_boot=10000 override 구현 가능 확인
Compute: conditional — 9항 1:1(§11.5) + 총량 정합; T_proj/amortization 증명은 orchestrator commit 시점, §12 산문 표기 1건
Scope: agree — route-only/association-only/H3 분리/lost controls 선언 유지
```

### Must-fix (ranked)

1. **(Blocker — D1)** §5 Stage D1 assertion 4/5/7/8과 13A.4 literal schema 정합: `cells`에 `m_records`/`generation_records`(per-cell), `n_docs_step0`, `n_docs_final`, `finite_ce:bool`을 추가하거나, 해당 assertion을 "위반 시 `mechanics_pass:false` + `partial:true` + `error`" in-process 게이트로 재정의하고 gate negative test가 각 위반을 뒤집음을 명시. 근거: `f0_d1_mechanics.json`이 유일한 D1 출력(§5)인데 현재 키 집합으로는 "(scalar counts, not objects)" 수치 기록 불가 → 승인 불가.
2. **(High — init)** 13A.6 비교 근거 명시: Phase 6는 init 가중치 hash를 기록하지 않았다(`d0_report.json` 무 hash, `runner:590` digest는 M 컨트롤 전용, frozen artifact는 최종 checkpoint hash뿐). (a) stage P 내 Phase 6 RNG-order rebuild로 init hash를 새로 기록해 비교하거나, (b) frozen-artifact 비교를 **final-hash** 불일치로 한정하고 zero-Phase-6-I/O audit을 init non-reuse 주 증거로 유지.
3. **(Medium — init)** stage P 감사 ↔ R 실행 결합: R `units/{cell}_{seed}.json`에 per-seed §4 init assertion 기록 추가, 또는 R 게이트가 stage P와 동일 `code_commit` 요구 — P 통과 후 코드 변경이 R 빌드에 유입되는 경로 차단.
4. **(Low — compute)** §12 산문 "9 terms" 열거(setup 포함, 20×5 step-100 eval 누락)를 공식과 정렬: "setup 밖 + per-seed 9항(20×5 step-100 eval 포함)".
5. **(Low — serialization)** 13A.2에 dtype 허용목록(예: f32/i64/bool)과 강제 LE cast 명시; test vectors 요구는 이미 존재.

### 잘못된 전제

- 13A.6/§0.4의 "F0 E11 **init** hash != frozen Phase 6 L hash"가 frozen artifact 비교로 가능하다는 전제 — Phase 6 init hash 미기록으로 불가. 실제 보장은 구조적 근거(LoRA reseed) + final-hash 불일치 + I/O audit.
- §12 산문의 "9항" 나열이 자기 공식과 1:1이 아님(must-fix 4) — 공식이 정확하므로 결과론적 영향 없음.
- P−PA 수치(+3.0652/SE .6209/14 of 15/SD 2.405)는 **잘못된 전제가 아님** — registered artifacts 재계산으로 전부 참 확인. F−L proxy .019170도 labels.json에서 정확히 재산출됨.

### 판정 사유

v1.2 블로커(DS-1 D1 materialization, DS-2 cohort estimand, DS-3 MDE 산술, DS-4 provenance, DS-6 n_boot)는 설계 수준에서 모두 해소되었고 핵심 수치는 레포 산출물로 독립 재검증되었다. 잔존 블로커는 1건이며 범위가 좁다(D1 artifact schema와 assertion 목록의 기계적 정합 — 구현 전 스펙 수정). 신규 10라운드 블록 round 3/10으로 수정 여지가 충분하다. → **NARROW**. F0 승인 금지·실행 금지 유지, D0/D1/R 각각 별도 stage 승인 유지.