# Independent external review — C5 / D-084 rev2

## Review identity, basis, and limits

- **Reviewer:** OpenAI Sol 6.1 (`openai/gpt-6.1-sol`), independently completing this review; no subagents or additional LLM calls.
- **Date:** 2026-11-07 UTC.
- **Repository:** `mandutt/unigem`; review basis: synchronized `origin/main`.
- **Synchronization:** ran `git fetch origin`, then `git pull --ff-only origin main`; both exited 0; pull reported `Already up to date.`
- **Resulting HEAD and origin/main:** `e8b6367c1bd16b010318145587aaaedc14a77027`.
- Read **all 346 lines** of the rev2 review request, **all 368 lines** of the rev2 draft, and **all 278 lines** of the prior synthesis. The prior synthesis is historical evidence, not a substitute for inspecting the current proposal or artifacts.
- Inspected the existing audit and v1 verifier code, selector, saved audit JSON, strict selection artifacts, four checkpoint metric files, validation prediction metadata/URL spans, and saved error-analysis aggregates. Only validation prediction files were opened; no clean/full mixed-split corpus files or test-163 records were opened.
- Did **not** execute the old audit, tests, training, generation, or test evaluation. The old audit would both read mixed-split data and write an artifact. Numerical checks here were read-only aggregation of existing validation artifacts and elementary exact-binomial arithmetic.
- This report is the **only repository file written**. No production code, gate, decision record, selection artifact, or model was changed. This is advice, **not approval of a gate change**.

## Executive judgment

**Conditional support for the revised design direction; not ready for implementation approval as a fully specified decision protocol, and not ready for candidate/product approval.** URL-only 084a is the appropriate measurement baseline. Keep qualifier, unit, and alias reasoning in report-only 084b, including a narrow qualifier rule: dropping `오전` is loss of information, not merely repairing extraction. The architectural split is substantially better, but the proposed public API and single `status` field do not yet enforce it.

**2,586 is a defensible provisional review nominee under the stated point-screen/max-F1 rule, not a currently validated selection.** D-083 still has no eligible full-train checkpoint. If the expected URL-only results survive a complete, spec-faithful rescore and the other unchanged screens, 2,586 mechanically outranks 1,293 by F1. Its omission evidence is a reason to withhold approval and allow a human-review veto, not to quietly substitute another checkpoint or alter the gate. If “formal candidate” means certified, adequate, or approved, the correct answer today is **no candidate established**. These two statements are compatible.

Keep **1,940 gate-ineligible and human-exploratory**; its quality evidence merits investigation but cannot authorize an alias exception. Keep **pilot300 as the strict fallback/control, not a product approval**. Keep **test 163 sealed**. The sequence needs two freezes: measurement/selection/protocol specifications before rerunning or rating, then the final candidate/artifact freeze before any separately authorized future one-shot test. Completion of a checklist must not automatically release the test.

## Evidence index

References below use these short names; line numbers refer to this reviewed HEAD.

| Key | Document/artifact and relevant locations |
|---|---|
| **REQ** | `reports/EXTERNAL_REVIEW_C5_D084_REV2_2026-11-07.md`, especially L65–84 (strict/paired results), L128–187 (084a/b), L193–231 (candidate/human/test), L237–278 (R/Q definitions), L308–346 (limits/requirements). |
| **D** | `docs/D-084_verifier_v2_rev2_2026-11-07.md`, fully read; sections/line ranges cited below. |
| **SYN** | `reports/C5_D084_3AI_REVIEW_SYNTHESIS_2026-11-07.md`, fully read; L101–172 (baseline, roles, uncertainty, test), L176–238 (implementation defects/Must-fix). |
| **AUD-CODE** | `runner/c5_a1_verifier_v2_audit.py`: L28–48 (unconditional regex repair), L78–158 (matching), L162–221 (mixed-corpus loading/target audit), L223–272 (checkpoint variants/output). |
| **V1** | `eval/slot_verify.py`: L95–110 (NFKC, lowercase/comma stripping), L113–150 (extraction/offsets), L153–188 (uniqueness/report). |
| **SEL** | `reports/provenance/C5_a1/full_2ep/selection.json` and `selection_summary.json`; JSON keys `gates`, `selected_step`, `full_train_selected_step`, `fallback`, `candidates`. |
| **SELECTOR** | `runner/c5_a1_select.py`, L19–40 (four screens), L46–49 (max F1/tie rule), L75–81 (result/output). |
| **AUD-JSON** | `reports/provenance/C5_a1/full_2ep/verifier_v2_audit.json`; JSON paths `corpus`, `target_audit/excluded`, `target_audit/clean`, `checkpoints/{pilot300,0647,1293,1940,2586}`. These are old matcher results, **not** implemented 084a results. |
| **METRICS** | `reports/provenance/C5_a1/full_2ep/eval_step_{0647,1293,1940,2586}/eval.metrics.json`; validation metrics only. |
| **ERR** | `reports/provenance/C5_a1/full_2ep/error_analysis_1940_vs_2586.json`, `checkpoints/{1940,2586}` and `delta_1940_to_2586`; also `reports/C5_A1_error_analysis_2026-11-07.md`, L14–61 and L65–114. |
| **GATE** | `docs/gates.md`, L25 (G-C5), L28–46 (minimum sample/CP/INCONCLUSIVE). |
| **TRAIN-REPORT** | `reports/C5_A1_full_train_2ep_2026-11-07.md`, L5–13, L17–62, L64–79. |

