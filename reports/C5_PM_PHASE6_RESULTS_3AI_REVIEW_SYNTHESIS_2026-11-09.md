# C5 Phase 6 P/M Results — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_pm_results_review_2026-11-09/`
- 검토 기준 HEAD: `d809e0002d0653e3c4207c58a38bb8af0b641467`
- 데이터 기준 HEAD: `8118204`
- 새 독립 스레드 3개, 기존 스레드 미사용
- test 163: sealed
- P1: unused
- 추가 학습/평가: 없음

## 0. 한 줄 결론

> **3/3 NARROW.** 세 검토자 모두 **B0-B candidate false와 Phase 6 negative 종료**에는 동의했다. 그러나 “adapter bottleneck”을 EG2 전체로 일반화하는 것은 과대 주장이며, **registered/label/replay/gate 실행 코드가 커밋되지 않은 provenance gap**과 **F0 설계 confound**가 핵심 must-fix다.

## 1. 판정

| 검토자 | 모델 | 최종 판정 | B0-B false | Phase 6 종료 |
|---|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **NARROW** | 동의 | negative 종료 |
| DeepSeek | `deepseek-v4.1-flash-1017` high | **NARROW** | 동의 | negative 종료 |
| Sol | `gpt-6.1-sol` medium | **NARROW** | 동의 | negative 종료 |
| **종합** | — | **NARROW 3/3** | **동의 3/3** | **negative 3/3** |

## 2. 합의된 것

- `L_COPY_SIGNAL=false`, `L_FULL_SIGNAL=false`, `l_signal=false` — 재계산 일치.
- `tail_driven=true`, `leave_top3_mean=-0.0279` — 재계산 일치.
- `signal_status=MEAN_CONTRAST_ONLY`.
- `B0-B candidate gate=false`.
- **M_PASS는 donor-specific content-use 증거가 아니다.**
- Phase 6는 **negative**로 종료해야 한다. B0-B/B1/B2/Stage C 자동 진행 금지.
- threshold/seed/donor/step/LR 사후 변경 금지.
- P vs PA에서 adapter 부착 시 native signal이 사라지는 것은 지지됨.

## 3. Must-fix (consensus, ranked)

### MF-1. 실행 코드 provenance gap (blocker for 재현)

- GLM/DS 공통 지적.
- `runner/c5_pm_phase6.py`의 `main()`은 `--mode registered`를 거부한다.
- registered run driver, label/replay/gate driver, cause-analysis script가 **커밋되지 않았다**.
- 수치는 커밋된 artifact로 재현되지만, **커밋된 코드로 registered 결과를 재생성할 수 없다**.
- `runner/c5_pm_labels.py`는 pure module이며 `b0_b_candidate_gate` 계산 함수/CLI가 없다.

**Fix**:
1. `run_registered` / label/replay/gate driver를 repo에 커밋.
2. 최소 1 unit end-to-end 재생성 테스트.
3. `labels_computed` 전환에 code commit/command/input SHA 기록.

### MF-2. labels/registry 상태 불일치

- `registered_report.json`은 `labels_computed:false`인데 labels.json/registry는 true.
- `FREEZE.json manifest_commit:null` vs external `05b7abe` 표기 일관성.
- `labels_computed` audit chain이 없다.

**Fix**: 상태 필드 정합 + code commit/command/input SHA를 labels artifact에 기록.

### MF-3. “adapter bottleneck” 과대 일반화

- GLM: Q2 conditional agree.
- DS: P→PA native에서는 지지되지만 **EG2/F-L 일반화, 구조적 “bottleneck” 명칭, variance 인과는 미확립**.
- Sol: well-supported working diagnosis, not uniquely established.
- DS: Adapter는 512→512로 width bottleneck이 없음; LayerNorm/input-insensitive mapping 가능성.
- centered cosine/CV/eff_rank가 거의 동일해 98% variance 감소는 norm/공통평균 효과일 수 있음.
- raw EG2 mean cosine 0.998.

