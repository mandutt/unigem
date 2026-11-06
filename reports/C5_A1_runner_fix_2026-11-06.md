# C5 A1 runner 수정 보고 (2026-11-06)

## 범위

3-AI 검토의 코드 Must-fix 중 **full train 실행 전에 필요한 runner 변경**만 수행했다.

- `runner/c5_a1_lora.py`
- `runner/c5_a1_eval_batch.py`
- `runner/c5_a1_select.py` (신규)
- `eval/tests/test_a1_runner.py` (신규)

**full train은 실행하지 않았고, test 163도 사용하지 않았다.**

## 변경 내용

| 항목 | 변경 |
|---|---|
| LoRA 인자 wiring | `build_model(rank, alpha, dropout)` 추가; `attach_lora`에 실제 전달 |
| epoch reshuffle | `build_order(n, seed, epoch)`로 epoch마다 새 permutation; `seed+epoch` 기록 |
| checkpoint 저장 | `--checkpoint-dir`, `--checkpoint-steps 647,1293,1940,2586`, `--save-every N` |
| checkpoint val eval | `--eval-checkpoints`; checkpoint마다 `eval_step_XXXX/eval.jsonl` + `eval.metrics.json` |
| step-time stop | `--step-time-limit` (기본 60초); 초과 시 exit 4 |
| RSS stop | `--rss-limit-gb` (기본 13GB); 초과 시 exit 3 |
| optimizer | `--weight-decay` (기본 0.01)를 AdamW에 명시 |
| adapter contract | checkpoint에 `format_version`, rank/alpha/dropout, prefix, max_input/max_target, tokenizer eos/pad, decoder start, label format, optimizer, reshuffle 저장 |
| eval metrics | `slot_preservation_mean/min`, missing/zero docs, slots/doc, slotfree docs, non-vacuous grounded rate, prefix/max_input/max_new/adapter 추가 |
| checkpoint 선택 | `runner/c5_a1_select.py` — gate 통과 후 max char F1, tie는 이른 step |

## 검증

### 1. 정적 검사

```text
py_compile: PASS
unittest discover -s eval/tests: 14 tests OK
```

### 2. LoRA wiring smoke

```text
--rank 4 --alpha 8 --dropout 0.1 --steps 1 --no-save
lora_modules 144
trainable_params 737,280  (rank8의 1,474,560과 구분)
step 4.87초, RSS 1.73GB
```

### 3. checkpoint 저장

```text
--steps 2 --checkpoint-steps 1 --checkpoint-dir .../checkpoints --adapter .../adapter.pt
```

- `checkpoints/step_0001.pt` 저장
- 종료 시 `adapter.pt` 저장
- metadata:
  - `format_version=2`
  - `rank=4`, `alpha=8`, `dropout=0.1`
  - `input_contract`: prefix, max_input 1024, max_target 512, eos 1, pad 0, decoder_start 2
  - `optimizer`: AdamW, lr, weight_decay
  - `reshuffle=epoch`

### 4. step-time stop

```text
--step-time-limit 0.1 --steps 1
{"event":"step_time_stop","step":1,"step_seconds":4.85,"limit":0.1}
exit 4
```

### 5. checkpoint eval

```text
--steps 2 --checkpoint-steps 1 --eval-checkpoints --eval-limit 1 --eval-max-new 32
```

- `eval_step_0001/eval.jsonl` + `eval.metrics.json` 생성
- 최종 `eval.jsonl` + `eval.metrics.json` 생성
- metrics에 `slot_preservation`, `slots_per_doc`, `slotfree_docs`, `grounded_rate_nonvacuous` 포함

### 6. checkpoint selection

합성 metrics로 gate 동작 확인:

- step1: grounded 1.00, F1 0.64 → eligible
- step2: grounded 0.98, F1 0.66 → ineligible
- 결과: **step1 선택**

## Full train 실행안 (아직 미실행)

```bash
.venv/Scripts/python.exe -u runner/c5_a1_lora.py \
  --mode full \
  --steps 2586 \
  --lr 2e-4 \
  --prefix "summarize: " \
  --rank 8 --alpha 16 --dropout 0.05 --weight-decay 0.01 \
  --checkpoint-steps 647,1293,1940,2586 \
  --checkpoint-dir data/models/f5_t5gemma2_lora/full_2ep/checkpoints \
  --eval-checkpoints --eval-limit 0 \
  --adapter data/models/f5_t5gemma2_lora/full_2ep/adapter.pt \
  --out reports/provenance/C5_a1/full_2ep
```

선택:

```bash
.venv/Scripts/python.exe runner/c5_a1_select.py \
  --root reports/provenance/C5_a1/full_2ep
```

예상:

- 학습 2,586 step × 약 4.2초 ≈ **3.0~3.6시간**
- checkpoint val161 평가 4회 + 최종 1회 ≈ **1~1.5시간**
- 총 **4~5시간** CPU, peak RSS 약 2.5GB
- test 163은 선택 후 최종 후보 1회만

## 남은 것

1. **full train 승인** — 아직 실행하지 않았다.
2. **selection gate 사전등록** — `grounded ≥ 0.99`, `new-slot micro ≤ 0.01`, `EOS ≥ 0.95`, `repeated4 ≤ 0.06`을 full train 전에 확정해야 한다. 이 값은 현재 reviewer-proposed guardrail이며 제품 gate와 동일하지 않다.
3. **gradient accumulation** — 현재 구현하지 않았다. 계획의 “batch 1 + accumulation” 문구는 batch 1로 정정하거나 별도 구현이 필요하다.
4. **B1d bridge** — 별도 실험이다. `encoder_outputs` 경로·oracle/NLL control은 아직 구현하지 않았다.
5. **full train 후** — `slot_preservation`을 포함한 val161 표, 사람 50건, test 163 1회.

## 산출물

- 코드: `runner/c5_a1_lora.py`, `runner/c5_a1_eval_batch.py`, `runner/c5_a1_select.py`
- 테스트: `eval/tests/test_a1_runner.py`
- test 163: **미사용**
