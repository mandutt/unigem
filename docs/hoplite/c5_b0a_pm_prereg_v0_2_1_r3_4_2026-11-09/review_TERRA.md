# Terra 6.1 high reviewer — independent r3.4 review

**Verdict: NARROW.** Do not freeze r3.4 or authorize implementation, unit tests, D0, D1, or the registered run on this text. Correct the contract in a text-only revision, consolidate it into a self-contained normative v1.0, independently review that exact revision, and freeze only after the unresolved choices are settled before any new results. This is advice, not an operational authorization.

## Basis and limitations

- Independently reviewed the complete review request, r3.4, r3.3, the r3.3 synthesis, preflight JSON, P0 report, runner and metric test specified in the request; also checked relevant inherited v0.2/v0.2.1 errata clauses. The synthesis is context, not a substitute for this review; I did not read prior individual model answers.
- `git fetch origin` and `git pull --ff-only origin main` succeeded; reviewed HEAD and `origin/main` were both `05de3ae1b0a4b3bc3df5170efdfe037b45038b9b`. Preflight file SHA-256 independently checked: `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`.
- No training, evaluation, test suite, subagent, additional model, external API, P1 data, or sealed test was used. I performed only read-only metadata arithmetic and a synthetic state-framing hash calculation. Historical “54 tests pass” is not current evidence of PM implementation or PM tests.
- References below use `r3.4 §...` for `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_4.md`. Historical P0 is descriptive: train/val mean copy delta +3.7617/+5.2375 with stated CIs; val median 2.9739 and top-3 share .4862. Untrained real CE 12.7/13.2 exceeds ln|V| 12.43, and P0 used source max length 256 rather than M's 512. It is neither a trained P/PA/M result nor B0-B evidence.

## Q1. Total factored contract

**Verdict: disagree.** The dispatcher is largely specified for already-valid scalar inputs: `ANDn` is false-dominant, validity has explicit tier precedence, and small-N is a signal-axis label with validity/control retained independently (r3.4 §§2–5, F1–F11). But the **whole data-to-decision contract is not total**. In particular, the tail gate lacks a named control/variant, PA validity has to be recovered from older errata, and the workload-specific F/L memory-length rule is not settled (§§7–9). The “primitive” fixtures 16–18 inject `validity_status` and `m_evaluable` rather than deriving all path/availability primitives (§6.2), so they do not by themselves prove end-to-end reachability. The allowed domain/error handling for malformed or nonfinite statistics and missing records also needs an explicit mapping, not silent Python fall-through.

**Next steps:** (1) Specify raw input domains, complete derivations and reject/NA/error behavior through all three axes, including `p_valid` and `pa_valid`; (2) add fully primitive named fixtures and per-axis tests, preserving F11's explicit triple and the registered precedence.

## Q2. L consensus and fixtures

**Verdict: agree, at the stated derived-predicate level.** The nine rows of r3.4 §2.4 agree with §2.3 and its scalar `ANDn`/`NOT3`: true/false and false/true have `l_signal=NA` with `copy_only` and `full_only` respectively true; false/NA does not become `MEAN_CONTRAST_ONLY`. With the §6.2 injected prerequisites, fixtures 16/17/18 derive `EXPLORATORY_L_SIGNAL`, `MEAN_CONTRAST_ONLY`, and `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE` respectively. Dispatch checks copy/full-only before generic NA, after small-N and validity handling.

**Next steps:** (1) Test all nine pairs across valid/invalid/NA validity and n=14/15; (2) derive fixture prerequisites from raw flags in addition to the useful component-level examples.

## Q3. M preflight and cohort

**Verdict: conditional.** The artifact supports the mechanical counts: at K=753, 16/20 train contributors and 15/20 val targets; K=754 has 14 targets; native lengths are 512 for all 20 train and val; common IDs are exactly 15. Its full-K secondary field reports 11/20; I did not open underlying caches to reproduce that field. The 15-of-15 boundary has zero slack and is an exploratory selected cohort, not a representative or independent confirmatory holdout. The P0 val set has already been observed. Reusing those same 15 IDs for signal is a pre-result design choice, not a logical consequence that every shuffled contrast *must* have n≤15.

The remaining ambiguity is material: signal is a shuffled-minus-real contrast (§9.2), whereas M uses a donor-free 753 prefix (§8.3). The inherited donor rule is five nearest from val20 with `K=min` (v0.2 §4; runner lines 318–326, 423–427). A read-only calculation from preflight metadata for the target with length 753 yields nearest donor lengths 754, 751, 755, 750, 764: two paired crops would be <753. This example is conditional on that inherited val20 donor pool and rule; it is not an observed model result. The revision must settle whether this is the intended signal estimand and explicitly distinguish it from the M prefix and 15-ID selection.

