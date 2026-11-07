# Independent external review — C5 / D-084

**Reviewer:** Sol 6.1 (`openai/gpt-6.1-sol`), independent consultation, 2026-11-07.  
**Repository:** `mandutt/unigem`. **Review basis:** `ae2a5d49777e6999350c945a660f8ed073fed3d7`.

## 1. Scope, synchronization, and executive conclusion

I ran `git fetch origin`, then `git pull --ff-only origin main`; both succeeded. HEAD and `origin/main` both resolved to the commit above. The thread's existing branch was retained; its HEAD was fast-forwarded to main. The initial working tree was clean. I read **all 446 lines** of `reports/EXTERNAL_REVIEW_C5_D084_2026-11-07.md`, the complete 260-line D-084 draft, the audit report/JSON, verifier and audit code, selection artifacts/code, and the relevant saved validation artifacts. This review does not adopt the earlier multi-model recommendations as authority.

**Recommendation:** retain D-083 exactly, including `selected_step = null` and pilot300 as a **fallback, not product approval**. D-084 is worth pursuing as **outcome-informed exploratory measurement development**, not as a retrospective preregistration or evidence that D-083 passed. I do **not** recommend approving generic v2 as the default baseline in its present form. Start with a narrowly specified **URL-only v2**, including correction of the existing URL false equivalence; retain qualifier and numeric-unit policies as separately audited exploratory variants. A conservative URL repair is itself conditional on tests and source evidence, not automatically approved by this review.

Under the **reported audit-generic scenario**, 2,586 is the formal max-F1 eligible checkpoint; 1,940 is not eligible. If an independently justified, human-adjudicated alias policy eventually makes 1,940 eligible, the same frozen selection rule would choose it. But the current audit's alias implementation is not evidence that such adjudication succeeded: it can match a date to a people count. For human review, use the policy-selected candidate as the **decision primary** (provisionally 2,586), pilot300 as control, and include 1,940 and 1,293 on the same 50 documents. 1,940 remains an important exploratory comparator; that does not confer eligibility.

**No gate change, candidate promotion, human protocol, or test release is approved by this report.** No training, model generation, subagents, additional LLMs, P1 data, or test-163 contents/evaluation were used in this review. The only repository file written is this report. Raw P0 source corpora are absent here; I therefore cannot honestly adjudicate the five excluded flips or certify the real `04709` source-to-summary semantic alignment.

## 2. Evidence register and independently checked results

References below are repository-relative; line numbers refer to the reviewed HEAD.

| Ref | Evidence inspected |
|---|---|
| R | `reports/EXTERNAL_REVIEW_C5_D084_2026-11-07.md`, all lines 1–446; especially §§2, 4–7, 9 |
| D | `docs/D-084_verifier_v2_draft_2026-11-07.md`, all lines 1–260; rules 98–152, selection 156–186, API/DoD 190–236 |
| A | `reports/provenance/C5_a1/full_2ep/verifier_v2_audit.json`, complete; `reports/C5_A1_verifier_v2_audit_2026-11-07.md`, complete |
| V1 | `eval/slot_verify.py`, complete; canonicalization 95–110, extraction 113–150, unique/count/report semantics 153–188 |
| VA | `runner/c5_a1_verifier_v2_audit.py`, complete; URL repair 28–48, matching 78–159, corpus access 162–221, scoring/output 223–279 |
| S | `reports/provenance/C5_a1/full_2ep/selection.json`, `selection_summary.json`; `runner/c5_a1_select.py`, especially 36–49 and 75–81 |
| E | All four full-train `eval_step_*/eval.metrics.json` and saved `eval.jsonl`; pilot300 `pilot300_val161/metrics.json` and `predictions.jsonl`; `runner/c5_a1_eval_batch.py` |
| X | `reports/provenance/C5_a1/full_2ep/error_analysis_1940_vs_2586.json`; `reports/C5_A1_error_analysis_2026-11-07.md`; `runner/c5_a1_error_analysis.py` |
| G | `docs/decisions.md`, D-022/D-080/D-083; `docs/gates.md` lines 25 and 28–43 |

### 2.1 Strict results versus audit scenarios

I independently aggregated all five saved **validation** prediction files. Each has 161 unique IDs, and all five have the same ID set. Their stored grounded counts, slot/new counts, mean F1, slot-free counts, and source-preservation means agree with the following strict table. This aggregation does not rerun generation or access test data.

| System | Strict F1 | Strict grounded | Strict new / summary slots | Strict slot-free | Audit generic grounded | Audit alias grounded |
|---|---:|---:|---:|---:|---:|---:|
| pilot300 | .657580 | 161/161 | 0/837 | 6 | 161/161 | 161/161 |
| 647 | .669853 | 155/161 | 6/877 | 2 | 158/161 | 158/161 |
| 1,293 | .665946 | 159/161 | 2/854 | 8 | 160/161 | 160/161 |
| 1,940 | .682278 | 158/161 | 4/860 | 4 | 159/161 | 160/161 |
| 2,586 | .668982 | 159/161 | 3/762 | 11 | 160/161 | 160/161 |

The last two columns reproduce **existing audit JSON**, not an independently rerun production v2. Their denominators must not be combined with v1 slot counts to fabricate v2 micro rates. The JSON lacks the full v2 slot-denominator metrics needed to complete a faithful four-gate rescore. 647 also fails repeated4 (.06840 > .06); its EOS 160/161 passes.

