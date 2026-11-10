# C5 F0 v1.12 — Independent Review (GLM)

- 작성일: 2026-11-10
- 검토자: GLM (`z-ai/glm-5.3-flash`)
- 대상: `docs/plan_c5_f0_v1_12_2026-11-09.md`
- **reviewed HEAD: `f994c1033729f2ebe2705bcad335a5f19d7018d6`** ("docs: add C5 F0 v1.12 review request", mandu, 2026-11-10 14:22:03 +0900)
- 동기화: `git fetch origin` → `git pull --ff-only origin main` → "Already up to date.", HEAD = `f994c103`. 이 HEAD에서 읽은 파일: `reports/EXTERNAL_REVIEW_C5_F0_V1_12_2026-11-09.md`, `docs/plan_c5_f0_v1_12_2026-11-09.md`, `docs/plan_c5_f0_v1_10_2026-11-09.md`, `reports/C5_F0_BLOCK2_3AI_REVIEW_SYNTHESIS_2026-11-10.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py` (추가 코드 검증: `runner/c5_mt5_lora_b0.py`의 `donors_for`/`token_losses`/`copy_ce`).
- 새 10라운드 블록 round **1/10**. 새 독립 검토, v1.11 및 이전 블록 결론 상속 없음.
- 추가 학습/평가 없음. test 163 sealed, P1 unused, T5Gemma2 D-108 STOP 확인. 파일 수정 없음 (지정 report만).

## 0. Verbatim paired E01−E11

v1.12 plan §6.3 인용 (그대로):

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

- Primary positive (§6.3, 그대로): `mean_D > 0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0`.
- `D(d)`의 재료 (§6.2, 그대로): `delta_c(s,d) = mean_donor( CE_wrong_donor - CE_real )`, per-doc seed average `delta_c(d) = mean_s delta_c(s,d)`.

## 1. Q1 — Donor-count / D1 custody

판정: **conditional agree**

근거:

- **Donor-count/load 모순 해소 확인.** §0 변경 1 + §13A.5(501–504행): `evaluated_donors==5`/`expected_donors==5`는 **R-only**, "D1 has no donor-count assertion and no donor-map load." §13A.4 D1 `cells`(445–454행)에 donor 필드 없음, `donor_map_loads: int (must 0)`(486행)와 `wrong_donor_ce_calls: int (must 0)`(484행)가 `mechanics_pass` 조건(495행)에 결합. 코드 검증상 자기정합: `runner/c5_pm_phase6.py`의 `m_records_for`(621행)는 `real_prefix`와 control(`M_POS_MEAN`/`M_NORM`)만 평가하고 wrong-donor 메모리를 건드리지 않으므로, D1이 M 120/cell(=15 targets×2 variants×2 memory_kind×2 endpoint, `m_records_for` 구조와 정확히 일치)을 계산하면서 `wrong_donor_ce_calls:0`·`donor_map_loads:0`을 유지하는 것은 모순이 아니다. D1 mechanics eval은 새 `c5_pm_f0_mechanics.py`(§11)가 real-memory-only로 수행하므로 donor map이 불필요하다. v1.11 DS 계열의 frozen table donor_count vs `donor_map_loads:0` 모순은 논리적으로 해소됨.
- **D1 seal 코어는 유지.** §5 D1: signal delta/per_doc/phase7/final 비materialize, `f0_d1_mechanics.json` 유일 출력 + exact-key allowlist, `d1_report.json` exact-path 금지 + `d1_sealed/` 부재 + gate negative test non-zero exit, checkpoint digest-only/삭제/`checkpoint_absent:true`, §13A.4(497–499행) writer/consumer allowlist + filesystem tests + crash path `partial:true`+`error`+checkpoint 삭제+"no other file".
- **잔여 결손 — 승인 blocker.** §0 변경 6(30–31행)이 "**allowed filesystem delta, success/crash inventory, sanitized logs**, checkpoint cleanup"을 약속하지만 본문에는 (a) D1 stage가 생성 허용된 파일의 명시적 delta(whitelist) 목록, (b) success/crash 후 파일 inventory assertion, (c) log 파일 inventory와 temp 경로 테스트가 어디에도 없다. 있는 것은 §13 405행("stdout/log must not print CE values")과 §13A.4 497–499행뿐이며, 이는 v1.10/v1.11 리뷰에서 이미 지적된 log/temp inventory 결손과 동일하다. 변경 요약이 본문 반영을 주장하지만 실제 반영되지 않았다.

