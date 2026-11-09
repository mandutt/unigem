# C5 Phase 6 v0.2.1-r2 — External Review (GLM 5.3 Flash max)

- 작성일: 2026-11-09
- 검토자: **GLM 5.3 Flash (reasoning max)** — r2 라운드에 배정된 신규 독립 외부 검토자.
  r1 라운드의 GLM 검토(`docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r1_2026-11-09/review_GLM.md`)와는
  별개의 라운드이며, 다른 모델의 답을 재사용하지 않았다. 모든 근거는 본 검토자가 직접 읽고
  재계산한 것이다.
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_1_R2_2026-11-09.md` (전문 직접 열람)
- 검토 기준 HEAD: **`fc5680ef051bb6d00dbe74e7a0c08da193725b38`**
  ("docs: add C5 P/M v0.2.1-r2 review request")
  - 동기화: `git fetch origin` → `git pull --ff-only origin main` = **"Already up to date"**.
  - 요청서 작성 HEAD `308648e`과의 diff(`git diff --stat 308648e..HEAD`)는 본 요청서와
    오케스트레이션 파일(dispatch/prompts/watch_reviews)뿐이다. plan/report/preflight/runner/test
    원문은 `308648e`와 동일하므로 검토 근거가 달라지지 않는다.
- 제약 준수: 학습·평가 실행 없음. test 163 미개봉. P1 미사용. subagent/추가 LLM 호출 없음.
  파일 수정은 본 보고서 1개뿐이다. T5Gemma2는 D-108 STOP 유지로 다루지 않는다.

---

## 0. 독립 재검증 결과 (본 검토자가 직접 수행)

문서의 주장을 그대로 받아들이지 않고, 저장소 artifact로 직접 재계산한 결과:

| # | 검증 항목 | 결과 |
|---|---|---|
| V1 | preflight hash | `sha256sum(m_cohort_preflight.json)` = **`3ee3f1ca…37af`** = `.sha256` sidecar = `git cat-file blob HEAD:… \| sha256sum` (LF) **모두 일치**. r2 §1.4와 일치 |
| V2 | max-K 규칙 | JSON 길이표로 재계산: val20 h≥753 = **15**, h≥754 = **14** → 753이 최대 K ✓. train20 h≥753 = **16**(≥10) ✓. train/val median **768.5/766.5** ✓ |
| V3 | excluded-5 | `l_excluded_at_k` 5개 ID의 val h(751, 750, 718, 708, 728)가 h<753 집합과 정확히 일치 ✓ |
| V4 | common cohort 15 | `common_ids` 15개 = val h≥753 15개와 정확히 일치 ✓ |
| V5 | full-K 11/20 | v0.2.1 errata §3.2–3.3의 per-target `K_real`(=타깃 자신의 길이) + contributor≥10 규칙으로 재계산 → 제외 9개(h≥771) 재현. 예: `05258` h=771, train h≥771 = 9명(<10) → 제외 ✓. r2/preflight는 이 규칙을 재기술하지 않으나 errata 상속으로 정의됨 |
| V6 | 54 tests | `eval/tests` 7개 파일의 `def test_` 합계 = 2+1+7+11+10+11+12 = **54** ✓. 단, `test_c5_b0_metric.py` 7개는 모두 B0/P0 시대의 metric/tool test이며 Phase 6 P/M 계약 test는 **0개** |
| V7 | Phase 6 코드 부재 | `runner/ eval/ tools/ train/` 전체에서 `validity_status`, `m_evaluable`, `M_CONTROL_INVALID` grep = **0건**. runner 모드는 `smoke / metric-smoke / train(F/L) / p0-sanity`뿐. "코드는 승인 후 작성" 규칙이 실제로 지켜지고 있음을 확인 |
| V8 | P0 수치 | provenance JSON과 report 표 정확히 일치: train mean Δcopy **3.7617** [1.8917, 5.6050], 14/20 positive, Δfull 3.5027, real CE 12.7022 / wrong 16.4639. val **5.2375** [2.5013, 8.0753], 18/20, Δfull 5.2936, 13.2352 / 18.4727 ✓ |
| V9 | ln\|V\| | `ln(250100) = 12.4296` → 요청서의 "ln\|V\| 12.43" 확인(mt5-small vocab 기준, 산근 미기록) |
| V10 | stale hash | r2 §12 checklist 항목 6의 **`07c3fe4c…`** 는 `docs/ reports/` 전체 grep에서 **출처 없음**(phantom). §1.4가 고정한 `3ee3f1ca…`과 불일치 |
| V11 | stale naming live | 현 runner `bootstrap_paired`는 per-doc delta 배열에 대해 `seeds_positive = int((arr > 0).sum())`를 저장 — 실제로는 **문서 수**를 `seeds_positive`라는 이름으로 기록 중(P0 provenance에 `seeds_positive: 14`로 실재). r2 §13 DoD의 금지 test 대상이 유효함을 확인 |
| V12 | P0 source length | P0 provenance의 **`source_max_length: 256`**, `donor_count: 5`, `test_split_used: false`. 반면 preflight/r2 §1.2의 "native 512 all 20"은 **data-only 토크나이저 사실**(max_length=512 truncation). P0 민감도 증거는 256-token memory에서 획득된 것이며 512 경로에서 직접 측정된 적 없음 — 어디에도 기록 없음(MF-5) |

---

## 1. Q1 — Total factored contract

- **판정: conditional** (구조에는 agree, cell 1개 잔존으로 인한 조부)
- 근거:
  - r2의 factored contract는 v0.2.1의 단일 headline + P/PA interaction 표(`ADAPTER_REGIME_LOSS` 생성기)를 실제로 폐기했다. §2 flag inventory가 5개 path/test flag + 2개 P/PA valid + 7개 M flag + 2개 L flag로 **개별 열거**되어 있고, §2.4 precedence가 이름 붙은 flag 단위로 서술되어 있다. "이름만 바꾼 precedence 표"라는 비판은 r2에 대해 성립하지 않는다. 근거: §2.1 목록, §2.4 분기, V7(구현 부재로 문서만 존재).
  - 본 검토자가 §2.4/§5.2/§6.2의 입력 조합을 추적한 결과, control_status(§5.2)와 signal_status(§6.2)는 선언된 입력에 대해 **total**이다. control은 `m_evaluable not true`(false·NA 모두) → `M_NOT_EVALUABLE`, `m_valid=false` → `M_CONTROL_INVALID`, `m_valid=NA` → `NOT_ASSESSABLE`, `m_pass_l` T/F/NA → PASS/FAIL/NOT_ASSESSABLE로 빠짐없이 라우팅된다. r1 MF-1의 "P/PA M fail이 M_CONTROL_PASS로 샐 수 있다"는 구멍은 `m_valid` 슬롯 + `M_CONTROL_INVALID`로 닫혔다. 게다가 `m_evaluable` 정의에 `p_valid, pa_valid`가 포함되어(§2.2) P/PA invalid 상태에서 control PASS가 원천적으로 불가능하다(§5.2의 2차 검사는 중복이지만 방어적).
  - validity_status에 **잔존 hole 1개**: §2.4 분기 1은 `test_split_used is true`만 검사하고, 분기 2의 NA aggregate는 `assay_path_ok / p0_path_ok / p_step100_path_ok`만 포함한다. 따라서 `test_split_used=NA`는 **모든 분기를 통과해 `VALID`에 도달**할 수 있다. §7.2 요구사항도 "test_split_used=true는 항상 ASSAY_INVALID"만 규정하므로, exhaustive truth-table test는 이 cell을 잡아내지 못한다. 유출 게이트 flag의 NA가 VALID를 낼 수 있다는 것은 factored contract의 존재 이유와 정면으로 충돌한다.
  - 부수적 비대칭(VALID 위험 없음): 분기 2가 분기 3보다 앞서므로, 예컨대 `{assay=T, p0=NA, p_step100=F}`는 `ASSAY_INVALID`가 아니라 `NOT_ASSESSABLE`이 된다 — 알려진 p path 실패가 다른 flag의 NA에 가려진다. 반대로 분기 1에서는 false가 NA보다 강하다. 같은 path 축에서 우선순위가 분기마다 뒤집혀 있으므로 문서화가 필요하다. 또 `pa_step100_path_ok=NA`는 aggregate에서 의도적으로 제외되어(§2.4 주석) 통과하는데, `pa_valid=true ⇒ pa_step100_path_ok=true`라는 교차 제약이 §7.3 fixture에 명시되어 있지 않다.
  - 소요 도메인은 유한하다: §7.1 기준 3^5(path/test) × 3^5(status flags) × 3^2(l flags) × 5(n_signal) = **2,657,205** 조합 — 순수 함수 기준 exhaustive test가 현실적으로 가능하다(§7.3 "model/데이터 없이 실행" 요건과 정합).
- 다음 단계:
  1. §2.4에 `test_split_used is not_assessable → NOT_ASSESSABLE`(또는 ASSAY_INVALID 중 택일; NA≠used이므로 NOT_ASSESSABLE 권장) 분기를 추가하고, §7.2 요구사항에 대응 cell을 추가한다.
  2. §7.3에 교차 제약 fixture 추가: `pa_valid=true ⇒ pa_step100_path_ok=true`, `m_valid≠NA ⇒ m_evaluable=true` 등.
  3. 분기 2의 NA-masking(알려진 p-path 실패가 NOT_ASSESSABLE로 표기될 수 있음)을 §2.4에 명시적으로 문서화한다.

## 2. Q2 — L preservation / small N

- **판정: conditional** (consensus 설계에는 agree, 라벨 공백 1종 인정)
- 근거:
  - `l_signal` consensus(both T→T, both F→F, else NA)는 r1 synthesis MF-3이 권고한 AND3(`l_copy=F, l_full=NA → l_signal=F`)와 **의도적으로 다른 선택**이다. r2 §3은 이유를 명시한다 — "한쪽만 false인 경우를 no signal로 접지 않는다". 본 검토자는 이 편차가 합리적이라고 판단한다: F+NA에서 "신호 없음"을 선언하는 것은 부분 결측을 확증으로 바꾸는 일이고, consensus는 그것을 거부한다(더 보수적). 다만 §15 closure 표는 MF-3을 "closed"로만 표기하고 이 **편차 자체를 기록하지 않으므로**, r3에서 "MF-3의 AND3 세부 권고는 consensus로 대체했다"는 문장을 추가해야 검토 이력이 정직해진다.
  - L-qualified 라벨 체계는 l_signal=true의 모든 control/validity 조합을 커버한다: `L_SIGNAL_M_CONTROL_FAIL`, `L_SIGNAL_M_CONTROL_INVALID`(신설), `L_SIGNAL_M_CONTROL_NOT_EVALUABLE`, `L_SIGNAL_CONTROL_NOT_ASSESSABLE`, `L_SIGNAL_VALIDITY_INVALID` 신설로 "L signal + validity 불량 → EXPLORATORY 오인"을 차단한다. small-N 계열(`INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL/_WITH_COPY_ONLY/_WITH_FULL_ONLY`)은 r1의 "n<15는 항상 INCONCLUSIVE" vs "L 불변식" 충돌을 라벨 분리로 해소했다. `EXPLORATORY_L_SIGNAL`은 validity VALID + control PASS를 정의상 요구한다(§6.3).
  - 잔존 공백: 부분 결측(`l_copy=T, l_full=NA` → l_signal=NA)과 `n_signal=NA`는 n≥15에서 **generic `NOT_ASSESSABLE`** 로 가고, L은 flags+`signal_reason`에만 남는다. §6.4가 "문자 그대로의 불변식은 사용하지 않는다"고 선언했으므로 계약 위반은 아니나, headline 라벨만으로는 "L 정보 없음"과 "L 부분 증거"를 구분할 수 없다. `copy_only/full_only`는 반대편 명시 false를 요구하므로 이 공백을 메우지 못한다.
  - zero-margin n=15는 실행 가능하다: `MARGINAL_SIGNAL_COHORT=true` flag(V2에서 15/20 확인), 사전등록된 fallback("한 doc의 copy mask가 빠지면 n=14 → rule 변경 없이 `INCONCLUSIVE_SMALL_N` 계열", §1.3)이 결과 후 rule 변경 유혹을 차단한다. 또한 M cohort(길이 기반 15)와 n_signal(copy/full endpoint 기반)이 **서로 다른 카운트**임이 §6.1로 구분되어 있어, n=14 + cohort 15 공존이 모순 없이 표현된다.
- 다음 단계:
  1. §13 DoD에 `signal_reason` 어휘 열거를 추가하고, 부분-NA cell이 flags+reason으로만 보존됨을 명시한다.
  2. §15 closure 표에 MF-3 세부 권고(AND3) → consensus 대체 편차를 기록한다.
  3. truth-table fixture에 `n_signal=NA ∧ l_signal=true` 및 `l_copy=T ∧ l_full=NA` 조합을 포함시켜 generic-NOT_ASSESSABLE 경로를 고정한다.

## 3. Q3 — M preflight (K_M_L=753)

- **판정: agree**
- 근거:
  - 선택 규칙이 문자로 고정되었고(§1.1), 본 검토자가 JSON으로 독립 재계산하여 전부 재현했다: val h≥753=15, h≥754=14(경계 문서 `01331` h=753), train h≥753=16, median 768.5/766.5, excluded-5 일치(V2–V4). 규칙은 **length-only, 결과 전, hash 고정** — r1 MF-4의 요구를 정확히 충족한다.
  - zero-margin은 은닉되지 않았다: `zero_margin: true`, `MARGINAL_SIGNAL_COHORT=true`, 그리고 사전등록된 고장 경로(n<15 → rule 변경 없이 INCONCLUSIVE)가 있다. 753이 "15 longest-of-20"이라는 성격과 length-conditioned cohort임이 라벨 `M_CONTROL_PREFIX753_COHORT15`로 명시된다.
  - prefix 753 vs full-real-K 원칙: full-K(per-target `K_real`, contributor≥10)에서는 11/20이라 M gate 자체가 `M_NOT_EVALUABLE`이 된다(V5 재현). 753은 full prefix(~768까지)의 약 98% 위치를 보존하며, 잘리는 것은 tail 위치다. 이 손실은 (a) full-K 11/20을 **secondary descriptive**로 병행 보고하고, (b) `M_CONTROL_PREFIX753_COHORT15`를 "full-real-K control로 부르지 않는다"(§1.5, §9.3)는 선언으로 통제된다. gate의 목적이 "memfree 평균 memory가 real memory에 지는가"의 calibrate라면, 동일 위치·동일 길이 비교(§9.3)로 내부 일관성이 유지되므로 과도한 훼손이라고 보지 않는다.
  - 다만 재현성 관점에서 full-K 규칙의 정의(per-target `K_real`, contributor≥10)가 r2/preflight에 재기술되어 있지 않고 errata 상속에 의존한다(V5). secondary라도 한 줄 포인터가 있으면 좋다.
- 다음 단계:
  1. preflight JSON에 full-K 정의 포인터(errata §3.2–3.3 상속, per-target K_real + contributor≥10)를 한 줄 추가한다.
  2. freeze 후 K/cohort 재산출 금지(§1.4)와 hash 검증을 3-seed checklist에서 실행 가능한 형태로 유지한다(단, hash는 MF-1 수정 후).
  3. report template에 cohort label + excluded-5 + zero-margin flag 출력을 의무화한다.

## 4. Q4 — M builder / aggregation / replay

- **판정: agree** (경미한 명시화 보강 권고 포함)
- 근거:
  - builder 결정론이 고정되었다: `adapter.eval()`, `model.eval()`, `torch.no_grad()`(§9.2), seed별 builder 재구성(§9.6), 별도 프로세스 replay + checkpoint/state hash + `atol=1e-5, rtol=1e-4`(§9.7). r1 MF-5의 세 요구가 모두 반영되었다.
  - 집계 규칙이 누수-free다: target별 delta를 **seed 평균한 뒤** document bootstrap, "3 seeds × 15 docs를 45 independent units로 취급하지 않는다"(§9.6) — 유의미한 유의수준 과대 설계를 차단한다. common cohort 15/20에 P/PA가 **동일 target ID**로 평가되고(§9.3), L/P/PA별 per-variant 표 + pooled 표 별도 저장 요건이 있다.
  - `delta_memfree_full = mean_full_ce − real_full_ce`(copy 동일, §9.4)가 재정의되어 r1 MF-5의 미정의 항목이 닫혔다. `M_POS_MEAN`-only pass 금지, `M_GLOBAL` rescue 금지, `M_PASS_NORM_CONFOUNDED`는 descriptive-only — M_NORM이 타깃 real prefix의 Frobenius norm에 맞춰 스케일되는 순환성(confound)을 pass 경로에서 차단한다.
  - cohort 규칙: 길이 기반 eligibility(h≥753 / native≥512)와 endpoint 기반 n_signal의 분리로, cohort_ok와 n_signal이 어긋나는(예: 15 vs 14) 상황이 모순 없이 처리된다(§6.1 vs §2.2).
- 다음 단계:
  1. 구현 시 cohort_ok는 길이 기반 15, n_signal은 endpoint 기반임을 검증하는 unit test를 추가한다(두 카운트가 우연히 일치하는 것을 전제하지 않도록).
  2. replay test는 aggregate가 아니라 **per-doc CE** 비교로 수행한다는 점을 §9.7에 명시한다.
  3. replay state hash가 커버하는 범위(adapter + LoRA + builder 입력 순서)를 manifest 스키마에 열거한다.

## 5. Q5 — PA

- **판정: agree**
- 근거:
  - PA는 "acquisition control"로 명명되고(§8.2), `ADAPTER_REGIME_LOSS` 사용 금지 + `PA_STEP100_NOT_VALID` 도입으로 v0.2.1의 인과적 오명(regime loss)이 제거되었다. 현 runner/eval에서 `ADAPTER_REGIME_LOSS`는 문서 금지 조항 외 잔존하지 않음을 확인했다(grep V7 범위).
  - `pa_step100_path_ok=false`와 `pa_valid=false` 모두 `PA_STEP100_NOT_VALID`로 라우팅되고(§2.4), 이는 "PA path fail은 ASSAY_INVALID에 넣지 않는다"는 r1 MF-2 해법과 정확히 일치한다. P path fail만 `ASSAY_INVALID`로 통일되어 assay 전체와 PA 개별 실패가 구분된다.
  - `PA_RETENTION` null/무정보 허용 + non-gate, step0 random re-basing의 별도 실행, mT5 final hidden vs EG2 layer19의 scale/geometry caveat을 artifact에 기록하는 요건(§8.2)은 r1 §3.3을 온전히 상속·유지한다.
  - 경미한 공백: PA_VALID의 threshold가 r2에 재기술되지 않는다(r1 §3.2 상속, 충돌 규칙 r2>r1으로 유효). 동결 문서로서는 단일 지점 참조가 안전하다.
- 다음 단계:
  1. report template에 "PA_VALID threshold = P_VALID와 동일(r1 §3.2 상속)"을 명시한다.
  2. PA step0(랜덤 re-basing)와 P step0(zero-LoRA)이 서로 다른 regime임을 검증하는 test를 유지한다(r2 §13에 PA step0 test 있음).
  3. PA artifact에 scale/geometry caveat 문구를 필수 필드로 고정한다.

## 6. Q6 — Cap / D0 / D1

- **판정: conditional**
- 근거:
  - 산술은 정확하다: registered 12 units × 100 updates = **1,200**(§11.1), 4 arms × 3 seeds = 12 units와 정합. D0는 **0 optimizer updates**, ≤4 configs, ≤15min, seed 20261111(§11.2). D1은 4 arm-seeds × 1 update, ≤20min, 별도 승인(§11.3). 0.8×2h = **96분**(§11.4). D0/D1 모두 "registered cap과 별도"로 회계 분리되어 r1의 cap 혼용 문제가 닫혔다.
  - 승인 경계도 정합이다: "D0는 3-seed timing을 추정하지 않는다"(zero-update라 backward/optimizer 시간이 측정 불가 — r1 MF-6의 지적을 정확히 반영), "D1은 3-seed timing projection의 측정 근거", "D1 없이 3-seed timing projection을 주장하지 않는다", "D1은 implementation gate의 필수조건이 아니다"(§11.3). r1에서 충돌했던 checklist 항목 6(timing projection) vs §6.3(D1 optional)은 "D1 **또는 별도 승인된 timing probe**"라는 이중 경로로 해소되었다.
  - 잔존 모호성 1: "4 arm-seeds × 1 update, **seed 20261111**" — 4개 arm이 하나의 seed를 공유하는지, arm별 파생 seed인지 불명확하다. 파생이라면 파생 규칙이 없고, 공유라면 "arm-seeds" 복수 표기가 오해를 낳는다. debug seed가 registered {20261108, 20261109, 20261110}에 없다는 것은 checklist 항목 7이 보장하지만, D1 내부 seed 체계는 미기재다.
  - 잔존 모호성 2: §11.4의 외삽 공식 자체(per-phase timing → 3-seed wall-clock)가 정의되지 않았다. "projection은 finite이고 ≤96분"이라는 결과 조건만 있고, 어떤 phase timing을 어떻게 합산하는지는 D1 artifact 스키마에 달려 있다.
- 다음 단계:
  1. §11.3에 D1 seed 체계를 한 줄로 확정한다(예: "4 arms 모두 seed 20261111" 또는 "20261111에서 파생, 파생식 기재").
  2. §11.4에 timing projection의 산식(측정 phase 목록과 합산 규칙)을 명시하고, D1 artifact가 그 산식의 입력을 갖추도록 요구한다.
  3. D1에도 D0과 동일한 `labels_computed:false`, `not_a_result:true` 필드를 artifact 스키마로 명시한다(§11.3은 "no outcome labels" 문구만 있음).

## 7. Q7 — Statistics

- **판정: agree** (상수 고정·구현 가능, 세부 주의 3건)
- 근거:
  - 상수가 완전히 고정되었다: `n_boot=1000`, percentile 2.5/97.5, `bootstrap_seed=20261109`, `unit=document`, `seed_average_before_bootstrap=true`, `n_min_signal=15`(§10). `per_doc_delta[doc] = mean over seeds`, `pooled_mean`, `documents_positive = count(per_doc_delta > 0)`, `seeds_positive = count(seed_mean > 0)`로 두 카운트가 분리 정의되어 r1 MF-6의 stale naming이 계약 수준에서 닫혔다.
  - V11이 보여주듯 현 runner의 `bootstrap_paired`는 **문서 수를 `seeds_positive`라는 이름으로 저장**하는 stale 동작이 실제로 살아 있고, P0 provenance에 `seeds_positive: 14`(=양성 문서 14)로 기록되어 있다. r2 §13의 "stale seeds_positive 사용 금지 test"는 이 live 결함을 겨냔 것이므로 유효하다. Phase 6 구현은 §10 상수(특히 bootstrap seed 20261109)를 **명시적 인자**로 사용해야 하며, runner의 기본값 20261108을 실수로 재사용하면 안 된다.
  - top-3 share, leave-top-3-out, `tail_driven` flag-only(라벨 자동 변경 없음), `MARGINAL_SIGNAL_COHORT`의 라벨 중립성 — 모두 실행 가능한 정의다. `L>F` paired per-document difference 명시도 유지된다.
  - 주의 3건: (a) bootstrap seed 20261109가 registered training seed #2(20261109)와 수치가 겹친다 — RNG 도메인이 달라 기능적 결합은 없으나 기록해 두는 것이 좋다. (b) anti-conservative CI 경고가 "20-doc bootstrap"으로 표기되어 있는데 M cohort는 15다. (c) `n_boot=1000`과 percentile 방식은 상수로 고정되어 결과 후 변경 금지 규칙(§16)과 정합 — 본 검토는 어떤 통계 옵션 변경도 제안하지 않는다.
- 다음 단계:
  1. 구현 DoD에 "Phase 6 통계 경로에서 bootstrap seed == 20261109 명시 사용" 검증 test를 추가한다.
  2. anti-conservative 경고 문구를 "15-doc(M cohort)/20-doc"으로 확장한다.
  3. `documents_positive`/`seeds_positive`를 §10 정의 그대로 구현하고, runner 스타일의 stale 저장을 금지하는 test를 유지한다.

## 8. Q8 — 남은 Must-fix / r2가 새로 만든 문제

- **판정: conditional** (r1 Must-fix는 대부분 실질 close, r2가 신규 결함 2건 + 이식 결함 1건)
- r1 MF-1~6 closure 평가:
  - MF-1(m_valid 슬롯) — **closed**: §2.1 flag, §5.1 정의, §5.2 라우팅, §14 B0-B predicate에 `m_valid==true`까지 명시.
  - MF-2(path 열거/PA 충돌) — **closed**: §2.1 개별 열거, §2.4 precedence에서 P path→ASSAY_INVALID / PA path→PA_STEP100_NOT_VALID 분리, "pa는 any-path aggregate 제외" 명시. 단 test_split_used=NA hole은 신규(Q1).
  - MF-3(L 보존) — **closed(편차 있음)**: L-qualified labels + small-N family + §6.4의 불변식 재정의. AND3 세부 권고는 consensus로 대체 — 합리적이나 편차 기록 필요(Q2).
  - MF-4(K_M_L 규칙) — **closed**: §1.1 max-K 규칙 + hash(V1 검증) + label + excluded-5 + zero-margin.
  - MF-5(builder/집계/delta_memfree) — **closed**: §9.2/9.3/9.4/9.6/9.7.
  - MF-6(D0/D1 seed·timing gate·stale naming) — **closed(1건 예외)**: seed 20261111 명시, D0-only projection 금지, D1=3-seed 필수, `documents_positive` 분리. 예외: checklist 항목 9 "P/PA M_VALID true"는 r1 synthesis 권고를 **실행 순서 검증 없이** 이식했다 — M_VALID는 훈련된 P/PA checkpoint에서만 계산 가능하므로 launch 사전조건으로는 자기모순이다(MF-3).
- **r2가 새로 만든/드러낸 문제 — ranked list**:
  1. **MF-1: checklist 항목 6의 phantom hash `07c3fe4c…`** (§12, 672행). 저장소 전체에서 출처 없고(V10), §1.4가 고정한 `3ee3f1ca…`과 불일치한다. 커밋 `308648e`("pin r2 M preflight hash to committed blob")가 §1.4만 고정하고 checklist를 놓친 미완결 pin이다. 3-seed launch의 필요조건이 존재하지 않는 hash를 검증하도록 되어 있어, 동결 시 checklist 자체가 실행 불가능해진다. **가장 시급한 text-only 수정.**
  2. **MF-2: `test_split_used=NA → VALID` hole** (§2.4, §7.2). 유출 게이트 flag의 미평가 상태가 VALID를 낳을 수 있는 유일한 잔존 cell(Q1 상세).
  3. **MF-3: checklist 항목 9 "P/PA M_VALID true"의 순서 모순** (§12). launch 전에 검증 불가능한 사후 지식이 필요조건으로 들어 있다. "등록 스코프에 P/PA M 평가가 포함되며 M_VALID 결과는 보고될 뿐 사전에 가정되지 않는다"로 재분류하거나, report 게이트 checklist로 이동해야 한다.
  4. **MF-4: D1 seed 체계 모호성**(Q6) — "4 arm-seeds × 1 update, seed 20261111"의 공유/파생 불명.
  5. **MF-5: P0 증거 경로 불일치 무기록**(V12) — P0 민감도는 `source_max_length=256`에서 획득되었는데, 등록 P/PA M 경로는 prefix **512**이고 "512 all 20"은 토크나이저 사실이다. 어느 문서도 이 간극을 기록하지 않는다. P_VALID/PA_VALID가 실제 512 경로에서 측정되므로 gate 정합성은 유지되지만, P0의 증거 범위를 512로 읽으면 안 된다는 단서를 r3가 명시해야 한다. (P0 재실행이나 threshold 변경을 제안하는 것이 아니다 — 기록 추가가 전부다.)
  6. **MF-6(nit군)**: AND3의 5-인자/4-인자 사용(§2.2, §5.1) — variadic strong-Kleene conjunction으로 정의 1줄 필요. full-K 정의 포인터 부재(Q3). anti-conservative 경고의 15-doc 확장(Q7). 분기 2 NA-masking 문서화(Q1). bootstrap seed 겹침 기록(Q7).
- 다음 단계: 위 1–6을 **MUST-FIX만** 수정한 r3로 반영(§16의 자체 규정 경로). threshold/seed/donor/step/LR 변경은 일절 포함하지 않는다.

## 9. Q9 — 동결·구현 승인

- **판정: conditional**
- 근거:
  - **현문서 그대로의 동결은 승인할 수 없다.** 동결 대상 문서의 3-seed checklist가 존재하지 않는 hash를 참조하고(MF-1), 총합함수 주장에 유출 flag NA hole이 남아 있으며(MF-2), checklist 항목이 실행 순서 모순을 품고 있기 때문이다(MF-3). 이들은 전부 text-only이지만, 사전등록 문서의 성격상 "출처 없는 hash를 검증하는 절차"를 포함한 채 얼리는 것은 계약 무결성을 훼손한다.
  - 반면 r2는 r1 3-AI Must-fix 6건을 **실질적으로** 닫았다(Q8). 구조 개선은 미명(명칭 변경)이 아니라 실질이다: factored 3-status + tri-state + 개별 flag 열거 + hash 고정 preflight + builder/replay 명세 + cap 분리. Phase 6 코드가 아직 한 줄도 없음을 확인했으므로(V7), "구현은 freeze 후" 규율도 유효하다.
  - 따라서 본 검토의 권고는: **MF-1~MF-6만 반영한 r3 작성 → r3 freeze → 구현 + unit tests + D0 승인**. r3가 이 목록 이외의 변경을 포함하지 않는다면, freeze 승인에 또 한 번의 3-모델 풀 라운드는 불필요하다고 본다(본 목록과의 diff 대조로 충분). 최종 결정권은 소유자에게 있다.
  - 구현 전 필수 test/contract(§13 DoD 위에 본 검토가 추가하는 것):
    1. **순수 결정 함수**: torch/model import 없이 실행(§7.3), §7.1 도메인 **exhaustive** 2,657,205 조합 전수 실행 — 각 조합에서 `(validity, control, signal)` 정확히 1개, 입력 flag 무변형.
    2. `test_split_used=true → 항상 ASSAY_INVALID` **및 (수정 후) `test_split_used=NA → NOT_ASSESSABLE`** cell test(MF-2).
    3. `m_valid=false ∧ P/PA valid → M_CONTROL_INVALID`, `m_valid=NA → NOT_ASSESSABLE` cell test.
    4. PA path cell test: `pa_step100_path_ok=false ∧ p_valid=true → PA_STEP100_NOT_VALID`, P/PA 동시 path fail → P 우선.
    5. L 보존: raw flags 불변 + l_signal=true 조합 전부에서 L-qualified label 도달.
    6. M cohort preflight test: hash `3ee3f1ca…` 대조, common 15/20, excluded-5 불변.
    7. seed-average-before-bootstrap test(45-unit 오류 차단), replay per-doc CE equality(atol=1e-5, rtol=1e-4).
    8. 부재 test: `ADAPTER_REGIME_LOSS`, `M_CONTROL_NOT_VALID`, stale `seeds_positive`(V11의 live 결함 겨냥).
    9. manifest/checkpoint/state hash test, `test_split_used:false` assertion.
    10. 통계 상수 test: bootstrap seed 20261109 명시 사용, n_boot=1000, percentile 2.5/97.5.
- 다음 단계:
  1. r3(MF-1~6 only) 작성·커밋.
  2. r3 freeze commit hash 확정.
  3. 순수 결정 함수 + exhaustive truth table을 **가장 먼저** 구현하고, runner 확장(P/PA arm, M eval)은 그 뒤에 한다.

## 10. Q10 — D1 / 3-seed

- **판정: conditional**
- 근거:
  - D1(1-update smoke)과 3-seed를 별도 gate로 유지하는 경계는 이제 정합적이다: D1 = 별도 명시 승인 + 3-seed timing의 측정 근거(§11.3), 3-seed = 자체 checklist 15항목(§12) + 명시적 승인. r1의 "D1 optional vs timing gate 충돌"은 "D1 또는 별도 승인된 timing probe"로 해소되었다.
  - checklist 결함(수정 필요): 항목 6 phantom hash(MF-1), 항목 9 순서 모순(MF-3). 이 둘은 3-seed gate의 체크리스트 자체 결함이므로 Q9보다 우선 수정 대상이다.
  - checklist에 빠진 항목(본 검토 추가 제안): (a) **replay artifact hash** 존재 확인(M 평가의 재현성 증거가 launch 시점에 있는가), (b) **timing projection 산식과 그 입력의 완전성**(§11.4의 ≤96분 판정이 검증 가능하려면 산식 필요 — Q6), (c) D1 artifact의 `labels_computed:false / not_a_result:true` 필드 명시, (d) M 평가 설정(P/PA 포함)이 등록 스코프에 포함되어 있음을 확인하는 항목(MF-3 재분류의 대안 표현).
  - "모두 필요조건이며 충분조건이 아니다"라는 checklist의 성격 선언은 유지하는 것이 옳다.
- 다음 단계:
  1. 항목 6 hash 수정 + 항목 9 재분류를 r3에서 수행한다.
  2. 위 (a)–(d)를 checklist에 추가한다.
  3. D1 승인 요청 시 타이밍 projection 산식과 원시 per-phase timing을 함께 제출하도록 요건화한다.

## 11. Q11 — B0-B boundary

- **판정: agree**
- 근거:
  - §14는 "어떤 Phase 6 label도 B0-B/B1/B2/Stage C를 자동 승인하지 않는다"를 유지하고, predicate이 r2 라벨 체계로 재진술되어 있다: `validity_status == VALID AND control_status == M_CONTROL_PASS AND signal_status == EXPLORATORY_L_SIGNAL AND m_valid == true AND tail_driven == false (or explicitly reported) AND leakage/mode/metric pass AND artifact complete AND separate prereg/approval`. 이는 r1 synthesis가 요구한 재진술 그대로다.
  - `m_valid == true`는 `M_CONTROL_PASS`의 정의상 이미 함축되지만(§5.2–5.3), 명시적 중복은 방어적 가치가 있다. `EXPLORATORY_L_SIGNAL` 단독 불충분 선언, `M_CONTROL_PREFIX753_COHORT15` scope 명시 의무, "full-K 11/20 결과는 B0-B 근거가 아니다" — 3개의 차단 장치가 모두 유지된다.
  - 아울러 본 검토는 B0-B를 승인하지 않으며, r2 결과가 좋아도 이 경계가 자동으로 풀리지 않는다는 점을 재확인한다. B0-B는 별도 사전등록·별도 승인이다.
- 다음 단계:
  1. predicate을 r3에서 문자 그대로 유지한다(변경 없음이 원칙).
  2. report template에 cohort label + scope 문구 출력을 의무화한다(§14 요구의 실행 형태).
  3. `tail_driven` flag와 그 산식(top3_share > .50 or leave_top3_mean <= 0)이 artifact에 함께 기록되는지 DoD에서 확인한다.

## 12. Q12 — 최종 판정

- **판정: NARROW** (본 검토자 1/3 — r1과 동일한 판정 유형이나, 잔존 물량은 r1보다 한 등급 작다)
- 근거 요약: r2는 r1 Must-fix를 "이름 바꾸기"가 아니라 실질로 닫았다(V1–V11 독립 검증). 그러나 (1) launch checklist의 phantom hash, (2) 유출 flag NA→VALID hole, (3) checklist 항목 9의 순서 모순이 동결 텍스트 안에 남아 있어, 현문서 동결은 승인할 수 없다. 전부 text-only이며 등록 수치(threshold/seed/donor/step/LR)에는 손대지 않는다.

```text
최종 판정: NARROW
r2 동결:        현문서 그대로는 불가. MF-1~MF-6만 반영한 r3 동결은 승인 권고
구현+unit tests: r3 freeze 후 승인 권고 (순수 결정 함수 + exhaustive truth table 최우선)
D0:             r3 freeze 후 승인 권고 — 0 updates, ≤4 configs, ≤15min, seed 20261111,
                labels_computed:false, not_a_result:true
