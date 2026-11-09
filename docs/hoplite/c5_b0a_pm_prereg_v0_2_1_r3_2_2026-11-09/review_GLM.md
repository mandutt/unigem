# C5 Phase 6 v0.2.1-r3.2 — Independent External Review (GLM 5.3 Flash max)

- 작성일: 2026-11-09
- 검토자: **GLM 5.3 Flash (reasoning max)** — OpenRouter `z-ai/glm-5.3-flash`. 이것은 r3.1 라운드와 의도적으로 별도인 **새로운 독립 검토 라운드**다. 다른 모델의 답변을 읽지 않았고 재사용하지 않았다.
- 동기화: `git fetch origin` → `git pull --ff-only origin main` → **Already up to date**. 결과 HEAD = **`6aac52f0c486f4137a47cf4e173be77e81975a80`** ("docs: add C5 P/M v0.2.1-r3.2 review request"). 요청서가 명시한 작성 기준 HEAD `44bbef6`는 `git fetch --deepen=3`으로 확인한 직계 부모이고, `git diff --stat 44bbef6..6aac52f` 델타는 **review 요청서 + review 오케스트레이션 파일(+690줄, 6 files)뿐** — plan 본문은 `44bbef6`과 동일하다. 따라서 본 검토는 요청서 기준 HEAD와 실질적으로 동일한 내용을 검토한다.
- 성격: **consultation-only.** 저장소 수정 없음(이 파일이 유일한 write). 학습·평가 실행 없음. test 163 미개봉(sealed 유지). P1 미사용. subagent/추가 LLM 미호출. T5Gemma2 **D-108 STOP 유지 확인**(`docs/decisions.md` D-108 = bridge 3/3 STOP).
- 요약 판정: **CONTINUE (조건부)** — §5 Must-fix(MF-1~MF-8, 전부 text-only)를 반영한 micro-errata를 freeze 커밋 전에 반영하면 r3.2 동결 + 구현 + unit tests + D0를 승인한다. D1 / 3-seed / B0-B / B1 / B2 / Stage C는 이 라운드에서 승인하지 않는다. **MF를 반영하지 않고 r3.2를 그대로 동결하는 것은 불가**하며, 그 경우 본 판정은 NARROW로 격하된다.

---

## 0. 독립성·방법

- 요청서 `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_1_R3_2_2026-11-09.md`를 전문 직접 읽었다.
- 지정 원문 7건을 모두 읽었다: `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_2.md`(900줄 전문), `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_1.md`(771줄 전문), `reports/C5_B0A_PM_PREREG_V0_2_1_R3_1_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/provenance/C5_b0a/m_cohort_preflight.json`, `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md`, `runner/c5_mt5_lora_b0.py`(802줄), `eval/tests/test_c5_b0_metric.py`.
- 교차검증을 위해 추가로 읽기 전용으로 확인한 것(요청서가 금지하지 않는 확인): `docs/plan_c5_b0a_pm_prereg_v0_1.md` / `v0_2.md` / `v0_2_1_errata.md` / `r3.md`(상속 계약 출처 추적), `reports/provenance/C5_clean/splits.json`(preflight ID 검증), `reports/provenance/C5_b0a/p0_native_sanity.json`(P0 통계 재계산), `docs/decisions.md`(D-108/D-112/D-117/D-120/D-121), git 이력·blob OID.
- r3.1 라운드의 `review_GLM.md`/`review_DS1017.md`/`review_SOL.md` 원문은 **읽지 않았다**(독립성 유지). 3-AI synthesis 보고서만 읽었다. 본 라운드는 요청서 §0.1대로 다른 모델의 답을 재사용하지 않았다.
- 실행한 것은 읽기 전용 명령뿐이다(git / sha256sum / grep / sed / python 읽기 재계산). 모델 로드, 테스트 실행, 학습·평가 없음.

---

## 1. 검증 로그 (읽기 전용 사실 확인)