### Three result layers that must not be conflated

| System | **D-083 strict, saved result** | **084a URL-only, expected only** | **Old generic matcher / alias variant**, not selection evidence |
|---|---:|---:|---:|
| pilot300 | 161/161 | 161/161 | 161/161 / 161/161 |
| 647 | 155/161 | 156/161 | 158/161 / 158/161 |
| 1,293 | 159/161 | 160/161 | 160/161 / 160/161 |
| 1,940 | 158/161 | 158/161 | 159/161 / 160/161 |
| 2,586 | 159/161 | 160/161 | 160/161 / 160/161 |

The middle column is D §3.4's hypothesis, **not a rescore performed in this review**. The right column is AUD-JSON's defective historical matcher; it must not be relabeled as finalized 084b results. New 084b outputs remain diagnostics only.

Confirmed strict state: `selected_step = null`; pilot300 fallback. Full training completed 2,586 steps / 2 epochs in 15,617.9 seconds (4 h 20 min 18 s), exit 0. The old generic matcher has five excluded-pair flips, not five proven false accepts. Its 902/1,617 numeric-unit collision count is an exposure statistic from the old mixed-corpus audit, not a calibrated error rate.

## R1–R8 decisions

**ID convention:** use the **request's eight R items**, not the draft's six-item table. D L354–355 currently uses R5 for human review and R6 for test, whereas REQ uses R5 for 1,940, R6 for human review, R7 for audit, and R8 for test. That cross-reference mismatch should be corrected before approval.

### R1 — 084a baseline: **conditional**

**Evidence.** URL-only is the right boundary (D §3, §4.1–4.3; REQ L128–187). V1 L99–103 demonstrably destroys URL case/comma distinctions. Repairing that and a demonstrable soft wrap changes measurement; removing a time qualifier changes what information is accepted. However, “source-attested” and “trailing sentence punctuation” are not executable definitions yet.

**Next steps.**
1. Retain URL-only; specify source-side attestation, ambiguity, delimiters, and punctuation treatment before implementation.
2. Freeze positive/negative fixtures, including the actual 02742 source/summary spans and strict URL identity cases, then rescore every saved validation output, not only old failures.

### R2 — 084b numeric unit: **agree**

**Evidence.** D §4.2 explicitly prohibits automatic grounding and selection use. AUD-JSON records 902 collision documents and five generic excluded flips; neither establishes that bare numbers retain the correct unit, entity, or event. A unique unit type still does not establish a semantic relationship.

**Next steps.**
1. Emit `unit_dropped` candidates/collisions separately, preserving typed values and all occurrence spans.
2. Make enabling/disabling these diagnostics leave 084a matches, counts, eligibility, and ranking unchanged; label any hypothetical policy ablation report-only.

### R3 — 084b alias: **agree**

**Evidence.** Default off is correct (D §4.3). AUD-CODE L132–145 bypasses uniqueness when alias is enabled, does not require source unit `명`, and checks a substring window in a different coordinate space after repair. ERR confirms 04709 already preserves `18명`; its extra bare `18` is a contextual question, not a missing-counter typo established by regex.

**Next steps.**
1. Keep automatic alias matching disabled, including after adjudication of this single example; do not use it to make 1,940 eligible.
2. If studied separately, annotate closed-table candidates with explicit person unit, entity/event/time scope, original offsets, and human dispositions for every firing; do not feed those dispositions into 084a selection.

### R4 — 2,586 provisional candidate: **conditional**

**Evidence.** Under D §5.2's point-screen/max-F1 rule, the expected eligible full-train set is 1,293 and 2,586; their F1 gap is **0.003035**, favoring 2,586. Its F1 advantage over pilot300 has CI crossing zero (REQ L83), preservation is .418823 versus pilot .45583, and ERR shows 11 slot-free documents, nine with target slots. No corrected audit or human judgment yet supports approval.

