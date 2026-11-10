# C5 F0 v1.7 — Independent Review (DS1017)

- **Reviewed HEAD:** `779bf218e83a09f5bd1c18d23f9899595e43adbb`
- **Sync:** `git fetch origin`; `git pull --ff-only origin main` fast-forwarded `e5d69ab..779bf21` (the first attempt reported "Already up to date" at `e5d69ab`; a re-fetch fast-forwarded to `779bf21`). No conflict.
- **Basis:** new independent review, round 7/10. v1.6 conclusions are not inherited.
- **Read:** `reports/EXTERNAL_REVIEW_C5_F0_V1_7_2026-11-09.md`; `docs/plan_c5_f0_v1_7_2026-11-09.md`; `docs/plan_c5_f0_v1_6_2026-11-09.md`; `reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`; `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`; `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`; `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`; `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`; `runner/c5_pm_phase6.py`. Also checked `runner/c5_pm_stats.py`, `runner/c5_pm_registered.py`, `reports/provenance/C5_b0a/labels/labels.json`, `labels_audit.json`, `cause_analysis.json`, `d1/d1_report.json`, `registered/registered_report.json`, `docs/decisions.md`.
- **Constraints respected:** no training/eval, no test163/P1, no subagents, no repository edits except this file.

---

## 0. Mandatory verbatim: paired E01−E11 primary contrast (v1.7 §6.3)

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

Primary positive (v1.7 §6.3, line 232):

```text
mean_D > 0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0
```

---

## 1. Q1 — Q gate / 3 seeds / init manifest

- **판정: conditional**
- **근거:**
  - The initialization contract is materially stronger than v1.6. §4 (lines 96-125) fixes the seed order (`torch.manual_seed(seed)`, adapter, then `torch.manual_seed(seed ^ 0x5EED10A5)`, then LoRA), makes per-step reseeding structural, and lists assertions 1-9. The 12-entry golden table in §4 is arithmetically correct: I recomputed `(seed ^ ((0x9E3779B9*(step+1)) & 0xffffffff)) & 0xffffffff` for seeds 20261108/09/10/20261111 at steps 0/1/2 and every value matches the plan (`0x9f02514d/4c/4f/4e`, `0x3d5bdb86/87/84/85`, `0xdb9345df/de/dd/dc`). The parentheses are unambiguous.
  - v1.7 correctly removes the v1.6 "≥2 seeds remain" escape (§5 R, v1.6 line 184) and makes any Q seed failure `NOT_EVALUABLE` (§5 R, v1.7 lines 188-190; §13A.1 line 430). This closes the 2-seed continuation concern.
  - **Gap (approval-relevant):** `pre_r_seed_audit_pass[seed]` is required for each R seed (§13A.1 line 428; §5 R line 188) and `pre_r_init_audit_pass:true` is required before `r/` creation (§13 line 418; §13A.6 line 516), but neither predicate is defined. §13 lists `pre_r/pre_r_init_audit.json` (line 401) with no literal schema, and there is **no Q artifact path at all** in the §13 artifact manifest (lines 395-410). The Q gate therefore cannot be audited: an implementer can decide post hoc what "pass" means.
  - **Gap:** the init manifest hashes `common_ids_sha256`, `donor_map`, `base_state_sha256`, `cache_sha256`, `labels_sha256` (§4 lines 113-114; §6.1 lines 198-200), but it does **not** hash the ordered `train20` list used by `train20[step%20]` (§3 line 81). `common_ids_sha256` covers only the 15 val docs. A different train order would change training without being caught by the recorded hashes. Add ordered `train20_ids_sha256` and `val20_ids_sha256`, and specify whether `common_ids_sha256`/`donor_map` are canonicalized in preflight order or sorted order.
  - **Minor:** `post_step0_rng_state_sha256` is stated as CPU RNG state (§13A.2 line 444). Phase 6 recorded "GPU none" (prereg §11.1 line 1261), but F0's host/device is not stated. If any arm uses CUDA, CPU state does not prove dropout parity. State `device=cpu` explicitly.
- **다음 단계:**
  1. Add literal P/Q/pre-R schemas and a Q artifact path (e.g. `pre_r/q_seed_audit_{seed}.json`) with exact keys.
  2. Define `pre_r_init_audit_pass` (all 3 P seeds × 4 cells present; P hashes equal R hashes; KAT referenced) and `pre_r_seed_audit_pass[seed]` (Q RNG parity + group change + `wrong_donor_finite:true`).
  3. Add ordered `train20_ids_sha256`/`val20_ids_sha256` and canonicalization rules; state `device=cpu`.

---