다음 단계: (1) §5 또는 §13A.4에 D1 allowed-delta whitelist(생성 가능 파일의 정확한 경로 목록), success/crash 후 파일 inventory assertion, log/temp 경로 inventory 테스트를 명시. (2) R-only donor-count는 §6.1과의 정합 유지.

## 2. Q2 — Overrun / provenance

판정: **conditional agree**

근거:

- **4,939.884s 표기 통일 확인.** §12 372행: "D1 1,180.6s = 3 threads/arm measured (D-156); registered 4,939.884s = 2 threads/arm measured (D-157); neither is F0. `4,939.884s` is D-157 measured at 2 threads/arm; it is not an F0 measurement and cannot be used as one." — v1.10의 "Wall anchor (estimate): ... not a measurement" 모순 표현이 삭제되고 단일 문구로 통일됨. 377행 "Wall anchor: D-157 measured 4,939.884s at 2 threads/arm; not an F0 measurement"도 정합. 리뷰 요청서 §1-3의 주장은 사실과 일치.
- **Overrun 단일 규칙 — 부분 반영, 잔여 모순.** §12 377행에 D1 규칙 신설: "if measured wall exceeds 25 min → hard abort, `partial:true`, new code SHA + explicit stage re-approval." 그러나 (a) **§12 compute table 369행은 여전히 D1 cap을 "≤25 min provisional"로 표기**하여 같은 §12 내에서 377행과 충돌, (b) §5 D1 157행은 cap만 선언하고 overrun 시 귀결 문장이 없음, (c) §0 변경 2(23행)가 "§0/§5/§12/D0 모두 동일"이라 주장하지만 D0 136행은 별개 규칙("If measured >15 min, repair first")이며 P ≤10min·Q ≤15min cap에도 overrun 처분이 없음, (d) R의 **측정** wall이 96 min을 초과하는 mid-run 처분이 없음 — 379행 hard abort는 pre-run `T_proj_R` 추정치에만 적용되고 519행은 "R binding gate is measured wall ≤96 min"이라 말할 뿐 초과 시 행동을 규정하지 않음.
- **Provenance code-commit 요건 유지.** §11: `runner/c5_pm_f0*.py` committed at recorded SHA + clean tree before D0, D0/D1/R artifacts에 `code_commit`/command/input SHA. §13A.4 `provenance` 객체(476행) + `provenance_ok`(495행 mechanics_pass 조건). Phase 6 등록 드라이버 부재(MF-1) 재발 방지 조치로 충분한 방향.

다음 단계: (1) 369행 "provisional" 삭제, §5 D1·D0·P·Q에 각 cap의 overrun 처분을 §12 377행과 동일 문구로 기술. (2) R 측정 wall >96 min의 mid-run 처분(hard abort + partial + 재승인)을 §12에 추가.

## 3. Q3 — Q/R schema / counts

판정: **conditional (R schema 결손으로 승인 불가)**

근거:

- **Q schema 수정 확인.** §13A.10 `q/q_seed_audit/{seed}.json`(548–556행)에 `wrong_donor_ce_calls:int`(555행) 추가 — v1.11 리뷰가 지적한 "§0 변경이 약속한 필드가 Q schema에 없다"는 prereg 자체 모순이 해소됨. §13A.8(524–526행) "Q is the first execution (finiteness/shape only, no persistence); R is the first persisted/aggregated use"와 정합. §12 stage 순서(P→Q→D0→D1→R)에서 Q가 D1보다 먼저 wrong-donor CE를 실행하고 D1은 0, R이 최초 persisted 사용 — 3단계 카운트 체인은 자기정합.
- **D1 error enum 폐쇄형 확인.** §13A.4 490행 `error: enum{TIMEOUT,OOM,CE_NONFINITE,SHAPE_MISMATCH,CHECKPOINT_DIGEST_FAIL,OTHER_REDACTED}|null` — CE 값이 error 경로로 유출 불가. §13 405행과 합쳐 CE 누출 경로 차단. Q/P/D0 crash는 audit false → `NOT_EVALUABLE`로 fail-closed라 enum 미적용은 허용.
- **R schema — 승인 blocker.** §0 변경 5(29행)가 "R schema: CPU affinity/quota/thread-pool, donor-map/per-doc donor hash, **expected counts literal**"을 약속하지만, `r/r_mechanics_pass.json`(562–573행) schema는 `seeds/cells/updates_total/m_records/phase7_records/real_memory_ce_calls/wrong_donor_ce_calls/donor_map_loads/provenance_ok/r_mechanics_pass`뿐이고 (a) CPU 필드 전무(D1 `parallel` 객체 472행에만 존재), (b) `donor_map_sha256`/per-doc donor-ID hash 필드 전무, (c) expected-count literal 필드 전무 — "Expected R counts ... exact table frozen before R"(574행)가 어디에 저장되고 무엇과 비교되는지 스키마상 정의되지 않음(D1은 `expected_real_memory_ce_calls`(485행)이 있는데 R에는 없음). §6.1 191행이 약속하는 "R report records `donor_map_sha256` and per-doc donor-ID hash and asserts equality"의 sink인 `r/f0_report.json`의 스키마는 plan 어디에도 정의되지 않음. 약속된 gate 필드가 검증 불가능한 상태.
- **카운트 산술 검증(커밋된 코드 기준).** R counts: updates 900 = 3 cells×3 seeds×100 ✓, M 1,440 = 4×3×120 ✓(§3 "120 records/cell/seed"와 `m_records_for` 15×2×2×2 일치), phase7 7,200 = 4×3×600 ✓(`phase7_records_for` 15 targets×5 donors×2 variants×2 memory_kind×2 endpoint), generation 240 = 4×3×20 ✓. §13A.4 D1 `expected_real_memory_ce_calls`는 frozen operation table의 독립 instrumented run(§13A.4)으로 산출 — post-hoc 방지 유지.
- **잔여(비blocker).** Q의 `wrong_donor_ce_calls:int`(555행)에 expected 값·범위가 없어 Q stage 카운트가 감증 불가(Q는 wrong-donor CE를 실제 실행하므로 0이 아니어야 함); Q가 donor-crop/wrong-donor finiteness check를 몇 docs×donors로 수행하는지 미규정.

다음 단계: (1) `r_mechanics_pass.json`에 CPU 필드·`donor_map_sha256`·per-doc donor hash·expected-count literal(또는 별도 frozen table artifact 경로) 추가. (2) `r/f0_report.json` literal schema 신설. (3) Q에 expected `wrong_donor_ce_calls`와 check 범위 규정.

## 4. Q4 — Near-threshold / .0255

판정: **agree (경미한 표기 잔여)**

근거:

