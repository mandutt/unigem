# C5 P/M v1.0.11 — Sol own-loop final confirmation

Date: 2026-11-09. Reviewer: Sol 6.1. Same consultation thread; no new thread, subagent, or additional LLM.

**Reviewed HEAD: `6fad89e`**, full SHA `6fad89e59e4aa2222010f2360e5eb4c2572c4023`.

Mandatory verbatim quote from §17.3:

```text
-> own training loop
```

## Scope and evidence limits

This is a scoped continuation: own training/evaluation lifecycle, exclusion of train_arm/evaluate_arm throughout the transitive Phase-6 path, and implementability of the owned training loop under §§2.5/2.7. Already-closed v1.0.10 symbol/hash/custody and scientific items were not re-reviewed.

Read the new request and required v1.0.10 synthesis, and inspected the v1.0.11 plan's changed clauses and relevant §§2.2–2.7/13.5/16.1/17.1/17.3 context, template, and golden JSON. The synthesis supplied review history; the conclusions below rest on current normative clauses, not another model's answer. No older runner source needed reopening: this version expressly prohibits the composite helper previously inspected.

`git fetch origin` succeeded. Local checkout HEAD remains `a826308f64301179cb54c7a87a208bf3f1bc6af4`, with prior untracked reports preserved. Reviewed sources were read directly from Git objects at **6fad89e**, not represented as local checkout files. Fetched origin/main is `9954c986a7f48ffba422908dfb84b1ddab13035e`. Exact byte comparisons confirmed that all four underlying review sources at 6fad89e are unchanged at fetched origin/main. No merge was attempted over older local review files.

No training, evaluation, model import/forward, generation, D0/D1, sealed test-163 access, or P1 use occurred. Only this new report was written. Golden payloads differ from v1.0.10 only in the spec label; closed digest calculations were not rerun. No implementation correctness, passing runner tests, trained result, timing feasibility, or completed freeze is claimed.

## Executive verdict

**CONTINUE**, limited to **valid protocol freeze → implementation + unit tests → gated zero-update D0**. The prior training-only reuse blocker is closed at the specification level: neither composite legacy helper is an allowed call edge anymore. The owned-loop implementation must still demonstrate compliance with the preserved training/measurement rules and the transitive exclusion assertion before D0.

No remaining pre-freeze Must-fix was identified within this round's scope. D1, registered three-seed execution, B0-B/B1/B2/Stage C, P1/test-163 use, and T5Gemma2 reopening are outside this recommendation and remain unapproved. This consultation performs no experimental execution.

| Question | Verdict | Conclusion |
|---|---|---|
| Q1 — Own-loop lifecycle | agree | Post-freeze owned-loop implementation needs no edit of pinned legacy composite helpers. |
| Q2 — Exclusion/transitive path | agree | Both helpers and legacy bootstrap are forbidden across the explicitly rooted transitive call graph. |
| Q3 — Training correctness | conditional | §§2.5/2.7 supply an implementable contract; actual code/mode/RNG/gradient compliance remains to be tested. |
| Q4 — Residual problems | agree | No scoped pre-freeze blocker remains; implementation acceptance obligations are not completed evidence. |
| Q5 — Final | agree | CONTINUE only through freeze, implementation/tests, and gated D0. |

## Q1. Is own-loop ownership consistent with no-code-before-freeze?

**Verdict: agree.**

Evidence: §16.1 retains no code before freeze. §17.3 lines 1755–1758 now show the new entrypoint owning both training and evaluation; lines 1765/1767 bind that ownership to the mode/RNG contract and state that no pre-freeze helper edit is required. The former train_arm call edge and its misleading training-only claim are gone.

The implementer can freeze the protocol and existing permitted helper contracts first, then write the owned loops afterward. There is no need to modify the pinned legacy train_arm/evaluate_arm behavior before freeze, or to alter it afterward while claiming to reuse its frozen behavior. Owning the loops means implementing the existing measurement/training contract, not inventing a new scientific method.

Next steps:
1. Complete the established freeze procedure without modifying legacy composite helpers for Phase 6.
2. Implement the new loops only after valid freeze and under the project's implementation authorization; keep all experimental execution behind its existing gates.

## Q2. Are train_arm/evaluate_arm exclusions and the transitive path clear enough?

**Verdict: agree as a specification and acceptance requirement.**

Evidence:

- §13.5 line 1586 now prohibits importing either train_arm or evaluate_arm in the Phase-6 path.
- §17.3 lines 1762–1764 prohibit import/call of both composite helpers and legacy bootstrap.
- Line 1766 explicitly explains that train_arm calls evaluate_arm and must not be reused.
- Line 1768 defines Phase-6 path as the **transitive call graph rooted at `runner/c5_pm_phase6.py`**.
- Line 1769 requires no train_arm, evaluate_arm, or legacy bootstrap in that transitive path; line 1771 prohibits a monkeypatch-only workaround.
- §17.1 lists permitted primitives such as Adapter, make_labels, load_layer_cache, LoRALinear, attach_decoder_lora_mt5, and native_memory, not either composite helper.

This closes the direct-versus-indirect loophole: a wrapper around train_arm, an alias, or an intermediate helper that calls evaluate_arm is not compliant merely because the entrypoint lacks a literal direct import. Importing a permitted primitive from a source module does not itself mean invoking every dormant function defined in that module; the assertion must distinguish permitted primitive dependencies from forbidden reachable calls/import bindings. P0 remains outside this entrypoint's transitive experiment path; §17.3 line 1770 explicitly preserves its p0_eval_split route.

Next steps:
1. Implement a source/call-graph assertion covering the actual reachable helpers and aliases/module-qualified calls; do not reduce it to an entrypoint-only grep or reject permitted primitives solely for sharing a source module.
2. Before D0, require evidence that both owned loops and their dependencies satisfy the exclusion. No such implementation test was run in this consultation.

## Q3. Can the owned training loop preserve §§2.5/2.7 correctness?

**Verdict: conditional — the contract is implementable; implementation correctness is not yet established.**

§17.3 explicitly retains §2.7, while §2.5 remains the normative measurement contract. Owning the loops does not authorize reusing the incompatible composite runner's F/L-only policy or silently changing model modes, RNG ordering, token alignment, memory construction, or optimizer settings.

Required implementation mapping:

| Concern | Preserved contract to implement and test |
|---|---|
| Fresh state and initialization | §2.7: fresh model per arm, no cross-arm state reuse; manual_seed(seed), adapter first for F/L/PA, then LoRA for L/P/PA, no reseed between those construction steps. P constructs no dummy adapter and consumes no adapter initialization RNG. |
| Arm trainable sets | §§2.1/2.5.4: F adapter only; L adapter+decoder LoRA; P decoder LoRA only; PA adapter+decoder LoRA. Base decoder and native encoder remain frozen; assert the exact parameter inventory. |
| Modes | §2.7: base decoder eval for all arms; native encoder eval for P/PA; adapters train for F/L/PA; LoRA branches/dropout train for L/P/PA. A blanket model.train() must not reactivate frozen layers; evaluation sets all relevant modules to eval, with training policy restored before any subsequent update. |
| Memory/gradient path | §2.5.3: F/L use adapter(EG2 cache); P native encoder with identity; PA native encoder then adapter. Native encoder may be detached/frozen, but PA's adapter output and LoRA computation must retain the gradients needed by their trainable parameters. Do not wrap the entire training forward in no_grad. |
| Training input | §§2.3/2.5.3: real memory only; no donors and no M-only 753-length eligibility filter on training. Preserve the registered train20 order and no padding/drop/substitution rules. |
| Labels/loss | §§2.5.1–2.5.2: local slow T5 tokenizer, stated prefix/source/target lengths, native special tokens; built-in mT5 CE with its internal shift, no extra logits/label shift or label smoothing; nonfinite loss aborts. Batch dimension and all-ones attention mask must match the actual memory length. |
| Optimization | §2.2: AdamW, weight_decay .01, adapter LR 1e-3 where applicable, LoRA LR 1e-4 where applicable, batch 1, registered 100 updates, train20_ids[step % 20], clip 1.0. No adapter group for P. Debug stages retain their separate update limits. |
| Owned evaluation | §2.5 remains binding for same-position full/copy CE, copy mask/guard, donor matching/cropping, and decoding policy. Evaluation ownership is not permission to change those measurements or import the excluded composite evaluator. |

These obligations can be implemented using the allowed primitives and a new orchestration loop. None requires restoring train_arm/evaluate_arm or editing them before freeze. In particular, a frozen encoder does not imply a frozen PA adapter, and an eval-mode base decoder does not imply LoRA dropout must be disabled during training.

Next steps:
1. During authorized implementation, add pure/synthetic unit fixtures for arm-specific inventory/mode policy, initialization ordering/no reseed, training-only real-memory selection, and approval/update guards.
2. Verify intended trainable gradient flow, frozen-parameter invariance, loss/token alignment, and eval→train mode restoration through the project's authorized test/debug stages; do not claim those model-backed checks ran here or use this review to authorize extra updates.
3. Require the existing acceptance suite and the new transitive exclusion tests before D0. Registered training remains a later separately approved stage.

