# Sol 6.1 high reviewer — independent v0.2.1 errata review

**Reviewer:** Sol 6.1, high reasoning. This is a new, independent external review of mandutt/unigem for Hoplite project proj_2e8de5ed594f47c7b851f1d7c5b52c61, not a continuation of the v0.2 review.

**Final recommendation: NARROW (conditional). Do not freeze v0.2.1 as written.** The changes substantially improve the design, but its missingness/decision contract and debug-inclusive budget remain internally inconsistent. A small, outcome-blind contract correction should precede implementation and unit tests. Mechanics debug additionally requires passing tests, reconciled accounting, and explicit authorization. This consultation grants **no Phase 6 execution approval**, no registered three-seed run, and no B0-B approval.

## Review basis and compliance

- Date: 2026-11-09.
- Ran `git fetch origin`, then `git pull --ff-only origin main`, in that order. Both succeeded; pull reported `Already up to date.`
- Resulting HEAD and `origin/main`: **`075621596fbe4e169c02f0c4c75ad65b3d42853f`**. This is the review basis, not the request's historical authoring HEAD `672db63`.
- Existing workspace branch: `hoplite/skepsis-973fba2b`; its HEAD equals `origin/main`. No branch switch, commit, push, or PR was made.
- Read the entire external review request and all seven user-listed materials, plus the v0.1 synthesis and repair report requested by the review request. Inspected the shared Adapter/LoRALinear definitions and relevant legacy aggregation source to check implementation implications.
- Prior syntheses are historical context only. I did not open individual prior model reviews or reuse their conclusions as a substitute for this review. No subagents, additional models, external APIs, training, evaluation, or test execution were used.
- No dataset, split manifest, cache, or model-weight file was opened. **Test 163 remains sealed; P1 was not used. T5Gemma2 remains closed by D-108 STOP.**
- This report is the only working-tree file written. Requested Git synchronization necessarily updates Git metadata.
- Historical passing tests are not fresh verification. No trained P/PA/M result is asserted or inferred.

### Source keys

All line references below refer to the synchronized HEAD above.

| Key | Source |
|---|---|
| R | `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_1_2026-11-09.md` |
| E | `docs/plan_c5_b0a_pm_prereg_v0_2_1_errata.md` |
| V | `docs/plan_c5_b0a_pm_prereg_v0_2.md` |
| S2 | `reports/C5_B0A_PM_PREREG_V0_2_3AI_REVIEW_SYNTHESIS_2026-11-09.md` |
| S1 | `reports/C5_B0A_PM_PREREG_3AI_REVIEW_SYNTHESIS_2026-11-09.md` |
| P0 | `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md` |
| Repair | `reports/C5_B0A_REPAIR_2026-11-09.md` |
| Runner | `runner/c5_mt5_lora_b0.py` |
| Tests | `eval/tests/test_c5_b0_metric.py` |
| Aggregate | `runner/c5_b0a_aggregate.py` |

## Executive assessment

**Genuinely improved:** separate L flags; explicit P/PA interaction; PA's own random-adapter step0; optimizer/movement fields; full-real-K M reference; POS **and** NORM conjunctions for L and for both positive controls; separate contributor and target-cohort minima; seed-average-before-document-bootstrap; paired L−F; an unregistered short debug; wall-clock terminology; and checkpoint/manifests requirements.

**Not yet closed:**

1. A Boolean fallback does not make the function total over the actual domain, which includes unavailable CIs, missing seeds, small cohorts, and path failures. `not_assessable` is stored but never consulted by the headline function.
2. The common-cohort rules do not explicitly align all required arms, all three seeds, both endpoints, and M variants. Numerical failures and structural ineligibility are not consistently distinguished.
3. Debug is included in a cap already fully consumed by twelve registered 100-update units. Four additional debug arm-seeds cannot fit that cap.
4. Statistical implementation and artifacts still need exact scope, replay, missingness, and enforcement contracts. The current code is a repaired F/L/P0 runner, not an implemented PM protocol.

P0 is useful historical assay evidence, not a trained positive-control result or bridge success. Its reported train/val mean copy deltas are +3.7617/+5.2375 with CIs [1.8917, 5.6050]/[2.5013, 8.0753] (P0:27–35). The request reports val median 2.9739 and top-three share .4862 (R:197–209). That is a strong reason to retain distributional reporting and limit claims, not to change thresholds after results.

