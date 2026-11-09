# Independent external review — Sol 6.1 medium reviewer

**Reviewer:** Sol 6.1, medium reasoning. **Round:** new, independent v1.0.1 consolidated-repair review, 2026-11-09. This is my own review of the current artifacts, not reuse of an earlier model's report. The required historical synthesis is background evidence, not authority for my conclusions.

**Final recommendation: NARROW.** The mixed-domain repair is real and arithmetically correct. However, the current candidate is not yet a total, internally consistent single implementation authority. Recommend text-only repair and re-review before freeze, implementation, or D0. No Phase 6 execution, D1, registered three-seed run, or B0-B is approved by this review.

## Review basis and read-only verification

- Ran `git fetch origin`, then `git pull --ff-only origin main`; both succeeded, and pull reported `Already up to date.`
- Resulting `HEAD` and `origin/main`: **`30b62191afe88d0a36389871e3a69fc524b4bbaa`**, `docs: add C5 P/M v1.0.1 review request`.
- The request's authored-basis `7ecf973` is provenance, not the reviewed checkout. This report reviews the synchronized HEAD above.
- Candidate file content SHA-256: **`d11a234580e89b0a351f08f0d518da7dc63094437ffeddd6b02cf5016e64e1b5`**. This identifies the reviewed candidate; it is **not** a freeze approval.
- Read the complete review request and required v1.0.1 plan, golden vectors, synthesis, preflight, P0 report, runner, and metric tests. Compared the historical v1.0 plan with the candidate. Inspected the runner's Adapter/LoRA/label helpers and the existing P0 artifact's metadata for specific compatibility questions. Did not read individual earlier reviewer reports.
- Read-only, standard-library, in-memory checks reproduced the preflight content hash and all three golden digests, and enumerated only synthetic endpoint keys from the approved preflight identities. No model was loaded and no training, evaluation, unit-test suite, timing probe, or D0/D1 run was executed. No additional model or subagent was used. No external API was used for review analysis; the explicitly requested Git synchronization was the only remote operation.
- Test 163 was not opened. No P1 data was used. T5Gemma2 remains closed under D-108 STOP. The only intentional repository content write is this report.

Unless qualified, section references below refer to `docs/plan_c5_b0a_pm_prereg_v1_0_1.md` at that HEAD.

### Confirmed arithmetic and integrity

