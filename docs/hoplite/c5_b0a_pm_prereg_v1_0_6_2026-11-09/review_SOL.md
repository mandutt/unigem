# Independent external review — C5 P/M prereg v1.0.6

- Reviewer: OpenAI Sol 6.1; independent current-round review, 2026-11-09.
- Repository: mandutt/unigem, main.
- Requested synchronization: `git fetch origin`, then `git pull --ff-only origin main` both succeeded; pull reported “Already up to date.”
- Reviewed HEAD and origin/main: `e619885ce34c9f498008b00fd6d0a52e40c7316d`.
- Review basis: current checked-out normative plan, template, golden vectors, request, historical synthesis, five requested provenance JSON files, runner and metric tests. Historical synthesis was used only to identify residuals, not as proof of closure or as another model's answer.
- Consultation only. No training, model evaluation, generation, D0/D1, or metric test execution. No test-163 data, split file, model weights, or P1 data opened. The P1 usage attestations were read as requested. No subagents or additional LLMs.
- Only review_SOL.md is written; protocol, code, templates and provenance remain unchanged.

## Executive verdict

**NARROW — text/schema corrections and re-review only; do not freeze or begin implementation/D0 as-is.**

Six of eight residual categories are closed at the specification level; phase-7 prefix bounding and freeze handoff are partial. All five golden digests independently reproduce. The new equal-dimension assertion detects a mismatch but does not define bounded prefixes that avoid it. The freeze sequence is noncircular, but its normative example still names v1.0.5 while the template names v1.0.6.

This is a review recommendation, not project-owner authorization. No Phase 6/B0-B/B1/B2/Stage C approval is given. There is no trained P/PA/M result.

## Independent read-only evidence

Standard-library-only in-memory calculations read the supplied golden JSON and preflight/P0 metadata. They did not import the runner or execute model forwards.

| Check | Independently obtained value | Result |
|---|---|---|
| State framing | `43ecb58e197d5789df0a9dbbc67beba11538b8063c3da8ac46f96e1e95d65712` | Matches |
| Empty state | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | Matches |
| Sorted replay array | `c43ea35c46c51a0e82cebe5764a989d1b67012b2690246a0f89a94dff7851667` | Matches |
| Sorted key-coverage array | `8277a713fd52b2ba8c5c3c859c83fd78593aa5a381f8640448e2128a97af7a20` | Matches |
| Sorted control frames | `6b50c226ecc402323787bd25b20e57fe57376caeb925c040b57985ccc0ec1938` | Matches |
| Preflight content SHA256 | `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` | Matches |

Per-record JSON concatenation produced a different digest for both replay fixtures. The control JSON actually lists M_NORM before M_POS_MEAN.

P0 per-document arithmetic reproduces train mean copy delta +3.7617264, full +3.5027401, 14/20 positive; val copy +5.2374585, full +5.2936482, 18/20 positive, median +2.9739293. Stored copy CIs are [1.8916853, 5.6049574] and [2.5013211, 8.0752724]; CIs were read, not bootstrap-recomputed in this review. P0 source_max_length is 256. Real copy CE 12.7022/13.2352 and native-path sensitivity do not establish trained control calibration at 512.

## Q1 — Eight residual closures

**Verdict: conditional.** Not all eight are closed.

| Residual | Status | Current evidence |
|---|---|---|
| 1. §13.5 seeds_positive token | Closed | §13.5 bans legacy seeds_positive in registered stats; §13.3 still requires registered_seeds_positive. |
| 2. Array digest | Closed | §12.2 explicitly requires one sorted canonical JSON array and forbids per-record concatenation; both replay goldens reproduce. |
| 3. Phase-7 equal dimensions | Partial | §9.6.1 lines 1087–1091 adds the assertion, but leaves raw memory prefixes and an unbounded two-length minimum. |
| 4. Control golden order | Closed | §12.3 and golden JSON agree on canonical-name order; digest reproduces. |
| 5. Bootstrap RNG/percentile | Closed | §10.3 fixes fresh default_rng(20261109)/PCG64, 1,000 draws, linear percentiles. |
| 6. Freeze handoff | Partial | §16.2 provides a noncircular order, but lines 1651/1658 still name v1.0.5; template names v1.0.6. |
| 7. Postrun/P1 coverage | Closed at contract level | §1.5 requires expansion to actual files and self-listing; §4.0 makes unreadable/missing artifacts NA and known contradictions false. No postrun evidence exists yet. |
| 8. P0/schema/misc | Closed | 256 limitation in §10.4; schema_version=1 in spec/template; MARGINAL_SIGNAL_COHORT informational; array/control tests in §13.4. |

