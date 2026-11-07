# Independent review — C5 A1, verifier v2, D-084 (reviewer: Sonnet 5.5)

- Review basis: `origin/main` HEAD `fc31b0719f3cd0ad1a9c18b326baf7426c12103e` ("docs: add D-084 review prompts with Sonnet 5.5 high").
- Sync: `git fetch origin` OK; `git pull --ff-only origin main` → "Already up to date". Nothing was modified except this file.
- Read in full: `reports/EXTERNAL_REVIEW_C5_D084_2026-11-07.md` (all 446 lines), `docs/D-084_verifier_v2_draft_2026-11-07.md`, `reports/C5_A1_verifier_v2_audit_2026-11-07.md`, `reports/provenance/C5_a1/full_2ep/{verifier_v2_audit,selection_summary}.json`, `eval/slot_verify.py` (v1), `runner/c5_a1_verifier_v2_audit.py`, `reports/provenance/C5_clean/target_slot_audit.json`, the C5_A1 error-analysis and 3-AI synthesis (targeted greps), and one eval row.
- Not done: no training, generation, or test 163 access; no subagents or other models; no P1.
- **Limit on verification:** `data/external/f5_pairs_v3*.jsonl` is not in the repo or sandbox (the audit runs locally on Windows `.venv/Scripts`). I could not re-run the audit or inspect the source text for `04709`, `03801`, `03992`, or the 5 flipped excluded pairs. Statements about those documents come from the audit JSON and the audit code, not from the raw text. Items I derived myself are marked **[derived]**. Anything I could not check is marked **[unverified]**.
- **Strict vs hypothetical.** Every "v2" number below is a hypothetical, audit-matcher result. It is not D-083, not production, and not an approved gate. D-083 strict stands: `selected_step = null`, pilot300 fallback, not product approval. Nothing in this report approves a gate change.

---

## 0. Headline findings

1. **Under every policy that has no unit alias, the max-F1 eligible candidate is 2,586.** 1,940 only wins under the alias. **[derived]** From the fail IDs in the audit JSON:

   | policy (reviewer ladder) | pilot300 | 647 | 1,293 | 1,940 | 2,586 |
   |---|---:|---:|---:|---:|---:|
   | v1 strict (D-083) | 161 | 155 | 159 | 158 | 159 |
   | URL wrap only **[derived]** | 161 | ≈156 | 160 | 158 | 160 |
   | URL + qualifier (audit "generic" minus unit clause) **[derived]** | 161 | ≈158 | 160 | 159 | 160 |
   | generic v2 (audit, artifact) | 161 | 158 | 160 | 159 | 160 |
   | generic + counter alias (audit, artifact) | 161 | 158 | 160 | **160** | 160 |

   - 647 is ineligible under every row because repeated4 is 0.0684 > 0.06.
   - 1,940's three v1 failures are `03978` (qualifier), `04709` (bare 18) and `04951` (genuine). Only the alias removes `04709`.
   - 2,586 is eligible under every row except strict v1. 1,940 is eligible only in the alias row.
2. **The generic unit clause appears inert for every selection-relevant outcome.** **[derived]**
   - 1,293 and 2,586 reach 160/161 through the URL fix alone.
   - 1,940 is still blocked at `04709` under the generic guard.
   - So the unit clause buys nothing for selection. It carries the whole risk: 902/1,617 collision documents, and all 5 excluded-pool flips. Those 5 `v1_new` values (2020, 2021, 404, 20, 5000/200) are plain numbers, so only the unit clause can have produced them.
   - The audit never ran a "no unit" variant (see §3 Q14), so this should be confirmed by an ablation.
3. **The audit matcher does not match the D-084 spec.** The audit numbers are provisional until it is re-run with a spec-faithful matcher. Details are in Q12 and Q14.
   - The URL path/query case/comma strictness is not implemented. `extract_slots`/`_canonical` still lowercase and comma-strip URLs.
   - The uniqueness guard counts occurrences, not distinct unit slots.
   - The alias is far looser than described.
   - The summary-side URL join is not source-attested.
