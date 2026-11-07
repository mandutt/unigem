# Independent review — C5 D-084 rev2, URL-only baseline (reviewer: GLM 5.3 Flash)

- Review basis: `origin/main` HEAD `e8b6367c1bd16b010318145587aaaedc14a77027` ("docs: add D-084 rev2 review prompts and dispatch").
- Sync: `git fetch origin` OK; `git pull --ff-only origin main` → "Already up to date". HEAD before and after: `e8b6367c1bd16b010318145587aaaedc14a77027`. Nothing modified except this file.
- Read in full: `reports/EXTERNAL_REVIEW_C5_D084_REV2_2026-11-07.md` (all 346 lines), `docs/D-084_verifier_v2_rev2_2026-11-07.md` (all 368 lines), `reports/C5_D084_3AI_REVIEW_SYNTHESIS_2026-11-07.md` (all 278 lines).
- Read in full or targeted: `runner/c5_a1_verifier_v2_audit.py` (all 279 lines), `eval/slot_verify.py` (all 188 lines), `reports/provenance/C5_a1/full_2ep/verifier_v2_audit.json`, `selection.json`, `selection_summary.json`, `error_analysis_1940_vs_2586.json`, `eval_step_{0647,1293,1940,2586}/eval.metrics.json`, `pilot300_val161/metrics.json`, `reports/C5_A1_verifier_v2_audit_2026-11-07.md`, `reports/C5_A1_full_train_2ep_2026-11-07.md`, `reports/C5_A1_3AI_REVIEW_SYNTHESIS_2026-11-07.md`, `docs/D-084_verifier_v2_draft_2026-11-07.md`, prior review files in `docs/hoplite/c5_d084_2026-11-07/` and `docs/hoplite/c5_fulltrain_2026-11-07/` (targeted).
- Not done: no training or generation; no test 163 access or evaluation; no subagents or additional LLM calls; no P1 data; no production file edits. The audit script was **not** re-run (it writes `verifier_v2_audit.json` into the repo; and its input data is absent here).
- Verification limit: `data/external/f5_pairs_v3*.jsonl` is **not present in this sandbox** (confirmed: `data/external/` does not exist). The P0 corpus, val sources, and raw text of `03992`/`04709`/`03801`/`03978` and the 5 flipped excluded pairs could not be inspected. Statements about them come from committed audit JSON/code/reports only. Items derived by me are marked **[derived]**; unverifiable items **[unverified]**.
- Status discipline: D-083 strict stands (`selected_step: null`, pilot300 fallback, not product approval). Every 084a/084b number below is a **provisional, pre-spec-audit** value. This report approves no gate change, no candidate, no promotion.

---

## 0. Headline findings

1. **rev2's provisional 084a expected table is consistent with the committed artifacts, and the key 1,940 number (158, not 159) is now analytically right.** [derived]
   - From `error_analysis_1940_vs_2586.json`: 1,940's v1 `new_kinds` = `{time: 1, number: 3}` over fail docs `03978`, `04709`, `04951`. `04709` contributes 1 number-new and `04951` 2 number-new, so **`03978`'s new slot is the single `time`-type new**. In the audit matcher (`runner/c5_a1_verifier_v2_audit.py` `match_v2`), only the time-qualifier clause can resolve a time-type new (URL clause matches `url` kind; unit clause matches `number`). Therefore **URL-only cannot fix `03978`**, and 1,940 stays 158/161 under 084a — exactly rev2's expectation, and a correction of the prior synthesis table that conflated "URL-only/generic" at 159.
   - 2,586's v1 `new_kinds` = `{url: 1, number: 2}`: `02742` is the url-new (source wraps `http://coronamap.\nsite`; 2,586's summary has the joined `http://coronamap.site`; both-side join makes them identical), `04951` (`2.3%`/`2.2%`) remains a genuine negative. So URL-only → 160/161. Consistent with rev2.
   - 1,293: fails are `02742` (url) + `03801` (identifier, per A1 synthesis §3.3/§3.4) → 160/161 under URL-only. Consistent.
   - 647: fails `00114`, `00818`, `01767`, `02742`, `03086`, `03978`; only `02742` is known url-type. The other five kinds are **unclassified in any committed artifact** (A1 synthesis §3.4 says so explicitly). Rev2's 156 assumes none of the five is summary-side URL-wrap-fixable. Plausible but unproven — see finding 5 and Must-fix 2. Selection-invariant either way (647 is disqualified by repeated4 0.0684 > 0.06 regardless).
