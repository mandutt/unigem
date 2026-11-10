# C5 F0 v1.8 — Independent Review (DS1017)

- 검토일: 2026-11-10
- 대상: `docs/plan_c5_f0_v1_8_2026-11-09.md`
- **Reviewed HEAD: `ac1ee40da32427d452bd5d89bb339f034b2b7c9c`**
- 동기화: `git fetch origin` ok; `git pull --ff-only origin main` → **Already up to date.**
- 범위: consultation only. 학습/평가 없음, test 163/P1 없음, subagent 없음, 이 파일 외 repo 수정 없음.
- v1.7 결론 상속 없음. 새 10-round block, round 8.

---

## 0. Verbatim paired E01−E11 (mandatory)

§2 (line 69):

```text
- Primary: **E01 vs E11** (LoRA initialization matched).
```

§6.2 (line 216):

```text
delta_c(s,d) = mean_donor( CE_wrong_donor - CE_real )
```

§6.3 (lines 225–229):

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

§6.4 (lines 243–248):

```text
SIGNAL(c,copy) = mean(delta_c) >= .05
                 AND CI.lower > 0
                 AND 2/3 seeds > 0
SIGNAL(c,full) = mean(delta_c) > 0
                 AND CI.lower > 0
                 AND 2/3 seeds > 0
```

---

## 1. 판정 요약

| Q | 판정 | 핵심 |
|---|---|---|
| Q1 P/Q/R gates/schema/hash | **conditional** | init audit는 강하나 §13A.10 P/Q schema가 seed 차원을 표현 못 함 |
| Q2 D1 real CE/seal/telemetry | **conditional** | seal은 강하나 `expected_real_memory_ce_calls` 산식이 틀림 |
| Q3 STOP/MDE/near-threshold | **agree** | 4-state 상호배타·전체포괄; MDE 산술 검증됨 |
| Q4 cohort/cell CI | **agree** | 15 common frozen, doc 3/3, n_donors=5, n_boot=10000 |
| Q5 compute 2/arm/caps/lower-bound | **conditional** | 2/arm·900 updates·96 min 정합; D1 25 min fallback 부재 |
| Q6 scope/negative reads | **agree** | read-path negative test, ROUTE_STOP route-only, H3 제거 |

**최종 판정: NARROW.**

---

## 2. Q1 — P/Q/R gates/schema/hash

**판정: conditional.**

### 2.1 검증된 것 (agree)

- **step_seed golden table (§4, lines 116–119)**: 직접 계산해 전부 일치.
  - `step_seed(20261108,0..2) = 0x9f02514d / 0x3d5bdb86 / 0xdb9345df`
  - `20261109 = 0x9f02514c / 0x3d5bdb87 / 0xdb9345de`
  - `20261110 = 0x9f02514f / 0x3d5bdb84 / 0xdb9345dd`
  - `20261111 = 0x9f02514e / 0x3d5bdb85 / 0xdb9345dc`
  - Formula `(seed ^ ((0x9E3779B9 * (step+1)) & 0xffffffff)) & 0xffffffff`와 일치.
- **구조적 RNG equality (§4, line 105)**: per-step reseed가 dropout RNG를 구조적으로 고정. E01/E11이 `manual_seed(seed ^ 0x5EED10A5)`를 동일하게 호출하므로 adapter 생성 여부와 무관하게 post-init RNG가 같다. assertion 4/5가 타당.
- **Phase 6 I/O assert (§4, line 125)**: “F0 E11 ≠ Phase 6 L”라는 untestable 주장을 `open`/`torch.load` path audit zero로 대체. 올바른 방향.
- **§13A.6 (lines 517–525)**: hash-inequality assertion을 tautological로 제거한 것 타당. protected path 3종 + negative probe.
- **§13A.2 serialization grammar (lines 437–449)**: fixed-width LE, dtype whitelist, KAT fixture. 재현 가능.

### 2.2 결함 (disagree)

**MF-2 (blocker): `pre_r_init_audit.json`이 seed 차원을 표현하지 못한다.**

§13A.10 (lines 547–556):

