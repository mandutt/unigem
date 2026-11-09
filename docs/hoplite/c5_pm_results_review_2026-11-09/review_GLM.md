# C5 Phase 6 P/M — Results & Cause Analysis Independent Review (GLM 5.3 Flash)

- 작성일: 2026-11-09
- 모델: `z-ai/glm-5.3-flash`, 신규 독립 스레드. 이전 C5 prereg 스레드의 결론을 상속하지 않음. 타 모델 답변 미재사용, 서브에이전트/추가 LLM 미사용.
- **검토 기준 HEAD SHA: `d809e0002d0653e3c4207c58a38bb8af0b641467`** ("docs: add C5 Phase 6 results review request"). 동기화: `git fetch origin` + `git pull --ff-only origin main` → "Already up to date". 요청서 기재 HEAD `8118204`(cause analysis 등록 커밋)는 이 HEAD의 직전 데이터 커밋.
- **필수 verbatim 인용: `adapter bottleneck`** — 본 보고서와 원문(`reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md` 결론 행, cause_analysis D-159)에 그대로 등장하는 구절로, 이 검토는 그 결론의 타당성을 재판정한다.
- 범위 준수: 학습·평가 실행 없음(모델 forward 없음), test 163 미개봉, P1 미사용, repository 수정 없음(지정 report 파일 1개만 작성). 수치 검증은 커밋된 artifact(JSON) 대상 순수 재계산(PCG64 20261109, 1,000 resamples 재현 포함)뿐.
- 상태: **B0-B 미승인 (candidate gate false)**. Phase 6 registered 3-seed 완료, labels/cause 완료. 본 검토는 새 실험 승인이 아니다.

---

## 0. 독립 재계산 결과 (커밋된 artifact만 사용)

재계산 입력: `registered/units/{arm}_{seed}.json`의 `final.per_doc`(signal population), `registered/m_records_{arm}_{seed}.json`(1,680), `phase7_records/`(diagnostic), `labels/labels.json`, `labels/cause_analysis.json`, `labels/cause_centered.json`, freeze/registry 파일.

| 항목 | 재계산 | 결과 |
|---|---|---|
| freeze chain 5종 hash (plan blob `327a3e34…`, freeze manifest blob `f5d9ac8a…`, p1 `69af129a…`, golden `30cbd1c1…`, preflight content `3ee3f1ca…`) | `git show <commit>:<path>` + SHA256 재계산 | **전부 일치** (`freeze_manifest_commit.txt`=`05b7abe…` 포함) |
| M primary 16행 (F/L 15 targets, P/PA 20, `delta=control−real`, seed-average → bootstrap) | m_records에서 독립 재계산 | **16/16 행 mean·CI 소수점 3자리까지 정확 일치** (예: L M_POS_MEAN copy 0.367 [0.313, 0.427], P full 6.118 [3.913, 8.644], PA full 0.576 [0.554, 0.601]) |
| M record count | unit당 F/L 120, P/PA 160, 합계 **1,680** | **일치** |
| `L_COPY_SIGNAL` | unit final per-doc 15 common, seed-avg, PCG64 20261109 ×1,000 재부팅 | mean **−0.113506** [−0.234090, −0.001167], seed means **−0.133083 / −0.104326 / −0.103110 (0/3)**, paired L−F **−0.002639** [−0.040845, 0.034302] (8/15) — labels.json과 **전치 일치** |
| `L_FULL_SIGNAL` | 동일 (full) | **−0.108550** [−0.223406, −0.005734], paired −0.000866 — 일치 |
| signal tail | 동일 population | top3_abs_share **0.477464**, signed **0.803495**, leave_top3_mean **−0.027881**, top3 = 01518/00020/01951 → `tail_driven=true`(leave≤0 규칙) — 일치 |
| `P−PA` paired contrast (copy) | unit final per-doc | **+3.065202** (14/15), P 3.076413 vs PA 0.011211 — cause_analysis와 일치 |
| cause §1 `wrong−real Δ` 행 | unit final full, **20-doc 전체** 평균 | F **+0.0008**, L **−0.0167**, P **+2.5306**, PA **+0.0129** → 표기 0.001/−0.017/2.531/0.013과 일치 (population: 20-doc uncapped donor crop) |
| collapse 지표 (cause_centered) | 재독해 | raw EG2 between-var **4.883** → F **0.085** / L **0.081**(−98.3%), native **0.841** → PA **1.284**; pair distance 3.142/0.418/0.405/1.324/1.623 — 보고서 표와 일치 |
| replay | `labels/replay_report.json` 12 keys `all_ok:true`, unit replay 12개 파일 (m 120/160 + phase7 600, `atol=1e-5`,`rtol=1e-4`) | 커밋 확인. CE 수준 재실행은 금지 범위라 미수행 (아래 한계 명시) |
| signal population ≠ phase7 | phase7(K_M 절단 diagnostic)에서 같은 방식 재계산 시 L copy mean **−0.0407** | labels(−0.1135)와 **다름이 정상** — §2.3 signal(uncapped donor crop) vs §9.6.1 diagnostic(K_d≤K_M)의 설계된 이중 population (§4 참고) |

