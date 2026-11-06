# 외부 검토 요청 — F5 A1 T5Gemma2 LoRA와 EG2→T5 bridge

- 날짜: 2026-11-06
- 검토 기준: **본 문서가 포함된 `origin/main` HEAD** (`git rev-parse HEAD`로 확인; shallow clone이면 이 커밋만 존재)
- 검토 스냅샷: **`834d598`** (3-AI가 실제로 읽은 HEAD; 이후 정정은 §0.1)
- 실험 산출물 기준: **`1fa8bbb`** (참조용; 코드·산출물은 그 이후 변경 없음)
- 저장소: `C:\code\unigem` (비공개 `mandutt/unigem`, main, origin과 0/0)
- 검토 범위: **F5 메모리용 추상 요약**
- test 163: **A0가 이미 사용(D-080, 0.6072); A1에는 미사용·봉인**
- 이 문서는 **자기완결형**입니다. 검토자는 이전 스레드나 대화를 읽지 않아도 됩니다.
- 데이터 등급: F5 clean 데이터는 **P0(공개·합성 가공)**. P1 개인 데이터는 사용하지 않았습니다.

---

## 0. 한눈에 보는 결론

1. **A2-null(EG2 → adapter → frozen T5Gemma2 decoder external memory)은 제품 후보에서 중단**했다.
   - full val 161: char F1 **0.1277/0.1169**, grounded **0/161, 1/161**, EOS **6~10%**, repeated4 **0.85~0.87**.
   - 그러나 memory-ablation ΔNLL은 양수(real vs shuffled **+0.058**)여서 “memory가 전혀 없다”는 아니다.
   - 원인은 **merged decoder q/k/v/o를 frozen으로 둔 adapter-only bridge**로 해석한다. T5Gemma2 논문의 merged attention 구조와 일치한다.
2. **A1(native T5Gemma2 encoder + q/k/v/o LoRA)은 val 161에서 A0를 상회**했다.
   - A1 pilot300: char F1 **0.6576**, grounded **161/161** (non-vacuous **155/155** + slot-free **6/161**), new slot **0**, EOS **161/161**, repeated4 **0.0554**. `slot_preservation` 평균은 **0.4558**로 별도 보고.
   - A0 extractive: **0.6111**.
   - paired 차이 **+0.0465**, 95% CI **[+0.0336, +0.0603]**, A1 우세 **112/161**.
   - 단, **pilot300은 full train이 아니고**, test·사람 검토 미실시다.
3. **`summarize: ` prefix는 학습·평가에 넣은 조건과 추론에만 넣은 조건이 다르다.**
   - pilot100(bare 학습)에 inference prefix만: 0.4659 → **0.6118**.
   - pilot300(summarize prefix 학습): val 161 **0.6576**.
   - prefix-trained pilot300은 bare 입력 val 5에서도 **0.6522**로 요약이 유지됐다. 단, **val 161에서는 bare 0.6335 < prefix 0.6576** (paired +0.0241 CI [+0.0132,+0.0351])로 prefix가 load-bearing이었다.
4. **EG2→T5의 “최소 adapter” 가능성**은 문헌상 존재하지만, A2처럼 external memory를 decoder에 직접 넣는 방식이 아니라 **soft token을 encoder input에 넣는 방식**이 유망하다. 특히 **T5Gemma2 native encoder hidden을 teacher로 쓰는 B1d distillation**은 summary label 없이 P0 text만으로 adapter를 정렬할 수 있어 범용 bridge의 최소 경로 후보이다. 아직 구현·검증하지 않았다.
5. **결정이 필요한 것**:
   - A1 full train(2 epoch) 승인 여부
   - prefix 고정 / bare / prefix dropout 중 full train 조건
   - B1d teacher-hidden distillation bridge를 A1 full train 전에 할지
   - A2를 raw control 없이 종결해도 되는지
   - 최종 test 163과 사람 50건의 실행 조건

---

## 0.1 검토 후 정정 (2026-11-06)

이 절은 3-AI 검토가 끝난 뒤 확인된 오류와 추가 실측을 반영한다. 원문 본문은 검토 스냅샷 `834d598`의 기록이며, 아래가 현재 정본이다.

