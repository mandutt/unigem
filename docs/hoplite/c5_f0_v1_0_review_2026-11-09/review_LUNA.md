# C5 F0 v1.0 — Final Independent Review (Luna)

- Review date: 2026-11-10
- Reviewed HEAD: `80a723f83b2e559ebc1f64bc7bff12d7ed582d48`
- Synchronization: `git fetch origin` and `git pull --ff-only origin main` both succeeded; pull reported `Already up to date.`
- Scope: document/code review only. No training, evaluation, test-163/P1 access, or experiment execution.
- F0 status in the reviewed plan: **DRAFT, unapproved, unrun** (`docs/plan_c5_f0_v1_0_2026-11-09.md` §§0,18).

## Verbatim paired E01−E11 preregistration

The registered paired estimand is:

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
```

The seed gate is specified verbatim as: “`D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary.” (`plan_c5_f0_v1_0`, §6.3, lines 207–215.) The positive rule is `mean_D > 0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0` (§6.3, line 212). These are **planned estimands and gates, not observed results**: no paired E01/E11 mean, CI, or seed signs exist because F0 is unrun.

## Q1. Initialization — **Conditional**

The design is materially stronger than an informal “same seed” claim: §4 (lines 81–114) uses a dedicated F0 builder, resets the LoRA seed independently of adapter construction (`0x5EED10A5`), reseeds every forward with `0x9E3779B9`, requires 64 matching LoRA module names, compares E01/E11 LoRA A/B initialization hashes and RNG-state hashes, compares E10/E11 adapter hashes, and records base/cache/label hashes. That is a sound contract in principle: it does not reuse Phase 6 `build_arm`, and explicitly says F0 E11 is not Phase 6 L at initialization (§4, line 111).

The normative body does not, however, complete several audit requirements claimed in the v1.0 change summary (§0, lines 32–34): it gives a canonical *record digest* rule (§4, line 110), but not a canonical tensor-byte encoding (key ordering, dtype, shape encoding, byte order/device transfer and contiguous layout); no step-seed golden input/output table is present; and no post-step0 **weight non-equality** assertion is present. Equal post-step0 RNG-state hashes alone do not prove that the trained E01/E11 weights diverged as expected. The promised freeze hashes likewise need a pinned input/manifest interpretation, not only “recorded and equal across cells.”

**Next step:** put the serialization contract and explicit golden vectors/assertions in the normative spec or an attached, frozen implementation DoD before D0 approval; keep the registered seeds and training settings unchanged.

## Q2. D1 seal — **Disagree (approval blocker)**

The intended policy is correct (§5, lines 155–165): do not materialize or persist D1 signal, keep one mechanics artifact, forbid checkpoint loading, and reject signal-bearing input. The executable contract is incomplete and internally inconsistent:

1. The plan says three trained checkpoints “exist” (§5, line 151), but then says their files are discarded and only digests remain (§5, lines 160–162). It must define whether D1 ever serializes a checkpoint, exactly when its digest is made, and assert that no checkpoint file remains or can be loaded. §13 lists a generic `checkpoints/{cell}/{seed}.pt` artifact path (lines 367–384) without limiting it to Stage R.
2. “Exact-key allowlist” is named but the permitted key inventory and value types are not actually enumerated in §5 (lines 155–163). The listed negative test only names `d1_report.json`, `per_doc`, and `delta_*`; it does not specify rejection of arbitrary unknown keys, forbidden nested keys, alternate paths, or writer-side failures. The change summary’s “writer-side key/dir asserts; phase7 filesystem assert” (§0, line 29) is not expanded into testable requirements in the body.
3. The current Phase 6 runner is **not** a safe implementation template for this F0 D1 contract. In `runner/c5_pm_phase6.py`, `save_d1_checkpoint()` writes a persistent checkpoint (lines 765–775); `run_d1()` writes phase7 records and checkpoints and includes `step0`/`final` in its output (lines 813–835, 850–882). Those behaviors violate F0 §5’s no-phase7/no-final/digest-only contract. F0 §11 correctly calls for new F0 entrypoints (lines 333–342), but must explicitly prohibit reusing the Phase 6 D1 writer/save path and require tests proving the filesystem remains clean.

This is also the unresolved detail behind the v0.8/v0.9 review history: the earlier syntheses report a schema/path fix, but independently checking v1.0, the promised literal schema is still absent from the normative section. **Do not approve D1** until the exact schema, writer/reader restrictions, checkpoint lifecycle and negative/invariance tests are specified and implemented.

## Q3. STOP/MDE — **Conditional**

The decision partition is coherent as written (§7, lines 249–298). `PASS_POSITIVE` requires `CI_D.lower > +.05`; `EQUIVALENT` requires the full CI within `[-.05,+.05]`, so those labels cannot overlap. With `PROTOCOL_VALID`, the ordered rules yield PASS, otherwise ROUTE_STOP exactly when all four E01/E11 × copy/full signals fail, otherwise INDETERMINATE; invalid protocol is NOT_EVALUABLE. `ALL_FAIL` excludes E00/E10, and the fallback `no_signal_uncertain` covers the remaining ALL_FAIL case. No automatic H3 transition is implied.

The MDE caveat is directionally responsible: §12 (line 359) says `.05` is not a powered effect threshold and requires the realized `CI_D` half-width. But the stated `.166`/`.216` “50%/80% power” approximations cannot be reconstructed from a single-arm Phase 6 L half-width of about `.117` without a paired-contrast variance/covariance assumption. For example, a simple independent, equal-variance normal approximation gives about `.166` at 50% and `.237` at 80%; the actual paired design may differ. The plan must state the calculation and assumptions or mark these as rough, non-inferential heuristics—not present `.216` as a reproducible 80% MDE.

