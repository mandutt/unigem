# C5 B2 layer12 300 — offline slot repair (2026-11-08)

## 1. 요약

B2 layer12 val100 출력에 문장 단위 slot repair를 적용했다.

- 원본: F1 **0.3464**, grounded **21%**
- drop-new-sentences: grounded **100%**, F1 **0.2929**
- oracle subset: grounded **100%**, F1 **0.3076**
- **grounded 100%의 F1 상한은 0.308**로, 원본보다 낮다.
- grounding post-processing만으로는 제품 품질에 도달하지 못한다.

## 2. 결과

| 방법 | grounded | char F1 | preservation | missing | gen_len |
|---|---:|---:|---:|---:|---:|
| 원본 | 21% | **0.3464** | 0.2512 | 927 | 443.2 |
| drop-new-sentences | **100%** | 0.2929 | 0.1424 | 1,065 | 197.2 |
| oracle subset | **100%** | **0.3076** | 0.1384 | 1,070 | 136.6 |

- n=100, n_sentences_mean **3.54**, n_bad_sentences_mean **2.10**
- new slot **322** → 0
- oracle subset은 target을 사용하는 **상한**이며 배포 가능한 방법이 아니다.

## 3. 해석

- layer12 feature로 F1/grounded는 개선됐지만, **문장 절반 이상이 new slot을 포함**한다.
- new-slot 문장을 제거하면 grounded 100%는 달성되지만,
  **F1이 0.346 → 0.293**으로 하락하고 preservation도 0.251 → 0.142로 악화된다.
- oracle subset도 **0.308**로, A1 native(0.6576)의 절반 수준이다.
- **slot repair는 안전 필터일 뿐**이며, 생성 단계의 grounding 개선이 필요하다.

## 4. 다음

1. **decoder LoRA r16** — free-running/EOS 개선 여지
2. **slot auxiliary / copy mechanism** — new slot 생성 억제
3. **slot-constrained decoding** — 추론 시 source에 없는 slot 금지
4. **on-policy KD** — exposure bias

## 5. 산출물

- `reports/provenance/C5_b1d/slot_repair_layer12_val100.json`
- `reports/provenance/C5_b1d/slot_repair_layer12_val100.jsonl`
- `runner/c5_b2_slot_repair.py` (relative path handling 수정)
- test 163 미사용