## Q1. Total decision function

**Verdict: disagree — syntactically exhaustive for supplied Booleans, not yet a coherent total function over real protocol states. L preservation is materially improved.**

**Evidence.** E:65–105 has a final `otherwise`, so every complete Boolean input can return something. E:110–112 explicitly preserves L_COPY_SIGNAL/L_FULL_SIGNAL/L_SIGNAL even when validity dominates the headline. This addresses suppression at the artifact/report level; I do not require L_SIGNAL to outrank a genuine validity failure.

However, E:126–132 says unavailable CIs must not become pass/fail, one missing seed prohibits a pooled headline, and small document counts are inconclusive. The headline function never checks `not_assessable`, seed completeness, or document count. Specific counterexamples:

- With paths valid, P/PA and M valid, `not_assessable=true`, and unavailable L/M results coerced to false, row 12 returns `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE`. The evidence was unavailable, not an observed non-pass. An unavailable M contrast must not become row 7's `L_SIGNAL_M_CONTROL_FAIL` either.
- With P valid but `pa_step100_path_ok=false`, row 4 is skipped. The result can become M_NOT_EVALUABLE or M_CONTROL_NOT_VALID, depending on other flags. E:128 instead requires a path/finite/shape failure to be ASSAY_INVALID. Similarly, row 2 gives a P path failure P_STEP100_NOT_VALID while E:128 says ASSAY_INVALID.
- With a missing P CI represented as `p_valid=null`, ordinary `not p_valid` Boolean coercion can select row 3. E:129 expressly prohibits converting an unassessable result to a statistical failure.
- With fewer than 15 common endpoint documents and false L flags, rows 11 or 12 can fire before row 13. With coherent definitions of L_SIGNAL and the two exclusive endpoint flags, ordinary assessable cases already exhaust rows 7–12; the final fallback is not a real small-N check.

Also, row 3 contains two slash-separated names rather than one canonical output. `copy_only`/`full_only` need explicit derivation from endpoint results, and derived flags must not be freely contradictory. The P/PA four-cell table covers assessed T/F results, not missing/path-invalid states. M_NOT_EVALUABLE must distinguish absent prerequisites from an actually assessed M validation failure.

**Next steps (3):**
1. Freeze a typed input/result schema: status, nullable assessed flags, explicit reason codes, canonical headline, and derived-flag invariants. Distinguish observed fail, structural ineligibility, not run, and unavailable. A missing registered seed must produce no pooled scientific headline, as E:131 requires.
2. Add explicit integrity/missingness/cohort precedence before scientific pass/fail rows; reconcile P/PA path failures with E:128. Preserve any independently assessable L flags and show them alongside the headline, not only inside hidden JSON.
3. Require synthetic truth-table tests for all reachable assessed cases, missing/null/error cases, PA path failure, and L true under every validity headline. Reject inconsistent combinations rather than interpreting them opportunistically.

## Q2. P/PA contract

**Verdict: conditional — the key baseline confound is addressed, but this is not complete causal isolation or an executable missingness contract yet.**

**Evidence.** E:142–159 fixes AdamW, weight decay .01, adapter LR 1e-3, LoRA LR 1e-4, 100 updates, cyclic order, clipping 1.0, base eval, and LoRA initialization reseeding. E:163–187 correctly distinguishes native zero-LoRA P step0 from native **random-adapter** zero-LoRA PA step0 and records movement/retention. P0 cannot substitute for PA step0. E:206–207 correctly makes both positive controls prerequisites for M interpretation.

The P-valid/PA-invalid cell is useful. But its condition compares the final P and PA screens; it does not require a measured decline from PA step0. PA may already have been insensitive at random initialization. Therefore `ADAPTER_REGIME_LOSS` must always be glossed as **P passes, PA does not pass**, not “training destroyed PA selectivity” or “the adapter caused the loss.” E:123's descriptive-only restriction is essential. Native P/PA success still does not establish that EG2 memory occupies the same useful operating regime.

