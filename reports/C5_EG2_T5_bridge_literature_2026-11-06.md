# EG2 → T5Gemma2 최소 adapter bridge — Exa 문헌 조사

- 날짜: 2026-11-06
- 질문: T5Gemma2의 범용 생성 능력을 EG2 embedding과 최소 학습으로 연결할 수 있는가?
- A2-null의 external memory 방식과 대안 비교
- 주의: 아래 사례는 대부분 vision/audio/LLM 또는 NMT 실험이며, EG2 text + T5Gemma2 270M에서 그대로 재현된 결과가 아니다.

## 0. 결론

**가능성은 있다. 그러나 “shape만 맞추는 adapter”로는 안 된다.**

가장 유망한 인터페이스는:

```text
EG2 embedding
→ small trainable adapter
→ K개의 soft token (T5Gemma2 hidden 640)
→ T5Gemma2 encoder input embeddings 앞에 prepend
→ native encoder + decoder가 그대로 생성
```

A2-null은 반대로 했다:

```text
EG2 feature → adapter 640
→ decoder의 external encoder_outputs (cross-attention memory)
→ decoder는 frozen
```

즉 **T5Gemma2 encoder를 건너뛰고 decoder에 직접 memory를 주입**했다. 이 방식은 decoder cross-attention이 새 분포를 읽도록 학습해야 하는데, decoder가 frozen이라 실패했다.

## 1. 가장 직접적인 사례

### Gemini Embedding as a Universal Multimodal Encoder

- frozen Gemini Embedding API → **17M MLP adaptor** → **k virtual tokens** → frozen LLM(Qwen3-4B)의 prefix
- LLM은 완전 frozen; adaptor만 학습
- task별 supervision(예: image classification)으로 학습; GPU에서 <1분/태스크
- **핵심**: external memory가 아니라 **LLM 입력의 virtual token prefix**로 주입

URL: https://kangwooklee.com/blogs/gemini_embedding_as_universal_multimodal_encoder_for_LLMs.html
- blog/engineering report, peer-reviewed 아님
- image/audio 대상; text EG2에 그대로 적용한 것은 아님

### LatentPress

- frozen decoder가 **continuous memory token**을 **input-embedding interface**로 직접 읽음
- 작은 writer: decoder의 **0.18~0.25%** 파라미터
- decoder weights는 전부 frozen; writer만 학습
- 단, writer는 **reader-matched**: decoder의 frozen 2 layers를 재사용해 text segment를 soft token으로 압축
- QA/context compression용; summarization fine-tuning은 아님

URL: https://arxiv.org/html/2609.01507

### LLINK (Language as Modality)

- frozen multilingual encoder → **contrastive projector** → **K soft slots** at reserved position
- **Stage A**: encoder embedding → LLM latent space
- **Stage B**: soft slots + **low-rank LoRA**로 decoder가 그 신호를 실제로 사용하도록 학습
- “decoder may still disregard the aligned representation without explicit training signals”라고 명시
- **시사점**: adapter-only alignment만으로는 decoder가 신호를 무시할 수 있으므로, 소량의 decoder LoRA가 필요할 수 있다.

URL: https://arxiv.org/html/2510.27254

### eP-ALM

- frozen perceptual encoder + frozen LM
- **linear projection만** trainable; encoder의 여러 layer [CLS] token을 LM의 여러 layer에 주입
- task-specific training; image/audio
- **시사점**: “최소 파라미터” 연결은 가능하지만, **어느 layer에 주입하느냐**가 중요

URL: https://doi.org/10.48550/arxiv.2303.11403

### Mixing and Matching Encoders/Decoders

- independently trained NMT encoder/decoder를 결합
- **dimension adapter + representation adapter transformer layers**를 encoder와 decoder 사이에 삽입
- encoder/decoder는 frozen; adapter만 end-to-end 학습
- adapter-only가 부족할 때 **2-stage: adapter 학습 후 decoder 일부 unfreeze**
- **시사점**: 서로 다른 두 모델의 representation space를 연결하려면 단순 linear projection보다 **representation adapter layers**가 필요할 수 있다.

URL: https://aclanthology.org/2024.moomin-1.5.pdf

### VLAP

- frozen vision encoder → **single linear layer** → frozen LLM의 **word embedding space**
- optimal transport assignment + image captioning objective로 linear layer 학습
- **시사점**: decoder가 이해하는 **word embedding space**로 매핑하는 것이 핵심; 임의의 640d memory가 아니다.

URL: https://arxiv.org/html/2404.09632

### SLM (Speech-Language Model)

- frozen speech encoder + frozen LLM + **adapter (few transformer layers)**
- adapter 출력을 LLM의 **text embedding space**에 매핑하고, text instruction과 concatenate
- next-token prediction loss로 adapter 학습; 1% 파라미터
- **시사점**: adapter는 “few transformer layers”가 필요할 수 있고, **text embedding space로의 매핑**이 중요