S confirms that **all four full-train checkpoints fail strict selection**. The hypothetical generic eligible set contains 1,293 and 2,586, with pilot300 retained as fallback/control; 2,586 has the highest F1 among them. Its lead over 1,293 is only .003035, not evidence of superior adequacy. The reported paired F1 intervals in R §2.3 concern reused validation data and are neither semantic-fidelity proof nor selection-adjusted confirmatory inference.

X confirms that 2,586 has 11 slot-free documents, of which **9 have target slots**; the target counts among those nine are three documents with one slot and six with three/four slots. This establishes omission of extracted reference slots, not automatically omission of nine documents' essential facts. Source preservation falls from .47610 at 1,940 to .41882 at 2,586. These observations motivate human adequacy review, not silently substituting a new selection objective.

### 2.2 Material audit implementation findings

I called only the already-inspected pure matcher functions on **handwritten synthetic strings**, with Python bytecode disabled. I did not run the audit script's `main()` or rescore any corpus. The following are reproduced findings, not hypothetical concerns.

1. **The audit still inherits the URL false acceptance.** V1 canonicalization lowercases the entire slot and removes commas. VA imports that extractor and matches its canonical strings. Both audit variants mark source `https://example.com/Case?key=A,B` and summary `https://example.com/case?key=ab` grounded, with no new/missing slots. Thus A is not a measurement of the full D-084 URL specification, which promises to preserve path/query case, comma, and escapes.
2. **Numeric uniqueness is necessary but not sufficient.** With source `증가율은 18%다.` and summary `18 확진자가 발생했다.`, generic `match_v2` returns grounded with no new slots. It also accepts source `회의는 18일 열린다.` against that summary. The extractor calls summary `18` bare, although `확진자` supplies an implicit human-count type. Uniqueness alone does not prevent cross-dimension semantic false accepts. This is a concrete reason not to default-enable the generic unit rule now.
3. **The alias option does not enforce its own proposed clause.** VA lines 132–145 bypass uniqueness and merely seek `확진자` within a 24-character suffix; there is no requirement that the source unit be `명`, that it be adjacent, or that event/entity/scope agree. Source containing only `18일` can pass as `18 확진자`. Source `회의는 18일 열렸고 확진자는 18명이었다.` versus summary `확진자는 18명이며 18 확진자를 격리했다.` gives generic `new=['18'], missing=['18일']`, but alias gives `new=[], missing=[]`: the alias improperly credits preservation of the **date**.
4. **The “+ alias” code is not necessarily additive.** For source `환자는 20명이다.` and summary `환자 20`, generic passes while alias fails. Enabling the option applies its `확진자` condition even to generic-unique matches. Therefore the audit variant cannot generally be interpreted as generic plus only an extra legitimate relation.
5. **Occurrence/unique-slot semantics diverge.** Repeating the same source `20명` makes `len(snum[value]) != 1` and blocks the generic relation, despite only one canonical value+unit. `dict.fromkeys(Slot)` retains occurrences with different offsets, whereas the canonical maps collapse them; reported source/summary counts use the former. V1 counts unique canonical slots. The draft must distinguish unique unit types, repeated mentions, and semantic referents, and keep denominator definitions coherent.
6. **Repair is not yet the promised attested repair.** `repair_url_wraps` joins lexical matches without an attestation/ambiguity argument. It joins `https://example.com/path/` followed by newline and `news is a new sentence.` into a different URL. This probe demonstrates ambiguity, not that every such join is wrong. Summary repairs are discarded from the report, and alias suffix indexing uses original summary text with offsets obtained from repaired/normalized text. Evidence spans can therefore drift.

The actual `04709` validation prediction contains two exact `18명` mentions plus `18 확진자`; X's strict missing list contains `18일`, not `18명`. Combined with VA's “skip already matched source” loop, this means the reported rescue can be supported by an unmatched date rather than by the already matched people count. The synthetic example above reproduces that failure mode. A real-source edge trace and human adjudication are still needed; **160/161 is not evidence of a valid human-approved counter alias**.

### 2.3 Test-seal and “read-only” qualifications

VA loads all clean 1,617 rows, loops over their sources at 174–190, and runs target verification on **every clean row** at 195–203. Since clean includes train 1,293 + val 161 + test 163, the corpus-wide audit code covers held-out sources/targets too. This does **not** establish that A1 predictions were generated or scored on test 163; it does require a more precise exposure history than “test contents were never touched.” I inspected the code, not those held-out contents. Future D-084 rule development should use explicit **train/val and excluded-only inputs**, not rerun this all-clean audit.

Also, VA's `main()` writes `verifier_v2_audit.json` at 271–274. “Read-only” here means no production-verifier/model/source-data mutation, not literally no filesystem writes. Its published reproduction command is unsuitable for this consultation's write restrictions and was not executed.

## 3. Decision items D4-1 through D5-4

Each verdict evaluates the recommendation stated in its row, not an assertion that the project has approved it.

### D4-1 — Unit policy: **disagree** with generic-unit default now

**Evidence:** R §4.3/§4.5, D §5.3, and VA's reproduced cross-dimension acceptances above. The 902 collision documents show exposure, not a measured error rate; even a unique source numeric value can refer to the wrong semantic type. Clean's unchanged binary grounded status is not a safety validation.

**Next steps:** (1) Make the first proposed baseline URL-only, with time/unit equivalences disabled. (2) Keep generic-unit and qualifier variants separate and require contextual negative controls plus human rule audit before considering defaults. (3) Specify repeated-mention, implicit-unit, entity, and scope handling; do not add aliases to target 1,940's eligibility.