결론: **세 보고서의 모든 수치는 커밋된 artifact에서 재현 가능하며, 산술·bootstrap·tail 오류는 발견되지 않았다.** 단, "수치 재현"과 "실행 코드 재현"은 별개다 (Q6).

---

## 1. Q1 — Label/gate 정확성

- 판정: **agree** (labels/gate 산출은 frozen v1.0.11과 정확히 일치. 경미한 잠재 결함 2건은 본 실행에서 발화하지 않음)
- 근거:
  - `runner/c5_pm_labels.py`는 §3.2 연산자(`and_n` false-dominant, `not3`, §3.4 9-pair 표), §3.5 술어(copy `>=.05`, full `>0`, CI lower `>0`, paired `>0`, **2/3** seeds)를 문자 그대로 구현한다. 본 실행 입력(both false, 15 docs, 3 seeds)에서 `l_signal=false`, `copy_only/full_only=false`는 표대로다.
  - `signal_status` dispatch(§6.3): n=15, VALID, control=M_CONTROL_PASS, l_signal=false → **MEAN_CONTRAST_ONLY** 정확. `validity_status`/`control_status` 우선순위(§4.2 known-failure first, §5.4)도 코드와 일치.
  - `tail_driven`: §10.4 규칙(leave_top3_mean≤0 → true) 적용 결과 true. `top3_abs_share 0.4775<.50`이어도 leave≤0이면 true인 것이 동결 규칙이며, 요청서의 기술도 정확하다.
  - `b0_b_candidate_gate=false`는 §14의 9조건 중 `signal_status==EXPLORATORY_L_SIGNAL`(false)과 `tail_driven==false`(true) 2개 실패로부터 기계적으로 도출된다.
  - M pass: `m_pass_l`(L, delta>0+CI>0 양 variant·양 endpoint)와 `m_valid`(P/PA, copy `>=.05`+CI>0) 모두 재계산된 M 수치와 양립 — 문서화된 threshold asymmetry(§4.5 note) 그대로 적용되었다.
  - 잠재 결함 (미발화): (a) `l_predicate`는 `per_seed_means`의 개수가 3임을 강제하지 않는다 — 계산 스크립트가 2 seeds만 넘기면 금지된 "2-of-available"가 가능(본 실행은 3 seeds 확인). (b) labels/replay/cause를 실제 계산한 스크립트가 커밋되지 않아 caller 측 가드가 감사 불가 (Q6).
- 다음 단계: (1) label/replay 계산 드라이버를 커밋하고 `len(seed_means)==3` 가드를 caller에 명시. (2) reports에 "signal population(uncapped) vs phase7(capped) 불일치" 주석 추가. (3) labels.json에 M pass의 4-conjunct 세부(`delta`, `ci_lower`)를 저장해 재판정 가능하게 유지.

## 2. Q2 — "adapter bottleneck" 타당성과 confounders

