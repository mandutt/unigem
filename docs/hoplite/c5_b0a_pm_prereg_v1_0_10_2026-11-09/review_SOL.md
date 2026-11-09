# C5 P/M v1.0.10 Option A — Sol same-thread final confirmation

Date: 2026-11-09. Reviewer: Sol 6.1. Same consultation thread. No subagents or other LLMs.

**Reviewed HEAD: `a88c714`**, full SHA `a88c71416764949d496e40b23255a242c8bb50f6`.

Mandatory verbatim quote from §17.3:

```text
own eval loop                       # no evaluate_arm
```

## Scope, access, and limits

This review covers only Option A's lifecycle, evaluate_arm exclusion, and train_arm training-only reuse. The v1.0.9 symbol/hash/custody findings remain closed and were not substantively re-reviewed. No scientific thresholds, seeds, donors, steps, LR, or existing budgets were reconsidered.

Read the new request and required v1.0.9 synthesis from fetched origin/main; read the v1.0.10 plan's scoped change/context, template, and golden JSON from Git objects at a88c714. Inspected only the relevant train_arm/evaluate_arm source bodies at that same revision to answer Q3; parsed their call sites without importing or executing the runner. Historical synthesis is context, not authority replacing the current source evidence.

`git fetch origin` succeeded. Fetched origin/main is `206117bd31e29d2b5fd391e2bd0fc7a831c3d6d7`. Exact byte comparisons confirmed the plan, template, golden JSON, and synthesis are unchanged between a88c714 and fetched origin/main. Local checkout HEAD remains `a826308f64301179cb54c7a87a208bf3f1bc6af4`; earlier untracked consultation reports were preserved, not overwritten to force a pull. The reviewed revision is the inspected Git object, not local checkout HEAD.

Only this v1.0.10 review file was written. No older report, source, template, fixture, or provenance artifact was modified. No training, evaluation, model import/forward, generation, D0/D1, test-163 access, or P1 use occurred. AST/source inspection is not training/evaluation. Golden data differ from v1.0.9 only in the version label; no already-closed digest calculations were rerun.

## Executive result

**NARROW.** The prior pre-freeze-edit contradiction is removed from the text. However, Option A's positive call edge to `c5_mt5_lora_b0.train_arm` does not implement the asserted training-only boundary: the frozen function unconditionally evaluates after training. The result is the exact transitive evaluate_arm/legacy-bootstrap path Option A prohibits.

This is one scoped reuse-contract defect, not a reopening of the closed v2-symbol or hash contract. A narrow correction is to make Phase 6 own the training loop as well as evaluation, reusing only suitable frozen primitives—not the composite legacy train_arm function. That preserves no-code-before-freeze: the new implementation is written after protocol freeze, without editing the pinned legacy helper before freeze.

| Question | Verdict | Conclusion |
|---|---|---|
| Q1 — Lifecycle | conditional | No pre-freeze edit is now required, but the advertised unchanged-helper reuse path remains inconsistent with its exclusion rule. |
| Q2 — evaluate_arm exclusion | conditional | Direct and transitive prohibition/test are adequate requirements; a direct-import check alone is insufficient. |
| Q3 — train_arm reuse | disagree | Calling the frozen train_arm reaches evaluate_arm and then legacy bootstrap; a comment does not make it training-only. |
| Q4 — Residual | agree | One Must-fix: remove or explicitly replace the composite train_arm call edge with a genuine training-only route. |
| Q5 — Final | conditional | NARROW; correct that route before freeze/implementation/gated D0. |

## Q1. Does Option A satisfy no-code-before-freeze and helper reuse together?

**Verdict: conditional.**

Evidence:

- §16.1 line 1660 retains “No code before freeze.”
- §17.3 removes the v1.0.9 requirement to edit evaluate_arm before freeze; line 1765 expressly says no pre-freeze helper edit is required.
- Lines 1756/1764 still advertise reuse of `c5_mt5_lora_b0.train_arm` for training, while lines 1762/1766 prohibit evaluate_arm throughout the Phase-6 path.

