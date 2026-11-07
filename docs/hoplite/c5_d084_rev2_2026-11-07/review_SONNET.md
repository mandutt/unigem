# Independent review — C5 A1, D-084 rev2 (reviewer: Sonnet 5.5)

- Review basis: `origin/main` HEAD `e8b6367c1bd16b010318145587aaaedc14a77027` ("docs: add D-084 rev2 review prompts and dispatch").
- Sync: `git fetch origin` OK; `git pull --ff-only origin main` → "Already up to date".
- Read in full: `reports/EXTERNAL_REVIEW_C5_D084_REV2_2026-11-07.md` (346 lines), `docs/D-084_verifier_v2_rev2_2026-11-07.md` (368 lines), `reports/C5_D084_3AI_REVIEW_SYNTHESIS_2026-11-07.md` (278 lines). I also read `runner/c5_a1_verifier_v2_audit.py`, `eval/slot_verify.py`, `reports/C5_A1_verifier_v2_audit_2026-11-07.md`, `reports/provenance/C5_a1/full_2ep/{verifier_v2_audit,selection_summary,error_analysis_1940_vs_2586}.json`, the per-checkpoint `eval.jsonl` files, the pilot300 predictions, D-083/D-080 rows in `docs/decisions.md`, and my own earlier review (`docs/hoplite/c5_d084_2026-11-07/review_SONNET.md`).
- Not done: no training or generation; test 163 not opened; no P1; no subagents or other models; no repository file modified other than this report.
- **Limit on verification.** `data/external/f5_pairs_v3*.jsonl` is not in the repo. I could not re-run the audit or read the source text of `02742`, `03801`, `03992`, `04709`, `04909` or the 5 excluded flips. I did run read-only, in-memory probes: v1 `extract_slots`/`verify_summary` on synthetic strings, a paired bootstrap on the per-document `char_f1` stored in the committed `eval.jsonl` files, and Clopper-Pearson (CP) arithmetic. Tags: **[verified]** = read from an artifact or reproduced; **[derived]** = my inference from artifacts; **[unverified]** = could not be checked.
- **Three result classes are kept separate throughout.** *D-083 strict* (artifact, binding): `selected_step = null`, pilot300 fallback, no product approval. *084a provisional* (hypothetical, hand-derived, not yet run by a spec-faithful matcher). *084b report-only* (never selection-bearing). Nothing here approves any gate change; D-083 is not overwritten; test 163 stays sealed; no alias is proposed to make 1,940 eligible.

---

## 0. Headline findings

1. **rev2 separates 084a from 084b well on paper, but three seams still leak.**
   - The DoD and the audit section mix 084a and 084b obligations. The "5 excluded flips" (`v1_new` = 2020, 2021, 404, 20, 5000/200) are plain numbers. They can only have come from the unit clause (084b), yet they are the headline adjudication item in the 084a DoD. **[verified]** from `verifier_v2_audit.json` and the audit code.
   - The `grounded` field of `SlotReportV2` is policy-dependent but nothing stops `selection_v2` from reading a 084b-enabled value. There is no hard assertion that `policy == 084a-only` when selection runs.
   - Qualifier, unit and alias flags default to False in `VerifierV2Policy`, which is good, but the report fields (`qualifier_dropped`, `unit_dropped`, …) must be computed in a separate pass and must never change `grounded`.
2. **084a's whole effect on selection is one validation document.** **[verified]** v1 failure IDs: 1,293 = {02742, 03801}; 2,586 = {02742, 04951}; 1,940 = {03978, 04709, 04951}; the `02742` URL wrap appears in the pilot300, 647, 1,293, 1,940, 2,586 `url_repair_docs`. **[derived]** Fixing `02742` moves 1,293 and 2,586 from 159 to 160 and nothing else. So 2,586's eligibility rests on a single document, it has zero spare margin, and its one remaining failure (`04951`, `2.3%`/`2.2%`) is a real source-unsupported number.
3. **A qualifier clause would not change the outcome, so excluding it from 084a costs nothing.** **[derived]** `03978` (오전 dropped) fails only in 647 and 1,940. 647 stays ineligible on repeated4 (0.0684 > 0.06). 1,940 would reach 159/161 and still fail on `04709` + `04951`. Eligible set and winner are identical with or without the qualifier.
4. **`CP95 + INCONCLUSIVE` is under-specified and can silently void the selection rule.** **[derived]** Doc-level CP lower bound at 161/161 is 0.9773 (<0.99); at 160/161 it is 0.9659. So at doc level *every* system, including pilot300, is INCONCLUSIVE at 0.99. rev2 §5.2 does not say whether INCONCLUSIVE removes eligibility. See Q8.
5. **v1's URL extractor absorbs trailing Hangul particles, and rev2 does not mention URL boundaries.** **[verified]** probe on v1: `"문의는 https://coronamap.site에서 확인"` yields one URL slot `https://coronamap.site에서`. That is a measurement defect of the same class as the wrap, and it is not covered by "scheme/host lowercase, path/query preserved, trailing sentence punctuation removed".
6. **The strictness half of 084a can push results in the bad direction, and the expected table only looks one way.** The provisional table was derived from existing failure IDs, so it cannot show a currently-passing document that becomes a failure under case/comma-preserving URL matching. pilot300 (the D-083 fallback) has a URL repair in `02742` and must be re-scored.
7. **`03801` (1,293, `identifier` kind) is still uncharacterized.** I flagged it in my previous review; rev2 only lists it as "residual". 1,293 is a named sensitivity arm, so its status matters.
8. **No pre-registered decision rule connects human 50 to anything.** "2,586 decision primary" does not name the comparator, the metric, the threshold or the action on failure.