| # | 확인 내용 | 결과 |
|---|---|---|
| V1 | 동기화/HEAD | `git pull --ff-only origin main` = "Already up to date"; HEAD `6aac52f0…`("docs: add C5 P/M v0.2.1-r3.2 review request"); 작업 브랜치 `hoplite/thespiai-a6d6e264`. `--deepen=3` 후 부모 사슬 `6aac52f → 44bbef6 → 93dfa92 → 0d88a48` 확인. `diff --stat 44bbef6..HEAD` = dispatch.sh(41) / prompt_ds1017(58) / prompt_glm(56) / prompt_sol(56) / watch_reviews.py(176) / EXTERNAL_REVIEW r3.2(303) = **+690줄, plan 본문 무변경** ✓ |
| V2 | preflight hash | `sha256sum reports/provenance/C5_b0a/m_cohort_preflight.json` = `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` — **§1.1 선언값과 일치** ✓. git blob OID는 `b02af5877f5ee1fe8e195b291881a11ac39acda7`로 별개 — §1.1의 "content SHA-256이며 blob OID가 아님" 서술이 정확 ✓ (r3.1 blocker "blob 표현" closed) |
| V3 | preflight ↔ splits.json | `train20_ids == train[:20]`, `val20_ids == val[5:25]` 정확히 일치, val 전체 161 ✓ |
| V4 | K 선택 산술 | train h≥753 = **16**(=l_contributors_at_k), val h≥753 = **15**, val h≥754 = **14** → "K=753 최대 / K=754에서 14 / zero margin" 재현 ✓. excluded 5 = h<753(751/718/708/750/728) 목록 일치 ✓. full-K L 11/20(excluded 9) secondary ✓. native 20/20 = 512 truncation ✓ |
| V5 | 상속 계약 출처 | v0.2 §6.2: `L_COPY_SIGNAL = mean Δcopy >= .05`, `L_FULL_SIGNAL = mean Δfull > 0` (lines 213/218) + v0.2.1 errata §4.3(paired per-document L−F, 2/3 seeds) — **r3.2 §9.2와 정확히 일치** ✓ |
| V6 | r3.2 내 ".05" 전수 조사 | 출현 7곳 = blocker 표기(32, 868), P_VALID(487), LoRA dropout(514), L_COPY_SIGNAL(622), "full은 >0; .05 아님" 해설(635/636). **full에 .05가 붙은 잔존 없음** — r3.1 blocker 1 완전 closed ✓ |
| V7 | fixture 16–18 도달성 | §5.3 dispatch로 손재현: F16(l both true, m_pass_l=true, control=PASS) → `EXPLORATORY_L_SIGNAL`; F17(l both false, m_pass_l=true, control=PASS) → `MEAN_CONTRAST_ONLY`; F18(l both false, m_pass_l=false → control=M_CONTROL_FAIL) → `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE` — 전부 primitive-derived, 도달 가능 ✓ (r3.1 blocker 2 closed) |
| V8 | F1–F11 재현 | §3.2(known failure first) → §3.3(assay-tier NA) → §3.4(P/PA) → else VALID 순서로 F1–F11 전부 재현. F9(p_step NA + p_valid false → §3.3 선행 → `NOT_ASSESSABLE`), F10(pa_path NA + pa_valid false → §3.4 path-NA 선행 → `NOT_ASSESSABLE`), F11(n<15 우선 + validity 별도 기록, §5.5) ✓ — r3.1 blocker 7/8 closed |
| V9 | runner 통계 현실 | `bootstrap_paired(..., seed=20261108)` + `seeds_positive = int((arr>0).sum())`(**문서 수를 seed 개수로 오기**) 실재 — §9.3 "새 모듈 / P0 helper 재사용 금지"의 근거 ✓. `--mode` choices에 pm 모드 없음 → Phase 6 코드 미작성(freeze-후-코드 규칙과 일관) ✓. donors 5 length-nearest 결정적 ✓, metric_smoke의 L−F가 common-id per-document 차 ✓, train_arm의 AdamW/wd .01/clip 1.0/`train_ids[step % n]`/adapter 1e-3·lora 1e-4 = §7.3 ✓, `--max-new-tokens` 기본 256 = §10.3 phase 5 ✓ |
| V10 | P0 수치 재계산 | `p0_native_sanity.json`에서 재계산: train mean 3.7617 / val mean 5.2375, **val median 2.9739 ✓, val top3_share .4862 ✓** (요청서 §4와 일치). leave_top3_mean train 2.5569 / val 3.1659 — 둘 다 >0, top3 ≤.50이므로 §9.4 기준을 적용하면 P0 val은 `tail_driven=false`에 해당하나 P0는 descriptive. ln(250,100)=12.4296 — untrained real CE 12.7022/13.2352 > 12.43 ✓ |
| V11 | cap 산술 | registered 12×100 = 1,200 updates / 2h wall; D0 = 0; D1 = 4×1 = 4; 합산 **1,204 updates / 120+15+20 = 155 min** ✓; T_proj 상한 96 = 0.8×120 ✓ |
| V12 | r3.2 회귀/소실 조사 | (a) §7.2의 "scale/geometry caveat 기록"(r3.1:431)이 r3.2에 **부재**; (b) r3 §8.3 builder recipe(`M_POS_MEAN[j] = mean_i A(h_i)[:753][j]` 포함, r3:520-536)이 r3.2에 **부재**; (c) `delta_memfree_full = mean_full_ce − real_full_ce` 정의(r3:549, v0.2:176-177)가 r3.2 §8.5에 **부재**; (d) `NOT3` 정의(r3.1:66) 부재, r3.2 §2.3(85-86행)은 **사용**; (e) §13 DoD에서 "truth-table per-axis + named cells"(r3.1:706)와 "PA acquisition labels"(r3.1:708) **삭제**; (f) §15 closure 표의 "blob 표현 → §1.4"는 **dangling**(실제 절은 §1.1) |
| V13 | 상태 확인 | D-108 STOP 유지(`docs/decisions.md`:122, bridge 3/3 STOP, test 163 sealed) ✓. `eval/tests`의 `def test_` 정적 합계 = **54**(실행 안 함; historical evidence) — PM 계약 테스트는 부재(§13 DoD대로 구현 후 작성 대상) ✓ |