**Next steps.**
1. Call 2,586 a **conditional review nominee** until the full corrected audit passes the frozen screens; keep D-083 selected null.
2. Predeclare that failed audit, adverse adequacy review, or unresolved evidence means no approved candidate/hold; do not choose another arm because it looks better in the human ratings.

### R5 — 1,940 gate-ineligible, human exploratory: **agree**

**Evidence.** Strict 158/161 is confirmed by SEL; expected URL-only remains 158/161 (D L134–140). Its remaining strict failures are 03978, 04709, and 04951 (AUD-JSON). URL repair does not solve qualifier omission, contextual bare `18`, or the unsupported percentages. F1 .682278 and preservation .476096 justify a quality comparator, not a rule exception.

**Next steps.**
1. Preserve its exploratory human arm and report paired quality contrasts without eligibility language.
2. Keep qualifier/alias adjudication separate; no need to settle or adopt an alias before proceeding with 084a.

### R6 — human-50 four-arm design: **conditional**

**Evidence.** D §5.3 correctly uses the same documents, blinding, two raters, and separate strata. It still lacks exact sample allocation, an operational rubric, primary endpoint/contrast, disagreement handling, and decision consequences. Fifty documents × four arms × two raters is **400 output ratings**, not 50 independent judgments; effective document n remains at most 50.

**Next steps.**
1. Freeze the primary contrast as **2,586 versus pilot300**, with adequacy/essential-fact coverage and unsupported content evaluated separately; 1,293 sensitivity and all 1,940 comparisons remain exploratory.
2. Predeclare strata, sample IDs/seed, blind arm mapping/order, source-grounded rubric, third-rater arbitration, and stop/hold criteria before ratings.
3. Budget the actual rating workload and report stratum-specific paired results; use document/article-family units, not 400 ratings, for uncertainty.

### R7 — stronger spec-faithful audit DoD: **conditional**

**Evidence.** D §6/§8 adds most right categories, but an item such as “negative tests” does not yet specify pass/fail semantics. URL strictness can turn old passes into failures. The draft has one `status` without a rule for combining point-screen eligibility and CP uncertainty; the public booleans could permit equivalence policies in a selection-bearing report.

**Next steps.**
1. Add the concrete URL, isolation, attribution, typed-key, and diagnostic-invariance requirements below, with complete counts and input/code/spec hashes.
2. Require adjudication of **all newly observed changed decisions**, not merely the five historical generic flips; retain reversed decisions and unresolved cases.
3. Specify the selection/evidence status truth table and preserve all four existing D-083 screen thresholds explicitly.

### R8 — test 163 sealed / later separately authorized one-shot: **agree**

**Evidence.** REQ §5.3 and D §5.4 properly distinguish A0 D-080 usage, prior corpus-wide source/target audit exposure, and no A1 predictive usage. Therefore it is sealed for A1, not a historically untouched holdout. D L342 already requires separate approval; the earlier flow should say so equally clearly.

**Next steps.**
1. Keep it unopened now and enforce allowlisted audit inputs without first loading mixed-split files.
2. Make any future release a separate explicit authorization after acceptable audit/human evidence and final artifact freeze; predefine failure/inconclusive handling and no retuning against that one-shot result.

## Q1–Q14 responses

### Q1 — measurement versus equivalence separation: **conditional**

**Evidence.** D L147–178 states the correct conceptual separation. But `VerifierV2Policy` (L283–310) exposes equivalence booleans through the same `verify_summary_v2()` that returns `grounded`, and the output uses generic `v2_grounded`. The prose alone cannot prevent a downstream consumer from selecting on a permissive variant.

**Next steps.**
1. Return an immutable, explicitly named **084a baseline result** plus a separate diagnostic report; use an analysis configuration rather than flags that can silently change the selection result.
2. Have the selection reader accept only the frozen 084a policy/spec hash and reject 084b-derived inputs. Require diagnostic-toggle invariance tests.

### Q2 — URL attestation, fine.fss., and negative tests sufficient: **disagree**

**Evidence.** D L96–106/L238–243 gives desirable examples but not a deterministic attestation algorithm. AUD-CODE L28–48 joins syntactically matching text without checking source support. Both source and summary may contain the same wrap; demanding an already contiguous source URL would fail the intended golden case, while using the model's completed URL to certify the source would be circular. `site` can also be a normal Latin word; a regex alone cannot establish a wrap. “Trailing punctuation” can itself be a valid path/query character.