Thus the previous literal timing contradiction is closed. But the full proposed path is not valid as written because the unchanged train_arm is a composite training/evaluation/generation routine, not a training-only callable. Editing that pinned routine to make the comment true would reintroduce the helper-edit question; silently doing so is not the stated Option A.

A coherent Option A needs no pre-freeze edit if the prospective Phase-6 implementation instead owns its loops and reuses suitable frozen lower-level primitives. This is an implementation-path clarification, not a change to measurement semantics.

Next steps:
1. Remove the positive call edge to the composite legacy train_arm, or define an explicit post-freeze training-only implementation that does not invoke it or alter pinned helper behavior.
2. Then follow protocol freeze → implementation/unit tests → gated D0, retaining no experimental execution before authorization.

## Q2. Are the evaluate_arm exclusion rule and tests sufficient?

**Verdict: conditional — adequate when interpreted transitively, not as an entrypoint-only import ban.**

Evidence:

- §13.5 line 1586 adds “Phase 6 path does not import evaluate_arm.”
- §17.3 line 1762 forbids both import and call of the legacy evaluate_arm.
- Line 1766 strengthens this to a source/call-graph assertion that neither evaluate_arm nor legacy bootstrap appears in the Phase-6 path; line 1767 prohibits a monkeypatch-only workaround.

These requirements cover the right boundary if “path” includes reachable helper bodies. But not importing evaluate_arm directly in c5_pm_phase6.py does not prevent a called helper from invoking it. The prescribed positive train_arm edge currently fails the stronger requirement. An assertion should reject that path, not be weakened to accept it.

Next steps:
1. Keep the transitive source/call-graph assertion, including helper-to-helper calls and aliases/module-qualified access; do not reduce it to a grep of entrypoint imports.
2. During authorized implementation, prove that the actual training and evaluation routes do not reach evaluate_arm, and that the owned evaluation loop uses the already-closed v2 contract. No such test was run here.

## Q3. Does training-only train_arm reuse avoid the legacy evaluation path?

**Verdict: disagree for the explicitly named frozen function.**

Evidence at reviewed commit a88c714 in `runner/c5_mt5_lora_b0.py`:

| Source | Observation |
|---|---|
| Lines 665–750 | train_arm is a composite function with signature `train_arm(args, arm)`; there is no training-only/evaluation-disabled argument. |
| Line 723 | After the optimizer loop it calls `evaluate_arm(model, adapter, val_cache, val_ids, labels_by_id, copy_by_id, donors)`. |
| Line 724 | It also calls generate_arm. |
| Line 460, inside evaluate_arm | The returned statistics call legacy `bootstrap_paired(deltas)`. |

The reachable chain is therefore:

```text
c5_pm_phase6.py
  -> c5_mt5_lora_b0.train_arm
     -> evaluate_arm
        -> legacy bootstrap_paired
```

Appending `# training only` to the diagram does not stop execution before line 723. Ignoring the function's returned evaluation, adding a separate own eval loop afterward, or omitting a direct evaluate_arm import does not prevent the old evaluation/statistics from executing. No training/evaluation was run to establish this; it is confirmed by source and AST call-site inspection at the reviewed revision.

Reusing training logic conceptually in a new post-freeze loop could be compliant, but that is not calling the named frozen train_arm as the diagram currently specifies. The spec must distinguish those alternatives explicitly.

Next steps:
1. Prefer the smallest consistent text correction: Phase 6 owns its training loop and its evaluation loop; it does not call legacy train_arm/evaluate_arm, while reusing permitted frozen primitives under their contracts.
2. Add a transitive regression assertion that rejects the composite legacy train_arm route. Do not use monkeypatching, exceptional early termination, or ignored evaluation results as a training-only workaround.

## Q4. Did v1.0.10 leave or introduce a problem? Ranked list

**Verdict: agree — one scoped blocker remains.**

### MF-1 — High, Option A path blocker: composite train_arm mislabeled as training-only

Sources: §17.3 lines 1756/1764 versus runner lines 723/460, together with §17.3's transitive exclusion at line 1766.

The positive call graph reaches forbidden evaluation/statistics through the unchanged helper. The negative rules are explicit but cannot both be satisfied by following that positive edge. A reviewer should not claim this path is compliant merely because the eventual source assertion would catch and reject it.