---

## 2. Q1–Q12

### Q1. Total factored contract

- 판정: **agree**
- 근거:
  - §2.1 tri-state, §2.2 `ANDn`/`ORn`(2/4/5 operand 명시, 3-arity 절단 금지)은 r3.1에서 닫힌 residual을 유지한다. §4.2 "false-dominant; mixed false+NA → false / missingness-first 금지"는 `ANDn`의 any-false-first 순서와 정확히 같은 뜻이라 내부 모순이 없다.
  - validity §3.2 → §3.3 → §3.4 → else `VALID`는 if/elif/else로 **total**이다. r3.2가 r3.1 §4.3의 `p_valid not true → M_NOT_EVALUABLE`(NA를 접음)을 `false → M_NOT_EVALUABLE` / `NA → NOT_ASSESSABLE`로 분리한 것은 정밀화이며 §5.3의 `L_SIGNAL_CONTROL_NOT_ASSESSABLE` 라벨과 정합하다.
  - control §4.3의 모든 분기(`M_NOT_EVALUABLE`, `NOT_ASSESSABLE`, `M_CONTROL_INVALID`, `M_CONTROL_PASS`, `M_CONTROL_FAIL`)가 도달 가능하고, 마지막 else는 `m_evaluable=true ∧ p/pa valid ∧ m_valid=true ∧ m_pass_l=NA`에서 도달한다.
  - signal §5.3은 **total**이다. 특히 `l_signal=NA ∧ copy_only=NA ∧ full_only=NA`(예: l_copy=NA, l_full=NA) 조합이 안전하게 `NOT_ASSESSABLE`로 종결되고, `l_copy=true ∧ l_full=false`는 `copy_only=true → COPY_ONLY_WEAK`로, `l_copy=NA ∧ l_full=false`는 NA로 떨어짐을 손으로 확인했다.
  - §5.5 small-N precedence가 "의도된 계약 + F11 fixture"로 텍스트 고정됐다 — r3.1 MF-7의 small-N 축 closed. small-N이 validity를 숨기지 않는 `(validity, control, signal, flags, reason)` triple 기록도 명시됐다.
  - §6.1 선언 도메인(3^5 + 3^2 + 3^4 + 3^1 + 3^4 + 3^2 + n_signal 22값) + §6.3 named cells는 ≈465 케이스 규모로 실행 가능하다(full Cartesian 강제 없음 유지).
- 남은 것(경미): `validity_status`가 5개 열거값 외의 문자열이면 §5.3의 `!= VALID` 분기에서 INVALID로 처리된다. fail-closed 방향이지만, DoD에 **enum assertion**(허용 5값 외 입력 시 raise)을 명시하는 것이 안전하다(MF-8에 포함).
- 다음 단계: (1) §5.3 순서 그대로 단일 순수 함수로 구현(DoD 이미 요구), (2) enum assertion 추가.

### Q2. L predicates / fixtures

- 판정: **agree**
- 근거:
  - 상속 계약과의 일치를 원문에서 확인했다: v0.2 §6.2는 `L_COPY_SIGNAL = mean Δcopy >= .05 AND copy CI lower > 0 AND L>F on copy AND 2/3 seeds > 0 on copy`, `L_FULL_SIGNAL = mean Δfull > 0 AND full CI lower > 0 AND L>F on full AND 2/3 seeds > 0 on full`이고, v0.2.1 errata §4.3이 L−F를 paired per-document로 특정한다. r3.2 §9.2는 이 4-conjunct 구조를 **전문 재기술**하고 있어 정확히 일치한다. "threshold 변경 없음" 선언(§0, §9.2)과도 모순이 없다.
  - V6 전수 조사: r3.2 어디에도 full에 `.05`를 붙인 잔존이 없다. r3.1 blocker 1(`L_FULL_SIGNAL` `.05` 회귀)은 완전히 닫혔다.
  - fixture 16–18(V7): 세 fixture 모두 §6.2 원칙("primitive에서 derive; control_status 직접 주입 금지")대로 입력이 구성되고, §4.3(control derive) → §2.3(consensus) → §5.3(dispatch) 순서로 기대 label에 도달한다. 특히 구 fixture 17("M pass L false + control PASS")의 도달 불가능 문제가 m_pass_l=false → control=M_CONTROL_FAIL로 분리되어(F18) 해소됐고, m_pass_l=true ∧ l both false → MEAN_CONTRAST_ONLY(F17)가 도달 가능해졌다. r3.1 blocker 2 closed.
  - `seed_mean` = 해당 endpoint의 arm-L shuffled-minus-real mean, L−F와 별개 — errata §4.2("seeds_positive = seed_mean >0 count")와 일치. r3.2 §9.3의 "seeds_positive = seed mean only"도 같은 뜻이다.
