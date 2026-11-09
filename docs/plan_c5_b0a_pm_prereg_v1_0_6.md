# C5 Phase 6 P/M Prereg — v1.0.6 Consolidated Normative Spec

- 작성일: 2026-11-09
- 상태: **v1.0.6 review candidate. 실행 미승인.**
- 문서 성격: **구현 권위 문서(단일 normative spec)**
- 대체 대상: `v0.2.1-r3.4` 및 그 이전 P/M prereg chain
- 역사 문서: `v0.2`, `v0.2.1`, `r1`, `r2`, `r3`, `r3.1`, `r3.2`, `r3.3`, `r3.4`는 **traceability only**
- 충돌 시: **v1.0.6 > 모든 이전 P/M 문서**
- freeze 후: **v1.0.6 + 번호가 붙은 ERRATA만** 유효
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

---

## 0. Authority and scope

### 0.1 Normative status

이 문서는 C5 Phase 6 P/M 실험의 **유일한 구현 계약**이다.

- 구현자는 이 문서만 읽고 코드를 작성할 수 있어야 한다.
- 이전 r3.x 문서를 참조하지 않는다.
- 이전 문서와 충돌하는 문장은 모두 이 문서가 대체한다.
- 리뷰 보고서는 역사 기록이며 구현 권위가 아니다.

### 0.2 Scope

- Phase 6: F/L/P/PA 4-arm, 3 seeds, 100 updates.
- M: eval-only memory control.
- D0: zero-update mechanics.
- D1: separate timing/debug run.
- 3-seed: separate registered run.
- B0-B: separate downstream gate.

### 0.3 Non-goals

- STT/F2 재개 없음.
- T5Gemma2 bridge 재개 없음.
- B0-B/B1/B2/Stage C 자동 승인 없음.
- test 163/P1 사용 없음.
- 결과 후 threshold/seed/donor/step/LR 변경 없음.

### 0.4 Preflight artifact

- `reports/provenance/C5_b0a/m_cohort_preflight.json`
- content SHA-256: **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`**
- git blob OID가 아닌 file content hash.
- frozen preflight hash.

---

## 1. Data, cohorts, identities

### 1.1 Splits

- clean F5: 1,617
- train/val/test: **1,293 / 161 / 163**, seed 42
- Phase 6 uses:
  - train20 = `train[:20]`
  - val20 = `val[5:25]`
  - test 163 = **sealed**

### 1.2 Length cohorts

| cohort | 정의 | n |
|---|---|---:|
| train20 | train[:20] | 20 |
| val20 | val[5:25] | 20 |
| L signal eligible | val20 with `h_len >= 753` | **15** |
| L M targets | common_ids at K=753 | **15** |
| P/PA M targets | native val20 at 512 (15 common + 5 native-only) | **20** |
| native P/PA | all val20 at 512 | **20** |

- preflight `common_ids` = 15.
- zero-margin: K=753, K=754 → 14 eligible.
- 15→14 substitution 금지.

### 1.3 IDs

- `train20_ids` and `val20_ids` are frozen in preflight.
- `common_ids` = 15 L-eligible val IDs.
- no target replacement.
- no duplicate target.
- no test ID.

### 1.4 Leakage

- test 163 not read.
- P1 not used.
- no external API on P1.
- P0 only external (public/synthetic).
- preflight no model forward.

### 1.5 P1 usage manifest and allowlist

- `reports/provenance/C5_b0a/p1_usage.json`:
  ```json
  {
    "manifest_version": 1,
    "p1_used": false,
    "test_split_read": false,
    "checked_artifacts": []
  }
  ```
- allowlist = frozen train20_ids ∪ val20_ids from preflight.
- `test_split_used` is evaluated by allowlist membership, **not** by scanning sealed test 163.
- any artifact ID outside allowlist → `test_split_used=true`.
- `checked_artifacts` must list every Phase 6 artifact inspected; before artifacts exist, empty list is valid.
- `p1_usage.json` is **frozen at freeze time** with empty inventory; SHA256 in freeze manifest as `p1_manifest_sha256`.
- postrun inventory is a separate file `p1_usage.postrun.json`; it does not modify the frozen file.
- postrun `checked_artifacts` expands every glob in `phase6_artifact_registry.json` and lists actual files; self-lists `p1_usage.postrun.json`.
- expected artifact registry: `reports/provenance/C5_b0a/phase6_artifact_registry.json`; it covers checkpoints, control tensors, and phase-7 records.
- `assay_path_ok` uses the frozen hash; postrun inventory is audit-only.
- contradiction rule: any `p1_used=true`, any `test_split_read=true`, or any ID outside allowlist → `false`.
- missing/malformed manifest → `assay_path_ok=NA`.
- unknown keys (e.g. `note`) are allowed.
- a false declaration is an attestation, not proof of non-access; test 163 remains sealed.

---

## 2. Arms and training

### 2.1 Arm table

| arm | memory | M K | adapter | trainable | role |
|---|---|---:|---|---|---|
| F | EG2 layer19 | 753 | trained | adapter | reference |
| L | EG2 layer19 | 753 | trained | adapter + decoder LoRA | B0-A 재검증 |
| P | native mT5 encoder | 512 | none (`A=identity`) | decoder LoRA only | positive control |
| PA | native mT5 encoder | 512 | random-init trained | adapter + decoder LoRA | P/F regime 정합 |

- 12 units = 4 arms × 3 seeds.
- M K applies only to M; see §2.3.
- F/L adapter geometry 512; memory prefix 753.

### 2.2 Hyperparameters

```text
optimizer: AdamW
weight_decay: .01
adapter_lr: 1e-3 for F, L, PA
lora_lr: 1e-4 for L, P, PA
updates: 100
batch: 1
order: train20_ids[step % 20]
clip: 1.0
base decoder: eval
LoRA: 64 modules, r8 alpha16 dropout .05
```

- P has no adapter; adapter_lr not applied.
- `adapter_lr` applies to F/L/PA.
- `lora_lr` applies to L/P/PA.

### 2.3 Workload-specific length/crop

**M memory**:

- F/L: `M_POS_MEAN` from `A(h_i)[:753]`
- P/PA: `A(h_i)[:512]`
- donor-crop 금지
- target prefix `A(h_t)[:K_M]`

**Training/eval signal**:

- training forward: real memory only; no donor.
- eval signal: donor-crop `K = min(len(real), len(donor))` per document.
- all 20 train/val docs.
- 753 not required.
- no padding/drop/order change.

**Generation**:

- 20 val docs.
- `max_new_tokens=256`.
- 753 not required.

**Rule**:

- `K_M=753` is **M-only**.
- training/eval/generation must not require 753.
- 이 규칙은 4 train/5 val short docs를 처리한다.

### 2.4 P/PA initialization

- P: native mT5 encoder, no adapter.
- PA: native mT5 encoder + random-init adapter + decoder LoRA.
- PA adapter seed: same registered seed.
- PA is acquisition control; not retention gate.

### 2.5 Measurement semantics (normative)

This section defines the measurement path. No implementation may substitute
a different tokenizer, loss, mask, donor rule, or decoding policy.

#### 2.5.1 Model and tokenizer

```text
model = data/models/mt5-small
tokenizer = T5Tokenizer, use_fast=False, local_files_only=True
source_prefix = "summarize: "
source_max_length = 512
target_max_length = 256
```

- source text = `source_prefix + passage`.
- `add_special_tokens=True`, `truncation=True`.
- target labels = same tokenizer on `summary`, `max_length=256`.
- no manual BOS insertion; no manual EOS duplication.
- labels are `input_ids` including native special tokens.
- the model's internal seq2seq shift is authoritative; no extra `logits[:, :-1]` shift.

#### 2.5.2 Training loss

```text
out = model(encoder_outputs=BaseModelOutput(last_hidden_state=memory),
            attention_mask=ones(1, len(memory)),
            labels=labels)
