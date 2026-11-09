# C5 Phase 6 v0.2.1-r3.1 — Independent External Review (GLM 5.3 Flash max)

- 작성일: 2026-11-09
- 검토자: **GLM 5.3 Flash (reasoning max)** — OpenRouter `z-ai/glm-5.3-flash`. 이것은 r3 라운드와 의도적으로 별도인 **새로운 독립 검토 라운드**다. 이전 라운드의 어떤 검토 답변(본인 라운드 포함)도 읽지 않았고 재사용하지 않았다.
- 검토 기준 HEAD: `c4ed30a1f120b01905291602e3aec53f87c765fc` (origin/main, "docs: add C5 P/M v0.2.1-r3.1 review request")
- 동기화: `git fetch origin` → `git pull --ff-only origin main` → **Already up to date** → HEAD `c4ed30a1…`. `git diff --stat 7264c55..c4ed30a`로 확인한 요청서-HEAD 이후 델타는 review-request 파일과 review 인프라 파일뿐이다(plan 본문 변경 없음).
- 성격: **consultation-only.** 저장소 수정 없음(이 파일이 유일한 write). 학습·평가 실행 없음. test 163 미개봉. P1 미사용. subagent/추가 LLM 미호출. T5Gemma2 **D-108 STOP 유지 확인**(docs/decisions.md D-108 = bridge 3/3 STOP).
- 요약 판정: **CONTINUE (조건부)** — §3 Must-fix를 동결 전에 text-only로 반영하면 r3.1 동결 + 구현 + unit tests + D0를 승인한다. D1 / 3-seed / B0-B / B1 / B2 / Stage C는 이 라운드에서 승인하지 않는다.

---

## 0. 독립성·방법

- 요청서 `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_1_R3_1_2026-11-09.md`를 전문 직접 읽었다.
- 지정 원문 7건을 모두 읽었다: r3.1 plan(771줄 전문), r3 plan(795줄 전문), r3 3-AI synthesis, `m_cohort_preflight.json`, P0 native sanity 보고서, `runner/c5_mt5_lora_b0.py`(802줄), `eval/tests/test_c5_b0_metric.py`.
- 교차검증을 위해 추가로 읽기 전용으로 확인한 것(요청서가 금지하지 않는 확인): `docs/plan_c5_b0a_pm_prereg_v0_2.md`(v0.2 base — signal/L>F/PA/donor-length 규칙 출처), `reports/provenance/C5_clean/splits.json`(preflight ID 검증), `docs/decisions.md`(D-108/D-117/D-120/D-121), git 이력(커밋·blob·내용 해시).
- r3 라운드의 `review_GLM.md`/`review_DS41.md`/`review_TERRA.md` 원문은 **읽지 않았다**(독립성 유지). r3 종합 보고서만 읽었다.
- 실행한 것은 읽기 전용 명령뿐이다(git / sha256sum / grep / python read). 모델 로드, 테스트 실행, 학습·평가 없음.

## 1. 검증 로그 (읽기 전용 사실 확인)

