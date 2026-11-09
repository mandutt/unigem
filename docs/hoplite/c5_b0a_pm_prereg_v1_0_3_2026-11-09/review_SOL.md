# Independent external review — C5 P/M preregistration v1.0.3

- **Reviewer: Sol 6.1 medium** (`openai/gpt-6.1-sol`).
- Date: 2026-11-09 UTC.
- Review basis: current `origin/main`, **`82648462b087e013fc9d85568d16faefe993ef63`**.
- Synchronization: `git fetch origin` succeeded; `git pull --ff-only origin main` succeeded, reporting `Already up to date.` HEAD and `origin/main` are identical. The workspace remains on its existing Hoplite task branch; no branch switch or repository-content edit was needed for synchronization.
- This is a new, direct v1.0.3 review, not a reused v1.0.2 answer. I read the complete external request, v1.0.3 contract, supplied golden artifact, synthesis, three provenance artifacts, runner and metric tests. Historical v1.0.2 was compared through its text diff against the directly read v1.0.3; it is not implementation authority. I did not read individual previous review answers.
- **No training, evaluation, model forward, generation, test suite, subagent, additional LLM, or external API was run. No P1 data or sealed test 163 was opened.** Verification consisted of source/artifact inspection and in-memory, standard-library hashing and arithmetic over the supplied synthetic vectors and existing preflight metadata. No verification scripts were saved.
- Only this requested report is written. No implementation changes, commit, PR, or execution approval is issued.

## Executive conclusion

**NARROW — do not freeze v1.0.3 as-is.** The repair is substantial and the advertised golden constants and replay counts are correct. I classify the ten previous blockers as **7 closed, 3 partial, 0 wholly open**, at the specification level, not as implemented/tested functionality.

Remaining work is a bounded text/schema correction before freeze: disambiguate phase-7 memory lengths and donor-specific baselines; state the exact flattened replay hash projection; give the 12-checkpoint manifest a concrete serializable/restorable schema; and resolve the lifecycle of the frozen P1 manifest versus its growing artifact inventory. None requires examining results, changing thresholds, or expanding the experiment.

After those corrections, a recorded freeze and targeted recheck can support **implementation + synthetic unit tests**, followed by a separately controlled **D0 mechanics-only** run. This consultation does not run or presently authorize any of those steps. D1 and the registered three-seed experiment remain separately unapproved, as do Phase 6 execution, B0-B/B1/B2/Stage C. T5Gemma2 remains closed by D-108 STOP.

## Evidence anchors and independent checks

Unless otherwise stated, section references below refer to `docs/plan_c5_b0a_pm_prereg_v1_0_3.md` at the reviewed HEAD.

### File-content identities

| Artifact | SHA-256 of file bytes |
|---|---|
| v1.0.3 contract | `d3fa42bd59eb5da2e3eba5f0504c6cccd4d4ffd8fadfa2a6087e200ab4162c51` |
| v1.0.3 golden JSON file | `2f59902ae5ad3088311b197efc0c1cae7a2735b99a78d233faae52e95be4a9d7` |
| cohort preflight | `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` |
| P1 attestation manifest | `69af129a4f58f7400189c361ba2447f12e17d35f012d7a36c26efdf485a3a2dc` |
| historical P0 sanity artifact | `8528936a0cec5e766b1ab59ebcad79e3f925d0158d5a18aa343ec8f8e4982283` |

The preflight hash exactly matches §0.4. The request's authoring HEAD `97e9d12` is historical metadata, not the review basis; the synchronized current HEAD above is the basis.

### Synthetic golden results

I independently framed tensors using the stated little-endian lengths, dtype, shape and payload, sorting by canonical name. For replay I sorted records by the seven specified key fields and hashed a compact, `sort_keys=True` JSON array of **flat objects containing those fields plus `ce`**. All five expected constants matched:

| Vector | Independently reproduced SHA-256 |
|---|---|
| state | `43ecb58e197d5789df0a9dbbc67beba11538b8063c3da8ac46f96e1e95d65712` |
| empty state | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| base replay | `c43ea35c46c51a0e82cebe5764a989d1b67012b2690246a0f89a94dff7851667` |
| supplemental replay | `8277a713fd52b2ba8c5c3c859c83fd78593aa5a381f8640448e2128a97af7a20` |
| control frames | `6b50c226ecc402323787bd25b20e57fe57376caeb925c040b57985ccc0ec1938` |

Reversing each replay fixture's input order and then sorting also reproduced its expected hash. This verifies these fixtures, not a future replay implementation or trained output. In the control fixture `M_NORM/doc_a` must sort before `M_POS_MEAN`, notwithstanding its input position.

### Arithmetic and cohort checks

- F/L: `15 × 2 variants × 2 endpoints × 2 kinds = 120` records/unit; `3 × 120 = 360` per arm.
- P/PA: `20 × 2 × 2 × 2 = 160` records/unit; `3 × 160 = 480` per arm.
- D1 phase 5: `120 + 120 + 160 + 160 = 560`.
- Registered primary: `360 + 360 + 480 + 480 = 1,680`.
- Common doc: `4 × 3 × 2 × 2 × 2 = 96` records; native-only doc: `2 × 3 × 2 × 2 × 2 = 48`. Hence `15 × 96 + 5 × 48 = 1,680`.
- Phase 7: `15 × 5 × 2 × 2 × 2 = 600` per arm-seed, **2,400** across D1's four units and **7,200** across registered twelve units. These are record counts, not necessarily distinct forward calls.
- Preflight lengths reproduce 16 EG2 training contributors, 15 eligible validation targets at 753 and 14 at 754; native lengths are all 512.
- Registered control tensors: `6 × 16 + 6 × 21 = 222` files/tensors. Float32 payload is **280,166,400 bytes**, approximately **0.280 GB / 0.261 GiB**, excluding container/metadata/checkpoint overhead.

## Q1. Are all ten previous blockers closed?

**Verdict: conditional.** Not all are fully closed as a single unambiguous implementation contract.

| # | Previous blocker | Closure | Evidence and qualification |
|---|---|---|---|
| 1 | `donor_sort` versus `donor_id` | **closed** | §12.2 consistently serializes `donor_id`; `donor_sort` is internal only. Both replay goldens reproduce without renaming the field. A separate wire-envelope ambiguity is described under Q3/MF-2. |
| 2 | 12-checkpoint replay | **partial** | §§11.4/12.1 explicitly require twelve `(arm,seed)` identities and per-unit restore. The single-checkpoint mistake is fixed. However, no concrete manifest layout, checkpoint-file binding or map example is supplied; see MF-3. |
| 3 | 420 versus 360/480 | **closed** | §11.5 now correctly distinguishes per-unit 120/160 and per-arm 360/480. Independent arithmetic above agrees. |
| 4 | Phase-7 enum/CE/donor prefix | **partial** | §§9.6.1/12.2 fix enums, raw CE, baseline and delta definitions. Prefix length and baseline conditioning remain ambiguous for actual preflight lengths; see MF-1. |
| 5 | Supplemental canonical order | **closed** | Artifact order is now ascending, including PA `donor` before `real`. Supplemental `8277a7…` independently matches; base remains `c43ea…`. |
| 6 | P1 strict flags/inventory | **partial** | §§1.5/4.0 gate both flags, hash and malformed/known-use states. The current manifest is valid before Phase 6 artifacts exist, but frozen-hash versus later inventory updates is not operationally resolved; MF-4. |
| 7 | `P_VALID` tri-state/F9 | **closed** | §4.5 separates integrity from calibration; F9/F10 in §7.2 now use reachable missing-path/missing-validity states. Known nonfinite failure dominates unknown. |
| 8 | Control tensor schema | **closed** | §12.1 fixes `tensor`, shared target sentinel, canonical names, dtype/shape and frame—not ZIP—hashing. Control golden matches. Manifest container example is still useful, but tensor serialization itself is defined. |
| 9 | P/PA calibration asymmetry | **closed** | §4.5 explicitly omits L's 2/3 and paired L>F conjuncts for P/PA. This is a prospective arm asymmetry, not grounds to retune after results. |
| 10 | D0/artifact/native assert | **closed** | §§2.6/11.2 specify one config per arm, zero updates, native 512 assertion, control path/retention and approximate footprint. |

