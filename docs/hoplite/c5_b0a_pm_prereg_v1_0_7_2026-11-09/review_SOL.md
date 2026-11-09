# Independent external review — C5 P/M v1.0.7

Reviewer: Sol 6.1. Date: 2026-11-09. New independent review round; no subagents or additional LLMs were used. The required v1.0.6 synthesis was read as historical context, not adopted as this round's answer.

## Review identity and access limits

- **Reviewed HEAD SHA (request's protocol baseline): `9613ef6`**, full SHA `9613ef60094b253df13213cfa3d911306b5d9f78`.
- First synchronization commands: `git fetch origin`, then `git pull --ff-only origin main`. Both succeeded; pull reported `Already up to date.`
- **Actual synchronized workspace HEAD and `origin/main`: `a826308f64301179cb54c7a87a208bf3f1bc6af4`**, not `9613ef6`. The existing workspace branch was retained; it is `hoplite/siphnos-3e45b1e7`, not a local branch named `main`.
- A bounded history fetch established that `9613ef6` is the parent protocol commit. `git diff --exit-code 9613ef6 HEAD -- <required underlying sources>` confirmed that the plan, freeze template, golden vectors, synthesis, five provenance JSON files, runner, and metric tests are byte-unchanged. The newer commit adds the review request and dispatch infrastructure. Thus this review covers current `origin/main` while identifying the requested, unchanged `9613ef6` protocol baseline accurately.
- All twelve requested files were read, including the external-review request. Additional inspection was limited to the cited adapter/cache/label and LoRA helper source contracts, Git metadata, and in-memory checks of the supplied fixtures/artifacts.
- No training, evaluation, model forward, generation, D0, D1, or metric-test execution occurred. No model/data modules were imported. No sealed test-163 data or split file was opened; no P1 data was accessed. The explicitly requested P1 usage attestations were read, not P1 data.
- The only review output written is this file. No source, plan, template, fixture, or provenance artifact was modified. No commit, push, or PR is part of this consultation.

Mandatory verbatim quote from §9.6.1:

```text
K_d = min(K_M, len(real_prefix), len(donor_prefix))
```

## Executive verdict

**NARROW — do not freeze v1.0.7 as written.** Five of the six prior residuals are closed at the specification level. The sixth, freeze/manifest identity, is only partial: the new `manifest_commit` field introduces a circular Git identity requirement. Fix that text/schema issue before freeze or implementation. This is not a request for a scientific redesign, threshold change, extra seed, donor change, or extra experiment.

After a narrowly corrected, reviewed freeze contract and a valid manifest, implementation and unit tests are reasonable next steps; D0 must then follow the predeclared tests and its own zero-update limits. This consultation does not authorize any execution now. D1 and the registered three-seed run remain separately gated. B0-B/B1/B2/Stage C remain unapproved. T5Gemma2 remains **D-108 STOP**.

## Q1–Q13 summary

| Question | Judgment | Main conclusion |
|---|---|---|
| Q1 — Six residuals | conditional | Five closed as specification requirements; freeze/manifest commit chain partial. |
| Q2 — Self-containedness | conditional | Scientific mechanics are substantially consolidated; freeze lifecycle is not executable as written; pinned helpers remain explicit dependencies. |
| Q3 — Freeze | disagree | v1_0_7 paths align, but a manifest cannot normally embed the hash of its own containing commit. |
| Q4 — T_proj | agree | Per-seed 120/160, outer factor 3, and aggregate 360/480/1,680 are consistent. |
| Q5 — Phase 7 | agree | K_M cap, slicing, baseline/delta, and 600-record domain are coherent on paper. |
| Q6 — Key coverage | agree | Four-record canonicalization fixture and 600-record numeric diagnostic are explicitly separate. |
| Q7 — Legacy bootstrap | conditional | No-import assertion is a useful guard, not sufficient behavioral statistical proof by itself. |
| Q8 — Hash/golden | agree | All five supplied digest constants independently reproduced without model execution. |
| Q9 — D0/D1/cap | conditional | Counts and caps are coherent; timing feasibility is unmeasured and not approved. |
| Q10 — Must-fix | agree | One freeze-blocking text/schema defect: self-containing `manifest_commit`. |
| Q11 — Freeze/implementation/D0 | conditional | No as-is approval; corrected freeze, implementation acceptance tests, then separately controlled D0. |
| Q12 — Downstream boundaries | agree | Exact joint B0-B predicate and separate approvals remain mandatory. |
| Q13 — Final | conditional | NARROW; no current execution authorization; bounded conditional next-step path only. |

## Q1. Have the six residuals actually closed?

**Judgment: conditional.** Distinguish a closed protocol requirement from an implemented/passing test.

| Residual | Status | Source and rationale |
|---|---|---|
| §16.2 freeze paths | **closed** | Manifest path and embedded `plan_path` both name v1_0_7; template agrees. |
| T_proj per-seed versus aggregate | **closed** | §11.5 explicitly supplies 120/160 to the per-seed term and forbids 360/480 there; §13.5 requires arithmetic coverage. |
| Phase-7 K_d <= K_M | **closed** | §9.6.1 includes K_M in `min`, bounds assertions, four equal-length slices, and no K_d renormalization. |
| freeze_commit/manifest_commit | **partial** | §16.2 now distinguishes their meanings and places the manifest SHA in D0, but embeds the manifest's own containing commit in that manifest. See Q3. |
| Key-coverage wording | **closed** | §11.4 step 5 and §12.3 explicitly distinguish four fixture records from the 600/arm-seed numeric diagnostic. |
| Legacy bootstrap assertion | **closed as a specification requirement** | §§10.2/13.5 prohibit reuse/import. The future `runner/c5_pm_stats.py` is absent, so implementation compliance is not yet established. |

Next steps:
1. Repair only the circular commit placement, keeping the other five closures unchanged.
2. Require future tests to demonstrate these contracts; do not count prose requirements as executed tests.

## Q2. Is v1.0.7 self-contained?

**Judgment: conditional.** Sections 1–14 now specify the cohorts, model paths, loss alignment, copy mask, arm-specific donors, modes/RNG order, M controls, statistics, tri-state precedence, replay domains, and downstream gate without requiring the older r3.x chain. That is a substantial consolidation.

It is not literally a standalone document with no dependencies: §17.1 explicitly binds helper implementations at the freeze commit; §1 and §12 bind preflight and golden artifacts. Those are acceptable explicit, versioned dependencies, not a reason to reopen historical preregistrations. The inspected helpers support the stated Adapter geometry, native labels, cache-length slicing, and LoRA initialization. They must actually be pinned in the final manifest.

The unresolved freeze lifecycle prevents treating the current text as a complete executable authority. There are also ordinary implementation obligations, not new scientific choices: define concrete primary-CE/step100 output locations, preserve their exact key sets, and include every inspected output in the postrun audit. The supplied registry explicitly lists checkpoint/control/phase-7 artifacts; it is not by itself a complete description of every future result report.

Next steps:
1. Close Q3 before claiming an implementable frozen authority.
2. Pin the listed helper revisions and existing artifacts; use v1.0.7 plus numbered ERRATA, not prior review answers, as normative authority.
3. Make result-storage/inventory wiring explicit in implementation and its tests, without altering measurement semantics.

## Q3. Do the paths and freeze identity chain work without self-reference?

**Judgment: disagree as a whole; agree on paths and template intent.**

- §16.2 line 1654 names `docs/plan_c5_b0a_pm_prereg_v1_0_7_FREEZE.json`.
- The schema's line 1661 and the template's `plan_path` name the v1_0_7 plan.
- The template contains the schema's binding fields, helper names, registered seeds, and preflight hash. `status="template"`, null placeholders, and its explanatory `note` are expected template differences, not an already-frozen manifest.
- `freeze_commit` as the earlier final plan/helper commit is noncircular. Hashing the already committed plan bytes and later hashing manifest bytes is also noncircular.

**Blocking issue:** the schema includes `manifest_commit` inside `_FREEZE.json` (line 1664), defines it as the commit of that file (line 1679), and requires populating the file before making the manifest commit (line 1680). A Git commit identifies a tree containing those file bytes. Inserting the eventual commit hash changes the file, tree, and commit hash. A placeholder commit followed by a filling commit does not solve this: either the field identifies the wrong version of the file, or the new containing commit again changes. This is a cryptographic self-reference, not merely an ordering inconvenience.

Minimal recommended correction: retain `freeze_commit` and the content hashes in the committed manifest, but record **`manifest_commit` externally**, for example alongside `freeze_manifest_sha256` in the later D0 provenance report. The normal chain is then:

```text
C_plan: corrected final plan + referenced helper sources
  -> M: manifest binds C_plan and the artifact content hashes
C_manifest: commits M, without embedding C_manifest inside M
  -> later provenance binds C_manifest + SHA256(M)
```

Update the normative schema, template, and freeze-order wording together before freezing. This is a recommendation for a later authorized text/schema correction; none was made in this review.

Next steps:
1. Move the self-containing commit identity to later/external provenance and review the matching text/template correction.
2. Verify a normal two-commit freeze chain, with exact plan/manifest bytes and an external reference to the manifest-containing commit.
3. Require D0 to record both the external manifest commit and `freeze_manifest_sha256`; never accept stale/null identities as a workaround.

## Q4. Are T_proj and the primary counts correct?

**Judgment: agree on the contract and arithmetic, not on unmeasured runtime.** §§9.5/11.3–11.5/13.5 agree:

```text
F/L per seed: 15 * 2 variants * 2 endpoints * 2 memory kinds = 120
P/PA per seed: 20 * 2 * 2 * 2 = 160
one seed across arms: 120 + 120 + 160 + 160 = 560
registered: 3 * 560 = 1,680
per-arm registered: F=360, L=360, P=480, PA=480
```

The outer factor of three therefore acts on per-seed measurements. Passing aggregate 360/480 into the inner term would produce the incorrect 5,040 replay records' worth of work; the current wording expressly forbids that. Initial M CE and its later primary replay are separate workloads, so both timing terms are intentional.

Next steps:
1. Add the required per-seed arithmetic regression test and a negative aggregate-input case during implementation.
2. Test time units and all timing components separately; obtain actual durations only through a separately approved D1, never a D0 timing substitute.

## Q5. Is phase 7 executable and compatible with K_M=753/512?

**Judgment: agree at specification level.** §9.6.1 is now dimensionally coherent. It caps K_d, asserts positive bounds and equal slice lengths, slices both controls and real/donor memory identically, and truncates an already K_M-scaled M_NORM without renormalizing.

Using only the supplied preflight lengths and the specified donor sort, an in-memory read-only calculation found:

| Domain | Target–donor pairs per arm-seed | K_d distribution |
|---|---:|---|
| F/L, 15 common targets | 75 | 750: 3; 751: 3; 753: 69 |
| P/PA, same 15 diagnostic targets | 75 | 512: 75 |

Thus the shorter-donor case is concrete, and the long-prefix case remains bounded at K_M. Each pair produces 2 variants ×2 endpoints ×2 kinds = 8 records; 75×8 = **600 per arm-seed**. Across 12 registered units that would be 7,200 diagnostic records, not a replacement for the primary 1,680.

`ce` is the raw real/donor CE; `baseline_ce` is a phase-7 recomputation on the selected cropped control; `delta=baseline_ce-ce`. Reusing phase-5 K_M CE for a shorter crop would violate the recipe. Duplicate raw CE across variants is legitimate because the baseline changes. Phase-7 baseline/delta are numeric replay fields, excluded from the flat hash record. Diagnostic failure is reported separately and does not redefine primary `replay_ok` (§11.4).

Next steps:
1. Test K_d=K_M and K_d<K_M, including the supplied 750/751 cases, with synthetic tensors.
2. Assert no second M_NORM normalization and no phase-5 baseline reuse.
3. Require all 600 keys and numeric ce/baseline_ce/delta comparisons at the prescribed tolerance when execution is eventually authorized.

## Q6. Are four-record key coverage and 600-record diagnostics separate?

**Judgment: agree.** §11.4 step 5, §12.3, and `golden_vectors.json` explicitly separate:

1. `key_coverage_golden`: four fixed synthetic records, including P/PA, M_NORM, null donor, and donor_id=4; exact canonical digest.
2. Phase 7: 600 records per arm-seed; ce/baseline_ce/delta numeric replay only, atol=1e-5 and rtol=1e-4.

The four-record fixture does not prove complete primary or diagnostic coverage. The primary mixed-domain exact key-set check remains independent and mandatory.

Next steps:
1. Use separate test names/results for fixture digest, primary key coverage, and phase-7 numeric replay.
2. Ensure four-record success cannot satisfy either the 1,680-key requirement or the 600-record diagnostic requirement.

## Q7. Is a no-import legacy-bootstrap test sufficient?

**Judgment: conditional.** It is sufficient as the requested dependency guard, **not as the entire statistics test suite**. The legacy function at `runner/c5_mt5_lora_b0.py:384` defaults to seed 20261108 and returns document positives under `seeds_positive`. A name-only import ban cannot prove a new implementation uses the correct seed or distinguishes documents from registered seeds; aliases or an indirect wrapper can also evade a naive textual check.

The complete protocol already supplies behavioral requirements in §§10.1–10.3/13.3: seed 20261109; fresh default_rng/PCG64 per call; 1,000 resamples; linear percentile; document-level pairing after seed averaging; distinct positive counts; no missing-seed pooling. Together with dependency isolation, these are adequate acceptance criteria. The new stats module is not yet present, as expected before implementation approval. No implementation assertion was run or claimed to pass.

Next steps:
1. Add an import/dependency assertion that accounts for aliases/module-qualified access, not just one literal import string.
2. Add deterministic behavioral fixtures for bootstrap output, seed averaging, missing registered seeds, and separate positive counts.
3. Keep historical P0 outputs unchanged; do not reinterpret its `seeds_positive` field as registered-seed evidence.

## Q8. Are hash framing, record ordering, and five goldens coherent?

**Judgment: agree.** Independent Python-standard-library calculations over the supplied synthetic JSON reproduced every expected digest:

| Golden | Recomputed SHA-256 | Result |
|---|---|---|
| State | `43ecb58e197d5789df0a9dbbc67beba11538b8063c3da8ac46f96e1e95d65712` | match |
| Empty state | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | match |
| Base replay | `c43ea35c46c51a0e82cebe5764a989d1b67012b2690246a0f89a94dff7851667` | match |
| Four-record key coverage | `8277a713fd52b2ba8c5c3c859c83fd78593aa5a381f8640448e2128a97af7a20` | match |
| Synthetic control frames | `6b50c226ecc402323787bd25b20e57fe57376caeb925c040b57985ccc0ec1938` | match |

The checks used little-endian tensor framing, name-sorted control frames (M_NORM before M_POS_MEAN), flat eight-field replay objects, canonical key sorting with internal null→-1 donor_sort, and canonical JSON over one sorted array. Serialized donor_id remains null/0..4; donor_sort is not an extra field. No supplied constant was regenerated or overwritten.

This verifies the specification fixtures, not a future runner's hash implementation, trained tensors, or numeric replay. The control golden is intentionally [1,1], not proof about actual [K_M,512] tensors.

Next steps:
1. Preserve these independent constants in implementation tests.
2. Add the specified permutation, duplicate/missing-key, nonfinite-CE, array-versus-concatenation, and control-order negative tests.
3. Verify real tensor/checkpoint digests only from authorized artifacts; do not confuse exact hash integrity with tolerant numerical replay.

## Q9. Are D0, D1, eight phases, and compute caps correct?

**Judgment: conditional.** The declared accounting is consistent; feasibility has not been measured here.

- D0: at most four zero-update configs, one per F/L/P/PA arm; debug seed 20261111; no variant/seed duplication; ≤15 min; no decision labels, result claim, or projection.
- D1: four arms ×one debug seed ×one update = **four updates**; ≤20 min; separate approval; not a result. Target-token labels for CE are distinct from prohibited decision/signal labels.
- All eight listed phases must be measured. Step0 must truly precede the update or use restored step0 state, despite its position after the update in the numbered workload list.
- Primary initial CE and replay: **560** records each across the four debug units, 120/160 per unit. Diagnostic phase 7: **600 per arm-seed**, or 2,400 across the four debug arms.
- Registered run: 12 units ×100 updates = **1,200 updates**, six threads, no GPU, no retry; ≤120 min hard abort. Three-seed eligibility requires finite/nonnegative **T_proj≤96 min** from a separately approved complete D1. A numerical T_proj was not computed from real timings in this review.
- Prospective combined ceiling, only if separately approved: **1,204 updates / 155 min** = D0 15 + D1 20 + registered 120. This is not one blanket allowance.

Next steps:
1. Test update/config counters, step0 restoration, eight-phase completeness, and cap fail-closed behavior before any debug execution.
2. Do not project from D0 or an ad hoc timing probe; request separate D1 approval only after the preceding gates.
3. Preserve hard abort and no retry/extension; exceeding the projection gate is not permission to tune after results.

## Q10. Remaining Must-fix, ranked

**Judgment: agree that a residual blocker remains.**

### MF-1 — High, freeze-blocking: self-containing manifest commit identity

Sources: plan §16.2 lines 1664, 1678–1681 and freeze template `manifest_commit`.

The attempted separation of plan and manifest identity is scientifically harmless but operationally incomplete: the committed manifest must know its own containing commit. The minimal correction is external placement of that identity, with corresponding schema/template/order changes (Q3). Until then, neither a faithfully populated manifest nor an unambiguous freeze audit is established.

I found no second demonstrated scientific blocker in the six targeted repairs. The no-import test's limitations, future P/PA mode support, primary-result inventory wiring, and timing checks are implementation acceptance obligations, not justification to expand the experiment or alter thresholds.

Next steps:
1. Make a narrowly scoped pre-freeze text/schema correction and independently verify the acyclic chain.
2. Re-review that correction only; retain the existing seeds, donors, thresholds, steps, LR, and compute ceilings.

## Q11. Can freeze, implementation/unit tests, and D0 be approved?

**Judgment: conditional; not as written.** Withhold freeze now because of MF-1. Under §16.1's no-code-before-freeze rule, do not authorize implementation/unit-test changes ahead of the corrected freeze either. I recommend the bounded sequence **correction/review → valid freeze → implementation + unit tests → D0**, with no execution performed by this consultation.

Before implementation, lock the acceptance-test plan; execute those tests once the implementation exists, before D0. Required coverage is the existing §13 matrix, especially:

1. Pure tri-state decision tests: ANDn arities 2/4/5, F1–F11, nine L pairs, fixtures 16–18, label reachability, false/NA precedence, small-N preservation, no input mutation, no model/data in dispatch.
2. M/coverage tests: F/L contributors 16 and targets 15; P/PA contributors/targets 20; P identity; same-space M_NORM; zero/nonfinite norms; exact mixed 1,680 keys, 96 appearances/common target and 48/native-only target; no duplicate/missing keys or 15→14 substitution. The existing §13.2 shorthand “target appears 96 times” must be applied using §9.5's explicit common/native distinction, not to all 20 targets.
3. Phase-7 tests: K_M cap and four equal-length slices, short donor, no renormalization, freshly recomputed baseline, and 600 numeric records/unit kept outside primary gating.
4. Statistics tests: the full Q7 requirements, paired retained IDs, missing registered seed→NA, correct copy/full thresholds, top-three absolute share/ties, and signal-tail rather than M-tail gating.
5. Hash/replay tests: all five goldens, flat eight-field array hash, exact primary key coverage, 12-checkpoint map, per-unit counts, control-manifest framing/order, numeric versus exact-integrity separation, debug/final separation.
6. Safety/mechanics tests: frozen P1 attestation hash plus separate postrun inventory; malformed/missing attestations→NA; contradiction/outside-allowlist→failure without opening sealed test IDs; frozen base/native encoder modes; fresh per-arm state and RNG order; P no adapter; PA adapter+LoRA; hard D0/D1/registered approval and update/time gates.

The inspected existing `eval/tests/test_c5_b0_metric.py` covers alignment, copy-mask behavior, legacy F/L mode policy, donor behavior, and descriptive P0 decisions. It is not the Phase-6 suite: the class requires a local model and includes model forwards/generation, so it was **not run** under the no-evaluation constraint. Existing `set_training_mode` supports only legacy `frozen`/`lora` arms; future P/PA mode support needs implementation, not an assumption that the current runner already complies.

Next steps:
1. Resolve MF-1 and validate the freeze binding without running any experiment.
2. Implement against the frozen contract and pass the predeclared pure/synthetic acceptance suite; keep model-backed checks separately authorized.
3. Only then consider separately controlled D0: four configs maximum, seed 20261111, zero updates, ≤15 min, `not_a_result:true`, no decision/signal labels, no timing projection.

## Q12. Are downstream boundaries sufficient? Restate B0-B.

**Judgment: agree.** §14 requires the joint predicate below, not a favorable single flag:

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS
AND signal_status == EXPLORATORY_L_SIGNAL
AND m_valid == true
AND n_signal == 15
AND tail_driven == false
AND leakage/mode/metric pass
AND artifact complete
AND separate B0-B preregistration and approval
```

Because n_signal is capped at 15, the spec's `>=15` is exactly `==15`. Tail true or NA blocks passage. The relevant tail is the L copy wrong-donor signal on the 15 common eligible documents, not a descriptive M tail. P/PA calibration is joint and includes PA; nullable PA_RETENTION does not replace a gate. The scientific scope remains `M_CONTROL_PREFIX753_COHORT15`, not general content-use proof or broad retention.

D1 needs separate approval after D0; registered three-seed execution needs complete D1 and T_proj≤96 plus separate approval. Neither implies B0-B, and B0-B never automatically approves B1/B2/Stage C. `EXPLORATORY_L_SIGNAL` alone grants nothing.

Next steps:
1. Encode the exact joint predicate and true/NA tail blocking in tests.
2. Keep D1, three-seed, and B0-B authorization records separate; fail closed on missing evidence.
3. Preserve sealed test 163, no P1 use, and T5Gemma2 D-108 STOP at every boundary.

## Q13. Final verdict, freeze scope, and compute

**Judgment: conditional. Final verdict: NARROW.**

| Item | This review's recommendation / boundary |
|---|---|
| v1.0.7 freeze | **Withhold as-is.** Correct MF-1 and review the acyclic schema/commit chain first. |
| Implementation + unit tests | **Conditional next step only after valid corrected freeze.** No implementation performed or presently granted by this consultation. |
| D0 | **Not run/authorized now.** After preceding gates and explicit operational authorization: ≤4 configs, zero updates, seed 20261111, ≤15 min; no decision labels/results/projection. |
| D1 | **Not approved.** Separate approval; four debug units/updates, ≤20 min; eight measured phases. |
| Registered three-seed run | **Not approved.** Separate approval after full D1 and T_proj≤96; 1,200 updates/120 min hard abort. |
| B0-B/B1/B2/Stage C | **Not approved.** Exact §14 predicate plus new preregistration/approval; no automatic progression. |
| Test 163 | **Sealed.** Not opened; never needed for allowlist-based leakage checks. |
| P1 | **No use.** Usage-attestation files are not P1 data; no P1 experiment/access is authorized. |
| T5Gemma2 | **D-108 STOP maintained.** No reopening. |
| Maximum compute now | **Zero experimental optimizer updates; no model execution authorized.** This consultation used only read-only source/JSON/Git inspection and in-memory fixture/arithmetic checks. |
| Prospective ceilings | D0 0 updates/15 min; separate D1 4 updates/20 min; separate registered 1,200 updates/120 min. Combined 1,204/155 is a ceiling, not a grant. Six threads, CPU only, no retry or extension. |
| Single implementation authority | Substantially consolidated but **not freeze-ready as written**. After MF-1, use corrected v1.0.7 plus numbered ERRATA and its explicitly bound artifacts/helpers; no historical-answer substitution. |

Next steps:
1. Text/schema-only repair of MF-1, with matching template and external manifest identity record.
2. Verify and freeze that corrected contract; only then proceed through the separately controlled implementation/test/D0 sequence.
3. Keep all scientific settings fixed; any genuinely new scientific choice needs a new prospective preregistration, never a post-result adjustment.

## Supporting artifact observations and reproducibility

- Verified preflight content SHA-256: `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`.
- Plan content SHA-256: `afa360989e15d0e8a32c086ed1939791e30b52217e0820d89f8950d0c300df4f`.
- Golden file SHA-256: `7f5584f689bc2a9234596dee87c55c89d59b3f607b6040d1dc0b5c50fe2ede6f`.
- Freeze-template SHA-256: `e50b97cad09e50499aff26eb6fdce88ceda9c23238996351ab0e4cad0d10af1d`.
- Frozen P1-attestation file SHA-256: `69af129a4f58f7400189c361ba2447f12e17d35f012d7a36c26efdf485a3a2dc`.
- A synthetic key-domain enumeration produced 1,680 distinct primary keys: F=360, L=360, P=480, PA=480; 15 common documents each appeared 96 times and five native-only documents each appeared 48 times. This is arithmetic/specification verification, not a replay of an experiment.
- Preflight confirms K_M=753, 16 F/L training contributors, 15 common val targets, and only 14 targets at 754; P/PA native lengths are all 512 with 20 contributors/targets. No cohort replacement is warranted.
- Historical P0: train mean Δcopy +3.7617, CI [1.8917,5.6050], mean Δfull +3.5027, 14/20 positive documents; val +5.2375, CI [2.5013,8.0753], mean Δfull +5.2936, 18/20 positive documents. `seeds_positive` here counts documents. Source maximum was 256, not Phase-6 native 512. Untrained real-copy CE is approximately 12.7/13.2. These are descriptive sensitivity observations, **not trained P/PA/M evidence**.
- `p1_usage.json` declares both usage flags false and has an empty pre-run inventory. `p1_usage.postrun.json` is explicitly `not_run` with an empty inventory. Registry v2 describes future checkpoint, control, and phase-7 paths. These are not proof of completed execution or non-access; no trained P/PA/M result is established by them.
- The required historical synthesis records **2/2 substantive NARROW; GLM process-invalid**, not three substantive votes. This review's conclusions instead rest on the current source text and the checks described above.

### Incorrect premises to avoid

1. The fetched current HEAD is not `9613ef6`; it is `a826308`. The underlying reviewed protocol bytes are identical, and both identities are reported rather than silently substituting one.
2. Separating the names `freeze_commit` and `manifest_commit` does not itself make the manifest's own commit field noncircular.
3. No-import prose is not an executed dependency test or proof of correct bootstrap behavior.
4. Fixture hashes and record counts do not establish trained calibration, numeric replay success, timing feasibility, or downstream approval.
5. P0 positive deltas, an empty pre-run audit inventory, or an exploratory label cannot justify B0-B or any later stage.

**Bottom line: NARROW; one freeze-blocking schema repair, then controlled verification. No Phase 6/B0-B approval, no P1/test-163 use, no T5Gemma2 reopening, and no post-result changes.**