The movement fields need scope and definitions: per-document versus cohort delta, parameter-space adapter delta norm versus output movement, and an exact numerical rule for an “unstable” retention denominator. Negative or tiny PA step0 deltas can make ratios misleading. None of these ratios may become an undisclosed scientific gate.

Runner:329–380 currently accepts only frozen/lora and requires an adapter, so P's adapter-free mode is not implemented. Existing training attaches LoRA after adapter initialization without the errata's immediate reseed (Runner:677–680). The current mode test covers F/L only (Tests:62–84).

**Next steps (3):**
1. Specify gate split and aggregation scope explicitly: validation is the primary screen; any training-panel movement is descriptive. Compute retention from matched step0/step100 documents, donors, and crop semantics, with a preregistered numerical null guard and reason field.
2. Test P zero-LoRA equivalence to the native P0 path, PA zero-LoRA equivalence to its own saved random adapter, reproducible LoRA initialization, and explicit mode restoration after step0 evaluation.
3. Implement P/PA eligibility as assessed-status-aware prerequisites, not false-for-missing flags; report final P/PA discordance alongside PA's own step0 and movement rather than attributing a cause.

## Q3. P gate

**Verdict: agree — it remains weak, and the screen-only interpretation is appropriate. It is not a meaningful minimum-retention guarantee.**

**Evidence.** E:192–202 retains copy mean >=.05 and strictly positive copy/full CI lower bounds, with full mean >0. Relative to the reported P0 copy means, .05 is about **1.33% of train** and **0.95% of val**. Thus a large reduction in sensitivity can still satisfy the point-estimate floor; the CI conditions add uncertainty screening but do not impose substantial retention.

E:200–201 correctly calls this a post-training native-path sensitivity screen and disallows claiming LoRA learned selectivity. P0 real copy CE 12.7022/13.2352 (P0:29–30; V:278–283) exceeds the uniform-reference ln(250112) approximately 12.43. This comparison does not by itself diagnose a cause, but demonstrates why a large wrong-minus-real delta is not evidence of good calibrated generation or learned semantic use. The reused 20-document validation panel is not a confirmatory holdout (V:154).

**Next steps (2):**
1. Keep the registered .05, CI, full/copy, seed, donor, step, and LR rules unchanged. Describe P_VALID/PA_VALID as survival-of-sensitivity screens; do not relabel them strong retention or learning gates.
2. Present step0/step100 absolute real and wrong CE, deltas, retention where interpretable, and heavy-tail summaries together. A stronger scientific question would require a separately approved preregistration, not a post-result gate adjustment.

## Q4. M contract

**Verdict: conditional — adequate direction for a bounded negative-control diagnostic, not yet a fully specified leakage-free executor or proof of semantic content use.**

**Evidence.** E:215–217 correctly uses full real K, not donor-cropped CE. E:243–259 now requires positive full/copy contrasts with positive CI lower bounds for **both POS and NORM**, separately for P and PA, and likewise both variants for L. This closes the weakest-variant rescue loophole. GLOBAL cannot rescue a failure (E:253).

The contributor floor >=10 and common target floor >=15/20 are distinct and both needed (E:224–237). They do not eliminate length-selection bias. E:265–267 precisely chooses whole K×512 Frobenius scaling and correctly acknowledges that NORM uses target memory magnitude. Therefore the POS builder can be train-only conditional on K, but the NORM control is **not strictly target-independent**. “Leakage-free” must mean no target label, validation vector contribution to the mean direction, or donor contribution, with the deliberate target-norm dependence explicitly recorded.

Remaining operational gaps:

- Common M eligibility must be an intersection over L/P/PA **and all three registered seeds and both endpoints/variants** used in the pooled comparison, not a separately chosen cohort for each cell. F is not required for M alone, but is required in the paired L−F panel.
- The builder must use each arm/seed's own checkpoint: identity/native encoder memory for P; that PA checkpoint's adapter outputs for PA; that L checkpoint's adapter outputs for L. V:133 supports this, but the executor schema must encode it.
- E:230 declares zero/non-finite norm M_NOT_EVALUABLE, whereas E:128 classifies finite/path failures ASSAY_INVALID. E:237 is cohort-level, while E:272 also lists contributor shortage without specifying whether it excludes one target or stops the entire probe. Freeze that distinction. Non-finite execution must not become an outcome-dependent opportunity to drop targets until a gate passes.
- “M_GLOBAL over all eligible positions” should specify whether it pools full contributor lengths or their first K rows. It is secondary, but must still be replayable.

