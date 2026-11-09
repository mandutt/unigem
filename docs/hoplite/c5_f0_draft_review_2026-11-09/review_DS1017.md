# C5 F0 Draft Prereg — Independent Review (DS1017)

- Review date: 2026-11-09
- **Reviewed HEAD: `68957bdc711acb8462cb9959e2c85b5299e65fd8`** (`docs: add C5 F0 draft review request`)
- Workspace sync: `git fetch origin` + `git pull --ff-only origin main` → `Already up to date.` No error.
- Target document: `docs/plan_c5_f0_2026-11-09.md`, blob `9a0ccf81b28c53491c0c8673a1d7f518ad6b75c3` at reviewed HEAD
- Review request cites authoring HEAD `244b25c`; that commit is **not reachable in this depth-1 checkout** (`git cat-file -t 244b25c` → "Not a valid object name"). All findings below are against the file content at `68957bd`.
- New independent round. Prior Phase 6 / Results-review conclusions were not inherited; every number below was re-read from the cited artifacts.
- No training, no evaluation, no test 163, no P1, no subagents. Repository unmodified except this file.
- Scope boundary: the reviewed claim is **adapter-associated signal loss**, not a structural bottleneck diagnosis.

---

## 0. Summary

| Q | Topic | Verdict |
|---|---|---|
| Q1 | 2×2 validity | **conditional** |
| Q2 | Stage D decision / selection bias | **disagree** (rule as written) |
| Q3 | H3 LN / projection / residual | **conditional** |
| Q4 | M / signal / E00 baseline | **conditional** |
| Q5 | Compute realism | **conditional** |
| Q6 | Interpretation boundaries | **disagree** (§8 contradicts §1 H2) |

**Overall: NARROW.** The question ("does adapter presence change EG2 donor-specific signal with LoRA fixed") is the right next question, and the 2×2 is the right skeleton. But the draft as written cannot answer it, for four structural reasons:

1. §8's STOP rule contradicts §1 H2 and draws a track-level conclusion from one seed.
2. The primary contrast reproduces exactly the capacity/LR confound that §0 itself lists as disqualifying for P vs PA.
3. E01 (raw EG2 into mT5 cross-attention with no adapter and no alignment map) has no control that would make a negative result interpretable.
4. Stage D's numeric rule has no magnitude, no tail-robustness, and omits the E11-loss clause that §1 H1 requires.

---

## Q1. 2×2 validity

**판정: conditional**

### What is valid

- The four cells map onto a complete 2×2 over the manipulable factors (`docs/plan_c5_f0_2026-11-09.md` §2): `(adapter, LoRA) ∈ {none, trained} × {none, 64 modules}`. The fourth cell `(none, none)` is legitimately degenerate — no trainable parameter exists — so E00 = 0 updates is not a missing cell but a degenerate one. §2's statement "E00 has no trainable parameters; it is an evaluation-only baseline, not a 4th trained unit" is correct.
- E01 vs E11 does fix the LoRA side legitimately: both attach the same 64 decoder modules at `r8 alpha16 dropout .05` (`docs/plan_c5_b0a_pm_prereg_v1_0_11.md` §2.2, `runner/c5_pm_phase6.py` `EXPECTED_LORA_MODULES = 64`). The manipulation is clean at the *module presence* level.
- All four cells are EG2 layer19, so they share one donor regime. In Phase 6 the donor lists differed between F/L (EG2 `h_len`) and P/PA (native length, all 20 = 512, tie-break `doc_id` asc) per §2.5.6. In F0 every cell is EG2 `h_len`, so `donors_for(val_ids, cache)` yields identical donor IDs and identical `K_d = min(len(real), len(donor))` for all four cells. F0 should assert this as an artifact invariant; it is a genuine improvement over P/PA.

### What breaks the causal reading

**(a) E01 vs E11 is not a clean isolate of the adapter; it isolates "adapter module + adapter training".**

The adapter is `Linear(512,512) → GELU → Linear(512,512) → LayerNorm(512)` with **all** parameters trainable (`runner/c5_mt5_layer_probe.py:52-63`; `runner/c5_pm_phase6.py` `build_arm` asserts `all(p.requires_grad for p in adapter.parameters())`). Parameter count:

```
512*512 + 512 = 262,656
512*512 + 512 = 262,656
LayerNorm(512) weight+bias = 1,024
total = 526,336
```

That is the same `+526,336` that §0 item 2 lists as a confound for P vs PA, and the adapter runs at `adapter_lr: 1e-3` against `lora_lr: 1e-4` (§2.2) — the same 10× that §0 item 2 lists as a confound for P vs PA. F0 therefore criticizes the P/PA contrast for capacity + LR and then builds its **primary** contrast with the identical capacity + LR asymmetry:

