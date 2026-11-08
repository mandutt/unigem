# C5 EG2 → multilingual decoder — layer role probing 및 Stage A/B0/B1/B2 검토요청서

- 작성일: 2026-11-08
- 대상: EG2(EmbeddingGemma 2) hidden layer의 역할 분석과, mT5-small / UMT5-small decoder 연결 계획
- 상태: **계획 검토용**. test 163은 봉인. 이 문서는 P0 데이터만 사용한다.
- 직전 HEAD: `949df7a` (문서 커밋 전)

---

## 0. Reviewer instructions

이 문서는 저장소 접근 없이 읽을 수 있도록 작성됐다. 다음을 지켜 달라.

1. **수치의 기준을 구분**하라. `T5Gemma2 teacher cosine`, `mT5 CE`, `UMT5 CE`는 서로 다른 target/tokenizer를 사용하므로 **절대값을 직접 비교하면 안 된다.**
2. **실측 / 문헌 / 추론을 구분**하라. 이 문서에서 `추론`이라고 표시한 것은 검증된 사실이 아니다.
3. **test 163은 어떤 제안에서도 사용하지 말 것.** test는 최종 제품 후보가 확정된 뒤 1회만 사용한다.
4. **새 학습·평가를 제안할 때 데이터·seed·target·metric·중단 조건을 함께 제시**하라.
5. 최종 판정은 **STOP / NARROW / CONTINUE** 중 하나로 하고, 그 근거와 must-fix를 적어 달라.
6. 이 계획의 목적은 “좋은 모델 하나 만들기”가 아니라 **어느 단계에서 어떤 원인을 분리할 수 있는지**를 판정하는 것이다.

---

## 1. Executive summary

### 1.1 목표

EG2를 상주 인코더로 재사용해, 경량 다국어 decoder(mT5-small 또는 UMT5-small)에 연결할 수 있는지 판정한다.

- **제품 목표**: F5 요약 품질을 유지하면서 EG2를 재사용
- **연구 목표**: EG2의 어느 layer가 decoder memory로 유용한지, 그리고 layer 역할을 어떻게 측정할지 확립
- **확장 목표**: F4 맞춤법 교정, F6 STT 후처리, F3 비전 태깅으로 decoder를 재사용

### 1.2 현재 결론

- **T5Gemma2 bridge는 D-107/D-108에서 종료**됐다. 3-AI 검토 3/3 STOP.
  - A1 native: **F1 .6552 / grounded 100% / EOS 100%**
  - bridge 최고: **F1 .4074 / grounded 12% / EOS 69%**
  - slot repair grounded-100 상한: **.3203**
- **mT5/UMT5 Stage A**는 완료됐다.
  - mT5: 23개 layer real CE **6.623~7.469**, best layer19 **6.623**, Δzero 18.4~19.3, **Δshuffled 최대 .189**
  - UMT5: best layer12 **8.185**, Δzero 3.5~4.0, **Δshuffled 최대 .009**
  - 양쪽 모두 **real vs zero는 크지만 real vs shuffled는 거의 0** → frozen decoder는 memory의 존재/길이를 쓰지만 내용 선택성은 확인되지 않음.
- 따라서 이 계획은 **layer 역할을 측정**하고, **decoder adaptation이 병목인지**를 단계적으로 분리하는 데 초점을 둔다.

### 1.3 핵심 질문

1. EG2 layer별로 어떤 정보가 linearly accessible한가?
2. frozen decoder에서 content selectivity가 없었던 원인이 decoder adaptation인가?
3. decoder LoRA를 붙이면 content selectivity가 생기는가?
4. layer를 바꾸면 성능이 달라지는가?
5. 같은 layer에서 mT5와 UMT5의 차이가 있는가?
6. 어느 단계에서 중단해야 하는가?

---

## 2. 배경

### 2.1 EG2의 실제 구조

- 이름: EmbeddingGemma 2 (EG2)
- 기반: **Gemma 4 decoder-only → bidirectional embedding backbone**
- 24 transformer layers, `d_model=512`
- **PLE(per-layer embeddings)**: 각 layer에 입력 token embedding의 projection residual을 주입
- mean pooling → **512→768 projection** → L2 normalize
- 로컬 config: `data/models/embeddinggemma-2-f9972ac2/config.json`

