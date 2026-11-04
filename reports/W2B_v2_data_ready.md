# Wave 2B V2 data preparation — READY

- Finished: 2026-11-05 01:34 KST
- No GPU rented; no model training performed.

## V2 vocabulary

- File: `data/wave2b/vocab_v2.json`
- V1 chars: **1,101**
- V2 chars: **2,342**
- New chars: **1,241**
- V1 char order/IDs preserved; new chars appended in first-seen order.
- V2 CTC head size: **2,343 rows** (blank + 2,342)
- Source: Wave 1 6h manifest + KsponSpeech_05 train transcript (`train.trn`, 620,000 lines).
- No eval/test text used to build the vocabulary.

## OOV audit

| Set | Clips | OOV clips | OOV rate | OOV chars / total | Char rate |
|---|---:|---:|---:|---:|---:|
| dev 500 | 500 | 0 | 0.0000% | 0 / 8,247 | 0.0000% |
| test 2,400 | 2,400 | 1 | 0.0417% | 1 / 40,788 | 0.0025% |
| spare 90 | 90 | 0 | 0.0000% | 0 / 1,473 | 0.0000% |

Test OOV is one occurrence of `뺴`.

## V2 short subset

- Manifest: `data/wave2b/short_4h_v2.jsonl`
- Summary: `data/wave2b/short_4h_v2_summary.json`
- Rows: **5,066**
- Hours: **4.0035**
- V2 OOV-excluded clips: **0 / 97,628 (0.00%)**
- Bins:
  - 0–2s: 1.0002h (2,348)
  - 2–4s: 1.4005h (1,717)
  - 4–6s: 0.8011h (588)
  - 6–8s: 0.8017h (413)
- Folders: 124

## V2 features

| Item | Rows | Frames | Bytes |
|---|---:|---:|---:|
| `feats_short_v2/fc.feats.npy` | 5,066 | 361,486 | 2,961,293,440 |
| `feats_10h_v2/fc.feats.npy` | 7,450 | 902,142 | 7,390,347,392 |

- `feats_10h_v2` hours estimate: **10.0238**
- `feats_10h_v2` rows = 2,384 Wave 1 + 5,066 V2 short.
- Provenance: `reports/provenance/W2B/v2_data_ready.json`
- Sentinel: `data/wave2b/V2_READY.json`

## Important: training not started

V2 changes the CTC head from 1,102 to 2,343 rows. The 2A reader cannot be
loaded directly with `--init-ckpt`; the head must be remapped by character
(V1 character rows copied, new V2 rows initialized). B0′ must also be
retrained under V2 before any B3/B3-nat comparison. The existing V1 B0′
`0.3663` is **not** a V2 baseline.

Next step after approval:

1. Implement character-wise head remap for `--init-ckpt`.
2. Retrain B0′ V2 on 6h.
3. Train B3 V2 (10h, balanced) and B3-nat V2 (10h, natural).
4. Only then consider B1/B2 LoRA and GPU rental.
