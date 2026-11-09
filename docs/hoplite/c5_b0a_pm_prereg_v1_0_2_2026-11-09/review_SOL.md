# Independent external review — C5 P/M prereg v1.0.2

**Reviewer: Sol 6.1 medium**  
**Date:** 2026-11-09  
**Repository:** `mandutt/unigem`, `main`  
**Review basis:** current `origin/main`, `445a9cc2b1ff758edd807da659a3e50c9c703d1d`  
**Final recommendation: NARROW — text-only must-fix round; do not freeze as-is.**

## Review provenance and limits

I ran `git fetch origin`, then `git pull --ff-only origin main`. Both succeeded; pull reported `Already up to date.` Resulting HEAD and `origin/main` were both `445a9cc2b1ff758edd807da659a3e50c9c703d1d`. The initial working tree was clean. The request's historical authoring HEAD is not substituted for the current review basis.

This is a new independent v1.0.2 review, not a duplicate of the v1.0.1 round. I directly read the full external-review request, v1.0.2 plan, golden JSON, required synthesis, preflight, P0 and P1 provenance artifacts, runner and metric tests. I compared relevant v1.0.1 text for change provenance, not as implementation authority, and inspected the existing cache/adapter loader for schema compatibility. I did not consult individual earlier model reviews or delegate any analysis.

Checks were read-only static inspection and standard-library calculations over the supplied provenance/golden artifacts: content hashes, tensor-frame hashing, replay JSON ordering, cohort/donor arithmetic, and summaries of already-recorded P0 values. **No training, evaluation, model forward, generation, D0, D1, or test suite was run.** No test-163 file or split contents were opened; no P1 data or external API was used. Raw F5 data, EG2 cache and local mT5 model directories are absent in this checkout; claims about their current contents are therefore limited to the frozen provenance and loader source. The only repository file written by this review is this report.

References below use **S** = `docs/plan_c5_b0a_pm_prereg_v1_0_2.md`, with line numbers at the reviewed HEAD. The reviewed plan's content SHA256 is `834fe640609fedb30ab356d3e450b237a9b3d4351ae33dc498ac89566ab86e59`; this identifies the candidate, **not an approved freeze**.

## Executive assessment

The central scientific-contract repair is real: **artifact validity is now independent of calibration success.** `M_CONTROL_INVALID` is reachable, and it is not unconditional. The arm-specific donor rule is also executable and removes the previous contradictory cross-arm sharing requirement. Persisted control tensors remove the previous impossible hash-only reconstruction requirement.

However, **all 15 blockers are not fully closed**. My closure assessment is **10 closed, 5 partial, 0 wholly open**, at the text-contract level, not an implementation certification. The partial items are control serialization, allowlist/P1 validation, phase-7 measurement/schema, timing/replay counts, and golden correctness. In particular:

* The supplemental replay digest contradicts the required canonical record ordering.
* The total 1,680 remains correct, but the new per-arm registered count of 420 is wrong: F/L are 360 each and P/PA 480 each.
* Phase 7 names tensors but still does not unambiguously bind its variant, memory kind, CE/baseline and hash schema.
* The P1 manifest's `test_split_read` field is not actually consumed by the normative assay predicate.
* Control tensor persistence is feasible, but its canonical digest identity/order and exact payload schema remain implicit.

These are pre-result contract fixes, not grounds to change thresholds, seeds, donors, updates, LR, cohorts or compute caps.

## Q1. Have all 15 blockers closed?

**Verdict: disagree** with complete closure; substantial but incomplete repair.