1. **B1d 인터페이스 정정**: B1d는 `inputs_embeds`가 아니라 **`encoder_outputs` replacement**다. `H_s`를 encoder의 `inputs_embeds`로 넣으면 encoder가 다시 실행되어 “런타임 encoder 미실행”이 성립하지 않는다. B1/B3만 encoder-input 경로(`inputs_embeds`)이고, B1d는 encoder-output 경로다.
2. **A1 slot 보존 추가**: pilot300 val161 `slot_preservation` 평균 **0.455827** (A0 0.801190), **153/161** 문서가 원문 slot을 1개 이상 누락. `grounded 161/161`은 신규 slot 없음만 뜻하며, non-vacuous **155/155**와 slot-free **6/161**을 분리 보고해야 한다.
3. **test 163 이력 정정**: test 163은 A0가 이미 사용했다(D-080, char F1 0.6072). “미사용”은 **A1에 미사용**으로 한정한다.
4. **pilot300 governance**: D-082는 smoke 1 step + pilot 50~100 step만 승인했다. pilot300은 범위를 넘었으므로 승인 기록이 필요하다. D-042(EG2 text hidden의 F4/F5 제품 사용 폐기)도 B-family 제품 채택 전에 명시적으로 대체해야 한다.
5. **H4′ 정정**: H4′는 코퍼스 v2 4,695문장의 token-string 분절 일치이며, D-027의 **id 불일치 6,186개 + `<eos>` 차이**를 없애지 않는다. F5 passage/prompt/special token에서 token id·offset·mask를 재감사해야 한다.
6. **파라미터·비용 정정**: B3 K32 MLP는 **21.78M**(22.4M 아님), B3 trainable 범위는 **4~22M**, B1b 표준 2-layer는 **7~10M**(2~5M 아님), B2 decoder-only q/k/v/o r8은 **737,280**(A1의 1,474,560 아님). B3 시간 표기 3~4h와 2~4h는 하나로 통일해야 한다.
7. **prefix/bare 추가 실측**: pilot300 prefix **0.657580**, bare **0.633491**, paired prefix−bare **+0.024089** CI **[+0.013186,+0.035089]**. Prefix가 load-bearing이므로 full train은 prefix 고정. zero-shot `summarize: `는 **0.226113**, EOS **0/161**로 base model의 낮은 천장을 확인했다.
8. **Full train 코드 미구현**: `c5_a1_lora.py`는 종료 시 1회 저장, epoch 재셔플 없음, `--rank/--alpha/--dropout`가 LoRA 구성에 전달되지 않음, step-time stop 미구현. full train 전에 수정이 필요하다.

---

## 1. 자가완결 맥락

### 1.1 프로젝트

`unigem`은 EG2(EmbeddingGemma 2) 상주 인코더를 여러 기능에 재사용하는 연구 프로젝트다. 현재 활성 라인은 **F5: 메모리용 추상 요약**이다.

- 목표: 원문 passage를 3~5문장의 추상 요약으로 변환
- A0: 추출형 기준선(최종 구현 아님)
- A1: T5Gemma2 native encoder-decoder + LoRA
- A2: EG2 adapter → T5Gemma2 external memory (exploratory, 현재 중단)
- STT(F2)는 **D-079로 동결**되어 이 검토 범위가 아니다.
- F5의 gate는 G-C5: **grounded ≥99%, 신규 슬롯 ≤1%** (D-080).

### 1.2 모델·환경

- CPU only: Ryzen 5 7600 6C/12T, RAM 15.6GiB, GPU 없음
- Python 3.12, `.venv`, torch 2.15.0+cpu, transformers 5.22.1
- T5Gemma2: `data/models/t5gemma-2-270m-270m/`
  - vision tower 제거 text-only **370,637,824 params**
  - encoder non-embedding 100M, decoder non-embedding 100M, tied embedding 168M, vision 417M (논문 Table 2와 일치)
  - decoder hidden 640, 18 layers, merged self/cross attention
- EG2: `data/models/embeddinggemma-2-f9972ac2/`, final projection 768×512, nullity 256
- PEFT 미사용; 직접 LoRA wrapper 구현

### 1.3 데이터

- `data/external/f5_pairs_v3_clean.jsonl`: **1,617쌍**
  - 원본 2,000쌍에서 신규 slot이 0인 clean만 선택
- `reports/provenance/C5_clean/splits.json`: seed 42
  - train **1,293** / val **161** / test **163**
- passage token: mean 762.2, p95 828, max **908**; 1024 초과 0
- target token: mean 208.9, p50 204, p95 289, p99 333, max **439**
- target repeated4 평균 **0.0270**
- pad **0**, eos **1**, bos **2**
- test 163은 최종 후보 1회만 사용

### 1.4 핵심 결정

| 결정 | 내용 |
|---|---|
| **D-080** | F5 재개, clean 1,617, G-C5를 grounding rate로 확정, A0 test 163 char F1 0.6072 |
| **D-081** | A2-null exploratory 승인, 제품 채택은 A1 대비 별도 결정 |
| **D-082** | A1 T5Gemma2 LoRA smoke/pilot만 승인; full train·test는 별도 승인 |
| A2 중단 | 2026-11-06 full val 결과로 제품 후보 중단 **권고**; 삭제·폐기는 아님 |
| A1 full train | **미승인·미실행** |