### D4-2 — Candidate under generic v2: **conditional** agreement with 2,586

**Evidence:** A/R §4.4 and S: 2,586 F1 .668982 exceeds 1,293 .665946 among the audit-generic eligible checkpoints. 1,940 is 159/161 and cannot enter that ranking. X supplies an independent adequacy warning, not permission to rewrite the ranking.

**Next steps:** (1) Faithfully implement and validate the chosen policy before issuing `selection_v2.json`. (2) Recompute all four gates for every checkpoint and retain pilot300 as fallback/control. (3) If 2,586 is selected, make it a human-review candidate only; if it fails separately frozen adequacy criteria, report that failure rather than automatically promoting the runner-up.

### D4-3 — Candidate under alias: **defer** 1,940 eligibility

**Evidence:** A's 160/161 is conditional on an automatic, structurally unsafe alias implementation, not a signed human decision. D §5.4 requires same event/group/scope and human adjudication; those requirements are not implemented by VA.

**Next steps:** (1) Audit `04709` using the full permitted source and exact summary, with checkpoint identities hidden. (2) Bind any accepted alias to the people-count span and an immutable adjudication record, never `18일`. (3) Only after independent policy approval and all-checkpoint rescoring may the unchanged max-F1 rule select 1,940 under that distinct policy.

### D4-4 — Nonvacuous, adequacy, CP, INCONCLUSIVE: **agree** as separately specified additions

**Evidence:** X's vacuous passes; G distinguishes slot grounding from source coverage and requires sample/interval reporting. D §6.3 already recognizes this distinction but omits operational thresholds and decision semantics.

**Next steps:** (1) Adopt the explicit denominators and proposed, not approved, criteria in §5 below. (2) Separate empirical screening, statistical uncertainty, and human adequacy in result fields. (3) Preserve D-083 thresholds/results; register any additional prospective criterion independently.

### D4-5 — Five excluded flips: **defer** individual adjudication

**Evidence:** A lists IDs and old new-slot strings, but no source/summary spans or event evidence. The raw corpora are absent. Rejection by v1 is not a gold label; acceptance by v2 is not an equivalence proof.

**Next steps:** (1) Human-review all five with two independent raters and arbitration (§4). (2) Require zero confirmed false accepts **and zero unresolved automatically accepted cases** in the audited changes before accepting a policy. (3) Keep all 383 excluded pairs excluded from the training dataset in this task, including legitimate measurement fixes.

### D4-6 — URL case/comma: **agree** to fix in v2, with audit in the same release

**Evidence:** R §4.6, D §5.5, V1 lines 99–103, and the reproduced audit false acceptance. Merely adding wrap repair while retaining this canonicalizer is not the specified v2.

**Next steps:** (1) Preserve raw path/query/fragment, comma and escapes; lowercase only scheme/host. (2) Test wraps on both source and summary, attestation, punctuation ambiguity, and negative URL pairs. (3) Audit both new accepts and new rejects before any v2 selection; leave v1 unchanged.

### D5-1 — Human 50: **conditional** agreement with a four-system paired protocol

**Evidence:** R §7 Q7 and X: 2,586 is the generic decision candidate but has the largest slot-free burden; 1,940 has the highest observed F1; 1,293 is an eligible sensitivity comparator; pilot300 is the strict fallback. None has completed human 50.

**Next steps:** (1) Use the policy-selected system as decision primary versus pilot300—provisionally 2,586, not because it is terminal. (2) Evaluate all four on the same 50 documents, blinded, with two raters and separately labeled diagnostic cases. (3) Freeze sampling, rubric, primary contrast and decision/INCONCLUSIVE rules before rating (§5).

### D5-2 — Test 163: **agree** to keep sealed

**Evidence:** D-083 and R §9: A1's single-candidate test is unused; human 50 is absent; policy and candidate are unresolved. A0 already used this split in D-080. VA adds a corpus-audit exposure caveat, not an A1 predictive test result.

**Next steps:** (1) Do not open, generate, or score it now. (2) Require completed verifier DoD, approved human review, adequacy disposition, and frozen candidate/adapter/tokenizer/decoding/policy/adjudication hashes before a separate authorized one-time A1 evaluation. (3) Report all A0, corpus-audit and A1 exposure history explicitly; do not call it a globally untouched confirmatory holdout.

### D5-3 — Next experiment: **agree** with verifier implementation/audit first

**Evidence:** D-083 training completed successfully, but rule validity—not missing training compute—is the immediate blocker. Changing seed or compression cannot validate the existing audit's acceptance decisions.

**Next steps:** (1) After authorization, build a separate URL-only v2 with regression tests and allowlisted inputs. (2) Resolve rule changes and human 50 before another training arm. (3) Prefer a frozen seed-43 replication only after the measurement protocol is stable; defer a compression objective until human review establishes which omissions matter.

### D5-4 — D-084 status: **conditional** support for outcome-informed exploratory approval

**Evidence:** R §4 exposes candidate-dependent outcomes before policy choice; D line 29 still uses preregistration language. That history cannot be undone, but valid measurement research need not be discarded.

**Next steps:** (1) Call D-084 an outcome-informed exploratory amendment, with known outcomes and policy alternatives recorded. (2) Freeze its prospective implementation/audit/human procedures without claiming the existing validation results were preregistered under v2. (3) Keep strict artifacts immutable; any later confirmatory claim needs independently planned, uncontaminated P0 evidence.