**Next steps:** (1) Resolve the two partial categories without changing scientific choices. (2) Re-review the corrected normative text and template before freeze.

## Q2 — Self-containedness

**Verdict: disagree as-is.**

§0.1 promises one implementation authority, but implementers must currently choose how to cap phase-7 prefixes and whether §16.2 or the template supplies the actual versioned freeze path. §17.1 explicitly delegates helper semantics to four source files at recorded commits; this is a declared dependency, not a need to reconstruct old r3.x protocols. Model/tokenizer/cache assets also remain external inputs.

The inspected Adapter and label/cache helpers agree with the stated geometry, same-position labels and scalar lengths. The current runner is a legacy two-arm utility, not a complete F/L/P/PA Phase 6 implementation. Its bootstrap default is 20261108 and its seeds_positive is a document count; §10.2 correctly prohibits using that helper as registered statistics. Its set_training_mode only accepts frozen/lora and assumes an adapter, so it cannot simply be applied unchanged to P.

**Next steps:** (1) Correct phase-7 and freeze authority. (2) Pin the declared helpers and implement the new four-arm orchestration against the consolidated contract, not the old runner CLI.

## Q3 — Hash contract

**Verdict: agree.**

§12.2 defines the flat eight-field hash_record, canonical JSON object keys/separators, ascending seven-part record key, internal donor_sort=-1 for null, and one array envelope. donor_sort is not serialized. All five expected digests reproduce independently; baseline_ce/delta are excluded, and numerical tolerance is distinct from exact hash integrity.

The fixtures contain ASCII identifiers; byte-level escaping/Unicode policy and document ordering should be exercised explicitly if broader identifiers are ever permitted, rather than silently assuming arbitrary JSON serializers are equivalent.

**Next steps:** (1) Implement positive fixtures and array-vs-concatenation negatives after freeze. (2) Test permutation invariance, duplicate/missing keys, flat-vs-nested shape and null-vs-donor ordering without replacing expected constants.

## Q4 — Phase 7

**Verdict: conditional; not executable unambiguously as written.**

Count and replay semantics are coherent: 15×5×2×2×2=600 records per arm-seed; memory_kind is real/donor; each variant supplies its own recomputed baseline_ce; delta=baseline_ce-ce; diagnostic_replay_ok is separate from primary replay_ok (§11.4).

However, §9.6.1 lines 1087–1091 defines prefixes as memory(doc) and K_d=min(their lengths), with no explicit K_M bound. The added bound assertion is tautological, and equal dimensions fail if both memories exceed 753.

Concrete preflight counterexample: target REPORT-news_r-00020-00001 has length 777; one of its five deterministic donors is REPORT-news_r-05258-00002, length 771. Written raw-length K_d is 771, while both M controls have 753 rows. The equality assertion fails. Using the frozen lengths and donor rule, 64/75 F/L target-donor pairs have raw minimum >753, six are <753 and five equal 753. This is metadata arithmetic, not model evaluation. If “prefix” was intended to imply truncation, that missing definition is precisely the ambiguity.

**Next steps:** (1) Explicitly define real_prefix=memory(target)[:K_M] and donor_prefix=memory(donor)[:K_M], then K_d=min(lengths), or equivalently K_d=min(K_M,len(real_memory),len(donor_memory)). Retain equal-dimension checks and K_M-scaled M_NORM without renormalization. (2) Add synthetic both-long, short-donor, boundary-753 and native-512 regressions, plus baseline/delta corruption checks. Do not drop diagnostic pairs to evade the mismatch.

## Q5 — Seeds and statistics

**Verdict: agree.**

§13.5 no longer forbids the required registered_seeds_positive field. §10.2 distinguishes document positives from registered-seed mean positives. §3.5 requires all three registered seeds 20261108/09/10 and two positive means out of those three, not two of available. §10.3 fixes document-level paired resampling after seed averaging, default_rng/PCG64 with a fresh generator and linear 2.5/97.5 percentiles. P/PA calibration's omission of L's paired-L>F and two-of-three conjuncts is explicit (§4.5), not a defect to “repair” after results.

**Next steps:** (1) Test deterministic CI behavior with a fixed retained-ID order and fresh RNG per call. (2) Test missing-seed NA, document-vs-seed counts and intentional L/P/PA asymmetry.