### 1.5 직전 3-AI 검토

A2-null 3-arm 결과에 대해 GLM 5.3 Flash(max), Opus 5.5(medium), Terra 6.1(high)에 검토를 요청했다.

- **GLM**: full val 161 first, 현재 INCONCLUSIVE(부정 방향)
- **Opus**: Pivot to A1. 전환 전 memory-ablation ΔNLL + raw-vs-seq control
- **Terra**: full val 161 first, 이후 A1 smoke/pilot; A2 decoder LoRA 자동 연속 금지
- 공통: **지금 A2 decoder LoRA를 시작하지 않는다**
- 원문: `docs/hoplite/c5_a2null_2026-11-06/`
- 종합: `reports/C5_A2NULL_3AI_REVIEW_SYNTHESIS_2026-11-06.md`

---

## 2. 직전 검토 이후 진행

1. A2 full val 161 + A0 val 161 + zero-shot T5Gemma2 + memory ablation
2. A2 제품 후보 중단, A1 전환
3. A1 smoke 1 step → pilot100 → prompt 진단 → lr 2e-4/300 step
4. A1 pilot300 val 5 → val 161 batch
5. T5Gemma2 논문(arXiv 2512.14856) 구조 확인
6. EG2→T5 최소 bridge 문헌 조사(Exa)
7. B-family soft-prefix bridge(B3/B1/B1d/B2)는 **아직 미구현**

---

## 3. 실측 상세

### 3.1 A2-null full val 161

| system | char F1 | grounded | new-slot micro | EOS | repeated4 | len |
|---|---:|---:|---:|---:|---:|---:|
| A0 extractive | **0.6111** | grounding reject 0 | 0 | — | — | — |
| A2 EOS | 0.1277 | **0/161** | 0.9059 | 9.94% | 0.8695 | 449 |
| A2 LN | 0.1169 | **1/161** | 0.9486 | 6.21% | 0.8468 | 449 |
| zero-shot T5Gemma2 | 0.2333 | 0.6584 macro | 0.5862 | 1.86% | 0.8383 | 449 |

- A2 EOS − A0 paired char F1 **−0.4834** CI [−0.4981,−0.4688]
- A2 LN − A0 **−0.4942** CI [−0.5086,−0.4786]
- zero-shot: prefix `다음 글을 3~5문장으로 요약하세요.\n\n`; native encoder/frozen decoder; adapter 없음

### 3.2 A2 memory ablation

| adapter | real NLL | shuffled NLL | Δ shuffled | positive | Δ zero |
|---|---:|---:|---:|---:|---:|
| EOS | 3.1160 | 3.1740 | **+0.0580** CI [+0.0520,+0.0640] | 149/161 | +3.2041 |
| LN | 3.1288 | 3.1870 | **+0.0582** CI [+0.0518,+0.0643] | 157/161 | +3.1913 |

- **real vs shuffled는 유의** → memory에 문서 특정 신호가 있음
- **real vs zero**는 크지만 zero가 OOD이므로 절대 비교로 과해석하지 않음
- **raw-vs-seq control은 미실행** (A2 재개 시 필수)

### 3.3 A1 smoke / pilot

| 항목 | 값 |
|---|---|
| text-only | 370,637,824 params |
| LoRA | 144 modules q/k/v/o, rank 8, alpha 16, dropout 0.05 |
| trainable | 1,474,560 (0.40%) |
| smoke 1 step | 4.4~4.7초, RSS 1.7~1.8GB |
| pilot100 | 416초(4.16초/step), RSS 2.32GB |
| pilot300 | **1,258.7초(4.20초/step)**, RSS peak ~2.45GB |
| pilot300 adapter | 5,998,227 bytes |
| pilot300 loss | mean 0.6624, first10 0.7193 → last10 0.6016 |
| NaN | 0 |

### 3.4 A1 pilot300 val 161

- 평가: batch 8, greedy, `max_new_tokens=448`, `summarize: ` prefix
- **test 163: A1에는 미사용** (A0는 D-080에서 사용)

| metric | A0 | A1 pilot300 |
|---|---:|---:|
| char F1 | 0.6111 | **0.6576** |
| grounded | — | **161/161** |
| new-slot micro | 0 | **0** |
| EOS | — | **161/161** |
| repeated4 | — | **0.0554** |
| distinct2 | — | 0.8231 |
| mean len | — | 248.3 |
| summary slots | — | 837 |