**Next steps:** (1) Freeze exact signal target IDs, donor pool, crop and invalid/missing rules, preserving pre-registered donor choices; (2) document zero-margin abort and the distinction between M eligibility and the signal design, without changing K or substituting targets.

## Q4. M builder, M_NORM, endpoint and replay

**Verdict: conditional.** The specific r3.3 omissions are substantially repaired: F/L use 753 and their own adapter, P uses identity at 512, PA uses its own adapter at 512; `h_len_i` is scalar; `real_prefix_t=A(h_t)[:K_M]` puts the M reference and norm in the same space (§§8.1–8.3). With two variants, two endpoints, and two memory kinds, the 1,440-record Cartesian product is arithmetically correct (§8.4). But its meaning must be per *full key*, not “no duplicate target”: each target necessarily appears 96 times. Require the exact key set, not just count, finite values and a duplicate-target check.

The arm table calls F/L memory K=753 without limiting that claim to M (§7.4); the training order traverses all 20 (§7.3), but four preflight train memories are shorter than 753. Likewise the timed generation workload is 20 val documents, five of which are shorter (§10.3). If K=753 applies to all stages, those requirements cannot all be met; if it is M-only, the table is ambiguous. Do not invent padding, drop documents, or change the 20-document training order to resolve this.

Replay is still underspecified: §10.3 phase 5 is donor-free primary M but phase 7 has a 5-donor factor; §10.6 permits donor ordinals 0–4 while the only variants listed are donor-free M variants. The relation of those 600 records to the 120 primary records, the actual source-ID mapping, and whether this is an additional diagnostic workload or true replay are not defined. The JSON record field carrying CE, exact collection encoding and mixed null/integer key ordering are not fixed. Sorting tuples with an identical prefix and both `null` and integer donor IDs is not generally defined by ordinary Python comparison. A tolerance comparison (`atol=1e-5`, `rtol=1e-4`) also does not imply byte-identical SHA-256 hashes; distinguish artifact integrity from tolerant numeric replay.

The independent golden-vector procedure is a real improvement, but the stated replay's three records and expected digest are not yet supplied. For the exact two synthetic state tensors and frames in §10.6, my independent standard-library framing calculation produced SHA-256 `43ecb58e197d5789df0a9dbbc67beba11538b8063c3da8ac46f96e1e95d65712`; empty is `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. These are review calculations, not a committed golden artifact or a test of an implementation.

**Next steps:** (1) Specify lengths, masks and crop rules separately for training, shuffled evaluation, M and generation; (2) define exact endpoint/replay datasets, donor identity mapping, canonical CE/JSON and tolerance versus hash comparisons; (3) publish independently derived, complete state and replay golden inputs/bytes/digests before freeze and test missing, duplicate and mixed-null keys after implementation is separately authorized.

## Q5. PA

**Verdict: conditional.** The acquisition-control name, `PA_STEP100_NOT_VALID`, separate PA step0, descriptive nullable retention and differing native/EG2 geometry are appropriate (§§4.2, 7.2). The PA M veto is an explicit **joint P/PA calibration policy**, not evidence that the native memory regime as a whole is intrinsically invalid: a trained random-initialized PA adapter can fail for reasons P does not. The r3.4 text's stronger causal rationale overstates what this control establishes. `PA_VALID` is not actually defined in r3.4 §7.2; older v0.2.1 errata §2.4 says the same step100 shuffled criteria as P. Missingness, cohort and seed aggregation should be explicit in the consolidated contract, not inferred from naming.

**Next steps:** (1) Restate the complete P/PA validity and path derivations and the PA veto as a conservative preregistered joint criterion; (2) preserve PA retention as non-gating and avoid causal or retention-equivalence claims.

## Q6. Cap, D0 and D1

**Verdict: conditional.** The arithmetic is correct: 4 arms × 3 seeds × 100 = 1,200 registered updates; prospective D1 adds 4 updates, D0 adds zero; 120 + 20 + 15 = 155 minutes total prospective maximum, not a grant. Phase 5 is 15×2×2×2=120 records/arm-seed and phase 7 is 15×5×2×2×2=600; 3×sum over four arms of the eight measured terms is the stated projection (§10). A record is not necessarily a separate forward pass: copy/full can share one forward, so time the actual full workload rather than applying a record count multiplier twice.

Two issues block accepting the timing as executable: the primary/replay workload identity and non-M lengths in Q4, and “D1 no labels” (§10.3) is ambiguous because one supervised update and CE scoring require target label tensors (runner lines 107–125, 692–705). It can mean no *decision/result labels*, but cannot literally mean no model target labels. Also, extrapolating one document's update time 100 times is an estimate, not a proven upper bound for 20 differing sequence lengths; specify which preselected update is timed, hardware/process assumptions and how overhead and variable lengths are covered without adding updates or relaxing caps. ≤96 minutes provides headroom, not a wall-time guarantee.

