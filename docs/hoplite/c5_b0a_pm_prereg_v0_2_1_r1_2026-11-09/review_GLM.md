# C5 Phase 6 v0.2.1-r1 — External Review (GLM 5.3 Flash, max reasoning)

- 작성일: 2026-11-09
- 검토자: **GLM 5.3 Flash (reasoning max)** — v0.2.1-r1 신규 독립 검토 라운드. v0.2.1 라운드의 GLM 검토와 별개이며, 다른 모델(Sonnet/Sol)의 답을 재사용하지 않았다. subagent·추가 LLM 호출 없음.
- 검토 기준 HEAD: `4920953bca28ab502372780e67e3f87f41082ec2` (`docs: add C5 P/M v0.2.1-r1 review request`)
  - 동기화: `git fetch origin` → `git pull --ff-only origin main` → **"Already up to date"**, HEAD = `4920953…`. 요청서 기재 HEAD `0fce2e2`는 본 워크스페이스 shallow clone(depth 1)에 없어 로컬 diff 불가 — 현재 HEAD 트리의 원문을 기준으로 검토했다.
- 제약 준수: 학습·평가 실행 없음 / test 163 미개봉 / P1 미사용 / 저장소 수정은 이 보고서 파일 1개뿐 / threshold·seed·donor·step·LR 변경 제안 없음.

---

## 0. 요약

**판정: NARROW.**

r1은 v0.2.1 3-AI Must-fix의 골격을 실제로 닫았다. factored 3-status, tri-state Kleene, data-only M preflight(K_M_L=753), debug/registered 분리 회계, PA acquisition 재명명, statistics constants — 방향과 구조 모두 v0.2.1 대비 뚜렷한 개선이다. M preflight 수치를 reviewer가 독립 재계산했고 전부 재현됐다(§A).

그러나 **factored 재작성 과정에서 새로운 계약 결함 3개**가 생겼고, 동결 전 text-only r2로 닫아야 한다:

1. P/PA M validation(`m_valid_p`/`m_valid_pa`)과 M_VALID 전제(P_VALID∧PA_VALID)가 factored status 함수와 truth-table 어디에도 슬롯이 없다. r1이 `M_CONTROL_NOT_VALID`를 삭제했으나 대체 경로를 만들지 않았다.
2. "any path/test flag false → ASSAY_INVALID"(§2.3 rule 1)와 "PA path fail → PA_STEP100_NOT_VALID"(§2.3 각주)가 충돌한다. path/test flag 벡터가 열거되지 않아 기계적 판정이 불가하다.
3. §2.8 불변식 "L flag true인 조합은 signal_status가 L을 잃지 않는다"가 (l_signal=T, m_pass_l=NA, n≥15) cell에서 깨진다(→ NOT_ASSESSABLE로 L 소실).

r2가 Must-fix B-1~B-5만 수정하면(§B) **동결 → 구현 + unit tests → D0(0-update)** 승인이 가능하다. D1·3-seed·B0-B/B1/B2/Stage C는 본 라운드에서 승인하지 않는다. test 163은 sealed, P1 미사용, T5Gemma2는 D-108 STOP 유지.

---

## A. 독립 검증 (reviewer 재계산)

