# Sol 6.1 medium reviewer — independent v0.2.1-r2 review

**Reviewer:** Sol 6.1, medium review round. Independent external consultation for mandutt/unigem; this is a new r2 review, not a continuation or reuse of an individual r1 review.

**Final recommendation: NARROW. Do not freeze r2 as written.** The repairs are substantive, especially M calibration routing and the length-only preflight, but the contract still contains fail-open unknown-path cells, inconsistent test requirements, an unreachable signal label, and a circular launch prerequisite. A small, text-only r3 should close these before freeze, implementation, or D0. This is not a scientific STOP on the bridge hypothesis.

## Review basis and work performed

- Date: 2026-11-09.
- Ran `git fetch origin`, then `git pull --ff-only origin main`, in that order. Both succeeded; pull reported `Already up to date.`
- Resulting HEAD and `origin/main`: **`fc5680ef051bb6d00dbe74e7a0c08da193725b38`**, `docs: add C5 P/M v0.2.1-r2 review request`.
- The request's reference to drafting HEAD `308648e` is historical metadata; this review uses the synchronized current HEAD above.
- Personally read the complete external review request, r2, r1, the requested r1 synthesis, M preflight JSON, P0 report, runner, and metric tests. Also consulted the inherited v0.2 arm/M definitions and v0.2.1 errata's M/statistics clauses to avoid treating inherited specifications as absent. I did not read individual prior reviewers' reports or other r2 opinions.
- Read-only verification: SHA256 and arithmetic over the already committed preflight JSON. No source corpus, sealed test, P1 data, model weights, or model outputs were opened for a new analysis.
- **No training, evaluation, smoke, generation, unit tests, subagents, additional models, or external APIs were run/called.** Git synchronization was the explicitly requested remote operation. Historical “54 tests pass” is not a current verification result and is not evidence that PM is implemented.
- The only new/modified repository file from this consultation is this report. No fixes, protocol edits, commit, or PR were made.

### Citation notation

`r2 §x (Lx–Ly)` refers to `docs/plan_c5_b0a_pm_prereg_v0_2_1_r2.md` at the reviewed HEAD. `r1`, `synthesis`, `preflight`, `P0`, `runner`, and `metric tests` refer to the seven artifacts named in the request. Inherited clauses are identified explicitly.

## Executive assessment

| Area | Independent assessment |
|---|---|
| Factored output | Real improvement, not merely a renamed headline. Nevertheless, a deterministic `else` is not proof of correct validity or consistent acceptance tests. |
| M calibration | The old “P/PA M failed but L control passes” leak is closed by §5 when the prerequisite flags are coherent and available. |
| Paths | Boolean PA-vs-P failure is distinguished; unknown PA path and unknown test-use provenance can still fall through to `VALID`. |
| L preservation | Raw flags plus explicit qualifiers resolve the old literal-string invariant; small-N precedence now needs to be reconciled with the new test requirements. |
| M preflight | Max-K=753, contributors=16, targets=15, and native 512 lengths are supported by the frozen JSON. Length-conditioned, zero-margin, exploratory scope only. |
| M construction | Eval/no-grad, common IDs, seed averaging, and replay are materially better. M_NORM remains target-magnitude-conditioned, not fully target-independent. |
| Debug/cap | 1,200 registered updates, D0 zero updates, D1 four updates are arithmetically coherent and separately authorized. Timing coverage still needs explicit scope. |
| Launch checklist | Incorrect hash reference and an impossible prelaunch requirement for trained P/PA M_VALID. These must not induce an unregistered preliminary run. |
| Future phases | No automatic B0-B/B1/B2/Stage C approval; preserve that boundary. |

## Concrete contract counterexamples

These are **manual traces of the written pseudocode**, not outputs from an implemented decision function or a test execution. Unless overridden, take all path-success flags true, `test_split_used=false`, P/PA valid, M evaluable/valid/L-pass true, copy/full L signals true, and n_signal=15.

