# 외부 검토 요청 — F5 A1 T5Gemma2 LoRA와 EG2→T5 bridge

- 날짜: 2026-11-06
- 검토 기준 커밋: **`1fa8bbb`** (`1fa8bbb docs: survey minimal EG2-to-T5Gemma2 bridge methods`)
- 저장소: `C:\code\unigem` (비공개 `mandutt/unigem`, main, origin과 0/0)
- 검토 범위: **F5 메모리용 추상 요약**
- test 163: **봉인, 이 요청서 작성 시점까지 미사용**
- 이 문서는 **자기완결형**입니다. 검토자는 이전 스레드나 대화를 읽지 않아도 됩니다.
- 데이터 등급: F5 clean 데이터는 **P0(공개·합성 가공)**. P1 개인 데이터는 사용하지 않았습니다.

---

## 0. 한눈에 보는 결론

1. **A2-null(EG2 → adapter → frozen T5Gemma2 decoder external memory)은 제품 후보에서 중단**했다.
   - full val 161: char F1 **0.1277/0.1169**, grounded **0/161, 1/161**, EOS **6~10%**, repeated4 **0.85~0.87**.
   - 그러나 memory-ablation ΔNLL은 양수(real vs shuffled **+0.058**)여서 “memory가 전혀 없다”는 아니다.
   - 원인은 **merged decoder q/k/v/o를 frozen으로 둔 adapter-only bridge**로 해석한다. T5Gemma2 논문의 merged attention 구조와 일치한다.
2. **A1(native T5Gemma2 encoder + q/k/v/o LoRA)은 val 161에서 A0를 상회**했다.
   - A1 pilot300: char F1 **0.6576**, grounded **161/161**, new slot **0**, EOS **161/161**, repeated4 **0.0554**.
   - A0 extractive: **0.6111**.
   - paired 차이 **+0.0465**, 95% CI **[+0.0336, +0.0603]**, A1 우세 **112/161**.
   - 단, **pilot300은 full train이 아니고**, test·사람 검토 미실시다.
3. **`summarize: ` prefix는 학습·평가에 넣은 조건과 추론에만 넣은 조건이 다르다.**
   - pilot100(bare 학습)에 inference prefix만: 0.4659 → **0.6118**.
   - pilot300(summarize prefix 학습): val 161 **0.6576**.
   - prefix-trained pilot300은 bare 입력 val 5에서도 **0.6522**로 요약이 유지됐다.
4. **EG2→T5의 “최소 adapter” 가능성**은 문헌상 존재하지만, A2처럼 external memory를 decoder에 직접 넣는 방식이 아니라 **soft token을 encoder input에 넣는 방식**이 유망하다. 아직 구현·검증하지 않았다.
5. **결정이 필요한 것**:
   - A1 full train(2~3 epoch) 승인 여부
   - prefix 고정 / bare / prefix dropout 중 full train 조건
   - B3 pooled soft-prefix bridge를 A1 full train 전에 할지
   - A2를 raw control 없이 종결해도 되는지
   - 최종 test 163과 사람 50건의 실행 조건

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
7. B3 soft-prefix bridge는 **아직 미구현**

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
- **test 163 미사용**

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

### 3.7 EG2→T5 최소 bridge 문헌 조사

Exa 결과:

- **Gemini Embedding as Universal Encoder**(blog): frozen embedding → 17M MLP → k virtual tokens → frozen LLM; task-specific supervision; GPU <1분/태스크
- **LatentPress**(arXiv 2609.01507): frozen decoder가 continuous memory token을 input-embedding interface로 직접 읽음; writer 0.18~0.25%
- **LLINK**(arXiv 2510.27254): projector → K soft slots + small LoRA; “decoder may disregard aligned representation without explicit training signals”
- **eP-ALM**(arXiv 2303.11403): frozen encoder/LLM, linear projection only, multi-layer injection
- **Mixing Encoders/Decoders**(Moomin 2024): dimension adapter + representation adapter layers; frozen encoder/decoder; optional 2-stage decoder unfreeze
- **VLAP**(arXiv 2404.09632): single linear mapping to frozen LLM word-embedding space + captioning objective
- **SLM**(arXiv 2310.00230): frozen speech encoder + frozen LLM + few transformer adapter layers; next-token loss
- **Vec2Text**: embedding inversion; strong but separate iterative model, not minimal

**제안 B3**: EG2 pooled 768 → MLP → K soft tokens 640 → T5Gemma2 encoder `inputs_embeds` 앞에 prepend; encoder/decoder frozen; adapter만 학습. 아직 미실행.

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
| **D3** | B3 soft-prefix bridge | A1 full train 전 / 후 / 하지 않음 | **B3 smoke/pilot을 A1 full train 전에 2~3시간** |
| **D4** | A2 종결 | raw control 후 / full val 근거로 종결 | **현재 근거로 제품 후보 종결**, raw는 exploratory 기록 |
| **D5** | test 163 | full train 후 1회 / B3 후 / 보류 | **A1 full train best val 1개만 1회** |
| **D6** | 사람 50건 | full train 전 / 후 | **full train 후, test 전** |

---

## 6. 검토 질문

**Q1.** A1 pilot300 val 161(0.6576 vs A0 0.6111, paired +0.0465 CI [+0.0336,+0.0603], 112/161)은 full train을 시작할 충분한 근거인가? 아니면 추가 control이 필요한가?

**Q2.** A1 full train 2 epoch와 3 epoch 중 어느 쪽을 먼저 해야 하는가? 1 epoch 90분, 2 epoch 3시간, 3 epoch 4.5시간(CPU)이다. val 161 best 선택과 early stop을 어떻게 고정해야 하는가?

**Q3.** `summarize: ` prefix를 학습에 넣는 것이 F5 전용으로는 타당한가? bare/prefix dropout과 비교할 가치가 있는가? 다른 task(F4/F6/F3) 재사용 가능성과 분리하는 설계가 충분한가?

**Q4.** EG2→T5의 “최소 adapter” 목표를 위해 B3 pooled soft-prefix를 지금 구현할 가치가 있는가? 아니면 A1 full train을 먼저 완료하고 B3를 후속 exploratory로 두는가?

**Q5.** A2를 raw-vs-seq control 없이 제품 후보에서 종결하는 것이 정당한가? memory-ablation 양성 신호를 남기되, 추가 decoder LoRA를 하지 않는 판단이 맞는가?

**Q6.** A1 val161의 지표 구성이 충분한가? char F1, grounded, new-slot micro, EOS, repeated4, copy rate, 길이를 봤다. ROUGE-L, BERTScore, 사람 수용도, slot-free 6건 처리 중 무엇이 필수인가?

**Q7.** 6/161 summary slot-free 문서의 grounded를 vacuous로 볼 때, G-C5 grounded 100%를 어떻게 보고해야 하는가? gate 분모에서 제외해야 하는가, 별도 표기해야 하는가?

**Q8.** A1 full train에서 LoRA target을 q/k/v/o r8로 유지할 것인가, FFN 또는 rank 16을 추가할 것인가? T5Gemma2 merged attention 구조에서 우선순위는?

**Q9.** test 163은 A1 full train best val 1개에만 1회 사용하는 현 계획이 맞는가? B3를 병행할 경우 test를 어떻게 배분해야 하는가?

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

> A1 pilot300의 val 161 결과가 full train을 시작할 충분한 근거인지, `summarize: ` prefix를 F5 전용으로 고정해도 되는지, B3 soft-prefix bridge를 지금 실험할 가치가 있는지 판정해 주세요.