| # | Prior blocker | Closure | Evidence and remaining qualification |
|---|---|---|---|
| 1 | P0 `no_training` | **closed** | S:467–494 accepts `mode=p0_sanity_no_training` and `test_split_used=false`. Actual legacy P0 has these fields and no `no_training` key. No P0 result rewrite is needed. |
| 2 | Donor basis | **closed** | S:262–285 explicitly separates EG2 lengths for F/L from native lengths for P/PA, shares only within arm across seeds, and excludes train donors. |
| 3 | Replay control tensors | **partial** | S:1330–1344 stores actual float32 NPZ tensors and replay loads them. Hash-only reconstruction is fixed. Canonical frame identity/order, NPZ payload field and per-tensor hash target are not completely specified; see MF-5. |
| 4 | `test_split_used` / P1 | **partial** | S:96–105, 450–465 supplies a frozen allowlist and a real P1 manifest. But the gate requires only `p1_used=false`, not `test_split_read=false`; checked-artifact scope/schema and contradictory-attestation handling need binding. See MF-4. |
| 5 | `h_len` / data paths | **closed** | S:296–321 pins paths, JSONL fields, cache fields and source length semantics. Existing `load_layer_cache` reads `lengths[i]` and slices `h[i,:n]`. Raw-passage copy mask is explicit. Actual local data revalidation remains pending, not a missing textual definition. |
| 6 | P/PA seed aggregation | **closed** | S:599–601, 1097–1106, 1120–1150 requires all three registered seeds, seed mean before document bootstrap and missing-seed NA. |
| 7 | P/PA alias / invalid-control reachability | **closed** | S:549–600 separates integrity predicates from pass thresholds; S:667–690 can now reach `M_CONTROL_INVALID` after true validity. |
| 8 | Copy-token `<5` | **closed** | S:254–259 separates signal exclusion from primary M `endpoint_ok=false`; S:1020–1045 forbids silent primary-key omission. |
| 9 | Phase-7 recipe | **partial** | S:1059–1080 supplies crops and 600 count, but does not finish CE/baseline binding or reconcile `{real,donor}` with S:1357's `{control,real}`. `donor_prefix` also lacks an explicit binding. See MF-3. |
| 10 | Threshold asymmetry | **closed** | S:569–600 makes P/PA copy `>=.05` acquisition calibration distinct from L directional M copy `>0`; full is `>0`. No post-result discretion. |
| 11 | F11 label | **closed** | S:809, 815–816 gives `INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL` and preserves INVALID in the reported triple, matching small-N-first dispatch. |
| 12 | Training mode / RNG | **closed** | S:323–348 supplies per-arm mode table, fresh states and seed→adapter→LoRA without reseeding; trainable inventory is required. Mode restoration must be implemented and tested, not assumed from old runner helpers. |
| 13 | T_proj primary replay | **partial** | S:1285 now includes primary replay. S:1292–1293 nevertheless assigns 420 to each registered arm, contradicting mixed coverage. Distinct initial/replay timings also need explicit measurement mapping. See MF-2. |
| 14 | D1 no-labels / `not_a_result` | **closed** | S:1224–1234 distinguishes decision/signal labels from target-token CE labels and explicitly marks D1 `not_a_result:true`. |
| 15 | Golden coverage | **partial** | Version header and P/PA/M_NORM/donor-4 examples exist. Supplemental expected digest fails the normative ordering, and `donor` is absent from the general enum. See MF-1/MF-3. |

**Next steps:**
1. Resolve the five partial items in a bounded pre-freeze text/golden correction.
2. Recheck the corrected contract against independently fixed expected bytes and domain counts before freezing; do not weaken tests to preserve erroneous constants.

## Q2. Is v1.0.2 self-contained?

**Verdict: disagree as-is.**

Evidence: S:21–26 promises a sole implementation contract. Most formerly implicit information is now present: paths, tokenizer, mask, architecture, LoRA, update order, donor lengths, seed aggregation and status precedence. The remaining gaps are inside this candidate, not a need to resurrect old r3.x text: phase-7 record meaning, control-digest naming/ordering, manifest validation and contradictory timing counts.

The runner is historical two-arm code, not a ready four-arm PM implementation. Its `set_training_mode` accepts only `frozen`/`lora` and assumes an adapter; its old donor docstring says all arms/seeds; `bootstrap_paired` defaults to 20261108 and misnames positive documents `seeds_positive`. S:1133–1140 correctly forbids adopting that bootstrap helper unchanged. `token_losses`/`forward_loss` call `model.eval()`, so they are evaluation helpers, not substitutes for a training-mode-preserving forward.

**Next steps:**
1. Put all MF-1–MF-5 resolutions into the single authority and its version-bound golden/schema artifacts.
2. Freeze with commit and content SHA256 only after review; bind implementation to that identity, not historical helper behavior.

## Q3. Validity, calibration and `M_CONTROL_INVALID`

**Verdict: agree on the logical repair.**