---

## 1. Compact verdict table

| ID | Verdict | One-line answer |
|---|---|---|
| R1 | agree (conditional) | URL-only 084a is the right baseline, with the boundary and source-side join fixes in Must-fix 1–2. |
| R2 | agree | Unit stays report-only; make "no effect on `grounded`" machine-enforced. |
| R3 | agree | Alias stays off; no firing may touch selection. |
| R4 | conditional | 2,586 is the only 084a-eligible max-F1 checkpoint, but call it "formal candidate for human review" and make "no candidate" the explicit default if human 50 fails. |
| R5 | agree | 1,940 = gate-ineligible under 084a, human exploratory comparator. |
| R6 | conditional | 4 arms on the same 50 are fine; name the decision contrast (2,586 vs pilot300) and pre-register the action. |
| R7 | conditional | Stronger than before, but split into a 084a DoD and a 084b DoD and fix the mismatches in §3 Q9. |
| R8 | agree | Keep test 163 sealed; add the conditions in Q11. |
| Q1 | agree (conditional) | Structure is right; enforcement and DoD split are needed. |
| Q2 | conditional | Source-attested join is circular for the source side as written; add recall scan and Hangul boundary. |
| Q3 | agree | Accept 158/161; do not settle alias policy first. |
| Q4 | agree | Report-only/default off; qualifier stays out of 084a (outcome-neutral). |
| Q5 | conditional | Keep 2,586 as the formal candidate with an honest label; do not report "no candidate" yet, but pre-commit to it. |
| Q6 | agree (conditional) | 1,293 as sensitivity arm is enough; not a formal candidate; characterize `03801`. |
| Q7 | conditional | Valid design; the decision contrast and the action rule are missing. |
| Q8 | conditional | Define PASS/FAIL/INCONCLUSIVE semantics before running; slot-level CP is the only version that can PASS at n=161. |
| Q9 | conditional | Missing: URL boundary, bidirectional flips, clean-target regression check, source-side join rule, percent-hex/trailing-slash policy. |
| Q10 | conditional | Realistic for 084a (few firings); the 5-flip item belongs to 084b. |
| Q11 | conditional | Add a pre-registered action rule, a freeze manifest and a "no candidate" exit. Order is otherwise fine. |
| Q12 | conditional | Seven Must-fix items below. |
| Q13 | conditional | Most of the prior findings are resolved; four remain (see Q13). |
| Q14 | — | Errors, overstatements and omissions listed in Q14. |

---

## 2. R1–R8

### R1 — 084a baseline: URL-only / URL+qualifier / generic
- **Verdict:** agree (conditional).
- **Evidence:**
  - URL wrap and URL case/comma strictness are the only two items that are measurement defects of the extractor, not choices about what counts as "equivalent". **[verified]** v1 `_canonical` lowercases the whole string and drops commas: `https://example.com/Case?key=A,B` vs `.../case?key=ab` gives `new = ()` in my probe. v1's URL regex also stops at whitespace, which truncates `http://coronamap.\nsite` to `http://coronamap` (`02742`).
  - A qualifier clause is outcome-neutral (Headline 3), so there is no selection reason to add it, and a principled reason not to: dropping 오전 is an information loss, not a measurement error.
  - The unit clause is not needed for any eligibility decision (1,293 and 2,586 reach 160/161 by URL alone; 1,940 stays blocked on `04709` + `04951`).
- **Next steps:**
  1. Approve 084a only after the URL boundary rule (Hangul particles, closing brackets/quotes) is added to the spec; this is the same class of defect.
  2. Pin the 084a expected table (as written in rev2 §3.4) in a commit **before** the spec-faithful run, so deviations are visible.
  3. Re-score all five systems in both directions (new failures as well as new passes).

