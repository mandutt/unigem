# Independent external review — C5 P/M v1.0.4

Date: 2026-11-09. Reviewer: OpenAI Sol 6.1, independent new review round.

## Review basis and method

- Ran `git fetch origin`, then `git pull --ff-only origin main`; both succeeded, pull reported `Already up to date.`
- Resulting HEAD and `origin/main`: **`0bfee85d20dd0017fe6f07f2e8939ff4c7ccf203`**. The existing workspace branch was retained; no branch switch was necessary to inspect this exact remote-main revision.
- Read the requested review request, v1.0.4 specification, golden vectors, historical v1.0.3 synthesis, five provenance JSON files, runner, and metric tests. Also inspected the helper definitions cited by specification §17.1. The historical synthesis was used to identify residual questions, not to substitute for independent analysis. No other review answer or model was used.
- Performed only read-only source inspection and standard-library, in-memory JSON/hash/framing/length/arithmetic checks. No repository Python modules were imported. No training, evaluation, model forward, generation, D0, D1, or unit-test suite was run. The existing metric suite performs model forwards and was therefore inspected, not executed.
- Did not open the sealed test split, split JSON, raw dataset, model weights, or P1 data. Reading the requested P1 *usage attestations* is not P1-data use.
- Initial worktree was clean. The sole review output is this permitted file; no implementation or protocol artifact is changed. No commit, PR, or execution approval is issued.

Reference shorthand: **S** = `docs/plan_c5_b0a_pm_prereg_v1_0_4.md`; **G** = the v1.0.4 `golden_vectors.json`; **PF** = `reports/provenance/C5_b0a/m_cohort_preflight.json`; **R** = `runner/c5_mt5_lora_b0.py`; **T** = `eval/tests/test_c5_b0_metric.py`.

## Executive verdict

**NARROW — text/schema repair and re-review only. Do not freeze v1.0.4 as-is.**

The flat hash, null ordering, checkpoint-map declaration, tensor framing, and workload arithmetic are substantially improved and independently consistent. However, the phase-7 bound still fails to account for the actual control length, and the frozen/postrun separation does not yet define a complete auditable artifact domain. These are prospective contract defects, not evidence that a trained arm failed. There is **no trained P/PA/M result** in the supplied evidence.

### Verified constants and arithmetic

