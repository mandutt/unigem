# C5 F0 v1.10 — Independent Review (GLM)

- 작성일: 2026-11-10
- 검토자: GLM (`z-ai/glm-5.3-flash`)
- 대상: `docs/plan_c5_f0_v1_10_2026-11-09.md`
- **reviewed HEAD: `de90ebdb16a584a7d406c9b0b325ee8a096daf20`** ("docs: add C5 F0 v1.10 final review request", 2026-11-10 12:42:44 +0900)
- 동기화: `git fetch origin` → `git pull --ff-only origin main` → "Already up to date." HEAD = `de90ebdb`. 이 HEAD에서 읽은 파일: `reports/EXTERNAL_REVIEW_C5_F0_V1_10_2026-11-09.md`, `docs/plan_c5_f0_v1_10_2026-11-09.md`, `docs/plan_c5_f0_v1_9_2026-11-09.md`, `reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py`.
- 새 독립 검토. v1.9 결론 상속 없음. 새 10라운드 블록 round 10/10 (final).
- 추가 학습/평가 없음. test 163 sealed, P1 unused, T5Gemma2 D-108 STOP 확인.

## 0. Verbatim paired E01−E11

v1.10 plan §6.3 인용 (그대로):

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

- Primary positive (§6.3, 그대로): `mean_D > 0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0`.

## 1. Q1 — CE count/schema/hash

판정: **conditional agree**

근거:

- §0 변경 1 + §13A.4: operation table `{cell, phase, doc_count, donor_count, copy_full, calls}`을 D1 전 freeze하고 독립 instrumented run으로 `expected_real_memory_ce_calls`를 산출. schema는 `real_memory_ce_calls` / `expected_real_memory_ce_calls` / `real_memory_ce_calls_ok` 쌍으로 고정. v1.0 DS-1·v1.9의 "post-hoc expected count" 문제가 구조적으로 제거됨.
- §13A.2 serialization grammar(`name_len:u32le | name | dtype_len:u8 | dtype | ndim | shape | nbytes:u64le | le_bytes`, dtype whitelist) + KAT fixture를 `serialization_kat.json`으로 `init_hashes.json` 외부에 분리 — 구현 독립 검증 가능.
- §4 assertions 1–9와 §13A.6: hash-inequality assert 제거("tautological")는 정당. E01/E11 LoRA init equality, E10/E11 adapter equality는 `build_arm_f0` 구조(seed → adapter → `seed ^ 0x5EED10A5` → LoRA)상 유효한 equality assert. `runner/c5_pm_phase6.py` `build_arm`(142–155행)의 RNG order(seed→adapter→LoRA)와 §4 계약 일치, F0는 `build_arm`을 수정하지 않음(§4, §11).
- 잔여 (a): counted op = "real_memory_ce per doc×donor×cell×phase"(§13A.4)인데 D1은 donor가 없음(`wrong_donor_ce_calls:0`, `donor_map_loads:0` absolute, §13A.8). D1 frozen table에 donor_count=0 행과, m_records 내 memory_kind=real CE(15 targets × 2 variants × 2 endpoints = 60/cell)를 카운트에 포함할지 여부를 명시해야 `real_memory_ce_calls_ok`가 리뷰 시점에 검증 가능.
- 잔여 (b): §13A.10 `r/r_mechanics_pass.json`은 realized int만 기록하고 expected 값을 artifact에 남기지 않음 — D1과 달리 사후 감증 불가.

다음 단계: (1) D1/R frozen table에 donor_count=0 행 + M-real CE 스코프 명시(D1 stage approval에서 확인). (2) r_mechanics_pass.json에 expected_* 필드 또는 별도 expected-table artifact.

## 2. Q2 — D1 materialization/seal/overrun

판정: **agree** (조건 1개)

근거:

- §13A.4 exact-key allowlist("Only these keys") + writer/consumer allowlist + §5 negative test(`d1_report.json`/`per_doc`/`delta_*` 입력 시 non-zero exit) + checkpoint digest-only/삭제/로딩 금지 + crash path(`partial:true`+`error`, checkpoint 삭제, "no other file") — v1.0 DS-1과 v1.9 seal must-fix의 실질 충족.
- `eval_arm_d1`의 `if not real_copy: continue` 문서 drop(runner/c5_pm_phase6.py 464–465행)에 대한 대응도 §6.1 "a missing doc means `NOT_EVALUABLE`, never a smaller cohort"로 고정.
- M/generation은 memory에서 계산 후 counts만 persist(§0 변경 8), D1 phase7=0, `d1_signal_read:false`, "D1 values must not be read for Stage R or STOP"(§5) — schema와 stage 규칙으로 강제.
- >25 min hard abort → new code SHA + stage re-approval(§0 변경 5, §12). silent extension 차단. D-156(Phase 6 D1 wall 1,180.6s at 3 threads/arm, donor-crop eval 포함) 대비 F0 D1은 donor CE가 없어 per-arm workload가 작고, 2 threads/arm에서 25 min provisional cap은 그럴듯함. fail-closed 경로가 정의되어 있으므로 cap 산술 자체는 blocker 아님.
- 조건: crash-path `error` 필드가 free string이다. §13 "D1/Q stdout/log must not print CE values"만으로는 불충분 — assertion/exception 메시지에 CE 값이 포함되면 log/`error` 경유 유출 가능.

다음 단계: `error`를 enum 코드로 제한하거나 sanitize 요건을 §13A.4에 추가.

## 3. Q3 — R mechanics/gates

판정: **conditional agree**

근거:

- §13A.10 카운트 산술 검증 일치: phase7 7,200 = 3 seeds × 4 cells × 600(15 docs × 5 donors × 2 variants × 2 endpoints × 2 memory_kinds; Phase 6 prereg §11.5 "phase 7 = 600/arm-seed"와 동일 구조), M 1,440 = 3×4×120, generation 240 = 3×4×20, updates 900 = 3×3×100.
- 게이트 구조 signal-free: "Start only after D0/D1 mechanics pass and Q `pre_r_seed_audit_pass[seed]`; no signal-based gate"(§5). Q 실패 → `NOT_EVALUABLE`, no 2-seed continuation(§5, §13A.10). P(§13A.1)→Q→R hash proof fail-closed.
- 남는 우회 경로: (a) §13A.1 "Q also runs donor-crop/wrong-donor CE finiteness + shape check"와 §13A.8 "Primary wrong-donor CE numerical path is first exercised at R"가 문자적으로 모순 — Q가 같은 수치 경로를 계산하므로 "first exercised at R"은 사실과 다름(Q에서 최초 실행, 값 미 persist가 정확). (b) q schema(`q_seed_audit/{seed}.json`)에 donor CE call 카운트가 없어 Q 시점 donor 접촉량이 감증되지 않음. (c) R artifact(`per_doc`)는 존재하므로 decision driver 외부 인간 요인 우회는 구조적으로 남음 — 이는 선언된 한계로 수용.

다음 단계: (1) 13A.1/13A.8 문구 정합화. (2) q schema에 donor_map_loads/CE call 카운트 추가.

## 4. Q4 — Cohort/CI/STOP/near-threshold

판정: **agree**

근거:

- §6.1: 15 length-eligible conditional estimand + fixed donor graph + "Generalization to the 20-doc val population is forbidden" + 20-doc descriptive — v1.0 DS-2(cohort length-selected)의 수용 형태. LOO donor sensitivity + donor reuse 선언. "Each doc must have exactly 5 donors; donor sets identical for E00/E10/E01/E11" — F0은 전 셀이 EG2 lengths 기반이므로 Phase 6 prereg §2.5.6의 per-arm donor 분기 없이 단일 donor map으로 자연 정합.
- §6.3/6.4: CI_D doc-level only, `D_s`는 gate/descriptor. Cell CI frozen(`bootstrap_paired_v2(n_boot=10000, seed=20261109, percentile linear)`) + "no re-bootstrap at decision time" — 재계산 변동 제거. `l_predicate`/`f0_labels.json` alias 금지 — v1.0 DS-6 재발 차단.
- §7: 상태 우선순위 NOT_EVALUABLE > PASS_POSITIVE > ROUTE_STOP > INDETERMINATE, reason 우선순위 EQUIVALENT > harm > benefit. PASS(`CI_D.lower > +.05`)와 EQUIVALENT(`upper <= +.05`)는 lower>.05 ⇒ upper>.05로 수학적으로 비중복. ALL_FAIL = E01/E11 × copy/full 고정, default reason `no_signal_uncertain` 존재 — v1.0 Q3 지적("default reason") 해소.
- 근접 판정: m_mean/m_lower/m_sign 3개 signed margin + non-decisional(§7) — v1.9 must-fix 충족. minor: margin의 `b`가 endpoint별로 미정의(copy=.05, full=0으로 추정).
- EQUIVALENT `SE_D <= .0255`(§12) = `.05/1.96` 필요조건, realized paired SE 사용 — DS-3 재발 없음. `.019170=.037573/1.96`을 "F−L LoRA contrast planning proxy, not a validated E01−E11 SE"로 격하 표기 + P−PA reference dispersion(mean +3.0652, SE 0.6209, per-doc SD 2.405) 병기 — 원인 보고서 §2 수치(+3.065, 14/15)와 일치.

