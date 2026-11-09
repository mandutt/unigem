# C5 B0-A Phase 5 — P0 Native Sanity

- 작성일: 2026-11-09
- 범위: native mT5 encoder memory + frozen decoder, **no training**
- train 20 / val 20 (`val[5:25]`), 5 length-matched donors
- source prefix: `summarize: `
- test 163: **미사용**
- P1: **미사용**
- B0-B/B1/B2/Stage C: **미실행**

---

## 1. 목적

B0-A의 primary metric은 CE 정렬 결함으로 손상됐고, F/L dropout 비대칭과 mask 과잉 관대 문제가 있었다.

P0는 **학습 없이** native mT5 encoder가 만든 source memory를 사용해,

> 실제 source memory가 길이-matched shuffled source memory보다 target copy/full CE를 낮추는가?

를 확인한다. 이것은 **metric/path sensitivity** 진단이며, EG2 bridge나 decoder adaptation의 성능 증거가 아니다.

---

## 2. 결과

| split | docs | mean Δcopy | copy CI | mean Δfull | real copy CE | wrong copy CE | copy coverage |
|---|---:|---:|---|---:|---:|---:|---:|
| train | 20 | **+3.7617** | [1.8917, 5.6050] | **+3.5027** | 12.7022 | 16.4639 | .8351 |
| val | 20 | **+5.2375** | [2.5013, 8.0753] | **+5.2936** | 13.2352 | 18.4727 | .8246 |

- positive documents: train **14/20**, val **18/20**
- copy guard failed: **false** both
- bootstrap: 1,000 document resamples, paired
- `Δ = wrong − real`; positive means real source memory is better

### 판정

```text
train: SENSITIVE_POSITIVE
val:   SENSITIVE_POSITIVE
```

판정 규칙은 descriptive:

```text
SENSITIVE_POSITIVE   = mean Δcopy > 0 and bootstrap CI lower > 0
INSENSITIVE_NEGATIVE = mean Δcopy <= 0 and bootstrap CI upper < 0
INCONCLUSIVE         = otherwise
```

이는 새 threshold가 아니다.

---

## 3. 해석

### 확립

- 새 same-position CE metric은 native source vs shuffled source를 **강하게 구분한다.**
- `Δcopy`와 `Δfull`이 같은 방향이고 크다.
- copy coverage와 guard가 정상 범위다.
- mT5 encoder → frozen decoder 경로는 aligned metric에서 작동한다.

### 확립되지 않음

- EG2 layer19 memory가 같은 sensitivity를 갖는다는 것
- adapter/LoRA가 이 sensitivity를 보존하거나 개선한다는 것
- decoder adaptation이 content selectivity를 만든다는 것
- B0-A 결과의 재해석

특히 P0의 Δcopy 절대값을 B0-A의 Δcopy와 직접 비교하면 안 된다. memory source, adapter, training 상태가 다르다.

---

## 4. 결정

```text
P0 = SENSITIVE_POSITIVE (metric/path sanity pass)
B0-B = 미승인
B1/B2/Stage C = 미승인
Phase 6 P/M = 새 사전등록 + 별도 승인 필요
```

### 다음

1. **Phase 6 P/M 사전등록서 작성**
   - P: native mT5 encoder + decoder LoRA
   - M: training-only mean memory
   - 20/20, original seeds, final checkpoint only
   - 새 threshold 없음; 기존 B0-A threshold를 소급 변경하지 않음
2. P/M 실행 전 **사용자 승인**
3. P/M 결과 후에도 B0-B 자동 승인 없음

---

## 5. 산출물

| 경로 | 내용 |
|---|---|
| `reports/provenance/C5_b0a/p0_native_sanity.json` | 원시 결과 |
| `reports/provenance/C5_b0a/p0_native_sanity.log` | 실행 로그 |
| `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md` | 이 보고서 |
| `runner/c5_mt5_lora_b0.py` | `--mode p0-sanity` |
| `eval/tests/test_c5_b0_metric.py` | P0 donor/decision tests |

## 6. 재현

```bash
cd C:/code/unigem
.venv/Scripts/python.exe runner/c5_mt5_lora_b0.py \
  --mode p0-sanity \
  --train-limit 20 --val-limit 20 --val-start 5 \
  --donor-count 5 \
  --out reports/provenance/C5_b0a/p0_native_sanity.json
```