## 4. Five-flip adjudication and false-accept criterion

All five are **candidates**, not already proven false accepts or legitimate fixes.

| Excluded ID | V1 unmatched value(s) | Present verdict | Required evidence |
|---|---|---|---|
| `REPORT-news_r-00291-00002` | `2020` | defer | Full source and summary; matched source value/unit and the year/event/referent relation |
| `REPORT-news_r-01844-00001` | `2021` | defer | Same; establish scope rather than inferring correctness from a plausible year |
| `REPORT-news_r-03253-00001` | `404` | defer | Source and summary spans, type/unit and contextual referent; value equality is insufficient |
| `REPORT-news_r-04791-00001` | `20` | defer | Exact quantity/unit and event/entity scope supporting the bare number |
| `REPORT-news_r-05019-00001` | `5000`, `200` | defer | Separate evidence for **both** claims; one legitimate match does not ground the document |

Two Korean-capable humans should independently label each changed claim **entailed equivalent / unsupported or wrong scope-unit-entity / unresolved**, with model/checkpoint identity and selection consequences hidden. Show the full source, summary, original and repaired spans, candidate edge, and rule reason—not just old/new counts. A third person arbitrates disagreement. Record evidence, reviewer IDs and source/summary hashes. Only adjudicated entailment permits an equivalence. Unresolved cases stay unmatched/needs-review; they do not silently pass.

**Finite audit acceptance:** zero human-confirmed false accepts and zero unresolved auto-accepts across all changed acceptances in the 383 excluded pool and saved permitted validation predictions, plus all prespecified adversarial negative controls remaining rejected. Inspect **slot-level acceptance changes even when document grounded does not flip**, and inspect reverse flips caused by safer URL canonicalization. Retain `04951`'s unsupported `2.3%`/`2.2%` as a must-reject negative control. Do not solve a failure by blacklisting its ID: reject or narrow the responsible rule and rerun all allowed data.

This criterion does not require zero legitimate v1→v2 flips. Nor does 0/5 errors certify a low false-accept population rate: the two-sided 95% CP upper bound for 0/5 is **52.18%**, and the cases are selected, not an IID sample. Add independently constructed negatives and a separate representative P0 validation cohort before making population claims. Confirming these flips must not reopen training-data filtering or add the five pairs to training under D-084.

## 5. Concrete metric and human-review proposals — not approved gates

### 5.1 Denominators, thresholds, and confidence

1. **D-083 document screen stays unchanged:** grounded means no new extracted slot, including vacuous documents. Denominator is all 161 outputs. Grounded ≥.99 allows at most one failure. New-slot micro ≤.01, EOS ≥.95 and repeated4 ≤.06 remain distinct gates. Do not replace `grounded` with V1's `not rejected`: V1 `rejected` also includes missing source slots, while generation metrics use `not rep.new`.
2. **Proposed v2 nonvacuous screen:** report and, only with separate approval, require grounded ≥.99 among documents with at least one extracted summary slot. Denominator is that subset, not 161. A zero denominator is INCONCLUSIVE. Under the reported generic audit and unchanged slot-free membership: pilot300 155/155, 1,293 152/153, 1,940 155/157, 2,586 149/150; hypothetical valid alias would make 1,940 156/157. Recalculate these with the actual production-v2 extractor before use.
3. **G-C5 slot grounding is not document grounding:** let `Nslot` be the sum of per-document unique summary-slot counts under the declared verifier, and `Nnew` the corresponding unmatched count. Report grounding `1 − Nnew/Nslot` and new-slot micro `Nnew/Nslot`, the existing ≥.99/≤.01 targets, and G's minimum **300 slots**. Label raw outputs separately from verifier-accepted outputs; zero new slots in the latter is a filtering property, not model fidelity. Declare typed-slot deduplication and any changes from v1 before comparing versions. Report numerator/denominator when no source or summary slots exist, rather than rewarding empty output implicitly.
4. **Confidence:** report exact two-sided 95% CP by declared document/slot unit. Use separate fields for empirical PASS/FAIL and interval sufficiency. A point pass whose interval does not establish the target is **statistically INCONCLUSIVE**, not a statistical certificate. Slots within a document, and related article prefixes, are dependent; slot-binomial CP is a descriptive convention, not sufficient independent evidence. Add document/article-group-aware uncertainty for differences and generalization. Reused validation remains exploratory even if an interval clears a threshold.
5. **Coverage/adequacy:** keep source preservation descriptive; do not retrofit an absolute .465 or other source-coverage gate to these observed checkpoints. For automatic reference-supported slot recall, define `T_i` as reference slots supported by the source and `M_i` as those retained by the prediction under the same declared matching policy. Report macro recall over documents with `|T_i|>0`, micro `Σ|M_i|/Σ|T_i|`, and zero-slot predictions among reference-slot-positive documents. A **prospective proposal** is candidate macro recall noninferior to pilot300 with margin **−.05**, using a paired document/group-aware 95% lower confidence bound; otherwise INCONCLUSIVE or FAIL as specified before rating. This is an adequacy criterion separate from grounding, not a retrospective D-083 override. References are imperfect; human essential-fact review remains necessary.

I computed the following CP intervals using in-memory binomial inversion, without installing packages:

| Document grounded observation | Two-sided 95% CP interval |
|---|---|
| 161/161 | [97.735%, 100%] |
| 160/161 | [96.588%, 99.984%] |
| 159/161 | [95.585%, 99.849%] |

