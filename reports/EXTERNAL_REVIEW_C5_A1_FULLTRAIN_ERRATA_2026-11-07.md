# Errata — C5 A1 full-train review request (2026-11-07)

대상: `reports/EXTERNAL_REVIEW_C5_A1_FULLTRAIN_2026-11-07.md` (검토 기준 `5694cc7`)
근거: 3-AI 원문 `docs/hoplite/c5_fulltrain_2026-11-07/review_{GLM,OPUS,SOL}.md`

| # | 기존 서술 | 정정 |
|---|---|---|
| 1 | `03978` missing **8개** | **7개** (`1일, 45, 15일, 1, 오전9시30분, 10, 20`) |
| 2 | `04709` missing **18개**, `18명` 포함 | **15개**; `18명`은 missing이 아님. prediction에 두 번 보존됨 |
| 3 | `04709`의 `18` | `18 확진자`에서 추출된 bare number. `18명` 자체는 grounded |
| 4 | trailing punctuation을 v2 신규 normalization으로 기재 | `_canonical`이 이미 모든 kind에 대해 처리. **신규 작업 아님** |
| 5 | v2 교정 시 1,940/2,586만 160/161 | **URL 수정만으로 1,293도 160/161** 가능. full re-selection 필요 |
| 6 | 647의 EOS 160/161을 gate fail로 서술 | EOS 160/161 = 0.9938로 **0.95 기준 통과**. 647은 grounded와 repeated4에서 실패 |
| 7 | “grounded 실패 5건 중 3건”을 전체처럼 서술 | 이 분석은 **1,940/2,586에 한정**. 647/1,293의 미분석 실패가 별도로 존재 |
| 8 | `04951`을 “hallucination”으로 단정 | **source-unsupported extrinsic content**로 표기. real-world-looking이므로 human rubric에서 별도 분류 |

## Strict 결과 불변

- D-083 `selected_step: null`, pilot300 fallback은 **변경 없음**.
- 위 정정은 측정·보고 정합성에 관한 것이며, v2를 적용하거나 gate를 통과시킨 것이 아니다.
- D-084는 아직 **미승인·미작성**이다.