| 검증 항목 | 결과 |
|---|---|
| train20 h median = 768.5, val20 h median = 766.5 | ✓ 재계산 일치 (`m_cohort_preflight.json`) |
| K=753 → val target eligible 15/20, train contributors 16 | ✓ 재계산 일치 |
| **K_M_L 선택 규칙 역산** | **753 = (val_eligible ≥ 15 ∧ contributors ≥ 10)을 만족하는 최대 K** (K=754면 eligible 14로 감소). 단, 이 규칙은 r1/preflight 어디에도 명시돼 있지 않음 → B-4 |
| full-K 11/20 | per-target K_real에서 contributor<10인 target이 정확히 preflight의 9개 excluded와 일치 ✓ — 즉 full-K 불가능은 데이터 부재가 아니라 v0.2.1 규칙(contributor≥10)의 **구조적 귀결** |
| common cohort 15/20 | val20 − excluded5 = common_ids ✓ |
| val20 == splits.val[5:25], train20 == splits.train[:20] | ✓ (`splits.json`: train 1293 / val 161 / seed·sha256 포함) |
| preflight data-only | `data_only / no_model_forward / no_training: true` ✓ — 사용 값은 EG2 layer19 cache의 hidden **길이**뿐, 결과 데이터 미사용 |
| P0 raw artifact | train mean Δcopy 3.76173, CI [1.89169, 5.60496], positive 14/20 ✓ 보고서와 일치. 단 문서 수가 `seeds_positive` 키에 저장됨(runner/c5_mt5_lora_b0.py:395) — stale naming, B-6 |
| Adapter 구조 | `runner/c5_mt5_layer_probe.py:52-63` = Linear–GELU–Linear–LayerNorm(512→512) ✓ r1 §3.2 서술과 일치 |
| PM 결과 부재 | `reports/provenance/C5_b0a/pm/` 없음 ✓ — "no trained P/PA/M result"와 일치 |
| 테스트 수 | eval/tests 합계 54개 test 함수(2+1+7+11+10+11+12) ✓ — "54 tests" 주장과 일치. 단 PM 결정 로직·M·통계 테스트는 현존하지 않음 |
| runner 현실 | `c5_mt5_lora_b0.py` train mode는 frozen/lora 2-arm만 지원 → P/PA/M은 전부 신규 코드(r1 §0 "코드는 승인 후 작성"과 정합). **현존 어느 artifact에도 timing 필드 없음** → 2h cap 근거 미계측 |
| `delta_memfree` 정의 | v0.2 L176-177: `Δmemfree_full = mean_full_ce − real_full_ce`, `Δmemfree_copy = mean_copy_ce − real_copy_ce` — r1은 재기술하지 않고 상속(§F 한계 참조) |
| stale label | `REGIME_ERASES_SELECTIVITY`는 v0.2 L207/251/392에 존속(§12 B0-B 목록 포함). r1 §9가 label 체계를 갱신해 precedence로 덮음 — v0.2 단독 독자에게는 여전히 혼란 가능 → B-6 |

---

## B. 남은 Must-fix (ranked)

### B-1. m_valid_p / m_valid_pa + M_VALID 전제의 슬롯 상실 (최상위, r1 신규 결함)

**문제.** r1 §4.5는 `M_VALID = M_PASS_POS(P) ∧ M_PASS_NORM(P) ∧ M_PASS_POS(PA) ∧ M_PASS_NORM(PA)`이고 "M_VALID는 P_VALID와 PA_VALID를 전제로 한다"고 정의한다. 그러나 factored status 함수(§2.3-2.5)는 `m_evaluable`과 `m_pass_l`만 소비한다:

- P/PA M validation이 **계산되어 실패**(m_valid_p=false)해도 control_status는 m_pass_l=true면 `M_CONTROL_PASS`를 낼 수 있다. 이는 v0.2.1 headline rule 6(`M_CONTROL_NOT_VALID`)이 커버하던 cell을 r1이 삭제만 하고 대체하지 않은 것이다.
- p_valid/pa_valid=false(step100 screen 실패)여도 control_status는 `M_CONTROL_PASS`가 가능하다 — §4.5의 "M_VALID는 P_VALID∧PA_VALID 전제"가 status 함수에 강제되지 않는다.
- §2.8 truth-table 입력 8변수(path, p_valid, pa_valid, m_evaluable, m_pass_l, l_copy, l_full, n_signal)에 m_valid_p/m_valid_pa가 없다.

**왜 위험한가.** M control은 "real memory가 content-free mean memory(Δmemfree>0)를 이기는가"를 묻는 instrument validation이다(v0.2 L176-177). control arm(P/PA)의 validation이 실패했는데 L의 M 결과를 PASS/FAIL로 출력하면, instrument 자체가 무효인 상태에서 L 해석이 나온다 — v0.2.1 §2.5가 경고한 "L M 실패를 content-use 부재로 해석하지 않는다"의 역방향 오류(L M 성공을 유효한 긍정으로 해석)가 생긴다.

**수정(text-only).** control_status rule 1을 다음으로: `if m_evaluable is not true OR m_valid_p is false OR m_valid_pa is false OR p_valid is false OR pa_valid is false → M_NOT_EVALUABLE` (raw m_valid/p_valid/pa_valid는 flags에 보존). truth-table 입력에 m_valid_p, m_valid_pa ∈ {T,F,NA}를 추가한다(그리드 3^9×4 = 78,732조합 — 여전히 exhaustive 실행 가능). `M_NOT_EVALUABLE`로의 매핑은 "계산 실패"가 아니라 "통제로서 해석 불가"를 뜻하며, v0.2.1 §2.5 의미와 정합한다. `M_CONTROL_NOT_VALID` 라벨을 되살릴 필요는 없다.