Evidence: S:554–564 requires P/PA step100 integrity and complete finite native-20 measurements, **not positive contrasts**. S:591–600 derives the four independent calibration flags. Under S:670–685, with availability true and both validity predicates true:

* all four calibration flags true and both L M passes true → `M_CONTROL_PASS`;
* one calibration flag false → `M_CONTROL_INVALID`;
* calibration true and L M pass false → `M_CONTROL_FAIL`.

These are logical witnesses, not observed trained results. Finite CE does not force either sign or a positive CI; hence validity does not make calibration fail unconditionally or pass tautologically. Availability false/NA still exits first as `M_NOT_EVALUABLE`. Artifact validity false is not invalid calibration. The `.05` versus `>0` distinction is explicit and consistent when P/PA use §4.5 and L uses §9.6; do not route every arm through one undifferentiated generic threshold helper.

Caveat: S:938 calls `PA_STEP100_NOT_VALID` an acquisition failure, but with the revised definitions it is an artifact/path failure, not evidence that a complete trained PA failed acquisition. This is a terminology cleanup; the executable predicates take precedence.

**Next steps:**
1. Add derived-flag reachability tests for all three witnesses, including the full validity/control/signal triple.
2. Test availability/validity exits and missing-seed NA separately from calibration failures, including false-dominant calibration combinations.
3. Align the explanatory PA wording with artifact validity; preserve all numerical thresholds.

## Q4. Are donors executable and appropriately arm-specific?

**Verdict: agree.**

Evidence: S:264–285 is deterministic: val20 minus self, `(absolute length difference, doc_id)` ascending, first five, indices 0–4; no train donor. From the frozen preflight, target `REPORT-news_r-04161-00002` has:

* F/L donor suffixes: `04798-00001`, `03991-00001`, `05258-00002`, `03271-00001`, `01058-00001`.
* P/PA: `00020-00001`, `00430-00001`, `01058-00001`, `01127-00001`, `01331-00001`.

All 20 native val lengths are 512 in provenance, so native donors reduce to lexicographic order excluding self. F/L remain paired on the same EG2 length map; P/PA remain paired on the same native map. Comparing raw signal magnitudes across EG2 and native arms is not a matched-donor causal comparison, but the specified positive-control calibration does not require that interpretation. Primary M is donor-free. `shuffled` unambiguously means wrong-document memory, not token permutation.

**Next steps:**
1. Freeze/export actual donor maps and lengths per arm; test self exclusion, tie order, seed invariance and indices 0–4.
2. Keep primary M donor-free and describe cross-regime signal comparisons with their donor/crop caveat.

## Q5. Can control tensors and replay actually reconstruct measurements?

**Verdict: conditional.**

Evidence: S:1264–1273 and 1330–1344 now load actual tensors and checkpoint state, set eval modes and recompute CE. That fixes the old impossibility of reconstructing tensors from a hash. Primary numeric replay tolerances `atol=1e-5`, `rtol=1e-4` are separate from exact integrity hashes; debug and registered hashes are explicitly different domains. Phase-7 failure is separately reported and does not redefine primary replay success.

Persisting one mean plus 15/20 target-normalized controls per arm/seed is feasible: **222 NPZ tensor payloads**, approximately **280,166,400 raw bytes (267.2 MiB)** across three seeds, before metadata/compression. This is not an intrinsically excessive design and does not justify deleting tensors. Its I/O belongs in measured overhead; timing feasibility has not been demonstrated.

But canonical control frames need explicit identifiers and ordering; phase-7 measurement/schema and supplemental hashing remain inconsistent. The golden constant is a synthetic serializer fixture, not a digest that a real diagnostic run could be required to equal. S:1270 should say which of those two verifications is intended.

**Next steps:**
1. Close MF-1, MF-3 and MF-5 before implementing replay.
2. Require missing/corrupt tensor, wrong target/seed/shape/dtype and tampered checkpoint failures, plus full primary numeric replay coverage.
3. Benchmark actual save/load/recompute costs only in an independently approved D1; do not infer runtime from storage size.

## Q6. Does allowlisting protect sealed test/P1 without opening them?

**Verdict: conditional.**

