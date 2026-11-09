# Independent external review — C5 B0-A P/M prereg v0.2.1-r1

**Reviewer: Sol 6.1 medium reviewer.** This is a new, independent r1 review, not a continuation or reuse of the earlier Sol review.

**Final recommendation: NARROW. Do not freeze r1 as written.** The factored architecture, data-only prefix control, PA acquisition naming, and separate debug budgets are real improvements. A small text-only r2 is still needed before contract freeze, implementation authorization, and D0. This is not a bridge STOP and does not approve Phase 6 or B0-B.

## 1. Basis, synchronization, and limits

- Review date: 2026-11-09.
- Repository: `mandutt/unigem`; requested base: `main`, current `origin/main`.
- Executed `git fetch origin`, followed by `git pull --ff-only origin main`. Both succeeded; pull reported “Already up to date.”
- Resulting HEAD and origin/main: **`4920953bca28ab502372780e67e3f87f41082ec2`**. The request document's historical `0fce2e2` is not the reviewed workspace HEAD.
- Initial working tree was clean. No applicable AGENTS.md or CLAUDE.md files were found in the workspace hierarchy inspected.
- I read the complete external review request, r1, v0.2.1 errata, supplied synthesis, M preflight JSON, P0 report, runner, and metric test file. I also inspected relevant inherited v0.2 clauses to distinguish omissions from inherited requirements. The supplied synthesis was background, not a substitute for deriving this review from the current contract and code. I did not read earlier individual model reports.
- No training, evaluation, model forward, test suite, external API, subagent, or additional model was run. Test 163 was not opened; no P1 data was used. The only artifact written is this report.
- Verification was static inspection plus a read-only, standard-library arithmetic check of the supplied preflight JSON. It reproduced train/val medians 768.5/766.5, 16 train contributors at 753, 15 eligible validation documents, exact common-ID agreement, 11 full-K targets with at least ten contributors, and disjoint listed train/val IDs. This verifies internal metadata consistency, not underlying cache/model hashes or native tokenization.
- “54 tests pass” is historical evidence, not a fresh check or evidence that PM decision/M/replay tests exist.

### Citation shorthand

- **R1**: `docs/plan_c5_b0a_pm_prereg_v0_2_1_r1.md`.
- **E21**: `docs/plan_c5_b0a_pm_prereg_v0_2_1_errata.md`.
- **V2**: `docs/plan_c5_b0a_pm_prereg_v0_2.md`.
- **Preflight**: `reports/provenance/C5_b0a/m_cohort_preflight.json`.
- **P0**: `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md`.
- **Runner**: `runner/c5_mt5_lora_b0.py`.
- **Tests**: `eval/tests/test_c5_b0_metric.py`.

## 2. Executive findings

1. **The factoring is genuine but the complete contract is not yet unambiguous.** A failure in validity no longer necessarily overwrites the other outputs. Internal ordering within a factor is not itself a defect. However, “any path/test flag” conflicts with the special PA-path rule, and `M_VALID` is not explicitly connected to `m_evaluable`. Therefore an implementation can follow the pseudocode yet misclassify cells.
2. **Strong Kleene operators do not make arbitrary status dispatch Kleene-complete.** With `n_signal=15`, both L endpoints true, `m_evaluable=true`, and `m_pass_l=NA`, control is `NOT_ASSESSABLE` and signal falls through to `NOT_ASSESSABLE`. The raw L flag survives, but the unconditional promise that signal_status preserves L does not. Small-N/true-L combinations likewise contradict the exhaustive invariant unless the input domain is constrained.
3. **753 is a defensible, explicitly narrower estimand, not restoration of full-K.** The metadata arithmetic checks out. It is length-conditioned, prefix-matched evidence on 15 selected documents, with no spare eligibility margin. Calling it full-real-K content-use evidence would be incorrect.
4. **Cap arithmetic is repaired; runtime feasibility is unproved.** Twelve times 100 equals 1,200; debug no longer consumes that allowance. Zero-update D0 does not measure backward/optimizer cost. A finite, credible all-in timing projection must be required, not inferred automatically from a successful D0.
5. **PA naming is substantially repaired.** The inherited prohibition on using retention as a gate remains important. P0 is a coarse path sensitivity check, not proof that trained P/PA/L works.

## 3. Q1–Q12

### Q1. Is the factored tri-state contract genuinely total?