- 판정: **conditional agree** — 어댑터가 결정적 차별 요인이라는 방향은 데이터가 강하게 지지하지만, "bottleneck"이라는 **메커니즘 단일화**는 아직 과잉 주장이다.
- 근거 (지지):
  - **P vs PA는 어댑터 유무만 다르다** (native 512, decoder LoRA, 동일 seed/updates/K): copy signal 3.076 → 0.011, paired +3.065, 14/15, seed-consistent. 어댑터 삽입이 donor specificity를 소멸시킨다는 사실 관계는 견고하다.
  - **F vs L (paired −0.0026, 8/15)**: decoder LoRA는 signal에 사실상 무관 — LoRA 기각은 타당.
  - **PA의 variance 증가(0.841→1.284)에도 signal 소멸** → "단순 global collapse" 하나로는 설명 안 됨 — cause report의 자기 인식이 정확하다.
  - F/L 어댑터의 between-doc variance 98.3% 수축(4.883→0.085)과 M control−real Δ(wrong−real≈0과 대비)는 "generic shift 학습, donor-specific 성분 미보존" 메커니즘과 부합한다.
- 근거 (한계/confounders):
  1. **메커니즘 후보가 여럿 남는다**: (a) 정보 bottleneck, (b) optimization interference(어댑터 526,336 params, `adapter_lr=1e-3`는 LoRA lr의 10배, joint 학습 간섭), (c) decoder off-manifold(학습되지 않은 어댑터 출력 분포를 decoder가 못 씀), (d) **구조적 원인 — Adapter의 마지막 LayerNorm**(검증: `runner/c5_mt5_layer_probe.py` L52-63, Linear→GELU→Linear→LayerNorm): per-token 정규화가 token 공통 성분을 제거하고 학습된 affine β가 문서 무관 상수 벡터를 재주입 — "generic shift + donor specificity 소멸"을 정확히 만드는 구조. PA가 variance를 유지하며 specificity만 죽는 것도 (c)/(d)와 양립.
  2. **P/PA vs F/L 비교는 memory source와 K(512 vs 753)가 함께 다르다** — 요청서 지적이 정확. cross-family 결론은 F0 없이 불가.
  3. **경미한 RNG confound**: PA는 adapter init이 RNG를 먼저 소모하므로 동일 seed에서 P와 LoRA A init이 다르다(init 함수값은 `lora_B=0`으로 동일, gradient 경로는 상이). "어댑터만 다름"은 함수적으로 참, 확률적으로 근사.
  4. cause §1 표의 `wrong−real Δ`는 **20-doc uncapped** population, M 행은 K_M primary population — 혼합 비교(descriptive). 15-doc signal cohort에서 F/L의 wrong−real은 −0.108로 명확히 음수(즉 real이 wrong보다 **나쁨**) — "wrong donor가 real과 거의 같다"는 서술은 방향적으로 맞지만 cohort를 명시해야 한다.
  5. M control은 train20(=학습에 쓴 20 docs)의 어댑터 출력 평균 — M Δ의 일부는 학습된 generic shift 자체.
- 다음 단계: (1) F0 (Q3)로 어댑터 제거 시 signal 부활 여부 확인 — necessity 확인. (2) 메커니즘 판별은 새 prereg의 H3 계열로: residual/identity-preserving adapter(`x+α·A(x)`), **final-LayerNorm 제거/교체 비교**, capacity·lr 매칭 — 단, v1.0.11 결과에 대한 사후 변경이 아닌 신규 prereg로만. (3) cause report에 cohort/population 각주 추가.

## 3. Q3 — F0 설계

