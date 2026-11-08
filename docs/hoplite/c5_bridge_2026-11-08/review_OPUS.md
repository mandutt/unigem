# C5 EG2 → T5Gemma2 bridge: independent external review (Opus 5.5)

- Reviewer: Hoplite / anthropic claude-opus-5-5. This is a separate review round, done without consulting any other model's answer.
- Date: 2026-11-08 (UTC)
- Sync: `git fetch origin` + `git pull --ff-only origin main` returned "Already up to date". **Reviewed HEAD = `f8c33a69c3dced040a401faf552a74437a696d02`** ("chore: add C5 bridge review dispatch and prompts"). The request names `ee084af` as its basis. The commits after it (`8eeb0d3` and `f8c33a6`) add only docs and dispatch files, so all result artifacts match `ee084af`.
- Mode: read-only. No training was run. Test 163 was not opened. No P1 data or external API was used. `eval/slot_verify.py` SHA256 was re-verified as `a262cee0…69d03` (unmodified).
- I read the full request (`reports/EXTERNAL_REVIEW_C5_BRIDGE_2026-11-08.md`, 624 lines). I then inspected `runner/c5_b1d_b2.py`, `runner/c5_b1d_generate.py`, `runner/c5_b2_slot_repair.py`, `eval/slot_verify.py`, `docs/decisions.md` (D-083, D-105~D-107), and the raw per-document JSONL/metrics in `reports/provenance/C5_b1d/` and `reports/provenance/C5_a1/`.
- I recomputed paired statistics (McNemar on grounded, paired bootstrap 5,000× on char F1, Wilson CIs) from the stored per-document rows. The script lived in `/tmp`, outside the repository. Numbers labelled **[recomputed]** below come from that script, not from the request.

---

## 1. Verdict

**STOP** the bridge as a product or replacement track. The pre-registered D-107 closure is valid and should stand. Switch to the A1 native pilot300 product path as already decided.

I do **not** recommend NARROW. No single experiment I can design could reverse the *product* conclusion:

1. **Grounding.** The bridge's per-slot hallucination rate is about **0.54–0.69** in every arm (new-slot micro). A1 native is at **0.000** (pilot300) and **0.002–0.007** (full-train checkpoints). Reaching G-C5 (doc grounded ≥ 99%) needs a per-slot rate of about ≤ 0.2% at ~5 slots per summary. That is a 250–300× reduction. Across eight arms, no intervention moved the per-slot rate by more than ~0.15 in either direction.
2. **Quality.** Even if grounding were solved by construction (constrained decoding or repair), the F1 gap to A1 is **0.25** (0.4074 vs 0.6552). The best direct-repair ceiling is **0.3203**. The largest F1 gain any bridge lever produced was **+0.061** (SS slot-aware vs layer12, CI [+0.029, +0.093] [recomputed]).

If the owner still wants one research-closure datapoint, §5 gives one **inference-only** diagnostic: source-constrained decoding. It costs about 1 CPU-hour and needs no training. It is ranked first among the remaining levers, but it is explicitly **not** a reason to reopen the track. It also cannot overturn STOP unless it meets a bar that I expect it to miss (F1 ≥ 0.55 with grounded ≥ 99% on val100).

---

## 2. Key independent findings (from raw artifacts)

### F1. The slot-aware "partial recovery" is statistical noise
Paired on the same 100 IDs [recomputed]:

| comparison | grounded lost → gained | McNemar p | ΔF1 (95% bootstrap CI) |
|---|---|---:|---|
| layer12 → SS | 17 → 6 (21%→10%) | **0.035** | +0.032 [−0.003, +0.066] |
| layer12 → SS slot-aware | 16 → 7 (21%→12%) | 0.093 | **+0.061 [+0.029, +0.093]** |
| SS → SS slot-aware | 5 → 7 (10%→12%) | **0.77** | +0.029 [−0.003, +0.061] |
| layer12 → layer9 | 14 → 15 (21%→22%) | 1.00 | −0.012 [−0.049, +0.026] |
| gold300(final768) → layer12 | 14 → 17 | 0.72 | +0.012 [−0.017, +0.043] |