**Next steps:** (1) Correct MF-1 through MF-4 in text/schema only. (2) Recheck affected sections and fixed vectors before recording freeze. (3) Preserve the closed items and all scientific constants.

## Q2. Is v1.0.3 self-contained?

**Verdict: conditional.** Nearly, but not yet a sufficient *unambiguous* single implementation authority.

**Evidence:** §§2.5–2.7 now provide tokenizer, source prefix/limits, same-position CE, copy mask, donor rule, initialization and mode order. §§3–10 define tri-state decisions, cohorts and statistics; historical r3.x references are explicitly nonnormative. Repository-local model/cache/data artifacts are legitimate dependencies, not a need to consult old scientific prose.

The unresolved choices are operationally significant: what length `memory(real doc)` means in phase 7; whether `{key,ce}` is shorthand or a nested serialized object; how the checkpoint map locates twelve actual states; and how a frozen P1 attestation acquires complete postrun inventory without violating its frozen hash. A reader should not need to infer those from older documents or choose a wire schema independently.

The existing runner is not the missing v1.0.3 implementation: `set_training_mode` and `train_arm` handle only `frozen`/`lora`, the legacy bootstrap defaults to 20261108 and misnames positive-document count `seeds_positive`, and no four-arm PM manifest/replay contract is implemented in that file. These are implementation obligations, not evidence that trained P/PA/M exists. The inspected metric tests cover CE alignment and historical helpers, not the required PM decision/replay matrix.

**Next steps:** (1) Put the four clarifications into the normative contract and bind any companion schemas by hash. (2) Supply concrete synthetic manifest examples. (3) After freeze, implement against that authority rather than importing legacy defaults unchanged.

## Q3. Do canonical keys, checkpoint maps and goldens agree?

**Verdict: conditional.** **Yes for all supplied digest constants and the corrected key; not yet fully specified for production serialization/restoration.**

**Evidence:** All five digests reproduce as recorded above. Adding `donor_id` is not a new base-vector mutation: the base artifact already uses that field, so its `c43ea…` digest remains correct. `sort_keys` handles dictionary member order only; the separate ascending record sort in §12.2 is necessary and now present.

MF-2 is a genuine remaining ambiguity, not an observed golden failure. §9.6.1 line 1107 says the canonical projection is `{key,ce}`, whereas §12.3 and the JSON golden serialize key fields at the top level. A literal nested-key-object interpretation produces **`33c945a2f858dddd9cd466b578bc4c81fde94b32c1b3b2bf83ff2edf6e0ca62c`** for the base fixture and **`e5936867eb8f59d4e849956b9210edddc6a0652f7e8830f111353a98ff1f253c`** for the supplemental fixture, not the registered digests. State explicitly that the hash array contains flat eight-field records and excludes phase-7 `baseline_ce`/`delta`.

A `(arm,seed)` identity is mathematically sufficient but is not a JSON object key. §§11.4/12.1 need a normative encoding such as string `arm/seed` keys and an unambiguous link to serialized trainable states. No real postrun map should exist yet; the missing item is its schema/example, not trained checkpoints.

Within each replay domain, null versus integer donor IDs never competes at an otherwise identical key. If mixed-domain inputs are accepted, use the specified internal sentinel for comparisons only; never serialize `donor_sort` or silently mix diagnostic records into primary coverage.

**Next steps:** (1) Freeze the flat projection explicitly, preserving existing goldens. (2) Add a synthetic twelve-entry checkpoint/manifest example with missing/duplicate/unknown-unit rejection. (3) Require canonical ordering, finite floats, permutation and domain-separation tests after implementation.

## Q4. Is replay arithmetic and T_proj correct?

**Verdict: agree** on the repaired arithmetic and structural projection, **not** on any claim of measured runtime feasibility.