### R2 — 084b numeric unit
- **Verdict:** agree.
- **Evidence:** 902/1,617 clean documents have a numeric unit collision (audit JSON `numeric_unit_collision_docs`). rev2 §4.2 forbids automatic grounded credit. The 5 excluded flips are all plain numbers, so the unit clause is where false accepts would come from.
- **Next steps:**
  1. Keep `unit_dropped` as candidates only and compute it in a pass that cannot write to `grounded`.
  2. Add a unit test that asserts `grounded` is identical with and without the 084b report pass.
  3. Do not spend adjudication budget on the 5 flips as part of the 084a approval path (see Q10).

### R3 — 084b counter alias
- **Verdict:** agree.
- **Evidence:** the audit alias keys on the string `확진자` within 24 characters of the summary number, does not require the source unit to be `명`, and bypasses the uniqueness guard (`runner/c5_a1_verifier_v2_audit.py` lines 132–148). rev2 §4.3 correctly forbids using it as a production rule.
- **Next steps:**
  1. Keep it off. Do not implement it in `eval/slot_verify_v2.py` in this round.
  2. If it is ever reconsidered, it needs its own decision ID, a closed head-noun table, `명`-only constraint and adjudication of every firing across all five systems and the corpus, before any selection re-run.

### R4 — formal candidate: 2,586 / 1,293 / defer
- **Verdict:** conditional.
- **Evidence:**
  - Under 084a (provisional) the eligible set is {pilot300, 1,293, 2,586}; max F1 picks 2,586 (0.668982 vs 0.665946). **[derived]**
  - 2,586 is not shown to be better than anything: paired F1 vs pilot300 +0.0114 with a bootstrap 95% interval about [−0.0001, +0.0231]; vs 1,293 +0.0030, interval about [−0.0093, +0.0154] (my bootstrap on per-doc `char_f1`; the committed 2,586−pilot300 interval in the request is [−0.000398, +0.023058], consistent). **[verified]**
  - Over-compression is real: summary slots 762 vs 837 (pilot300), 854 (1,293), 860 (1,940); slot-free documents 11 vs 6/8/4; preservation 0.4188. 9 of the 11 slot-free documents had ≥1 target slot. **[verified]** from `error_analysis_1940_vs_2586.json`. Some of the grounded gain is vacuous: nonvacuous grounded for 2,586 is 148/150 strict, **[derived]** 149/150 after the `02742` fix.
  - "No candidate" would also be defensible, but the rule is pre-registered (D-083: max F1 among gate passers). Re-labeling the outcome after seeing it would be a different kind of post-hoc change than fixing a measurement defect.
- **Next steps:**
  1. Record 2,586 as "formal candidate for human review only; not promoted; not shown better than pilot300". This is already what rev2 says; keep the wording.
  2. Pre-commit that if human 50 fails the pre-registered criteria (Q7), the project reports **no A1 candidate** and test 163 is not opened for A1.
  3. Add "one-document margin" to the limitations: eligibility flips if `02742` is judged differently.

### R5 — 1,940 role
- **Verdict:** agree.
- **Evidence:** 1,940 has the best F1 (0.682278) and preservation (0.4761) and its paired F1 advantage over 2,586 is +0.0133, interval [+0.0012, +0.0249] (request §1.3); I reproduce a +0.0163 mean advantage over 1,293 with interval about [+0.0044, +0.0284]. But it has 158/161 under 084a (failures `03978`, `04709`, `04951`) and 4 new slots in 860 (two-sided CP upper 1.187%, above 1%). **[derived]** The only route to eligibility is `04709` plus `03978` rules that are outside 084a. That route is closed by the task constraints.
- **Next steps:**
  1. Keep it as an exploratory arm and include `03978`, `04709` and `04951` as targeted documents to learn whether the verifier rejections were benign (this informs a future 084b, never this selection).
  2. State in the record that human preference for 1,940 cannot rescue it under D-083/084a.

### R6 — human 50
- **Verdict:** conditional.
- **Evidence:** 4 arms × 50 = 200 summaries is feasible. Blinding is imperfect: mean generated length is 248 (pilot300) vs 190–200 (full-train checkpoints) **[verified]**, so raters may identify pilot300 by length. The request itself notes 16/161 val documents share a train article prefix and val was reused for prompt/LR/pilot selection.
- **Next steps:**
  1. Name the decision contrast (2,586 vs pilot300), the metric and the action rule before rating (Q7).
  2. Exclude or separately flag the 16 prefix-sharing documents in the random stratum.
  3. Randomize arm order per document; hide length cues as far as possible; record whether raters guessed the arm.

