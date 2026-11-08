# C5 layer role probing · Stage B0/B1/B2 계획 외부 검토 — GLM 5.3 Flash (독립 라운드)

- 작성일: 2026-11-08
- 검토자: GLM 5.3 Flash (이번 라운드용 신규 독립 검토. 다른 모델·다른 라운드의 답을 재사용하지 않았다)
- 검토 대상 문서: `reports/EXTERNAL_REVIEW_C5_LAYER_PLAN_2026-11-08.md` (618줄 전체 직접 열람)
- **검토 기준 HEAD: `bb8bf702cbff4c73129098d4b660784be289fd75`** ("docs: add C5 layer-plan 3-AI review prompts and dispatch")
  - 동기화: `git fetch origin` → `git pull --ff-only origin main` → "Already up to date" (로컬이 이미 동일 HEAD)
- 준수 사항: consultation-only (이 파일 외 저장소 쓰기 없음), 학습 실행 없음, **test 163 미사용**(분할 메타데이터 외 test 데이터 열람 없음), subagent·추가 LLM 호출 없음, P1/외부 API 미사용, `eval/slot_verify.py` 미수정 (SHA256 `a262cee0…869d03` 재확인 일치)
- gate 변경 승인 아님: 이 문서의 판정은 **계획 검토 의견**이며, Stage C·제품·재개 관련 gate는 별도 decision record가 필요하다.

---

## 0. 최종 판정

### **CONTINUE — 조건부**

- **Layer role probing + Stage B0를 승인**한다. 단, 아래 Must-fix M1(LoRA attach 네이밍/assert)과 M2(tokenizer 불일치 정량화·네이티브 재캐시)가 **B0 실행의 선행 조건**이다.
- **Stage B1은 B0 통과 시에만**, **Stage B2는 B1 완료 후에만** 실행한다 (계획의 의존관계 유지).
- **Stage C는 이 승인 범위에서 제외**한다 (별도 decision + metric audit 선행).
- T5Gemma2 재개 없음 (D-108 STOP 유지). test 163 봉인 유지.

요약 근거: 계획은 "어느 단계에서 어떤 원인을 분리하는가"(§0.6)라는 목적에 맞게 단계·gate·비용이 잘 구성되어 있다. 그러나 (1) 실행 계층에서 LoRA attach가 mT5/UMT5에서 **조용히 0개 모듈**에 붙을 위험이 있고, (2) layer19 anchor가 Stage A 자체 결론("real CE 순위 확정 불가", D-110/D-111) 및 신규 정량 증거(아래 F3·F4)와 충돌하며, (3) shuffle 통제와 분석 단위가 미규정이다. 이 세 가지는 저비용으로 수정 가능하고, 수정 없이는 B0~B2의 결과가 해석 불가능하거나 무효가 될 수 있다.

---

## 1. 검증 방법과 근거

### 1.1 직접 열람·검증한 것

- 검토 요청서 618줄 전체 (요약·발췌에 의존하지 않음)
- `reports/C5_MT5_UMT5_LAYER_PROBE_2026-11-08.md`, `reports/C5_MT5_LAYER_PROBE_2026-11-08.md`, `reports/C5_EG2_ALL_LAYER_SWEEP_2026-11-08.md`
- `reports/provenance/C5_b1d/mt5_layer_probe.json`, `umt5_layer_probe.json`, `all_layers_pretest.json` (수치 재계산 포함)
- `docs/decisions.md` D-100~D-111, `reports/C5_STATUS_2026-11-06.md` §37~§54 헤더, `reports/C5_BRIDGE_3AI_REVIEW_SYNTHESIS_2026-11-08.md`
- 코드: `runner/c5_mt5_layer_probe.py`, `runner/c5_eg2_all_layers_cache.py`, `runner/c5_b1d_b2.py`(일부), `runner/c5_a1_lora.py`(일부), `runner/c5_b1d_generate.py`(grounded 1줄), `eval/slot_verify.py` (전체)
- `reports/provenance/C5_clean/splits.json` (seed 42, 1,293/161/163, sha256 기록 확인)

### 1.2 이번 환경에서 검증할 수 없었던 것 (한계 선언)