다음 단계: §7에 b per endpoint 명시(copy .05 / full 0).

## 5. Q5 — Compute/scope

판정: **conditional agree** — 스키마 불일치 1건은 must-fix.

근거:

- §12 테이블: P ≤10 min / Q ≤15 min / D0 ≤15 provisional / D1 ≤25 provisional / R ≤96 binding; 8 logical threads(2/arm × 4 arms); `nproc<16` hard abort; 현재 4-vCPU workspace는 non-qualifying(§13A.7) — 내부 일관.
- Provenance 검증: `docs/decisions.md` D-156(Phase 6 D1, 4 arms 병렬 3 threads each, wall 1,180.6s/1,200s cap), D-157(registered 3 waves × 2 threads, wall 4,939.9s/7,200s = 82.3/120 min) — plan §12 인용("1,180.6s = 3 threads/arm measured (D-156); registered 4,939.884s = 2 threads/arm measured (D-157); neither is F0")과 정확히 일치. R cap 96 min은 Phase 6 measured 82.3 min anchor 대비 정상 마진(F0 R은 updates 900으로 Phase 6 1,200보다 적음).
- **must-fix**: §0 변경 6 "Record CPU set/quota/all thread pools; `nproc` alone not capacity proof"가 normative schema에 없음. §13A.4 `parallel` = `{nproc, threads_per_arm, parallel_wall_s, contention_ratio}`뿐이고, §13A.10 R schema에는 parallel 블록 자체가 없음. CPU affinity set / cgroup quota / torch thread pool 기록 필드가 어느 artifact에도 정의되지 않음 — 변경 요약과 normative schema의 직접 불일치이며, 이대로 구현하면 MF-1/MF-6류 provenance gap 재발.
- **must-fix**: §13 artifacts에 `r/f0_replay.json`이 존재하나 plan 어디에도 schema/내용/게이트가 정의되지 않음(`grep replay` 결과 409행 유일). 정의되지 않은 artifact는 감증 불가 — Phase 6 prereg §11.4 방식의 numeric replay 정의 또는 artifact 제거 필요.
- scope: allowlist-first loader("Loader applies train20/val20 allowlist before parsing full-split sources", §13A.9) + transitive test163/P1 read-path negative tests(§0 변경 4, §13A.7) — v1.9 scope must-fix 충족. shared JSONL(`data/external/f5_pairs_v3_clean.jsonl`)이 test 행을 byte 수준으로 포함하는 점은 Phase 6 prereg §1.5의 allowlist-membership 평가 규칙과 정합하므로 선언만으로 수용.

다음 단계: (1) compute observability 필드를 §13A.4 `parallel`과 R provenance에 추가. (2) `f0_replay.json` 정의 또는 삭제.

## 6. Q6 — Route/limitations

판정: **agree**

근거:

- §8 route-as-configured 열거 + §14: association-only, ROUTE_STOP route-only(EG2 track STOP 아님, B0-B 구제 아님, H3 개시 아님), descriptive contrasts 무추론, lost controls(MF-4 zero/permuted null, 1-seed signal gate) 명시적 인정 — 과대 주장 차단 장치가 plan 본문에 고정.
- §13A.8 wrong-donor residual risk explicit + 1-doc `donors_for`/crop dry-run mitigation.
- §10 H3 완전 분리 + "F0 results do not automatically launch H3" + "prevents negative F0 results from being rescued by H3".
- 원인 보고서(`C5_B0A_PM_PHASE6_CAUSE` §5/§9 MF-3 correction)의 축소된 결론("native 경로 adapter-associated signal loss", 구조적 bottleneck/variance 인과 철회)과 F0 질문(§1: LoRA init matched 상태에서 adapter 유무가 EG2 donor-specific signal을 바꾸는가)이 정합. P/PA 관찰(+3.065 → 0.011, 14/15 positive)을 EG2에서 직접 시험하는 단일 contrast가 올바른 다음 단계. `runner/c5_pm_phase6.py` `arm_spec`이 F/L/P/PA만 지원(125–139행)하는 것과 §11 "New `runner/c5_pm_f0.py`" 계획도 정합.