Minimal fix: delete the legacy train_arm call edge and state that the new post-freeze Phase-6 implementation owns the training loop as well as evaluation, using the frozen primitives without changing scientific semantics. If another training-only reuse design is selected, define its callable and lifecycle explicitly; do not imply the existing composite function already supports it. No source edit is requested or authorized in this consultation.

No second scoped Must-fix was identified. The old pre-freeze replacement sentence is gone; symbol/hash/custody findings stay closed. The golden fixture rules, statistical thresholds, cohorts, and cap arithmetic were not reopened.

Next steps:
1. Make the narrow call-graph/reuse wording correction consistently in §17.3 and its acceptance test description.
2. Confirm the corrected route preserves no-code-before-freeze and excludes legacy composite evaluation transitively before recommending freeze.

## Q5. Final recommendation and scope

**Verdict: conditional. Final recommendation: NARROW.**

Withhold as-is Option A freeze approval until MF-1 is resolved. After a coherent prospective training-only route is specified, recommend the bounded sequence freeze → implementation/unit tests → gated zero-update D0. Source inspection here does not certify an implemented Phase-6 runner, passing tests, trained results, timing feasibility, or any completed freeze.

Next steps:
1. Correct the single training-only reuse contract without changing scientific settings.
2. Complete the established freeze process; implement and pass the existing acceptance suite plus transitive exclusion checks.
3. Consider D0 only after those gates; stop before D1/registered/downstream execution without separate approval.

## Final STOP / NARROW / CONTINUE block

```text
Final verdict: NARROW.
v1.0.10 freeze: Withhold as-is Option A approval pending MF-1 training-only path correction.
Implementation + unit tests: Conditional after corrected protocol freeze;
                             no implementation performed or authorized here.
D0: Not approved/run now. After correction/freeze/tests: <=4 zero-update configs,
    one per arm, seed 20261111, <=15 minutes, no decision/signal labels,
    no scientific-result claim, no timing projection.
D1: NOT APPROVED; separate approval, <=4 total updates / 20 minutes.
3-seed: NOT APPROVED; separate approval after complete D1 and T_proj<=96 minutes;
        prospective 1,200 updates / registered 120-minute hard abort.
Forbidden: P1 use; opening test 163; T5Gemma2 reopening (D-108 STOP);
           automatic Phase 6 registered/B0-B/B1/B2/Stage C progression;
           post-result threshold/seed/donor/step/LR changes; retry/extension.
Maximum compute now: No experimental execution; zero optimizer updates.
Prospective separate ceilings: D0 0/15 min + D1 4/20 + registered 1200/120
                              = 1,204 updates / 155 minutes, not a blanket grant.
                              Six threads, CPU only, no GPU, no retry.
Must-fix (ranked): MF-1 — the named frozen train_arm is not training-only and
                  reaches evaluate_arm -> legacy bootstrap_paired.
v1.0.10 self-contained: Option A requires one explicit training-only path correction;
                       prior closed symbol/hash items remain accepted.
Incorrect premises: A '# training only' comment changes neither helper behavior
                    nor the transitive call graph. Ignored eval outputs still execute.
                    Direct import exclusion is not transitive call exclusion.
Test 163: SEALED; not opened. P1: unused. T5Gemma2: D-108 STOP maintained.
```

## Inspected source identities and preservation

| Source at a88c714 | SHA-256 |
|---|---|
| v1.0.10 plan | `d9d6599451714ac0cde024d9e25ac17454b56b1c024371c5570480457bd12d9b` |
| v1.0.10 template | `567d8afbb65229b4070b39d18ab86baf5a26205a91856aaf3233374dfcfe1583` |
| v1.0.10 golden JSON | `795bd0852f51d8e428024386f2a88a1409e25221500d3460c34094d8a1617b1c` |
| v1.0.9 synthesis | `0588a4fc7002353532e18defea6ab23df42f729a57d6854d8de0b44467ecf9b8` |

These fingerprints identify read source bytes, not experimental artifacts. Older local v1.0.7/v1.0.8/v1.0.9 report fingerprints were captured before writing this report and checked afterward for preservation. No older report was modified.