- `data/*`는 gitignore(`.gitignore`: "데이터·캐시 (P0/P1 모두)")로 이 체크아웃에 가중치·캐시가 없다. 따라서 **재실행·재측정은 불가능**하며(애초에 금지), 수치 검증은 `reports/provenance`의 JSON과 보고서 간 교차 확인 수준이다.
- `transformers`가 이 샌드박스에 설치되어 있지 않다. 따라서 아래 F9의 HF 네이밍 판단은 **T5/MT5/UMT5 소스 관례(q/k/v/o) + T5Gemma2 쪽은 D-102의 r8/r16 결과 차이라는 간접 증거**에 근거하며, B0 runner에서 **assert로 강제 확인**해야 한다 (Must-fix M1).
- EG2 config(PLE 구조)와 네이티브 tokenizer 파일은 이 체크아웃에 없어 문서 기술(§2.1, §3.4)을 그대로 신뢰한다.

### 1.3 artifact·코드에서 이번에 새로 확인한 사실

| ID | 사실 | 근거 |
|---|---|---|
| F1 | **zero CE가 모델 내 23개 layer에서 상수**: mT5 `25.877`, UMT5 `12.214` (unique 값 1개씩). Δzero는 layer와 무관한 off-manifold 값 | `mt5_layer_probe.json`/`umt5_layer_probe.json` 재계산 |
| F2 | mT5 Δshuffled: **mean .0366 / median .0302 / 18/23 양수 / max .1889(layer17)**. layer19는 **.0302**. UMT5: mean .0013, max .009(layer19) | JSON 재계산 |
| F3 | layer 간 `train_ce_last`와 `val_real_ce`의 Pearson **r=.813** → real CE의 layer 산포(6.623~7.469)의 상당 부분이 adapter 최적화·초기화 노이즈 | JSON 재계산 |
| F4 | Stage A는 layer마다 `torch.manual_seed(20261108 + layer)`로 **초기화 seed를 layer와 함께 바꾼다** → layer 효과와 init 효과 혼재 | `runner/c5_mt5_layer_probe.py:133` |
| F5 | shuffled memory = **cyclic 이웃 1개**(`rid2 = ids[(i+1) % len(ids)]`), n=5, 이웃 문서 memory의 길이·내용 동시 변경, permutation 1회 | 동일 파일 `:104` |
| F6 | adapter는 **real memory로만** 학습. zero/shuffled 평가는 학습 분포 밖(OOD) 평가다 | 동일 파일 `probe_layer`/`eval_ablation` |
| F7 | Stage A JSON에 **per-doc CE가 저장되지 않는다** → 사후 CI·검출력 분석 불가 | JSON 구조 |
| F8 | EG2 캐시 스크립트는 **`t5_tok`(T5Gemma2 tokenizer)로 source를 tokenize**한다. EG2 네이티브 tokenizer(`tok`)는 로드만 되고 텍스트 처리에 미사용 | `runner/c5_eg2_all_layers_cache.py:73,74,103` |
| F9 | `attach_decoder_lora`의 TARGETS는 **`q_proj/k_proj/v_proj/o_proj`** (Gemma 계열 네이밍). T5Gemma2에서는 유효했음(D-100/D-102: r8 vs r16 결과 차이 → 모듈 attach·학습 실제 작동). **mT5/UMT5의 HF T5 계열 attention은 `q/k/v/o` 네이밍**이므로 동일 matcher는 0개 모듈에 attach될 위험 | `runner/c5_b1d_b2.py:38,41` |
| F10 | `grounded = not rep.new` (no-new-only) — 코드로 재확인 | `runner/c5_b1d_generate.py:147` |
| F11 | Stage A layer당 ~85초 → 전체 재실행 ≈ 33분. EG2 전 layer 캐시 재추출 ≈ 418초 (25 layer × 400문서, 문서당 1 forward) | JSON `elapsed_sec`, cache script 헤더 |
| F12 | probe의 train/val은 분할의 **접두 리스트**(`split["train"][:5]`, `split["val"][:5]`). B0의 20/20도 동일 방식이면 `val[:20]` | `runner/c5_mt5_layer_probe.py` main |
| F13 | A1 native matched val100 **preservation .4446** (grounded 100%는 no-new-only) | 3-AI synthesis §5.2 (기록) |

---

