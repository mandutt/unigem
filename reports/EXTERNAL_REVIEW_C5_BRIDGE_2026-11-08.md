# C5 EG2 → T5Gemma2 bridge — 외부 AI 검토요청서

- 작성일: 2026-11-08 (KST)
- 프로젝트: `unigem` / F5 중요정보 요약
- 대상: EG2(EmbeddingGemma 2) → T5Gemma2 bridge
- 기준 commit: **`ee084af`** (`origin/main` 0/0)
- 데이터 등급: **P0(공개·합성)만 사용**
- test split: **163건 sealed, 미사용**
- 목적: 지금까지의 bridge 실측·연구 결과를 독립적으로 검토하고, **중단/축소/추가 실험**을 판정

---

## 0. Reviewer instructions

당신은 이 프로젝트와 무관한 독립 reviewer입니다.

- 아래 문서 **만으로** 판단하십시오. 문서에 없는 수치·맥락을 추정하지 마십시오.
- 수치가 상충하면 **명시적으로 지적**하십시오.
- “좋아 보인다” 식의 총평보다, **증거 → 해석 → 반증 가능성** 순서로 판정하십시오.
- 제안은 **실행 가능한 실험 1~2개**로 제한하고, 각 실험에 **DoD·예상 비용·중단 조건**을 붙이십시오.
- test 163 사용, gate 사후 변경, P1 데이터·외부 API 사용은 **금지**입니다.
- 현재 환경은 **CPU only**(Ryzen 5 7600, 6C/12T, 15.6GiB)입니다.

요청하는 최종 출력:

1. **Bridge viability verdict**: `STOP` / `CONTINUE` / `NARROW`
2. Q1~Q12 답변
3. 이슈 표: severity(Critical/High/Medium/Low), evidence, fix
4. 다음 실험 **최대 2개**와 각각의 DoD·예상 시간·중단 조건
5. 문서 내 수치·비교의 오류 또는 누락

---

## 1. Executive summary

### 1.1 목표

F5는 문서 → **추상 요약**을 생성하는 과제다. 원래 목표는
**EG2를 상주 인코더로 재사용**하고, EG2 표현을 T5Gemma2 decoder에 연결하는
**bridge**를 학습하는 것이었다.

### 1.2 현재 결론

**bridge는 A1 native를 대체하지 못했다.**

| system | val100 char F1 | grounded | EOS | 비고 |
|---|---:|---:|---:|---|
| **A1 native** | **0.6552** | **100%** | **100%** | bridge val100과 동일 ID; val161은 .6576 |
| B2 full 1,293 | 0.3128 | 15% | 55% | val100 subset; val161은 .3349/18.01% |
| B2 layer12 300 | 0.3464 | 21% | 60% | layer12 기준 |
| B2 layer9 300 | 0.3340 | 22% | 55% | bridge 최고 grounded |
| B2 layer12 SS | 0.3783 | 10% | 59% | F1/rep4 개선 |
| **B2 layer12 SS slot-aware** | **0.4074** | **12%** | **69%** | bridge 최고 F1 |

- bridge 최고 F1은 **0.4074**, grounded **12%**
- bridge 최고 grounded는 **22%**(layer9, F1 **.3340**), layer12는 **21%**(F1 .3464)
- A1 native는 **0.6552 / 100% / 100%**
- slot repair로 grounded 100%를 강제하면 **F1 상한 0.320**

### 1.3 판정

사전 등록한 DoD:

| 지표 | 기준 | slot-aware SS |
|---|---:|---:|
| val100 F1 | ≥ 0.36 | **0.4074 PASS** |
| grounded | ≥ 20% | **12% FAIL** |
| EOS | ≥ 58% | **69% PASS** |

→ **SLOT_AWARE_SS_DOD_FAIL_GROUNDED**  
→ 사전 등록대로 **bridge 계열 종료**, **A1 native 제품 경로**로 전환.

**검토 핵심 질문**: 이 종료 판정이 타당한가?  
아니면 copy/slot auxiliary 같은 마지막 직접 수단을 **새 트랙으로 승인**할 근거가 있는가?

---