- E01: 100 updates, all gradient to LoRA at 1e-4, memory is untransformed raw `h`.
- E11: 100 updates split between 526,336 adapter parameters at 1e-3 and LoRA at 1e-4; the adapter branch plausibly takes most of the update budget.

So a negative `E01 − E11` is consistent with three distinct causes that F0 cannot separate: the adapter *transformation* destroys donor information; adapter training *crowds out* LoRA adaptation within the fixed 100-step budget; or the trained adapter output moves off the decoder-usable manifold while E01's raw memory does not.

**(b) E01 has no alignment control, so a negative E01 is uninformative.** For F/L the only map from EG2's 512-dim hidden state into mT5's cross-attention keys/values is the adapter itself (`memory_probe`: `memory = built["adapter"](h) if built["adapter"] is not None else h`). E01 feeds a foreign model's hidden space into mT5 cross-attention and asks 100 LoRA updates on 20 training documents to discover an alignment. A negative E01 is therefore equally consistent with "EG2 has no donor signal" and "EG2's basis is not linearly aligned to mT5's cross-attention". §1 H2 and §8 both say this distinction is not resolved — and then §8 stops the track anyway (see Q6).

This is not hypothetical: the cause report's own representation table shows raw EG2 layer19 has **between-doc variance 4.883**, the *highest* of every representation measured (F adapter 0.085, L adapter 0.081, native raw 0.841, PA adapter 1.284), with centered cosine −0.068 and raw mean cosine 0.998. Document-level information is strongly present in raw EG2 in the *variance* sense. If E01 nevertheless returns ~0, the most consistent reading is alignment/decoder usability, not information absence. F0 must contain a probe that separates these before it is allowed to return a verdict.

**(c) The draft registers only two of the four marginal contrasts.** §3.2 lists `E10 vs E00` and `E11 vs E10`; it omits `E01 vs E00`, which is the direct LoRA-only reference needed to interpret the primary. The full set is:

| contrast | isolates |
|---|---|
| E00 → E01 | LoRA training on raw memory, no adapter |
| E00 → E10 | adapter training, no LoRA, decoder frozen |
| E10 → E11 | LoRA training, adapter present |
| E01 → E11 | adapter training, LoRA present (**primary**) |

Only with all four is the 2×2 interpretable as a factorial. Omitting `E01 − E00` leaves the primary without a baseline for "how much does LoRA alone buy on this memory".

**(d) E00 vs E10 is the one *clean* contrast in the draft, and it is under-used.** Both have a frozen base decoder; the only difference is a trained adapter. §3.2 does list it, but §2's "E00 is 0-update baseline" language undersells it. E00 does not confound "any training" because there is nothing else trainable in that cell — it isolates adapter adaptation specifically. That should be stated explicitly so it is not later dismissed as an unfair baseline (see Q4).

### Next steps

1. **Add E11-F (untrained-adapter null): adapter frozen at random init + LoRA, 100 updates.** This single cell separates "the 526,336-parameter transform is present" from "that transform was trained", and thereby removes the capacity/training confound from the primary contrast.
2. **Add E01-L (frozen alignment map): `x → W·x` where `W` is a fixed 512×512 linear map fitted once on train20 (EG2 layer19 → mT5 native encoder output, ridge or least squares), no adapter, no training.** This is the direct test of H2's unresolved split. E01-L positive with E01 negative ⇒ alignment, not features. Both negative ⇒ genuine feature/decoder incompatibility.
3. **Add a donor-discrimination probe (no training, no new cell): linear probe on the 15-doc memory tensors predicting donor-doc identity, computed on raw `h`, on `Adapter(h)` at init, and on `Adapter(h)` after 100 updates.** This is the cheapest decisive measurement of "is donor information present in the representation the decoder is given" and should be reported alongside M, not as a gate.
4. Register `E01 − E00` as a named secondary alongside the existing two.

---

## Q2. Stage D decision and selection bias

**판정: disagree (rule as written)**

§8:

```
E01 copy mean delta > 0
AND E01 − E11 paired copy mean > 0
AND both E01/E11 endpoints finite on 15 common docs
```

### (a) The rule omits the clause §1 H1 requires

§1 H1 is a two-part claim: "`E01` …는 donor-specific signal을 보인다. `E11` …는 signal을 잃는다. `E01 − E11 > 0`". §8 operationalizes only the third clause plus a bare `E01 > 0`. If `E01 = +0.060` and `E11 = +0.050`, the rule **passes** even though E11 did not lose signal and the adapter is not implicated. The rule must require the loss, e.g. `E11 copy mean delta ≤ 0`, or better: `E01` satisfies the registered positive predicate **and** `E11` does not. As written, §8 is inconsistent with §1 on the normative definition of the hypothesis.

### (b) No magnitude, on a 15-document cohort whose signal is known to be concentrated