- **Verdict: disagree**, with the claim that it is already a single unambiguous total contract; agree with the architectural direction.
- **Evidence:** R1 §§2.1–2.5 separates validity/control/signal and supplies default branches. Once its inputs are fully specified, each dispatch can return an enum. But R1 lines 106–109 say any failed/unknown path/test triggers assay-invalid/not-assessable, while lines 126–127 distinguish P path failure from PA path failure. E21 §1.1 explicitly lists `pa_step100_path_ok` among independent path flags. If it belongs to “any path,” PA failure becomes `ASSAY_INVALID`, contradicting `PA_STEP100_NOT_VALID`; if it does not, that exclusion and conversion into `pa_valid` must be stated. A single aggregate `path` in R1 §2.8 cannot test this distinction.
- **Evidence:** R1 §4.5 defines `M_VALID` from P/PA POS and NORM passes, with P_VALID/PA_VALID prerequisites. Sections 2.3–2.4 consume `m_evaluable`, not `M_VALID`, and never give its exact derivation. For example, with paths/P/PA valid, adequate cohort, one P M-validation contrast false, and L M pass true: interpreting evaluable as “CE/cohort available” permits `(VALID, M_CONTROL_PASS, EXPLORATORY_L_SIGNAL)`, although the negative control failed calibration. Routing this to M-not-evaluable instead is plausible but not specified for known-false calibration. Removing the old label did not remove the need to route that case.
- **Next steps:**
  1. Enumerate path/test inputs and exact inclusion/exclusion rules; give explicit P- and PA-path-failure cases, including simultaneous failures and missing flags.
  2. Define `m_evaluable` from mechanical eligibility, required seeds/cohort, replay, P/PA validity, and P/PA M validation; record known calibration failure separately from missingness in raw reasons. No calibrated L pass/fail claim when those prerequisites are not true.
  3. Freeze legal input types/dependencies and a truth-table oracle before implementation. Test both separate path flags and M-validation inputs, not only pre-aggregated booleans.

### Q2. Are signal labels executable and is L always preserved?

- **Verdict: conditional.** The principal label meanings are much clearer, but the asserted invariants exceed the written dispatch.
- **Evidence:** R1 §§2.5–2.6 makes small-N reachable and defines copy-only/full-only through AND3/NOT3. With both endpoints known false and M passing, `MEAN_CONTRAST_ONLY` is now reachable and interpretable. Neither single-endpoint label should imply evidence that its other endpoint is missing; the NOT3 definitions correctly avoid that.
- **Evidence:** The Q1 example with L=true and control `NOT_ASSESSABLE` has no L-specific branch at R1 lines 166–181. In addition, §2.8 simultaneously demands that `n_signal<15` always yield `INCONCLUSIVE_SMALL_N` and every true-L combination retain L in signal_status. Its Cartesian product includes `n_signal=0, l_copy=T, l_full=T`, so these assertions cannot both hold literally. An upstream rule might prohibit true L with small N, but the stated exhaustive test includes that input. “Any required signal flag” also needs an explicit list; including M prerequisites there could unintentionally suppress the dedicated M-not-evaluable L label.
- **Next steps:**
  1. Specify L=true/control-unknown behavior explicitly: either preserve it with an L-qualified unassessable label or explicitly limit the signal-status preservation promise while always retaining raw L flags and reasons.
  2. Define whether impossible/inconsistent combinations are rejected, normalized, or tested as raw combinations; make the small-N invariant and L-preservation invariant compatible.
  3. Enumerate required signal flags, keep M missingness separate from donor-endpoint missingness, and test all signal labels including NA and exact N boundaries 14/15.

### Q3. Is the M preflight/prefix compromise legitimate?

