# Independent external review — C5 P/M prereg v1.0.5

- Reviewer: OpenAI Sol 6.1 (`openai/gpt-6.1-sol`), independent new review round.
- Date: 2026-11-09 UTC.
- Review basis: current `origin/main`, **`d38264fcb713bb43e718fb7b89a46ed2c403d6b6`**.
- Synchronization: `git fetch origin` succeeded; `git pull --ff-only origin main` succeeded, reporting `Already up to date.` HEAD equals origin/main. Initial worktree was clean.
- Workspace branch is `hoplite/smyrna-857ae59e`, at that same commit; no checkout or branch change was made. The request document's `50653b5` is historical metadata, not this review's basis.
- Consultation only. Only this permitted report was written. No subagents or additional LLMs. The supplied v1.0.4 synthesis was historical context, not an answer reused for this review.
- No training, model evaluation, generation, D0, D1, or unit-test execution. No model imports. No P1 data used; no sealed test-163 data or split file opened. Reading the requested P1 attestations is not using P1 data.

## Executive verdict

**NARROW — documentation clarification and freeze preparation only.**

v1.0.5 substantially repairs the ten reported residuals. The freeze schema, three-field diagnostic numeric replay, seed-count naming, golden-domain separation, record schemas, and P1 contradiction rules are present. All five supplied golden digests independently reproduce. Primary-record arithmetic is correct.

However, §9.6.1 does not unambiguously cap the F/L phase-7 `real_prefix` at `K_M`. Its literal `K_d=min(len(real_prefix),len(donor_prefix))` can exceed the 753-row stored controls. Python slicing then silently leaves the control shorter than real/donor. A second implementation can instead read “prefix” as the already-capped §9.3 `real_prefix_t`. Those implementations produce different diagnostic CE/deltas while each can pass its own numeric replay. This is a prospective contract clarification, not evidence of a failed experiment.

**Do not freeze or start implementation/D0 as-is.** Resolve the prefix contract before freeze and then perform the actual freeze handoff. No change to scientific thresholds, seeds, donor selection, optimizer updates, or learning rates is proposed. No trained P/PA/M result exists in the reviewed evidence.

## Evidence and verification limits

Directly reviewed the request, full v1.0.5 plan, freeze template, golden JSON, v1.0.4 synthesis, preflight, P0 JSON, both P1 JSON files, registry v2, entire B0 runner, and metric tests. Inspected the source-bound helper definitions and relevant historical v1.0.4 differences. No other reviewer's individual answer was consulted.

Read-only checks used Python standard-library JSON parsing, SHA-256/byte framing, length/donor arithmetic, and Cartesian key enumeration. These are static checks of supplied artifacts, not training or evaluation.