**Next steps.**
1. Build source URL evidence deterministically **before looking at the summary**, with exact original source spans, boundary/continuation rules, and an ambiguity outcome. Define how a wrapped source span itself establishes support; no guessed suffix, network lookup, or prediction-assisted source repair.
2. Require fixtures for both-side wrap, wrapped-source/contiguous-summary and the reverse, indentation/CRLF, unrelated next-line Latin words, multiple continuations, case/query/comma/escape/fragment differences, and ambiguous terminal punctuation. Preserve raw URL text rather than inheriting global NFKC/lowercase canonicalization.
3. Keep `fine.fss.` unresolved; an unresolved **material URL mismatch** must not be accepted by falling back to a truncated v1 prefix. Do not confuse report-only 084b ambiguity with an automatic 084a failure.

### Q3 — accept 1,940 at expected 158/161 and exploratory role: **agree**

**Evidence.** AUD-JSON's strict failure IDs and ERR's failure descriptions support D §3.4's derivation. Validation 02742 already passes v1 for 1,940 because its prediction is also wrapped; a symmetric repair should not give it an extra grounded document. Its old generic 159 and alias 160 are different policy scenarios.

**Next steps.**
1. Retain the expected 158/161 as provisional until every document is rescored; explicitly preserve the other three failure reasons.
2. Keep the human-exploratory role; do not delay the measurement audit for an alias policy and do not grant an eligibility exception.

### Q4 — keep 084b report-only and exclude the qualifier from 084a: **agree**

**Evidence.** Agree with report-only and **do not include the qualifier**. `오전 9시30분` → `9시30분` removes disambiguation even without an observed competing afternoon time (D §4.1; ERR 03978). The seven old collision documents are not a proof that qualifier loss is harmless elsewhere. A narrow rule can be studied without redefining the measurement baseline.

**Next steps.**
1. Keep qualifier diagnostics under 084b and preserve the 084a new-slot result.
2. In a separate ablation, distinguish exact bare-time matches, dropped qualifiers, newly added qualifiers, competing qualifiers, and unresolved scope. Diagnostic ambiguity must not override a genuine baseline exact match.

### Q5 — 2,586 versus no candidate because of over-compression: **conditional**

**Evidence.** Nomination follows the stated selector; approval does not. ERR's slot-free histogram is **2 with target 0, 3 with target 1, 1 with target 3, 5 with target 4**. Thus six omit all of at least three target slots. Nonvacuous reporting removes empty-slot passes but does not detect a summary retaining one number and omitting all other essential facts. The F1 CI does not demonstrate superiority or inferiority to pilot300.

**Next steps.**
1. Use distinct labels: strict selection null; provisional 084a review nominee 2,586; approved candidate none.
2. Allow an adequacy veto/hold under a frozen human protocol. If it fails, report no approved candidate rather than retroactively adding a preservation cutoff or selecting a human winner.

### Q6 — 1,293 as sensitivity arm versus formal candidate: **agree**

**Evidence.** As an arm it is important: expected 160/161, F1 .665946, preservation .457055, slot-free 8, compared with 2,586's .668982/.418823/11 (METRICS). The .003035 F1 gap does not establish a practically meaningful advantage, but uncertainty alone does not invalidate the already stated point-estimate ranking rule.

**Next steps.**
1. Keep 1,293 in the common-document human comparison and calculate the existing-output paired F1/coverage contrast with 2,586.
2. Do not promote it post hoc. If audit results change the eligible set, rerun the frozen selector; if a new adequacy-based selection policy is desired later, register it as a new outcome-informed policy, not a correction of D-083.

### Q7 — four arms and decision-primary; GLM quality-primary proposal: **conditional**

**Evidence.** The four arms answer distinct questions (D §5.3; SYN L139–148): fallback, earlier eligible sensitivity, quality-exploratory comparator, and the conditional policy nominee. 1,940's exploratory quality comparison is valuable, but making it decision-primary would conflate quality and eligibility.

**Next steps.**
1. Name the **endpoint and contrast**, not only the primary arm: paired source-grounded adequacy for 2,586 versus pilot300, with factuality/critical-omission safety outcomes separately reported.
2. Give 1,940 a prespecified secondary quality analysis against both pilot and 2,586, clearly exploratory and incapable of making it eligible.
3. Separate targeted challenge findings from randomly sampled validation findings; do not present an unweighted pooled mean/CI as representative of val or a wider population.

### Q8 — nonvacuous, coverage, CP95, INCONCLUSIVE sufficient: **disagree**

