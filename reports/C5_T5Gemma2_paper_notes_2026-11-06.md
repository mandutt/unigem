# T5Gemma 2 논문(2512.14856) — A1/A2 현재 상황 관련 메모

- 날짜: 2026-11-06
- 원문: https://arxiv.org/abs/2512.14856 / https://arxiv.org/html/2512.14856
- 용도: A1/A2 설계 해석. 논문은 summarization fine-tuning/LoRA 레시피를 제공하지 않는다.

## 1. 가장 중요한 구조 — merged attention

논문 §2:

```text
Q = X W_q                         # decoder input X
K = [X ; H] W_k                   # decoder self + encoder H
V = [X ; H] W_v
O = Softmax(QK^T / sqrt(d_h) ⊙ M) V W_o
```

- decoder의 **self-attention과 cross-attention이 하나의 모듈**로 합쳐져 있다.
- 따라서 T5Gemma2에는 T5의 별도 `EncDecAttention`이 없다.
- **decoder q/k/v/o를 동결하면 cross-attention뿐 아니라 self-attention까지 적응할 수 없다.**

### A2-null에 대한 직접 해석

A2-null은 external memory adapter만 학습하고 T5Gemma2 decoder는 전부 frozen이었다.

- decoder q/k/v/o가 고정 → external memory `H`에 대한 Q/K/V 투영을 적응할 수 없음.
- encoder도 사용하지 않고 adapter가 만든 640d memory를 `H`로 주입.
- memory-ablation ΔNLL +0.058로 memory signal은 있었지만, free-running generation은 붕괴.
- **A2의 실패는 “memory가 없다”가 아니라 “merged decoder의 Q/K/V/O가 external memory 분포에 적응하지 못했다”로 설명하는 것이 논문과 일치한다.**

### A1에 대한 해석

A1은 native encoder + decoder q/k/v/o LoRA.

- merged attention의 q/k/v/o를 모두 조정 → self-attention과 cross-attention을 동시에 적응.
- A1 pilot300이 A2보다 훨씬 정상 생성(EOS 5/5, repeated4 0.10)인 것과 방향이 일치.
- **A1에서 q/k/v/o를 target으로 잡은 선택은 논문 구조상 타당하다.**

## 2. 파라미터 구조

논문 Table 2 (270M-270M):

| 구성 | params |
|---|---:|
| vision encoder (frozen) | 417M |
| embedding (tied) | 168M |
| encoder non-embedding | 100M |
| decoder non-embedding | 100M |

- 우리가 vision tower를 제거한 text-only model은 **370.6M**으로 이 표와 일치한다.
- **tied word embedding**: encoder input, decoder input, decoder output softmax가 같은 embedding을 공유한다.
- A2 adapter는 external memory를 만들 뿐 tied embedding을 바꾸지 않는다. A2의 문제를 embedding 쪽으로 돌리기는 어렵다.

## 3. Pretraining / post-training

- **pretraining**: Gemma 3에서 초기화, UL2 denoising, **~2T tokens**, input/output up to **16K**.
- **post-training**: distillation만 사용하고 compute가 적음. 논문은 이를 **lower bound**로 표기.
- 270M-270M은 **한국어 요약 instruction-tuned 모델이 아니다.**
- 우리 zero-shot T5 char F1 0.2333, EOS 1.86%는 이 한계와 일치한다.
- **`summarize: ` prefix가 효과 있었던 것은 T5 계열 관례와 post-training의 약한 instruction following에 기대는 부분**으로 해석할 수 있다. 논문이 `summarize:`를 명시하지는 않는다.

## 4. Long context / 절단

- 128K context, 16K pretraining sequences.
- 우리 clean passage max **908 tokens**, target max **439** → 절단은 원인이 아니다.
- long-context 능력은 현재 문제와 무관하다.

## 5. Merged attention ablation

논문 Table 1:

| variant | quality | params |
|---|---:|---:|
| baseline | 47.8 | 4,417M |
| tied embedding | 47.7 | 4,417M (590M) |
| merged attention | 47.5 | 4,049M |
| cross-attention global layers only | 46.5 | 4,233M |

- merged attention은 약 **0.3 point** 손실로 6.5% 파라미터 절감.
- **global layer에만 cross-attention을 두는 변형은 1.3 point 하락** → cross-attention을 모든 층에서 쓰는 것이 중요.
- A2는 external memory를 모든 decoder 층에 넣지만, **Q/K/V/O를 학습하지 않아 이 cross-attention을 적응시키지 못했다.**

## 6. 논문이 직접 답하지 않는 것

- summarization fine-tuning / LoRA hyperparameter (lr, rank, target modules, epoch)
- `summarize:` prompt의 필요성
- EOS/pad label 계약
- 한국어 요약 성능
- A2-null/external memory 주입

따라서 논문은 **구조적 원인**은 설명하지만, **A1 full train hyperparameter**는 우리 실측으로 정해야 한다.

## 7. 현재 판단

1. **A2-null 중단 유지** — merged decoder를 frozen으로 둔 external-memory adapter는 구조적으로 불리.
2. **A1은 native encoder + q/k/v/o LoRA 유지** — 논문의 merged attention 구조와 일치.
3. **`summarize: ` prefix를 A1 학습·평가에 일관되게 사용** — 우리 실측 +0.1459 char F1.
4. **full train은 별도 승인** — 300 step pilot은 아직 full val 161이 아니다.
5. **A1 LoRA를 확장한다면 FFN 또는 rank 16** — 논문의 구조 설명과 T5Gemma2 fine-tuning 예시가 attention-only r8보다 넓은 target을 권한다.
