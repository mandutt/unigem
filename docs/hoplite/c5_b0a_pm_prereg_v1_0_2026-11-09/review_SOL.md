# Sol 6.1 medium reviewer — independent v1.0 external review

Reviewer: **Sol 6.1, reasoning medium** (`openai/gpt-6.1-sol`), reviewing the consolidated v1.0 contract independently. Date: 2026-11-09 UTC. **Final recommendation: NARROW. Do not freeze the present text or authorize implementation/D0 yet.** This is a consultation, not execution approval.

## Review basis and method

- Ran `git fetch origin`, then `git pull --ff-only origin main`. Both succeeded; pull reported `Already up to date.`
- Resulting HEAD and `origin/main`: **`78fa7b455c8963e246eb6a3d9206491843e5e3d1`**. The platform checkout remains on its existing `hoplite/parion-d8ede51b` branch; its reviewed content equals the requested remote-main HEAD. No branch switch or commit was made.
- Normative spec content SHA-256: `3f1dcd3156d728eaf4758c36f42805e9d0482156eaa80d3e1498dfbb9ec2039d`.
- Preflight content SHA-256 independently verified: `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`.
- Golden artifact content SHA-256: `9258385a6dedecce16b7de1bc9f18a4e41250258abe2df7d2f9f277a79883e7e`.
- Read the complete external-review request and v1.0 spec, golden vectors, r3.4 synthesis, historical r3.4 plan, preflight, P0 report, complete `runner/c5_mt5_lora_b0.py`, and `eval/tests/test_c5_b0_metric.py`. Inspected the existing Adapter and generic LoRA definitions to understand the runner, not to resume any closed model work. Historical documents were used for traceability, not to fill normative gaps silently. No individual prior-model review was reused.
- Checks performed: read-only source inspection and standard-library, in-memory reconstruction of the three golden digests and preflight count arithmetic. No model/library runner was imported or invoked; no training, evaluation, generation, D0, D1, or test suite was run. The claimed historical 54 passing tests are **not freshly verified**.
- No test-163 contents, P1 data, external APIs, subagents, or additional LLMs were used. The only repository file written by this review is this report.

## Executive conclusion

v1.0 is a substantial consolidation, not merely another precedence layer. The variant/control tensor table, direct L bindings, tri-state consensus, PA validity formula and veto rationale, signal-tail identity, absolute/signed distinction, workload-specific K scope, and committed golden constants are genuine improvements.

However, **the advertised 20-native-document P/PA M calibration cannot be implemented from the advertised exact 1,440-record endpoint set**. Sections 4.5, 5.2 and 8.3 require 20 native documents; sections 9.1 and 9.5 allow only 15 common targets for P/PA. This contradiction also invalidates the claim that the D1/projection workload covers every gate-bearing endpoint. In addition, the training crop statement is not an executable recipe, replay is named but incompletely specified, and several data-to-primitive definitions remain outside the supposedly self-contained authority.

These are pre-result contract repairs, not reasons to abandon the experiment or change thresholds. **NARROW rather than STOP** is appropriate. No trained P/PA/M evidence exists to support a scientific advance or a downstream approval.

| Question | Verdict | Main conclusion |
|---|---|---|
| Q1 | disagree | Not yet a self-contained implementation authority |
| Q2 | conditional | Scalar decision dispatch is coherent; input derivation/fixtures are incomplete |
| Q3 | conditional | Tensor grid is sound; endpoint domain contradicts native calibration |
| Q4 | conditional | Builder formulas improve; replay recipe/comparison pair remain incomplete |
| Q5 | conditional | M-only K closes short-document exclusion; training crop remains ambiguous |
| Q6 | conditional | P/PA validity/veto policy is sound; M data coverage is not |
| Q7 | conditional | Statistical constants/tail identity improve; missing-data/estimand rules need closure |
| Q8 | conditional | Update/time ceilings are arithmetically sound, but timing workload is incomplete |
| Q9 | conditional | All three goldens reproduce; schema/replay validation needs more specificity |
| Q10 | disagree | Not all r3.4 Must-fix items are actually closed |
| Q11 | disagree | No unconditional freeze, implementation, or D0 endorsement now |
| Q12 | conditional | Downstream predicate is appropriately narrow; restore explicit launch checklist |
| Q13 | conditional | NARROW; text-only repairs and renewed freeze decision, not execution |