**Evidence.** The additions are necessary, not sufficient. D §5.2 does not say whether CP controls eligibility or only evidential certification; §6.4 offers only one status. GATE already requires CP and minimum slot counts, while source coverage is presently a reference metric. Direct arithmetic gives two-sided CP95 lower bounds **.965881 for 160/161** and **.977348 for 161/161**: even pilot300 cannot certify a .99 document-level population rate with this n. The all-success minimum is 368 documents under that interval convention. Slot observations are also clustered within documents/article families.

**Next steps.**
1. Preserve and explicitly list the existing point screens: grounded ≥.99, new-slot micro ≤.01, EOS ≥.95, repeated4 ≤.06. Separately report screen eligibility and evidence status; if CI straddles a relevant bound or a required denominator is missing/insufficient, evidence is INCONCLUSIVE, not certified PASS. Define one-/two-sided CP and its unit in advance; use two-sided 95% if retaining the numbers above.
2. Freeze definitions: nonvacuous denominator = documents with ≥1 extracted summary slot; zero such documents yields undefined/INCONCLUSIVE, not 100%. Report source coverage, target-slot recall, essential-fact adequacy, and target≥3/summary=0 counts separately. The old summary-slot totals 837/877/854/860/762 are not automatically the corrected denominators.
3. Specify human stop/hold thresholds before rating. My conservative proposal, **not an approved gate**, is zero confirmed critical unsupported/inverted assertions and a zero-margin paired adequacy non-inferiority requirement versus pilot (0–4 rubric; lower paired 95% bound ≥0 in the random stratum). A confirmed critical error or adequacy interval wholly below zero stops; an adequacy interval spanning zero holds as INCONCLUSIVE. If a nonzero margin is preferred, justify it by user harm/cost before ratings, not by these checkpoint scores. Do not invent a source-preservation ≥.465 gate from a descriptive target average.

These human thresholds are deliberately conservative screening recommendations, not population safety guarantees. A policy choosing CI-certified .99 grounding as a prerequisite would have **no certified candidate at n=161**; it cannot simultaneously call 2,586 certified merely because its point rate is 160/161. CP intervals on the reused validation set remain descriptive/conditional, not protection against model selection or leakage.

### Q9 — spec-faithful audit DoD and missing Must-fix: **conditional**

**Evidence.** D §6 and §8 cover the principal historical defects, but original offsets, extraction interactions, baseline/diagnostic invariance, changed-pass review, and strict output validation remain unspecified. V1 normalizes text before extraction; AUD-CODE deduplicates offset-bearing dataclasses and then maps only by canonical string. “Distinct typed slot” needs an actual identity definition, not a label.

**Next steps.**
1. Use `(kind, canonical value)` identities with occurrences recorded separately. Extract URLs from raw text with reversible original-span mappings; exclude recognized URL spans from other extractors so query digits/path fragments do not become spurious slots. Keep unrelated v1 non-URL semantics fixed except explicitly documented consequences of correct URL spans.
2. Materialize allowlisted train/val/excluded inputs before this audit; never read full/clean mixed-split files and filter afterward. Validate exact ID sets, disjointness, uniqueness, completeness, schema, and prediction hashes; missing/malformed rows must fail closed, not change n.
3. Rescore all five systems and all 383 excluded pairs under separately labeled policies; record raw spans, repair reasons, both-direction flips, new/missing/unresolved slots, typed denominators, and policy attribution. Reject selection input not matching frozen 084a. Include deterministic repeatability and the baseline-invariance checks.

### Q10 — 383 audit, five flips, two raters, zero false accepts: **conditional**

**Evidence.** AUD-JSON has exactly five old **generic** excluded flips. They are not necessarily the flips of corrected URL-only 084a; strict canonicalization may expose different cases, and 084b diagnostics should not accept anything. Blind two-rater review plus arbitration is appropriate. “Zero confirmed false accepts + zero unresolved auto-accepts” is realistic as a release rule for a narrow clause, not as a population estimate. Even zero errors among five would have a two-sided CP95 error upper bound of about **52.2%**, before considering the selected nature of the sample.

**Next steps.**
1. Run all 383 through the corrected audit and adjudicate every new decision change/accept, with policy-specific denominators. Track the historical five separately and review changed validation decisions as well.
2. First let two raters independently judge the source/summary relationship without checkpoint, desired outcome, or matcher rationale; then reveal rule traces for diagnostic coding. Use a third arbitrator; unresolved material support stays unaccepted.
3. If any enabled 084a clause produces a confirmed false accept, narrow/remove it and rerun its complete suite/pool before reconsideration. Do not require an 084b report-only diagnostic to be semantically “accepted,” and do not silently add excluded pairs to training/selection data.