## 2. 핵심 질문(요청 상단 6개) 요약 답변

| # | 질문 | 답 |
|---|---|---|
| 1 | layer role probing 설계로 lexical/numeric·date/slot-overlap/sentence-position 구분 가능? | **부분 가능 (conditional)**. 4 probe 축은 커버하나, ① 관측된 실패 양상(내용 선택성 부재)을 직접 재는 **문서 식별·검색가능성 probe** 결측, ② 23×4 격자의 다중성 통제 결측, ③ slot label 정의(source vs summary) 혼용, ④ bootstrap 단위(문서) 미규정 |
| 2 | Stage B0가 병목 진단의 최소 실험으로 적정? DoD 충분? | **적정 (conditional)**. 20/20 + decoder LoRA + 3 seed로 "frozen decoder 병목 가설"을 검증하는 올바른 최소 실험. DoD는 방향이 옳으나 **분석 단위·통제·임계 근거가 미규정** → M3 필요 |
| 3 | B1/B2 순서·통제·factorial 분리 충분? | **순서·통제는 옳음 (agree)**. 단, layer index의 모델 간 의미 동일성 가정을 명시하고, B2의 generation 기준을 수치로 사전등록해야 함 |
| 4 | 계획의 최상위 방법론 결함? | M1~M5 (§5): ① LoRA attach 0-모듈 리스크, ② layer19 anchor의 해석 불가성 + 단일 layer STOP 과대일반화, ③ shuffle 통제 설계(길이 혼재·1-permutation), ④ Δzero degenerate, ⑤ 분석 단위·다중성 미규정 |
| 5 | Stage A를 EG2 네이티브 tokenizer로 재실행해야 하나? | **조건부 예**. 먼저 ID 일치율을 측정(E1, ~10분)하고, 기본 권고는 **role probing과 Stage B 전에 네이티브 재캐시(~7분)**. Stage A는 screening으로 유지(재판정 금지) |
| 6 | STOP / NARROW / CONTINUE? | **CONTINUE (조건부)** — M1·M2 선행, B0 통과 시 B1, Stage C 제외, 상한 ~12 CPU-h |

---

## 3. §13 Q1~Q10 항목별 판정

각 항목: **판정 → 근거 → 다음 단계(1~3개)**.

### Q1. Layer role probing의 설계 — **conditional**

**근거**

- 4 probe(surface frequency / numeric·date / slot overlap / sentence position)는 요청한 4개 정보 축을 커버한다. linear probe + 문서 내 label permutation 통제 + 문서 단위 분할은 §5.1이 스스로 규정한 "접근성 측정" 목적에 적합하다. **causal ablation 선행은 불필요**하다 — B1의 layer 교체가 이미 인과적(브릿지 인터페이스 수준) 비교이고, head 단위 ablation은 현재 CPU 예산 대비 정보가 낮다.
- 결측 ①: **문서 식별/검색가능성 probe**. Stage A의 관측 실패는 "decoder가 memory의 문서를 구분하지 못함"이다(§1.2, D-110/D-111). layer별 pooled 표현으로 own-doc vs other-doc 유사도(retrieval AUC)를 재면, 어떤 layer부터 문서 판별 정보가 선형 접근 가능한지 직접 잰다. 이것이 4 probe 중 가장 결정력 있는 추가다.
- 결측 ②: **다중성 통제**. 23 layer × 4 probe = 92개 검정에서 "최소 1개 probe에서 selectivity > 0"(§5.4 DoD)은 우연으로도 거의 충족된다. primary probe 사전등록(slot overlap, numeric·date) + 나머지 BH-FDR이 필요하다.
- 결측 ③: slot overlap 정의(§5.3)가 `extract_slots(summary)`의 slot 문자열을 source token span과 대응시킨다. 이는 "source에 있는 slot"과 "요약이 실제 쓴 slot"을 혼용한다. `eval.slot_verify.extract_slots`는 source에 직접 적용 가능하며(verify_summary가 그렇게 쓴다), **source 추출을 primary**, summary∩source를 secondary로 분리 권고.
- 결측 ④: bootstrap 단위 미규정 — 문서 내 token 상관 때문에 **문서 단위 cluster bootstrap**이어야 한다. token-level bootstrap은 분산을 과소추정한다. 또한 class-weighted accuracy에 더해 **AUC 병기**, probe 자체 재적합 2 seed 권고.
- 보조 제안: char-type(한글/라틴/숫자/구두) probe는 NER 부재(§5.6 인정)의 부분 대체로 저렴하다. 숫자는 "포함 여부" 이진만으로는 값 보존을 못 재므로 값 회귀(가능하면) 추가. layer0을 calibration baseline으로 포함.

