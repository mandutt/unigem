# C5 F0 v1.12 — Independent Review (DS1017)

- **Reviewed HEAD: `f994c1033729f2ebe2705bcad335a5f19d7018d6`** (`docs: add C5 F0 v1.12 review request`, 2026-11-10 14:22:03 +0900)
- Sync: `git fetch origin` → exit 0, no output. `git pull --ff-only origin main` → **Already up to date.** Work tree clean at review time.
- 대상: `docs/plan_c5_f0_v1_12_2026-11-09.md` (655 lines, 상태 `DRAFT v1.12 — 미승인, 미실행`)
- 새 10-round block **round 1**. v1.10/v1.11 결론 상속 없음 — 본 판정은 아래 인용과 재계산에만 근거한다.
  - 문서 불일치(비차단): 요청서 §0 제목은 "Block 3 Round 2/10", 사용자 지시는 "new 10-round block, round 1". §4-6에 기록.
- 열람: 지정 8종 + `runner/c5_pm_phase6.py`(970 lines) + `runner/c5_mt5_lora_b0.py`(`donors_for` 318–326) + `docs/decisions.md`(D-156:216, D-157:218).
  - `docs/plan_c5_f0_v1_11_2026-11-09.md`는 **이번 라운드 delta 분리용 diff 기준**으로만 사용했다(결론 상속 아님). `v1_10`은 요청대로 직접 열람.
- 금지 준수: 학습/평가 없음, D0/D1/P/Q/R 미실행, test 163 미사용(sealed), P1 미사용, subagent 없음, repo 수정 없음(**이 파일 1개만 생성**).

## 0. Reviewed HEAD + verbatim paired E01−E11

HEAD: `f994c1033729f2ebe2705bcad335a5f19d7018d6`

§6.3 Primary contrast (plan lines 213–218), verbatim:

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

§6.3 (lines 223–224), verbatim:

```text
- Primary positive: `mean_D > 0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0`.
- `D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary.
```

§7 taxonomy (line 298), verbatim:

```text
| 2 | `PASS_POSITIVE` | `mean_D>0` AND `CI_D.lower > +.05` AND `SIGNAL(E01,copy)` AND 2/3 seeds `D_s>0` |
```

line 227, verbatim: `PASS_POSITIVE` requires the paired contrast, E01 absolute copy signal, and seed replication; this is not a per-cell significance conjunction.

→ line 223, line 298, line 227이 **동일 조건**이고 line 224가 `D_s`(seed-level gate)를 doc-level `CI_D`와 분리한다. **paired E01−E11 정의의 내부 정합은 agree.**

## 1. Q1–Q6

### Q1. CPU / D1 custody — **conditional** (D1 custody agree / CPU disagree)

- **D1 custody는 승인 가능 수준이다.** writer/consumer allowlist 단일화(line 497), success/partial 2형태만 허용(line 496), crash가 `partial:true`+`error`만 쓰고 checkpoint 삭제(line 499), checkpoint digest 기록 후 삭제·no-load(line 154, 486–487), `per_doc`/`delta_*`/`d1_sealed` negative test(line 498), CE 값 로그 금지(§13 line 405), `error` enum 6값 고정(line 490) — v1.11에서 지적된 crash-path 자유문자열 누출 경로가 닫혔다. agree.
- **§0 item 6 (line 31)의 "allowed filesystem delta"는 본문에 없다.** 13A.4 line 498은 "post-success no checkpoint / post-crash no checkpoint / negative tests"만 열거한다. "정확한 파일 목록"은 있고 "그 목록 외 delta 0"이라는 allowlist diff 주장은 문장만 있다. → MF-6(낮음).
- **CPU: disagree.** §0 item 5 (line 29)는 "R schema — CPU affinity/quota/thread-pool"을 반영했다고 쓰지만 사실이 아니다:
  - `parallel` object(`cpu_affinity`, `cgroup_cpu_quota`, `torch_threads`, `thread_pool_counts`)는 **D1 schema 전용**(line 472)이다.
  - R의 유일한 schema artifact `r/r_mechanics_pass.json`(lines 562–574)에는 `parallel` object도, 네 필드도 **없다**.
  - §11 line 354도 `c5_pm_f0_parallel.py` 산출을 `wall_estimate_s`/`parallel_arms`/`cap_ok`/`nproc`/`threads_per_arm`/`parallel_wall_s`/`contention_ratio`/per-phase timings로 한정한다.
  - 즉 R은 여전히 `nproc`+`threads_per_arm` 수준이며, `nproc` alone이 capacity proof가 아니라는 §13A.7 (line 517) 자신의 요구를 R에서 충족하지 못한다. **v1.11 §0 item 1과 동일 주장의 2회차 반복**이다. → MF-1.
- Host 전제는 명시적이다: line 517 "current 4-vCPU workspace fails; no F0 run there". 승인은 16-core host 확보 조건부. agree.
- 다음 단계: MF-1(CPU/parallel 필드를 R schema에), MF-6(파일 delta allowlist를 test 항목으로).

### Q2. wrong-donor / error enum — **conditional**

- **Q `wrong_donor_ce_calls`는 이번에 실제로 추가됐다**(line 555). v1.11의 "§0는 주장하고 schema에는 없음" 결함은 닫혔다. agree.
- **그러나 gate에 연결되지 않았다.** `pre_r_seed_audit_pass[seed]`의 정의(line 558)는 "all 4 cells present, unit pass, finite/shape true"뿐이다. `wrong_donor_ce_calls`는 **기대값 literal이 없고 비교도 없다**(line 555는 주석 없는 `int`). Q가 wrong-donor 경로의 "first execution"이라면(13A.8 lines 524–525) (a) `expected_wrong_donor_ce_calls` literal, (b) count 일치 in predicate, (c) per-doc `evaluated_donors==5`가 필요하다.
- **왜 실질 위험인가.** 재사용 가능한 Phase 6 루프는 donor pair를 조용히 버린다: `runner/c5_pm_phase6.py:459` `if rc is not None and wc is not None:`, `:464` `if not real_copy: continue`, `n_donors`는 `:467`에 기록만 되고 **어디서도 assert되지 않는다**. 이 형태를 F0 Q가 복제하면 전 donor가 drop된 doc도 `wrong_donor_finite:true`(공허하게)·`shape_ok:true`로 통과한다. Q 통과 시 그 seed로 R이 열린다(line 560 "Any false → NOT_EVALUABLE; no R"). → MF-4.
- **error/partial은 D1 전용이다**(lines 489–490). Q schema(550–556)와 R schema(563–574)에는 `error`도 `partial`도 없다. 그런데 §12 line 377은 overrun을 "hard abort, `partial:true`, new code SHA + re-approval"로 정의하고 R은 **96 min binding cap**이다. R에는 그 `partial:true`를 실을 필드도 `error` enum도 없다 → overrun 결과가 artifact로 표현 불가. P/Q도 동일. → MF-4.
- 다음 단계: MF-4(Q/R `partial`/`error` 신설, Q count gate 실효화).

### Q3. donor-count / overrun / provenance — **disagree**

이 항목이 이번 판의 차단 사유다.

**(a) donor-count 모순은 절반만 닫혔다.**
13A.5를 "R only"로 좁힌 것(lines 503–504)과 D1 `cells`에서 donor 필드를 뺀 것, `donor_map_loads:0`(485)/`wrong_donor_ce_calls:0`(484)는 서로 정합한다. **그러나** 13A.4 line 494은 여전히 "Frozen operation table (before D1): cell×phase×doc_count×**donor_count**×copy/full"이다. D1이 donor map을 0회 load하고 wrong-donor CE를 0회 호출한다면 D1 행의 `donor_count`는 **정의상 1**이어야 하는데 그 문장이 없다. 수치가 갈린다:

```text
donor_count = 1 : 20 docs × 2 phases × 4 cells = 160 expected_real_memory_ce_calls
donor_count = 5 : 20 docs × 5 donors × 2 phases × 4 cells = 800
```

800으로 생성되면 `real_memory_ce_calls_ok:false` → D1 전체 NOT_EVALUABLE(line 494 "mismatch → NOT_EVALUABLE"). 즉 문서 안의 미정의 하나가 D1을 **결정적으로 무효화**할 수 있다. 게다가 v1.11 §0 item 5에 있던 봉합 문장 — "`donor_count`는 frozen metadata; D1 `donor_map_loads`는 runtime count만. Metadata read는 load로 세지 않음"(v1.11 plan line 30) — 이 v1.12 §0에서 **삭제**됐다. 모순을 설명하던 문장을 지우고 13A.5만 좁힌 셈이다. → MF-3.

**(b) overrun은 단일 규칙이 아니다.** §0 item 2 (line 23)는 "§0/§5/§12/**D0** 모두 동일: >25 min → hard abort, `partial:true`, new code SHA + explicit stage re-approval"이라고 주장한다. 실제는 4종이다:

| stage | cap (문서) | 초과 시 결과 | 근거 |
|---|---|---|---|
| P | ≤10 min | **무규정** | line 366 |
| Q | ≤15 min | **무규정** | line 367 |
| D0 | ≤15 min provisional | "**repair first**" — partial 없음, 재승인 없음 | line 136 |
| D1 | ≤25 min | hard abort + partial + 재승인 | lines 157, 377 |
| R | ≤96 min binding | abort라고만 하고 `partial` 필드 없음 | lines 370, 377 / schema 563–574 |

§0 item 2의 "D0 모두 동일"은 **사실이 아니다**(D0는 15분 repair-first). → MF-5.

**(c) provenance.** D1은 `provenance{code_commit, command, input_sha256, clean_tree}`를 갖는다(line 471) ✓. R은 `provenance_ok:bool`(line 572) 하나뿐이라 §11 line 357의 "D0/D1/R artifacts record `code_commit`, command, input SHA"를 담을 필드가 **없다**. → MF-1.

**(d) §15 Q3 "남는 우회 경로"에 대한 직접 답 — driver read list가 gate를 배제한다.**
- §5 line 181: "Stage R decision driver reads `f0_d1_mechanics.json`, `f0_r_labels.json`, `init_hashes.json`; never `d1_sealed/*`."
- §7 lines 264–269: `PROTOCOL_VALID`는 "D0 pass predicate", "D1 pass predicate", "R mechanics pass"를 **요구**한다.
- 그런데 `r/r_mechanics_pass.json`(13A.10이 정의한 R mechanics gate 입력)과 `d0/f0_d0.json`(§13 line 390)은 read list에 **없다**. 따라서 "R mechanics가 실패했는데 labels는 확정"되는 경로가 스펙상 열려 있다.
- 같은 절 line 168 "**D1 values must not be read for Stage R or STOP**"는 §7의 "D1 pass predicate" 및 line 181의 `f0_d1_mechanics.json` 판독과 **문자 그대로 충돌**한다. 의도는 "D1 **signal/CE 값** 금지"일 것이나 한정어가 없다. 실행 gate가 이 문장을 그대로 구현하면 D1 mechanics를 읽을 수 없고, 반대로 구현하면 금지 문장을 위반한다. → MF-2.

- 다음 단계: MF-2(read list + 한정어), MF-3(donor_count≡1 + 기대표 literal), MF-5(overrun 통일).

### Q4. near-threshold / EQUIVALENT — **conditional**

- **산술 재계산은 전부 일치한다.** `.037573/1.96 = .019170` ✓; `1.96×.0255 = .049980` ✓; `2.405/√15 = .6210` vs 기재 `SE 0.6209` ✓; `2.802×.019170 = .053714` → 80% MDE `.0537` ✓. `.0255`를 nominal로 한정한 line 380/§0 item 8(line 35)도 일관된다. agree.
- `EQUIVALENT iff 95% CI_D is entirely within [-.05, +.05]`(line 248)와 `.0255`의 관계도 정확하다(SE=.0255이면 mean=0일 때 CI 폭이 정확히 ±.05). plan의 proxy(SE .019170)에서 EQUIVALENT가 성립하는 mean 범위는 `±.012427`인데 line 253이 "No `±.0124` equivalence mean range is asserted"라고 **부인**한다 — 주장하지 않는 것이 옳다(그 수치는 고정 15-doc cohort에서만 성립). agree.
- **`m_b`는 동어반복이다.** line 304: "m_mean=mean-b, m_lower=CI.lower-b, **m_b=m_mean**". `m_mean`이 이미 b-relative이므로 `m_b`는 독립 정보가 0이고, "report all four"는 실제로 3개다. §0 item 7(line 33)의 "`m_b` separate b-relative margin"은 **이행되지 않았다**. 독립 정의(`m_b = mean − .05`, b 고정) 또는 삭제가 필요하다. → MF-6.
- **donor pool은 정합한다.** `donors_for(val20, cache)`(line 191)는 prereg §2.5.6("only val20 has donors", "donor list is **per arm**")과 일치하고, F0 4셀이 모두 EG2이므로 per-arm donor list가 1개로 붕괴해 line 194 "donor sets identical for E00/E10/E01/E11"과도 정합한다. agree. 비차단 잔여: donor pool(20) ≠ estimand cohort(15 common)이므로 배제된 5개 doc이 donor로 들어갈 수 있다 — line 191이 `val20`을 명시하므로 은폐는 아니다.
- `n_boot=10000`(lines 216, 242)은 prereg §10.1 `n_boot=1000`(prereg line 1172)의 변경이다. assert로 감사 가능하지만 §3의 frozen-values 목록에도 §14 non-goals에도 deviation으로 등재되지 않았다. → MF-9(낮음).
- 다음 단계: MF-6(m_b), MF-9(n_boot 등재).

### Q5. R donor identity / hash (+ counts) — **disagree**

- **§6.1 line 191의 요구가 artifact로 존재하지 않는다.** "R report records `donor_map_sha256` and per-doc donor-ID hash and asserts equality"라고 하지만:
  - `r/f0_report.json`은 §13 line 400에 **경로만** 있고 schema가 문서 어디에도 없다.
  - `r/r_mechanics_pass.json`(562–574)에는 `donor_map_sha256`도, per-doc donor hash도, `parallel`도, `provenance` object도 없다. `r_mechanics_pass` 정의(line 576)는 "all expected counts equal, provenance_ok, no missing seed/cell"뿐이다 → **donor identity는 gate되지 않는다.**
  - §7 line 272의 `PROTOCOL_VALID` 요건("each doc has exactly 5 donors; donor sets identical for E00/E10/E01/E11")과 13A.5 line 503의 `expected_donors`도 이를 담을 필드가 **어떤 schema에도 없다.**
- **R artifact 5종 중 schema가 있는 것은 1종뿐이다.** `r_units/{cell}_{seed}.json`, `r/f0_report.json`, 그리고 **driver가 읽는 주 입력인 `r/f0_r_labels.json`**(line 181)까지 schema가 없다. primary label 파일의 literal schema 부재가 R-side 최대 결함이다. → MF-1.
- **§11에 R 산출 주체가 없다.** lines 350–360의 모듈은 `c5_pm_f0.py`(셀+builder), `c5_pm_f0_parallel.py`(실행), `c5_pm_f0_mechanics.py`(D1), `c5_pm_f0_gate.py`(driver) 4개뿐이고, `f0_r_labels.json`/`f0_report.json`을 쓰는 모듈이 미배정이다. Phase 6 results review MF-1(커밋되지 않은 label/gate driver)과 **동일 계열**의 provenance gap이다. → MF-1.
- **counts는 3/6만 literal이다.** `updates_total:900`/`m_records:1440`/`phase7_records:7200`(566–568)은 literal이고 prereg와 정합(`600×12=7,200`, `120×12=1,440`, `20×12=240`, `300×3=900`). 그러나 `real_memory_ce_calls`/`wrong_donor_ce_calls`/`donor_map_loads`(569–571)는 **값 없는 `int`**이고 line 575 "exact table frozen before R"로 유예된다. §0 item 5의 "expected counts literal"은 절반만 참이다. → MF-3.
- `replay_ok`이 v1.11 §0 item 2에 있었으나 v1.12에는 그 문자열 자체가 없다(문서 내 `replay`는 line 373의 Phase 6 항목명뿐). R은 재계산/재현 검증을 갖지 않는다. → 낮음, MF-9.
- 다음 단계: MF-1(R label/report/units schema + 산출 모듈), MF-3(literal 기대표).

### Q6. scope / route — **agree**

- `ROUTE_STOP`은 route-only로 한정된다: §14 line 588 "stops only the route as configured (EG2 layer19 raw + this LoRA/adapter configuration). It does not stop the EG2 track, does not rescue B0-B, and does not launch H3." ✓
- H3 제외(§10 lines 340–346)와 "F0 results do not automatically launch H3"(line 345) ✓.
- §14 line 590 "lost controls: the earlier MF-4 zero/permuted null and 1-seed signal gate are intentionally out of scope; F0 cannot claim they were replaced." — Phase 6 review MF-4의 null control 미이행을 **은폐 없이 선언**했다. 승인 가능한 축소다. agree.
- causal factor는 §4 line 96 "adapter-as-configured (adapter params + adapter LR + adapter-conditioned forward graph)"로 명시되어, E01−E11이 adapter LR 10×·capacity(+526,336)를 포함함을 부인하지 않는다. 단일 대조의 정직한 한정 ✓.
- association-only·no population inference는 §6.5 lines 251–253과 §14 line 587에서 유지 ✓.
- **잔여(비차단→MF-4에 포함):** wrong-donor 경로의 첫 실행이 Q(13A.8 lines 524–525)인데 Q의 donor 검증이 finiteness/shape뿐이므로, 문서가 적은 "residual risk"보다 실제 잔여 위험이 크다. 완화책(13A.8 line 526, 1-doc unit test)은 **커밋 전 테스트**를 요구하지 않아 증거가 남지 않는다.

## 2. 최종 판정

**NARROW.**

- 설계 코어는 재계산·코드 대조로 정합이다: paired E01−E11 정의(§6.3), cell-level CI, EQUIVALENT 처리와 `.0255` nominal 한정, STOP taxonomy와 reason precedence(§7 lines 295–313), 15-doc conditional estimand, route-only 한정(§14 line 588), step_seed golden 10값, compute 산술. **STOP이 아닌 이유다.**
- 그러나 이번 판 §0가 주장하는 fix 8건 중 **3건이 본문에 없거나 부분적**이다(R CPU schema, R donor hash/provenance, D0 포함 overrun 단일화). 그중 2건은 v1.11 §0와 **동일한 주장의 반복**이다.
- 그리고 gate driver의 read list가 `r_mechanics_pass.json`/`f0_d0.json`을 배제해(§5 line 181) `PROTOCOL_VALID`(§7 lines 264–269)가 **실행상 성립하지 않는다**. fail-closed가 닫히지 않았다.
- MF-1~MF-3은 승인 전 반드시 닫혀야 한다. 다만 문구·schema·필드 수정으로 닫히는 종류라 CONTINUE가 아니라 **NARROW**다.

```text
최종 판정: NARROW

Init: agree
  build_arm_f0 분리(§4 lines 75–94), LORA_SEED_XOR/STEP_SEED_MUL 고정, per-step reseed의 구조적 동일성,
  assertion 9종(lines 96–104). step_seed golden 10값 전부 재계산 일치.
  잔여(비차단): assertion 9(post_step0_weight_change)는 0-update인 P에 적용 불가 → P/Q 목록 분리 권장.

D1: conditional
  custody/seal agree (§Q1). 미해결: D1 frozen table의 donor_count 미정의(MF-3),
  Q/R로의 error/partial 확장 부재(MF-4), off-run overrun 규정 부재(MF-5).

STOP/MDE: agree
  .019170 = .037573/1.96 재계산 일치; 50% MDE .0376, 80% MDE .0537 일치.
  P−PA(+3.0652, SE .6209, 14/15)를 ROUTE_STOP 증거가 아닌 PASS-direction context로 한정(line 380) ✓.
  ALL_FAIL = E01/E11 × copy/full, reason precedence 4단(§7 lines 280–300) ✓.

Cohort: agree
  15 frozen common_ids, 20-doc 일반화 금지(line 190), <15 or <3 seeds → NOT_EVALUABLE(line 260),
  eval_arm_d1 silent drop → NOT_EVALUABLE(line 196). donor pool=val20는 prereg §2.5.6과 정합.

Compute: conditional
  900/1,440/7,200/240 및 D1 480 산술 ✓. R 96 min vs D-157 82.3 min(1,200 updates)
  → F0 900 updates 환산 하한 ≈ 61.7 min, cap 내 ✓.
  미해결: R CPU/affinity 필드 부재(MF-1), T_proj_R operand와 "Wall anchor" 역할 미구분(MF-7),
  P/Q overrun 무규정(MF-5).

Scope: agree
  ROUTE_STOP route-only(line 588), H3 제외(lines 340–346), lost controls 명시(line 590),
  association-only(line 587). 잔여 위험은 Q의 donor 검증 강도(MF-4).
```

## 3. Must-fix (ranked)

1. **[blocker] R artifact schema와 R 산출 주체를 확정하라.** 13A.10에 `r/f0_r_labels.json`, `r/f0_report.json`, `r/units/{cell}_{seed}.json`의 literal schema를 추가하고, 최소 다음을 포함한다: `donor_map_sha256`, `per_doc_donor_id_sha256`, `provenance{code_commit,command,input_sha256,clean_tree}`, `parallel{nproc,threads_per_arm,parallel_wall_s,contention_ratio,cpu_affinity,cgroup_cpu_quota,torch_threads,thread_pool_counts}`, `partial:bool`, `error:<enum>`. §11에 R label/report 모듈을 명시 배정. §0 item 5의 주장을 본문과 일치시키거나 주장을 삭제. (§6.1 line 191, 13A.10 lines 562–576, §11 lines 350–360)
2. **[blocker] decision driver read list를 `PROTOCOL_VALID`와 정합시켜라.** §5 line 181에 `r/r_mechanics_pass.json`과 `d0/f0_d0.json`을 추가하고, line 168을 "no D1 **signal/CE** value; the mechanics predicate may be read"로 한정. `c5_pm_f0_gate.py` negative test에 "labels present + `r_mechanics_pass:false` → non-zero exit"를 추가. (§5 lines 168, 181; §7 lines 264–275)
3. **[blocker] D1 `donor_count`를 정의하고 기대 호출수를 literal로 확정하라.** 13A.4 line 494의 frozen table에서 D1 행의 `donor_count≡1`(또는 열 삭제)을 명시하고, v1.11의 "metadata read ≠ runtime `donor_map_loads`" 구분을 복원. D1 기대치는 `160 = 20 docs × 2 phases × 4 cells`, R은 per-seed/cell/phase 기대표를 literal로 동결(현재 line 575 유예). (13A.4 line 494, line 484–485, 13A.5 lines 501–504)
4. **[high] Q gate를 실효화하고 Q/R에 `error`/`partial`을 신설하라.** `expected_wrong_donor_ce_calls` literal + `pre_r_seed_audit_pass` predicate에 count 일치와 per-doc `evaluated_donors==5` 추가. Q/R schema에 `partial:bool`·D1 enum 재사용 `error` 필드 추가. 근거 코드: `runner/c5_pm_phase6.py:459,464,467`. (13A.10 lines 548–576, §12 line 377)
5. **[high] overrun 단일 규칙을 실제로 통일하라.** §0 item 2에서 D0를 빼고 D0 cap을 25 min+partial로 올리거나, D0를 별도 규칙으로 선언. P/Q 초과 시 결과(abort/partial/NOT_EVALUABLE)를 §12에 명시. 모든 stage의 `partial:true`에 new code SHA + 재승인 절차를 연결. (§0 line 23, §5 line 136, §12 lines 366–377)
6. **[medium] `m_b`를 독립 정의하거나 삭제하라.** `m_b = mean − .05`(b 고정)로 정의해 `m_mean`과 분리하거나 필드를 제거하고 "report all four"를 실제 필드 수와 맞춘다. §0 item 7과 line 304의 표현을 동기화. (§7 line 304)
7. **[medium] `T_proj_R` anchor의 역할을 명시하라.** line 376을 "context only; **not** an operand of the ×3 term"으로 고친다. 4,939.884를 per-arm 항으로 오독하면 `T_proj_R = 3 × 4,939.884 = 14,819.7s = 247.0 min` ≫ 96 min이 되어 line 379의 hard abort가 무조건 발동한다. 정합 해석(3 × 1,646s ≈ 82.3 min)과 F0 900-update 하한 61.7 min을 함께 기재. (§12 lines 372–379)
8. **[medium] P artifact의 단일 권위와 Q hash binding을 정하라.** `d0/init_hashes.json`(13A.1 line 418 append-only)와 `pre_r/pre_r_init_audit.json`(13A.10 lines 537–546) 중 `pre_r_init_audit_pass`의 권위 출처를 하나로 지정(또는 상호 일치 assert). Q schema(548–558)에 P hash echo 필드를 넣어 hash binding을 boolean이 아닌 값으로 만든다.
9. **[low] deviation 등재.** `n_boot=1000→10000`(prereg line 1172)을 §14 deviation 항목으로 등재하고, R의 replay/재계산 검증 유무(`replay_ok` 소멸)를 명시. (§12 lines 216, 242; §14)

## 4. 잘못된 전제

1. **"§0 item 5에서 R schema에 CPU affinity/quota/thread-pool·donor hash를 추가했다"(line 29) — 본문에 없다.** `parallel`은 D1 전용(line 472), R schema(562–574)에는 해당 필드도 `provenance` object도 없다. v1.11 §0 item 1/9와 동일 주장의 반복이다.
2. **"§0/§5/§12/**D0** 모두 동일 overrun 규칙"(line 23) — 아니다.** D0는 15분 repair-first(line 136), P/Q는 결과 무규정(lines 366–367), R은 partial 필드 부재.
3. **"donor-count/load 모순 해결"(lines 19–21) — 절반만.** 13A.5만 R-only로 좁혔고, D1 frozen table의 `donor_count` 열(line 494)과 v1.11의 metadata/load 구분 문장(삭제됨)은 남았다.
4. **"`m_b` separate b-relative margin"(line 33) — 독립 필드가 아니다.** `m_b=m_mean`(line 304).
5. **"D1 values must not be read for Stage R or STOP"(line 168) — §7의 "D1 pass predicate"와 line 181의 판독과 충돌한다.** "signal/CE 값" 한정어가 필요하다.
6. **문서 식별 불일치(비차단).** 요청서 §0 제목 "Block 3 Round 2/10" vs 사용자 지시 "new 10-round block, round 1". 또한 요청서 §0는 `v1_11`을 열람 대상으로 적고 사용자 지시는 `v1_10`을 적는다 — 두 판 모두 열람했고, 판정은 어느 쪽 결론도 상속하지 않는다.

## 5. 검증 완료 / 검증 불가

- **검증 완료(재계산·코드 대조):**
  - HEAD `f994c10`, `fetch`/`pull --ff-only` up-to-date.
  - step_seed golden 10값 전부: 20261108 → `0x9f02514d`, `0x3d5bdb86`, `0xdb9345df`; 20261109/10/11 → `0x9f02514c/4f/4e`, `0x3d5bdb87/84/85`, `0xdb9345de/dd/dc`.
  - 통계: `.037573/1.96=.019170`, `1.96×.0255=.049980`, `2.405/√15=.6210`, `2.802×.019170=.053714`, EQUIVALENT mean 범위 `±.012427`.
  - count: `300×3=900`, `120×12=1,440`, `600×12=7,200`, `20×12=240`, D1 `120×4=480`; D1 donor_count 분기 `160` vs `800`.
  - 코드: `arm_spec` F/L/P/PA 한정(`runner/c5_pm_phase6.py:125–139`), `donor_map`:404, `eval_arm_d1` silent drop `:459`, `:464`, `n_donors` 무검증 `:467`, `K_M_L=753` `:57`, `EXPECTED_LORA_MODULES=64` `:54`; `donors_for`(`runner/c5_mt5_lora_b0.py:318–326`).
  - 문서: prereg §2.5.6(donor rule), §9.6.1(phase7 600/arm-seed), §10.1(`n_boot=1000`), `n_min_signal=15`; decisions D-156(:216), D-157(:218).
  - v1.10→v1.12 및 v1.11→v1.12 diff로 이번 라운드 변경 범위 특정.
- **검증 불가:** F0 코드 미구현(§11 line 359 "No F0 code is implemented by this draft") → D1 seal/gate는 문구 수준 검토. `r/f0_report.json`·`r/f0_r_labels.json`은 schema 부재로 검토 대상 자체가 없다(MF-1).
- **상태 불변:** F0 = 미승인·미실행. Phase 6 = negative 종료, B0-B = 미승인, test 163 = sealed, P1 = unused, T5Gemma2 = D-108 STOP.