```text
schema_version:"1"
seeds:[20261108,20261109,20261110]
cells:{E00,E10,E01,E11 -> {hash, lora_names,n_params}}
kat_sha256:string
p_r_hash_equal:bool
pre_r_init_audit_pass:bool
```

- `cells`는 단일 object이고 seed nesting이 없다. 그런데 바로 아래 predicate는 “`pre_r_init_audit_pass` = **3 seeds × 4 cells** present”라고 요구한다 (line 557).
- 3 seeds × 4 cells = 12 hash를 담을 자리가 schema에 없다. `p_r_hash_equal`도 seed별이어야 하는데 scalar bool 하나뿐이다.
- 결과: 구현자가 (a) 마지막 seed만 덮어쓰거나 (b) schema를 임의 확장해야 한다. 어느 쪽이든 “frozen schema”가 아니다.

**MF-3 (blocker): `q_seed_audit/{seed}.json`의 per-seed count가 틀렸다.**

§13A.10 (lines 559–568):

```text
seed:int
units:12
trained_updates:9
e00_updates:0
cells:{... -> {post_step0_rng_sha256, group_change_ok, wrong_donor_finite, shape_ok}}
pre_r_seed_audit_pass:bool
```

- 파일 경로가 `{seed}.json`이므로 per-seed artifact다. per-seed는 **4 units / 3 trained updates**다 (§13A.1 line 431: “3 seeds × 4 cells = 12 units, 9 trained updates”는 3-seed 총계).
- `units:12`, `trained_updates:9`는 총계를 per-seed 파일에 넣은 것. predicate “all 4 cells present” (line 568)와도 모순.
- §12 compute table Q row (line 378)의 “12 units (9 trained updates)”는 총계로 맞지만, artifact schema와 혼동을 만든다.

### 2.3 다음 단계

1. `pre_r_init_audit.json`을 `per_seed:{seed -> {cells:{...}, p_r_hash_equal}}`로 재정의하고, top-level `p_r_hash_equal`은 per-seed AND로 정의.
2. `q_seed_audit/{seed}.json`을 `units:4`, `trained_updates:3`으로 고치고, 12/9는 §12 aggregate에만 남긴다.
3. 두 schema를 D0 이전에 commit하고 KAT와 함께 freeze.

---

## 3. Q2 — D1 real CE/seal/telemetry

**판정: conditional.**

### 3.1 검증된 것 (agree)

- **D1 seal 구조 (§5, lines 150–180)**: digest-only checkpoint, `checkpoint_absent:true`, loading forbidden, `d1_report.json` exact-path forbidden, `d1_sealed/` 부재, negative test. v1.0 DS-1의 “checkpoint oracle” 지적을 정면으로 닫았다.
- **literal allowlist (§13A.4, lines 456–512)**: `f0_d1_mechanics.json` key를 전부 열거하고 “Only these keys”로 닫음. `per_doc`/`final`/`delta_*`/`signal`/`phase7` object 금지.
- **crash path (§13A.4, line 511)**: `partial:true` + `error` + checkpoint 삭제, 다른 파일 없음. success/partial 두 shape만 허용.
- **§13A.8 (lines 533–538)**: D1이 wrong-donor CE를 호출하지 않음을 명시하고, Q는 finiteness/shape만, 첫 numerical exercise는 R이라는 residual risk를 명시. 정직한 한계 선언.

### 3.2 결함 (disagree)

**MF-1 (blocker): `expected_real_memory_ce_calls` 산식이 차원적으로 틀렸고 §5 D1과 모순된다.**

§13A.4 (line 506):

```text
Expected `real_memory_ce_calls` = E00 step0 1 + E10/E01/E11 step0 1 each
  + E10/E01/E11 final donor-crop 15 docs × 5 donors each + M CE count from report;
  exact integer frozen in `f0_d1_mechanics.json` and compared.
```