**다음 단계**

1. `runner/c5_eg2_layer_role_probe.py` 설계에 **doc-identity retrieval probe**(layer별 pooled AUC)를 primary로 추가한다.
2. primary probe(slot overlap, numeric·date)를 사전등록하고 나머지에 BH-FDR을 적용한다. bootstrap은 문서 단위로 명시한다.
3. slot label을 source passage 직접 추출로 정의하고, summary 기반 정의는 secondary로 라벨링한다.

### Q2. Stage A의 해석 — **conditional**

**근거**

- "frozen decoder 병목"은 **가설**이며 확립된 결론이 아니다. 근거: 5문서/1 seed, permutation 1회(F5), per-doc 값 부재로 CI 불가(F7), 단일 seed 변동(max .189)이 B0 임계(0.10)보다 크다.
- 동시에 **검출력 부족 가능성이 유력**이라는 판단은 타당하다: mT5 mean Δshuffled .0366(F2)은 완전한 0은 아니지만(18/23 양수 — 길이 불일치 효과 가능성 포함), 내용 선택성 주장에는 1~2 순위 작다. UMT5는 mean .0013으로 사실상 0.
- 확실한 부분: real < zero는 견고하다(존재/길이 사용). 단 F1(zero CE 상수) 때문에 Δzero의 크기 자체는 off-manifold 아티팩트이지 "memory 의존도" 척도가 아니다.

**다음 단계**

1. B0 보고서에 "Stage A는 병목을 증명도 반증도 않았다; B0가 그 검정이다"를 명시한다 (D-110/D-111 문구 유지).
2. Stage A JSON에 per-doc delta를 저장하도록 runner를 고치고(하위호환 필드 추가), 이후 모든 probe에서 기록한다.
3. (선택, ~4분) 네이티브 캐시에서 layer19·17·12 3개만 재측정해 screening 순위의 민감도를 확인한다.

### Q3. Stage B0의 단일 layer 선택 — **conditional**

**근거**

- B0의 목적이 "decoder adaptation이 병목인가"라면 **성공 분지는 1 cell로 충분**하다(존재 증명). 문제는 **실패 분지**다: §11의 "B0: Δshuffled ≤ 0 또는 CI lower ≤ 0 → STOP"은 단일 layer(layer19)의 실패를 "bridge 전체 종료"로 일반화한다. layer19이 나쁜 layer였을 가능성(아래)과 구분되지 않는다.
- layer19 anchor의 근거가 약하다: ① Stage A 자체가 "layer별 real CE 차이를 내용 사용성 순위로 해석할 수 없다"고 결론냈다(D-110/D-111, 보고서 §5). ② F3(r=.813) — real CE 산포의 상당 부분이 최적화 노이즈. ③ F4 — layer마다 adapter init seed가 달라 layer 효과와 init 효과가 혼재. layer19 선택은 "Stage A 1위"라는 관행적 연속성일 뿐, 정보상 근거는 없다.

**다음 단계**

1. B0를 **2-cell**로: layer19(primary) + layer5(confirmatory, cosine 최고 layer). 실행 추가 비용 ~15~25분뿐이다. 대안(최소 변경): 단일 layer 유지 + "실패 시 layer5 1회 confirmatory 후 STOP"을 사전등록.
2. B0 runner에 LoRA attach assert를 넣는다 (M1).
3. stop-rule 문구를 "layer19(및 confirmatory layer)에서 LoRA로도 selectivity 없음 → 이 layer 집합에서의 bridge 기회 낮음"으로 한정한다.

### Q4. DoD — **conditional**

**근거**

