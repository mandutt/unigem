# Independent review — C5 A1 full train and verifier normalization

**Reviewer:** Sol 6.1 (`openai/gpt-6.1-sol`), independent external review

**Date:** 2026-11-07 UTC

**Repository / review basis:** `mandutt/unigem`, current `origin/main`

**Reviewed HEAD:** `5694cc7fbe0d371f0b4800830037fa36269e44c3`

## Scope, synchronization, and limitations

I ran `git fetch origin`, then `git pull --ff-only origin main`. Both succeeded; the pull reported “Already up to date.” Local HEAD and `origin/main` both resolved to the commit above. The platform checkout remains on its existing workspace branch, `hoplite/selinous-9d030988`; I did not switch branches.

I read **all 350 lines** of `reports/EXTERNAL_REVIEW_C5_A1_FULLTRAIN_2026-11-07.md`, in two chunks, and inspected the result reports, selection JSON, all four checkpoint metric files, validation prediction artifacts, error-analysis JSON, relevant runner/verifier code, existing tests, and recorded decisions. I did not use prior model review answers or their synthesis as a substitute for independent analysis, call subagents or additional models, run training or generation, open/evaluate test 163, or use P1 data. The sole working-tree write for this consultation is this report.

**Important limitation:** `data/external/f5_pairs_v3_clean.jsonl` is absent in this checkout. The error-analysis JSON contains extracted source slots and prediction/target prefixes, but not complete source passages. Full validation predictions are available and were inspected for the disputed cases. Thus I can assess the proposed rules and the saved extraction evidence, but cannot complete source-context adjudication of the three normalization candidates. Their status remains **candidate**, not officially corrected error. I accept the execution totals supplied in the request; I did not rerun training or inspect model weights.

Read-only verification performed: all four full-train prediction files contain 161 unique IDs and match the validation ID manifest; the existing slot-verifier unit suite passed **11/11** using bytecode-disabled Python. Small in-memory verifier probes reproduced the three format mismatches and an existing URL false-equivalence problem described below. No runner/model test or model evaluation was executed.

## Executive recommendation

**Do not rewrite the D-083 outcome.** Full train completed successfully, but `selected_step = null`; no full-train checkpoint is eligible under the recorded strict verifier and gates. Preserve **pilot300 as the strict fallback**, not as an already approved product. In a separately labeled exploratory human comparison, use **1,940 as primary**, with pilot300 as the reference and 2,586 as the compression comparator.

**A narrowly specified verifier v2 is legitimate; blanket equivalence is not.** Repair unambiguous URL wrapping and prose delimiters. Treat AM/PM omission as possible supported weakening with a separately recorded qualifier loss, not lossless equality. Permit number/unit aliases only when the unit, entity, scope, and quantity are unambiguous. Prepare an explicit **proposed D-084** before new scoring/adjudication. It cannot make already-observed evidence prospectively independent, and no gate change is approved by this review. Keep test 163 sealed until verifier audit, human review, and candidate/protocol freeze are complete.

## Evidence index

Paths below are relative to the repository; line references refer to the reviewed HEAD.