| Check | Observed result |
|---|---|
| State fixture | `43ecb58e197d5789df0a9dbbc67beba11538b8063c3da8ac46f96e1e95d65712` matches |
| Empty state | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` matches |
| Three-record replay base | `c43ea35c46c51a0e82cebe5764a989d1b67012b2690246a0f89a94dff7851667` matches |
| Four-record key coverage | `8277a713fd52b2ba8c5c3c859c83fd78593aa5a381f8640448e2128a97af7a20` matches |
| Synthetic control framing | `6b50c226ecc402323787bd25b20e57fe57376caeb925c040b57985ccc0ec1938` matches |
| Preflight content SHA-256 | `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` matches |
| Primary keys, static enumeration | 1,680 unique; F=360, L=360, P=480, PA=480; one seed=560; common/native-only target multiplicity=96/48 |
| Actual freeze manifest | Absent; only `status:template` JSON exists |
| P1 postrun inventory | `status:not_run`, empty; not evidence of completed coverage |

Current content hashes, **not a freeze declaration**:

- Plan: `a949b767e10f290074fa2275457dd0ab9ae554a20ddb8337316d1b3a8a4e9931`.
- Golden JSON: `b6251a0768ab28fa28870236abd575a0d3614fcd87b1808266948f6d0294c64f`.
- Frozen-intended P1 attestation: `69af129a4f58f7400189c361ba2447f12e17d35f012d7a36c26efdf485a3a2dc`.

Any prospective plan correction requires a new plan hash. Do not copy these values into a manifest for different bytes.

## Q1. Are the ten residuals closed?

**Verdict: conditional — nine closed at the document-contract level, one partial.** “Closed” does not mean implemented, tested, frozen, or approved to execute.

| # | Residual | Status | Evidence / remaining distinction |
|---|---|---|---|
| 1 | Freeze manifest | closed, schema-level | §16.2, lines 1644–1670, defines path, status, plan/commit/P1/golden/preflight/helpers/seeds. Actual freeze remains a handoff prerequisite. |
| 2 | Phase-7 baseline/delta numeric replay | partial | §9.6.1 and §11.4 now explicitly replay `ce`, `baseline_ce`, `delta`, and isolate `diagnostic_replay_ok`. The phase-7 input-prefix bound still needs MF-1 below. |
| 3 | `registered_seeds_positive` | closed | §§4.5, 10.2, 13.3 distinguish registered seed means from P0 document positives. |
| 4 | Key-coverage golden | closed | §12.3 and JSON explicitly separate four-record fixture from 600-record numeric-only diagnostics. Digest reproduces. |
| 5 | Stored/hash record | closed | Lines 1117–1118 and §12.2 distinguish nested stored records from flat eight-field hash records. |
| 6 | P1 contradiction/registry | closed, contract-level | §1.5 adds explicit contradictions and registry coverage; registry v2 includes checkpoints, controls, diagnostic files. Postrun is correctly still a placeholder, not a completed audit. |
| 7 | `donor_sort` ordering | closed | Lines 1436–1438 and golden ordering agree: null serialized, internal -1 for sorting. |
| 8 | M_NORM truncation | closed as a scaling rule | Lines 1093, 1104–1105 say scale at K_M, truncate without renormalization. This does not independently resolve the missing prefix cap under #2. |
| 9 | Checkpoint base | closed | Line 1309 gives full provenance base and per-arm/seed path; no single checkpoint. |
| 10 | Informational flag/line count/prefix | closed | Line 727 makes MARGINAL informational; plan is actually 1,721 lines; line 1403 separates logical `control/` from filesystem `control_manifest/`. |

Next steps:
1. Resolve MF-1 before freeze without changing the registered primary assay.
2. Keep schema closure distinct from subsequent implementation tests and artifact production.

## Q2. Is v1.0.5 self-contained?

**Verdict: conditional.** It is substantially a single protocol authority, not a standalone implementation package.

Evidence: §§2.5–2.7 specify model/tokenizer, CE alignment, copy mask, donors, modes, initialization and paths; §§3–14 give dispatch, statistics, replay and gates. §17.1 deliberately binds external helper source files, and the plan also depends on the preflight and golden JSON. The inspected `Adapter`, `make_labels`, `load_layer_cache`, `LoRALinear`, `attach_decoder_lora_mt5`, and `native_memory` definitions support those interfaces. Earlier preregistration prose should not be needed as implementation authority. The phase-7 prefix identity is still implicit.

The current runner is historical two-arm machinery, not a completed four-arm v1.0.5 runner. Its `set_training_mode` accepts only `frozen`/`lora` and assumes an adapter; P needs new handling. Its legacy bootstrap seed is 20261108. Its CLI readers load full JSONL/split files. They must not be blindly invoked under this review's no-test-read constraint. No such reader was invoked here.

Next steps:
1. Resolve the prefix identity; bind the helper revisions and external artifacts through the real freeze manifest.
2. Implement the four-arm protocol from that frozen contract, rather than treating the existing CLI as conformant.

## Q3. Is the freeze schema usable and non-self-referential?

**Verdict: conditional — yes as a schema; no actual frozen handoff yet.**

Evidence: §16.2 names `docs/plan_c5_b0a_pm_prereg_v1_0_5_FREEZE.json`; the template has null hash/commit fields and `status:template`. Plan hashing excludes the manifest, so there is no content-hash cycle. A commit containing the final plan/helpers can be referenced by a subsequently created manifest; that commit need not contain the manifest that names it. Full Git revisions bind helper content; fixed plan, P1, golden, preflight hashes and registered seeds provide the specified source bindings.

`assay_path_ok` becomes assessable only against a valid, resolved freeze and matching P1/preflight. A template, unresolved revision, null hash, or mismatched bytes must not be accepted as a successful frozen handoff. Other step100 flags remain NA at D0 because trained artifacts do not exist; that must not prevent separately assessing the D0 mechanics/path checks.

Next steps:
1. After MF-1 and review, select a commit containing the final normative bytes and helper sources; create the separate populated manifest with `status:frozen`.
2. Before D0, verify all referenced revisions/paths/hashes and exact seeds; reject the template as a freeze.

## Q4. Is phase-7 numeric replay executable and independently auditable?

**Verdict: conditional.** The old missing-field audit is repaired; the tensor-prefix ambiguity remains.

Evidence: lines 1110–1114 recompute baseline CE in phase 7 and prohibit reuse of phase-5 K_M CE. Lines 1313–1315 require all three numeric fields at atol=1e-5/rtol=1e-4 and separate `diagnostic_replay_ok`. The flat hash projection excludes baseline/delta, which is acceptable because they are explicitly recomputed and compared, not asserted protected by the CE-only hash. Reproducibility also requires restoring the checkpoint/control tensors and eval modes, not merely hashing records.

**Counterexample from the frozen preflight, without model execution:** target `REPORT-news_r-01518-00001` has length 830. Its five length-nearest donors have lengths 807, 806, 796, 794, 792. If `real_prefix`/`donor_prefix` in lines 1087–1089 mean full arm memories, all five K_d values exceed 753. The controls at lines 1092–1093 still have only 753 rows. Across the 75 F/L target–donor pairs, 64 have literal uncapped K_d>753. The present assertion repeats the definition's upper bound and cannot detect this.

This does not make a model call impossible: unequal-length CE calls can run. It makes the intended common-prefix diagnostic non-unique. If `real_prefix` means the §9.3 already-capped `real_prefix_t`, the mismatch disappears, but that identity must be explicit.

Next steps:
1. Resolve MF-1 prospectively. State the exact prefix tensors and assert equal first dimensions for real, donor, and both controls in phase 7.
2. Later add synthetic tests for long donors, short donors, no-renormalization, independent baseline/delta corruption, and diagnostic-only failure isolation. Do not run model evaluation now.

## Q5. Does seed naming eliminate the collision?

**Verdict: agree.**

Evidence: §10.2 explicitly defines registered seed means separately from document positives and prohibits legacy bootstrap reuse. The existing helper at runner lines 384–398 returns `seeds_positive=int((arr>0).sum())` on document deltas, with seed 20261108. P0's 14/20 and 18/20 are document counts, not 14 or 18 training seeds. §3.5 requires all three registered seeds and at least two positive seed means for L; §4.5 deliberately does not add that conjunct to P/PA calibration.

Line 1570, “no stale `registered_seeds_positive`,” should be read as no stale value, not a ban on the required field. It is awkward editorial wording; it does not outweigh the repeated affirmative field definition. Prefer spelling out “no legacy `seeds_positive` in registered stats; no stale registered counts” when editing for MF-1.

Next steps:
1. Implement separate document/registered-seed counters and test 2-of-3 versus missing-seed NA.
2. Preserve the preregistered bootstrap seed 20261109 and document-level pairing.

## Q6. Are the golden domains distinct?

**Verdict: agree.**

Evidence: the golden JSON has distinct `replay_base`, `key_coverage_golden`, `phase7_diagnostic`, and `control_manifest_golden` objects. Base=3 records, coverage=4 records, diagnostics=600 per arm-seed and numeric-only, control fixture=[1,1] synthetic framing. Real controls are [753,512] or [512,512], not represented by the small fixture. All fixture digests independently reproduce; none is a trained-result digest.

Next steps:
1. Test fixtures as immutable constants, with permutation and missing/duplicate-key failures; include null-versus-zero donor identity tests.
2. Keep the fixture check separate from exact real diagnostic coverage and numeric replay; do not compare a 600-record file to the four-record digest.

## Q7. Are P1 attestations and registry fail-closed, and is coverage real?

**Verdict: conditional — contract yes, completed postrun coverage no.**

Evidence: §1.5 and §4.0 make known P1 use, test reading, or any ID outside the preflight train20∪val20 allowlist a failure, with missing/malformed evidence NA. Neither false nor NA permits a valid assay. Unknown `note` is harmless metadata, not an override. The supplied frozen-intended attestation has both flags false and an empty inventory. The separate postrun JSON is `not_run` with an empty inventory. Registry v2 enumerates checkpoint, map, control-manifest/tensor, phase-7, and attestation patterns. It is not a populated audit and cannot establish non-access.

The registry contains patterns, not concrete per-unit file coverage. On an actual run, expected domains must be expanded from the registered arms/seeds/target IDs, not just from whichever files happen to exist. Otherwise missing files disappear from a glob. Independent endpoint/checkpoint completeness requirements must still fail. The postrun inventory must also list every inspected Phase 6 artifact, including primary records, even where a registry pattern is not enumerated for that artifact. Do not interpret “audit-only” to excuse known-use contradictions.

Next steps:
1. Preserve the frozen file/hash and keep postrun inventory separate; never scan sealed test IDs for membership.
2. Later audit concrete registry expansion and all inspected artifacts; missing artifacts/known-use cannot become a valid result through an empty inventory. No postrun success is asserted now.

## Q8. Are checkpoint naming and primary counts correct?

**Verdict: agree — contract/arithmetic, not observed checkpoints.**

Evidence: §11.4 gives `reports/provenance/C5_b0a/checkpoints/{arm}/{seed}.pt`. §12.1 specifies the exact 12-key arm/seed state-hash map and tensor-frame hashing, excluding frozen base. F/L: 15×2 variants×2 endpoints×2 memory kinds=120/unit; P/PA: 20×2×2×2=160/unit. Across three seeds: 360+360+480+480=1,680. Common targets occur 96 times; five native-only targets occur 48 times. Static enumeration reproduced these numbers.

§13.2's shorthand “target appears 96 times” is correct for common targets only; the authoritative mixed-domain §9.5 explicitly says 96/48. Implement the mixed domain, not an all-targets-96 assertion. The metric test file does not establish checkpoint/replay conformance.

Next steps:
1. Test exact map/key-set equality, not only counts, and verify restored states against their state hashes.
2. Test missing/extra units and P/PA native-only targets. No checkpoint success is claimed before artifacts exist.

## Q9. Are D0/D1 and compute boundaries coherent?

**Verdict: agree — specified limits are coherent; measured feasibility is deferred.**

Evidence: §11.2 permits at most four zero-update D0 configs, one per arm, debug seed 20261111, ≤15 minutes, no decision/signal labels, no timing projection. §11.3 separately defines four D1 units, one update per arm, same debug seed, ≤20 minutes and eight required workload phases. Its listed phase-1/update versus step0 ordering is qualified at line 1293: step0 must be before update or restored. Target-token labels needed for CE are not decision labels.

Phase 5 is 120/160 per unit, 560 for one debug seed; phase 7 is 600 per arm-seed, hence 2,400 over four D1 arms, not 600 total. Registered phase 7 would be 7,200 diagnostic records. §11.5 explicitly budgets both initial primary CE and primary replay, plus diagnostics. All phases and overhead must be measured; no D0 extrapolation. T_proj must be finite, nonnegative and ≤96 minutes before any separately approved registered run; registered hard abort is 120 minutes, CPU six threads, no GPU/retry/extension.

Next steps:
1. Keep D0, D1 and registered approval records separate; this review grants none of their execution.
2. If subsequently approved, use actual complete D1 measurements, including repeated primary replay, to evaluate the unchanged projection gate.

## Q10. Ranked remaining Must-fix

**Verdict: agree — a narrow, concrete repair is still required.**

### MF-1 — Define the phase-7 prefix bound before freeze (medium; normative blocker)

Affected: plan §9.6.1, lines 1087–1095, linked to §9.3 and stored [K_M,512] controls.

Define `real_prefix` explicitly as the capped `real_prefix_t`, or state an equivalent K_d bound that includes K_M. For the intended equal-length prefix contrast, an explicit recipe would cap K_d by K_M and assert that both controls, real and donor actually have K_d rows. Preserve the K_M-based M_NORM scale with no K_d renormalization, the frozen donor selection/order, the 600-record domain and diagnostic-only role.

The protocol owner must confirm that this is the intended clarification. Do not silently choose a cap in implementation. If unequal-length full-memory diagnostics were intended instead, that choice must be explicitly preregistered/reviewed before results rather than being inferred by a coder. This issue is inherited by the phase-7 recipe; the v1.0.5 numeric-audit extension does not itself create it, but also does not close it.

### MF-2 — Complete the actual freeze handoff before implementation/D0 (operational prerequisite)

The absence of `_FREEZE.json` is expected for a review candidate, not a newly discovered schema defect. Nevertheless, a template with null values is not approval or an assessable frozen binding. After MF-1, a reviewed final plan commit and fully populated, independently checked manifest are required. The plan hash must reflect the corrected bytes.

Nonblocking editorial follow-ups: clarify “no stale” seed wording; qualify the §13.2 96-count shorthand as common-target-only; keep fixture verification distinct from real phase-7 coverage. Do not inflate these into new scientific decisions.

Next steps:
1. Make the prospective MF-1 text clarification and review it; no code or execution in this consultation.
2. Only after resolution and explicit authorization, complete MF-2 and proceed through the staged approval process.

## Q11. Can freeze, implementation/unit tests, and D0 be approved now?

**Verdict: conditional — not as-is.**

§16.1 says no code before freeze. MF-1 prevents a unique phase-7 contract, and no actual manifest exists. I recommend a documentation-only correction now. After its acceptance and actual freeze, a separate explicit decision could permit implementation, synthetic unit tests, and bounded D0. This report does not execute or confer that approval.

Required implementation tests before D0 (not tests claimed to have run):

- §13.1: false-dominant ANDn(2/4/5), tri-state precedence, F1–F11, all nine L pairs, fixtures 16–18, all labels reachable, small-N triple preservation and input nonmutation.
- §13.2: four-arm builders, P identity, zero/nonfinite norms, exact 1,680 mixed keys and 96/48 multiplicities, no cohort substitution, independent POS/NORM outcomes.
- §13.3: bootstrap seed 20261109/1,000 samples, seed-average-before-document-bootstrap, paired IDs, missing registered seeds NA, document versus seed counters, tail absolute share/ties/zero denominator.
- §13.4: five fixed golden digests, null-versus-zero key identity, exact 12-key checkpoint map and tensor-frame integrity, numeric-versus-exact-hash distinction, primary/diagnostic isolation and debug/final separation.
- New regression for MF-1: F/L target and donor both >753, donors <753, and native512; equal tensor lengths; no M_NORM renormalization; baseline/delta-only corruption must fail diagnostic replay without rewriting primary replay status.
- Freeze/P1 negative cases: template/null/mismatched bindings, malformed/missing manifests, either known-use flag true, outside-allowlist IDs, benign notes, incomplete concrete inventory and missing expected files.
- Source-compatible metric checks: same-position token CE, copy minimum/mask, no extra shift, correct LoRA/base/adapter modes and inventory. The existing metric tests are source evidence only; their class can load a model and perform forwards, so they were not run here.

Next steps:
1. Repair and freeze first; then seek explicit implementation/test/D0 authorization.
2. Require passing synthetic checks before any approved model-facing D0 mechanics; no decision labels or optimizer update in D0.

## Q12. Are downstream boundaries sufficient? Restate B0-B.

**Verdict: agree.**

D1 and registered three-seed execution are separate decisions under §§11 and 16.3. B0-B requires all of the following (§14), not merely an attractive L label:

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS
AND signal_status == EXPLORATORY_L_SIGNAL
AND m_valid == true
AND n_signal == 15
AND tail_driven == false
AND leakage/mode/metric checks pass
AND artifacts complete
AND separate B0-B preregistration and approval
```

