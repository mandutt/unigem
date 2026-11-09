# C5 Phase 6 P/M — 결과·원인 분석 독립 검토 (DS1017)

- 검토일: 2026-11-09
- 검토자: DeepSeek V4.1 Flash 1017 (`deepseek-v4.1-flash-1017`)
- **reviewed HEAD: `d809e0002d0653e3c4207c58a38bb8af0b641467`**
- 결과 산출 기준(data) HEAD: `8118204` (현재 HEAD는 `d809e00`, review request 문서만 추가)
- 동기화: `git fetch origin` → `git pull --ff-only origin main` = **Already up to date**
- 범위: 문서·코드·아티팩트 읽기와 산술 재계산만 수행. 학습/평가 실행 없음, test 163/P1 미사용, subagent/추가 LLM 미사용, 지정 파일 외 수정 없음.
- 독립성: 이전 C5 prereg 스레드의 결론을 상속하지 않고 아래 파일만으로 재검토함.

재검토 대상: `reports/EXTERNAL_REVIEW_C5_PM_PHASE6_RESULTS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11_FREEZE.json`, `reports/C5_B0A_PM_PHASE6_{REGISTERED,LABELS,CAUSE}_2026-11-09.md`, `reports/provenance/C5_b0a/{registered/registered_report.json,labels/labels.json,labels/cause_analysis.json,labels/cause_centered.json,registered_m_records.json,units/*.json,phase6_artifact_registry.json}`, `runner/c5_pm_phase6.py`, `runner/c5_pm_labels.py`, `runner/c5_pm_stats.py`.

## 0. 사전 재현 확인 (판정의 전제)

모델을 돌리지 않고 커밋된 아티팩트만으로 다음을 재계산했다.

| 항목 | 재계산 결과 | 판정 |
|---|---|---|
| plan SHA-256 at freeze commit `6fad89e` | `327a3e34…d007` | freeze와 일치 |
| plan at HEAD vs freeze commit | diff 없음 | 동결 후 plan 무변경 |
| manifest SHA-256 at `05b7abe` | `f5d9ac8a…4764` | registry/요청서와 일치 |
| `FREEZE.json`의 `manifest_commit` | `null` | registry는 `05b7abe` (note대로 외부 txt가 권위) |
| registry 7개 핵심 아티팩트 해시 | 전부 일치 | OK |
| M 레코드 수 / phase7 수 | 1,680 / 7,200 | 일치 |
| `registered_m_records.json`에서 M 표 재계산 | 16개 셀 전부 4자리까지 일치 | OK |
| L label 15-doc 평균 | `-0.113506…` | labels/cause/units와 일치 |
| tail 3지표 | `0.477464 / 0.803495 / -0.027881` | 일치 |
| unit/phase7/M의 target ID | 전부 train20/val20 내부 | test/P1 ID 없음 |
| replay | 12/12 `replay_ok` | 일치 |

즉 **수치 자체는 재현된다.** 아래 지적은 수치 오류가 아니라 설계·해석·재현 경로에 관한 것이다.

---

## Q1. Label/gate 정확성

**판정: agree (조건부)**

### 근거

1. **L predicate**: 동결 §3.5의 네 conjunct(copy `>=.05`, CI lower `>0`, paired L>F `>0`, 2/3 seed `>0`; full은 `>0`)와 `runner/c5_pm_labels.py:l_predicate`가 일치한다. `labels.json`의 threshold도 copy `0.05`, full `0.0`으로 동결값 그대로다. 결과는 copy `-0.1135`, full `-0.1085`, CI upper가 둘 다 0 미만, paired `-0.0026/-0.0009`, seed 0/3 → 두 predicate 모두 `false`가 맞다.
2. **Tri-state**: `l_copy=false`, `l_full=false` → §3.4 표에 따라 `l_signal=false`, `copy_only=false`, `full_only=false`. 코드의 `l_signal_consensus` 및 `and_n([x, not3(y)])` 구현과 일치한다.
3. **tail**: 동결 §10.4 규칙(`leave_top3_mean`이 NA가 아니고 `<=0`이면 true)을 그대로 적용해 `-0.0279 <= 0 → true`. `top3_abs_share=0.4775 < .50`은 이 경우 무의미하며, 보고서의 설명대로 gate는 true다. top3 tie-break(`|delta|` desc, `doc_id` asc)도 재계산과 일치한다.
4. **dispatch**: `n_signal=15`, `validity=VALID`, `copy_only=false`, `full_only=false`, `l_signal=false`, `control=M_CONTROL_PASS` → §6.3의 마지막 분기 `MEAN_CONTRAST_ONLY`. 정확하다.
5. **control/validity**: `m_valid=ANDn(P_POS,P_NORM,PA_POS,PA_NORM)=true`, `m_evaluable=true`, `p_valid=pa_valid=true` → `M_CONTROL_PASS`; `validity=VALID`. §4~§5와 일치한다.
6. **B0-B gate**: §14의 9개 conjunct 중 `signal_status==EXPLORATORY_L_SIGNAL`과 `tail_driven==false`가 false이므로 `b0_b_candidate_gate=false`가 맞다.
7. **사후 변경 없음**: plan은 freeze 이후 무변경, threshold/seed/donor/step/LR 변경 흔적 없음.