**Next steps:** (1) Define D0/D1 target-label versus decision-label prohibition and exact phase inputs; (2) resolve replay and length semantics, then require complete measured phase accounting and a conservative, predeclared projection within existing limits.

## Q7. Statistics

**Verdict: disagree that all statistics are executable.** The document correctly specifies 1,000 document-level resamples, percentile 2.5/97.5, seed 20261109, seed averaging before bootstrap, registered 2-of-3 with a missing registered seed yielding NA, and separately names `documents_positive` (§9). Legacy runner `bootstrap_paired` uses seed 20261108 and calls the count of positive documents `seeds_positive` (lines 384–397), so it is not a drop-in implementation. But §9.4 specifies L/copy/cohort and `control_copy_ce` without identifying **shuffled donor control, M_POS_MEAN, or M_NORM**, while §§8–9 contain all of these possible contrasts. That is an unresolved r3.3 blocker; it can change the hard B0-B gate. The synthesis's suggested M_POS_MEAN variant does not automatically make it normative in r3.4. The rule should also say how the three seeds and donors are reduced to one delta per document, how partial records/nonfinite values map to NA, and how equal |delta| ties select top three. With mixed-sign tied magnitudes, different tie choices can change leave-top-three mean and hence the gate.

The ordered tail logic itself is clear once inputs are defined: known nonpositive leave-top-three mean → true; otherwise a null input → NA; otherwise absolute share >.50 → true; else false. Its explicit ordering gives NA, not true, when the mean is null even if share alone exceeds .50. This conservative behavior should be tested as written. Percentile interpolation/RNG algorithm, input ordering, and fixed synthetic bootstrap vectors are also needed for bit-reproducible CIs; retain the stated statistical thresholds.

**Next steps:** (1) Freeze one named tail contrast/variant and reduction/tie rules before results, consistent with intended estimand; (2) specify bootstrap RNG, percentile, ordering, missing/nonfinite behavior and independent fixed examples for CI, 2/3 and tail boundaries.

## Q8. Ranked remaining must-fix

**Verdict: disagree with the blanket “closed” claim in r3.4 §15.** Many r3.3 textual fixes are real, but these remain freeze blockers:

1. **Signal estimand and tail gate:** identify signal/shuffled versus M variants, target and donor pools, crop lengths, reduction across donors/seeds, ties and missingness (Q3, Q7). Tail control/variant was explicitly an r3.3 blocker and remains unspecified.
2. **Workload-specific lengths and native source path:** separate K_M from training, shuffled and generation memory; resolve the F/L short-train/short-val conflict and clarify P/PA source length per workload. Never silently pad, drop or replace documents (Q4).
3. **Replay and timing:** define donor-free primary versus donor-level replay, actual donor mapping, record key set and numeric-vs-hash validation; reconcile this with D1 phases and projection (Q4, Q6).
4. **Complete statistical/decision and PA primitives:** explicitly derive P/PA validity and missingness, CI generation, stable tail ordering and fully primitive named fixtures; correct PA veto rationale without changing the veto (Q1, Q5, Q7).
5. **Freeze-ready golden vectors and debug semantics:** supply full independently obtained state/replay vectors and exact wire schema; distinguish supervised target tensors from decision labels in D1 (Q4, Q6).

The table correction, identity builder, same-space norm, adapter LRs and 120/600/1,440 arithmetic are improvements. They are not evidence that these integration-level questions have been closed. The F/L length-scope conflict and D1 label wording are additional problems made more visible by r3.4's expanded claims, not evidence of a trained result.

**Next steps:** (1) Resolve this ranked list text-only, before implementation/results; (2) trace every correction into the consolidated spec and independently review it.

## Q9. Freeze, implementation and D0

**Verdict: disagree.** No r3.4 freeze, PM implementation, PM unit-test work, or D0 is recommended now. The text itself says code follows approval/freeze (§16); a plausible implementation chosen while key estimands and replay rules are unsettled risks accidentally preregistering by code. This is not a recommendation to run anything in this consultation.

After a separately reviewed, frozen spec and appropriate authorization, minimum tests should include §2.4's nine pairs and F1–F11; full primitive fixtures; four-arm memory identity/length/short-input tests; zero/nonfinite norms and exact 1,440-key set; PA/validity calibration; missing seed/donor/endpoint and 2/3; paired bootstrap and tail ties/NA; independent state/replay golden digests, tolerance and duplicate/missing keys; mode, metric alignment and sealed-split assertions. D0 must remain no-update, non-result, and separately bounded as specified.

**Next steps:** (1) Complete Q8 and freeze a reviewed spec; (2) only then seek explicit authorization for implementation, unit tests and D0 with the above test contract.

## Q10. D1 and 3-seed boundary