| Cell | r2 pseudocode outcome | Why it matters |
|---|---|---|
| C1: `pa_step100_path_ok=NA` | `VALID / M_CONTROL_PASS / EXPLORATORY_L_SIGNAL` | §2.4 checks PA path false, but never PA path NA. Unknown step100 path is accepted. Declaring this input inconsistent does not provide fail-closed handling for the all-input contract. |
| C2: `test_split_used=NA` | Same affirmative tuple | Test usage has an explicit tri-state domain (§7.1), but only true is checked. Unknown sealed-split provenance must not authorize a valid assay. |
| C3: `assay_path_ok=NA`, `p_step100_path_ok=false` | `NOT_ASSESSABLE` validity | The earlier any-NA branch wins over known P path failure, contradicting §2.4's prose and §7.2's “P path fail → ASSAY_INVALID.” |
| C4: n_signal=14, L true, validity not VALID | `INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL` | Sensible small-N output, but §7.2 also unconditionally demands `L_SIGNAL_VALIDITY_INVALID` for invalid validity plus L signal. Both cannot be the single signal_status. |
| C5: `m_evaluable=false`, P/PA valid, `m_valid=false` | `M_NOT_EVALUABLE` control | §7.2 unconditionally asks for `M_CONTROL_INVALID` when m_valid false and P/PA valid. It omits the m_evaluable=true antecedent used by §5. |
| C6: one P/PA M component false, another NA | §3/§5.1 AND3 gives false | §9.5 says “any missing/CI unavailable → NA” and also “any false → false.” The mixed case needs the declared false-dominant AND3 rule, not a second missingness-first implementation. |

**Unreachable-label proof:** §5 can yield `control_status=M_NOT_EVALUABLE` only if m_evaluable is not true or P/PA validity is not true. In every such case §2.4 yields a validity other than VALID. For n>=15 and L true, §6.2 therefore takes `L_SIGNAL_VALIDITY_INVALID` before its `L_SIGNAL_M_CONTROL_NOT_EVALUABLE` branch. For small N or NA N it exits earlier. Consequently **`L_SIGNAL_M_CONTROL_NOT_EVALUABLE` is unreachable in the composed function**, even though §7.2 requires every label to be reached. An arbitrary externally supplied status tuple is not evidence of reachability through the specified composed function.

## Q1. Total factored contract

- **Verdict: disagree** with the claim that the whole r2 contract is already freeze-ready and consistent.
- **Evidence:** r2 §§2–6 supply deterministic branches, three output axes, strong-Kleene primitives, and actual M calibration routing. §5.2 (L270–290) now blocks a pass when m_valid=false or P/PA validity is unavailable. That closes the principal r1 M leak. However, C1–C3 are unresolved validity semantics, C4–C6 contradict acceptance requirements or aggregation prose, and the unreachable-label proof defeats §7.2 (L426–439). The pseudocode is syntactically total on its finite input domain; the **specification and required invariants are not jointly satisfiable as stated**. A separate `constraint_violation` flag is useful, but must have a defined non-affirmative admission consequence rather than coexist with an apparently valid result.
- **Next steps:**
  1. Specify fail-closed handling of both missing path/provenance flags and known failures mixed with NA; keep P/PA failure precedence explicit.
  2. Reconcile label reachability, small-N priority, and the antecedents of all §7.2 assertions; define the composed input/derived-flag contract.
  3. After text freeze, implement the pure function and exhaustive model-free truth table, including mixed false/NA M components and all C1–C6 cells.

## Q2. L preservation / small N

- **Verdict: conditional.**
- **Evidence:** §3 (L216–227) explicitly changes l_signal to a consensus: both true → true; both false → false; discordant or missing → NA. That is different from AND3 but is now an intentional, executable definition. Copy-only/full-only require an explicitly false opposite endpoint. §6.2 provides small-N qualifiers and a control-not-assessable L qualifier; §6.4 (L393–399) correctly replaces the impossible universal “L in every status string” requirement with raw-flag preservation. For n=NA with raw L true, `NOT_ASSESSABLE` plus flags/reason is allowed by this revised invariant. However, C4 and the dead M-not-evaluable qualifier remain, and “common target docs” has not unambiguously distinguished the L donor assay from the M prefix cohort.
- **Next steps:**
  1. State that small-N and unknown-N branches take precedence, with raw endpoint flags and reasons retained under all validity/control outcomes.
  2. Identify the exact ID set counted by n_signal and distinguish it from M's common-prefix cohort; do not silently refit the signal population during implementation.
  3. Freeze fixtures for n=NA/0/14/15/20 and all nine copy/full tri-state pairs. n=15 is executable but fragile; loss of an eligible endpoint must never trigger K/cohort replacement.

## Q3. M preflight