| Check | Independently observed result |
|---|---|
| PF file SHA256 | `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` — matches S §0.4 |
| State framing | `43ecb58e197d5789df0a9dbbc67beba11538b8063c3da8ac46f96e1e95d65712` — matches G |
| Empty state | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` — matches G |
| Flat base replay | `c43ea35c46c51a0e82cebe5764a989d1b67012b2690246a0f89a94dff7851667` — matches G |
| Sorted flat supplemental replay | `8277a713fd52b2ba8c5c3c859c83fd78593aa5a381f8640448e2128a97af7a20` — matches G |
| Name-sorted synthetic control frames | `6b50c226ecc402323787bd25b20e57fe57376caeb925c040b57985ccc0ec1938` — matches G |
| Primary M per arm-seed | F/L: `15×2×2×2=120`; P/PA: `20×2×2×2=160` |
| Primary M across seeds | F=360, L=360, P=480, PA=480; total **1,680** |
| Four-arm debug primary M | `120+120+160+160=560` |
| Diagnostic records | `15×5×2×2×2=600` per arm-seed, separate from primary M |
| Stored real-control payload | **280,166,400 bytes** before container/metadata overhead, approximately 0.28 GB / 267.2 MiB |

These are fixture/provenance checks, not trained or replayed scientific results. Expected constants were not rewritten.

## Q1. Have the ten residuals closed?

**Verdict: conditional — 8 closed, 2 partial at the specification level; implementation remains unverified.**

| Residual | Status | Evidence and qualification |
|---|---|---|
| 1. Phase-7 K_d / baseline_ce | **partial** | S §9.6.1, lines 1085–1114, explicitly recomputes the baseline and forbids phase-5 CE reuse, but does not bound K_d by the available control length. See Q3. |
| 2. Null total order | **closed** | S §12.2, lines 1430–1432: internal -1 for null, null serialized unchanged, ascending seven-component key. |
| 3. Flat eight-field hash | **closed** | S §§9.6.1/12.2 explicitly exclude nested hash records and exclude baseline_ce/delta; both replay fixture digests reproduce. |
| 4. Twelve-key checkpoint map | **closed** | S §§11.4/12.1 provide JSON object shape, twelve arm/seed keys, file paths, per-unit restore, and aggregate coverage. This is not implemented by the legacy runner. |
| 5. P1 frozen/postrun | **partial** | S §1.5 resolves mutation/hash identity. The registry lists only five artifact patterns and the postrun file is a not_run placeholder; complete inspection-domain and completion semantics remain unspecified. See Q6. |
| 6. Control fixture shape | **closed** | S §12.3 explicitly distinguishes synthetic [1,1] framing from real [K_M,512] postrun tensors; name-sorted fixture digest reproduces. |
| 7. External module contracts | **closed, source-bound** | S §17.1 names all seven helpers and binds behavior to source at the freeze commit. Definitions exist and agree with the stated helper roles. Final commit/hash binding is still a required freeze deliverable. |
| 8. D0 labels/timing | **closed, wording-level** | S §§11.2–11.3 specify four zero-update configurations and clarify decision/signal labels versus target-token labels and manifest timing. The label explanation appears under D1; it should be applied consistently to D0 as well. |
| 9. Per-arm notation | **closed** | S §11.5 explicitly gives F=360/L=360/P=480/PA=480; §11.6 identifies 155 minutes as a prospective envelope, not a grant. |
| 10. dtype / fixture order / note | **closed** | S §§12.1/12.2/1.5 specify <f4, ordering, and allowed unknown keys. Canonical-name ordering is explicit in §12.1 even though G lists the two control tensors in the opposite order. |

**Next steps:** (1) Repair residuals 1 and 5 before freeze. (2) After renewed authorization, demonstrate the closed contracts with synthetic tests; declarations alone are not implementation evidence.

## Q2. Is v1.0.4 self-contained?

**Verdict: conditional — a much better consolidated authority, but not yet a uniquely executable contract.**

**Evidence:** S §§2.5–2.7 define tokenizer, same-position CE, masks, initialization order, training modes, donor rules, and generation. S §§3–7 define tri-state dispatch rather than relying on prior r3.x prose. S §17.1 explicitly incorporates helper source at the freeze commit, so implementation no longer requires hunting through historical reviews. Nevertheless, Q3 admits incompatible phase-7 length interpretations and Q6 leaves the artifact audit domain incomplete. Literal document-only independence is also not the same as source-bound self-containedness: exact helper behavior is incorporated by reference, and the new stats module in §10.2 is still to be implemented.

**Next steps:** (1) Resolve the two contract gaps without importing historical text as authority. (2) Freeze the repaired spec, G, PF, P1 attestation, registry, and exact helper-source identities together. (3) Treat v1.0.4 plus its explicit frozen source dependencies and numbered corrections as authority, not previous model answers.

## Q3. Are phase-7 K_d, baselines, deltas, and 600 records executable?

**Verdict: disagree as an unconditional closure claim. Baseline semantics and counts are repaired; length compatibility is not.**

**Evidence:** S §9.6.1 sets K_d to the minimum of the real and donor memory lengths and asserts the same bound. That assertion is essentially tautological and says nothing about the controls. S §§9.2–9.3 and 12.1 construct/store F/L controls with **753 rows**. With the ordinary full arm-memory interpretation of real_prefix/donor_prefix, the frozen PF lengths and S §2.5.6 donor rule produce **75 pairs** per F/L unit:

- **64 pairs have K_d > 753**, five equal 753, six are below 753; range **750–807**.
- Concrete example: target `REPORT-news_r-00020-00001` has length **777**; nearest donor 0, `REPORT-news_r-05258-00002`, has length **771**. Thus K_d=771, but M_POS_MEAN[:771] and M_NORM(t)[:771] still contain only **753** rows.
- Python slicing silently returns the shorter tensor. A CE forward can therefore succeed while real/donor use 771 positions and the baseline uses 753. This is not a matched-length diagnostic and an assertion on real/donor alone will not catch it.
- If “real_prefix” was instead intended to mean the already K_M-capped M prefix, that construction must be explicit for **both** real and donor. Currently the recipe says memory in arm space, while primary M and signal workloads have different crop rules.

The positive repairs are real: baseline_ce must be recomputed for the same target/endpoint/variant in phase 7, ce is raw record CE, delta=baseline_ce-ce, and phase-5 K_M CE reuse is explicitly forbidden. The 600-key product is correct and diagnostic-only. P/PA lengths of 512 do not exhibit this particular oversize-control problem.

**Next steps:** (1) Obtain an explicit prospective prefix/crop correction that makes real, donor, and selected control lengths identical; do not silently clamp or extend tensors in code. (2) Require equality of all actual tensor lengths, not only an upper bound on real/donor. (3) Add boundary tests below/equal/above 753, including the frozen 777/771 example, and a spy/call-count test that rejects phase-5 baseline reuse. Any measurement-policy correction must be preregistered before execution; primary K_M, cohorts, thresholds, and donors must not be tuned from results.

## Q4. Are canonical hashing and golden vectors consistent?

**Verdict: agree for the normative wire projection and supplied constants.**

**Evidence:** S §12.2 defines the flat fields {doc_id, arm, seed, variant, endpoint, memory_kind, donor_id, ce}; the logical key is for sorting, not a nested hash object. donor_sort is internal only. Sorting records with null→-1 and serializing with sort_keys=True and separators=(',',':') reproduces **c43ea…** and **8277a7…**. baseline_ce and delta are deliberately outside that domain. The stored phase-7 envelope in §9.6.1 can contain key/ce/baseline_ce/delta without contradicting the separate *hash projection*.

This defines a contract; it does not prove a future implementation rejects nested input. Nor does the ce digest authenticate excluded diagnostic fields. The supplemental constant is a four-record synthetic fixture, not the expected digest of actual 600-record diagnostics.

**Next steps:** (1) Test nested-object rejection, flat projection, permutation invariance, and null/donor collisions on otherwise identical key components. (2) Test duplicate/missing-key rejection separately from digest matching. (3) Recompute/compare baseline_ce and delta in diagnostic audit independently of the unchanged ce-only canonical digest; use full-artifact integrity hashes where appropriate.

## Q5. Are checkpoint map and counts correct and aligned with the runner?

**Verdict: conditional — agree with the new contract, but the current runner does not already implement it.**

**Evidence:** S §12.1 enumerates exactly four arms × three registered seeds, using arm/seed keys and sha256-prefixed state digests; §11.4 restores the checkpoint for each unit from checkpoints/{arm}/{seed}.pt. The counts are 120/160 per unit, 360/480 per arm, and 1,680 overall. The state hash covers adapter and LoRA A/B state, excluding the frozen base; it is not necessarily the serialized .pt-file byte hash.

R's train_arm (lines 666–754) accepts only frozen/lora, returns a result object, and does not save the twelve checkpoint files or map. Its CLI at lines 757–802 has no P/PA training arms and rejects zero-step train mode. That is an implementation gap expected before the proposed implementation stage, not evidence that the new map is already verified or that existing outputs can be relabeled into it.

**Next steps:** (1) Implement four-arm, per-seed state save/load only after freeze authorization. (2) Test exact map key set, wrong arm/seed binding, missing/extra entries, and per-unit state restoration. (3) Preserve the distinction between canonical state hashes, container-byte integrity hashes, and the frozen base/config/mode manifest.

## Q6. Is P1 frozen/postrun handling auditable and fail-closed?

**Verdict: conditional — frozen identity is repaired; complete postrun audit closure is not.**

**Evidence:** The requested p1_usage.json contains version 1, p1_used=false, test_split_read=false, checked_artifacts=[], and an allowed note. Its content SHA256 is **69af129a4f58f7400189c361ba2447f12e17d35f012d7a36c26efdf485a3a2dc**. S §1.5 freezes that identity and correctly moves inventory to a separate postrun file. §4.0 says malformed/missing inputs are NA, known-use is false, and known false dominates unknown; no sealed-test scan is required.

However, phase6_artifact_registry.json lines 4–11 list only checkpoint templates, the checkpoint map, the top-level control manifest, and two P1 manifest files. They omit explicit measurement-record/result artifacts and do not define how all nested control tensors and run artifacts are discovered or how inventory completion is reconciled. The file calls itself a “Base registry only.” p1_usage.postrun.json is currently only status=not_run plus an empty inventory, with no item schema/completion contract. S §1.5 also says checked_artifacts must list every inspected artifact while freezing that field empty; the intended postrun binding needs to be explicit.

The frozen attestation is not evidence that all future artifacts were inspected. If test_split_used is evaluated over an incomplete or empty checked set, it can be vacuously false. “Postrun audit-only” should mean the frozen hash is not mutated, not that missing coverage may be called a completed clean audit. S §14 already requires artifact completeness, so this can be repaired without changing a scientific gate.

**Next steps:** (1) Before freeze, define the complete required artifact domain/expansion rules and postrun item/completion schema, including measurement outputs and transitive tensor paths. (2) Bind the live audit's test_split_used to that required domain; missing/unreadable coverage remains NA, any observed out-of-allowlist ID or known P1/test access dominates as failure. (3) Test not_run/empty/missing/malformed/type-invalid manifests, hash mismatch, permitted unknown note, known-use contradictions, and incomplete inventories; never open sealed test IDs to perform these checks.

## Q7. Are control shapes, storage, digest, and footprint coherent?

**Verdict: agree for primary M storage/framing, subject to Q3 for diagnostic slicing.**

**Evidence:** S §12.1 specifies NPZ key tensor, canonical names control/{arm}/{seed}/M_POS_MEAN and control/{arm}/{seed}/M_NORM/{target_id}, <f4, and [K_M,512]. The per-tensor digest covers the canonical tensor frame, not NPZ ZIP bytes. control_digest concatenates frames sorted by canonical name. G's [1,1] example is expressly synthetic, and its name-sorted digest reproduces **6b50…**. It is not a real run digest.

There are three seeds × two F/L arms × (1 shared mean + 15 target norms), and three seeds × two P/PA arms × (1+20). Their float32 payload is **280,166,400 bytes**, consistent with the approximate 0.3 GB claim before overhead. The real digest is necessarily postrun-only.

**Next steps:** (1) Test realistic [753,512]/[512,512] synthetic tensor round-trips, dtype/endian/shape checks, and NPZ tensor-key enforcement. (2) Verify every target norm and shared mean against the complete manifest on load. (3) Retain required controls through B0-B without treating retention as B0-B approval.

## Q8. Are external module contracts sufficient and is missing→NA safe?

**Verdict: conditional agreement for source-bound reuse, not unqualified standalone reimplementation.**

**Evidence:** All seven symbols listed by S §17.1 exist. Adapter in runner/c5_mt5_layer_probe.py lines 52–63 is Linear→GELU→Linear→LayerNorm; make_labels lines 79–83 returns [1,T] long labels with native special tokens; load_layer_cache lines 66–76 slices h by the stored scalar length. LoRALinear in runner/c5_a1_lora.py lines 45–65 uses kaiming A, zero B, dropout, and alpha/r. R lines 52–75 assert 64 attached decoder modules; native_memory lines 135–141 returns detached encoder hidden states. repeated_4gram_rate is whitespace-stripped character-fourgram repetition and telemetry-only.

These sources plus the explicit S semantics are a sufficient reuse starting point. The tiny table alone is not a full independent API specification. Missing-helper→NOT_ASSESSABLE is conservative only if execution stops before a dependent forward and the failure is recorded; it must not fabricate a result or let unavailable telemetry silently satisfy an integrity gate. R's old mode helper requires an adapter and only frozen/lora arm names, so it cannot be applied unchanged to P.

**Next steps:** (1) Record exact helper revisions/content identities in the eventual freeze manifest. (2) Test dimensions, label shape, RNG construction order, four-arm mode/trainable sets, and P's no-adapter path. (3) Fail before execution on required missing helpers; report NA rather than substituting behavior.

## Q9. Are D0/D1, eight phases, and compute caps consistent?

**Verdict: agree with the prospective limits; execution readiness remains conditional.**

**Evidence:** S §11 gives D0 ≤4 configs, one per arm, seed 20261111, zero optimizer updates, ≤15 minutes, no timing projection; D1 separately requires four arms × one debug seed × one update, ≤20 minutes, not_a_result=true, and no decision/signal labels. Target-token labels are still needed for CE. Step0 must precede updates or use restored initial state despite its placement after the update in the phase enumeration. Four-arm debug primary M totals **560**, diagnostic work is **600 per arm-seed**. All eight phases must be measured, including separately accounting for primary replay in §11.5; a missing phase means no projection.

Registered training is 12 units ×100 updates = **1,200**, CPU six threads, no GPU, no retry, a **120-minute hard abort**; D1's finite, nonnegative T_proj must be **≤96 minutes**. The total prospective envelope is **1,204 updates /155 minutes**, not an authorization. There is no fresh timing evidence in this review, and no basis to say the projected run fits.

**Next steps:** (1) Fix Q3 before declaring the phase-7 workload executable. (2) Test D0 zero-update behavior, proper step0 restoration, and complete phase accounting. (3) Seek separate D1 authorization and then separate registered-run authorization; D0 cannot substitute for D1 timing.

## Q10. What must still be fixed?

**Verdict: disagree that v1.0.4 has no remaining freeze blockers. Ranked list:**

1. **High — phase-7 length contract (freeze blocker).** S §9.6.1 does not ensure the controls can represent K_d. The frozen 777/771 example proves the issue without a model forward; 64/75 F/L pairs are affected under the natural full-memory interpretation. Explicitly resolve prefix construction and require actual equal lengths before any execution. Do not silently change primary K_M/cohorts or pad/extend the mean.
2. **Medium — complete postrun artifact/audit contract (freeze blocker).** S §§1.5/4.0/17.2 and the base registry do not define a complete required inventory or a completed postrun audit. Bind the separate inventory to all required produced artifacts and define incomplete/contradictory behavior. Keep the frozen attestation immutable; do not turn its empty list into proof of a clean run.

**Implementation acceptance requirement, not a request to change the eight-field hash:** diagnostic baseline_ce and delta must have recomputation/consistency checks outside the raw-ce hash. S §11.4 explicitly describes CE comparison but does not establish verification evidence for excluded fields. Test their tampering separately before accepting diagnostic outputs. A full artifact integrity hash can coexist with the fixed canonical projection.

The twelve-key map is now well specified; lack of corresponding legacy-runner code is expected future work, not another schema blocker. Small cleanup: §13.2's “target appears 96 times” applies to common targets only; native-only targets appear 48 times as correctly specified in §9.5. Distinguish the synthetic supplemental golden from actual diagnostic hashes in implementation names/reporting. Neither cleanup warrants retuning science.

**Next steps:** (1) Make only the two prospective text/schema repairs and review the diff. (2) Re-review before freeze. (3) Keep the hash/diagnostic acceptance tests fixed before implementation results exist.

## Q11. May freeze, implementation/unit tests, and D0 proceed?

**Verdict: conditional in principle, withheld for the current candidate.**

**Evidence:** S §16.1 prohibits code before freeze. Q3 and Q6 prevent treating the present candidate as an unambiguous frozen contract. T checks same-position CE, masks, generation telemetry, F/L modes, native donor assignment, and descriptive P0 decisions, but it does not establish the proposed four-arm M/state/replay/audit implementation. It loads the real local model in setUpClass and therefore was not run during this consultation.

Required test specifications should be fixed before implementation, with executable checks staged after renewed authorization:

- Pure tri-state/decision tests: ANDn 2/4/5, all nine L pairs, F1–F11, fixtures 16–18, false-vs-NA precedence, label reachability, preserved small-N validity triple, input immutability.
- Exact endpoint domains: 1,680 keys; per-unit 120/160 and per-arm 360/480; common multiplicity 96 versus native-only 48; duplicate/missing/short-copy rejection; zero/nonfinite norms and no 15→14 substitution.
- Builder/mode/RNG tests: four arm contracts, P identity/no adapter, PA adapter-first/LoRA-next RNG order, frozen native encoder/base decoder, LoRA-only trainability where required, eval control construction, all native lengths 512.
- Phase-7 tests: resolved equal-length construction, below/equal/above-cap cases, per-donor recomputed baseline for each target/endpoint/variant, delta arithmetic, 600 keys, and no diagnostic effect on primary replay_ok/m_valid.
- State/replay tests: all five independently fixed goldens; flat projection, null sort, permutation invariance, exact key set; twelve checkpoint bindings; tensor-frame vs NPZ-byte hashing; numeric atol=1e-5/rtol=1e-4 versus exact integrity hashes; debug/final separation; excluded diagnostic-field audit.
- Audit/statistics/cap tests: complete inventory and strict manifest fields, frozen-file immutability, failure-dominant contradictions, missing coverage NA; document-level seed-average-first bootstrap (1,000 draws, seed 20261109), missing registered seed NA, seed counts distinct from document counts, tail ties/zero denominators; D0 zero updates/no labels/no projection and hard run boundaries.

**Next steps:** (1) Repair and re-review before freeze. (2) If subsequently approved, implement and run synthetic/unit mechanics checks before any data/model D0. (3) Consider D0 only after the requisite tests pass and its own scope is authorized; no D0 is authorized or executed by this report.

## Q12. Are downstream boundaries adequate, and what is the B0-B predicate?

**Verdict: agree with the boundary, not with any claim that a gate has passed.**

**Evidence:** Restating S §14 in v1.0.4 labels:

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS
AND signal_status == EXPLORATORY_L_SIGNAL
AND m_valid == true
AND n_signal == 15
AND tail_driven == false
AND leakage/mode/metric pass
AND artifacts complete
AND separate B0-B preregistration and approval
```

