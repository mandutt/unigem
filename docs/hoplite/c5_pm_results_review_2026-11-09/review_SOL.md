# Independent C5 Phase 6 P/M results review — SOL

Date: 2026-11-09

**Reviewed HEAD:** `d809e0002d0653e3c4207c58a38bb8af0b641467`.

## Scope and evidence

This is a new independent results/cause review, not a continuation of a preregistration review. No prior-thread conclusions or other reviewers' reports were consulted. The review request, frozen v1.0.11 plan/manifest, three requested result reports, three requested JSON artifacts, and both requested runner files were read. Supporting inspection covered the statistics/adapter helpers, label-test source, registry, replay reports, stored M/Phase-7 records, control-manifest metadata, and usage attestations.

Initial synchronization ran `git fetch origin`, then `git pull --ff-only origin main`; both succeeded and the pull reported “Already up to date.” The working tree was initially clean. A later history-only fetch (`--deepen=40`) made the freeze/result commits inspectable; it also observed `origin/main` advance to `0d36150`. It did not change the checked-out HEAD. This report reviews the full SHA above, not that later remote revision.

Verification was **static inspection and arithmetic/key/hash checks on already-produced artifacts only**. No training, model forward, evaluation, replay, or unit-test execution was performed. No test-163 data, split file, F5 source dataset, EG2 caches, or P1 content was opened. No subagents or additional LLMs were used. This report is the sole intentional working-tree addition.

## Q1. Label/gate correctness

**Verdict: conditional — agree with the observed signal/tail arithmetic and the blocked gate; do not independently certify every supplied validity flag.**

### Evidence

Frozen §§3.5, 6, 10.4 and 14 imply the reported negative decision:

| Quantity | Reviewed result | Contract consequence |
|---|---:|---|
| L copy mean | -0.1135062493 | fails `>= .05` |
| L copy stored 95% CI | [-0.2340902249, -0.0011667131] | fails lower bound `>0` |
| Paired L−F copy mean | -0.0026393551 | fails `>0` |
| L copy positive seed means | 0/3 | fails 2/3 |
| L full mean | -0.1085498810 | fails `>0` |
| L full stored 95% CI | [-0.2234064522, -0.0057343320] | fails lower bound `>0` |
| Paired L−F full mean | -0.0008659808 | fails `>0` |
| L full positive seed means | 0/3 | fails 2/3 |

I independently recomputed the copy/full means from final per-document records, averaging the three seeds within document. The 15 common IDs match the label cohort. These are 15 document units, not 45 independent observations. The CI values above are the stored values: I inspected the PCG64/1,000-resample/linear-percentile implementation, but did not independently regenerate those intervals (NumPy is not installed in this review interpreter). Their exact reproduction is not needed to establish that the observed negative means fail the frozen positive-mean conjuncts.

`L_COPY_SIGNAL=false`, `L_FULL_SIGNAL=false` therefore give `l_signal=false`, `copy_only=false`, `full_only=false` under the frozen consensus, not a missing/mixed-endpoint state. The pure decision functions implement the relevant false-dominant operators and dispatch correctly for these supplied inputs.

The independently recomputed signal-tail absolute share is `0.4774638896`, and the leave-top-three mean is `-0.0278806395`. The latter triggers `tail_driven=true` **before** the `.50` absolute-share test. Signed share `0.8034952989` is descriptive, not the gate. Here “tail_driven” is a conservative positivity/robustness label; it does not mean three outliers alone explain the negative finding.

All 1,680 stored primary-M records have the exact expected mixed-cohort keys, no duplicates, finite CE, and endpoint flags/copy-token counts meeting the stated availability requirements. Recomputed M means agree with `registered_report.json`. The supplied M passes yield `m_pass_l=true`, `m_valid=true` and `M_CONTROL_PASS`. Given the supplied `VALID`, dispatch is correctly `MEAN_CONTRAST_ONLY`, and B0-B is false on **both** signal and tail. Separate approval is also absent.

Two qualifications prevent a blanket implementation/integrity endorsement:

* `l_predicate` accepts unkeyed seed means and does not enforce all three registered seed identities or complete paired cohorts. Two positive supplied seeds could pass; empty data become boolean false rather than necessarily NA. The current artifacts do contain all three seeds, so this does not explain the observed result, but missingness enforcement must exist in a documented caller.
* `VALID`, `assay_path_ok=true`, and artifact completeness require provenance beyond successful numeric label dispatch. Q6 identifies unresolved support for those inputs. If assay validity becomes unknown or invalid, the frozen signal-status dispatch changes to `NOT_ASSESSABLE` for these negative L predicates; B0-B remains false. Do not silently retain a certified `VALID` while acknowledging unresolved assay evidence.