loss = out.loss
```

- built-in mT5 CE loss.
- `loss` finite; nonfinite aborts.
- batch=1.
- no label smoothing.
- `logits[t]` predicts `labels[t]`; no additional shift.
- full CE = `out.loss`.
- token CE = `cross_entropy(logits.reshape(-1,V), labels.reshape(-1),
  reduction='none', ignore_index=-100)`.

#### 2.5.3 Memory construction

- F/L: EG2 layer19 cache `h`; `A(h)` adapter output.
- P: native mT5 encoder output on source IDs; `A=identity`.
- PA: native mT5 encoder output; `A=adapter` random-init.
- F/L M: `A(h_i)[:753]`; P/PA M: `A(h_i)[:512]`.
- signal/eval donor crop: `K=min(len(real), len(donor))`.
- no padding; no truncation beyond stated K; no drop.
- training forward uses **real memory only**; donor crop is eval-only.

#### 2.5.4 Adapter / LoRA initialization

```text
torch.manual_seed(seed)
Adapter(512, 512): Linear(512,512) -> GELU -> Linear(512,512) -> LayerNorm(512)
```

- F/L/PA adapter is random-init from the registered seed.
- P has no adapter (`A=identity`).
- LoRA: 64 mT5 decoder q/k/v/o modules.
- `r=8`, `alpha=16`, `dropout=.05`, `scale=alpha/r`.
- `lora_A` kaiming_uniform(a=sqrt(5)); `lora_B` zeros.
- base decoder frozen; only adapter/LoRA trainable.

#### 2.5.5 Copyable mask and copy CE

```text
source_norm = NFKC(source).replace(" ", "")
for each target token id:
  special -> false
  piece = NFKC(tokenizer.decode([id])).strip().replace(" ", "")
  if no [0-9A-Za-z가-힣] -> false
  else piece in source_norm
```

- `copy_tokens = sum(copyable mask)`.
- `copy_ce = mean(token_ce[copyable mask & labels != -100])`.
- fewer than 5 copy tokens → `copy_ce=None`.
- **signal/eval path**: document excluded from copy endpoint and `n_signal`.
- **primary M endpoint**: any target with <5 copy tokens makes `endpoint_ok=false` → `M_NOT_EVALUABLE`; no silent key omission.
- token CE is same-position; no shift.
- copy coverage = `copy_tokens / target_tokens`.

#### 2.5.6 Donors

```text
donor lengths:
  F/L: EG2 layer19 h_len
  P/PA: native source token length after "summarize: " truncation at 512
      (all 20 val docs are 512; tie-break is doc_id asc)

donors(rid, arm):
  candidates = val20 IDs except rid
  sort by (abs(len_arm[c] - len_arm[rid]), c) ascending
  take first 5
  donor_id = 0..4 in sorted order
```

- donor list is **per arm**, not shared across F/L and P/PA.
- same donor list for all seeds within an arm.
- only val20 has donors; train20 has no donor.
- `K=min(len(real), len(donor))`.
- `shuffled` is a legacy name: it means **wrong-donor memory**, not token shuffle.
- wrong-donor CE = mean over the 5 donors.
- real CE = mean over the same 5 donor crops.
- donor lists and donor lengths are artifacts.
- no train-doc donor pool.

#### 2.5.7 Generation

- greedy decoding (`do_sample=false`, `num_beams=1`).
- `max_new_tokens=256`.
- `decoder_start_token_id = config.decoder_start_token_id or pad_token_id`.
- `eos_token_id`, `pad_token_id` from tokenizer.
- generation is telemetry only; not a gate.
- 20 val docs; no 753 requirement.

### 2.6 Data paths and h_len

```text
F5 JSONL:
  data/external/f5_pairs_v3_clean.jsonl
  fields: id, passage, summary

splits:
  reports/provenance/C5_clean/splits.json
  fields: train, val, test

EG2 layer19 cache:
  data/wave2c/eg2_native_layer19/layer19
  per-split npz: ids, lengths, h
  h_len = lengths[i]

native tokenizer:
  data/models/mt5-small
  source = "summarize: " + passage
  h_len = len(input_ids) after truncation at 512
```

- `h_len` is always the **source sequence length**, not tensor shape.
- `copyable_mask` uses the raw `passage` (no prefix).
- JSONL rows are read by `id`; no row order dependence.
- preflight `val_native_lengths` and `native_target_eligible_at_512` are the authority; assert every P/PA source length is 512.
- no test split read.

### 2.7 Training mode and RNG order

| arm | base decoder | native encoder | adapter | LoRA |
|---|---|---|---|---|
| F | eval | n/a (EG2) | train | none |
| L | eval | n/a (EG2) | train | train |
| P | eval | eval | none | train |
| PA | eval | eval | train | train |

- base decoder eval is mandatory; `model.train()` must not re-enable frozen layers.
- LoRA dropout is active only in train mode.
- evaluation restores all modules to eval.
- each arm starts from fresh model state.
- RNG order:

```text
torch.manual_seed(seed)
adapter = Adapter(512,512)      # F/L/PA
attach LoRA                    # L/P/PA; no reseed between
```

- adapter first, then LoRA.
- no reseed between construction steps.
- parameter inventory asserts expected trainable sets.
- P has no adapter.
- no cross-arm state reuse.

---

## 3. Primitive semantics

### 3.1 Tri-state

```text
true | false | not_assessable
```

### 3.2 Operators

```text
ANDn(args):
  any false -> false
  else any NA -> NA
  else true

ORn(args):
  any true -> true
  else any NA -> NA
  else false

NOT3(x):
  true -> false
  false -> true
  NA -> NA
```

- scalar tri-state predicates only.
- no seed/endpoint axis inside operator.
- `m_pass_l`(2), `m_valid`(4), `m_evaluable`(5).

### 3.3 L consensus

```text
l_signal = true   if l_copy_signal=true and l_full_signal=true
           false  if l_copy_signal=false and l_full_signal=false
           NA     otherwise

l_copy_signal := L_COPY_SIGNAL
l_full_signal := L_FULL_SIGNAL
```

- **binding is direct**; no alias.
- `l_signal` is not `ANDn`.
- `ANDn` only for `m_pass_l`, `m_valid`, `m_evaluable`, `copy_only`, `full_only`.

```text
copy_only = ANDn(l_copy_signal, NOT3(l_full_signal))
full_only = ANDn(l_full_signal, NOT3(l_copy_signal))
```

### 3.4 L table

| l_copy | l_full | l_signal | copy_only | full_only |
|---|---|---|---|---|
| true | true | true | false | false |
| true | false | **NA** | true | false |
| true | NA | NA | NA | false |
| false | true | **NA** | false | true |
| false | false | false | false | false |
| false | NA | NA | false | NA |
| NA | true | NA | false | NA |
| NA | false | NA | NA | false |
| NA | NA | NA | NA | NA |

- `copy_only`/`full_only` precede `l_signal` in dispatch.
- `false+NA` → `NOT_ASSESSABLE`; not `MEAN_CONTRAST_ONLY`.

### 3.5 L predicates

```text
L_COPY_SIGNAL = mean delta_copy >= .05
                AND copy CI lower > 0
                AND paired L>F copy mean > 0
                AND 2/3 registered seed copy means > 0

L_FULL_SIGNAL = mean delta_full > 0
                AND full CI lower > 0
                AND paired L>F full mean > 0
                AND 2/3 registered seed full means > 0