tail_driven is **L copy-signal tail on the 15 eligible docs**, not an M-variant tail; true/NA blocks. m_valid is joint P/PA calibration, not merely artifact validity. EXPLORATORY_L_SIGNAL alone is insufficient. D1, registered three-seed work, B0-B, B1, B2, and Stage C require their respective separate authorization; debug seed 20261111 is never a registered-seed substitute.

P0 reports train +3.7617 [1.8917,5.6050] and val +5.2375 [2.5013,8.0753], with 14/20 and 18/20 positive documents. Its legacy seeds_positive field counts **documents**, not training seeds. Val median is 2.9739 and absolute top-three share is 0.433549 (signed share 0.4862 is descriptive). P0 source length is 256, not the proposed native 512; untrained real copy CE is about 12.70/13.24, above the supplied ln|V| reference near 12.43. These facts support native-path sensitivity only, not trained P/PA/L quality or a downstream gate.

**Next steps:** (1) Keep each authorization boundary explicit. (2) Accept only complete registered evidence for the predicate; no missing-seed pooling or post-result changes. (3) Preserve test 163 sealed, P1 unused, and T5Gemma2 D-108 STOP.

## Q13. Final verdict and freeze scope

**Verdict: conditional — final recommendation NARROW.** The appropriate action is prospective contract repair, not a scientific STOP conclusion about unrun trained arms and not CONTINUE into execution.