## Ranked Must-fix before freeze

### MF-1 — Blocker: reconcile native-20 M calibration with exact endpoint identity and timing

**Evidence:** v1.0 §4.5 explicitly says P/PA `m_pass_pos/norm` use 20 native documents; §5.2 and §8.3 repeat this. But §9.1 lists P/PA M targets as `15 common`, and §9.5 requires the exact Cartesian set `15 × 3 × 4 × 2 × 2 × 2 = 1,440`, with each target appearing 96 times. An implementation cannot both reject additional keys and evaluate the missing five native targets. §5.1 also checks only “all 15” real-prefix norms and points `endpoint_ok` at §9.4, although its definition is §9.5.

**Required repair:** Preserve the declared 20-native calibration policy and define its complete gate-bearing key domain. A mixed-cohort representation has `(15 + 15 + 20 + 20) × 3 × 2 × 2 × 2 = 1,680` primary records. Alternatively retain the 1,440 common-cohort records as an explicitly named audit view **plus 240 native-only calibration records**, with exact coverage validation of both. This is a representation/completeness repair, not permission to switch the P/PA gate back to 15 documents. The 15 common targets each have 96 records; each of the other five native targets has 48 in the combined domain.

Propagate that domain to builder validity, `endpoint_ok`, manifests, numerical replay coverage, unit-test expectations, and timing. F/L phase-5 counts remain 120 per arm-seed; P/PA require 160 each. Thus D1 primary coverage is 560 rather than 480 records across four arms. Phase 7 can remain a separately defined 15-common diagnostic domain if that is explicitly intended; if extended to native-20, its P/PA counts become 800 rather than 600. Do not silently choose either diagnostic scope, omit extra scoring/replay cost, or loosen the 96/120-minute limits. State whether any missing native calibration document yields NA/failure; do not silently subset it.

### MF-2 — High: define training separately from donor-cropped evaluation

**Evidence:** §2.3 says **training/eval** uses `K=min(len(real),len(donor))`, but §2.2 prescribes one document per update and does not define a training donor, donor cycling, or an objective involving donors. Existing `train_arm` (`runner/c5_mt5_lora_b0.py`, lines 709–731) uses the complete real `h`, not a donor crop. Existing `evaluate_arm` uses five length-nearest donors and crops each pair. The consolidation therefore either accidentally changes the training protocol or leaves the new one undefined.

**Required repair:** Write distinct training, signal-evaluation, M, and generation recipes. Establish the intended existing training recipe from pre-result protocol provenance; do not let the implementer invent a donor schedule. If donor-cropped training is intentional rather than an editorial conflation, explicitly register that change and its deterministic schedule before results; it is not a silent consolidation edit. Preserve 100 updates, 20-document order, registered seeds/LRs, and all caps.

### MF-3 — High: complete operational identities and data-to-primitive contracts

**Evidence:** §§1–4 name EG2 layer19/native mT5 and generic path flags, but do not fully specify the model/tokenizer identity, adapter architecture/initialization and F/L pairing, native source prefix/tokenization, target construction, donor selection/ties/split restrictions, or exact evidence establishing `assay_path_ok`, `p0_path_ok`, `p_step100_path_ok`, and `pa_step100_path_ok`. “Leakage/mode/metric pass” and “artifact complete” in §14 also have no concrete acceptance checklist. These are not recoverable from a 512-dimensional shape alone.

The existing runner establishes many relevant facts: local `mt5-small`, float32 frozen base, decoder self/cross-attention q/k/v/o LoRA, `summarize: ` native prefix, five nearest-length donors with ID tie-break and self exclusion, same-position CE, and a minimum five copy tokens. Its `copyable_mask` has a specific normalization/lexical rule. `Adapter` is Linear–GELU–Linear–LayerNorm, not an arbitrary 512→512 map. v1.0 does not normatively bind all these mechanics, and the legacy runner is not already a four-arm PM implementation.