- SS reduces grounded (p = 0.035). Slot-aware masking does **not** measurably recover it: 10 → 12 is 5 docs lost and 7 gained, p = 0.77.
- The "layer9 paradox" is **not significant** in either F1 or grounded. Treat it as noise rather than a mechanism.
- Wilson 95% CIs: 12/100 → [7.0%, 19.8%]; 20/100 → [13.3%, 28.9%]; 21/100 → [14.2%, 30.0%]; 22/100 → [15.0%, 31.1%]. On n = 100, a grounded DoD of 20% cannot separate 12% from 20% with much power. It did exclude 20% narrowly (upper CI 19.8%).

### F2. The grounding collapse is driven by slot volume, not by worse per-slot fidelity
[recomputed, val100]

| system | summary slots/doc | new slots/doc | per-slot new rate | grounded | pred chars (gold 321) |
|---|---:|---:|---:|---:|---:|
| A1 native | 5.1 | 0.00 | 0.000 | 100 | 283 |
| gold300 (final768) | 6.2 | 4.72 | 0.76 | 18 | 383 |
| layer12 300 | 6.0 | 3.22 | 0.54 | 21 | 443 |
| layer9 300 | 5.1 | 3.53 | 0.69 | 22 | 454 |
| layer12 SS | **9.7** | 5.94 | 0.61 | 10 | 420 |
| layer12 SS slot-aware | **8.6** | 4.80 | 0.56 | 12 | 397 |

Grounded vs number of emitted slots: layer12 has 0 slots 4/4, 1–3 slots 14/31, 4–8 slots 3/41, ≥9 slots 0/24. SS slot-aware has 3/3, 5/11, 4/54, 0/32. Doc-level grounded is roughly (1 − p_slot)^k. With p_slot ≈ 0.55, a summary with ≥ 4 slots is almost never grounded. SS made the model emit **43–60% more slot tokens** at about the same per-slot hallucination rate, so doc-level grounded fell. Char F1 rose partly because digits and units overlap gold characters even when the values are wrong.

This is a real mechanism, but its target is **slot volume**, not "context contamination". Any DoD on doc-level grounded therefore partly measures how *few* slots a model emits.

### F3. The SS experiments have no "continue training without SS" control
Both D-106 and D-107 start from `b2_layer12_300/adapter_final.pt` and add **one more epoch at lr 1e-4** (`*_ss_metrics.json` `init`, `epochs`, `lr`). There is no arm with `--ss-prob 0` and the same extra epoch. The +0.03 to +0.06 F1 and the grounded change therefore cannot be attributed to scheduled sampling rather than additional low-lr training.

### F4. The `grounded` definition in the request does not match the code
- §2.3 defines grounded as "source slot preservation + no new slot". `runner/c5_b1d_generate.py` sets `grounded = not rep.new`, which checks only for no new slots. Preservation is ignored. The A1 pipeline uses the same rule (`c5_a1_verifier_v2_audit.py`), so the comparison is consistent, but the document is wrong.
- §2.1 says slots include proper nouns (고유명사). `slot_verify._PATTERNS` covers url/path/date/time/version/Latin identifier/number only. **Korean named entities are not verified.** Bridge outputs visibly invent names (for example, `REPORT-news_r-00430-00001` contains invented people and programme names and is flagged only for 2 numeric slots). So grounded **overstates** bridge fidelity, and it also leaves A1's entity hallucination unmeasured.

### F5. Teacher-forced "fidelity" is measured on val100 against the A1 teacher, not on train
All `b2_*_fidelity_teacher.json` files have `n: 100`, `target: "teacher"`, and evaluate the first 100 val IDs that have teacher predictions. §5.2 labels the column "train n" with values 99/300, which is wrong for at least the gold300, layer12, layer9, SS and SS slot-aware rows (verified). The models are trained on **gold**, but fidelity is scored against **A1 teacher** text. Layer9's higher fidelity therefore means "closer to A1 under teacher forcing", which need not predict gold char F1. This explains a good part of the "paradox".

### F6. Provenance gaps
- `b2_layer12_300_ss_metrics.json` records `ss_prob: null` and `ss_slot_aware: null`. The D-106 report and decision log say ss_prob 0.2, but the run artifact does not record it.
- `b2_layer12_300_metrics.json` records `feature_dir: null` and `input_dim: null`, although it is the layer12 run (older code path). Reproducing it requires the report, not the artifact.
- Only one seed (`20261107`) is used anywhere in the bridge series.

