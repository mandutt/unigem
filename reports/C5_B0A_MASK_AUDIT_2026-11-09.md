# C5 B0-A Copyable Mask Audit

- 작성일: 2026-11-09
- 범위: train 20 / val 20 (`val[5:25]`), no training, test 163 미사용
- 목적: as-run mask의 coverage와 candidate stricter rule을 **보고만** 함
- 규칙 변경: **없음**

---

## 1. As-run rule

현재 `copyable_mask()`:

1. NFKC 정규화
2. source와 target piece에서 공백 제거
3. target token이 special이 아니고 letter/digit을 포함하며
4. 공백 제거한 piece가 source에 substring으로 존재하면 copyable=1

이 규칙은 한국어 단일 음절·조사·어미를 매우 쉽게 match시킨다.

---

## 2. Coverage

| split | docs | target tokens | mean | median | p05 | p95 |
|---|---:|---:|---:|---:|---:|---:|
| train | 20 | 4,312 | **0.8351** | 0.8322 | 0.7813 | 0.8766 |
| val | 20 | 4,093 | **0.8246** | 0.8307 | 0.7574 | 0.8721 |

- B0-A aggregate의 val coverage **0.8246**와 일치한다.
- 문서별 편차는 작고, 거의 모든 target token이 copyable로 표시된다.
- 기존 guard는 `median < 0.10`만 막으므로 **upper coverage를 통제하지 못한다.**

---

## 3. Candidate stricter rule — 보고만

Candidate: normalized piece length **>= 2** (한국어 2음절 이상).

| split | docs | copy tokens | mean | median | p05 | p95 |
|---|---:|---:|---:|---:|---:|---:|
| train | 20 | 927 | **0.2161** | 0.1996 | 0.1133 | 0.2891 |
| val | 20 | 974 | **0.2427** | 0.2282 | 0.1667 | 0.3365 |

- As-run 대비 coverage가 약 **1/3.4**로 감소한다.
- 이것은 **채택안이 아니다.** 새 mask rule은 새 사전등록과 사용자 승인이 필요하다.
- B0-A의 as-run 결과는 historical로 보존한다.

---

## 4. Sample audit

- 각 split에서 mask=1 token 최대 100개를 sample로 저장했다.
- 출력에는 doc_id, token_id, piece, source_context가 포함된다.
- `sample_status`: **manual/blind adjudication required**.
- 자동 집계를 precision으로 부르지 않는다.

산출물:

- `reports/provenance/C5_b0a/mask_audit_train.json`
- `reports/provenance/C5_b0a/mask_audit_val.json`

---

## 5. 판정

```text
as-run mask: historical, coverage 0.8246 val / 0.8351 train
candidate strict: candidate only, coverage .2427 val / .2161 train
rule change: none
B0-A reinterpretation: none
```

- B0-A의 `Δshuffled_copy`는 **CE 정렬 결함 + 과잉 관대 mask**의 이중 영향을 받는다.
- 다음 실험 전에 **새 사전등록**으로 mask rule, upper-coverage guard, primary/secondary metric을 고정해야 한다.
- B0-B/B1/B2/Stage C는 계속 미승인이다.