- paired A1−A0 **+0.0465** CI **[+0.0336,+0.0603]**
- A1 우세 **112/161**, 열세 49/161
- `summary_slot_count=0` **6/161** → 해당 문서 grounded는 vacuous
- tuning 첫 5건 제외 156건: A1 **0.6586**, A0 0.6115
- source 4-gram copy: A0 **0.9923**, A1 **0.8364**

### 3.5 Prompt / prefix 진단

| 조건 | char F1 | grounded | EOS | repeated4 |
|---|---:|---:|---:|---:|
| pilot100 bare 학습 + bare eval | 0.4659 | 5/5 | 3/5 | 0.4860 |
| pilot100 bare 학습 + `summarize: ` eval | **0.6118** | 5/5 | **5/5** | 0.2166 |
| pilot100 bare 학습 + 한국어 instruction eval | 0.4027 | 3/5 | 5/5 | 0.3200 |
| pilot300 `summarize: ` 학습 + prefix eval | **0.6272** (val5) | 5/5 | 5/5 | 0.1004 |
| pilot300 prefix 학습 + **bare eval** | **0.6522** (val5) | 5/5 | 5/5 | 0.0407 |

- `summarize: `는 특별 토큰이 아니라 입력 텍스트 일부
- prefix-trained adapter가 bare에서도 요약을 유지 → **prefix 의존은 아님**
- pilot100의 bare-trained adapter는 prefix inference로 개선 → base model의 task cue 효과

### 3.6 T5Gemma2 논문 구조

논문 arXiv 2512.14856:

```text
Q = X W_q
K = [X ; H] W_k
V = [X ; H] W_v
O = Softmax(QK^T/√d ⊙ M) V W_o
```

- decoder self-attention과 cross-attention이 **merged attention**으로 하나
- decoder q/k/v/o frozen → self/cross attention 모두 적응 불가
- A2가 실패한 구조적 이유와 일치
- T5Gemma2는 UL2 pretraining(2T tokens, 16K), post-training은 distillation 중심의 가벼운 수준; 270M은 한국어 요약 IT 모델이 아님
- 128K context; 우리 input max 908, target max 439 → truncation 배제

### 3.7 EG2→T5 최소 bridge — 설계 공간과 후보

이 절은 이번 검토의 핵심이다. **F5 summary adapter**와 **범용 EG2→T5 bridge**를 분리해서 본다.

#### 3.7.1 목표 정의

두 목표는 다르다.

| 목표 | 정의 | 학습 데이터 | 재사용 |
|---|---|---|---|
| **F5-only bridge** | EG2 표현으로 F5 요약을 잘 생성 | summary 1,293쌍 | F5만 |
| **범용 bridge** | EG2 표현을 T5Gemma2 decoder가 여러 task에서 사용 | 대규모 P0 text + task prompts | F4/F6/F3 등 |

A2-null은 F5-only bridge의 한 구현이었다. A1은 bridge가 아니라 **T5Gemma2 native encoder**를 쓰는 별도 경로다.

#### 3.7.2 A2와 B-family의 차이

A2:

```text
EG2 token feature
→ adapter 640
→ decoder의 encoder_outputs (external memory)
→ decoder frozen
```

B-family:

```text
EG2 feature
→ adapter
→ soft tokens (640d)
→ T5Gemma2 encoder의 inputs_embeds 앞에 prepend
→ native encoder + decoder
```

| 항목 | A2 | B-family |
|---|---|---|
| T5 encoder | **우회** | **사용** |
| 주입 위치 | decoder cross-attention memory | encoder input embedding |
| decoder | frozen | frozen(B1/B3) 또는 small LoRA(B2) |
| task cue | 없음 | 없음(soft token) 또는 선택적 prefix |
| A2 실패 원인 | merged decoder 적응 부재 | encoder 분포 유지로 완화 기대 |

T5Gemma2 `forward`는 `encoder_outputs`가 주어지면 encoder를 건너뛴다. **B1/B3**는 `inputs_embeds`를 encoder에 넣어 native encoder 경로를 보존하지만, **B1d는 `encoder_outputs`를 직접 공급해 encoder를 건너뛴다.** B1d를 `inputs_embeds` 경로로 구현하면 encoder가 다시 실행되므로 B1d가 아니다.

#### 3.7.3 B3 — pooled soft-prefix

가장 단순한 후보.

```text
e = Pool(EG2_text_hidden) ∈ R^768
s = Adapter(e) ∈ R^{K×640}
H_in = [ s ; Embed_T5(passage) ]       # (K+T)×640
mask = [1_K ; passage_mask]
logits = T5Gemma2(inputs_embeds=H_in, attention_mask=mask, labels=y)
```