## 2. 과제·데이터·평가 프로토콜

### 2.1 과제

- 입력: 한국어 뉴스/리포트 문서
- 출력: **추상 요약**
- 핵심 제약: 요약의 숫자·날짜·금액·고유명사 등 **slot이 source에 존재해야 함**
- 목표 품질: `grounded`와 `char F1`을 동시에 확보

### 2.2 데이터

| 항목 | 값 |
|---|---:|
| 원본 v3 | 2,000 |
| clean(primary) | **1,617** |
| repaired | 1,953 |
| split (seed 42) | **train 1,293 / val 161 / test 163** |
| test | **sealed, 미사용** |
| bridge train subset | **300** |
| bridge val subset | **100** (val 앞 100건) |

- clean 데이터는 **grounding 100%, 신규 slot 0**으로 정제된 것
- **G-C5 제품 gate**: grounding ≥99% + 신규 slot ≤1%
- test 163은 **어떤 실험에도 사용하지 않음**
- P1(개인) 데이터·외부 API는 사용하지 않음

### 2.3 평가 지표

| 지표 | 정의 |
|---|---|
| `char F1` | prediction vs gold summary character-level F1 |
| `teacher char F1` | prediction vs A1 native teacher output |
| `grounded` | `eval/slot_verify.py` 기준 source slot 보존 + 신규 slot 없음 |
| `EOS` | EOS token 생성 여부 |
| `rep4` | repeated 4-gram rate (낮을수록 좋음) |
| `new slot micro` | 신규 slot / 전체 summary slot |
| `slot preservation` | source slot 보존율 |
| `hidden cosine` | adapter 출력 vs teacher hidden의 token cosine |

### 2.4 주의

- bridge의 **val100**은 val 161건 중 앞 100건이다.
- A1 native의 원 보고는 **val161** 기준(.6576)이지만, 비교를 위해
  **bridge val100과 동일한 100개 ID**로 재계산하면 **.6552**다.
  같은 val의 앞 100건 기준(.6506)과는 다른 값이므로 혼동하지 말 것.
- B2 full의 원 보고는 **val161**(.3349/18.01%)이고,
  동일 앞 100건은 **.3128/15%**다.
- 따라서 **val100 표와 val161 표를 섞어 해석하면 안 된다.**

---

## 3. 구조

### 3.1 Bridge 정의

```text
문서
  → EG2 (frozen)
  → token features (512 or 768)
  → adapter (trainable)
  → T5Gemma2 decoder (frozen + decoder LoRA, trainable)
  → summary
```

- **bridge = adapter만**을 의미하는 좁은 정의도 사용한다.
- **B2 = adapter + decoder LoRA**다.
- **A1 native = T5Gemma2 encoder + LoRA**다. EG2를 사용하지 않는다.

### 3.2 EG2 feature

| feature | 차원 | 비고 |
|---|---:|---|
| final hidden | 768 | retrieval/embedding objective |
| layer12 | 512 | 중간 layer |
| layer9 | 512 | 중간 layer, sweep 최고 |
| layer6 | 512 | 중간 layer |
| concat(layer12+final) | 1280 | concat pretest에서 기각 |

- `summarize: ` prefix 포함
- T5 tokenizer 기준 token alignment **1,454/1,454 = 100%**
- test 미사용

### 3.3 Adapter

`B1dFullAdapter`:

```text
input_dim (512/768/1280)
  → Linear(input_dim, hidden)
  → GELU
  → Linear(hidden, 640)
  → LayerNorm
  → scale
```

- hidden 768/1536 비교
- 출력 640 = T5Gemma2 decoder hidden size
- **T5Gemma2의 1024는 q projection/head 내부 폭**이며,
  adapter의 1024/1536은 T5Gemma2 차원이 아닌 **임의 MLP hidden**이다.

### 3.4 T5Gemma2 decoder

- text-only **370,637,824 params**
- `hidden_size 640`, `num_heads 4`, `head_dim 256`
- q: 640→1024, k/v: 640→256, o: 1024→640
- **merged attention**: 별도 `encoder_attn` 없음, `k_proj`/`v_proj` self/cross 공유
- decoder LoRA: `q_proj`, `k_proj`, `v_proj`, `o_proj`
  - r8 α16: **72 modules / 737,280 params**
  - r16 α32: **1,474,560 params** (기각)

