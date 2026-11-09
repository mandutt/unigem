# C5 P/M v1.0.8 — Sol same-thread closure review

Date: 2026-11-09. Reviewer: Sol 6.1. Same consultation thread as the v1.0.7 review; no additional LLMs or subagents.

## Review identity, scope, and access

**Reviewed HEAD: `38a2a81`**, full SHA `38a2a813978bd9688992fb5425b468fd47f6ca69`.

Mandatory verbatim quote, as requested:

```text
manifest_commit is always null inside _FREEZE.json.
```

The corresponding literal clause in §16.2 is:

> `manifest_commit` is always `null` inside `_FREEZE.json`; a file cannot contain the SHA of the commit that adds it.

Synchronization/access qualification:

- `git fetch origin` succeeded. The subsequent `git pull --ff-only origin main` failed because the remote now tracks the still-untracked local v1.0.7 `review_SOL.md`: Git reported that this file would be overwritten by merge and aborted.
- I did **not** remove, move, overwrite, stage, or commit that prior report. Local checkout HEAD consequently remains `a826308f64301179cb54c7a87a208bf3f1bc6af4`.
- Fetched `origin/main` is `d4e9dfaefa0e25696864bd2623a57283d7f7d3aa`, which adds the v1.0.8 request/dispatch material after protocol commit `38a2a81`. I read the new request from that fetched revision and the four requested review sources directly from Git objects at `38a2a81`.
- Exact byte comparisons confirmed that the v1.0.8 plan, template, golden JSON, and v1.0.7 synthesis at `38a2a81` are unchanged at fetched `origin/main`. Thus the blocked local pull does not prevent inspecting the requested protocol revision; this report does not misstate it as local checkout HEAD.
- Read the new request, the v1.0.8 document, its template/golden JSON, and the requested v1.0.7 synthesis. A focused version diff identified the changed clauses. Already-closed v1.0.7 mechanics were not re-reviewed; the golden payload comparison found only its version label changed, and the five digest calculations were **not rerun**.
- No training, evaluation, model import/forward, generation, D0, D1, test-163 access, or P1 use occurred. No underlying data, old runner/helper source, or other models' individual reports were opened for this follow-up. Only this new report was written.

## Summary

**Final recommendation: CONTINUE**, limited to **freeze → implementation + unit tests → gated D0 zero-update mechanics**. All seven requested residuals are closed as **protocol requirements**. Legacy-bootstrap exclusion and paired L>F still need implementation evidence; specification closure is not a claim that future code or tests already pass.

No remaining pre-freeze Must-fix was demonstrated within this narrowly defined follow-up. No D1, registered three-seed execution, B0-B/B1/B2/Stage C, P1/test-163 use, or T5Gemma2 reopening is approved by this recommendation. The current task remains consultation only; no experimental execution is authorized or performed here.

| Question | Verdict | Closure conclusion |
|---|---|---|
| Q1 — Seven residuals | agree | All seven closed at specification level; implementation proof remains required. |
| Q2 — Freeze chain | agree | Null in manifest, actual SHA externally, and later D0 binding remove the circular identity. |
| Q3 — Legacy bootstrap | conditional | Transitive exclusion is now required, including evaluate_arm reuse; source/call-graph tests must demonstrate it. |
| Q4 — Paired L>F | agree | Fifteen common IDs, matched axes/seeds, seed-averaged per-document contrast, missing→NA. |
| Q5 — Cap/labels | agree | Registered 120 minutes is distinct from the prospective aggregate 155-minute envelope. |
| Q6 — P0 tail | agree | Derived-not-stored/descriptive attribution closes the provenance-label issue. |
| Q7 — §4.6 | agree | Corrected p_step NA + p_valid=NA matches F9 and assay-tier precedence. |
| Q8 — Self-containedness | conditional | Adequate consolidated implementation authority with explicit frozen dependencies, not a dependency-free document. |
| Q9 — Final/freeze | agree | CONTINUE only through the bounded freeze/test/D0 sequence. |

## Q1. Closure of the seven residuals

**Verdict: agree — seven protocol closures, not seven executed implementation tests.**