### Next steps

1. Preserve the negative L predicates, signal-tail calculation, and false B0-B decision without threshold/cohort changes.
2. Bind the validity/availability flags to explicit evidence and document the caller's exact seed/cohort/missingness enforcement.
3. Record the distinction between “correct label calculation given inputs” and “independently audited assay validity.”

## Q2. Is the adapter-bottleneck explanation established?

**Verdict: conditional — “adapter bottleneck” is a well-supported working diagnosis of this tested regime, not a uniquely established mechanism.**

### Evidence

On the same 15-document seed-averaged copy endpoint, P is `3.0764133618`, PA is `0.0112111388`, and P−PA is `3.0652022229` with 14/15 positive paired contrasts. That is strong evidence that the **adapter-added training regime** loses decoder-usable native donor specificity under this budget. Native PA's failure makes EG2 layer19 an insufficient *sole* explanation. It does not establish that raw EG2 is adequate.

F/L adapter outputs show between-document mean-vector variance falling from `4.882894` to `0.084995`/`0.080694` (about 98.26%/98.35% contraction). But PA variance rises from native `0.840866` to `1.283642` while its signal is tiny. Thus variance contraction is neither a universal mechanism nor a sufficient proxy for usable information. These are pooled mean-token-vector diagnostics, not a measurement of all token-level content or decoder attention. Centered cosine near -0.067, close to the geometric reference -1/(15−1), and retained effective ranks also caution against treating cosine/scale changes as proof of erased content. The centered JSON does not itself supply a full seed-indexed extraction/provenance recipe.

Important confounders and overstatements:

* **P/PA are not identically initialized LoRA interventions.** `build_arm` seeds, constructs PA's random adapter, then attaches LoRA without reseeding. P skips adapter construction and consumes a different RNG stream for LoRA A/dropout. Both use the same LoRA *configuration*, not identical trainable initialization. Adapter insertion also changes the function at step zero, trainable parameter count, optimizer groups and joint gradient clipping. The comparison identifies the whole regime change, not capacity versus initialization versus optimization versus alignment.
* **Loss of compatibility precedes training.** The registered table already shows P step-zero copy contrast around +7.06 on val20, versus PA negative seed-dependent contrasts. The results do not isolate a collapse *caused by training*. A random non-identity `Linear→GELU→Linear→LayerNorm` transformation can disrupt the pretrained native encoder–decoder interface immediately.
* **F versus L is not an equivalence test.** Paired copy mean -0.00264 has stored CI [-0.04084, 0.03430]. Lack of a detected LoRA benefit here does not rule out LoRA interactions, different acquisition timescales, or the frozen decoder interface as limitations. P refutes “LoRA universally destroys specificity,” not every LoRA-related explanation.
* **The cause table mixes estimands.** Its F/L M full contrasts use 15 targets at fixed prefix 753, whereas its wrong−real figures match final **val20** full contrasts: F `+0.0007721`, L `-0.0167319`. On the actual common-15 signal cohort these are F `-0.1076839`, L `-0.1085499`. P's table value `2.5306140` is likewise val20, versus `2.8204737` on common15. F/L donor-cropped signal length also differs from primary M's fixed prefix. Ratios such as wrong−real/M should not be interpreted as fractions of content use without matching population, crop, endpoint and weighting.
* Copy-token availability does not establish the copy mask's semantic validity. Three consistently negative seed averages and the bootstrap interval support this registered negative result, but do not eliminate sampling uncertainty or prove the mechanism. Likewise, P/PA matching K=512 cannot rule out F/L-specific donor/crop effects.

A generic memory-distribution shift is consistent with the observations. It is not directly separated from interface rotation, scale/normalization, random-initialization damage or under-acquisition. The negative result is stronger than the proposed mechanistic certainty.

### Next steps

1. Qualify the causal claim and replace mixed-cohort/crop ratios with explicitly matched descriptive comparisons from existing artifacts where available.
2. In a new prereg only, match saved LoRA initialization across adapter/no-adapter arms and specify step-zero versus final contrasts.
3. If mechanism identification is the aim, preregister a tightly bounded identity-preserving/frozen-adapter control rather than claiming variance contraction alone proves causation.

## Q3. Proposed F0 design

**Verdict: disagree with `F0/F/P/PA` as a clean 2×2; conditional support for a corrected adapter-free EG2 diagnostic.**

