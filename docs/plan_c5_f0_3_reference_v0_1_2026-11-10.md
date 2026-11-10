# C5 F0.3 — E00/E10 Reference Decomposition (Prereg v0.1, DRAFT)

- 작성일: 2026-11-10
- 상태: **DRAFT — 승인 전 코드·실행 금지**
- 목적: E00(no adapter/no LoRA)와 E10(adapter-only)을 추가해 E11(adapter+LoRA) signal의 구성을 descriptive하게 분해
- 중요: **새 confirmatory PASS/ROUTE_STOP 실험이 아니다.** F0/F0.2 label을 변경하지 않는다.

## 1. 실행 조건

| cell | adapter | LoRA | updates | adapter LR |
|---|---|---|---:|---:|
| E00 | none | none | 0 | — |
| E10 | 512→512 | none | 400 | 1e-3 |

- seeds: 20261108 / 09 / 10
- **E10 fit gate**: 3/3 seeds `loss_last/loss_first <= 0.35`; 실패 시 `NOT_EVALUABLE_OPTIMIZATION`
- E00는 0-update baseline; fit gate N/A
- E11은 **F0.2의 기존 unit/labels를 external reference로만 사용** (재실행 없음)
- E01은 사용하지 않음

## 2. Endpoints

- final checkpoint donor-crop, 15 common docs × 5 donors
- `delta_c(s,d) = mean_donor(CE_wrong − CE_real)`
- E00/E10 copy/full cell signal
- paired `D_E10_E00(d) = delta_E10(d) − delta_E00(d)` copy/full
- `D_E11_E10`는 F0.2 E11 labels와 E10을 결합한 **descriptive comparison only**
- bootstrap: `n_boot=10000`, seed 20261109
- no `PASS_POSITIVE`, no `ROUTE_STOP`; status = `REFERENCE_DECOMPOSITION`
- E10/E00 signal은 descriptive; population inference 없음

## 3. 비목표

- F0/F0.2 재판정
- E11 재실행
- E01
- M/phase7/generation
- H3/B0-B
- threshold/seed/donor/step 변경

## 4. Compute

- E00 3 units (0 updates), E10 3 units (400 updates)
- fit gate 후 signal
- cap **60분**
- unit 완료 즉시 flush

## 5. Artifacts

```text
reports/provenance/C5_f0_3/
  freeze.json
  summary.json
  units/{E00,E10}_{seed}.json
  labels.json
```

## 6. Approval

승인 후:

1. `runner/c5_pm_f0_3_reference.py` + unit tests
2. prereg freeze
3. 6 units 실행
4. E10 fit gate → E00/E10 signal decomposition