## Q6 — Control golden

**Verdict: agree.**

The actual golden JSON is ordered M_NORM then M_POS_MEAN. Canonical-name-sorted tensor frames reproduce 6b50c226… . The synthetic [1,1] tensors test framing only; real [K_M,512] tensors, per-target normalization, NPZ key tensor and postrun control_digest are separate (§12.1–12.3). No trained control result is implied.

**Next steps:** (1) Preserve the synthetic expected constant and test input-order invariance. (2) Test real geometry, frame-vs-NPZ-byte hashes and nonfinite/zero norms in implementation tests.

## Q7 — Freeze chain

**Verdict: conditional.**

The proposed order is noncircular: commit final plan/helper bytes; populate manifest with plan content hash and freeze_commit; commit manifest; D0 records its content SHA256. The manifest need not be included in freeze_commit. schema_version, helper_commits, registered_seeds, P1/golden/preflight bindings are present.

But normative §16.2 says docs/plan_c5_b0a_pm_prereg_v1_0_5_FREEZE.json and plan_path=docs/plan_c5_b0a_pm_prereg_v1_0_5.md. The v1.0.6 template correctly uses v1.0.6. No actual v1.0.6 freeze manifest is tracked; this is appropriate before approval, not itself evidence of a failed freeze.

**Next steps:** (1) Correct both normative paths and enforce equality with the v1.0.6 template. (2) After final text review, validate non-null hashes and helper revisions against freeze_commit, create the manifest separately, and bind D0 to its SHA256. Do not freeze the wrong plan merely because its hash is valid.

## Q8 — P1/postrun

**Verdict: conditional; contract improved, execution unproven.**

§1.5 requires actual-file expansion and postrun self-listing, separates the frozen attestation from mutable audit inventory, and makes any known P1/test-use contradiction false. §4.0 distinguishes missing/unreadable NA from known false. The actual frozen attestation declares both flags false with empty inventory; postrun status=not_run is a placeholder, not successful coverage proof.

The registry uses brace placeholders ({arm}/{seed}/{target_id}), not literal shell-glob syntax. An implementation must instantiate expected domains first and then check existence, not count only whatever files happen to match. The expected registry families do not eliminate the separate requirement to inventory every Phase 6 artifact inspected, including persisted primary/signal reports when created. Hash-matching an empty frozen inventory is not postrun non-access proof.

**Next steps:** (1) Test missing expected units, malformed flags, placeholder/not_run inventory, self-listing and true contradictions even when another artifact is missing. (2) Require expected-domain completeness and artifact-complete evidence before any downstream gate; never scan sealed test IDs.

## Q9 — D0/D1/cap

**Verdict: agree on accounting; conditional on mechanics and separate approvals.**

D0: at most four configs, one per arm, debug seed 20261111, zero optimizer updates, ≤15 minutes, no decision labels/projection. D1: four arms×one debug seed×one update=4 updates, ≤20 minutes, target-token labels allowed but no decision/signal labels. Step0 must precede the update or use restored initial state.

Primary CE counts are F/L 120 per arm-seed and P/PA 160: D1 total 560, registered total 1,680, distributed F=360/L=360/P=480/PA=480. Diagnostic 600 is per arm-seed, not a four-arm total (D1 2,400; registered 7,200). The eight measured phases and explicit primary replay term in T_proj must all be accounted for without substituting D0 timing. T_proj must be finite, nonnegative and ≤96 minutes; registered hard abort is 120 minutes. Future combined ceiling is 1,204 updates/155 minutes, not a current grant.

**Next steps:** (1) Repair phase-7 mechanics before any D0. (2) Require separate D1 approval and complete timing evidence before separately considering three-seed approval.

## Q10 — Remaining must-fix

**Verdict: disagree with “all residuals closed.”**

Ranked blockers:

1. **MF-1: Define K_M-bounded phase-7 prefixes (§9.6.1, lines 1087–1091).** Adding an assertion alone exposes, rather than resolves, the existing undefined prefix scope. The frozen preflight provides concrete failures. Preserve all 600 keys and no-renormalization semantics.
2. **MF-2: Correct v1.0.5 freeze/plan paths (§16.2, lines 1651/1658).** They contradict this plan's authority and the v1.0.6 template. Otherwise an implementer can faithfully hash and freeze the superseded plan.

Golden array bytes and control ordering are not remaining blockers. Postrun coverage/domain expansion and deterministic stats ordering are implementation acceptance requirements, not evidence that postrun already passed.