### B-2. path/test flag 미열거 + rule-1↔PA-path 충돌 (r1 신규 결함)

**문제.** §2.3 rule 1은 "any path/test flag is false → ASSAY_INVALID"인데, 같은 절의 각주는 "PA path fail → PA_STEP100_NOT_VALID"다. `pa_step100_path_ok`가 "path/test flag"에 포함되면 두 규칙이 모순되고( rule 1이 먼저 발화), 포함되지 않으면 rule 1의 범위 자체가 정의되지 않는다. v0.2.1 §1.1은 `assay_path_ok / p0_path_ok / p_step100_path_ok / pa_step100_path_ok`를 열거했으나 r1은 이 목록을 재기술하지 않았다. 또한 §2.8의 입력 `path ∈ {T,F,NA}`는 복수 path flag를 하나로 뭉개므로, P-path-fail+PA-path-ok 등 규칙이 구분해야 하는 조합을 test할 수 없다.

**수정.** r2에 PM artifact의 path/test flag 벡터를 열거한다(최소: `assay_path_ok`, `p_step100_path_ok`, `pa_step100_path_ok`, M mechanics/replay flag). rule 1의 범위를 `assay_path_ok ∧ p-step100-path`로 한정하고, `pa_step100_path_ok=false → PA_STEP100_NOT_VALID`(validity 내 전용 분기), M mechanics 실패 → `m_evaluable=false`로 명시한다. truth-table의 path 입력을 열거된 개별 flag로 교체한다. P↔PA 비대칭(P path fail=ASSAY_INVALID, PA path fail=PA_STEP100_NOT_VALID) 자체는 방어 가능하다 — P path 실패는 M 전제 전체를 무효화하는 assay 수준 failure이고, PA path 실패는 P를 살려두므로 arm 수준 failure다 — 다만 이 근거를 문서에 한 줄 기록해야 한다.

### B-3. §2.8 불변식 위반 cell (r1 신규 결함)

**문제.** l_copy=T, l_full=T(l_signal=T), m_evaluable=T, m_pass_l=NA, n≥15인 조합: control_status=NOT_ASSESSABLE(§2.4 else). signal ladder에서 l_signal-true 분기는 control이 PASS/FAIL/M_NOT_EVALUABLE일 때만 발화하고, copy_only/full_only는 AND3(·,NOT3(·))로 모두 false, control도 PASS/FAIL이 아니므로 최종 else → **NOT_ASSESSABLE**. 즉 L signal이 signal_status에서 사라진다 — §2.8의 5번째 검증("L flag가 true인 조합은 signal_status가 L을 잃지 않는다")과 직접 모순된다. flags에는 L이 남으므로 정보 폐기는 아니지만, 문서가 스스로 요구한 불변식을 만족하지 못한다.

**수정.** (a) `l_signal true ∧ control_status == NOT_ASSESSABLE → L_SIGNAL_M_CONTROL_NOT_ASSESSABLE` label을 추가하거나, (b) control NA를 `L_SIGNAL_M_CONTROL_NOT_EVALUABLE`로 매핑하고, 불변식을 "signal_status가 L을 잃는 유일한 경우는 control_status가 NOT_ASSESSABLE일 때이며 flags는 항상 L을 보존한다"로 정정한다. (a) 권장 — label 추가가 사다리를 가장 적게 건드린다.

### B-4. K_M_L=753 선택 규칙 미기재

**문제.** 역산 결과 753은 "(common cohort ≥15/20) ∧ (contributors ≥10)을 만족하는 최대 K"다(§A). 그러나 이 규칙이 r1 §1 어디에도 명시되지 않아, 사후 선택으로 오독될 여지가 있다. 실제로는 data-only(no_model_forward) preflight이고 결과 전 결정이지만, 사전등록 문서의 목적상 규칙이 문자로 고정돼야 한다. 또한 15/20은 정확히 하한선(여유 0), K=753은 val 문서 1개의 길이(01331=753)와 일치하는 경계값이다 — 데이터가 frozen이므로 수용 가능하나, 재산출(recompute) 금지와 artifact 고정이 필요하다.