## 2. Q2 — D1 predicates / seal / telemetry

- **판정: conditional**
- **근거:**
  - The D1 seal is now concrete and substantially closes DS-1/Luna. §13A.4 (lines 452-500) gives a literal key/type schema, forbids `per_doc`/`final`/`delta_*`/`signal`/`phase7`, defines `mechanics_pass` as a conjunction of `partial==false`, `error==null`, `checkpoint_absent==true`, all assertions, `phase7_records==0`, `wrong_donor_ce_calls==0`, `donor_map_loads==0`, and the five provenance/scope flags (line 499). §5 D1 adds checkpoint digest-then-delete, `checkpoint_absent`, no loading, and negative tests (§5 lines 158-176). `cells_ok`, `updates_total_ok`, `e00_steps_zero` are explicitly defined (line 498). This is stronger than "sealed": the signal values are never materialized in D1.
  - **Gap (approval-relevant):** §0.4 line 33 claims a "D1 real-memory CE exact count assertion", but §13A.4 line 488 only declares `real_memory_ce_calls: int` with no expected value, and `mechanics_pass` (line 499) does not include it. The claimed assertion is not implementable as written. Specify the expected count (e.g. per-cell step0 + final + update calls) and add `real_memory_ce_calls == expected` to `mechanics_pass`.
  - **Gap:** `provenance` (`code_commit`, `command`, `input_sha256`, `clean_tree`) is recorded (line 478) but not gated. A dirty-tree or uncommitted D1 run can still have `mechanics_pass:true`. Add `provenance_ok = clean_tree AND code_commit != null AND input_sha256 != null` to `mechanics_pass`; the same applies to D0 and R.
  - **Residual bypass:** §13A.8 (lines 523-527) states D1 does not call wrong-donor CE, and Q only checks wrong-donor CE finiteness/shape. A finite-but-wrong wrong-donor CE is first exercised numerically at R. The plan accepts this explicitly, which is reasonable, but it should be listed as a residual risk rather than left implicit; the "unit-test `donors_for`/crop on 1 doc" mitigation does not test the CE values.
  - D0 has no literal schema or named `d0_pass` predicate, although D0 is a `PROTOCOL_VALID` condition (§7 lines 273-283). D0 assertions 1-10 (§5 lines 134-143) are clear, but the artifact allowlist is not.
- **다음 단계:**
  1. Define `real_memory_ce_calls` expected value and add it to `mechanics_pass`.
  2. Add `provenance_ok` to D0/D1/R pass predicates.
  3. Add a D0 literal schema and a one-line `d0_pass` predicate.

---

## 3. Q3 — STOP / MDE / near-threshold / harm-benefit

- **판정: conditional**
- **근거:**
  - The four-state table (§7 lines 304-320) is mutually exclusive and exhaustive in the stated priority. `PASS_POSITIVE` requires `SIGNAL(E01,copy)` (§6.3 line 232; §6.4 lines 240-250), while `ALL_FAIL` requires `FAIL(E01,copy)`; they are disjoint. `EQUIVALENT` (`CI_D.lower >= -.05 AND CI_D.upper <= +.05`, line 290) and `PASS_POSITIVE` (`CI_D.lower > +.05`) are disjoint. `INDETERMINATE` is defined as the residual "not ALL_FAIL and not PASS", so the partition is complete. The `EQUIVALENT > harm > benefit` precedence (line 296) is coherent, and the explicit non-exclusivity of harm/benefit with PASS (line 317) is correct: every PASS has `CI_D.lower > .05 > 0`, hence `harm` is also true. That is a labeling convention, not a state conflict.
  - **Gap (approval-relevant):** `PROTOCOL_VALID` includes "R mechanics pass" (§7 line 278), but no R mechanics predicate or artifact schema is defined anywhere in v1.7. §5 R (lines 174-190) lists counts and caps but no `r_mechanics_pass` formula. This is a gate condition that an implementer must invent, exactly the discretionary-gate risk prior rounds flagged.
  - **Gap:** the near-threshold rule (line 313) is defined on `mean_D` and `CI_D` (`D=E01−E11`), but `ALL_FAIL` is defined on cell-level `SIGNAL(c,e)` at `.05`/`0` (§6.4 lines 240-250). The quantity that drives `ROUTE_STOP` is cell-level; the near-threshold diagnostic is paired-contrast. It therefore does not report whether the cell-level `.05`/`0` boundaries are near. Either define the diagnostic on the cell-level means/CIs that drive `ALL_FAIL`, or relabel it explicitly as a paired-contrast diagnostic (not a near-threshold `ROUTE_STOP` check).
  - The MDE provenance is now traceable. I verified from `labels.json` `L_COPY_SIGNAL.paired`: mean `-0.002639`, CI `[-0.040845, 0.034302]`, half-width `0.0375735`, `/1.96 = 0.0191702`; 50% MDE `.0376`, 80% MDE `.0537`. I also verified `cause_analysis.json` `P_minus_PA`: mean `3.065202`, per-doc SD `2.404764`, SE `0.620907`, 14/15 positive. These match §12 line 389.
  - **Minor:** `.104` ("gate mean") and `.0876` ("50% boundary") are not traceable to a committed artifact. `labels.json` `L_COPY_SIGNAL.seed_means` are `-0.133083`, `-0.104326`, `-0.103110`; `-0.1043` is a seed mean, not a gate mean. Either define these two numbers or remove them; they are not needed for the F0 decision.