- Pool: mean 또는 attention pooling
- Adapter: `Linear(768, K*640)` 또는 `MLP(768→1024→K*640)` + LayerNorm
- K: 8 / 16 / 32
- soft token scale: T5 embedding과 같은 scale (`sqrt(640)` 또는 learned scalar)
- base encoder/decoder frozen; adapter만 학습
- CE loss는 target summary label
- **로컬 probe(2026-11-06)**: `T5Gemma2ForConditionalGeneration.generate(inputs_embeds=...)`가 동작함을 확인했다. 단 모델 dtype이 **bf16**이므로 adapter 출력도 bf16으로 cast해야 한다(float32 입력은 dtype mismatch).

**파라미터**

| K | Linear 768→K·640 | MLP 768→1024→K·640 |
|---:|---:|---:|
| 8 | 3.9M | 6.0M |
| 16 | 7.9M | 11.3M |
| 32 | 15.7M | **21.78M** |

**학습 비용(예상)**

- 300 step: 20~30분
- 1,000 step: 70~90분
- val 5: 2~3분; val 161: 10~15분
- 구현·smoke: 1.5~2.5시간

**실패 모드**

1. decoder가 soft token을 무시 (cross-attention이 text token에만 집중)
2. soft token이 T5 embedding scale과 불일치
3. pooled 1개 vector가 passage의 token-level 정보를 잃음
4. summary 1,293쌍만으로는 task-agnostic bridge가 아님

#### 3.7.4 B1 — token-level soft-prefix / teacher distillation

EG2 token hidden을 T5 encoder 입력으로 매핑한다.

```text
H_e = EG2_token_hidden ∈ R^{T×768}
H_s = Adapter(H_e) ∈ R^{T×640}
H_in = [ H_s ; Embed_T5(prompt) ]  # 또는 prompt를 EG2에도 포함
```

변형:

- **B1a**: per-token `Linear(768→640)` (약 0.49M) — 가장 단순
- **B1b**: 2-layer Transformer adapter (표준 width 640에서 약 **7~10M**) — 문맥 보정
- **B1c**: Perceiver/resampler, K queries → K×640 (2~10M)

**중요**: H4′에서 T5Gemma2와 EG2의 분절이 코퍼스 v2 4,695문장에서 **token-string 100% 일치**했다. 그러나 D-027의 **id 불일치 6,186개 + `<eos>` 차이**가 남아 있고, F5 passage·prompt·special token·padding·truncation에서 재검증되지 않았다. 따라서 token-level 정렬은 **전제가 아니라 사전 감사 대상**이다. prompt를 EG2에도 넣어 teacher와 student 입력을 맞추는 것과 별개로, 실제 token id/offset/mask를 확인해야 한다.

**Teacher-hidden distillation (B1d)**

T5Gemma2 native encoder를 teacher로 사용한다.

```text
H_T = T5Encoder(prompt + passage)       # frozen teacher, 640d
H_s = Adapter(EG2(prompt + passage))    # student, 640d
L_align = 1 - cosine(H_s, H_T) + MSE(H_s, H_T)
```

- **summary label이 필요 없다.** P0 text만 있으면 된다.
- adapter만 학습; encoder/decoder frozen.
- **런타임에는 T5 encoder를 쓰지 않는다.** EG2 → adapter → H_s를 **`encoder_outputs=BaseModelOutput(last_hidden_state=H_s)`** 로 넣고 decoder가 생성한다. teacher는 학습 시에만 사용한다. `inputs_embeds`를 쓰는 B1/B3 경로와 혼동하지 말 것.
- 이후 decoder는 native encoder hidden과 같은 분포의 H_s를 받는다.
- **범용 bridge에 가장 가까운 최소 학습 경로**다.
- 단, T5 encoder hidden은 token-level 문맥을 포함하므로 per-token linear만으로 부족할 수 있다(B1b).
- teacher hidden cache: 1,617×~900×640 fp16 ≈ **1.9GB** raw; **학습에는 train 1,293만 사용**하고 test passage를 cache/fitting에 넣지 않는다(train-only ≈ **1.49GB**). CPU에서 생성·보관 가능.
- 대규모 P0 text로 확장하면 task-agnostic bridge 가능성이 있다. 현재 1,617건은 feasibility만.

#### 3.7.5 B2 — B1 + small decoder LoRA

LLINK 결과처럼 adapter alignment만으로 decoder가 신호를 무시할 수 있다.

```text
B1 adapter + q/k/v/o LoRA
```

- LoRA 1.47M (r8) 추가
- adapter + LoRA 학습; encoder frozen
- B3/B1이 decoder에서 무시될 때만
- LLINK: “decoder may still disregard the aligned representation without explicit training signals”
- 비용: B1 + 1~2시간