### Q11 — test conditions and order: **conditional**

**Evidence.** D §5.4's outline is sensible, but it freezes policy only after selection/human review and is not explicit there about satisfactory results or a separate release approval. D §9 does mention separate approval. The current wording could allow “human 50 completed,” even with adverse findings, to unlock the test.

**Next steps.**
1. Before implementation/rescoring, freeze the URL spec, policy/hash contract, point-screen/evidence rules, adjudication criteria, and human protocol. After audit, freeze the deterministic nominee and blind arm identities before human ratings; an invalidated nominee requires a documented hold/new protocol, not an automatic winner swap.
2. After acceptable evidence, freeze the final candidate/hash, verifier and decode policy, evaluation endpoints, and outcomes/stop rules; require **separate explicit future authorization** for any one-shot test. Failed or inconclusive prerequisites do not unlock it.
3. Retain the A0/exposure/A1-predictive use-log distinctions and prohibit retuning on the eventual result. This review does not request or authorize opening it.

### Q12 — Scope/DoD/API/order and implementation prerequisites: **conditional**

**Evidence.** D §2 excludes human rating itself while §9 includes it as a later dependency; that is manageable if approval scopes are explicit. The API conflates analysis options and a selection-bearing result; `selection_v2.json` lacks exact count/denominator semantics and full input/model/code provenance. D §5.2 also names only the grounding threshold, relying on readers to carry forward the other three screens.

**Next steps.**
1. Adopt the seven Must-fix items below as explicit acceptance criteria, with separate permissions for measurement implementation, accepting its evidence, the human study, and any eventual test release.
2. Extend the result contract with baseline policy ID/spec/code hashes, prediction/checkpoint/manifest hashes, raw counts and denominators, original-span evidence, screen eligibility, evidence status/reasons, provisional selected step, and separate diagnostic attribution. Serialize undefined metrics explicitly, not as successful defaults.
3. Make outputs versioned/separate and refuse accidental overwrites of D-083 files. Keep production `eval/slot_verify.py` byte-identical; do not modify production selection under this consultation.

### Q13 — prior review concerns actually resolved: **conditional**

**Evidence.** The main **design-level** concerns are addressed: URL-only baseline, report-only equivalence, roles separated, provisional figures, strict history preserved, test sealed. The code defects themselves are not fixed—D says so, and AUD-CODE still exhibits them. SYN's mixed “URL-only/generic” table (L115–121) is corrected conceptually by D §3.4, but must not be treated as new empirical verification.

**Next steps.**
1. Publish a traceability checklist separating **specified in rev2 / implemented / verified** for each historical concern; only the first state currently applies to the new module.
2. Remove the overstatements below and replace derived expected results with observed per-policy results only after the corrected audit is actually run.

### Q14 — factual errors, overstatement, and omissions: **conditional**

**Evidence.** I accept the core strict numbers and history, but the following corrections are needed:

1. **Not a proven upper bound.** REQ L320 and D L62 call all existing v2 numbers an “optimistic upper bound.” URL canonicalization may be permissive, but occurrence-count uniqueness can falsely reject and alias mode can remove generic matches (AUD-CODE L132–145). No monotonicity theorem makes these outputs an upper bound on a faithful implementation. Say **unvalidated, potentially biased in either direction, policy-specific exploratory estimates**.
2. **Absence of superiority evidence is not evidence of inferiority/equality.** D L362 says 2,586 “is not superior” to pilot300. The supported claim is **superiority has not been established**; its F1 CI crosses zero. Quality/omission concerns are real but distinct.
3. **“No test” needs a qualifier.** AUD-JSON `scope` and the old audit report say no test, but AUD-CODE L163–203 reads clean 1,617 source/target records, including test records, and full 2,000. Rev2 properly acknowledges this exposure; label the old scope claim as **no A1 predictive test evaluation**, not no test-data access.
4. **The expected table is not an exhaustive delta proof.** Derivation from old failure IDs cannot exclude new failures among old passes after case/comma/escape strictness, changed URL spans, or ambiguity handling. Every expected grounded count, including pilot300's 161, remains provisional.
5. **Five is a historical generic flip count, not an 084a truth count.** REQ/D DoD wording must not hard-code those five as the complete corrected flip set or call 5/383 a false-accept rate.
6. **R IDs differ between request and draft.** The eight-item request mapping should govern this review and be reconciled in the decision document.
7. **“1,940 has best preservation” needs scope.** It is highest among the proposed four human arms, but 647 has .487288 versus 1,940's .476096. It is not the highest of every full-train checkpoint; 647 separately fails the repetition/grounding screens.
8. **Metric naming can overclaim.** Current `slot_preservation` is source-slot coverage (V1 L175), not target-slot recall, essential-fact coverage, or semantic adequacy. A clean-corpus zero-flip result can document regression behavior, but the v1-clean construction does not validate false-accept control.
9. **Human effort/independence and approval consequences are omitted.** Four arms/two raters yields 400 ratings, with shared-document/article dependence. No human endpoint, margin, hold criterion, or stopping rule is yet executable.