`n_signal>=15` means exactly 15 because its domain ends at 15. Signal-tail `true` or NA blocks; M-tail telemetry does not replace it. Invalid/unassessable validity, M_NOT_EVALUABLE, calibration failure, small-N, or copy-only/full-only labels cannot pass. `EXPLORATORY_L_SIGNAL` alone grants nothing. Scope remains `M_CONTROL_PREFIX753_COHORT15`; P0, full_k_secondary and PA_RETENTION are not substitutes.

Next steps:
1. Enforce separate explicit D1, registered-run, and downstream decisions even after mechanics pass.
2. Keep B0-B/B1/B2/Stage C unapproved, test163 sealed/P1 unused, and T5Gemma2 D-108 STOP.

## Q13. Final decision and freeze scope

**Verdict: conditional; final recommendation NARROW.**

| Scope | This review's disposition |
|---|---|
| v1.0.5 freeze | Hold until MF-1 is resolved/reviewed; then actual manifest handoff required |
| Implementation + unit tests | Hold under §16.1; prospective approval requires accepted correction and freeze |
| D0 | Hold; later separate bounded authorization only after freeze/tests |
| D1 | Not approved |
| Registered three-seed/Phase 6 execution | Not approved |
| B0-B/B1/B2/Stage C | Not approved |
| P1 / test163 | P1 unused; test163 sealed; neither authorized |
| T5Gemma2 | D-108 STOP unchanged |
| Current experiment compute authorization | Zero model/optimizer/debug runs; consultation/static checks only |