### Caveats (수치 오류는 아님)

- `tail_driven=true`는 여기서 **독립 증거가 아니다.** delta 평균이 음수이면 `leave_top3_mean`도 음수가 되어 규칙상 자동으로 true가 된다. 따라서 "tail 때문에 실패"와 "신호가 없어서 실패"는 이 결과에서 같은 사건이며, 보고서가 이를 구분해 서술하지는 않는다.
- 15-doc cohort는 `h_len>=753`인 **길이 선택 코호트**다. 20-doc 전체 평균은 L `-0.0222`(seed mean `-0.0374/-0.0120/-0.0171`), F `+0.0002`로 0에 가깝다. 즉 음의 신호는 길이-eligible 15개에서 집중된다. Gate는 동결대로 맞지만, "broad negative"라는 서술은 15-doc 코호트 한정임을 명시해야 한다.
- `c5_pm_labels.py`에는 `b0_b_candidate_gate`를 계산하는 함수가 없고, "leakage/mode/metric pass"는 `labels.json`의 필드가 아니라 보고서의 서술이다. Gate 정의가 코드로 닫혀 있지 않다.
- 코드 품질(결과 무영향): `mean_ok = ... if copy else ...`는 연산자 우선순위에 의존하는 취약한 표현이고, `seeds_ok`는 seed mean에 `None`이 오면 `TypeError`가 난다. 이번 입력에서는 발생하지 않았다.

### 다음 단계

1. `labels.json`/`b0_b_candidate_gate`를 만드는 **커밋된 driver + 단위 테스트**를 추가해 gate를 코드로 닫아라.
2. `leakage/mode/metric pass`를 boolean 필드로 기록하라(현재는 주장).
3. 새 prereg에서는 "전면 음의 평균"과 "소수 outlier 주도"를 구분하는 tail 규칙을 재정의하거나, 현 규칙의 중복성을 문서에 명시하라.

---

## Q2. Cause analysis 타당성 — "adapter bottleneck"

**판정: conditional (부분 disagree)**

### 지지되는 부분

- **P vs PA는 memory-path 기준으로 깨끗한 대조다.** 둘 다 native mT5, K=512, decoder LoRA, 100 updates, 3 seeds이고 차이는 adapter뿐이다. P `3.076` vs PA `0.011`, paired `+3.065`, 14/15 positive는 "native memory 경로에 adapter를 넣으면 donor-specific signal이 사라진다"는 결론을 강하게 지지한다.
- `cause_analysis.json`의 `P_minus_PA.mean=3.0652`, `positive=14`로 보고서 수치가 정확하다.
- F/L/PA의 `wrong-real`이 각각 `0.001/-0.017/0.013`으로 real과 wrong donor가 구분되지 않는 반면, P만 `2.531`이다. 이는 donor specificity 상실을 보여주는 유효한 증거다.

### 지지되지 않는 부분