#### 중요한 인덱스 사실

실제 HF `language_model(..., output_hidden_states=True)` 출력:

```text
hidden_states[0..23] = 512d
hidden_states[24]     = 768d projection
```

- **layer0**: embedding
- **layer1~23**: transformer hidden 512
- **layer24**: retrieval projection 768 — **transformer hidden이 아님**

따라서 adapter 입력 후보는 **layer1~23**이고, layer24는 bridge memory로 쓰면 안 된다.

### 2.2 EG2와 T5Gemma2의 관계 정정

- **EG2는 Gemma 4 기반**이다. T5Gemma2는 Gemma 3를 UL2로 encoder-decoder adaptation한 모델이다.
- **EG2는 T5Gemma2와 같은 encoder-decoder 계보가 아니다.**
- T5Gemma2 논문의 “EmbeddingGemma” 언급은 1세대(EmbeddingGemma, Gemma 3/T5Gemma encoder)에 해당한다.
- 따라서 “같은 계보이므로 자연스럽다”는 bridge 근거는 **철회**한다.

### 2.3 mT5-small / UMT5-small

| 항목 | mT5-small | UMT5-small |
|---|---|---|
| params | ~300M | ~300M |
| d_model | 512 | 512 |
| decoder layers | 8 | 8 |
| languages | 101 | 107 |
| license | Apache 2.0 | Apache 2.0 |
| 구조 | T5 encoder-decoder | T5 encoder-decoder |
| cross-attention | **독립** | **독립** |

- 두 모델 모두 `encoder_outputs`를 외부 memory로 받을 수 있다.
- mT5/UMT5의 tokenizer는 서로 다르므로 **target CE 절대값 비교는 금지**한다.

### 2.4 이미 확인된 제약

- test 163 sealed
- P1 데이터·외부 API 미사용
- CPU only (GPU 없음), 15.6GB RAM
- gate 사후 변경 금지
- `eval/slot_verify.py` production 파일 미수정
  - SHA256 `a262cee0cd25307a74f3a87995624e2999b47daed9294000f036d27ea1869d03`
- `grounded`는 현재 코드상 **no-new-only**이며 preservation을 검사하지 않는다.
  - 3-AI errata로 등록됨. entity audit도 미실행.

---

## 3. 기존 실측 요약

### 3.1 EG2 all-layer ↔ T5Gemma2 teacher cosine

- teacher: **base T5Gemma2 encoder hidden 640** (A1 LoRA 없음)
- train 300 / val 100, adapter linear/MLP, hidden cosine

| layer | MLP1536 |
|---:|---:|
| 5 | **.7927** |
| 8 | .7907 |
| 9 | .7910 |
| 10 | .7886 |
| 12 | .7747 |
| 2 | .7621 |
| 3 | .7704 |
| 24 projection | .7102 |

**주의**: 이 값은 **T5Gemma2 teacher alignment**이며, mT5/UMT5의 decoder 유용성이나 layer 역할을 의미하지 않는다. D-109에 범위 정정이 등록되어 있다.

### 3.2 Stage A — mT5/UMT5 direct decoder probe

프로토콜:

- EG2 layer1~23
- adapter: MLP 512→512→512 + LayerNorm
- decoder frozen, encoder bypass via `encoder_outputs`
- train 5 / val 5, 100 step, 1 seed
- real / zero / shuffled memory CE

| 모델 | best real CE | Δzero | Δshuffled 최대 |
|---|---:|---:|---:|
| mT5 | layer19 **6.623** | 18.4~19.3 | **.189** |
| UMT5 | layer12 **8.185** | 3.5~4.0 | **.009** |

**판정**: 양쪽 모두 `PARTIAL_MEMORY_USE_NO_CONTENT_SELECTIVITY`.