| # | 확인 내용 | 결과 |
|---|---|---|
| V1 | preflight hash `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` | **파일 내용 SHA-256으로 현재 커밋 내용과 일치**(`sha256sum` 재현 ✓). 단 "committed blob" 표현은 부정확: git blob OID는 `b02af5877f5ee1fe8e195b291881a11ac39acda7`이고, r1 커밋(`0fce2e2`) 시점 내용의 SHA-256은 `849ec05b…`(r2 커밋 `57c69ca`에서 native-length/k-selection 필드가 추가돼 파일이 확장됨). **값 자체는 유효.** |
| V2 | preflight ↔ splits.json | train20/val20 ID가 `train[:20]`/`val[5:25]`와 정확히 일치, val 전체 161, common 15 IDs ⊂ val20, excluded 5 = 여집합 일치 ✓ |
| V3 | K 선택 규칙 산술 | train h≥753 = 16(contributors), val h≥753 = 15, val h≥754 = 14 → "K=753 최대 / 754에서 14" 재현 ✓, zero-margin 기록 ✓, native 512 전량 truncation(20/20) ✓ |
| V4 | F1–F8 fixtures | §3.2(known failure first)→§3.3(NA fail-closed)→§3.4(P/PA) dispatch 순서로 8개 전부 재현 ✓ — r3 residual R-3의 충돌이 실제로 제거됐다 |
| V5 | runner 통계 현실 | `bootstrap_paired(..., seed=20261108)` + `seeds_positive = (arr>0).sum()`(문서 수를 seed 개수로 오기) 실재 — §9.2 "새 모듈 / P0 helper 재사용 금지"의 근거 ✓. `--mode` 선택지에 `pm-diagnostic` 없음 → Phase 6 코드 미작성(freeze-후-코드 규칙과 일관) ✓ |
| V6 | 테스트 수 | `eval/tests/`의 `def test_` = 54개(정적 카운트; 실행 안 함). PM 계약 테스트는 미존재 — §13 DoD대로 구현 후 작성 대상 ✓ |
| V7 | P0 256 제한 | `p0_sanity`가 `source_max_length = args.target_max_length`(기본 256)로 기록 — §12 limitation 서술과 일치 ✓ |
| V8 | P0 수치 | 요청서 §4 = P0 보고서 = v0.2 §7 참고값 일치(train +3.7617 [1.8917, 5.6050] / val +5.2375 [2.5013, 8.0753] / val median 2.9739 / top-3 .4862 / real CE 12.7022·13.2352 > ln 250112 ≈ 12.43) ✓ |
| V9 | cap 산술 | 12×100 = 1,200 updates; D1 = 4×1 = 4; 합산 1,204 updates / 120+15+20 = 155 min ✓; 96 min = 0.8×2 h ✓ |
| V10 | r3 3-AI 합의 경로 | "2 CONTINUE(조건부) / 1 NARROW → r3.1 text-only errata → 재검토" — r3.1은 그 합의 경로를 정확히 이행한다 ✓ |

## 2. Q1–Q12

### Q1. Total factored contract

- 판정: **agree**
- 근거:
  - §2.1 tri-state, §2.2 `ANDn`/`ORn`/`NOT3`는 정의상 total이고 `ANDn`의 false-dominance(§4.2 "mixed false+NA → false")와 정확히 일치한다(any false → false가 NA보다 선행). `AND3`의 2/4/5 operand 사용 문제는 alias 금지 + 2/4/5 operand test 요구로 닫혔다(R-1 closed).
  - validity §3.2 → §3.3 → §3.4 → else `VALID`는 if/elif/else로 total이고 §3.5 불변식과 모순이 없다. `M_NOT_EVALUABLE`/`M_CONTROL_INVALID`가 validity에서 배제됐다(r3 구조 유지).
  - control §4.3은 분기가 완전하다. 마지막 else(`NOT_ASSESSABLE`)는 `m_evaluable=true ∧ p/pa valid ∧ m_valid=true ∧ m_pass_l=NA` 상태에서 도달 가능하고, 모든 분기가 도달 가능하다.
  - signal §5.3은 total이다. 특히 `l_signal=NA` ∧ copy_only/full_only=NA 조합이 안전하게 `NOT_ASSESSABLE`로 떨어진다.
  - §6.1 선언 도메인(3^5 + 3^2 + 3^4 + 3^1 + 3^4 + 3^2 + n_signal 22값)과 named cells 17개의 per-axis 전략은 ≈465 케이스로 실행 가능한 크기다(R-9 closed; full Cartesian 강제 없음).
- 남은 것(§3 Must-fix로 기록):
  - (a) §1 closure map의 "truth-table strategy | **§6.4**"는 r3.1에 존재하지 않는 절 참조다(실제는 §6.1–6.3). 표기 오류.
  - (b) signal dispatch에서 `n_signal<15` 분기가 validity 분기보다 **앞선다**. 따라서 n<15 ∧ validity=INVALID(예: `test_split_used=true`)인 상태의 1차 signal label은 `INCONCLUSIVE_SMALL_N*`가 된다 — validity failure가 small-N label로 가려진다. 결정적 결함은 아니다: 동작은 결정적·fail-closed이고, §5.4대로 (validity, control, signal, flags, reason)이 함께 기록되며 B0-B predicate는 `validity==VALID`를 요구하므로 승인 경로에는 영향이 없다. 그러나 이 선행 관계가 "의도된 계약"인지 텍스트로 명시돼 있지 않다. named cell 11(n=14 + L true)은 small-N 우선을 암시하지만 validity 교차 케이스 fixture는 없다.
  - (c) §3.4 내부 순서에서 `pa_valid=false`(known) + `pa_step100_path_ok=NA`(unknown) → `NOT_ASSESSABLE`(unknown이 known PA 실패를 가림), `p_valid=NA` + `pa_valid=false` → `NOT_ASSESSABLE`. 둘 다 fail-closed지만 "known failure first" 교리를 §3.4 내부에 일관 적용했는지 문장으로 고정돼 있지 않다(§3.5는 path=false 케이스만 다룸).
