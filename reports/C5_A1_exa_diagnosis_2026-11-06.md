# C5 A1/A2 붕괴 원인 — Exa 문헌 조사 + 로컬 진단

- 날짜: 2026-11-06
- 범위: A2-null 반복 붕괴, A1 T5Gemma2 LoRA pilot의 잔여 반복
- test 163 미사용

## 0. 결론

**단일 버그가 아니라 두 층의 문제다.**

1. **A2-null의 붕괴는 “memory가 없어서”가 아니다.**
   - memory-ablation에서 real vs shuffled ΔNLL **+0.058** (CI >0)로 문서 특정 신호는 있었다.
   - 그러나 A2 adapter-only + **완전 frozen decoder**는 640d external memory를 요약 토큰으로 변환하지 못했다.
   - A2 full val char F1 **0.1277/0.1169**, grounded **0/161, 1/161**.
   - A1 native encoder + decoder LoRA는 pilot 100 step에서 char F1 **0.4659**, grounded **5/5**로 훨씬 정상이다.
2. **A1 pilot의 잔여 반복은 “A2와 같은 붕괴”가 아니라 undertraining·긴 target·greedy decoding의 혼합**으로 보인다.
   - 100 step, EOS 3/5, 2/5가 448 cap, repeated4 0.486.
   - full val 비교는 아직 없다.
3. **label/EOS·pad/EOS 충돌·truncation·target 반복은 이번 데이터에서 배제됐다.**
   - input max **908** (<1024, 0건 초과), target max **439** (<512)
   - pad **0**, eos **1**, bos **2** — 서로 다름
   - clean target repeated4 평균 **0.027** (2.7%) — 데이터 반복이 주원인이라고 보기 어려움

## 1. 로컬 실측

### 1.1 길이·토큰 계약

| 항목 | 값 |
|---|---:|
| clean pairs | 1,617 |
| input tokens mean / p50 / p95 / max | 762.2 / 762 / 828 / **908** |
| input >1024 | **0** |
| target tokens mean / p50 / p95 / p99 / max | 208.9 / 204 / 289 / 333 / **439** |
| target repeated4 mean | **0.0270** |
| pad / eos / bos | **0 / 1 / 2** |

→ **truncation과 pad=eos 버그는 아니다.** T5Gemma2 tokenizer의 pad/eos가 같은 id라는 흔한 무한 생성 원인도 해당 없음.

### 1.2 A2-null vs A1

| 항목 | A2-null EOS | A2-null LN | A1 pilot 100 |
|---|---:|---:|---:|
| train/teacher-forced NLL | 3.1160 (val) | 3.1288 (val) | train loss **0.8425** |
| full val char F1 | 0.1277 | 0.1169 | — (val 5: 0.4659) |
| grounded | 0/161 | 1/161 | 5/5 (val 5) |
| EOS | 9.94% | 6.21% | 60% (3/5) |
| repeated4 | 0.870 | 0.847 | 0.486 |
| memory signal | Δshuffled +0.058 | +0.058 | native encoder |

A2의 memory signal은 양성이지만 **decoder가 그 memory를 요약으로 쓰지 못한다.** A1은 native encoder와 attention LoRA로 훨씬 낮은 NLL과 정상적인 요약을 보인다.

## 2. Exa 문헌 조사

### 2.1 Encoder-decoder adaptation

- **Encoder-decoder adapters** (posttrainllm.com): seq2seq에는 encoder self-attention, decoder self-attention, **decoder cross-attention** 세 적응 지점이 있다. cross-attention이 “원문에서 복사·수정할 위치”를 결정하므로 중요하다.
  - A2-null은 external memory adapter만 학습하고 decoder attention은 전부 frozen → cross-attention 적응 부재.
  - A1은 q/k/v/o LoRA로 encoder/decoder attention을 모두 조정.
- **To Adapt or to Fine-tune (arXiv 2208.14559)**: 일반적으로 full FT > adapter. 극저자원에서는 adapter가 대등할 수 있지만, 1,293쌍은 adapter-only가 underfit할 수 있는 경계다.
- **Low-Rank Adaptation for Multilingual Summarization (NAACL 2024 Findings)**: LoRA는 low-data에서 full FT와 경쟁적이며, 특히 저자원 요약에서 유리하다. 단, **target module·rank·steps**가 중요하다.

### 2.2 T5Gemma 2

- **공식 model card / transformers docs**: T5Gemma 2는 encoder-decoder이며 **merged decoder self/cross-attention** 구조다. 270M-270M은 pretrained 모델이고, 128K context, 140+ 언어를 지원한다.
- **HF discussion (google/t5gemma-2-4b-4b)**: 요약 prompt 예시가 `"summarize: [document]"` 또는 `"Summarize the following document..."`다.
- **DataCamp T5Gemma-2 fine-tuning tutorial**: LoRA 예시는 `r=16`, `lora_alpha=32`, **q/k/v/o + gate/up/down**, lr **1e-4**, 1 epoch, `max_target=128`이다.
  - 우리 A1은 r=8, attention only, lr **1e-3**, 100 step, target 512.
  - **lr 1e-3은 튜토리얼보다 10배 높고, FFN은 적응하지 않았다.** loss 진동의 후보.
- **zero-shot**: 270M pretrained는 한국어 요약 instruction-tuned가 아니므로 zero-shot char F1 0.2333, EOS 1.86%는 모델 한계로 해석해야 한다.

### 2.3 반복 붕괴 문헌