1. **P vs PA도 "adapter만" 다르지 않다.** PA는 adapter 526,336 params를 `lr=1e-3`으로 추가 학습하고, P는 LoRA만 `lr=1e-4`로 학습한다(`optimizer_for`). 즉 architecture 대조이면서 동시에 **capacity/LR 대조**다. "adapter 구조 때문"과 "추가 capacity/10× LR 때문"이 분리되지 않는다.
2. **F/L vs P/PA는 memory source뿐 아니라 K(753 vs 512), token 수, feature 분포가 모두 다르다.** 동결 plan 자신이 `geometry caveat: 512 vs 753; no direct retention comparison`(§ 부근 line 969)이라고 명시한다. 그런데 cause 보고서는 F/L의 variance 붕괴를 P/PA와 묶어 일반적인 adapter 기제로 승격한다. 동결 문서가 금지한 직접 비교를 원인 일반화에 사용한 셈이다.
3. **variance 붕괴 증거는 scale/mean artifact다.** `cause_centered.json`을 보면:

   | representation | between_var | centered_cos_mean | pair_dist_cv | eff_rank |
   |---|---:|---:|---:|---:|
   | raw EG2 | 4.883 | -0.0681 | 0.2445 | 11.26 |
   | F adapter | 0.085 | -0.0682 | 0.2100 | 11.18 |
   | L adapter | 0.081 | -0.0674 | 0.2289 | 10.85 |
   | native raw | 0.841 | -0.0688 | 0.1659 | 11.83 |
   | PA adapter | 1.284 | -0.0665 | 0.2111 | 10.17 |

   centered cosine과 pair-distance CV, effective rank가 **모두 거의 동일**하다. 4.883→0.085는 구조 붕괴가 아니라 **norm 축소 + 공통평균 성분**의 변화다. "between-doc variance 98% 감소"를 "content-specific 성분 보존 실패"로 읽는 것은 과대해석이다.
4. **raw EG2 자체가 이미 거의 동일하다.** uncentered mean cosine이 raw EG2 `0.9981`, native `0.9424`다. 즉 EG2 mean-pooled memory는 adapter 이전에 이미 공유 성분이 지배적이다. F/L에서 관찰된 붕괴의 상당 부분은 **adapter의 결과가 아니라 입력의 사전 성질**일 수 있다. "원인인지 결과인지"를 이 분석은 분리하지 못한다.
5. **mean-token variance는 decoder-usable content의 잘못된 대리지표다.** decoder는 753개 token vector에 attention한다. 평균벡터의 between-doc variance는 token-level 정보 보존 여부를 말해주지 않는다.
6. **"bottleneck"이라는 명칭이 구조와 맞지 않는다.** Adapter는 `Linear(512,512)→GELU→Linear(512,512)→LayerNorm`으로 **차원 축소가 없다**. 정보 병목은 구조적 width가 아니라 LayerNorm + 20-doc/100-update/`1e-3` 학습이 만드는 input-insensitive generic mapping일 가능성이 높다. 보고서의 mechanism 서술(§4)도 사실상 이를 말하지만, 결론 라벨은 구조적 bottleneck으로 읽힌다.
7. **추가 control이 없다**: (i) zero/permuted memory로 output이 input에 의존하는지, (ii) 고정 random-orthogonal projection, (iii) residual adapter `x+αA(x)`, (iv) memory 자체의 real-vs-donor cosine/retrieval probe, (v) train doc 수/steps/LR ablation, (vi) uncentered norm 보고.

### 다음 단계

1. 결론을 "**native 경로에서 adapter 부착 시 donor-specific signal 소실**"로 좁히고, EG2/F-L로의 일반화와 "bottleneck" 기제 주장을 철회하라.
2. `cause_centered.json`의 centered cosine/CV/eff_rank를 본문 증거로 승격하고, variance 붕괴 서술을 norm/공통평균 효과로 수정하라.
3. 새 prereg에 input-sensitivity control(zero/permuted memory), 고정 projection, residual adapter, donor-discrimination probe를 포함하라.

---

## Q3. F0 설계 (EG2 raw + decoder LoRA, no adapter)

**판정: disagree (현 설계로는 confound를 분리하지 못함)**

### 근거

1. **짝이 틀렸다.** LoRA를 고정한 2×2는 다음과 같다.

   | | adapter 없음 | adapter 있음 |
   |---|---|---|
   | native | **P** (기존) | **PA** (기존) |
   | EG2 raw | **F0** (제안) | **L** (기존) |

   F0의 올바른 adapter 대조는 **L**이다(둘 다 EG2 raw, 둘 다 decoder LoRA). 제안된 `F0/F/P/PA`는 L을 빼고 F를 넣어, F0 vs F에서 **adapter와 LoRA가 동시에** 달라진다. 따라서 "F0 positive → adapter 원인 확정"이라는 분기는 현 arm set으로는 검정 불가능하다.
