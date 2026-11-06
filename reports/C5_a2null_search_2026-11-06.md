# A2-null 생성 붕괴 원인 조사 — Exa 검색 + 로컬 검증

- 날짜: 2026-11-06
- 대상: `runner/c5_a2null_full_train.py`, `runner/c5_a2null_train.py`, `runner/c5_a2null_eval.py`
- 상태: **코드 결함 1건 확정·수정, full retrain 미실행**

## 1. 결론

### 1.1 확정된 코드 결함 — label에 `<bos>`가 들어가고 `<eos>`가 없음

T5Gemma2 tokenizer는 target 문자열 앞에 `<bos>`(id 2)를 자동으로 붙이지만, `<eos>`(id 1)는 붙이지 않는다.

기존 학습 코드는 이 tokenizer 출력을 그대로 label로 사용했다.

```text
tokenizer(summary) = [<bos>, ...content..., .]
labels             = [<bos>, ...content..., .]   # eos 없음
```

T5Gemma2의 `prepare_decoder_input_ids_from_labels()`는 label을 오른쪽으로 shift하고 맨 앞에 `<bos>`를 붙인다.

```text
decoder_input = [<bos>, <bos>, ...content...]
```

따라서 모델은

1. 첫 번째 target으로 `<bos>`를 예측하도록 학습되고,
2. 문장이 끝날 때 `<eos>`를 예측하는 법을 배우지 못한다.

생성은 `<bos>`에서 시작해 `<eos>` 없이 `max_new_tokens`까지 진행한다. 반복 붕괴와 정지 실패에 직접 부합하는 결함이다.

**수정 내용**

- `add_special_tokens=False`로 `<bos>`를 제거
- content 뒤에 `<eos>`를 명시적으로 추가
- 이후 padding은 `-100`으로 mask
- `max_target - 1`로 truncate해 `<eos>` 자리를 확보

수정 후 label:

```text
[...content..., <eos>, -100, -100, ...]
decoder_input = [<bos>, ...content..., <eos>, <pad>, ...]
```

검증:

- 2-step full-train smoke: exit 0, train loss 8.6310
- 20-step pilot: exit 0, 여전히 미학습 붕괴(20 step은 정상 범위)
- tokenizer/label 확인: `<bos>` 0개, `<eos>` 1개, padding 337개

**기존 full train 결과(train loss 3.2487, val loss 3.1196)는 이 결함 때문에 무효다.**

### 1.2 보조 가설 — adapter 출력 스케일 불일치

로컬 실측:

| 대상 | mean | std | norm mean | norm max |
|---|---:|---:|---:|---:|
| adapter 출력 (3 val records) | -0.11 ~ -0.16 | **10.4 ~ 12.9** | **162.5 ~ 210.8** | **1,912 ~ 2,100** |
| T5Gemma2 encoder hidden (1 passage) | -0.043 | **5.08** | **126.3** | **404.7** |

adapter 출력의 std가 T5 encoder hidden의 약 2배, max norm이 약 5배다. Cross-attention의 key/value가 과도한 스케일이면 attention logit이 포화되어 고빈도 토큰 반복으로 이어질 수 있다.

아직 인과관계는 미확인. EOS 수정 후에도 붕괴하면 `LayerNorm(640) × 5`(T5 encoder norm 평균에 맞춘 초기화) 또는 learnable output scale을 적용한다.

### 1.3 Decoder 적응 부족 — Exa 근거

Exa 검색에서 확인한 관련 근거:

- **T5-large XA-only** 모델 카드: decoder cross-attention + final layer norm만 학습(100.7M / 737M, 13.7%)해도 SQuAD F1 **0.8128**; LoRA r=8(2.4M) **0.8152**, full fine-tune **0.8162**. "architecture alignment dominates over brute-force optimization."
- **Encoder-decoder adapters**: seq2seq에는 encoder self-attention, decoder self-attention, decoder cross-attention의 세 적응 지점이 있으며, 재작성/요약에서는 cross-attention이 가장 중요할 수 있다고 설명.
- **To Adapt or to Fine-tune (arXiv 2208.14559)**: 요약에서 일반적으로 full fine-tuning > adapter; 단, 극저자원(수백~3,000 예시)에서는 adapter가 대등하거나 우세. 우리 1,293쌍은 경계 구간.
- **Low-Rank Adaptation for Multilingual Summarization (arXiv 2311.08572)**: LoRA는 저자원에서 full fine-tuning보다 안정적이고 우수; 단 decoder-only 중심 연구라는 한계.

