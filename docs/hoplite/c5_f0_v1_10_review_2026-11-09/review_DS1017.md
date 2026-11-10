# C5 F0 v1.10 — Independent Review (DS1017)

- 작성일: 2026-11-10
- 검토 대상: `docs/plan_c5_f0_v1_10_2026-11-09.md`
- 검토 라운드: 새 10라운드 블록 **round 10/10 (FINAL)**, 독립 스레드
- v1.9 결론 상속: **없음** (본 검토는 v1.10 본문과 현재 HEAD 코드만 근거로 재판정)
- 모델: `deepseek-v4.1-flash-1017`
- 수행: 문서 8종 열람, `runner/c5_pm_phase6.py`(970 lines)·`runner/c5_pm_mt5_lora_b0.py`·`runner/c5_pm_stats.py`·`runner/c5_pm_gate.py`·`docs/decisions.md`(D-156/D-157) 대조, step_seed golden table 재계산
- **학습/평가 없음, test 163/P1 미사용, subagent 없음, repository 수정 없음 (이 파일 1개만 생성)**

## 0. Reviewed HEAD

```text
git fetch origin           -> ok (From https://github.com/mandutt/unigem, branch main -> FETCH_HEAD)
git pull --ff-only origin main -> Already up to date.
HEAD = de90ebdb16a584a7d406c9b0b325ee8a096daf20
       "docs: add C5 F0 v1.10 final review request"  (2026-11-10 12:42:44 +0900)
working tree = clean (git status --porcelain empty)
```

- 검토는 위 HEAD의 워크스페이스 사본에서 수행했다.
- 본 문서 작성 시점의 HEAD도 동일하다 (`de90ebdb…`).

## 1. Verbatim paired E01−E11 (review 대상 계약)

§1 질문 (plan L54):

```text
> **LoRA initialization을 match한 상태에서 adapter 유무가 EG2 donor-specific signal을 바꾸는가?**
```

§2 cells 표 중 primary pair (plan L62−L63), verbatim:

```text
| E01 (F0) | EG2 raw | none | 64 modules | 100 | adapter-free + LoRA |
| E11 (L) | EG2 raw | trained | 64 modules | 100 | adapter + LoRA |
```

§2 primary 지정 (plan L65), verbatim:

```text
- Primary: **E01 vs E11** (LoRA initialization matched).
```