- **Verdict: conditional**, in favor of the narrower prefix experiment over abandoning all primary M diagnostics, provided its scope is explicit.
- **Evidence:** R1 §1 and Preflight agree: K=753 gives 16/20 train contributors and 15/20 eligible validation targets; the original full-K criterion gives only 11/20. These counts and common IDs are reproducible from the supplied lengths. No trained P/PA/M outcome is claimed to have been seen. Selecting on lengths before outcomes is preferable to changing K to rescue an observed M result.
- **Evidence:** R1 §4.3 compares real prefix and mean at equal positions/length, avoiding a memory-length confound within that contrast. For the selected targets, 753 retains approximately **90.72%–100%** of stored hidden positions, calculated from the supplied lengths. That is useful context, not a semantic-content guarantee. The five short-document exclusions and four excluded train contributors change the population and builder. Full-K 11/20 remains secondary and cannot validate all 20 targets. Native 512 counts are asserted in the artifact but cannot be independently rederived from EG2 lengths alone.
- **Next steps:**
  1. Freeze K, selected IDs/contributor IDs, exclusion reasons, source hashes, and the prefix-specific estimand before outcomes; do not generalize to all-20/full-K evidence.
  2. Keep full-K secondary and accept `M_NOT_EVALUABLE` if prefix copy/full/seed-complete eligibility falls below 15; no replacement targets or later K search.
  3. Explicitly resolve native tokenizer maximum length to 512 in the executable configuration: V2 §4 says 256, while R1 requires 512-position native memory. Do not silently pad or rely on the current runner's default 256 to satisfy this requirement.

### Q4. Are aggregation, validation, and replay sufficient and leakage-free?

- **Verdict: conditional.** The design is consistent with training-only control construction, not yet evidence of a verified implementation.
- **Evidence:** R1 §§4.2, 4.5–4.7 uses seed-specific builders, POS AND NORM in L, both P and PA calibration, and seed-average-before-document-bootstrap. This correctly avoids treating 45 seed-document observations as 45 independent documents. E21 §§3.2/3.5 retains zero/nonfinite-norm handling and explicitly says NORM is magnitude-matched rather than strictly target-independent. V2 §3 clarifies that PA uses its adapter outputs, not raw native hidden states.
- **Evidence:** R1 §4.7 actually specifies `atol=1e-5, rtol=1e-4`, not a strict absolute CE difference of 1e-5. An allclose-style bound at reference CE 13 is about 0.00131. That is not inherently unacceptable, but the implementation and description must agree. Equality of an aggregate alone could conceal opposing per-document errors. Preflight ID disjointness supports separation but does not prove builder isolation or checkpoint correctness.
- **Next steps:**
  1. Require all three expected seeds and fixed document-ID alignment; use the same assessable common cohort across P/PA/L and both endpoints for M calibration/comparison. Preserve the inherited missing-seed prohibition; never average only available seeds.
  2. Specify eval/no-grad builder state, trained PA adapter placement, frozen native encoder, source/contributor hashes, and checkpoint association. Test that val/summary/donor changes cannot alter POS/GLOBAL; NORM's explicitly allowed dependence is the real-prefix scalar norm, not target labels or learned target-specific direction.
  3. Compare keyed per-document/per-seed CE for each required POS/NORM/real variant in replay, with the exact tolerance formula and all required state restored; missing or mismatched replay makes M unassessable, not a failed content-use result.

### Q5. Is PA acquisition naming sufficient and retention non-gating?

- **Verdict: agree**, subject to implementing the path dispatch repair in Q1.
- **Evidence:** R1 §§3.2–3.3 replaces `ADAPTER_REGIME_LOSS` with `PA_STEP100_NOT_VALID`, identifies random Linear–GELU–Linear–LayerNorm step0, and distinguishes native final hidden from EG2 layer19 scale/geometry. E21 §2.3 explicitly makes both retention ratios descriptive and null for unstable denominators; R1 does not override that prohibition. PA step0 is not P0. A trained PA sensitivity pass supports this native acquisition regime, not successful EG2 transfer or a causal diagnosis of adapter damage.
- **Evidence:** P0 reports train/val copy deltas +3.7617/+5.2375 with positive CIs, but val median 2.9739, top-three share .4862, and real CE about 12.7/13.2 versus ln|V|≈12.43 (the latter diagnostics are also supplied in the request/V2). These observations do not establish trained PA validity. The unchanged .05 gate is a weak sensitivity screen, not a meaningful improvement over P0.
- **Next steps:**
  1. Carry null/non-gating retention semantics into the artifact schema and regression tests, including near-zero step0 denominators.
  2. Require separate P and PA step0 records and preserve the scale/geometry caveat and noncausal naming in reports.

### Q6. Are budgets and two-hour feasibility executable?