2. **F0 negative는 해석 불가능하게 갈린다.** native memory는 이미 mT5 decoder가 기대하는 encoder space에 있고, EG2 raw feature는 out-of-distribution + 거의 collinear(raw mean cos 0.998)다. F0에는 memory-side trainable alignment가 전혀 없고 decoder LoRA(`1e-4`, 100 updates)만 있다. F0=0은 "EG2 content 부족"과 "EG2→decoder alignment 부재/최적화 부족"을 구분하지 못한다.
3. **F0 negative가 예상된다.** raw EG2의 uncentered mean cosine이 0.998이므로 mean-pool 수준의 donor 정보는 이미 거의 없다. 즉 F0는 negative로 나올 가능성이 높고, 그 경우 정보량이 적은 branch("EG2 feature 부족")로 흘러가기 쉽다.
4. **빠진 arm/control**: L(또는 5-arm `F0/F/L/P/PA`), 고정 random/orthogonal projection arm, label-free linear projection arm, residual adapter arm, zero/permuted-memory null, memory donor-discrimination probe. 또한 F0의 K는 753이므로 P와 직접 비교하면 K까지 confound된다.
5. **비용 산술**: F0를 F/L과 같은 120 records/unit으로 두면 제안 4-arm은 M 1,680이 맞다. L을 추가하면 1,800이다.

### 다음 단계

1. EG2 2×2를 `F0` vs `L`로 정의하라(또는 5-arm). LoRA는 모든 arm에서 고정하라.
2. 고정 alignment control(예: label-free linear projection 또는 random orthogonal projection) 1개와 residual adapter 1개를 추가하라.
3. 네 가지 결과(F0±, projection±)의 해석을 **사전에** 표로 고정하라. 특히 "F0 negative + projection positive = alignment 문제이지 EG2 content 문제가 아님"을 명시하라.

---

## Q4. M endpoint 해석

**판정: agree (문서보다 강하게)**

### 근거

- M은 `delta = control(global mean) CE − real CE`의 단측 비교다. F/L/PA는 `M_PASS`이면서 `wrong−real ≈ 0`이고, P만 `wrong−real=2.531`, ratio `0.414`다. 즉 **M_PASS는 donor specificity를 전혀 요구하지 않는다.**
- F/L/PA의 M_PASS는 "real이 global mean보다 낫다"는 것뿐이며, input-independent 또는 global-mean 근처 memory로도 달성 가능하다. 실제로 F/L/PA의 판별력은 0에 가깝다.
- 따라서 `M_PASS all arms true`를 content-use evidence로 쓰는 것은 부적절하다. 보고서의 `M_PASS ≠ content-use signal` 결론에 동의한다.
- **M 정의를 결과 후 재해석하는 것은 허용되지 않는다.** 다만 "M은 calibration이며 content-use가 아니다"라는 *서술적* 해석은 동결 문서 자체(§5)와 일치하므로 문제없다. B0-B는 이미 signal에서 false이므로 M을 구제할 필요도 없다.

### 다음 단계

1. 새 prereg에서 M은 **calibration/validity**로만 유지하고, content-use의 primary는 donor contrast로 두라.
2. input-dependence를 직접 요구하는 control(zero/permuted memory)을 추가하라. 단 이는 새 gate이므로 새 prereg에서만.
3. 현 v1.0.11의 M threshold/정의는 변경하지 말고, B0-B 재판정에 사용하지 말라.

---

## Q5. Phase 6 종료 vs 새 prereg

**판정: NARROW**

### 근거

- 동결 gate 기준으로 B0-B candidate는 **false**이며, 이는 측정 오류가 아니라 실제 신호 부재로 보인다. L/F/PA의 donor specificity가 0에 가깝고 3/3 seed 음수다.
- 따라서 Phase 6는 **negative result로 종료**해야 한다. 결과를 본 뒤 threshold/seed/donor/step/LR을 바꿔 재실행하거나 B0-B를 재판정하는 것은 금지다.
- 원인 결론은 P→PA 범위로만 유효하고, F0 설계는 현안대로는 confound를 분리하지 못한다. 따라서 "F0를 바로 3-seed로 실행"은 이르다.
- EG2 resident encoder 트랙을 지금 접을 필요는 없지만, **선험확률은 낮다**: 유일한 positive arm은 native memory이고, raw EG2는 이미 거의 collinear다. 접기/유지 결정은 통제된 F0 결과 이후로 미뤄야 한다.