Frobenius matching does not restore token directions, row-norm distributions, covariance, or an on-manifold input. A joint pass supports a checkpoint-specific real-versus-these-controls contrast; it does not establish a complete causal mechanism.

**Next steps (3):**
1. Freeze the exact M cohort intersection, structural eligibility algorithm, contributor/source identities, GLOBAL reduction, and action for zero denominator/zero real norm/non-finite values before outcomes. Use validation targets only for the primary M panel and assert source/target disjointness.
2. Define separate invariance oracles: fixed-K target/summary/donor changes cannot alter POS; NORM may change with the target Frobenius norm, but must not depend on target labels or target direction when K and norm are fixed. Test source-order invariance and the intended memory-row permutation property without asserting that arbitrary train-row perturbations preserve a position-wise mean.
3. Persist actual final checkpoint files and hashes, then verify replay reconstructs contributor IDs, K, norms, memories, and both endpoint contrasts. A hash alone is not persistence.

## Q5. Statistics

**Verdict: conditional — the central mathematics is executable, but complete-case scope and several deterministic details remain to be frozen.**

**Evidence.** E:281–295 correctly averages three seeds within document, then bootstraps documents 1,000 times; 60 seed-document rows are not 60 independent observations. E:300–320 defines paired L−F mean >0 per endpoint and seed-level positivity. The requirement is **at least two of three** positive seed means, not exactly two, and it applies to L's endpoint deltas, not an unstated per-seed L−F or M gate.

The current bootstrap helper gives a useful inherited numerical convention: seeded NumPy RNG and percentile bounds 2.5/97.5 (Runner:384–398). Its `seeds_positive` still counts positive **documents**, so a PM caller cannot reuse that field unchanged. The existing aggregate already averages seeds per document and pairs F/L, but its historical positive gate requires L−F CI lower >0 (Aggregate:100–106). The errata requires only paired L−F **mean** >0. Blindly reusing that legacy gate would silently implement a different protocol.

E:324–325 chooses a common copy/full subset and minimum 15, but does not explicitly align it across compared arms and all three seeds. Runner:201–202 and 437–438 drop the entire document when copy CE is unavailable, discarding otherwise valid full CE. PM must retain endpoint-specific availability before selecting the registered common primary panel. `copy_ce` currently needs at least five selected valid positions (Runner:311–315); inherit or explicitly restate that rule, not just a generic “copy mask eligible” label.

Unspecified details include per-document donor reduction when fewer than five valid donors remain, exact source-duplicate detection, top-three-share denominator and tie handling, and zero/non-positive denominator behavior. The strict mask remains secondary; insufficient strict-mask tokens must not silently shrink the co-primary cohort.

**Next steps (3):**
1. Freeze a complete-case cohort for each planned paired contrast across all required arms/seeds/endpoints; average exactly three observed seed values per retained document, never `nanmean` over a changing seed count. Keep full-only/copy-only counts and reasons, and distinguish missing an entire seed from structural document ineligibility.
2. Specify deterministic 95% percentile bootstrap/RNG/version behavior, >=2-of-3 counting, donor reduction/completeness, and heavy-tail formulas with explicit null handling. Keep L−F CI descriptive rather than adding the legacy CI gate; do not add an unregistered M seed-consistency gate.
3. Test .05 equality, zero CI bounds, zero paired means, two versus three positive seeds, missing donors, duplicate sources, shuffled document order, null CIs, and unequal endpoint eligibility using synthetic fixtures.

These CIs remain descriptive screening intervals conditional on the trained checkpoints and this reused small panel. Shared donor sources, shared fitted checkpoints, and heavy tails limit an independent-document interpretation. The contract should acknowledge those limits, not upgrade the bootstrap into confirmatory inference.

## Q6. Debug

**Verdict: conditional — the exposure controls are substantially improved; budget, execution, and artifact isolation still need enforcement.**

**Evidence.** E:342–346 freezes prereg/code/test hashes, uses unregistered seed **20261111**, limits each F/L/P/PA arm to at most five updates, and prohibits M outcome labels. E:350–366 enumerates mechanical checks and forbids using registered 100-step results or searching seed/donor/step/LR. This removes the intended source of registered-seed pilot outcomes, provided these are validated hard constraints rather than optional CLI defaults.