### 3.5 Teacher

- **A1 native T5Gemma2** (encoder+LoRA)를 teacher로 사용
- teacher train100: F1 **0.6697**, grounded **99/100**, EOS **100/100**
- teacher val161: F1 **0.6576**, grounded **161/161**, EOS **161/161**
- teacher val100 subset: F1 **0.6552** (bridge val100과 동일 ID)

---

## 4. 실험 원장 (D-087 ~ D-107)

### 4.1 Bridge 복귀와 인터페이스

| ID | 실험 | 핵심 결과 | 판정 |
|---|---|---|---|
| D-087 | B1d bridge feasibility probe | token alignment **1,454/1,454 100%**; `encoder_outputs=BaseModelOutput(last_hidden_state=H_s)`로 generate 성공; teacher-hidden control은 정상 한국어; adapter-only hidden은 degenerate | **PASS_INTERFACE**, quality 미달 |
| D-088 | B1d full hidden distillation | val hidden cosine **0.0172→0.7271**; norm 1.023; MSE 0.00085; free-running **F1 .0477 / grounded 10% / EOS 0% / rep4 .792** | adapter-only 생성 실패 |
| D-089 | B1d-CE (frozen decoder) | val CE **3.9323→3.0686**; F1 **.2061**, EOS **10%**, grounded 5% | CE 필요, frozen decoder 불충분 |
| D-090 | B2 decoder LoRA pilot | LoRA 72 modules/737,280; val CE 3.2226(overfit); F1 **.2708**, EOS **40%**, grounded **0%** | 구조 개선, grounding 붕괴 |
| D-091 | usage-contrast diagnostic | train usage gap 1.936 / val .744; margin 0.5에서 **penalty 0** | decoder는 H_s를 이미 문서별로 사용; usage-contrast 병목 아님 |
| D-092 | B2 full 1,293 | val CE 3.0707→2.6341; val161 **F1 .3349 / grounded 18.01% / EOS 60.25% / rep4 .5856**; val100 subset **.3128/15%/55%** | bridge 계열 최고(당시), A1 대체 불가 |
| D-093 | B2 offline slot repair | drop-new **grounded 100% / F1 .2624 / fallback 71/161**; oracle **.2719** | post-processing은 안전 필터, F1 상한 .272 |

### 4.2 A1 teacher / target / capacity

| ID | 실험 | 핵심 결과 | 판정 |
|---|---|---|---|
| D-094 | adapter-only teacher-fidelity pilot | teacher train100 F1 .6697; adapter+frozen decoder; train CE 3.0069→2.2161/token 39.02→52.71; val CE 2.9384→2.7705/token 40.29→43.58; hidden cos .6967→.6634; val20 **teacher F1 .2333 / gold .2592 / grounded 15% / EOS 40%** | **ADAPTER_ONLY_TEACHER_FIDELITY_PARTIAL** |
| D-095 | H_s zero/shuffle + teacher bias ablation | real **2.7705/43.58**; zero H_s **6.1708/17.70**; other-doc **3.4829/34.70**; teacher hidden **0.5837/87.51**; teacher_shuffle **0.5835/87.59** | adapter content는 사용됨; teacher hidden에 크게 미달 |
| D-096 | B2 teacher vs gold matched 100 | teacher arm train 2.2161→1.3024/val 3.0095; gold arm train 2.6729→1.6723/val 2.9969; val20 teacher final **.2964**/15%/50%, gold final **.3498**/10%/75%, teacher ep1 **.3499**/10%/70% | **B2_100_TARGET_INCONCLUSIVE_EARLY_STOP_DEPENDENT** |
| D-097 | B2 gold 300 | val CE 2.9375→2.8314; teacher-forced **2.7204/44.92%**; val20 .3664(낙관); val100 **.3341/18%/67%**; copy4 .1085/leading .6254 | **DATA_SCALING_PARTIAL_GROUNDING_UNCHANGED** |
| D-098 | adapter capacity pretest | hidden cosine: linear **.6665**, MLP768 **.6998**, MLP1536 **.7102**; linear→MLP +3.33%p, MLP→wide +1.05%p | **CAPACITY_PARTIAL_DIMINISHING**; 3-arm 2시간 미실행 |

