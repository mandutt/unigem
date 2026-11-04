# Wave 2B data preparation — READY (with V1 OOV caveat)

- Finished: 2026-11-05 01:09 KST
- Download: KsponSpeech_05.zip
  - bytes: **15,641,266,705**
  - PCM entries: **126,545**
  - source: AI Hub dataset 123, filekey 50215
- Short selection: `data/wave2b/short_4h.jsonl`
  - rows: **5,119**
  - hours: **4.0023**
  - bins: 0–2s 1.0001h (2,358), 2–4s 1.4001h (1,748), 4–6s 0.8006h (592), 6–8s 0.8014h (421)
  - folders: 124
- Short feature: `data/wave2b/feats_short/`
  - rows: **5,119**
  - frames: **361,368**
  - `fc.feats.npy`: **2,960,326,784 bytes**
- 10h cache: `data/wave2b/feats_10h/`
  - rows: **7,503** (2,384 Wave 1 + 5,119 short)
  - frames: **902,024**
  - estimated hours: **10.0225**
  - `fc.feats.npy`: **7,389,380,736 bytes**
- Provenance: `reports/provenance/W2B/data_ready.json`

## V1 OOV caveat (blocking decision)

The short-selection V1 policy excluded clips containing characters outside the
2A 1,101-char vocabulary.

- duration-eligible clips: **97,628**
- OOV-excluded clips: **88,575**
- OOV rate: **90.727%**
- OOV by bin:
  - 0–2s: 17,696 / 20,436 = 86.59%
  - 2–4s: 35,635 / 39,561 = 90.08%
  - 4–6s: 21,843 / 23,565 = 92.69%
  - 6–8s: 13,390 / 14,054 = 95.28%

This is far above the 5% threshold in D-067. Under the registered policy,
**B3/B3-nat must not start on this V1 short subset without a separate V2
decision**. The 4h subset is mechanically ready but is selected from the
roughly 9% of duration-eligible clips whose transcripts fit the FLEURS-derived
2A vocabulary; that selection may bias the short-domain experiment.

No GPU was rented and no model training/evaluation was performed in this step.