**수정.** r2 §1에 선택 규칙을 명시하고, `m_cohort_preflight.json`의 hash를 manifest에 고정하며, "실행 시 cohort는 preflight artifact의 common_ids를 그대로 사용하고 재계산하지 않는다"를 추가한다(현재 r1 §4.1은 "common IDs: m_cohort_preflight.json"로 참조만 한다).

### B-5. M builder 결정론 / M_VALID cohort / per-variant 집계 미지정

**문제.**

- M builder가 adapter를 어떤 모드로 돌리는지 미지정. dropout(.05)이 켜진 상태의 `A(h_i)`면 seed-평균과 replay equality(atol=1e-5, §4.7)가 무의미해진다. 기존 `evaluate_arm`은 `adapter.eval()`을 명시한다(runner:411) — builder도 동일하게 고정해야 한다.
- M_VALID(P/PA validation)의 target cohort가 미지정 — common 15인지 전체 20인지. 대칭성상 common 15로 고정하는 것을 권고하되, 어느 쪽이든 문자로 박아야 한다.
- M_NORM variant와 M_POS_MEAN variant의 delta가 각각 독립으로 seed-평균→bootstrap됨을 명시해야 한다(혼합 금지). M_NORM의 real norm은 seed-independent(데이터 속성)이므로 문제없다.
- `delta_memfree` 정의를 r1이 재기술하지 않는다(v0.2 L176-177 상속). precedence상 유효하지만 synthetic fixture test의 기준식이 필요하다.
- (경미) M_NORM의 "magnitude-matched negative control, strictly target-independent 아님" 자격 표기가 v0.2.1 §3.5에는 있으나 r1에는 없다 — 상속으로 커버되나 r2에 한 줄 재기술 권고.

### B-6. D0/D1 debug seed 미재기술 + 기존 코드 stale naming

**문제.**

- r1 §6.2는 D0에서 "no seed 20261108/09/10 training"만 말하고 D0/D1이 사용할 debug seed를 재기술하지 않는다. v0.2.1 §5.1의 미등록 seed 20261111이 상속되지만, D0/D1이 v0.2.1 §5의 "5 updates/arm" debug를 대체하는 새 구조이므로 r2에 명시해야 한다.
- 기존 runner의 `bootstrap_paired`가 문서 수를 `seeds_positive` 키로 저장한다(runner:395, P0 raw artifact에도 동일). r1 §5 금지규정("seeds_positive를 문서 수에 쓰지 않는다")과 DoD의 stale-naming 금지 test가 정확히 이를 겨냥한다 — PM 구현에서 반드시 `documents_positive`로 분리돼야 한다.
- (경미) v0.2 §12의 B0-B 금지 목록에 삭제된 `REGIME_ERASES_SELECTIVITY`가 여전히 있다(v0.2:392). r1 §9가 precedence로 덮지만, v0.2 단독 독자 혼란 방지를 위해 r2에 "v0.2 §12는 r1 §9로 대체" 한 줄을 권고한다.
- (관찰, 변경 아님) bootstrap_seed 20261109가 registered training seed 20261109와 숫자가 같다. 서로 다른 RNG stream(numpy `default_rng` vs torch)이라 기능적 문제는 없으며, **변경은 제안하지 않는다**(결과 후 seed 변경 금지 준수). 감사 혼란 방지 차원의 문서화만 권고.

---

## C. Q1~Q12

### Q1. Factored decision

- **판정: conditional**
- 근거: 구조는 factored가 맞다. r1 §2.1이 3-status를 항상 동시 출력하고 §2.7이 L flag 비억제를 보장하며 headline을 "편의 문자열, 판정 근거 아님"으로 강등했다. v0.2.1의 단일 13-rule precedence(MF-1: L_SIGNAL이 6/13 cell에서 숨음, `not_assessable` 미사용, dead cell)가 만든 정보 파괴는 실제로 제거됐다 — renamed precedence table이 아니다. 그러나 **total·self-consistent까지는 미달**: (i) B-2의 rule-1↔PA-path 충돌, (ii) B-1의 m_valid_p/pa·M_VALID 전제 슬롯 상실, (iii) B-3의 (l_signal T, m_pass_l NA) cell이 §2.8 불변식 위반. §2.8 exhaustive grid(현재 사양 3^7×4=8,748조합)는 실행 가능하나, 입력 열거 자체가 불완전하므로 "모든 조합에서 정확히 하나"의 증명이 현재 사양 위에서는 성립하지 않는다.
- 다음 단계: (1) B-2대로 path flag 열거 및 rule 1 범위 한정, (2) B-1대로 m_valid_p/pa·P/PA 전제를 control_status에 편입, (3) B-3대로 NA-control cell label 추가 후 §2.8을 수정판 사양에 대해 exhaustive test로 강제.