- 다음 단계: (1) fixture 16–18 + F1–F11을 unit test로 고정(§13 DoD 대상), (2) L predicate 테스트에 경계값(copy = .05 exactly → true, full = 0 exactly → false) 포함.

### Q3. M preflight / cohort

- 판정: **agree**
- 근거:
  - V2: preflight content SHA-256이 선언값과 정확히 일치하고 blob OID와 구별된다(§1.1). frozen anchor로 사용 가능.
  - V3: preflight의 train20/val20이 `splits.json`의 `train[:20]`/`val[5:25]`과 정확히 일치 — cohort 정의의 데이터 출처가 닫혀 있다.
  - V4: K=753 선택 규칙("max K such that #train h≥K ≥10 and #val h≥K ≥15")의 산술이 재현된다: contributors 16(L), target-eligible 15, K=754에서 14, zero margin. excluded 5 ID 목록과 full-K 11/20(secondary)도 일치. `common_cohort_at_k=15 = required 15` — cohort_ok가 최소선을 정확히 충족한다.
  - endpoint 15/15 요구(§4.1)는 preflight `common_ids` 15개와 정확히 대응하고, §8.4가 "exact 15 IDs from preflight hash / no 15→14 substitution / no target replacement"를 요구한다.
- 유의점(기록용, 조치 아님): zero margin — `REPORT-news_r-01331-00001`의 h 길이가 정확히 **753**이므로 K 경계가 토크나이저/캐시 재계산에 민감하다. 길이 산출 경로가 preflight와 달라지면 15→14가 되고, 이는 fail-closed(`M_NOT_EVALUABLE`)라 안전하지만 실행 자체가 막힌다. 구현은 preflight hash로 ID·길이를 고정해야 하고(§8.4 이미 요구), D0에서 길이 재계산 일치를 확인하는 것이 좋다.
- 다음 단계: (1) 구현 시 preflight hash로 15 ID 고정, (2) D0에서 h-length 재계산 일치 assert 추가(선택).

### Q4. M builder / M_NORM / endpoint / replay

- 판정: **conditional**
- 근거:
  - **M_NORM 고정 공식 복원은 r3.1 MF-4를 닫는다.** §8.3의 `M_NORM(t) = M_POS_MEAN * (||real_prefix_t||_F / ||M_POS_MEAN||_F)` + "one global train-only mean matrix + per-target scalar magnitude + per-target matrix 금지"는 상속 계약의 자연스러운 독해와 일치한다: v0.2:130 "real memory norm에 맞춘 mean", errata §3.5 "**whole K×512 Frobenius norm** 사용 / per-row norm은 secondary / strictly target-independent가 아님 → magnitude-matched negative control 표기". r3의 모호한 `||real_prefix_753||_F` 표기를 `||real_prefix_t||_F`로 특정한 것은 명확화이며, `builder_ok`가 all-15 `||real_prefix_t||_F > 0`으로 §4.1=§8.3 내부 일관이다.
  - endpoint identity(§8.4): 15×3×4×2, exact IDs from preflight hash, 중복/누락/치환 금지, CE finite, `copy_ce != None`, copy tokens ≥5 — 하나라도 실패 → `M_NOT_EVALUABLE`. r3.1과 동일 유지 ✓.
  - canonical hash(§10.6): checkpoint(sorted keys, adapter+LoRA A/B, dtype/shape/little-endian/contiguous, SHA256) + replay(sorted `(doc_id, arm, seed, variant, endpoint)` canonical JSON, CE float64, SHA256) + golden-vector test + debug/final 분리 — r3.1 MF-5를 닫는 충분한 메커니즘이다.
  - **그러나 세 가지가 빠져 있다(V12):**
    1. r3 §8.3의 builder recipe(`M_POS_MEAN[j] = mean_i A(h_i)[:753][j]` — **753 위치 절단** 포함)이 r3.2에 없다. 이 절단은 `||M_POS_MEAN||_F`와 `||real_prefix_t||_F` 양쪽 값에 직접 영향을 주므로 §8.3 공식의 실행 가능성에 필요하다. (L 기여자 최소 길이는 756이므로 절단 없이는 positionwise mean 자체가 정의되지 않는다.)
    2. `delta_memfree_full = mean_full_ce − real_full_ce` 정의(r3:549, v0.2:176-177)가 r3.2 §8.5에 없다. 방향(mean-memory CE − real CE > 0 = real이 더 좋음)은 상속으로 여전히 유효하지만, 동결 문서가 self-contained여야 한다는 요구와 충돌한다.
    3. §10.6 replay hash key `(doc_id, arm, seed, variant, endpoint)`에서 **variant 집합**이 특정되지 않았다(replay가 signal real/shuffled 레코드를 커버하는지, M_POS_MEAN/M_NORM 레코드만인지). key space가 확정되지 않으면 "replay equality"의 대상 집합도 확정되지 않는다. 또한 F-arm의 M-variant endpoint 역할(gate? descriptive?)이 명시되지 않았다.