`E01 copy mean delta > 0` with no margin means `+0.001` passes. For scale: the entire Phase 6 LoRA contrast was `−0.0026` (8/15 positive; 60 seed-doc pairs `−0.0224`, 30/60). A Stage D threshold that admits a +0.001 screen is below the noise floor the same project already measured.

Worse, the cohort is fixed at 15 documents and Phase 6 showed the signal lives in a few of them: `top3_abs_share = 0.4775`, `top3_signed_share = 0.8035`, `leave_top3_mean = −0.0279` (labels report §3). With three documents carrying ~48% of absolute mass, a one-seed positive screen is dominated by document identity, not by the manipulation. The draft already has the exact machinery for this (`leave_top3_mean`, v1.0.11 §10.4) and does not use it in §8.

### (c) Selection bias: smaller than it first appears, but not zero

Credit where due: Stage D uses seed `20261111`, Stage R uses `20261108/09/10` (§3), so **the Stage D seed is disjoint from the registered seeds**. That removes direct seed reuse and is a real mitigation — the naive "screen on seed 1, estimate on seed 1" bias does not apply.

What remains is **document-level selection**. The 15 common documents are identical in Stage D and Stage R. Conditioning Stage R on a favorable Stage D draw therefore selects on the *documents* (via the seed-specific draw on those same 15 docs), not just on the seed. With a 3-document concentration of ~0.48, one favorable seed can be nothing but a favorable draw on the same three documents that will recur in Stage R. Seed disjointness does not repair that.

Second-order bias: Stage R is run only on draws where both directional clauses were satisfied, so any eventual Stage R estimate is conditional on an independent favorable realization. If Stage R's registered predicate (mean ≥ .05, CI lower > 0, 2/3 seeds > 0, §3.1) is used as the confirmatory rule, this conditioning inflates the effective false-positive rate. The draft does not state that the Stage R result is conditional, and §3.1 presents the predicate as unconditional.

### (d) The STOP side is the more damaging error

§8 lets one debug seed terminate F0 and (per the branch text) the EG2 resident track. A false STOP destroys information that 82 minutes of compute (measured; see Q5) would have produced. The asymmetry is entirely in the wrong direction: the cheap error (running 3 seeds on a dead hypothesis, ~87 min) is guarded against, while the expensive error (killing a track on one seed of 15 documents) is not.

### (e) Is Stage D too lenient or too strict?

Both, in different dimensions. Too lenient in effect-size margin and tail robustness; too strict in that it is conjunctive over two noisy single-seed means with no interval, so its *pass* rate under a true small effect is low, while its pass rate under a lucky document draw is unacceptably high. A screen with no margin and no robustness check is not a conservative screen; it is an arbitrary one.

### Next steps

1. **Split the gate.** Make Stage D a *mechanics and validity* gate only: 4 cells run, 0 non-finite losses, `endpoint_ok` on all 15 common docs, donor IDs and `K_d` identical across all four cells, `n_signal = 15`. Delete the two directional clauses from the gate.
2. **Move the scientific decision to Stage R's registered predicate**, and state explicitly that Stage R is run whenever Stage D mechanics pass. At ~87 min measured (Q5), the compute saving from a 29-min screen does not justify the selection.
3. If a directional screen is retained, it must carry: `E01 mean ≥ .05`; `E11` fails the registered predicate; `leave_top3_mean > 0` on the primary contrast; and a written statement that Stage R is conditional and its labels are exploratory, not confirmatory.

---

## Q3. H3 — LN / projection / residual

**판정: conditional**

### (a) `E01-LN` does not isolate the adapter's LayerNorm

The adapter's LayerNorm is the **final** op, `LayerNorm(512)`, applied to the output of `Linear → GELU → Linear`, and it is **trained** (`all(p.requires_grad for p in adapter.parameters())`). §1 H3 defines `E01-LN` as "raw EG2 + fixed LayerNorm (no learned adapter)". That is a different operator in a different position:

- it normalizes the *input* representation, not the output of two learned linear layers;
- it is fixed, so it cannot express the trained affine rescale the adapter learns;
- it adds a normalization the baseline E01 never had, so `E01` vs `E01-LN` is "raw vs raw+LN", not "adapter with LN vs adapter without".

A positive `E01-LN` would therefore not implicate the adapter's LayerNorm; a negative would not exonerate it. The direct test is the **inverse** ablation on the observation arm: E11 with the adapter's final `LayerNorm` replaced by `Identity`, everything else (both Linears, GELU, LoRA, 100 updates, 1e-3) unchanged. That arm answers "does removing the adapter's output normalization restore donor signal" — the actual H3-LN question.

### (b) `E01-P` is a useful null, but only if "orthogonal" is preregistered