### 4.3 Feature layer / decoder capacity

| ID | 실험 | 핵심 결과 | 판정 |
|---|---|---|---|
| D-099 | EG2 layer12 512 pretest | final 768 MLP768 .6998; layer12 linear **.7424**, MLP768 **.7629**, MLP1536 **.7747** | layer12 > final; feature layer가 width보다 중요 |
| D-100 | B2 layer12 300 | val CE 3.6873→**2.2983**; teacher-forced **2.1190/56.11%**; val100 **.3464/21%/60%**; new slot .535 | **LAYER12_FEATURE_GAIN_PARTIAL** |
| D-101 | layer12 slot repair | original .3464/21%; drop-new **grounded 100%/F1 .2929**; oracle **.3076** | grounded ceiling .308 |
| D-102 | decoder LoRA r16 | val CE **2.3536**(r8 2.2983); fidelity 2.1723/54.88%; val20 **.2765/35%/45%** | **DECODER_R16_NO_GAIN**; overfit |
| D-103 | concat 1280 pretest | concat linear .7157 / MLP768 .7345 / MLP1536 .7450 vs layer12 .7747 | **CONCAT_HURTS_HIDDEN_ALIGNMENT**; B2 미실행 |
| D-104 | EG2 layer sweep | **layer9 .7910** > layer6 .7883 > layer12 .7747 > concat .7450 > final .7102 | **LAYER9_BEST_FEATURE** |
| D-105 | B2 layer9 300 | val CE **2.2201**; fidelity **1.8904/59.58%**; val100 **.3340/22%/55%**; new slot .687 | **LAYER9_FIDELITY_GAIN_NO_FREE_RUNNING_GAIN** |

### 4.4 On-policy / scheduled sampling

| ID | 실험 | 핵심 결과 | 판정 |
|---|---|---|---|
| D-106 | B2 layer12 SS | init r8; 300/100; 1 epoch; lr1e-4; **ss_prob .2**; val CE **2.2356**; fidelity **2.0335/57.46%**; val100 **.3783/10%/59%**; rep4 **.4625**; new slot .612 | **SCHEDULED_SAMPLING_F1_GAIN_GROUNDING_LOSS** |
| D-107 | B2 layer12 SS slot-aware | slot/number/EOS corruption 금지; val CE **2.2406**; fidelity **2.0339/57.51%**; val100 **.4074/12%/69%**; rep4 **.4054**; new slot .559 | **SLOT_AWARE_SS_DOD_FAIL_GROUNDED**; bridge 종료 |

---

## 5. 통합 결과

### 5.1 Hidden alignment pretest

| feature | linear | MLP768 | MLP1536 |
|---|---:|---:|---:|
| final 768 | .6665 | .6998 | .7102 |
| layer12 512 | .7424 | .7629 | .7747 |
| layer6 512 | .7582 | .7766 | .7883 |
| **layer9 512** | **.7604** | **.7798** | **.7910** |
| concat 1280 | .7157 | .7345 | .7450 |

- layer9 > layer6 > layer12 > concat > final
- **hidden alignment와 free-running은 단조 관계가 아니다.**

### 5.2 Teacher-forced fidelity

| system | train n | CE | token acc |
|---|---:|---:|---:|
| adapter-only teacher100 | 99 | 2.7705 | 43.58% |
| B2 teacher100 final | 99 | 3.0060 | 41.91% |
| B2 gold100 final | 99 | 2.8877 | 42.07% |
| B2 gold100 ep1 | 99 | 2.7673 | 43.25% |
| B2 gold300 final 768 | 300 | 2.7204 | 44.92% |
| B2 layer12 300 | 300 | **2.1190** | **56.11%** |
| B2 layer9 300 | 300 | **1.8904** | **59.58%** |
| B2 layer12 SS | 300 | **2.0335** | **57.46%** |
| B2 layer12 SS slot-aware | 300 | **2.0339** | **57.51%** |