Evidence: the allowlist can reject any checked document identity outside the frozen train20∪val20 without reading test 163. The actual P1 manifest has both strict JSON booleans false. A missing/unreadable preflight or P1 manifest maps to NA under S:465; present known failures should be false under S:498. This is a sound conservative ID-domain check, not proof that no sealed file was read.

Counterexample to the predicate as written: a manifest with `p1_used:false` and `test_split_read:true`, alongside all allowlisted output IDs, satisfies the listed P1 condition at S:463. It must not be accepted. Likewise, a forged all-false attestation cannot be detected from that attestation and output IDs alone. The contract should not promise cryptographic proof of historical non-use. Define the finite required artifact inventory, document-bearing fields and strict validation; synthetic golden IDs and parameter names must not be mistaken for data IDs. Empty ID sets cannot establish completeness.

**Next steps:**
1. Require both manifest fields to be present, boolean and false; any explicit prohibited-use evidence must invalidate the assay even if outputs are allowlisted.
2. Bind required inventory and identity extraction, including target/contributor/donor identities; test missing, unreadable, malformed and contradictory artifacts with known-failure dominance.
3. Preserve the seal: use approved loader/access provenance plus output allowlisting, not a test-ID scan, and state the attestation's limits honestly.

## Q7. Paths, `h_len`, mask and native all-512 assumption

**Verdict: conditional on later data-only verification, not a textual-path blocker.**

Evidence: S:296–321 agrees with runner constants and the existing cache loader: shard `ids`, `lengths`, `h`; `h_len=lengths[i]`; padded storage shape is not source length. `copyable_mask` in the runner uses raw passage, NFKC and per-token surfaces, matching the normative definition. Token CE remains same-position because mT5 shifts decoder inputs internally.

The preflight content hash independently matches `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`. It records 20/20 native train and 20/20 native val lengths exactly 512; EG2 train range 707–875, val 708–830; contributors at 753 are 16; eligible val at 753 is 15, at 754 is 14. These corroborate the candidate, but raw data/cache/model are unavailable here. No current tokenizer re-run or source-data inspection was performed.

**Next steps:**
1. In an approved data/mechanics stage, verify only allowlisted records, cache lengths and native truncation against frozen provenance, without opening sealed test records.
2. Assert exact cohorts and fail rather than replace IDs or change K if an input artifact disagrees.

## Q8. Is the M arithmetic and tensor geometry consistent?

**Verdict: conditional; principal counts correct, new per-arm statement incorrect.**

Evidence:

| Domain | Derivation | Count |
|---|---|---:|
| F, registered | 15 docs ×3 seeds ×2 variants ×2 endpoints ×2 kinds | 360 |
| L, registered | same | 360 |
| P, registered | 20×3×2×2×2 | 480 |
| PA, registered | same | 480 |
| All primary | 360+360+480+480 | **1,680** |
| Common target multiplicity | 4 arms ×3×2×2×2 | **96** |
| Native-only target multiplicity | 2 arms ×3×2×2×2 | **48** |
| D1 primary | 120+120+160+160 | **560** |
| Phase 7, per arm-seed | 15×5×2×2×2 | **600** |

Thus common 15×96=1,440 plus native-only 5×48=240 gives 1,680. S:1292–1293's 420 per arm is an equal split of the total, not the mixed-domain workload. S:1436's generic “target appears 96 times” also needs the existing common/native-only qualification.

Mean/norm tensors are `[753,512]` for F/L and `[512,512]` for P/PA. A single global mean direction scaled by the target Frobenius norm is well-defined with nonzero finite norms; “no per-target matrix” at S:1003 should be read as no learned target-specific transform, not a ban on storing the required target-specific scaled tensor. `endpoint_ok` demands exact keys, finite CE and ≥5 copy tokens; low-copy targets cannot silently reduce 1,680. Phase-7 600 is a combinatorial count, not yet a complete executable measurement identity.

**Next steps:**
1. Correct registered per-arm counts and any shorthand multiplicity statements without changing domains.
2. Add exact mixed-domain tests, not count-only tests, and geometry/norm/low-copy negative cases.

## Q9. D0/D1 phases, timing and cap

**Verdict: disagree that the timing contract is ready as written.**