Thus even 161/161 does not establish population document grounding ≥99% at 95% confidence. With **zero errors**, an IID, prespecified sample needs at least **299 documents for a one-sided 95% lower bound ≥99%**, or **368 for a two-sided 95% CP lower bound ≥99%**. These are planning lower limits, not guarantees if failures occur, and neither split reuse nor article dependence disappears by increasing a nominal denominator. Do not enlarge the present validation set opportunistically until a bound passes, and do not use test 163 to supply the missing sample.

For comparison, v1 slot-error CP upper bounds are 0/837 → .440%, 4/860 → 1.187%, and 3/762 → 1.146%. This illustrates why low observed micro error and the document gate give different answers. These bounds apply to the **v1 counts**, not to unreported v2 denominators.

### 5.2 Human 50 protocol

- **Population/sample:** freeze a seeded random 50-document sample from the existing val 161 before rating; use all four systems on those same documents. Record article-prefix/train-overlap flags and report sensitivity, without claiming independence from reused validation. Keep known failure cases and slot-free stress cases as a separate diagnostic supplement unless random sampling selects them. Do not mix an enriched stress-case fraction into an unweighted population success rate.
- **Blinding:** randomize system labels and per-document presentation order; two independent Korean-capable raters plus arbitration. The full source is the factual authority. Define essential source facts before examining system outputs; use the reference as an aid, not infallible truth. The raw source availability is a prerequisite not met in this sandbox.
- **Rubric:** factual errors including wrong entity, role, time, unit, causality and negation; critical omissions; core-event adequacy; readability/repetition. Adequacy 0–3: 0 wrong/unusable gist, 1 major essential omissions, 2 correct gist and most essential facts with only minor omissions, 3 essential facts retained without material omission. Extracted slots alone cannot score these dimensions.
- **Proposed continuation criteria:** at least **45/50** outputs with adequacy ≥2, **zero adjudicated critical factual errors or critical omissions** in the reviewed candidate outputs, and a paired candidate-minus-pilot mean adequacy lower 95% confidence bound ≥**−.25** on the 0–3 scale. Report diagnostic-panel critical errors separately but require an explicit disposition before proceeding. Margins are proposals for user approval before rating, not numbers validated by current results. With 50 documents, noninferiority may remain INCONCLUSIVE; do not loosen the margin after seeing ratings.
- **Primary contrast:** the policy-selected candidate versus pilot300. On present generic evidence this is 2,586; 1,940-versus-pilot is a prespecified exploratory contrast, with 1,293 an eligibility/compression sensitivity comparator. If a legitimate alias policy is independently approved **before ratings**, update the primary according to the frozen selection rule and document why. Do not switch the primary to whichever system wins the human ratings.
- **Interpretation:** even zero critical errors in 50 gives a two-sided 95% CP upper bound **7.11%**, not <1%. Human 50 screens qualitative acceptability and diagnoses failure; it cannot certify 99% population factuality. Failure or insufficient precision blocks test release until an approved disposition, rather than authorizing sequential candidate fishing on test.

## 6. Questions Q1 through Q14

### Q1 — Generic baseline versus URL-only: **disagree** with immediate generic approval

**Evidence:** D §5 labels time/unit changes equivalence policies, not just repair; VA accepts a unique percentage/date as an implicit person count. Five excluded flips remain unadjudicated, and the URL part is not yet faithful to the draft.

**Next steps:** (1) Approve only a conditional URL-only development baseline first. (2) Keep qualifier-only and generic-unit arms explicitly versioned and exploratory. (3) Require the §4 audit, including semantic negative controls, before considering either a default.

### Q2 — Separate counter-alias clause: **conditional**

**Evidence:** R §4.3 and D §5.4 correctly distinguish entity/scope adjudication from normalization. VA's substring heuristic does not meet that definition.

**Next steps:** (1) Use a general human-adjudication protocol for the relevant construction, not a rule keyed to number 18 or document `04709`. (2) Require a source people-count unit, same referent/event/scope, exact spans and agreement record. (3) Keep the default off; do not let a Boolean alone grant semantic approval.

### Q3 — Five flips and acceptance: **defer** their labels, endorse a strict audit criterion

**Evidence:** A reports five old-fail/new-pass cases, not their truth labels; source data are unavailable here. Both legitimate unit omission and unsupported reinterpretation can produce that signature.

**Next steps:** (1) Execute the case-level plan in §4 on permitted P0 evidence. (2) Require zero confirmed false accepts and zero unresolved auto-accepts in changed decisions and controls. (3) Report finite-audit coverage and uncertainty; do not infer <1% false acceptance from five cases.

### Q4 — Exploratory D-084 or discard v2: **conditional** support for exploratory D-084

**Evidence:** Measurement defects are real, but R §4.4 shows that outcomes are already known. Calling this retrospective policy choice preregistered would be misleading; discarding all fixes would also be unnecessary.

**Next steps:** (1) Record known outcomes and the exploratory amendment rationale. (2) Preserve D-083 artifacts and publish distinct versioned scenarios after actual implementation. (3) Reserve confirmatory claims for subsequently planned independent P0 evidence.

### Q5 — Formal candidate when generic excludes 1,940: **agree** with 2,586, conditionally on a valid rescore

**Evidence:** Generic's eligible set and max-F1 rule choose 2,586, not the overall highest-F1 ineligible checkpoint. Earlier reviewers' preferred human comparator cannot override this rule. 1,293's lower F1 does not win on “earlier” because that tie-break applies only to a tie.