- real CE < zero CE: memory 존재/길이는 사용
- real CE ≈ shuffled CE: **다른 문서 memory와 구분하는 내용 선택성은 없음**
- 5문서/1 seed이므로 **탐색적**이며, 이 결과만으로 모델/layer를 확정하지 않는다.

### 3.3 T5Gemma2 bridge의 종료된 결과

| system | val100 F1 | grounded | EOS |
|---|---:|---:|---:|
| B1d full | .0477 | 10% | 0% |
| B1d-CE | .2061 | 5% | 10% |
| B2 full | .3349 | 18% | 60% |
| B2 layer12 | .3464 | 21% | 60% |
| B2 layer9 | .3340 | 22% | 55% |
| SS | .3783 | 10% | 59% |
| slot-aware SS | .4074 | 12% | 69% |
| **A1 native** | **.6552** | **100%** | **100%** |

- B1d probe에서 `encoder_outputs=BaseModelOutput(last_hidden_state=H_s)` 경로는 **성공**했다.
  - token alignment 1,454/1,454
  - hidden cosine .7271까지 상승
- 그러나 adapter-only free-running은 **F1 .0477 / EOS 0%**였고, decoder LoRA를 붙여도 제품 기준에는 미달했다.
- T5Gemma2 merged attention은 self/cross K/V를 공유한다. 우리는 shared K/V를 사용했다.
- **external K/V projection 분리**, A1 encoder hidden teacher, layer5 B2는 **미시도**다.
- T5Gemma2 bridge는 D-108에서 종료됐으므로, 이 계획에서 **재개하지 않는다.** 재개하려면 별도 decision record + 명시적 승인이 필요하다.

### 3.4 알려진 errata

- `grounded` = no-new-only; preservation 미검사
- teacher hidden = base T5Gemma2 encoder (A1 LoRA 없음)
- B1d/B2의 초기 feature final 768 = **projection output**, hidden 아님
- Stage A는 5문서/1 seed
- 기존 EG2 cache는 **T5Gemma2 tokenizer**로 source를 tokenize했다. EG2 native tokenizer와 대부분 ID가 유사하지만 **완전 동일하지 않다.**
  - 이 문서의 layer role probing은 **EG2 native tokenizer**를 사용할 것을 제안한다.
  - Stage A와의 tokenizer 차이는 **reviewer가 반드시 판정해야 할 위험**이다.

---

## 4. 계획 개요

| 단계 | 질문 | 상태 | 예상 |
|---|---|---|---|
| **Layer role probing** | 각 layer에 어떤 정보가 선형적으로 접근 가능한가? | **미실행** | 1~2시간 (cache 제외) |
| **Stage A** | frozen decoder가 memory 내용을 쓰는가? | **완료** | — |
| **Stage B0** | decoder LoRA를 붙이면 content selectivity가 생기는가? | **미실행** | 2.5~3.5시간 |
| **Stage B1** | mT5 내부에서 layer 효과가 있는가? | **미실행** | 2~3시간 |
| **Stage B2** | 같은 layer에서 model 효과가 있는가? | **미실행** | 1~2시간 |
| **Stage C (선택)** | 300문서에서 제품 기준을 넘는가? | **미실행** | 2~4시간 |

- Layer role probing과 Stage B0는 **독립적**이므로 병렬 가능하다.
- 단, **B0 layer 선택을 role probing 결과로 하지 않는다.** B0는 Stage A의 real CE 1위(layer19)를 고정한다.
- B1 이후에만 role probing 결과를 **후보 추가/해석**에 사용한다.

---

## 5. Layer role probing 계획

### 5.1 목적

EG2 layer별로 **어떤 정보가 linearly decodable한가**를 측정한다.  
이것은 **layer의 인과적 역할**을 증명하는 실험이 아니라, **표현 접근성(accessibility)** 을 측정하는 실험이다.

### 5.2 데이터

- F5 clean: train 300 / val 100
- source: passage
- EG2 **native tokenizer**로 tokenize (기존 T5Gemma2 tokenizer cache와 별도)
- test 163 미사용

### 5.3 Probe tasks