An orthogonal 512×512 map is norm-preserving and invertible, so it does not destroy information; it changes basis and scale. If signal survives `E01-P` and dies in `E11`, the adapter's effect is not information destruction — consistent with the cause report's own caution that the 98% variance contraction (4.883 → 0.085) "may not be causal evidence" when centered cosine is essentially unchanged (−0.068 raw vs −0.068 F, −0.067 L, and raw mean cosine already 0.998). That is a good null. Two requirements: the matrix generation must be seeded and frozen in the prereg (construction, seed, dtype), and `E01-P` must be compared against `E01`, not against E11, or the two changes (projection + adapter training) will be confounded again.

### (c) `E01-R` is not identity-preserving as specified

§1 H3 labels `x + Adapter(x)` "(identity-preserving)". It is not:

- `Adapter(x)` at initialization is **not zero** — the first Linear uses default kaiming-uniform init, so `x + Adapter(x) ≠ x` even at step 0;
- the adapter's terminal `LayerNorm` normalizes the *branch output* (unit variance), so the residual sum is `x + LN(z)`, whose scale and direction are dominated by the branch, not by `x`;
- there is no `α` gate, so nothing is initialized to a small value.

If the intent is genuine identity preservation at init, the arm must be `x + α·Adapter_without_final_LN(x)` with `α = 0` (or a zero-initialized second Linear, LoRA-style `B = 0`), and the LayerNorm must be removed from the branch or applied before the residual. As written the arm is "residual with a randomly initialized non-zero branch", a different and weaker intervention, and the draft's stated rationale for it does not hold.

### (d) Placement: primary vs separate prereg

- **Belongs in neither as currently written**: `E01-LN` (wrong operator) and `E01-R` (wrong init semantics). Both need respeccing before they can be registered anywhere.
- **Belongs in the F0 primary**: the untrained-adapter null (Q1 step 1) and the frozen alignment map (Q1 step 2). These are not H3 mechanism arms; they are necessary conditions for interpreting E01 vs E11 at all. Keeping them out of F0 means F0 cannot answer its own question.
- **Belongs in a separate prereg**: adapter training-dynamics variants (`α` sweep, adapter capacity, auxiliary loss, LR matching), i.e. the cause report §6 H3 list. §9's non-goal "adapter capacity/LR tuning in this prereg (H3 separate)" is correct.

### Next steps

1. Respec `E01-LN` as **E11-LNab** (adapter minus final LayerNorm) or delete it; do not register it as an `E01`-based arm.
2. Respec `E01-R` to `x + α·branch` with `α = 0` init and no branch LayerNorm, or delete it and leave residual adapters to the separate prereg.
3. Freeze `E01-P`'s orthogonal matrix (construction, seed, dtype) and pair it against `E01`.
4. Move the untrained-adapter null and the alignment arm into the F0 primary (§2), not H3.

---

## Q4. M / signal / E00 baseline

**판정: conditional**

### (a) Arithmetic is correct where §3 and §5 state it

- M per cell per seed: `15 common × 2 variants × 2 endpoints × 2 memory kinds = 120` — correct.
- §5: `E10/E01/E11 = 3 × 100 = 300` updates for Stage D — correct.
- §5: Stage R `9 trained units × 100 = 900`; the other 3 of 12 artifacts are E00 at 0 updates — correct, and the draft states the trained-unit count correctly.

### (b) But §6 contains an unresolved wrong number

§6: "`F0-R: registered 3 seeds, 1,680? EG2 only 4 cells ×3 seeds ×120 = 1,440 M records`". The sentence contains both `1,680?` and `1,440`, with a literal question mark, and `1,680` is Phase 6's number (v1.0.11 §9.5, driven by P/PA native-20 records). F0 has no P/PA, so **1,440 is the only correct value**. A prereg may not freeze with an unresolved alternative in a normative record count.

The same defect appears twice more: §2.1 ends with "source max 512? For EG2 memory, source h token length" and §6 begins "M 480? Wait E00/E10/E01/E11 M 120 each = 480". Authoring artifacts ("Wait", "?") left inside a specification that will be frozen and hashed.

### (c) The endpoint identity is not redefined for F0

v1.0.11 §9.5 pins `endpoint_ok` to **1,680** records with the exact domain "F/L: 15 common IDs; P/PA: 20 native IDs". F0 runs no P/PA and must have its own identity:

```
4 cells × 3 seeds × 15 common × 2 variants × 2 endpoints × 2 memory kinds = 1,440
common target appears 48 times
```

Without a stated key set, "no missing key" cannot be checked, and §7's `f0_replay.json` has no domain definition at all (v1.0.11 §11.4 defines primary vs phase-7 replay separately; F0 does not).

### (d) `m_valid` / `control_status` cannot be reused unchanged