- **15 vs 20**: §5 D1 assertion 4 (line 160)는 `n_docs_step0 == 20` and `n_docs_final == 20`을 요구한다. 산식은 15 docs를 쓴다. 15는 R primary cohort이고 D1 cohort가 아니다.
- **“1” per cell vs per-eval call count**: “E00 step0 1 + E10/E01/E11 step0 1 each”는 eval pass 수(4)와 call 수를 섞는다. 실제 real CE call은 evaluator 설계에 따라 (a) `eval_arm_d1` 재사용 시 doc×donor = 20×5 = 100/eval, (b) 신규 mechanics evaluator가 doc당 1회면 20/eval이다. 어느 쪽도 “1”이 아니다.
- **총계**: F0 D1은 E00 1 eval + E10/E01/E11 2 evals = 7 evals. (a)면 700, (b)면 140. 산식 `1+3+3×15×5 = 229`는 둘 다 아니다.
- 이 값은 `mechanics_pass`의 hard gate다 (§13A.4 line 507: `real_memory_ce_calls_ok==true`). 틀린 정수를 freeze하면 D1이 항상 실패하거나, counter를 틀린 산식에 맞춰 정의해 gate가 무의미해진다.

**MF-4 (high): “values are never materialized” overclaim.**

§5 D1 (line 177): “This is stronger than a seal: the values are never materialized in D1.”

- 그러나 §5 D1 assertion 5 (line 161)는 “M records == 120/cell; total 480”, assertion 7 (line 163)는 “generation == 20/cell; total 80”을 요구한다. M records와 generation은 D1에서 계산된다. M record는 real CE 값을 담는다.
- 정확한 주장은 “**signal delta values**는 materialize되지 않는다”이다. M/generation count는 in-memory로 계산되지만 persist되지 않는다(§13A.4 “counts only”). 문장을 그렇게 한정해야 한다.

### 3.3 다음 단계

1. `expected_real_memory_ce_calls`를 committed mechanics evaluator의 실제 call graph에서 유도해 freeze. 최소한 20 docs를 쓰고, “1 per cell”을 “per-eval call count”로 바꾼다.
2. §5 D1 line 178을 “signal delta values are never materialized; M/generation counts are computed in memory but not persisted”로 수정.
3. D1 negative test에 “wrong `expected_real_memory_ce_calls` → `mechanics_pass:false`”를 추가.

---

## 4. Q3 — STOP/MDE/near-threshold

**판정: agree.**

### 4.1 4-state taxonomy (§7, lines 291–324)

- **상호배타**: `PASS_POSITIVE`는 `CI_D.lower > +.05` (line 309), `EQUIVALENT`는 `CI_D.upper <= +.05` (line 293). lower > .05이면 upper > .05이므로 교집합 없음. `PASS_POSITIVE`는 `SIGNAL(E01,copy)`를 요구하고 `ROUTE_STOP`은 `ALL_FAIL`(=`FAIL(E01,copy)` 포함)을 요구하므로 교집합 없음. `harm`(lower>0)과 `benefit`(upper<0)은 교집합 없음.
- **전체포괄**: priority 1 `NOT_EVALUABLE`, 2 `PASS_POSITIVE`, 3 `ROUTE_STOP`(ALL_FAIL), 4 `INDETERMINATE`(not ALL_FAIL and not PASS). PROTOCOL_VALID 하에서 네 상태가 모든 경우를 덮는다.
- **reason precedence** (line 310): `no_signal_equivalent` > `adapter_harm` > `adapter_benefit` > `no_signal_uncertain`. EQUIVALENT와 harm이 동시에 성립(예: CI_D=[.01,.04])해도 EQUIVALENT가 우선하므로 결정적.
- **harm/benefit vs PASS** (line 319): PASS는 CI_D.lower>.05를 요구하므로 PASS⇒harm. “not mutually exclusive with PASS”는 서술 방향으로서 맞고, ROUTE_STOP reason과는 ALL_FAIL 배타성으로 충돌하지 않는다.

### 4.2 near-threshold (§7, line 315)

- v1.7의 “paired mean_D/CI_D로 cell gate 진단” 모순을 **cell-level SIGNAL copy/full means and CIs**로 고쳤다. boundary b∈{.05,0}, h=(CI.upper−CI.lower)/2, near if |mean−b|<=h. ALL_FAIL을 구동하는 통계와 동일한 통계를 쓰므로 정합.
- paired `mean_D/CI_D`는 “paired-contrast diagnostic”으로 명시적으로 relabel. 올바른 분리.