**Required repair:** Consolidate the required values/recipes into v1.0, or make narrowly identified immutable code definitions explicit normative dependencies and qualify the claim “this document alone.” Define each path flag's true/false/NA evidence, missing-artifact behavior, and required manifest fields. Explicitly set the standalone adapter to eval during M construction and all evaluation, freeze native encoder/base parameters, specify LoRA/adapter train modes and initialization ordering, and forbid self/cross-split donor leakage. Define whether P/PA donors use native lengths and F/L donors use EG2 lengths, with fixed donor-to-ordinal mappings. Do not copy legacy behavior opportunistically after outcomes.

### MF-4 — High: define replay mechanics, not just its dimensions and digest

**Evidence:** §§11.3–11.4 distinguish 120 donor-free and 600 donor-level records, but do not define which memory tensors a phase-7 donor changes. The §9.4 table is target-prefix/global-mean based and donor independent. Merely adding five donor ordinals could repeat identical scores; alternatively donor-cropping could change the estimand. Neither meaning is specified. `replay_ok = numeric replay pass` does not identify the two score sets, checkpoint states, or reload procedure being compared. Initial phase-5 scoring alone is not proof of replay.

**Required repair:** Define phase-7 real/control memory recipes and whether any donor crop is diagnostic only; it must never replace fixed-prefix primary M scoring. Define a same-checkpoint reference-versus-reloaded recomputation procedure for every gate-bearing primary key, exact key equality before tolerance comparison, a fixed comparison direction/formula for atol/rtol, and mismatch handling. Account for that work in D1 phase timings. Keep D1-debug and registered-final identities separate. Clarify that a synthetic serializer test is not the full-data D1 timing workload.

### MF-5 — High: finish estimands, missingness, fixtures, and launch gates

**Evidence:** §3.5 uses “paired L>F mean” without an explicit difference-of-deltas formula or an explicit definition that seed sign counts refer to L's shuffled-minus-real mean, not L−F. Historical r3.4 §9.2 did state the latter. §6.1 counts valid endpoints but omits a complete donor/seed/finite/copy-coverage membership rule; §10.4 names a 15-document tail but lacks an explicit complete-cohort/complete-seed precondition. F1–F11 still use abbreviated flag assignments without fully specified residual defaults. Fixtures 16–18 supply `validity_status` and `m_evaluable`, which are themselves derived, so they are dispatch fixtures rather than complete raw-path end-to-end fixtures. The detailed historical 3-seed checklist has been replaced by much shorter “D0/D1 gates” bullets.

**Required repair:** Define donor→document→seed aggregation, paired L−F as the paired difference of arm-level deltas if that is the registered intent, and seed signs explicitly. Define retained IDs, finite/copy-token guards, incomplete donors, missing registered seeds, P/PA complete-native-20 behavior, and tail NA behavior; no seed/document substitution or available-case rescue. State whether small-N flags are descriptive partial-cohort flags or forced NA, keeping that choice consistent with the required reachability of small-N-with-signal labels. Give complete fixtures, path-flag defaults, and one canonical NA encoding. Restore an explicit D1/3-seed launch checklist: frozen spec/code/preflight identities, passing new tests, D0 artifact, separately approved D1 artifact, all measured workloads and finite projection ≤96, complete manifest/replay plan, no parameter changes, explicit separate run approval, and sealed-data assertions.

## Q1. Self-containedness

- **Verdict: disagree.**
- **Evidence:** §0.1 and §16.2 assert sole implementation authority, but MF-1 gives a direct internal contradiction. MF-2/MF-3 identify operational choices not fixed by the document. The stale `endpoint_ok = §9.4` in §5.1 points to the tensor table, not §9.5's endpoint predicate. Historical-only status is clear; it does not make omitted definitions executable. There is no reason to inherit missing rules automatically from r3.x.
- **Next steps:** (1) Repair MF-1 and the cross-reference. (2) Consolidate/bind the missing mechanics in MF-2/MF-3. (3) Freeze content and commit hashes only after a consistency review of the corrected single authority.