| Key | Evidence |
|---|---|
| R | `reports/EXTERNAL_REVIEW_C5_A1_FULLTRAIN_2026-11-07.md`, especially §§1.3–5 and §8; read in full |
| F | `reports/C5_A1_full_train_2ep_2026-11-07.md`, lines 15–79: metrics, selection, paired comparisons, limitations |
| A | `reports/C5_A1_error_analysis_2026-11-07.md`, §§1–4: error categories and compression drift |
| J | `reports/provenance/C5_a1/full_2ep/error_analysis_1940_vs_2586.json`: `checkpoints.1940`, `checkpoints.2586`, and `delta_1940_to_2586` |
| S | `reports/provenance/C5_a1/full_2ep/selection.json` and `selection_summary.json`; `runner/c5_a1_select.py:19–49,53–77` |
| M | `reports/provenance/C5_a1/full_2ep/eval_step_{0647,1293,1940,2586}/eval.metrics.json` and corresponding `eval.jsonl` |
| P | `reports/provenance/C5_a1/pilot300_val161/metrics.json` and `predictions.jsonl`; prefix/bare context in `reports/C5_A1_bare_val161_2026-11-06.md` |
| V | `eval/slot_verify.py:58–110,113–188`: extraction, canonicalization, deduplication, and verification |
| L | `runner/c5_a1_lora.py:97–100,169–174,221–339,343–421`: order, labels, training/evaluation, and checkpoint selection inputs |
| B | `runner/c5_a1_eval_batch.py:55–115`: batch generation, padded generation lengths, and metrics |
| T | `eval/tests/test_slot_verify.py`; `eval/tests/test_a1_runner.py` (the latter tests epoch ordering, not verifier v2) |
| D | `docs/decisions.md`, rows **D-080** and **D-083**; `docs/gates.md:25–42` |
| U | [RFC 3986 §6.2.2.1](https://www.rfc-editor.org/rfc/rfc3986.html#section-6.2.2.1): scheme/host case-insensitivity does not imply case-insensitive path/query components |

### Results that remain strict D-083 results

| System | char F1 | Grounded documents | New slots | Slot-free documents | Status |
|---|---:|---:|---:|---:|---|
| pilot300 | 0.657580 | 161/161 | 0 | 6 | Strict fallback; not product approval |
| 647 | 0.669853 | 155/161 | 6 | 2 | Ineligible; grounded and repetition fail |
| 1,293 | 0.665946 | 159/161 | 2 | 8 | Ineligible |
| 1,940 | 0.682278 | 158/161 | 4 | 4 | Ineligible; primary exploratory human-review candidate |
| 2,586 | 0.668982 | 159/161 | 3 | 11 | Ineligible; secondary exploratory comparator |

Sources: R §2; S; M; J. A hypothetical v2 result of **160/161 = 0.993789** is not a result in this table. It requires successful, general-rule adjudication and checking for additional changes across the entire evaluation set. Even that hypothetical result leaves the genuine `04951` hallucination intact.

## D1–D5: decisions

### D1 — Verifier v2 normalization

**Verdict: conditional.** Approve the direction of a conservative audit, not a blanket “URL + AM/PM + unit are all equivalent” policy.

**Evidence:** V extracts a URL only until whitespace, so canonicalization cannot recover a hostname suffix that was never extracted. J records source value `http://coronamap.` versus prediction `http://coronamap.site`, supporting R's wrapping explanation. The time and unit cases differ: `오전` carries information, and `18` is only a person count when context establishes it. V currently compares sets of canonical strings, without entity/relation binding. A numeric match alone cannot establish a true proposition.

**Next steps:**
1. Specify the allowlist and reject/ambiguity rules in Q1–Q3, with raw-span provenance and distinct labels for formatting repair, qualifier loss, unit inference, and unsupported content.
2. Have humans inspect complete validation sources for the three candidates; do not automatically mark them correct from the abbreviated artifact.
3. Version and audit v2 under proposed D-084, leaving v1 code/results and D-083 selection unchanged.

### D2 — Candidate versus strict fallback

**Verdict: conditional.** Keep pilot300 as the D-083 fallback **and** nominate 1,940 for exploratory human review. These are different decisions, not competing labels for the same status.

**Evidence:** S explicitly records no selected full-train checkpoint. D-083 requires safety eligibility before maximizing F1. Yet R §2 reports a paired 1,940–pilot300 F1 difference of +0.024698, nominal bootstrap CI [+0.012027, +0.037295]. J shows 1,940 retains more slots and has fewer slot-free documents than 2,586. That justifies investigation, not retrospective promotion.

**Next steps:**
1. Maintain a decision table with separate columns for strict eligibility, v2 audit status, human-review nomination, and product approval.
2. Compare the three fixed outputs on the same human-50 documents, with 1,940 primary and pilot300 as reference.
3. Require the approved future protocol and human findings before any promotion; a nominal v2 pass alone is insufficient.

### D3 — Human 50 timing

**Verdict: agree — before test, not after and not omitted.**

**Evidence:** D-083 explicitly says human 50 precedes test. R §§1.3,3.4,8 establish that char F1 is lexical and grounded ignores omissions. J shows nine target-slot-positive documents become slot-free at 2,586. Automatic metrics therefore leave the central memory-utility question unresolved.

**Next steps:**
1. Freeze the sampling, blinding, rubric, severity definitions, and disposition rules before rating, using Q9's concrete design.
2. Rate source-supported facts, entity/relation correctness, important omissions, qualifier loss, fluency, and memory usefulness—not just slot counts.
3. Adjudicate disagreements and record the human go/no-go recommendation before considering test access.

### D4 — Test 163 disposition

**Verdict: defer — retain the seal now; later allow one frozen A1 candidate once, not B-family reuse.**

**Evidence:** D-083 already limits test to one final A1 candidate, once, after human review, and excludes B-family bridge use. D-080 documents prior A0 test use. Thus this is A1-unused, not a universally untouched research holdout. The unsettled verifier and candidate are sufficient reasons not to open it now.

**Next steps:**
1. Complete the audit and human review, then freeze the candidate, adapter hash, input/decoding contract, scorer version, gates, and analysis plan.
2. If authorized and all prerequisites are met, evaluate only that single A1 candidate and report success, failure, or inconclusive without test-driven retuning.
3. Use a fresh P0 holdout for subsequent confirmation or B-family selection; do not recycle test 163 as development data.

### D5 — Next experiment priority

**Verdict: agree — verifier audit first, with prospective gate/protocol design; then humans, replication, and only then targeted compression intervention.**

**Evidence:** Three of five checkpoint-level grounded failures are normalization candidates, while the same genuine invented percentages persist in both main checkpoints (J). The late checkpoint loses 98 slots, 0.057273 mean source-slot preservation, and seven net slot-free documents (J). A new training run cannot resolve a measurement-definition dispute.

**Next steps:**
1. Execute **A + E design first**: audit v2 and prepare proposed D-084 without reducing D-083 thresholds or overwriting its outcome.
2. Execute **B**, the blinded paired human comparison, then **C**, seed-43 replication under a frozen protocol if further training is warranted.
3. Execute **D** only when the audit/humans support a concrete over-compression hypothesis; change one factor, not length and slot objectives simultaneously.

## Q1–Q12: detailed answers

### Q1 — URL wrapping and trailing punctuation

**Verdict: conditional — yes to proven extraction repair, no to arbitrary whitespace/punctuation deletion.**

**Evidence:** The URL regex in V:59 terminates at a newline. `_canonical` subsequently strips whitespace and terminal punctuation, but too late to recover `.site`. R §3.2 and J's `checkpoints.2586.grounded_failures` support the specific candidate. U also establishes that URL case normalization must be component-specific. An in-memory probe confirmed an existing false pass: source `https://example.com/Case?key=A,B` and summary `https://example.com/case?key=ab` currently produce no `new` or `missing` slots.

**Allowed boundary:** Reconstruct a **source-attested, unambiguously wrapped** URL before extraction. For the supplied hostname example, join the newline and indentation only if the source span shows continuation inside the same URL, not the beginning of prose. Preserve the original span and record the repair. Apply the same deterministic parsing policy to source and summary. Lowercase scheme and host only; preserve path/query case, commas, escapes, and meaningful delimiters. Remove surrounding quotation/bracket wrappers or clearly external sentence punctuation, not a generic set of valid URL characters. If an ambiguous terminal character or continuation cannot be distinguished from URL content, leave it unresolved for manual adjudication. Do not follow links or use the generated URL to guess a missing source suffix.

**Next steps:**
1. Adjudicate the complete `02742` source span; accept these two URL strings as equivalent only if the claimed wrap is confirmed.
2. Add positive and negative URL fixtures: wrapped host/path, prose after a URL, differing suffixes, case-sensitive paths/queries, commas, balanced delimiters, and terminal query punctuation.
3. Replace the broad canonicalizer behavior only in an independently audited future version; measure newly introduced false accepts as well as fixed false rejects.

### Q2 — `오전 9시 30분` versus `9시 30분`

**Verdict: conditional — potentially not a new unsupported time, but not lossless slot equality.**

**Evidence:** J records `오전9시30분` as missing and `9시30분` as new for 1,940 `03978`. Its full prediction also contains nearby `오전 10시` and `오전 10시 20분`, making a same-morning event plausible. However, stripping AM/PM globally would also collapse incompatible morning/evening events. Source passages are unavailable here, so the specific contextual link remains unconfirmed.

**Allowed boundary:** Match a qualified source time to an unqualified summary time **directionally**, only for the same event and compatible hour/minute precision. Record `qualifier_dropped` and reduced specificity; do not award full qualifier preservation. An explicit opposite qualifier is a contradiction, and a newly supplied qualifier unsupported by the source is not licensed. Reject or manually adjudicate ambiguous event alignment, multiple same-clock times, date-boundary changes, and unresolved 12-hour/24-hour conversions. `오후 9시` must not become `오전 9시` by canonicalization.

**Next steps:**
1. Adjudicate `03978` at event/sentence level and separately label unsupported invention versus loss of specificity.
2. Test AM versus PM conflicts, unspecified-to-specified direction, noon/midnight, multiple events, and genuine format-only 24-hour equivalents.
3. Include qualifier loss in the proposed adequacy/human rubric so a grounding correction does not erase lost information.

### Q3 — `18명` versus `18 확진자`; unit limits

**Verdict: conditional — allow a context-bound person-counter alias; disagree with unit erasure.**

**Evidence:** The full `04709` prediction contains `18명` earlier and later the awkward phrase `의성 53·B씨 등 18 확진자는 ...`. The artifact flags the later bare `18`. Importantly, J's actual missing list does **not** contain `18명`: that canonical slot was already preserved elsewhere. This is an occurrence/context issue, not simply recovery of an absent aggregate value. V's set-based matching does not establish that every mention has the right referent.

**Allowed boundary:** Treat an integer count of the same people as equivalent when a count noun such as `확진자` unambiguously supplies the omitted `명`, with the same group, event, and scope. If the phrase might denote an ordinal patient identifier, a different subgroup, or corrupted syntax, do not auto-match it. Preserve magnitude, sign, bounds, precision, range, denominator, and unit dimension. Do not collapse `18명`, `18%`, `18건`, `18일`, `18만원`, or unrelated bare `18`; do not round `2.3%` or `2.2%` into an existing `2%`. Unit conversion, if ever introduced, needs an exact, separately specified rule—not approximate numeric similarity.

**Next steps:**
1. Inspect the complete `04709` source and classify whether the later phrase is a same-group person count or a different/corrupted assertion.
2. Use an explicit counter/noun alias policy with entity/scope evidence and ambiguity abstention; retain mention-level provenance even if reporting unique-slot counts.
3. Audit counter, percent, currency, date, ordinal, and repeated-value counterexamples, keeping `04951` as an unfixed negative control.

### Q4 — D-084 versus post-hoc gate change

**Verdict: agree — require a new explicitly approved D-084 protocol; do not call the existing reanalysis prospectively preregistered.**

**Evidence:** D-083 and S fix the original verifier-derived eligibility and produce null selection. R:148–151 explicitly separates the hypothetical corrections from strict results. The rules are being proposed after seeing both errors and checkpoint rankings; a new decision ID cannot remove that dependence.

Legitimate bug correction and transparent post-hoc reanalysis are allowed scientific activities. What is not legitimate is rewriting D-083 as a pass or selecting normalization rules because they yield 160/161. “Preregister D-084” can mean freezing **future implementation, audit, selection, human rubric, and confirmation**, while labeling existing-val rescoring exploratory. The numerical grounded threshold stays 0.99; any changed measurement semantics or added adequacy gate must be explicit. This review grants no approval.

**Next steps:**
1. Preserve original metrics/selection and draft D-084 with versioned rules, counterexamples, adjudication rules, sample plan, acceptance criteria, and candidate-selection policy.
2. After authorization, rescore the fixed outputs for **pilot300 and all four checkpoints**, not only the two near-misses; publish every changed decision and metric side by side.
3. Confirm the frozen rules on independently labeled P0 examples not used to design them, and reserve any A1 test evaluation for the already-frozen candidate/protocol.

### Q5 — Strict fallback versus near-miss human review

**Verdict: agree — maintain strict pilot300 fallback and allow exploratory 1,940 review.**

**Evidence:** D-083 preserves the fallback and forbids promotion of unsuitable full-train results. Nothing in that rule makes inspection of a failed candidate a product approval. F1 and coverage differences in R §§2,4 give a concrete reason to inspect 1,940. Both main checkpoints still invent `2.3%` and `2.2%` in `04951`, so neither is presently an unqualified safety improvement.

**Next steps:**
1. Label 1,940 “D-083-ineligible, exploratory human-review primary,” not “selected checkpoint.”
2. Keep pilot300 unchanged as the reference, and inspect the genuine hallucination under a preregistered severity rubric.
3. Do not count normalization-sensitive documents as corrected or human-review nomination as permission to deploy or open test.

### Q6 — Primary human-review checkpoint

**Verdict: agree — 1,940 primary; 2,586 secondary.**

**Evidence:** R §2 reports 1,940 versus 2,586 F1 +0.013297, nominal paired-bootstrap CI [+0.001197, +0.024928]. J shows 860 versus 762 slots, preservation 0.476096 versus 0.418823, and slot-free 4 versus 11. Of 1,940's four slot-free cases, only one has a slot-positive target; of 2,586's eleven, nine do. Both have EOS 161/161; 2,586's lower repetition is real but does not compensate automatically for missing memory content. If all disputed matches were accepted, both would retain the same one genuine failing document, not an established safety advantage for 2,586.

**Next steps:**
1. Make 1,940 the primary comparison against pilot300, with 2,586 as a predefined secondary compression comparator.
2. Blind raters to checkpoints and report paired preferences, severity, and important-slot recall—not F1 alone.
3. Reverse the provisional preference only on predefined human utility/safety evidence, not simply because 2,586 is the terminal adapter or has better repetition.

### Q7 — Vacuous grounding, preservation, and a gate at n=161

**Verdict: agree to a separate preservation/adequacy requirement; disagree with redefining every omission as a grounding hallucination. The current 0.99 gate is a screening rule, not a demonstrated population guarantee.**

**Evidence:** L:375 defines grounded as `not rep.new`; V:183's stricter `rejected` is `bool(missing or new)`. They are deliberately different predicates. J shows 2,586's nine target-slot-positive slot-free outputs and its preservation decline. D-080 made source coverage a reference metric; changing G-C5 requires an explicit new decision. Moreover, existing G-C5 was framed around slot grounding and a slot-level minimum sample, whereas D-083 also imposes document-level “no new slot” success. These denominators must not be conflated.

For **161 documents**, grounded ≥0.99 means **at most one failing document**: 160/161 passes, 159/161 fails. Under an independent-document binomial model, two-sided 95% exact intervals are approximately:

| Grounded | Rate | Exact 95% interval |
|---|---:|---:|
| 158/161 | 98.14% | [94.65%, 99.61%] |
| 159/161 | 98.76% | [95.58%, 99.85%] |
| 160/161, hypothetical v2 | 99.38% | [96.59%, 99.98%] |
| 161/161 | 100% | [97.73%, 100%] |

These are reviewer arithmetic, not new model results. Even 161/161 has only a 98.16% one-sided 95% lower bound. With zero failures, at least **299 independent documents** are needed for a one-sided 95% lower bound ≥99% (368 for the two-sided convention). Related article chunks or repeated selection on this validation set further limit an independent-sample interpretation. Hundreds of correlated slots do not provide hundreds of independent document trials.

Retain 0.99 for the historical screen; do not lower it to rescue a checkpoint. A future product confidence requirement can instead return **INCONCLUSIVE** when evidence is insufficient. For adequacy, add source-slot coverage as a diagnostic, reference/key-slot recall and material-omission severity as quality criteria, qualifier-loss counts, and slot-free frequency conditional on a slot-positive target/source. Do **not** demand 99% retention of all source slots: summarization intentionally omits details, and raw slot recall can be gamed by copying irrelevant numbers.

**Next steps:**
1. State document, micro-slot, macro-coverage, and nonvacuous denominators separately, with confidence intervals and source-cluster caveats.
2. Propose G-C5's additional adequacy axis under D-084; set its numerical/severity limits from memory requirements and independent P0 calibration, not a cutoff chosen between 0.4188 and 0.4761.
3. Preserve grounded's meaning, report omissions independently, and distinguish validation-screen PASS from population-safety evidence and final product authorization.

### Q8 — Two epochs and early stopping

**Verdict: conditional — the two-epoch budget was reasonable; treating its last adapter as best would not be.**

**Evidence:** D-083 already registered four checkpoints and best-eligible selection. L implements fresh deterministic epoch ordering and restores training mode after checkpoint evaluation. The run therefore was designed to inspect a trajectory, not automatically adopt the endpoint. R §4 and J support a late compression regression, but do not establish its mechanism or repeatability. At one epoch, 1,293 has lower F1 than 1,940 and still fails grounded; the evidence does not support declaring one epoch the answer. Approximately 1.5 epochs is the best observed lexical/coverage compromise, not a proven universal optimum.

**Next steps:**
1. Retain the failed checkpoints as trajectory evidence and keep final-adapter location separate from selected-candidate status.
2. In a seed-43 replication, freeze the same checkpoint schedule and measurement/selection rules before running; test whether the late decline repeats.
3. Only then test a task-motivated early-stop or compression-control arm, monitoring hallucination and salient recall together rather than enforcing length alone.

### Q9 — Concrete human-50 sampling plan

**Verdict: conditional — a deduplicated, risk-enriched paired audit is appropriate, but it must not be presented as an unweighted random 50-document benchmark.**

**Evidence:** J provides the eleven slot-free IDs, three normalization-candidate IDs, genuine hallucination ID, and document-level losses. M provides per-document F1 and unbatched output lengths. Pilot300 is needed to determine whether the provisional 1,940 gain is useful to humans. Target slot presence alone does not establish importance, and omission of one decisive date/amount need not be “mild.”

Proposed **50 unique validation documents**, selected before ratings:

| Stratum, in selection order | Documents | Rule |
|---|---:|---|
| Genuine hallucination | 1 | `REPORT-news_r-04951-00002` |
| 2,586 slot-free | 11 | All eleven J IDs, including the two whose targets are also slot-free |
| Normalization candidates | 3 | `03978-00001`, `04709-00001`, `02742-00001`, with the full `REPORT-news_r-` prefix |
| Lowest lexical overlap | 6 | Lowest remaining `min(F1_1940,F1_2586)`; prioritize the lowest-decile cases; exclude all previously selected IDs |
| Longest output | 4 | Highest remaining `max(gen_len_1940,gen_len_2586)`; exclude all previous IDs |
| Random remainder | 25 | Uniform without replacement from the remaining 136 validation IDs, using a seed fixed in the protocol |
| **Total** | **50** | **25 certainty/risk-selected + 25 random** |

Predeclare deterministic ID-based tie-breaking. Present all three systems on these same documents with randomized anonymous labels/order, full validation source access, and two independent human raters followed by adjudication. The rubric should capture unsupported facts, wrong entity/relation/polarity, missing material facts, time/unit specificity, coherence, repetition, and usefulness for later memory retrieval. Calibrate raters before opening the selected outputs; do not rewrite model predictions while rating them.

Report risk strata separately. For a descriptive full-val mean under this exact design, the certainty stratum contributes its observed sum and the other 136 documents are estimated by the random-remainder mean: `(certainty_sum + 136 * random_mean) / 161`. Report design-aware uncertainty; do not use a naive 50-row bootstrap as if sampling were uniform. A random remainder of 25 remains very imprecise for rare failures and does not certify 99% safety.

**Next steps:**
1. Register and then materialize the 50-ID manifest, sampling seed, tie rules, blinded presentation, and rubric before rating.
2. Budget for 150 outputs and 300 independent ratings; approximately **12–20 person-hours**, depending on passage length, calibration, and adjudication, is more credible than assuming a brief one-system review.
3. Publish paired results and severity adjudications by stratum, plus any design-weighted summary; use them for development decisions, not as independent holdout confirmation.

### Q10 — Open test now?

**Verdict: defer — no, not before verifier v2 audit, human 50, and candidate/protocol freeze.**

**Evidence:** D-083 already requires this order. D-084 has not been approved, and the residual hallucination and adequacy problem remain unresolved. R §8 correctly says A1 has not used test; D-080 means “never used by the project” would be false.

**Next steps:**
1. Keep test sealed while resolving the current measurement and human-quality questions; this review does not authorize opening it.
2. Freeze one candidate and an immutable evaluation record: adapter/data-manifest hashes, code/scorer revision, prefix, truncation, decoding, gates, uncertainty method, and human disposition. If legacy and v2 scores are both desired on the one frozen output set, specify that in advance.
3. After the single authorized A1 test evaluation, report its outcome without selecting another checkpoint or changing rules against those same 163 examples; use a fresh P0 holdout for later iterations.

### Q11 — Ranking the five proposed workstreams

**Verdict: agree with A first; E should be designed alongside A, not used later to rescue an observed score. Then B, C, D.**

**Evidence:** The uncertainty is first about measurement (V/J), then semantic utility/omission (J/R), then seed stability (one completed seed), and only finally training intervention. Freezing a gate after looking at new human outcomes would create another selection loop.

**Next steps:**
1. **A + E:** define conservative matching and proposed future adequacy/uncertainty criteria; obtain explicit approval and freeze the audit/human plan before new scores or ratings. If utility thresholds cannot yet be justified, retain an inconclusive status rather than inventing a passing number.
2. **B:** run the paired human-50 audit with 1,940 primary, pilot300 reference, and 2,586 secondary.
3. **C → D:** replicate first if training continues; add a single compression intervention only when the diagnosis supports it, without opening test or changing multiple factors at once.

### Q12 — Factual errors, overstatements, and omissions

**Verdict: conditional — the main accounting and strict-versus-candidate distinction are sound; several secondary descriptions need correction or qualification.**

**Evidence and corrections:**

1. **EOS did not improve from 1,940 to 2,586.** Both are 161/161. R:218 and A §3 say repetition and EOS improved; only repetition improved for this pair. F:40 also incorrectly describes 647's EOS 160/161 as a gate failure: 0.993789 exceeds 0.95. Its grounded and repeated4 metrics fail instead.
2. **Two missing-list descriptions disagree with J.** R §3.1 lists eight missing slots for `03978`, but J lists seven. It describes `04709` as including `18명` among eighteen missing slots, but J lists fifteen and does not include `18명`; the full prediction already contains `18명`. This does not change the verified strict grounded/new-slot counts.
3. **160/161 is conditional, not a demonstrated v2 measurement.** The three candidates differ in epistemic status: URL wrapping is an extraction-repair hypothesis; time qualification is lost specificity; the person counter requires referent/scope adjudication. A general re-score may change other cases and slot denominators. None should be individually exempted merely to cross 0.99.
4. **“One genuine hallucination” is narrower than factual safety.** It means one distinct document among the checked numeric/identifier failure cases, recurring in both checkpoints, with two invented percentages. The five checkpoint-level failures are four distinct document IDs, not five independent examples. V does not cover arbitrary Korean entity errors, relations, causal claims, negation, or wrong attribution; existing canonicalization can also hide mismatches.
5. **“Over-compression” is a supported descriptive concern, not a proven training mechanism.** Slot/length declines and correlations support the concern, but no human salience ratings, controlled length experiment, or seed replication establish causality. Nor does target slot count alone justify classifying one-slot omissions as mild and larger counts as necessarily severe.
6. **Lexical significance is not semantic superiority or independent confirmation.** The reported bootstrap intervals are nominal validation comparisons after checkpoint inspection; they do not address checkpoint selection, other development reuse, or possible source/article clustering. Article-level split/resampling independence is not established by this request.
7. **G-C5, D-083, and `SlotReport.rejected` are not interchangeable.** The first historically uses slot grounding, D-083 adds a document-level no-new-slot screen, and strict verifier rejection includes omissions. Report their denominators and predicates explicitly. The available 161 documents cannot establish a 99% population success guarantee merely by a point-estimate pass.
8. **Pilot versus full-train length needs caution.** B:69 records each batch's padded generation length, whereas L:365 records an unbatched generation length. This does not invalidate the 1,940–2,586 length comparison, but a pilot-versus-full length claim would need lengths trimmed at EOS/padding under a common definition.
9. **Auditability has a source-access limitation here.** The request lists dataset and adapter paths, but the raw clean dataset is not present in this checkout. Extracted slots and saved predictions support diagnosis, not final source-context equivalence. A1-unused test is not globally pristine test because A0 used it under D-080.

**Next steps:**
1. In a separately authorized documentation update, correct EOS and missing-list wording while preserving all historical strict results; this consultation does not edit those files.
2. Add an explicit terminology/denominator table and label hypothetical corrections, nominal validation comparisons, and unavailable-source limitations.
3. Supply complete **validation-only** source spans to authorized adjudicators and check source/article grouping before making independent-sample confidence claims; do not expose test or P1 data to resolve these issues.

## Must-fix before promotion or test opening (maximum seven)

1. **Preserve the decision record:** D-083 remains no eligible full-train checkpoint; pilot300 remains fallback, not product approval. No silent re-selection or overwrite.
2. **Approve and freeze proposed D-084:** precise matching semantics, ambiguity handling, full-output re-scoring scope, human protocol, adequacy criteria, and uncertainty conventions. A new ID does not retroactively preregister known outcomes.
3. **Complete source-context verifier audit:** adjudicate the three candidates, keep `04951` as a genuine negative control, and test false acceptance—including current URL case/comma collisions—not only the observed false rejections.
4. **Complete blinded human 50 before test:** 1,940 primary, pilot300 reference, 2,586 secondary; separately assess material omissions, entity/relation errors, and qualifiers. Decide how severe fabricated numbers affect eligibility under the approved rubric.
5. **Add a separately named adequacy requirement:** key/reference-slot recall and material-omission checks, plus slot-free diagnostics; do not relabel missing content as invented content or set a cutoff specifically to pass 1,940.
6. **Correct inference and reporting:** document versus slot denominators, small-n confidence limits, checkpoint-selection caveats, EOS wording, and missing-list discrepancies. A 0.99 validation point estimate is not a 99% population guarantee.
7. **Enforce the test firewall:** human disposition and candidate/scorer/decoding freeze first; one authorized A1 candidate once; no B-family selection and no test-driven retuning afterward.

## Additional experiments (maximum five; none executed here)

Costs are planning estimates, not measured promises; training figures assume a host comparable to the completed run. All data should remain P0.

| Priority | Experiment and decision it informs | Expected cost |
|---|---|---|
| 1 | **Conservative v2 audit and fixed-output re-adjudication.** Develop positive/negative fixtures on independent P0 examples, adjudicate the three validation candidates, then score pilot300 and all checkpoints under frozen rules. Publish every changed accept/reject and coverage effect. | Roughly 0.5–1 engineering day plus 1–3 hours source adjudication; CPU seconds/minutes for saved-text scoring, no training |
| 2 | **Blinded paired human 50**, as Q9 specifies. Determine whether 1,940's lexical/coverage gain improves memory utility and whether 2,586's compression is materially harmful. | About 12–20 person-hours for two raters, 150 outputs, calibration, and adjudication; negligible model compute if using saved outputs |
| 3 | **Seed-43 replication under a frozen checkpoint protocol.** Assess stability of the 1,940 preference and late compression decline; same validation set means this is seed robustness, not fresh holdout confirmation. | Approximately 4.5 CPU wall-hours at the reported setup, plus analysis; no test use |
| 4 | **One controlled anti-over-compression arm**, only if humans/replication justify it: task-aligned length/coverage control or a salient-supported-slot objective, changing one factor against the fixed baseline. Check unsupported content and copying, not length alone. | One comparable training run, approximately 4.5 CPU wall-hours, plus paired validation/human spot review; implementation cost depends on the selected intervention |
| 5 | **Fresh P0 confirmatory memory/safety set** after the model and scorer are frozen. Use source/article-disjoint documents, human key-fact labels, predefined precision and adequacy endpoints, and a sample-size plan. For a one-sided 95% document-success lower bound ≥99%, 299 independent zero-failure documents is the best-case minimum, not an assurance that the experiment will pass. | Several annotation person-days, depending on label depth; inference cost not measured here. Do not claim test 163 alone can provide that guarantee |

## Final recommendation

Keep the official conclusion simple: the two-epoch run succeeded operationally, but **D-083 selected no full-train checkpoint**. Preserve pilot300 as fallback and take **1,940—not the terminal 2,586 adapter—as the primary exploratory human-review candidate**. The higher F1, greater slot retention, and lower slot-free rate justify that nomination; they do not override the genuine numerical hallucination or prove semantic faithfulness.

Proceed with a narrowly bounded, explicitly approved **future D-084** audit/protocol, then a blinded paired human review, and only afterward freeze a candidate and consider the single authorized A1 test evaluation. Report strict and normalization-sensitive results side by side, retain ambiguity and qualifier loss rather than normalizing them away, and add adequacy evidence without weakening historical gates. During this consultation, no training or generation was run, no operational assets were modified, no gate change was approved, and no test access occurred.
