# Wave 2B — B0′ reader-only baseline

- Date: 2026-11-04
- Arm: `b0p_s42`
- Data: Wave 1 F-C features, 6h (2,384 clips)
- Dev: `data/wave2b/dev_500.jsonl`, Kspon eval_clean 500, 7,755 chars
- Init: `data/wave2a_lite/frozen/w2a_fc_concat_s42.best.pt`
- Architecture: base reader, 9,096,142 params
- Seed: 42
- Batch 2, grad accumulation 4, threads 6
- Epochs: 12 (no early stop)

## Result

| Epoch | Loss | Dev CER | Errors / chars | Sec |
|---:|---:|---:|---:|---:|
| 1 | 0.1798 | 0.4089 | 3,171 / 7,755 | 295.5 |
| 2 | 0.1249 | 0.3939 | 3,055 / 7,755 | 279.4 |
| 3 | 0.0892 | 0.3961 | 3,072 / 7,755 | 262.0 |
| 4 | 0.0537 | 0.3810 | 2,955 / 7,755 | 263.2 |
| 5 | 0.0318 | 0.3787 | 2,937 / 7,755 | 261.3 |
| 6 | 0.0161 | 0.3732 | 2,894 / 7,755 | 264.6 |
| 7 | 0.0096 | 0.3715 | 2,881 / 7,755 | 266.9 |
| 8 | 0.0051 | 0.3674 | 2,849 / 7,755 | 262.3 |
| 9 | 0.0036 | **0.3663** | **2,841 / 7,755** | 263.6 |
| 10 | 0.0026 | 0.3667 | 2,844 / 7,755 | 263.4 |
| 11 | 0.0020 | 0.3669 | 2,845 / 7,755 | 268.2 |
| 12 | 0.0019 | 0.3670 | 2,846 / 7,755 | 263.5 |

- Best: **epoch 9, dev CER 0.3663**
- Final: epoch 12, dev CER 0.3670
- Checkpoints:
  - `data/wave2b/ckpt/b0p_s42.best.pt`
  - `data/wave2b/ckpt/b0p_s42.pt`

## Interpretation

- This is a **Kspon eval_clean dev 500** baseline, not comparable with Wave 2A FLEURS dev (0.209).
- B0′ uses the same 6h data and F-C features as the prior reader; the lower/higher difference is domain + eval set.
- B0′ is the **6h baseline** for the 10h arms (B3, B3-nat); do not treat it as the final 10h baseline.
- CPU epoch time is about **4.4 minutes**; 12 epochs ≈ 53 minutes.