#### 3.7.6 기타 후보

| 후보 | 내용 | 판단 |
|---|---|---|
| **prefix tuning** | decoder-only prefix; PEFT는 encoder-decoder에서 encoder prefix를 지원하지 않음 | 부적합 |
| **eP-ALM식 다층 주입** | encoder [CLS]를 decoder 여러 layer에 linear projection | B1b/B2보다 침습적, 후순위 |
| **ACP representation adapter** | dimension adapter + 2~4 transformer layers | B1b와 유사; 파라미터 더 큼 |
| **VLAP식 word-embedding mapping** | EG2 → T5 word embedding space + captioning loss | soft token과 결합 가능 |
| **Vec2Text** | EG2 embedding → text inversion → T5 | 별도 inversion model·iterative; “최소” 아님 |
| **A2 external memory** | decoder에 직접 주입 | full val에서 실패 |

#### 3.7.7 후보 비교

| 후보 | T5 encoder | decoder | trainable | task-agnostic | 예상 |
|---|---|---|---|---|---:|
| A2 | 우회 | frozen | 1.08M | 아니오 | 실패 |
| **B3** | 사용 | frozen | 4~22M | F5-only | 3~4h |
| **B1a** | 사용 | frozen | 0.49M | teacher distillation 시 가능 | 4~6h |
| **B1b** | 사용 | frozen | 7~10M | teacher distillation 시 가능 | 4~6h |
| **B2** | 사용 | small LoRA | 0.7M + adapter | F5/B1 | 5~8h |
| **B1d** | teacher 사용 | frozen | student spec에 따라 0.5~5M | **가장 유망** | 4~7h |

#### 3.7.8 권고 순서

1. **B1d teacher-hidden distillation** — 4~7시간, task-agnostic bridge의 핵심 후보. 단, `encoder_outputs` 경로·oracle/NLL control 먼저.
2. **B1a/B1b** — B1d가 불안정할 때의 fallback; summary-label 기반 F5-only
3. **B2** — B1이 decoder에서 무시될 때
4. **B3** — augmentation 목적일 때만; real/shuffled/constant control 필요
5. **A1 full train** — 검증된 F5 경로; B3/B1과 동시에 CPU에서 돌리지 않음

#### 3.7.9 평가 계약

- 같은 clean val 5 → val 161
- `summarize: ` 없이 bare passage; task prefix를 쓰는 경우 별도 표기
- metrics: char F1, grounded, new-slot micro, EOS, repeated4, copy rate
- A0 0.6111, A1 pilot300 0.6576와 비교
- test 163은 최종 후보 1회만
- **B3/B1a/B1b은 F5-only adapter**이므로, “범용” 주장은 multi-task/teacher distillation 확장 전에는 하지 않는다.
- **B1d teacher-hidden distillation**은 teacher prompt를 다양화할 때만 task-agnostic 후보가 된다; 현재 1,293 summary만으로는 여전히 F5-specific이다.


---

## 4. 해석과 남은 가설

### 지지되는 해석

1. **A2 실패는 memory 부재가 아니라 decoder adaptation 부재**다.
   - memory signal은 양성
   - merged decoder q/k/v/o가 frozen
   - A1은 native encoder + q/k/v/o LoRA로 정상 생성
2. **A1의 prompt mismatch는 실제 원인 중 하나**다.
   - inference prefix만으로 +0.1459 char F1
   - prefix 학습으로 추가 개선
3. **A1 pilot300은 A0보다 val 161에서 우수**하다.
   - paired CI > 0, 112/161 우세
   - grounded/EOS 100%, new slot 0
4. **truncation·pad/eos·target 반복·adapter scale은 주원인이 아니다.**
   - input max 908, target max 439
   - pad 0 vs eos 1
   - target repeated4 2.7%
   - LayerNorm×5가 개선 없음

### 아직 확정되지 않은 것

- A1 pilot300이 **full train**에서도 유지되는지
- A1 val161의 0.6576이 **prompt/lr 선택 편향**을 얼마나 포함하는지 (첫 5건 제외 0.6586)
- prefix 고정이 **다른 task 일반화**를 해치는지
- B3 soft-prefix가 A1보다 나은지, 아니면 decoder LoRA가 필요한지
- A2 raw-vs-seq control 없이 종결해도 되는지
- 6/161 slot-free 문서를 gate에서 어떻게 처리할지
- 사람 50건 수용도와 G-C5 test 결과

---

## 5. 결정 필요 표