| Residual | Status | Evidence |
|---|---|---|
| manifest_commit self-reference | closed | §16.2 schema and template retain null; actual manifest-containing SHA is written afterward to a separate provenance file. |
| Legacy bootstrap reachability | closed as a contract | New §17.3 names the only entrypoint, requires v2 statistics, requires replacing the bootstrap inside reused evaluate_arm, demands a source/call-graph assertion, and disallows a monkeypatch-only workaround. |
| Paired L>F | closed | §3.5 fixes cohort, matching axes/seed, per-doc difference, seed averaging, and missing-pair NA/no 15→14. |
| Template note | closed | §16.2 explicitly allows an optional note string in a frozen manifest. |
| Cap 120 versus 155 | closed | §11.6 labels 120 as registered-only and 155 as D0 15 + D1 20 + registered 120, not one run's cap. |
| P0 tail provenance | closed | §10.4 explicitly labels .4862/.43355/.455 as derived from the P0 JSON, not stored fields, descriptive only. |
| §4.6 p_valid=NA | closed | The changed bullet uses p_step NA + p_valid=NA and matches §7.2 F9. |

**Next steps:**
1. Freeze using the corrected v1.0.8 lifecycle, with actual content hashes and helper references populated.
2. Turn the new reachability, pairing, identity, and cap requirements into acceptance tests before D0; do not reopen already-closed scientific mechanics.

## Q2. Is the freeze chain noncircular?

**Verdict: agree.** §16.2 now provides an implementable temporal chain:

```text
C_plan = final normative plan/helper-source commit
M = _FREEZE.json with freeze_commit=C_plan and manifest_commit=null
C_manifest = commit containing M
external freeze_manifest_commit.txt = C_manifest, written afterward
D0 provenance = C_manifest + SHA256(M)
```

The earlier defect is removed: M never needs to contain C_manifest. Committing the external text file later does not change the identity of the earlier manifest commit; the external file points backward, not to its own containing commit. D0 also points backward to already-existing bytes/identity. `freeze_commit` remains explicitly the final plan commit, distinct from the manifest commit. The template keeps `manifest_commit:null`, its plan_path names v1_0_8, and the optional note permission resolves the template's extra key.

The external text file stores the commit SHA, not the manifest content hash. D0 must calculate `freeze_manifest_sha256` over the manifest bytes and record the actual commit identity obtained from the text file; those two fields are not interchangeable.

**Next steps:**
1. At freeze, follow the specified order and leave manifest_commit null permanently inside M.
2. Before D0, validate that the external SHA resolves to the commit containing the exact reviewed frozen-manifest bytes, and bind those bytes by SHA-256 in D0 provenance.

## Q3. Does §17.3 close transitive legacy-bootstrap reachability?

**Verdict: conditional — yes as an implementation contract; runtime/source compliance is not yet demonstrated.**

The new sole entrypoint is `runner/c5_pm_phase6.py`. Its prescribed statistics target is `c5_pm_stats.bootstrap_paired_v2`. Crucially, §17.3 no longer stops at banning a direct import: if `c5_mt5_lora_b0.evaluate_arm` is reused, its bootstrap call **must be replaced** by v2, and a source/call-graph assertion must exclude `bootstrap_paired(` from the Phase-6 path. A monkeypatch-only workaround is expressly prohibited.

This also governs evaluate_arm when reached indirectly through train_arm. A direct-entrypoint grep alone is not compliance: the assertion must cover reachable helper bodies, aliases/module-qualified calls, and nested evaluation paths. Unrelated historical P0 code may retain legacy behavior, provided it is unreachable from the Phase-6 path. No historical statistics rewrite is required.

§10.2's generic bootstrap contract remains seed 20261109 with the §10.3 algorithm. §17.3 supplies the concrete Phase-6 callable name `bootstrap_paired_v2`; the generic notation is not permission to call the prohibited legacy symbol. Naming v2 alone also cannot substitute for behavioral statistical tests.

This is a preregistration review, not an implementation review. I did not inspect or execute newly implemented entrypoint code and do not claim the call-graph test already exists or passes. That is an acceptance gate, not a reason to reject a now-explicit prospective contract.

**Next steps:**
1. Implement the sole entrypoint and make every reachable evaluation/statistics path use v2 structurally, including train_arm→evaluate_arm.
2. Before D0, pass the source/call-graph exclusion assertion and the predeclared pure/synthetic statistics tests; fail if legacy is reachable through an alias or wrapper.

## Q4. Is paired L>F operationally defined?

**Verdict: agree.** §3.5 now defines the pairing that was previously implicit:

- Exactly the 15 common target IDs.
- Same endpoint, variant, memory_kind, and registered seed on the F/L sides.
- Contrast for each document/seed is delta_L(doc) − delta_F(doc).
- Average those paired contrasts over registered seeds before document-level bootstrap.
- Any missing pair produces NA; no silent reduction to 14 documents and no missing-seed pooling.