### Q2. Signal labels

- **판정: agree**
- 근거: 9 label 전부 도달 가능하다. `INCONCLUSIVE_SMALL_N`은 n_signal<15 첫 분기로 dead cell이 아니게 됐고(v0.2.1 MF-1 해소), `MEAN_CONTRAST_ONLY`는 §2.6 "M control pass, L donor signal 없음"으로 정의돼 도달 가능하고, `COPY_ONLY_WEAK`/`FULL_ONLY_WEAK`는 AND3(·, NOT3(·))로 tri-state와 정합, `L_SIGNAL_M_CONTROL_NOT_EVALUABLE`은 control M_NOT_EVALUABLE 분기에서 도달한다. L flag는 §2.7에 따라 flags에 항상 저장되고 signal_status는 validity와 독립 계산된다. 유일한 예외는 Q1-(iii)의 control-NA cell(label만 NOT_ASSESSABLE, flags에는 L 존속)이다. 또한 L signal flag의 계수식(mean≥.05 ∧ CI lower>0 ∧ paired L−F>0 ∧ 2/3 seeds>0)은 v0.2.1 §4.3에서 변경 없이 상속된다 — threshold 변경 없음 ✓.
- 다음 단계: (1) control-NA cell 처리(B-3), (2) "required signal flag"의 정확한 열거(l_copy_signal, l_full_signal — L−F paired 성분 포함 여부)를 r2에 명시.

### Q3. M preflight

- **판정: agree**
- 근거: 재계산으로 전 수치 재현(§A). K_M_L=753은 규칙상 최대K이고 contributors 16≥10, common 15/20. full-K 11/20은 contributor-floor의 구조적 귀결로, preflight가 이를 결과 전에 정확히 진단했다 — 이것이 r1의 가장 강한 부분이다. "M primary = target prefix"의 비용: estimand가 "전체 길이 real memory의 가치"에서 "공통 753-prefix 위치에서의 메모리 가치"로 바뀐다. 그러나 real/M이 동일 위치·길이로 paired라 contrast의 내부 타당성은 유지되고, full-K 결과는 secondary descriptive로 남아 정보가 폐기되지 않는다. excluded 5개는 최단 문서(708-751)이므로 M cohort는 길이 편향(long-side)이 있음을 표기해야 한다. 대안(M_NOT_EVALUABLE 수용)은 frozen cohort에서 M gate를 영구 무정보로 만들고 어차피 신규 사전등록을 강제하므로 prefix-753이 더 정보적인 선택이다. 단 zero-margin(정확히 15/20)과 K 선택 규칙 미기재(B-4)는 r2로 닫아야 한다.
- 다음 단계: (1) B-4대로 선택 규칙 명시 + preflight artifact hash 고정 + 재계산 금지 명문화, (2) 보고서 템플릿에 "primary = prefix M(K=753/512), full-K = secondary descriptive" 강제, (3) M cohort의 길이 편향을 interpretation에 표기.

### Q4. M aggregation/replay

- **판정: conditional**
- 근거: seed별 builder 재구성 → target별 delta seed 평균 → document bootstrap(§4.6)은 3 seeds×15 docs를 45 independent units로 오독하지 않고, builder는 train20 전용이므로 target(val) leakage가 없다. replay는 별도 프로세스 1회, atol=1e-5/rtol=1e-4, 초과 시 M_NOT_EVALUABLE(§4.7)로 pass/fail 오염을 차단한다. 빠진 조건: (a) builder adapter eval-mode/dropout-off 미지정(B-5) — replay equality의 전제, (b) m_valid_p/pa 실패와 P/PA step100 실패가 m_evaluable/control에 어떻게 매핑되는지 미정의(B-1), (c) M_VALID의 cohort 미지정(common 15 vs 20, B-5), (d) delta_memfree 정의 상속 의존(v0.2 L176-177).
- 다음 단계: (1) builder eval-mode 고정 + 결정론 unit test, (2) M_VALID cohort를 common 15로 고정, (3) delta_memfree 정의와 synthetic fixture test를 DoD에 추가.