D1:             본 라운드 미승인 (별도 명시 승인 유지)
3-seed:         본 라운드 미승인 (별도 gate 유지; checklist는 r3 수정 후 유효)
금지 범위:      Phase 6 학습/평가 실행, B0-B/B1/B2/Stage C 자동 승인, test 163 개봉,
                P1 사용, T5Gemma2(D-108 STOP), 결과 후 threshold/seed/donor/step/LR 변경,
                D0/D1을 registered 1,200-update 회계에 포함하는 것
최대 compute:   r3 text 수정 + 구현/유닛테스트(CPU 전용, 순수 함수·synthetic fixture,
                등록 seed 미사용) + D0 ≤15분. 그 외 일절 없음.
test 163:       sealed 유지
```

---

## 13. Must-fix (ranked, 최종)

| 순위 | 항목 | 위치 | 성격 |
|---|---|---|---|
| 1 | checklist 항목 6 phantom hash `07c3fe4c…` → `3ee3f1ca…` | r2 §12 | r2 신규 결함(미완결 pin) |
| 2 | `test_split_used=NA → NOT_ASSESSABLE` 분기 + §7.2 요구 추가 | r2 §2.4, §7.2 | 잔존 totality hole |
| 3 | checklist 항목 9 "P/PA M_VALID true" 재분류(사후 gate로) | r2 §12 | r1 권고 무검증 이식 |
| 4 | D1 seed 체계(공유/파생) 명시 + projection 산식 | r2 §11.3–11.4 | 모호성 |
| 5 | P0(256-token) vs 등록 경로(512-prefix) 증거 범위 단서 기록 | r2 또는 report template | 무기록 간극(V12) |
| 6 | nit: AND3 variadic 정의, full-K 정의 포인터, 15-doc anti-conservative 문구, NA-masking 문서화, bootstrap-seed 겹침 기록, MF-3 편차(consensus) 기록 | 다수 | 문서 위생 |

## 14. 잘못된 전제 (본 검토가 발견한 것)

1. 요청서 key facts의 "native 20/20 at 512"는 preflight의 토크나이저 사실이며, **P0 민감도 증거는 source_max_length=256에서 획득**되었다(provenance `source_max_length: 256`). 양자를 동일시하면 P0 근거를 512 경로로 과독하게 된다(MF-5).
2. r2 §15 closure 표의 "closed"는 checklist 관련 2건(항목 6 hash, 항목 9)에 대해서는 과대 표기다 — 채택은 했으나 검증이 안 된 이식이다(MF-1, MF-3).
3. "r1 Must-fix 미 close"라는 전제가 있었다면 현재는 대부분 해소되었다. 다만 MF-3의 세부 권고(AND3)는 채택이 아니라 **consensus로의 대체**였으며, 이 편차는 문서에 기록되어 있지 않다(Q2).
4. "untrained CE 12.7/13.2 > ln|V| 12.43"의 12.43은 mt5-small vocab 250,100의 자연로그(12.4296)다 — 수치는 옳으나 산근이 어디에도 기록되어 있지 않다.
5. "54 tests"는 eval/tests 전체의 역사적 집계(2+1+7+11+10+11+12=54)로 확인되지만, 그중 Phase 6 P/M 계약 test는 0개다(V6). "54 tests pass"가 r2 계약의 검증 상태를 의미하지 않도록 주의가 필요하다.

## 15. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r2_2026-11-09/review_GLM.md` | 본 보고서 (유일한 신규 write) |

## 16. 제한

- 본 보고서는 승인이 아니라 독립 검토 의견이다. NARROW 1/3이며 다른 검토자의 판정과 독립적이다.
- 본 검토는 학습·평가를 실행하지 않았고, test 163을 개봉하지 않았으며, P1을 사용하지 않았다.
- 본 검토는 Phase 6, B0-B, B1/B2, Stage C, T5Gemma2를 승인하지 않는다.
- 제안된 모든 수정은 text-only이며, threshold/seed/donor/step/LR 변경을 포함하지 않는다.