- **다음 단계:**
  1. Define `r_mechanics_pass` (updates, counts, finite, no NaN/duplicate, artifact presence) and add it to §7.
  2. Align the near-threshold diagnostic with the cell-level `SIGNAL` boundaries, or relabel it.
  3. Define or delete `.104`/`.0876`; keep `.037573`/`.019170` as the verified F−L planning proxy.

---

## 4. Q4 — Cohort / cell CI / donor conditional

- **판정: agree**
- **근거:**
  - §6.1 (lines 194-210) freezes the estimand on the 15 length-eligible `common_ids` plus the fixed donor graph, forbids generalization to the 20-doc val population, records the donor-map sha256, requires exactly 5 donors per doc, requires donor-set equality across E00/E10/E01/E11, and requires 3/3 seed completeness. This directly addresses the v1.0 DS-2 length-selection concern.
  - §6.3 (lines 220-236) overrides the frozen `N_BOOT=1000` explicitly with `n_boot=10000, seed=20261109` and asserts the realized values. I verified `bootstrap_paired_v2` accepts `n_boot` and `seed` (`runner/c5_pm_stats.py` lines 29-31) and that `N_BOOT=1000` is only a default; the override is implementable, not a silent revert. `l_predicate` is explicitly forbidden.
  - §6.1/6.6 correctly convert `eval_arm_d1`'s silent drop to `NOT_EVALUABLE`: the code `continue`s when `real_copy` is empty (`runner/c5_pm_phase6.py` line 465), and the plan says a missing doc is `NOT_EVALUABLE`, never a smaller cohort (§6.1 line 205; §6.6 lines 264-269). This is the right direction.
  - The cell-level CI construction (15 docs × 5 donors, seed mean over 20261108/09/10, `bootstrap_paired_v2(n_boot=10000, seed=20261109, linear)`, 2.5th percentile) is coherent, and `CI_D` is explicitly doc-level only (line 235). The 2/3 seed-sign gate is a replication descriptor, not a second primary.
- **다음 단계:**
  1. Specify the canonicalization of `common_ids_sha256` and `donor_map` (preflight order vs sorted) so the frozen binding is unambiguous.
  2. Report the leave-one-donor-out range as planned (§6.1 line 201) alongside the primary; no change to the primary decision rule.

---

## 5. Q5 — Compute: 16-core / 1-thread / estimate provenance