| Item | Independently checked result |
|---|---|
| Preflight content SHA-256 | `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` — matches §0.4 |
| F/L contributors and targets at 753 | 16 training contributors; 15 validation targets |
| Validation targets at 754 | 14; zero-margin warning is substantiated |
| Primary mixed endpoint domain | `(15+15+20+20) × 3 × 2 × 2 × 2 = 1,680` unique keys |
| Per-document multiplicities | 15 common documents each 96; 5 native-only documents each 48 |
| D1 phase-5 domain | `120+120+160+160 = 560` keys |
| Diagnostic domain | `15 × 5 × 2 × 2 × 2 = 600` per arm-seed; not primary M |
| State golden | `43ecb58e197d5789df0a9dbbc67beba11538b8063c3da8ac46f96e1e95d65712` — reproduced |
| Empty-state golden | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` — reproduced |
| Replay golden | `c43ea35c46c51a0e82cebe5764a989d1b67012b2690246a0f89a94dff7851667` — reproduced |

These checks establish arithmetic and canonicalization examples, not implemented Phase 6 correctness or feasibility within the compute cap. Historical “54 tests pass” is not fresh verification, and the existing metric tests are not the proposed PM test matrix.

## Ranked Must-fix before freeze

### MF-1 — Blocking: reconcile the P/PA bindings with the control state space and thresholds

Evidence: §§4.5, 5.2, 5.4, 7.5, 9.6, 13.1.

The direct bindings now imply:

```text
p_valid  = ANDn(m_pass_pos_p,  m_pass_norm_p)
pa_valid = ANDn(m_pass_pos_pa, m_pass_norm_pa)
m_valid  = ANDn(all four of those operands)
```

Under the specified false-dominant ANDn, `p_valid=true` and `pa_valid=true` imply all four operands are true, hence `m_valid=true`. In §5.4, false or NA P/PA validity exits before calibration. Therefore **`M_CONTROL_INVALID` cannot be produced by consistent measured inputs**. Its signal labels `L_SIGNAL_M_CONTROL_INVALID` and `NO_L_SIGNAL_CONTROL_INVALID` are also unreachable. This conflicts with “every label reachable” and the defined condition “P/PA valid but calibration fail.” A synthetic function test can force inconsistent aliases, but that would not establish an executable end-to-end contract.

There is also a threshold naming conflict: §4.5 requires P/PA copy contrast `>= .05`, while generic `M_PASS_POS/NORM` in §9.6 requires copy contrast `>0`. The explicit aliases bind P/PA calibration to §4.5, so the generic four-conjunct rule must be clearly limited to L, or otherwise reconciled without changing the registered numeric thresholds.

**Required repair:** state whether validity and calibration are intentionally the same tests. If so, document the unreachable statuses as reserved/remove their reachability obligation and reconcile dispatch/tests; do not fabricate an independent gate just to exercise a label. If distinct validity was intended, it needs an explicit pre-outcome definition and review. Write direct L aliases as well. Preserve all current numeric cutoffs; no result-dependent adjustment.

### MF-2 — High: choose one donor-length authority consistent with “same donors for all arms”

Evidence: §2.5.6; preflight `val_h_lengths` versus `val_native_lengths`; runner `donors_for` and `native_donors_for`.

The donor algorithm is now explicit, but “same donor set for all arms/seeds” conflicts with “donor lengths from the same cache as the real document.” EG2 lengths vary; all 20 native source lengths are 512. Using each arm's own lengths gives different donor lists.

For target `REPORT-news_r-04161-00002`, preflight-only sorting gives:

- EG2 nearest five: `04798`, `03991`, `05258`, `03271`, `01058` (all IDs have the report's `REPORT-news_r-...-00001/00002` form).
- Native nearest five: `00020`, `00430`, `01058`, `01127`, `01331`.

Thus “same” is not satisfied by the literal arm-local interpretation. This is observable from lengths alone, without evaluation.

**Required repair:** identify and pin the canonical donor length map and ordered lists shared across arms if the shared-donor policy is intended; distinguish that selection map from each arm's actual memory lengths used for crop. Explicitly say native memory is encoded under the fixed source policy and then cropped as a tensor, rather than inheriting P0's re-encode-after-token-crop behavior. Define any train-split telemetry separately from the val20 donor pool; do not create a new training-donor forward.

### MF-3 — High: make path validation compatible with actual artifacts and total over missingness

Evidence: §4.0; `reports/provenance/C5_b0a/p0_native_sanity.json`; runner `p0_sanity` payload; §§4.2–4.7.

The existing P0 artifact has `mode=p0_sanity_no_training`, `test_split_used=false`, and `source_max_length=256`, but **no `no_training` field**. The runner's P0 payload likewise does not emit that field. §4.0 requires `no_training=true`. Strict interpretation cannot return `p0_path_ok=true` for the actual historical artifact; present-but-inconsistent interpretation makes it false and §4.2 makes the assay invalid. Missing-field-as-NA still does not pass. Do not silently mutate historical evidence or treat an absent field as true.

Other gaps: P/PA step100 flags say an artifact exists and its seed is a member of the registered set, not that all three required arm-seed artifacts exist exactly once. The exact checked-artifact inventory is unspecified. `test_split_used` does not explicitly resolve a known forbidden ID plus a different missing artifact. P0/step100 unreadable artifacts and missing fields need an explicit classification, not parser-dependent behavior. `assay_path_ok` also needs known failure versus unknown input precedence.

**Required repair:** define a pinned legacy-P0 compatibility rule using verified provenance, or a separate versioned integrity attestation, without changing the P0 result. Define the inventory and per-seed aggregation, explicit missing/unreadable/malformed-field handling, and known-failure dominance. Use allowed-ID allowlists from the frozen train20/val20 preflight to reject unexpected IDs; validating leakage must not require opening the sealed test split.

### MF-4 — High: finish replay mechanics and account explicitly for primary replay time

Evidence: §§11.3–11.5, 12.1–12.2.

The new replay procedure correctly requires a fresh recomputation of the 1,680 primary keys. However, the projection currently includes **initial** M CE plus the **600-key donor diagnostic** term; it has no explicit primary-M reload/recompute term. Phase 7 is explicitly diagnostic, so it cannot silently stand for primary replay. Another primary pass costs 120/160 records per arm-seed, 560 per debug four-arm set, or 1,680 across the registered run. No timing measurement exists to justify ignoring that work. The cap arithmetic is correct, but the workload coverage is not yet auditable.

The diagnostic has a key count, but not a complete tensor recipe: what donor memory, crop, control, and real tensor correspond to each `(variant, memory_kind, donor_id)`, and what stored baseline is compared? Ordinary step0/final wrong-donor CE does not by itself provide both M-variant baselines. The general procedure mandates three-seed 1,680 coverage while D1 has one debug seed and 560 primary keys. “D1 synthetic only” is also unclear beside D1's one real update per arm.

**Required repair:** define debug and registered replay procedures separately; specify checkpoints per arm-seed, baseline records, diagnostic tensor recipe, and actual control-digest verification. Include primary replay and any required baseline/control rebuild explicitly in the eight-phase accounting or a clearly named measured subphase. Retain the 96-minute projection gate and 120-minute abort; do not relax caps to accommodate missing work. Clarify that D0/D1 “no labels” means no decision/result labels, not a ban on target tokens needed for CE.

### MF-5 — Medium: make training mode and RNG construction order normative

Evidence: §§2.2, 2.5.4, 9.2; runner `set_training_mode`; metric test `test_training_mode_is_symmetric`.

The candidate specifies base decoder eval and LoRA dropout .05, and fully specifies evaluation modes, but does not give the corresponding arm-specific training-mode table. The existing repaired runner explicitly keeps base eval while training adapter/LoRA branches and LoRA dropout. Merely calling `model.eval()` would turn the registered dropout off; `model.train()` would re-enable frozen-base stochastic layers. “Trained parameters” and “base decoder eval” alone do not determine the wrapper/dropout modes.

Likewise, `manual_seed(seed)` plus separate adapter and LoRA initialization formulas does not define whether LoRA is constructed before or after the adapter, whether RNG is reseeded between them, or whether arms begin from fresh model state. Those choices alter LoRA A and later dropout draws. This is fixable now without looking at results.

**Required repair:** copy the intended repaired mode policy into the single normative spec, including P's no-adapter case, frozen native encoder, and restoration after eval. Define fresh per-arm state, initialization/reseeding order, and parameter inventory assertions. This is a protocol-completion request, not a learning-rate, seed, or dropout-value change.

## Q1–Q13

### Q1. Self-containedness

- **Verdict: disagree.**
- **Evidence:** §2.5 is a substantive improvement: native tokenizer, prefix, lengths, built-in aligned CE, copy guard, donor averaging, and greedy generation are now written down. §§4.0 and 11.4 add real operational definitions. Nevertheless MF-1 through MF-5 leave incompatible or underdetermined implementations. In particular, donor-length selection is not unique and the existing P0 artifact cannot satisfy the new literal integrity predicate.
- **Next steps:** (1) Repair the five ranked items in the candidate itself, not by making a historical reviewer report normative. (2) Re-review the repaired text and identify the eventual freeze commit and content hash. No freeze now.

### Q2. Decision contract

- **Verdict: disagree.**
- **Evidence:** §§3.2–3.4 give executable three-valued operators and all nine L pairs. Mixed true/false is NA consensus, not ANDn; copy-only/full-only dispatch and false+NA behavior are explicit. §§4.2–4.7 and 7.2 establish F1–F11 precedence. §6 preserves the validity/control/signal triple under small N. Fixtures 16–18 are internally consistent derived cases. But MF-1 proves a structural reachability contradiction after the new bindings. The pure dispatcher is total on an abstract input domain; the specified measurement-to-dispatch pipeline does not support every claimed label.
- **Next steps:** (1) Reconcile reachable versus reserved states and assert alias consistency. (2) After freeze, cover ANDn arities 2/4/5, all L pairs, F1–F11, fixtures 16–18, and every genuinely reachable label with synthetic tests; do not force impossible aliases to claim coverage.

### Q3. Mixed M domain

- **Verdict: agree.**
- **Evidence:** §§1.2, 4.5, 5.2, 8.3, 9.1, 9.5, 9.8 consistently choose mixed targets. I independently obtained 1,680 unique full keys, multiplicities 96/48, and debug count 560. P/PA `m_valid` uses native20; L `m_pass_l` uses common15. The preflight supports 16 F/L contributors, 20 native contributors, and the exact 15/20 target cohorts. Missing native keys cannot be silently reduced to common15.
- **Next steps:** (1) Implement the exact mixed key domain only after freeze, including extra-key, missing-key, and duplicate-key rejection. (2) Correct §13.2's shorthand “target appears 96 times” to distinguish common96/native-only48; the normative §9.5 definition is already correct.

### Q4. M builder / M_NORM / endpoint / replay

- **Verdict: conditional.**
- **Evidence:** §§9.2–9.4 now specify seed-local eval/no_grad means, P identity, contributor minimum 10, same-space Frobenius scaling, and target-specific real prefixes. §5.1 rejects zero/nonfinite norms, and §9.5 requires exact mixed coverage and finite copy/full CE. §12.1 adds M tensor digest binding. The mathematical builder is adequate. Replay is improved but incomplete under MF-4; arm-specific meaning of `h_len_i` should explicitly select EG2 versus native lengths.
- **Next steps:** (1) Define and verify the concrete control tensor inventory: one M_POS_MEAN and 15 or 20 M_NORM tensors per arm-seed, with named target IDs. (2) Complete the replay baseline, restore/rebuild, digest-verification, and timing rules. (3) Test P identity, norm equality, zero/nonfinite rejection, and exact domains on synthetic tensors after freeze.

### Q5. F/L memory length scope

- **Verdict: agree.**
- **Evidence:** §§2.3, 2.5.3, and 9.8 explicitly make 753 M-only. Training uses real memory without donors, donor crop is evaluation-only, and generation covers 20 val documents with a 256-new-token cap. Preflight shows four short training documents and five short validation documents, so this separation prevents an unintended drop/pad/753 training requirement. The registered donor identity still depends on MF-2, not on changing this length policy.
- **Next steps:** (1) Add synthetic short-document cases ensuring training/generation are not rejected for length <753. (2) Assert the independent M failure at insufficient common/native coverage without replacing targets or changing K.

### Q6. P/PA

- **Verdict: conditional.**
- **Evidence:** §§4.5 and 8 fix native20 P/PA acquisition tests and direct bindings; P has no adapter, PA has a random trained adapter. PA failure deliberately vetoes joint calibration. `PA_RETENTION` is nullable descriptive telemetry, not a gate. The 512-versus-753 geometry caveat correctly prevents a clean retention claim. But the new equivalence between validity and M calibration creates MF-1, and the generic versus P/PA copy thresholds must have a unique scope.
- **Next steps:** (1) Preserve native20 and PA veto while resolving the alias/state contradiction. (2) State L's >0 and P/PA's >=.05 copy criteria with unambiguous names. (3) Test P's absence of adapter parameters and PA's adapter-plus-LoRA inventory after freeze.

### Q7. Statistics / tail

- **Verdict: conditional.**
- **Evidence:** §10 fixes document resampling, 1,000 replicates, percentile 2.5/97.5, seed 20261109, seed averaging before bootstrap, documents_positive, and signal-tail identity. §3.5 requires 2/3 registered seed means and makes a missing registered seed NA rather than 2-of-available. The absolute-share gate, .50 strict inequality, top-three tie rule, zero denominator, and n<4 behavior are stated. No threshold change is warranted by P0. Remaining reproducibility details include RNG family/percentile method, explicit three-seed averaging for tail inputs, and finite/missing-value treatment before sorting or bootstrap. The old helper uses seed 20261108 and misnames document counts as seeds_positive, so it must not be imported unchanged.
- **Next steps:** (1) Pin RNG/percentile conventions and missing/nonfinite handling in the new stats contract. (2) Test missing seed, partial endpoints, exact .50, ties, zeros, and adverse leave-top3 cases. (3) Keep all constants fixed before outcomes; any later scientific change requires a new preregistration.

### Q8. D0/D1/cap

- **Verdict: conditional.**
- **Evidence:** §11 correctly totals 12 registered units/1,200 updates; D1 adds four updates, yielding prospective 1,204 updates. Separate 15-minute D0, 20-minute D1, and 120-minute registered caps total 155 minutes. Phase 5 is 560 per four-arm debug set and phase 7 is 600 per arm-seed, or 2,400 across D1's four arms. But MF-4 prevents accepting T_proj as complete: primary replay recomputation is not explicitly included. No measured runtime currently establishes feasibility at <=96 minutes. Step0 must actually precede the update or restore the initial state, as §11.3 already notes.
- **Next steps:** (1) Repair complete phase/subphase accounting without changing caps. (2) Keep D0 zero-update and non-result, not a timing substitute. (3) Require separate D1 approval and a complete, finite, nonnegative <=96-minute projection before even seeking three-seed approval.

### Q9. Hash/golden

- **Verdict: conditional.**
- **Evidence:** The §12 state framing, empty-state hash, replay JSON, null-to-minus-one donor sorting, finite CE requirement, and exact integrity versus tolerant numeric comparison are sound. All three frozen expected digests reproduce independently. I used donor_sort only for ordering; JSON retains `donor_id:null` or an integer, as in the golden. However, the three-record replay golden does not exercise PA/P, M_NORM, all donor ordinals, or non-ASCII ordering. Control digest framing is specified but lacks a worked tensor-inventory vector, and the replay procedure must verify actual tensor bytes rather than trust a manifest string.
- **Next steps:** (1) Preserve the existing independent golden constants. (2) Add small complementary independent fixtures for donor null/0..4 ordering, P/PA M_NORM, duplicate/missing keys, and control-digest target changes after freeze. (3) Define per-arm-seed checkpoint/control digest ownership and verification; never compare debug hashes directly to registered final hashes.

### Q10. Remaining Must-fix

- **Verdict: conditional.** The repair closes important v1.0 failures, but not the claim that all must-fixes are closed.
- **Evidence:** Historical synthesis MF-1 is genuinely closed by mixed1,680/D1560; MF-3 wrong-donor meaning and MF-8 real-only training wording are closed at text level. MF-5 measurement semantics and MF-7 control digest are substantially improved. Historical MF-2 donor selection is only partial because the length authority is inconsistent; MF-4 path flags is only partial because P0 compatibility and missingness are unresolved; MF-6 replay is only partial because executable diagnostic/timing coverage remains unspecified. MF-9 bindings/3^6 are added, but direct P/PA aliases expose the reachability contradiction. Supplemental golden coverage remains a test deliverable, not a reason to discard valid existing constants.
- **Next steps:** (1) Address ranked MF-1 to MF-5 above, in that order. (2) Make only pre-outcome contract repairs, then obtain a new freeze decision; do not use P0 to tune gate values.

### Q11. Freeze and implementation approval

- **Verdict: disagree.** Not for the current bytes.
- **Evidence:** §16.1 requires no code before freeze. Freezing now would require implementers to decide donor authority, invent an unreachable-state policy, and choose replay timing scope. Existing metric tests establish intended historical invariants in source form, not the complete new implementation. The class is also guarded by local-model availability; a historical test count cannot substitute for fresh executed PM coverage.
- **Next steps:** (1) Repair and re-review text; record freeze commit and content SHA only after acceptance. (2) After authorized freeze, implementation plus model-free unit tests should precede D0: tri-state/alias consistency; all L pairs and precedence fixtures; exact 1,680/560 domains and 96/48 multiplicities; builder/norm edge cases; canonical donor lists; path missingness/legacy P0; bootstrap/tail; golden/digest/replay behavior; mode/inventory/reset checks. (3) Only then seek/perform separately authorized D0 within its existing limits. No model-forward test is proposed for this consultation.

### Q12. B0-B / D1 / three-seed boundaries

- **Verdict: agree** on the stated approval boundaries, not on feasibility or present permission to run.
- **Evidence:** §§11 and 16.3 separate D0, D1, registered runs, and downstream approval. §14's downstream predicate is conservative and does not make a positive label sufficient. Restated using v1.0.1 names:

```text
B0-B may only be considered if:
  validity_status == VALID
  AND control_status == M_CONTROL_PASS
  AND signal_status == EXPLORATORY_L_SIGNAL
  AND m_valid is true
  AND n_signal == 15
  AND tail_driven is false                 # L copy / wrong-donor signal tail
  AND leakage, mode, and metric checks pass
  AND required artifacts are complete and verified
  AND a separate B0-B preregistration and explicit approval exist.