### 4.3 MDE (§12, line 391)

- `.019170 = .037573/1.96` 검증: Phase 6 `labels.json` `L_COPY_SIGNAL.paired` CI = [−0.0408448, +0.0343022], half-width = 0.0375735, SE = 0.0191702. 일치.
- P−PA reference dispersion 검증: 15 common ids에서 mean **3.06520**, SD **2.40476**, SE **0.62091**, **14/15** positive. 문서 값(+3.0652, 0.6209, 2.405, 14/15)과 일치.
- `.104`/`.0876` 제거, `.037573`/`.019170` 유지. “F−L LoRA contrast planning proxy, not a validated E01−E11 SE”로 한정. 올바름.
- §6.5 (line 264): “With n=15, .0376 F−L proxy and P−PA SD 2.405: expected branch is undetermined; PASS and ROUTE_STOP are both live.” 정직한 power statement.

### 4.4 다음 단계

1. 없음 (Q3는 승인 가능). 단, MF-1/MF-2/MF-3 수정 후 §7의 cell CI가 §13A.10 schema와 일치하는지 재확인.

---

## 5. Q4 — cohort/cell CI

**판정: agree.**

- **15 common frozen binding (§6.1, lines 196–210)**: `common_ids`는 preflight frozen, length-selected(20 중 5 제외, K=753). “Generalization to the 20-doc val population is forbidden” 명시. 20-doc F/L은 descriptive only.
- **doc 3/3 seed completeness (§6.1, line 207)**: `eval_arm_d1`이 non-copyable doc을 silently drop하므로 “missing doc means NOT_EVALUABLE, never a smaller cohort” (line 208). v1.0 DS-2의 15→14 substitution 위험을 닫음.
- **n_donors=5 + all-cell donor set equality (§6.1, lines 205–206; §13A.5, lines 513–516)**: doc마다 정확히 5 donors, E00/E10/E01/E11 donor set 동일. `evaluated_donors == expected_donors == 5` abort.
- **n_boot=10000 override (§6.3, lines 227–228)**: frozen N_BOOT=1000을 explicit override하고 `assert realized.n_boot == 10000 and realized.seed == 20261109`. `l_predicate` bootstrap 금지. v1.0 DS-6을 닫음.
- **doc-level CI + seed-sign gate (§6.3, lines 230–238)**: `CI_D`는 doc-level only, `D_s`는 seed-level gate/descriptor. “not a per-cell significance conjunction” 명시. 올바른 분리.
- **donor-cluster sensitivity (§6.1, line 203)**: leave-one-donor-out recomputation + range. donor reuse from val docs declared. 적절.
- **cell CI construction (§6.4, line 253)**: 15 docs × 5 donors, seed mean over 3 seeds, `bootstrap_paired_v2(n_boot=10000, seed=20261109, percentile linear)`, `CI.lower` = 2.5th percentile. `ALL_FAIL`/`ROUTE_STOP`은 frozen cell CI를 소비하고 decision time re-bootstrap 없음 (line 254).

### 5.1 잔여 (non-blocking)

- 15-doc cohort의 length-selection은 acknowledged. 다만 `SIGNAL(c,copy)`의 `mean>=.05`가 15-doc에서 얼마나 안정적인지는 realized CI가 결정한다. 문서가 “undetermined”로 정직하게 남긴 것은 적절.

### 5.2 다음 단계

1. 없음 (Q4는 승인 가능). MF-2/MF-3 수정 시 `pre_r_init_audit`/`q_seed_audit`가 15-doc cohort와 독립임을 재확인.

---

## 6. Q5 — compute 2/arm/caps/lower-bound

**판정: conditional.**

### 6.1 검증된 것 (agree)