**Fix**: 결론을 **“native 경로에서 adapter 부착 시 donor-specific signal 소실”**로 한정. EG2 전체/구조적 bottleneck/variance 인과 철회 또는 별도 증거.

### MF-4. F0 설계 confound

- 제안 `F0 = EG2 raw + decoder LoRA, no adapter` vs F는 **adapter와 LoRA가 동시에 다름**.
- P/PA는 adapter 외 capacity(+526,336 params)와 adapter LR(10×)도 다름.
- 필요한 것:
  - **F0 vs L** (LoRA 고정, adapter만 차이)
  - fixed projection / residual adapter
  - zero/permuted null
  - donor-discrimination probe
  - 1-seed D-level diagnostic → pass 후 3-seed
- F0 negative는 “EG2 content 부족”과 “decoder-space alignment 부재”를 구분하지 못함.

### MF-5. M endpoint 해석

- M은 global-mean 대비 calibration이며 donor specificity를 요구하지 않는다.
- M을 사후 재정의해 B0-B를 구제하는 것은 금지.
- 새 prereg에서 donor-specificity endpoint를 별도로 두어야 한다.

### MF-6. Audit/access chain

- test 163/P1은 attestation이지 proof가 아니다.
- replay 12/12는 **평가 결정성**만 증명; 학습 재현성 manifest 없음.
- wall/threads는 telemetry이며 artifact로 검증되지 않음.
- Sol: executed data-access path와 assay/non-access claim 보강 필요.

## 4. 검토자별 특이 지적

### GLM

- `signal`은 unit-final donor crop(§2.3)에서 계산되며 phase7 K_M diagnostic과 다르다.
  - phase7에서 재계산하면 **-0.0407**, unit-final은 **-0.1135**.
  - 둘 다 설계상 맞지만 문서에 명시되지 않아 오독 위험.
- F0 0-update EG2-raw usability probe 추가.
- “F0 negative ⇒ EG2 feature 부족” overclaim 수정.
- Phase 6 negative 종료, F0 single prereg만.

### DeepSeek

- 실행 코드/데이터 재생성 불가가 최대 must-fix.
- `registered_report` stale fields.
- 15-doc cohort와 20-doc 평균 차이:
  - L 15-doc -0.1135 vs 20-doc -0.0222
  - F +0.0002
- “P/PA adapter만 다르다”는 capacity/LR confound로 부정확.
- F0는 F0/L 2×2 + projection/residual/null로 재설계.

### Sol

- 실험 데이터 접근 경로와 assay/non-access 주장 보강.
- causal exclusion을 한정하고 mixed-cohort/crop ratio를 mechanism claim에서 제거.
- F0 factorial/RNG/length/cohort 설계 수정.
- negative frozen label 유지.

## 5. 결정

```text
B0-B = 미승인 (3/3 동의)
Phase 6 = negative 종료
F0/H3 = 새 prereg + 별도 승인, 즉시 실행 금지
Must-fix = MF-1~MF-6
```

## 6. 다음 단계

1. **MF-1/MF-2 fix**: registered/label/replay/gate driver 커밋 + audit chain.
2. **MF-3 fix**: cause report 결론 축소.
3. **F0 재설계**: F0/L 2×2, projection/residual/null, 1-seed D-level.
4. 3-AI 재검토.
5. 새 prereg 승인 후에만 F0 실행.

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_pm_results_review_2026-11-09/review_GLM.md` | GLM NARROW |
| `.../review_DS1017.md` | DeepSeek NARROW |
| `.../review_SOL.md` | Sol NARROW |
| `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |

## 8. 제한

- 이 종합은 새 실험 승인이 아니다.
- 3/3 NARROW: Phase 6 negative, F0/H3 새 prereg만.
- test 163 sealed; P1 unused; T5Gemma2 D-108 STOP.