```

- `delta_copy = shuffled_copy_ce - real_copy_ce`.
- `delta_full = shuffled_full_ce - real_full_ce`.
- positive = real memory better.
- full threshold **`>0`**, copy **`.05`**.
- registered seeds 20261108/09/10.
- missing registered seed → predicate `NA`; 2-of-available 금지.
- existing 2 seeds only → `NA`, not 2/2.

---

## 4. Validity

### 4.0 Path flags

Four path flags gate `ASSAY_INVALID`. They are defined here.

```text
allowed_ids = train20_ids ∪ val20_ids   # frozen preflight
test_ids = sealed test 163 (never opened)

test_split_used:
  true   if any checked artifact contains an ID outside allowed_ids
  false  if every checked artifact's IDs are within allowed_ids
  NA     if an artifact is missing/unreadable

assay_path_ok:
  true   if preflight content hash matches §0.4
         AND preflight train20/val20 IDs match §1.1
         AND test_split_used is false
         AND P1 manifest SHA256 matches freeze `p1_manifest_sha256`
         AND `p1_used=false` AND `test_split_read=false`
  false  if any condition fails or contradictory known-use
  NA     if preflight or P1 manifest missing/malformed/unreadable

p0_path_ok:
  true   if P0 artifact exists
         AND `mode=p0_sanity_no_training`
         AND `test_split_used=false`
  false  if present but inconsistent
  NA     if missing

p_step100_path_ok:
  true   if exactly one P artifact per registered seed exists
         AND each has arm=P
         AND updates=100
         AND base_decoder=eval
         AND test_split_used=false
  false  if present but inconsistent
  NA     if any required artifact is missing

pa_step100_path_ok:
  true   if exactly one PA artifact per registered seed exists
         AND each has arm=PA
         AND updates=100
         AND base_decoder=eval
         AND test_split_used=false
  false  if present but inconsistent
  NA     if any required artifact is missing
```

- P0 is descriptive; `p0_path_ok` verifies artifact integrity, not a scientific gate.
- legacy P0 compatibility: `mode=p0_sanity_no_training` is sufficient; no `no_training` key is required.
- no test-ID scan of sealed test 163; allowlist membership only.
- path flags are recorded in every manifest.
- missing artifact is `NA`, not silently false/true.
- known failure (false) dominates unknown (NA).

### 4.1 Values

```text
ASSAY_INVALID
P_STEP100_NOT_VALID
PA_STEP100_NOT_VALID
NOT_ASSESSABLE
VALID
```

### 4.2 Known failure first

```text
if assay_path_ok is false
   or p0_path_ok is false
   or test_split_used is true
   or p_step100_path_ok is false:
    ASSAY_INVALID
```

### 4.3 Assay-tier NA

```text
elif assay_path_ok is not_assessable
   or p0_path_ok is not_assessable
   or p_step100_path_ok is not_assessable
   or test_split_used is not_assessable:
    NOT_ASSESSABLE
```

### 4.4 P/PA

```text
elif p_valid is false:
    P_STEP100_NOT_VALID
elif p_valid is not_assessable:
    NOT_ASSESSABLE
elif pa_step100_path_ok is not_assessable:
    NOT_ASSESSABLE
elif pa_step100_path_ok is false:
    PA_STEP100_NOT_VALID
elif pa_valid is false:
    PA_STEP100_NOT_VALID
elif pa_valid is not_assessable:
    NOT_ASSESSABLE
else:
    VALID
```

### 4.5 P_VALID / PA_VALID / calibration

**Validity (artifact integrity, not pass)**:

```text
P_VALID:
  false  if p_step100_path_ok is false
         OR any required tensor is nonfinite
  NA     if p_step100_path_ok is NA
         OR any required artifact is missing/unreadable
  true   if p_step100_path_ok is true
         AND for each registered seed, 20 native val20 docs
             ×2 variants ×2 endpoints ×2 memory kinds
             are present and finite
         AND no test/P1 ID

PA_VALID = same for PA, each registered seed
```

- validity does **not** require the M pass thresholds.
- `p_valid := P_VALID`; `pa_valid := PA_VALID`.
- `P_VALID` is tri-state; missing is NA, nonfinite is false.
- P/PA cohort = **20 native val20 docs**, 512.
- L/F cohort = 15 common IDs.
- P/PA validity does not use test 163.

**Calibration (M pass, separate)**:

```text
P_POS_PASS = 20 native val20 docs, 100-step:
             delta_pos_copy >= .05
             AND pos copy CI lower > 0
             AND delta_pos_full > 0
             AND pos full CI lower > 0

P_NORM_PASS = 20 native val20 docs, 100-step:
              delta_norm_copy >= .05
              AND norm copy CI lower > 0
              AND delta_norm_full > 0
              AND norm full CI lower > 0

PA_POS_PASS = same on 20 native val20 docs
PA_NORM_PASS = same on 20 native val20 docs
```

- bindings:

```text
m_pass_pos_p := P_POS_PASS
m_pass_norm_p := P_NORM_PASS
m_pass_pos_pa := PA_POS_PASS
m_pass_norm_pa := PA_NORM_PASS
```

- `m_valid = ANDn(m_pass_pos_p, m_pass_norm_p, m_pass_pos_pa, m_pass_norm_pa)`.
- P/PA validity + calibration failure → `M_CONTROL_INVALID` reachable.
- threshold asymmetry is intentional: P/PA acquisition strength uses copy `>= .05`; L M calibration uses copy `>0` (directional). No post-result change.
- P/PA use 3 registered seeds; seed mean first, then bootstrap; missing registered seed → `NA`; no 2-of-available.
- P/PA calibration intentionally does not use the `2/3 registered_seeds_positive` or paired `L>F` conjuncts used by L; there is no paired P/PA counterpart. This is documented arm asymmetry, not a threshold change.
- no alternate cohort.

### 4.6 Tier precedence

- assay-tier NA before P/PA validity.
- `p_step NA + p_valid=false` → `NOT_ASSESSABLE`.
- `pa_path NA + p_valid=false` → `P_STEP100_NOT_VALID`.
- `pa_path NA + pa_valid=false` → `NOT_ASSESSABLE`.
- F1–F11 in §7.

### 4.7 Core invariants

- validity never returns M status.
- test_split_used=true → ASSAY_INVALID.
- p_step false → ASSAY_INVALID.
- P valid + PA path false → PA_STEP100_NOT_VALID.
- P invalid + PA path false → P_STEP100_NOT_VALID.

---

## 5. Control

### 5.1 Availability

```text
cohort_ok  = common M target IDs >= 15/20
endpoint_ok = §9.5
seed_ok    = 3 registered seeds
replay_ok  = numeric replay pass
builder_ok = contributors >=10
             AND all M tensors finite
             AND ||M_POS_MEAN||_F > 0
             AND all M-target ||real_prefix_t||_F > 0 (F/L 15, P/PA 20)
```

```text
m_evaluable = ANDn(cohort_ok, endpoint_ok, seed_ok, replay_ok, builder_ok)
```

- `m_evaluable` false or NA → `M_NOT_EVALUABLE`.
- availability NA collapse is intentional; no silent true.
- seed_ok only registered seeds; no substitutes.

### 5.2 m_pass

```text
m_pass_l = ANDn(m_pass_pos_l, m_pass_norm_l)

m_valid = ANDn(
  m_pass_pos_p, m_pass_norm_p,
  m_pass_pos_pa, m_pass_norm_pa
)
```

- false-dominant; mixed false+NA → false.
- missingness-first 금지.
- P/PA pass uses 20 native val20 docs.
- M L pass uses 15 common targets.

### 5.3 PA veto

- PA is native 512 + random-init adapter + decoder LoRA.
- PA failure vetoes joint P/PA calibration; it does not prove native memory regime is intrinsically invalid.
- `m_valid` includes PA intentionally.
- `PA_RETENTION` is descriptive/nullable; never a gate.

### 5.4 control_status

```text
if m_evaluable is not true:
    M_NOT_EVALUABLE