§6.3 pairing 정의, verbatim:

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
```

§6.3 PASS gate, verbatim:

```text
- Primary positive: `mean_D > 0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0`.
```

위 5개 인용이 본 검토가 평가한 E01−E11 계약의 전문이며, 아래 Q1−Q6 판정은 이 pair에 대해서만 유효하다.

## 2. Q1. CE count / schema / hash

- **판정: conditional**

근거:

1. **frozen operation table은 실제로 존재하고 형식이 고정됐다** (§13A.4, plan L502): `cell×phase×doc_count×donor_count×copy/full`, `expected_real_memory_ce_calls` = 표의 "independent instrumented run", 20-doc mechanics와 15-doc donor-crop 분리, mismatch → `NOT_EVALUABLE`. v1.9의 "D1 출력에서 사후 유도" 문제는 실제로 닫혔다.
2. **그러나 D1 게이트와 표가 서로 모순이다 (blocker).** §13A.4의 `donor_count` 열과 "15-doc donor-crop" 기대 카운트는 "doc × donor" 단위 호출을 전제하는데, 같은 스키마가 `donor_map_loads: int (must be 0)`(L475), `wrong_donor_ce_calls: int (must 0)`(L475), §5 D1 assertion 6 "phase7 records == 0", §13A.5 "evaluated_donors == 5"를 동시에 요구한다. `real = memory_for(rid)`를 5개 donor crop으로 자르려면 `K = min(len(real), len(donor))`를 위해 donor 길이/텐서 접근이 필요하다 (`runner/c5_pm_mt5_lora_b0.py:318 donors_for`, `runner/c5_pm_phase6.py:429 eval_arm_d1`가 실제로 `donors[rid]`를 순회). 즉 `donor_map_loads:0`을 절대 조건으로 두면 `donor_count=5`짜리 CE 표는 실행 불가하고, 표를 실행하면 게이트가 실패한다. D1이 `mechanics_pass`에 도달할 수 있는 해석이 문서에 하나도 명시돼 있지 않다. 이건 문구 문제가 아니라 **D1 통과 가능성 자체를 좌우하는 모순**이다.
3. **`real_memory_ce_calls`의 "independent instrumented run"이 산출물로 고정되지 않았다.** 누가/어떤 커밋으로 그 계수를 만들고 어디에 남기는지(§13 artifacts에 해당 파일 없음, plan L397−L411), evaluator와 독립이라는 것을 무엇으로 증명하는지가 없다. "not D1 output"이라는 부정 조건만 있고 양성 증거 요구가 없다.
4. **hash binding이 스키마에서 빠져 있다 (blocker).** §0 item 2(L23−L24)는 "P and R store canonical pre-update hashes per seed/cell; compare at Q/R start"라고 선언하지만, §13A.10의 Q 스키마(L555−L562)는 `{post_step0_rng_sha256, group_change_ok, wrong_donor_finite, shape_ok}`뿐이고 **pre-update hash 필드가 없다.** R 쪽도 `r/init_hashes.json`은 artifacts 목록에만 있고, `r_mechanics_pass.json`(L574−L582)에는 hash equality 필드가 없다. 따라서 "Q/R start에서 비교"는 스키마상 표현 불가능하고, `p_r_hash_equal`(L548)은 P 내부 자기비교로만 남는다. v1.9 must-fix 2가 changelog에만 반영되고 normative schema에는 반영되지 않았다.
5. **R의 CE 기대값이 수치로 동결되지 않았다 (blocker).** §13A.10(L581)은 "per seed/cell/phase CE, donor-map loads … exact table frozen before R"이라고만 하고 `updates 900 / M 1440 / phase7 7200` 외에는 숫자가 없다. 그런데 `r_mechanics_pass`는 "all expected counts equal"을 요구하므로, **비교 대상 값이 존재하지 않는 필드(`real_memory_ce_calls`, `donor_map_loads`)에 대해 gate가 정의되지 않는다.** D1은 표를 동결했지만 R은 동결 선언만 하고 표를 비워 둔 상태다.
6. step_seed golden table은 **재계산 결과 문서와 완전히 일치**한다 (검증: seed 20261108 → `0x9f02514d/0x3d5bdb86/0xdb9345df`, 20261109 → `…4c/…87/…de`, 20261110 → `…4f/…84/…dd`, 20261111 → `…4e/…85/…dc`). §4 L112−L115와 §13A.2 직렬화 문법(`name_len|dtype|ndim|shape|nbytes|LE bytes`)은 승인 가능한 수준으로 구체적이다. 이 항목은 결함 없음.

다음 단계:

1. D1 표에서 `donor_count` 열의 의미를 확정하고, `donor_map_loads`/`wrong_donor_ce_calls` 금지 조건과 양립하는 문구(예: donor 접근은 `donors_for` 1회 계산 후 캐시된 길이만 사용, wrong-donor CE 호출 0)로 재작성.
2. Q 스키마에 `pre_update_hash`, `p_q_hash_equal`을, R 스키마에 `p_r_hash_equal`·`hash_binding_ok`를 추가.
3. R의 `expected_real_memory_ce_calls` / `expected_donor_map_loads` 수치를 문서에 동결하고, instrumented run 산출물 경로를 §13 artifacts에 추가.

## 3. Q2. D1 materialization / seal / overrun

- **판정: conditional**

근거:

1. seal의 핵심 구조는 v1.9 대비 실제로 강화됐다: §5 L165−L168 (signal delta 미계산, `f0_d1_mechanics.json` 단일 출력, `d1_report.json` exact-path 금지, `d1_sealed/` 부재), §13A.4 literal schema(L456−L503), `checkpoint_digests` + `checkpoint_absent`(L476−L477), partial/error 두 형태만 허용(L504), "post-success no checkpoint / post-crash no checkpoint" 파일시스템 테스트(L506). `mechanics_pass` conjunction(L503)은 `wrong_donor_ce_calls==0`, `donor_map_loads==0`, `d1_signal_read==false`까지 묶어 재량 여지를 거의 없앴다. **materialization 문구는 승인 가능한 수준이다.**
2. **overrun 조치가 이중 정의되어 있다 (blocker 성격의 불일치).** §0 item 5(L30)는 ">25 min hard abort requires new code SHA and stage re-approval", §5 L164는 "cap ≤25 min parallel; sequential is diagnostic only", §12 L384는 "if measured wall exceeds 25 min, repair or re-review; no silent extension"이다. 세 문장이 서로 다른 조치(코드 SHA 재승인 vs re-review vs repair)를 말한다. abort 후 어떤 경로가 정본인지 정해지지 않으면 초과 시 임의 해석이 가능하다.
3. **로그/crash/temp 경로 테스트가 §0에만 있고 본문에 없다.** §0 item 5(L30)는 "logs/crash/temp paths tested"를 약속하지만, §13(L414−L416)은 "D1/Q stdout/log must not print CE values; only counts/booleans"와 artifacts 규칙만 있고, temp 파일·crash traceback·torch 저장 임시경로에 대한 테스트 항목이 없다. §13A.4 파일시스템 테스트(L506)도 checkpoint/per_doc/d1_sealed만 언급한다. 즉 CE 텐서가 repr로 traceback에 실려 나가는 경로가 이 계획에서 유일하게 검사되지 않은 leak channel로 남는다.
4. D1 assertion 4(n_docs 20/20, L156)와 assertion 5(M 120/cell, L157), assertion 7(generation 20/cell, L159)는 scalar count만 요구하므로 immunize되어 있다. 이 부분은 문제 없음.

다음 단계:

1. overrun 조치를 한 문장으로 통일 (권고: hard abort → 새 `code_commit` 기록 + stage 재승인, re-review는 선택).
2. §13에 temp/crash-traceback 경로 negative test를 명시 (`torch.save` 임시파일, `traceback` 출력의 CE 미포함).

## 4. Q3. R mechanics / gates

- **판정: conditional**

근거:

1. R counts 자체는 정합하다: 900 updates = 3 trained cells × 100 × 3 seeds, M 1,440 = 120 × 12, phase7 7,200 = 600 × 12 (Phase 6 `docs/plan_c5_b0a_pm_prereg_v1_0_11.md:1296,1298`의 600/arm-seed와 일치), generation 240 = 20 × 12. §5 L172−L175와 §12 표가 같은 값을 쓴다. 이 산술은 오류 없음.
2. **P/Q gate는 fail-closed로 잘 닫혀 있다**: §13A.10(L552) `pre_r_init_audit_pass` = 3×4 존재 + canonical hash + `p_r_hash_equal` + KAT 참조; 누락/중복/malformed/stale/partial → false. §5 L186과 §13A.9 L537−L539의 단일 writer atomic append+validate도 타당하다.
3. **남는 우회 경로 1 — donor identity 미검증.** §13A.8(L530−L532)은 "Q checks finiteness/shape only, primary wrong-donor CE numerical path is first exercised at R"이라고 정직하게 밝힌다. 그러나 R의 `r_mechanics_pass`(L574−L582)는 **count 기반**이므로, donor map이 잘못되어도(예: 후보 정렬 오류, `rid` 자기참조 포함) 호출 수는 동일하게 나온다. Phase 6 schema는 record마다 `donor_id`를 남기지만(`plan_c5_b0a_pm_prereg_v1_0_11.md:1123`), F0 R 스키마에는 `donor_id`도 donor-map sha 재검증도 없다. 즉 "finite하고 count가 맞는 잘못된 donor"가 전 게이트를 통과한다. §6.1 L196이 donor map sha256을 `init_hashes.json`에 기록한다고만 하고, R이 실제 사용 donor를 그 sha와 비교한다는 요구가 없다.
4. **남는 우회 경로 2 — hash binding 부재** (Q1 근거 4와 동일). R 시작 시 builder/seed 일치를 검증할 필드가 스키마에 없어, P와 R이 서로 다른 코드 경로로 초기화되어도 gate가 잡지 못한다.
5. Q의 12 units/9 trained updates 표기(L564)는 §12 aggregate와 정합. 문제 없음.

다음 단계:

1. R record 또는 seed/cell 단위로 `donor_id` 집합과 donor-map sha256 재검증 필드를 추가하고 `r_mechanics_pass` conjunction에 포함.
2. R 시작 시 P hash 대조 필드 추가 (Q1 다음 단계 2와 동일 항목).

## 5. Q4. Cohort / CI / STOP / near-threshold

- **판정: conditional**

근거:

1. **조건부 estimand는 이제 명시적이다** (§6.1 L192−L199): primary = 15 length-eligible + fixed donor graph, 20-doc은 descriptive, 20-doc 모집단 일반화 금지, donor-cluster leave-one-out sensitivity. v1.0 synthesis DS-2의 blocker는 문서상 해소됐다.
2. **EQUIVALENT 산술은 검증 결과 정확하다**: `SE_D <= .0255` ⟺ 1.96·SE_D ≤ .05 (§12 L388). `MDE .019170 = .037573/1.96` (계산 .019170), 50% MDE .0376, 80% MDE 2.802×.019170 = .0537 — 세 값 모두 재계산 일치. "F−L proxy는 planning proxy이며 validated E01−E11 SE가 아니다"라는 한정도 유지됐다.
3. **near-threshold 수식은 동결됐으나 기호 `b`가 정의되지 않았다.** §7 L311: `m_mean=mean-b, m_lower=CI.lower-b, m_sign=(#seeds>0)-2`. SIGNAL(copy)의 `b=.05`, SIGNAL(full)의 `b=0`(§6.4)인데 §7은 어느 endpoint에 어떤 `b`를 쓰는지 말하지 않는다. non-decisional이라 해도 리포트 값이 달라지는 모호성이다.
4. **state table은 상호배타·전체포괄로 유지된다**: priority 1 `NOT_EVALUABLE` → 2 `PASS_POSITIVE` → 3 `ROUTE_STOP` → 4 `INDETERMINATE`, reason precedence `EQUIVALENT > harm > benefit`. `ALL_FAIL`이 E01/E11 × copy/full로 한정되고 ROUTE_STOP이 cell-level FAIL을 쓰는 점도 일관적이다.
5. **잔여 구조적 사실(결함 아님, 명시 필요)**: P−PA dispersion SE 0.6209, per-doc SD 2.405, n=15이면 예상 `SE_D`는 .0255보다 1자리 이상 크다. 즉 EQUIVALENT는 **설계상 사실상 도달 불가**하고, §6.5가 "expected branch is undetermined; PASS and ROUTE_STOP are both live"라고 쓴 것은 정확하지만 state table의 priority 1이 실질적으로 죽은 분기라는 점이 명시되지 않는다. 이는 README급 한 줄이면 충분하다.
6. `n_boot=10000` override(§6.1 L203, §6.3)와 `l_predicate` 금지는 실제 코드 기본값 `N_BOOT = 1000`(`runner/c5_pm_stats.py:15`)·`l_predicate`(`runner/c5_pm_gate.py:37`)를 정확히 겨냥한다 — v1.0 synthesis DS-6이 올바르게 반영됐다.

다음 단계:

1. §7에 endpoint별 `b` 값을 명시.
2. §6.5 또는 §7에 "EQUIVALENT branch is nominal under expected dispersion" 한 줄 추가.

## 6. Q5. Compute / scope

- **판정: disagree**

근거:

1. **CPU observability가 changelog와 질문에만 있고 normative 본문에 없다.** §0 item 6(L31−L32)는 "Record CPU set/quota/all thread pools; `nproc` alone not capacity proof"라고 약속하고 §15 Q5(L619)도 "CPU affinity/quota"를 묻지만, 실제 기록 필드는 §12 L386의 `nproc`, `threads_per_arm`, `parallel_wall_s`, `contention_ratio`가 전부이고, §13A.4 `parallel` 객체(L479)도 같은 4개뿐이다. `sched_getaffinity`, cgroup quota, `torch`/`OMP`/`MKL` thread pool 설정은 문서 어디에도 없다(grep 결과 "affinity/quota/thread pool"은 L32와 L619 두 곳에서만 등장). 즉 이 must-fix는 **문서 내부에서 선언만 되고 반영되지 않았다.**
2. **동일 수치가 "measured"와 "not a measurement"로 동시에 표기된다.** §12 L379: "D1 1,180.6s = 3 threads/arm **measured** (D-156); registered 4,939.884s = 2 threads/arm **measured** (D-157)". §12 L380: "Wall anchor (estimate): Phase 6 registered 4,939.884s at 2 threads/arm; **not a measurement**." 두 줄이 같은 숫자를 정반대로 규정한다. `docs/decisions.md:218`(D-157)도 4,939.9s를 wall로 적고 있으나, v1.4 review가 지적한 대로 이는 `registered_report.json`의 `wall_estimate_s`(wave-max 합)이며 end-to-end 측정이 아니다. thread 귀속(2 vs 3)은 v1.7 지적이 v1.10에서야 수정됐고, 성격 규정은 아직 모순 상태다.
3. **D1 cap과 스레드 설정의 정합이 한 줄로 봉합되지 않았다.** L379는 "D1 25 min applies at 2 threads/arm"이라 하지만 앵커 1,180.6s는 3 threads/arm 측정(D-156)이다. §5 L151도 D1을 2 threads/arm으로 규정한다. 2 threads/arm에서 3-thread 앵커를 그대로 쓰면 cap은 보수적이 아니라 **검증되지 않은 외삽**이며, 이 외삽 가정이 문장으로 명시되지 않는다.
4. **nproc≥16 vs 8 logical의 2배 여유가 설명되지 않는다.** §12 L387 "Hard abort if nproc < 16"인데 실제 사용은 4 arms × 2 threads = 8 logical(§12 표). §13A.7 L522는 "current 4-vCPU workspace is not a qualifying host"라고만 한다. 16의 근거가 없다.
5. **allowlist-first loader는 방향이 옳다**: §13A.9 L537−L539 (allowlist를 full-split 파싱 전에 적용, transitive test163/P1 read-path test), §13A.7 L527 (직접 open 시도가 실패해야 함, flag는 증거가 아님). 다만 §11이 "No F0 code is implemented by this draft"이므로 이는 아직 코드 계약이며, 승인 시 D0에서 실제 테스트로 확인해야 한다.

다음 단계:

1. §12/§13A.4에 `cpu_set`, `cpu_quota`, `omp_threads`, `torch_threads`, `mkl_threads` 필드를 추가하고 §0 item 6과 일치시킬 것.
2. L379/L380 중 하나로 통일 (권고: "4,939.884s = wave-max 합, end-to-end wall 아님"), D1 cap의 스레드 외삽 가정을 명시.
3. `nproc≥16` 근거를 쓰거나 8 logical에 맞춰 하향.

## 7. Q6. Route / limitations

- **판정: agree**

근거:

1. `ROUTE_STOP`의 범위가 route-as-configured로 한정된다 (§8 route 정의, §14 L594: "stops only the route as configured … does not stop the EG2 track, does not rescue B0-B, and does not launch H3"). Phase 6 cause report(`reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md` §9)의 축소 결론("adapter-associated donor-specific signal loss, native path")과 일치한다.
2. wrong-donor 잔여 위험이 명시적으로 선언된다 (§13A.8 L530−L532). 문서가 위험을 숨기지 않는다. 다만 Q3 근거 3의 검증 수단 부재는 별도 must-fix다.
3. H3 제외가 §10에서 "prevents H3 details from blocking F0 approval and prevents negative F0 results from being rescued by H3"로 목적까지 밝혀져 있다. Phase 6 synthesis MF-4가 요구한 zero/permuted null과 1-seed gate의 미이행도 §14 마지막 bullet에서 "intentionally out of scope; F0 cannot claim they were replaced"로 정직하게 처리했다.
4. association-only 한정(§14)과 "adapter-as-configured" 정의(§4 L124)는 과대 일반화를 막는 방향으로 일관적이다. 이 항목에는 승인 차단 요소가 없다.

다음 단계:

1. 없음 (Q3 must-fix에 donor identity 검증이 흡수됨).

## 8. 최종 판정

```text
최종 판정: NARROW
Init:      conditional — step_seed golden table 및 직렬화 문법은 재계산 일치(결함 없음).
           단 §4 L117−L118의 `\n` delimiter 문장이 코드 스팬 중간에서 줄바꿈되어 깨져 있음(사소).
           RNG parity assertion(§4 L106−L107)이 E01/E11만 대상이고 E10은 빠짐(사소).
D1:        conditional — schema/seal/partial/파일시스템 테스트는 승인 가능.
           blocker: §13A.4 frozen table의 donor_count와 donor_map_loads:0/wrong_donor_ce_calls:0의 모순.
           high: overrun 조치 3중 정의(§0 L30 / §5 L164 / §12 L384), temp·traceback 경로 테스트 부재.
STOP/MDE:  agree — 4-state table 상호배타·전체포괄, EQUIVALENT 산술(.0255, .019170, .0537) 재계산 일치.
           잔여: near-threshold `b` 미정의(§7 L311), EQUIVALENT 분기가 사실상 nominal임을 미명시.
Cohort:    conditional — 15-doc 조건부 estimand·fixed donor graph·20-doc descriptive 분리는 해소됨.
           잔여: R에서 donor identity 미검증, Q/R hash binding 필드 부재.
Compute:   disagree — §0 item 6의 CPU set/quota/thread pool이 본문·스키마에 없음.
           4,939.884s가 §12 L379 "measured" / L380 "not a measurement"로 모순.
           D1 cap의 2-vs-3 threads 외삽 미명시, nproc≥16 근거 없음.
Scope:     agree — route-only/association-only/H3 제외/lost-controls 선언 모두 타당.
H3:        agree — F0에서 완전 제외, 자동 개시 금지 명시.
```

### Must-fix (ranked)

1. **[blocker] D1 CE 표와 D1 seal 게이트의 모순 (Q1/Q2).** §13A.4 L502의 `donor_count`·15-doc donor-crop 기대 카운트와, 같은 스키마의 `donor_map_loads (must be 0)`/`wrong_donor_ce_calls (must 0)`(L475)·§13A.5가 양립 불가. D1이 `mechanics_pass`에 도달할 수 있는 실행 해석을 한 문장으로 확정해야 한다. (`runner/c5_pm_phase6.py:429`는 donor 순회를 실제로 수행한다.)
2. **[blocker] Q/R hash binding이 스키마에 없음 (Q1/Q3).** §0 L23−L24의 "compare at Q/R start"가 §13A.10 Q 스키마(L555−L562)·R 스키마(L574−L582)에 필드로 존재하지 않음. `pre_update_hash`/`p_q_hash_equal`/`p_r_hash_equal`/`hash_binding_ok` 추가.
3. **[blocker] R의 expected CE/donor_map_loads 수치 미동결 (Q1/Q3).** §13A.10 L581은 "exact table frozen before R"이라고만 하고 숫자가 없어 `r_mechanics_pass`의 비교 대상이 정의되지 않는다.
4. **[high] compute observability 미반영 (Q5).** §0 item 6·§15 Q5가 약속한 `cpu_set`/`cpu_quota`/thread pool 필드가 §12 L386과 `parallel` 객체(L479)에 없다.
5. **[high] 4,939.884s의 성격 모순 (Q5).** §12 L379 "measured" vs L380 "not a measurement"; D1 25-min cap의 2-threads 외삽 가정 명시.
6. **[medium] D1 overrun 조치 3중 정의 (Q2).** §0 L30(new code SHA + stage re-approval) / §5 L164 / §12 L384(repair or re-review) 중 하나로 통일.
7. **[medium] donor identity 미검증 (Q3).** R record 또는 seed/cell 요약에 `donor_id` 집합·donor-map sha256 재검증을 추가하고 `r_mechanics_pass`에 포함.
8. **[low] near-threshold `b` 미정의 (Q4).** §7 L311에 endpoint별 `b` 값 명시.
9. **[low] §4 L117−L118 코드 스팬 중간 줄바꿈, E10 RNG parity assertion 누락 (Q1).**

### 잘못된 전제

1. **"LoRA initialization을 match하면 adapter 효과가 clean causal이 된다."** §4 L90−L101의 init match는 LoRA 초기값만 같게 만들 뿐, §3 L77의 adapter lr 1e-3 vs LoRA lr 1e-4(10배 차)와 adapter 파라미터(512→512, Phase 6 대조 +526,336) 차이는 그대로다. §4 L124가 "adapter-as-configured"로 정직하게 한정한 것과 §2 L65 "LoRA initialization matched"의 함의가 어긋난다. F0는 adapter *설정 전체*의 효과를 재는 것이지 adapter 가중치만의 효과가 아니다.
2. **"matched init이면 E01/E11의 dropout RNG도 같다."** 실제로는 §4 L101의 per-step `step_seed` reseed가 그 보증을 만든다. init match 자체는 RNG 보증이 아니며, 문서는 이를 structural로 옳게 다뤘지만 Q1 질문 문구("LoRA initialization matched")는 여전히 init match를 보증처럼 읽히게 한다.
3. **"R mechanics pass면 R의 signal 경로도 검증됐다."** `r_mechanics_pass`는 count/provenance 검사이고, wrong-donor CE의 수치 경로는 R에서 처음 실행된다(§13A.8). count가 맞는 잘못된 donor는 통과한다.
4. **"4,939.884s는 96-min cap의 측정 앵커다."** 이는 wave-max의 합이며(`registered_report.json wall_estimate_s`), 동시에 §12 L380이 스스로 "not a measurement"라고 쓴다. cap 앵커로 쓰려면 성격을 하나로 확정해야 한다.
5. **"15-doc 조건부 cohort에서 EQUIVALENT가 실제 분기다."** 산술상 예상 `SE_D`가 .0255를 크게 넘어(per-doc SD 2.405, n=15) EQUIVALENT는 nominal이다. 문서는 "undetermined"라고만 쓰고 이 사실을 명시하지 않는다.

## 9. 승인 차단 요약

- **승인 불가 상태다.** 설계 골격(단일 대조, 조건부 estimand, 4-state taxonomy, route-only 경계)은 타당하지만, must-fix 1−3은 **D1/R 게이트가 자기 스키마와 모순되어 실행 시 통과 불가 또는 무의미**해지는 문제다. 이는 과학적 재설계가 아니라 문서 내부 정합성 수정이며, 코드 구현 이전에 닫을 수 있다.
- must-fix 1−3이 반영되면 D0 승인으로 진행 가능하다. must-fix 4−5(compute)도 같은 수정 라운드에서 함께 닫는 것을 권고한다 — 승인 후 측정 시점에 cap 근거가 흔들리면 R 96-min gate의 신뢰가 먼저 무너진다.
- 학습/평가, test 163/P1, subagent 사용은 본 검토에서 발생하지 않았다.