- 다음 단계: (1) MF-2/MF-3/MF-7을 r3.3에 반영, (2) golden-vector 기대 SHA-256을 test 상수로 동결(MF-8).

### Q5. PA

- 판정: **conditional**
- 근거:
  - §7.2에 PA = native memory + random adapter + decoder LoRA, **acquisition control**, `PA_STEP100_NOT_VALID`, `ADAPTER_REGIME_LOSS` 금지, `PA_RETENTION` null 가능/비gate, PA step0 별도 실행 — 명명과 gate 아님 계약은 유지·강화됐다. §3.4는 `pa_step100_path_ok=false`와 `pa_valid=false`를 모두 `PA_STEP100_NOT_VALID`로 모은다(단, path NA는 assay-tier/P-valid 규칙에 따라 먼저 처리 — §3.5 tier rule이 의도를 명시). 일관적이다.
  - **그러나 r3.1 §7.2의 "scale/geometry caveat 기록" 한 줄이 r3.2에서 무음 삭제됐다**(V12-a; r3.1:431 존재, r3.2 grep 부재). r3.2는 스스로를 "r3.1의 freeze blocker만 닫는 text-only errata"로 정의하므로, blocker가 아닌 기존 계약 라인의 무음 삭제는 원칙 위반이다. PA는 native-memory regime과 adapter+LoRA regime의 혼합이라 scale/geometry 차이 기록이 없으면 `PA_STEP100_NOT_VALID` 판정의 해석 근거가 약해진다.
- 다음 단계: (1) r3.3에서 §7.2에 caveat 라인 복원(MF-1), (2) §13 DoD에 "PA acquisition labels" 복원(MF-5).

### Q6. Cap / D0 / D1

- 판정: **agree**
- 근거:
  - V11 산술: registered 12 units × 100 updates = 1,200 / wall 2h / threads 6 / GPU none / retry none. D0 = 0 updates, ≤4 configs, ≤15 min, seed 20261111, `labels_computed:false`, `not_a_result:true`, 등록 cap과 별도. D1 = 4 arm-seeds × 1 update = 4, ≤20 min, seed 20261111 shared, 별도 승인, no labels. 합산 상한 1,204 updates / 155 min — "not a grant" 명시 ✓.
  - r3.1 MF-3이 지적한 누락이 모두 채워졌다: §10.3 timed phases에 **generation 20 docs × max_new_tokens=256**, **M builder 20 train + 15 target × 2 variants**(20-train M build 포함 명시), **replay 15 targets × 5 donors × 2 variants**, **load/checkpoint/process/report overhead**가 있고 "각 arm-run은 7 phase 전부 측정, missing phase → no projection"이다. §10.4 T_proj 공식에 `t_generate_20x256_arm`이 포함되고 ×3 seeds ×100 updates 구조가 산술적으로 정확하다.
  - 96 min = 0.8 × 120 min launch screen이고 실제 방어선은 §10.1의 2h wall + §10.5 cap abort/no retry/no extension이다.
  - 방향성 참고: D1에서 측정되는 `t_train_arm`은 프로세스 내 첫 update라 warmup 비용을 포함한다 → T_proj는 과대추정(보수적) 경향. cap screen 용도로는 안전한 방향이다.
- 다음 단계: (1) D1 승인 시 7-phase 측정 로그를 artifact로 저장, (2) "subset 사용 금지" 유지 확인.

### Q7. Statistics

- 판정: **agree** (조건 1개: MF-6)
- 근거:
  - §9.1 상수(n_boot 1000, percentile 2.5/97.5, bootstrap_seed **20261109**, unit=document, seed_average_before_bootstrap=true, n_min_signal=15)는 r3.1과 동일 유지다.
  - §9.3 새 모듈 요구(`runner/c5_pm_stats.py`, seed=20261109, `documents_positive`, `seeds_positive`=seed mean only, P0 helper 재사용 금지)의 필요성이 **코드에서 실재 확인됐다**(V9): runner의 `bootstrap_paired`는 seed=20261108이고 `seeds_positive` 키에 문서 수를 넣는다. 금지 조항은 근거 있는 금지다.
  - §9.2의 2/3 seed rule과 §9.4의 partial endpoint 처리(same retained IDs for copy/full/L−F, missing seed no pooling, excluded ID/reason, nonfinite CE excluded, n_signal은 valid endpoints만), top3_share denominator 0 → null, leave_top3_mean n<4 → null, tail_driven tri-state(known positive → true, both known false → false, else NA), B0-B false-only는 모두 명시적이고 구현 가능하다.
  - V10: P0 artifact에서 median/top3_share 공식을 실제로 재계산해 요청서 수치(val median 2.9739, top3_share .4862)와 일치시켰다 — 통계 정의가 기존 산출물과 동일 방식으로 계산 가능함을 확인.