### F7. Pre-registration is genuine but conditioned on D-106
`git log` shows the D-107 DoD table was committed in `adc08f2` (16:28:59 KST, "feat: add slot-aware scheduled sampling") **before** the result commit `ee084af` (17:26:04). It was written after D-106 was known, and the threshold "grounded ≥ 20%" means "recover to the layer12 baseline of 21%". That is legitimate pre-registration for a recovery test. It is not post-hoc rationalisation.

### F8. A1 numbers check out
Re-reading `C5_a1/pilot300_val161/predictions.jsonl` on the 100 bridge IDs gives F1 **0.6552**, grounded 100/100, EOS 100/100, 0 new slots. Targets match the bridge rows 100/100. Full-train checkpoints (`full_2ep/selection_summary.json`) reach F1 0.666–0.682 with grounded 96.3–98.8%, i.e. 2–6 failures out of 161, and per-slot new rate 0.002–0.007.

---

## 3. Q1–Q12

### Q1. Bridge premise: is STOP correct?
**Verdict: agree (STOP).**
- Evidence: A1 0.6552/100/100 vs best bridge 0.4074/12/69 on identical IDs (F8). The F1 gap is 0.25. The per-slot hallucination gap is about 0.55 vs about 0 (F2), and it stayed in the 0.54–0.76 band across feature layer, adapter width, decoder rank, data size (300 vs 1,293), SS and slot-aware SS. The best grounded-forced F1 is 0.3203 (§5.4). The bridge goal (reuse EG2 as a resident encoder) is a cost or architecture goal, but the bridge does not reach even the floor quality that would make that saving worthwhile.
- No single falsification experiment can flip the product decision. It would have to close both a 250× slot-fidelity gap and a 0.25 F1 gap. The most informative inference-only test is constrained decoding (§5, E1), and success would only show "grounded but half-quality".
- Next steps: (1) Record STOP as final for the B-family product path and freeze the bridge artifacts. (2) If research closure is wanted, run only E1 as a separately registered diagnostic that cannot reopen the track below the §5 bar. (3) Redirect effort to A1 productisation checks (Q9 and Q11).

### Q2. Was the D-107 termination post-hoc?
**Verdict: agree (not post-hoc), with a caveat on DoD design.**
- Evidence: The DoD was committed in `adc08f2`, 58 minutes before results in `ee084af` (F7). Grounded 12% is outside the threshold, with Wilson upper bound 19.8%.
- Caveat: the DoD was a *recovery* test against a 21% baseline, far below the G-C5 product gate of 99%. Passing it would not have produced a product candidate. On n = 100, the 20% grounded threshold has low resolution (F1). And because doc-level grounded depends on slot count (F2), the DoD partly rewarded emitting fewer slots. The DoD was weak in that sense, but it was not inappropriate for its stated purpose: deciding whether slot-aware SS undid the SS damage. The answer is no, and the track-level STOP rests on stronger evidence (Q1) anyway.
- Next steps: (1) Keep the D-107 verdict unchanged; do not reinterpret it post hoc. (2) For any future registered experiment, add the per-slot new rate and a minimum sample/CI rule to the DoD. (3) State explicitly in D-107 that the track STOP rests on the 250× slot-fidelity gap plus the F1 gap, not on one 12% vs 20% reading.

### Q3. Why did SS raise F1 and lower grounded? Was the slot-aware mask insufficient?
**Verdict: conditional.** Mostly (a) plus slot volume. (b) is unproven, (c) is not intrinsic, and (d) applies partly.
- Evidence:
  - SS shifts behaviour toward emitting more slots (6.0 → 9.7 per doc) at roughly constant per-slot hallucination (0.54 → 0.61). Doc-level grounded falls mechanically (F2).
  - The implementation (`ce_scheduled`) is one-pass "parallel" SS. Student argmax comes from a teacher-forced pass, so corrupted inputs are teacher-forced predictions, not true free-running prefixes. Labels stay gold. Training gold digits to be emitted after corrupted context teaches "produce numbers regardless of context", which is mechanism (a).
  - The slot-aware mask aligns correctly: `protect[j]` guards gold token j at decoder-input position j+1. It protects the slot *inputs* but not the slot *labels* after corrupted context, so the same pressure remains. Its effect on grounded is null (p = 0.77, F1).
  - On (c): A1 achieves F1 0.655 and 100% at the same time, so there is no intrinsic F1–grounding trade-off. The apparent trade-off is specific to this bridge.
  - On (d): partly a measurement artifact. Grounded is a binary function of slot count, char F1 rewards digit-character overlap, and there is no continuation control (F3). So "SS improves F1" is not causally established. The +0.032 F1 of plain SS has a CI that includes 0.