- 판정: **conditional agree** — 2×2(memory source × adapter) 완성으로 confound 분리는 유효. 단 3가지 보완 필요.
- 근거:
  - F0(EG2 raw + decoder LoRA, no adapter)는 기존 4-arm과 합쳐 `{EG2, native} × {adapter, no-adapter}`(LoRA 체제) 완전 계열을 만든다: **F0−P = memory source 순수 비교**(decoder LoRA 동일, K_M 512 동일, 어댑터 없음), **F0−L = EG2 위의 어댑터 효과 재확인**(P−PA의 EG2 버전). 설계 논리는 올바르다.
  - 동결 훼손 없음: 신규 prereg이므로 arm 추가는 허용 범위. 기존 threshold/seed/donor/step/LR 재사용이 비교 가능성을 유지.
  - 빠진 것:
    1. **0-update EG2-raw usability probe**: F0가 0이면 "EG2 feature에 정보가 없다"와 "EG2 feature가 decoder 입력 분포에서 벗어나 못 쓰인다"를 구분 못 한다(요청서의 "F0 0이면 EG2 feature 부족"은 과잉 주장). D0식 step-0 평가(base decoder가 EG2 raw memory vs native memory를 쓰는 baseline CE)를 F0 prereg의 diagnostic으로 사전 등록하면 이 ambiguity를 줄인다.
    2. (선택) native+adapter 무LoRA cell — L−F≈0이므로 우선순위 낮음.
    3. F0 세부 고정 필요: M K=512(요청서대로) 시 F/L과 M K가 달라지므로 M은 within-arm 비교임을 명시, contributor 규칙(h_len≥512, ≥10), M target 15 common, donor 규칙 변경 없음, 최소 검출 효과 크기(P의 3.08 대비 F0 기대치)를 사전 기술.
- 다음 단계: (1) F0 단일 arm(또는 F0 중심 소형 prereg) 기안 — 3 seeds, 100 updates, M 1,680 상당, phase7 진단, 동일 tail 규칙. (2) step-0 usability probe 포함. (3) 사전 판정 분기표(F0+, F0−, 각 경우의 해석 경계)를 prereg에 명문화.

## 4. Q4 — M endpoint 해석

- 판정: **agree** (보고서의 해석이 옳다: M_PASS ≠ content-use signal)
- 근거:
  - M은 `real vs global-mean control`이며 donor specificity를 측정하지 않는다(§9.2 builder). 데이터가 이를 실증: F/L/PA는 M Δ 0.365~0.576으로 pass이지만 signal-cohort wrong−real은 −0.108(실제로 wrong이 더 나쁨), P만 wrong−real +2.53~3.08로 specificity 존재. **M_PASS는 "메모리를 전혀 안 쓰는 것보단 낫다"의 증거이지 "올바른 문서의 메모리를 쓴다"의 증거가 아니다.**
  - 그러나 M을 완전히 무의미하게 볼 필요는 없다: B0-A 계열의 acquisition/calibration control로서 기능은 수행했고, P의 M Δ 6.12는 specificity와 정렬된다. **필요조건으로 유지, 충분조건 아님.**
  - **재해석 허용 범위**: 보고서/해설 층위의 재해석(descriptive)은 허용. 반면 gate 의미를 사후에 바꾸는 것(예: M에 specificity 조건을 소급 추가, threshold 조정)은 금지 — "결과 후 threshold 변경 금지"의 취지에 정확히 해당. 새 요구는 **새 prereg의 새 endpoint**(예: signal-cohort `wrong−real` 또는 donor-discrimination)로 추가해야 하며, M은 정의 그대로 연속성 유지.
- 다음 단계: (1) 새 prereg에 donor-specificity endpoint를 primary(또는 co-primary)로 등록. (2) M은 기존 정의 유지 + "M_PASS는 specificity 아님"을 문서화. (3) labels.json/registry에 이 해석 경계를 메타로 기록.

## 5. Q5 — Phase 6 종료 vs 새 prereg