**Evidence:** The independent counts above establish 1,680/560/600 and 120/160/360/480. §11.5 correctly uses `3 × sum(arm-seed workload)`; multiplying a preaggregated 360/480 timing by three again would be wrong. `t_primary_replay_arm` is a per-seed 120/160 workload, not a per-arm aggregate.

The projection includes 100 updates, step0 and final donor evaluations, M building, initial M CE, generation, primary replay, diagnostic replay and overhead. D1 must account for both initial CE and replay work; eight named phases are not permission to omit the second primary CE pass or loading/report overhead. Phase 7 is excluded from primary `replay_ok` explicitly in §11.4 steps 6–7. Its timing and separate diagnostic status still must be reported.

No D1 timings were supplied or measured in this review. Therefore neither `T_proj ≤96` nor completion within 120 minutes is established. Record counts also do not imply unique CE forwards because variants and endpoints can share computation.

**Next steps:** (1) Implement synthetic exact-domain checks for mixed cohorts. (2) Require separately identifiable initial-CE/replay timing and all eight phases in any later approved D1. (3) Admit a registered run only on a finite nonnegative ≤96-minute projection and separate approval.

## Q5. Is phase-7 measurement executable with 600 records?

**Verdict: conditional.** CE/sign/variant semantics are substantially fixed; prefix geometry and baseline conditioning need one more binding.

**Evidence:** §9.6.1 now makes `ce` raw target CE for real/donor memory, `baseline_ce` the selected control CE, and `delta=baseline_ce-ce`. `variant` selects the baseline, so duplicate raw real/donor CE across variants is intentional. The record count remains 600 without inventing a third memory kind or treating repeated values as independent samples.

However, `real_prefix = memory(real doc)` does not explicitly say full memory or `[:K_M]`, unlike `real_prefix_t` in §9.3. Applying the frozen donor rule to preflight lengths gives 75 F/L target-donor pairs: **64 have full-memory K_d>753, five equal 753 and six are below 753**. For example, target `REPORT-news_r-00020-00001` has length 777; donor rank 0 `REPORT-news_r-05258-00002` has length 771. Literal full-memory K_d is 771, but `M_POS_MEAN[:771]` and `M_NORM(t)[:771]` contain only 753 rows. Code can evaluate those tensors, but it would be a different-length baseline rather than an explicitly common-length comparison. Alternatively, interpreting both prefixes as M-capped memory yields K_d=753. Those are materially different diagnostics.

A shorter example also exists: target `REPORT-news_r-01058-00001` length 754 uses donor rank 2 `REPORT-news_r-00430-00001` length 751. The cropped control CE therefore depends on **donor/K_d**, not merely doc/endpoint. The prose description of `baseline_ce` omits this conditioning and could be misread as reusing the phase-5 baseline. M_NORM must also be stated to be the stored full-prefix-normalized tensor cropped for this diagnostic, rather than silently renormalized at each K_d.

This is ambiguity, not proof that every plausible implementation crashes. It does block reproducibility as a sole normative contract.

**Next steps:** (1) Bind the intended phase-7 prefix construction explicitly; a natural bounded clarification is to M-cap real and donor before their minimum, with no padding or rebuilding of controls. If differing baseline lengths are intended instead, declare that diagnostic estimand explicitly before results. (2) Bind baseline CE to the same `(arm,seed,target,donor_id,K_d,variant,endpoint)` and assert `delta=baseline-ce`. (3) Test synthetic >753, =753 and <753 cases while retaining exactly 600 keys and diagnostic-only status.

## Q6. Is P1/allowlist handling fail-closed without opening test 163?

**Verdict: conditional.** The boolean and access policy is sound; its frozen inventory lifecycle is incomplete.

**Evidence:** Current `p1_usage.json` has version 1, JSON booleans `p1_used:false` and `test_split_read:false`, and an empty inventory. §§1.5/4.0 require both flags, the freeze-recorded SHA and allowlist membership. Malformed/missing is NA; contradictory known-use is false. Unknown blocks validity rather than granting use. A 40-ID train20/val20 allowlist can detect an out-of-scope artifact ID without reading or enumerating sealed test IDs. It conservatively treats any other ID as a violation; that is not proof it was specifically a test record. Attestation is explicitly not proof of non-access.