2. **The largest unmodeled risk in rev2 is strictness-induced regression.** [derived] 084a's strict URL canonicalization is strictly narrower than v1's `_canonical` (which lowercases the whole URL and strips commas — `eval/slot_verify.py` lines 99–110). Strictness can only **remove** matches; the wrap join is the only match-adding change. Any val-161 or clean-1,617 pair that passed v1 only because path/query case or commas were erased would **newly fail** under 084a. The old audit structurally could not detect this (it reused v1's canonicalizer for all matching, `match_v2` lines 83–101), so "clean 1,617 v1/v2 diff = 0" is vacuous in the strict direction too. No committed artifact quantifies URL case/comma prevalence on val. If such a regression hits 1,293 or 2,586, the expected 160s break. Rev2 never states this direction.
3. **Under URL-only, excluded-383 flips should be zero, and the 5 known flips are unit-clause (084b) evidence.** [derived] All 5 flips' `v1_new` are plain numbers (`2020`, `2021`, `404`, `20`, `5000`+`200`; `verifier_v2_audit.json.target_audit.excluded.flips`). Only the bare-number/unit clause can produce those. The URL clause cannot. So the 383-flip adjudication is not on the 084a critical path; pre-register "expected 0 excluded flips under 084a; any flip that appears is URL-clause-caused and blocks".
4. **The candidate outcome is knife-edge by construction, and rev2 should say what happens if it collapses.** [derived] 2,586's 084a eligibility rests on exactly one repair (`02742`). If the spec-faithful matcher rejects that repair, or a strictness regression appears (finding 2), the eligible full-train set becomes empty and the honest outcome is **no candidate + pilot300 fallback remains**. Rev2 marks everything provisional but does not pre-register the no-candidate branch.
5. **Numbers cross-checked.** The strict table matches `eval.metrics.json`/`selection.json` exactly for all five systems (F1, grounded, new-slot micro, EOS, repeated4, preservation, slots/doc). The syntheses' CP figures are internally consistent with **two-sided 95% Clopper–Pearson**: 0/837 → upper 0.44%, 4/860 → 1.19%, 3/762 → 1.15%, 160/161 → lower 0.9659, 0-error two-sided pass-rate lower bound ≥ 0.99 requires n ≥ 368. [derived, recomputed] Gate arithmetic checks: 160/161 = 0.99379 ≥ 0.99 passes; 159/161 = 0.98758 fails.
6. **Confirmed audit-matcher defects** (code-level): (a) no URL case/comma strictness — matching uses v1 `Slot.canonical` (`match_v2` lines 83–101); (b) uniqueness guard is occurrence-count, not distinct typed-slot (`if len(snum[value]) != 1 ...`, line 132); (c) `counter_alias=True` **bypasses the uniqueness guard entirely** (same line: `and not counter_alias`) and checks only `"확진자" in summary[m.end:m.end+24]` (lines 142–145) — no source-unit `명` check, no head-noun check; (d) summary-side URL repairs are discarded (`_sm_repairs`, line 80) — `url_repair_docs` reflects source-side only, which is why all five systems show the same `["REPORT-news_r-02742-00001"]`; (e) no source-attestation for the summary-side join (regex-only, lines 28–31, 40–48); (f) the corpus wrap census scans `passage` only (line 175), so `url_wrap_docs=3` is source-side.

---

## 1. Verdict summary

| ID | Topic | rev2 position | Verdict |
|---|---|---|---|
| R1 | 084a baseline | URL-only | **agree** (conditional on spec-faithful audit + regression check) |
| R2 | 084b numeric unit | report-only | **agree** |
| R3 | 084b counter alias | off | **agree** |
| R4 | formal candidate | 2,586 provisional | **conditional** |
| R5 | 1,940 role | human exploratory, gate-ineligible | **agree** |
| R6 | human 50 | 4 arms, 2,586 decision primary | **agree** (conditional on pre-registration) |
| R7 | spec audit DoD | stronger | **conditional** (needs 4 additions) |
| R8 | test 163 | seal | **agree** |
| Q1 | measurement/equivalence separation | achieved | **agree** (with regression caveat) |
| Q2 | URL join conditions sufficient | source-attested, fine.fss. unresolved | **conditional** |
| Q3 | 1,940 = 158; exploratory vs alias-first | exploratory first | **agree** |
| Q4 | 084b report-only; qualifier in 084a? | keep qualifier out | **agree** |
| Q5 | 2,586 vs "no candidate" | 2,586 provisional | **conditional** |
| Q6 | 1,293 sensitivity arm | sufficient | **agree** |
| Q7 | human 50 design; GLM's 1,940 view | valid; quality preserved via exploratory role | **agree** (conditional) |
| Q8 | G-C5 additions/thresholds | shape right, thresholds missing | **conditional** |
| Q9 | spec-faithful audit DoD | sufficient? | **conditional** |
| Q10 | 383 flip adjudication realism | criterion | **conditional** (realistic for 084a; reframed) |
| Q11 | test 163 release conditions | sufficient, no reorder | **agree** |
| Q12 | missing from rev2 / must-fix | — | **conditional** (7 must-fix) |
| Q13 | did rev2 resolve 3-AI critiques | mostly | **conditional** (residual omissions) |
| Q14 | request fact errors | — | **agree with notes** (no material errors; 3 omissions) |

---

## 2. R1–R8 detail

### R1 — 084a baseline = URL-only → **agree** (conditional)

**Evidence.** The wrap join fixes a genuine surface-measurement artifact: 2,586's only url-type new (`02742`) exists because the source is wrapped and the summary is joined (`verifier_v2_audit.json` checkpoints `2586`, new_kinds in error analysis; golden pair in rev2 §3.1). URL wrap is rare (3/1,617 source docs), so blast radius is small. Everything else in the old "generic v2" — qualifier-drop and unit-drop acceptance — is semantic equivalence policy with real false-accept exposure (902/1,617 numeric-collision docs; all 5 excluded-pool flips are number-type). The 3-AI synthesis common conclusion (§2.1, §3.3 of the synthesis) is URL-only first; rev2 implements it. The unit clause is provably inert for selection: 1,293/2,586 reach 160 via URL alone, and 1,940 stays blocked by `04709` under the uniqueness guard (source contains both `18일` and `18명`).

**Condition.** "URL-only" must include the **stricter-direction** canonicalization with an explicit regression measurement (Headline 2); otherwise 084a is not a pure measurement fix and the expected table is one-sided.

**Next steps.**
1. Implement `eval/slot_verify_v2.py` with both-side, source-attested wrap join + strict canonicalization, and golden/negative tests from rev2 §3.3 before any re-scoring.
2. In the spec-faithful audit, report per system: fixes (v1-fail → 084a-pass) **and regressions** (v1-pass → 084a-fail) with doc IDs and clause attribution.
3. Keep `eval/slot_verify.py` byte-identical; verify by hash comparison in the audit output.

### R2 — 084b numeric unit report-only → **agree**

**Evidence.** 902/1,617 (55.8%) docs have same-value/different-unit collisions; all 5 excluded flips are plain-number flips; the audit's unit clause is the only rule that can produce them. The uniqueness guard (occurrence-count form) already blocks `04709` (`18일`+`18명` co-present). Making it selection-bearing would be outcome-informed gate tuning — exactly what the 3-AI review prohibited. Report-only preserves the information at zero selection risk.

**Next steps.**
1. Record `unit_dropped` candidates + collisions per doc in the 084b report; never auto-accept.
2. In the clause ablation, keep the `+unit` row so its (near-zero) selection effect and its flip exposure are both measured.
3. Carry the 5 known flips as the unit clause's adjudication backlog.

### R3 — 084b counter alias off → **agree**

**Evidence.** The audit's alias implementation bypasses the uniqueness guard (`and not counter_alias`, audit line 132) and uses a bare 24-char `"확진자"` window (lines 142–145), with no source-unit `명` check — the 3-AI synthesis §3.5 defects are all present in code. `04709`'s source contains both `18일` and `18명`, so a bare `18` in the summary is genuinely ambiguous; the prediction reportedly preserves `18명` twice, leaving the bare `18` of `18 확진자` as the only new (A1 synthesis §8 corrections). One document is not a policy basis. Alias stays off; it must never be used to make 1,940 eligible.

**Next steps.**
1. Keep `counter_alias: bool = False` default in the API; the alias column may be computed only as a clearly-labeled exploratory variant, never merged into the generic column (non-additivity).
2. If a future alias policy is ever pursued, pre-register it as a separate decision (closed head-noun table, source `명` attestation, entity/scope, all firings human-adjudicated) with its own evidence — not as part of D-084.

### R4 — formal candidate = 2,586 provisional → **conditional**

**Evidence.** Under 084a-expected, eligible = {pilot300, 1,293, 2,586}; max-F1 rule → 2,586 (0.6690 vs 1,293 0.6659; gap 0.003, noise; paired CI vs pilot300 includes 0). The designation is rule-based and explicitly "not promoted", which is honest. "No candidate" (Q5) would be less informative and would stall human 50's decision arm. However: eligibility rests on one repair (`02742`); quality is the worst of the three (preservation 0.4188 < pilot 0.4558 < target-implied ≈0.465; slot-free 11 of which 9 have target slots, slots/doc 4.73 vs target 5.63 — `error_analysis` and A1 synthesis §3.6); and strictness regressions (Headline 2) are unmeasured.

**Conditions.** (a) Spec-faithful audit confirms 2,586 = 160/161 under 084a with zero regressions; (b) rev2 pre-registers the no-candidate branch (Headline 4); (c) the candidate is never called better than pilot300 and never promoted.

**Next steps.**
1. Add one sentence to rev2 §5.2: "if the spec-faithful audit yields no eligible full-train checkpoint, the outcome is no candidate; pilot300 fallback and D-083 remain."
2. After the audit, re-state the eligible set and candidate with per-doc evidence (which repair fixed which ID).
3. Keep 1,293 in the report as the near-tie sensitivity comparator (0.003 gap) so the candidate's fragility is visible.

### R5 — 1,940 = human exploratory, gate-ineligible → **agree**

**Evidence.** URL-only leaves 1,940 at 158 (Headline 1: its `03978` failure is time-type; `04709` is blocked by co-present `18일`/`18명`; `04951` is genuine). Alias-first (Q3's alternative) would be outcome-driven: the alias's only val effect is exactly `04709`, the one doc standing between 1,940 and 160. 1,940's quality evidence is the best available (F1 0.6823, preservation 0.4761 ≈ target 0.465, slot-free 4) and is preserved in the exploratory role — this also honors the GLM-position from the prior round without touching the gate.

**Next steps.**
1. In the audit's `per_rule_attribution`, confirm `03978`'s old-audit flip was qualifier-clause-caused (predicted [derived]; make it a checked prediction).
2. If human 50 shows 1,940 quality dominance, route the outcome to a new pre-registered policy decision — never to a retroactive eligibility change via alias.

### R6 — human 50: 4 arms, 2,586 decision primary, 1,940 exploratory → **agree** (conditional)

**Evidence.** Matches the 3-AI common skeleton (same 50 unique val docs, blind, randomized, 2 raters, targeted+random strata separate, no pooled bootstrap, exploratory only). 2,586 is the policy-selected arm, so decision-primary is coherent; 1,293 covers the 2,586-vs-1,293 noise gap and compression sensitivity; pilot300 is the strict control. GLM's prior "1,940 quality-primary" view is operationalized as the exploratory comparator with prominence in reporting.

**Condition.** The protocol must be pre-registered (rubric, strata, primary/secondary contrasts, agreement metric, seed) before rating — currently rev2 lists it as a DoD item without content (Must-fix 7).

**Next steps.**
1. Pre-register primary contrast 2,586-vs-pilot300; secondary 2,586-vs-1,293 and 1,940-vs-2,586 (exploratory).
2. Include `04951` (genuine negative control), `04709`/`03978`/`02742` (normalization candidates), and the 2,586 slot-free docs in the targeted stratum; fix the random-stratum seed.
3. Report strata separately; two raters + arbitration; agreement on ≥ the random 20.

### R7 — spec-faithful audit DoD = stronger → **conditional**

**Evidence.** rev2's DoD (§8) covers the major 3-AI defects: separate v2 module with v1 byte-identical; URL wrap/strictness tests; 383 flip audit with no test load; 5-flip blind adjudication; side-by-side re-scoring; clause ablation (which finally executes the never-run "URL+qualifier only" row flagged in the prior synthesis §2.2); `selection_v2` with policy/spec_hash/CP95; human-50 protocol gate; seal log. Four additions are required (details in Q9/Q12): strictness-regression measurement, failure-kind classification of all residual fails, per-flip clause attribution, and a concrete INCONCLUSIVE rule.

**Next steps.**
1. Add the four items to the DoD as explicit checkboxes with acceptance criteria.
2. Add the no-candidate fallback branch (R4) to the DoD's selection_v2 item.

### R8 — test 163 sealed → **agree**

**Evidence.** A0 used test 163 in D-080; A1 has not; rev2 records both facts separately (§5.4) including corpus-wide audit exposure. The release chain (rev2 approval → spec-faithful audit → flip adjudication → selection_v2 → human 50 → candidate/hash/policy freeze → one-shot → no retuning) matches the 3-AI synthesis §3.8. Nothing in the artifacts justifies reordering; opening it now would add a second use on top of A0's, with no new information relative to the pending pipeline.

**Next steps.** Maintain the seal log with entry conditions; freeze hash of candidate + policy + verifier version before the single A1 run.

---

## 3. Q1–Q14 detail

### Q1 — Does URL-only 084a achieve the measurement/equivalence separation? → **agree**

**Evidence.** Yes, in kind: the wrap join and strict canonicalization are content-identity questions (what URL does the text actually contain), while qualifier/unit/alias are semantic-equivalence questions (what the number/time means). The old audit's `match_v2` conflated all of them (time clause lines 103–119, number clause lines 121–148); rev2 §4 strips both from selection. The 1,940 reclassification (158 under URL-only) is the concrete proof the split is now real: the old "generic" number was qualifier-clause-driven.

**Caveat.** Separation is complete only if the stricter canonicalization's match-removing effect is measured (Headline 2). Otherwise 084a is "measurement + an unmeasured tightening".

**Next steps.** (1) Regression check on val 161 + clean 1,617 (see R1). (2) Publish both directions of 084a's effect per system.

### Q2 — Are the wrap-join conditions (source-attested, fine.fss. unresolved, over-join negatives) sufficient? → **conditional**

**Evidence.** The conditions are the right list, but two are not operational: (a) "source-attested" is undefined for the summary side — it should mean: after source-side repair, the joined summary URL equals (as a full string or under strict canonicalization) a URL slot extracted from the repaired source. Without this, a summary wrap whose continuation merely looks plausible would be joined. (b) The negative tests cover sentence-word over-join and `fine.fss.`, but not **wrong-suffix join** (summary continuation token exists in the source but not as part of the source URL). Also, `fine.fss.`'s "unresolved" needs a trigger definition and a recorded outcome (it appears as a corpus wrap occurrence, so the audit regex does fire there; whether the true continuation is a URL is [unverified] here). Note the audit's regex would also join `URL._\nX` and lowercase-starting English words — the negative test set should pin all of these.

**Next steps.** (1) Write the operational attestation rule + wrong-suffix negative test before implementation. (2) Give `unresolved` a recorded field and a deterministic trigger. (3) Check `03992`'s source context locally (sandbox cannot) before finalizing tests.

### Q3 — Accept 1,940 at 158 under 084a? Exploratory vs alias-first? → **agree**

**Evidence.** Headline 1: `03978` is time-type → qualifier clause only → URL-only leaves it. The alias path would be adopted to fix exactly one document (`04709`), whose source contains both `18일` and `18명` — adopting it first would be outcome-informed policy selection, which all three prior reviewers prohibited. Exploratory-first preserves 1,940's quality evidence without touching the gate.

**Next steps.** (1) Verify the qualifier attribution for `03978` in the spec-faithful audit (it becomes a falsifiable prediction of this review). (2) Keep alias adjudication as a separate future decision.

### Q4 — 084b report-only/default off correct? Include qualifier in 084a? → **agree**

**Evidence.** Report-only is correct for all three channels (R2/R3). The qualifier specifically should stay out of 084a: it changes **no** selection outcome (1,940 would move 158→159, still < 160; 647 remains disqualified by repeated4 regardless; nothing else moves), so including it adds policy risk (7 collision docs; specificity-loss is not an identity question) with zero selection benefit. The old draft's "URL+qualifier only" row (§6.2) was never executed; the ablation DoD now covers it.

**Next steps.** (1) Keep `qualifier_dropped` as a report field with per-doc IDs. (2) In the ablation, quantify the qualifier row's selection invariance explicitly (expected: eligible set unchanged).

### Q5 — 2,586 as candidate vs "no candidate"? → **conditional**

**Evidence.** As R4. The rule-based provisional designation is more honest than an ad-hoc "no candidate" (which would itself be a judgment call made after seeing outcomes), **provided** the compression caveats ride along in the same table (preservation 0.4188, slot-free 11/9-target-omissions, CI vs pilot300 includes 0) and the no-candidate branch is pre-registered. "Eligibility ≠ superiority" must remain printed next to the candidate label.

**Next steps.** (1) Pre-register the no-candidate fallback. (2) Print strict/084a/quality metrics side-by-side wherever the candidate appears. (3) If the audit collapses the repair, report "no candidate" without re-litigating.

### Q6 — 1,293 as sensitivity arm sufficient? Reconsider as formal candidate? → **agree**

**Evidence.** 1,293 is expected 160/161 under 084a with the same URL fix and the better compression profile (preservation 0.4571 ≈ target 0.465; slot-free 8; slots/doc 5.30). Swapping the formal candidate to 1,293 now would be a post-hoc, quality-motivated gate adjustment — not permitted in this cycle. Keeping it as the named sensitivity arm in human 50 captures the information without changing the pre-registered rule (max F1 among eligible).

**Next steps.** (1) Name 2,586-vs-1,293 a pre-registered secondary contrast. (2) Document both arms' compression profiles in the human-50 protocol.

### Q7 — Human 50 design valid? How to reflect GLM's 1,940-quality view? → **agree** (conditional)

**Evidence.** The 4-arm blind design with separated decision/exploratory roles is the consensus resolution of the prior disagreement (synthesis §6: "selection과 quality를 분리"). To give 1,940's quality evidence its due weight: report its arm prominently as the quality ceiling, pre-register that a 1,940-dominant result routes to a new policy decision rather than a gate change, and put its failure docs (`04709`, `03978`) into the targeted stratum so the human data can later adjudicate the alias question on evidence.

**Next steps.** (1) Pre-registration content per R6/Must-fix 7. (2) Include material-omission and wrong-unit/qualifier rubric categories (A1 synthesis §5.2 rubric). (3) Exploratory label on every 1,940-specific analysis.

### Q8 — G-C5 additions (nonvacuous, coverage/adequacy, CP95, INCONCLUSIVE) sufficient? Thresholds? → **conditional**

**Evidence.** The shape is right and the denominators are now well-grounded (slot-level micro: pilot300 0/837, 1,940 4/860, 2,586 3/762; CP uppers 0.44%/1.19%/1.15% — all consistent with two-sided 95% CP [derived]). Doc-level 160/161 CP lower 0.9659 < 0.99 confirms "gate is a screen, not a certificate". What is missing is the **INCONCLUSIVE trigger** and the role of each new metric (gate vs report-only). Suggested pre-registration: (a) grounded 0.99 doc-level unchanged as the gate; (b) slot-level CP95 **reported**, not gated, in this cycle; (c) INCONCLUSIVE when (point passes the gate AND two-sided CP95 upper bound on the slot-level new-slot rate exceeds 1%) OR (any unresolved adjudication touches a gate-metric document); (d) nonvacuous grounded and slot-free-with-target≥3 reported beside; (e) preservation/adequacy report-only vs target-implied ≈0.465 — no new hard threshold post hoc.

**Next steps.** (1) Write the INCONCLUSIVE rule into rev2 §5.2 before selection_v2. (2) Label each G-C5 metric gate vs report-only.

### Q9 — Spec-faithful audit DoD sufficient? Missing must-fix? → **conditional**

**Evidence.** The four listed pillars (URL strictness; distinct typed-slot uniqueness; source-attested summary join; train/val+excluded-only inputs, no test load) cover the synthesis defect table §4 items 1–6, 9. Gaps: (i) distinct typed-slot uniqueness needs semantics + tests (see Must-fix 3) — "distinct typed slot" is currently one phrase without a definition; (ii) per-flip clause attribution (which clause flipped each doc) so the ablation is checkable; (iii) the alias column must be computed so it cannot contaminate the generic column (current code shares `matched_*` sets across a single pass — the non-additivity defect); (iv) strictness-regression measurement (Headline 2); (v) residual-failure kind classification (Headline 1, 647's five unknowns); (vi) previous all-clean exposure logged as history only (rev2 §6.3 has this — good).

**Next steps.** (1) Encode uniqueness semantics as tests first. (2) Restructure the matcher so each policy toggle runs in an isolated pass. (3) Emit `flip_ids` with `responsible_clause` per flip.

### Q10 — 383 flip adjudication + "false accept 0 + unresolved auto-accept 0" realistic? → **conditional**

**Evidence.** Realistic and well-aimed, with a reframe: under 084a the expected excluded-pool flip count is **0** (Headline 3 — all 5 known flips are number-type), so the criterion is cheap to meet for 084a and the 5 flips belong to 084b's evidence pile. The criterion as an acceptance bar means: any human-confirmed false accept removes/narrows the responsible clause and forces a re-run (3-AI synthesis §5.4 wording — rev2 DoD should adopt the removal clause explicitly, not just "0"). "Unresolved auto-accept 0" is a process rule (nothing unresolved may count as grounded) — realistic.

**Next steps.** (1) Pre-register "expected 0 excluded flips under URL-only". (2) Adopt "any confirmed/ambiguous false accept → clause removed/narrowed + re-run" as the written consequence. (3) Keep the 5-flip adjudication scheduled before selection_v2 (cheap; avoids ambiguity), while noting it is not 084a-blocking.

### Q11 — Test 163 release conditions sufficient? Reorder? → **agree**

**Evidence.** The chain and its recording of A0-use, audit exposure, and A1 non-use match the synthesis §3.8. Human 50 before candidate freeze before the one-shot is the right order: the freeze needs human-50's outcome to mean anything, and test 163's value depends on the freeze being single and final. No artifact suggests reordering.

**Next steps.** (1) Record the seal-log entries now (date, basis, conditions). (2) Define "retuning forbidden" as a written commitment covering gate, verifier, and policy.

### Q12 — Missing from Scope/DoD/API/implementation order? Must-fix before implementation? → **conditional**

**Evidence.** Scope exclusions are correct (no new training, no test, no human rating inside D-084, no production change). The API is close; two notes: `time_qualifier_drop`/`bare_number_unique`/`counter_alias` default `False` is right, and `SlotReportV2` should also carry `unresolved` per-item reasons (it lists `unresolved` — good) plus `flips`/`responsible_clause` at audit level. Implementation order is right; step ordering must add: hash freeze **before** re-scoring (step 2.5), and the no-candidate branch at step 6. See Must-fix list (§4).

**Next steps.** Incorporate Must-fix 1–7 before writing `slot_verify_v2.py`.

### Q13 — Did rev2 actually resolve the prior 3-AI critiques? Remaining overstatement/omission? → **conditional**

**Resolved.** 084a/084b split; URL-only baseline; unit/alias default off; alias demoted from candidate-making; all v2 numbers labeled provisional upper bounds; audit defect table carried into rev2 §1.3; DoD gains ablation + adjudication + CP; the prior synthesis's conflated "URL-only/generic" 1,940=159 is corrected to 158 (this review independently confirms 158 [derived]).

**Remaining omissions.** (a) Strictness-regression direction unmeasured/unstated (Headline 2) — the only place where rev2's framing ("measurement fix") could mislead. (b) No per-doc expected failure IDs/kinds under 084a — adding them (647: `00114`,`00818`,`01767`,`03086`,`03978` remain; 1,293: `03801` remains; 1,940: `03978`,`04709`,`04951` remain; 2,586: `04951` remains) turns the provisional table into a falsifiable prediction. (c) No pre-registered no-candidate branch. (d) The DoD's "5 flip" item does not say those flips are unit-clause-caused (084b evidence). (e) 2,586's single-repair fragility is in §11 but not linked to the candidate designation.

**Overstatement check.** None found in rev2 beyond what the provisional labels already hedge. The request's "Current state (verified)" block matches artifacts exactly.

### Q14 — Fact errors / overstatement / omission in the request? → **agree with notes**

**No material factual errors found.** Cross-checked against artifacts: strict table (all five systems), full-train run facts (2,586 steps / 4h20m18s / exit 0), pilot300 fallback and `selected_step: null`, gate arithmetic (160/161 passes, 159/161 fails), audit defect list (all six code-level defects confirmed in `runner/c5_a1_verifier_v2_audit.py`), CP figures (consistent [derived]), "02742 already grounded for 1,940" (v1_fail_ids omit it), slot-free 11 with 9 target-slot omissions (error analysis: 2 of 11 have target_slots=0).

**Notes (omissions/assumptions, not errors).**
1. The 647 expected value (156) assumes its five residual failures are not summary-side URL-wrap artifacts; their kinds are unclassified in committed artifacts [derived assumption]. Selection-invariant, but the number should be labeled as an assumption.
2. The expected table implicitly assumes zero strictness regressions (Headline 2) — should be stated.
3. "16/161 val docs share a train article prefix" — [unverified] here (no corpus); traceable to A1 synthesis (Opus/Sol) and consistently repeated; prior GLM review likewise marked it unverifiable.
4. `http://fine.fss.` context [unverified] here.

---

## 4. Must-fix (max 7, priority order)

1. **Operationalize the summary-side "source-attested" join** (joined summary URL must equal a URL slot in the repaired source, string- or strict-canonically) and add the **wrong-suffix over-join negative test**; give `unresolved` a deterministic trigger and recorded outcome (covers `fine.fss.`). [rev2 §3.1 gap]
2. **Require the spec-faithful audit to measure strictness-induced regressions** (v1-pass → 084a-fail) on val 161 and clean-1,617 targets with IDs per system, and to classify the **kinds of all residual failures** (647's `00114`/`00818`/`01767`/`03086`/`03978`; 1,293's `03801`) so the expected table becomes per-doc falsifiable. [new; not in rev2]
3. **Write the distinct typed-slot uniqueness semantics + tests before the audit**: bare summary number matches a source number+unit slot only if that value has exactly one distinct unit-type among source slots; `18일`+`18명` co-present → no auto-match; duplicate same-value-same-unit → allowed; `04951` (`2.3%`/`2.2%`) must-reject control. [rev2 §6.2 underspecified]
4. **Freeze `verifier_version` + `spec_hash` (code + spec + data manifest) before any val re-scoring**; `selection_v2.json` records the hash of the exact code that produced it. Ordering gate, not merely a field. [rev2 §6.4 lists fields without ordering]
5. **Per-flip clause attribution** in the audit output (`responsible_clause` per flip; a flip with no clause = bug), plus the pre-registration "expected 0 excluded flips under URL-only" and the written consequence "any confirmed/ambiguous false accept → clause removed/narrowed + re-run". [rev2 §3.3/§6.4 partial]
6. **Concrete INCONCLUSIVE rule before selection_v2**: point-pass + two-sided CP95 slot-level upper > 1% → INCONCLUSIVE; any unresolved adjudication touching a gate-metric document → INCONCLUSIVE; nothing unresolved may count as grounded. [rev2 §5.2 names CP95/INCONCLUSIVE without definition]
7. **Human 50 pre-registration as a blocking gate**: rubric (fabricated entity/number, wrong unit/qualifier, negation/attribution, material omission, fluency, memory utility), strata definitions, primary contrast (2,586 vs pilot300), secondary contrasts (2,586 vs 1,293; 1,940 exploratory), rater agreement metric, random-stratum seed — approved before any rating. [rev2 DoD has the item without content]

## 5. Additional experiments (max 5, estimated cost)

1. **Spec-faithful 084a audit + clause-ablation ladder** (URL / +qualifier / +unit / +alias) on val 161 + excluded 383, including the clean-1,617 regression check and per-flip attribution. Local CPU (data not in this sandbox), ~10–30 min compute; implementation 0.5–1 day. *This is the single gating item.*
2. **URL strictness exposure census**: count docs whose v1 pass depends on path/query case/comma loss (val 161, clean 1,617, excluded 383), with IDs. Same run as #1; minutes.
3. **Residual-failure kind taxonomy** for 647×5, 1,293×1 (`03801`), 1,940×3, 2,586×1 (`04951`) with source spans — ~1–2 h analyst. Feeds the falsifiable expected table and any future measurement-fix candidate.
4. **Human 50 dry run**: rubric pilot on 5–10 docs × 4 arms, 2 raters, agreement stats — ~2–3 person-hours, before the full pre-registered run.
5. **Full human 50** (after pre-registration approval): 12–20 person-hours (per A1 synthesis §9).

## 6. Fact errors / overstatement / omission (summary)

- Errors: none found. Overstatement: none beyond hedged provisionals. Omissions: strictness-regression direction; per-doc expected failure IDs/kinds (esp. 647's five unknown-kind fails); no-candidate fallback branch; unit-clause ownership of the 5 flips; single-repair fragility linked to the candidate label. See Q13/Q14.

## 7. Final recommendation

rev2 is directionally right and materially better than the draft it replaces: the measurement/equivalence split is now real rather than rhetorical (this review independently confirms that 1,940's 158 — not the prior synthesis's 159 — is the correct URL-only value, because `03978` is a time-type failure only the qualifier clause could resolve), every v2 number is labeled a pre-spec upper bound, and the DoD finally includes the ablation and adjudication the prior round demanded. The candidate/human/test architecture (2,586 provisional rule-based candidate, 1,940 exploratory, 1,293 sensitivity, pilot300 control and fallback, test 163 sealed) is coherent and consistent with the artifacts.

Implementation approval should be **conditional**, not blanket: incorporate the seven Must-fix items first, of which two are decisive — (i) measure the strictness-induced regression direction, because 084a's canonicalization can only remove matches and today nothing bounds that effect on val or clean data; and (ii) operationalize "source-attested" and distinct typed-slot uniqueness so the spec-faithful audit is testable before it runs. With those in place, run the spec-faithful audit and treat its output — not the provisional table — as the basis for selection_v2; pre-register that "no eligible checkpoint → no candidate, pilot300 remains" is an acceptable outcome. Nothing here changes D-083: `selected_step = null` and the pilot300 fallback stand regardless of what 084a finds, and no gate change, promotion, or test-163 opening is approved or proposed by this review.

---

## Appendix A — verification log

- Sync: `git fetch origin`; `git pull --ff-only origin main` → up to date; HEAD `e8b6367c1bd16b010318145587aaaedc14a77027` before/after.
- Artifacts read: `verifier_v2_audit.json` (scope, corpus counts, target_audit flips, all five checkpoint blocks), `selection.json` (gates: grounded ≥ 0.99, new-slot micro ≤ 0.01, EOS ≥ 0.95, repeated4 ≤ 0.06; all candidates ineligible), `selection_summary.json` (`selected_step: null`, fallback pilot300), `error_analysis_1940_vs_2586.json` (new_kinds, slotfree lists, deltas), `eval_step_*/eval.metrics.json`, `pilot300_val161/metrics.json`.
- Code read: `runner/c5_a1_verifier_v2_audit.py` lines 1–279 (regexes; `repair_url_wraps`; `match_v2` exact/URL/time/number clauses; alias window; corpus scan source-only; output writing), `eval/slot_verify.py` lines 1–188 (`_PATTERNS`, `_canonical` lower+comma-strip, `verify_summary`).
- Documents read in full: request (346 lines), rev2 (368), D-084 3-AI synthesis (278), A1 audit report (119), full-train report (99), A1 3-AI synthesis (318), original draft (272).
- Derived checks: CP recomputation (two-sided 95%: 0/837→0.44%, 4/860→1.19%, 3/762→1.15%, 160/161→0.9659 lower, n≥368 for 0-error); failure-kind attribution for `03978` (time) via new_kinds arithmetic; 2,586 slot-free decomposition (2 vacuous + 9 target-slot omissions); both-side wrap asymmetry mechanism for `02742`; alias-uniqueness bypass at audit line 132.
- Not verifiable in this sandbox: P0 corpus text (`data/external/` absent), `03992` wrap context, `04709`/`03801` source spans, the 5 flipped excluded pairs' text, `16/161` prefix-sharing claim. Audit not re-run (would write into the repo; data absent).