A different seed does not prevent adaptation by itself. Mechanics code must avoid producing scientific summaries that can be treated as preliminary success, and implementation must not accidentally use the normal full-run reporter. Testing the label function on synthetic fixtures is permitted; emitting experimental L/P/M pass/fail labels from debug is not. The permitted real M mechanics probe needs an exact target/call bound and must stay separate from synthetic label tests.

**Next steps (3):**
1. Give debug a dedicated execution mode that rejects registered seeds, >5 updates/arm, full scientific labeling, parameter exploration, and the normal output namespace. Fix probe selection independently of scores.
2. Produce a debug-only manifest containing hashes, seed, actual optimizer updates, shapes, finite/alignment/mode checks, allowed reproducibility evidence, timing and call counts, `mechanics_only:true`, and `not_for_scientific_gate:true`; make outcome labels absent, not merely marked non-gating.
3. Reconcile the shared cap first. After tests pass, seek explicit mechanics-only authorization; no three-seed launch may follow automatically. Any necessary bug fix gets a new code/test hash and documented mechanical recheck, not a free extra scientific attempt.

## Q7. Cap and artifacts

**Verdict: disagree — the literal budget is inconsistent, and runtime feasibility is unverified. The artifact inventory is a good start, not yet a replay/enforcement contract.**

**Evidence.** V:61 and 320 specifies F/L/P/PA × three registered seeds, 100 updates each: **12 units and 1,200 updates**. E:376–382 retains that ceiling while explicitly including debug in units and updates. Running five debug updates for four additional unregistered arm-seeds gives:

- registered run: 12 units / 1,200 updates;
- nonzero four-arm debug: 4 additional units / up to 20 updates;
- combined: **16 distinct trained arm-seed units / up to 1,220 updates**.

Even one extra debug optimizer update leaves no room for all twelve registered 100-update units within the unchanged 1,200-update ceiling. The five-step limit is a maximum, not a requirement, so a zero-update mechanics path is possible; the document must choose explicitly rather than silently exempt debug. Do not shorten registered runs, drop a seed, or relabel debug as free to make the arithmetic fit. This review authorizes **no budget increase**.

The two-hour wall-clock definition is clearer than “CPU-hours,” but E:378's “from process start” needs a shared scope across separate debug and arm processes. Otherwise each invocation can restart the clock. Six threads must not mean six per concurrently launched worker with an unbounded total.

The workload is nontrivial. Under the current real/wrong donor loop (Runner:423–436), the registered validation panel alone is 12 × 20 × 5 × 2 = **2,400 decoder CE forward calls**, before training, P/PA step0, native encoding, M, or generation. Six P/PA validation step0 panels would add 1,200 analogous calls if recomputed. Nine L/P/PA checkpoints × 20 targets × real/POS/NORM/GLOBAL can add up to 720 M CE calls before reuse. Legacy generation runs every selected val document (Runner:494–515, 724): 240 generations for twelve units, each with a configured cap up to 256 new tokens. These are workload-accounting examples, not observed PM timings or a demand to execute them now.

E:389–409 lists hashes and per-unit artifacts, but does not define a pooled artifact, checkpoint paths/serialization, partial-run records, or when per-unit `headline` is allowed. A three-seed headline cannot be computed independently inside the first completed arm-seed JSON.

**Next steps (3):**
1. Resolve debug versus registered accounting in a pre-result, explicitly approved budget statement. Under unchanged ceilings, optimizer-using debug plus the full registered run cannot both occur. A zero-update mechanics scope is the cap-preserving option; any broader envelope requires separate authorization, not an implicit exception.
2. Define one shared campaign ledger and enforceable wall-clock limit across subprocesses, cumulative updates/units, and total thread allocation. Include loading/encoding, step0, all M variants, generation, checkpoint I/O and artifact/report work; debit debug and retries. Write partial artifacts and stop on exhaustion, with no automatic extension.
3. Freeze generation/probe workload and artifact ownership: per-unit raw metrics/status; separate all-seed aggregate flags/headline; debug-only namespace; actual checkpoint paths plus hashes; replay/config/input identities; bootstrap/cohort provenance; final and failed-run timings. Use bounded mechanical timing evidence for feasibility, never a timing excuse to relax caps or alter scientific steps after outcomes.

