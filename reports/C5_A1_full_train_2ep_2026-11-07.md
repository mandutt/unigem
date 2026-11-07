# C5 A1 full train 2 epoch — 결과 보고 (2026-11-07)

## 실행

| 항목 | 값 |
|---|---|
| 결정 | **D-083** |
| 데이터 | F5 clean **train 1,293 / val 161**; test 163 미사용 |
| 설정 | 2 epoch = **2,586 step**, batch 1, prefix `summarize: `, lr **2e-4**, LoRA q/k/v/o **r8 alpha16 dropout0.05**, weight decay 0.01 |
| checkpoint | 647 / 1,293 / 1,940 / 2,586 |
| 실행 | **exit 0**, wall **15,617.9초 = 4시간 20분 18초** |
| final adapter | `data/models/f5_t5gemma2_lora/full_2ep/adapter.pt` (5,994,111 bytes) |
| test 163 | **미사용** |

## checkpoint val161

| checkpoint | char F1 | grounded | new slot (micro) | EOS | repeated4 | slots/doc | slot preservation | gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **pilot300** (fallback) | 0.657580 | **161/161 (1.0000)** | **0** | **161/161** | 0.05535 | 5.199 | 0.45583 | **PASS** |
| 647 | 0.669853 | 155/161 (0.9627) | 6 (0.00684) | 160/161 | 0.06840 | 5.447 | 0.48729 | FAIL |
| 1,293 | 0.665946 | 159/161 (0.9876) | 2 (0.00234) | **161/161** | 0.05866 | 5.304 | 0.45705 | FAIL grounded |
| 1,940 | **0.682278** | 158/161 (0.9814) | 4 (0.00465) | **161/161** | 0.05138 | 5.342 | 0.47610 | FAIL grounded |
| 2,586 | 0.668982 | 159/161 (0.9876) | 3 (0.00394) | **161/161** | **0.04450** | 4.733 | 0.41882 | FAIL grounded |

## Selection

D-083 gate:

```text
grounded_rate >= 0.99
new_slot_rate_micro <= 0.01
EOS >= 0.95
repeated4 <= 0.06
```

결과: **full train checkpoint 중 eligible 없음.**

- 1,940이 char F1 **0.682278**로 full train 최고지만, grounded **0.9814**로 gate 미달.
- 2,586은 grounded **0.9876**으로 가장 높은 full-train 수준이지만, 여전히 0.99 미달.
- 647은 grounded **155/161**와 repeated4 **0.0684**로 gate 미달. EOS 160/161 = 0.9938은 기준 0.95를 통과하므로 EOS 실패가 아니다.
- 따라서 D-083의 fallback 규칙에 따라 **pilot300을 fallback 후보로 유지**한다. 이는 제품 승격이 아니다.

`selection.json` / `selection_summary.json`:

- full train selected: **null**
- fallback: **pilot300**
- pilot300: F1 **0.6576**, grounded **161/161**, new slot **0**, EOS **161/161**, repeated4 **0.0554**

## Paired 비교

| 비교 | mean diff | 95% bootstrap CI | 승/패 |
|---|---:|---:|---:|
| 1,940 − pilot300 | **+0.024698** | **[+0.012027, +0.037295]** | 99 / 61 |
| 2,586 − pilot300 | +0.011402 | [−0.000398, +0.023058] | 92 / 69 |
| 1,940 − 2,586 | **+0.013297** | **[+0.001197, +0.024928]** | 86 / 75 |

해석:

- 1,940은 pilot300보다 **F1이 유의하게 높다.** 그러나 grounded gate를 통과하지 못한다.
- 2,586은 pilot300 대비 F1 우위가 **유의하지 않다** (CI가 0을 포함).
- 1,940 > 2,586은 유의하지만, **grounded가 더 나쁘다.**
- 따라서 “F1 최고”와 “gate 통과”가 분리되어 있으며, **F1만으로 1940을 선택하면 안 된다.**

## Grounded 실패의 내용

- 2,586: **159/161**; non-vacuous **148/150 (0.9867)**, slot-free 11/161.
- 1,940: **158/161**; non-vacuous 0.9809, slot-free 4/161.
- 1,293: **159/161**; non-vacuous 0.9869, slot-free 8/161.
- 647: **155/161**; non-vacuous 0.9623, slot-free 2/161.

`grounded`는 신규 slot 없음만 검사한다. `slot_preservation`은 full train 0.419~0.487로 pilot300 0.456과 비슷하거나 낮다. **사실 보존은 여전히 미해결**이다.

## 판정

1. **Full train 자체는 정상 완료**됐다. NaN·중단·RSS 초과 없음.
2. **Full train checkpoint는 D-083 gate를 통과하지 못했다.** 특히 grounded가 0.99에 도달하지 않았다.
3. **pilot300 fallback을 유지**한다. full train 1,940을 제품 후보로 승격하지 않는다.
4. **test 163은 계속 봉인**한다. 사람 50건도 아직 실행하지 않았다.
5. 다음 결정은 gate를 사후 변경하는 것이 아니라, **grounded 실패 원인 분석**(slot-free/누락/오류 유형)과 새 사전등록 실험으로 풀어야 한다.

## 다음 후보 (승인 필요)

| 후보 | 내용 | 비용 |
|---|---|---:|
| A | 1,940/pilot300의 grounded 실패 50건 유형 분석 | 1~2시간 |
| B | grounded가 높은 1,293/2,586을 기준으로 **사람 50건 rubric** | 2~3시간 human |
| C | full train **seed 43** 재현 | ~4.5시간 CPU |
| D | gate/목표 재설계 — 사후 변경 금지, 새 D-084 사전등록 필요 | 결정 필요 |

## 산출물

- `reports/provenance/C5_a1/full_2ep/eval_step_{0647,1293,1940,2586}/`
- `reports/provenance/C5_a1/full_2ep/selection.json`
- `reports/provenance/C5_a1/full_2ep/selection_summary.json`
- `data/models/f5_t5gemma2_lora/full_2ep/adapter.pt`
- `data/models/f5_t5gemma2_lora/full_2ep/checkpoints/step_{0647,1293,1940,2586}.pt` (각 5.99MB)
- `logs/C5/a1_full_train_2ep.log`
- `logs/C5/a1_full_train_2ep_watch.log`
- test 163: **미사용**