- 조건(유일한 모호점): **결측 seed 시 L predicate의 행동**. "2/3 seed copy means > 0"을 3개 등록 seed 기준으로 고정하고, 등록 seed가 결측이면 그 predicate을 `not_assessable`로 명시해야 한다(가용 2개의 2/2로 대체하는 것을 금지). 현재 §9.4의 "missing seed는 pooling하지 않는다"만으로는 2-of-available 대체를 문맥상 금지하는지 불명확하다(MF-6).
- 다음 단계: (1) c5_pm_stats.py 단위 테스트에 seed 20261109/documents_positive/2-of-3/tail tri-state 포함, (2) P0 helper 미사용을 import 검사로 강제.

### Q8. 남은 Must-fix + r3.2 신규 문제

- 판정: **conditional**
- 근거:
  - r3.1 freeze blocker 9개는 §15 표와 본문을 교차검증한 결과 **전부 closed**다: §9.2 전문 재기술(V5/V6), §6.2 fixtures 16–18(V7), §10.3–10.5 ledger(V11), §8.3 M_NORM 공식, §10.6 canonical hash, §14 tail_driven hard false, §5.5+F11 small-N precedence(V8), §3.7 F9/F10(V8), §6.4 dangling 해소(§6.1–6.4 존재), §1.1 content SHA-256(V2).
  - 그러나 r3.2가 **새로 만든 문제**가 있다(V12): 유일한 실질 회귀는 §7.2의 scale/geometry caveat 무음 삭제(MF-1)이고, 나머지는 "상속에는 유효하지만 동결 문서에서 재기술되지 않은" 소실(MF-2/3/4), DoD 항목 삭제(MF-5), 명확화 필요 항목(MF-6/7), 표기 오류(MF-8)다. threshold/seed/donor/step/LR 변경은 없음을 V6에서 확인했다.
- 다음 단계: 아래 §3의 MF-1~MF-8을 r3.3 micro-errata로 반영.

### Q9. 동결·구현 승인

- 판정: **conditional**
- 근거:
  - 9개 blocker가 닫혔고 잔여 결함이 전부 text-only micro 항목이므로, **"MF 반영 → freeze" 경로는 승인 가능**하다. 반대로 MF를 반영하지 않은 채 r3.2를 동결하는 것은 승인할 수 없다(계약 라인 무음 삭제 + 공식 재기술 누락이 동결 문서의 품질 기준을 벗어난다).
  - 동결 후 구현 + unit tests + D0는 승인 가능하다. D0 요건(0 update / ≤4 configs / ≤15 min / seed 20261111 / `labels_computed:false` / `not_a_result:true` / 등록 cap 별도 / no timing claim)은 §10.2에 완전하다.
  - 구현 전 필수 test/contract(§13 DoD 전 항목 + 보강): pure decision function, ANDn 2/4/5, F1–F11, fixtures 16–18, validity INVALID vs NOT_ASSESSABLE 라벨, m_valid/M_CONTROL_INVALID, m_pass_l derivation, builder_ok(zero/nonfinite/contributor/15-norm), endpoint identity 15×3×4×2(중복/누락/치환), M_NORM 고정 공식(스칼라 배율 정확성), M seed aggregation, canonical hash golden vector(**기대 digest 상수 동결**), replay prelaunch/final 분리, signal val20/M15 분리, n_signal 0..20, stats module(seed 20261109/documents_positive/2-of-3), L_COPY/L_FULL predicate 경계 테스트, tail tri-state/partial endpoint, 결측-seed NA(MF-6), P/PA mode/init, 금지 라벨 부재(`ADAPTER_REGIME_LOSS`/`M_CONTROL_NOT_VALID`), stale `seeds_positive` 부재, manifest/checkpoint/replay hash, `test_split_used:false`, validity enum assertion.
- 다음 단계: (1) r3.3 micro-errata 작성·커밋, (2) freeze commit hash 확정, (3) 동결 후 구현+unit tests+D0 개시.

### Q10. D1 / 3-seed

- 판정: **agree**
- 근거:
  - 경계 유지: D1은 별도 승인, ≤20 min, no labels, `not_a_result:true`, seed 20261111 shared(등록 seed와 별개 — checklist item 7이 "20261111 ∉ registered seeds"로 고정). "D1 없이 3-seed 금지 / D0-only projection 금지 / timing probe 대체 금지"(§10.4)가 대체 경로를 모두 차단한다.
  - 3-seed checklist는 15항목(r3.1) → 20항목(r3.2)으로 확장됐고, 추가된 16(test163/P1 미사용)·17(B0-B 자동 금지)·18(post-run final hash validation plan; item 14 ≠ final hash)·19(canonical hash golden-vector green)·20(stats module tests green)은 적절하다. item 14가 prelaunch debug hash만 요구하고 final hash는 post-run gate라는 분리(§10.6)도 유지됐다.
  - checklist 보강 제안(필수는 아님): (a) MF-6 결측-seed → predicate NA 확인 항목, (b) 모든 artifact의 `test_split_used:false` 기록 확인 항목(DoD에는 있으나 checklist에 없음), (c) MF-7 replay record variant 집합 고정 확인 항목.