- **Verdict: agree**, within the explicitly narrowed prefix/length-conditioned scope.
- **Evidence:** I independently calculated from the supplied JSON: maximum feasible K=753; train contributors=16; val targets=15; K=754 val targets=14; train/val medians=768.5/766.5. The threshold-derived target IDs match `common_ids`. All listed native train and val lengths are 512. SHA256 is **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`**, matching §1.4 and the sidecar. These support §§1.1–1.3 without examining raw documents or evaluating a model. The artifact reports full-K eligibility=11/20; I did not independently reconstruct that secondary eligibility from caches. Prefix 753 changes the estimand from full-real-K, but r2 §1.5 and §9.3 explicitly disclose that change rather than claiming equivalence. It is not inherently illegitimate merely because val lengths inform a result-blind feasibility rule.
- **Next steps:**
  1. Preserve this exact hash, K, ID set, and five excluded IDs in the freeze manifest and reports; fix the checklist's different hash.
  2. Always label the finding `M_CONTROL_PREFIX753_COHORT15` and disclose longest-15-of-20 selection and zero margin.
  3. Keep full-K 11/20 descriptive only. Do not add shorter documents, lower K, or change thresholds after outcomes or missingness are observed.

## Q4. M builder / aggregation / replay

- **Verdict: conditional.**
- **Evidence:** §9.2 specifies eval/no-grad and train-only contributor averaging; §9.3 places P/PA on the same 15 target IDs; §§9.4/9.6 define mean-minus-real deltas and seed-average-before-document-bootstrap. This is substantially more executable than r1. The inherited v0.2 M definition explicitly includes **PA adapter outputs**, so I do not treat PA post-adapter construction as absent; implementation must preserve mean(A_PA(native_i)), not apply A_PA to an already averaged native tensor. The inherited v0.2.1 §3.5 correctly says M_NORM uses target real-memory Frobenius norm and is a **magnitude-matched negative control, not strictly target-independent**. No target summaries enter the builder, but “fully leakage-free/target-independent” would overstate the norm control's independence. §9.7 adds cross-process replay and state hashes. At the stated tolerances, normal allclose means |a-b| <= 1e-5 + 1e-4|b|, not an absolute 1e-5 bound; near CE=13 this permits about .00131. No empirical replay has been verified here.
- **Next steps:**
  1. Freeze the per-doc/per-seed/per-arm/per-variant table schema, exact cohort intersections, and missing/finite eligibility rules before implementing aggregation.
  2. Test train-only contributor provenance, post-adapter PA averaging, whole-prefix Frobenius scaling, and inherited zero/non-finite norm rejection using synthetic fixtures.
  3. Define replay comparison granularity/reference, finite-value checks, and checkpoint/config/ID/mask hashes; compare matched per-doc CEs, not merely a canceling pooled mean, using the already registered tolerances.

## Q5. PA

- **Verdict: agree.**
- **Evidence:** r2 §8.2 (L462–470) names PA an acquisition control, requires an independent random-adapter step0, retains `PA_STEP100_NOT_VALID`, bans `ADAPTER_REGIME_LOSS`, and records mT5-final-hidden versus EG2-layer19 scale/geometry. r1 §3.2 and inherited v0.2.1 §2 specify PA_VALID with P's threshold, PA movement telemetry, and retention's possible null/uninformative meaning. This is adequate scientific naming: success would show acquisition in PA's own native-input regime, not validate EG2 transfer or prove that a formerly sensitive PA path was retained. The remaining PA-path NA defect is a validity-function defect (Q1), not a reason to revive the old interpretation.
- **Next steps:**
  1. Preserve separate P0/P-step0/PA-step0 artifacts and explicit memory/adapter provenance.
  2. Test random-adapter PA initialization and seed-reset LoRA initialization; retain acquisition/movement telemetry without making retention a gate.
  3. Report PA validity and geometry limitations alongside L, never as automatic evidence of successful EG2 transfer.

## Q6. Cap / D0 / D1

- **Verdict: conditional**; the arithmetic and approval separation agree.
- **Evidence:** §11 registers 4 arms × 3 seeds × 100 updates = **12 units / 1,200 updates / 120 minutes / 6 threads / CPU only / no retry**. D0 is <=4 configurations, **0 updates**, <=15 minutes, seed 20261111. D1 is **4 arm-seeds × 1 update = 4 updates**, <=20 minutes, seed 20261111, and separately approved. Distinguishing an implementation gate from a registered-run timing gate is correct; D0 cannot measure backward/optimizer work. If every phase were separately authorized, one D0 plus one D1 plus the registered run would total at most **155 minutes and 1,204 updates**, not 1,200 updates inclusive of debug. That is accounting, not permission. §§11.3–11.4 do not yet enumerate all phase costs covered by the D1 projection.
- **Next steps:**
  1. Make timing coverage explicit: load/build, train, donor CE, M variants, cross-process replay, required telemetry and artifact/checkpoint I/O; charge the registered workflow end-to-end against its cap.
  2. Keep the finite <=96-minute launch projection and hard <=120-minute registered stop; if a one-update probe cannot support a finite complete projection, do not launch.
  3. Keep any substitute timing probe separately authorized with its own explicit limits. Do not turn it into unbounded calibration, retries, or registered-seed rehearsal.

## Q7. Statistics

- **Verdict: conditional.**
- **Evidence:** §10 (L587–611) freezes 1,000 resamples, 2.5/97.5 percentiles, seed 20261109, document unit, seed-first averaging, n_min=15, and distinct document/seed positivity. The inherited v0.2.1 §4.3 supplies the L copy/full thresholds and 2/3-seed criterion; those have not disappeared. Paired per-document L−F is appropriate, and three seeds ×15 docs must not become 45 independent observations. But “common target docs” still needs separate donor-signal versus M-cohort definitions and missing-seed/variant rules. `sum(top3)/sum(all)` is undefined for a zero denominator, while negative/mixed totals are not ordinary positive-contribution shares. The contract has no explicit finite/NA behavior for those summaries. In current runner L384–398, bootstrap defaults to **20261108**, and `seeds_positive` counts elements of its document-delta array. These are expected implementation gaps in the old runner, not evidence that the new constants are already active.
- **Next steps:**
  1. Pin primary ID sets and require matched complete registered-seed/endpoint data for each pooled primary estimate; encode missingness rather than silently using nanmean or a varying seed denominator.
  2. Specify zero/non-finite denominator, fewer-than-three-doc, signed-total, ordering, and NA propagation behavior for tail summaries before results. Preserve the existing .50/zero thresholds; mark undefined summaries, do not substitute a favorable denominator.
  3. Test explicit bootstrap seed=20261109, seed-first pooling, paired L−F, document-versus-seed counts, and marginal-cohort flags with synthetic model-free inputs. Preserve historical P0 artifacts rather than recomputing them to make naming match.

## Q8. Remaining Must-fix

- **Verdict: disagree** that r2 §15 has closed every r1 item.
- **Evidence and ranked fixes:**

| Rank | Must-fix before freeze | Source and minimum closure |
|---|---|---|
| **MF-1** | Fail-closed path/provenance and known-failure priority | r2 §2.4/§7.1–7.2; C1–C3. Explicit PA-path NA and test-use NA handling; a known P-path failure must satisfy the declared invalidity invariant even with another NA. Define constraint violations as non-affirmative, without destroying raw flags. |
| **MF-2** | One consistent composed decision/test contract | r2 §§3/5/6/7/9.5; C4–C6 and unreachable-label proof. Qualify assertion antecedents; resolve the dead label by an explicit semantic choice, not a fake fixture; make false+NA M aggregation match AND3; retain small-N priority and flag preservation. |
| **MF-3** | Non-circular launch state machine and one artifact hash | r2 §12 items 6 and 9. Replace stale `07c3fe4c…` with the verified full `3ee3f1ca…` hash. P/PA M_VALID is a trained, seed-aggregated result and cannot be a prerequisite for obtaining those very results. Move it to result interpretation/later-phase eligibility, not an unregistered preliminary result screen. |
| **MF-4** | Exact endpoint/cohort/missingness and total summary schema | r2 §§1.3/2.2/6.1/9.3/10 plus inherited statistics. Separate the frozen M target population from L/F donor-signal population, name the n values, pin variant/seed intersections and finite/NA treatment, and define undefined tail summaries. No population/threshold change after results. |
| **MF-5** | End-to-end timing/cap accounting | r2 §§9.7/11/12. List all required work in the projection and registered wall clock, including replay. If the bounded D1 cannot estimate it, retain the launch block; no implicit extension. |

- **What really closed:** the original m_valid status-slot omission; naming/Boolean P-vs-PA distinction; raw L preservation direction; K's written max rule and hash in §1; M common cohort/delta/seed-aggregation direction; explicit debug seed and separate update arithmetic. The r1 synthesis itself also requested P/PA M_VALID prelaunch; r2 inherited that sequencing mistake. Being requested by an earlier synthesis does not make it executable.
- **New/exposed r2 problems:** the unreachable L-qualified branch, contradictory expanded test requirements, and the inconsistent checklist hash. No trained P/PA/M result is available to justify dismissing these as harmless.
- **Next steps:**
  1. Produce the narrowly scoped text-only r3 required by r2 §16, correcting MF-1–MF-5 without changing scientific thresholds, registered seeds, donors, steps, or LR.
  2. Publish repaired cell examples, a reachable-label policy, and the artifact/lifecycle schema in that same pre-results contract.
  3. Obtain explicit review/freeze approval before implementation or D0.

## Q9. Freeze / implementation approval

- **Verdict: disagree** with unconditional freeze and implementation+D0 approval now.
- **Evidence:** §16 says code follows freeze, and a NARROW r2 goes to a must-fix-only r3. MF-1–MF-4 affect the very expected outputs an implementer would encode; implementing first would allow the code author to decide protocol semantics. Current runner CLI (L753–802) only offers smoke, metric-smoke, train, and p0-sanity, with frozen/lora arms; train_arm (L665–750) is not PM. Metric tests cover corrected same-position CE, masks, modes, telemetry, native donors, and descriptive P0—not the PM truth table/M replay/statistics contract. The model-dependent test class is guarded by local-model existence (metric tests L13–14), so model-free PM tests should not be hidden behind that skip.
- **Next steps:**
  1. Before freeze, settle input/derived-flag schema, all counterexample expectations, reachable labels, population definitions, artifact hash, and lifecycle gates.
  2. After corrected freeze and explicit authorization, implement model-free decision/statistics tests first, then deterministic builder/PA/P fixtures, checkpoint/hash/replay and cap/approval guards.
  3. Only after that implementation gate passes, separately execute authorized D0 with zero updates and no result labels. This consultation does not execute or grant Phase 6.

## Q10. D1 / 3-seed gates

- **Verdict: conditional.**
- **Evidence:** §§11.3–11.4 correctly make D1 optional for implementation but necessary for timing evidence before registered execution (or require a separately approved substitute). §12 correctly requests commit hashes, green tests, D0, debug-seed disjointness, no hyperparameter drift, artifacts, and explicit approval. However, item 9 demands **P/PA M_VALID true before launch**, whereas §2.2 requires three seeds and §9 uses final trained checkpoints. No trained results have been seen, D0 has zero updates, and D1 has one debug update per arm and no labels. None can legitimately establish that condition. The launch checklist is therefore circular as written. Item 6 additionally names `07c3fe4c…`, not the committed preflight hash.
- **Next steps:**
  1. Separate prelaunch mechanics/provenance/timing approval from post-run calibration/control interpretation. Do not introduce a pilot P/PA outcome gate or new uncounted trained units to satisfy the circular item.
  2. Use the verified full hash, complete timing budget, wall-clock/update watchdogs, and explicit incomplete-run behavior in the launch checklist.
  3. Keep D1 separately approved and label-free; keep the 3-seed run separately approved after its prelaunch evidence exists. Incomplete or failed registered results are reported, not retried or used to adjust the protocol.

## Q11. B0-B boundary

- **Verdict: agree** that the no-automatic-approval boundary is preserved; future eligibility language is not current approval.
- **Evidence:** §14 (L708–727) and §17 explicitly prohibit progression by label alone. Restated in r2 terms, a **candidate for separate B0-B preregistration/review**, not an authorization, would require:

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS
AND signal_status == EXPLORATORY_L_SIGNAL
AND m_valid == true
AND leakage/mode/metric checks pass
AND complete, replayable artifacts
AND explicit M_CONTROL_PREFIX753_COHORT15 scope
AND tail diagnostics fully disclosed
AND separate preregistration, review, and explicit user approval
```

  The current `tail_driven == false (or explicitly reported)` clause is **a disclosure exception, not a robustness exclusion**: if either value is merely reported, it passes that part. Do not describe it as a hard heavy-tail robustness gate. Full-K 11/20 is not substitute gate evidence. Even a clean exploratory finding would not establish generalization, generation quality, or broader mechanism claims.