- **2 threads/arm (§0, lines 20–21; §12, lines 375–381)**: D-157 registered anchor가 2 threads/arm임을 확인 (`docs/decisions.md` D-157: “3 wave(4 arms each, 2 threads) wall 4,939.9s”). v1.7의 1/arm 및 v1.0의 3/arm 혼선을 정리.
- **900 updates (§5 R, line 185)**: 3 seeds × 3 trained cells × 100 = 900. E00 eval-only. 정확.
- **M 1,440 / phase7 7,200 / generation 240 (§5 R, line 186)**: 4×3×120, 4×3×600, 4×3×20. 정확.
- **R 96 min binding (§12, line 388)**: Phase 6 registered 4,939.9s = 82.3 min at 2 threads/arm. F0는 1,200→900 updates로 줄어드므로 96 min은 margin 있음.
- **T_proj lower bound (§13A.7, line 530)**: D1-derived T_proj가 R-only replay terms 부재로 lower bound임을 명시. R binding gate는 measured wall ≤96 min. 올바른 방향.
- **nproc>=16 hard abort (§12, line 390; §13A.7, line 528)**: 4-vCPU workspace는 non-qualifying. 정확.
- **contention_ratio (§12, line 389)**: `parallel_wall_s / sum(per_arm_phase_s)`, nproc/threads_per_arm 기록. 적절.

### 6.2 결함 (disagree, minor)

**MF-5 (medium): D1 25 min provisional에 measured >25 min fallback이 없다.**

- §5 D1 (line 168): “cap ≤25 min parallel; sequential is diagnostic only, not a gate and not a cap claim.”
- Phase 6 D1 measured 1,180.6s = **19.7 min at 3 threads/arm** (D-156). F0 D1은 2 threads/arm이므로 더 느릴 수 있다. 25 min은 tight.
- §5 D0는 “If measured >15 min, repair first” (line 147)라는 fallback이 있지만, D1에는 “measured >25 min이면 어떻게”가 없다. “provisional”만으로는 gate가 아니다.

**MF-6 (medium): `r_mechanics_pass.json`이 D1 대비 비대칭이다.**

- §13A.10 (lines 571–578): `seeds:3, cells:4, updates_total:900, m_records:1440, phase7_records:7200, provenance_ok, r_mechanics_pass`.
- D1은 `real_memory_ce_calls`, `wrong_donor_ce_calls`, `donor_map_loads`, `checkpoint_absent`를 gate하지만, R schema에는 없다. R은 real run이므로 checkpoint_absent는 N/A일 수 있으나, `real_memory_ce_calls`/`wrong_donor_ce_calls`/`donor_map_loads`는 R에서도 provenance gate로 유효하다. 비대칭의 이유를 명시하거나 필드를 추가해야 한다.

### 6.3 다음 단계

1. D1에 “measured wall >25 min → repair or re-review, no silent extension”을 명시.
2. `r_mechanics_pass.json`에 `real_memory_ce_calls`/`wrong_donor_ce_calls`/`donor_map_loads`를 추가하거나, R에서 N/A인 이유를 한 줄로 명시.

---

## 7. Q6 — scope/negative reads

**판정: agree.**

- **test163/P1 read-path negative tests (§13A.7, line 531)**: “direct open attempts must fail; flags alone are not evidence.” v1.0 MF-6의 “attestation is not proof” 지적을 read-path test로 닫음.
- **frozen ID allowlists (§13A.9, line 541)**: “Frozen ID allowlists apply in code; test 163 and P1 paths are not opened.” `data_scope.json` records `test_split_used:false`, `p1_used:false`.
- **ROUTE_STOP route-only (§14, line 592)**: “stops only the route as configured (EG2 layer19 raw + this LoRA/adapter configuration). It does not stop the EG2 track, does not rescue B0-B, and does not launch H3.” 정확한 경계.
- **H3 out of scope (§10, lines 351–358)**: H3 arm/trigger/rank/identity/null/donor-discrimination endpoint 미등록. “F0 results do not automatically launch H3.” v1.0의 H3 결합 위험을 제거.
- **association-only (§14, line 591)**: “F0 tests adapter-as-configured in this fixed EG2/LoRA route; it does not identify an architecture-only bottleneck.” Phase 6 cause report의 “adapter-associated signal loss (native path)” 한정과 일치.
- **lost controls (§14, line 594)**: “the earlier MF-4 zero/permuted null and 1-seed signal gate are intentionally out of scope; F0 cannot claim they were replaced.” 정직한 손실 선언.

