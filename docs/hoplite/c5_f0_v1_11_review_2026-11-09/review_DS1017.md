# C5 F0 v1.11 — Independent Review (DS1017)

- Reviewed HEAD: `5aa18b1c857a29b3190b683098e3f098f1ce4063`
- Sync: `git fetch origin` → `git pull --ff-only origin main` → **Already up to date.**
- 대상: `docs/plan_c5_f0_v1_11_2026-11-09.md` (659 lines)
- 새 10-round block round 1/10. v1.10 결론 상속 없음. 이 문서는 승인/실행이 아니다.
- test 163 sealed, P1 unused, T5Gemma2 D-108 STOP 유지.

## 0. Verbatim paired E01−E11 (plan §6.3, lines 219–224)

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

Primary positive (line 229):

```text
mean_D > 0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0
```

## 1. Q1–Q6

### Q1. CPU/D1 custody — **conditional**

- **CPU observability is only half-applied.** §0 item 1 (line 20) claims `parallel`/R provenance에 `cpu_affinity`, `cgroup_cpu_quota`, `torch_threads`, `thread_pool_counts`를 추가했다. 실제로는 D1 `parallel` object (line 478)에만 있다. R mechanics schema `r/r_mechanics_pass.json` (13A.10, lines 570–578)에는 네 필드가 모두 없고, §11 (line 350)도 `nproc`/`threads_per_arm`/`parallel_wall_s`/`contention_ratio`만 나열한다. 따라서 R provenance는 CPU 관측이 빠져 있다.
- **D1 custody는 대체로 충분하다.** §13 (lines 395–408) inventory는 `d1/f0_d1_mechanics.json` 단일이고, 13A.4 writer allowlist (line 503)와 일치한다. checkpoint digest 기록 후 삭제, `checkpoint_absent:true`, no-load, `per_doc`/`delta_*`/`d1_sealed` negative test는 seal로 인정한다.
- **남는 custody gap 3건.** (a) §0 item 11 (line 33)은 "logs/temp/crash paths tested"라고 하지만 13A.4 (line 504)의 filesystem test는 checkpoint/negative test만 열거하고 log/temp 경로 test가 없다. (b) §13 inventory에 `r/r_mechanics_pass.json`과 `data_scope.json`이 빠져 있다. (c) D0 overrun (line 142)은 "repair first"만 있고 hard abort/partial 규칙이 없다.
- **Host 전제.** 13A.7 (line 522)은 "current 4-vCPU workspace fails; no F0 run there"라고 명시한다. 따라서 승인은 16-core host 확보에 조건부다.

### Q2. wrong-donor/error enum — **conditional**

- **Error enum은 D1에만 있다.** `error: enum{TIMEOUT,OOM,CE_NONFINITE,SHAPE_MISMATCH,CHECKPOINT_DIGEST_FAIL,OTHER_REDACTED}|null`은 13A.4 (line 496)에만 정의된다. Q schema (13A.10, lines 550–560)와 R mechanics schema (lines 570–578)에는 `error`/`partial` 필드가 없다. 따라서 Q/R crash path는 schema상 표현 불가다.
- **Q schema `wrong_donor_ce_calls`는 실제로 없다.** §0 item 3 (line 25)과 13A.8 (line 530)은 "Q schema records `wrong_donor_ce_calls`"라고 하지만, 13A.10 Q schema는 `seed`, `units`, `trained_updates`, `e00_updates`, `cells{post_step0_rng_sha256, group_change_ok, wrong_donor_finite, shape_ok}`, `pre_r_seed_audit_pass`만 갖는다. 문서 내부 모순이다.
- **D1 `wrong_donor_ce_calls:0`은 13A.8과 정합한다.** D1은 wrong-donor CE를 호출하지 않으므로 (line 529) 0이 맞다. 다만 그 결과 13A.5의 `evaluated_donors == 5`와 충돌한다 (Q3).
- `OTHER_REDACTED`의 생성 규칙과 "CE 값 문자열 금지"의 test가 없다. redaction이 실제로 CE 값을 숨기는지 검증 불가.

### Q3. donor-count/overrun/provenance — **disagree**