## Q8. Remaining Must-fix

**Verdict: agree — meaningful Must-fix items remain. The checked boxes in E:416–426 overstate completion.**

**Evidence and ranked closure list:**

| Rank | Must-fix | Source / concrete completion criterion |
|---:|---|---|
| 1 | **Typed decision and missingness contract** | E:65–132: normalize tri-state inputs; honor absent-seed/no-pooled-headline and unavailable-CI rules; put real small-N checks before no-evidence labels; reconcile P/PA path failure precedence; one canonical row-3 output; preserve assessable L flags. |
| 2 | **Debug-inclusive cap arithmetic and enforcement** | E:342–345, 376–385 versus V:320: resolve 16/1,220 versus 12/1,200 without silently changing registered runs; one shared wall-clock/thread/update ledger and explicit workload. |
| 3 | **Cohort/eligibility and finite-value policy** | E:224–272, 324–325: exact intersections over required arms, seeds, endpoints and M variants; >=10 contributors versus >=15 targets; structural missingness versus integrity failure; no adaptive dropping. |
| 4 | **Exact P/PA and statistical execution semantics** | E:157–187, 281–334; Runner:186–193, 311–315, 384–398: matched step0/crops, numerical retention guard, paired mean-only L−F, deterministic bootstrap, donor/duplicate handling, heavy-tail definitions. |
| 5 | **Artifact scope, checkpoint replay, and mechanical acceptance tests** | E:389–410; V:309–316; Tests:13–23, 62–124: separate debug/unit/aggregate objects, actual saved weights, failed-run artifacts, pure fixture tests plus local-model integration checks. |

Relative to S2:58–112, separate flags, PA step0, POS+NORM conjunctions, explicit P AND PA, and the two cohort minima are real closures at the design level. They should not be re-litigated as absent. What remains is chiefly their consistent operational composition. Newly visible problems are the debug-inclusive arithmetic contradiction, an unused NOT_ASSESSABLE state inside a supposedly total decision function, and a false impression that per-unit files can always contain pooled headlines.

**Next steps (2):**
1. Commit a concise outcome-blind contract correction addressing these ranked items without changing scientific thresholds, registered seeds, donor policy, steps, or LR.
2. Replace unchecked assumptions with explicit acceptance criteria and synthetic examples; only mark a contract closed when its text and test oracle agree.

## Q9. Implementation plus unit tests

**Verdict: conditional — recommend approval only after the corrected contract is frozen and the owner explicitly authorizes implementation. Not approval of the current draft as-is.**

**Evidence.** E:22 says code follows errata approval. V:291–316 requires a PM mode and PM tests. Runner:755–756 exposes only smoke/metric-smoke/train/p0-sanity and frozen/lora/both; the reviewed runner does not implement P/PA/M or the new decision function. Historical 54-test claims therefore cannot validate this protocol (S2:168–171). Moreover, all seven current metric test methods are inside a class skipped without local mT5 weights (Tests:13–23), including tests that are conceptually pure fixtures. A nominally green suite can otherwise omit the new contract's core proof.

Before implementation starts, the test oracles should include:

- typed decision precedence, missing-seed/no-pooled-label, null CI, PA path failure, small-N, every P/PA interaction, M unavailable versus assessed failure, and independent L flag preservation;
- complete-case seed averaging, paired document identity, >=2 positive seeds, exact strict/inclusive threshold boundaries, bootstrap reproducibility, heavy-tail edge cases, and separate endpoint availability;
- train-only M identities, contributor 9/10 and target 14/15 boundaries, arm/seed checkpoint identity, whole-matrix norm scaling, zero/non-finite handling, POS-only non-pass and GLOBAL non-rescue;
- P adapter absence, PA random-adapter step0, zero-LoRA equivalence, reproducible LoRA A/B initialization, 64-module inventory only where applicable, frozen encoder/base parameters, evaluation modes, and training-mode restoration;
- counter/deadline enforcement with fake clocks, debug rejection rules, partial artifact output, no aggregate headline before all registered inputs, and checkpoint replay/provenance.