### Q5. PA

- **판정: agree**
- 근거: `ADAPTER_REGIME_LOSS` 삭제 → `PA_STEP100_NOT_VALID`(§2.3/§3.3)로 인과적 함의가 제거됐고(MF-4 해소), PA가 acquisition control임을 명시했으며, PA step0 random re-basing 별도 실행, `PA_RETENTION` null 허용 + 비gate, mT5 final hidden vs EG2 layer19 scale/geometry caveat의 artifact 기록(§3.3)까지 v0.2.1 요구를 전부 반영한다. PA_VALID가 P_VALID와 동일 threshold(.05)를 쓰는 것도 threshold 미변경 원칙과 일치한다. adapter 구조도 코드와 일치 확인(§A).
- 다음 단계: (1) PA artifact에 scale/geometry caveat을 필드로 고정(서술이 아닌 schema), (2) PA delta의 기준이 random-rebase step0임을 artifact에 명기해 step0 baseline의 제한된 의미를 표기.

### Q6. Cap

- **판정: conditional**
- 근거: 산술은 성립한다 — registered 12 units × 100 updates = 1,200 = cap(r1 §6.1), D0 = 0 optimizer updates(§6.2), D1 = 4 arm-seeds × 1 update = 4 updates + 별도 명시 승인(§6.3), 별도 회계. v0.2.1 MF-3(1,220 초과 불가능)이 실제로 닫혔다. 그러나 (a) **2h wall-clock의 현실성 근거가 전무하다** — 현존 artifact에 timing 필드가 없고(§A), registered run은 1,200 train step + arm·seed당 step0/step100 평가(20 docs×5 donors×2 memories) + M eval을 2h 안에 해야 한다; (b) §6.5 timing projection(>0.8×cap이면 launch 금지)이 D0만으로는 산출 불가 — D0는 forward-only라 backward/optimizer 비용을 측정하지 못하고, projection의 실질 근거는 D1(1 update/arm)뿐이다; (c) D0/D1의 debug seed가 r1에 재기술되지 않았다(B-6).
- 다음 단계: (1) r2에 debug seed 20261111 재기술 + "timing projection은 D1 측정 기반" 명시(또는 D1 미승인 시 별도 timing probe 승인 경로), (2) D0/D1 artifact의 per-phase timing 필수 유지, (3) cap 초과 시 중단·보고 절차를 runner 요구사항에 명시(retry none 상속).

### Q7. Statistics

- **판정: agree**
- 근거: n_boot=1,000, percentile 2.5/97.5, bootstrap_seed=20261109, unit=document, seed_average_before_bootstrap=true, n_min_signal=15, `documents_positive`/`seeds_positive` 구분, top-3 share=sum(top3)/sum(all), leave-top-3-out mean, tail_driven rule(≤0 또는 >.50, label 자동변경 금지), 20-doc bootstrap anti-conservative caveat(§5) — executable 수준으로 고정됐다(MF-5 해소). 기존 `bootstrap_paired`(runner:384-398)가 동일 구조(numpy default_rng, percentile)를 이미 구현해 템플릿이 존재한다. 단, 그 코드는 bootstrap seed 디폴트가 20261108이고 문서 수를 `seeds_positive` 키로 저장한다(B-6) — r1 상수(20261109)와 키 분리는 구현 단계에서 강제돼야 하고 DoD test가 이를 겨냥한다.
- 다음 단계: (1) r2에 RNG 호출 패턴 고정(`np.random.default_rng(20261109)`, replicate 생성 순서), (2) L−F paired bootstrap이 document index를 공유 resample함을 명시, (3) PM artifact에서 documents_positive 키 사용 + stale-naming 금지 test 유지.

### Q8. 남은 Must-fix