- 다음 단계:
  1. §1 map의 §6.4 → §6 수정.
  2. (b)에 대해 "small-N 우선"을 명시 문장 + fixture(n<15 ∧ validity INVALID → 기대 label)로 고정하거나 순서를 뒤집아 사전등록한다. 어느 쪽이든 **코드 작성 전에** text로 확정.
  3. (c) F9(`pa_path=NA`+`pa_valid=false`), F10(`p_valid=NA`+`pa_valid=false`) fixture를 추가해 현재 순서를 의도적으로 고정.

### Q2. L preservation

- 판정: **agree**
- 근거:
  - §5.2가 validity-INVALID(`*_VALIDITY_INVALID`)와 validity-NOT_ASSESSABLE(`*_VALIDITY_NOT_ASSESSABLE`) 라벨을 L/copy-only/full-only 각각 분리 — r3 residual R-2의 "unknown을 invalid로 과장"이 제거됐다.
  - small-N 라벨이 L 자격을 유지한다(`INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL/_WITH_COPY_ONLY/_WITH_FULL_ONLY`).
  - §5.4: raw L flags 항상 `flags`에 저장, `NOT_ASSESSABLE`에 `signal_reason`+raw flags, r3 §5.5의 "flags + L-qualified labels" 불변식 유지.
  - Q1(b)의 small-N-우선 상태에서도 small-N 라벨은 L 자격을 유지하므로 L 정보 자체는 보존된다(validity 정보만 1차 label에서 flags로 다운그레이드된다).
- 다음 단계: n<15 ∧ validity≠VALID 조합 fixture 1개 추가(현 출력 고정 또는 변경 결정을 기록).

### Q3. M preflight / cohort

- 판정: **agree**
- 근거:
  - preflight가 splits.json과 정확히 일치(V2)하고 K 규칙 산술이 재현된다(V3): contributors L 16 ≥ builder floor 10, P/PA 20; common cohort 15개 ID 전부 h_len ≥ 753, excluded 5개(751/718/708/750/728) 전부 < 753 — 15/20의 근거가 길이 규칙 하나로 결정적·재현 가능하다.
  - zero margin(`next_k=754 → 14`)이 preflight에 기록돼 코호트 민감성이 숨겨져 있지 않다. `M_COHORT_MARGIN`/`MARGINAL_SIGNAL_COHORT` 보고 체계와 정합.
  - full-K 11/20의 secondary 강등 근거(기여자 커버리지 부족)가 preflight `consequence`에 명시됐다.
  - endpoint 15/15는 런타임 계약(§8.3)이고 preflight는 길이 적격성만 보장한다는 구분이 정확하다(copy tokens ≥5 등은 실행 시 판정).
  - preflight hash가 현재 커밋 내용의 SHA-256으로 검증됨(V1).
- 다음 단계: 없음(내용 수준). 단 V1의 해시 **표현** 교정을 Must-fix #4로.

### Q4. M builder / endpoint / replay

- 판정: **agree**
- 근거:
  - `builder_ok`(§8.2) = contributors≥10 ∧ 모든 M 텐서 finite ∧ ‖M_POS_MEAN‖_F>0 ∧ ‖real_prefix‖_F>0 이고 `m_evaluable = ANDn(5)`에 포함 → zero/nonfinite norm·기여자 부족이 `M_NOT_EVALUABLE`로 라우팅된다(R-4 closed). M_NORM의 0-나눗셈은 ‖M_POS_MEAN‖_F>0 선행 조건으로 처리된다.
  - §8.3 endpoint identity: exact 15 IDs(preflight hash 바인딩) × 3 seeds × 4 arms × primary variants(M_POS_MEAN, M_NORM) × real/control CE finite × copy_ce≠None × copy tokens ≥5 × dup/missing 없음 × 15→14 대체 금지 — R-5 closed.
  - replay: r3 §8.6의 atol=1e-5/rtol=1e-4 separate-process 유지, r3.1 §10.5가 prelaunch `debug_replay_hash`(D1 artifact)와 post-run `final_checkpoint_hash`/`final_replay_hash`(결과 report gate)를 분리하고 checklist item 14 ≠ final hash를 명시(R-6의 hash 부분 closed).
  - M_NORM이 target real-prefix norm을 사용하는 **magnitude-matched, target-dependent** control임을 명시, target label leakage 금지, `M_PASS_NORM_CONFOUNDED` descriptive flag(§8.2) 유지.
