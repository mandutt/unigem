# C5 B0 two-arm runner — smoke result

- 날짜: 2026-11-09
- 범위: **runner 구현 + smoke only**. optimizer step / training / generation 없음.
- 캐시: `data/wave2c/eg2_native_layer19/layer19` (native EG2 tokenizer, layer19, 512d)
- 모델: `data/models/mt5-small`
- test 163 미사용.

## 1. 구현 결과

`runner/c5_mt5_lora_b0.py`에 2-arm runner를 추가했다.

| arm | decoder | trainable |
|---|---|---|
| `frozen` | frozen | adapter only |
| `lora` | frozen base + LoRA | adapter + decoder q/k/v/o LoRA |

LoRA 대상:

```text
decoder.block.*.SelfAttention.q/k/v/o
decoder.block.*.EncDecAttention.q/k/v/o
```

## 2. Smoke 결과

| 항목 | 값 |
|---|---:|
| attached modules | **64 / 64** |
| LoRA rank / alpha / dropout | 8 / 16 / 0.05 |
| LoRA trainable params | **458,752** |
| adapter params | **526,336** |
| frozen arm loss | **27.43998146057129** |
| LoRA arm loss (zero-init B) | **27.43998146057129** |
| loss abs delta | **0.0** |
| logits max abs delta | **0.0** |
| allclose atol 1e-5 | **true** |
| finite | **true** |
| base encoder frozen | **true** |
| test split used | **false** |

**zero-output LoRA가 frozen arm의 forward를 정확히 재현**했다. 즉 attach 경로가 실제 decoder에 붙었고, 초기 LoRA가 base 출력을 바꾸지 않는다.

## 3. 구현 상태

| 항목 | 상태 |
|---|---|
| mT5 decoder q/k/v/o attach | 완료 |
| 64-module assert | 완료 |
| adapter-only vs adapter+LoRA 공통 초기화 | 완료 |
| zero-LoRA 동등성 | 완료 |
| train loop (CE) | 구현됨, **실행 안 함** |
| val real/zero/shuffled ablation | 구현됨, **실행 안 함** |
| generation | **미구현** |
| native encoder positive control | **미구현** |
| memory-free/mean-memory control | **미구현** |
| 복수 length-matched donor / bootstrap | **미구현** |

## 4. 판정

**SMOKE PASS — TRAIN NOT RUN.**

- LoRA attach blocker는 해소됐다.
- 기존 `q_proj` target을 쓰던 경로를 mT5 `q/k/v/o`로 교체할 수 있음을 실제 module inventory와 forward로 확인했다.
- 아직 **B0 학습·평가 실행은 하지 않았다.**
- 3-AI 검토 기준의 정식 B0가 되려면 native positive control, memory-free/mean-memory, 복수 donor, bootstrap이 추가로 필요하다.

## 5. 다음 단계

1. B0 사전등록서 작성
   - 20/20 또는 300/100
   - frozen vs LoRA
   - native positive / memory-free
   - `Δshuffled_copy` + 문서×seed bootstrap
   - inconclusive branch
2. 사용자 승인 후 B0 실행
3. 결과가 pass일 때만 B1 새 decision

## 6. 산출물

- `runner/c5_mt5_lora_b0.py`
- `reports/provenance/C5_b0/mt5_lora_smoke.json`
- `reports/C5_B0_LORA_RUNNER_SMOKE_2026-11-09.md`
- `reports/C5_E0_NATIVE_AUDIT_2026-11-09.md`

## 7. 재현

```bash
cd C:/code/unigem
.venv/Scripts/python.exe runner/c5_mt5_lora_b0.py --mode smoke --train-limit 2 --val-limit 2
```
