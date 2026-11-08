# C5 B0 metric / donor / bootstrap / generation implementation smoke

- 날짜: 2026-11-09
- 범위: **구현 + metric smoke only**. training / B0-A / B0-B 실행 없음.
- 모델: mT5-small, native EG2 layer19 cache
- test 163 미사용.

## 1. 구현 완료 항목

`runner/c5_mt5_lora_b0.py`에 B0-A 평가 경로를 추가했다.

| 항목 | 상태 |
|---|---|
| copyable target token mask | 완료 |
| 5 length-matched donor 생성 | 완료 |
| real/wrong prefix crop (`K=min`) | 완료 |
| `Δshuffled_copy` aggregation | 완료 |
| `Δshuffled_full` secondary | 완료 |
| 문서 단위 bootstrap | 완료 |
| copy coverage guard | 완료 |
| val20 greedy generation 경로 | 완료 |
| frozen vs LoRA per-doc 비교 | 완료 |
| B0-A `train` path | 구현됨, **미실행** |
| B0-B 4-arm | 미구현 / 별도 승인 |

## 2. Metric smoke 결과

명령:

```bash
.venv/Scripts/python.exe runner/c5_mt5_lora_b0.py \
  --mode metric-smoke --train-limit 2 --val-limit 2 --val-start 5 \
  --donor-count 2 --smoke-new-tokens 8
```

| 항목 | frozen | LoRA (zero-init) |
|---|---:|---:|
| docs | 2 | 2 |
| `mean_delta_shuffled_copy` | **-0.14960** | **-0.14960** |
| `mean_delta_shuffled_full` | **-0.09768** | **-0.09768** |
| mean copy coverage | **0.78427** | **0.78427** |
| copy guard failed | false | false |
| L−F paired bootstrap mean | — | **0.0** |
| LoRA modules | — | **64** |

- zero-output LoRA이므로 frozen과 LoRA 값이 정확히 같다. **이 숫자는 성능 결과가 아니다.**
- 2문서/2donor smoke이며, B0-A의 20/20·5donor·3seed 결과가 아니다.
- generation은 8 token cap으로 호출해 경로만 확인했다. untrained adapter 출력이므로 품질 판정 아님.
- generation EOS: false, generated length 9. 이는 **붕괴/성공 판정이 아니라 wiring 확인**이다.

## 3. 산출물

- `runner/c5_mt5_lora_b0.py`
- `reports/provenance/C5_b0/metric_smoke.json`
- `reports/provenance/C5_b0/mt5_lora_smoke.json` (attach/zero-LoRA)
- `docs/plan_c5_b0_prereg_v0_1.md`

## 4. 남은 것

- **B0-A 실행**: 20/20, F/L, 3 seeds, 100 updates, 5 donors, val20 generation — **미실행**
- **B0-B**: 300/95, 4 arms — 별도 사전등록·승인
- B0-A 결과를 본 뒤 threshold 변경 금지.

## 5. 판정

**IMPLEMENTATION SMOKE PASS — B0-A NOT RUN.**

- metric/donor/bootstrap/generation 경로가 실제로 호출되고 JSON을 생성했다.
- copy coverage는 smoke에서 78.4%로 guard를 통과했다.
- B0-A 학습은 아직 시작하지 않았다.

## 6. 재현

```bash
cd C:/code/unigem

# attach / zero-LoRA
.venv/Scripts/python.exe runner/c5_mt5_lora_b0.py --mode smoke --train-limit 2 --val-limit 2

# metric/donor/bootstrap/generation wiring (no training)
.venv/Scripts/python.exe runner/c5_mt5_lora_b0.py \
  --mode metric-smoke --train-limit 2 --val-limit 2 --val-start 5 \
  --donor-count 2 --smoke-new-tokens 8
```