- 판정: **NARROW** — Phase 6는 negative로 종료하되, 단일 F0 prereg만 허용하는 좁은 연속.
- 근거:
  - B0-B candidate false는 측정 오류가 아니라 **실제 signal 부재**(labels 재현으로 확인)이며 원인이 국소화되었다(어댑터 삽입 시 소멸, P에서 존재 입증). 이는 STOP보다 좁은 단일 위증 실험을 정당화한다.
  - **F0 실패 시**: P(positive)+F0(zero)는 "decoder LoRA 하에서 EG2 layer19 raw feature는 donor-specific signal을 decoder에 전달하지 못한다"를 의미 → **EG2 상주 인코더-as-memory 트랙은 접는다(STOP)**. 어댑터 경로는 이미 PA로 소멸이 입증되었고 H3는 정보가 없는 feature를 정렬할 수 없으므로 트랙 연장 근거가 없다. (EG2를 다른 용도로 쓰는 건 본 실험 범위 밖.)
  - **F0 성공 시**: 원인이 어댑터 구조로 확정되므로 다음은 **어댑터 구조 변경(H3: residual/identity-preserving, final-LayerNorm 제거·교체, lr/capacity 정합)** — 별도 prereg. 이때 B0-B 재도전은 F0/H3 결과 이후 새 gate 정의로만.
  - H3를 지금 병행하지 않는 이유: F0 결과가 H3 설계(정보 존재 여부)를 사전 결정하므로 순차가 정보 효율적.
- 다음 단계: (1) Phase 6 종결 보고(B0-B candidate false, 원인 진단 첨부) 확정. (2) F0 prereg 초안(위 Q3 조건 포함) 작성·승인. (3) F0 분기표에 따른 STOP/H3 경로를 prereg에 명문화.

## 6. Q6 — Artifact/provenance 충분성

- 판정: **conditional** — artifact 무결성은 강하다. 그러나 **실행 코드 provenance 공백**이 B0-B/새 prereg 전 must-fix다.
- 근거 (강점):
  - freeze chain 5종 hash를 내가 재계산해 전부 일치(plan blob @`6fad89e`, manifest blob @`05b7abe`, p1, golden, preflight content, `freeze_manifest_commit.txt`). registry v7에 freeze 전체 재기록 일치.
  - 12 checkpoints + `final_checkpoint_hash.json`(12 keys), control manifest(`control_digest`), M 1,680 / phase7 7,200 / generation 240 counts 검증.
  - **모든 결정 수치가 커밋된 artifact에서 재현됨**(§0) — labels/cause의 결과는 신뢰 가능.
  - `test_split_used=false`는 allowlist 방식(§1.5)으로 코드·artifact 양쪽에서 확인됨 — artifact의 모든 ID가 train20∪val20 내부. test 163/P1 미사용과 T5Gemma2 D-108 STOP 경계 문장이 보고서마다 유지됨.
- 근거 (공백):
  1. **실행 드라이버 미커밋**: HEAD의 `runner/c5_pm_phase6.py` `main()`은 `--mode registered`에서 `NotApprovedError`를 던지고 `run_registered`/wave 코드가 파일에 없다 — 그럼에도 9d6be7a가 12-unit 결과를 커밋했다. labels(`d9aac0e`)는 pure 모듈만 커밋(`c5_pm_labels.py`는 테스트 외 미참조), cause 계산 스크립트도 부재. 즉 **registered 실행·label/replay·cause 계산의 정확한 코드가 저장소에 없고**, 재현은 "커밋된 artifact + 미커밋 코드"에 의존한다.
  2. `labels_computed:false`(실행 시) → `true`(labels.json) 전환이 커밋된 스크립트 없이 커밋 사이에서 발생 — 요청서 지적 audit gap이 실재한다. 수치 재현(§0)이 완화하지만 닫지는 못한다.
  3. `p1_usage.postrun.json`의 `checked_artifacts`가 2개 파일뿐 — §1.5는 registry glob 전수 확장을 요구. 사소하나 보완 대상.
  4. phase7 diagnostic이 primary M 분리 규칙(§9.6.1 "does not feed any gate")은 준수되었으나, **signal population과 phase7이 수치가 다름**(−0.1135 vs −0.0407)을 보고서가 명시하지 않아 재독자가 혼동할 수 있다(본 검토자도 초기에 혼동).
  5. CE 수준 replay 재실행은 본 검토 금지 범위로 미수행 — replay 12/12는 커밋된 리플레이 산출물의 존재·구조 확인까지가 본 검토의 검증 한계다.
- 다음 단계: (1) 미커밋 드라이버(registered wave, label/replay 계산, cause 계산)를 커밋하거나 정확 코드+실행 환경을 provenance로 영구 보관. (2) `p1_usage.postrun.json` 전수 확장. (3) signal vs phase7 population 주석을 labels/cause/registry에 추가.