| probe | label | 목적 |
|---|---|---|
| **surface frequency** | train split에서 token document-frequency를 5분위로 나눈 bucket | 초기 layer의 lexical/surface 정보 |
| **numeric/date** | token이 숫자·날짜·금액 pattern에 포함되는가 | number 보존 |
| **slot overlap** | `eval.slot_verify.extract_slots(summary)`의 slot 문자열과 source token의 character span이 겹치는가 | grounding에 필요한 slot 정보 |
| **sentence position** | passage 내 문장 index를 5 bucket으로 나눈 값 | 문장 순서/구조 정보 |

- **entity 후보**는 별도 NER 라벨이 없으므로 numeric/date와 slot overlap으로 근사한다. “entity role”이라고 부르지 않는다.
- 각 probe는 **token-level binary/multiclass logistic regression**(class weight 적용)으로 시작하고, 필요하면 2-layer MLP를 비교한다.
- **selectivity control**: label을 문서 내에서 permute한 control probe를 같은 조건으로 학습해 `accuracy_true - accuracy_permuted`를 primary로 보고한다.
- document-level split; token leakage 방지를 위해 **문서 단위 train/val**.
- 가능하면 1000회 bootstrap으로 CI를 보고한다.

### 5.4 DoD

- 최소 1개 probe에서 **selectivity > 0**, bootstrap 95% CI lower > 0
- layer별 selectivity curve가 재현 가능
- probe가 chance 수준이면 “해당 정보는 linearly accessible하지 않다”로 기록
- **이 결과만으로 causal role을 주장하지 않는다**

### 5.5 산출물

- `reports/C5_EG2_LAYER_ROLE_PROBE_2026-11-08.md`
- `reports/provenance/C5_b1d/eg2_layer_role_probe.json`
- runner: `runner/c5_eg2_layer_role_probe.py`
- cache: `data/wave2c/eg2_role_layer{0..23}/`

### 5.6 한계

- linear probe는 **decodability**만 측정; causal use와 다르다.
- PLE 때문에 layer별 역할이 일반 Transformer와 다를 수 있다.
- Korean tokenizer/형태소 분석 부재로 “syntactic role”은 직접 측정하지 않는다.
- probe label 품질이 낮으면 결론이 약해진다.

---

## 6. Stage A — 완료 (요약)

Stage A는 **frozen decoder + adapter-only**에서 layer별 memory 사용성을 본 실험이다.

- mT5: best real layer19 6.623; Δshuffled max .189
- UMT5: best real layer12 8.185; Δshuffled max .009
- conclusion: **content selectivity 없음**

Stage A의 목적은 layer 선택이 아니라 **frozen decoder 조건의 병목 확인**이었다.  
이 결과는 B0의 필요성을 지지한다.

---

## 7. Stage B0 — 단일 layer decoder adaptation 진단

### 7.1 목적

**한 모델·한 layer**에서 decoder LoRA를 붙였을 때 content selectivity가 생기는지 확인한다.

- 만약 B0에서도 real≈shuffled이면: layer role probing이나 layer sweep을 더 해도 bridge는 어려움
- 만약 B0에서 real<shuffled이면: frozen decoder가 병목이었다는 증거 → B1 진행

### 7.2 고정 조건

```text
model: mT5-small
layer: 19  (Stage A best real CE)
train: 20 docs
val: 20 docs
steps: 100
adapter: MLP 512→512→512 + LayerNorm
decoder: LoRA q/k/v/o
seeds: 20261108, 20261109, 20261110 (3 seeds)
```

### 7.3 측정

- `CE_real`, `CE_zero`, `CE_shuffled`
- per-doc `Δshuffled_i = CE_shuffled_i - CE_real_i`
- `Δzero_i = CE_zero_i - CE_real_i`
- generation 5 docs: non-empty, EOS, repetition
- adapter/LoRA gradient, loss finite

### 7.4 사전 등록 DoD

**Primary — content selectivity**

- mean `Δshuffled` ≥ **0.10 CE**
- paired bootstrap 95% CI lower > 0
- 3 seeds 모두 방향이 양수

**Secondary**

- mean `Δzero` > 0
- generation 5/5 non-empty
- EOS ≥ 3/5

