# Hoplite review — W2B domain/length controls (round `w2b_domain_length`)

- Reviewer: Opus 5.5 (reasoning level: medium), Hoplite. This is an independent round and is not a duplicate of the `w2b_v2_gate` threads.
- Input: `reports/EXTERNAL_REVIEW_W2B_DOMAIN_LENGTH_2026-11-05.md`. I read all 740 lines.
- Sync: `git fetch origin` succeeded. `git pull --ff-only origin main` reported "Already up to date". HEAD = `857eed071ff9be82e41d705862c0b17659ec3bf4` ("chore: prepare w2b_domain_length review dispatch"). The review request itself cites `069879f` as its basis.
- Scope: consultation only. I created no files other than this report and modified nothing. I ran **no training or decoding**. Every new number in this review comes from read-only Python analysis of files already committed:
  - `reports/provenance/W2B/devpred_*.json`
  - `testpred_*.json`
  - `*_bootstrap.json`, `domain_controls_budget.json`
  - `data/wave2b/short_4h_v2.jsonl`
  - `eval/normalize.py`
  - `reports/W2B_b3_v2.md`
  - `train/d5_reader.py`
  - `runner/w2b_select_{kspon,zeroth}_long.py`

---

## 0. Verdict

**B — accept with caveats.** Three conclusions hold:

- The same-length Kspon-vs-Zeroth result supports a large **Kspon-source advantage**. It does not support a "domain effect" in a narrow mechanistic sense.
- The length conclusion is correctly left **undetermined**.
- The Zeroth-long substitution is acceptable as long as it is described honestly.

Two things must change before any public claim. The public sentence needs rewording, and the step-matched B3-long arm needs to run.

Answers to the five items section 12 asks for:

1. **Minimum experiment to add now:** step-matched B3-long. Use `--batch 2 --grad-accum 4` → `--grad-accum 2`, 12 epochs, `--patience 99`, final-epoch CER pre-registered (exact spec in Q2).
2. **Claim not to make now:** that the B3 gain is a "short-utterance / short 4h data effect", or that it is 2.06 %p.
3. **Condition for moving to LoRA:**
   - LoRA *implementation and GPU smoke* may start now; it is not blocked.
   - Any LoRA *claim* needs three things first: a fresh, pre-registered holdout; a matched no-LoRA comparator (same data, steps, schedule and seed set); and the vocabulary frozen before the holdout is built.
4. **Can the domain conclusion stand without non-Kspon short 4h?** Yes, scoped as "at 8–16 s training length, evaluated on Kspon eval_clean dev". Domain-at-short and any domain×length interaction remain untested. A no-download 1.66 h hour-matched control can test them (Q3).
5. **Exact step-matched B3-long design:** see Q2.

---

## 1. Q1–Q11

### Q1. Domain conclusion — **B**

**Judgment:** The direction and size of the effect are robust. The label "domain" is too broad, and it hides several separable sources.

**Evidence:**

- **Matched comparison.** B3-long 0.283946 vs B3-zeroth-long 0.365571. Δ −8.16 %p, CI [−9.21, −7.16]. Matched on: 8–16 s, ~4.00 h added, ~10.01 h total, natural sampler, steps 5,568 vs 5,676, same init, same V2 vocab, same seed.
- **Size vs noise.** Δ is about 8× the CI half-width. It is also about 16× the spread among B0′-12/20/38 (≤0.5 %p). One seed is very unlikely to flip it.
- **The advantage holds in every dev length bin** (my read-only breakdown by normalized reference length; CER = Σerr/Σchars inside each bin):

  | ref chars | n | chars | B0′ | B3 | B3-nat | B3-long | B3-zeroth-long |
  |---|---:|---:|---:|---:|---:|---:|---:|
  | <8 | 165 | 779 | 0.526 | 0.343 | 0.325 | 0.394 | 0.523 |
  | 8–15 | 161 | 1,753 | 0.405 | 0.285 | 0.259 | 0.301 | 0.394 |
  | 16–29 | 100 | 2,057 | 0.353 | 0.264 | 0.269 | 0.275 | 0.361 |
  | ≥30 | 74 | 3,166 | 0.323 | 0.243 | 0.247 | 0.253 | 0.315 |