4. **The eligible set is knife-edge.** The ≥0.99 gate on 161 documents means "≤1 failure". One document (`04709`) flips 1,940. 161 documents cannot certify ≥0.99. A 0-failure Clopper-Pearson (CP) lower bound only reaches 0.99 at n ≥ 368; pilot300's 161/161 gives lower 0.9773. **[derived]**
5. **Eligibility is not superiority.** Under generic v2, 2,586 would formally be selected over pilot300. Its paired F1 CI against pilot300 includes 0 ([−0.0004, +0.0231]). Its slot preservation is below pilot300 (0.4188 vs 0.4558) and it has more slot-free documents (11 vs 6). The 2,586-vs-1,293 F1 gap is 0.003, which is noise-level.

---

## 1. Verdict table (compact)

| ID | Verdict | One-line answer |
|---|---|---|
| D4-1 | **disagree** (as drafted) / conditional | Unit rule must not be selection-bearing. Report `unit_dropped` as a side channel only. Selection baseline = URL (+ qualifier). |
| D4-2 | conditional | If a non-alias baseline is used, 2,586 is the formal max-F1 eligible candidate. It is not shown better than pilot300, and 1,293 differs by noise. |
| D4-3 | disagree | Do not name 1,940 an "alias candidate". Alias is not independently justified. |
| D4-4 | conditional | Add nonvacuous (co-reported) and CP/INCONCLUSIVE. Coverage/adequacy is report-only until human 50. No new hard thresholds after outcomes. |
| D4-5 | conditional | Treat the 5 flips as adjudication-needed. Use a clause-level removal rule, not "false accept 0 of 5". |
| D4-6 | agree | Fix URL case/comma now, as a stricter-direction measurement change. Audit historical v1 false accepts alongside. |
| D5-1 | conditional | No single primary. Blind arms pilot300, 1,940, 2,586 (1,293 optional). Pre-specify the contrasts. |
| D5-2 | agree | Keep test 163 sealed. |
| D5-3 | conditional | First: spec-faithful v2 + clause ablation + adjudication (CPU only). Then human 50. Seed 43 later. Compression arm: defer. |
| D5-4 | conditional | Approvable only as a labeled exploratory, outcome-informed protocol. Split into 084a (measurement) and 084b (equivalence). |
| Q1 | conditional | Only URL wrap + URL strictness is a "measurement fix". Qualifier is a narrow equivalence. Unit is not baseline. |
| Q2 | disagree (automatic) / conditional (human) | The alias is a per-case human adjudication, outside the gate, and the audit's implementation is overbroad. |
| Q3 | conditional | Call them adjudication-needed flips. Blind two-rater protocol. Any confirmed false accept removes or narrows the clause. |
| Q4 | conditional | Approvable as exploratory. Keep D-083 files immutable and print strict beside v2. Don't discard v2 wholesale (URL fix is legitimate). |
| Q5 | conditional | Formal candidate per rule = 2,586. 1,940 stays a co-primary human-review arm. Don't relabel it a candidate. |
| Q6 | disagree (now) | No independent justification yet. See conditions under which it could become one. |
| Q7 | conditional | Blind, randomized, stratified; pilot300 as control; 4 arms if rater budget allows, else drop 1,293. |
| Q8 | conditional | Nonvacuous: yes, same 0.99. CP + INCONCLUSIVE: yes. Coverage/adequacy: report-only. |
| Q9 | agree | Keep the gate as a screening rule with CP/INCONCLUSIVE. Enlarge the sample only via P0 unseen sources (not test 163, not P1). |
| Q10 | agree | Do not open now. Explicit release conditions and use-log below. |
| Q11 | agree | Fix in v2 now, plus a small separate audit of v1 history. |
| Q12 | conditional | Draft is directionally sound but needs seven must-fixes. |
| Q13 | agree | Separate "gate eligibility" from "human review inclusion". |
| Q14 | — | Eleven errors/overstatements/omissions listed in §3. |

---

## 2. Item-by-item (D4-1 … D5-4)

