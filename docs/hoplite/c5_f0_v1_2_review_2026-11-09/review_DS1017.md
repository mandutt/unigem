# C5 F0 v1.2 — Independent Review (Round 2, DS1017)

- Reviewer model: `deepseek-v4.1-flash-1017` (high)
- Review date: 2026-11-10 (UTC)
- Target: `docs/plan_c5_f0_v1_2_2026-11-09.md`
- Status of target: DRAFT v1.2 — not approved, not executed
- Independence: new review; v1.1 threads archived and their conclusions are not inherited.
- Execution boundary honored: no training/eval, no test 163, no P1, no subagents, no repository
  modification other than this file.

## 0. Workspace synchronization and reviewed HEAD

```text
git fetch origin            -> exit 0
git pull --ff-only origin main -> "Already up to date."
HEAD                        = f2525253efeb7de49d35a355b25c22b481594178
origin/main                 = f2525253efeb7de49d35a355b25c22b481594178
branch                      = hoplite/syrakousai-ea8e586d
HEAD subject                = "docs: add C5 F0 v1.2 review request" (2026-11-10 10:00:05 +0900)
```

**Reviewed HEAD: `f2525253efeb7de49d35a355b25c22b481594178`.** Working tree clean at review start.
All line citations below are against this commit.

## 1. Verbatim paired E01−E11 definition (mandatory)