- `mean Δshuffled ≥ 0.10` + paired bootstrap CI lower > 0 + 3 seeds 양수는 **방향이 옳은 primary**다. 그러나 ① **분석 단위 미규정**: 3 seed × 20 문서 = 60개 paired diff를 어떻게 모으는지(풀링 vs per-seed 판정) 미정. ② **bootstrap 단위**: 문서 단위 cluster이어야 한다. ③ **임계 근거**: Stage A의 단일 seed 변동(.189)이 0.10보다 크다 — 임계가 noise 대비 어디에 놓이는지 명시 필요(CI + 방향률이 체계성을 걸러주므로 0.10 유지 가능). ④ **통제 부족**: shuffled memory는 이웃 문서 것으로 **길이·내용이 동시에** 바뀐다. 길이 매칭(동일 길이 이웃 또는 절단) + **문서 내 token 순서 permutation**(내용 유지·순서 파괴) 통제를 추가하면 "내용" 선택성을 분리할 수 있다. ⑤ Δzero는 F1 때문에 **진단용으로 강등**하고, 대신 **mean-memory 통제**(train memory들의 평균 — in-distribution, 내용 무관)를 secondary로.
- 20문서/100 step/3 seeds: 진단 목적에는 충분하다. 더 강한 기준 불필요. 약한 기준(방향률 없음, 문서 bootstrap 아님)은 위험하다.

**다음 단계**

1. **DoD v2 사전등록**: pooled 60 paired diff, 문서 cluster bootstrap 95% CI, per-doc 방향률 ≥ 2/3, 3 seeds 전부 양수, 길이 매칭 + within-doc permutation 통제 병기.
2. 고정 하이퍼를 명시한다: rank 8 / alpha 16 / dropout 0.05 / lr 3e-4(`runner/c5_b1d_b2.py:184,195,196`의 B2 선례) + adapter·LoRA 파라미터 그룹별 lr 기록.
3. generation을 5문서 → **val 20문서 전체**로 확장하고, config manifest(seed, lr, rank, feature_dir, **tokenizer hash**, checkpoint hash)를 기록한다 (3-AI M6 재발 방지).

### Q5. B1 layer set — **agree**

**근거**

- 5/9/12/19 근거 서술은 각각 출처가 있고(§8.2), layer12의 "T5Gemma2 free-running 최고"는 D-109의 범위 정정(teacher=T5Gemma2 encoder)과 일관되게 **descriptive**로만 읽으면 문제 없다.
- 6/8/10/11 추가는 불필요하다: all-layer sweep에서 5~11이 plateau(.7883~.7927, `all_layers_pretest.json`)이고 decoder 측에는 layer 구조 증거가 없다(Stage A). 추가한다면 **early-layer 대비로 layer2 또는 3** 1개가 유읊다("early layer 약세" 가설의 decoder 측 검증).
- 4 layer × 3 seeds는 과도하지도 부족하지도 않다(실행 30~60분 추정 자체가 합리적).

**다음 단계**

1. layer 집합 유지 (선택: layer2 대비 cell 추가 시 사전등록으로).
2. B1의 best-layer 판정도 pooled seeds + 방향률 규격(B0 DoD v2)을 따른다.
3. B1 보고서에 role probing 결과를 "해석 보조"로만 사용한다는 §4 원칙 유지.

### Q6. B2 model comparison — **conditional**

**근거**

- 같은 layer에서 두 모델을 비교하는 설계는 **인터페이스 위치를 고정한 model 효과 분리**로서 옳다(§9.2의 "다른 layer 배정 금지" 원칙 동의). 단, 서로 다른 사전학습에서 같은 인덱스가 같은 역할이 아니므로 결론 표기를 "같은 인덱스에서의 model 효과"로 한정해야 한다.
- 절대 CE 비교 금지(§9.3)는 옳다. generation 중심 비교가 "더 적절"한가? — **20문서 F1/EOS는 분산이 커서 primary로는 부적합**하다. Δshuffled(모델 내부 대비, tokenizer 불변)를 primary로 유지하고 generation을 **사전등록된 수치 임계의 tiebreak**로 두는 것이 순서다.

**다음 단계**

1. B2 DoD에 generation 임계를 수치로 사전등록 (예: EOS ≥ mT5+10%p, 그리고 F1 차이 CI가 배제되지 않을 때만 우세 판정).
2. (선택) UMT5를 **자체 Stage A 상위 layer**(예: 12)에 넣는 supplementary cell — "model+layer joint"로 명확히 라벨링하고 factorial 주장에는 사용하지 않는다.
3. 두 모델 동일 adapter 구조·lr·rank·seed 유지.