- 다음 단계: (1) checklist에 보강 3항목 추가, (2) D1 승인은 이 라운드에서 하지 않는다(별도).

### Q11. B0-B

- 판정: **agree**
- 근거:
  - §14가 hard gate다: `tail_driven == false`만 통과하고 `NA`/`true`는 모두 B0-B 불가("explicitly reported" 우회가 제거됨 — r3.1 MF-6 closed). `m_valid == true`(일관성 검사), `n_signal >= 15`, leakage/mode/metric pass, artifact complete, **별도 사전등록·승인**이 유지된다. `EXPLORATORY_L_SIGNAL` 단독으로는 B0-B 승인 아님, `M_CONTROL_PREFIX753_COHORT15` scope 인용 필수, full-K 11/20·P0·PA_RETENTION은 B0-B 근거 아님 — 모두 명시다.
  - §16/§17도 "D1/3-seed/B0-B/B1/B2/Stage C 별도", "freeze 후 threshold 변경 금지"를 재확인한다. **r3.2 결과가 좋아도 자동 승인 경로는 없다.**
  - 구조적 참고: `EXPLORATORY_L_SIGNAL` 라벨 자체가 dispatch(§5.3)상 validity VALID ∧ n_signal≥15 ∧ l_signal=true ∧ control=M_CONTROL_PASS를 이미 함축하므로, B0-B predicate의 앞 3개 조건은 라벨의 재진술이고 실질적 추가 gate는 `tail_driven==false` + artifact complete + 별도 승인이다. 이 중복은 안전 방향이다.
- B0-B predicate 재진술(r3.2 label 기준):

```text
B0-B eligibility =
    validity_status == VALID
  AND control_status == M_CONTROL_PASS
  AND signal_status == EXPLORATORY_L_SIGNAL
  AND m_valid == true            (consistency check; PASS가 이미 요구)
  AND n_signal >= 15             (=15이면 MARGINAL_SIGNAL_COHORT 라벨 병기, non-gating)
  AND tail_driven == false       (tri-state; true도 NA도 불가)
  AND leakage/mode/metric pass
  AND artifact complete          (manifest + final_checkpoint_hash + final_replay_hash)
  AND B0-B 별도 사전등록·사용자 승인

scope 인용: M_CONTROL_PREFIX753_COHORT15
비근거: full-K 11/20, P0 SENSITIVE_POSITIVE, PA_RETENTION
```

- 다음 단계: (1) B0-B는 r3.2 3-seed 결과 이후 별도 사전등록으로만 진행, (2) `tail_driven` 산출 근거(leave_top3_mean, top3_share 원값)를 artifact에 보존해 gate 재검증 가능하게 한다.

### Q12. 최종 판정

- 판정: **CONTINUE (조건부)** — 상세는 §4.

---

## 3. Must-fix (ranked, r3.3 micro-errata 대상 — 전부 text-only, threshold/seed/donor/step/LR 변경 없음)

| # | 항목 | 근거 |
|---|---|---|
| MF-1 | §7.2에 PA **scale/geometry caveat 기록** 라인 복원 | r3.1:431 존재, r3.2 부재(V12-a). blocker-only errata의 무음 삭제 — 유일한 실질 신규 회귀 |
| MF-2 | §8에 builder recipe 재기술: adapter/model eval + `no_grad`, contributor 판정, **`M_POS_MEAN[j] = mean_i A(h_i)[:753][j]`**(P/PA는 [:512]), M_GLOBAL secondary 위치 | r3:520-536 내용. 위치 절단이 `‖M_POS_MEAN‖_F`·`‖real_prefix_t‖_F` 양쪽에 영향 — §8.3 공식 실행 가능성에 필요 |
| MF-3 | §8.5에 `delta_memfree_full = mean_full_ce − real_full_ce`(copy 동일) 정의 재기술 | r3:549, v0.2:176-177. 동결 문서 self-containedness |
| MF-4 | §2에 `NOT3` 정의 복원(NOT3: true↔false, NA→NA) | r3.1:66 정의가 삭제됐는데 r3.2 §2.3(85-86행)이 사용 중 |
| MF-5 | §13 DoD에 "truth-table per-axis + named cells"와 "PA acquisition labels" 복원 | r3.1:706/708 삭제 확인(V12-e) |
| MF-6 | L predicate 결측-seed 규칙 고정: "3개 등록 seed 중 ≥2개의 seed mean > 0"; 등록 seed 결측 시 해당 predicate = `not_assessable`(2-of-available 대체 금지); §9.4 문구와 정합화 | §9.2 "2/3" + §9.4 "no pooling"만으로는 대체 해석 여지 |
| MF-7 | replay record의 **variant 집합**과 replay가 커버하는 endpoint 레코드 범위를 특정(hash key space 확정); F-arm M-variant endpoint의 역할(descriptive) 명시 | §10.6 key `(doc_id, arm, seed, variant, endpoint)`의 variant 미정의 |
| MF-8 | 경미/하드닝 번들: §15 표의 "blob 표현 → **§1.4**"를 §1.1로 수정(dangling reference); golden-vector **기대 SHA-256을 test 상수로 동결**; DoD에 validity_status enum assertion 추가 | §15:877 vs §1.1; §10.6/§13 |