From `docs/plan_c5_f0_v1_2_2026-11-09.md` §6.3, lines 220–223, reproduced verbatim:

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
```

The per-cell quantity that this pairs, from §6.2 line 212, verbatim:

```text
delta_c(s,d) = mean_donor( CE_wrong_donor - CE_real )
```

Every quantitative criticism in Q3/Q4 below is about whether the variance used to power
`D(d)` actually belongs to this adapter-presence contrast.

## 2. Q1 — Initialization audit

**Verdict: conditional (direction correct; two asserts missing).**

What v1.2 fixes and what I verified:

1. The `build_arm_f0` seed schedule (§4 lines 90–99) closes a real Phase 6 confound. In the frozen
   Phase 6 builder, `torch.manual_seed(seed)` is called once and the adapter is constructed
   **before** LoRA attachment (`runner/c5_pm_phase6.py:147–153`), so adapter presence shifts the
   LoRA RNG stream. The adapter-independent `seed ^ 0x5EED10A5` reset before
   `attach_decoder_lora_mt5` is the correct repair, and the separately asserted
   `lora_names`/`lora_A`/`lora_B`/`adapter` hashes cover the mechanisms that matter.
2. The **step_seed golden table is arithmetically correct**. I independently evaluated
   `(seed ^ ((0x9E3779B9*(step+1)) & 0xffffffff)) & 0xffffffff` for all 12 vectors in §4 line 117:

   ```text
   20261108: 0x9f02514d 0x3d5bdb86 0xdb9345df
   20261109: 0x9f02514c 0x3d5bdb87 0xdb9345de
   20261110: 0x9f02514f 0x3d5bdb84 0xdb9345dd
   20261111: 0x9f02514e 0x3d5bdb85 0xdb9345dc
   ```

   All 12 match the plan exactly. The fixed parentheses remove the precedence ambiguity; this is
   now a testable unit vector rather than prose.
3. Per-step reseed is the right structural move. E01 and E11 have identical LoRA module sets and
   the adapter contains no RNG-consuming layer, so identical forward draw counts are a real
   consequence, not an assumption.

Gaps that must be closed before D0 approval:

- **Non-reuse is asserted by the wrong instrument.** §4 line 122 replaces “F0 E11 ≠ Phase 6 L”
  with an `open`/`torch.load` path audit that “records zero Phase 6 paths.” That proves
  non-*access*, not distinct *initialization*. Because the builder and seed schedule differ, the
  stronger and cheaply testable assertion is available: record the Phase 6 L init hash (already
  captured in the frozen `s2026*_lora.json` / checkpoint-hash artifacts) and assert F0 E11 init
  hash ≠ Phase 6 L init hash, and final hash ≠ final hash. Keep the I/O audit as an additional
  guard, not the primary evidence.
- **Assertion 9 is undefined for E00.** “`post_step0_weight_change`: at least one LoRA/adapter
  parameter changes” (§4 line 115) has no parameter to change in E00 (adapter absent, LoRA
  absent, 0 updates). State E00 as `N/A` explicitly; otherwise a literal implementation fails the
  D0 gate on a correct cell.
- `post_step0_rng_state_sha256` equality (§4 line 111) is near-tautological given reseeding before
  every forward. Keep it as a sanity check, but do not present it as the evidence that dropout
  paths match; the module-set equality plus zero RNG-consuming adapter ops is the actual argument.

## 3. Q2 — D1 seal

**Verdict: conditional (large improvement; instrumentation still prose-only).**

v1.2 correctly diagnoses the Phase 6 leak. The committed `run_d1`
(`runner/c5_pm_phase6.py:778–883`) does precisely what F0 forbids: it runs `eval_arm_d1` twice
(lines 804, 806), which materializes `per_doc` `delta_shuffled_copy/full`
(lines 466–476), writes `d1_report.json` (`D1_OUT`, line 882), `m_records.json` (line 858),
`phase7_records/{arm}/20261111.json` (lines 813–821), and saves checkpoints (line 823).
The v1.2 contract — new `runner/c5_pm_f0_mechanics.py`, no `eval_arm_d1`, no wrong-donor CE,
`f0_d1_mechanics.json` only, digest-then-delete checkpoints, crash-path delete — is the right
repair and is materially stronger than a post-hoc seal.

Remaining bypass paths, in order of importance:

1. **“No wrong-donor CE” is asserted only in the change summary (§0 item 4) and code plan
   (§11 line 352), not in the Stage D1 assertion list (§5 lines 153–164).** Assertion 8 there
   says only “all CE finite; no NaN,” which is ambiguous about *which* CE. Make it normative:
   D1 computes real-memory CE only, the donor map is never loaded, and a call counter for the
   wrong-donor path must be exactly 0. That converts “we do not write it” into “we never compute
   it,” which is the claim §5 line 174 actually makes.
2. **The allowlist/denylist are not given as literal key sets.** §5 line 168 says “exact-key
   allowlist” but never enumerates it. Enumerate the exact `f0_d1_mechanics.json` keys and assert
   *both* set equality (writer side) and a denylist regex `per_doc|final|delta_` (reader side).
3. **The crash artifact is undefined.** §0 item 4 mentions “crash path delete+absent,” but §5
   never names the partial artifact. Either forbid it outright or define `f0_d1_partial.json`
   with the same exact-key contract; `d1_partial.json` is what the Phase 6 runner writes
   (line 851), so an implementer copying that pattern would silently reintroduce a signal carrier.
4. **Checkpoint digest is still a residual oracle only if retained.** The plan is correct that
   digest-then-delete + load-forbidden is stronger than sealing; keep the explicit
   `checkpoint_absent == true` and a process-level “no `torch.load` of `checkpoints/`” assert.
5. `f0_d1_mechanics.json` “counts only” is compatible with assertions 4–7 (doc counts, 120 M
   records/cell, 80 generations). No conflict. §13 line 386 should nevertheless state that the
   `m_records_*`/`checkpoints/*` entries in §13 are Stage-R artifacts, not D1 artifacts.

## 4. Q3 — STOP taxonomy and MDE

**Verdict: agree on the taxonomy; disagree on the MDE/power/equivalence section.**

Taxonomy audit (§7 lines 265–312) — passes:

- States are evaluated in a fixed order (1 `NOT_EVALUABLE`, 2 `PASS_POSITIVE`,
  3 `ROUTE_STOP`, 4 `INDETERMINATE`), so they are mutually exclusive by construction and
  exhaustive after the ordered guards.
- `PASS_POSITIVE` requires `CI_D.lower > +.05` (§6.3 line 226); `EQUIVALENT` requires
  `CI_D.upper <= +.05` (§7 line 283). The two cannot co-occur. `PASS` and `ALL_FAIL` also cannot
  co-occur because `ALL_FAIL` requires `FAIL(E01,copy)` while `PASS` requires `SIGNAL(E01,copy)`.
- `ALL_FAIL` is correctly restricted to E01/E11 × copy/full (line 303); E00/E10 do not decide a
  route stop.
- The reason precedence `EQUIVALENT > harm > benefit` (line 291) matches the `ROUTE_STOP` reason
  ordering (line 300). The default `no_signal_uncertain` covers `ALL_FAIL` with a CI straddling 0.
- One wording nit: `adapter_harm` (line 306) fires on `ALL_FAIL + CI_D.lower>0`, i.e. adapter-free
  E01 is *less bad* than E11 while both fail signal. “Harm” is directional shorthand for
  “adapter-associated reduction,” not harm to the model; say so in the table footnote.

**MDE section is the primary approval blocker.** The numbers are traceable but are applied to the
wrong contrast:

- `.037573` and `.019170` are not an independently estimated SE. They come from
  `reports/provenance/C5_b0a/labels/labels.json`, field `L_COPY_SIGNAL.paired`:
  `ci_lower = -0.040844837294684515`, `ci_upper = 0.034302208052741166`. Mean `= -0.0032713`,
  half-width `= 0.03757352`, and `SE = half-width / 1.96 = 0.01917016`. §12 line 375 presents
  `.019170` as “paired SE” without stating that it is `half-width/1.96` from that artifact.
- That artifact is the **Phase 6 F−L contrast**, which varies LoRA with the adapter held present.
  The F0 primary `D(d)` varies the **adapter** with LoRA held present. These are not the same
  contrast, and Phase 6 contains a direct measurement showing the variance differs by an order of
  magnitude: the P−PA adapter contrast on the same 15 common docs has mean `+3.0652`, `14/15`
  positive, SE `0.6209`, i.e. per-doc SD `2.405`. The F−L per-doc SD I recomputed from the frozen
  registered units is `0.0775` (copy) / `0.0760` (full). Ratio ≈ **31×**.
- Consequence: if E01−E11 dispersion resembles the only measured adapter contrast, `CI_D`
  half-width is ≈`1.2`, not `.0376`. Then `EQUIVALENT` (CI entirely inside ±.05) is unreachable,
  and `PASS` needs a mean above ≈`1.27`. The plan removed the `0.117` half-width claim but replaced
  it with a proxy from a different contrast, so the reachability problem is not actually closed.
- Even accepting the proxy, the arithmetic is a z-normal approximation, not the percentile
  bootstrap the prereg uses: `80% power mean = .05 + (1.95996+0.84162)·.019170 = .10371` and
  `gate boundary = .05 + 1.95996·.019170 = .08757`. These match `.104`/`.0876`, but calling
  `.0876` an “observed boundary” is misleading — it is the analytic 50%-power point where
  `CI_D.lower = .05`. It is not an observed quantity.
- The `.104` figure is the power of the `CI_D.lower>.05` gate **alone**. `PASS_POSITIVE` also
  requires `SIGNAL(E01,copy)` and `2/3 seeds D_s>0` (line 226), so conjoint power is strictly
  lower. Label `.104` as gate-only power.

Required repair: state the proxy contrast and its source artifact explicitly; add a
pre-registered upper-bound projection using the P−PA adapter dispersion; make the realized
`CI_D` half-width govern `EQUIVALENT`; delete or explicitly conditionalize the `±.0124`
equivalence range (§6.5 line 254) and the “more likely” branch claim (see Q3/wrong premises).
None of this changes the decision rule’s computability, but without it the prereg’s power and
equivalence statements are not supported.

## 5. Q4 — Cohort / CI

**Verdict: conditional (estimand declaration is good; two assertions need sharpening).**

Verified against frozen artifacts:

- `reports/provenance/C5_b0a/m_cohort_preflight.json` has `train20_ids = 20`, `val20_ids = 20`,
  `common_ids = 15`, and `common_ids ⊂ val20_ids`. So §6.1 line 196 (“15 common = frozen
  preflight `common_ids`; 5 of 20 excluded at K=753”) is factually correct.
- The 3-seed means I recomputed from `registered/units/{F,L}_{seed}.json` on those 15 docs are
  F copy `-0.110867`, L copy `-0.113506`, matching the `-0.111/-0.1135` cited in §0 line 25 and
  the cause report. The cohort arithmetic in §6.5 is therefore correctly quoted.
- `donors_for(ids, cache, count=5)` (`runner/c5_mt5_lora_b0.py:318–326`) is deterministic,
  length-nearest, excludes self (`x != rid`), and is cell-independent. So “donor sets identical
  for E00/E10/E01/E11” (§6.1 line 201) is true by construction for every cell that uses the EG2
  cache — which is all four F0 cells.

Gaps:

- **The 5-donor assertion is on the wrong count.** `eval_arm_d1` records
  `n_donors = len(real_copy)` and silently continues when `real_copy` is empty
  (`runner/c5_pm_phase6.py:459–465`). Copy CE returns `None` when fewer than 5 copy tokens are
  available (`copy_ce`, `runner/c5_mt5_lora_b0.py:311–315`). So a doc can be averaged over fewer
  than 5 donors even though `donors_for` returned 5 candidates. §6.1 line 201 must assert the
  **evaluated** donor count equals 5 for copy *and* full, per doc × cell × seed, and a doc below 5
  must be `NOT_EVALUABLE`, never averaged over a smaller donor set. §6.6 currently forbids 15→14
  doc substitution but says nothing about donor-count substitution.
- `n_boot=10000` is a documented override of frozen `N_BOOT=1000`
  (`runner/c5_pm_stats.py:15`, default argument at line 31; prereg §10.1 line 1172). The override
  is legitimate and does not change the estimand, but it is a change to a frozen statistical
  constant and must appear in the F0 freeze manifest, not only in §6.3 prose. Also assert the
  returned `n_boot` field equals 10000, since the function silently defaults to 1000.
- `bootstrap_paired_v2` uses a fresh `numpy.random.default_rng(20261109)` per call and linear
  percentiles (`runner/c5_pm_stats.py:55–71`), matching §6.3’s seed and the frozen semantics.

## 6. Q5 — Compute

**Verdict: conditional (cap is plausible; two accounting defects).**

Verified:

- D-156 (`docs/decisions.md:216`) is **4 arms parallel at 3 threads each**, 1 update/arm,
  wall `1,180.6s / 1,200s`, `cap_ok:true`. That is the same 3-threads/arm configuration F0
  proposes (§12 line 366), so the D1 `≤25 min` cap has ≈27% headroom over 19.7 min. F0’s D1 also
  does strictly less than Phase 6 D1: M `480` vs `560`, phase7 `0` vs `2,400`. Credible.
- `900 updates` is consistent: E00 `0`, E10/E01/E11 `100` each, ×3 seeds (§5 line 182). M
  `1,440` = 15×8×4×3 ✓, phase7 `7,200` = 600×12 ✓, generation `240` = 20×12 ✓ (line 183).
- The hard abort `nproc < 12 or T_proj_R > 96 min` (line 374) plus “no cap increase without
  re-review” (line 372) is the right failure mode.

Defects:

- **The `T_proj_R` term list has 8 terms; Phase 6 §11.5 has 9.** F0 line 370:
  `setup + 3×(step0 + 100×step + m_build + m_ce + phase7 + primary + gen + overhead)`. Phase 6
  §11.5 lines 1333–1343 separately includes `t_step0_eval_20x5` **and**
  `t_step100_eval_20x5` **and** `t_primary_replay`. F0’s `primary` is not defined. If `primary`
  means the final 20×5 eval only, the primary replay is missing; if it means both, the eval is
  missing. Under-projecting one 20-doc × 5-donor pass per arm-seed is material at a 96-min cap.
  Give the term-by-term 1:1 map, or explicitly merge and say which two Phase 6 terms are merged.
- **“Setup once, not 3×” is not established.** §12 line 371 says `setup` is paid once and seed
  waves are sequential. But each registered unit is a fresh process that calls
  `load_frozen_inputs()` and `build_arm()` (`runner/c5_pm_phase6.py:890–902`, `142–146`), so
  model/cache setup is paid per arm and per seed, not once. Either define `setup_s` as
  per-process and use `3 × setup` for three waves, or state that one long-lived orchestrator
  amortizes it and prove that in the orchestrator commit. As written the projection can
  understate wall time by two setup passes.
- `setup_s` sits outside the `3 ×` in the formula, but `step0/step/...` sit inside. That is
  correct only if the setup is genuinely once; see above.

## 7. Q6 — Scope

**Verdict: conditional (H3 removal is right; the “lost controls” wording is wrong).**

- §10 removes H3 completely (no arm, trigger, rank, identity, null, or donor-discrimination
  endpoint) and requires a separate prereg. That is the correct boundary and prevents negative F0
  results from being rescued. §14 line 412 also correctly limits `ROUTE_STOP` to “route as
  configured” and refuses to stop the EG2 track or launch H3.
- The descriptive/no-inference boundary (§14 line 413) and the association-only claim
  (line 411) are honest about the `adapter-as-configured` confound (adapter params + adapter LR +
  adapter-conditioned graph). This is the right retreat from “bottleneck.”
- **Wording defect:** §14 line 414 lists “the earlier MF-4 zero/permuted null” as out of scope.
  The permuted (wrong-donor) null is not out of scope — it *is* the primary endpoint:
  `delta = CE_wrong_donor − CE_real` (§6.2 line 212). What is absent is a **zero/null-memory**
  control. Rewrite as: “wrong-donor permutation is present and is the endpoint; a zero-memory null
  is absent, so a positive E01 cannot separate content use from memory-presence.” Otherwise the
  prereg misdescribes its own design.

## 8. Final verdict

**NARROW.**

The design is executable, falsifiable, and substantially repaired relative to v1.1: the
adapter-independent LoRA seed and per-step reseed close a real Phase 6 init confound; the golden
step_seed table is exactly correct; the D1 contract closes the Phase 6 `eval_arm_d1` /
`phase7` / `d1_report.json` leak; the 15-doc estimand is frozen to preflight `common_ids`; the
4-state taxonomy is mutually exclusive and exhaustive; and the compute cap rests on a
3-threads/arm measurement (D-156). I would not STOP the program on this document.

I do not approve it yet. The MDE/equivalence section applies the variance of a LoRA contrast
(F−L, per-doc SD `0.0775`) to an adapter contrast (E01−E11), while the only measured adapter
contrast in Phase 6 (P−PA) has per-doc SD `2.405`. That makes both `EQUIVALENT` reachability and
the `.104` power claim unsupported, and the `ALL_FAIL more likely` branch claim contradicts the
plan’s own motivating evidence. Those are preregistration-integrity blockers, not cosmetic.

### Must-fix (ranked)

1. **MDE/equivalence re-derivation (blocker).** §12 line 375 and §6.5 line 254. State that
   `.019170 = .037573/1.96` from `labels.json` `L_COPY_SIGNAL.paired` and that this is the
   **F−L LoRA** contrast. Add the P−PA adapter-dispersion upper bound
   (mean `+3.0652`, SE `0.6209`, 14/15 positive, per-doc SD `2.405`). Make realized `CI_D`
   govern `EQUIVALENT`; delete or conditionalize `±.0124`; label `.104` as gate-only power and
   `.0876` as the analytic 50%-power boundary, not an observed value.
2. **§6.5/§0 expected-branch claim (blocker).** “ALL_FAIL→ROUTE_STOP is the more likely branch
   given Phase 6 F/L −.111/−.1135” (line 254; §0 line 25) is a non-sequitur: F and L both contain
   the adapter, so they cannot inform E01, which is adapter-free. The plan’s own P−PA result
   (`+3.065`, 14/15) predicts the opposite branch. Replace with “undetermined; PASS and
   ROUTE_STOP are both live.”
3. **T_proj completeness (required before R approval).** §12 line 370: give the 1:1 map to the
   nine Phase 6 §11.5 terms, including the separate 20×5 step-100 eval; and fix the setup
   accounting (per-process/wave vs once) or prove amortization in the orchestrator commit.
4. **Init non-reuse assert (required before D0 approval).** §4 line 122: add an explicit
   inequality between F0 E11 init/final hashes and the frozen Phase 6 L hash; keep the I/O path
   audit as a secondary guard. Also mark assertion 9 `N/A` for E00.
5. **D1 seal instrumentation (required before D1 approval).** §5 lines 153–164: enumerate the
   literal `f0_d1_mechanics.json` key set; define the partial/crash artifact; assert zero
   wrong-donor CE calls and zero donor-map loads; say “real-memory CE only” in the assertion list,
   not only in §0/§11.
6. **Donor-count assertion (required before R approval).** §6.1 line 201: assert evaluated
   `n_donors == 5` for copy and full per doc × cell × seed; `<5` evaluable ⇒ `NOT_EVALUABLE`.
   Record `n_boot=10000` in the F0 freeze manifest and assert the returned `n_boot`.
7. **Scope wording (required before approval).** §14 line 414: the wrong-donor permutation is the
   primary endpoint, not a lost control; only the zero-memory null is absent.

### 잘못된 전제 (wrong premises)

1. “F/L −.111/−.1135 ⇒ E01 likely fails” — F/L both include the adapter; they do not estimate E01.
2. “paired SE `.019170`” — it is `half-width/1.96` from the F−L LoRA contrast, not an estimated
   SE for E01−E11.
3. “EQUIVALENT mean range ≈±.0124” — conditional on a `.0376` half-width that is not established
   for the adapter contrast; under P−PA-like dispersion `EQUIVALENT` is unreachable.
4. “setup once, not 3×” — every unit process reloads inputs and rebuilds the arm; per-wave setup
   is not accounted.
5. “zero Phase 6 path opens ⇒ F0 E11 ≠ Phase 6 L” — proves non-access, not distinct init.
6. “MF-4 zero/permuted null out of scope” — the permuted (wrong-donor) null is the endpoint.

## 9. Verification notes

- HEAD/sync: `git fetch origin` exit 0; `git pull --ff-only origin main` “Already up to date”;
  HEAD = origin/main = `f2525253efeb7de49d35a355b25c22b481594178`.
- Step_seed vectors: independently recomputed for all 12 values; exact match.
- Phase 6 cohort: `m_cohort_preflight.json` → train 20 / val 20 / common 15, common ⊂ val.
- Phase 6 cell values: recomputed from `registered/units/{F,L,P,PA}_{20261108,09,10}.json`
  `final.per_doc` on the 15 common docs with 3-seed averaging:
  F copy `-0.110867`, L copy `-0.113506`, P copy `+3.076413`, PA copy `+0.011211`,
  P−PA `+3.065202` (14/15 positive, SE `0.6209`).
- MDE inputs: `labels.json` `L_COPY_SIGNAL.paired` = `[-0.040844837294684515,
  0.034302208052741166]`; mean `-0.0032713`, half-width `0.03757352`, implied SE `0.01917016`;
  `80% power mean .10371`, gate boundary `.08757`.
- Bootstrap/labels API: `runner/c5_pm_stats.py:15` `N_BOOT=1000`, `:29–33` signature
  `bootstrap_paired_v2(values, n_boot=N_BOOT, seed=BOOTSTRAP_SEED)`; `seed=20261109`.
- Compute provenance: `docs/decisions.md:216` D-156 = 4 arms parallel, 3 threads each,
  `1,180.6s / 1,200s`.
- No training, evaluation, test 163, or P1 access was performed. Only this file was written.