- **What "Kspon vs Zeroth" bundles together:**
  - (a) *Speaking style:* spontaneous conversational vs read, news-like sentences.
  - (b) *Eval-corpus match:* dev is Kspon itself, so the comparison is "in-distribution vs out-of-distribution training data", which is expected to win.
  - (c) *Transcription conventions.* `clean_kspon` keeps the first alternative of `(A)/(B)` dual transcriptions, i.e. the spelling form such as digits. 39/500 dev refs contain digits. One dev example: the ref is `…26일…25일날…`. B3-long outputs digits (`20육일…205일`); B3-zeroth-long outputs Hangul numerals (`이십육일…이십오일`).
  - (d) *Speakers, channel and recording.*
  - (e) *Selection asymmetries.* Kspon long used a 10 %-per-folder cap (`FOLDER_CAP_SEC=1440`); Zeroth long had no speaker cap. OOV exclusion was 7.33 % vs 4.47 %.
  - (f) *Redundancy.* Zeroth is already in Wave 1 (1,534 clips), so the Zeroth arm adds "more of a corpus the model has already seen" rather than "a new non-Kspon source".

**Required action:**

- Rename the claim to **"Kspon-source (in-distribution) training-data advantage at matched 8–16 s length"**.
- Do not imply that a mechanism has been identified.
- Optional and cheap, not blocking: a sub-hypothesis diagnostic with no retraining on the existing devpreds:
  - (i) CER on refs with digits/Latin characters vs without;
  - (ii) CER after mapping numerals to a single form;
  - (iii) error rate on high-frequency discourse markers and fillers (그니까, 이제, 막, 같애).

  This shows how much of the 8 %p comes from transcription convention rather than acoustics or style.

**Blocking:** It blocks the public wording only. It does not block the next experiment or LoRA.

### Q2. Length conclusion — **B**

**Judgment:** Correct, the length effect is not established. The evidence I found points both ways, which strengthens "undetermined" and makes the step-matched arm decisive.

**Evidence:**

- **Confound.** B3-nat runs 11,196 steps; B3-long runs 5,568. Per-step audio is ~38.6 s vs ~77.6 s. Total exposure is the same: 12 × ~10 h ≈ 120 h each.
- **Signal favoring a length-distribution effect.**
  - The B3-nat − B3-long gap sits in short refs: <8 chars 0.325 vs 0.394; 8–15 chars 0.259 vs 0.301.
  - It almost vanishes for longer refs: 16–29 chars 0.269 vs 0.275; ≥30 chars 0.247 vs 0.253.
  - A pure step-count effect would more naturally be spread across bins, though that is not guaranteed. Dev is short-heavy (326/500 refs <16 chars), so what is being tested is really **train/eval length-distribution match**, not "short data is intrinsically better".
- **Signal favoring step/optimization.** `reports/W2B_b3_v2.md` shows B3 balanced at epoch 6 (≈5,598 steps, half the exposure, mid-cosine and not annealed) at dev 0.2814. That is ≈ B3-long's *final, annealed* 0.2839 at 5,568 steps. At roughly equal steps, the gap shrinks from ~1.6–2.1 %p to ~0.25 %p. The comparison is biased in both directions (B3 is not annealed but also sees less exposure), so it is suggestive only. B3-nat per-epoch values are not in the request; pull its epoch-6 dev CER from the log as a free extra point.
- **Saturation prior.** B3-long's best was epoch 9 (0.2828) and its final 0.2839, which looks like a plateau. B0′ did not benefit from 2–3× more steps. Both suggest extra steps may not help B3-long much. This is a prediction, not evidence.
- **Length is also confounded with content.** Long Kspon clips carry more complex sentences and had a higher OOV exclusion rate (7.33 % vs 2.38 %).

**Exact step-matched design (minimum):**

- **Arm `b3long_sm_v2_s42`:** identical to B3-long (same 10 h Kspon-long cache, init, V2, seed 42, natural sampler, LR, weight decay, clip 5.0, threads), with these changes:
  - `--batch 2 --grad-accum 2` (keeps micro-batch composition and padding identical to B3-nat; only accumulation changes);
  - `--epochs 12 --patience 99`;
  - pre-register **final-epoch** dev CER.