---

## 7. 최종 판정 블록

```text
최종 판정: NARROW
B0-B candidate false:
  측정 오류 없음 — 실제 signal 부재. 9조건 중 signal_status(MEAN_CONTRAST_ONLY≠EXPLORATORY_L_SIGNAL)
  와 tail_driven=true 2개 실패. Phase 6는 negative로 종료 확정.
adapter bottleneck:
  어댑터 삽입 자체가 결정적 차별 요인이라는 방향은 P−PA(+3.065, 14/15)와 F/L variance 수축이 강하게 지지.
  다만 "bottleneck" 메커니즘 단일화는 미확정 — optimization interference, decoder off-manifold,
  Adapter final-LayerNorm의 generic-shift 구조가 병존. F0가 necessity 확인, H3(잔차/LN 제거)가 메커니즘 확인.
F0 설계:
  채택(조건부). {memory source × adapter} 2×2 완성. 필수 보완: step-0 EG2-raw usability probe,
  M K=512/cohort/donor/MDE 사전 고정, "F0− ⇒ EG2 feature 부족" 류의 과잉 해석 금지(분기표에 명문화).
Phase 6 종료/새 prereg:
  종료 = negative 확정. 신규 = F0 단일 prereg만(NARROW). F0 실패 → EG2 상주 인코더-as-memory 트랙 STOP.
  F0 성공 → H3 어댑터 구조 prereg. B0-B 재도전은 그 이후 새 gate 정의로만.
금지 범위:
  학습·평가 실행, test 163 열람, P1 사용, frozen v1.0.11에 대한 threshold/seed/donor/step/LR 사후 변경,
  B0-B/B1/B2/Stage C 자동 진행, 기존 C5 스레드 혼합 — 전부 유지. F0/H3는 별도 prereg+승인으로만.
Must-fix (ranked):
  1. 미커밋 실행/계산 드라이버(registered wave, label/replay, cause) 커밋 또는 코드+환경 provenance 영구 보관
     — 없으면 어떤 후속 prereg도 저장소만으로 재현 불가.
  2. 새 prereg에 donor-specificity endpoint(wrong−real/discrimination)를 사전 등록하고 M은 현 정의 유지.
  3. F0 prereg 세부 고정: M K=512, contributors(h_len≥512)≥10, 15 common targets, donor 규칙 동일,
     tail 규칙 동일, 최소 검출 효과 + 분기표.
  4. p1_usage.postrun.json registry-glob 전수 확장 + labels_computed false→true 전환의 스크립트 흔적 보존.
  5. (경미) signal vs phase7 population 주석, l_predicate 3-seed 가드, PA 어댑터-RNG 주의 각주.
잘못된 전제:
  - "F0 positive면 adapter 원인 확정": necessity 확인일 뿐 메커니즘 단일 확정이 아니다.
  - "F0 0이면 EG2 feature 부족": decoder 입력 분포 부적합(off-manifold) 가능성을 배제하지 못한다.
  - "P가 positive control": P는 native 메모리 사용의 positive control이지 EG2의 그것이 아니다.
  - cause §1 표의 wrong−real 행(20-doc uncapped)과 M 행(K_M primary)은 다른 population의 혼합 비교(descriptive).
  - phase7 수치는 signal 수치가 아니다(K_M 절단 diagnostic): L copy −0.0407 ≠ −0.1135 — 혼동 금지.
```

---

## 8. 검증 한계 (명시적)

- 모델 forward/CE 재계산 금지 준수로, replay의 CE 수치 일치와 collapse 지표의 원값 재계산은 커밋된 산출물 대상 재독해·재집계 수준까지 검증했다(집계·bootstrap·규칙은 독립 재현).
- checkpoint `.pt` 내용 대상 hash 재계산은 torch 미설치 환경으로 미수행 — `final_checkpoint_hash.json` 존재·12 keys·커밋 상태만 확인.
- 본 보고서는 지정 경로 1개만 작성했으며 다른 파일은 수정하지 않았다.