**Next steps:** (1) Make only these narrowly scoped normative corrections in an authorized follow-up. (2) Re-review the corrected diff and prepare the noncircular freeze handoff; change no thresholds, donors, seeds, update count or LR.

## Q11 — Freeze, implementation, tests, D0

**Verdict: conditional; withheld as-is.**

§16.1 says no code before freeze. The two normative blockers therefore prevent an unconditional implementation/unit-test/D0 recommendation. The existing metric tests cover alignment, mask, telemetry, mode symmetry, donors and descriptive P0 only; they are not Phase 6 DoD proof, and this review did not execute them because several load a model and perform forwards.

Before implementation, agree the following test contract; implement and pass it after valid freeze and before D0:

- Pure decision/tri-state axes, F1–F11, nine L pairs, fixtures 16–18, every label, small-N triple, no input mutation.
- Mixed-domain 1,680 exact keys, F/L 15 and P/PA 20, correct 96/48 per-target multiplicity; missing/duplicate/native-only failures; builder/zero-margin/finite-norm checks.
- Both-long and short-donor phase-7 slicing with all four tensors equal length; no renormalization; 600 keys; independent diagnostic baseline/delta replay.
- All five goldens, negative concatenation/nested records, checkpoint map 12 units and 120/160 per-unit numeric replay; debug/final separation.
- Three-seed averaging, missing-seed NA, document/registered positives, deterministic PCG64/linear CI, tail/tie rules.
- P/PA parameter/mode/init-order assertions, strict P1 inventories and contradiction precedence, correct-version freeze binding, D0 zero-update/cap/no-label guards.

**Next steps:** (1) Close MF-1/2 and complete explicit freeze review. (2) Then request implementation/tests approval followed by D0 authorization; this consultation performs neither.

## Q12 — Downstream boundaries

**Verdict: agree on boundaries; execution deferred.**

The v1.0.6 B0-B predicate (§14) is:

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS
AND signal_status == EXPLORATORY_L_SIGNAL
AND m_valid == true
AND n_signal == 15
AND tail_driven == false
AND leakage/mode/metric pass
AND artifact complete
AND separate B0-B preregistration/approval
```

n_signal>=15 means exactly 15 in this contract. Signal-tail true/NA blocks. P0, full_k_secondary, PA_RETENTION and EXPLORATORY_L_SIGNAL alone do not authorize B0-B. M scope is M_CONTROL_PREFIX753_COHORT15, not all val20 or a general retention result. D1 and three-seed runs each require their own approvals. B1/B2/Stage C remain unapproved.

**Next steps:** (1) Preserve this predicate and explicit approval ledger. (2) Assess any future downstream proposal only against completed frozen-run artifacts and a new authorized preregistration, never post-result threshold changes.

## Q13 — Final scope and freeze decision

**Verdict: conditional. Final recommendation: NARROW.**

| Scope | Recommendation now |
|---|---|
| v1.0.6 freeze | Withheld until MF-1/2 corrected and re-reviewed |
| Implementation + unit tests | Withheld as-is; follow valid freeze and explicit authorization |
| D0 | Withheld as-is; later ≤4 configs, 0 updates, ≤15 min, seed 20261111 |
| D1 | Not approved; separate ≤4 updates/≤20 min approval |
| Three-seed registered run | Not approved; future 1,200 updates/≤120 min, T_proj≤96 prerequisite |
| B0-B/B1/B2/Stage C | Not approved |
| test 163 | Sealed; no access |
| P1 | No use; attestations are not proof of non-access |
| T5Gemma2 | D-108 STOP unchanged |
| Current experimental compute authorization | Zero updates and zero model forwards in this consultation |
| Prospective combined maximum | 1,204 updates/155 min, only across separately approved stages; no retry/extension |
| Single implementation authority | Not sufficient as-is; two contradictions/ambiguities remain, plus explicitly pinned helpers |

**Next steps:** (1) Authorized text/schema-only correction and re-review. (2) Only then establish the actual freeze chain and separately authorize implementation/tests/D0. No scientific choice is reopened.

Incorrect premises to avoid: the presence of equal-dimension assertions does not make phase 7 executable; a correct v1.0.6 template does not override stale normative v1.0.5 paths by itself; passing synthetic goldens is not trained M evidence; empty/not_run P1 manifests do not prove completed audit coverage.

**STOP/NARROW/CONTINUE: NARROW.**