One subtle parity requirement deserves explicit treatment: P0 **crops source token IDs before native encoding** (Runner:186–193). Encoding a full bidirectional source and then cropping hidden rows is not equivalent. P/PA step0 must not accidentally change this real/wrong assay when implementing caching. F/L already crop cached hidden rows (Runner:423–427); M intentionally uses a different full-real-K reference.

**Next steps (3):**
1. Freeze the contract and test expectations above, including the native crop and independent source/target length flags, then obtain explicit implementation-only approval.
2. Keep pure decision/statistics/budget/builder tests outside the local-weight skip; use tiny synthetic fixtures and mocked I/O. Retain local-model metric/mode tests separately and report skips explicitly.
3. After implementation, run the authorized unit/integration checks and inspect their evidence before proposing mechanics debug. Do not use unit-test approval as permission to run experiment training or evaluation.

## Q10. One-seed mechanics debug

**Verdict: conditional — potentially acceptable after implementation/tests and cap reconciliation, not approved by this consultation.**

**Evidence.** E:342–366 bounds seed and mechanical checks; E:434 reserves the three-seed gate. Current code/tests cannot yet demonstrate that the debug executor obeys those constraints. The full-run reporter and all-seed decision function must not treat the lone unregistered seed as a partial registered panel or bootstrap it into a headline. Positive mechanical checks are not evidence of L signal, P validity, or M validity.

Required debug artifact identity includes prereg/code/test commits, exact bounded config, seed 20261111, arm, actual update counts, controlled M probe count, timing/cap ledger, fixture versus real-probe provenance, mechanical assertions, and an explicit statement that no registered-seed outcomes or scientific pass/fail labels were produced. A separate approval record must be required for any later three-seed execution.

**Next steps (3):**
1. Supply passing PM contract tests and fake-clock/counter/debug-isolation tests, then reconcile the cap and seek explicit debug-only authorization.
2. Execute only the authorized bounded mechanics scope in a separate namespace; keep raw mechanical diagnostics from being promoted into scientific conclusions or a successful three-seed gate.
3. End at the debug report. The next gate may inspect mechanics, integrity, artifacts and timings—not choose a new seed/LR/donor/threshold based on preliminary outcomes.

## Q11. Three-seed execution versus B0-B proposal

**Verdict: agree — these must remain separate approvals; no automatic advancement is justified.**

**Evidence.** E:434 explicitly requires a separate three-seed gate; V:347–355 places execution and B0-B at separate stages. V:378–397 sets necessary, not sufficient, B0-B review conditions. The errata's new observational labels must carry through to those boundaries; the old REGIME_ERASES_SELECTIVITY name must not leave stale allow/deny logic.

A future three-seed authorization should require frozen corrected prereg/code/test hashes, successful relevant unit/integration checks, bounded mechanics evidence if authorized, complete manifests, cap feasibility/accounting, no metric/mode/leakage failure, and an explicit owner go/no-go. It is permission to collect the registered diagnostic, not a scientific success verdict.

Only after an authorized complete diagnostic could a separate B0-B **proposal** be considered: assessed P/PA validity; valid POS+NORM controls in both P and PA; L's POS+NORM pass; L copy+full signal; direction retained after removing the top three; no integrity failure; complete artifacts; and transparent excluded cohorts/tail flags. A headline alone is insufficient. A top-three share >.50 should remain the disclosed tail flag, not an invented new automatic scientific gate; the existing leave-top-three-out direction requirement for B0-B review remains.

**Next steps (2):**
1. Document separate owner approvals for implementation, bounded mechanics, registered three-seed execution, and any subsequent B0-B proposal/execution. Missing or exhausted evidence halts progression.
2. Preserve the bans and observational language in every generated report: no B0-B/B1/B2/Stage C approval, no P1, sealed test 163, and no reopening T5Gemma2 under D-108 STOP.

## Q12. Final disposition

**Verdict: conditional. Final recommendation: NARROW.**

**Evidence.** E:17–22 aims to make an existing bounded diagnostic executable rather than authorize a new experiment. The baseline and negative-control revisions are sufficiently constructive that STOP of the research direction is not supported. Conversely, the decision/missingness conflict and budget contradiction prevent CONTINUE or unconditional freeze. E:434 and R:314–334 preserve execution and downstream approval boundaries.