**Next steps:** (1) Freeze the policy and rescore all gates/candidates. (2) Review 2,586 as the provisional decision candidate and retain 1,940 as exploratory. (3) If adequacy fails, record a separate failure/no advancement; do not covertly change max-F1 selection to prefer a prettier summary.

### Q6 — Basis for alias and the 18-day/person collision: **defer** approval

**Evidence:** The saved 1,940 output really contains exact `18명` plus bare `18 확진자`, and X lists `18일` as missing. VA can credit that date, which is not semantic evidence for a counter alias.

**Next steps:** (1) Human-trace bare 18 to the same 18-person source group and event, not merely a source value 18. (2) Record duplication/scope and whether both summary mentions truly refer to the same group. (3) If established, apply the independently defined adjudication procedure to every relevant system/case, then rerun selection; otherwise keep the claim unmatched.

### Q7 — Human 50 primary and four-way pairing: **conditional**

**Evidence:** E/X support distinct eligibility, F1, and compression questions. All four systems have the same 161 validation IDs, allowing a paired design without new generation.

**Next steps:** (1) Freeze the §5.2 design and policy-selected primary-versus-pilot contrast. (2) Include 1,940 and 1,293 on all 50, with diagnostic cases separately labeled. (3) Publish disagreements, adjudication, effect sizes and intervals, not just average scores or a majority vote.

### Q8 — G-C5 additions and thresholds: **conditional**

**Evidence:** G's slot-level gate is not D-083's document-level rule; X's slot-free omissions expose the gap. D §6.3 names useful additions without operational criteria.

**Next steps:** (1) Use §5.1's explicit document/nonvacuous/slot denominators and unchanged .99/.01 screening targets. (2) Obtain approval for the separately proposed coverage noninferiority and human adequacy criteria before ratings. (3) Report empirical and statistical dispositions separately; no post-hoc adequacy threshold chosen to pass/fail 2,586.

### Q9 — CP/INCONCLUSIVE versus larger samples: **agree** with both, for different purposes

**Evidence:** The exact intervals in §5.1 show that 160/161 is a point pass but not a ≥99% population guarantee. G already calls for CP and INCONCLUSIVE; repeated val/prefix overlap further limit inference.

**Next steps:** (1) Retain the empirical selection screen and add labeled CP/INCONCLUSIVE now. (2) If a population claim is required, prospectively size a new P0 article-group-disjoint evaluation cohort, fixing confidence sidedness, expected errors and stopping rule. (3) Do not spend test 163, append easy cases, or treat within-document slots as independent documents.

### Q10 — Test release and A0/A1 history: **agree** to keep closed now

**Evidence:** R §9 and D-083 require human review before A1's one-time final-candidate evaluation; A0 used the split in D-080. VA's full-clean target audit is an additional history item.

**Next steps:** (1) Meet the freeze/review conditions in D5-2 and obtain separate authorization. (2) Log “A0 used; corpus-wide verifier audit covered clean sources/targets; A1 predictive test unrun” until an A1 run actually occurs. (3) After the authorized single run, report failure as well as success, without using the result to tune or test a second A1 candidate.

### Q11 — Fix URL false equivalence now or separate audit: **agree** to fix in v2 with a coupled audit

**Evidence:** The mismatch is a known, reproduced false accept, and VA still inherits it. Deferring correction while calling a wrap-only matcher the specified v2 would overstate safety.

**Next steps:** (1) Implement typed URL canonicalization from raw spans, avoiding global lowercasing/comma deletion and unintended NFKC changes to path/query bytes. (2) Audit newly rejected pairs as well as newly accepted wraps, preserving meaningful punctuation/escapes. (3) Publish this as v2 only; preserve v1 and do not infer net safety improvement merely because one regression example is fixed.

### Q12 — Missing Scope/DoD/API/order: **conditional** pending must-fixes

**Evidence:** D's API carries policy Booleans but no human-decision input; VA has inconsistent count/matching semantics, incomplete repair provenance, and an all-clean access path. D's DoD covers binary flips but not every changed slot acceptance.

**Next steps:** (1) Resolve the prioritized seven must-fixes in §7. (2) Add immutable adjudication records keyed to source/summary hashes and spans, policy/version hashes, reason codes, unresolved status, and raw-to-normalized offset mapping. (3) Freeze spec/input manifests first, then implement/test, human-audit all changes, rescore all systems, publish selection, conduct separately approved human 50, and only later consider separately authorized test release.

### Q13 — Can 1,940 still be exploratory human primary: **agree**, with explicit separation

**Evidence:** Its .682278 F1 and lower slot-free burden make it scientifically informative even when generic grounding is 159/161. “Human comparator” and “eligible candidate” are different roles.

**Next steps:** (1) Allow a prespecified exploratory 1,940 contrast or diagnostic study. (2) In the advancement protocol keep the policy-selected candidate as decision primary; do not let the ambiguous word “primary” imply eligibility. (3) If human findings motivate changing policy or criteria, register another exploratory decision rather than retroactively passing D-083 or generic 1,940.

### Q14 — Errors, overstatement, and omissions: **agree** that material qualifications are needed

**Evidence:** §2 documents code-to-spec gaps, incomplete v2 denominators, and test-audit exposure. Several request statements are accurate but narrower than their phrasing implies.

**Next steps:** (1) Correct the specific claims below without altering strict results. (2) Distinguish measured audit outputs from policies not implemented or directly ablated. (3) Add provenance and uncertainty to the next revision before approval.