- **판정: conditional**
- 근거: §10의 14항 closure 표는 대체로 정확하나 self-assessment이다. 실질 잔여는 §B의 6개: B-1(m_valid 슬롯 상실, 신규·최상위), B-2(path flag 미열거·rule-1 충돌, 신규), B-3(§2.8 불변식 위반 cell, 신규), B-4(K_M_L 규칙 미기재), B-5(builder 결정론·M_VALID cohort·per-variant 집계), B-6(debug seed 미재기술·stale naming). **r1이 새로 만든 문제 = B-1, B-2, B-3** — factored 재작성이 v0.2.1의 결함을 닫는 과정에서 새 cell을 열었다. 이들은 전부 text-only로 닫히며 threshold/seed/donor/step/LR과 무관하다.
- 다음 단계: (1) r2 작성(B-1~B-6만, §11 "MUST-FIX만 수정한 r2" 경로), (2) r2는 본 검토의 B 항목을 체크리스트로 삼아 각 항의 수정 위치를 명시, (3) r2에 대한 재검토는 경량(변경분만)으로 가능.

### Q9. 동결·구현 승인

- **판정: conditional**
- 근거: B-1은 decision contract의 의미론적 구멍(P/PA control 무효 상태에서 M_CONTROL_PASS 가능)이고 B-2는 사양의 기계적 실행 불가다 — 이 상태의 r1을 동결하면 truth-table test조차 "무엇에 대해 exhaustive인가"가 정의되지 않는다. 반면 B-1~B-5는 전부 text 수정이고 데이터·임계값을 건드리지 않으므로, r2 작성 → 동결 후에는 구현·unit tests·D0 승인이 정당하다. 구현 전 필수 test/contract: r1 §8 DoD 14항(전부 유지) + 추가 5항 — (i) control_status m_valid/step100-전제 편입 test, (ii) path flag 열거 및 PA-path cell test, (iii) L-보존 불변식 test(수정판), (iv) K_M_L cohort-freeze test(preflight artifact hash + common_ids + contributors 16/20 고정), (v) builder eval-mode 결정론 test. 모든 unit test는 synthetic fixture 기반(학습·등록 seed 사용 금지)이어야 한다.
- 다음 단계: (1) r2 작성·동결(commit hash 고정), (2) unit tests 전부 green(DoD+5항), (3) D0 실행 — 0 optimizer updates, ≤4 configs, ≤15 min, 별도 예산, `labels_computed:false`/`not_a_result:true`.

### Q10. D1 / 3-seed

- **판정: conditional**
- 근거: 경계 설계는 적절하다 — D1은 별도 명시 승인(§6.3), "D1 없이도 D0+unit tests로 implementation gate 통과 가능"이 명문화돼 있고, debug artifact는 `labels_computed:false`/`not_a_result:true`(§6.4)로 결과화가 원천 차단된다. 3-seed checklist 10항(§7)은 전부 필요조건으로 명시돼 있다. 빠진 항목: (a) preflight artifact hash 고정, (b) debug seed ≠ registered seeds 단언(20261111 ∉ {20261108, 09, 10}), (c) freeze commit 이후 threshold/seed/donor/step/LR 무변경 확인(diff 기반), (d) timing projection의 측정 근거 — D0는 forward-only이므로 항목 6(≤0.8×cap)의 실질 근거는 D1이며, D1을 승인하지 않으면 이 항목은 근거 없는 선언이 된다.
- 다음 단계: (1) checklist에 상기 4항 추가(10→14항), (2) D1 승인 여부를 timing 필요성과 명시적으로 연결해 별도 결정, (3) D0/D1 결과의 3-seed gate 부적격성을 artifact 필드로 재확인.

### Q11. B0-B

- **판정: agree**
- 근거: §9 "어떤 Phase 6 label도 B0-B/B1/B2/Stage C를 자동 승인하지 않는다" + "`EXPLORATORY_L_SIGNAL`은 exploratory이며 B0-B 승인이 아니다" — v0.2.1 MF-5의 stale reference 문제가 label 체계 갱신으로 닫혔고 자동 승인 경로가 없다. r1 label 체계로 재진술한 B0-B 필요조건: validity_status=VALID(P_VALID ∧ PA_VALID), M_VALID(P/PA 각각 POS∧NORM), M_CONTROL_PASS_L(L POS∧NORM), l_signal=AND3(l_copy, l_full)=true ∧ n_signal≥15 — 즉 signal_status=EXPLORATORY_L_SIGNAL(COPY_ONLY_WEAK/FULL_ONLY_WEAK/MEAN_CONTRAST_ONLY는 불충분), tail robustness(tail_driven=false 또는 보고), leakage/mode/metric 실패 없음, artifact 완전성(manifest/checkpoint hash/timing/test_split_used:false), 별도 review/approval.
- 다음 단계: (1) B0-B 사전등록을 r1 label 체계로 별도 문서로 작성(본 라운드 범위 아님), (2) B-1 수정이 control_status 의미를 바꾸므로 B0-B 필요조건 재진술 시 수정판 status를 기준으로 삼을 것.