**Verdict: conditional.** Separate D1 approval and a further explicit 3-seed approval, with all eight measured phases and finite T_proj ≤96 minutes, are appropriate (§§10–11). D0 is not a substitute for D1; D1's debug seed 20261111 is distinct from registered 20261108/09/10. The 27-item checklist is useful but does not yet prove the Q3/Q4/Q6/Q7 unresolved semantics, exact full-key coverage, donor source mapping, input/model/tokenizer/config fingerprints, actual step0 state restoration, non-overlapping timing, or the identity and numerical replay comparison policy. It also should explicitly carry the reviewed consolidated freeze hash and reproducible synthetic expected vectors.

**Next steps:** (1) Add those concrete contract and artifact checks before considering D1/3-seed readiness; (2) require D0 evidence, full D1 timing, no cap overruns and a new explicit authorization at each boundary.

## Q11. B0-B boundary

**Verdict: agree on the stated boundary, conditional on defined inputs.** The necessary predicate in r3.4 §14 is `validity_status == VALID AND control_status == M_CONTROL_PASS AND signal_status == EXPLORATORY_L_SIGNAL AND m_valid == true AND n_signal >= 15 AND tail_driven == false AND leakage/mode/metric pass AND artifact complete AND separate preregistration/approval`. Because `n_signal` is at most 15, the numerical condition means exactly 15. `tail_driven` true or NA blocks; `EXPLORATORY_L_SIGNAL` alone, 11/20 secondary, P0 or PA retention never approves B0-B. These are prerequisites for considering a separate decision, not a grant of B0-B, B1, B2 or Stage C.

**Next steps:** (1) Preserve the literal r3.4 labels and false-only tail gate in the consolidated spec; (2) require separate B0-B preregistration/approval after valid, complete results and no automatic downstream action.

## Q12. Final verdict and approval scope

**Verdict: conditional for a NARROW outcome; recommendation is NARROW.** This review supports **text-only contract correction and independent review**. It does not grant or recommend r3.4 freeze, implementation, unit tests, D0, D1 or any 3-seed run now. The present consultation has **0 optimizer updates and 0 model-evaluation minutes authorized**. For context only, the prospective separate caps in r3.4 are D0 ≤15 minutes/0 updates, D1 ≤20 minutes/4 updates, registered run ≤120 minutes/1,200 updates, CPU/no GPU, six threads, no retry or extension: combined ≤155 minutes/1,204 updates, not a grant. No D0-to-D1 or D1-to-run automatic progression.

Test 163 remains sealed; no P1 or external APIs; T5Gemma2 remains closed by D-108 STOP. Phase 6 execution and B0-B/B1/B2/Stage C remain unapproved. Do not modify thresholds, seed set, donors, step count or LRs in response to observed results; any genuinely new design is a separate prospective preregistration.

**Next steps:** (1) Address Q8 text-only; (2) review/freeze v1.0 and seek explicit approvals in the stated order.

## Q13. Consolidation

**Verdict: agree: a self-contained normative v1.0 is needed before implementation.** r3.4 is explicitly an erratum with precedence through nine versions, while even PA_VALID must be recovered from v0.2.1 errata. r3.3's stale 20-document signal and mixed L table demonstrate the risk of inheriting obsolete text. The 256/512 source and M-only-versus-global K scope questions show why precedence alone is not an executable implementation contract. A single normative specification lowers implementation error risk; keep older documents as historical traceability, not competing implementation authority.

Minimum sections: (1) scope, approval and sealed boundaries; (2) data/model/cohort identities, donor and leakage rules; (3) four-arm initialization, training/eval modes and workload-specific memory/length/crop; (4) M builder, variants, endpoints and exact record schema; (5) statistical estimands, aggregation, CI and tail; (6) primitive three-axis decision tables and failure precedence; (7) canonical checkpoint/replay formats and independent vectors; (8) D0/D1 workload, timing, caps and gates; (9) artifacts, tests, B0-B boundary and aborts. Provide a clause-by-clause map from r3.4 and inherited normative rules, explicitly marking superseded clauses and resolving conflicts, plus immutable preflight/spec/code hashes. Do not silently introduce new scientific choices under the label of consolidation.

**Next steps:** (1) Draft text-only v1.0 incorporating the resolved must-fixes and traceability matrix; (2) conduct a separate review round on that exact complete document and freeze its commit before seeking implementation/D0 authorization.

## Wrong premises to avoid

- “n_signal is 15 because M has 15” is not a mathematical identity for the original donor-cropped signal; it is a new explicit cohort/estimand selection that needs a fully specified contrast.
- “120/600 records are automatically 120/600 model forwards” and “a matching count proves matching keys” are both false.
- “PA failure proves native memory itself invalid,” “P0 proves trained P/PA/M,” and “T_proj ≤96 guarantees completion” are unsupported.
- The full-K 11/20 field and historical test claims are artifact assertions, not freshly reproduced results in this review.