- **Next steps:**
  1. Preserve separate approval requirements for B0-B, B1, B2, and Stage C regardless of all favorable Phase 6 labels.
  2. State plainly whether later-phase tail handling is disclosure-only; any genuinely different later scientific rule belongs in a separately frozen preregistration, never a retroactive Phase 6 threshold change.
  3. Report prefix/length-selection and target-norm-conditioning limitations with any proposed later-phase evidence package.

## Q12. Final verdict and authorization scope

- **Verdict: conditional — NARROW.** r2 warrants targeted contract repair, not bridge STOP and not CONTINUE as written.
- **Evidence:** verified max-K preflight, substantive §5 M fix, and bounded debug design justify continued protocol work. The concrete validity leaks, impossible composed-label coverage, and circular prelaunch condition prevent an executable freeze. P0 supports historical native-path metric sensitivity only: train mean Δcopy +3.7617, CI [1.8917,5.6050]; val +5.2375, CI [2.5013,8.0753]. The supplied val median 2.9739/top-3 share .4862 and untrained real CE roughly 12.7/13.2 above ln|V|≈12.43 constrain interpretation. A strongly positive wrong-minus-real contrast is not trained-model quality or evidence that EG2/LoRA works. No trained P/PA/M result is available.
- **Next steps:**
  1. Repair MF-1–MF-5 in a text-only r3 and obtain freeze approval with immutable protocol/preflight hashes.
  2. Then seek explicit bounded implementation+unit-test+D0 authorization, without converting that into registered Phase 6 approval.
  3. Keep D1 and 3-seed execution behind separate evidence and explicit approvals; stop at caps without rescue tuning or retry.