elif p_valid is false or pa_valid is false:
    M_NOT_EVALUABLE
elif p_valid is not_assessable or pa_valid is not_assessable:
    NOT_ASSESSABLE
elif m_valid is false:
    M_CONTROL_INVALID
elif m_valid is not_assessable:
    NOT_ASSESSABLE
elif m_pass_l is true:
    M_CONTROL_PASS
elif m_pass_l is false:
    M_CONTROL_FAIL
else:
    NOT_ASSESSABLE
```

- `M_CONTROL_NOT_VALID` 금지.
- `M_CONTROL_INVALID` only when P/PA valid but calibration fail.
- `p_valid=false` routes to `M_NOT_EVALUABLE`, not `M_CONTROL_INVALID`.

---

## 6. Signal labels and dispatch

### 6.1 n_signal

```text
n_signal = number of 15 L-eligible docs with valid F/L copy and full endpoints
n_signal ∈ {NA, 0..15}
n_min = 15
```

- `n_signal=15` → `MARGINAL_SIGNAL_COHORT=true` (informational; not a dispatch input).
- val20 is descriptive only.
- no val20 signal count.
- missing seed no pooling.

### 6.2 Labels

- validity INVALID:
  - `L_SIGNAL_VALIDITY_INVALID`
  - `COPY_ONLY_VALIDITY_INVALID`
  - `FULL_ONLY_VALIDITY_INVALID`
- validity NOT_ASSESSABLE:
  - `L_SIGNAL_VALIDITY_NOT_ASSESSABLE`
  - `COPY_ONLY_VALIDITY_NOT_ASSESSABLE`
  - `FULL_ONLY_VALIDITY_NOT_ASSESSABLE`
- small N:
  - `INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL`
  - `INCONCLUSIVE_SMALL_N_WITH_COPY_ONLY`
  - `INCONCLUSIVE_SMALL_N_WITH_FULL_ONLY`
  - `INCONCLUSIVE_SMALL_N`
- valid-only:
  - `COPY_ONLY_WEAK`
  - `FULL_ONLY_WEAK`
  - `MEAN_CONTRAST_ONLY`
  - `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE`
- L/control:
  - `EXPLORATORY_L_SIGNAL`
  - `L_SIGNAL_M_CONTROL_FAIL`
  - `L_SIGNAL_M_CONTROL_INVALID`
  - `L_SIGNAL_M_CONTROL_NOT_EVALUABLE`
  - `L_SIGNAL_CONTROL_NOT_ASSESSABLE`
  - `NO_L_SIGNAL_CONTROL_INVALID`
  - `NO_L_SIGNAL_CONTROL_NOT_EVALUABLE`
- fallback `NOT_ASSESSABLE`.

### 6.3 Dispatch

```text
if n_signal is NA: NOT_ASSESSABLE
elif n_signal < 15:
    if l_signal true: INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL
    elif copy_only true: INCONCLUSIVE_SMALL_N_WITH_COPY_ONLY
    elif full_only true: INCONCLUSIVE_SMALL_N_WITH_FULL_ONLY
    else: INCONCLUSIVE_SMALL_N
elif validity == NOT_ASSESSABLE:
    if l_signal true: L_SIGNAL_VALIDITY_NOT_ASSESSABLE
    elif copy_only true: COPY_ONLY_VALIDITY_NOT_ASSESSABLE
    elif full_only true: FULL_ONLY_VALIDITY_NOT_ASSESSABLE
    else: NOT_ASSESSABLE
elif validity != VALID:
    if l_signal true: L_SIGNAL_VALIDITY_INVALID
    elif copy_only true: COPY_ONLY_VALIDITY_INVALID
    elif full_only true: FULL_ONLY_VALIDITY_INVALID
    else: NOT_ASSESSABLE
elif copy_only true: COPY_ONLY_WEAK
elif full_only true: FULL_ONLY_WEAK
elif l_signal is NA: NOT_ASSESSABLE
elif l_signal true:
    if control == M_CONTROL_PASS: EXPLORATORY_L_SIGNAL
    elif control == M_CONTROL_FAIL: L_SIGNAL_M_CONTROL_FAIL
    elif control == M_CONTROL_INVALID: L_SIGNAL_M_CONTROL_INVALID
    elif control == M_NOT_EVALUABLE: L_SIGNAL_M_CONTROL_NOT_EVALUABLE
    else: L_SIGNAL_CONTROL_NOT_ASSESSABLE
elif control == M_CONTROL_PASS: MEAN_CONTRAST_ONLY
elif control == M_CONTROL_FAIL: NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE
elif control == M_CONTROL_INVALID: NO_L_SIGNAL_CONTROL_INVALID
elif control == M_NOT_EVALUABLE: NO_L_SIGNAL_CONTROL_NOT_EVALUABLE
else: NOT_ASSESSABLE
```

### 6.4 Preservation

- raw flags always in `flags`.
- `(validity, control, signal, reason)` tuple.
- INVALID vs NOT_ASSESSABLE labels distinct.
- 9 L pairs preserved.
- small-N does not hide validity; triple always reported.

---

## 7. Truth-table and fixtures

### 7.1 Per-axis

- validity path 3^5
- P/PA 3^2
- control availability 3^4 + builder 3^1
- calibration 3^6 (m_pass_l 2 operands + m_valid 4 operands)
- L 3^2 (9 pairs; §3.4)
- n_signal `{NA,0..15}`

### 7.2 F1–F11

| fixture | flags | expected |
|---|---|---|
| F1 | test_split NA + P path false | `ASSAY_INVALID` |
| F2 | test_split NA + paths good | `NOT_ASSESSABLE` |
| F3 | pa_path NA + P invalid | `P_STEP100_NOT_VALID` |
| F4 | pa_path NA + P valid | `NOT_ASSESSABLE` |
| F5 | assay NA + P path false | `ASSAY_INVALID` |
| F6 | assay NA + paths good | `NOT_ASSESSABLE` |
| F7 | pa_path false + P valid | `PA_STEP100_NOT_VALID` |
| F8 | pa_path false + P invalid | `P_STEP100_NOT_VALID` |
| F9 | p_step NA + p_valid NA | `NOT_ASSESSABLE` |
| F10 | pa_path NA + pa_valid NA | `NOT_ASSESSABLE` |
| F11 | n<15 + validity INVALID + l_signal true | `INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL`; triple validity=INVALID |

### 7.3 Primitive fixtures 16–18

Fixtures use primitive flags; derived `m_pass_l`/`m_valid` are not inputs.

- F11 dispatches on small-N first; validity INVALID is preserved in the reported triple, not hidden.
- if l_signal is false in F11, expected small-N label follows the copy-only/full-only/plain order.

#### Fixture 16 — EXPLORATORY

```text
validity_status = VALID
n_signal = 15
l_copy_signal = true
l_full_signal = true
m_evaluable = true
p_valid = true
pa_valid = true
m_pass_pos_l = true
m_pass_norm_l = true
m_pass_pos_p = true
m_pass_norm_p = true
m_pass_pos_pa = true
m_pass_norm_pa = true
```

Derived:

```text
l_signal = true
m_pass_l = true
m_valid = true
control_status = M_CONTROL_PASS
signal_status = EXPLORATORY_L_SIGNAL
```

#### Fixture 17 — MEAN_CONTRAST_ONLY

```text
validity_status = VALID
n_signal = 15
l_copy_signal = false
l_full_signal = false
m_evaluable = true
p_valid = true
pa_valid = true
m_pass_pos_l = true
m_pass_norm_l = true
m_pass_pos_p = true
m_pass_norm_p = true
m_pass_pos_pa = true
m_pass_norm_pa = true
```

Derived:

```text
l_signal = false
m_pass_l = true
m_valid = true
control_status = M_CONTROL_PASS
signal_status = MEAN_CONTRAST_ONLY
```

#### Fixture 18 — NO_AFFIRMATIVE

```text
validity_status = VALID
n_signal = 15
l_copy_signal = false
l_full_signal = false
m_evaluable = true
p_valid = true
pa_valid = true
m_pass_pos_l = false
m_pass_norm_l = true
m_pass_pos_p = true
m_pass_norm_p = true
m_pass_pos_pa = true
m_pass_norm_pa = true
```

Derived:

```text
l_signal = false
m_pass_l = false
m_valid = true
control_status = M_CONTROL_FAIL
signal_status = NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE
```

### 7.4 Named cells

- F1–F11.
- 9 L pairs.
- control 5 values.
- named cells are fixtures 16–18 only.
- generic “M pass L” text must include validity/availability/calibration/L/n prerequisites.
- `m_pass_l=false` can yield `M_CONTROL_FAIL` only with `m_evaluable=true`, P/PA valid/calibrated, m_valid=true.
- no control PASS + m_pass_l=false cell.

### 7.5 Requirements

- every named cell exact output.
- every label reachable.
- inputs not mutated.
- pure function; no model/data.
- synthetic fixtures.
- no full Cartesian requirement; per-axis + named.

---

## 8. P/PA

### 8.1 P

- native mT5 512, no adapter, decoder LoRA.
- 100 updates.
- 20 native val20 docs.
- `P_VALID` §4.5.

### 8.2 PA

- native mT5 512, random-init adapter, decoder LoRA.
- 100 updates.
- 20 native val20 docs.
- `PA_VALID` §4.5.
- `PA_STEP100_NOT_VALID` is acquisition failure.
- `PA_RETENTION` nullable/descriptive; not gate.
- geometry caveat: 512 vs 753; no direct retention comparison.

### 8.3 P/PA M pass

- `m_pass_pos_p/norm_p`: 20 native val20 docs.
- `m_pass_pos_pa/norm_pa`: 20 native val20 docs.
- M L pass uses 15 common.
- `m_valid` = P/PA calibration.

---

## 9. M

### 9.1 Cohorts

| arm | M K | M targets | contributors |
|---|---:|---:|---:|
| F | 753 | 15 common | 16 |
| L | 753 | 15 common | 16 |
| P | 512 | 20 native (15 common + 5 native-only) | 20 |
| PA | 512 | 20 native (15 common + 5 native-only) | 20 |

- signal eligible 15.
- val20 descriptive.
- P/PA validity/M = **20 native val20 docs**; F/L = 15 common.
- `full_k_secondary` is historical/descriptive only; not in any gate.
- zero-margin: K=753; K=754→14; abort.
- no 15→14; no native→common substitution.

### 9.2 Builder

For each seed and arm:

```text
model.eval()
with torch.no_grad():
    contributors = [i for i in train20 if h_len_i >= K_M]
    if len(contributors) < 10: builder_ok=false
    else:
        h_i = A(h_i)[:K_M]       # K_M × 512
        M_POS_MEAN = mean_i h_i   # K_M × 512