### Q7. Stage C 진입 — **conditional (사실상 defer)**

**근거**

- B2 통과 후 300문서 진입은 "selectivity 확인 → 제품 기준 확인" 순서로 논리적이다. 그러나 20문서 실험은 300문서 제품 행동을 예측할 수 없고(§12.1 스스로 인정), **metric audit이 먼저**다(Q8). Stage C는 이 계획 승인과 별개의 decision record가 필요하다(§10도 "제품 후보 승인 아님"으로 스스로 규정).
- "B1에서 20문서 generation만으로 중단": selectivity가 없다면 그 전에(B0 또는 B1) 중단하는 것이 계획의 중단 규칙상 옳다.
- A1 native 비교: **baseline은 이미 고정**되어 있다(matched val100 .6552 / 100% / 100%, val161 .6576, preservation .4446). 새 A1 run은 불필요 — Stage C 전 비교는 "보고"의 문제지 "실행"의 문제가 아니다.

**다음 단계**

1. Stage C를 본 계획 승인에서 제외하고, 진입 조건 3개(B0~B2 selectivity + metric audit 완료 + 별도 decision)를 문서화한다.
2. B0~B2 보고서에 val20 F1을 항상 병기해 A1과의 격차를 조기 추적한다.
3. Stage C DoD(F1 ≥ .45, grounded ≥ 50%, EOS ≥ 60%)는 metric audit 이후 재검토한다.

### Q8. Metric — **agree (수정안 동반)**

**근거**

- `grounded`가 no-new-only라는 것은 코드로 재확인됐다(F10, `runner/c5_b1d_generate.py:147`) — 요청서 §2.4/§12.4의 서술과 일치하고 3-AI M1과 동일 결론이다.
- **수정 비용이 사실상 0**이다: `eval.slot_verify.verify_summary`는 이미 `slot_preservation`과 `new_slot_rate`를 계산해 반환하고, A1/B2 runner가 이미 import한다. production 파일 수정 없이 **보고 계층**에서 grounded_no_new / grounded_strict(preservation 포함)를 이중 표기할 수 있다.
- entity audit(한국어 고유명사 커버리지, 3-AI M2)은 제품 주장 전 필수이며, `c5_human50_*` 인프라(D-085 사전등록)를 재사용할 수 있다. B0~B2 screening의 게이트로는 필요 없다.
- Stage C DoD의 F1/grounded/EOS 3종은 preservation·new-slot micro·rep4·genlen·vacuity 보완이 필요하다.

**다음 단계**

1. (무훈련, 기존 artifact 재집계) metric audit 보고서: A1 pilot300 + bridge val100에 대해 no-new/strict/preservation/vacuity를 재집계한다 (3-AI 우선순위 1과 동일).
2. 이후 모든 F5 보고에 grounded 이중 표기 + preservation 병기를 표준으로 채택한다.
3. Stage C 이전에 entity audit 표본 설계(human50 프로토콜 연계)를 확정한다.

### Q9. T5Gemma2 재개 — **agree**

**근거**

- D-108 3/3 STOP의 근거(A1 .6552/100/100 vs bridge 최고 .4074/12/69, slot repair grounded-100 상한 .3203, F1 격차 Δ −0.2478 CI [−0.2773, −0.2192], McNemar p≈1e-14)는 압도적이고, 재개 요건(비용 동기 정량화 + 새 decision record + NARROW 승인)이 명문화되어 있다. 유지가 옳다.
- external K/V projection 분리와 A1 encoder hidden teacher, layer5 B2 미시도는 **종료 판단의 미검증 잔여 사항**으로 기록만 하고 재개하지 않는다 — "STOP이 인과적으로 완전하다"는 주장이 아니라 "재개 가치가 현재 증거로는 없다"는 판단이다.
- 주목할 점: B0의 decoder LoRA가 (M1 수정 후) **cross-attention q/k/v/o를 포함**하면, "external K/V 적응" 가설의 저계수(low-rank) 버전을 mT5/UMT5에서 자연히 검증하게 된다. T5Gemma2를 열지 않고도 같은 메커니즘 질문의 일부를 담는다.