**Next steps.**
1. Correct the wording/ID/provenance issues before the implementation specification is approved; keep the strict, expected 084a, and old generic/alias tables separate.
2. Add a machine-readable distinction between observations, derived expectations, unadjudicated policy diagnostics, and decisions. Do not advertise the audit rewrite or human study as already completed.

## Top Must-fix items — maximum seven, in priority order

These are requested changes for the project to consider later; this review does not perform or approve them.

1. **Enforce the selection boundary in the API and artifact reader.** Separate immutable 084a results from 084b diagnostics; pin the accepted policy/spec hash; reject permissive selection inputs. Prove diagnostic-toggle invariance of matches/counts/eligibility/ranking. Replace ambiguous `v2_grounded` with explicit baseline naming.
2. **Finish the executable URL specification before coding it.** Define source-only attestation, both-side wrap handling, delimiter/punctuation ambiguity, raw versus normalized offsets, and URL identity preservation. Freeze full-span goldens and challenging negatives; retain fine.fss. unresolved and 04951's 2.3%/2.2% unsupported. Recheck all old passes as well as failures.
3. **Enforce data isolation and reproducibility.** Use pre-materialized train/val/excluded allowlists, never mixed-corpus load-then-filter; fail on duplicate/missing/unexpected prediction IDs or bad schemas. Record input/prediction/model/spec/code hashes and exact denominators. Preserve v1 and strict artifacts byte-for-byte; write only new versioned audit/selection artifacts when separately authorized.
4. **Resolve screen eligibility versus statistical evidence versus approval.** List all four unchanged point screens, define nonvacuous/coverage/target recall counts, CP interval convention and units, and a PASS/FAIL/INCONCLUSIVE truth table. Point-screen eligibility may nominate a review candidate; it is not a CP-certified .99 rate or product approval. Freeze human adequacy/critical-error stop and hold criteria without retroactively changing D-083.
5. **Adjudicate the corrected policy's changes, not a fixed historical five.** Audit all 383 and all saved validation outputs; review newly accepted, newly rejected, and materially unresolved cases by policy, with blind two-rater judgments and arbitration. Zero confirmed false accepts/zero unresolved auto-accepts is a clause-release condition, not a population claim. Narrow a faulty enabled clause rather than accepting exceptions.
6. **Freeze an executable human-50 protocol.** Same 50 unique val documents, four arms, paired 2,586-versus-pilot primary, 1,293 sensitivity and 1,940 exploratory; defined random/targeted allocation, article-family handling, rubric/endpoint, blinding/order, arbitration, margin and uncertainty analysis. No automatic arm substitution; adverse/inconclusive results permit no approved candidate. Budget 400 ratings.
7. **Repair document/provenance and approval sequencing.** Reconcile R IDs, remove “upper bound”/“not superior” overstatements, qualify historical test exposure, and keep expected counts hypothetical. Freeze measurement/selection/study rules before execution, nominee before ratings, final artifacts afterward. Human completion alone never unlocks the test; require satisfactory evidence and a separate future release authorization.

## Additional experiments — maximum five; proposed, not executed

All use existing P0 train/validation/excluded material or synthetic fixtures. **No test-163 access, P1 data, training, generation, or additional LLM review is proposed.** Costs are planning estimates, not measured runs or commitments.