```

`m_valid` means P/PA native20 calibration, while the L M claim is prefix753/common15. P0, full_k_secondary, and PA_RETENTION cannot substitute. Tail true or NA blocks consideration. D1's debug seed and diagnostic records are not registered seed evidence.

- **Next steps:** (1) Encode separate launch authorization checks, including no D0-to-D1 or D1-to-three-seed auto-transition. (2) Repair projection coverage before D1 approval is requested. (3) Keep B1/B2/Stage C and T5Gemma2 closed regardless of a positive exploratory label.

### Q13. Final verdict and freeze

- **Verdict: conditional. Final recommendation: NARROW.**
- **Evidence:** The core repair is promising, the cohort arithmetic is now coherent, and no trained P/PA/M outcome has been seen. That supports a narrow pre-outcome specification repair, not STOP of the scientific question. MF-1 through MF-5 prevent CONTINUE/freeze of this exact document. P0 is only path sensitivity: train +3.7617 and val +5.2375 copy contrasts with positive CIs do not establish trained-arm validity; val median 2.9739, absolute/signed top-three differences, and real CE above ln|V| reinforce the limited interpretation. P0's 256-token source policy is not the registered native512 policy.
- **Next steps:** (1) Text-only repair of the ranked blockers and re-review. (2) If accepted later, freeze one revised authority with exact commit/content hash and permit only the explicitly approved implementation/tests/D0 scope. (3) Preserve separate approvals and all sealed-data/model boundaries.

## Final scope and disposition

| Item | Recommendation for the present candidate |
|---|---|
| Final verdict | **NARROW** |
| v1.0.1 freeze | **No**, not the reviewed content hash |
| Implementation + unit tests | **Not approved now**; text repair and accepted freeze first |
| D0 | **Not approved now**; eligible for later mechanics-only approval after repair/tests |
| D1 | **Not approved**, requires separate authorization and repaired timing/replay contract |
| Registered three-seed run | **Not approved**, requires D1 evidence and separate authorization |
| Phase 6 execution | **Not approved by this review** |
| B0-B / B1 / B2 / Stage C | **Not approved**; no automatic progression |
| Test 163 | **Sealed**, not opened, not proposed for use |
| P1 / external data APIs | **No use / no proposed use** |
| T5Gemma2 | **D-108 STOP remains in force** |
| Maximum compute authorized by this consultation | **0 optimizer updates; 0 training/evaluation/D0/D1 runs** |
| Prospective D0 envelope, only if later authorized | <=4 configs, 0 updates, <=15 minutes, seed 20261111, no decision labels or timing claim |
| Prospective D1 envelope, only if separately authorized | 4 arms × one debug seed, 1 update each, <=20 minutes, no registered labels |
| Prospective registered envelope, only if separately authorized | 12 units, 1,200 updates, <=120 minutes, CPU six threads, no GPU, no retry/extension; full-workload projection <=96 minutes |
| Prospective combined envelope, not a grant | 1,204 updates / 155 minutes including D0 and D1 |
| Single implementation authority sufficient today? | **No**; the document is substantially consolidated but still contradictory/incomplete |

**Must-fix summary:** (1) P/PA alias-induced unreachable control states and threshold scope; (2) unique donor-length authority; (3) actual P0 compatibility plus total path/inventory semantics; (4) executable debug/final replay and explicit primary-replay timing; (5) normative training-mode and RNG construction policy.

**Incorrect premises to avoid:** matching record counts does not prove replay feasibility; a golden hash does not prove an implementation exists; synthetic inconsistent flags do not establish reachable measured states; absence of a test ID in output does not alone prove no forbidden data was read; historical 54-test success is not current PM verification; P0 sensitivity is not a trained positive control; positive exploratory signal is not B0-B approval. No threshold, seed, donor, update-count, or learning-rate selection after results is recommended. A later scientific change would require a new preregistration, not an outcome-conditioned erratum.