**다음 단계**

1. D-108 STOP 유지를 본 검토에서 재확인으로 기록한다.
2. 미시도 3종(external K/V 분리, A1 hidden teacher, layer5 B2)을 "재개 시에만 고려" 목록으로 유지한다.
3. B0 결과가 selectivity를 보이면, 그것이 decoder-side 적응 가설의 지원 증거가 되도록 보고서에 연결한다.

### Q10. 우선순위 — **conditional**

**근거**

- role probing과 B0는 독립(§4)이므로 병렬 실행이 맞다. 둘 다 CPU-bound 소규모(1~2h vs 2.5~3.5h)이며, 6-thread 설정(`torch.set_num_threads(6)`) 기준 동시 실행도 수용 가능하다.
- 직렬이라면 **B0 먼저**다: B0가 분기 결정권(STOP/진행)을 갖고 role probing은 해석 보조이기 때문(§4 원칙도 B0 우선과 양립).
- 단, 병렬이든 직렬이든 **M1·M2가 B0의 선행 조건**이다.
- 가장 먼저 삭제/후순위: **Stage C**(제외), **B2**(B1 후로), role-probe의 2-layer MLP 비교와 1000-bootstrap(필요 시 후순위, 1~2h 예산 유지).

**다음 단계**

1. 실행 순서 확정: E1(tokenizer 감사) → [병렬] role probing ∥ B0 → (B0 pass) B1 → (B1 후) B2 → (조건 충족 시 별도 decision) Stage C.
2. 각 단계 직후 stop-review(B0 직후, B1 직후)를 명시한다.
3. Stage C 관련 작업은 이번 승인 범위에서 제외한다.

---

## 4. 요청서 §15 판정 — CONTINUE의 7가지 조건 답변

1. **가장 먼저 고쳐야 할 방법론적 결함**: 실행 계층 결함으로는 **M1(LoRA attach 네이밍 — mT5/UMT5에서 0개 모듈 attach 시 B0~B2 전체가 adapter-only 재현이 되어 무효)**. 실험 설계 결함으로는 **M3/M4(단일 layer 실패의 과대 일반화 + 분석 단위·통제 미규정)**.
2. **가장 먼저 실행할 실험 1~2개**: (a) **E1 tokenizer ID 일치율 감사**(무훈련 ~10분, Q5를 데이터로 종결) → (b) **수정 DoD의 Stage B0**(layer19 primary [+layer5 confirmatory]).
3. **삭제/후순위**: Stage C 제외(별도 decision), B2는 B1 후로, role-probe MLP 비교·bootstrap 1000회는 후순위 축소.
4. **DoD·중단 수정안**: §3 Q3·Q4 참조 — 요약: pooled 60 paired diff, 문서 cluster bootstrap, 방향률 ≥ 2/3, 길이 매칭 + within-doc permutation 통제, Δzero 강등→mean-memory 통제, B0 실패 시 confirmatory 1 cell 후 STOP, B1은 pooled 기준, 공통 규칙에 "길이 매칭 통제에서도 Δ≤0이면 selectivity 부정" 추가.
5. **tokenizer 불일치 처리**: 측정(E1) → 네이티브 재캐시(role probing·B0~B2 모두 동일 캐시) → Stage A는 screening errata로 유지 → **두 캐시를 어떤 분석에도 혼용 금지**(층 간 순위 비교 포함).
6. **최대 허용 비용**: 계획 자체 추정(role probing 1~2h + B0 2.5~3.5h + B1 2~3h + B2 1~2h = 6.5~10.5h) + 재캐시 ~0.5h → **상한 12 CPU-hours**. B0 직후·B1 직후 stop-review 필수. Stage C는 별도 예산.
7. **A1 native와의 관계**: A1 native pilot300은 **동결된 fallback/reference이지 승인 제품이 아니다**(D-108). 모든 신규 보고에서 A1 수치(.6552/100/100, preservation .4446)를 별도 섹션·표로 병기하고 bridge 탐색 수치와 절대 혼용하지 않는다. 승격 판단은 metric audit + 별도 decision 이후에만.

---

## 5. Must-fix 목록 (우선순위)

