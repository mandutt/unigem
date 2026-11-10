# C5 F0 — Consolidated Implementation Spec v1.0 (DRAFT)

- 작성일: 2026-11-10
- 상태: **DRAFT — 미승인·미실행**
- 대체 대상: `docs/plan_c5_f0_v1_13_2026-11-09.md` 및 이전 v1.0~v1.12 개정 연쇄
- 목적: 구현자가 과거 버전을 재구성하지 않도록 **단일 authoritative contract** 제공
- 리뷰 상태: v1.13까지 3-AI 리뷰 완료, v1.12 3/3 NARROW. 이 consolidated spec은 **아직 3-AI 리뷰를 받지 않았다.**
- F0 상태: **미승인·미실행**, D0/D1/P/Q/R 실행 없음
- test 163 sealed, P1 unused, T5Gemma2 D-108 STOP, Phase 6 negative 종료, B0-B 미승인

---

## 1. Scope

### 1.1 질문

LoRA initialization을 match한 상태에서 **adapter-as-configured**(adapter params + adapter LR + adapter-conditioned forward graph)의 유무가 EG2 layer19 raw route의 donor-specific copy signal을 바꾸는가?

### 1.2 설계

| cell | adapter | LoRA (64 modules) | updates |
|---|---|---|---:|
| E00 | none | none | 0 |
| E10 | trained | none | 100 |
| E01 | none | trained | 100 |
| E11 | trained | trained | 100 |

- **Primary contrast**: paired `D(d) = delta_E01(d) − delta_E11(d)` on copy.
- E00/E10/E01 vs E00 are descriptive; no causal inference.
- Association-only; architecture-only bottleneck claim 금지.

### 1.3 Cohort

- 15 length-eligible docs = frozen preflight `common_ids` (`K=753`-compatible).
- Fixed donor graph; 5 donors per doc; donor sets identical across E00/E10/E01/E11.
- 3 seeds: 20261108/09/10.
- 20-doc F/L values are descriptive; no population generalization.
- Donor-cluster / leave-one-donor-out sensitivity is descriptive.

### 1.4 Non-goals

- EG2 전체 track STOP/keep 결정
- B0-B, B1/B2, Stage C
- test 163, P1
- T5Gemma2
- native P/PA rerun
- adapter capacity/LR tuning
- H3 (별도 prereg)
- threshold/seed/donor/step/LR 변경

---

## 2. Stage contract

| stage | cells | updates | cap | gate |
|---|---:|---:|---:|---|
| P | 4×3 | 0 | 10 min | init-only pass |
| Q | 4×3 | 12 units / 9 trained updates | 15 min | per-seed pass |
| D0 | 4 | 0 | 15 min | mechanics |
| D1 | 4 | 3 | 25 min | mechanics/seal |
| R | 4×3 | 900 | 96 min | full R mechanics |

### 2.1 공통 overrun 규칙

모든 stage에서 cap 초과 시:

1. hard abort
2. `partial:true` 기록
3. new code SHA 없이는 재실행 금지
4. explicit stage re-approval 필요

별도의 “repair first”, “provisional extension”, “silent extension” 없음.

### 2.2 Stage P

- init-only, no optimizer step.
- seeds 20261108/09/10, 4 cells = 12 loads.
- assertions 1–4, 6–8 only; assert 5/9 N/A.
- `d0/init_hashes.json` append-only per `{stage,seed,cell}`.
- `pre_r_init_audit_pass` required before Q.

### 2.3 Stage Q

- 1 update per cell per R seed: 12 units, **9 trained updates**, E00 0.
- post-step0 RNG parity, expected group change, wrong-donor CE finiteness/shape only.
- `wrong_donor_ce_calls` recorded; no per-doc/delta/signal persistence.
- `q/q_seed_audit/{seed}.json`.
- Any seed failure → `NOT_EVALUABLE`; no 2-seed continuation.

### 2.4 Stage D0

- 4 cells, 0 updates, seed 20261111.
- mechanics only; no signal.
- `d0/f0_d0.json`.

### 2.5 Stage D1

- 4 cells, 3 updates (E10/E01/E11; E00 0).
- mechanics only; no signal/delta/per_doc/final.
- separate `eval_mechanics_only`; `eval_arm_d1` 금지.
- D1 outputs only `d1/f0_d1_mechanics.json`.
- D1 checkpoint: digest then delete; `checkpoint_absent:true`; loading forbidden.
- D1 allowed filesystem delta: that JSON only.
- success/crash/forced-kill inventory and log/temp tests required.
- `mechanics_pass` fail-closed and includes all seal flags, CE count, provenance.

### 2.6 Stage R

- 3 seed waves, 4 arms, 100 updates/arm, 900 updates.
- M 1,440; phase7 7,200; generation 240.
- 2 threads/arm, 8 logical threads, 16-core host.
- R cap 96 min; mid-run >96 min → hard abort + partial + re-approval.
- R report includes CPU affinity/quota/thread pools, donor map sha256, per-doc donor hash, expected counts, provenance.

---

## 3. Metrics and decision

### 3.1 Signal

```text
delta_c(s,d) = mean_donor( CE_wrong_donor − CE_real )
SIGNAL(c,copy) = mean(delta_c) >= .05 AND CI.lower > 0 AND 2/3 seeds > 0
SIGNAL(c,full) = mean(delta_c) > 0 AND CI.lower > 0 AND 2/3 seeds > 0
```

- Final checkpoint donor-crop; 15 docs × 5 donors.
- Cell CI: seed mean over 3 seeds; `bootstrap_paired_v2(n_boot=10000, seed=20261109, percentile linear)`.
- CI is conditional on the fixed donor graph; no population inference.

