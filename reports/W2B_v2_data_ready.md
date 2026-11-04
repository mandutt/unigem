# Wave 2B V2 data preparation — READY

- Finalized: 2026-11-05 08:14 KST
- No GPU rented.
- B0′ V2 CPU training started after data finalization; B3/B3-nat not started yet.

## V2 vocabulary

- File: `data/wave2b/vocab_v2.json`
- Draft all-train vocabulary retained for audit: `data/wave2b/vocab_v2_alltrain.json`
- V1 chars: **1,101**
- Final V2 chars: **1,329**
- New chars: **228**
- V1 char order/IDs preserved; new chars appended in first-seen order.
- V2 CTC head size: **1,330 rows** (blank + 1,329)
- Source: Wave 1 6h manifest + V2-selected short 4h refs.
- No eval/test text used to build the vocabulary.

The earlier draft vocabulary built from all 620,000 Kspon train transcripts had
2,342 chars. It was rejected because the registered V2 definition is
`chars(6h + short 4h)`. The final V2 uses only the 6h train manifest and the
selected short 4h subset.

## OOV audit

Final V2, measured on fixed eval manifests:

| Set | Clips | OOV clips | OOV rate | OOV chars / total | Char rate |
|---|---:|---:|---:|---:|---:|
| dev 500 | 500 | 5 | 1.0000% | 5 / 8,247 | 0.0606% |
| test 2,400 | 2,400 | 45 | 1.8750% | 53 / 40,788 | 0.1299% |
| spare 90 | 90 | 1 | 1.1111% | 1 / 1,473 | 0.0679% |

Test OOV types include `U 갭 굼 깅 댔 둡 뚤 렁 멓 뱃 벚 빕 빽 뺴 뾰 숟 쉴 썽 쏭 욘 좆 짼 쪘 찝 찼 챠 췄 캉 컬 텼 펐 폈`.
The test set was used only for this coverage audit, not vocabulary construction.

## V2 short subset

- Manifest: `data/wave2b/short_4h_v2.jsonl`
- Summary: `data/wave2b/short_4h_v2_summary.json`
- Rows: **5,079**
- Hours: **4.0016**
- Candidate OOV-excluded clips: **2,319 / 97,628 = 2.3753%**
- OOV exclusion is below the 5% threshold in D-067.
- Bins:
  - 0–2s: 1.0002h (2,368)
  - 2–4s: 1.4004h (1,713)
  - 4–6s: 0.8005h (585)
  - 6–8s: 0.8006h (413)
- Folders: 124

## V2 features

| Item | Rows | Frames | Bytes |
|---|---:|---:|---:|
| `feats_short_v2/fc.feats.npy` | 5,079 | 361,329 | 2,960,007,296 |
| `feats_10h_v2/fc.feats.npy` | 7,463 | 901,985 | 7,389,061,248 |

- `feats_10h_v2` hours estimate: **10.0221**
- `feats_10h_v2` rows = 2,384 Wave 1 + 5,079 V2 short.
- Provenance: `reports/provenance/W2B/v2_data_ready.json`
- Sentinel: `data/wave2b/V2_READY.json`

## Head remap

- Utility: `runner/w2b_remap_ckpt.py`
- Input: `data/wave2a_lite/frozen/w2a_fc_concat_s42.best.pt` (1,102 rows)
- Output: `data/wave2b/ckpt_v2/w2a_fc_concat_s42_v2head.pt` (1,330 rows)
- Shared characters copied: **1,101**
- New V2 rows initialized at small normal values.
- Smoke test passed: `missing=0 unexpected=0`; dev CER 0.3711 on one micro-batch.

## Training status

- B0′ V2: **started**, background CPU job, arm `b0p_v2_s42`.
- B3 V2 / B3-nat V2: **not started**.
- The V1 B0′ `0.3663` is not a V2 baseline.
- Next: finish B0′ V2, then B3 V2 (balanced) and B3-nat V2 (natural) from the same remapped initialization.