| Priority | Experiment and question | Outputs / safeguards | Expected incremental cost |
|---|---|---|---|
| 1 | **Synthetic/golden URL and API-isolation regression suite.** Does the implementation preserve URI identity, fail closed on material ambiguous repairs, and keep 084b out of baseline selection? | Both-side/asymmetric wraps, grammar/boundary/terminal-punctuation negatives, case/comma/escape/fragment cases, original-span checks, typed overlaps, and diagnostic invariance; no fetching URLs. | About **2–4 engineer-hours**, seconds to a few CPU minutes once implemented. |
| 2 | **Corrected policy-separated rescore/ablation.** Which changes really come from URL repair versus qualifier/unit/alias diagnostics? | Five systems × 161 saved outputs (**805 validation cases**), allowlisted train/val inputs plus 383 excluded pairs; independent clause attribution and cumulative hypothetical ablations labeled report-only. Review both-direction flips; freeze hashes before scoring. | About **2–4 engineer-hours** after the core module; likely **under 15 CPU minutes**, no model inference. |
| 3 | **Blind adjudication of every changed support decision.** Are corrected 084a accepts defensible, and what were the five old generic flips? | Two raters, third arbitration, source-grounded labels before rule explanations; separate policy buckets and unresolved outcomes. No reintroduction of excluded data into selection/training. | If ≤25 changed pairs, roughly **2–4 total rater-hours** plus **0.5–1 arbitration/administration hour**; expand budget transparently if the changed set is larger. |
| 4 | **Preregistered four-arm human-50 adequacy study.** Is 2,586's apparent omission drift decision-relevant, and how do 1,293/1,940 compare? | Same 50 docs, separate targeted/random results; source-first essential-fact rubric, independent factuality and omission outcomes; 2,586-versus-pilot primary, no post-hoc arm promotion. | **400 ratings**: around **10–20 total rater-hours** at 1.5–3 minutes/output, plus **2–4 hours** for protocol, arbitration, and analysis. Source-reading reuse may reduce effort; do not assume the old 2–3-hour estimate covers this design. |
| 5 | **Existing-output paired and leakage sensitivity analysis.** Is the tiny 2,586–1,293 F1 difference stable, and do omission conclusions depend on overlap strata? | Paired F1/target-slot recall/adequacy summaries, report the known 16/161 train-article-prefix overlap separately, and use document/article-family resampling where supported by existing metadata. No data-driven selection-rule change. | About **1–2 analyst-hours**, usually **under 10 CPU minutes**; remains exploratory on reused validation data. |

For the human study, one workable protocol to finalize is a **disjoint targeted subset of at most 20 plus at least 30 randomly sampled remaining documents**, while retaining the same 50 for all arms. Targeted membership must be fixed from known failure/omission criteria, not chosen after new human scores. This allocation is a proposal, not an already approved design; alternative allocations need the same prespecification and separate reporting. Fifty paired documents do not support a 99% population safety claim, regardless of the number of arms or ratings.

## Verification and immutable references

Read-only checks confirmed:

- Four full-train validation files each contain **161 rows and 161 unique IDs**; pilot300 likewise has 161/161. Full set equality remains a required implementation audit check, not something inferred from equal cardinalities.
- Saved 02742 prediction URL spans are contiguous for 647/1,293/2,586 and wrapped as `http://coronamap.\nsite` for 1,940, consistent with the draft's golden-pair motivation.
- Saved strict metric and selection JSON agree on the stated scores, gate thresholds, no selected full-train step, and pilot300 fallback.
- ERR independently confirms the 2,586 slot-free target-slot histogram and strict nonvacuous **148/150**; 1,940 strict nonvacuous is **154/157**. Corrected nonvacuous counts must be recomputed, not copied.
- Exact-binomial arithmetic confirmed the CP figures cited above. These are arithmetic checks, not fresh evidence of model performance.

Baseline SHA256 values recorded before writing this report:

| File | SHA256 |
|---|---|
| `eval/slot_verify.py` | `a262cee0cd25307a74f3a87995624e2999b47daed9294000f036d27ea1869d03` |
| `reports/provenance/C5_a1/full_2ep/selection.json` | `1aeda42dd549775e4f0a827fea3d3dc60e3200bdad79edebf07e1202fefdb470` |
| `reports/provenance/C5_a1/full_2ep/selection_summary.json` | `00aefe22809ea6dee9114f2d3c592b7ab570b299210ddd9c06c035972845cc04` |

## Final recommendation

Adopt the **direction**, not the unverified conclusions: finish a precisely specified URL-only 084a, enforce report-only 084b by construction, preserve D-083, and perform a complete isolated audit with per-policy adjudication. Treat 2,586 as a conditional review nominee only; retain 1,293 as sensitivity and 1,940 as an important but gate-ineligible quality comparator. A failed audit or unsatisfactory/inconclusive adequacy study should yield **no approved candidate**, not a new exception or a human-score-selected substitute. Nothing in this review approves a gate change or product promotion.

Keep test 163 sealed. Resolve the status/CP semantics, executable URL evidence rules, input isolation, and human study decision criteria before implementing the proposed decision path. Freeze specifications before measurement and the candidate/arm mapping before ratings; freeze final artifacts only after acceptable evidence. Any later one-shot A1 test must be separately authorized, explicitly acknowledge A0 and historical corpus exposure, and have prespecified no-retuning/stop rules. No such test access is needed for the work recommended here.