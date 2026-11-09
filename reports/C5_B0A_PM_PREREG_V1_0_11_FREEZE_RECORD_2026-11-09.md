# C5 Phase 6 P/M — v1.0.11 Freeze Record

- 동결일: 2026-11-09
- 승인: 사용자 명시 승인 ("좋아 승인할게")
- 3-AI 최종 판정: **CONTINUE 3/3**
  - GLM 5.3 Flash max
  - DeepSeek 1017 high
  - Sol 6.1 medium
- pre-freeze Must-fix: **none**
- test 163: **sealed**
- P1: **unused**
- T5Gemma2: **D-108 STOP**

## 1. 동결 대상

| 항목 | 경로/값 |
|---|---|
| 계획서 | `docs/plan_c5_b0a_pm_prereg_v1_0_11.md` |
| 계획서 SHA-256 | `327a3e34f5bb2721b8b2400718dfd7bc56a0946641d1e83e2c8b454bf656d007` |
| freeze commit | `6fad89e59e4aa2222010f2360e5eb4c2572c4023` |
| freeze manifest | `docs/plan_c5_b0a_pm_prereg_v1_0_11_FREEZE.json` |
| manifest commit | `05b7abe9a011ff1f7e0095dc7d2be37c61e0266e` |
| freeze manifest SHA-256 | `f5d9ac8a1ce8528991b7ae6f7f9eda8f3ef2b6d29df29d05489f2cbfa9f34764` |
| p1 manifest SHA-256 | `69af129a4f58f7400189c361ba2447f12e17d35f012d7a36c26efdf485a3a2dc` |
| golden SHA-256 | `30cbd1c1281235d0750c2bf9271b82cbe55eb64f099d8226216e14b2020ed3f6` |
| preflight SHA-256 | `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` |
| registered seeds | `20261108`, `20261109`, `20261110` |

- SHA-256은 **committed Git blob bytes(LF)** 기준입니다. Windows CRLF 작업 파일 hash와 다릅니다.
- `_FREEZE.json` 내부 `manifest_commit`은 `null`입니다.
- 실제 manifest commit은 `reports/provenance/C5_b0a/freeze_manifest_commit.txt`에 기록했습니다.

## 2. helper commits

| 파일 | commit |
|---|---|
| `runner/c5_mt5_layer_probe.py` | `949df7a521cd0e002a06ceec872bcafe1ea7eeb0` |
| `runner/c5_a1_lora.py` | `3f9f69f1c0966212d986248253ccdfc38bf7ee6f` |
| `runner/c5_mt5_lora_b0.py` | `d4a953874e1ac2d2a91a9f6d77ae71e521886635` |
| `runner/c5_a2null_eval.py` | `93b056c8165334bd5710815e96596bd8c506d382` |

## 3. 승인 범위

- v1.0.11 freeze: **승인**
- 구현 + unit tests: **승인**
- D0: **승인**
- D1: **미승인**
- 3-seed: **미승인**
- B0-B/B1/B2/Stage C: **미승인**
- test 163 개봉: **금지**
- P1 사용: **금지**
- T5Gemma2 재개: **금지** (D-108 STOP)

## 4. 구현 계약

```text
runner/c5_pm_phase6.py
  -> own training loop
  -> own eval loop
  -> c5_pm_stats.bootstrap_paired_v2
```

- `train_arm` import/call 금지
- `evaluate_arm` import/call 금지
- legacy `bootstrap_paired` import/call 금지
- Phase 6 path = transitive call graph rooted at entrypoint
- pre-freeze helper edit 없음
- post-freeze 수정은 numbered ERRATA만

## 5. 제한

- 이 동결은 D1/3-seed/B0-B/B1/B2/Stage C 승인이 아닙니다.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아닙니다.
- 동결 후 계획 변경은 ERRATA로만 가능합니다.