### 7.1 다음 단계

1. 없음 (Q6는 승인 가능). MF-1~MF-3 수정 후 §13A.9의 allowlist가 §13A.10 schema와 함께 freeze되는지 확인.

---

## 8. Ranked must-fix

| rank | severity | must-fix | 위치 |
|---:|---|---|---|
| 1 | **blocker** | `expected_real_memory_ce_calls` 산식을 committed mechanics evaluator의 실제 call graph에서 유도. 15→20 docs, “1 per cell”→per-eval call count. 틀린 정수를 freeze하면 `mechanics_pass` gate가 깨진다. | §13A.4 line 506; §5 D1 line 160 |
| 2 | **blocker** | `pre_r_init_audit.json`에 seed 차원 추가(`per_seed:{seed -> {cells, p_r_hash_equal}}`). 현재 schema는 3 seeds × 4 cells를 표현 못 함. | §13A.10 lines 547–556 |
| 3 | **blocker** | `q_seed_audit/{seed}.json`을 per-seed `units:4`, `trained_updates:3`으로 수정. 12/9는 §12 aggregate에만. | §13A.10 lines 559–568 |
| 4 | high | §5 D1 “values are never materialized”를 “signal delta values are never materialized; M/generation counts are computed in memory but not persisted”로 한정. | §5 D1 line 177 |
| 5 | medium | D1 measured wall >25 min fallback 명시(repair or re-review, no silent extension). | §5 D1 line 168 |
| 6 | medium | `r_mechanics_pass.json`에 `real_memory_ce_calls`/`wrong_donor_ce_calls`/`donor_map_loads` 추가 또는 R N/A 이유 명시. | §13A.10 lines 571–578 |

---

## 9. 잘못된 전제

1. **“D1 values are never materialized”** — M records 480과 generation 80은 D1에서 in-memory로 계산된다. materialize되지 않는 것은 signal delta values다. (§5 D1 line 177 vs assertions 5/7)
2. **“Q = 12 units, 9 trained updates” per seed** — 12/9는 3-seed 총계다. per-seed는 4/3이다. (§13A.1 line 431 vs §13A.10 lines 562–563)
3. **“15 docs × 5 donors” in D1 CE formula** — D1은 20 docs를 평가한다. 15는 R primary cohort다. (§13A.4 line 506 vs §5 D1 line 160)

---

## 10. 최종 판정

```text
최종 판정: NARROW

Init (Q1):        conditional — init audit는 강하나 P/Q schema가 seed 차원을 표현 못 함
D1 (Q2):          conditional — seal은 강하나 real_memory_ce_calls 산식이 틀림
STOP/MDE (Q3):    agree — 4-state 상호배타·전체포괄; MDE 산술 검증됨
Cohort (Q4):      agree — 15 common frozen, doc 3/3, n_donors=5, n_boot=10000
Compute (Q5):     conditional — 2/arm·900 updates·96 min 정합; D1 25 min fallback 부재
Scope (Q6):       agree — read-path negative test, ROUTE_STOP route-only, H3 제거

Must-fix (ranked): MF-1 (D1 CE count), MF-2 (P schema seed dim), MF-3 (Q per-seed count),
                   MF-4 (D1 materialization claim), MF-5 (D1 25 min fallback), MF-6 (R schema symmetry)

승인 조건: MF-1~MF-3 수정 + D0/D1/R 각각 별도 승인. MF-4~MF-6은 D0 이전 수정 권장.
```

**NARROW 이유**: 세 blocker(MF-1~MF-3)는 모두 §13A.4/§13A.10의 신규 v1.8 addenda에 있고, 설계 재작업 없이 schema/산식 수정으로 닫힌다. Q3/Q4/Q6는 승인 가능 수준이다. 따라서 STOP이 아니라 NARROW이며, MF-1~MF-3 수정 후 D0 승인을 권고한다.

---

## 11. 경계

```text
이 문서는 review이며 실행 승인이 아니다.
test 163 = sealed
P1 = unused
T5Gemma2 = D-108 STOP
B0-B/B1/B2/Stage C = 미승인
Phase 6 = negative 종료 불변
```