### 다음 단계

1. Phase 6를 B0-B candidate false의 negative로 종료하고, 재실행·threshold 변경을 금지하라.
2. 좁은 diagnostic prereg을 작성하라: `F0 + L`(LoRA 고정) + 고정 projection + residual adapter + zero/permuted null, 우선 1-seed D-level, D gate 통과 시에만 3-seed.
3. EG2 트랙의 stop rule을 사전에 정의하라(예: F0와 projection control이 모두 donor specificity 0이면 접기; projection이 살리면 alignment/H3로 좁히기).

---

## Q6. Artifact/provenance 충분성

**판정: conditional**

### 충분한 부분

- Freeze 무결성: plan SHA `327a3e34…`가 freeze commit과 HEAD에서 동일, manifest SHA `f5d9ac8a…`가 `05b7abe`에서 일치, freeze 이후 plan 무변경.
- Registry의 registered_report/M records/labels/replay/cause/final checkpoint hash **7개 해시 전부 일치**.
- Count: 12 units, 1,200 updates, M 1,680, phase7 7,200, checkpoints 12, generation 240. M 표 16셀과 label 산술을 raw records에서 재현.
- Cohort: unit/M/phase7의 모든 target ID가 train20/val20 내부. `p1_usage`/`postrun`은 `p1_used=false`, `test_split_read=false`를 기록.
- phase7(7,200, diagnostic)과 primary M(1,680)이 파일·gate 수준에서 분리되어 있고, phase7은 `m_valid`에 들어가지 않는다.
- replay 12/12, `atol=1e-5`, `rtol=1e-4`.

### 부족한 부분

1. **Registered run의 실행 코드가 커밋되어 있지 않다.** `runner/c5_pm_phase6.py`는 `run_d0`/`run_d1`만 있고, `main()`은 `--mode registered`에 대해 `NotApprovedError`를 던진다. `train_registered`는 존재하지만 도달 불가능하다. 커밋 `9d6be7a`(run commit)에도 `run_registered`가 없다. 즉 **커밋된 코드로 registered 결과를 재생성할 수 없다.**
2. **Labels/replay/cause/gate의 driver도 없다.** `c5_pm_labels.py`는 순수 모듈(CLI/I/O 없음)이고, `d9aac0e`는 출력 JSON만 추가했다. `b0_b_candidate_gate`를 계산하는 함수는 어디에도 없다. 따라서 `labels_computed:false → true` 전환은 **code identity/command/입력 해시 없는 audit gap**이다. (수치는 커밋된 unit `per_doc`에서 재현되므로 수치 신뢰성은 유지된다.)
3. **registered_report.json의 상태 필드가 낡았다.** `labels_computed=false`, `decision_labels_computed=false`인데 registry/labels.json은 `true`다. 같은 run에 대해 두 아티팩트가 모순된다.
4. **replay는 평가 결정성만 증명한다.** 저장된 checkpoint에서 eval을 재실행해 `replay_ok`를 얻었을 뿐, 학습 재현성(환경, seed/init, dataloader, code commit)을 묶는 manifest가 없다. wall/threads("3 waves, 4 arms parallel, 2 threads")도 아티팩트로 검증되지 않는 텔레메트리다.
5. **test 163/P1은 attestation이지 proof가 아니다.** `p1_usage.json` 스스로 그렇게 명시한다. ID containment는 일관되지만 파일 접근 감사는 없다.
6. **`FREEZE.json manifest_commit=null` vs 요청서/registry `05b7abe`** — note에 설계 의도가 적혀 있으나 보고서 표에는 일관되게 반영되지 않는다.

### 다음 단계

1. registered run driver와 label/replay/gate driver를 커밋하고, 최소 1개 unit에 대해 end-to-end 재생성 테스트를 붙여라.
2. `labels_computed` 전환에 code commit/command/input SHA를 기록하고 `registered_report.json` 필드를 갱신하라.
3. training reproducibility manifest(환경·seed·init·data order)와 leakage/mode/metric boolean을 아티팩트에 추가하라.