**Stop**

- mean `Δshuffled` ≤ 0, 또는 CI lower ≤ 0 → **bridge 종료**
- 0 < mean < 0.10 → **weak signal**; B1을 자동 진행하지 않고 reviewer 판단
- 학습 불안정/OOM → LoRA rank/모듈 축소 후 1회 재시도

### 7.5 비용

- 구현 1~2시간 (LoRA/generation 경로)
- 실행 10~20분
- 보고서 30분
- **총 2.5~3.5시간**

---

## 8. Stage B1 — mT5 내부 layer 효과

### 8.1 진입 조건

Stage B0 통과.

### 8.2 설계

```text
model: mT5-small 고정
layers: 5, 9, 12, 19
train: 20 docs
val: 20 docs
steps: 100
adapter + decoder LoRA
seeds: B0와 동일 3 seeds
```

layer 선정 이유:

- layer5: T5Gemma2 cosine 최고 (외부 proxy)
- layer9: 기존 T5Gemma2 free-running 상위
- layer12: 기존 T5Gemma2 free-running 최고
- layer19: Stage A mT5 real CE 최고

### 8.3 DoD

- 각 layer의 `Δshuffled`와 `CE_real`을 3 seeds로 보고
- best layer L*가 layer19 대비:
  - `Δshuffled` 개선의 paired bootstrap 95% CI lower > 0
  - 또는 `CE_real` 개선 CI lower > 0
- 개선이 없으면 **layer19 유지**, B2로 진행
- B0보다 낮은 selectivity면 해당 layer 기각

### 8.4 비용

- layer당 100 step ~1~2분 + eval/generation
- 4 layers × 3 seeds ≈ **30~60분 실행**
- 구현 재사용, 보고서 포함 **2~3시간**

---

## 9. Stage B2 — 같은 layer에서 model 효과

### 9.1 진입 조건

B1 완료, layer L* 확정.

### 9.2 설계

```text
layer: L* 고정
models: mT5-small / UMT5-small
train: 20 docs
val: 20 docs
steps: 100
adapter + decoder LoRA
seeds: 동일 3 seeds
```

**중요**: mT5 layer19, UMT5 layer12처럼 **다른 layer를 배정하지 않는다.**  
같은 layer에서만 모델을 비교해야 model effect를 분리할 수 있다.

### 9.3 DoD

- 두 모델의 `Δshuffled`, `CE_real`, generation을 비교
- 절대 CE는 tokenizer 차이로 비교하지 않는다.
- UMT5가 더 좋으려면:
  - `Δshuffled`가 mT5보다 높고 CI lower > 0
  - 또는 generation/EOS가 명확히 우세
- 차이가 없으면 **mT5 유지** (기존 baseline, 단순성)

### 9.4 비용

- 2 models × 3 seeds ≈ **30~60분 실행**
- 보고서 포함 **1~2시간**

---

## 10. Stage C (선택) — 300문서 F5

B0~B2에서 content selectivity가 확인된 경우에만:

```text
model: B2에서 선택
layer: L*
train: 300
val: 100
adapter + decoder LoRA
```

DoD:

- val100 F1 ≥ **.45**
- grounded ≥ **50%**
- EOS ≥ **60%**
- A1 native **.6552 / 100% / 100%**와 비교
- test 163 미사용

Stage C는 **제품 후보 승인**이 아니며, 통과해도 별도 제품 결정이 필요하다.

---

## 11. 의존관계와 중단 규칙

```text
Layer role probing ──(병렬 가능)──┐
                                  ▼
Stage A (완료) → B0 → B1 → B2 → C(선택)
```

| 지점 | 조건 | 다음 |
|---|---|---|
| B0 | Δshuffled ≤ 0 또는 CI lower ≤ 0 | **STOP** |
| B0 | 0 < Δshuffled < 0.10 | reviewer 판단 |
| B0 | 통과 | B1 |
| B1 | 어떤 layer도 layer19보다 낫지 않음 | layer19 유지, B2 |
| B1 | selectivity 붕괴 | **STOP** |
| B2 | 차이 없음 | mT5 유지 |
| B2 | UMT5 우세 | UMT5 후보 |
| C | DoD 미달 | 제품 후보 아님 |