### Q12. 최종 판정

```text
최종 판정: NARROW
r1 동결: 조건부 — r2가 B-1~B-5(text-only)를 수정한 뒤 commit hash freeze. B-6는 권고.
구현+unit tests: 동결 후 승인 — §8 DoD 14항 + 추가 5항, synthetic fixture only, 등록 seed 금지.
D0: 승인(동결 후) — 0 optimizer updates, ≤4 configs, ≤15 min, 별도 예산, labels_computed:false.
D1: 미승인 — 별도 명시 승인 필요. timing projection의 실질 근거이므로 승인 시 4 updates/≤20 min 이내.
3-seed: 미승인 — checklist(10+4항) 전체 + timing projection ≤0.8×cap + explicit user approval 후 별도 gate.
금지 범위: test 163(sealed), P1 데이터, T5Gemma2(D-108 STOP), B0-B/B1/B2/Stage C 자동 진행,
  결과 후 threshold/seed/donor/step/LR 변경, debug label의 headline 사용, M pass/fail label의 debug 산출,
  cohort 재계산(preflight artifact 고정), P0 Δcopy 절대값의 B0-A/PM 직접 비교.
최대 compute: registered 12 units / 1,200 updates / ≤2h wall / 6 threads / no GPU / no retry.
  D0 ≤4 configs ≤15 min(0 update). D1은 별도 승인 시에만 4 updates ≤20 min. 이번 라운드 승인 총계:
  학습 update 0(D0는 update 없음) + unit tests(학습 아님). 어떤 경우도 1,200을 넘지 않는다.
test 163: sealed 유지, 미개봉.
```

Must-fix (ranked): B-1 m_valid_p/pa·M_VALID 전제의 control_status 편입 > B-2 path flag 열거·rule-1 충돌 해소 > B-3 control-NA cell의 L-보존 > B-4 K_M_L 선택 규칙 명시·artifact hash 고정 > B-5 builder eval-mode·M_VALID cohort·per-variant 집계·delta_memfree 재기술 > B-6 debug seed 재기술·stale naming 제거.

잘못된 전제:

1. "r1이 v0.2.1 Must-fix를 닫았다(§10 전부 closed)" — 3개 신규 결함(B-1~B-3) 때문에 사실이 아니다. §10은 self-assessment다.
2. "text-only repair이므로 검토만 거치면 곧 동결 가능" — truth-table 사양이 아직 기계적으로 실행 불가(플래그 미열거)다. r2가 필요하다.
3. "2h cap" — 계측 근거가 전혀 없다. §6.5 projection이 방어선이지만 그 근거는 사실상 D1이다.
4. "full-K 11/20은 데이터 문제" — contributor-floor(≥10)의 구조적 귀결이다. preflight 진단은 정확했다.

---

## F. 검토 한계

- 워크스페이스가 shallow clone(depth 1)이라 `0fce2e2`(요청서 기재 HEAD)와 현재 HEAD `4920953`의 diff를 로컬에서 확인하지 못했다. 검토 대상 문서·artifact는 현재 HEAD 트리에서 직접 읽었고, `git pull --ff-only`가 "Already up to date"를 반환했으므로 origin/main 기준 최신이다.
- `docs/plan_c5_b0a_pm_prereg_v0_2.md`(v0.2)는 요청서 artifact 목록에 없으나, `delta_memfree` 정의와 stale label 존재 확인을 위해 필요 부분만 grep으로 확인했다(L176-177, L207/251/392). 전문 정독은 하지 않았다.
- P0/기존 B0 artifact의 실행 재현은 하지 않았다(실행 금지). 수치 대조는 저장된 artifact 값 기준이다.
- 본 보고서는 승인이 아니라 독립 검토 의견이다. 최종 승인권은 사용자에게 있다.