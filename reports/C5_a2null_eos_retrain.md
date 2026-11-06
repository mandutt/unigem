# A2-null EOS 수정 full retrain 결과

- 날짜: 2026-11-06
- 실행: `runner/c5_a2null_full_train.py --out data/models/f5_a2null_full_eos --epochs 1`
- 수정: target label = `content + <eos>` (`<bos>` 제거, `add_special_tokens=False`)

## 1. 학습

| 항목 | 값 |
|---|---:|
| train / val | 1,293 / 161 |
| steps | 1,293 |
| elapsed | **2,539.7초 (42.3분)** |
| train loss | **3.2525** |
| val loss | **3.1160** |
| final RSS | **1,998.2MB** |
| adapter | `data/models/f5_a2null_full_eos/adapter.pt` (4.3MB) |

기존 label 결함 상태의 full train(train/val 3.2487/3.1196)과 loss 값을 직접 비교하지 않는다. label 정의가 바뀌었다.

## 2. Val 5건 생성

`max_new_tokens=128`, greedy.

| id | gen_len | eos | char F1 | grounded | new slot |
|---|---:|---|---:|---|---:|
| REPORT-news_r-00365-00001 | 129 | False | 0.0628 | False | 1.00 |
| REPORT-news_r-00420-00001 | 129 | False | 0.2462 | False | 1.00 |
| REPORT-news_r-02318-00002 | 129 | False | 0.2727 | False | 1.00 |
| REPORT-news_r-04679-00001 | 129 | False | 0.3388 | False | 0.80 |
| REPORT-news_r-03915-00001 | 129 | False | 0.2277 | False | 1.00 |

평균:

- char F1 **0.2297** (기존 0.1603)
- grounded **0/5**
- new slot **0.96**
- **5/5가 128 토큰 상한까지 생성, `<eos>` 없음**

출력 예:

```text
10일 서울 강남구 신촌동에 위치한 롯데백화점 롯데백화점 롯데시네마 ...
```

## 3. 판정

- EOS label 수정은 **char F1을 0.1603 → 0.2297로 개선**했다.
- 그러나 **EOS를 전혀 생성하지 못했고**, 반복·환각·신규 슬롯 문제가 남아 있다.
- 따라서 **EOS 수정만으로는 A2-null이 usable해지지 않는다.**
- 1 epoch·adapter-only·T5 decoder 완전 동결 조건의 한계로 본다. EOS는 175토큰 중 1개라 class imbalance도 있다.

## 4. 다음 후보

1. **adapter 출력 정규화**: 실측 adapter norm mean 162~211 / max 1,912~2,100 vs T5 encoder 126 / 405. `LayerNorm(640) × 5`로 스케일을 맞춘다.
2. **decoder cross-attention LoRA / XA-only**: Exa 근거(T5-large XA-only 13.7% params F1 0.8128)와 현재 frozen decoder 병목에 부합.
3. **더 많은 epoch**: EOS 학습과 반복 완화에 필요할 수 있으나, decoder 적응 없이 2 epoch만 늘리는 것은 우선순위가 낮다.
4. **A1 T5Gemma 2 LoRA**: A2-null이 계속 실패하면 최종 abstractive 경로로 전환.

## 5. 산출물

- adapter: `data/models/f5_a2null_full_eos/adapter.pt`
- last checkpoint: `data/models/f5_a2null_full_eos/last.pt`
- train report: `data/models/f5_a2null_full_eos/train_report.json`
- predictions: `reports/provenance/C5_a2null/a2null_eos_val5_predictions.jsonl`
- train log: `logs/C5/a2null_full_eos.log`
- watchdog: `logs/C5/a2null_full_eos_watch_state.json`