## Q2. Decision contract

- **Verdict: conditional.**
- **Evidence:** §§3–7 give coherent typed scalar dispatch: false-dominant ANDn, consensus rather than AND for L, all nine L pairs, invalid-versus-NA tiers, and separate validity/control/signal outputs. For example true/false is L-consensus NA but copy_only true; false/NA cannot become MEAN_CONTRAST_ONLY. Control availability false/NA intentionally maps to M_NOT_EVALUABLE; valid P/PA plus false calibration maps to M_CONTROL_INVALID. Fixtures 16–18 are internally consistent at their stated intermediate-input boundary. Small-N precedence does not conceal the separately reported validity axis. However, MF-3/MF-5 prevent end-to-end totality from raw artifacts, and abbreviated F1–F11 do not fully specify standalone test inputs.
- **Next steps:** (1) Define the primitive flag/evidence schema and defaults. (2) Provide full raw-input versions of F1–F11 and 16–18, preserving existing outputs. (3) Require synthetic per-axis ANDn 2/4/5, nine-pair, reachability, small-N triple, immutability, and invalid/NA tests before D0; no full Cartesian explosion is necessary.

## Q3. M variant × memory_kind

- **Verdict: conditional.**
- **Evidence:** §9.4 correctly binds M_POS_MEAN control to the global train mean and M_NORM control to its target-magnitude-scaled version, with the same target real prefix for both. §9.6 correctly separates delta_pos and delta_norm, removes delta_memfree, and requires both predicates. The two controls are distinct definitions, not statistically independent experiments; norm equality can legitimately make them coincide for a target. Repeated real-CE values across variant keys are also legitimate. The 1,440/96 arithmetic is correct **only for the 15-common audit domain**, not all native-20 calibration inputs.
- **Next steps:** (1) Repair the gate-bearing key domain under MF-1. (2) Test tensor binding and independent Boolean pass evaluation, allowing legitimate numerical coincidences. (3) Test exact missing/duplicate/wrong-target keys rather than counts alone, including the extra native keys.

## Q4. M builder / M_NORM / endpoint / replay

- **Verdict: conditional.**
- **Evidence:** §§9.2–9.3 give a useful all-arm builder: train-only eligible contributors, F/L 753, native 512, P identity, same-adapter target norm ratio, no primary donor crop. Preflight confirms 16 F/L and 20 native contributors. Zero/nonfinite norms must block evaluation, not be regularized into a different control. But native-20 target-norm coverage is not represented; standalone adapter eval is only implicit; and phase-7/reload semantics are missing (MF-4). Serialization of donor ordinals is not a memory-construction recipe.
- **Next steps:** (1) Make model/adapter eval and native-20 norm/endpoint checks explicit. (2) Specify reference/reloaded primary replay plus the diagnostic donor-memory table. (3) Test identity, shapes, train-only contributors, per-target scaling, zero/nonfinite rejection, and replay mismatches with synthetic tensors before model mechanics debug.

## Q5. F/L memory length scope

- **Verdict: conditional.**
- **Evidence:** §2.3 genuinely closes the mistaken requirement that every workload have 753 memory positions. Verified preflight counts: four train and five val EG2 documents are below 753; 15 val documents meet 753, and only 14 meet 754. M-only prefix checking therefore avoids an impossible 20-document training/generation constraint. All-20 generation at max_new_tokens 256 is appropriate as non-gating telemetry. The unresolved point is specifically the combined “training/eval donor-crop” statement versus the existing full-real-memory training loop, not the M-only rule itself.
- **Next steps:** (1) Resolve MF-2 before code is written. (2) Add synthetic short-target/short-donor tests proving no padding, dropping, reordered training, or primary-M donor crop. (3) Keep 20-document generation distinct from the 15-document L signal gate.

## Q6. P/PA