- **What it produces:** 928 steps/epoch → **11,136 steps**, vs 11,196. Exposure stays 120 h. Audio per step is ≈38.8 s, matching B3-nat's ≈38.6 s. Cosine `T_max` rescales automatically, since `epochs * len // (batch*grad_accum)` appears in `d5_reader.py`. Wall time is about the same as B3-long (~1.5 h), because the number of micro-batches does not change.
- **Why not `batch=1, grad_accum=4`:** it gives the same 4 clips per step but changes micro-batch composition and padding relative to every other arm. That adds a second change for no benefit.
- **Remaining difference:** clips per update are 4 instead of 8, at unchanged peak LR. CTC uses `reduction='mean'` (per-utterance length-normalized, then averaged over the batch), so gradient noise roughly doubles. That is why a bracket arm is useful.
- **Replay (24 epochs at grad_accum 4) as the minimum?** No. It matches steps and clips per step but doubles exposure (240 h) and repetition. Run it only as an optional **second bracket arm** (`b3long_rep2`). If both the sm arm and the replay arm stay ≥1 %p worse than B3-nat, the length conclusion is robust to the matching choice.
- **Pre-registered decision rule (dev 500, paired bootstrap B=20,000, seed 42):**
  - If B3-nat − B3-long-sm ≤ −1.0 %p and the CI excludes 0: "Kspon train/eval length-distribution match contributes (exploratory, dev-only, one seed)".
  - If the CI includes 0: "no length effect detectable once steps are matched".
  - Either way, report the per-bin table above.

**Blocking:** It blocks any length claim. It does not block LoRA engineering.

### Q3. Zeroth-long substitution — **B**

**Judgment:** Methodologically acceptable as a documented deviation (D-074a). It is not a decisive flaw for the domain-at-long claim. It does leave the 2×2 factorial incomplete, so domain-at-short and the domain×length interaction remain untested.

**Evidence:**

- 1.657 h of eligible Zeroth short data remained, almost all 4–8 s and none 0–2 s. A 4 h arm was impossible without new data.
- The substitute is a clean same-length comparison.

**Required action:**

- **Cheaper than downloading FLEURS train:** an hour-matched control at **1.66 h** with no new data.
  - Arm 1: B0′ + Zeroth short (all 1,012 clips, 1.657 h).
  - Arm 2: B0′ + a Kspon short subsample from `short_4h_v2`, matched to the Zeroth short duration histogram (2–4 / 4–6 / 6–8 s bins: 52 / 548 / 412 clips or equal hours) and to the step count.
  - Same V2 vocabulary, seed and sampler; dev-only.
  - The domain effect is ~8 %p at long length, so a 1.66 h control has enough power to detect a large domain effect at short length.
- **FLEURS train:** not recommended now. FLEURS dev is the guardrail, so training on FLEURS train changes what the guardrail means. FLEURS ko is read Wikipedia text with long-ish utterances, so a 4 h 0.5–8 s subset may not exist either.

**Blocking:** It blocks only a "domain at short" or "domain×length" claim. It does not block LoRA.

### Q4. V2 vocabulary — **B**

**Judgment:** Holding V2 fixed makes arms comparable in output space, but V2 is not neutral.

**Evidence:**

- V2 was built from Kspon short refs in a two-pass loop, so its character coverage is tuned to Kspon short.
- Per-arm OOV exclusion differs: 2.38 % / 7.33 % / 4.47 %. Excluding OOV clips removes rare-character sentences at different rates per arm, which shifts the text distribution of what was trained on.
- Eval refs keep OOV characters and score them as errors (test 2,400/2,400 kept). That is the correct choice and should be stated.

**Required action:**

- Wording for absolute CER: "CER with a fixed 1,329-character output vocabulary derived partly from the Kspon-short training selection; training clips containing out-of-vocabulary characters were excluded (2.4–7.3 % per arm); evaluation references were not filtered."
- "V2 vocab-conditioned" alone is not enough. Readers need the exclusion rates.
- Keep V2 fixed for all future arms in this series.
- For a fresh holdout, freeze the vocabulary *before* building the holdout.
- Optional sensitivity check: re-score the existing predictions counting holdout OOV characters separately, or compare against `data/wave2b/vocab_v2_alltrain.json`.