### Evidence

F0 = raw EG2 layer19 memory + decoder LoRA, without an adapter, is a useful intervention. However, the matched EG2 adapter-present comparator is **L**, not F:

| Memory source | No adapter; decoder LoRA | Adapter; decoder LoRA |
|---|---|---|
| EG2 layer19 | F0 | L |
| Native mT5 | P | PA |

In `F0/F/P/PA`, F0 versus F changes both adapter presence **and LoRA presence**. Historical near-zero L−F does not make these interventions interchangeable. Use `F0/L/P/PA`; keep F only if a separately justified extra LoRA ablation is needed. This is a new experiment, not a relabeling of existing units.

“raw 512” must mean **512 feature dimensions**, unless a new token-prefix experiment is explicitly intended. The frozen EG2 M length is 753 tokens; native M is 512 tokens. Changing F0 to a 512-token prefix while comparing it to historical F/L at 753 introduces another intervention. Specify training, signal, M and generation lengths separately. Three seeds and 100 updates may be a bounded diagnostic, not a guarantee of sufficient acquisition or statistical power.

Counts `M=1,680` and Phase-7 `7,200` are valid only if the new contract preserves the 15/15/20/20 target domains, three seeds, and relevant endpoint/variant/donor axes. Re-derive them; do not inherit counts by arm name. Source-specific donor rules differ in the frozen experiment. Within-source adapter contrasts need identical donors/crops; any cross-source interaction claim additionally needs a predeclared common-donor/crop estimand or an explicit limitation. Same seed numbers alone do not match RNG initialization.

A positive F0 with a matched negative L would support adapter-regime interference for EG2 under the specified budget, not prove a unique bottleneck mechanism. A null F0 would not establish that EG2 features lack information: raw EG2 and native mT5 share width but not a learned coordinate system, scale or tokenization. Small decoder LoRA and 100 updates may not learn that alignment. A new prereg must define F0's own positive/negative/inconclusive criteria; the old L>F predicate is not automatically appropriate for F0.

### Next steps

1. Preregister `F0/L/P/PA`, matched LoRA initial state within pairs, immutable donors/cohorts, and explicit sequence-length semantics.
2. Freeze paired adapter contrasts plus source-specific donor-use endpoints, seed/document aggregation, tail rules and an inconclusive region before running anything.
3. Make P replication a required assay check, retain M as a separately interpreted control, and bound any identity-preserving H3 control in advance rather than adding it after F0 is seen.

## Q4. M endpoint interpretation

**Verdict: agree that M_PASS is not donor-specific content-use evidence; disagree with retrospective removal of the frozen M gate.**

### Evidence

M compares real memory with a train-derived position-wise mean, or that mean rescaled to the target real-prefix Frobenius norm. It tests a particular mean-replacement contrast. Wrong-donor testing preserves a different set of memory statistics and asks whether the *correct document* helps. There is no contradiction in passing M while failing the latter.

For example, L's primary full M means are `+0.3646992` (POS) and `+0.3782898` (NORM), while its common15 wrong−real full signal is `-0.1085499`. Both findings can hold. M_NORM controls one scalar norm, not token covariance, higher-order distribution, semantic alignment or all distribution shifts; it even retains target-derived magnitude. M superiority alone therefore cannot certify donor identity use, factual grounding, good free generation, or an F5-quality resident encoder.

The frozen contract already distinguishes `MEAN_CONTRAST_ONLY` from `EXPLORATORY_L_SIGNAL` and requires both signal and M-related conditions for B0-B. Clarifying this interpretation is faithful reporting, not changing an endpoint. Replacing thresholds, removing PA calibration, deleting M from the old gate or promoting M_PASS into content-use success would be retrospective changes. For a genuinely new prereg, M may be descriptive or a necessary-but-not-sufficient sanity/calibration condition; that role must be chosen prospectively. Removing M never removes the need for a donor-specific primary assay and separate approval.

### Next steps

1. Keep all frozen M numerical results, thresholds and gate roles in this Phase 6 record.
2. State “mean-memory contrast” rather than unqualified “content use”; keep fixed-prefix primary M separate from cropped donor diagnostics.
3. Choose and justify M's role prospectively in any new prereg, without using that choice to rescue this result.

## Q5. Terminate Phase 6 or open a new prereg?

**Verdict: agree with terminating this registered Phase 6 as negative for advancement; NARROW any possible follow-on to a separately approved diagnostic.**

### Evidence