- 남은 것:
  - "all M tensors finite"의 텐서 열거가 없다(M_POS_MEAN/M_NORM/M_GLOBAL 중 무엇?). M_GLOBAL은 secondary인데 nonfinite하면 primary 경로가 같이 막힌다 — 과도하지만 fail-closed. 열거 한 줄 권장.
  - §6.2 named cells(특히 5/13/14/15)의 fixture가 완전 입력 벡터(가용성 flag 전제)를 명시하지 않는다. 구현 시 cell 5는 availability 5개가 모두 true여야 `M_CONTROL_INVALID`가 나온다.
- 다음 단계: (1) builder_ok 텐서 열거 한 줄, (2) named cells에 완전 입력 전제 명시, (3) builder_ok 3변형 fixture(영 norm / 비유한 / contributors=9).

### Q5. PA

- 판정: **agree**
- 근거:
  - §7.2: acquisition control 명명, `PA_STEP100_NOT_VALID`, `ADAPTER_REGIME_LOSS` 금지, `PA_RETENTION` null 가능·비gate, scale/geometry caveat 기록 — r2/r3 요구가 유지된다.
  - v0.2 §6.1 PA_VALID = P와 동일 기준, P_RETENTION descriptive — 흐름 일관.
  - r3 §7.2의 `make_adapter(seed)` 후 `torch.manual_seed(seed)` 순서와 seed별 LoRA init 재현 test가 §13 "P/PA mode/init tests"로 유지된다.
- 남은 것:
  - r3 §7.2의 "PA step0는 별도 실행" 문장이 r3.1 §7.2에서 재진술되지 않았다. 충돌 규칙(r3.1 > r3)상 r3가 그대로 적용되지만, errata의 성격상 재진술이 안전하다.
  - D1 §10.3 phase 2 "step0 eval 20 docs"가 PA의 random-adapter step0 상태를 측정하는지, "별도 실행"과 어떤 관계인지 한 줄 정의가 없다.
- 다음 단계: (1) "PA step0 별도 실행" 재진술, (2) D1 phase 2와 PA step0의 관계 한 줄 정의.

### Q6. Cap / D0 / D1

- 판정: **conditional**
- 근거:
  - 산술 ✓(V9): 등록 12 units × 100 = 1,200 updates / wall 2 h / threads 6 / GPU none / retry none(§10.1). D0 0 updates·≤4 configs·≤15 min·seed 20261111·`labels_computed:false`·`not_a_result:true`·등록 cap 별도(§10.2). D1 4 arm-seeds × 1 update·≤20 min·seed 20261111 shared·별도 승인(§10.3). `T_proj = 3 × Σ_arm(100·t_train + t_step0_eval_20 + t_step100_eval_20 + t_M_build_15 + t_replay_15)`은 12-unit 구조와 정확히 대응하고 ≤96 min = 0.8×2 h. 합산 상한 1,204 updates/155 min에 "not a grant" 명시(§10.6).
  - 승인 경계 ✓: "D1 없이 3-seed 금지 / D0-only projection 금지 / timing probe 대체 금지"(§10.4), D1 eval counts 20/20/15/15 고정(R-6 closed), "each of 4 runs measures all five phases; missing phase → no projection".
- 조건(D1 승인 전 필요 — 이 라운드는 D1을 승인하지 않는다):
  - (i) **generation 스코프**: v0.2 §5.2·D2가 generation telemetry를 PM artifact 구성요소로 두는데, r3.1의 5개 timed phase에는 generation이 없다. 등록 런이 문서당 greedy generation을 수행한다면 T_proj는 이를 누락해 과소추정한다(96-min gate 오탐 위험). "등록 평가에 generation 없음(debug-only)" 또는 "t_gen phase 추가" 중 하나를 text로 확정해야 한다.
  - (ii) `t_M_build_15` 명칭 vs §10.3 phase "M builder **20 train / 15 target**": 측정 phase가 train-side encode(20건)를 포함함을 명확히 해야 과소추정을 방지한다.