```

- `h_len_i` scalar.
- `A=adapter` F/L/PA; `A=identity` P.
- F/L `[:753]`; P/PA `[:512]`.
- eval/no_grad; no dropout.
- seed builder; seed-average before bootstrap.
- M primary reference = `A(h_t)[:K_M]`.
- donor-crop 금지.
- `M_GLOBAL` secondary.

### 9.3 M_NORM

```text
real_prefix_t := A(h_t)[:K_M]
M_NORM(t) = M_POS_MEAN * (||real_prefix_t||_F / ||M_POS_MEAN||_F)
```

- one global mean direction.
- per-target magnitude scalar.
- same adapter space.
- no raw EG2 embedding.
- no per-target matrix.
- M primary reference and real memory use `real_prefix_t`.

### 9.4 Variant × memory table

| variant | control tensor | real tensor | delta name |
|---|---|---|---|
| `M_POS_MEAN` | `M_POS_MEAN` | `real_prefix_t` | `delta_pos` |
| `M_NORM` | `M_NORM(t)` | `real_prefix_t` | `delta_norm` |

- `memory_kind ∈ {control, real}`.
- `M_POS_MEAN` and `M_NORM` are distinct controls.
- Both variants pass independently.
- `M_PASS_POS` uses `delta_pos`; `M_PASS_NORM` uses `delta_norm`.
- not the same test twice.
- `M_GLOBAL` descriptive only.

### 9.5 Endpoint identity

`endpoint_ok`:

- exact common/native target domain:
  - F/L: 15 common IDs
  - P/PA: 20 native IDs (15 common + 5 native-only)
- 3 registered seeds.
- 4 arms F/L/P/PA.
- 2 variants M_POS_MEAN/M_NORM.
- 2 endpoints copy/full.
- 2 memory kinds control/real.
- **record count = 1,680**
  - common target: 15 × 96 = 1,440
  - native-only target: 5 × 48 = 240
- common target appears **96 times**; native-only target appears **48 times**.
- exact key set, not only count.
- P/PA native-20 must be fully covered; missing native doc → `M_NOT_EVALUABLE`.
- real/control CE finite.
- copy_ce != None.
- copy tokens >=5.
- no duplicate full key.
- no missing key.
- no 15→14 substitution.
- no native→common substitution.
- no donor-crop for primary M.

### 9.6 delta/pass

```text
delta_pos_copy = control_pos_copy_ce - real_copy_ce
delta_pos_full = control_pos_full_ce - real_full_ce
delta_norm_copy = control_norm_copy_ce - real_copy_ce
delta_norm_full = control_norm_full_ce - real_full_ce
```

- positive = real memory better.
- no `delta_memfree` term.

### 9.6.1 Phase-7 diagnostic recipe

```text
docs = 15 common
donors = 5 per doc (same donor rule)
real_prefix = memory(real doc) in arm memory space
donor_prefix = memory(donor doc) in arm memory space
K_d = min(len(real_prefix), len(donor_prefix))
assert 1 <= K_d <= min(len(real_prefix), len(donor_prefix))
assert real_prefix[:K_d].shape[0] == donor_prefix[:K_d].shape[0] == M_POS_MEAN[:K_d].shape[0] == M_NORM(t)[:K_d].shape[0] == K_d

control_pos = M_POS_MEAN[:K_d]
control_norm = M_NORM(t)[:K_d]   # K_M-scaled vector truncated; no renormalization
real = real_prefix[:K_d]
wrong = donor_prefix[:K_d]

records = 15 docs × 5 donors × 2 variants × 2 endpoints × 2 memory kinds
        = 600 per arm-seed
memory_kind ∈ {real, donor}
endpoint ∈ {copy, full}
variant ∈ {M_POS_MEAN, M_NORM}
```

- `M_NORM(t)[:K_d]` is the §9.3 K_M-scaled vector truncated at `K_d`; do not renormalize at `K_d`.
- P/PA always `K_d=K_M=512`; F/L donors with `h_len<753` are the only truncation case.
- `donor_prefix` is the donor document's memory in the **same arm memory space**; it is not a token shuffle.
- donor only determines `K_d`; donor content is not mixed into real.
- `control` is a **baseline**, not a record memory kind in phase 7.
- each record stores:
  - `ce` = raw CE of the record tensor (real or donor) on the target;
  - `baseline_ce` = `CE(control_variant[:K_d], target, endpoint)` recomputed **in phase 7**;
  - `delta` = `baseline_ce - ce`.
- phase-5 stored CE at `K_M` must not be reused as `baseline_ce`.
- `variant` selects the baseline; raw `ce` may duplicate across variants, but `delta` differs.
- phase 5 subset is `{control, real}`, `donor_id=null`; phase 7 subset is `{real, donor}`, `donor_id=0..4`.
- phase 7 is diagnostic; it does not feed `m_valid` or any gate.
- `stored_record` = `{key, ce, baseline_ce, delta}` (nested key allowed).
- `hash_record` = flat 8-field object including `ce`; `baseline_ce`/`delta` are excluded.
- no third memory axis.

```text
M_PASS_POS = delta_pos_full > 0
             AND full CI lower > 0
             AND delta_pos_copy > 0
             AND copy CI lower > 0