- **Verdict: conditional.**
- **Evidence:** §4.5 directly defines both 100-step validity predicates on 20 native documents: copy mean ≥.05, copy CI lower >0, full mean >0, full CI lower >0. §5.3 correctly treats PA failure as a joint-calibration veto, not proof that native memory is intrinsically invalid; PA_RETENTION is nullable and non-gating. §8.2 correctly warns that native 512 and EG2 753 are not direct retention comparators. Preflight confirms all 20 native source lengths at 512. But the native M-pass inputs required by §8.3 are absent from the exact §9.5 domain.
- **Next steps:** (1) Preserve native-20 validity and calibration while repairing endpoint coverage. (2) Define complete-native-cohort missingness and initialization/mode rules. (3) Test PA acquisition failure and calibration failure separately; neither PA_RETENTION nor P0 can rescue either gate.

## Q7. Statistics / tail

- **Verdict: conditional.**
- **Evidence:** §10 fixes document-level paired bootstrap, 1,000 resamples, percentile 2.5/97.5, seed 20261109, seed-average first, and documents_positive as strictly-positive document count. §3.5 explicitly disallows 2-of-available in place of the three registered seeds 20261108/09/10. §10.4 now unambiguously makes the hard tail gate **L copy shuffled-minus-real signal, variant NA**, not either M tail. Absolute share, ID tie-break, exactly three removed documents, zero-denominator NA and ordered tail conditions are useful and executable on complete inputs. This tail choice is a substantive explicit clarification relative to the synthesis's suggested M_POS_MEAN tail; it should be recorded as such, not described as identical to that suggestion.

  The report's P0 means/CIs are historical sensitivity evidence only: train +3.7617 [1.8917,5.6050], val +5.2375 [2.5013,8.0753]. The request's val median 2.9739, signed .4862 versus absolute .43355, and untrained CE 12.7/13.2 exceeding ln|V|≈12.43 reinforce the narrow interpretation. v1.0 labels absolute .43355 for val20 and .455 for common15 correctly; neither P0 cohort is trained-L gate evidence. Missing-data/paired-estimand rules still need MF-5. An incomplete 14-document tail must not be silently certified false as a complete 15-document result.
- **Next steps:** (1) Finish MF-5 and state tail aggregation after seed averaging. (2) Bind bootstrap RNG/resample order and percentile implementation for reproducibility; test boundaries and missingness without changing any threshold. (3) Retain raw tail IDs/sums, both shares, document counts, and per-registered-seed means; never reuse the P0 helper's mislabeled seeds_positive field.

## Q8. D0/D1/cap

- **Verdict: conditional.**
- **Evidence:** §11's resource arithmetic is correct: registered 12 units ×100 =1,200 updates/120 min; D0 zero updates/≤4 configs/≤15 min; D1 four arms ×one debug seed ×one update =4 updates/≤20 min; prospective total 1,204 updates/155 min. Debug seed 20261111 is outside the registered set. Six CPU threads, no GPU, no retries/extensions, and finite nonnegative projection ≤96 provide a 24-minute headroom against the registered hard cap. All eight phases, including generation and overhead, are named, and step0-before-update/restored-state is explicit.

  The 120/600 record calculations are locally correct for 15 targets. They do **not** prove coverage of native-20 calibration, nor specify actual forward counts: one forward can supply copy and full CE, and variant-independent real CE may be cached. MF-1 and MF-4 therefore require workload correction before a valid projection. A single-update timing is an admission screen, not a guarantee of 100-update wall time. “No labels” must mean no scientific decision/status labels; CE workloads necessarily use teacher-forcing target labels.
- **Next steps:** (1) Correct full-workload D1/projection coverage without raising caps. (2) Specify execution order, state restoration/RNG handling, timing boundaries, and actual scoring/replay work behind the record counts. (3) Keep D0 non-projective and require separate D1 and registered-run approvals; abort rather than retry or trim workloads.

## Q9. Hash/golden