### R7 — spec-faithful audit DoD
- **Verdict:** conditional.
- **Evidence:** rev2 §6 and §8 are a clear improvement (distinct typed slots, test not loaded, source-attested join, manifest hashes). But the DoD is a single list for two specs, one clause (the 5 flips) is attached to the wrong spec, and items relevant to 084a are missing (Q9).
- **Next steps:** split the DoD; add the Q9 items; make the "train/val + excluded only" input restriction a code-level allow-list.

### R8 — test 163
- **Verdict:** agree.
- **Evidence:** A0 used it in D-080 (char F1 0.6072); A1 has not; D-083 says test is for the single final A1 candidate, once; no candidate is frozen; human 50 has not run.
- **Next steps:** see Q11.

---

## 3. Q1–Q14

### Q1 — is the measurement/equivalence separation achieved?
- **Verdict:** agree (conditional).
- **Evidence:**
  - Structure: 084a (URL wrap, URL strictness) vs 084b (qualifier, unit, alias), defaults all False (`VerifierV2Policy`), selection "084b not used", separate report fields. **[verified]** rev2 §3–§5, §7.
  - Leaks: (i) no enforcement that `selection_v2` runs with the 084a-only policy; (ii) the DoD's 5-flip item belongs to 084b; (iii) §6.2 puts uniqueness and the `04951` negative control in the 084a audit although 084a has no unit rule; (iv) the URL boundary (Hangul particles) is missing, so 084a is not yet a complete measurement fix.
- **Next steps:**
  1. `selection_v2.json` writer asserts `policy == {url_wrap_join: True, url_strict_canonical: True, others: False}` and records `spec_hash`; otherwise it refuses to write.
  2. Name the 084b report fields with a `report_` prefix and compute them in a second function that takes `grounded` as read-only input.
  3. Split the DoD (R7).

### Q2 — URL wrap source-attestation, `fine.fss.`, negative tests
- **Verdict:** conditional.
- **Evidence:**
  - As written, "the next token must be source-attested as a URL continuation" works for the **summary** side (the summary URL is allowed to join only if the joined string is also present in the source). On the **source** side it is circular: nothing external attests the source's own wrap. rev2 says the continuation must "fit URL grammar", is not Hangul and is not a sentence-initial word, which is a heuristic, not an attestation. State it as two rules.
  - The audit's wrap regex (`URL_WRAP`) requires the line to end in one of `. / _ -` and the next token to start with `[a-z0-9]`. A wrap after `?`, `=`, `&`, `#`, `%` or in the middle of a token is not detected, so recall is unknown. The corpus count of 3 wrap documents (2 coronamap + `fine.fss.`) is the count of what this regex found, not of all wraps.
  - `fine.fss.` ends with a dot at a line break, which is exactly the shape of a sentence-final period before a new sentence, or of a wrapped `fine.fss.or.kr`. **[unverified]** I could not read the source. "Unresolved" is a safe default but needs a defined scoring rule: no credit, no penalty beyond v1 behaviour, logged. A broken continuation that becomes a spurious `identifier` slot (e.g. a wrapped `or.kr`) also affects `slot_preservation`; that is a side effect of the join to report.
  - Test list in rev2 is good but thin on real data: 02742 and 04909 are both coronamap wraps (04909 breaks after `/`, a different terminator). Only 02742 is named as a golden case.
- **Next steps:**
  1. Specify the source-side rule explicitly (character-class continuation, ASCII-only, directly after line break, no blank line, no Hangul, previous token a URL ending in `. / - _`) and the summary-side rule (join only if the joined URL string occurs in the source after source-side joining).
  2. Run a recall scan on train/val source text (not test) for any newline within or adjacent to a URL, with terminators other than `. / - _`, and report counts. If it finds new shapes, add them as unresolved/negative cases, not as new joins.
  3. Golden tests: 02742 (source wrapped, 1,940 wrapped, 2,586 joined), 04909 (break after `/`), 03992 (`fine.fss.`, unresolved), over-join negatives such as `...사이트 http://a.com/.\nthe next` and Hangul-initial continuation, plus a URL-with-Hangul-particle case.