The lifecycle gap is concrete: if freeze binds the current **`69af129a…`** bytes, keeping its empty list once Phase 6 artifacts exist violates §1.5 and gives NA; populating that same file changes its bytes and violates the frozen SHA. It is repairable prospectively, not a reason to loosen either flag. A future freeze could predeclare a complete inventory, or the contract could distinguish immutable policy/expected inventory from a separately hashed run attestation. The current text does not choose or describe either process, nor the `checked_artifacts` item schema.

**Next steps:** (1) Define that lifecycle and inventory entry schema before freezing; do not simply bless a new SHA after seeing outcomes. (2) Include coverage-completeness in the derived assay predicate and test missing fields, nonboolean values, malformed lists, unknown IDs, hash mismatch and known-use-plus-unknown precedence. (3) Keep test 163 sealed and P1 unused throughout.

## Q7. Are P_VALID, M_CONTROL_INVALID and fixtures coherent?

**Verdict: agree.**

**Evidence:** §4.5 integrity requires each registered seed's 20 native targets ×2×2×2 records to exist and be finite; calibration is not part of `P_VALID`/`PA_VALID`. Nonfinite is false; missing/unreadable/path NA is NA unless a known false dominates. Thus good artifact paths, complete finite native records, `m_evaluable=true`, valid P/PA and a failed P/PA calibration conjunct make `m_valid=false` and reach `M_CONTROL_INVALID` through §5.4. Conversely integrity failure yields `M_NOT_EVALUABLE`, not calibration-invalid.

F9 (`p_step NA + p_valid NA`) is realizable when the required P artifact is absent; F10 is realizable when PA is missing with the preceding P/assay prerequisites good. The old §4.6 precedence examples involving false+NA can remain useful low-level robustness cases: nonfinite or another known failure can coexist with missing information. They do not invalidate the repaired named fixtures.

P/PA use all three registered seeds and document-first inference after seed averaging, but deliberately do not demand L's 2/3-positive-seeds or paired L>F conditions. The asymmetry is scientifically interpretable as acquisition calibration rather than evidence of matched geometry or trained performance. P0 is descriptive: train copy delta **+3.7617 [1.8917,5.6050]**, val **+5.2375 [2.5013,8.0753]** at source length 256, with high real CE. It supplies no trained P/PA/L or M result.

**Next steps:** (1) Implement derived validity/calibration separately. (2) Require end-to-end reachable F9/F10 and calibration-failure fixtures, not merely arbitrary flag injection. (3) Preserve registered-seed requirements and the prospective asymmetry unchanged.

## Q8. Are control tensors and footprint reproducible?

**Verdict: agree** at the schema/golden level; actual tensors are not yet produced or replay-tested.

**Evidence:** §12.1 binds NPZ array key `tensor`, dtype `<f4`, `[K_M,512]`, shared `M_POS_MEAN` with `target_id="__shared__"`, per-target M_NORM filenames and canonical names. Tensor-frame SHA avoids unstable ZIP metadata. The independently reproduced `6b50…` golden validates the name framing/order, not a trained tensor. M_NORM uses a shared mean direction with a per-target scalar, while saving the resulting tensor remains consistent with the prohibition on fitting a per-target matrix.

Twelve registered units require 222 tensor payloads totaling about 0.28 GB, consistent with the stated ~0.3 GB estimate. There is no specified overall disk cap to certify against; this does not establish all checkpoints/containers fit a separate unstated storage budget. D0/D1 artifacts must be namespaced away from registered artifacts if retained alongside them. A versioned control-manifest container example would remove minor implementer choice, but the repaired tensor identity/hash schema is itself reproducible.

**Next steps:** (1) Implement frame hashing and NPZ round-trip against the fixed synthetic golden. (2) Verify exact tensor name/domain/shape coverage, norms and finiteness; never reconstruct tensors from hashes. (3) Include actual storage and I/O overhead in later D1 accounting and retain artifacts as required.

## Q9. Are D0/D1 and compute caps correct?

**Verdict: conditional.** Definitions and cap arithmetic agree; runtime sufficiency is deferred pending separately approved evidence.