§4 says "Reuse frozen v1.0.11 definitions exactly". But v1.0.11 §5.2 defines `m_valid = ANDn(m_pass_pos_p, m_pass_norm_p, m_pass_pos_pa, m_pass_norm_pa)` and §5.4 routes `p_valid`/`pa_valid` absence into `M_NOT_EVALUABLE`. F0 has no P and no PA. Reusing the frozen module (`runner/c5_pm_labels.py`) verbatim will therefore emit `M_NOT_EVALUABLE` / `NOT_ASSESSABLE` for every F0 cell. F0 needs an explicit F0-scoped control table, e.g. `m_valid_cell = ANDn(m_pass_pos_cell, m_pass_norm_cell)` per cell, with the F0 dispatch stated. This is not a wording issue; it is a code path that will fire.

### (e) M_PASS is correctly not a gate, but its failure has no stated consequence

§3.2 lists M_PASS as secondary and §4 forbids threshold changes — both correct, and consistent with the Phase 6 lesson that `M_PASS ≠ content-use signal` (M only asks "real beats the global mean"; L still had `mean Δ copy = −0.1135`, CI `[−0.2341, −0.0012]`, 6/15 positive docs, 0/3 seeds positive, with `m_pass_l` true). But if `M_CONTROL_FAIL` occurs on E01 or E11, the signal delta is uninterpretable and the primary claim must be suppressed. v1.0.11 §6.3 already does this (`L_SIGNAL_M_CONTROL_FAIL` → no affirmative label). F0 should state that a control failure on either primary cell makes the primary contrast reportable only as `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE`, not as a positive or negative adapter result.

### (f) E00 vs the 100-update cells: defensible, needs precise framing

E00 is a legitimate eval-only baseline. Because the base decoder is frozen in every cell and E00 has no trainable parameter, `E00 → E10` differs only by adapter adaptation (nothing else can train). That is fair. `E00 → E01` differs only by LoRA adaptation. Also fair, and currently unregistered (Q1). What E00 cannot do is serve as a *training control* for the 100-update cells in general — §2 already says so, and that should be repeated at each place E00 is used, so a later reader does not read `E00 vs E01` as "training effect".

### (g) Cohort margin is zero

`n_signal = 15` and `n_min = 15` (v1.0.11 §6.1). A single document failing copy eligibility routes the whole dispatch to `INCONCLUSIVE_SMALL_N` (§6.3). Phase 6 landed exactly at 15/15 with coverage ~0.8. F0 changes the memory path for two cells (raw EG2), so copy coverage is not guaranteed identical. The prereg should state the expected 15/15 assertion and the fallback label in advance instead of discovering it post hoc.

### Next steps

1. Replace every `?` / `Wait` with a single number; fix `1,680` → **1,440**; delete the alternative readings.
2. Write an F0 §9.5-equivalent endpoint identity (1,440) and an F0 §11.4-equivalent replay domain (primary 1,440 phase-5 records; phase-7 7,200), with `atol=1e-5, rtol=1e-4`.
3. Write an F0-scoped validity/control table and state which v1.0.11 §5/§6 functions are reused vs replaced.
4. State that `M_CONTROL_FAIL` on E01/E11 suppresses the primary claim.

---

## Q5. Compute realism

**판정: conditional — the arithmetic is right, the caps are realistic only under an unstated parallel schedule**

### (a) Measured Phase 6 baseline

From `reports/provenance/C5_b0a/registered/units/*.json` (`elapsed_s`), per unit, covering 100 updates + step0/final eval + M + phase 7 + generation + checkpoint:

| arm | elapsed_s range | minutes |
|---|---:|---:|
| F | 1,502.1 – 1,715.7 | 25.0 – 28.6 |
| L | 1,527.4 – 1,751.4 | 25.5 – 29.2 |
| P | 1,460.2 – 1,701.8 | 24.3 – 28.4 |
| PA | 1,518.2 – 1,732.5 | 25.3 – 28.9 |

Serial sum: **19,452 s = 324.2 min** for 12 units.

`registered_report.json` reconciles this: `parallel_units_per_wave: 4`, `wall_estimate_s: 4,939.88 s` (**82.3 min**), `cap_seconds: 7,200` (120 min), `cap_ok: true`. So Phase 6 ran **4 units concurrently in 3 waves**, and the 120-min cap is only meaningful in that schedule. A serial reading of the same run would have been 324 min against a 120-min cap.

### (b) F0 Stage D

- 4 cells, 1 wave at `parallel_units_per_wave = 4`: wall ≈ max unit ≈ **29.2 min**, inside the 45-min cap (1.5× margin).
- Serial at 6 threads: 3 trained × ~27 min + E00 ≈ **~93 min**, roughly **2× over** the 45-min cap.