### D4-1 — unit policy
- **Verdict:** disagree with generic uniqueness as a selection-bearing baseline; conditional agree as a report-only side channel.
- **Evidence:**
  - Audit §4.5/§1: 902/1,617 documents (55.8%) have the same numeric value under different units. The request itself says "unit을 전면 무시하면 광범위한 false accept".
  - The only target-side evidence on this clause is 5 flips on the excluded pool, all plain numbers. So those flips came from the unit clause.
  - The clause moves no selection outcome. 1,293 and 2,586 pass on URL alone, and 1,940 is still blocked at `04709` under the generic guard **[derived]**.
  - The uniqueness guard is a weak false-accept control. It only checks that the *source* has the value once with a unit. It does not check that the *summary's* bare number refers to that source quantity. A hallucinated "18" is accepted whenever the source has a lone `18%`.
  - Clean targets contain only verbatim-canonical numbers (`target_slot_audit.json`: new = 0, preserved 10,174/10,174). So the model was trained on targets that never drop units. Relaxing the gate for unit-drop changes the contract between training data and the gate.
- **Next steps:**
  1. Define the selection baseline as 084a (URL wrap + URL strictness) plus, optionally, the narrow qualifier clause. Emit `unit_dropped` events as a non-gating column.
  2. Produce the clause-ablation table (URL / +qualifier / +unit / +alias) on val for all 5 systems and on the 383 pool. Show the unit clause's marginal effect, expected to be zero for eligibility.
  3. If the unit clause stays at all, require the summary's following context to be consistent. Do not rely on source uniqueness alone.

### D4-2 — candidate if generic
- **Verdict:** conditional.
- **Evidence:**
  - 2,586: F1 0.6690, 160/161. 1,293: 0.6659, 160/161. The difference is 0.003, well inside noise.
  - 2,586 is eligible under every non-strict row of my ladder. It is the only full-train checkpoint that is policy-robust.
  - 2,586 vs pilot300: F1 CI [−0.0004, +0.0231]. Slot preservation is 0.4188 vs 0.4558, and slot-free is 11 vs 6.
  - 1,293's remaining failure `03801` (identifier) is not characterized anywhere in the request. Its eligibility rests on an unadjudicated failure.
  - D-083 as written has no margin over the fallback. Under it, "max F1 among passing" would replace pilot300 with 2,586 on a CI that includes 0.
- **Next steps:**
  1. Record "eligible candidate (policy output), not promoted, not shown better than fallback". Do not write "selected".
  2. Adjudicate `03801`. If it is a surface artifact, 1,293 and 2,586 remain both eligible and the tie is by F1 only.
  3. Require human 50 evidence before any replacement of pilot300.

### D4-3 — alias candidate
- **Verdict:** disagree.
- **Evidence:**
  - The alias is supported by one document (`04709`).
  - The audit implementation lets the alias bypass the uniqueness guard for all values: `if len(snum[value]) != 1 and not counter_alias: continue`. It also does not require the matched source unit to be `명`, so a bare `18` could consume `18일`.
  - Choosing it makes 1,940 win. The request itself calls that order post-hoc.
- **Next steps:**
  1. Do not list an "alias candidate" in any selection table. Report an alias sensitivity row, clearly labeled outcome-informed.
  2. See Q6 for the conditions under which an alias could become independently justified.