- Next steps: (1) Report per-slot new rate and slots/doc alongside grounded for every arm. (2) If anything is re-run (not recommended), add the missing control: 1 epoch, lr 1e-4, `--ss-prob 0`, same init. (3) Retire the "context contamination" explanation unless that control shows SS-specific damage.

### Q4. Layer9 paradox
**Verdict: disagree that a paradox needs explaining.** It is mostly a limitation of the teacher-forced metric, plus noise.
- Evidence: The layer9 vs layer12 F1 difference is −0.012 with CI [−0.049, +0.026], and grounded is 15 vs 14 discordant (F1). Fidelity is scored on val100 against the **A1 teacher**, while training uses gold (F5). Layer9 has fewer slots per doc (5.1) but a higher per-slot rate (0.69). The literature cited in §6.5 ("Cosine misleads") agrees that the proxy is poor.
- Layer9 full 1,293 is not worth running. B2 full 1,293 (final768) gave val161 0.3349/18% vs 300-doc val100 0.3341/18%, so 4× more data did not move the target metric, and layer9 is indistinguishable from layer12.
- Next steps: (1) Relabel §5.2 as "val100 vs teacher" (F5). (2) Drop teacher-forced fidelity as a selection criterion for generation tracks. (3) Do not run layer9 full.

### Q5. Is 300 docs enough to conclude?
**Verdict: agree for the STOP decision.** The data-scale information value is low.
- Evidence: Full 1,293 (final768) vs gold300 (final768): val100 0.3128/15% vs 0.3341/18%. More data did not improve the free-running metrics on the same subset. Per-slot hallucination of 0.76 at 300 docs was still roughly in the same band at 1,293 (val161 grounded 18%). A1 pilot300, trained on 300 docs, reaches 0.6576/100%. With the *same 300 docs*, native encoding solves the task and the bridge does not, which points to the information path rather than data volume.
- Next steps: (1) Do not run full 1,293 layer12 or SS. Even an optimistic +0.03 to +0.05 F1 leaves a gap of at least 0.20 and no grounding mechanism. (2) Add an explicit "same 300 docs, A1 vs bridge" row to the comparison table, because it is the strongest scale-controlled evidence. (3) If a scale check is ever required, use the cheapest one: a learning-curve point at 600 docs, under a pre-registered rule to stop if ΔF1 < 0.03.

### Q6. Slot repair: is the 0.3203 ceiling a repair problem or a generation problem?
**Verdict: agree that generation grounding is the root bottleneck.** Replacement or rewrite would add little.
- Evidence: An average of 2.12 out of 3.27 sentences per summary contain a new slot (`slot_repair_ss_slot_val100.json`). Dropping them removes about two thirds of the content. Even the target-aware **oracle** subset reaches only 0.3203 (non-deployable ceiling). Slot *replacement* (mapping a hallucinated number to a source number) can at most fix values. It cannot fix invented entities (F4) or wrong propositions around the slot, and with a 0.55 per-slot error the correct source value is ambiguous for most slots.
- A rough bound: replacement keeps sentence length, so F1 could move back toward the original 0.407, but not above it, and the correctness of the result is unverifiable. It only makes the output look grounded.
- Next steps: (1) Treat repair strictly as a safety filter, which matches D-093. (2) Do not develop replacement or rewrite for the bridge. (3) If slot replacement is ever explored, do it on A1 full-train checkpoints, where only 2–6 out of 161 docs fail. That is a separate, pre-registered A1 track, not a bridge track.

### Q7. Slot auxiliary vs copy vs constrained decoding vs B2 full: ranking, DoD, prior
**Verdict: conditional.** Rank only if the owner overrides STOP for research purposes.