**Next step:** preserve the `.05` gate and all frozen settings; document the paired MDE calculation (or withdraw the unsupported power label) and report realized CI width as already required.

## Q4. Cohort/CI — **Agree, bounded to the frozen cohort**

The primary is correctly paired at the document level: §6.1–6.3 fixes 15 `common_ids`, requires all 3 seeds and exactly 5 identical donors per document across all four cells, averages donor contrasts within document and seeds within document, then bootstraps the 15 paired `D(d)` values with explicit `n_boot=10000` (§6.2–6.3, lines 181–215). It does not treat 75 donor comparisons as independent units. Missing docs/endpoints make the result NOT_EVALUABLE rather than shrinking the cohort (§6.6, lines 242–247); the 2/3 seed-sign condition is a replication descriptor/gate, not a second CI.

This supports a bounded claim about the frozen 15-document cohort, not population-wide equality or broad EG2 generalization. The plan’s “exploratory/bounded” limitation is necessary given n=15 and the MDE caveat. Keep the fixed cohort, donor rule and 10,000 bootstrap override; do not substitute missing documents.

## Q5. Compute — **Conditional**

The arithmetic is internally consistent: D1 has 3 trained updates and a 25-minute cap; R has 3 trained cells × 100 updates × 3 seeds = **900 updates**, 12 logical threads, and a **96-minute** cap (§5, lines 138–175; §12, lines 344–360). The projection includes setup, step-0 evaluation, 100 training steps, M build/CE, phase-7 replay, primary replay, generation and overhead, with three sequential seed waves and a hard abort for `nproc < 12` or `T_proj_R > 96 min` (§12, lines 353–359). The documented Phase 6 D1 wall time, **1,180.6 s** (about **19.7 min**), is context only, not an F0 parallel-run measurement.

F0 code is explicitly not implemented (§11, lines 333–342), so neither the 12-way orchestration nor the 96-minute projection is yet demonstrated. In particular, §12 calls the R-only replay terms “included analytically,” while F0 D1 explicitly must not run phase7; the source and method for those estimated terms are not defined. The existing Phase 6 `run_d1()` also loops arms serially and sets six Torch threads (runner lines 778–795), so it cannot substantiate F0’s required four-arm/three-thread parallel wall time.

**Next step:** before R approval, require an F0-specific orchestration result recording actual usable `nproc`, per-arm/per-phase timing, parallel wall time and the calculation/source for both R-only replay terms. Keep the stated caps and abort conditions; do not treat the historical Phase 6 timing as F0 proof.

## Q6. Scope — **Agree**

The scope is appropriately narrowed to one registered E01–E11 contrast; E00/E10 are descriptive, and the claim is explicitly association-only rather than an architecture-only bottleneck claim (§0, lines 19–22; §§2, 8). H3, its triggers and automatic follow-on are explicitly excluded (§10, lines 325–331); the lost MF-4 null/one-seed gate is disclosed as out of scope (§0, lines 38–39; §14, lines 395–397). The report must not claim that F0 establishes adapter mechanism, repairs B0-B, or generalizes the native P/PA finding to EG2.

That boundary matches the source evidence: the Phase 6 cause report gives native-path `P` copy Δ **3.076** versus `PA` **0.011** and a **14/15** positive P-vs-PA paired contrast (§2, lines 53–60), while L’s copy signal was false at mean Δ **−0.1135**, CI **[−0.2341, −0.0012]**, with **6/15** positive documents and **0/3** positive seed means (§1, lines 12–27). The cause report expressly says EG2/F-L generalization and structural mechanism are unestablished (§5, lines 101–110). These are rationale for the narrow diagnostic, not evidence of an E01/E11 outcome.

## Final verdict: **NARROW**

Do **not** approve F0 execution from this draft. The single-contrast design, cohort, decision taxonomy and scope are generally sound, but the D1 artifact contract and initialization audit are not sufficiently executable, and the MDE/compute claims need reproducible derivations. This is a final-round NARROW disposition, not a request for another review round: close the ranked specification/implementation gaps through a versioned clarification and acceptance tests before seeking any separate D0, D1 or R stage approval. This review authorizes no stage.

### Must-fix (ranked)

1. **D1 oracle/artifact control:** enumerate the exact allowed `d1_mechanics.json` keys/types and all forbidden paths/keys; reconcile “three checkpoints exist” with digest-only discard; test that no signal, checkpoint, `final`, or phase7 artifact persists; add writer-side assertions and negative/invariance coverage. Ensure F0 does not reuse the conflicting Phase 6 D1 writer/checkpoint path.
2. **Initialization reproducibility:** specify canonical tensor serialization and pinned dtype/shape/byte representation; add explicit `step_seed` golden vectors; implement the promised post-step0 weight non-equality assertion and bind base/cache/label hashes to frozen inputs.
3. **MDE provenance:** give the paired-contrast variance/covariance and power calculation that yields `.166/.216`, or label those values only as unverified heuristics. Keep the realized `CI_D` half-width and do not change the `.05` gate.
4. **Compute projection provenance:** specify how D1 supplies or estimates the R-only primary/phase7 replay terms, then demonstrate the F0 12-thread orchestration and cap accounting before R approval.

No requested seed, donor, cohort, step, LR or threshold change is warranted by this review.