### Q3 — accept 1,940 at 158/161; human exploratory vs alias-first
- **Verdict:** agree.
- **Evidence:** the 084a table gives 158/161 for 1,940: `03978` (`9시30분` vs `오전 9시 30분`), `04709` (`18 확진자` vs `18명`), `04951` (two source-unsupported percentages). Resolving `03978` and `04709` needs 084b rules; resolving `04951` is impossible without accepting a fabricated number. Settling an alias policy first, in a process that has already seen which checkpoint it would rescue, is the post-hoc ordering the task forbids. Note also that the audit's explanation of `04709` ("source has `18일` and `18명`") is **[unverified]**: the guard counts occurrences of value `18` with a unit, so repeated `18명` alone could trigger it (`dict.fromkeys` over position-bearing `Slot` objects never collapses duplicates).
- **Next steps:**
  1. Keep 1,940 as an exploratory arm. Do not discuss an alias in the 084a record except as a "not adopted" item.
  2. Have two humans read `04709`'s source sentences and record whether `18 확진자` and `18명` are the same group and scope. This is evidence for a future 084b, not for selection.

### Q4 — 084b report-only; qualifier in 084a?
- **Verdict:** agree. Qualifier belongs in 084b.
- **Evidence:** outcome-neutrality (Headline 3). In addition, v1 counts the dropped 오전 as `new` (`9시30분`) **and** the source `오전9시30분` as `missing`; the second half is a real information loss that `slot_preservation` already measures, so accepting a qualifier drop would hide a true omission under a grounded pass. rev2 §4.1's unresolved rule for AM/PM collisions is sound (7/1,617 collision documents).
- **Next steps:**
  1. Keep `qualifier_dropped` report-only and make it add to, not remove from, the missing-slot count in `slot_preservation`.
  2. Report which of the five systems have any `qualifier_dropped` event so the reader can see it is selection-irrelevant.

### Q5 — 2,586 as formal candidate vs "no candidate"
- **Verdict:** conditional.
- **Evidence:** see R4. The pre-registered rule produces 2,586 mechanically. The concerns are interpretive: one-document margin, one real fabricated number (`04951`), preservation 0.4188 vs the target-implied about 0.465 (as stated in the request), slot-free 11, F1 interval vs pilot300 touching zero. Calling it "no candidate" now would pre-judge the human review; calling it a "candidate" without an exit would invite promotion by momentum.
- **Next steps:**
  1. Keep the label "formal candidate for human review; not promoted".
  2. Write the "no candidate" exit into the human-50 protocol (Q7) and the test-163 release conditions (Q11).

### Q6 — 1,293 as sensitivity arm vs formal candidate
- **Verdict:** agree (conditional).
- **Evidence:** 1,293 is eligible under 084a provisional (160/161) and is less compressed than 2,586 (preservation 0.4571 vs 0.4188, slot-free 8 vs 11, summary slots 854 vs 762). Its F1 deficit is 0.003 with an interval centered near zero, so the max-F1 rule picks 2,586 on noise. But the rule was pre-registered and tie-breaking by "earlier checkpoint" only applies to exact ties. Its residual failure `03801` (identifier) is **uncharacterized** and its eligibility rests on it.
- **Next steps:**
  1. Keep 1,293 as the sensitivity arm. Do not re-nominate it.
  2. Read `03801` (source vs summary identifier, case, separators) and classify it as surface artifact / genuine / unresolved before rev2 is approved.
  3. Report the 2,586 − 1,293 paired F1 interval next to the candidate statement.

### Q7 — human 50: 4 arms, 2,586 decision primary, 1,940 exploratory
- **Verdict:** conditional.
- **Evidence:** design elements are sound (same 50, blind, randomized, two raters, strata reported separately, exploratory). What is missing: (i) "2,586 decision primary" does not state the comparator; the incumbent and fallback is pilot300, so the only decision-relevant contrast is **2,586 vs pilot300**; (ii) no metric (pairwise preference? unsupported-content count? omission rating?); (iii) no threshold or action; (iv) 50 paired documents only resolve large effects, so an "inconclusive" outcome is likely and must have a default; (v) my earlier position was "pre-specify two primary contrasts, 2,586 vs 1,940 and 2,586 vs pilot300"; the request's §2.3 summarizes Sonnet as "2,586 decision primary", which is a simplification. I now support a single decision contrast (2,586 vs pilot300) and treat 2,586 vs 1,940 as a named exploratory contrast, to avoid multiplicity.
- **Next steps:**
  1. Pre-register: decision contrast 2,586 vs pilot300 on (a) count of documents with unsupported/extrinsic content and (b) omission of key facts, with discordant-pair counts and a sign-test style summary; define "non-inferior in unsupported content, not worse in omission beyond X discordant documents" before rating. Inconclusive ⇒ pilot300 remains fallback, no A1 candidate, test not opened for A1.
  2. Stratify ~30 random + ~20 targeted (`04951`, `04709`, `03978`, `02742`, `03801`, 2,586 slot-free documents with target slots ≥1). Report strata separately.
  3. Double-rate all 50 (200 summaries is manageable) or at least 20, report agreement, and have a third rater arbitrate disagreements on the decision metric.