### Final scope ledger

| Item | Recommendation in this review |
|---|---|
| r2 freeze | **No, not as written.** Text-only r3 first. |
| Implementation + unit tests | **Not yet.** Conditional recommendation after repaired contract freeze and explicit authorization. No implementation/tests run here. |
| D0 | **Not yet.** After repaired freeze/implementation checks and authorization: <=4 configurations, 0 updates, <=15 minutes, debug seed 20261111, no result labels. |
| D1 | **Not approved.** Separate authorization only: 4 arm-seeds ×1 update, <=20 minutes, debug seed 20261111, no outcome labels. |
| 3-seed registered run | **Not approved.** Corrected non-circular checklist, all required evidence, <=96-minute finite projection, then separate explicit approval. |
| Registered maximum if later authorized | 12 trained units, 1,200 updates, <=120 minutes end-to-end, 6 CPU threads, no GPU, no retries/extensions. M remains evaluation-only. |
| Combined accounting if all separately authorized | D0+D1+registered <=155 minutes and <=1,204 updates; not a current grant, and no unbounded substitute probe is included. |
| Compute authorized/performed by this consultation | **0 model forwards, 0 training updates, 0 evaluation/test runs.** Read-only document/hash/length arithmetic only. |
| Test 163 | **Sealed; unopened; no proposed use.** |
| P1 / external APIs | Not used; not proposed. |
| T5Gemma2 | D-108 STOP unchanged; not reopened. |
| Phase 6 / B0-B / B1 / B2 / Stage C | **No execution or downstream approval from this round.** |

### Incorrect premises to avoid

1. A complete chain of `if/else` branches proves correct total semantics and jointly satisfiable acceptance tests.
2. Every listed L-qualified label is reachable through the composed function.
3. Unknown sealed-split provenance or unknown PA path can safely count as valid because they are not explicitly false.
4. Trained three-seed P/PA M_VALID can be established by zero-update D0 or one-update label-free D1 before the registered run.
5. `M_CONTROL_PREFIX753_COHORT15` is full-real-K, a representative 20-doc result, or a confirmatory holdout result.
6. Norm-matched M is completely target-independent, or rtol+atol replay means absolute error <=1e-5.
7. Historical 54 passing tests imply PM implementation or current PM test coverage.
8. P0 sensitivity, PA acquisition, or a favorable exploratory label approves Phase 6 execution or any later stage.

**Bottom line: NARROW; repair the executable contract before freezing it. Do not move scientific thresholds or spend registered compute to resolve text-level contradictions.**