- **Verdict: conditional** on accounting and an evidenced projection; **defer** the empirical feasibility claim.
- **Evidence:** R1 §6 repairs the former 1,220-versus-1,200 inconsistency: registered 12×100=1,200; D0 is zero-update/at-most-four configurations/15 minutes; D1 is four arm-seeds×one update/20 minutes with separate approval. D1 is four updates, not four additional registered 100-step units. Two-hour feasibility has no current all-in timing evidence in the requested artifacts.
- **Evidence:** R1 §6.5 sets a launch cutoff at 0.8×2 hours = **96 minutes / 5,760 seconds**. D0 load/attach/forward does not time backward/optimizer, and D1 is optional. Therefore successful D0 cannot itself establish a valid training-time projection. A two-hour hard cap can be enforceable even if no complete run fits; feasibility and enforcement are different questions.
- **Next steps:**
  1. Define one registered job-level timer from process start, covering all 12 units, loading, step0/final diagnostics, M, generation, serialization, and separate-process replay; aggregate the ledger across children. Keep CPU time distinct from elapsed wall time.
  2. Require a conservative, justified full-workload projection including backward/optimizer cost and evaluation counts. If D0-only evidence cannot supply it, leave 3-seed blocked; D1 remains separately approved, not implicitly authorized by this need.
  3. Implement hard stop/no automatic retry or extension, counters, cap-exhaustion reason, and partial-artifact handling. Any requested cap change requires prospective approval, not an after-the-fact extension.

### Q7. Are statistical constants and tail diagnostics executable?

- **Verdict: conditional.** Most statistical choices are now fixed; the remaining edge cases matter for a total reporting contract.
- **Evidence:** R1 §5 fixes 1,000 percentile resamples, 2.5/97.5 endpoints, seed 20261109, document units, seed averaging, and separate document/seed-positive counts. E21 §4.3 already fixes both L endpoints, paired L−F comparison, and 2/3 seed positivity; these are not missing wholesale. R1 §5's `sum(top3)/sum(all)` is undefined at total zero and is not an ordinary concentration share with a negative total. Its single tail flag also needs to identify the endpoint/cohort used.
- **Evidence:** Runner lines 384–398 still default to bootstrap seed **20261108** and report document positives as **`seeds_positive`**. Its present evaluation returns a copy bootstrap but not a full-endpoint bootstrap. These are concrete integration hazards, not proof that the proposed future PM implementation has already failed. Tests presently do not verify the new pooling/constants/edge cases.
- **Next steps:**
  1. Freeze RNG/percentile interpolation behavior, deterministic document order, required-seed completeness, cohort alignment, and finite-value handling; add fixtures for equality at .05, zero CI lower bounds, and paired seed/document pooling.
  2. Define top-three ordering/tie-breaking, signed-total/zero-total behavior, and null/NA propagation. Compute endpoint-specific diagnostics and state how they feed the tail flag; do not convert an undefined ratio into a reassuring false flag.
  3. Add a PM-specific statistics path or explicit migration that uses seed 20261109, honest field names, and both endpoint CIs without silently rewriting historical P0 artifacts. Keep tail diagnostics descriptive; do not tune any gate after results.

### Q8. What remains Must-fix, ranked?

- **Verdict: disagree** with R1 §10's assertion that all listed Must-fixes are closed.
- **Evidence:** Sections 2 and 4 retain the concrete dispatch ambiguities above; §2.8 includes incompatible exhaustive assertions; §5 leaves arithmetic/domain cases unresolved. Sections 6–7 define sensible gates but not sufficient evidence for an all-in projection. These are narrower than the previous round's failures: small-N is now reachable, M eligibility is demonstrably possible, PA naming is fixed, and cap arithmetic no longer overflows.
- **Next steps:**
  1. Make a text-only r2 addressing the ranked list in §4 below; replace premature “closed” declarations with testable acceptance conditions.
  2. Review/freeze that repair before implementation; keep K/thresholds/seeds/donors/steps/LR unchanged and do not use outcomes to resolve these ambiguities.

### Q9. Can r1 freeze, implementation, unit tests, and D0 be approved now?