M_PASS_NORM = delta_norm_full > 0
              AND full CI lower > 0
              AND delta_norm_copy > 0
              AND copy CI lower > 0

m_pass_l = ANDn(M_PASS_POS_L, M_PASS_NORM_L)
# M_PASS_*_L = same four-conjunct pass on L arm, 15 common targets
```

### 9.7 Aggregation

- seed builder; seed-average.
- 3 seeds ×15/20 docs ≠ 45/60 independent.
- false-dominant.
- final checkpoint hash.
- replay separate.
- `m_pass_l` 2 operands.
- `m_valid` 4 operands.
- `m_evaluable` 5 operands.

### 9.8 Zero-margin

- K=753; 754→14.
- F/L cohort 15/15; P/PA cohort 20/20.
- F/L target <15, or P/PA native target <20, or contributors <10 → `M_NOT_EVALUABLE`.
- report `ZERO_MARGIN_COHORT_FAIL` + missing ID.
- no 15→14.
- no K change.
- D0 h-length assert.

---

## 10. Statistics

### 10.1 Constants

```text
n_boot=1000
ci=percentile 2.5/97.5
bootstrap_seed=20261109
unit=document
seed_average_before_bootstrap=true
n_min_signal=15
```

### 10.2 Stats module

- `runner/c5_pm_stats.py` new.
- `bootstrap_paired(seed=20261109)`.
- `documents_positive(delta)` = count of docs with delta > 0.
- `registered_seeds_positive` = count of registered seed means > 0.
- P0 helper `seeds_positive` is a **document** count; it is not the registered field.
- no P0 helper reuse (`seed=20261108`, mislabeled doc count).
- no legacy `bootstrap_paired`.

### 10.3 Bootstrap

- doc-level paired.
- seed average before bootstrap.
- 1,000 resamples.
- RNG: `numpy.random.default_rng(20261109)` (PCG64), fresh generator per bootstrap call.
- CI: `numpy.percentile(..., [2.5,97.5], method="linear")`.
- no legacy `RandomState`.
- same retained IDs copy/full/L−F.
- no pooling missing seed.
- no 3×15 independence.

### 10.4 Tail

`tail_driven` = **signal tail**:

```text
arm = L
endpoint = copy
control = shuffled donor
variant = NA (not an M variant)
cohort = 15 L-eligible docs
delta = shuffled_copy_ce - real_copy_ce
```

- `M_POS_MEAN`/`M_NORM` tails are descriptive:
  - `tail_driven_M_POS_MEAN`
  - `tail_driven_M_NORM`
- hard B0-B gate uses **signal tail only**.

```text
top3_abs_share = sum(top3 |delta|) / sum(all |delta|)
top3_signed_share = sum(top3 delta) / sum(all delta)
leave_top3_mean = mean(delta excluding top3 by |delta|)
```

- gate uses `top3_abs_share`.
- signed share descriptive.
- ties: sort by `|delta|` desc, then `doc_id` asc; top3 exactly 3.
- n<4 → `leave_top3_mean=NA`.
- denominator 0 → share=NA.

```text
if leave_top3_mean is not NA and leave_top3_mean <= 0: true
elif leave_top3_mean is NA or top3_abs_share is NA: NA
elif top3_abs_share > .50: true
else: false
```

- threshold `.50` unchanged.
- raw top3 IDs/sum/denominator/signed share artifact.
- P0 val:
  - signed share **.4862**
  - absolute share **.43355** (val20), **.455** (15 common)
  - P0 descriptive only; absolute is gate metric if it were used.
- P0 used `source_max_length=256`; Phase 6 M uses 512; P0 is not trained P/PA/L calibration.
- B0-B requires `tail_driven=false`; true/NA not pass.

---

## 11. D0/D1/cap

### 11.1 Registered

| 항목 | 값 |
|---|---:|
| units | 12 |
| updates | 1,200 |
| wall | 120 min |
| threads | 6 |
| GPU | none |
| retry | none |

### 11.2 D0

- 0 optimizer updates.
- ≤4 configs = one 0-update config per arm (F/L/P/PA); no variant/seed duplication.
- ≤15 min.
- seed 20261111.
- `labels_computed:false`.
- `not_a_result:true`.
- separate from registered cap.
- h-length assert: F/L cache length; P/PA native length = 512.
- no timing claim.
- control manifest path: `reports/provenance/C5_b0a/control_manifest/`; ~0.3 GB; retain through B0-B.

### 11.3 D1

- **4 arms × 1 debug seed = 4 units**.
- debug seed 20261111.
- 1 update/arm.
- ≤20 min.
- separate approval.
- no **decision** labels and no signal labels; target-token labels for CE are computed.
- `labels_computed:false` refers to decision/signal labels, not target-token labels.
- control manifest is built after step0, before any decision label.
- `not_a_result:true`.
- no registered seed.

Phases:

1. one train update per arm
2. step0 eval 20 docs ×5 donors
3. final eval 20 docs ×5 donors
4. M builder train20 + targets (F/L 15 common, P/PA 20 native) ×2 variants
5. primary M CE: F/L 15×2×2×2 = **120/arm-seed**; P/PA 20×2×2×2 = **160/arm-seed**; total **560** across 4 arms
6. generation 20×256
7. donor diagnostic replay: 15 common ×5×2×2×2 = **600/arm-seed**
8. load/checkpoint/process/report overhead

- phase 5 donor-free; `donor_id=null`.
- phase 7 donor-level; `donor_id=0..4`; 15 common diagnostic only.
- phase 7 is **diagnostic**, not primary.
- all 8 measured; missing phase → no projection.
- step0 before update or restored state.

### 11.4 Replay domains

- primary M replay: phase 5, donor-free, F/L 120, P/PA 160 per arm-seed; total **560**.
- donor diagnostic: phase 7, donor-level, 600/arm-seed; 15 common only.
- not comparable as same population.
- `debug_replay_hash` = D1 synthetic only.
- `final_replay_hash` = registered postrun.
- **never compare debug hash directly to final hash**.
- numeric replay: `atol=1e-5`, `rtol=1e-4`.
- artifact integrity: exact SHA256, separate field.

**Replay procedure**:

1. load `final_checkpoint_hash.json` (object, 12 keys `"arm/seed"` → `"sha256:..."`) + `control_manifest.json` + tensors; verify `control_digest`.
   - checkpoint paths: `reports/provenance/C5_b0a/checkpoints/{arm}/{seed}.pt`; no single checkpoint.
2. for each unit, restore mode: base decoder eval, adapter eval, LoRA eval.
3. recompute phase-5 unit CE: F/L 120 per unit, P/PA 160 per unit; aggregate exact 1,680 keys.
4. compare CE to stored values with `atol/rtol`.
5. recompute phase-7 diagnostic 600/arm-seed separately; verify key-coverage golden and numeric `ce`/`baseline_ce`/`delta` at `atol=1e-5`, `rtol=1e-4`.
6. `replay_ok` true only if primary 1,680 coverage and numeric comparison pass.
7. phase-7 diagnostic failure does not change primary `replay_ok`; it is reported separately as `diagnostic_replay_ok`.
8. no re-training; no optimizer step.

### 11.5 T_proj

```text
T_proj = 3 * sum_{arm in F,L,P,PA} (
            100 * t_train_arm
          + t_step0_eval_20x5_arm
          + t_step100_eval_20x5_arm
          + t_M_build_arm
          + t_initial_M_ce_arm
          + t_generate_20x256_arm
          + t_primary_replay_arm
          + t_replay_15x5x2x2x2_arm
          + t_overhead_arm
        )