### 3.2 Primary decision

```text
D(d) = delta_E01(d) − delta_E11(d)
mean_D = mean(D)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)
PASS_POSITIVE = mean_D > 0 AND CI_D.lower > +.05
                AND SIGNAL(E01,copy) AND 2/3 seeds D_s > 0
```

### 3.3 Labels

| priority | label | condition |
|---:|---|---|
| 1 | NOT_EVALUABLE | protocol invalid |
| 2 | EQUIVALENT | 95% CI_D entirely within [−.05,+.05] |
| 3 | ROUTE_STOP | ALL_FAIL (E01/E11 × copy/full) |
| 4 | PASS_POSITIVE | primary condition |
| 5 | INDETERMINATE | otherwise |

- Reason precedence: `no_signal_equivalent` > `adapter_harm` > `adapter_benefit` > `no_signal_uncertain`.
- ALL_FAIL + benefit still ROUTE_STOP.
- ROUTE_STOP is route-only; does not stop EG2 track, rescue B0-B, or launch H3.

### 3.4 MDE / nominal values

- `.019170` = SE; `.037573` = 95% half-width; 50% MDE `.0376`; 80% MDE `.0537`.
- 이는 Phase 6 F−L LoRA contrast의 **planning proxy**이며 F0 E01−E11의 validated SE가 아니다.
- P−PA reference dispersion: mean +3.0652, SE .6209, 14/15 positive, SD 2.405.
- `.0255` = nominal planning only; EQUIVALENT gate 아님. Realized `CI_D` governs.
- `n_boot=10000`은 Phase 6 frozen 1000과의 등록된 deviation.

---

## 4. Initialization / RNG

- `LORA_SEED_XOR = 0x5EED10A5`
- `STEP_SEED_MUL = 0x9E3779B9`
- `step_seed = (seed ^ ((STEP_SEED_MUL * (step+1)) & 0xffffffff)) & 0xffffffff`
- E01/E11 LoRA reset identical; E10/E11 adapter seed identical.
- per-step reseed before forward.
- assertions:
  1. `lora_names` E01==E11, 64.
  2. LoRA A/B sha equal at init.
  3. adapter sha E10==E11 at init.
  4. post-init RNG sha equal.
  5. post-step0 RNG sha equal.
  6. LoRA B zero-init separately asserted.
  7. E00/E01 adapter absent; E00/E10 LoRA 0.
  8. base/cache/label hashes equal.
  9. expected group weight change at first update.
- canonical tensor serialization + KAT fixture (`serialization_kat.json`).
- `d0/init_hashes.json`; R `r/init_hashes.json`.
- Phase 6 checkpoint I/O count 0; protected-path negative read test.

---

## 5. Artifacts

```text
reports/provenance/C5_f0/
  d0/f0_d0.json
  d0/init_hashes.json
  pre_r/pre_r_init_audit.json
  q/q_seed_audit/{seed}.json
  d1/f0_d1_mechanics.json
  r/units/{cell}_{seed}.json
  r/m_records_{cell}_{seed}.json
  r/phase7_records/{cell}/{seed}.json
  r/checkpoints/{cell}/{seed}.pt
  r/init_hashes.json
  r/f0_report.json
  r/f0_r_labels.json
  r/r_mechanics_pass.json
  data_scope.json
  serialization_kat.json
```

- `test_split_used:false`, `p1_used:false`.
- D1 writes only `d1/f0_d1_mechanics.json`.
- `r/f0_replay.json` 없음.
- R reader list: `d0/f0_d0.json`, `d1/f0_d1_mechanics.json`, `r/r_mechanics_pass.json`, `r/f0_r_labels.json`, `r/init_hashes.json`; never `d1_sealed/*`.

---

## 6. Provenance and compute

- F0 runner/orchestrator commit SHA + clean tree before D0.
- Each artifact: `code_commit`, command, input sha256, clean_tree.
- D1 1,180.6s = 3 threads/arm measured (D-156); registered 4,939.884s = 2 threads/arm measured (D-157); neither is F0.
- D1 cap 25 min at 2 threads/arm; R cap 96 min.
- `setup_s_effective = setup_wall_s`; `sum_process_setup_s` separate; no double count.
- `nproc>=16` alone is not capacity proof; record effective affinity/quota/thread pools.
- 4-vCPU workspace excluded.

---

## 7. Open blockers before any stage approval

1. **F0 implementation absent** — `runner/c5_pm_f0*.py` not committed; D0 cannot be approved.
2. **v1.13 not reviewed** — consolidated spec is DRAFT; 3-AI review required before freeze.
3. **Plus allowance** — current Hoplite allowance nearly exhausted; no 3-AI review until reset/top-up.
4. **R donor identity** — donor map/per-doc hash must be implemented and tested.
5. **D1 custody** — forced-kill and log/temp tests must be implemented, not only specified.
6. **Q/R expected count tables** — literal frozen tables must be committed before use.

---

## 8. Traceability

| consolidated section | source |
|---|---|
| §1 scope/arms | v1.13 §2, §6, §14 |
| §2 stages | v1.13 §5, §13A.1–13A.11 |
| §3 metrics | v1.13 §6–§7, §12 |
| §4 init/RNG | v1.13 §4, §13A.2 |
| §5 artifacts | v1.13 §13, §13A.4, §13A.10 |
| §6 compute | v1.13 §12, §13A.7 |
| open blockers | v1.12/v1.13 reviews |

이 문서는 **v1.13의 구현용 요약·단일 계약 후보**이며, 3-AI 리뷰와 사용자 승인 전에는 효력이 없다. F0는 계속 미승인·미실행이다.