**공통 중단 규칙**

- test 163 사용 금지
- 3 seeds 방향 불일치 시 “불안정”으로 기록
- `Δshuffled`가 0 근처면 layer를 더 추가하지 않는다
- model/layer를 동시에 바꾸지 않는다

---

## 12. 리스크와 한계

1. **작은 표본**: Stage A 5/5, B0/B1/B2 20/20. 제품 결론이 아니라 **병목 진단**이다.
2. **단일/3 seed**: B0부터 3 seeds로 보완하지만, seed 3개는 충분한 통계가 아니다.
3. **content selectivity 정의**: `CE_shuffled - CE_real`은 내용 선택성의 proxy다. 완벽한 causal metric이 아니다.
4. **grounded metric**: 현재 no-new-only. preservation/entity audit 미실행. Stage C 전에 metric audit 필요.
5. **tokenizer 차이**:
   - 기존 EG2 cache = T5Gemma2 tokenizer
   - layer role probing 제안 = EG2 native tokenizer
   - 두 cache의 token ID가 완전 동일하지 않다. **Stage A 재추출 여부를 reviewer가 판정해야 한다.**
6. **PLE**: layer role이 일반 Transformer와 다를 수 있다. depth prior 금지.
7. **T5Gemma2 재개 금지**: D-108 STOP. 이 계획은 mT5/UMT5에 한정된다.
8. **F4/F6/F3**: decoder 재사용은 F5 이후 별도 task adapter/LoRA가 필요하다. 이 계획은 F5만 검증한다.

---

## 13. 검토 질문

### Q1. Layer role probing의 설계

- surface/numeric/slot/sentence-position probe가 EG2 layer 역할을 이해하는 데 충분한가?
- **linear probe + selectivity control**이 적절한가, 아니면 causal ablation이 선행되어야 하는가?
- EG2 native tokenizer로 재추출하는 것이 맞는가?

### Q2. Stage A의 해석

- 5문서/1 seed에서 real≈shuffled인 결과를 **“frozen decoder 병목”**으로 해석하는 것이 타당한가?
- 아니면 5문서가 너무 작아 **selectivity를 검출할 힘이 없었던 것**인가?

### Q3. Stage B0의 단일 layer 선택

- layer19 하나로 B0를 하는 것이 타당한가?
- layer5/12를 함께 B0에 넣어야 하는가?
- B0의 목적이 “decoder adaptation”이라면 한 layer로 충분한가?

### Q4. DoD

- `Δshuffled ≥ 0.10 CE` + CI lower > 0 + 3 seeds 양수는 적절한가?
- 20문서/100 step/3 seeds가 이 판정에 충분한가?
- 더 강한/약한 기준이 필요한가?

### Q5. B1 layer set

- 5/9/12/19가 적절한가?
- layer6/8/10/11을 추가해야 하는가?
- 4 layer × 3 seeds가 과도/부족한가?

### Q6. B2 model comparison

- 같은 layer에서 mT5/UMT5를 비교하는 설계가 model effect를 분리하는가?
- UMT5 tokenizer가 target CE를 바꾸므로 **생성 품질 중심 비교**가 더 적절한가?

### Q7. Stage C 진입

- B2 통과 후 300문서로 가는 것이 맞는가?
- 아니면 B1에서 20문서 generation만으로 중단해야 하는가?
- A1 native와의 비교를 Stage C 전에 해야 하는가?

### Q8. Metric

- Stage C의 F1/grounded/EOS 기준이 충분한가?
- `grounded` no-new-only를 먼저 고쳐야 하는가?
- entity audit를 Stage C 전에 넣어야 하는가?

### Q9. T5Gemma2 재개

- D-108 STOP을 유지하는 것이 맞는가?
- external K/V projection 분리 실험을 별도 트랙으로 검토할 가치가 있는가?
- 아니면 mT5/UMT5에 집중해야 하는가?

### Q10. 우선순위