§5 specifies "cap: ≤45 min, **4–8 threads**". That reads as a single-process serial budget, which is the schedule in which the cap fails. It also understates the real resource shape: 4 concurrent processes at 6 threads each is 24 threads, not 4–8. Phase 6's observed wave time implies the host sustained that; F0 must say so and record the host core count.

### (c) F0 Stage R

- 12 units, 4 per wave, 3 waves: waves 1–2 = 4 trained each (~29 min), wave 3 = 1 trained + 3 E00 (E00 is faster, dominated by generation/M/phase 7). Estimate **≈ 87 min**, inside 150 min (1.7× margin).
- F0 is slightly cheaper than Phase 6 per unit at the M layer (120 records vs 160 for the native arms) but identical at phase 7 (600) and generation (20×256), so the per-unit figure is a fair proxy.
- Serial: 9 × 27 + 3 × ~12 ≈ **279 min**, ~1.9× over 150.

### (d) Do the caps include generation and phase 7?

Measured `elapsed_s` covers step0/final eval (20 docs × 5 donors), M builder, M records, phase 7 (600), generation (20 × 256 greedy), and checkpoint — i.e. **everything**. §5's bullet lists those as "outputs" but never says the cap includes them. It must, because §11.5 `T_proj` includes `t_generate_20x256_arm` and `t_replay_15x5x2x2x2_arm`.

### (e) "9 trained units + E00 eval-only" — correct

12 artifacts, 9 trained, 900 updates at Stage R; 3 trained + E00, 300 updates at Stage D. §5 states this correctly and I concur. Note E00 is not free: it still requires the donor-crop eval, M builder (with `A = identity`), phase 7 (600) and 20×256 generation; budget ~10–13 min, not zero.

### (f) Implementation gap

`runner/c5_pm_phase6.py` cannot express F0 cells:

```python
"memory_source": "eg2_layer19" if arm in {"F", "L"} else "native_mt5",
"adapter": arm != "P",
"lora": arm in {"L", "P", "PA"},
```

There is no arm with `eg2_layer19` **and** `adapter=False` (E01/E00), and no arm with `lora=False` **and** `memory_source=eg2` other than F (E10 needs `eg2 + adapter + no lora`). Also `train_registered` raises `ValueError` unless exactly 100 updates, so E00 cannot call it. F0 needs new `arm_spec` entries (or a cell-based spec) plus a 0-update path that still runs eval/M/phase 7/generation. This is a small change, but it is a change, and §9 ("no changes to v1.0.11 thresholds") does not cover it.

### Next steps

1. State the schedule explicitly: `parallel_units_per_wave = 4`, 6 threads per process, host core count, and that Stage D/R caps assume that schedule. Otherwise rewrite the caps to the serial values (~95 min / ~280 min).
2. Add one sentence that both caps include generation (20×256) and phase 7 (600/unit).
3. Register the `arm_spec` extension and the 0-update cell path as an implementation prerequisite, with an F0-D0 shape assertion for E00/E01 (`(753, 512)`, `adapter=None`).

---

## Q6. Interpretation boundaries

**판정: disagree — the boundary is stated in prose and violated in the operative rule**

### (a) The two clauses are in direct contradiction

§1 H2: "F0 negative는 트랙 STOP의 충분조건이 아니다."

§8: "If E01 negative and E11 negative → EG2 raw feature/alignment insufficient; **stop EG2 resident track**."

Both cannot be normative. The draft cannot claim the boundary in §1 and then terminate the track on one debug seed in §8. This is the most serious text defect in the document, because §8 is the operative rule and §1 is the disclaimer.

### (b) Is "F0 negative ≠ EG2 feature insufficiency" sufficiently specified? No.

Three things are missing:

1. **No alignment control**, so negative E01 cannot separate feature insufficiency from basis mismatch (Q1b). The cause report's own 4.883 between-doc variance on raw EG2 makes "information absent" the *less* plausible of the two readings.
2. **No statement that one seed of 15 documents cannot support a track-level conclusion.** §8 says "Stage D is 1 seed only; no statistical claim" and then draws the largest possible claim from it.
3. **No distinction between "this 512-dim layer19 memory under this decoder protocol is unusable" and "EG2 is unusable".** Only layer19 is tested; the plan is titled "EG2 resident track".

### (c) Does F0 positive establish adapter causality? No.

`E01 − E11 > 0` with the registered predicate would establish: *under fixed LoRA configuration, 100 updates, 20 training documents, adapter LR 1e-3, and EG2 layer19 memory, adding a trained 526,336-parameter adapter reduces the donor-specific copy contrast.* It would not establish:

- **that the adapter transformation is the cause** rather than adapter training consuming the update budget (E11 splits 100 steps between adapter@1e-3 and LoRA@1e-4; E01 gives all 100 to LoRA; no untrained-adapter null);
- **which mechanism** — the cause report explicitly lists "LayerNorm/input-insensitive mapping, optimization interference, decoder off-manifold 중 어느 것인지 미분리", and §1 H3's arms as currently specced do not resolve it (Q3);
- **generalization to the native path** (P vs PA remains observational, and differs by +526,336 params and 10× LR);
- **generalization beyond layer19, 20 train docs, 100 steps, or 512-dim memory**;
- **that EG2 as a memory source is implicated at all**, as opposed to this particular decoder alignment.

Nothing in §3.1 or §8 defines when a positive result may be called causal beyond the hedge "증거가 강해진다" in §1 H1. That phrase is appropriately hedged, but the required summary block invites a causal one-liner, so the ceiling must be written into the label, not the prose.

### (d) The Phase 6 numbers that must bound F0's claims

Any F0 write-up should carry these forward as the evidentiary floor, because they define how small the effects can be:

- L copy: mean **−0.1135**, CI **[-0.2341, -0.0012]**, 6/15 positive docs, 0/3 seeds positive.
- L full: **−0.1085**, CI [-0.2234, -0.0057].
- tail: `top3_abs_share` **0.4775**, `top3_signed_share` **0.8035**, `leave_top3_mean` **−0.0279**, `tail_driven` **true**.
- L−F: **−0.0026** (8/15); 60 seed-doc pairs **−0.0224** (30/60).
- P **3.076** vs PA **0.011**, paired **+3.065**, 14/15.
- representation variance: raw EG2 **4.883** → F **0.085**, L **0.081**; native raw **0.841**, PA **1.284**; centered cosine −0.068 / −0.067; raw mean cosine **0.998**.
- `signal_status` **MEAN_CONTRAST_ONLY**, `b0_b_candidate_gate` **false**, `m_pass_l` **true**.

### Next steps

1. Delete the `stop EG2 resident track` clause from §8 or make it conditional on a Stage R negative **plus** an alignment-control negative. Align §1 H2 and §8 to a single rule.
2. Write the interpretation ceiling into the F0 label vocabulary: `ADAPTER_ASSOCIATED_LOSS_UNDER_FIXED_PROTOCOL` (positive) vs `NO_DONOR_SIGNAL_UNDER_THIS_MEMORY_PROTOCOL` (negative), never "EG2 feature insufficient" and never "structural bottleneck".
3. Pre-register that a positive is reportable as causal only if the untrained-adapter null (Q1) is also non-null in the expected direction.

---

## Final