Evidence: D0 remains zero-update, ≤4 configs, ≤15 minutes, debug seed 20261111, no scientific labels and no result claim. D1 is four arms, one debug seed, one update each, ≤20 minutes, separate approval. Its initial primary count is correctly 560, and diagnostic count is 600/arm-seed. Step0 must precede the update or use restored initial state.

Adding `t_primary_replay_arm` is necessary and correct, but S:1292–1293 has the wrong registered arm counts. Within the outer ×3 projection, per-arm-seed primary replay must represent 120/120/160/160 keys, not 420. Across all seeds these are 360/360/480/480. Also S:1236–1250's eight-phase list explicitly lists initial primary CE and diagnostic replay, but does not explicitly assign a separately measured primary reload/recompute pass to the new term. It is not enough to charge one measurement twice or assume replay/reload is free. State the timer/subtimer mapping and that it completes inside D1's existing cap.

`T_proj≤96 min` is an admission ceiling, not a measured result. Registered hard abort remains 120 minutes, 12 units, 1,200 updates, six threads, CPU/no GPU, no retry. Prospective D0+D1+registered arithmetic remains **155 min / 1,204 updates**, not permission to spend it.

**Next steps:**
1. Correct the mixed per-arm projection and explicitly measure initial primary CE separately from primary replay/load costs within the eight-phase structure.
2. Reject a projection if any required timer is absent, negative or nonfinite; preserve ≤96 admission and 120-minute hard abort.
3. Seek D1 approval separately only after corrected freeze, implementation/tests and D0; no timing experiment was authorized by this consultation.

## Q10. Ranked remaining must-fixes

**Verdict: agree that a further narrow correction is necessary.**

### MF-1 — High: supplemental golden violates canonical sorting

**Evidence:** S:1348–1361 defines ascending record key `(doc_id, arm, seed, variant, endpoint, memory_kind, donor_sort)`. In `replay_supplemental.records`, the two PA rows have identical earlier key components, but `real` precedes `donor`. Ascending strings require `donor` before `real`.

Independently calculated SHA256 values:

| Serialization | SHA256 |
|---|---|
| Supplemental, listed insertion order | `38e5e2fbbcd30922902e456bb6f16cfca71f6f3b4afedd3806313cb0a08f6695` |
| Supplemental, normative ascending record order | `8277a713fd52b2ba8c5c3c859c83fd78593aa5a381f8640448e2128a97af7a20` |
| Base replay, normative order | `c43ea35c46c51a0e82cebe5764a989d1b67012b2690246a0f89a94dff7851667` |
| State framing | `43ecb58e197d5789df0a9dbbc67beba11538b8063c3da8ac46f96e1e95d65712` |

The base and state constants match; supplemental does not. JSON `sort_keys` sorts object keys, not array records. Resolve this pre-freeze with a reviewed canonical-order fixture/constant and permutation-invariance requirement; do not preserve insertion order by weakening the serializer. The synthetic correction does not touch a trained result or threshold.

### MF-2 — High: mixed replay counts and measured timing mapping

**Evidence:** S:1292–1293 says every registered arm has 420 keys; actual counts are F/L 360 and P/PA 480. S:1278's outer ×3 requires per-seed replay work, 120/160. The newly distinct primary replay term needs an explicitly measured timer/subtimer, separate from initial primary CE and diagnostic replay. Correct the contract and require complete timing components without relaxing either D1 or registered caps.

### MF-3 — High: finish phase-7 measurement and domain schema

**Evidence:** S:1064 uses unbound `donor_prefix`. S:1066–1069 constructs control/real/wrong tensors, but S:1073 records only `{real,donor}`; it never gives a formula specifying whether stored `ce` is raw real/donor CE with a shared variant control baseline, a contrast, or another quantity. Without that binding the two variants could merely duplicate identical raw real/donor CE while the constructed controls go unused. S:1357 allows only `{control,real}`, while the supplemental golden contains `donor`.

Define exact `real_prefix`/`donor_prefix` construction and K bounds, the tensor passed to each forward, raw CE versus derived contrast, the shared baseline storage/key and domain-specific enums. Preserve the 600 diagnostic slots with a separately defined baseline if that is the intended design; do not silently add a third memory axis. Separate primary and diagnostic key validation and digests. Clarify that the supplemental **golden** digest validates synthetic serialization, whereas actual diagnostic replay compares against its own stored run records with numeric tolerances. This is essential for reproducible diagnostics/timing even though diagnostic failure does not gate primary M.