- **HF forum “T5 generates repetitive sentences”**: teacher-forced 학습 후 생성에서 같은 문장/구절이 반복되는 사례. padding 부재, max_length 도달, EOS 미학습이 원인 후보로 논의된다.
- **HF forum “Repetitive Answers From Fine-Tuned LLM”**: 반복의 주요 원인으로 ① EOS를 거의 보지 못한 target ② prompt/template까지 loss에 포함 ③ greedy decoding을 든다. `repetition_penalty`는 완화책이지 근본 해결이 아니다.
- **“Repetition In Repetition Out” (arXiv 2310.10226)**: 학습 데이터의 반복이 degeneration과 강하게 연관된다. 우리 clean target repeated4는 **2.7%**로 낮아 주원인 가능성은 작다.
- **“Generic Mechanism for Reducing Repetitions in Encoder-Decoder” (RANLP 2021)**: encoder-decoder가 같은 source token에 반복적으로 attention하는 것이 반복의 한 원인. coverage/attention 제어가 해법.
- **“Decoder-Only or Encoder-Decoder?” (arXiv 2304.04052)**: **attention degeneration** — 생성이 길어질수록 source에 대한 attention이 줄어 반복이 생긴다. 우리 target mean 209, max 448 cap과 부합.
- **Sebastian Raschka repetition FAQ**: greedy decoding은 반복을 결정론적으로 강화한다. decoding penalty는 기본 loop가 올바른 뒤에 쓰는 보조 수단이다.

### 2.4 EOS·pad 계약

- **Unsloth “Fixing bugs in Gemma/Llama/Phi-3”**: pad token과 EOS token이 같으면 EOS가 loss에서 mask되어 **infinite generation**이 발생한다.
- 우리 모델은 pad **0**, eos **1**로 안전. A2/A1 label도 `<eos>`를 명시해 이 경로는 닫혔다.

## 3. 원인 우선순위

| 순위 | 가설 | 근거 | 판정 |
|---:|---|---|---|
| 1 | **A2 adapter-only + frozen decoder의 적응 부재** | A2 NLL 3.12, char F1 0.13; A1 native+LoRA NLL 0.84, char F1 0.47 | **강한 지지** |
| 2 | **A1 undertraining (100 step)** | 2/5가 448 cap, loss 진동, EOS 3/5 | **강한 지지** |
| 3 | **greedy decoding의 반복** | 반복 문헌 공통, penalty가 완화 | **부분 지지** |
| 4 | prompt mismatch (`summarize:` 미사용) | T5Gemma2 공식 예시는 `summarize:` | **미검증·저비용** |
| 5 | lr 1e-3이 너무 높음 | 튜토리얼 1e-4, loss 진동 | **미검증·저비용** |
| 6 | target/data 반복 | repeated4 2.7% | **낮음** |
| 7 | truncation | input max 908 <1024, target max 439 <512 | **배제** |
| 8 | pad=eos | 0 vs 1 | **배제** |
| 9 | label EOS 누락 | 수정 완료, A1도 EOS 3/5 | **부분 배제** |
| 10 | adapter 출력 scale | LayerNorm×5로 개선 없음 | **배제** |

## 4. 권고 — full train 전에 할 일

1. **A1 prompt 일관성 test**: 현재 학습은 bare passage, zero-shot은 한국어 prefix, T5Gemma2 공식 예시는 `summarize:`다. pilot adapter로 `summarize: ` prefix를 붙여 val 5를 비교한다.
2. **A1 learning rate/step diagnostic**: lr **2e-4**, 200~300 step, rank 16 또는 FFN 추가. lr 1e-3/100 step은 수렴 판단에 부족하다.
3. **decoding diagnostic only**: `no_repeat_ngram_size=4`/`repetition_penalty=1.2`를 적용해 반복이 decoding에서 얼마나 줄어드는지 본다. 이는 진단이며 최종 gate를 대체하지 않는다.
4. **A2는 재개하지 않는다**: memory signal은 exploratory 기록으로 남기고, 제품 후보는 A1로 간다.
5. **full train은 위 1~2 결과 후** 별도 승인한다.

## 5. 참고 링크

- https://arxiv.org/html/2208.14559
- https://posttrainllm.com/docs/learn/encoder-decoder-adapters/
- https://huggingface.co/google/t5gemma-2-270m-270m
- https://huggingface.co/docs/transformers/en/model_doc/t5gemma2
- https://huggingface.co/google/t5gemma-2-4b-4b/discussions/1
- https://www.datacamp.com/tutorial/fine-tuning-t5gemma-2
- https://discuss.huggingface.co/t/t5-generates-repetitive-sentences/38305
- https://discuss.huggingface.co/t/repetitive-answers-from-fine-tuned-llm/110024/13
- https://arxiv.org/html/2310.10226v1
- https://aclanthology.org/2021.ranlp-1.180.pdf
- http://arxiv.org/pdf/2304.04052v1
- https://ai.engineer/talks/fixing-bugs-in-gemma-llama-phi-3
- https://sebastianraschka.com/faq/docs/repetition-loops-generation.html

## 6. 한계

- Exa 결과는 preprint/블로그/포럼이며 우리 하드웨어·한국어·T5Gemma2 270M 재현이 아니다.
- A1 full val 161은 아직 없다. A1 pilot 5건은 sanity일 뿐이다.
- A2의 adapter-only 원인은 “frozen decoder”로 좁혀지지만, adapter capacity·memory distribution·cross-attention 부재를 개별 분리한 실험은 아직 없다.
