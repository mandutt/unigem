# C5 EG2 concat 1280 pretest — layer12 단독보다 열세 (2026-11-08)

## 1. 목적

EG2 layer12 512와 final 768을 concat(1280)하면
layer12 단독보다 teacher hidden alignment가 개선되는지 확인한다.

## 2. 결과

| input | adapter | params | val cosine |
|---|---|---:|---:|
| final 768 | MLP768 | 1,084,033 | 0.6998 |
| **layer12 512** | MLP1536 | 1,772,929 | **0.7747** |
| concat 1280 | linear | 821,121 | 0.7157 |
| concat 1280 | MLP768 | 1,477,249 | 0.7345 |
| concat 1280 | MLP1536 | 2,952,577 | 0.7450 |

- concat은 layer12 단독보다 **−2.97%p** (MLP1536 기준)
- final 768을 붙이면 **noise/redundancy**가 커진다.
- adapter capacity를 늘려도 concat의 손실을 회복하지 못한다.

## 3. 판정

**CONCAT_HURTS_HIDDEN_ALIGNMENT**

- concat 1280은 **기각**
- B2 concat 300은 실행하지 않는다.
- **layer12 512 단독이 최적**이다.

## 4. 다음

- EG2 **layer6 / layer9** 스캔으로 layer12가 최적인지 확인
- 이후 slot auxiliary/copy 또는 on-policy KD

## 5. 산출물

- `data/wave2c/eg2_concat/` (train 300 / val 100, 1280d)
- `runner/c5_concat_cache.py`
- `reports/provenance/C5_b1d/concat_pretest.json`
- test 163 미사용
