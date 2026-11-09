# C5 P/M v1.0.9 — Sol final same-thread confirmation

Date: 2026-11-09. Reviewer: Sol 6.1. Same consultation thread; no subagents or other LLMs.

**Reviewed HEAD: `e680c8f`** (`e680c8fcb676dbd3d578c9ff7dc0238d08cd66fe`).

Mandatory verbatim quote:

```text
c5_pm_stats.bootstrap_paired_v2
```

## Scope and source access

This confirmation covers only (1) bootstrap symbol consistency, (2) manifest hash definition/external-text custody, and (3) evaluate_arm replacement timing. Closed v1.0.8 scientific/mechanical items are carried forward, not re-reviewed.

Read the new review request and required v1.0.8 synthesis from fetched origin/main; read the v1.0.9 plan, template, and golden JSON directly from Git objects at e680c8f. A focused plan diff and numbered clause inspection were used for the three requested items. The synthesis was context, not a substitute for checking the current clauses.

`git fetch origin` succeeded. Fetched origin/main is `b9fd85417377bc77cbe1ee146e34a89c78448869`. Exact byte comparisons confirmed that the four underlying review sources at e680c8f are unchanged at that fetched revision. Local checkout HEAD remains `a826308f64301179cb54c7a87a208bf3f1bc6af4`: the prior round's pull had been blocked by the untracked historical review output. This round did not retry that merge or alter the prior reports. Reviewed HEAD denotes the inspected Git revision, not the local checkout.

No training, evaluation, model import/forward, generation, D0, D1, test-163 access, or P1 use occurred. No runner/helper code was changed or executed. Only this report was written. Golden payloads were inspected for version-delta scope: only the spec label differs from v1.0.8; the already-closed digest calculations were not rerun.

## Summary

**Final verdict: NARROW.** Symbol naming and manifest hash/custody are closed at the protocol level. The new pre-freeze evaluate_arm clause introduces a lifecycle conflict with the retained no-code-before-freeze rule. Resolve that single scoped text issue before treating the reuse path as freeze-ready. This is not a scientific redesign or a request to change thresholds, seeds, donors, steps, or LR.

| Question | Verdict | Conclusion |
|---|---|---|
| Q1 — Symbol closure | agree | §§10.2/17.3 name v2; §13.5 prohibits legacy rather than selecting a competing symbol. |
| Q2 — Hash/custody | agree | Committed manifest bytes define the hash; committed external text and its D0 hash establish custody without self-reference. |
| Q3 — evaluate_arm | conditional | Timing is explicit, but conflicts with §16.1's blanket pre-freeze code prohibition. |
| Q4 — Residual | agree | One ranked Must-fix: reconcile the two lifecycle rules for helper reuse. |
| Q5 — Final | conditional | NARROW; corrected lifecycle first, then freeze/implementation/tests/gated D0. |

## Q1. Is bootstrap_paired_v2 consistent and legacy excluded?

**Verdict: agree at specification level.**

Evidence:

- §10.2, line 1183: `c5_pm_stats.bootstrap_paired_v2(seed=20261109)` replaces the former ambiguous callable name.
- §17.3, lines 1755/1761: the entrypoint and reused evaluate_arm both target `c5_pm_stats.bootstrap_paired_v2`.
- §13.5, line 1585: the stats module must not import legacy `bootstrap_paired`. This is a negative dependency rule, not a second positive callable definition. It does not repeat the v2 name, but is consistent with the explicit positive bindings above.
- §§10.2/17.3 prohibit legacy reuse; §17.3 requires a source/call-graph assertion over the Phase-6 path and forbids a monkeypatch-only workaround.

The symbol conflict is closed. This does not establish that a future implementation actually excludes indirect legacy calls or already passes the assertion.

Next steps:
1. Implement/import the exact v2 symbol and preserve the specified algorithm/seed; no compatibility alias may route Phase 6 to the legacy implementation.
2. Before D0, demonstrate transitive exclusion through reachable helper calls, including train_arm→evaluate_arm, with the required source/call-graph and behavioral tests. A grep limited to the entrypoint is insufficient evidence.

## Q2. Are freeze_manifest_sha256 and external text custody defined noncircularly?

**Verdict: agree.**

Evidence from §16.2:

- Line 1690 defines `freeze_manifest_sha256` as SHA256 of the **committed `_FREEZE.json` bytes**. It is neither a Git blob/commit identifier nor the hash of the external text file.
- Line 1688 keeps `manifest_commit:null` inside the manifest; the template matches.
- Lines 1689/1691 require the actual manifest commit SHA in `reports/provenance/C5_b0a/freeze_manifest_commit.txt`, created afterward and itself committed; D0 also records that text file's SHA256.
- Line 1692 requires D0 to record the manifest hash and manifest commit identity.

The valid custody chain is:

```text
C_plan: final plan/helper-source commit
M: _FREEZE.json binds C_plan, with manifest_commit=null
C_manifest: contains M
T: freeze_manifest_commit.txt contains C_manifest
C_custody: later commit contains T
D0: records C_manifest, SHA256(M at C_manifest), and SHA256(T)
```

T points to the earlier manifest commit, not its own containing commit. Neither M nor T needs to predict its own containing commit hash. The text's requirement that T is committed means its commit must occur before the D0 record is finalized, not merely that an uncommitted text file is present.

The phrase “records both ... from that external file” at line 1692 must be read with the explicit definition at line 1690: obtain **manifest_commit** from T, then compute **freeze_manifest_sha256** from committed M at that commit. T contains the commit SHA, not both digest values. The new explicit definition resolves that source distinction without a new scientific choice.

Next steps:
1. At actual freeze, commit T after C_manifest; verify that its SHA resolves to the commit containing the exact frozen manifest bytes.
2. In D0 provenance keep SHA256(M), SHA256(T), and the Git commit SHA as distinct values, calculating each from its stated source. Do not substitute working-tree/reformatted JSON bytes for committed M.

## Q3. Is evaluate_arm replacement timing sufficiently clear?

**Verdict: conditional — explicit timing, but not a consistent executable lifecycle for the reuse branch.**

Evidence:

- New §17.3 line 1761 says that, if evaluate_arm is reused, its bootstrap call is replaced by v2 **before the freeze commit**.
- Retained §16.1 line 1659 says **“No code before freeze.”**
- §16.2 line 1687 defines freeze_commit as the final plan commit containing normative bytes and helper sources; §17.1 freezes helper behavior at that commit.

The new line removes uncertainty about the intended replacement timing but conflicts with the blanket prohibition: an implementer taking the prescribed reuse branch must change helper code before freeze and must also not write code before freeze. Delaying the replacement until after freeze would violate §17.3 and change a pinned helper contract; silently treating the new clause as an authorization exception is also unsafe because no such exception is stated.

This is a conditional branch defect, not proof that every possible implementation is impossible. Avoiding legacy evaluate_arm entirely may avoid the branch, but the document expressly presents reuse as an allowed path; forcing an unannounced alternative is not closure of that path.

The source/call-graph assertion is an appropriate acceptance requirement when it covers the transitive path, aliases/module-qualified calls, and nested evaluation. It does not resolve the conflicting authorization/timing rules, nor prove that replacement has landed. No new code or tests were inspected/executed in this consultation.

Next steps:
1. Reconcile §16.1 and §17.3 explicitly. The smallest repair preserving the new timing is a narrowly authorized pre-freeze helper-bootstrap replacement exception, while retaining the ban on experimental execution and broader implementation before freeze. This review recommends a text correction; it does not authorize making that code change now.
2. After the corrected lifecycle is approved, land the allowed helper change and appropriate v2 dependency before the final freeze_commit, verify transitive legacy exclusion, and bind the resulting helper revision in the manifest.

## Q4. Did v1.0.9 introduce any residual problem? Ranked list

**Verdict: agree — one scoped lifecycle residual.**

### MF-1 — Medium, freeze-readiness blocker for evaluate_arm reuse

**Conflict:** §16.1 line 1659 prohibits code before freeze; new §17.3 line 1761 requires the reused helper's code replacement before freeze.

**Impact:** faithful implementation of the allowed reuse path has no unambiguous authorized ordering. Freezing old helper bytes and changing them later does not satisfy the newly required pre-freeze replacement or helper pinning.