| Scope | Review recommendation at this HEAD |
|---|---|
| v1.0.4 freeze | **Withheld** pending the two must-fixes and re-review |
| Implementation + unit-test execution | **Withheld** under the current no-code-before-freeze contract; test requirements may be planned |
| D0 | **Not approved**; only potentially eligible after repaired freeze, tests, and explicit authorization |
| D1 | **Not approved**; separate four-arm, one-update timing/debug decision required |
| Registered three-seed run | **Not approved**; separate decision after complete D1 projection ≤96 minutes |
| Phase 6/B0-B/B1/B2/Stage C | **No execution/downstream approval** |
| Maximum compute now | **Zero optimizer updates and zero model forwards**; consultation/source/fixture checks only |
| Prospective caps, not a grant | D0 ≤15 min/0 updates; D1 ≤20 min/4 updates; registered ≤120 min/1,200 updates; combined ≤155 min/1,204 updates, six CPU threads, no GPU/retry/extension |
| Test 163 | **Sealed; not opened** |
| P1 | **Unused; no external API use** |
| T5Gemma2 | **D-108 STOP remains; no reopening** |
| Sole implementation authority | **Not sufficient as-is**; repaired frozen spec plus explicit frozen helper/artifact identities and numbered corrections can serve this role |

**Next steps:** (1) Address only the ranked must-fixes in a prospective correction. (2) Re-review and record actual freeze commit/content hashes if accepted. (3) Request subsequent narrow implementation/unit-test/D0 authorization without bundling D1, three-seed, or downstream approval.

### Incorrect premises to avoid

- Adding K_d <= min(real_len, donor_len) does not guarantee K_d fits a 753-row control.
- A successful Python slice is not evidence of equal sequence lengths.
- A frozen false-use attestation or empty postrun placeholder is not a completed non-use audit.
- Matching synthetic hashes is not a real checkpoint/control replay or a trained result.
- The twelve-key schema is not already supported by the legacy two-arm runner.
- Positive untrained P0 contrasts are not trained P/PA/M calibration or B0-B approval.
- No result may justify changing threshold, seed, donor, update count, learning rate, or cohort after the fact; a changed scientific policy requires a separate prospective preregistration.

### Reviewed file identities (not a freeze declaration)

```text
HEAD/origin/main 0bfee85d20dd0017fe6f07f2e8939ff4c7ccf203
spec SHA256     68eb00d7b4f10fc5612aaa10ee64bfbd5bbfb4245bd01636ea75f9086d2418a0
golden SHA256   74a91006be456ae4dc569e06d947a34bd14d0ed64a8e8aeff282fdde34b30564
P1 SHA256       69af129a4f58f7400189c361ba2447f12e17d35f012d7a36c26efdf485a3a2dc
PF SHA256       3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af
```