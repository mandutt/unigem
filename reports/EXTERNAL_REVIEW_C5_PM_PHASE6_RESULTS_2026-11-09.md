# C5 Phase 6 P/M — Results & Cause Analysis Review Request

- 작성일: 2026-11-09
- 작성 기준 데이터 HEAD: `8118204`
- 대상: C5 Phase 6 P/M, frozen v1.0.11, registered 3-seed 완료 후
- 상태: **B0-B 미승인**, cause analysis 완료
- test 163: **sealed**
- P1: **unused**
- T5Gemma2: **D-108 STOP**
- **새 독립 검토 라운드**. 이전 C5 prereg 스레드의 후속이 아니며, 중복 요청이 아님.

---

## 0. Reviewer Instructions

1. 새 스레드에서 독립 검토하라. 이전 스레드의 결론을 상속하지 말라.
2. 아래 파일을 직접 읽어 수치를 재확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_11_FREEZE.json`
   - `reports/C5_B0A_PM_PHASE6_REGISTERED_2026-11-09.md`
   - `reports/C5_B0A_PM_PHASE6_LABELS_2026-11-09.md`
   - `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`
   - `reports/provenance/C5_b0a/registered/registered_report.json`
   - `reports/provenance/C5_b0a/labels/labels.json`
   - `reports/provenance/C5_b0a/labels/cause_analysis.json`
   - `runner/c5_pm_phase6.py`
   - `runner/c5_pm_labels.py`
3. 학습·평가 실행 금지. test 163/P1 사용 금지. 서브에이전트/추가 LLM 금지.
4. repository 수정 금지. 지정 report 파일만 작성.
5. 각 Q1~Q6에 **판정 + 근거 + 다음 단계 1~3개**.
6. 최종 판정은 **STOP / NARROW / CONTINUE**.
7. 보고서 경로:
   `docs/hoplite/c5_pm_results_review_2026-11-09/review_{MODEL}.md`
8. `reviewed HEAD`와 verbatim quote `adapter bottleneck`을 보고서에 포함하라.

---

## 1. 배경

C5는 EG2(EmbeddingGemma 2)를 상주 인코더로 재사용해 F5 요약 품질을 얻을 수 있는지 보는 실험이다.

- F5: 1,617 clean Korean summary pairs.
- clean split: train 1,293 / val 161 / test 163 (seed 42). test 163은 sealed.
- Phase 6 P/M: EG2 layer19 adapter(F/L) vs native mT5(P/PA) 4-arm, 3 seeds, 100 updates.
- M: eval-only memory control. M_POS_MEAN/M_NORM.
- Phase 7: donor-level diagnostic.
- B0-B: downstream gate, 별도 prereg/승인.

## 2. 동결 계약

| 항목 | 값 |
|---|---|
| plan | `docs/plan_c5_b0a_pm_prereg_v1_0_11.md` |
| freeze commit | `6fad89e59e4aa2222010f2360e5eb4c2572c4023` |
| manifest commit | `05b7abe9a011ff1f7e0095dc7d2be37c61e0266e` |
| plan SHA-256 (blob) | `327a3e34f5bb2721b8b2400718dfd7bc56a0946641d1e83e2c8b454bf656d007` |
| freeze manifest SHA-256 | `f5d9ac8a1ce8528991b7ae6f7f9eda8f3ef2b6d29df29d05489f2cbfa9f34764` |
| registered seeds | 20261108 / 20261109 / 20261110 |
| debug seed | 20261111 |
| arms | F / L / P / PA |
| units | 12 (4×3) |
| updates | 100/arm, total 1,200 |
| wall cap | 120 min |
| M records | 1,680 |
| phase7 records | 7,200 |
| test 163 | sealed |

Arm:

| arm | memory | adapter | LoRA | M K |
|---|---|---|---|---|
| F | EG2 layer19 | trained | none | 753 |
| L | EG2 layer19 | trained | decoder | 753 |
| P | native mT5 | none | decoder | 512 |
| PA | native mT5 | trained | decoder | 512 |

## 3. 실행 이력

### D0

- 4 configs, 0 updates, debug seed 20261111.
- `labels_computed:false`, `not_a_result:true`.
- 4 arms memory probe: F/L 753×512, P/PA 512×512.
- LoRA 0/64/64/64; adapter params 0/526,336/0/526,336.

### D1

- 4 arms ×1 update, debug seed 20261111.
- M 560; phase7 2,400; generation 80.
- wall 1,180.6s / 1,200s.
- 1차 시도 P/PA `inference_mode` tensor training 실패 → `no_grad` 수정 → 2차 완료.

### registered 3-seed

- 12 units ×100 updates = 1,200.
- 3 waves, 4 arms parallel, 2 threads/arm.
- wall estimate **4,939.9s / 7,200s (82.3/120 min)**.
- M **1,680**; phase7 **7,200**; generation 240; checkpoints 12.
- replay **12/12** `replay_ok:true`, `atol=1e-5`, `rtol=1e-4`.

## 4. 결과

### 4.1 M primary

`delta = control CE - real CE`; seed-average before bootstrap; 1,000 resamples; PCG64 seed 20261109.

| arm | variant | endpoint | mean Δ | 95% CI | docs | pass |
|---|---|---|---:|---|---:|---|
| F | M_POS_MEAN | copy | 0.548 | [0.487, 0.623] | 15 | true |
| F | M_POS_MEAN | full | 0.576 | [0.522, 0.644] | 15 | true |
| F | M_NORM | copy | 0.548 | [0.487, 0.622] | 15 | true |
| F | M_NORM | full | 0.576 | [0.522, 0.644] | 15 | true |
| L | M_POS_MEAN | copy | 0.367 | [0.313, 0.427] | 15 | true |
| L | M_POS_MEAN | full | 0.365 | [0.312, 0.423] | 15 | true |
| L | M_NORM | copy | 0.379 | [0.324, 0.439] | 15 | true |
| L | M_NORM | full | 0.378 | [0.324, 0.436] | 15 | true |
| P | M_POS_MEAN | copy | 6.327 | [4.249, 8.533] | 20 | true |
| P | M_POS_MEAN | full | 6.118 | [3.913, 8.644] | 20 | true |
| P | M_NORM | copy | 6.168 | [4.787, 7.820] | 20 | true |
| P | M_NORM | full | 5.774 | [4.387, 7.509] | 20 | true |
| PA | M_POS_MEAN | copy | 0.586 | [0.563, 0.615] | 20 | true |
| PA | M_POS_MEAN | full | 0.576 | [0.554, 0.601] | 20 | true |
| PA | M_NORM | copy | 0.660 | [0.637, 0.689] | 20 | true |
| PA | M_NORM | full | 0.672 | [0.644, 0.700] | 20 | true |

- `M_PASS_POS` all true; `M_PASS_NORM` all true; `m_pass_l:true`; `m_valid:true`.

### 4.2 L signal

| predicate | mean Δ | 95% CI | paired L>F | seeds >0 | value |
|---|---:|---|---:|---:|---|
| `L_COPY_SIGNAL` | **-0.1135** | [-0.2341, -0.0012] | -0.0026 | 0/3 | **false** |
| `L_FULL_SIGNAL` | **-0.1085** | [-0.2234, -0.0057] | -0.0009 | 0/3 | **false** |

- `l_signal:false`; `copy_only:false`; `full_only:false`; `n_signal:15`.
- positive docs 6/15.

### 4.3 Tail

| 항목 | 값 |
|---|---:|
| top3_abs_share | 0.4775 |
| top3_signed_share | 0.8035 |
| leave_top3_mean | **-0.0279** |
| tail_driven | **true** |

- top3_abs_share < .50이지만 leave_top3_mean <=0으로 true.

### 4.4 Validity / control / dispatch

| 항목 | 값 |
|---|---|
| `validity_status` | **VALID** |
| `control_status` | **M_CONTROL_PASS** |
| `signal_status` | **MEAN_CONTRAST_ONLY** |
| `m_evaluable` | true |
| `m_valid` | true |
| `n_signal` | 15 |
| `b0_b_candidate_gate` | **false** |

B0-B 요구:

```text
VALID
AND M_CONTROL_PASS
AND EXPLORATORY_L_SIGNAL
AND m_valid
AND n_signal >= 15
AND tail_driven == false
AND leakage/mode/metric pass
AND artifact complete
AND separate prereg/approval
```

실패: **signal (MEAN_CONTRAST_ONLY)**, **tail_driven true**.

## 5. Cause analysis

### 5.1 M vs donor specificity

| arm | M control−real Δ | wrong−real Δ | ratio |
|---|---:|---:|---:|
| F | 0.576 | 0.001 | 0.001 |
| L | 0.365 | -0.017 | -0.046 |
| P | **6.118** | **2.531** | **0.414** |
| PA | 0.576 | 0.013 | 0.022 |

- F/L/PA: wrong donor가 real과 거의 같고, 둘 다 global mean보다 좋음.
- P만 donor specificity가 있음.
- **M_PASS와 L_SIGNAL false는 모순이 아님**: M은 real vs global mean, L은 real vs wrong donor.

### 5.2 LoRA vs adapter

- F vs L: 15-doc paired -0.0026, 8/15 positive; 60 seed-doc -0.0224, 30/60.
- P vs PA: copy Δ 3.076 vs 0.011; paired **+3.065**, **14/15 positive**.
- P/PA는 adapter 유무만 다름.
- **LoRA 기각, adapter 결정적.**

### 5.3 Representation variance

| representation | between-doc variance | pair distance |
|---|---:|---:|
| raw EG2 layer19 | 4.883 | 3.142 |
| F adapter | 0.085 | 0.418 |
| L adapter | 0.081 | 0.405 |
| native raw | 0.841 | 1.324 |
| PA adapter | 1.284 | 1.623 |

- F/L adapter: EG2 variance 98%+ 감소.
- PA adapter: variance 증가, 그러나 donor-specific decoder signal 소멸.
- 단순 global collapse 아님; adapter가 content-specific 성분을 decoder-usable하게 보존하지 못함.

### 5.4 배제

| 가설 | 판정 |
|---|---|
| decoder LoRA | 기각 |
| EG2 layer19 단독 | 부분 기각 (PA native도 0.01) |
| donor crop length | 기각 (P/PA K=512) |
| copy mask | 기각 (endpoint 1,680 all true) |
| seed noise | 기각 (0/3 positive, CI upper <0) |
| M endpoint 실패 | 기각 (M pass all) |
| tail-only outlier | 기각 (top3 제거 후 -0.0279) |

## 6. 검토 질문

### Q1. Label/gate 정확성

`L_COPY_SIGNAL`, `L_FULL_SIGNAL`, `l_signal`, `copy_only/full_only`, `tail_driven`, `signal_status=MEAN_CONTRAST_ONLY`, `b0_b_candidate_gate=false`가 frozen v1.0.11과 정확히 일치하는가? 산술·tri-state·tail 규칙 오류가 있는가?

### Q2. Cause analysis 타당성

“adapter bottleneck” 결론이 **P vs PA**와 F/L variance contraction으로 충분히 지지되는가? 
- P/PA는 adapter만 다르지만, P/PA vs F/L은 memory source도 다름.
- F/L adapter variance 감소가 원인인지 결과인지.
- 추가로 필요한 control은 무엇인가?

### Q3. F0 설계

다음 별도 prereg로 `F0 = EG2 layer19 raw 512 -> mT5 decoder LoRA only (no adapter)`를 제안한다.

- F0가 positive면 adapter 원인 확정, 0이면 EG2 feature 부족.
- P(native no-adapter)가 positive control.
- F0/F/P/PA 4-arm, 3 seeds, 100 updates, M 1,680, phase7 7,200, same donor/tail.
- 이 설계가 confound를 실제로 분리하는가? 빠진 arm/control이 있는가?

### Q4. M endpoint 해석

M_PASS all arms true vs L signal false를 어떻게 해석해야 하는가?
- M을 “content-use evidence”로 쓰는 것이 부적절한가?
- M을 descriptive로만 두고 B0-B에서 제외해야 하는가?
- threshold 변경 없이 M 정의를 재해석하는 것은 허용 가능한가?

### Q5. Phase 6 종료 vs 새 prereg

B0-B candidate false를 **negative Phase 6**로 종료할지, F0/H3 새 prereg로 갈지 판단하라. 
- F0가 실패하면 EG2 resident encoder 트랙을 접어야 하는가?
- F0가 성공하면 adapter 구조 변경이 필요한가?

### Q6. Artifact/provenance

replay 12/12, freeze hash, labels, registry가 B0-B/새 prereg 전에 충분한가? 
- `labels_computed:false` → `true` 전환의 audit gap.
- phase7 diagnostic과 primary M 분리.
- test 163/P1 미사용 입증.

## 7. 답변 형식

```text
Qn.
- 판정: agree / disagree / conditional / defer
- 근거
- 다음 단계: 1~3개
```

마지막:

```text
최종 판정: STOP / NARROW / CONTINUE
B0-B candidate false:
adapter bottleneck:
F0 설계:
Phase 6 종료/새 prereg:
금지 범위:
Must-fix (ranked):
잘못된 전제:
```

## 8. 금지

- 학습·평가 실행 금지
- test 163 열람 금지
- P1 사용 금지
- repository 수정 금지 (지정 report 파일만)
- subagent/추가 LLM 금지
- 결과 후 threshold/seed/donor/step/LR 변경 금지
- B0-B/B1/B2/Stage C 자동 진행 금지
- 기존 C5 스레드와 혼합 금지 (새 독립 스레드)
