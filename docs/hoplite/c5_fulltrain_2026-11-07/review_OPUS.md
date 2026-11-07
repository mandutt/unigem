# Independent external review: C5 A1 full train and the grounded gate (Opus 5.5)

- Reviewer: Hoplite thread, model `anthropic/claude-opus-5-5`. Independent review; no subagents or other models were consulted.
- Review basis: `origin/main` HEAD **`5694cc7fbe0d371f0b4800830037fa36269e44c3`** ("docs: add full-train 3-AI review prompts and dispatch").
  `git fetch origin` and `git pull --ff-only origin main` ran with no errors ("Already up to date").
- Request reviewed in full: `reports/EXTERNAL_REVIEW_C5_A1_FULLTRAIN_2026-11-07.md` (350 lines, read in two chunks: 1–250 and 250–350).
- Mode: read-only. No training or generation ran, test 163 was not opened or evaluated, and no P1 data was used. This file is the only write.

## 0. What I verified myself and what I could not

| Item | How | Result |
|---|---|---|
| Strict D-083 selection | `selection.json`, `selection_summary.json` | `full_train_selected_step: null`; fallback pilot300 (F1 0.657580, grounded 1.0, new 0, EOS 1.0, rep4 0.05535). **Confirmed.** |
| Per-step grounded failures | Recounted from each `eval_step_*/eval.jsonl` | 647: 6 (`00114, 00818, 01767, 02742, 03086, 03978`), 1,293: 2 (`02742, 03801`), 1,940: 3 (`03978, 04709, 04951`), 2,586: 2 (`02742, 04951`). Slot-free: 2 / 8 / 4 / 11. **Confirmed.** |
| pilot300 val161 | `pilot300_val161/predictions.jsonl` + `metrics.json` | 161/161 grounded, 837 summary slots, gen_len 248.3. **Confirmed.** (Note: `pilot300_lr2e4_prefix/eval.jsonl` covers only 5 docs.) |
| Paired bootstrap (2,000 resamples, seed 42) | Recomputed from per-doc `char_f1` | 1,940−p300 +0.024698 [+0.0120, +0.0371] 99/61; 2,586−p300 +0.011402 [−0.0004, +0.0228] 92/69; 1,940−2,586 +0.013297 [+0.0011, +0.0248] 86/75. **Matches the request exactly.** |
| Slot-free target-slot breakdown at 2,586 | `error_analysis_1940_vs_2586.json` | target slots 0:2, 1:3, 3–4:6. **Confirmed.** |
| 1,940→2,586 drift | Same JSON `delta_1940_to_2586` | −98 slots, 73/51/37 loss/gain/same docs, 8 newly slot-free, 1 recovered (`00467`). **Confirmed.** |
| Verifier behaviour | `eval/slot_verify.py` | URL regex `https?://[^\s<>"')\]]+` stops at whitespace/newline. Time regex captures an optional `오전/오후` qualifier as part of the slot. Number regex attaches an optional unit (`명`, `%`, …). `_canonical` already strips trailing `.,;:!?()[]{}<>"'` for every kind, URLs included. |
| `04951` is a genuine source-external number | Prediction text only | Both checkpoints write "JP모건은 … 경제성장률이 2.3%에서 2.2%로 하락할 것으로 전망". **I could not check this against the source passage:** `data/external/f5_pairs_v3_clean.jsonl` is not in git (`data/README.md`: raw data is never committed). The verifier extracted `3%` and `2%` from the source, which suggests the source has a different figure. |
| Leakage of the `04951` figure through sibling chunks | `splits.json` article prefixes | `REPORT-news_r-04951` has **no** train siblings. The figure most likely comes from pretraining or from a different train article on the same event. That is unverified because train targets are not in the repo. |

**Strict D-083 results** (sections 2 and 3 of the request, and this table) and **verifier-normalization candidates** (v2, not adjudicated) are kept separate throughout this review. Nothing here implies that a gate change has been approved.

---

## 1. Decisions D1–D5

### D1. Verifier v2 normalization: **conditional**