**Blocking:** Not blocking.

### Q5. Test reuse and confirmatory status — **B**

**Judgment:** "In-domain procedural holdout, used once" is accurate but incomplete.

**Required action:**

- Use the fuller label: "Kspon eval_clean procedural holdout (not speaker-independent), used once, for the pre-registered B3-vs-B0′ gate".
- Status of future evaluations on test 2,400:
  - step-matched B3-long, non-Kspon short, seeds: **descriptive/secondary only**. Results are known, there are multiple comparisons, and the test was already touched;
  - LoRA: **no confirmatory claim on test 2,400**.
- **Fresh holdout is required** for any new confirmatory claim.
- **Spare 90 is not sufficient.** It has ~1.4 k reference characters; a paired-delta CI would be several %p wide, unable to resolve 1 %p.
- **Recommended fresh holdout:**
  - ≥2,000 utterances from **Kspon train folders never touched by any selection** (folder-disjoint, which is a better proxy for session/speaker separation than eval_clean);
  - duration-stratified to a pre-declared distribution;
  - exact- and near-duplicate text-deduplicated against all training manifests;
  - vocabulary frozen first;
  - pre-registered.
- Kspon eval_other is acceptable as a secondary set, noting it was already measured once in Wave 2A-lite.

**Blocking:** It blocks LoRA *confirmatory* claims. It does not block the step-matched experiment.

### Q6. B0′ matched-budget controls — **A/B (B for wording)**

**Judgment:** The conclusion is well supported.

**Evidence:**

- B0′-12/20/38 are 0.3701 / 0.3657 / 0.3687. All pairwise CIs include 0, so B0′ is saturated at 12 epochs.
- Repetition caveat: it would weaken the control only if repetition actively hurt. B0′-20 (exposure-matched, 1.67× repetition) did not help either, and B0′-38 is not significantly worse than B0′-20.
- LR schedule: every arm anneals fully to zero over its own budget, so each is a properly finished schedule. The difference in shape is a minor caveat.
- **B0′-rep10 is unnecessary.** It would be the same 6 h repeated, essentially B0′-20.

**Required action:**

- Correct the inference. These controls show the gain needs **new data beyond Wave 1**. They do not show that the B3 data is special.
- Put them together with B3-zeroth-long (new non-Kspon data ≈ no gain) to get the defensible statement: "**additional Kspon-source data**, not more compute or more of any data".

**Blocking:** Not blocking.

### Q7. B3-nat and sampler — **B**

**Judgment:** "No sampler difference detected on dev (B3 − B3-nat +0.49 %p, CI [−0.23, +1.21])" is enough.

**Evidence:**

- Not evaluating B3-nat on test is correct; it is not a defect, and it saves the test.
- The sampler does **not** contaminate the domain or length comparisons. B3-long, B3-zeroth-long and B3-nat all use the natural sampler, and a balanced sampler would be meaningless for a single 8–16 s bin.

**Required action:** Keep B3-nat, not B3 balanced, as the reference for every length comparison, as already done.

**Blocking:** Not blocking.

### Q8. Text overlap — **B (largely closed by my read-only reproduction; formalize it)**

**Evidence (computed now, read-only):**

- **Test.** Using the project normalizer `eval/normalize.normalize_nospace`, exact-match comparison of test refs from `testpred_b3_v2_s42.json` against `data/wave2b/short_4h_v2.jsonl` texts gives **136/2,400** overlapping refs.
  - That exactly reproduces Sonnet's count.
  - Every overlapping ref is a 3–6 character backchannel: 103 are 3 characters, 30 are 4 (e.g. 그런가, 그래서, 아진짜, 뭐먹었어, 맞아맞아).
  - They hold **445/38,224 normalized ref characters (1.16 %)**.