All registered units are reported complete. The registered EG2 L signal fails both endpoints and its tail gate. No B0-B candidate or downstream authorization follows. Provenance qualifications may change the strength of the assay-validity claim, but cannot make these artifacts an affirmative advancement result.

A corrected F0 diagnostic is scientifically reasonable if the limited goal is deciding whether to retain this specific EG2/decoder interface. It is not an extension/retry of the frozen Phase 6. H3 residual/identity-preserving adapters are hypotheses for a new bounded comparison, not mandatory modifications implied by the current causal story.

If F0 fails while a matched P control succeeds, stop the **tested raw-layer19 + specified decoder-LoRA budget** route under a predeclared decision rule. Do not infer impossibility for every EG2 layer, interface or resident-encoder design. If P fails, interpretation is assay failure/inconclusive rather than EG2 rejection. If F0 succeeds and L fails, adapter-free continuation might be preferable; success does not logically require rebuilding the adapter. Neither outcome alone establishes generation quality or authorizes B0-B.

### Next steps

1. Close and archive the frozen run as “no affirmative L donor-use signal; B0-B blocked,” retaining unresolved integrity qualifications.
2. Resolve Q6 and freeze a corrected, separately approved F0 protocol before any new execution; no current threshold/seed/donor/step/LR changes.
3. Define prospective success, failure, inconclusive and resource-stop rules; keep H3 separate unless explicitly included before results.

## Q6. Artifact/provenance sufficiency

**Verdict: conditional — enough stored evidence for the negative decision and to formulate a new question; insufficient for unconditional audit closure or B0-B readiness.**

### Positive evidence

* Historical committed plan bytes at freeze commit `6fad89e59e4aa2222010f2360e5eb4c2572c4023` hash to `327a3e34f5bb2721b8b2400718dfd7bc56a0946641d1e83e2c8b454bf656d007`. Historical manifest bytes at `05b7abe9a011ff1f7e0095dc7d2be37c61e0266e` hash to `f5d9ac8a1ce8528991b7ae6f7f9eda8f3ef2b6d29df29d05489f2cbfa9f34764`. HEAD blobs match those hashes. `manifest_commit:null` inside the frozen JSON is intentional; the external commit file resolves it correctly.
* Registry entries carrying concrete file paths and SHA-256 values matched the present file bytes in my check. There are 12 registered checkpoint-map keys; filesystem inventory contains 16 checkpoint files including four debug units, and corresponding control files are present. Presence/file hashes do not verify canonical tensor/state hashes or model compatibility.
* The exact stored primary-M domain is 1,680 finite records. Each of the 12 stored Phase-7 units has exactly its expected 600 keys, finite CE/baseline/delta, and internally correct `delta=baseline_ce−ce`: 7,200 diagnostic records total. This is stored-record checking, not numeric replay.
* Replay reports attest 12/12 success with `atol=1e-5`, `rtol=1e-4`. I did not perform fresh replay. Git history separates registered completion (`9d6be7a`) from labels/replay (`d9aac0e`). Therefore `labels_computed:false` in the immutable registered report and `true` in the later label artifact are not inherently contradictory.

### Material gaps