현재 A2-null은 **adapter만 학습**하고 T5 decoder는 완전 동결이다. Exa 근거는 "external memory를 decoder가 쓰려면 cross-attention을 적응시키는 것이 효과적"이라는 방향을 지지한다.

### 1.4 T5Gemma2 특정 이슈 — 현재는 해당 없음

Exa에서 확인한 HuggingFace 이슈:

- **#45521 / #45540**: T5Gemma2 cross-attention cache가 encoder 길이 ≥ sliding_window일 때 잘못 truncate되는 버그. 5.22.1에서는 `_prepare_cache_for_generation()`이 cross-attention을 full attention으로 설정하도록 수정되어 있음.
- 우리 환경: transformers **5.22.1**, memory length **629~910**, decoder `sliding_window=512`. Cross-attention cache는 full로 설정되므로 이 버그에는 해당하지 않는다.
- `decoder_start_token_id`는 config에서 `None`이지만, generation은 `bos_token_id=2`로 fallback한다. 수정된 학습 label도 decoder input을 `<bos>`로 시작하므로 train/generation이 일치한다.

### 1.5 반복 붕괴 일반론 — 지금은 decoder 훈련 문제가 우선

- Holtzman et al. (arXiv 1904.09751): likelihood/beam search가 반복을 선호하는 degeneration.
- Welleck et al. (arXiv 1908.04319): unlikelihood training으로 반복 토큰 확률을 낮춤.
- Yan et al. (arXiv 2206.02369, DITTO): 문장 반복의 self-reinforcement.
- Exposure bias (arXiv 2109.08705): teacher-forced loss가 free-running 생성 품질을 보장하지 않음.

`no_repeat_ngram_size`, `repetition_penalty`, beam search는 **진단용**으로는 유용하지만, 근본 원인(label/decoder 적응)을 가릴 수 있으므로 최종 해법으로 먼저 쓰지 않는다.

## 2. Exa 검색 쿼리

- frozen pretrained seq2seq decoder external encoder memory adapter repetitive generation
- adapter only versus LoRA decoder abstractive summarization limited data
- T5Gemma2 encoder_outputs external memory generation attention mask
- null space projection injection intermediate text hidden layers embedding model
- neural text generation repetition degeneration causes fixes teacher forcing
- T5 encoder_outputs different encoder adapter projection decoder fine-tuning
- summarization repetition penalty no_repeat_ngram_size beam search

## 3. 출처

- Encoder-decoder adapters: LoRA on a seq2seq model — https://posttrainllm.com/docs/learn/encoder-decoder-adapters/
- T5-large XA-only SQuAD model card — https://huggingface.co/medelharchaoui/t5-large-xa-only-squad
- To Adapt or to Fine-tune: A Case Study on Abstractive Summarization — https://arxiv.org/html/2208.14559
- Low-Rank Adaptation for Multilingual Summarization — https://arxiv.org/html/2311.08572v2
- T5Gemma2 long-input cross-attention cache issue — https://github.com/huggingface/transformers/issues/45521
- T5Gemma2 cross-attention cache fix — https://github.com/huggingface/transformers/issues/45540
- HuggingFace generation strategies — https://huggingface.co/blog/how-to-generate
- The Curious Case of Neural Text Degeneration — https://arxiv.org/html/1904.09751v2
- Neural Text Degeneration with Unlikelihood Training — https://arxiv.org/html/1908.04319v2
- Learning to Break the Loop (DITTO) — https://arxiv.org/html/2206.02369v2
- Relating Neural Text Degeneration to Exposure Bias — https://arxiv.org/pdf/2109.08705v1.pdf

## 4. 다음 순서

1. **EOS 수정 label로 full retrain 1 epoch** (약 45분) → val 5건 생성
2. 그래도 붕괴하면 adapter 출력 정규화(`LayerNorm × 5`)만 추가해 재학습
3. 그래도 붕괴하면 decoder cross-attention LoRA 또는 XA-only
4. A2-null이 살아나면 A1 T5Gemma 2 LoRA와 val 비교
5. test 163은 최종 후보 1회만

## 5. 주의

- 기존 full train 산출물(`data/models/f5_a2null_full/adapter.pt`)은 label 결함 상태다. **재학습 전까지 성능 근거로 사용하지 않는다.**
- 20-step pilot의 붕괴는 학습량 부족과 label 결함이 겹친 결과이므로 A2-null 자체의 실패로 해석하지 않는다.
- Exa 결과 중 T5 XA-only는 SQuAD QA 모델 카드이므로 요약 성능으로 직접 일반화하지 않는다.