## Q4. Did v1.0.11 create a new scoped problem? Ranked residuals

**Verdict: agree that the scoped residuals are now closed; no pre-freeze Must-fix identified.**

The positive call graph no longer contradicts the negative exclusion rules. Both loop ownership and test scope are explicit, the composite helper is named as forbidden, and §§2.5/2.7 still define how the new loop must behave. The permitted helper list does not introduce a competing composite train entrypoint.

Ranked pre-freeze Must-fix list: **none within this confirmation's scope**. Implementation-time priorities, not further protocol blockers:

1. Demonstrate transitive exclusion rather than just direct import exclusion.
2. Demonstrate arm-specific mode/RNG/parameter/gradient correctness under the existing training contract.

No symbol/hash/custody, golden algorithm, threshold, cohort, or cap re-review is implied. No trained P/PA/M evidence is established by an own-loop diagram.

Next steps:
1. Freeze this contract through the established process, rather than adding another unneeded scientific choice.
2. Track the two implementation evidence obligations before D0; do not convert unimplemented assertions into a claim of completed verification.

## Q5. Final verdict and recommendation scope

**Verdict: agree. Final recommendation: CONTINUE.**

The v1.0.10 composite-helper blocker is closed as a prospective protocol requirement. Recommend valid freeze, followed by implementation/unit tests and bounded zero-update D0 after the acceptance gates. This is not blanket Phase-6 execution approval, not evidence that implementation exists or works, and not a downstream gate pass.

Next steps:
1. Complete valid freeze and record the established revision/content bindings.
2. Implement the owned loops and pass acceptance tests, including transitive exclusions and the arm-specific training obligations.
3. Proceed only to the gated D0 scope; obtain separate approval before D1, registered three-seed execution, or downstream work.

## Final STOP / NARROW / CONTINUE block

```text
Final verdict: CONTINUE (scoped protocol-readiness recommendation; consultation only).
v1.0.11 freeze: Recommend proceeding with the established freeze process.
Implementation + unit tests: Recommend proceeding after valid freeze; own training/eval
                             loops must preserve §§2.5/2.7 and exclude composite helpers.
D0: Recommend gated mechanics only after implementation/tests pass:
    <=4 zero-update configs, one per arm, seed 20261111, <=15 minutes;
    no decision/signal labels, no scientific-result claim, no timing projection.
D1: NOT APPROVED; separate approval, <=4 total updates / 20 minutes.
3-seed: NOT APPROVED; separate approval after complete D1 and T_proj<=96 minutes;
        prospective 1,200 updates / registered 120-minute hard abort.
Forbidden: P1 use; opening test 163; T5Gemma2 reopening (D-108 STOP);
           automatic Phase 6 registered/B0-B/B1/B2/Stage C progression;
           post-result threshold/seed/donor/step/LR changes; retry/extension.
Maximum compute now: No experimental execution in this consultation; zero optimizer updates.
Prospective separate ceilings: D0 0/15 min + D1 4/20 + registered 1200/120
                              = 1,204 updates / 155 minutes, not a blanket grant.
                              Six threads, CPU only, no GPU, no retry.
Must-fix (ranked): None remaining before freeze within this round's scope.
                  Implementation/test evidence remains mandatory before D0.
v1.0.11 self-contained: Adequate consolidated protocol with explicitly pinned primitive
                       dependencies; not proof of implemented or trained correctness.
Incorrect premises: Own-loop ownership is not a passing implementation test.
                    Frozen base/native encoder does not freeze adapter/LoRA gradients.
                    Primitive reuse does not authorize composite train_arm/evaluate_arm reuse.
                    CONTINUE is not registered Phase 6 or B0-B approval.
Test 163: SEALED; not opened. P1: unused. T5Gemma2: D-108 STOP maintained.
```

## Source identity and preservation

| Source at 6fad89e | SHA-256 |
|---|---|
| v1.0.11 plan | `327a3e34f5bb2721b8b2400718dfd7bc56a0946641d1e83e2c8b454bf656d007` |
| v1.0.11 template | `dab5655f0e3684b8924dc03fdc17dd4ae2a48c24a143e616024b3108667fdd13` |
| v1.0.11 golden JSON | `30cbd1c1281235d0750c2bf9271b82cbe55eb64f099d8226216e14b2020ed3f6` |
| v1.0.10 synthesis | `f295dcc3e6eaf94099b1adc8b6b0d6d57a39e786c740a59b88c106d96fcd81ec` |

These identify inspected source bytes only. Earlier local v1.0.7–v1.0.10 report fingerprints were captured before writing and checked afterward; no older report was modified.