Specific corrections/qualifications:

- **“Generic + counter alias” is not a faithful policy implementation:** no source-`명` constraint, no manual judgment, broad suffix test, and non-additive behavior. Its 1,940 160/161 is an exploratory code output, not a validated semantic rescue.
- **Audit URL behavior differs from the draft:** case/comma loss remains, source attestation is absent, summary repair evidence is not retained. A production-conforming URL change can introduce reverse flips; its final eligible set is unmeasured here.
- **“Clean v1→v2 change 0/1,617” means binary grounded flips are zero under the audit matcher.** It does not establish unchanged extraction, matching edges, missing slots, adequate summaries, or false-accept rate. The clean pool was selected by v1, making it a weak safety-only comparison.
- **Test history needs two axes:** no A1 predictive evaluation, versus previous A0 use and full-clean source/target verifier audit. The aggregate audit does not make A1 test scores available, but “completely untouched” is too strong.
- **Uniqueness wording is ambiguous:** “unit-inclusive unique” could mean one occurrence, one value+unit type, or one semantic referent. VA uses occurrence count. It does not supply entity disambiguation and can skip the correct people-count slot once an exact match consumed it.
- **Five flips are not five proven false accepts.** Two are year-looking numbers, but their truth cannot be inferred from those strings; there are six changed numeric values across five documents.
- **The tables label all v2 remaining failures as “new failures.”** IDs such as `04951` were already strict failures; “remaining unmatched/grounding failures” is clearer.
- **URL-only/no-unit sensitivity needs explicit ablation.** A report states URL repair alone fixes 1,293/2,586, and the strict failure identities support that expectation, but VA exports no per-rule-only checkpoint run and its matcher always enables qualifier/unit processing. D's URL+qualifier table is a scenario, not a proof of the final safer URL-only implementation.
- **CP convention and status semantics are absent from the draft.** One-sided versus two-sided confidence, clustered slots, reused selection and article-prefix overlap matter. A point pass is not statistical certification.
- **“Target-slot omission” is not automatically critical semantic omission**, and “only 04951 is genuine” is too conclusive without contextual adjudication of the other cases. The five 1,940/2,586 failure observations cover four distinct documents, with `04951` shared.
- **Human cost and capacity are understated if four systems are double-rated.** Fifty documents produce 200 summaries and 400 ratings, plus source-fact annotation and arbitration, not merely 50 brief judgments.
- The already corrected facts remain correct: `03978` missing **7**, `04709` missing **15** with `18명` preserved, 647 EOS passing, and v1 already stripping trailing punctuation. Do not treat broad trailing-punctuation stripping as universally safe for URLs.

## 7. Must-fix before recommending D-084 acceptance — maximum seven

1. **P0 — Do not bless the current alias implementation.** Require human evidence tied to a source people-count span and same entity/event/scope; prevent date/percent aliases, accidental loss of generic matches, and wrong-edge preservation. Retain reported alias counts only as unvalidated audit outcomes.
2. **P0 — Make the URL baseline faithful and conservative.** Separate URL canonicalization from V1's lossy canonicalizer; preserve meaningful URL components, repair both sides with auditable attestation/ambiguity handling, and test positive and negative cases. Keep time/unit policies off by default initially.
3. **P0 — Finish the human acceptance audit.** All five excluded flips, every changed accepted claim in allowed predictions/targets, reverse URL flips, and prespecified controls need evidence and adjudication. Zero confirmed false accepts and zero unresolved auto-passes; no ID-specific exceptions or training-pool expansion.
4. **P0 — Enforce and accurately describe the test boundary.** Replace all-clean rule-development inputs with explicit train/val and excluded-only manifests. Document historical aggregate source/target audit exposure separately from unused A1 predictive test. Do not rerun the existing audit main against all clean rows.
5. **P1 — Freeze policy and preserve decision lineage.** Call D-084 outcome-informed exploratory, retain strict files unchanged, specify candidate pool/fallback and tie behavior, and issue a distinct hashed `selection_v2.json` only after all gates are recomputed for all systems. No alias chosen for a preferred checkpoint.
6. **P1 — Complete the API and metric contract.** Add adjudication inputs, immutable provenance/reason codes, unresolved status and offset mapping; define unique typed slots versus occurrences and matching cardinality; report all v2 numerators/denominators, nonvacuous, slot-free, coverage, confidence convention and separate empirical/statistical statuses.
7. **P1 — Freeze the human/adequacy protocol before ratings.** Four-system paired sample, policy-selected decision primary, blinded raters, essential-fact rubric, separately labeled diagnostics, approved margins/thresholds and INCONCLUSIVE handling; preserve test sealing through an explicit disposition.

## 8. Top additional experiments and approximate cost — maximum five

These are proposed future work, **not performed or authorized by this consultation**. All inputs must remain P0 and exclude test 163. Cost estimates are planning ranges, not measured runtime guarantees.