**Evidence:** D0 is one zero-update config per arm, seed 20261111, no seed/variant sweep, ≤15 minutes. It is mechanics-only, `not_a_result:true`, `labels_computed:false`, and cannot substitute for timing projection. D1 is four arms × one debug seed, one update/arm, ≤20 minutes, eight measured phases, 560 primary CE records plus primary replay work and 600 phase-7 records per unit. Step0 must occur before updating or use a restored initial state. Its `labels_computed:false` explicitly concerns decision/signal labels, not target-token labels necessary for CE.

Registered work is twelve units ×100 updates =1,200 updates, ≤120 minutes, CPU-only six threads and no retry/extension. The prospective combined ceiling is **1,204 updates and 155 minutes** (`15+20+120`), not a grant. D1 projection must be ≤96 minutes, leaving 24 minutes versus the registered hard abort, but this is not a guarantee against seed/runtime variation. No such projection was measured here.

**Next steps:** (1) After correction/freeze and implementation checks only, consider bounded D0. (2) Require a separate D1 approval, complete timing ledger and no result labels. (3) Keep the three-seed gate and hard abort explicit; no extra timing probes, retries or extensions.

## Q10. What Must-fix remains before freeze/implementation?

**Verdict: disagree** with the premise that all blockers are already closed. Ranked, bounded fixes follow.

### MF-1 — High: bind phase-7 prefix lengths and donor-conditioned baseline

- **Evidence:** §9.6.1 lines 1081–1103, contrasted with §§2.3/9.3. The preflight donor rule produces 64/75 F/L pairs above the control's 753-row capacity under the full-memory interpretation; 6/75 are shorter and make baseline CE donor-dependent.
- **Required correction:** State whether both prefixes are M-capped before the minimum, or explicitly intend unequal-length diagnostic baselines. Bind baseline to donor/K_d and specify crop-without-renormalization for stored M_NORM if that is the intended recipe. No change to primary M lengths, cohorts or gates.
- **Acceptance evidence:** A synthetic long/equal/short crop fixture with asserted tensor lengths, baseline dependency and 600 exact phase-7 keys.

### MF-2 — Medium: specify the replay hash wire projection, not just its fields

- **Evidence:** §9.6.1's `{key,ce}` wording admits a nested serialization that does not produce §12.3's flat golden digests; independently computed alternatives are recorded in Q3.
- **Required correction:** Explicitly hash an array of flat `{doc_id,arm,seed,variant,endpoint,memory_kind,donor_id,ce}` objects after canonical record sorting. Stored diagnostic objects may carry baseline/delta, but those fields are deliberately excluded from this projection. Preserve all existing golden constants.
- **Acceptance evidence:** Exact projection/round-trip tests, order-invariance, rejection of extras in the hash projection, and separate full-artifact integrity plus baseline/delta consistency. Excluding baseline/delta is not inherently a collision or scientific error; it just means the CE replay digest alone does not authenticate them.

### MF-3 — Medium: make the twelve-checkpoint contract concretely serializable and restorable

- **Evidence:** §§11.4/12.1 stipulate a map but contain no manifest example or binding from each arm/seed hash to actual checkpoint state storage. Tuple notation and slash notation are used without a normative JSON shape.
- **Required correction:** Define one versioned manifest representation, exact twelve-key set, mapping to actual checkpoint files/states and per-unit canonical state hash. Bind base/config/mode identity sufficiently for replay; hashes are not loadable states. No trained artifacts are requested before implementation.
- **Acceptance evidence:** A synthetic twelve-unit manifest validates and round-trips; missing, duplicate or substituted identities fail; each replay unit loads its own verified state and matching controls.

### MF-4 — Medium: resolve frozen P1 hash versus postrun inventory

- **Evidence:** §§1.5/4.0 and the current empty `checked_artifacts` manifest. Leaving it unchanged becomes incomplete; updating it invalidates the frozen bytes.
- **Required correction:** Specify a prospectively complete frozen inventory or a separately provenance-bound immutable policy plus per-run attestation lifecycle, with a concrete item schema and completeness rule. Freeze that design before results; preserve both false flags and fail-closed behavior.
- **Acceptance evidence:** A synthetic before-artifacts/after-artifacts lifecycle passes only with complete, properly bound inventory; stale empty inventory, unauthorized hash changes and known use never pass.