| Item | Disposition |
|---|---|
| v0.2.1 freeze | **Not as written.** Freeze only after the outcome-blind contract corrections above. |
| Implementation + unit tests | **Conditionally recommend**, following corrected freeze and explicit owner authorization. None performed in this review. |
| Mechanics debug | **Conditionally recommend later**, after tests, cap reconciliation, and explicit bounded authorization. None performed or approved here. |
| Registered three-seed run / Phase 6 execution | **Not approved.** Requires a separate gate and owner authorization. |
| B0-B | **Not approved.** A future favorable diagnostic can only support a separately reviewed proposal. |
| B1/B2/Stage C | **Not approved.** |
| P1 / test 163 | **No use; test 163 sealed.** |
| T5Gemma2 | **D-108 STOP remains closed.** |
| Maximum compute now | **Zero training/evaluation.** This consultation used read-only source inspection and the requested Git sync. |
| Future registered envelope, if separately authorized | No increase granted: **<=12 trained arm-seed units, <=1,200 total updates, <=2 hours shared wall-clock, six total threads, no GPU; debug/retries included; no automatic extension.** Nonzero four-arm debug plus all twelve registered units does not fit; reconcile before either is authorized. |

**Next steps (3):**
1. Resolve Must-fix ranks 1–5 and commit the corrected protocol without changing post-result scientific rules.
2. Obtain implementation-only authorization, implement and test, and return with complete mechanical/replay evidence and an arithmetically consistent cap statement.
3. Stop at each subsequent explicit approval gate. Do not infer Phase 6 or B0-B approval from this NARROW recommendation.

## Compact Q1–Q12 summary

| Question | Verdict | Bottom line |
|---|---|---|
| Q1 Total decision | disagree | Boolean fallback is not total over missing/error states; retain L flags. |
| Q2 P/PA | conditional | Correct separate baselines; finish scope, null handling and noncausal interpretation. |
| Q3 P gate | agree | Still weak; acceptable only as a sensitivity screen, not strong retention/learning. |
| Q4 M | conditional | Correct AND controls; finish cohort, norm, leakage and replay semantics. |
| Q5 Statistics | conditional | Core math correct; freeze cross-arm/seed completeness and exact numerical rules. |
| Q6 Debug protocol | conditional | Good isolation design; enforce executor, artifact and budget boundaries. |
| Q7 Cap/artifacts | disagree | Debug plus full run can be 16 units/1,220 updates, not 12/1,200. |
| Q8 Must-fix | agree | Five ranked operational contracts remain open. |
| Q9 Implementation/tests | conditional | Corrected freeze and explicit authorization first; pure tests must not skip. |
| Q10 Mechanics debug | conditional | Later bounded approval only after tests and budget reconciliation. |
| Q11 Three-seed/B0-B | agree | Distinct gates; a positive diagnostic never automatically approves B0-B. |
| Q12 Final | conditional | **NARROW; no execution approval.** |

## Incorrect premises to avoid

- A final `otherwise` is sufficient to reconcile NOT_ASSESSABLE, small-N and missing-seed semantics.
- The presence of independent L fields guarantees users see them; reports must explicitly show assessable positive L flags under validity headlines.
- .05 is substantial retention of the P0 effect, or a trained P/PA success has already been seen.
- PA random-adapter step0 plus a P/PA discordance proves an adapter-caused training loss.
- Whole-matrix norm matching makes M target-independent or on-manifold; train-only contributors alone prove the entire M pipeline leakage-free.
- >=10 contributors means >=15 analyzed targets; a per-arm common cohort necessarily matches all three seeds.
- Unavailable CI, missing seed or numerical failure is an observed negative scientific result.
- Historical 54 passing tests verify P/PA/M, or a model-skipped suite verifies pure protocol logic.
- Debug is free because its seed is unregistered, or “two hours from process start” automatically enforces a shared multi-process budget.
- An EXPLORATORY_L_SIGNAL headline, or this review, authorizes Phase 6 execution or B0-B.

**No scientific threshold, registered seed, donor policy, training step, or LR change after results is recommended. No training/evaluation or forbidden data access was performed.**