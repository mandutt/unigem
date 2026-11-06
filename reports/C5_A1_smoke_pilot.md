# A1 T5Gemma2 LoRA — smoke/pilot 보고

- 날짜: 2026-11-06
- 결정: **D-082** — smoke/pilot만 승인. full train·test 163은 별도 승인.
- 데이터: `data/external/f5_pairs_v3_clean.jsonl` train 1,293 / val 161 (test 163 봉인)
- 코드: `runner/c5_a1_lora.py`
- adapter: `data/models/f5_t5gemma2_lora/pilot100.pt` (5.99MB)

## 0. 결론

- **smoke PASS**: text-only 370.6M params, LoRA 1,474,560 trainable(0.40%), 1 step **4.4~4.7초**, RSS **1.7~1.8GB**.
- **pilot functional**: 100 step 완료, NaN/붕괴 없음, val 5건에서 char F1 **0.4659**, grounded **5/5**, EOS **3/5**, repeated-4 **0.486**.
- **pilot loss는 수렴을 확정하지 못했다**: mean 0.8425, first10 0.8255 → last10 0.7719로 방향은 약간 하락했지만 진동이 크다(0.44~1.15).
- full train은 시작하지 않았다. test 163도 사용하지 않았다.

## 1. 구현

| 항목 | 값 |
|---|---|
| base | `data/models/t5gemma-2-270m-270m` |
| text-only | **370,637,824 params** (vision tower 제거) |
| LoRA 대상 | encoder text + decoder의 q/k/v/o **144 modules** |
| LoRA | rank **8**, alpha **16**, dropout 0.05 |
| trainable | **1,474,560 params (0.40%)** |
| base frozen | yes |
| label | content + `<eos>`, `<bos>` 제거, padding `-100` |
| input / target | max 1024 / 512 tokens |
| optimizer | AdamW, lr 1e-3, grad clip 1.0 |
| precision | bf16 base + float32 LoRA |
| PEFT | 미사용(직접 LoRA wrapper) |

## 2. Smoke

- model load 5.2~5.4초, RSS **1.24~1.28GB**
- 1 step: input 776 tokens, target 293 tokens, loss **0.7268**, **4.4~4.7초**, RSS **1.7~1.8GB**
- 중단 기준(step >60초, RSS >13GB) 대비 충분한 여유

## 3. Pilot 100 step

| 항목 | 값 |
|---|---:|
| steps | 100 |
| wall time | **416.0초** |
| step time | **4.16초** |
| RSS peak | **2.32GB** |
| train loss mean | **0.8425** |
| first-10 mean | 0.8255 |
| last-10 mean | 0.7719 |
| final loss | 0.8530 |
| loss range | 0.4394~1.1530 |
| NaN / nonfinite | **0** |
| adapter size | **5,994,341 bytes** |

50 step 시도는 학습 자체는 완료됐지만 adapter 저장 디렉터리가 없어 저장 단계에서 실패했다. **학습 실패가 아니며**, 100 step 재실행으로 adapter를 확보했다.

## 4. Pilot val 5 생성

| id | char F1 | EOS | gen len | summary slots | new slots |
|---|---:|---|---:|---:|---:|
| REPORT-news_r-00005-00001 | 0.3366 | false | 449 | 6 | 0 |
| REPORT-news_r-00020-00001 | **0.7747** | true | 156 | 9 | 0 |
| REPORT-news_r-00023-00001 | 0.5931 | true | 210 | 8 | 0 |
| REPORT-news_r-00060-00001 | 0.1366 | false | 449 | 1 | 0 |
| REPORT-news_r-00114-00001 | 0.4884 | true | 312 | 3 | 0 |
| **mean** | **0.4659** | **3/5** | 315.2 | 27 | **0** |

- grounded: **5/5**
- new-slot: **0**
- repeated-4-gram mean: **0.4860**
- distinct-2 mean: **0.4485**
- 같은 5건의 A0 char F1: **0.5981** (A1 0.4659; A1이 2/5에서 우세)

이 5건은 **pilot sanity**입니다. full val 161의 성능 주장이 아니며, A1이 A0보다 우수하다는 결론도 아직 아니다.

## 5. DoD 대비

| # | 항목 | 상태 |
|---|---|---|
| 1 | text-only 로드 | **PASS** — 370.6M, vision 제거 |
| 2 | CPU smoke 1 step | **PASS** — 4.7초, RSS 1.8GB |
| 3 | pilot 50~100 step loss/붕괴 | **PARTIAL/INCONCLUSIVE** — NaN·붕괴 없음, 생성은 기능; loss 진동으로 수렴 미확정 |
| 4 | full train | **미실행** — 별도 승인 |
| 5 | test 163 | **봉인** |
| 6 | 사람 50건 | **미실행** |

## 6. 재현

```bash
# smoke
.venv/Scripts/python.exe -u runner/c5_a1_lora.py --mode smoke --steps 1 --no-save

# pilot 100 + val 5
.venv/Scripts/python.exe -u runner/c5_a1_lora.py --mode pilot --steps 100 \
  --eval-limit 5 --adapter data/models/f5_t5gemma2_lora/pilot100.pt \
  --out reports/provenance/C5_a1/pilot100

# adapter reload + 1건 생성 검증
.venv/Scripts/python.exe -u runner/c5_a1_lora.py --mode eval \
  --adapter data/models/f5_t5gemma2_lora/pilot100.pt --eval-limit 1 \
  --out reports/provenance/C5_a1/reload_check
```

## 7. 다음

1. **full train 전에 A1 pilot 연장을 결정**한다. 100 step은 functional signal일 뿐 수렴 근거가 아니다.
2. full train(2~3 epoch)은 **별도 승인** 후 실행한다. 예상: 1 epoch 1,293 step × 4.16초 ≈ **90분**, 2 epoch ≈ 3시간, 3 epoch ≈ 4.5시간(평가 제외).
3. full train 시 val 161로 best checkpoint를 고르고, test 163은 최종 후보 1회만 사용한다.
4. full val 생성은 batch generation으로 처리한다. 현재 `c5_a1_lora.py --mode eval`은 1건씩이므로, full train 전에 batch evaluator를 추가해야 한다.
5. **A2-null 제품 후보 중단**과 decoder LoRA 보류는 유지한다.

## 8. Artifacts

- `runner/c5_a1_lora.py`
- `reports/provenance/C5_a1/pilot100/eval.jsonl`
- `reports/provenance/C5_a1/pilot100/eval.metrics.json`
- `reports/provenance/C5_a1/reload_check/` (adapter reload 검증)
- `data/models/f5_t5gemma2_lora/pilot100.pt` (로컬 보존, git 미포함)