- **판정: disagree (blocker)**
- **근거:**
  - The stage arithmetic is correct for R and D1: R `900 = 3 trained cells × 100 × 3 seeds`; D1 `3 = 3 trained cells × 1`; P `0`. **But Q is wrong:** §12 table (line 376) says Q has **12 trained updates**, and §13A.1 line 427 says "1-update per cell per R seed (3 seeds × 4 cells = 12 units)". E00 is explicitly 0-update (§2 line 64; §5 D0 line 133; §5 D1 line 151). Q therefore has **9** trained updates (3 seeds × 3 trained cells), not 12. Twelve is the unit count, not the update count.
  - **The registered anchor thread count is misstated.** §12 line 381 says "D1 anchor used 3 threads/arm" (correct for D1: `docs/decisions.md` D-156 line 216 says "4 arms 병렬(3 threads each), wall 1,180.6s"), but line 385 says "Phase 6 registered 4,939.884s at **3 threads/arm**." The committed registered record says the opposite: D-157 line 218 says "3 wave(4 arms each, **2 threads**) wall 4,939.9s". The committed driver defaults to `--threads 2` (`runner/c5_pm_registered.py` line 30), and `labels_audit.json` commands use `--threads 2` (lines 10-11). Prereg §11.1 line 1260 separately says "threads 6". v1.7 has conflated D1's 3 threads/arm with registered's 2 threads/arm. The 96-min cap is therefore anchored to a thread configuration that is not the one v1.7 states, and no committed artifact records `threads_per_arm`/`nproc`/`parallel_wall_s`/`contention_ratio` for the Phase 6 registered run (the `registered_report.json` has none of these fields).
  - **16 cores with 1 thread/arm is internally inconsistent.** §0 line 23 and §5 D1 line 153 mandate "16 cores, 1 thread/arm, 4 arms = 4 worker threads"; §12 line 388 hard-aborts if `nproc < 16`. Four arms × one thread = 4 logical threads, so a 4-vCPU host would satisfy the actual thread demand. If 16 cores is needed for data loading/eval/headroom, say so and quantify it; otherwise the `nproc>=16` floor is unjustified and the "4-vCPU host fails" rule is arbitrary. This matters because the plan uses the 16-core floor as a precondition for the cap claim.
  - **The 25-min D1 cap is not reconciled with 1 thread/arm.** The D1 anchor `1,180.6s` is 19.7 min at 3 threads/arm (D-156), and `wall_estimate_s:1180.577` is the `d1_report.json` field. At 1 thread/arm, D1 has no provisional-cap clause (unlike D0, which says "provisional; final cap set from measured D0 timing", §5 line 145). If 1-thread D1 exceeds 25 min, the stage aborts before any R measurement. Make D1 provisional/measured or state the scaling assumption.
  - **Positive:** §11 line 366 and §13A.7 line 521 correctly require `runner/c5_pm_f0*.py` to be committed at a recorded SHA with a clean tree before D0, and §12 line 381 says the final cap requires measured `parallel_wall_s`. The provenance *architecture* is right; the *numbers* and the host floor are not.
  - **Provenance of the two anchors:** `d1_report.json` has `"wall_estimate_s": 1180.577`, `"cap_seconds": 1200`, `"parallel_arms": true`; `registered_report.json` has `"wall_estimate_s": 4939.884`, `"cap_seconds": 7200`, `"wave_max_elapsed_s": {20261108:1661.098, 20261109:1751.427, 20261110:1527.358}`. The 4,939.884 is the sum of measured wave maxima, so calling it an estimate is fair. The thread-count attribution is not.
- **다음 단계:**
  1. Correct §12 to state registered = 2 threads/arm (D-157) and D1 = 3 threads/arm (D-156); state the 1-thread/arm scaling assumption and make D1 cap provisional from measured D1 `parallel_wall_s`.
  2. Justify `nproc>=16` under 1 thread/arm or reduce the floor to the actual logical-thread demand (and say what the extra cores are for).
  3. Correct Q to 9 trained updates (12 units, E00 0 updates).

---

## 6. Q6 — Scope / route-only

- **판정: agree**
- **근거:**
  - §10 (lines 349-356) removes H3 completely: no H3 arm, trigger, rank, identity, null, or donor-discrimination endpoint; H3 requires a separate prereg and approval; F0 results do not launch H3. This is a clean boundary and avoids the prior "H3 rescue" problem.
  - §14 (lines 535-548) is explicit: ROUTE_STOP stops only the route as configured (EG2 layer19 raw + this LoRA/adapter configuration), does not stop the EG2 track, does not rescue B0-B, and does not launch H3; E00/E10/E01-vs-E00 are descriptive; the earlier MF-4 zero/permuted null and 1-seed signal gate are intentionally out of scope and F0 cannot claim they were replaced. The association-only claim is correctly limited to adapter-as-configured (adapter params + adapter LR + adapter-conditioned forward graph, §4 line 126), not an architecture-only bottleneck.
  - The E01 vs E11 primary is the right single contrast for the stated question because LoRA initialization is matched (§4 assertions 1-5). It does not isolate adapter capacity/LR from architecture, and the plan says so.
  - **Limitation to keep visible:** dropping the zero/permuted null means a positive/negative D cannot be attributed to donor-specific content versus a generic adapter effect beyond what the donor-crop contrast itself controls. §14 already declares this; it should stay in the report's limitations, not be softened.
- **다음 단계:**
  1. Keep the §14 limitations verbatim in the F0 report.
  2. Do not add an H3 trigger or a post-hoc null to F0; any such addition requires a new prereg.

---

## 7. Final

```text
최종 판정: NARROW
```

**Why NARROW, not STOP:** the scientific design is coherent and most prior must-fix items are closed (Q 3-seed gate, init contract, D1 literal seal, `cells_ok`/`updates_total_ok`/`e00_steps_zero`, `common_ids_sha256`, harm/benefit non-exclusivity, H3 removal). **Why not CONTINUE:** two approval blockers remain: (1) the compute provenance misstates the registered thread configuration and the 16-core/1-thread floor is internally inconsistent; (2) the pre-R gate predicates (`pre_r_init_audit_pass`, `pre_r_seed_audit_pass[seed]`, `R mechanics pass`) and the Q artifact path/schema are undefined, so the gate is not auditable. These are fixable in a v1.8 text/schema revision without changing the scientific design.

