# A2-null LayerNorm×5 retrain 결과

- 날짜: 2026-11-06
- 실행: `runner/c5_a2null_full_train.py --out data/models/f5_a2null_full_ln --epochs 1`
- 조건: EOS 수정 label + adapter 출력 `LayerNorm(640) × 5`

## 1. 학습

| 항목 | 값 |
|---|---:|
| train / val | 1,293 / 161 |
| steps | 1,293 |
| elapsed | **2,561.9초 (42.7분)** |
| train loss | **3.2513** |
| val loss | **3.1288** |
| final RSS | **2,145.4MB** |
| adapter | `data/models/f5_a2null_full_ln/adapter.pt` |

## 2. Val 5건 생성

`max_new_tokens=128`, greedy.

| id | gen_len | eos | char F1 | grounded | new slot |
|---|---:|---|---:|---|---:|
| REPORT-news_r-00365-00001 | 129 | False | 0.1893 | False | 0.6667 |
| REPORT-news_r-00420-00001 | 129 | False | 0.1606 | False | 1.00 |
| REPORT-news_r-02318-00002 | 123 | **True** | 0.3227 | False | 1.00 |
| REPORT-news_r-04679-00001 | 129 | False | 0.3135 | False | 0.6667 |
| REPORT-news_r-03915-00001 | 129 | False | 0.1486 | False | 1.00 |

평균:

- char F1 **0.2269**
- grounded **0/5**
- new slot **0.8667**
- **eos 1/5** (한 건만 정지, 내용은 반복)

## 3. 비교

| arm | char F1 | grounded | new slot | eos |
|---|---:|---|---:|---:|
| 기존 label 결함 | 0.1603 | 0/5 | 0.90 | 0/5 |
| EOS 수정 | **0.2297** | 0/5 | 0.96 | 0/5 |
| EOS + LayerNorm×5 | 0.2269 | 0/5 | **0.8667** | **1/5** |

LayerNorm은 EOS 1건을 만들고 신규 슬롯을 약간 줄였지만, char F1은 EOS 수정보다 낮고 grounded는 여전히 0이다. **스케일 불일치는 주원인이 아니었다.**

## 4. 판정

- A2-null은 **adapter-only + T5 decoder 완전 동결**로는 usable하지 않다.
- EOS·스케일을 고쳐도 decoder가 반복 붕괴에서 벗어나지 못했다.
- 다음 병목은 **decoder 적응**이다.

## 5. T5Gemma2 구조 확인

T5Gemma2 decoder는 **self/cross merged attention**을 쓴다.

```text
self_attn = T5Gemma2MergedAttention
  q_proj: Linear(640 → 1024)
  k_proj: Linear(640 → 256)
  v_proj: Linear(640 → 256)
  o_proj: Linear(1024 → 640)
```

T5처럼 별도 `EncDecAttention` 모듈이 없다. 따라서 Exa에서 본 **T5-large XA-only**를 그대로 이식할 수 없고, decoder LoRA를 q/k/v/o에 적용하는 방식이 현실적이다.

## 6. 다음 후보

1. **decoder LoRA** — q/k/v/o, rank 8~16, adapter와 함께 학습. merged attention이라 self/cross가 함께 적응한다.
2. **decoder 전체 LoRA + 더 많은 epoch** — 1 epoch로 부족한지 확인.
3. **A1 T5Gemma2 LoRA** — A2-null이 계속 실패하면 최종 abstractive 경로로 전환.

## 7. 산출물

- train report: `data/models/f5_a2null_full_ln/train_report.json`
- predictions: `reports/provenance/C5_a2null/a2null_ln_val5_predictions.jsonl`
- train log: `logs/C5/a2null_full_ln.log`
- watchdog state: `logs/C5/a2null_full_ln_watch_state.json`