**핵심 모순**: layer9가 teacher-forced 최고(1.8904/59.58%)인데
free-running F1은 layer12보다 낮다(.3340 vs .3464).

### 5.3 Free-running val100 (matched subset)

| system | char F1 | teacher F1 | grounded | EOS | rep4 | gen_len | new slot | preservation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A1 native | **.6552** | — | **100%** | **100%** | **.0634** | — | **0** | .4446 |
| B2 full 1,293 | .3128 | — | 15% | 55% | .6201 | — | — | — |
| B2 layer12 300 | .3464 | .3392 | **21%** | 60% | .588 | 309.6 | .535 | .2512 |
| B2 layer9 300 | .3340 | .3239 | **22%** | 55% | .5755 | 315.3 | .687 | — |
| B2 layer12 SS | .3783 | .3696 | 10% | 59% | .4625 | 312.9 | .612 | .3618 |
| **B2 layer12 SS slot-aware** | **.4074** | **.4020** | 12% | **69%** | **.4054** | 286.4 | .559 | **.3656** |

- SS/slot-aware는 **F1/rep4/EOS를 개선**
- 그러나 **grounded가 21% → 10~12%로 하락**
- layer9는 grounded 22%로 최고지만 F1/EOS가 낮다.

### 5.4 Slot repair ceiling

| source | original F1/grounded | drop-new F1 | oracle F1 | preservation |
|---|---:|---:|---:|---:|
| B2 full 1,293 (161) | .3349 / 18.01% | .2624 | .2719 | .1200 |
| B2 layer12 100 | .3464 / 21% | .2929 | .3076 | .1424 |
| B2 layer12 SS 100 | .3783 / 10% | .3165 | .3180 | .1518 |
| B2 layer12 SS slot 100 | .4074 / 12% | .3159 | **.3203** | .1621 |

- 문장 단위 slot repair로 grounded 100%는 가능
- 그러나 **F1 상한 .320**; A1 native .6552의 절반 이하
- repair는 안전 필터이며 생성 품질을 만들지 못한다.

### 5.5 Ablation

D-095, val100 teacher-forced:

| condition | CE | token acc |
|---|---:|---:|
| real H_s | **2.7705** | **43.58%** |
| zero H_s | 6.1708 | 17.70% |
| other-doc H_s | 3.4829 | 34.70% |
| teacher hidden | 0.5837 | **87.51%** |
| teacher_shuffle | 0.5835 | 87.59% |

- adapter content는 실제로 사용됨(zero/other-doc 악화)
- 그러나 teacher hidden과의 격차가 큼
- token_shuffle은 teacher도 동일 → shuffle 자체가 유효한 causal ablation이 아님

---

## 6. 연구 가설과 증거

### H1. EG2 final layer의 정보 병목

**증거**

- final 768 hidden cosine .7102
- layer9 .7910, layer6 .7883, layer12 .7747
- concat .7450 (final을 붙이면 오히려 악화)

**판정**: **부분 지지**. 중간 layer가 더 좋다.  
**반증**: layer9가 free-running에서 layer12보다 나쁘다.

### H2. adapter capacity 부족

**증거**

- linear .6665 → MLP768 .6998(+3.33%p)
- MLP768 → MLP1536 .7102(+1.05%p)
- concat MLP1536 .7450

**판정**: capacity는 필요하지만 **diminishing**.  
**반증**: B2 decoder r16은 오히려 악화.

### H3. Decoder capacity/rank 부족

**증거**

- r16: val CE 2.3536 vs r8 2.2983
- teacher-forced 2.1723/54.88% vs 2.1190/56.11%
- val20 F1 .2765 vs .3623

**판정**: **기각**. rank는 병목이 아니다.

### H4. Exposure bias / teacher-forcing mismatch

**증거**

- teacher-forced 56~59% vs free-running F1 .33~.41
- SS가 F1/rep4를 개선했지만 grounding은 악화
- slot-aware SS도 grounded 12%