### MF-4 — High: bind P1/test attestation into fail-closed validation

**Evidence:** S:100 defines both fields but S:463 consumes only `p1_used`. Require strict booleans `p1_used=false` **and** `test_split_read=false`, and invalidate on contradictory known-use evidence. Specify the required checked-artifact inventory, data-ID extraction and malformed/absent handling. A false declaration is not self-authenticating proof of non-access; retain the seal and state the trust boundary rather than promising forgery detection from output IDs.

### MF-5 — Medium: make control tensor serialization interoperable

**Evidence:** S:1339–1341 specifies values/dtype/shape and “canonical tensor frames”, but S:1317's frame requires a `name` and only state-dictionary sorting is defined. Control tensors have no prescribed canonical names/order; `M_POS_MEAN` has no intrinsic target ID although NPZ metadata generically requires `target_id`. The NPZ tensor-array key and whether the per-tensor SHA hashes framed payload or archive bytes are also unspecified.

Pin a minimal versioned payload/manifest schema: tensor-array key, shared-target sentinel, canonical arm/seed/variant/target name and ordering, dtype/endian/shape, and exact per-file versus canonical-tensor hash semantics. Add a tiny independent multi-tensor control-manifest golden (including shared mean and target norm). Do not redesign or discard the actual tensors; this is an integrity/implementation contract, not a new scientific choice.

**Not additional blockers:** P_VALID is not unconditionally invalid; arm-specific donors do not invalidate paired F/L or P/PA comparisons; approximately 267 MiB of raw control tensors is reasonable pending real I/O timing. No trained P/PA/M outcome has been inspected or inferred. P0 is descriptive native sensitivity at source length 256, not trained calibration at 512 or evidence for L.

**Next steps:**
1. Resolve MF-1–MF-5 text/fixture-only before freeze; keep every registered scientific choice and cap unchanged.
2. Review corrected schemas, formulas and independent golden values together, then freeze once without post-result tuning.

## Q11. Freeze, implementation, unit tests and D0 approval

**Verdict: disagree for this exact candidate; conditional support after the narrow fixes.**

S:1540–1564 says no code before freeze and excludes later stages from the requested approval. A purported single contract with a contradictory expected digest and projection count should not be frozen merely to let implementation choose which sentence wins. This review recommends **text/fixture correction only now**. After the must-fixes are reviewed and a corrected authority is explicitly frozen, implementation and synthetic/unit tests can be separately authorized, followed by bounded D0. This is not retroactive Phase 6 execution approval.

Minimum acceptance tests to specify before implementation and pass before D0/admission:

* Pure decision logic: ANDn/ORn/NOT3, all nine L pairs, F1–F11 and fixtures 16–18, no mutation, all actual labels reachable; explicit valid-artifacts/calibration-false witness and small-N triple preservation.
* Paths/provenance: legacy P0 compatibility, missing/inconsistent artifacts, duplicate/missing seed artifacts, all required manifest booleans and allowlisted data-ID fields, contradiction dominance; no sealed-test scan.
* Donors/geometry: arm-specific maps and stable indices 0–4; real-only training; no train donors; fixed M K versus eval crops; native identity/PA adapter; contributor/target domains and norm failures.
* Metrics/statistics: same-position CE; raw-passage mask; 4 versus 5 copy tokens in signal and primary M; correct seed-first document bootstrap, 1000 resamples/20261109, missing seed NA, paired retained IDs, threshold equality boundaries and signal-tail tie/zero rules.
* Mode/RNG: fresh F/L/P/PA states, correct trainable inventory, seed→adapter→LoRA initialization, base/native encoder eval/frozen, LoRA dropout active only in training, full eval restoration and training re-entry.
* Coverage/integrity: exact mixed 1,680 keys, D1 560, qualified 96/48 multiplicities, phase-7 600 schema, no duplicates/substitution, canonical permutation-invariant state/replay/control hashes, independently fixed goldens and tensor round-trip/tamper tests, tolerance checks separate from exact integrity.
* Timing/gates: correct 120/160 per-seed and 360/480 registered replay costs, independent initial/replay timing fields, complete finite projection, no D0 projection, hard cap and separate-approval enforcement.