| rank | lever | why | DoD (val100, slot_verify unmodified) | stop condition | prior P(meets DoD) |
|---|---|---|---|---|---|
| 1 | **Source-constrained decoding** (inference-only) | Attacks the binding failure (new slots) directly and cheaply. Costs about 25 min of generation per arm on CPU and needs no training. Makes new numeric slots impossible by construction. | grounded ≥ 95% **and** F1 ≥ 0.40 (no worse than unconstrained) **and** EOS ≥ 60%; per-slot new rate ≤ 0.02 | F1 < 0.38 or grounded < 90% → close. Even if passed, F1 < 0.55 means research note only, no product claim. | grounded ≥ 95%: ~70% (numeric kinds dominate). F1 ≥ 0.40 at the same time: ~35%. F1 ≥ 0.55: < 3%. |
| 2 | Copy/pointer over H_s | Directly targets copying. But the merged-attention decoder has no separate cross-attention head to reuse, H_s is an adapter projection of a frozen retrieval encoder (projector bound, §6.5), and it needs new architecture plus training on CPU. | grounded ≥ 50%, per-slot new ≤ 0.10, F1 ≥ 0.40 | No grounded gain ≥ +15pp after 1 epoch on 300 docs → stop | ~15% for that DoD; < 5% for product-level (≥ 99%, F1 ≥ 0.55) |
| 3 | Slot auxiliary head | Indirect, and the per-slot error band did not move under any loss or feature change. Probably teaches *where* slots go, not *which value*. | per-slot new ≤ 0.35 and grounded ≥ 25% | No per-slot improvement ≥ 0.10 → stop | ~10% |
| 4 | B2 full 1,293 (layer12/SS) | Already tested in spirit (D-092). Data did not move grounding. | F1 ≥ 0.45 and grounded ≥ 30% | — (do not run) | < 5% |

- Next steps: (1) If anything runs, run only rank 1, inference-only, at most 2 CPU-hours. (2) Do not start rank 2–4 without first seeing rank 1's per-slot result. (3) Register the DoD and stop conditions above before running.

### Q8. Metric: is grounded too harsh? Is A1's 100% an artifact?
**Verdict: conditional.** Grounded is not too harsh on the bridge (it is, if anything, lenient), and A1's 100% is real for the slot kinds it checks.
- Evidence: Grounded checks only new slots and ignores preservation (F4). It does not check Korean named entities, so bridge entity hallucinations pass unnoticed. A1's 100% is consistent with A1 full-train per-slot rates of 0.002–0.007 (F8). That is not "teacher copy". A1 pilot300 emits 5.1 slots per doc and preserves 44% of source slots, so it is not winning by emitting no slots. Copy bias exists (PLATE-style copy4 in teacher audits), but copying from the source is legitimate for grounding.
- How to combine: use a **gate then rank** rule, as D-083 already does. First, the safety gate: doc grounded ≥ 0.99 and per-slot new ≤ 0.01. Then rank by char F1. Never average F1 with grounded.
- Next steps: (1) Fix the §2.3 definition to match the code. (2) Add an entity-level audit (human-50 or a P0 NER-based check, without modifying the production verifier) for A1 before product promotion. (3) Report per-slot new rate and slots/doc as secondary metrics so doc-level grounded is not confounded by volume.

### Q9. A1 native product path: fix pilot300? Re-evaluate full 1,940/2,586?
**Verdict: agree to fix pilot300 as the product candidate. Defer** re-evaluating the full checkpoints.
- Evidence: Pilot300 val161 0.6576 / 161/161 / EOS 100% / rep4 0.055 passes the pre-registered D-083 gate (grounded ≥ 0.99, new ≤ 0.01, EOS ≥ 0.95, rep4 ≤ 0.06). Full-train checkpoints fail grounded at 96.3–98.8% (2–6 failures out of 161), and step 647 also fails rep4. Step 1940 has F1 0.682, but 3 out of 161 docs fail. Pilot300 at 161/161 vs step 1940 at 158/161 is not statistically distinguishable at n = 161, but changing the gate after seeing results is forbidden, so the fallback stands.
- Caveat: val161 has been reused for many A1 choices (prompt variants, lr, pilot sizes; `C5_a1/*` directories), so 0.6576 is a dev-set estimate with some adaptive optimism.
- Next steps: (1) Freeze pilot300 (`pilot300_lr2e4_prefix.pt`), recording its hash and the generation config. (2) Do not re-evaluate full checkpoints under the current gate. If desired, register a *future* separate proposal for "full ckpt + drop-new slot filter", but do not apply it retroactively. (3) Run the minimal validation in Q11.