- **Verdict: conditional; not as written.** I do not recommend freezing r1 or starting PM implementation/D0 on this contract. A repaired, explicitly accepted r2 can authorize implementation and synthetic tests first, followed by D0 after their acceptance.
- **Evidence:** R1 §§8/11/12 makes contract approval precede code and treats a new NARROW as grounds for a Must-fix-only r2. The existing runner's CLI (lines 753–798) exposes smoke/metric-smoke/train/p0-sanity, not pm-diagnostic or P/PA training. `train_arm` accepts frozen/lora only; `set_training_mode` assumes an adapter. That is expected preimplementation state, not an available D0 implementation. The seven tests in the requested metric file are within a model-dependent class; even pure donor/decision checks are skipped when the local model is absent.
- **Next steps:**
  1. Before implementation authorization, require a typed flag schema and expected-output fixtures for separate P/PA paths, M calibration false/NA, L+unknown-M, small N, zero/negative tail denominators, and missing seeds.
  2. During implementation, add model-independent exhaustive decision/statistics tests plus M leakage/cohort/replay and PA/P mode/init tests; assert D0 cannot call optimizer.step, compute outcome labels, or fall through into legacy evaluation/generation modes.
  3. After code/hash/test acceptance and explicit authorization, permit only bounded D0 mechanics; any real-data mechanics probe must stay within the frozen D0 contract, not an unlabeled full diagnostic run.

### Q10. Are D1 and 3-seed boundaries sufficient?

- **Verdict: conditional.** The approval separation is good; operational acceptance needs tightening.
- **Evidence:** R1 §§6.3/7 explicitly makes D1 optional and separately approved; all ten launch items are necessary, not sufficient, and explicit user approval is required. E21 §5.1's unregistered debug seed **20261111** remains applicable. No D0 or D1 pass automatically grants registered training. The inherited missing-seed prohibition must survive cap aborts and partial output.
- **Next steps:**
  1. Put immutable budget category, seed 20261111 for debug, requested/permitted updates, cumulative elapsed time, and approval reference in D0/D1 artifacts. D1 has exactly one permitted update per arm, no outcome labels, and no checkpoint promotion into registered runs.
  2. Extend checklist acceptance to the resolved M-validation mapping, full-workload timing evidence, fixed per-seed/cohort coverage, exact effective configuration/hashes, replay completeness, and cap-abort semantics.
  3. Require fresh registered initialization and explicit three-seed authorization after checklist review; do not permit a missing/NaN timing projection to pass or interpret D0 completion as approval.

### Q11. Does the B0-B boundary remain intact?

- **Verdict: agree.** It is explicit and must remain a separate prospective decision.
- **Evidence:** R1 §9 says no Phase 6 label automatically approves B0-B/B1/B2/Stage C and requires separate preregistration and review/approval. Replacing stale references with current prerequisites repairs the intended boundary. Because signal is factored, `EXPLORATORY_L_SIGNAL` alone is insufficient: it can coexist with invalid validity_status unless consumers check the whole tuple.
- **Necessary conditions, not authorization:** all path/mode/metric/leakage checks pass; P_VALID and PA_VALID true; M mechanically evaluable and P/PA POS+NORM calibration true; L POS+NORM pass; copy+full L donor signal including paired L>F and seed consistency; adequate fixed cohorts; endpoint-specific heavy-tail robustness reviewed; complete manifests/checkpoints/replay/artifacts; and a separate prospective B0-B preregistration plus explicit approval. A clean `(VALID, M_CONTROL_PASS, EXPLORATORY_L_SIGNAL)` is at most one input to that later review, not a sufficient launch condition.
- **Next steps:**
  1. Make downstream consumers check the tuple, flags, robustness evidence, and authorization rather than the convenience headline or signal label alone.
  2. Keep B0-B/B1/B2/Stage C launch impossible from D0/D1/registered-run completion; no favorable result creates an automatic next-stage entitlement.

### Q12. Final STOP / NARROW / CONTINUE and exact scope

- **Verdict: conditional — final recommendation NARROW.** The repair direction is sound enough to continue contract work, but not to freeze r1 or run the experiment.
- **Evidence:** Prefix preflight and budget arithmetic solve important structural failures; Q1/Q2/Q7 still provide concrete unclosed contract cases. R1 §11.1 itself calls for a Must-fix-only r2 if review returns NARROW.
- **Next steps:**
  1. Produce the text-only r2 and resolve the ranked items below before freezing a protocol commit.
  2. Obtain explicit acceptance for implementation/synthetic tests and later D0; separately request D1 or registered execution only when their own gates are met.
  3. Preserve all sealed-data/model/stage boundaries and report partial or unassessable results honestly; no post-result threshold/seed/donor/step/LR changes.

## 4. Ranked Must-fix before freeze