- **Donor-count 모순은 해소되지 않았다.** §0 item 5 (line 29)는 `donor_count`를 frozen metadata, `donor_map_loads`를 runtime count로 분리한다. 그러나 13A.5 (line 509)는 "For every doc/cell: `evaluated_donors == 5` and `expected_donors == 5`; abort otherwise"를 요구하고, D1 schema는 `donor_map_loads: int (must 0)` (line 491)을 요구하며 `cells` object (lines 460–470)에 donor 필드가 없다. donor를 평가하면 `donor_map_loads > 0`이고, 평가하지 않으면 `evaluated_donors == 5`가 성립하지 않는다. 두 조건은 동시에 성립할 수 없다. v1.10의 DS 지적과 동일한 모순이 남아 있다.
- **Overrun "single rule"은 통일되지 않았다.** §0 item 6 (line 31)은 ">25 min: hard abort, partial, new code SHA + explicit stage re-approval. §0/§5/§12 문구 통일"이라고 선언한다. 실제 문구는 세 가지다: §5 D1 (line 163) "cap ≤25 min parallel; sequential is diagnostic only"; §12 (line 383) "repair or re-review; no silent extension"; D0 (line 142) "repair first". hard abort/partial/new-SHA/re-approval은 §0에만 있다.
- **4,939.884s provenance 모순이 그대로다.** §12 line 378은 "registered 4,939.884s = 2 threads/arm **measured** (D-157)"라고 하고, line 382는 "Wall anchor (estimate): Phase 6 registered 4,939.884s at 2 threads/arm; **not a measurement**"라고 한다. 같은 §12 안에서 measured/not-measured가 충돌한다.
- **R mechanics expected count가 schema에 없다.** 13A.10 (lines 570–578)은 `real_memory_ce_calls`, `wrong_donor_ce_calls`, `donor_map_loads`를 int로만 두고 `expected_*` 필드가 없다. line 579의 "all expected counts equal"은 literal schema로 표현할 수 없다.

### Q4. near-threshold/EQUIVALENT — **conditional**

- **b∈{+0.05,0}는 추가됐지만 m_sign이 b를 쓰지 않는다.** §7 (line 310)은 `m_mean=mean-b`, `m_lower=CI.lower-b`, `m_sign=(#seeds>0)-2`를 정의한다. b=+0.05일 때 sign gate는 `D_s > 0.05`인 seed 수여야 하는데, 식은 `D_s > 0`인 seed 수를 센다. 또한 `mean`이 `mean_D`인지 cell mean인지 명시되지 않는다.
- **EQUIVALENT 정의는 정합한다.** §6.5 (line 254) "95% CI_D entirely within [-.05,+.05]"와 §7 (line 305) `CI_D.lower >= -.05 AND CI_D.upper <= +.05`는 같다. §12 (line 386) `SE_D <= .0255`는 1.96×SE ≤ .05와 일치한다.
- **"EQUIVALENT is nominal only; realized CI governs" (line 310)는 자기모순이다.** EQUIVALENT는 realized CI로 정의되므로 "nominal only"가 성립하지 않는다. 의도가 "population equality claim이 아니다"라면 그렇게 써야 한다.
- PASS와 EQUIVALENT는 상호배타적이다 (PASS: lower > +.05; EQUIVALENT: upper ≤ +.05). 이 부분은 정합한다.

### Q5. R donor identity/hash — **conditional**

- **필드는 추가됐지만 canonicalization과 schema home이 없다.** §6.1 (line 197)은 "R report records `donor_map_sha256` and per-doc donor-ID hash and asserts equality"라고 한다. 그러나 (a) hash 입력의 canonical form (정렬 여부, delimiter, UTF-8, doc ID vs 0..4 index)이 정의되지 않았고, (b) `r/f0_report.json` schema가 없으며 `r/r_mechanics_pass.json` (lines 570–578)에도 `donor_map_sha256`이 없고, (c) "asserts equality"의 대상 (`init_hashes.json`의 donor map hash)이 정의되지 않았다.
- **donor identity 자체는 재현 가능하다.** `donors_for` (runner/c5_mt5_lora_b0.py:318)는 length-nearest + id tie-break로 결정적이고, "same for all arms/seeds"다. 따라서 canonicalization만 고정하면 hash binding은 성립한다.

### Q6. scope/route — **agree (with caveats)**

- ROUTE_STOP route-only, H3 out of scope (§10, §14)는 적절하다. B0-B rescue 금지, EG2 track STOP 아님, H3 자동 launch 없음이 명시돼 있다.
- Primary E01 vs E11은 LoRA를 고정하고 adapter만 바꾸는 F0-vs-L 대조로, Phase 6 cause report의 H1/MF-4 요청과 일치한다. E00/E10은 descriptive로 한정했다.
- **Caveat 1:** §14는 zero/permuted null과 1-seed gate를 의도적으로 제외하고 "F0 cannot claim they were replaced"라고 한다. 정직하지만, wrong-donor numerical path는 Q에서 finiteness/shape만 보고 R에서 처음 persist/aggregate된다 (13A.8, line 530). 유일한 mitigation은 1-doc unit test (line 531)이고, F0에는 positive control (P)이 없다. R 전에 known-doc real-vs-wrong CE ordering 같은 numerical sanity check가 필요하다.
- **Caveat 2:** F0 code가 없다. line 365 "No F0 code is implemented by this draft", `runner/`에 `c5_pm_f0*.py` 없음. Stage approval은 committed code + SHA 이후에만 가능하다.