- 다음 단계: (1) generation 스코프 문장 추가, (2) t_M_build 명칭/범위 정리, (3) "5 phase 전부 측정"을 checklist 독립 항목으로(Q10).

### Q7. Statistics

- 판정: **agree**
- 근거:
  - §9.1 상수(n_boot 1,000, percentile 2.5/97.5, bootstrap_seed=20261109, unit=document, seed_average_before_bootstrap=true) — r3 §9와 동일, threshold/seed 변경 없음 ✓.
  - §9.2 새 stats 모듈(`runner/c5_pm_stats.py`) + P0 helper 재사용 금지 — runner의 `seed=20261108`·`seeds_positive` 문서-수 오기가 실재함을 확인(V5)해 정당하다(R-8 closed).
  - `documents_positive`/`seeds_positive` 분리, 2/3 seed rule(v0.2 §6.2 "2/3 seeds > 0 on copy/full"·§7 "seed별 mean >0"과 정합), L>F paired per-document, top-3 share(분모 0/비유한 → null), leave-top-3-out, `tail_driven = leave_top3_mean ≤ 0 or top3_share > .50`, `MARGINAL_SIGNAL_COHORT` 비gate — 모두 실행 가능한 명세다.
  - n_signal ∈ {NA, 0..20}으로 16~19 복원(R-7 closed) + `n_signal=15 → MARGINAL_SIGNAL_COHORT=true`.
- 유의:
  - r3.1 §9.2의 "paired L>F > 0"은 축약 표현이다. v0.2 §6.2의 "L > F on copy"가 출처지만, 모듈 docstring/test에 정확한 정의(문서별 seed-평균 L−F의 부호 조건)를 명시해야 한다.
  - bootstrap_seed 20261109가 등록 학습 seed {20261108, 20261109, 20261110} 중 하나와 수치적으로 같다. 역할이 다르므로 결함은 아니지만 artifact에 역할 구분 한 줄을 권장한다.
- 다음 단계: (1) L>F 정의 문장, (2) seed 역할 구분 주석, (3) stats 모듈 테스트(seed 고정 재현 / documents_positive≠seeds_positive / 2-of-3 / 분모 0 → null).

### Q8. 남은 Must-fix