**Evidence**
- All three candidates are artefacts of `slot_verify.py`'s surface matching, not of model invention:
  - `02742`: the source URL `http://coronamap.\n site` is cut at the newline, and `_canonical` then strips the trailing `.`, giving `http://coronamap`. The URL also appears as *missing* in the 2,586 record (`missing_slots: url "http://coronamap."`), so the bug distorts both `new` and `slot_preservation`.
  - `03978`: the source slot is `오전 9시 30분`. The prediction says "16일 오전 10시쯤 … 9시 30분쯤 현장에 도착", which is unambiguous in context. The time regex folds the qualifier into the canonical, so `9시30분` ≠ `오전9시30분`.
  - `04709`: the prediction has `18명` **twice** ("가운데 18명이 …", "등 18명이"), and both match the source. Only the third mention, "18 확진자", gives a bare `18`. A number the same summary already grounds is being flagged as invented.
- The same patterns show up beyond the two checkpoints the request analysed. `02742` (URL) also fails at 647 and 1,293, and `03978` (bare `9시 30분`) also fails at 647. 1,293's other failure involves `www.shucle.com` (identifier kind), and 647's include date-like and time-like slots (`1981년 1월 20일`, `2020년 5월 25일`, `1시 20분`). I could not classify these without the source text.
- Dangerous generalisations must stay out. Unit-agnostic matching would let `18%` match `18명`. Qualifier-agnostic matching in the other direction would let a summary *add* `오후` that is not in the source.

**Allowed normalizations (each one-directional and narrow):**
1. **URL soft-wrap join**: in source *and* summary, before extraction, join a URL fragment ending in `.`, `/`, `-` or `_` with the next token when (a) the whitespace between them contains at least one newline and (b) the continuation matches `[A-Za-z0-9][A-Za-z0-9.\-/_%?=&#]*`. Hangul or sentence text never joins. No other URL fuzzing (no scheme or `www.` stripping, no prefix match).
2. **Time qualifier drop**: a summary time *without* `오전/오후` counts as grounded if the source has the same `H시[M분]` with any qualifier. Record it as `qualifier_dropped`, not `new`. A summary time *with* a qualifier must match exactly. No 12h↔24h conversion (`오후 3시` ≠ `15시`) in v2.
3. **Bare-number unit drop**: a summary number with **no unit** counts as grounded if the source has a number slot with the identical numeric value (after comma removal, exact decimals), with or without a unit. Record it as `unit_dropped`. A summary number **with** a unit must match value and unit exactly. No rounding, no `만`/`억` ↔ digit expansion, no `%` ↔ `퍼센트`.
4. Trailing-punctuation trimming needs no change, because `_canonical` already does it for every kind. The request lists it as new work; it is not.

**Next steps**
1. Implement v2 as a *new* function or version flag (`verify_summary_v2`, `verifier_version` in every metrics file). Leave v1 output untouched and report both side by side.
2. Before any re-score of val161, measure the v2 false-accept rate on an independent P0 audit set that is not val or test. The 383 pairs excluded from v3 (2,000 → 1,617) are the natural pool. Human-check every pair whose verdict flips from v1-reject to v2-accept.
3. Add unit tests for each rule and each forbidden generalisation (`18%`≠`18명`, added `오후` stays new, a newline followed by Hangul does not join).

### D2. Candidate: **conditional** (strict answer pilot300, exploratory answer 1,940)

**Evidence:** under D-083 the only eligible model is pilot300 (`selected_step: null`). Under D-083's own wording ("full train 결과가 부적합하면 제품 승격 금지"), neither 1,940 nor 2,586 can be promoted. 1,940 is a near miss (one doc beyond the ≤1-failure tolerance), and its F1 gain over pilot300 is the only one whose CI excludes zero (+0.0247 [+0.0120, +0.0371]).

**Next steps**
1. Record pilot300 as the strict D-083 outcome and do not edit `selection_summary.json`.
2. Put 1,940 forward as an *exploratory near-miss* for human review only, with no product promotion. Use 2,586 as the contrast arm.
3. Make any later switch to 1,940 depend on a new decision (D-084) plus human-50 evidence, never on v2 alone.