| # | Must-fix | 등급 | 근거 |
|---|---|---|---|
| M1 | B0/B1/B2 runner의 LoRA attach를 T5 계열 네이밍(`q/k/v/o`)으로 수정하고 **attach 모듈 수 assert**(mT5-small 예상 64 = 8 decoder block × self+cross × 4) + provenance에 모듈 목록 기록 | **Blocker** | F9 (`c5_b1d_b2.py:38,41`). 미수정 시 계획 전체가 조용히 adapter-only 재현이 된다 |
| M2 | EG2 네이티브 vs T5Gemma2 tokenizer **ID 일치율 측정**(50~100문서) 후 네이티브 재캐시; 캐시 혼용 금지 | **High** | F8, 요청서 §3.4·§12.5 |
| M3 | B0 DoD v2 사전등록(분석 단위·bootstrap 단위·방향률·통제 2종·Δzero 강등·generation 20문서·하이퍼 고정·manifest) | **High** | F1·F5·F6·F7, §3 Q4 |
| M4 | B0 stop-rule 범위 수정(단일 layer 실패 → confirmatory 1 cell 후 STOP; 결론 문구 한정) | **High** | F2·F3·F4, §3 Q3 |
| M5 | role probing 통계 규격(primary 사전등록, BH-FDR, 문서 cluster bootstrap, AUC, probe 2 seed) | **Medium** | §3 Q1 |
| M6 | 보고 위생 유지: exploratory bridge 수치와 A1 native fallback 수치 분리 표기, gate 사후 변경 없음, test 163 봉인, metric 이중 표기 | **Medium** | D-108, F10, F13 |

---

## 6. 추가 실험 제안 (계획 외, 우선순위)

| # | 실험 | 비용 | 근거·기대 |
|---|---|---|---|
| E1 | tokenizer ID 일치율 감사: 50~100문서를 두 tokenizer로 tokenize해 위치별 ID 불일치율·길이 차이 보고 | ~10분, 무훈련 | Q5의 유일한 데이터 기반 종결. 불일치율이 낮으면 재캐시 논쟁 종료, 높으면 M2 실행 |
| E2 | 문서 식별/검색가능성 probe: layer별 pooled 표현의 own-doc vs other-doc retrieval AUC | probing에 +~30분 | Stage A 실패 양상("문서 구분 불가")의 직접 측정. layer 선택 해석력을 가장 올린다 |
| E3 | (선택) adapter 통과 후 접근성 probe: 후보 layer의 adapter 출력에 동일 probe 적용 | 소액 | 브릿지 실제 입력의 접근성 측정. 단, adapter가 소규모 학습이라 과적합 편향 주의 |
| E4 | (선택) B0 체크포인트로 val20 teacher-forced vs free-running의 slot 보존 비교 | 소액 | CE 통제만으로 안 보이는 생성 측 내용 사용성 조기 신호 |

---

## 7. 확인된 금지 사항 (본 검토의 준수 선언)

- test 163: 열람·사용 없음 (분할 크기 메타데이터만 확인). 어떤 제안에도 사용하지 않는다.
- P1 데이터·외부 API: 사용하지 않는다.
- T5Gemma2 bridge: D-108 STOP 유지. 새 decision record 없이는 어떤 제안도 재개로 읽지 않는다.
- gate 사후 변경: 없다. Stage C·승격·재개는 별도 decision.
- `eval/slot_verify.py`: 미수정 (SHA256 재확인 일치).
- A1 native = 동결된 fallback/reference. 승인 제품으로 표기하는 문구를 어떤 제안에도 넣지 않는다.

---

## 8. 본 검토의 한계

- 실행·재측정 불가 환경(§1.2) — 수치는 provenance JSON·보고서·decision record의 교차 확인이며, 원본 데이터·가중치 접근은 없었다.
- F9의 HF 네이밍 판단은 설치된 라이브러리 검증 없이 소스 관례 + 간접 증거 기반. M1의 assert로 실행 시점에 확정된다.
- EG2 PLE 구조·네이티브 tokenizer 파일은 문서 기술을 신뢰했다(로컬 파일 부재).

---

*독립 검토 라운드(GLM 5.3 Flash). 이 파일 외 어떤 저장소 파일도 변경하지 않았다.*