None of these is a demand to retrain, tune thresholds, change donors/seeds/steps/LR after outcomes, or reopen any closed route. The checkpoint count correction and golden fixes should not be undone while fixing schema precision.

**Next steps:** (1) Make only these bounded normative/schema corrections. (2) Independently recheck the revised text and unchanged vectors. (3) Freeze commit/content hashes before implementation; later corrections require numbered ERRATA.

## Q11. Can freeze, implementation, unit tests and D0 proceed?

**Verdict: conditional — not as-is.**

**Evidence:** §16.1 prohibits code before freeze, and §§16.2–16.3 require a frozen authority before implementation/D0. Current ambiguities permit divergent implementations even though the fixture constants now match. This review therefore supports text/schema repair and recheck now, not unqualified implementation or D0 approval.

Before implementation, the existing synthetic vectors can be independently verified without a model (done here); the corrected manifest and phase-7 examples must also be concretely inspectable. Implementation tests necessarily run after code exists, so “required tests before implementation” should not be interpreted as demanding execution of nonexistent modules.

**Required implementation/unit-test gate before D0:**

1. Pure decision tests: ANDn/ORn/NOT3, all nine L pairs, F1–F11, fixtures 16–18, false-over-unknown precedence, small-N tuple preservation, every label reachable, no input mutation, integrity versus calibration reachability.
2. Exact synthetic domains: 1,680 primary keys, 560 D1 primary keys, 600 diagnostic keys/unit; native-only targets have 48 aggregate appearances, common targets 96; duplicate/missing/wrong-domain keys rejected; missing registered seed is NA.
3. Hash/state/schema tests: all five fixed goldens, empty state, sorted flat projection, twelve-state round-trip, actual control NPZ reload, name/shape/finite/norm checks, numeric tolerance versus exact artifact identity.
4. Measurement/stats fixtures: same-position CE and copy mask, <5 copy-token handling, raw CE/baseline/delta dependency, independent variants, corrected bootstrap seed 20261109, seed-average-before-document-bootstrap, 2/3 only where specified, signal-tail absolute share/ties/NA.
5. Access/mode/limits: strict P1 booleans and complete inventory, allowlist only, base/encoder eval versus adapter/LoRA training, P identity/PA random adapter, native 512 assert, debug/registered isolation, hard budget gates and no automatic downstream run.

The current metric test file is source evidence of intended CE alignment, not a passing test run in this consultation; its model-dependent class also cannot establish PM readiness by itself.

**Next steps:** (1) Close MF-1–MF-4 and record freeze. (2) Implement and pass the synthetic gates without accessing sealed/P1 data. (3) Only then seek/confirm the bounded D0 step; do not roll directly into D1.

## Q12. Are D1/three-seed/B0-B/downstream boundaries adequate?

**Verdict: agree.**