## 2. Init / D1 / STOP-MDE / Cohort / Compute / Scope

- **Init: agree.** §4 golden table을 직접 재계산해 검증했다. `step_seed(20261108,0..2)=0x9f02514d/0x3d5bdb86/0xdb9345df`; 20261109/10/11 = `0x9f02514c/4f/4e`, `0x3d5bdb87/84/85`, `0xdb9345de/dd/dc`. 공식 `(seed ^ ((0x9E3779B9*(step+1)) & 0xffffffff)) & 0xffffffff`와 일치한다. per-step structural reseed, `LORA_SEED_XOR`, adapter-independent reset은 sound하다.
- **D1: conditional.** Custody는 대체로 충분하나 donor-count 모순, log/temp test 부재, D0 overrun 규칙 부재가 남는다.
- **STOP/MDE: conditional.** Taxonomy는 mutually exclusive/exhaustive하고 precedence가 명확하다. 다만 near-threshold `m_sign`이 b를 쓰지 않고, EQUIVALENT "nominal only" 문구가 자기모순이다.
- **Cohort: agree (with caveat).** 15 length-eligible docs, 3 seeds, 5 donors, fixed donor graph, 20-doc descriptive only는 정합한다. Donor map이 `donors_for(val20, cache)`이므로 제외된 5 docs가 donor가 될 수 있다는 점을 명시적으로 declare해야 한다.
- **Compute: conditional.** 16-core host 필수 (13A.7 line 522), 현재 4-vCPU workspace는 실행 불가. D1 25min/R 96min cap은 그럴듯하나 overrun 규칙이 통일되지 않았다.
- **Scope: agree.** Route-only, H3 out, no B0-B rescue, no test163/P1.

## 3. Must-fix (ranked)

1. **Donor-count/load 모순 해소 (blocker).** 13A.5 `evaluated_donors==5` vs D1 `donor_map_loads must 0`; D1 `cells`에 donor 필드를 추가하거나 13A.5를 R 전용으로 한정하라.
2. **Overrun single rule 통일 (blocker).** §0/§5/§12/D0에 하나의 hard-abort/partial/new-SHA/re-approval 규칙을 적용하라.
3. **4,939.884s measured/not-measured 모순 제거 (blocker).** §12 line 378과 line 382 중 하나로 통일하라.
4. **Q schema에 `wrong_donor_ce_calls` 추가 또는 §0 item 3/13A.8 문구 철회 (blocker).**
5. **R mechanics schema 보강.** `expected_*` counts, `error`/`partial`, `cpu_affinity`/`cgroup_cpu_quota`/`torch_threads`/`thread_pool_counts`, `donor_map_sha256`을 추가하라.
6. **`donor_map_sha256` canonicalization 정의 + schema home 부여.**
7. **Q/R crash path에 error/partial enum 추가.**
8. **Near-threshold `m_sign`을 b 기준으로 수정하고 statistic을 명시.**
9. **Artifact inventory 완성.** `r/r_mechanics_pass.json`, `data_scope.json` 추가.
10. **R 전 wrong-donor numerical sanity check 추가.** 1-doc unit test만으로는 부족하다.
11. **F0 code commit + SHA, 16-core host 확인 후 stage approval.**

## 4. 잘못된 전제

- "§0/§5/§12 문구 통일" — 거짓. 세 가지 overrun 문구가 남아 있다.
- "Q schema에 `wrong_donor_ce_calls` 추가" — 거짓. Q schema에 없다.
- "4,939.884s measured" — 같은 §12의 "not a measurement"와 충돌한다.
- "donor_count metadata vs donor_map_loads runtime" — 13A.5의 `evaluated_donors==5`를 해소하지 못한다.
- "parallel/R provenance CPU fields" — D1에만 있고 R schema에는 없다.

## 5. 최종 판정

**NARROW.**

설계 자체는 sound하고 init contract는 검증됐다. 그러나 v1.11은 여전히 문서 내부 모순 (donor-count/load, overrun 3중 문구, 4,939.884s measured/not-measured, Q schema 누락, R schema expected-count 부재)을 포함하며, 이 상태로 D1/R artifact를 만들면 재조정 불가능하다. 위 must-fix 1–5를 먼저 수정하고 재검토하라. 실행은 승인하지 않는다.