### D3. Human 50: **agree, before test**

**Evidence:** D-083 already says "사람 50건은 test 전". The two open questions (whether the normalization candidates are harmless, and whether 2,586's slot-free outputs are real omissions) need human judgement that no automated metric here provides.

**Next steps:** see Q9 for the sample design. Pre-register the rubric and the decision rule before rating. Rate pilot300, 1,940 and 2,586 blind on the same 50 docs.

### D4. Test 163: **defer (keep sealed)**

**Evidence:** D-083 allows "test 163은 A1 최종 후보 1개에만 1회". No final candidate exists yet: strict gives pilot300, while the exploratory candidate depends on D-084 and the human review. Opening test now would spend the one shot on an unfrozen choice. A0 already used test 163 (D-080). That does not contaminate A1, but A0-vs-A1 test comparisons should be labelled as A0 having seen test once.

**Next steps**
1. Keep test sealed until (a) D-084 is registered, (b) human 50 is done, and (c) a single A1 adapter path and SHA256 are frozen in `docs/decisions.md`.
2. Pre-register the test report format (strict v1 *and* v2 numbers, Clopper-Pearson bounds) before opening.
3. Do not use test for B-family work (already in D-083).

### D5. Next experiment: **conditional**, ordered A → B → E → C → D

**Evidence:** A (verifier audit) needs no generation; it re-scores stored predictions. B (human 50) is the only way to settle coverage versus faithfulness. E (gate redesign) should be folded into D-084 together with A. C (seed 43) matters because the F1 path 0.6699 → 0.6659 → 0.6823 → 0.6690 is non-monotonic at about ±0.01, about the size of the 1,940−2,586 gap. D (over-compression fix) needs a design, and its benefit is still a hypothesis.

**Next steps:** see Q11 and section 3.

---

## 2. Questions Q1–Q12

### Q1. Join URL line breaks? Is `http://coronamap.\n site` the same as `http://coronamap.site`? **Agree (narrow rule only)**

- Evidence: the source split is a typesetting artefact. The regex stops at `\s`, and canonicalisation strips the dangling `.`, so the verifier turns one URL into a truncated one and then reports the correct, complete URL as invented. The same record shows `http://coronamap` as *missing*. The case recurs at 647, 1,293 and 2,586.
- Next steps: (1) implement the newline-only join from D1 rule 1. (2) Count how many source passages in train, val and the 383 excluded pairs contain a URL followed by a newline, to size the impact. (3) Re-score all five models, not only 2,586.

### Q2. Is `오전 9시 30분` the same slot as `9시 30분`? **Conditional: "qualifier_dropped", not "new"**

- Evidence: dropping a qualifier loses information but invents none. The verifier's `new` list is meant to catch invented content. In `03978` the context ("오전 10시쯤 … 9시 30분쯤") makes the time unambiguous. Elsewhere a bare `9시` can be ambiguous, which is a faithfulness issue but a different one.
- Next steps: (1) treat it as grounded for the hallucination gate, but count `qualifier_dropped` per model and report it. (2) Keep *added* qualifiers as `new`. (3) Include `03978` in human 50 to confirm raters see no factual error.

### Q3. Is `18명` the same slot as `18 확진자`? **Conditional: bare numbers only, exact value**

- Evidence: in `04709` the same summary already contains `18명` twice, grounded. The extractor misses "18 확진자" only because `확진자` is not in the unit list. Unit-agnostic matching in general is unsafe (`18%` vs `18명`). The source also has `18일`, so the bare-number rule will sometimes match a different referent. That is acceptable for a *new-slot* (invention) check but should be visible.
- Ignore the unit only when the summary number has none. Never substitute one unit for another. Exact numeric equality only.
- Next steps: (1) implement D1 rule 3 with a `unit_dropped` counter. (2) Spot-check every `unit_dropped` match in the audit set. (3) Leave the unit list unchanged in v2, because adding `확진자`-style nouns would change extraction everywhere.

### Q4. Pre-register as D-084, or forbid as post hoc? **Conditional: D-084 is legitimate only as a disclosed, outcome-informed, forward-looking gate**

- Evidence: these rules were found by looking at val161 failures, so this is not pre-registration in the strict sense, and val161 has already driven selection, including the choice of pilot300 itself through the pilot and prompt variants. Fixing a measurement instrument with a documented bug is legitimate. Then calling the re-scored val result a "pass" that overrides D-083 is not.
- Under v2, both 1,940 and 2,586 would sit at exactly 160/161 = 0.99379, a one-document margin over 0.99. That makes the outcome extremely sensitive to rule details, which is another reason to fix the rules before re-scoring.
- D-084 should say:
  1. Verifier v2 spec (D1 rules 1–3), frozen as code plus tests plus SHA **before** re-scoring.
  2. Validation on an independent audit set (D1 step 2), with an acceptance criterion written in advance, e.g. zero human-confirmed false accepts.
  3. Re-adjudication of **all** candidates under v2 (pilot300, 647, 1,293, 1,940, 2,586), with v1 numbers kept alongside.
  4. Gate additions so the change is not a pure loosening: non-vacuous grounded, and a coverage/omission guard (Q7).
  5. Results labelled "val-reused / exploratory". Confirmation comes only from human 50 plus the single test-163 run.
  6. The D-083 record stays as is: "no eligible full-train checkpoint".
- Next steps: (1) draft D-084 in `docs/decisions.md` with the items above. (2) Freeze the v2 code SHA in the decision. (3) Only then run the re-score.

### Q5. Keep the pilot300 fallback, or send 1,940 to human review? **Conditional: both**

- Evidence: pilot300 is the only model that passes strict D-083, and that stands. Sending a near-miss to *human review* is not selection or promotion, and D-083 does not forbid it. 1,940 has a CI-significant F1 gain, the second-best slot preservation (0.4761, behind 647's 0.4873), only 4 slot-free outputs, and exactly one candidate genuine invention.
- Next steps: (1) record pilot300 as the strict fallback. (2) Label 1,940 "exploratory near-miss, human review only" in the status doc. (3) If 1,940 later becomes the A1 candidate, let that come only from D-084 plus human 50.

### Q6. Primary for human 50: 1,940 or 2,586? **1,940 primary, 2,586 secondary/contrast**

- Evidence:
  - F1: 1,940 > 2,586 by +0.0133 [+0.0011, +0.0248], significant, though only barely.
  - Slot preservation: 0.4761 vs 0.4188.
  - Slot-free: 4 vs 11, and 6 of the 11 at 2,586 drop 3–4 target slots.
  - Both have repeated4 under 0.06 and EOS 161/161.
  - Hallucinations are similar: 4 vs 3 new slots, both containing `04951`.
  - 2,586 is better only on repetition (0.0445) and length, and the length gain comes with information loss.
  - Without length control, char F1 also favours shorter outputs less than it may appear: pilot300 averages 248 tokens against 199.5/190.3. Interpret F1 alongside length.
- Next steps: (1) rate pilot300, 1,940 and 2,586 on all 50 docs, blind and in randomised order, so 1,940 is judged against both. (2) Report omission scores separately from factuality scores. (3) Pre-register "1,940 must be non-inferior to pilot300 on factuality".

### Q7. Is it right that slot-free outputs don't fail grounded? Extend G-C5 with slot preservation? **Conditional: keep grounded pure, add a separate coverage guard**

- Evidence: `grounded` is a hallucination check, and folding coverage into it would mix two failure modes. Vacuous passes do inflate it, though:
  - non-vacuous grounded: 1,940 is 154/157 (0.981) and 2,586 is 148/150 (0.987).
  - 9 of 2,586's 11 slot-free docs drop target slots.
  - G-C5 in `docs/gates.md` already says coverage is "참고 지표로 별도 보고". Promoting it to a gate is a gate change and needs D-084.
- Raw preservation numbers (about 0.42–0.49) are low by construction, because summaries should drop slots. A preservation threshold therefore needs an anchor: pilot300 (0.4558) or the target's own preservation against the source. The latter is not in the artefacts and should be computed.
- Proposed additions (thresholds to be fixed *before* seeing new data):
  1. Report non-vacuous grounded alongside grounded.
  2. Count slot-free outputs whose target has ≥3 slots, with a cap anchored on pilot300 (whose 6 slot-free docs should be broken down the same way).
  3. Slot preservation as a non-inferiority guard against pilot300 (e.g. no worse than pilot300 − 0.03), not an absolute floor.
- Next steps: (1) compute the target's slot preservation against the source as a ceiling reference. (2) Break down pilot300's 6 slot-free docs by target slots. (3) Write the guard into D-084, not into D-083.

### Q8. Was 2 epochs right? Would 1 epoch or a 1,940 stop be better? **Conditional: 2 epochs with checkpoints was a sound design; the late drift is plausible but under-evidenced**

- Evidence:
  - Checkpointing at 647/1,293/1,940/2,586 is what exposed the drift, so the design did its job.
  - LR is **constant 2e-4 with no warmup or decay** (`runner/c5_a1_lora.py`: plain `AdamW`, no scheduler), so late checkpoints are not annealed, and drift under a constant LR is unsurprising.
  - F1 is non-monotonic (0.6699 / 0.6659 / 0.6823 / 0.6690) on one seed. The "peak at 1,940" may partly be noise.
  - The slot trend is more consistent: 5.45 → 5.30 → 5.34 → 4.73, with preservation 0.487 → 0.457 → 0.476 → 0.419. That points to real compression only at the end.
- Next steps: (1) run seed 43 with the identical config and the same checkpoints to see whether the 1,940 > 2,586 ordering holds. (2) In a later, separately approved run, consider linear decay to 0 over the same 2 epochs, which is the standard fix for late drift under a constant LR. (3) Do not retrofit a 1,940 early-stop rule onto this run's selection.

### Q9. Human-50 sample design: **specific allocation below**

Rate the **same 50 docs** for pilot300, 1,940 and 2,586 (150 outputs), blind, with order randomised per doc.

| Stratum | n | Source |
|---|---:|---|
| All grounded failures at 1,940/2,586 | 4 | `03978, 04709, 04951, 02742` (`04951` covers both) |
| Slot-free union at 1,940 ∪ 2,586 | 12 | the 11 at 2,586 plus `00467` (slot-free at 1,940 only) |
| Largest slot losses 1,940→2,586 not already included | 5 | from `top_slot_losses` (`01082, 04855, 03991, 00476, 05207` …) |
| Lowest F1 decile at 1,940, not already included | 6 | from `eval_step_1940/eval.jsonl` |
| Longest outputs, not already included | 3 | longest `gen_len` across the three models |
| **Simple random** from the remainder (seed fixed in advance) | 20 | gives an unbiased estimate |

- The targeted 30 are diagnostic and the random 20 are inferential. Report them separately and never pool them into one rate.
- Rubric per output: (a) intrinsic factual error, (b) extrinsic or unsupported content (e.g. `04951`), (c) key-fact omission (0–2), (d) fluency (0–2), (e) usefulness as a memory entry (0–2). For normalization cases also ask whether the dropped qualifier or unit changes meaning.
- Use two raters on at least the random 20, and report agreement.
- Next steps: (1) freeze the doc list and seed in a file before rating. (2) Pre-register the decision rule, e.g. 1,940 has no more factual errors than pilot300 on the random 20 and fewer omissions than 2,586. (3) Build the rating sheet from val only, no test docs.

### Q10. Open test 163 now? **Disagree, keep it sealed**

- Evidence: there is no frozen candidate, D-084 does not exist yet, human 50 has not run, and D-083 allows one use only.
- Next steps: open it only after D-084, human 50 and a frozen adapter SHA. Run once, report v1 and v2 numbers with Clopper-Pearson bounds, and do not iterate afterwards.

### Q11. Priority of next experiments: **A > B > E > C > D**

| Item | Why this position | Cost estimate |
|---|---|---|
| A. Verifier v2 audit + re-adjudication | Removes known instrument bugs. CPU re-scoring of stored predictions plus a human check of flipped verdicts on the audit set | about 0.5–1 day, no GPU |
| B. Human 50 on pilot300/1,940/2,586 | The only evidence on omission vs faithfulness | 150 judgements, about 4–6 h per rater |
| E. Gate redesign (in D-084) | Non-vacuous grounded, coverage guard, CP bounds. Paperwork that must come before re-scoring | about 0.5 day |
| C. Seed 43 full train | Tests whether the checkpoint ordering holds | about 4 h 20 min train plus 4 × val161 eval |
| D. Over-compression fix (LR decay / length or slot auxiliary) | Promising, but needs its own approval and design | about 1 day design plus about 4–5 h per run |

Next steps: run A and E together, then B, then C. Keep D behind a new decision.

### Q12. Factual errors, exaggerations and omissions in the request: **conditional, mostly accurate with the corrections below**

Factual errors:
1. §3.1 `03978` "missing `오전9시30분` 포함 **8개**": the JSON has **7** missing (source 15, preservation 0.5333, so 8 *preserved*).
2. §3.1 `04709` "missing `18명` 포함 **18개**": the JSON has **15** missing, and **`18명` is preserved, not missing**. The prediction contains `18명` twice. This strengthens the unit-drop argument.
3. §5.2 Q1 lists "trailing punctuation" as a v2 normalization, but `_canonical` already strips trailing punctuation for every kind.

Exaggerations or framing:

4. "3 of 5 failures are normalization candidates" covers only 1,940 and 2,586. The same patterns occur at 647 (`02742`, `03978`) and 1,293 (`02742`), and 1,293's `03801` and 647's other four failures are not analysed. Re-adjudication must cover all candidates and pilot300.
5. `04951` is called hallucination ("원문에 없는 금리·성장률 수치"). It is unsupported by the source, and correctly a grounded failure, but it reads like a real-world fact (JP Morgan's forecast revision), not a fabrication. That matters for the human rubric (extrinsic vs intrinsic). I could not inspect the source, and the article has no train siblings, so where the figure came from is unverified.
6. "9/11 target slot 누락" is relative to the *reference summary*, not the source. Call it "slots the reference kept".

Omissions:

7. `docs/gates.md` G-C5 is defined at **slot level** (new slots ≤1%, minimum ≥300 slots, Clopper-Pearson, INCONCLUSIVE when underpowered). D-083 uses a doc-level 0.99. The relationship is never discussed. Under the CP rule, 1,940's new-slot micro (4/860) has a 95% upper bound of **1.19%**, so it is not demonstrably ≤1% even before the grounded gate.
8. **Val is chunk-split**: 16/161 val docs share an article prefix with train docs. This does not affect the grounded failures discussed (none have train siblings) but slightly inflates absolute F1.
9. Val161 has been reused for prompt, LR and pilot choices (`pilot100`, `prompt_bare`, `prompt_korean`, `pilot300_*`). pilot300 itself is val-selected, so all val comparisons carry selection bias.
10. LR is constant (no schedule). This is relevant to the drift interpretation and not mentioned.
11. Length confound: pilot300's mean generation length is 248.3 against 199.5/190.3. Bag-of-characters F1 is length-sensitive, and no target-length reference is reported.

Next steps: (1) fix items 1–3 in the error-analysis report. (2) Add a §3 table covering 647 and 1,293. (3) Add the G-C5 slot-level CP view.

---

## 3. Statistical note on the grounded ≥0.99 gate (n=161)

- At n=161, ≥0.99 means **at most 1 failing doc** (160/161 = 0.9938 passes, 159/161 = 0.9876 fails).
- Pass probability under a true per-doc failure rate p (binomial, ≤1 failure): p=0.5% → **0.81**, p=1% → **0.52**, p=1.86% → **0.20**. The gate barely tells a 1% model from a 2% model.
- 95% Clopper-Pearson upper bounds:

  | Case | Upper bound |
  |---|---:|
  | pilot300, 0/161 docs | 2.27% |
  | 1,940, 3/161 docs | 5.35% |
  | 2,586, 2/161 docs | 4.42% |
  | Hypothetical v2 result, 1/161 | 3.41% |
  | 1,940, 4/860 slots | 1.19% |
  | 2,586, 3/762 slots | 1.15% |
  | v2 1,940, 1/860 slots | 0.65% |

- So the ≥0.99 point estimate is **appropriate as a threshold. Do not lower it.** It is **underpowered as evidence**: even pilot300 does not *demonstrate* a doc-level rate below 1%.
- Recommendation for D-084: keep ≥0.99, add CP bounds and an INCONCLUSIVE outcome as `gates.md` already requires, and widen the grounding evaluation. Grounding needs no reference summary, so it can run on extra P0 passages from outside train, val and test (article-deduplicated against test by ID only, without reading test content), which tightens the bounds without touching test.

---

## 4. Must-fix (priority order, at most 7)

1. **Keep the strict D-083 record intact**: `selected_step = null`, pilot300 fallback. Every later document should show v1 and v2 side by side and never replace v1.
2. **Implement verifier v2 as a versioned, unit-tested function** with the three narrow, one-directional rules in D1. Forbidden generalisations get tests too.
3. **Validate v2 on an independent audit set** (e.g. the 383 excluded pairs) before re-scoring val. Human-check every verdict flip.
4. **Register D-084 before re-scoring**: frozen v2 SHA, all-candidate re-adjudication (pilot300, 647, 1,293, 1,940, 2,586), non-vacuous grounded, a coverage guard anchored on pilot300, CP bounds and INCONCLUSIVE, and an "exploratory / val-reused" label.
5. **Correct the request and error-analysis facts**: 7 and 15 missing (not 8 and 18), `18명` preserved, trailing punctuation already handled, 647/1,293 failures added.
6. **Run human 50 (pilot300/1,940/2,586, blind) with a pre-registered rubric and decision rule** before any test use.
7. **Keep test 163 sealed** until D-084, human 50 and a frozen adapter SHA. Then run once.

## 5. Additional experiments (at most 5, with cost)

1. **Verifier v2 audit**: re-score stored predictions and human-check flips on the audit set. About 0.5–1 day CPU plus human time, no training.
2. **Human 50**: 150 blind judgements, about 4–6 h per rater, two raters on the random 20.
3. **Grounding-only extended eval** on extra non-test P0 passages (target ≥600 docs, or slots ≥600 per gates.md) for pilot300 and 1,940 to tighten CP bounds. Generation only, about 1.5–3 h per model at current val speed (no training).
4. **Seed 43 full train**, identical config and checkpoints. About 4 h 20 min plus 4 × val161 eval.
5. **Constant-LR vs linear-decay A/B** (same 2 epochs, needs a separate approval) as the first over-compression fix, before any auxiliary length/slot loss. About 4–5 h per run.

## 6. Final recommendation

Strict D-083 says no full-train checkpoint qualifies, so pilot300 remains the fallback. That outcome should be recorded unchanged. The error analysis is still persuasive that most of the gap is a measurement problem. Of the five 1,940/2,586 failures, three come from verifier surface-matching bugs (soft-wrapped URL, dropped `오전`, and a bare `18` beside two grounded `18명`), and only `04951` is source-unsupported content. Fixing the instrument is legitimate. Using the fixed instrument to flip a val result that has already been seen into a pass is not. The right path is D-084: a narrow, versioned, independently audited verifier v2, applied to every candidate, with grounded kept at ≥0.99, plus a coverage guard and CP bounds so the new gate is stricter where the old one was blind (slot-free outputs).

For human review, 1,940 should be the primary exploratory candidate: best F1 (CI-significant over pilot300 and over 2,586), better slot preservation, and 4 rather than 11 slot-free outputs. Use 2,586 as the over-compression contrast and pilot300 as the strict baseline, all rated blind on the same 50 docs. Test 163 stays sealed until D-084 is registered, human 50 is done and one adapter is frozen. Seed 43 and an LR-decay run come after, since a single seed with ±0.01 checkpoint noise cannot yet establish that 1,940 is a real optimum.