**판정**: **부분 지지**. free-running 행동은 별도 문제다.  
**미해결**: true on-policy KD(생성 prefix에 teacher distribution)는 아직 하지 않았다.

### H5. Grounding/copy 병목

**증거**

- grounded 21~22%가 layer12/layer9의 최고
- slot repair 상한 .320
- new slot .535~.687

**판정**: **강하게 지지**. 현재 decoder는 slot을 source에서 복사하지 않고 생성한다.

### H6. Teacher target / distillation

**증거**

- teacher100 vs gold100 matched: val20 gold final .3498, teacher final .2964
- teacher target이 일관되게 낫지 않음
- teacher bias copy4/leading40가 student로 전이

**판정**: **teacher output KD의 이득 없음**.  
**미해결**: stronger LLM teacher는 별도 트랙(비용/P0).

---

## 6.5 외부 문헌 단서 (Exa 검색)

reviewer의 해석을 돕기 위한 참고이며, 프로젝트의 실측은 아니다.

| 출처 | 단서 |
|---|---|
| Zero to Frontier | `I(Y;g(f(x))) ≤ I(Y;f(x))` — projector는 encoder가 버린 정보를 복원할 수 없다 |
| Rethinking Projector Training | projector 데이터 10~20%로 downstream 대부분 회복, **coarse alignment** 담당 |
| Don't Throw Away Data | teacher가 student보다 너무 크면 capacity curse, weak→strong staged |
| Memorization Inheritance | sequence KD가 hallucination/ExMem 악화 → slot filter 필요 |
| Audio-Native Speech ASR | frozen decoder에서 **projector–attention deadlock**, CTC auxiliary로 돌파 |
| ByteKaz | Stage A adapter → Stage B attention-only |
| T5Gemma 2 | 1B-1B distillation +0.4점 후 **drop**; merged attention |
| Deep decoder NMT | train ppl 낮은데 translation 급락, decoder가 source 무시 가능 |
| Cosine Misleads | cosine vs accuracy **r=−0.94**, latent 제거해도 accuracy 4점 이내 |
| PLATE | teacher pseudo summary **copy4 56% vs ref 15%**, leading 40% 문장 74% vs 64% |
| Cross-Attention is All You Need | T5 XA-only 13.7% params로 F1 0.8128 vs full 0.8162 |
| BLIP-2 / Q-Former | 32 learned query, 2단계 progressive alignment |

**시사점**

- adapter/feature를 더 키우는 것보다 **정보 경로와 objective**가 중요할 수 있다.
- teacher-forced cosine/CE는 free-running behavior의 **proxy**일 뿐이다.
- copy/pointer 또는 slot auxiliary는 위 문헌의 **projector–attention deadlock**과
  **copy bias** 문제를 함께 검토해야 한다.

---

## 7. 지금까지의 결정

| 결정 | 내용 |
|---|---|
| D-079 | STT 동결 |
| D-080 | clean 1,617 / split 1,293/161/163 |
| D-083 | A1 full 2 epoch **gate FAIL**, pilot300 fallback, `selected_step: null` |
| D-084~086 | 평가 트랙 **INCONCLUSIVE** |
| D-087 | bridge 복귀, interface PASS |
| D-092 | B2 full 1,293, bridge 최고(당시) |
| D-093 | slot repair는 안전 필터 |
| D-100 | layer12 feature partial gain |
| D-101 | layer12 repair ceiling .308 |
| D-102 | decoder r16 기각 |
| D-103 | concat 기각 |
| D-104 | layer9 최적 feature |
| D-105 | layer9 fidelity ↑, free-running ↓ |
| D-106 | SS F1 ↑, grounding ↓ |
| D-107 | slot-aware SS **DoD FAIL**, bridge 종료 |

---

## 8. 검토 질문

### Q1. Bridge 전제

A1 native가 val100 **.6552/100%/100%**이고,
bridge 최고가 **.4074/12%/69%**다.
이 조건에서 bridge를 **STOP**하는 것이 타당한가?
STOP이 아니라면, 어떤 **단일 반증 실험**이 결론을 바꿀 수 있는가?

### Q2. 종료 판정