### Q10. Comparison fairness and selection bias
**Verdict: conditional.** The core A1-vs-bridge comparison is fair. Secondary comparisons have bias.
- Evidence: The A1 vs bridge val100 comparison uses the same 100 IDs and the same targets, which I verified (F8). It is fair. Sources of bias:
  - (i) **Teacher train100** is the 100 longest-sorted docs, so its F1 of 0.6697 is not comparable with val.
  - (ii) Fidelity is scored against the teacher on val100 but labelled as train (F5).
  - (iii) val20 numbers are used for some decisions (D-096, D-102 r16 at 0.2765 vs r8 at 0.3623) and are too small for that. The request itself notes val20 0.3664 vs val100 0.3341 for gold300 as optimistic.
  - (iv) val100 has been used to select feature layer, width, rank and SS. Adaptive reuse slightly inflates all bridge numbers, which only strengthens STOP.
  - (v) gold300 (final768, EOS 67%) is missing from §5.3. It shows that EOS 69% for SS slot-aware is not unique.
- Next steps: (1) Add gold300 to §5.3 and drop val20-based claims from the H3 evidence. (2) Add paired CIs (bootstrap ΔF1, McNemar on grounded) for every headline comparison. (3) Label every number with its eval set (val100, val161, val20) and target (gold or teacher).

### Q11. Stop criteria if the bridge continues; validation needed for A1
**Verdict: agree that criteria are needed.** They are given here.
- If the bridge continues (not recommended):
  - Total budget is at most **2 CPU-hours**, inference-only (E1).
  - Any training-based bridge experiment requires a new decision record.
  - Stop immediately if per-slot new rate > 0.10, or if F1 with grounded ≥ 95% is below 0.40.
  - Product consideration requires F1 ≥ 0.55 **and** grounded ≥ 99% on val100 and val161. Anything less is filed as research.
- A1 minimal validation before promotion (no test 163, no P1):
  - (a) Reload determinism: reproduce the val161 metrics from the frozen checkpoint. `pilot300_reload_check` exists; confirm it matches exactly.
  - (b) Paired bootstrap CI on val161 F1 and Wilson CI on grounded (161/161 → lower bound about 97.7%).
  - (c) An entity-hallucination audit on a P0 sample (human-50 per D-083) covering the slot kinds `slot_verify` does not check.
  - (d) CPU latency and memory on the target device, plus input-length truncation behaviour for long documents.
- Next steps: (1) Write these A1 checks into a decision record before running them. (2) Add the E1-only budget cap to D-107 if a diagnostic is approved. (3) Any further use of the sealed test follows only the existing D-083 plan and the owner's decision; this review does not propose it.

### Q12. Must-fix (top 3)
**Verdict: agree.** The items:
1. **Fix the metric definitions and labels.** Grounded is "no new slot", not "preservation + no new". Korean proper nouns are not covered. Fidelity is val100 vs teacher, not train. Severity: High. Fix §2.1, §2.3, §5.2 and the D-106/D-107 text.
2. **Fix causal attribution of SS.** There is no 1-epoch no-SS continuation control (F3). The slot-aware recovery is not significant (p = 0.77). The layer9 paradox is not significant. Severity: High. Restate D-106/D-107 conclusions as "SS-arm vs continuation not separated; slot-aware ≈ SS on grounding". If kept, add paired CIs.
3. **Fix reproducibility and provenance.** `b2_layer12_300_ss_metrics.json` has `ss_prob: null` and `b2_layer12_300_metrics.json` has `feature_dir: null`. Everything uses a single seed. Severity: Medium. Backfill via an addendum note (do not rewrite the artifacts) and record the generation config (greedy, max_new 448) in every metrics file.

---

## 4. Issue table

| # | severity | issue | evidence | fix |
|---|---|---|---|---|
| 1 | High | `grounded` in the document ≠ code | §2.3 vs `c5_b1d_generate.py: grounded = not rep.new` | Correct the document; report preservation separately |
| 2 | High | Korean named entities unverified; bridge invents names | `slot_verify._PATTERNS`; sample `…00430-00001` | Entity audit for A1 before promotion; state the limitation |
| 3 | High | No continuation control for SS | `init=b2_layer12_300`, +1 epoch at lr 1e-4 | Restate the attribution; control only if the track reopens |
| 4 | High | Slot-aware "recovery" and layer9 "paradox" not significant | McNemar p = 0.77 / 1.00; ΔF1 CI includes 0 | Add paired CIs to all headline claims |
| 5 | Medium | Doc-level grounded confounded by slot volume | slots/doc 6.0 → 9.7; grounded by slot bin | Add per-slot new rate and slots/doc to DoDs |
| 6 | Medium | §5.2 "train n 300" is actually val n = 100 vs teacher | `b2_*_fidelity_teacher.json` n = 100, target = teacher | Relabel |
| 7 | Medium | Provenance nulls (ss_prob, feature_dir) | metrics JSONs | Addendum |
| 8 | Medium | val20 used for decisions (D-096, D-102) | §4, H3 | Use only val100 or larger for verdicts |
| 9 | Low | Single seed throughout | `torch.manual_seed(20261107)` | Note as a limitation |
| 10 | Low | Over-length outputs (397–454 chars vs gold 321, A1 283), and 31–45% of outputs never emit EOS (truncated at 448 tokens) | per-doc rows | Report F1 stratified by EOS (no-EOS F1 about 0.18–0.23 vs EOS about 0.41–0.49) |