### Q8 — G-C5 additions: nonvacuous, coverage/adequacy, CP95, INCONCLUSIVE
- **Verdict:** conditional.
- **Evidence:**
  - Doc-level: 161/161 gives CP lower 0.9773, 160/161 gives 0.9659, 159/161 gives 0.9558 (two-sided 95%, my computation). None reaches 0.99, so "INCONCLUSIVE if lower bound < 0.99" labels all five systems INCONCLUSIVE, pilot300 included. **[derived]**
  - Slot-level new-slot micro, two-sided 95% CP upper bounds: pilot300 0/837 → 0.440%; 1,293 084a (assumed 1 new/854) → 0.651%; 2,586 084a (assumed 2 new/763) → 0.944%; 1,940 4/860 → 1.187%. **[derived]** These denominators come from `summary_slot_count` in `eval.jsonl`; the 084a counts are assumptions until the spec-faithful run. Slot-level CP is the only version under which a system can PASS at n = 161 documents. It also keeps 2,586 eligible only narrowly: 3 new slots in 763 would give about 1.15%.
  - Coverage/adequacy has no pre-registered threshold. Adding one now would be outcome-informed.
- **Next steps:**
  1. State, before running: eligibility is the D-083 point-estimate gate (grounded ≥0.99 doc-level, new-slot micro ≤0.01, EOS, repeated4). CP95 is reported as a label: doc-level CP is "screen, not certificate"; slot-level CP upper vs 1% is reported with PASS / INCONCLUSIVE. INCONCLUSIVE does **not** remove eligibility, otherwise the selection rule is vacuous.
  2. Report nonvacuous grounded with its own denominator (150 for 2,586, 157 for 1,940) and the equivalence "≤1 failure" for n ≤ 199.
  3. Keep coverage/adequacy as report-only until after human 50; do not add a hard threshold in this round.