D-107의 DoD(F1 ≥ .36, grounded ≥20, EOS ≥58)는
**실험 전에** 등록됐고 grounded 12%로 실패했다.
이 종료가 **사후 합리화**가 아니라고 보는가?
반대로, DoD 자체가 bridge에 부적절했는가?

### Q3. SS의 해석

SS가 F1/rep4/EOS를 개선하면서 grounded를 21%→10%로 떨어뜨린 원인은 무엇인가?

- (a) gold label을 유지한 채 decoder input만 corrupt하는 방식의 한계
- (b) slot token을 보호해도 **slot 주변 문맥**이 오염됨
- (c) F1과 grounding의 **trade-off**가 본질
- (d) 측정 artifact

slot-aware가 grounded를 12%까지만 회복한 것은 **mask가 불충분**했기 때문인가?

### Q4. Layer9 역설

layer9는 teacher-forced 최고(1.8904/59.58%)인데
free-running F1은 layer12보다 낮다(.3340 vs .3464).
이것은 **300문서 overfit**인가, **feature-noise**인가,
아니면 **teacher-forced 지표의 한계**인가?
layer9로 full 1,293을 돌릴 가치가 있는가?

### Q5. 데이터 규모

현재 bridge 핵심 비교는 **300 train / 100 val**이다.
B2 full 1,293은 val161 .3349/18.01%로 300과 거의 같았다.
bridge 결론을 300문서로 내려도 되는가?
full 1,293을 layer12/SS로 다시 돌리는 것이 **정보 가치**가 있는가?

### Q6. Slot repair

grounded 100% F1 상한이 **.3203**이다.
이것은 “repair가 나쁘다”는 증거인가,
“생성 grounding이 근본 병목”이라는 증거인가?
sentence drop 대신 **slot replacement/rewrite**를 하면 F1이 더 오를 수 있는가?

### Q7. Slot auxiliary vs copy

남은 직접 수단:

- slot auxiliary head (저비용, 간접)
- copy/pointer mechanism (고비용, 직접)
- constrained decoding (중간)
- B2 full 1,293 (데이터)

우선순위와 **DoD**를 어떻게 정해야 하는가?
copy mechanism이 성공할 확률을 **사전 확률**로 얼마로 보는가?

### Q8. 평가 지표

`slot_verify`의 grounded는 **conservative**하다.
A1 native가 100%인 것은 **teacher-copy artifact**인가,
실제 품질인가?
bridge의 grounded 12%는 지나치게 가혹한가?
char F1과 grounded를 **어떻게 결합**해야 제품 판정이 가능한가?

### Q9. A1 native 제품 경로

A1 native pilot300은 val100 .6552/100%/100%다.
D-083 full 2 epoch는 gate FAIL로 `selected_step: null`이다.
제품 후보로 pilot300을 고정하는 것이 타당한가?
full 1,940/2,586 checkpoint를 재평가할 가치가 있는가?

### Q10. 비교 공정성

- A1 native는 val161 원 보고(.6576), bridge는 val100
- 우리는 A1 val100을 **bridge val100과 동일 ID로 .6552**로 재계산했다.
  같은 val의 앞 100건 기준은 .6506이다.
- B2 full은 val161(.3349), val100(.3128)
- teacher train100은 **길이 정렬 상위 100건**으로 val100과 분포가 다르다.

이 비교에 **selection bias**가 있는가?
어떤 matched control이 필요한가?

### Q11. 연구 중단 기준

bridge를 계속할 경우, **어떤 조건**에서 중단해야 하는가?
반대로 A1 native 제품화를 위해 **어떤 검증**이 필요한가?

### Q12. Must-fix

지금 문서/실험에서 **즉시 고쳐야 할** 방법론·수치·재현성 문제는 무엇인가?
우선순위 3개만 제시하라.

---

## 9. 재현 정보

### 9.1 코드