| Rank | Must-fix | Acceptance evidence required |
|---|---|---|
| 1 | **Typed validity/control routing:** enumerate path flags, reconcile PA path rule, and connect M_VALID/prerequisites to m_evaluable. | Expected outputs for P/PA path combinations and P/PA M-validation true/false/NA, with raw reasons retained; calibration failure cannot yield a calibrated L claim. |
| 2 | **Compatible signal invariants:** L+unknown-control cell, required-signal list, and legal-input/small-N policy. | A consistent truth-table oracle; raw flags always preserved; every declared label reachable on its declared domain; contradictory exhaustive assertions removed. |
| 3 | **Statistical/cohort edge cases:** exact endpoint-specific tail semantics, zero/negative totals, deterministic pooling, all required seeds and paired IDs. | Frozen arithmetic/schema and expected fixtures; undefined ratios or missing seeds do not silently become false/pass; both endpoint CIs use the PM constants. |
| 4 | **Executable M configuration/replay:** effective native source max 512, PA adapter-space construction, deterministic eval state, qualified NORM target dependence, complete keyed replay/tolerance. | One effective config and manifest specification; explicit contrast/cohort/seed and tolerance rules; inherited source-max 256 cannot silently defeat native eligibility. |
| 5 | **Budget gate evidence and enforcement:** all-in timing model, job-level wall ledger, zero/one-update guards, partial/abort behavior. | Projection includes backward and all mandatory diagnostics/replay and must be finite and ≤96 min; inability to justify it blocks launch without implicitly approving D1. |

Ranks 1–3 are contract correctness defects, not stylistic preferences. Rank 4 consolidates critical inherited details so an implementation cannot resolve them accidentally. Rank 5 does not require proving two-hour feasibility during this consultation; it requires defining how unproved feasibility blocks launch. No new trained outcome or threshold change is needed to close any item.

## 5. Approval/budget disposition

| Item | Recommendation in this review |
|---|---|
| r1 freeze | **No, as written.** Must-fix-only r2, review acceptance, then immutable hash. |
| PM implementation + unit tests | **Conditional, after repaired-contract acceptance and explicit authorization.** No implementation performed here. |
| D0 | **Not authorized now.** Subsequently conditional on accepted code/tests and explicit mechanics scope: 0 optimizer updates, ≤4 configs, ≤15 min wall, no outcome labels, unregistered debug seed. |
| D1 | **Not approved.** Optional, separate explicit approval; four arm-seeds×one update = four updates total, ≤20 min wall, no result labels. |
| Registered three-seed Phase 6 | **Not approved.** Separate checklist plus explicit launch approval; 12 arm-seeds, 100 updates each, ≤1,200 updates, ≤2 h all-in wall, 6 threads, no GPU, no automatic retries/extensions. |
| B0-B/B1/B2/Stage C | **Not approved; never automatic.** Separate preregistration/review/approval. |
| Test 163 | **Sealed; unopened and unused.** |
| P1 | **Unused and prohibited in this round.** |
| T5Gemma2 | **D-108 STOP remains closed.** |

**Maximum compute authorized by this consultation: zero training/evaluation; only read-only review and this report.** Conditional future budgets above are not grants. If all three budgets were separately approved later, D0+D1+registered ceilings would total at most 155 minutes wall and 1,204 optimizer updates across 12 registered trained units plus four D1 smoke units; their separate categories, timers, and approval boundaries must remain visible. Pure unit-test work should have its own transparent accounting and must not disguise a real-data evaluation as a test.

## 6. Incorrect premises to avoid

- Factoring alone does not prove all semantic cells or dependency mappings are specified; Kleene arithmetic does not repair an ambiguous dispatch domain.
- Retaining raw L flags is not the same as fulfilling an unconditional claim that every signal_status retains L. The latter is currently contradicted by explicit inputs.
- Fifteen length-eligible targets are not proof of fifteen finite, copy-eligible, seed-complete outcome records. There is no margin for an additional exclusion.
- A 753-position mean-vs-real-prefix contrast is not full-K validation and does not cover excluded documents. NORM is not strictly target-independent.
- A replay rule with nonzero relative tolerance is not a strict 1e-5 absolute-error promise.
- Passing historical repair tests or P0 does not establish PM implementation correctness, PA acquisition, EG2 transfer, or registered runtime feasibility.
- D0/D1 success and a favorable exploratory signal do not approve registered Phase 6 or B0-B. No result permits retrospective protocol tuning.

**Bottom line: NARROW — preserve the improvements, repair the remaining contract before freeze, and keep every execution gate closed pending its own explicit approval.**