---

## 최종 판정

```text
최종 판정: NARROW
B0-B candidate false: 동의. 동결 v1.0.11 gate 기준 false가 정확하고, 산술·tri-state·tail·dispatch 모두 재현됨. Phase 6는 negative로 종료하고 재실행/threshold 변경 금지.
adapter bottleneck: P→PA(native, K=512)에서는 "adapter 부착 시 donor specificity 소실"이 지지됨. 그러나 EG2/F-L로의 일반화, "bottleneck"이라는 구조적 명칭, variance 붕괴 인과 해석은 미확립. centered cosine/CV/eff_rank가 거의 동일해 98% variance 감소는 norm/공통평균 효과로 보이며, raw EG2 자체가 이미 mean cos 0.998임.
F0 설계: 현안(F0/F/P/PA)은 confound 분리 실패. LoRA를 고정한 F0 vs L 짝이 필요하고, 고정 projection·residual adapter·zero/permuted null·donor-discrimination probe가 빠져 있음. F0 negative는 "EG2 content 부족"과 "alignment 부재"를 구분하지 못함.
Phase 6 종료/새 prereg: Phase 6는 negative 종료. F0/H3는 새 prereg + 별도 승인. 우선 1-seed D-level diagnostic으로 좁히고, D 통과 시에만 3-seed.
금지 범위: 결과 후 threshold/seed/donor/step/LR 변경, B0-B/B1/B2/Stage C 자동 진행, test 163/P1 사용, 현 v1.0.11 M 정의의 사후 재해석으로 B0-B 구제.
Must-fix (ranked):
  1. Registered run + labels/replay/gate driver 커밋 (현 main()은 --mode registered 거부, gate 함수 부재).
  2. labels_computed false→true audit: code commit/command/input SHA 기록 및 registered_report 상태 필드 정합.
  3. cause 결론 축소: "native 경로의 adapter-induced signal loss"로 한정, EG2 일반화·bottleneck·variance 인과 철회.
  4. variance 증거를 centered cosine/CV/eff_rank + norm으로 교체하고 mean-pool 한계 명시.
  5. F0를 F0/L 2×2(+projection, residual, null)로 재설계.
  6. replay를 넘는 training reproducibility manifest 추가.
  7. 15-doc 길이 선택 코호트와 20-doc 평균(-0.022, F +0.000) 차이를 명시.
잘못된 전제:
  1. "P/PA는 adapter만 다르다" — PA는 +526,336 params와 10× adapter LR도 다름(capacity/LR confound).
  2. "adapter variance 붕괴가 signal 소실의 원인" — centered geometry는 보존되며 raw EG2도 이미 collinear.
  3. "F0가 F와 짝이면 adapter를 분리한다" — F0 vs F는 adapter와 LoRA가 동시에 다름.
  4. "M_PASS가 content-use 증거" — M은 global-mean 대비 calibration이며 donor specificity를 요구하지 않음.
  5. "adapter bottleneck" — Adapter는 512→512로 width bottleneck이 없음; 기제는 LayerNorm/input-insensitive mapping 쪽.
  6. "F0 negative면 EG2 feature 부족" — decoder-space alignment 부재와 구분되지 않음.
```

---

## 부록. 본 검토에서 수행한 재계산 (모델 실행 없음)

- `registered_m_records.json` 1,680건에서 arm×variant×endpoint별 seed-average doc delta 재계산 → 보고서 M 표와 일치.
- `units/{arm}_{seed}.json`의 `final.per_doc`에서 15 common IDs 평균 재계산 → `L` seed means `-0.1331/-0.1043/-0.1031`, 전체 평균 `-0.1135`; `F` `-0.1109`; `P` `3.0764`; `PA` `0.0112`.
- `cause_analysis.json`의 per-doc L delta에서 mean/positive(6/15)/top3/abs_share/signed_share/leave_mean 재계산.
- 20-doc 전체 평균 대조: L `-0.0222`, F `+0.0002` (15-doc 코호트와 구분되는 길이 선택 효과).
- registry 해시 7종, freeze plan/manifest SHA, checkpoint hash 12 keys, replay 12/12, cohort ID containment 확인.