---

## 5. Next experiments (maximum 2)

**E0 (recommended, not an experiment): A1 pilot300 freeze and validation** (Q11 a–d). Cost: about 0.5 CPU-day plus the human-50 audit time. DoD: exact reproduction of val161 metrics, a recorded CI, and an entity audit with ≤ 1 out of 50 entity hallucinations (or the owner's pre-registered threshold). Stop if reload does not reproduce: investigate before anything else.

**E1 (optional research closure, separate registration): source-constrained decoding on the frozen D-107 checkpoint.**
- Method: at generation time, a logits processor allows a digit- or Latin-slot-bearing token only if the running slot span is a prefix of some source slot surface string. Otherwise it masks that token. Same greedy decoding, max_new 448. Score with the unmodified `slot_verify`.
- Cost: about 25 minutes of generation per arm on CPU (measured unconstrained: 1,234 s per 100 docs), so about 1 hour for 2 arms (layer12 300 and SS slot-aware) and at most 2 CPU-hours including implementation checks. No training.
- DoD (register before running): grounded ≥ 95%, per-slot new ≤ 0.02, F1 ≥ 0.40, EOS ≥ 60%.
- Interpretation: passing only shows that grounding can be imposed. The bridge stays non-product unless F1 ≥ 0.55 with grounded ≥ 99%.
- Stop: F1 < 0.38 or grounded < 90% → close permanently. No follow-on training arms in any case without a new decision record.

---

## 6. Numerical inconsistencies and omissions in the request

1. Base commit `ee084af` vs current HEAD `f8c33a6`. The later commits are docs only (benign), but the document should note them.
2. §2.3 grounded definition ≠ code (F4). §2.1 lists proper nouns, which the verifier does not cover.
3. §5.2 column "train n" (99/300) vs artifacts `n: 100`, val, target teacher (F5). §5.5 also says "val100 teacher-forced" for D-095, which conflicts with the "train n 99" row in §5.2 for the same 2.7705 figure.
4. §5.3 omits gold300 (val100 0.3341 / 18% / EOS 67%), which is relevant to the EOS and F1 claims.
5. H3 cites r8 val20 F1 0.3623, which appears nowhere else in the document, and compares val20 numbers.
6. `docs/decisions.md` D-107 gives the best grounded as "21% / F1 0.3464". The request (§1.2) correctly says layer9 22%. This is an internal inconsistency, though not significant (F1).
7. Preservation 0.3656 (§5.3) vs 0.1621 (§5.4) for the same system. The §5.4 value is post-repair, but the column label does not say so.
8. D-106's run artifact lacks `ss_prob` (F6).
9. §1.3 presents D-107 as the bridge-ending criterion, but the stronger justification (the per-slot hallucination gap and the F1 gap) is never quantified in the document.

---

## 7. Answers to §11 requested items

1. **Most important methodological defect:** headline mechanism claims (SS effect, slot-aware recovery, layer9 paradox) without paired significance tests or a continuation control, combined with a doc-level grounded metric confounded by slot volume and mis-defined in the document.
2. **Next experiments:** E0 (A1 freeze and validation). E1 is optional and inference-only (§5).
3. **Numeric inconsistencies:** §6.
4. **Maximum allowed bridge cost:** at most 2 CPU-hours, inference-only, no new training, under a separate registration. Anything more requires a new decision record and is not recommended.
5. **Minimum A1 validation before productisation:** Q11 (a) reload reproduction, (b) CIs, (c) entity-hallucination audit, (d) latency, memory and long-input behaviour.

*No repository file other than this report was written. Test 163 was not accessed. No gate change is claimed or proposed as approved. Bridge results are exploratory and kept separate from the A1 native product fallback.*