- Layer role probing과 Stage B0를 병렬로 하는 것이 맞는가?
- 아니면 B0를 먼저 하고, role probing은 B1 이후로 미뤄야 하는가?
- 전체 계획에서 **가장 먼저 삭제해야 할 단계**는 무엇인가?

---

## 14. 산출물·재현 정보

### 14.1 현재 artifact

- `reports/C5_EG2_ALL_LAYER_SWEEP_2026-11-08.md`
- `reports/C5_MT5_LAYER_PROBE_2026-11-08.md`
- `reports/C5_MT5_UMT5_LAYER_PROBE_2026-11-08.md`
- `reports/EXTERNAL_REVIEW_C5_BRIDGE_2026-11-08.md`
- `reports/C5_BRIDGE_3AI_REVIEW_SYNTHESIS_2026-11-08.md`
- `reports/provenance/C5_b1d/all_layers_pretest.json`
- `reports/provenance/C5_b1d/mt5_layer_probe.json`
- `reports/provenance/C5_b1d/umt5_layer_probe.json`
- `runner/c5_eg2_all_layers_cache.py`
- `runner/c5_mt5_layer_probe.py`
- `docs/decisions.md` D-087~D-111
- `reports/C5_STATUS_2026-11-06.md` §37~§54

### 14.2 데이터

- `data/external/f5_pairs_v3_clean.jsonl` (1,617)
- `reports/provenance/C5_clean/splits.json` (1,293/161/163, seed 42)
- `data/wave2c/eg2_layer{0..24}/` (현재 caches)
- `data/models/mt5-small`, `data/models/umt5-small`

### 14.3 제약

- test 163 sealed
- P1/외부 API 미사용
- CPU only
- production `eval/slot_verify.py` 미수정
- D-108 STOP 유지 (T5Gemma2 bridge 재개 금지)

### 14.4 대표 재현 명령

```bash
# all-layer EG2 cache (existing; T5Gemma2 tokenizer)
.venv/Scripts/python.exe runner/c5_eg2_all_layers_cache.py \
  --layers 0-24 --out-root data/wave2c --out-prefix eg2_layer --overwrite

# mT5 Stage A
.venv/Scripts/python.exe runner/c5_mt5_layer_probe.py \
  --model-type mt5 --model-dir data/models/mt5-small \
  --layers 1-23 --train-limit 5 --val-limit 5 --steps 100 \
  --out reports/provenance/C5_b1d/mt5_layer_probe.json

# UMT5 Stage A
.venv/Scripts/python.exe runner/c5_mt5_layer_probe.py \
  --model-type umt5 --model-dir data/models/umt5-small \
  --layers 1-23 --train-limit 5 --val-limit 5 --steps 100 \
  --out reports/provenance/C5_b1d/umt5_layer_probe.json
```

> Stage B0/B1/B2용 decoder LoRA runner는 **아직 구현되지 않았다.** 이 검토요청서는 구현 전 계획 검토용이다.

---

## 15. 요청하는 최종 판정

다음 중 하나를 선택하고 근거를 제시하십시오.

- **STOP**: layer role probing과 B0~B2를 모두 중단하고 A1 native/다른 트랙으로 간다.
- **NARROW**: B0 하나만 실행하거나, role probing 하나만 실행한다.
- **CONTINUE**: layer role probing + B0 + B1 + B2 계획을 승인한다. 단, must-fix를 조건으로 한다.

그리고 다음을 명시하십시오.

1. 이 계획에서 **가장 먼저 고쳐야 할 방법론적 결함**
2. **가장 먼저 실행할 실험 1~2개**와 그 이유
3. **삭제하거나 후순위로 미룰 단계**
4. Stage B0/B1/B2의 **DoD·중단 조건**에 대한 수정안
5. **tokenizer 불일치**를 어떻게 처리해야 하는지
6. 이 계획을 계속할 경우 **최대 허용 비용**
7. A1 native 제품 경로와의 관계

---

*이 문서는 P0 데이터와 비밀값 없이 작성되었습니다. test 163은 봉인 상태입니다.*