1. **Non-access is not established by the current loader/attestation.** `p1_usage.postrun.json` lists only the registered summary and combined M-record file. Frozen §1.5 requires expanded inventory covering checkpoints, control tensors and Phase-7 artifacts, and self-listing the postrun manifest. The registry still has generic `pending_d1` entries despite later specific entries. Most importantly, `load_frozen_inputs` calls `read_jsonl_by_id(DATA)`, which reads and parses the entire F5 JSONL before selecting the frozen IDs; it also reads the full splits JSON. If the documented full clean dataset was used through this path, this is inconsistent with a literal claim that test rows were never read, even if no test examples were evaluated. The actual registered driver is not supplied by the advertised CLI, so I cannot establish its exact access behavior. Do not inspect sealed data to resolve this: obtain the executed code/command and access evidence. Confirmed prohibited access must be reported as assay-invalid, not hidden by an allowlist-only output check. No P1 use is shown by the reviewed results, but negative attestations are not proof of non-access.
2. **Canonical control hashing differs from the frozen specification.** Frozen §12 requires logical control names plus dtype/shape/length-framed tensor bytes and per-tensor metadata. `tensor_digest` instead hashes local key, NUL and raw float32 bytes; `write_control_manifest` returns an aggregate entry without the mandated per-tensor name/dtype/shape/frame metadata. The registered control manifest has per-unit summaries rather than that full schema. Successful CE replay or a JSON-file SHA does not establish compliance with the canonical control digest. Request a documented actual hashing implementation and correspondence to retained tensors; do not rewrite historical digests and claim they were original.
3. **The execution-to-label audit chain is incomplete.** `c5_pm_phase6.py` has `train_registered`, but `main --mode registered` still raises `NotApprovedError`. The supplied label module contains primitives, not the artifact-loading/orchestration code that produced all the final flags. Per-unit replay JSON contains success booleans/counts/tolerance, not a full checkpoint/control/final-record digest binding or the executing implementation identity. Preserve the actual registered, replay, label and cause-analysis commands/scripts, revisions, environments, input hashes, output hashes and authorization records. Bind the transition to `labels_computed:true` explicitly to immutable registered inputs. Commit ordering explains the transition, but does not by itself make it reproducible.
4. **Primary/diagnostic and resource compliance need explicit records.** Frozen §11.4 requires primary replay and `diagnostic_replay_ok` to be separate; supplied reports have primary and Phase-7 component booleans but one overall `replay_ok`, without the requested separate diagnostic field. The executed combination rule is not auditable from those booleans. Also, four simultaneous arms × two threads describes eight threads, versus the frozen six-thread budget. `4939.884s` is a sum of wave-max unit elapsed times, not a demonstrated end-to-end wall measurement including the separately reported replay stage. This does not prove a cap overrun, but neither the full-cap claim nor any resource deviation is closed without timing/approval evidence.

These issues are not a reason to rerun training or evaluation in this consultation. They are reasons to narrow the validity claim, retain the negative decision, and repair the evidentiary package through a separately authorized process. A new prereg may be drafted now; execution should not inherit unsupported “artifact complete” or “test never read” claims.

### Next steps

1. Prioritize executed-path/non-access evidence and a complete expanded postrun inventory, using only frozen allowlists and unsealed metadata; record unresolved or confirmed violations honestly.
2. Preserve and bind actual orchestration/replay/label/cause code and canonical-hash evidence, separating primary from diagnostic replay and documenting resource accounting.
3. Publish an append-only audit clarification rather than altering frozen artifacts, historical negative results or their preregistered rules.

## Final decision block

**최종 판정: NARROW**

**B0-B candidate false:** Confirmed as the only justified advancement decision. Both registered L endpoints fail, signal-tail is true, and separate approval is absent. Supplied `VALID` remains provenance-qualified, not independently certified.

**adapter bottleneck:** Plausible leading regime-level explanation, especially P versus PA; not a uniquely established causal mechanism. Random non-identity initialization/interface damage, RNG/optimization differences, and pooled-variance diagnostics prevent “adapter decisive; all alternatives rejected” certainty.

**F0 설계:** Use a new prereg with `F0/L/P/PA`, not `F0/F/P/PA`, for a LoRA-held-constant 2×2. Specify feature width versus token length, matched initialization/donors/crops, re-derived record domains, and positive/negative/inconclusive rules. No execution is authorized here.

**Phase 6 종료/새 prereg:** STOP the frozen Phase 6 as a negative advancement result. NARROW possible future work to provenance closure and an independently approved bounded diagnostic; do not CONTINUE into B0-B or retrofit current results.

**금지 범위:** No training/evaluation/replay in this consultation; no test 163/P1 access; no additional LLMs/subagents; no retrospective threshold/seed/donor/step/LR changes; no automatic B0-B/B1/B2/Stage C; T5Gemma2 remains D-108 STOP. No repository edits other than this report.

**Must-fix (ranked):**
1. Resolve the executed data-access path and assay/non-access claims without opening sealed data; complete inventory and qualify `VALID` until supported.
2. Complete the execution/replay/label/hash/resource audit chain; distinguish primary from diagnostic replay and retain immutable historical artifacts.
3. Correct the proposed F0 factorial, RNG/length/cohort design and prospective interpretation before new approval.
4. Qualify causal exclusions and remove mixed-cohort/crop ratios from mechanistic claims; keep the negative frozen labels intact.

**잘못된 전제:** Same seed numbers do not imply identical LoRA initialization; F0/F is not an adapter-only contrast; 512-dimensional memories need not share a decoder-compatible representation; mean-vector variance contraction is not proof of information destruction; M_PASS is not donor-specific content use; a null result is not an equivalence proof; F0 failure does not condemn all EG2 resident-encoder designs, and F0 success neither proves a unique cause nor mandates a new adapter. Replay flags and frozen hashes do not by themselves prove non-access or full provenance completeness.