```

- phase 5 = F/L 120, P/PA 160; total 560 (D1 debug).
- registered primary replay = 1,680 total; per arm-seed F/L 120, P/PA 160; per-arm across seeds `F=360, L=360, P=480, PA=480`.
- `t_primary_replay_arm` uses the arm-seed phase-5 record count (D1 120/160; registered 120/160 per seed; 360/480 per arm across 3 seeds).
- phase 7 = 600/arm-seed diagnostic.
- `T_proj` finite/nonnegative/≤96 min.
- D1 없이 3-seed 금지.
- D0 projection 금지.
- no timing probe substitute.
- 120-min hard abort.

### 11.6 Cap

- D0/D1 separate.
- prospective max 1,204 updates / 155 min (not grant).
- no retry/extension.

---

## 12. Canonical hash / golden vectors

### 12.1 Checkpoint state hash

```text
sorted state_dict keys
include adapter parameters + LoRA A/B
exclude frozen base
frame:
  name_len:u32 LE | name_utf8
  dtype_len:u8 | dtype_str
  ndim:u8 | shape:u32×ndim LE
  nbytes:u64 LE | little_endian_contiguous_bytes
SHA256 over concatenated frames
```

```json
{
  "F/20261108": "sha256:...",
  "F/20261109": "sha256:...",
  "F/20261110": "sha256:...",
  "L/20261108": "sha256:...",
  "L/20261109": "sha256:...",
  "L/20261110": "sha256:...",
  "P/20261108": "sha256:...",
  "P/20261109": "sha256:...",
  "P/20261110": "sha256:...",
  "PA/20261108": "sha256:...",
  "PA/20261109": "sha256:...",
  "PA/20261110": "sha256:..."
}
```

- `dtype_str` is numpy charcode, e.g. `<f4`; no `torch.float32` strings.
- no padding.
- empty state → SHA256 empty bytes.
- frozen base/config/mode in manifest.
- `final_checkpoint_hash` postrun map: JSON object with 12 keys `"arm/seed"` → `"sha256:..."`; checkpoint paths `checkpoints/{arm}/{seed}.pt`; no single-checkpoint replay.

**Control tensor schema**:

```text
control_manifest/
  {arm}/{seed}/M_POS_MEAN.npz
  {arm}/{seed}/M_NORM/{target_id}.npz
  control_manifest.json
```

- NPZ array key: `tensor`.
- `M_POS_MEAN` is shared per arm/seed; metadata `target_id="__shared__"`.
- `M_NORM` metadata `target_id` = M target doc_id.
- canonical name prefix is logical `control/`; filesystem prefix is `control_manifest/`.
- canonical name:
  - `control/{arm}/{seed}/M_POS_MEAN`
  - `control/{arm}/{seed}/M_NORM/{target_id}`
- dtype `<f4`, shape `[K_M,512]`.
- `control_manifest.json` version 1 fields: `name`, `path`, `array_key`, `target_id`, `dtype`, `shape`, `sha256`.
- `sha256` is over the canonical **tensor frame**, not the ZIP archive bytes:

```text
u32le name_len | name_utf8 | u8 dtype_len | dtype_str
| u8 ndim | u32le shape[ndim] | u64le nbytes
| little_endian_contiguous_bytes
```

- `control_digest` = SHA256 over all control frames sorted by canonical name.
- replay loads tensors, verifies `control_digest`, and recomputes CE.
- hash-only reconstruction is forbidden.
- includes all 15 F/L or 20 P/PA M target tensors.

### 12.2 Replay record

```text
key = (doc_id, arm, seed, variant, endpoint, memory_kind, donor_id)
```

- `doc_id` only; not `id`.
- `arm ∈ {F,L,P,PA}`.
- `seed ∈ {20261108,20261109,20261110}`; debug 20261111.
- `variant ∈ {M_POS_MEAN,M_NORM}`.
- `endpoint ∈ {copy,full}`.
- `memory_kind ∈ {control,real,donor}`.
- phase 5 subset: `{control,real}`, `donor_id=null`.
- phase 7 subset: `{real,donor}`, `donor_id=0..4`.
- `donor_id` is the canonical field: `null` for phase 5; `0..4` for phase 7.
- `donor_sort` is internal only: `-1` for null, `0..4` for donors; it is not serialized and not hashed.
- sort ascending by `(doc_id, arm, seed, variant, endpoint, memory_kind, donor_sort)`; null sorts before 0.
- `ce` float64 finite; nonfinite reject.
- `hash_record` is a **flat 8-field object**, not `{key, ce}`:
  ```json
  {"arm":"L","ce":1.0,"doc_id":"doc_a","donor_id":null,"endpoint":"copy","memory_kind":"control","seed":20261108,"variant":"M_POS_MEAN"}
  ```
- `baseline_ce` and `delta` are excluded from the hash domain.
- canonical JSON `sort_keys=true,separators=(',',':')`.
- SHA256 over the canonical JSON of the **sorted record array** (one array); record-by-record concatenation is forbidden.
- `debug_replay_hash` D1 only.
- `final_replay_hash` postrun only.
- numeric replay tolerance; hash exact.

### 12.3 Golden vectors

State vector:

```text
a: dtype <f4, shape [2], bytes 0000803f 000000c0
b: dtype <f4, shape [1,1], bytes 0000003f
```

Expected SHA256:

```text
state_full = 43ecb58e197d5789df0a9dbbc67beba11538b8063c3da8ac46f96e1e95d65712
state_empty = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

Replay vector records:

```json
[
  {"arm":"L","ce":1.0,"doc_id":"doc_a","donor_id":null,"endpoint":"copy","memory_kind":"control","seed":20261108,"variant":"M_POS_MEAN"},
  {"arm":"L","ce":2.0,"doc_id":"doc_a","donor_id":null,"endpoint":"copy","memory_kind":"real","seed":20261108,"variant":"M_POS_MEAN"},
  {"arm":"L","ce":3.5,"doc_id":"doc_b","donor_id":0,"endpoint":"full","memory_kind":"real","seed":20261108,"variant":"M_POS_MEAN"}
]
```

Expected SHA256:

```text
replay_three = c43ea35c46c51a0e82cebe5764a989d1b67012b2690246a0f89a94dff7851667
```

- Expected digests are independent constants; implementation must not compute and overwrite them.
- `docs/hoplite/c5_b0a_pm_prereg_v1_0_6_2026-11-09/golden_vectors.json` stores base, key-coverage, and control-manifest vectors:

```text
state       43ecb58e197d5789df0a9dbbc67beba11538b8063c3da8ac46f96e1e95d65712
empty       e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
replay_base c43ea35c46c51a0e82cebe5764a989d1b67012b2690246a0f89a94dff7851667
key_coverage 8277a713fd52b2ba8c5c3c859c83fd78593aa5a381f8640448e2128a97af7a20
control     6b50c226ecc402323787bd25b20e57fe57376caeb925c040b57985ccc0ec1938
```
- `key_coverage_golden` is a 4-record key-coverage fixture, not the 600-record phase-7 domain; phase-7 diagnostics are numeric-only.
- permutation/duplicate/missing-key tests.
- control-manifest golden is a synthetic `[1,1]` framing fixture, not a trained tensor.
- control-manifest tensors are sorted ascending by canonical name (`M_NORM` before `M_POS_MEAN`).
- real control tensors are `[K_M,512]`; their `control_digest` is postrun-only and is not represented by the synthetic fixture.