In the signal predicate, delta is the already-defined wrong-donor minus real CE at the corresponding copy/full endpoint (§3.5); it is not a raw L-minus-F CE comparison or an M-control contrast. For the signal path, variant is not an M variant (the signal's NA convention remains explicit in §10.4). Matching metadata means matching the same measurement path, not selecting an M_NORM/M_POS_MEAN endpoint for L_SIGNAL. The existing conjunct is **paired mean >0**; the mention of bootstrap does not add a new paired-CI pass threshold.

An implementation can join by document and measurement axes, form one paired contrast per seed/document, require all registered pairs, then seed-average to one number per document. Nothing here requires a new scientific choice.

**Next steps:**
1. Add synthetic row-order/axis-mismatch and missing-document/seed fixtures; joins must use identities, not row positions.
2. Verify difference direction, seed-average-before-bootstrap, and NA propagation; do not add a new CI threshold to the paired-mean conjunct.

## Q5. Are registered 120 minutes and aggregate 155 minutes unambiguous?

**Verdict: agree.** New §11.6 wording explicitly separates:

| Stage | Maximum updates | Maximum wall time | Status |
|---|---:|---:|---|
| D0 | 0 | 15 min | Subsequent mechanics stage only |
| D1 | 4 total | 20 min | Separate approval |
| Registered Phase 6 | 1,200 | 120 min hard abort | Separate approval, complete D1 and T_proj≤96 required |
| Prospective aggregate | 1,204 | 155 min | Sum of separate ceilings; not a grant or single-run limit |

The 155-minute envelope does not permit a registered run to continue past minute 120, borrow unused debug time, retry, or extend. This patch changes labels/clarity, not the established budgets. The decision/signal-label prohibition during debugging remains distinct from target-token labels used for CE in D1; no debug output becomes a scientific result by relabeling its cap.

**Next steps:**
1. Use separate per-stage counters/timeouts and stage authorization checks; never implement one 155-minute registered timeout.
2. Test that leftover D0/D1 budget cannot extend registered execution, and retain no-retry/no-extension behavior.

## Q6. Is derived-not-stored sufficient for the P0 tail provenance issue?

**Verdict: agree for the scoped attribution fix.** The added §10.4 sentence states that .4862/.43355/.455 are **derived from p0_native_sanity.json**, **not stored fields**, and **descriptive only**. Nearby text distinguishes signed share .4862, absolute share .43355 on val20, and absolute share .455 on the 15 common documents. That resolves the mistaken implication that these were literal JSON fields.

This round did not reopen the P0 artifact or recompute these numbers; acceptance here concerns the corrected provenance claim, not a new independent numerical certification. P0 remains historical sensitivity at source_max_length=256, not trained P/PA/L calibration at 512. Its tails cannot satisfy a future registered L-signal tail gate or justify a post-result threshold adjustment. A separate derived artifact is not necessary to close this descriptive wording issue.

**Next steps:**
1. Retain the derived/descriptive and cohort labels whenever quoting these values.
2. If a later authorized audit recomputes them, preserve input IDs and the existing formula/tie rule; do not promote the historical P0 values to registered gate evidence.

## Q7. Does §4.6 now match F9? Any remaining unreachable example?

**Verdict: agree on the changed clause and its intended precedence.** §4.6 now says `p_step NA + p_valid=NA` → NOT_ASSESSABLE. This is exactly §7.2 F9, consistent with missing P-path evidence yielding an unknown P_VALID and §4.3 handling assay-tier NA before §4.4's P/PA tier.

As elsewhere in the fixture table, this expected result assumes no earlier known assay failure; §4.2 still makes a known failure dominate an NA. The repair must not be implemented as an unconditional rule that overrides a separate false path flag.

No additional contradictory/unreachable example requiring a text fix was identified in the scoped §4.6 check. In particular, `pa_path NA + p_valid=false` concerns different arms and can express a known P failure despite unknown PA-path evidence. `pa_path NA + pa_valid=false` is still useful as a defensive precedence input: §4.5 permits known nonfinite tensor evidence to force false, while §4.4 checks the unknown PA path first once earlier tiers pass. A pure dispatch fixture need not imply that every flag combination comes from missingness alone. I have not reopened the full already-closed truth-table review.

**Next steps:**
1. Keep F9 as a regression fixture for the corrected input.
2. Test the fixture with otherwise passing paths, and retain known-failure-first tests separately; do not weaken false-over-NA precedence.

## Q8. Is v1.0.8 a sufficient single implementation authority?

**Verdict: conditional — yes for a consolidated, explicitly artifact-bound protocol, not a standalone dependency-free file.** The seven scoped gaps no longer require an implementer to choose a freeze identity scheme, guess whether transitive bootstrap reuse is legal, infer the L/F pairing population, or reinterpret cap/provenance labels.

The remaining external references are intentional: §17.1's helper sources pinned at freeze_commit, the frozen preflight, golden vectors, and provenance/attestation artifacts. Historical preregistrations and other reviewers' answers are not additional normative authorities. The newly named `c5_pm_phase6.py` and `c5_pm_stats.bootstrap_paired_v2` are implementation obligations, not assumed existing evidence.

The template is still a template: status must become frozen and required binding hashes/revisions must be populated. Its note is allowed; its null **manifest_commit must stay null**, unlike the other placeholders. Golden vectors were read as requested and their payloads are unchanged apart from the spec version label. Previously closed golden algorithms, counts, and phase-7 mechanics are carried forward without re-review.

**Next steps:**
1. Populate and commit a valid freeze manifest against the final plan/helper sources, then record the external manifest SHA as specified.
2. Implement only against v1.0.8 plus numbered ERRATA and its pinned dependencies; require the existing acceptance suite plus the new closure tests before D0.

## Q9. Final verdict and bounded next-stage recommendation

**Verdict: agree. Final recommendation: CONTINUE.** The v1.0.7 freeze blocker is removed and the other six requested closure clauses are sufficiently explicit. No further pre-freeze text/schema Must-fix was established in this scope. Implementation evidence remains a mandatory next-stage gate, not a retroactive assertion of completed work.

**Next steps:**
1. Complete the acyclic freeze sequence and validate the external manifest identity/content binding.
2. Implement and pass the predeclared unit/synthetic tests, including transitive legacy exclusion, paired-axis/missingness cases, cap separation, and corrected F9.
3. Only after those gates proceed to the bounded D0 mechanics stage through the project's approval process; stop before D1 or registered execution without their separate approvals.

## Final STOP / NARROW / CONTINUE block

```text
Final verdict: CONTINUE (protocol-readiness recommendation; consultation only).
v1.0.8 freeze: Recommend proceeding with the specified null/external identity chain.
Implementation + unit tests: Recommend proceeding after valid freeze; no edits/execution here.
D0: Recommend gated zero-update mechanics after implementation/tests pass:
    at most 4 configs, one per arm; seed 20261111; <=15 minutes;
    no decision/signal labels, no scientific result, no timing projection.
D1: NOT APPROVED; separate authorization, <=4 total updates / 20 minutes.
3-seed: NOT APPROVED; separate authorization after complete D1 and T_proj<=96;
        prospective 1,200 updates / 120-minute hard abort.
Forbidden: P1 use; opening test 163; T5Gemma2 reopening (D-108 STOP);
           B0-B/B1/B2/Stage C automatic advancement;
           post-result changes to thresholds/seeds/donors/steps/LR;
           retry/extension or borrowing aggregate time for the registered run.
Maximum compute now: No experimental execution in this consultation; 0 optimizer updates.
Prospective maximum: D0 0/15 + separately approved D1 4/20 + registered 1200/120
                     = 1,204 updates / 155 minutes, not a blanket grant.
                     Registered settings remain 6 threads, CPU only, no GPU, no retry.
Must-fix (ranked): None remaining before freeze within the seven scoped items.
                  Before D0: implementation/test evidence for the stated contracts is mandatory.
v1.0.8 self-contained: Sufficient consolidated normative contract with explicit frozen
                      artifact/helper dependencies; not proof of implemented compliance.
Incorrect premises: Local pull did not succeed; reviewed 38a2a81 was read from Git objects.
                    A source assertion requirement is not an already-passing test.
                    P0 derived tails are not stored fields or trained calibration.
                    155 minutes is not the registered-run cap.
                    CONTINUE is not Phase 6 registered-run or B0-B approval.
Test 163: SEALED; not opened.
```

## Source identity record

Read-only SHA-256 calculations over the reviewed Git-object bytes:

| Source | SHA-256 |
|---|---|
| v1.0.8 plan | `50d4bf218ec93b590c3866ce987a570b9ed3844601f07dfe249a6afde38345ca` |
| v1.0.8 template | `97b4d7ab59f4b5d62aa6caeefe49d8f9f3b69c61e962aabde639c5192c9ffa69` |
| v1.0.8 golden JSON | `0aa8284cbe1b4b4c4524fb682c10bb5f37bd73016800130209df959b73517e32` |
| v1.0.7 synthesis | `a6c808e9c0b3acf9a03625e38afbffbc1f655a468d93c68c44ca86dca3cd50f2` |

These identify the inspected files, not newly certified experimental artifacts. Template/schema inspection confirmed matching plan_path and null manifest_commit; the template's only extra key is note, now explicitly permitted. The earlier v1.0.7 report and all other workspace files were left unchanged.