URL: https://arxiv.org/pdf/2310.00230

## 2. Embedding inversion (Vec2Text)

- dense embedding에서 원문 text를 복원하는 방법
- zero-step model + iterative corrector; 32-token text 92% exact (원 논문)
- **최소 학습으로 general generation**이라기보다는 **별도 inversion model + iterative decoding**이 필요
- EG2 embedding → text reconstruction → T5Gemma2 summarization 파이프라인은 가능하지만:
  - inversion model 학습이 별도로 필요
  - reconstruction이 원문과 완전히 같지 않으면 요약 품질 저하
  - latency가 multi-step
- **A2 bridge보다 무겁고, “최소 학습”과 거리가 있다.**

URL: https://aclanthology.org/2023.emnlp-main.765/
URL: https://github.com/vec2text/vec2text

## 3. T5Gemma2 구조상 중요한 점

T5Gemma2 `forward`는 `encoder_outputs`를 받으면 encoder를 건너뛰고 그 hidden state를 decoder에 넘긴다.

```python
if encoder_outputs is None:
    encoder_outputs = self.encoder(...)
encoder_hidden_states = encoder_outputs.last_hidden_state
decoder_outputs = self.decoder(..., encoder_hidden_states=...)
```

즉 A2는 **encoder를 완전히 우회**했다. 반면 soft-prefix 방식은:

```python
inputs_embeds = concat([adapter(EG2), tok_embed(passage)], dim=1)
encoder_outputs = model.encoder(inputs_embeds=inputs_embeds, attention_mask=...)
```

로 **T5Gemma2 encoder를 정상 사용**한다. encoder/decoder가 pretrained 분포에 가깝게 유지된다.

## 4. 제안 — B1 soft-prefix bridge

A2를 재개하는 대신, 별도 exploratory로:

```text
EG2 token features (768 or pooled)
→ MLP/resampler adapter
→ K soft tokens (640d, K=8~32)
→ T5Gemma2 encoder inputs_embeds 앞에 prepend
→ frozen T5Gemma2 encoder+decoder
→ summary labels로 adapter만 학습
```

- **B1**: adapter only, decoder frozen
- **B2**: B1 + q/k/v/o LoRA (작게) — LLINK/ACP 결과처럼 decoder가 soft token을 무시할 때
- **B3**: pooled EG2 embedding → MLP → K soft tokens (더 단순)
- **공통**: `summarize:` prefix 없이도 가능; task-specific 데이터는 필요
- **평가**: clean val 161, A0/A1과 동일 지표

### B1이 A2와 다른 점

| | A2-null | B1 soft-prefix |
|---|---|---|
| EG2 → T5 | adapter → decoder external memory | adapter → encoder input soft tokens |
| T5 encoder | **우회** | **사용** |
| decoder | frozen | frozen (B1) / LoRA (B2) |
| distribution | decoder cross-attn에 직접 | native encoder→decoder 경로 |
| prefix | 없음 | 없음 (soft token) |

## 5. 범용성에 대한 결론

- **task-specific adapter**는 여전히 task-specific이다. summary 1,293쌍만 학습하면 다른 task에 쓰기 어렵다.
- **범용 bridge**를 원하면:
  1. **multi-task instruction tuning**: summarize/correct/tag 데이터를 섞고 task prefix 사용
  2. **task-agnostic pretraining**: 대규모 text로 EG2→T5 soft token reconstruction/denoising
  3. **task별 adapter 분리**
- `summarize:` prefix는 **task cue**일 뿐이며, 없애려면 B1/B3에서 bare 입력으로 학습하면 된다.
- T5Gemma2 base는 frozen이므로, F5 adapter가 다른 task에 영향을 주지는 않는다. 단 F5 adapter를 재사용하면 요약으로 편향된다.

## 6. 추천 순서

1. **B3 pooled soft-prefix** — 가장 단순, adapter MLP만; 300~1,000 step
2. **B1 token soft-prefix** — EG2 token sequence → K soft tokens
3. **B2 + decoder LoRA** — B1이 decoder에서 무시될 때
4. A1 full train은 별도로 유지; B1/B3와 val 161 비교

## 7. 참고 링크

- https://kangwooklee.com/blogs/gemini_embedding_as_universal_multimodal_encoder_for_LLMs.html
- https://arxiv.org/html/2609.01507
- https://arxiv.org/html/2510.27254
- https://doi.org/10.48550/arxiv.2303.11403
- https://aclanthology.org/2024.moomin-1.5.pdf
- https://arxiv.org/html/2404.09632
- https://arxiv.org/pdf/2310.00230
- https://aclanthology.org/2023.emnlp-main.765/
- https://github.com/vec2text/vec2text