Prospective ceilings, **not a grant**: D0=0 updates/≤4 configs/15 minutes; D1=4 total updates/20 minutes; registered=12 units×100=1,200 updates/120 minutes, contingent on complete D1 and T_proj≤96. The combined upper bound is 1,204 updates/155 minutes only if every stage receives separate authorization. No GPU, no retry or extension, six CPU threads for the registered workload. No timing feasibility is established by this review.

### Scientific interpretation and incorrect premises to avoid

- P0 is historical native-path sensitivity, not trained positive-control or M evidence. Stored train Δcopy=+3.761726 [1.891685,5.604957]; val=+5.237459 [2.501321,8.075272]. Positive document counts are 14/20 and 18/20. Val median is 2.973929. Stored mean real copy CE is 12.702185/13.235205; P0 used source_max_length=256, not the registered native512 regime.
- Passing golden hashes verifies framing, not a trained checkpoint, completed replay, absence of leakage, or scientific signal.
- The current postrun placeholder does not cover produced artifacts, and its emptiness is not proof of non-access. No trained P/PA/M result is established.
- A schema-complete template is not a frozen protocol. Numeric replay can reproduce a length-mismatched implementation; it cannot resolve an ambiguous contract.
- v1.0.5 is almost a consolidated protocol authority but is not yet sufficient as an unambiguous frozen implementation authority. It remains source-bound to the declared helpers/preflight/golden, not to old preregistration prose.
- No result-conditioned threshold, seed, donor, step or LR change is recommended. Any genuinely new scientific choice belongs in a separate prospective preregistration, not a post-result patch.

Next steps:
1. Resolve MF-1 as a documentation-only prospective clarification and obtain acceptance; do not change the scientific gates.
2. Complete and verify the real freeze manifest, then request the limited implementation/test/D0 decision. Do not advance automatically.