---

## 13. Test matrix / DoD

### 13.1 Decision tests

- ANDn 2/4/5.
- F1–F11.
- §3.4 9 L pairs.
- fixtures 16–18.
- all labels reachable.
- validity INVALID vs NOT_ASSESSABLE.
- small-N triple.
- `m_valid`/`M_CONTROL_INVALID`.
- availability NA → `M_NOT_EVALUABLE`.
- `m_pass_l` derivation.
- no `M_CONTROL_NOT_VALID`.

### 13.2 M tests

- F/L/P/PA builder.
- P identity.
- `h_len_i`.
- `M_POS_MEAN` shape.
- `M_NORM` same adapter.
- endpoint 1,680 exact mixed key set.
- duplicate/missing target.
- target appears 96 times.
- zero/nonfinite norm.
- seed aggregation.
- M_PASS_POS/NORM independent.
- no delta_memfree.
- zero-margin abort.

### 13.3 Stats tests

- n_boot 1000.
- seed 20261109.
- documents_positive.
- registered_seeds_positive.
- 2/3 registered.
- missing seed NA.
- tail signal; variant NA.
- top3 absolute/signed.
- tie rule.
- partial endpoint.

### 13.4 Hash/replay tests

- state golden 43ecb…
- empty golden e3b0…
- replay base golden c43ea…
- key-coverage golden 8277a7…
- canonical JSON; ascending `key` sort.
- canonical key uses `donor_id` null/0..4; `donor_sort` internal only.
- permutation invariance.
- 12 checkpoint map; per-unit 120/160; aggregate 360/480/1,680.
- phase-5 subset {control,real}; phase-7 subset {real,donor}.
- array-envelope digest; per-record concatenation must fail.
- control tensor canonical-name order.
- numeric tolerance vs exact hash.
- debug vs final separation.
- P1 strict both flags; malformed → NA.

### 13.5 Implementation DoD

- pure decision function.
- no model/data in decision.
- `test_split_used:false`.
- validity enum assertion.
- manifest/checkpoint/replay hash.
- D0/D1 gates.
- no B0-B auto.
- no test 163/P1.
- no legacy `seeds_positive` in registered stats; no stale registered counts.
- no `ADAPTER_REGIME_LOSS`.
- no `PA only`.
- no 0..20.
- no 753 training requirement.

---

## 14. B0-B boundary

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS
AND signal_status == EXPLORATORY_L_SIGNAL
AND m_valid == true
AND n_signal >= 15
AND tail_driven == false
AND leakage/mode/metric pass
AND artifact complete
AND separate prereg/approval
```

- n_signal max 15; `>=15` means exactly 15.
- tail true/NA blocks.
- `EXPLORATORY_L_SIGNAL` alone not approval.
- full_k_secondary/P0/PA_RETENTION not evidence.
- M scope `M_CONTROL_PREFIX753_COHORT15`.
- no B1/B2/Stage C auto.

---

## 15. Traceability appendix

Historical only; not implementation authority.

| v1.0.6 area | source chain |
|---|---|
| arms | r3.4 §7.4 |
| L table | r3.4 §2.4; r3.3 §2.3 |
| F/P builder | r3.4 §8.2 |
| real_prefix_t | r3.4 §8.3 |
| n_signal 15 | r3.4 §5.1 |
| M endpoints 1,680 | v1.0.1 §9.5 + v1.0.6 repair |
| tail | v1.0.1 §10.2 + v1.0.6 repair |
| P/PA cohort 20 | v1.0.1 §9.1 + v1.0.6 separation |
| replay domains | v1.0.1 §11.4 + v1.0.6 tensors |
| L binding | v1.0.1 §9.6 + v1.0.6 bindings |
| F/L memory scope | v1.0.1 §2.3 + v1.0.6 §2.6 |
| PA_VALID | v1.0.6 §4.5 |
| golden vectors | v1.0.6 §12.3 |
| full_k_secondary | historical only; not normative |

Superseded:

- r3.4 and all earlier P/M docs.
- any statement `n_signal 0..20`.
- any statement `PA only`.
- any statement `M pass L false + control PASS`.
- any `delta_memfree`.
- any 753 training/generation requirement.
- any replay debug/final direct comparison.

---

## 16. Freeze / review

### 16.1 Review

- v1.0.6 review required.
- If NARROW: must-fix only; no new scientific choices.
- No code before freeze.

### 16.2 Freeze

- freeze manifest: `docs/plan_c5_b0a_pm_prereg_v1_0_5_FREEZE.json`
- schema:

```json
{
  "schema_version": 1,
  "status": "frozen",
  "plan_path": "docs/plan_c5_b0a_pm_prereg_v1_0_5.md",
  "plan_sha256": "...",
  "freeze_commit": "...",
  "p1_manifest_sha256": "...",
  "golden_sha256": "...",
  "preflight_sha256": "...",
  "helper_commits": {
    "runner/c5_mt5_layer_probe.py": "...",
    "runner/c5_a1_lora.py": "...",
    "runner/c5_mt5_lora_b0.py": "...",
    "runner/c5_a2null_eval.py": "..."
  },
  "registered_seeds": [20261108, 20261109, 20261110]
}
```

- freeze order: (1) final plan commit; (2) populate `_FREEZE.json`; (3) manifest commit; (4) D0 report records `freeze_manifest_sha256`.
- plan/content SHA-256 is computed after step 1; the manifest is not part of the plan hash.
- implementation references only freeze commit + manifest.
- post-freeze corrections only numbered ERRATA.
- `p1_manifest_sha256` binds `p1_usage.json`.
- `golden_sha256` binds `golden_vectors.json`.

### 16.3 Approval

> **v1.0.6을 Phase 6 protocol contract로 동결하고, 구현 + unit tests + D0 zero-update mechanics debug를 진행해도 되는가?**

Approval does not include:
- D1
- 3-seed
- B0-B/B1/B2/Stage C
- test 163/P1
- T5Gemma2 (D-108 STOP)

---

## 17. Implementation appendix

### 17.1 External module contracts

These helpers are authoritative; implementation must import them or reproduce their contract exactly.

| symbol | path | contract |
|---|---|---|
| `Adapter` | `runner/c5_mt5_layer_probe.py` | 512→512 adapter, `forward(x)` |
| `make_labels` | `runner/c5_mt5_layer_probe.py` | tokenizer labels, `max_length` |
| `load_layer_cache` | `runner/c5_mt5_layer_probe.py` | `split, dir` → cache dict |
| `LoRALinear` | `runner/c5_a1_lora.py` | A kaiming, B zeros |
| `attach_decoder_lora_mt5` | `runner/c5_mt5_lora_b0.py` | 64 modules, `r=8`, `alpha=16` |
| `native_memory` | `runner/c5_mt5_lora_b0.py` | native encoder hidden |
| `repeated_4gram_rate` | `runner/c5_a2null_eval.py` | generation diagnostic only |

- signatures and behavior are frozen by the cited files at the freeze commit.
- no local reimplementation with different semantics.
- missing helper → `NOT_ASSESSABLE`; do not guess.
- helper commit hashes are recorded in the freeze manifest.

### 17.2 File artifacts

```text
reports/provenance/C5_b0a/checkpoints/{arm}/{seed}.pt
reports/provenance/C5_b0a/final_checkpoint_hash.json
control_manifest/
phase7_records/{arm}/{seed}.json
p1_usage.json
p1_usage.postrun.json
phase6_artifact_registry.json
```

- `p1_usage.json` is frozen; postrun file is separate.
- `phase6_artifact_registry.json` lists expected artifacts.
- no artifact path outside `reports/provenance/C5_b0a/` for provenance.