**Evidence:** §§11/14/16.3 explicitly separate implementation/D0 from D1, registered three-seed training and B0-B. The B0-B predicate, using current labels, is:

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS
AND signal_status == EXPLORATORY_L_SIGNAL
AND m_valid == true
AND n_signal == 15
AND tail_driven == false
AND leakage/mode/metric checks all pass
AND required artifacts are complete
AND separate B0-B preregistration and explicit approval exist
```

`n_signal>=15` is equivalent to exactly 15 because its maximum is 15. `tail_driven` is the **L signal-copy donor contrast** tail, not an M-variant tail; true or NA blocks. Neither positive P0, PA_RETENTION, full_k_secondary nor the exploratory signal label alone approves B0-B. Phase-7 failure is diagnostic, although its timing/artifact status must still be disclosed. The scientific geometry caveat remains native 512 versus EG2 753; it does not authorize cohort substitution.

No current trained P/PA/M result is supplied; nothing in this review satisfies these future gates. B1/B2/Stage C require their own approvals and are not implied by B0-B eligibility. T5Gemma2 remains D-108 STOP.

**Next steps:** (1) Encode these as explicit non-automatic gates in later implementation. (2) Keep approval records separate for D0, D1, registered execution and B0-B. (3) Preserve test 163 sealed, P1 unused and the T5Gemma2 stop.

## Q13. Final disposition and freeze scope

**Verdict: conditional. Final category: NARROW.**

**Evidence:** Golden/key repair and arithmetic are confirmed. Remaining contract ambiguities are local and repairable prospectively; they do not justify STOP of the research idea, but they prevent CONTINUE/freeze of this exact text. No outcome data were generated and no scientific threshold change is recommended.

| Scope | Disposition from this review |
|---|---|
| v1.0.3 freeze as-is | **No**; resolve MF-1–MF-4 first, then targeted recheck and recorded freeze |
| Text/schema correction and independent artifact inspection | Supported now, within existing no-training/no-evaluation constraints |
| Implementation + unit tests | **Conditional after corrected freeze**; not run or unconditionally approved here |
| D0 | **Conditional after freeze + implementation/unit gates**, ≤4 configs, zero updates, ≤15 min; not run/approved now |
| D1 | **Not approved**; separate permission, four updates total, ≤20 min |
| Registered three-seed / Phase 6 execution | **Not approved**; separate permission and complete D1 with T_proj≤96; prospective 1,200 updates, ≤120 min hard abort |
| B0-B/B1/B2/Stage C | **Not approved**; no automatic progression |
| test 163 | **Sealed; do not open** |
| P1 | **Unused; no P1 data or external APIs on P1** |
| T5Gemma2 | **D-108 STOP remains closed** |
| Compute granted by this consultation | **0 optimizer updates; 0 training/evaluation/model runs** |
| Prospective total ceiling, not a grant | **1,204 updates / 155 min**, CPU-only six threads, no retries/extensions |

**v1.0.3 self-contained:** not fully as-is; close the four operational/schema ambiguities, then it can serve as the single scientific implementation authority together with explicitly bound artifacts/schemas and, after freeze, numbered ERRATA only.

**Incorrect premises to avoid:** “all ten blockers closed” is too strong; “goldens still disagree” is false for the supplied vectors; 420 per arm is no longer the contract; twelve hashes without restorable state bindings are not twelve replayable checkpoints; 600 is per arm-seed, not the whole run; a flat CE replay digest does not authenticate excluded baseline/delta; a P1 false attestation is not proof of non-access; historical P0 is not a trained P/PA/M result; and this review is not Phase 6 or B0-B approval.

**Next steps:** (1) Bounded text/schema repair only. (2) Targeted recheck and prospective freeze with commit/content identities. (3) Seek only implementation/unit-test/D0 progression next; keep D1, three-seed and downstream execution explicitly separate.

## Compact Q1–Q13 summary

| Question | Verdict | Bottom line |
|---|---|---|
| Q1 | conditional | 7 closed / 3 partial / 0 wholly open |
| Q2 | conditional | Near self-contained; four operational/schema clarifications remain |
| Q3 | conditional | All five goldens match; flat wire projection and checkpoint schema must be explicit |
| Q4 | agree | Counts and projection structure correct; runtime not measured |
| Q5 | conditional | Raw CE/delta defined; crop length and donor-conditioned baseline ambiguous |
| Q6 | conditional | Both false flags and allowlist sound; frozen inventory lifecycle unresolved |
| Q7 | agree | Validity/calibration separated; F9/F10 and conditional invalid reachable |
| Q8 | agree | Control schema/golden reproducible; 222 payloads, ~0.28 GB |
| Q9 | conditional | Definitions/caps correct; no D1 timing proof or execution approval |
| Q10 | disagree | Four ranked text/schema Must-fixes remain |
| Q11 | conditional | No freeze as-is; implementation/unit tests/D0 only after corrected freeze/gates |
| Q12 | agree | Separate approvals and exact B0-B boundary preserved |
| Q13 | conditional | **NARROW**; no training/evaluation/downstream approval |