### D4-4 — gate additions
- **Verdict:** conditional.
- **Evidence (my computations, [derived] from the request's tables):**
  - Nonvacuous grounded = (grounded − slot_free) / (161 − slot_free), since slot-free documents are grounded trivially. The slot-free counts are the request's v1-based table, assumed unchanged under v2.
  - pilot300 155/155; 1,293 152/153 (0.9935); 2,586 149/150 (0.9933); 1,940 generic 155/157 (0.9873) and alias 156/157 (0.9936).
  - So nonvacuous with the same 0.99 gives identical eligibility. It exposes how many "passes" are vacuous (2,586: 11 slot-free documents).
  - CP 95% two-sided for grounded: 161/161 [0.9773, 1]; 160/161 [0.9659, 0.9998]; 159/161 [0.9558, 0.9985]. Every lower bound is below 0.99, so everything is INCONCLUSIVE against ≥0.99.
- **Next steps:**
  1. Report both document-level grounded and nonvacuous grounded with CP. Define the label as "PASS-point / INCONCLUSIVE-CP" when point ≥ 0.99 and CP lower < 0.99.
  2. Keep coverage/adequacy (slot_preservation, slot_free) report-only. Calibrate with human 50 before any threshold. Setting a threshold now would be chosen after seeing 0.4188.
  3. Use document-level (cluster) bootstrap for slot-level metrics. Do not pool slots across documents as independent.

### D4-5 — the 5 excluded flips
- **Verdict:** conditional (protocol over label).
- **Evidence:**
  - The pool is 383 pairs, all v1-ungrounded (`v1_grounded = 0`). It is a mix of true hallucinations and v1 false rejects. The 5/383 (1.3%, CP [0.4%, 3.0%]) is a flip rate, not a false-accept rate. "False accept" presupposes v1 was right.
  - A deterministic rule with a confirmed false accept is a counterexample to the rule. A tolerable rate is the wrong frame for a safety gate.
  - Draft DoD says "human-confirmed false accept 0". With n = 5, 0/5 only bounds the rate at ≤ 0.52 (two-sided CP). It cannot demonstrate safety. It can only falsify.
  - `v1_new` = `2020`, `2021` may be year-without-`년` (probably benign). `404`, `20`, `5000/200` are not obviously so. I could not inspect the text **[unverified]**.
- **Next steps:**
  1. Two raters, blind to v1/v2 and to the checkpoint, classify each flip: legitimate v1 false reject (same entity and quantity, only unit or format dropped) vs false accept vs ambiguous. Provide source and target spans.
  2. Rule: any confirmed or ambiguous false accept removes or narrows the responsible clause. Do not accept the clause at "k/5".
  3. Add a synthetic mutation test (see experiments): swap source numbers across units inside clean targets and require v2 to reject them.

### D4-6 — URL case/comma
- **Verdict:** agree (fix now).
- **Evidence:**
  - v1 `_canonical` lowercases everything and strips all commas, so `Case?key=A,B` equals `case?key=ab`. The change is toward stricter, so it cannot inflate grounded.
  - Exposure is tiny: `target_slot_audit.json` shows 4 URL slots in clean sources and 0 in clean targets. The fix is low-risk, and so is the "clean target unchanged" claim for URL (vacuous, see Q14).
  - The audit matcher does **not** implement it (it uses v1 `extract_slots`), so no v2 number in the request reflects the stricter URL canonicalization.
  - The same lowercase/comma-fold also applies to `path` and `identifier` slots (246 identifier source slots). The request mentions only URLs.
- **Next steps:**
  1. Implement scheme/host-only lowercase in v2 and keep trailing sentence-punctuation stripping (v1 does it implicitly in `_canonical`; the draft does not say so). Add the tests.
  2. Re-run the audit with it and report any v1→v2 changes on val/clean as *new rejections*.
  3. Audit `path`/`identifier` case-folding as a separate item. Do not fix it silently.

### D5-1 — human 50 primary
- **Verdict:** conditional.
- **Evidence:**
  - There is no defensible single primary. The F1 and preservation advantage of 1,940 depends on a CI [0.0012, 0.0249]. The policy-robust eligible checkpoint is 2,586.
  - The live questions are (a) 1,940 vs 2,586 and (b) whether a policy-forced 2,586 beats pilot300.
  - Val 161 was reused for prompt/LR/pilot selection, so human 50 is exploratory and cannot be confirmatory. 50 paired documents only resolve large effects.
- **Next steps:**
  1. Arms: pilot300 (control), 1,940, 2,586. Add 1,293 only if rater capacity allows; otherwise drop it. Same 50 documents, blind, randomized order, checkpoint identity hidden.
  2. Pre-specify two primary contrasts: 2,586 vs 1,940 and 2,586 vs pilot300 (pairwise preference plus unsupported-content and omission ratings).
  3. Stratify: about 30 random val documents plus about 20 targeted (`04951`, `04709`, `03978`, `02742`, `03801`, 2,586's slot-free documents). Report the random and targeted parts separately.

### D5-2 — test 163
- **Verdict:** agree (seal).
- **Evidence:** the draft's own DoD and §0.5 keep it sealed. A0 already used it in D-080 (0.6072). A1 has not used it. No candidate is frozen and D-084/human 50 are open.
- **Next steps:** see Q10.

### D5-3 — next experiment
- **Verdict:** conditional.
- **Evidence:**
  - v2 implementation and ablation are CPU only and cheap, and they gate every other decision.
  - Seed 43 is the only experiment that tells whether 1,940-vs-2,586 (and the 1-document gate flips) is a real effect or noise. It costs about 4 h 20 min of training plus eval, so it should come after cheap evidence.
  - A compression arm has no mechanism evidence yet: 2,586's over-compression is an inference from preservation 0.4188 vs implied about 0.465.
- **Next steps:**
  1. spec-faithful v2 plus ablation plus flip adjudication → then human 50.
  2. Decide on seed 43 after those.
  3. Defer the compression arm.

### D5-4 — D-084 status
- **Verdict:** conditional agree.
- **Evidence:**
  - Policy scenarios were already computed (generic, alias, URL-only), so the protocol cannot be called blind. It is outcome-informed.
  - The URL wrap fix is a legitimate source-attested measurement correction, so v2 should not be discarded.
  - The draft header says both "사용자 승인을 받은 초안" and "DRAFT / 미승인", which is ambiguous.
- **Next steps:**
  1. Approve only as "D-084 exploratory, outcome-informed". Split it: 084a (measurement: URL wrap plus URL strictness, a verifier version bump) and 084b (equivalences: qualifier; unit report-only; alias off).
  2. Preserve D-083 files byte-identical (record SHA-256, git tag) and print strict, 084a, 084b columns side by side in every table.
  3. Fix the header to a single unambiguous status.

---

## 3. Q1 … Q14

### Q1 — generic v2 vs URL-only
- **Verdict:** conditional.
- **Evidence:** the audit's URL repair alone moves 1,293 and 2,586 to 160/161. The qualifier is a 7/1,617 collision exposure and has a collision guard. The unit clause is 902/1,617 exposure with weak guards and no selection benefit **[derived]**. URL wrap needs both-sides application (1,940's prediction contains `http://coronamap.\nsite`).
- **Next steps:** (1) URL (+ strictness) is the baseline. (2) Qualifier is a separate named equivalence with `qualifier_dropped` reporting. (3) Unit is report-only unless the ablation and adjudication justify it.

### Q2 — counter alias
- **Verdict:** disagree as an automatic rule; conditional as a per-case human adjudication outside the gate.
- **Evidence:**
  - `18 확진자` ↔ `18명` is a lexical-semantic coreference judgment, not a normalization.
  - The audit's implementation is broader than the text:
    - It checks "확진자 anywhere in the next 24 characters", not "바로 뒤".
    - It uses `summary[m.end:m.end+24]` on the raw summary with offsets taken from the NFKC-normalized, URL-repaired text. Those offsets can misalign.
    - It does not constrain the matched source unit to `명`, so it could consume `18일`.
    - It disables the uniqueness guard for every value.
  - Support is a single document.
- **Next steps:**
  1. Record `04709` as a human-adjudicated case (source spans for `18일`, `18명`, and the `18 확진자` sentence). Report it as a separate column "human-adjudicated grounded". It does not affect the gate.
  2. If an alias is ever pursued, make it a closed, pre-listed table of head noun → unit (`확진자`, `사망자`, `환자` → `명`), unit-constrained, with a bounded window.
  3. Enumerate every firing across all checkpoints and the 383 pool, not just `04709`.

### Q3 — acceptance criterion for the 5 flips
- **Verdict:** conditional.
- **Evidence:** see D4-5. Also: the flips come from the v1-ungrounded pool, so they are not representative of the model-output distribution. The adjudication should also cover the val flips (v1→v2 on all 5 systems) and the remaining unexplained failures (`03801`, `00114`, `01767`, `03086`, `00818`).
- **Next steps:**
  1. Replace "false accept 0" with: every adjudicated flip judged legitimate by both raters; any other result drops or narrows the clause. Write it in the DoD.
  2. Include disagreement handling (third reviewer) and record spans.
  3. Report the flip count with a CP interval, but frame it as falsification, not as a rate.

### Q4 — D-084 as outcome-informed exploratory; D-083 preservation
- **Verdict:** conditional.
- **Evidence:** all three policy scenarios and their results are already in the draft and request, so no part of the rule choice is blind. The draft wisely refuses to call any scenario a product candidate. D-083 outputs are `selection.json` and `selection_summary.json` (`full_train_selected_step: null`).
- **Next steps:**
  1. Label D-084 "exploratory, outcome-informed". Its output may produce "candidate for human review", never "selected_step" or product approval.
  2. Keep D-083 files unmodified, hash them, and write `selection_v2.json` as a separate file carrying `verifier_version` and `policy`.
  3. Never print a v2 table without the strict column.

### Q5 — 1,940 vs 2,586 as candidate
- **Verdict:** conditional.
- **Evidence:** 2,586 is the only checkpoint eligible in every non-strict policy. The 3-AI "1,940 primary" recommendation predates the audit and assumed the verifier artifacts could all be repaired. Relabeling 1,940 a candidate would require the alias (Q6).
- **Next steps:**
  1. Formal record: eligible candidate under the chosen baseline = 2,586 (if no alias). State it is not shown better than pilot300.
  2. Human review treats 1,940 and 2,586 as co-primary arms (D5-1).
  3. Any promotion needs the human result plus a frozen test protocol.

### Q6 — alias justification and `18일`/`18명` adjudication
- **Verdict:** disagree for now.
- **Evidence:** the only argument is that it makes 1,940 pass, which is the order the request forbids. The audit alias does not even prove the matched slot was `18명`. My `[unverified]` observation: the guard failure on `04709` could also come from `18명` occurring more than once in the source, because the audit builds its source slot list with `dict.fromkeys(extract_slots(...))` over `Slot` objects that include positions. So repeated identical slots are never collapsed, and `len(snum["18"])` counts occurrences, not distinct unit slots. If so, the "18일/18명 collision" description is not the (only) cause.
- **Next steps:**
  1. Adjudicate `04709` by reading the source sentences: does the `18 확진자` refer to the same group, date, and scope as `18명`? Record both raters' answers.
  2. Justify an alias only if (a) it is stated as a closed head-noun table, (b) it is unit-constrained to `명`, (c) every firing on the corpus is adjudicated, and (d) its effect on all checkpoints (not just 1,940) is reported before any selection is re-run.
  3. Fix the occurrence-vs-distinct counting first. It may change the Q1/D4-1 reading.

### Q7 — human 50 design
- **Verdict:** conditional.
- **Evidence:** see D5-1. Blind evaluation of all arms on the same 50 documents is correct. 4 arms × 50 = 200 summaries; the effect size detectable with 50 pairs is large.
- **Next steps:**
  1. Randomize order and hide checkpoint IDs. Include pilot300 as control.
  2. Rubric: unsupported content (extrinsic, including `04951`-type), omission of key facts, readability, usefulness as a memory item. Double-rate at least 15 documents for agreement.
  3. Treat all findings as exploratory (val was reused). Do not use P1. Do not use test 163.

### Q8 — G-C5 additions and thresholds
- **Verdict:** conditional.
- **Evidence:** see D4-4. The document-level 0.99 stays and the denominator is 161 for grounded, and (161 − slot_free) for nonvacuous. Slot-level metrics (preservation, new-slot micro) keep slot denominators and a document-cluster interval.
- **Next steps:**
  1. Add nonvacuous grounded with the same 0.99. State the equivalence "≤1 failure" for n ≤ 199.
  2. Add CP 95% and the label INCONCLUSIVE when the lower bound is below 0.99.
  3. Keep adequacy report-only; decide a threshold only after human 50.

### Q9 — 161 documents and the 0.99 gate
- **Verdict:** agree (keep gate + CP; enlarge only through P0 unseen sources).
- **Evidence:** 161 documents cannot certify ≥0.99 even at 161/161 (lower 0.9773). A 0-failure certificate needs n ≥ 368. The 383 excluded pairs' *sources* were never in A1 training (clean = train 1,293 + val 161 + test 163). They are P0 and are not test 163. They are biased toward numerically messy documents, so that bias must be stated.
- **Next steps:**
  1. Keep the gate as a screening rule; print CP and INCONCLUSIVE.
  2. Optionally (E4 below) generate on the 383 unseen sources for the top candidates only, reference-free grounded check.
  3. Do not describe any 161-document pass as a certification.

### Q10 — test 163
- **Verdict:** agree. Do not open now.
- **Evidence:** no candidate is frozen, the verifier is still draft, and human 50 has not happened. A0 saw test 163 (D-080, 0.6072), so even the A1 run is not an untouched test.
- **Next steps:**
  1. Release only when all hold: D-084 closed; human 50 done; one candidate frozen in a commit (adapter SHA-256, verifier version and hash, decode config, pass/fail criteria including the fallback rule); one-shot, one candidate.
  2. Add a use-log: `test163: A0 opened D-080 (0.6072); A1 unused as of fc31b07`. Label any future A1 result "confirmatory with prior project exposure (A0)".
  3. No verifier change after opening.

### Q11 — URL canonicalizer
- **Verdict:** agree (fix now in v2) plus a small separate audit.
- **Evidence:** see D4-6. Also check the draft pattern against the code: the draft says `[./_-]\n[space]...`, the code allows `[ \t]*` before the newline, a lazy URL prefix, and a lowercase-alnum continuation. A URL ending in `.` followed by an English sentence starting in lowercase would be joined. The audit itself flags `03992 → http://fine.fss.` as "문맥 확인 필요".
- **Next steps:**
  1. Fix and test the stricter canonicalization.
  2. Require summary-side joins to be source-attested: after joining, the URL must equal a (source-joined) source URL, else leave it unjoined.
  3. Count how many v1-accepted historical documents (clean filter, val) would change. This is a small audit and should be reported even if the answer is zero.

### Q12 — draft gaps and Must-fix
- **Verdict:** conditional.
- **Evidence:** the draft is sound on scope and on refusing to promote anything. The gaps are spec/code drift, missing ablation, ill-posed DoD, and no freeze protocol. See Must-fix list in §4.
- **Next steps:** apply Must-fix 1–7 before implementation.

### Q13 — 1,940 as human-review arm
- **Verdict:** agree.
- **Evidence:** "eligible" is a pre-registered, measurement-dependent label. "Included in human review" is a scientific choice to resolve exactly that dispute. 1,940's preservation (0.4761 vs 0.4188) and F1 advantage need human evidence either way.
- **Next steps:**
  1. Label 1,940 "gate-ineligible under strict and generic v2; alias-dependent". Do not call it a primary.
  2. Include `04709` and `03978` in the targeted stratum.
  3. Keep the two concepts in separate columns in the report.

### Q14 — errors, overstatements, omissions
- **Verdict:** n/a (list). Each item has a check.
  1. **"clean target v1→v2 change 0/1,617" is vacuous.** All 1,617 clean targets are v1-grounded by construction. The audit matcher only adds acceptances. Clean targets contain 0 URL slots (`target_slot_audit.json`), so the URL strictness could not have changed anything. The statement says nothing about v2 safety.
  2. **The "URL+qualifier only / no unit rule" row is not an artifact.** The audit script and JSON have only `generic` and `alias` variants. The row is derivable from fail IDs but was not run.
  3. **Draft §5.1/§5.5 says v2 preserves URL path/query case and commas; the audit matcher does not.** It reuses v1 `extract_slots`/`_canonical`. All v2 numbers lack this rule.
  4. **The audit "counter alias" is looser than described.** 24-character window anywhere vs "바로 뒤"; guard bypassed for every value; matched unit not constrained to `명`; offsets taken from repaired/normalized text but applied to the raw summary.
  5. **The "uniqueness guard" is not "unique including unit".** The code counts source slot occurrences (positions make `Slot` objects distinct), not distinct canonical slots. The description of `04709` as an `18일`/`18명` collision may be incomplete **[unverified]**.
  6. **"False-accept candidates" for the 5 flips presumes v1 was right,** and the 383 pool is entirely v1-ungrounded. So 5/383 is a flip rate in a mixed pool, not a false-accept rate. The pool's composition (why 383 excluded) is not described.
  7. **The 3 URL wrap documents may include a false join.** `03992 → http://fine.fss.` is flagged for context check but still counted in 3/1,617.
  8. **Remaining val failures are not characterized.** `03801` (1,293's identifier failure) and 647's `00114`, `01767`, `03086` are unexplained, yet D4-2 depends on 1,293's eligibility.
  9. **ID mismatch.** The draft's open-decision table has D4-1…D4-4, D5-1, D5-2. The request has D4-1…D4-6 and D5-1…D5-4. Draft header ambiguity as noted (D5-4).
  10. **Reproducibility.** `data/external/*.jsonl` is not in the repo, and the reproduction command is a Windows `.venv` path. Reviewers cannot verify the flips, `04709`, or `03992`. No data hash is given.
  11. **Omissions.** No F1-noise statement for 2,586 vs 1,293 and pilot300. No statement that A0's use of test 163 limits what an A1 test result means. No seed-variance caveat for a gate that flips on one document.

---

## 4. Must-fix (priority order)

1. **Spec/code parity.** Re-run the audit with a matcher that implements the spec before any approval: URL path/query strictness, distinct-canonical uniqueness counting, source-attested summary-side URL join, and (if kept) a unit-constrained, bounded-window alias. Treat all current audit numbers as provisional.
2. **Split D-084.** 084a = measurement (URL wrap + URL strictness). 084b = equivalences (qualifier; unit report-only; alias off). Name the selection baseline explicitly in the text.
3. **Clause ablation with attributed flips.** Table of URL / +qualifier / +unit / +alias, for every v1→v2 document on val (5 systems) and on the 383 pool, with the responsible clause.
4. **Rewrite the flip DoD.** Replace "false accept 0" with a blind two-rater protocol and a clause-removal rule. Add a synthetic mutation test (cross-unit number swaps; `2.3%`-type extrinsic numbers; 오전↔오후; URL case/comma). Add regression tests that v2 still rejects `04951`'s `2.3%`/`2.2%`.
5. **Terminology and immutability.** Separate "eligible", "selected", "promoted". Hash D-083 outputs, write `selection_v2.json` separately, and always print strict next to v2. Label the whole protocol outcome-informed.
6. **Gate reporting.** Define nonvacuous grounded, CP, and the INCONCLUSIVE label numerically. Note that 161 documents cannot certify ≥0.99. Add no new hard thresholds after seeing outcomes.
7. **Freeze and reproducibility.** Test-163 freeze protocol (adapter hash, verifier hash, decode config, single-use) with a use-log. Add data hashes and excerpts for adjudicated documents so reviewers can check them.

---

## 5. Additional experiments (≤5, rough cost)

| # | Experiment | Cost (rough) | Why |
|---|---|---|---|
| E1 | Spec-faithful v2 plus clause ablation plus val/383 flip attribution (CPU only, no model runs) | about 0.5–1 day dev; minutes to run | Removes the audit/spec drift. Shows whether the unit clause matters at all. |
| E2 | Synthetic mutation set from clean pairs: cross-unit number swaps, extrinsic numbers, 오전↔오후, URL case/comma; measure v1 vs v2 false-accept/false-reject (CPU only) | under 1 day | Gives a real false-accept estimate. The 5/383 flips cannot. |
| E3 | Human 50, blind, arms pilot300 / 1,940 / 2,586 (+1,293 optional), double-rate ≥ 15 | on the order of a few rater-hours per arm-set (my estimate, not measured) | Resolves 1,940 vs 2,586 and "policy-forced 2,586 vs pilot300". Exploratory. |
| E4 | Reference-free grounded check on the 383 unseen P0 sources for the top candidates (generation needed; only after E1, with explicit approval) | 383 × per-document greedy time × number of arms; per-document time is **not measured by me**, take it from existing eval logs | Enlarges the grounded sample. Biased toward numerically messy documents. Not test 163, not P1. |
| E5 | Seed 43, same recipe | about 4 h 20 min train plus eval | Only conditional, after E1–E3. Quantifies how much the 1-document gate flip and the 1,940/2,586 gap are seed noise. |

---

## 6. Final recommendation

D-083 strict stands: no full-train checkpoint is eligible, and pilot300 remains the strict fallback. That is not product approval. D-084 can be approved only as a labeled exploratory, outcome-informed protocol, split into a measurement part (URL wrap and URL strictness) and an equivalence part (qualifier; unit report-only; alias off). Approval does not change any gate. Before any approval the audit has to be re-run with a spec-faithful matcher, because the current audit differs from the draft in several ways (Q14 items 3–5), and none of its v2 numbers should be treated as final.

The central finding is that 1,940 beats 2,586 only if an alias is adopted. The alias rests on a single document and is loosely implemented, so it should not be adopted to rescue 1,940. Without it, 2,586 is the formal max-F1 eligible candidate under every enumerated policy. But 2,586 is not shown to beat pilot300 (F1 CI includes 0, lower preservation, 11 slot-free documents). The sensible path is to put 1,940, 2,586 and pilot300 in a blind human review with pre-specified contrasts, and to keep test 163 sealed until D-084 is closed, a single candidate is frozen, and a use-log records A0's prior use.