다음 단계: 없음(선언으로 충분).

## 최종 판정

**CONTINUE** (조건부)

```text
Init:     agree — build_arm_f0 계약 + assertions 1–9 + KAT로 충분. D0 stage approval에서 확인.
D1:       agree — seal 구조 완비; error-string enum 제한 1건 조건.
STOP/MDE: agree — 4-state 상호배타·전체 포괄, PASS/EQUIVALENT 비중복,
          MDE는 labeled proxy + realized SE_D 지배. b per endpoint 정의만 보완.
Cohort:   agree — 15-doc conditional estimand + LOO sensitivity + donor 선언.
Compute:  conditional — CPU set/quota/thread-pool schema 추가 전까지 §0 변경 6은 미이행.
Scope:    agree — allowlist-first + transitive negative tests; f0_replay.json 정의 필요.
```

### Must-fix (ranked)

1. **CPU affinity/quota/thread-pool 기록 필드 추가** — §13A.4 `parallel`과 R provenance schema에 `cpu_affinity`, cgroup quota, torch thread pool 수를 추가(§0 변경 6 이행). 이것이 없으면 compute 관측 근거가 `nproc` 하나로 퇴화 — plan이 스스로 금지한 상태. [schema, D0 전]
2. **`r/f0_replay.json` 정의 또는 삭제** — §13 artifacts(409행)에만 존재하고 정의가 없음. numeric replay 스펙(Phase 6 §11.4 유추) 또는 artifact 제거. [spec, D0 전]
3. **13A.1 vs 13A.8 모순 정리** — "wrong-donor CE numerical path is first exercised at R"을 "Q에서 최초 실행(finiteness/shape), 값 미 persist, R에서 최초 사용"으로 수정 + q schema에 donor CE 카운트 추가. [spec, D1 전]
4. **crash-path `error` enum 제한** — CE 값이 `error` 문자열/log로 유출되는 경로 차단. [seal, D1 전]
5. **D1/R frozen operation table 완결** — donor_count=0 행 명시, M-real CE 스코프 명시, `r_mechanics_pass.json`에 expected_* 필드. [auditability, 각 stage approval 전]
6. **near-threshold `b` per endpoint 명시** (copy .05 / full 0). [minor]

### 잘못된 전제

없음. 보정 2건: (a) D1 25 min은 provisional이고 §12가 fail-closed 경로를 규정 — blocker 아님; (b) D-156의 1,180.6s는 donor-crop eval을 포함한 Phase 6 D1이므로 F0 D1(무 donor)과 직접 환산 불가 — plan이 이미 "neither is F0"으로 선언.

### 실행 조건

- must-fix 1–5는 D0 stage approval 이전에 번호 붙은 ERRATA 또는 schema 추가로 반영. threshold/seed/donor/step/LR 변경 아님 — 재 review round 불요.
- D0/D1/R 각각 별도 stage approval. `runner/c5_pm_f0*.py` committed clean-tree SHA가 D0 선행 조건(§11).
- H3는 F0 완료·검토 후 별도 prereg(§10). B0-B/B1/B2/Stage C 자동 진행 금지(§17).

## 7. 10라운드 블록 위치

신규 블록 v1.1–v1.10 중 최종 라운드. v1.10은 v1.9까지의 반복 must-fix(D1 CE count post-hoc, hash proof, R mechanics, scope, seal/overrun, compute observability, near-threshold, materialization, provenance, EQUIVALENT, Q 정합)를 구조적으로 흡수했고, 본 검토의 잔여 must-fix는 설계 변경이 아닌 schema/spec 일관성 항목으로 stage gate에서 검증 가능. 설계 수준 blocker는 발견하지 못함.