```text
Init:        conditional — strong contract; missing P/Q/pre-R predicates, Q artifact path, ordered train/val ID hashes, device declaration.
D1:          conditional — strong seal; `real_memory_ce_calls` expected value missing; provenance not in `mechanics_pass`; D0 schema missing.
STOP/MDE:    conditional — partition is sound; `R mechanics pass` undefined; near-threshold uses paired CI while ALL_FAIL is cell-level; `.104`/`.0876` untraceable.
Cohort:      agree — 15 frozen docs + fixed donor graph + n_boot=10000 override + 3/3 seed completeness are sufficient and correctly conditional.
Compute:     disagree — registered anchor thread count wrong (D-157 says 2/arm, v1.7 says 3/arm); 16-core floor unjustified for 4 logical threads; Q update count 12 should be 9; D1 cap not reconciled with 1 thread/arm.
Scope:       agree — H3 removed; route-only/association-only/descriptive boundaries are explicit.
```

### Must-fix (ranked)

1. **Fix compute provenance and caps (Q5, blocker).** §12 line 385 says registered `4,939.884s` at 3 threads/arm; committed D-157 says 2 threads/arm, the registered driver defaults to `--threads 2`, and prereg §11.1 says "threads 6." Correct the record, state the 1-thread/arm scaling assumption, and make the 25-min D1 cap provisional from measured D1 `parallel_wall_s` (as D0 already is).
2. **Define the pre-R and R gate predicates and the Q artifact (Q1/Q3, blocker).** Add literal schemas for `pre_r/pre_r_init_audit.json` and a Q artifact; define `pre_r_init_audit_pass` (3 P seeds × 4 cells present; P hashes equal R hashes; KAT referenced), `pre_r_seed_audit_pass[seed]`, and `r_mechanics_pass`. Without these, `PROTOCOL_VALID` is discretionary.
3. **Make D1's claimed exact-count assertion real (Q2).** Specify the expected `real_memory_ce_calls` and add it to `mechanics_pass`; add `provenance_ok` (`clean_tree`, `code_commit`, `input_sha256`) to D0/D1/R pass predicates.
4. **Align the near-threshold diagnostic (Q3).** `ALL_FAIL` is cell-level at `.05`/`0`; the current near-threshold uses paired `mean_D`/`CI_D`. Define it on the cell-level statistics that drive `ROUTE_STOP`, or relabel it as a paired-contrast diagnostic.
5. **Add ordered ID hashes and canonicalization (Q1).** Record `train20_ids_sha256` and `val20_ids_sha256`; specify whether `common_ids_sha256` and `donor_map` are preflight-order or sorted; state `device=cpu` for `post_step0_rng_state_sha256`.
6. **Correct the Q update count (Q5).** §12 line 376 and §13A.1 line 427 say 12 trained updates; E00 is 0-update, so Q is 9 trained updates and 12 units.
7. **Resolve `.104`/`.0876` (Q3).** Define them from a committed artifact or remove them; `.037573`/`.019170` are verified.
8. **Record the wrong-donor CE residual risk (Q2).** D1 makes 0 wrong-donor CE calls; Q checks only finiteness/shape; the first numerical exercise is R. State this in §13A.8/§14 rather than leaving it implicit.

### 잘못된 전제

- "Phase 6 registered `4,939.884s` at 3 threads/arm" is false. D-157 (`docs/decisions.md` line 218) says the registered run used 2 threads/arm; `runner/c5_pm_registered.py` defaults to `--threads 2`; `labels_audit.json` commands use `--threads 2`. Only D1 used 3 threads/arm (D-156).
- "Q = 12 trained updates" is false. E00 is 0-update (§2, §5 D0/D1), so Q = 3 seeds × 3 trained cells = 9 updates; 12 is the unit count.
- "16 cores, 1 thread/arm, 4 arms" implies 12 idle cores. The host floor is not justified by 4 logical threads; either state the headroom purpose or reduce `nproc`.
- "D1 real-memory CE exact count assertion" is not a predicate as written: §13A.4 line 488 declares `int` with no expected value, and `mechanics_pass` line 499 does not include it.
- "`pre_r_init_audit_pass`" / "`R mechanics pass`" are names, not defined predicates. §7 line 278 and §13 lines 418/516 reference them without a schema or formula.