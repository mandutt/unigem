# C5 F0 — Reuse Pack / Closure Record (2026-11-10)

## 목적

F0 라인을 **삭제하거나 폐기하지 않고**, 향후 F5/H3/후속 분석에서 재사용할 수 있도록
증거·코드·checkpoint·prereg를 한 곳에 고정한다.

## 1. 무엇을 재사용할 수 있는가

### 1.1 Raw evidence

| 자료 | 위치 | 재사용 |
|---|---|---|
| F0 R units 12개 | `reports/provenance/C5_f0/r/units/` | E00/E10/E01/E11 × 3 seeds, final per_doc |
| F0 R checkpoints 12개 | `reports/provenance/C5_f0/r/checkpoints/` | E00/E10/E01/E11 × 3 seeds |
| F0 R M/phase7 | `reports/provenance/C5_f0/r/m_records_*.json`, `phase7_records/` | M/phase7 재분석 |
| F0.2 units 6개 | `reports/provenance/C5_f0_2/units/` | E01/E11 matched 400 updates, per_doc |
| F0.3 units 6개 | `reports/provenance/C5_f0_3/units/` | E00/E10 reference, per_doc |
| F0.4 units 6개 | `reports/provenance/C5_f0_4/units/` | fresh-seed E01/E11, per_doc |
| F0.1a units 9개 | `reports/provenance/C5_f0_1/units/` | E01 loss curves, fit ratios |

### 1.2 Analysis assets

- F0 post-mortem: `reports/C5_F0_POSTMORTEM_2026-11-10.md`
- F0 synthesis: `reports/C5_F0_SYNTHESIS_2026-11-10.md`
- per-stage result reports: `reports/C5_F0_*_RESULT_2026-11-10.md`
- prereg/freeze:
  - `docs/plan_c5_f0_CONSOLIDATED_v1_0_2026-11-10.md`
  - `docs/plan_c5_f0_1a_opt_v0_2_2026-11-10.md`
  - `docs/plan_c5_f0_2_signal_v0_1_2026-11-10.md`
  - `docs/plan_c5_f0_3_reference_v0_1_2026-11-10.md`
  - `docs/plan_c5_f0_4_confirm_v0_1_2026-11-10.md`
- runners:
  - `runner/c5_pm_f0.py`
  - `runner/c5_pm_f0_mechanics.py`
  - `runner/c5_pm_f0_registered.py`
  - `runner/c5_pm_f0_audit.py`
  - `runner/c5_pm_f0_1_opt.py`
  - `runner/c5_pm_f0_2_signal.py`
  - `runner/c5_pm_f0_3_reference.py`
  - `runner/c5_pm_f0_4_confirm.py`
  - `runner/c5_pm_f0_postmortem.py`

## 2. 재사용 가능한 결론

- **F0 ROUTE_STOP은 계약 label이며 adapter-null 증거가 아니다.**
- **E01(LoRA-only) underfit**: 100 updates/LR 1e-4에서 final loss ≈19.7, ratio ≈0.736.
- **E01 optimization rescue**: 400 updates/LR 3e-4에서 ratio ≈0.252, 3/3 seeds fit.
- **F0.2 matched**: E11 copy +0.1152 (CI 0.0598–0.1718), E01 non-signal; label INDETERMINATE.
- **F0.3 reference**: E10 adapter-only copy +0.1382 (CI 0.0716–0.2084); E11−E10 −0.0230 (CI −0.0839–0.0309).
- **F0.4 fresh seeds**: E11−E01 +0.09166 (CI −0.01668–0.21448), 3/3 seed direction positive, but signal/benefit not confirmed → NO_BENEFIT.

## 3. 재사용 금지 / 주의

- F0.2/F0.3/F0.4를 **독립 population replication**으로 취급하지 않는다. 모두 같은 15 docs/fixed donor graph를 사용했다.
- F0.2/F0.3/F0.4의 label을 사후 변경하지 않는다.
- F0 R `ROUTE_STOP`을 “adapter useless”로 인용하지 않는다.
- F0.4 `NO_BENEFIT`을 “no effect”로 인용하지 않는다. **directional but unconfirmed**다.
- E00는 0-update noisy baseline이며 causal control이 아니다.
- F0.2/F0.3/F0.4는 final checkpoint를 저장하지 않았다. **model weight 재사용이 필요하면 rerun이 필요하다.**
  - F0 R checkpoint만 존재한다.
  - F0.2/F0.4 E01/E11 400-update weights는 저장되지 않았다.

## 4. 향후 사용 방법

### A. F5 abstract summary

F0 결과는 F5 제품 트랙을 막지 않는다. F5는 별도 prereg로 진행한다.

### B. H3

H3는 F0 결과로 자동 시작하지 않는다. 별도 prereg/승인 필요.

### C. 추가 confirmatory 실험

새 docs/cohort가 확보되면 F0.4 code/prereg를 재사용해:
- E01/E11 400 updates, LoRA 3e-4, adapter 1e-3
- fit gate ≤0.35
- E11−E01 directional endpoint
- n_boot 10000
로 새 데이터에서 검정할 수 있다.

### D. Weight reuse

F0.2/F0.4 E01/E11 trained weights가 필요하면 runner에 checkpoint save를 추가하고 rerun해야 한다. F0 R checkpoint는 100-update 상태이므로 E01은 사용하지 않는다.

## 5. Closure statement

F0 line status:

```text
line_status = CLOSED_DIRECTIONAL_UNCONFIRMED
contract_labels_preserved = true
raw_evidence_preserved = true
checkpoints_preserved = F0_R_only
population_claim = none
H3/B0-B = not opened
```

이 문서는 F0를 “버린다”는 뜻이 아니라, **재현·재분석·후속 설계에 사용할 수 있는 종료 기록**이다.