- **Verdict: conditional.**
- **Evidence:** Independently reconstructed the supplied little-endian framed state and sorted compact-JSON replay **in memory using the Python standard library**, not future implementation code. All expected constants matched:
  - state: `43ecb58e197d5789df0a9dbbc67beba11538b8063c3da8ac46f96e1e95d65712`;
  - empty: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`;
  - replay: `c43ea35c46c51a0e82cebe5764a989d1b67012b2690246a0f89a94dff7851667`.

  §12 correctly separates state frames, donor_sort (-1/null versus 0..4), exact artifact hashes, and numerical tolerances. Equal tolerance-level results need not have equal hashes. Remaining schema details matter: make donor_id a required serialized null/integer field and donor_sort sorting-only; define exact serialized fields and list ordering, supported dtype naming, adapter/LoRA key namespacing, duplicate rejection, and canonical string/float encoding/runtime. The vector's ASCII names and simple finite floats do not cover every encoding corner. Most importantly, a correct hash does not establish a correct replay population or independent recomputation.
- **Next steps:** (1) Preserve immutable expected constants and add permutation/duplicate/missing/null-vs-omitted and dtype/namespace tests. (2) Complete the exact schema and same-state comparison contract in MF-4. (3) Record frozen model/config/mode identities separately; never equate debug and final hashes or replace numeric replay with a file-integrity check.

## Q10. Remaining Must-fix

- **Verdict: disagree** with the proposition that every r3.4 Must-fix is closed.
- **Evidence:** Text-level closure is real for variant binding, direct L binding, PA_VALID/veto, M-only K scope, documents_positive, explicit signal tail, absolute/signed distinction, and committed goldens. Full-K is safely removed from gate authority; there is no need to invent a new secondary gate. But P/PA cohort closure contradicts endpoint closure, replay-domain naming is not replay mechanics, and consolidation omits previously explicit seed-sign/launch requirements. See ranked MF-1 through MF-5 above.
- **Next steps:** (1) Repair those five contract issues in rank order, without new outcome-dependent choices. (2) Update the traceability table to distinguish actual closure, intentional semantic clarification, and remaining work. (3) Re-review only the changed contract and affected cross-references before freeze.

## Q11. Freeze / implementation approval

- **Verdict: disagree** with unconditional approval of the current text.
- **Evidence:** §16.1 says no code before freeze. MF-1 alone prevents a correct implementation from satisfying all normative clauses, so endorsing implementation now would delegate an unregistered domain choice to the coder. Historical metric tests cover alignment, generation telemetry, mode symmetry, donors and descriptive P0 decisions; they do not demonstrate PM decision totality, native-20 M coverage, or reload replay. They are also guarded by local-model availability, so a future green run must disclose skips.
- **Next steps:** (1) Correct/freeze the contract first, including immutable hash identities and exact expected synthetic cases. (2) Then implement and run synthetic decision, stats, M-domain/builder, hash, replay and zero-margin tests plus relevant existing regressions; all must pass before D0. (3) Seek a separate narrow approval for capped zero-update mechanics only after those prerequisites; do not treat this report as granting it.

  **Mandatory pre-D0 tests:** ANDn 2/4/5 false+NA; nine L pairs; F1–F11 and full-input 16–18; every label and small-N triple; copy ≥.05/full >0/CI lower >0 boundaries; native20 versus common15 key coverage; missing seed/donor/nonfinite/copy-token guards; P identity and same-space M_NORM; zero norms and K=754/14-target abort; golden hashes and exact-schema violations; same-state numeric replay pass/fail independent of SHA equality; D0 zero-step/no-decision-label and separate launch/cap guards. These are requirements for future work, not claims that tests were run here. Before implementation, their expected inputs/outputs must be specified; runnable tests naturally accompany implementation after freeze.

## Q12. B0-B / D1 / 3-seed boundaries

- **Verdict: conditional.**
- **Evidence:** §14's downstream logic and §16.3's approval exclusions are appropriately conservative. Restated with v1.0 labels, **eligibility to request separate B0-B approval**, not authorization, requires:

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS
AND signal_status == EXPLORATORY_L_SIGNAL
AND m_valid is true
AND n_signal == 15
AND tail_driven is false
AND leakage/mode/metric checks pass
AND required artifacts are complete
AND separate B0-B preregistration and explicit approval exist
```

  All conditions must be known true; NA fails eligibility. m_valid checks native P/PA calibration; M scope remains the L prefix753/common15 control. P0, full_k_secondary and PA_RETENTION cannot substitute. The boundaries are scientifically adequate in intent, but concrete artifact acceptance and the detailed registered launch gate need restoration under MF-3/MF-5. An exploratory L label alone is never a downstream grant.