**Minimal correction:** explicitly permit the narrowly defined helper-bootstrap compatibility change before final freeze_commit, with execution still prohibited, or revise the lifecycle coherently to another explicitly reviewed ordering. Do not simply weaken transitive legacy exclusion or accept a stale helper pin. This is a text/authorization-order fix, not a result-driven methodological choice.

No separate symbol or custody Must-fix was demonstrated. The lack of an explicit v2-name repetition in §13.5 is not a competing definition; the positive bindings in §§10.2/17.3 are unambiguous. The manifest hash's input bytes and the external text's committed custody are now explicit. Closed v1.0.8 scientific items are not reopened.

Next steps:
1. Make only the lifecycle text correction and review its consistency with helper pinning and the no-execution boundary.
2. Then verify the authorized pre-freeze source changes and complete freeze; retain all scientific settings and budgets unchanged.

## Q5. Final verdict and approval scope

**Verdict: conditional. Final recommendation: NARROW.**

Symbol and hash/custody closure are accepted. Withhold as-is approval for the protocol's helper-reuse lifecycle until MF-1 is resolved. After that correction, recommend proceeding through the authorized helper preparation, valid freeze, remaining implementation/unit tests, and gated D0. This consultation itself performs or authorizes no experimental run.

Next steps:
1. Resolve the single pre-freeze helper timing contradiction prospectively, not through an unstated exception.
2. Validate the v2 call path and manifest custody against the actual authorized revisions before D0.
3. Stop before D1/registered execution or downstream stages without their separate approvals.

## Final STOP / NARROW / CONTINUE block

```text
Final verdict: NARROW.
v1.0.9 freeze: Withhold as-is approval of the evaluate_arm reuse lifecycle;
              reconcile §16.1 and §17.3, then bind the authorized helper revision.
Implementation + unit tests: Conditional next stage under the corrected lifecycle;
                             no implementation performed in this consultation.
D0: Not approved/run now. After correction, valid freeze and passing acceptance tests:
    <=4 zero-update configs (one per arm), debug seed 20261111, <=15 minutes;
    no decision/signal labels, no result claim, no timing projection.
D1: NOT APPROVED; separate authorization, <=4 total updates / 20 minutes.
3-seed: NOT APPROVED; separate authorization after full D1 and T_proj<=96 minutes;
        prospective 1,200 updates / 120-minute registered hard abort.
Forbidden: P1 use; opening test 163; T5Gemma2 reopening (D-108 STOP);
           automatic Phase 6 registered/B0-B/B1/B2/Stage C progression;
           post-result threshold/seed/donor/step/LR changes; retry/extension.
Maximum compute now: No experimental execution; zero optimizer updates.
Prospective separate ceilings: D0 0 updates/15 min + D1 4/20 + registered 1200/120
                              = 1,204 updates/155 min, not a single-run cap or grant.
                              Six threads, CPU only, no GPU, no retry.
Must-fix (ranked): MF-1 — pre-freeze helper replacement versus no-code-before-freeze.
v1.0.9 self-contained: Symbol/hash definitions adequate; helper-reuse lifecycle
                      needs one explicit ordering/authorization correction.
Incorrect premises: Defining a pre-freeze requirement does not override a conflicting
                    blanket code prohibition without an explicit exception.
                    Contract/source-assertion wording is not proof of passing code.
                    Manifest-byte hash, text-file hash, and Git commit SHA are distinct.
Test 163: SEALED; not opened. P1: not used. T5Gemma2: D-108 STOP maintained.
```

## Reviewed source fingerprints

| Source at e680c8f | SHA-256 |
|---|---|
| v1.0.9 plan | `3b662b27ee8078cc93031cb2acea04634205e96db487057c4e6514b01d5bb719` |
| v1.0.9 freeze template | `dc7c6d9737256851ad425c9f7f222c6e3fb1a7082facf85d683ec35c5ff6f9a4` |
| v1.0.9 golden JSON | `9223cb9257962b090c6acd397c6aa68c89ba86d6271f7d6a39464a0c4e43339b` |
| v1.0.8 synthesis | `7b40f441097cf8bdbba0f49e9b8aef3ed02aa276b6112ad4adfb5da03643821a` |

Fingerprints identify inspected source bytes only. No trained results, runtime feasibility, completed freeze, or implementation-test success is inferred.