The existing metric test file provides useful historical tests for CE alignment, masks, modes, donor selection and P0 interpretation; it is not PM acceptance evidence. Its entire class is model-path-gated, and the model is absent here. No historical “54 tests” claim is treated as a fresh passing check.

**Next steps:**
1. Complete/review corrections and obtain an explicit corrected freeze plus implementation/test authorization.
2. Pass synthetic/unit acceptance before D0; subsequently keep D0 at zero updates, ≤4 configs, ≤15 min, seed 20261111, `not_a_result:true`, no decision/signal labels.

## Q12. D1 / 3-seed / B0-B boundaries

**Verdict: agree with the staged boundaries; no execution approval follows from this review.**

Evidence: S:1224–1234, 1295–1305 and 1484–1503 explicitly separate D1, registered three-seed and B0-B. The B0-B eligibility predicate restated in v1.0.2 labels is:

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS
AND signal_status == EXPLORATORY_L_SIGNAL
AND m_valid == true
AND n_signal == 15
AND tail_driven == false
AND leakage/mode/metric checks pass
AND required artifacts are complete
AND separate B0-B preregistration and approval exist
```

`tail_driven` is the L **wrong-donor signal copy** tail after the specified aggregation, not an M-control tail; true or NA blocks. `EXPLORATORY_L_SIGNAL` alone is insufficient. P0, `PA_RETENTION`, and historical full-K secondary results do not substitute for any predicate. Native-512 calibration is not evidence of retention equivalence to EG2-753. No B1/B2/Stage C implication follows.

**Next steps:**
1. Preserve explicit D1 approval after D0, then a separate registered-run decision using a complete ≤96-minute projection and the 120-minute hard cap.
2. Restate the exact tuple and signal-tail requirement in any later B0-B request; do not execute that stage automatically.

## Q13. Final recommendation and freeze decision

**Verdict: conditional progression; final category NARROW.**

The experiment need not be abandoned: the principal validity/calibration defect is fixed and no trained positive-control outcome has been seen. But this exact candidate is not yet a fully executable single authority. Resolve its remaining contract inconsistencies before implementation, not through implementer discretion or after results.

| Decision item | Recommendation at this review |
|---|---|
| **Final category** | **NARROW** |
| v1.0.2 freeze as-is | **No** |
| Immediate allowed follow-up | Text/golden/schema must-fixes and review only |
| Implementation + unit tests | **Not yet**; conditional on corrected explicit freeze/authorization |
| D0 | **Not yet**; later only after acceptance and explicit authorization, zero updates, ≤4 configs, ≤15 min |
| D1 | **Not approved**; separate request, four debug updates total, ≤20 min |
| Registered 3-seed | **Not approved**; later 12 units/1,200 updates, admission projection ≤96 min, hard wall ≤120 min |
| Phase 6 execution / B0-B / B1 / B2 / Stage C | **Not approved** |
| Current authorized experimental compute from this consultation | **0 model runs; 0 optimizer updates** |
| Prospective total ceiling, not a grant | D0+D1+registered: **155 min / 1,204 updates**, CPU, six threads, no GPU, no retries/extensions |
| test 163 | **Sealed; do not open** |
| P1 / external API use | **Forbidden by this review scope** |
| T5Gemma2 | **D-108 STOP remains closed** |
| Single implementation authority | **Not sufficient as-is; correct MF-1–MF-5, then freeze with commit/content hash** |

**Incorrect premises corrected:** the fifteen repairs are not all fully closed; matching an insertion-order supplemental hash does not satisfy canonical sorting; 420 is not the registered per-arm mixed workload; an all-false usage declaration plus allowlisted outputs cannot prove no forbidden read occurred. Conversely, separating P_VALID from calibration does **not** make invalid calibration unconditional, and P0 sensitivity does not establish any trained P/PA/L/M pass.

**Next steps:**
1. Make only pre-result contract/fixture corrections, independently verify them, and obtain a corrected freeze decision.
2. Seek bounded implementation/tests/D0 authorization after that gate; retain separate D1, three-seed and downstream approvals.
3. Do not alter registered thresholds, seeds, donors, steps, LR, K, cohorts or caps based on outcomes. Any future scientific redesign requires a new preregistration.