```text
최종 판정: NARROW

F0 2×2:
  Keep the four-cell skeleton; it is a valid 2×2 with one degenerate cell (E00).
  Not valid as a causal isolate of adapter *training* until the untrained-adapter
  null (E11-F) exists. E01 is not interpretable without a frozen alignment arm
  (E01-L) and a donor-discrimination probe. Register E01−E00 as a secondary.

Stage D:
  Demote to a mechanics/validity gate only. Drop "E01>0 AND E01−E11>0" from the
  gate. If retained, it must add the E11-loss clause, mean ≥ .05, and
  leave_top3_mean > 0. Never allow Stage D to stop the EG2 track on 1 seed of
  15 documents.

H3:
  Keep mechanism arms out of the primary and out of F0 as currently specced.
  E01-LN does not isolate the adapter's LayerNorm (wrong operator, wrong
  position, and the adapter's LN is trained). E01-R is not identity-preserving
  (Adapter(x) ≠ 0 at init, terminal LayerNorm, no α gate). Respec as E11-LNab
  and x + α·branch with α=0, or defer to a separate prereg. Freeze E01-P's
  orthogonal matrix and compare it to E01.

M/signal:
  Arithmetic is correct (120/cell/seed; 300 / 900 updates; 9 trained units).
  Fix §6's "1,680?" to 1,440 and delete every "?"/"Wait". Write F0's own
  endpoint identity (1,440) and replay domain (phase-5 1,440, phase-7 7,200).
  Do not reuse v1.0.11 §5.2/§5.4 verbatim: with no P/PA it will emit
  M_NOT_EVALUABLE for every cell. M_PASS stays non-gating, but a control
  failure on E01/E11 must suppress the primary claim.

Compute:
  900 updates / 150 min and 300 updates / 45 min are realistic ONLY under the
  Phase 6 schedule of 4 concurrent units per wave (measured 1,460–1,751 s per
  unit; wave estimate 4,939.88 s = 82.3 min for 12 units). Serial at 6 threads
  is ~93 min for Stage D and ~279 min for Stage R, i.e. both caps fail.
  State parallel_units_per_wave = 4, threads per process, host cores, and that
  the caps include generation (20×256) and phase 7 (600/unit). The caps do not
  cover the unstated implementation work either: arm_spec cannot express
  E00/E01/E10, and train_registered rejects 0 updates.

금지 범위:
  No F0 execution before approval. No test 163, no P1, no native P/PA rerun.
  No threshold/seed/donor/step/LR changes. No B0-B/B1/B2/Stage C progression.
  No re-interpretation of Phase 6 to rescue B0-B. No track STOP on Stage D.
  No "bottleneck" or "EG2 feature insufficient" wording in any F0 output.

Must-fix (ranked):
  MF-1. §8 contradicts §1 H2: remove "stop EG2 resident track" or condition it
        on a Stage R negative plus an alignment-control negative.
  MF-2. Add E11-F (untrained adapter frozen at init + LoRA): without it the
        primary contrast confounds adapter transformation with adapter
        training, and F0 repeats the +526,336 / 10× LR confound it criticizes.
  MF-3. Add E01-L (frozen ridge/PCA alignment map EG2→mT5 native, no adapter)
        and a donor-discrimination probe, or E01 negative is uninterpretable.
  MF-4. Stage D rule: add the E11-loss clause, mean ≥ .05, leave_top3_mean > 0,
        or demote Stage D to a mechanics gate and always run 3 seeds.
  MF-5. Fix §6 1,680 → 1,440; delete the three "?"/"Wait" authoring artifacts;
        write the F0 endpoint identity and replay domain.
  MF-6. Write an F0-scoped validity/control table (m_valid_cell, control_status,
        dispatch); v1.0.11 §5.2/§5.4 cannot be reused unchanged without P/PA.
  MF-7. State the compute schedule (4 parallel units/wave, 6 threads, host
        cores) and that the caps include generation and phase 7.
  MF-8. Respec E01-LN → E11-LNab and E01-R → x + α·branch (α=0, no branch LN),
        or move both to a separate prereg.
  MF-9. Add the arm_spec / 0-update extension as an implementation prerequisite
        with an F0-D0 shape assertion for E00/E01.

잘못된 전제:
  1. "E01 vs E11 separates the adapter effect under fixed LoRA" — it separates
     module presence + training + 526,336 params + 10× LR; the draft's own §0
     disqualifies that bundle for P vs PA.
  2. "E01-LN tests the adapter's LayerNorm" — false: the adapter's LN is trained
     and sits after two Linear+GELU layers; E01-LN normalizes raw input.
  3. "x + Adapter(x) is identity-preserving" — false: the branch is non-zero at
     init, is LayerNorm'd, and has no α gate.
  4. "F0 negative ⇒ EG2 feature/alignment insufficient ⇒ stop the track" — one
     seed, 15 documents, no alignment control, and it contradicts §1 H2.
  5. "F0 positive ⇒ adapter causality" — no: budget split, mechanism, native
     path, layer generality and decoder alignment all remain unseparated.
  6. "4–8 threads / 45 min" is not a coherent compute unit — Phase 6 actually
     ran 4 concurrent units at 6 threads (24 threads) in 82.3 min for 12 units.
  7. "12 units" as trained units — 12 artifacts, 9 trained, 3 E00 at 0 updates
     (§5 states this correctly; §6's 1,680 does not).
```

---

## Appendix — files read

| file | use |
|---|---|
| `reports/EXTERNAL_REVIEW_C5_F0_DRAFT_2026-11-09.md` | review scope, Q1–Q6, prohibited actions |
| `docs/plan_c5_f0_2026-11-09.md` | target §0–§13 |
| `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md` | L/P/PA contrasts, variance table, MF-3 boundary |
| `reports/C5_B0A_PM_PHASE6_LABELS_2026-11-09.md` | tail metrics, M/validity flags, B0-B gate |
| `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | MF-1…MF-6 context (reference only, not inherited conclusion) |
| `docs/plan_c5_b0a_pm_prereg_v1_0_11.md` | §2.1, §2.2, §2.5.4, §5.2, §5.4, §6.1, §6.3, §9.5, §10.4, §11.3–§11.6 |
| `runner/c5_pm_phase6.py` | `arm_spec`, `build_arm`, `memory_probe`, `train_registered`, `main` |
| `runner/c5_mt5_layer_probe.py` | `Adapter` definition (geometry, terminal LayerNorm) |
| `reports/provenance/C5_b0a/registered/units/*.json`, `registered_report.json` | measured per-unit `elapsed_s`, `parallel_units_per_wave`, `wall_estimate_s` |

Note: at reviewed HEAD the MF-1 provenance gap from the prior synthesis is materially narrower — `runner/c5_pm_registered.py`, `runner/c5_pm_replay.py`, `runner/c5_pm_gate.py`, `runner/c5_pm_labels.py`, and `runner/c5_pm_stats.py` are present, and `main()` accepts `--mode registered`. That does not help F0 directly, because `arm_spec` still hardcodes F/L/P/PA (Q5f), but it removes a blocker the F0 plan inherits from the earlier review.