- **m_b/m_sign 분리 확인.** §7 304행: "b∈{+0.05,0}; m_mean=mean-b, m_lower=CI.lower-b, m_b=m_mean; m_sign=(#seeds>0)-2 is zero-based seed-sign margin; report all four; non-decisional." m_b≡m_mean(주어진 b에 대한 재표기)이라 중복이지만 자기모순은 아니고, m_sign=(#seeds>0)-2는 3 seeds에서 {-2,-1,0,1}로 0이 "2/3 seeds>0"(§6.3 seed gate)과 대응하는 올바른 zero-based 정의. §0 변경 7 요약과 본문 정합.
- **EQUIVALENT 정합.** §6.5 248행과 §7 282행 정의 동일(`CI_D.lower >= -.05 AND CI_D.upper <= +.05`), §12 380행 ".0255 is a nominal planning threshold only; realized CI governs" — §0 변경 8과 정합. EQUIVALENT가 practical-equivalence label이며 population equality claim이 아님(251행)도 명시.
- **잔여(비blocker).** (a) §15 Q4 609행이 여전히 "EQUIVALENT `SE_D<=.0255`"로 표기하여 §0 변경 8·380행과 표면 충돌(§15는 리뷰 질문 텍스트이므로 갱신 필요). (b) m_mean/m_lower/m_sign의 대상 통계량이 명시되지 않음 — primary D(mean_D/CI_D)인지 cell delta인지; near-threshold는 ALL_FAIL/INDETERMINATE 분기 문맥이므로 primary D로 읽는 것이 자연스러우나 명시 권장. (c) bootstrap n_boot 1000→10000 override(prereg §10.1 1172행 frozen `n_boot=1000`)는 §6.3에 "explicit override of frozen N_BOOT=1000"으로 선언되어 금지 항목(threshold/seed/donor/step/LR)이 아니며 통계 정밀도 상수 변경으로 허용 가능. 단 bootstrap seed 20261109가 registered training seed와 우연히 동일함 — 독립 RNG 스트림이라 무해하지만 문서 1줄 명시 권장.

다음 단계: §15 Q4 표기를 "EQUIVALENT realized CI_D, `.0255` nominal"로 갱신; near-threshold 대상 통계량 명시.

## 5. Q5 — R donor identity / hash

판정: **conditional (sink schema 부재로 승인 불가)**

근거:

- **Donor identity는 코드로 검증됨.** `runner/c5_mt5_lora_b0.py` `donors_for`(318–326행): 길이 최근접 + id 정렬 tiebreak의 결정적 함수, "same for all arms/seeds" — E00/E10/E01/E11이 동일 donor set을 갖는 §6.1 요건("donor sets identical for E00/E10/E01/E11 per doc")과 정합. Phase 6 `run_registered_unit`(905행)도 F/L에 동일 함수 사용.
- **Hash 약속은 있으나 sink 없음 — blocker(Q3과 동일 근원).** §6.1 191행 "R report records `donor_map_sha256` and per-doc donor-ID hash and asserts equality" — 그러나 `r_mechanics_pass.json`·`r/units` 어디에도 해당 필드가 없고 `f0_report.json` schema 미정의(§3). `donors_for`가 결정적이라 해시 비교는 실효성이 있음(캐시 재생성/allowlist 변경 감지), 스키마만 보완하면 됨.
- **CPU 필드는 D1에만 존재.** §13A.4 472행 `cpu_affinity`/`cgroup_cpu_quota`/`torch_threads`/`thread_pool_counts` — D1 mechanics에는 반영됐으나 R 측 artifact schema에는 없음(§5 R 178행은 `nproc`/`threads_per_arm`/`parallel_wall_s`/`contention_ratio` 기록만 명시). R이 96 min binding gate의 대상 stage인데 그 stage의 실행 환경 증거가 스키마에 없음.

다음 단계: Q3 다음 단계 (1)·(2)와 동일 — R artifact schema에 donor hash·CPU 필드 추가가 단일 fix로 해소됨.

## 6. Q6 — Scope / route

판정: **agree**

근거:

- §14 Non-goals: association-only claim("F0 tests adapter-as-configured in this fixed EG2/LoRA route"), ROUTE_STOP route-only("stops only the route as configured ... does not stop the EG2 track, does not rescue B0-B, and does not launch H3"), descriptive contrasts 명시, **lost controls**(MF-4 zero/permuted null·1-seed signal gate가 의도적으로 scope 밖이며 F0가 대체하지 않음)까지 자기 규정 — 과대 주장 방지 장치로 충분.
- §10 H3 완전 분리(별도 prereg), wrong-donor residual risk는 §13A.8(D1 무호출 absolute + Q first execution + R first persisted use + 1-doc unit test mitigation)로 관리. E01−E10/E01−E00 "not clean causal" 명시(§2).
- 잘못된 결과 해석 방지: §9 "M_PASS is not donor-specific content-use evidence", M evaluability는 PROTOCOL_VALID 요건이지만 M_PASS는 ROUTE_STOP 요건 아님 — Phase 6 MF-5 재발 방지 정합.

다음 단계: 없음 (유지).

## 7. 최종 판정

```text
최종 판정: NARROW
```

설계 방향은 수렴 중이고 v1.11 blocker 3건(Q schema 필드, error enum, 4,939.884s 통일)은 실제로 해소됐으며 donor-count/load 모순도 코드 수준 검증으로 자기정합이 확인됐다. 그러나 §0 변경 요약 5·6번(R schema 확장, D1 custody 추가)이 본문에 반영되지 않았고 overrun 단일 규칙도 §12 내부 모순(369 vs 377행)을 남긴다. 이는 전부 스키마/문구 수준의 수정 가능한 결손이므로 STOP이 아니라 NARROW다.

```text
Init:       agree — §4 contract·assertion 9항목·KAT·Phase 6 I/O assert(13A.6) 유지, build_arm_f0 격리 명확.
D1:         conditional — seal 코어 유지·error enum 폐쇄형 확인. custody 추가 항목(allowed-delta/inventory/log-temp test) 본문 부재 = blocker.
STOP/MDE:   agree — PASS/EQUIVALENT/harm/benefit 정의·우선순위(290행)·reason enum(305–310행) 자기정합. .0255 nominal-only 확인. MDE .019170(SE)·50% .0376·80% .0537는 F−L planning proxy로 한정됨(380행) — 유지 적절. realized CI_D governs 문구 일관.
Cohort:     agree — 15 length-eligible fixed cohort + fixed donor graph 조건부 estimand, 20-doc 일반화 금지, non-copyable drop 시 NOT_EVALUABLE(§6.1; `eval_arm_d1`의 silent drop을 코드에서 확인 — `if not real_copy: continue`), donor-cluster sensitivity(LODO) 유지.
Compute:    conditional — 8 logical threads·nproc<16 hard abort·affinity/quota D1 기록은 확인. R 측 CPU 필드 부재(blocker), R mid-run wall>96min 처분 부재, D1 25min@2threads는 D-156 1,180.6s@3threads 기준 위험 있으나 F0 D1은 wrong-donor CE를 제거하므로 여유 가능 — D1 stage approval에서 D-156 phase timing 기반 projection 제시 권장.
Scope:      agree — §14 route-only·association-only·lost controls 자기 규정 충분.

Must-fix (ranked):
1. R artifact schema 보완 (blocker): `r_mechanics_pass.json`에 CPU affinity/quota/thread-pool 필드, `donor_map_sha256` + per-doc donor-ID hash + equality assertion, expected-count literal(또는 frozen table의 artifact 경로) 추가; `r/f0_report.json` literal schema 신설(§0 변경 5, §6.1 191행, §13A.10 562–573행).
2. D1 custody 본문 반영 (blocker): allowed filesystem delta whitelist, success/crash 파일 inventory assertion, log-file/temp-path inventory 테스트를 §5/§13A.4에 명시(§0 변경 6; 현 본문은 497–499행뿐).
3. Overrun 단일 규칙 완성: §12 369행 "provisional" 삭제, §5 D1(157행)·D0(136행)·P·Q에 overrun 처분을 377행과 동일 문구로 통일, R 측정 wall>96min mid-run 처분 신설.
4. (minor) §13A 제목 413행 "v1.11 implementation addenda"→v1.12 갱신, §15 Q4 609행 `SE_D<=.0255` 표기를 nominal-only로 갱신, Q `wrong_donor_ce_calls` expected 값 규정, near-threshold m_* 대상 통계량 명시, bootstrap seed 20261109=training seed 우연 일치 1줄 명시.

잘못된 전제:
- 리뷰 요청서 §1과 plan §0 변경 요약 5·6번은 v1.12가 R schema 확장과 D1 custody 추가를 "반영"했다는 전제 — 실제 본문(§13A.10, §5, §13A.4)에는 반영되지 않았다. 변경 요약은 구현이 아니라 의도이며, 승인 판정은 본문 기준이어야 한다.
- §0 변경 2의 "§0/§5/§12/D0 모두 동일" 전제 — §12 table이 여전히 "provisional"이고 D0는 별개 규칙이므로 성립하지 않는다.
- R gate가 `pre_r_seed_audit_pass`만으로 R 자체 init을 보장한다는 암묵 전제 — §4 assertion은 "per registered seed"라 P/Q/R에 적용되지만 R stage 본문(§5)에 assertion 실패 시 `NOT_EVALUABLE` 처리가 재진술되어 있지 않다. §7 PROTOCOL_VALID가 이를 흡수하나 명시 권장.
```

판정 요약: **NARROW** — must-fix 1–3이 해소되면 CONTINUE 가능한 상태. F0 미승인·미실행 유지, test 163 sealed, P1 unused, D0/D1/R 실행 없음.