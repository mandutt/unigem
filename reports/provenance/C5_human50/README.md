# C5 human 50 — single-rater rating workflow

## Files

- `reports/C5_human50_primary_rating_sheet.html` — blind primary sheet (200 ratings)
- `reports/provenance/C5_human50/manifest.json` — frozen 50-doc sample, arm order, sessions, hashes
- `runner/c5_human50_expand_ratings.py` — maps blind `slot` export to canonical `arm`
- `runner/c5_human50_single_rater_analysis.py` — pre-registered analysis

## Primary pass

1. Open `reports/C5_human50_primary_rating_sheet.html` in a browser.
2. Rate all 50 docs × 4 summaries (A–D), 5 sessions of 10 docs.
3. The sheet autosaves in `localStorage`.
4. When progress reaches **200 / 200**, click **JSONL 내보내기**.
5. Save the download as `reports/provenance/C5_human50/primary_raw.jsonl`.

The raw export intentionally contains `slot` (0–3), not `arm`.

## Convert and analyze

```bash
.venv/Scripts/python.exe runner/c5_human50_expand_ratings.py \
  --input reports/provenance/C5_human50/primary_raw.jsonl \
  --output reports/provenance/C5_human50/primary_ratings.jsonl
```

The converter uses the frozen manifest to map `slot` → `arm`.

## Repeat pass

After at least 7 days:

1. Generate the repeat sheet from the same manifest (10 docs × 4 summaries).
2. Rate 40 repeats; do not look at primary scores.
3. Export `repeat_raw.jsonl`; convert it to canonical arm-labelled rows (the converter accepts `pass: 2` rows).
4. Run the analysis only after primary + repeat are complete:

```bash
.venv/Scripts/python.exe runner/c5_human50_single_rater_analysis.py \
  --ratings reports/provenance/C5_human50/primary_ratings.jsonl
```

## Important

- Do not change the manifest, sample, rubric, arm order, or decision rule after ratings start.
- Do not use test 163.
- The result is **single-rater evidence only**; inter-rater reliability is not available.
