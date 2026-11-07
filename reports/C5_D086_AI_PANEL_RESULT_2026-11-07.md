# C5 D-086 AI Panel 결과 — INCONCLUSIVE (2026-11-07)

## 0. 결과 요약

D-086 AI panel 150 calls를 완료했고 **600/600 ratings가 유효**했다.  
그러나 **사전등록된 AI panel gate가 실패**하여 D-086은 **INCONCLUSIVE**로 종료한다.

| gate | 실측 | 기준 | 판정 |
|---|---:|---:|---|
| AI inter-judge ICC(2,1), adequacy | **0.59987** | ≥ 0.60 | **FAIL** |
| Contested rate | **166/200 = 83%** | ≤ 10% | **FAIL** |
| AI ratings valid | **600/600** | 600 | PASS |
| Threads archived | **150/150** + retry 2 | — | PASS |

따라서:

- `status: INCONCLUSIVE`
- `candidate_status: NO_APPROVED_CANDIDATE`
- **pilot300 fallback**
- **test 163 sealed**
- **human calibration 미실행** — AI panel이 primary가 될 수 없으므로 D-086 절차상 진행하지 않음

## 1. 실행

| 항목 | 값 |
|---|---|
| AI tasks | 150 = 3 judges × 50 docs |
| judges | GLM `z-ai/glm-5.3-flash` max / Sonnet `claude-sonnet-5-5` low / Luna `gpt-6-luna` high |
| ratings | 600 |
| 완료 | 150/150 |
| JSON parse | 600/600 |
| retry | Sonnet 2건 (`00871`, `03954`) — delimiter 오류 후 재전송 성공 |
| archive | 150/150 + retry 2 |
| active threads | 0 |

## 2. AI panel 결과

### 2.1 Inter-judge agreement

- adequacy ICC(2,1): **0.5998736140633079**
- 기준 0.60에 **0.000126** 미달
- 즉 3 judge가 “비슷한 점수를 내는가”는 경계선이고, 사전등록 기준으로는 **FAIL**

### 2.2 Contested

- 전체 doc-arm 200
- contested **166**
- 비율 **83%**
- 기준 10% 대비 매우 높음

`contested` 정의:

- adequacy range ≥ 2, 또는
- critical flag의 judge vote가 0/3 또는 3/3이 아님

3 judge 구조에서 critical flag가 조금만 갈려도 contested가 되므로, **83%는 “대부분의 doc-arm에서 judge 의견이 갈렸다”**는 뜻이다.

이 결과는 “AI panel consensus가 안정적이다”라는 가정을 지지하지 않는다.

## 3. Descriptive AI-only contrast

D-086 primary는 금지되어 있지만, 참고용 **AI-only descriptive** 값은 다음과 같다.

| contrast | adequacy mean diff | 95% CI | critical unsupported diff | 95% CI |
|---|---:|---|---:|---|
| **2586 − pilot300** | **+0.04** | [−0.20, +0.28] | −0.02 | [−0.16, +0.12] |
| 2586 − 1293 | +0.16 | [−0.08, +0.40] | −0.12 | [−0.28, +0.04] |
| 1940 − pilot300 | −0.26 | [−0.46, −0.06] | +0.18 | [+0.04, +0.34] |

- 2,586 vs pilot300 adequacy 차이는 **0을 포함**하며, “낫다”는 증거가 없다.
- 1,940은 AI-only descriptive에서도 pilot300보다 낮은 방향이다.
- 이 수치는 **AI panel이 gate를 통과했을 때만** primary가 될 수 있었고, 지금은 **참고용**이다.

## 4. 해석

1. **AI 3-judge consensus는 더 안정적이지 않았다.**
   - ICC는 기준선에 근접했지만 미달.
   - contested 83%는 critical flag 기준에서 judge 분산이 매우 큼을 보여준다.

2. **AI panel 단독으로 제품 후보를 승격할 수 없다.**
   - D-086 사전등록 gate를 지키면 **no approved candidate**다.
   - 결과를 보고 gate를 완화하거나 contested 정의를 바꾸면 post-hoc 변경이다.

3. **human calibration을 실행하지 않은 이유**
   - AI inter-judge/contested gate가 먼저 실패했다.
   - 이 상태에서 20-doc human calibration을 해도 AI panel을 primary로 승격할 수 없다.
   - human rating을 추가로 쓰려면 **새 protocol/amendment**가 필요하다.

4. **pilot300 fallback 유지**
   - D-083 strict `selected_step: null`도 그대로다.
   - 2,586은 여전히 `PROVISIONAL_NOMINEE` 근거가 없다.
   - 1,293/1,940으로 사후 변경하지 않는다.

## 5. 산출물

- `reports/provenance/C5_hybrid/ai_outputs/` — 150 judge outputs
- `reports/provenance/C5_hybrid/ai_ratings.jsonl` — 600 canonical ratings
- `reports/provenance/C5_hybrid/ai_output_validation.json` — 600/600 valid
- `reports/provenance/C5_hybrid/ai_outputs.sha256` — raw output hash
- `reports/provenance/C5_hybrid/ai_panel_aggregated.jsonl` — 200 doc-arm aggregates
- `reports/provenance/C5_hybrid/ai_panel_summary.json` — **INCONCLUSIVE**
- `reports/provenance/C5_hybrid/dispatch_state.json` — 150 done
- `reports/provenance/C5_hybrid/archive_ledger.json` — archived threads
- `reports/provenance/C5_hybrid/dispatch.log`
- `reports/provenance/C5_hybrid/archive.log`

## 6. 다음 선택지

D-086은 **INCONCLUSIVE로 종료**한다. 다음은 별도 결정이다.

1. **pilot300 fallback 유지** — product candidate 없음; test 163 sealed.
2. **새 exploratory AI panel protocol** — human calibration 전에 contested 정의/aggregation을 재설계하되, 이미 결과를 본 상태이므로 **confirmatory가 아닌 exploratory**로 명시.
3. **D-085 human-only 재개** — 1인 human 50; AI panel 결과와 독립적으로 새로 실행. D-085는 현재 superseded 상태이므로 새 amendment/version 필요.
4. **test 163** — 어떤 경우에도 별도 명시 승인 전 금지.

## 7. 최종 상태

| 항목 | 값 |
|---|---|
| D-086 | **INCONCLUSIVE** |
| AI panel | 600/600 valid, gate FAIL |
| human calibration | NOT_RUN |
| candidate | **NO_APPROVED_CANDIDATE** |
| fallback | **pilot300** |
| test 163 | **SEALED** |
| active Hoplite threads | 0 |