| Priority | Experiment / purpose | Estimated incremental cost |
|---|---|---|
| 1 | Separate URL-only v2 plus synthetic regression/negative cases and explicit URL-only, qualifier-only, generic and adjudicated-alias ablations on saved permitted predictions. Establish actual policy sensitivity without regeneration. | Roughly 0.5–1 engineer-day; CPU minutes once source packets and allowlists are available. No training. |
| 2 | Blinded rule-change adjudication: five excluded flips, all changed claims, permitted collision examples and adversarial type/scope/URL controls. Distinguish legitimate repair from false acceptance. | Approximately 4–8 person-hours for a compact packet; increase the estimate if slot-level change enumeration yields many more cases. CPU audit minutes; no training/generation. |
| 3 | Paired human 50 on pilot300, 1,293, 1,940, 2,586, with separate stress panel and essential-fact annotation. Test adequacy rather than lexical overlap. | About 16–24 person-hours including arbitration: 400 ratings at ~2 minutes already require ~13.3 hours. Uses saved outputs; no new generation. |
| 4 | Prospectively planned, fresh P0 article-group-disjoint evaluation cohort for a **single frozen** model/policy, if a generalization/99% claim is actually needed. Exclude existing test and all prior tuning material; provenance review before collection/evaluation. | Curation/adjudication roughly 1–3 person-days depending on sources; evaluation CPU measured in a later approved plan. 368 IID zero-error documents is only a two-sided-95% planning floor, not a guaranteed adequate design. No such data were accessed here. |
| 5 | Fixed seed-43 replication after measurement/human protocol freeze, same train/val and predeclared checkpoint rule. Quantify training-seed sensitivity, not repair validation reuse or prove generalization. | Approximately 4.5 CPU-hours for one full run, based on the reported 4 h 20 min baseline, plus evaluation/review overhead. Separate approval required; no test use. |

A compression-control training arm is **not the immediate next experiment**. First determine whether the observed slot losses are essential-fact losses and whether apparent improvement is a length/metric confound. If humans confirm a specific compression failure, preregister a controlled arm with matched evaluation and its own budget rather than tuning minimum length or auxiliary losses until this val set looks better. Seed replication and a new objective should not be conflated as a single causal comparison.

## 9. Compact verdict table

| Item | Verdict | Recommendation |
|---|---|---|
| D4-1 | disagree | No generic-unit default now; URL-only baseline, broader policies as audited challengers |
| D4-2 | conditional | 2,586 under a validated generic rescore; no automatic product advancement |
| D4-3 | defer | 1,940 alias eligibility needs independent semantic adjudication |
| D4-4 | agree | Separate nonvacuous/adequacy/CP/INCONCLUSIVE; preserve strict gate |
| D4-5 | defer | Adjudicate all five; zero confirmed false accepts/unresolved auto-passes |
| D4-6 | agree | Fix URL case/comma in v2 with coupled audit; v1 immutable |
| D5-1 | conditional | Four-system paired human 50; policy-selected decision primary |
| D5-2 | agree | Keep test sealed through verifier, human review, freeze and separate approval |
| D5-3 | agree | Verifier correctness/audit first; defer more training |
| D5-4 | conditional | Outcome-informed exploratory D-084, not retrospective preregistration |
| Q1 | disagree | Do not approve generic as the immediate baseline |
| Q2 | conditional | Separate human-adjudicated alias clause, default off |
| Q3 | defer | Five truth labels unavailable; adopt finite-audit safety criterion |
| Q4 | conditional | Salvage valid measurement research without rewriting D-083 |
| Q5 | agree | Generic decision candidate is 2,586, not ineligible 1,940 |
| Q6 | defer | Source span/entity/scope evidence needed for 18-person alias |
| Q7 | conditional | Same 50 documents, four blinded systems, predeclared primary |
| Q8 | conditional | Explicit denominators and separately approved adequacy criteria |
| Q9 | agree | Keep point gate + CP/INCONCLUSIVE; new independent P0 sample for population claims |
| Q10 | agree | Do not open test now; disclose A0/audit/A1 histories separately |
| Q11 | agree | URL safety fix belongs in v2 with acceptance/rejection audit |
| Q12 | conditional | Repair Scope/DoD/API and access/provenance gaps before implementation approval |
| Q13 | agree | 1,940 may be exploratory human comparator/primary, not an eligible candidate by implication |
| Q14 | agree | Correct implementation, exposure, denominator and inference overstatements |

## 10. Verification performed and final recommendation

I verified synchronization and clean initial status; read the complete request/draft/audit JSON; inspected the relevant verifier, selection, evaluation and analysis code; independently aggregated the five saved validation files; reproduced the narrow synthetic matcher failures; and computed the stated binomial intervals in memory. `PYTHONDONTWRITEBYTECODE=1 python -m unittest eval.tests.test_slot_verify -v` passed **11/11** existing v1 tests. Those tests do not validate the proposed v2; the full eval suite, training, generation and corpus-audit main were not run. No source-level human adjudication was possible because the raw P0 corpora are absent. Test 163 was neither opened nor evaluated by this review.

D-083 remains a completed but unsuccessful full-train selection: no eligible checkpoint, pilot300 fallback, no product approval. D-084 can be a useful exploratory correction process if it records its outcome-informed origin, fixes URL safety rather than preserving a convenient false equivalence, and treats unit/qualifier semantics as policy choices requiring evidence. Current alias counts must not be used to promote 1,940. A faithful URL-only baseline is the lowest-risk next measurement step; generic and manually adjudicated variants should remain separately visible until validated.

After policy validation, the formal max-F1 candidate should drive the decision-primary human review—provisionally 2,586 under the reported generic/no-unit scenarios—with pilot300, 1,293 and 1,940 paired on the same blinded sample. Human findings may stop advancement or motivate another explicit exploratory decision, but cannot retroactively pass D-083 or make an ineligible checkpoint eligible. Keep test 163 closed now, preserve its full exposure history, and seek fresh, independently planned P0 evidence if the goal is a defensible population or product claim.