- 판정: **conditional** — r3 residual 9개는 전부 닫혔다(§1 map ↔ 실제 절 대조 확인, §15 self-assessment도 정확). 그러나 아래 micro-residual이 남는다.
- **Must-fix ranked list: §3 표 참조.**
- r3.1이 새로 만든 문제: **치명적 새 결함은 없다.** 신규 항목은 (1) §1 map의 §6.4 댕글링 참조, (2) `t_M_build_15` 명칭(R-6 수정 과정에서 생긴 표기), (3) n_signal 0..20 확장이 "등록 데이터에서 실제 도달 가능한가"라는 새 해석 의문을 만든 것(signal endpoint 길이 규칙 미명시 — Must-fix #5) 정도다. 전부 한 줄 수정 범위다.

### Q9. 동결·구현 승인

- 판정: **conditional**
- 조건: Must-fix 1–5(최소 1–4)를 **코드 작성 전에** text-only로 r3.1에 반영한다(동결 커밋에 포함하거나 r3.2 micro-errata로). 내 항목은 전부 routing/문서/fixture라서 threshold/seed/donor/step/LR 변경이 아니다 — errata 규율과 충돌하지 않는다.
- 반영 후: 동결 + 구현 + unit tests + D0 승인 가능.
- 구현 전 필수 test/contract:
  - §13 DoD 전 항목(ANDn 2/4/5, F1–F8 + F9/F10, builder_ok 변형, endpoint identity 15×3×4×variants, M seed aggregation, replay prelaunch/post-run 분리, stats module, truth-table per-axis + named cells, P/PA mode/init, `ADAPTER_REGIME_LOSS`/`M_CONTROL_NOT_VALID`/stale `seeds_positive` 부재 test, manifest/checkpoint/replay hash, `test_split_used:false` assertion).
  - **PM 결정함수·통계 테스트는 모델 불필요(pure function)여야 한다.** 현재 유일한 관련 테스트 파일(`test_c5_b0_metric.py`)은 `@unittest.skipUnless(MODEL.exists(), …)`로 로컬 모델 부재 시 전량 skip된다. PM 계약 테스트가 모델 의존이 되면 재현성이 떨어지므로, 결정함수/라벨/통계 테스트는 합성 fixture만 쓰도록 §6.3 원칙을 테스트 구조에도 강제할 것.
  - named cells의 완전 입력 벡터 명시(Q4).
- D0 승인 범위(조건 충족 시): 0 updates / ≤4 configs(F/L/P/PA) / ≤15 min / seed 20261111 / `labels_computed:false` / `not_a_result:true` / 등록 cap 별도 / timing claim 없음.
- 다음 단계: (1) micro-errata 반영 → (2) 동결 커밋(해시 알고리즘 표기 포함) → (3) 모델-free PM 테스트 작성 → D0.

### Q10. D1 / 3-seed

- 판정: **agree** (경계 유지는 충분; checklist 보강 2건)
- 근거:
  - D1 ≤20 min·no labels·`not_a_result:true`·별도 명시 승인(§10.3), D1 없이 3-seed 금지·D0-only projection 금지·timing probe 대체 금지(§10.4) — D1과 3-seed의 분리가 명확하다.
  - checklist 18항목(§11)이 전부 필요조건이고, prelaunch debug replay hash(item 14) ≠ post-run final hash(item 18) 구분이 명시됐다. debug seed 20261111 ∉ {20261108, 20261109, 20261110}(item 7).
- checklist에 빠진 것:
  - "4개 arm-run 각각 5 phase를 전부 측정(누락 phase → no projection)"을 독립 체크박스로 승격(현재 §10.3 요구가 item 5 "D1 timing artifact"에 암묵적으로만 담김).
  - item 6에 해시 알고리즘 표기("content SHA-256, LF") — "blob" 오해 방지(V1).
  - (Q6 조건) generation 스코프 확정 여부 확인란.
- 다음 단계: 위 2–3개 체크박스 추가. **D1 자체는 이 라운드에서 승인하지 않는다.**

### Q11. B0-B

- 판정: **agree**
- 근거:
  - §14 predicate이 r3.1 label 체계로 정확히 재진술됐다:
    ```text
    validity_status == VALID
    AND control_status == M_CONTROL_PASS
    AND signal_status == EXPLORATORY_L_SIGNAL
    AND m_valid == true (implied; consistency check)
    AND tail_driven == false (or explicitly reported)
    AND leakage/mode/metric pass
    AND artifact complete
    AND separate prereg/approval
    ```
  - `M_CONTROL_PASS`는 §4.3상 이미 m_evaluable=true ∧ p/pa valid ∧ m_valid=true ∧ m_pass_l=true를 함축하므로 m_valid consistency check는 well-defined다.
  - `EXPLORATORY_L_SIGNAL` 단독으로는 B0-B 불가, `M_CONTROL_PREFIX753_COHORT15` scope 인용 의무, full-K 11/20·P0·PA_RETENTION 비근거, B0-B/B1/B2/Stage C 별도(§14, §17) — 경계 유지 ✓.
  - 이 라운드는 어떤 결과도 가정하지 않은 상태에서 경계만 평가하며, B0-B/B1/B2/Stage C를 승인하지 않는다.
- 다음 단계: 없음(B0-B는 별도 사전등록 대상).

### Q12. 최종 판정

- **CONTINUE (조건부)** — 세부는 §4 블록.
- 판단 근거 요약: 9개 residual이 원문 대조로 전부 닫혔고, 산술·preflight·fixture가 검증됐으며, 남은 결함은 label routing 명시 1건과 timing-projection 명료성 1건을 포함한 one-liner 묶음이다. r3 라운드의 합의 경로("r3.1로 닫고 재검토")가 이행됐으므로 또 한 번의 full review 라운드를 요구하는 NARROW는 비례하지 않는다. 반면 residual을 문서화 없이 동결하는 것은 prereg 위생상 부적절하므로, 조건부 CONTINUE가 정확한 위치다.

## 3. Must-fix (ranked)

| 순위 | 항목 | 성격 | 시점 |
|---|---|---|---|
| 1 | signal dispatch에서 `n_signal<15` 분기의 validity 분기 선행을 명시적 계약으로 고정(현순서 유지 또는 변경 결정) + fixture (n<15 ∧ validity INVALID/NA) | label routing / prereg 명료성 | 동결 전 |
| 2 | D1 projection 완전성: 등록 평가의 generation 포함 여부 확정(포함 시 timed phase 추가, 배제 시 v0.2 D2 generation telemetry를 debug-only로 스코프), `t_M_build`가 20-train encode를 포함함을 명시 | timing gate 정확도 | D1 승인 전(동결 시 문장 추가 권장) |
| 3 | §3.4 known-vs-NA edge fixture화: F9(`pa_path=NA`+`pa_valid=false`), F10(`p_valid=NA`+`pa_valid=false`) + 교리 문장 | label routing(fail-closed 확인됨) | 동결 전 |
| 4 | preflight hash 표현 교정: "committed blob" → "content SHA-256 (LF)"; git blob OID `b02af587…` 병기 권장(값 `3ee3f1ca…`은 검증됨) | 문서 정확성 | 동결 전 |
| 5 | signal cohort(val20) L/F endpoint의 길이 규칙 한 줄 명시(v0.2 §4 donor-length 규칙 참조: F/L은 cache hidden length, 753 crop은 M 계약에만 적용) → n_signal 16..20의 데이터 도달성과 `MARGINAL_SIGNAL_COHORT` 구조성 여부 판단 근거 | 해석 명료성 | 동결 전 |
| 6 | 표기 정리: §1 "§6.4"→§6, "PA step0 별도 실행" 재진술, "paired L>F > 0" 정의, builder_ok 텐서 열거, named-cell 완전 입력 벡터, checklist 보강 2건(Q10) | 편집 | 동결 전 |

전 항목이 text-only이며 threshold/seed/donor/step/LR 변경이 아니다.

## 4. 최종 판정

```text
최종 판정: CONTINUE (조건부)
r3.1 동결: 조건부 승인 — Must-fix 1–5(최소 1–4)를 동결 커밋 전에 text로 반영할 것
구현+unit tests: 조건부 승인 — 동결 후. 모델-free pure-function 계약 테스트 포함(§13 DoD + F9/F10 + named-cell 완전 입력)
D0: 조건부 승인 — 동결 + unit tests green 후. 0 updates / ≤4 configs / ≤15 min / seed 20261111 / labels_computed:false / not_a_result:true / 등록 cap 별도 / timing claim 금지
D1: 이 라운드 미승인 (별도 승인; ≤20 min / 4 updates / seed 20261111 shared / 5 phase 전부 측정 / generation 스코프 확정 후)
3-seed: 이 라운드 미승인 (별도 gate; checklist 18항목 + Q10 보강 2건 + T_proj ≤96 min)
금지 범위: test 163(sealed) / P1 데이터 / T5Gemma2(D-108 STOP) / B0-B·B1·B2·Stage C / P0 재실행 / 결과 관측 후 threshold·seed·donor·step·LR 변경 / ADAPTER_REGIME_LOSS·M_CONTROL_NOT_VALID·stale seeds_positive 부활 / D0·D1 산출물을 결과로 보고하는 것
최대 compute: 등록 cap 그대로 — 12 units / 1,200 updates / wall 2 h / threads 6 / GPU none + D0 ≤15 min(0 updates). D1은 별도 승인 시에만 +4 updates / ≤20 min. 합산 상한 1,204 updates / 155 min은 승인이 아니라 상한 표기("not a grant").
Must-fix (ranked): §3 표
잘못된 전제: (1) "committed blob" — 실제는 content SHA-256(값은 검증됨, blob OID는 b02af587…); (2) n_signal 0..20이 등록 데이터에서 도달 가능하다는 암시 — L signal endpoint 길이 규칙이 명시될 때까지 해석 유보; (3) "54 tests"는 B0/A1 세대의 역사적 테스트이며 PM 계약 테스트는 아직 없음(synthesis §8 서술이 정확); (4) r3.1 §0의 "구조적 6/6 closure"는 r2 must-fix 그룹 기준 서술이고 r3 residual 9개와는 별개 개수다.
```

## 5. 한계

- 실행 검증 없음: 학습·평가·테스트 실행을 하지 않았다(요청 제한). 모든 코드 관찰은 정적 독해다.
- 단일 검토자 라운드: 3-AI 합의 절차가 아니며 이 보고서는 합성이 아니라 독립 의견이다.
- v0.1 원문, r1/r2 plan 원문, r3 라운드 review 파일 3건은 읽지 않았다(범위 밖; 교차검증에 필요한 v0.2/splits/decisions만 확인).
- 등록 런의 실측 시간(96-min gate), 캐시 실재성, copy-token 분포는 런타임 작업이라 확인하지 않았다.
- 이 문서는 승인이 아니라 검토 의견이다. 최종 승인권은 사용자에게 있다.