| ID | 결정 | 선택지 | 권고 |
|---|---|---|---|
| **D1** | A1 full train 승인 | 2 epoch / 3 epoch / 보류 | **2 epoch 먼저**, val 161 best |
| **D2** | full train prefix 조건 | `summarize: ` 고정 / bare / prefix dropout | **F5 전용이면 prefix 고정**; 범용성 우선이면 dropout arm |
| **D3** | EG2→T5 bridge 우선순위 | B1d / B1a-b / B2 / B3 / A1 full train 먼저 | **B1d 4~7h first, `encoder_outputs` 수정 후**; B3는 augmentation 목적일 때만 |
| **D4** | A2 종결 | raw control 후 / full val 근거로 종결 | **현재 근거로 제품 후보 종결**, raw는 exploratory 기록 |
| **D5** | test 163 | full train 후 1회 / B-family 후 / 보류 | **A1 full train best val 1개만 1회**; test는 A0가 이미 사용 |
| **D6** | 사람 50건 | full train 전 / 후 | **full train 후, test 전** |

---

## 6. 검토 질문

**Q1.** A1 pilot300 val 161(0.6576 vs A0 0.6111, paired +0.0465 CI [+0.0336,+0.0603], 112/161)은 full train을 시작할 충분한 근거인가? 아니면 추가 control이 필요한가?

**Q2.** A1 full train 2 epoch와 3 epoch 중 어느 쪽을 먼저 해야 하는가? 1 epoch 90분, 2 epoch 3시간, 3 epoch 4.5시간(CPU)이다. val 161 best 선택과 early stop을 어떻게 고정해야 하는가?

**Q3.** `summarize: ` prefix를 학습에 넣는 것이 F5 전용으로는 타당한가? bare/prefix dropout과 비교할 가치가 있는가? 다른 task(F4/F6/F3) 재사용 가능성과 분리하는 설계가 충분한가?

**Q4.** EG2→T5의 “최소 adapter” 목표를 위해 **B3 pooled soft-prefix, B1a-b token soft-prefix, B1d teacher-hidden distillation, B2 LoRA** 중 어디부터 실험해야 하는가? B1d가 범용 bridge의 가장 유망한 최소 경로인가, 아니면 B3 decoder-readability test가 먼저인가?

**Q5.** A2를 raw-vs-seq control 없이 제품 후보에서 종결하는 것이 정당한가? memory-ablation 양성 신호를 남기되, 추가 decoder LoRA를 하지 않는 판단이 맞는가?

**Q6.** A1 val161의 지표 구성이 충분한가? char F1, grounded, new-slot micro, EOS, repeated4, copy rate, 길이를 봤다. ROUGE-L, BERTScore, 사람 수용도, slot-free 6건 처리 중 무엇이 필수인가?

**Q7.** 6/161 summary slot-free 문서의 grounded를 vacuous로 볼 때, G-C5 grounded 100%를 어떻게 보고해야 하는가? gate 분모에서 제외해야 하는가, 별도 표기해야 하는가?

**Q8.** A1 full train에서 LoRA target을 q/k/v/o r8로 유지할 것인가, FFN 또는 rank 16을 추가할 것인가? T5Gemma2 merged attention 구조에서 우선순위는?

**Q9.** test 163은 A1 full train best val 1개에만 1회 사용하는 현 계획이 맞는가? B-family bridge를 병행할 경우 test를 어떻게 배분해야 하는가?

**Q10.** A1이 EG2를 사용하지 않고 T5Gemma2 native encoder를 쓰는데, 이것이 “F5 메모리 요약” 목표에는 맞지만 “EG2 재사용” 목표에는 어긋난다. 프로젝트 목표를 어떻게 정의해야 하는가?

**Q11.** full train 1,293쌍에서 2~3 epoch가 과적합 위험을 고려해 적절한가? early stop, weight decay, dropout, data ordering을 어떻게 고정해야 하는가?

**Q12.** 이 검토에서 반드시 고쳐야 할 factual error나 누락이 있는가?

---

## 7. 사전등록 초안 — A1 full train (승인 시)

- 데이터: clean train 1,293 / val 161 / test 163
- 입력: `summarize: ` + passage; max input 1024
- label: content + `<eos>`, `<bos>` 없음, padding -100, max target 512
- LoRA: q/k/v/o, r8, alpha16, dropout0.05, base frozen
- optimizer: AdamW, lr **2e-4**, grad clip 1.0
- epochs: **2** (1차), val 161 best; early stop patience 1
- generation: greedy, max_new 448, batch 8
- gate: val 161에서 grounded ≥99%, new slot ≤1%; A0 char F1 대비 개선; EOS ≥95%; repeated4 보고
- test: val best checkpoint 1개만 test 163 1회
- human: 50건, 수용 ≥60%, 치명적 사실 누락 없음
- **금지**: test 결과를 보고 hyperparameter 변경, A2 decoder LoRA 동시 실행, F4/F6 LoRA 재사용