| 파일 | 역할 |
|---|---|
| `runner/c5_eg2_layer12_cache.py` | EG2 layer feature cache (`--layer`) |
| `runner/c5_layer12_pretest.py` | hidden cosine pretest (`--feature-dir`, `--input-dim`) |
| `runner/c5_b1d_b2.py` | B2 adapter+decoder LoRA, `--ss-prob`, `--ss-slot-aware` |
| `runner/c5_b1d_generate.py` | generation, layer feature 지원 |
| `runner/c5_b2_fidelity_eval.py` | teacher-forced fidelity |
| `runner/c5_b2_slot_repair.py` | offline slot repair |
| `runner/c5_teacher_bias_audit.py` | copy/leading bias |
| `eval/slot_verify.py` | grounding verifier (production, 미수정) |

### 9.2 주요 artifact

- `reports/C5_B2_LAYER12_2026-11-08.md`
- `reports/C5_B2_LAYER9_2026-11-08.md`
- `reports/C5_B2_LAYER12_SS_2026-11-08.md`
- `reports/C5_B2_LAYER12_SS_SLOT_2026-11-08.md`
- `reports/C5_EG2_LAYER_SWEEP_2026-11-08.md`
- `reports/C5_CONCAT_PRETEST_2026-11-08.md`
- `reports/provenance/C5_b1d/generation_val100_b2_layer12_300_ss_slot.metrics.json`
- `docs/decisions.md` D-087~D-107
- `reports/C5_STATUS_2026-11-06.md` §37~§50

### 9.3 대표 실행

```bash
# layer9 cache
.venv/Scripts/python.exe runner/c5_eg2_layer12_cache.py \
  --layer 9 --out-dir data/wave2c/eg2_layer9 --overwrite

# B2 layer12 SS slot-aware
.venv/Scripts/python.exe runner/c5_b1d_b2.py \
  --train-limit 300 --val-limit 100 --epochs 1 --lr 1e-4 \
  --hidden-weight 0.01 --input-dim 512 --adapter-hidden 1536 \
  --feature-dir data/wave2c/eg2_layer12 \
  --init data/models/f5_t5gemma2_lora/b2_layer12_300/adapter_final.pt \
  --target gold --ss-prob 0.2 --ss-slot-aware \
  --out-dir data/models/f5_t5gemma2_lora/b2_layer12_300_ss_slot \
  --report reports/provenance/C5_b1d/b2_layer12_300_ss_slot_metrics.json \
  --checkpoint-every 50 --no-resume
```

### 9.4 제약

- test 163 **미사용**
- P1 데이터·외부 API **미사용**
- CPU only
- gate 사후 변경 금지
- `eval/slot_verify.py` production 파일 **미수정**
  (SHA256 `a262cee0cd25307a74f3a87995624e2999b47daed9294000f036d27ea1869d03`)

---

## 10. Reviewer가 특히 봐야 할 것

1. **A1 native .6552/100% vs bridge .4074/12%** — 이 격차가 구조적 한계인지, 학습 부족인지
2. **SS의 grounding 붕괴** — F1 개선이 실제 품질인지, metric gaming인지
3. **layer9 역설** — teacher-forced와 free-running의 불일치
4. **slot repair 상한 .320** — 생성 단계에서 해결 가능한지
5. **DoD 종료 판정** — 사전 등록을 지킨 것이 맞는지, 너무 이른 종료인지
6. **300문서 결론** — 데이터 규모가 결론을 제한하는지
7. **A1 native 제품화** — pilot300 fallback이 제품 후보로 충분한지

---

## 11. 요청하는 최종 판정

다음 중 하나를 선택하고 근거를 제시하십시오.

- **STOP**: bridge를 종료하고 A1 native 제품 경로로 간다.
- **NARROW**: bridge를 축소해 **단일 반증 실험**만 한다.
- **CONTINUE**: copy/slot auxiliary를 포함한 새 트랙을 승인한다.

그리고 다음을 명시하십시오.

1. 가장 먼저 고쳐야 할 **방법론적 결함**
2. 다음 실험 **1~2개** (DoD, 예상 시간, 중단 조건)
3. 문서에서 **수치 불일치**가 있는 부분
4. bridge를 계속할 경우의 **최대 허용 비용**
5. A1 native 제품화 전에 필요한 **최소 검증**

---

*이 문서는 P0 데이터와 비밀값 없이 작성되었습니다. test 163은 봉인 상태입니다.*
