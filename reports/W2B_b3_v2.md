# Wave 2B V2 — B3 reader-only result

- Completed: 2026-11-05 11:16 KST
- Arm: `b3_v2_s42`
- Vocab: V2 1,329 chars (head 1,330)
- Init: `data/wave2b/ckpt_v2/w2a_fc_concat_s42_v2head.pt` (character-remapped 2A reader)
- Data: `data/wave2b/feats_10h_v2` (Wave 1 6h + V2 short 4h; 7,463 clips, 10.0221h)
- Dev: `data/wave2b/dev_500.jsonl`, 500 utterances, 7,755 chars
- Sampler: balanced (b4 40%, b8 30%, b16 30%)
- CPU; batch 2; grad accumulation 4; seed 42; 12 epochs

## Result

| Epoch | Loss | Dev CER | Errors / chars | Sec |
|---:|---:|---:|---:|---:|
| 1 | 1.0387 | 0.3226 | 2,502 / 7,755 | 622.5 |
| 2 | 0.7068 | 0.3090 | 2,396 / 7,755 | 618.5 |
| 3 | 0.5820 | 0.3024 | 2,345 / 7,755 | 613.2 |
| 4 | 0.4577 | 0.2903 | 2,251 / 7,755 | 619.3 |
| 5 | 0.3453 | 0.2941 | 2,281 / 7,755 | 624.4 |
| 6 | 0.2584 | 0.2814 | 2,182 / 7,755 | 625.1 |
| 7 | 0.1771 | 0.2807 | 2,177 / 7,755 | 635.2 |
| 8 | 0.1102 | 0.2735 | 2,121 / 7,755 | 629.6 |
| 9 | 0.0684 | 0.2754 | 2,136 / 7,755 | 621.8 |
| 10 | 0.0420 | 0.2709 | 2,101 / 7,755 | 610.0 |
| 11 | 0.0334 | 0.2696 | 2,091 / 7,755 | 616.3 |
| **12** | **0.0279** | **0.2682** | **2,080 / 7,755** | 650.3 |

- **Best/final: dev CER 0.2682**
- B0′ V2 baseline: **0.3701**
- Point difference: **−0.1019 (−10.19%p)**
- Checkpoints:
  - `data/wave2b/ckpt_v2/b3_v2_s42.pt`
  - `data/wave2b/ckpt_v2/b3_v2_s42.best.pt`

## Interpretation

B3 V2 shows a large short-data effect on dev 500. This is not yet the full gate:
B3-nat V2 (same 10h clip set, natural sampler) and paired utterance bootstrap
are still running/pending. The final comparison must use the same V2 head and
the pre-registered dev 500 primary rule; test remains sealed until selection.

## B3-nat control (final)

- Arm: `b3nat_v2_s42`, natural sampler, same 10h clip set
- Best epoch 11: **0.2633** (2,042 / 7,755)
- Final epoch 12: 0.2634
- B3 − B3-nat: **+0.490%p**, paired 95% CI **[-0.229, +1.205]**
- Sampler effect is not significant at 12 epochs.

The frozen candidate remains **B3 v2 s42**; B3-nat is not a candidate.
