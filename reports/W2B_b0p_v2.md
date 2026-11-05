# Wave 2B V2 — B0′ reader baseline

- Finished: 2026-11-05 09:10 KST
- Arm: `b0p_v2_s42`
- Vocab: `data/wave2b/vocab_v2.json` (1,329 chars; head 1,330)
- Init: `data/wave2b/ckpt_v2/w2a_fc_concat_s42_v2head.pt`
  - V1 1,102-row head remapped by character to 1,330 rows
  - shared characters: 1,101
- Data: Wave 1 F-C features, 6h (2,384 clips)
- Dev: `data/wave2b/dev_500.jsonl`, Kspon eval_clean 500, 7,755 chars
- Architecture: base CTC reader, 9,183,922 params
- Seed: 42; batch 2; grad accumulation 4; CPU; 12 epochs

## Result

| Epoch | Loss | Dev CER | Errors / chars | Sec |
|---:|---:|---:|---:|---:|
| 1 | 0.1882 | 0.4089 | 3,171 / 7,755 | 273.0 |
| 2 | 0.1294 | 0.3896 | 3,021 / 7,755 | 293.4 |
| 3 | 0.0803 | 0.3947 | 3,061 / 7,755 | 339.2 |
| 4 | 0.0538 | 0.3796 | 2,944 / 7,755 | 269.9 |
| 5 | 0.0281 | 0.3776 | 2,928 / 7,755 | 268.7 |
| 6 | 0.0160 | 0.3709 | 2,876 / 7,755 | 267.4 |
| 7 | 0.0091 | 0.3740 | 2,900 / 7,755 | 269.0 |
| 8 | 0.0063 | 0.3714 | 2,880 / 7,755 | 263.6 |
| 9 | 0.0037 | 0.3705 | 2,873 / 7,755 | 266.9 |
| 10 | 0.0024 | 0.3709 | 2,876 / 7,755 | 263.9 |
| 11 | 0.0021 | 0.3703 | 2,872 / 7,755 | 264.5 |
| **12** | **0.0018** | **0.3701** | **2,870 / 7,755** | 270.2 |

- Best: **epoch 12, dev CER 0.3701**
- Checkpoints:
  - `data/wave2b/ckpt_v2/b0p_v2_s42.pt`
  - `data/wave2b/ckpt_v2/b0p_v2_s42.best.pt`
  - `data/wave2b/ckpt_v2/b0p_v2_s42.last.pt`

## Interpretation

- This is a **V2 6h baseline**, not comparable to V1 B0′ `0.3663` because the
  output head and OOV policy differ.
- V2 test OOV is 1.875% of clips (45/2,400); V1 was 7.71% under the 2A vocab.
- B3 V2 (10h balanced) and B3-nat V2 (10h natural) start from the same
  remapped initialization, not from this B0′ checkpoint.
- CPU epoch time: ~270 s; 12 epochs ≈ 54 min.