- **Test with overlaps removed:** B0′ 0.3570, B3 0.2622, **Δ = +9.476 %p** (Sonnet's 9.48). The gate (≥1.0 %p) survives easily.
  - On the overlap subset alone, B0′ is 0.584 vs B3 0.265. That reflects a large gain on very short phrases, but its weight is tiny.
- **Dev:** 26/500 overlap (86/7,755 characters). That is enough to move dev numbers by roughly 0.1–0.3 %p, not to change any conclusion.

**Not checked:**

- near-duplicate (fuzzy) matches;
- overlap with the Kspon-long and Zeroth-long manifests (not present in the repository checkout);
- the CI of the deduplicated Δ.

Also note: the request's "53/40,788" test-character count does not match the 38,224 normalized nospace reference characters in `testpred`. The 40,788 presumably counts raw text or spaces; clarify which.

**Required action:**

- Commit an audit script and JSON covering dev, test and every training manifest (short, Kspon long, Zeroth long, Wave 1).
- Report the deduplicated Δ with a bootstrap CI next to the headline result.
- Make exact and near-duplicate text deduplication part of the fresh-holdout recipe.

**Blocking:** Not fatal and not blocking. It is P1 and costs minutes.

### Q9. The B3-zeroth-long "paradox" — **B**

**Judgment:** Most likely explanation: **domain/eval mismatch plus redundancy with the Zeroth already in Wave 1**.

**Evidence:**

- The model already has 1,534 Zeroth clips, and B0′ is saturated on that distribution. More read-news Zeroth speech, written in a different transcription convention, does little for spontaneous Kspon dev.
- **Long-only is ruled out.** B3-long is also long-only and gains 8.6 %p.
- **Step count is ruled out.** B3-zeroth-long ran 5,676 steps, more than B0′'s 3,576, and B0′ gained nothing from more steps.
- **Overfitting is unsupported.** Best epoch 9 was 0.3654 vs final 0.3656, with no divergence.
- In the 16–29 character bin, B3-zeroth-long (0.361) is even slightly worse than B0′ (0.353). This is consistent with a mild pull toward Zeroth style.

**Validity as a control:** Valid as a "**more non-Kspon data, same length**" control. It is not a control for "any new non-Kspon source", because Zeroth was not new.

**Required action:**

- Describe it as "Zeroth (already in base), long".
- Record whether the Zeroth-long selection overlaps Wave 1 Zeroth in speakers or sentence text. I could not check this here; the manifests are not in the checkout.

**Blocking:** Not blocking.

### Q10. Next priority

**Pick one: step-matched B3-long** (Q2 design). It is the only remaining causal ambiguity in the stated claims. It is cheap (~1.5 h CPU), uses existing caches, and has a pre-registrable decision rule.

"The domain effect is strong enough, so stop length work and go to LoRA" is acceptable **for LoRA engineering** (implementation, packaging, GPU smoke) in parallel. It is not acceptable if it means dropping the length question while still saying anything about "short" publicly. If length is dropped, delete every "short" causal wording.

The non-Kspon short question should use the 1.66 h hour-matched design (Q3), not a FLEURS download.

### Q11. Public claim sentence — **B (wording must change)**

**What is wrong with the proposed sentence:**

- It omits that the holdout is in-domain, not speaker-independent, and used once.
- It omits that the controls are single-seed and dev-only.
- It calls the effect "domain", which is too broad.
- The domain evidence comes from the *long* arms, not from the B3 short arm the sentence describes.
- "Adding Kspon short 4h" invites a duration reading.

**Revision:** see section 4.

**Why "short 4h data effect" must not be written (one sentence):** The B3 gain bundles Kspon-source data, which is strongly implicated, with short duration, whose contribution is step-confounded and untested outside Kspon, and it was measured on a non-speaker-independent in-domain holdout. Attributing it to the *short* property of the data is not supported.

---

## 2. Must-fix table

| ID | Issue | Required action | Priority | Blocks LoRA? |
|---|---|---|---|---|
| MF1 | Length effect step-confounded (11,196 vs 5,568 steps) | Run `b3long_sm` (batch 2, grad_accum 2, 12 epochs, patience 99, final-epoch pre-registered); optional replay bracket; per-bin report | **P0** | No (blocks length claims) |
| MF2 | "Domain" label is too broad | Public and internal wording: "Kspon-source (in-distribution) training-data advantage at matched 8–16 s"; list confounded components (style, transcription convention, speakers, selection asymmetry) | **P0** | No (blocks public claims) |
| MF3 | No fresh holdout for new confirmatory claims | Folder-disjoint Kspon train holdout ≥2,000, duration-stratified, text-deduplicated, vocabulary frozen first, pre-registered; plus matched no-LoRA comparator | **P0 for LoRA claims** | **Yes, for LoRA confirmatory claims** (not for implementation or smoke) |
| MF4 | Text-overlap audit not formalized | Commit audit (reproduced here: 136/2,400, 1.16 % of characters, deduplicated Δ +9.476 %p); add CI; extend to dev and to Kspon-long/Zeroth-long manifests; add near-duplicate check | P1 | No |
| MF5 | Domain-at-short untested | 1.66 h hour-matched Zeroth-short vs Kspon-short (duration-matched) arms, no download | P1 | No (blocks "domain at short" claims) |
| MF6 | Selection asymmetries undocumented | Document the folder cap (Kspon only), OOV exclusion per arm, Zeroth-long vs Wave 1 speaker/text redundancy, and the 40,788 vs 38,224 character-count definition | P2 | No |
| MF7 | Single seed | Seed 43 for B3-nat and `b3long_sm` (and B3-zeroth-long if cheap) before any length claim goes public | P2 | No |
| MF8 | Vocabulary conditioning | State the fixed V2 vocabulary plus per-arm OOV exclusion in every absolute-CER statement | P2 | No |

## 3. Next-experiment priorities

1. **Step-matched B3-long** (`--grad-accum 2`), plus the free check of B3-nat's epoch-6 dev CER from existing logs. Also commit the overlap audit, which takes minutes.
2. **Fresh-holdout construction**, pre-registered with the vocabulary frozen. Run LoRA implementation and GPU smoke in parallel.
3. **1.66 h hour-matched domain-at-short control**, then seed 43 for the key arms. The 20-epoch 3-arm run is low value; B0′ is already shown to be saturated.

Weakest points, ranked:

- **Length claim:** step confound ≫ length/content confound ≫ single seed.
- **Domain claim:** construct breadth (transcription convention, style, eval-corpus match) > selection/OOV asymmetry > single seed > text overlap (negligible).
- **Gate:** non-speaker-independent and reused test > vocabulary conditioning > text overlap (now quantified at ≈0.26 %p).

## 4. Public claim (revision)

> On an in-domain Kspon eval_clean holdout (not speaker-independent; used once for a pre-registered gate), an EG2 frozen-audio-tower CTC reader trained with Wave 1 6 h + 4 h of additional KsponSpeech training data achieved CER 0.262 vs 0.360 for the 6 h baseline (+9.7 %p, 95% CI [+9.2, +10.3]; +9.5 %p after removing 136 short test utterances whose text also appears in training). In exploratory single-seed dev-only controls, more epochs on the baseline data did not close the gap. At matched 8–16 s training length, Kspon data outperformed additional Zeroth data by 8.2 %p, indicating the gain comes mainly from in-distribution (Kspon-source) data. Whether short utterance duration contributes is not yet established. CERs are conditional on a fixed 1,329-character vocabulary.

Do **not** use "domain effect is strong" without the "Kspon-source / in-distribution, at 8–16 s" qualifier. Do not use "short 4h data effect" at all.

## 5. Uncertainties

- My per-bin analysis bins by normalized reference character count, not audio duration (dev durations are not in `devpred`). Bin CERs have no CIs. Treat them as descriptive.
- The epoch-6 comparison uses **B3 balanced** per-epoch values (only these are in `reports/W2B_b3_v2.md`), not B3-nat. It is confounded by annealing state and by exposure.
- The prediction that step-matching will not close the gap (because B3-long and B0′ both plateau) is a prior, not a result.
- I could not check Zeroth-long or Kspon-long overlap, or Wave 1 speaker/text redundancy, because those manifests are not in the checkout.
- The overlap reproduction is exact-match only, against `short_4h_v2.jsonl` only, without a bootstrap CI.
- Halving clips per update in `b3long_sm` changes gradient noise. If its result is borderline, the replay bracket is needed.
- I did not run any training, decoding or bootstrap. All model numbers come from committed provenance files.