---

## 4. 최종 판정

```text
최종 판정: CONTINUE (조건부)

r3.2 동결:      조건부 승인 — MF-1~MF-8을 반영한 r3.3 micro-errata를 커밋한 뒤
                freeze commit hash를 확정한다. r3.2를 그대로 동결하는 것은 불가
                (그 경우 NARROW로 격하). freeze 후 threshold/seed/donor/step/LR 변경 금지.
구현+unit tests: freeze 후 승인. §13 DoD 전 항목 + MF 보강(§2 Q9 목록)을 test contract으로.
D0:             freeze 후 승인. 0 update, ≤4 configs, ≤15 min, seed 20261111,
                labels_computed:false, not_a_result:true, 등록 cap 별도, no timing claim.
D1:             이 라운드 미승인 — 별도 승인 필요(7-phase 전부 측정, T_proj ≤96 min,
                seed 20261111 shared, missing phase → no projection).
3-seed:         이 라운드 미승인 — 별도 gate(checklist 1–20 + 보강 3항목).

금지 범위:      B0-B/B1/B2/Stage C 실행·자동 승인, test 163 개봉·사용(sealed),
                P1 사용, T5Gemma2(D-108 STOP 유지), threshold/seed/donor/step/LR 변경,
                결과 후 threshold 제안, P0 stats helper(20261108/오기 labels) 재사용,
                D1 없는 3-seed, D0-only projection, "timing probe" 대체,
                synthetic 아닌 fixture 입력, 등록 cap 초과·retry·연장.

최대 compute:   registered 12 units × 100 updates = 1,200 updates / 2h wall /
                6 threads / GPU none / no retry.
                + D0 ≤15 min(0 updates) + D1 ≤20 min(4 updates) — 각각 별도 승인 필요.
                combined prospective 1,204 updates / 155 min = 상한이지 승인이 아님.
                3-seed launch screen: T_proj ≤ 96 min.

test 163 지위:  sealed — 미사용·미개봉 유지. P1 미사용.

Must-fix (ranked): MF-1(§7.2 PA scale/geometry caveat 복원 — 신규 회귀),
                MF-2(builder recipe + [:753]/[:512] 절단 재기술),
                MF-3(delta_memfree 정의 재기술), MF-4(NOT3 정의 복원),
                MF-5(DoD 2항목 복원), MF-6(결측-seed → predicate NA 고정),
                MF-7(replay variant 집합 특정), MF-8(§1.4→§1.1 표기 + golden-vector
                상수 동결 + validity enum assertion).

잘못된 전제:    (a) "r3.2가 self-contained 동결 후보" — builder recipe/Δmemfree 정의/
                NOT3가 r3·r3.1에만 존재하고 r3.2는 이를 재기술하지 않았다
                (우선순위 규칙상 유효하지만 동결 문서로는 불완전).
                (b) "T_proj ≤96이 실제 소요 예측" — screen일 뿐; D1 첫-update warmup으로
                과대추정 경향이고, 실제 방어선은 2h hard cap + abort/no retry.
                (c) "P0 val이 tail 문제에서 안전" — top3_share .4862는 .50 기준 바로 아래
                (leave_top3_mean 3.1659 > 0이라 §9.4 기준상 tail_driven=false이지만
                마진이 얇고 mean 5.24 vs median 2.97 격차가 크다 — B0-B 판단 시
                reference로만 사용할 것).
                (d) 요청서의 "작성 기준 HEAD 44bbef6" — 실제 origin/main HEAD는
                6aac52f(요청서 추가 커밋)이지만 plan 본문 무변경이라 검토 유효성에는
                영향 없음.
```

---

## 5. 승인하지 않는 것 (재확인)

- Phase 6 실행, B0-B, B1, B2, Stage C — 이 라운드에서 승인하지 않는다.
- D1, 3-seed — 별도 승인/gate.
- test 163 — sealed 유지. P1 — 미사용.
- T5Gemma2 — D-108 STOP 유지.
- 본 보고서는 consultation이며 승인 문서가 아니다. 최종 승인은 사용자 결정이다.