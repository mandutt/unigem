# C5 B1d Full Distillation v0.1

## 0. 목적

B1d interface probe(`PASS_INTERFACE`) 이후, **train 1,293 / val 161 전체**로 teacher-hidden distillation을 수행해 adapter-only B1d의 품질 가능성을 측정한다.

## 1. 범위

- **train 1,293 / val 161**, test 163 **사용 금지**
- teacher: T5Gemma2 native encoder hidden `[T,640]`, `summarize: ` 포함
- student: EG2 text final hidden `[T,768]`, 동일 token sequence
- adapter: token-level 768→768→640, LayerNorm + learnable scale
- **2 epoch** full distillation, per-doc step
- val 161: hidden cosine + norm + generation screen
- generation `max_new_tokens=448`, greedy
- **human/AI panel 없음**
- **decoder LoRA 없음** — B1d adapter 단독

## 2. DoD

| 항목 | 기준 |
|---|---|
| teacher cache | train 1,293 + val 161, coverage 100% |
| student cache | train 1,293 + val 161, coverage 100% |
| token alignment | cache 단계에서 100% assert |
| adapter | train loss 감소, val cosine 기록 |
| generation | val 20 screen; nonempty/EOS/grounded/char F1 기록 |
| test | **미사용** |
| 결과 | **품질 gate 아님**, B1d 가능성 판정 |

## 3. 판정

- generation screen이 degenerate이고 val cosine이 낮으면 → **B2 decoder LoRA 필요**
- generation이 일부 정상이고 hidden cosine이 충분하면 → B1d full 확장 후보
- **어떤 경우에도 test 163은 열지 않는다**
- 제품 후보 승격은 별도 protocol

## 4. 체크포인트

- cache: shard 단위 atomic `.npz`, 존재하는 shard skip
- training: epoch 단위 adapter checkpoint
- generation: doc 단위 JSONL append + `--resume`
- 긴 작업은 background + notify, `process_manage(wait)`

## 5. 산출물

- `data/wave2c/b1d/teacher/{train,val}_*.npz`
- `data/wave2c/b1d/student/{train,val}_*.npz`
- `data/models/f5_t5gemma2_lora/b1d_full/adapter_ep{1,2}.pt`
- `reports/provenance/C5_b1d/full_metrics.json`
- `reports/provenance/C5_b1d/generation_val.jsonl`
- `reports/C5_B1D_FULL_2026-11-07.md`

## 6. 한계

- B1d adapter-only는 decoder frozen이다.
- hidden cosine은 요약 품질과 동일하지 않다.
- generation screen 20은 전체 161 품질을 대표하지 않는다.
- CPU-only, 단일 run.