- **Next steps:** (1) Restore explicit launch/artifact predicates. (2) Test rejection of tail true/NA, missing artifact, debug-seed contamination, and absent separate approval. (3) Keep D1, three-seed execution, and B0-B distinct approvals; retain B1/B2/Stage C as unapproved regardless of these outcomes.

## Q13. Final verdict and freeze scope

- **Verdict: conditional — NARROW.**
- **Evidence:** Genuine consolidation plus independently matching artifacts merits a bounded repair path rather than scientific STOP. But MF-1–MF-5 prevent present freeze and end-to-end implementation authority. The absence of trained P/PA/M results is an opportunity to repair the contract prospectively, not permission to infer that its calibration will pass.
- **Next steps:** (1) Make only the ranked pre-result contract repairs and review the corrected domain/workload. (2) Record an explicit freeze/approval decision before implementation, then establish passing new tests before any D0 mechanics. (3) Keep all later execution gates separate and retain original caps/thresholds/seeds/donors/steps/LRs; any genuinely new scientific protocol belongs in a separately approved preregistration, never a post-result adjustment.

## Final disposition

- **Final verdict:** **NARROW**.
- **v1.0 freeze:** **No, not this content hash.** Repair MF-1–MF-5 first; freeze the corrected spec's commit and content hashes only after renewed explicit acceptance.
- **Implementation + unit tests:** **Not endorsed now under §16.1.** After corrected freeze and explicit authorization, implementation plus synthetic/unit/regression verification is the next bounded work item.
- **D0:** **Not approved now.** Prospective ceiling only: zero optimizer updates, ≤4 configs, ≤15 min, debug seed 20261111, no scientific decision labels, no timing projection, not a result; requires frozen contract, passing tests and explicit authorization.
- **D1:** **Not approved.** Separate future approval, four debug units, one update each, ≤20 min, complete corrected eight-phase workload, no scientific labels/results or registered-seed substitution.
- **Three-seed run:** **Not approved.** Only after its own launch checklist, approved D1 and finite nonnegative full-workload projection ≤96 min, plus explicit authorization. Registered cap remains 1,200 updates/120 min, CPU six threads, no GPU, no retry/extension.
- **Maximum compute authorized by this consultation:** **Zero training updates and no model evaluation/debug execution.** Only document/source review, in-memory hash/arithmetic checks, and this report were performed. The 1,204-update/155-minute combined D0+D1+registered ceiling is prospective accounting, **not a grant**; corrected coverage must fit it or stop.
- **Prohibited scope:** No Phase 6 execution approval; no B0-B/B1/B2/Stage C approval or automatic progression; no P1 or external data/API work; no reopening T5Gemma2 (**D-108 STOP remains**); no post-result threshold/seed/donor/step/LR tuning.
- **Test 163:** **Sealed, unopened, excluded.** No use proposed.
- **Must-fix ranked:** (1) native20 M endpoint/timing contradiction; (2) training-versus-eval crop recipe; (3) operational identities/path evidence/manifest completeness; (4) diagnostic and same-state replay mechanics; (5) estimands/missingness/full fixtures/launch checklist.
- **v1.0 self-contained:** **Not yet.** The finite scalar dispatch is much closer than the complete data-to-decision protocol.
- **Incorrect premises to avoid:** 1,440 is not complete native20 M coverage; 120/600 timing does not by itself cover that coverage or prove reload replay; passing historical metric tests is not PM implementation validation; P0 sensitivity is not trained calibration or content-use evidence; a correct hash is not scientific validity; a reviewer recommendation is not execution authorization.