### Q9 — spec-faithful audit DoD
- **Verdict:** conditional.
- **Evidence:** present in rev2: URL strictness, distinct typed-slot uniqueness, source-attested summary join, train/val + excluded-only inputs with manifest. Missing or mismatched:
  1. **URL boundary.** v1 includes Hangul in URL slots (probe above), so `https://a.com/x에서` ≠ `https://a.com/x`. Not in rev2.
  2. **Bidirectional flips.** The audit reported only v1-ungrounded → v2-grounded flips and found v1/v2 differences of 0 on the 1,617 clean targets (vacuous, because clean targets are grounded-by-construction under v1; this is rev2's own limitation). Under case/comma-preserving strictness, clean targets can **newly fail**. That is the non-vacuous test: re-score the train/val clean targets (not test) with 084a and list every new failure.
  3. **Percent-escape and trailing-slash policy.** "Preserve escape" would treat `%2F` and `%2f` as different although RFC-equivalent; `https://x.com/` vs `https://x.com` is unspecified (04909 has a trailing `/`).
  4. **Wrong-spec items.** Uniqueness, `18일`/`18명` and the `04951` negative control are 084b/negative-control material; keep them but under a 084b DoD. The 5 excluded flips belong there too.
  5. **Reproducibility.** The data files are not in the repo; the audit cannot be re-run by a reviewer. Commit a manifest (file hashes, row counts, id lists) and the per-document result JSON for all five systems.
  6. **Non-vacuity of the positive path.** Require that the join fires on the known documents (02742 in source and in 1,940's summary; 04909) so a no-op implementation cannot pass.
- **Next steps:** add 1–6 to the DoD; code the input allow-list (train/val/excluded ids only) with a runtime assertion that no test id is read.

### Q10 — 383 flip adjudication, 5 flips, blind two-rater, "false accept 0 + unresolved auto-accept 0"
- **Verdict:** conditional.
- **Evidence:** the 5 flips (`00291-00002`, `01844-00001`, `03253-00001`, `04791-00001`, `05019-00001`) came from the generic matcher; their `v1_new` values are plain numbers, so only the unit clause explains them. **[derived]** Under 084a, the number of flips in the 383 pool should be near zero (URL clause only), so adjudication of the 5 does not bear on 084a. The excluded pool is also not representative of model output (it is the v1-rejected target pool), and 5/383 is a flip rate, not a false-accept rate. "False accept 0 + unresolved auto-accept 0" is realistic for 084a because the firings are few; it is not a realistic acceptance criterion for 084b at 902 collision documents.
- **Next steps:**
  1. For 084a, adjudicate **every** URL-clause firing (both directions) across train/val/excluded and the five systems' val predictions. The expected count is single digits.
  2. For 084b, treat the 5 flips and any other unit-clause firings as report-only evidence, double-rated with arbitration; no pass/fail acceptance for selection.
  3. Raters see source span and summary span only, not rule name or label.

### Q11 — test-163 release conditions; order D-084 rev2 → audit → human 50 → freeze
- **Verdict:** conditional.
- **Evidence:** the order is right: measurement first, then selection_v2, then human, then freeze. The gaps are the rules between steps. A0 used the test set (D-080), the corpus-wide audit loaded clean source/target text including test, and A1 has not used it; rev2 records all three.
- **Next steps:**
  1. Add the human-50 action rule (Q7) as an explicit release condition, including the "no candidate" exit that leaves test sealed.
  2. Freeze manifest: adapter hash, 084a `spec_hash`, `verifier_version`, decoding parameters, human-50 result file hash, and the one-shot command.
  3. Maintain the test use-log; forbid any post-test re-tuning of verifier, gate or checkpoint; state that a test result cannot revise D-083 or 084a.

### Q12 — Scope/DoD/API/order gaps; Must-fix before implementation
- **Verdict:** conditional.
- **Evidence:** see §4 (Must-fix list). The API is reasonable. Issues: no policy assertion in selection; `SlotReportV2.grounded` is ambiguous (which policy?); there is no field distinguishing doc-level and slot-level denominators (rev2 §5.2 asks for them, §7 does not list them); the implementation order puts rev2 approval first but does not freeze the expected table or the spec hash before step 5.
- **Next steps:** Must-fix 1–7 below.

### Q13 — did rev2 resolve the previous 3-AI findings?
- **Verdict:** conditional.
- **Evidence:** resolved: URL-only baseline; 084a/084b split; default-off alias; candidate vs eligibility separation; 1,940 not an alias candidate; 158/161 for 1,940 stated explicitly; 02742 golden pair; `fine.fss.` unresolved; test sealed; all v2 numbers marked provisional; audit restricted to train/val + excluded.
- Remaining: (i) `03801` still uncharacterized; (ii) `CP95 + INCONCLUSIVE` still has no semantics; (iii) 5-flip DoD attached to the wrong clause; (iv) 1,940 qualifies at 158 only because the table is hand-derived: the 647 value (156) assumes `00818` is not fixed by URL, which I could not verify (**[unverified]**; the audit's generic run fixes `00818` and `03978` for 647, but nothing says which clause); it does not affect selection because 647 fails repeated4, but it should be marked "derived, unrun" in the table; (v) "prior synthesis table" row for 1,940 says 159/161 under "URL-only/generic" while rev2 says 158/161; rev2 is the correct URL-only number, the old row is a generic-with-unit number, so the earlier document should not be quoted without that caveat.
- **Next steps:** fix (i)–(iii) before approval; mark the 647 cell as derived.

### Q14 — errors, overstatements, omissions in the request
1. §3.3 and rev2 §3.4 present the 084a expected values as "expected" for five systems; none was produced by a run. The 1,293/1,940/2,586 values follow from failure IDs **[derived]**; the 647 value (156) is **[unverified]**. Label the column "derived, not run".
2. §2.3 describes Sonnet as "2,586 decision primary"; my previous review proposed two pre-specified contrasts and 1,940 as co-primary human-review arm. The synthesis §6 itself says "co-primary/exploratory" for Sonnet. Minor misattribution.
3. §0 item 3 and the table in §1.2 are strict; I confirmed the committed numbers (grounded, preservation, EOS, repeated4, new-slot counts) against `selection_summary.json` and `eval.jsonl`. No discrepancy found. The pilot300 "slot preservation 0.45583" is not in `selection_summary.json`; **[unverified]**.
4. §4.2 "902/1,617 numeric unit collision; 5 excluded flips" sits under 084b, and rev2's DoD attaches the flips to 084a. Inconsistent.
5. §9 "2,586 slot-free 11, 9 are target slot omission" is **[verified]** (11 slot-free; target slots = 0 for 2, ≥1 for 9).
6. Omission: URL boundary (Hangul particles); percent-escape/trailing-slash policy; recall of the wrap regex.
7. Omission: no pre-registered action rule for human 50; no semantics for INCONCLUSIVE.
8. Omission: `03801` not characterized; the claim "1,293 sensitivity comparator" depends on it.
9. Omission: the one-document dependence of 2,586's eligibility is stated only indirectly ("02742 resolved").
10. Omission: data files are not in the repo, so claims about specific documents cannot be re-verified by a reviewer; the reproduction commands assume a local Windows `.venv`.
11. Overstatement risk: "max F1 expected 2,586 (0.6690)" reads as a result; it is a consequence of an unrun spec.

---

## 4. Must-fix (priority order)

1. **Specify the URL boundary and source-side join rule.** Hangul particles/closing characters after a URL; ASCII-only continuation; separate source-side and summary-side rules; percent-hex case; trailing-slash policy; scoring of `unresolved` (no credit, v1 behaviour, logged). *Why:* v1 absorbs `에서` into the slot; the "source-attested" wording is circular on the source side.
2. **Re-score in both directions and pin the expectation first.** Commit the rev2 expected table as the pre-registration, then run the spec-faithful 084a on all five systems and on train/val clean targets; list every new failure as well as every new pass; confirm pilot300 stays 161/161 or record the consequence (D-083 fallback remains by decision, not by re-score).
3. **Define PASS/FAIL/INCONCLUSIVE.** Eligibility stays on the D-083 point-estimate gate; CP95 and INCONCLUSIVE are labels; INCONCLUSIVE does not remove eligibility; report both doc-level and slot-level denominators.
4. **Split the DoD into 084a and 084b.** Move the 5 flips, `18일`/`18명` uniqueness and the alias to 084b. Add non-vacuity checks to 084a (the join fires on 02742 source and 1,940 summary, and on 04909).
5. **Machine-enforce the separation.** `selection_v2` refuses to write unless the policy is exactly 084a-only; `report_*` fields are computed read-only; a unit test asserts `grounded` is unchanged when the 084b pass runs.
6. **Pre-register the human-50 decision rule.** Contrast (2,586 vs pilot300), metrics (unsupported content, omission), discordant-pair summary, default action on inconclusive (no A1 candidate, pilot300 fallback, test sealed); 2,586 vs 1,940 as named exploratory; exclude/flag the 16 prefix-sharing documents.
7. **Characterize the residual failures that carry eligibility.** `03801` (1,293), `04951` (both), and `04709`'s true cause (distinct vs repeated `18명`), classified by two readers before approval; commit data manifests and per-document result JSON so the audit can be reproduced without the local data files.

---

## 5. Additional experiments (max 5)

| # | Experiment | Purpose | Cost |
|---|---|---|---|
| E1 | Spec-faithful 084a re-score of 5 systems (val) + train/val clean targets + excluded 383, both flip directions, no test ids | Replace the derived table with a run | CPU, minutes; about 1–2 h implementation |
| E2 | URL recall scan on train/val/excluded sources: any newline in or next to a URL, any terminator; Hangul-suffix URL count | Measure wrap/boundary recall; confirm 3-document wrap count is not a regex artifact | CPU, minutes |
| E3 | Two-reader characterization of `03801`, `04709`, `04951`, `03978`, `02742`, and the 647 residuals (`00114`, `01767`, `03086`) | Decide whether eligibility-carrying failures are artifacts or genuine | about 1–2 rater-hours |
| E4 | Human 50 with the pre-registered rule (4 arms, 200 summaries, blind, 2 raters) | Only experiment that speaks to quality vs pilot300; exploratory | about 6–10 rater-hours |
| E5 | Ablation table URL / +qualifier / +unit / +alias on the five systems, each clause executed (the earlier "URL+qualifier only" row was derived, never run) | Show that 084b clauses are selection-irrelevant and attribute each changed document | CPU, minutes after E1 |

Deferred, not recommended now: seed 43, compression arm, any training. Do not use P1 or test 163 for any of the above.

---

## 6. Final recommendation

D-083 strict stands: `selected_step = null`, pilot300 fallback, no product approval. rev2 is a materially better draft than the first D-084: it has the right split, the right defaults, and it keeps 1,940 out of the eligible set. I would approve it for **implementation of 084a only** (module, tests, spec-faithful re-score), not as a decision, after Must-fix 1–5, which are small and mechanical. The numeric consequence of 084a is a single-document fix (`02742`) that makes 1,293 and 2,586 eligible; 2,586 then wins on a 0.003 F1 margin. That is an honest mechanical result, but it is not evidence that 2,586 is a good adapter.

Treat 2,586 as a formal candidate for human review, with a pre-committed "no A1 candidate" exit if human 50 does not show it at least non-inferior to pilot300 on unsupported content and omission. Keep 1,940 as the exploratory arm that tells us what the verifier is rejecting, and keep 084b strictly report-only. Do not open test 163 until the action rule, freeze manifest and one-shot protocol exist and the human review has actually favored a single candidate. If it has not, the correct final statement is: no A1 candidate, pilot300 remains the fallback, and the 1,940-versus-2,586 question goes to a seed-43 run rather than to a verifier change.