---

## 8. 미실행·한계

| 항목 | 상태 |
|---|---|
| A1 full train | 미실행 |
| A1 test 163 | 미실행(봉인) |
| A1 사람 50건 | 미실행 |
| B3/B1/B2 soft-prefix | 미구현 |
| raw-vs-seq control | 미실행 |
| A2 decoder LoRA | 미실행·보류 |
| A1 bare full val 161 | 미실행 (bare val5 0.6522만) |
| ROUGE-L/BERTScore | 미측정 |
| 6/161 slot-free 처리 | 미확정 |
| F4/F6/F3 cross-feature | 미구현, 경계 문서만 |

- A1 0.6576은 **pilot300**이며, full train 성능이 아니다.
- val 161은 prompt/lr 선택에 첫 5건이 사용됐다(제외 156건 0.6586).
- 모든 평가는 CPU 1대, 단일 seed 42다.
- Exa/논문 사례는 다른 모델·과제이며, 우리 재현이 아니다.
- A2 raw control이 없으므로 “frozen decoder가 유일 원인”이라고 확정할 수는 없다.

---

## 9. 재현 정보

### 주요 코드

- `runner/c5_a1_lora.py` — A1 smoke/pilot/eval; `--prefix`, `--lr`, `--steps`, `--mode`
- `runner/c5_a1_eval_batch.py` — A1 val 161 batch evaluator
- `runner/c5_a1_watch.py` — A1 log watchdog
- `runner/c5_a2null_eval_batch.py` — A2 full val batch
- `runner/c5_a2null_ablation.py` — memory ablation ΔNLL
- `runner/c5_zero_shot_t5.py` — zero-shot T5Gemma2
- `runner/c5_a0_val161.py` — A0 same split
- `eval/slot_verify.py` — slot/grounding 검증기; `eval/tests` 12 tests

### 주요 산출물

- `reports/C5_A2NULL_VAL161_2026-11-06.md`
- `reports/C5_A1_smoke_pilot.md`
- `reports/C5_A1_prompt_diagnosis.md`
- `reports/C5_A1_val161_2026-11-06.md`
- `reports/C5_A1_exa_diagnosis_2026-11-06.md`
- `reports/C5_T5Gemma2_paper_notes_2026-11-06.md`
- `reports/C5_EG2_T5_bridge_literature_2026-11-06.md`
- `reports/provenance/C5_clean/a0_val161.*`
- `reports/provenance/C5_a2null/*`
- `reports/provenance/C5_a1/pilot300_val161/*`
- `reports/provenance/C5_a1/prompt_bare|prompt_summarize|prompt_korean/*`
- `logs/C5/*`

### 재현 명령

```bash
# A1 pilot300 (prefix)
.venv/Scripts/python.exe -u runner/c5_a1_lora.py --mode pilot --steps 300 \
  --lr 2e-4 --prefix "summarize: " --eval-limit 5 \
  --adapter data/models/f5_t5gemma2_lora/pilot300_lr2e4_prefix.pt \
  --out reports/provenance/C5_a1/pilot300_lr2e4_prefix

# A1 val 161 batch
.venv/Scripts/python.exe -u runner/c5_a1_eval_batch.py \
  --adapter data/models/f5_t5gemma2_lora/pilot300_lr2e4_prefix.pt \
  --batch-size 8 --max-new 448 --prefix "summarize: " \
  --out reports/provenance/C5_a1/pilot300_val161/predictions.jsonl \
  --metrics reports/provenance/C5_a1/pilot300_val161/metrics.json
```

- 모델 가중치·adapter는 git에 포함하지 않는다.
- test 163은 어떤 명령에서도 사용하지 않았다.

---

## 10. 답변 형식

다음을 순서대로 주세요.

1. **verdict**: A1 full train 승인 / 조건부 / 보류
2. **D1~D6 권고**: 각 한 줄
3. **Q1~Q12 답변**: 번호별
4. **Must-fix**: full train 전 반드시 고칠 것 최대 5개
5. **추가 실험**: 최대 3개, 예상 비용 포함
6. **사실 확인**: 이 문서의 수치·해석 중 틀린 것

---

## 11. 한 줄 요청

> A1 pilot300의 val 161 결과가 full train을 시작할 충분한 근거인지, `summarize: ` prefix를 F5 전용으로 고정해도 되는지, B3/B1/B1d/B2 중 EG2→T5 bridge를 어디부터 실험해야 하는지 판정해 주세요.
