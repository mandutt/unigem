# C5 A1 — D-084 rev3 / 084a audit 결과 (2026-11-07)

## 0. 범위

- **D-084 rev3 084a**의 spec-faithful audit.
- 입력: clean **train 1,293 + val 161**, excluded **383**; **test 163 미로드·미평가**.
- 코드:
  - `eval/slot_verify_084a.py` (new, v1과 분리)
  - `runner/c5_a1_verifier_084a_audit.py`
  - `runner/c5_a1_select_084a.py`
  - tests: `eval/tests/test_slot_verify_084a.py`
- v1 `eval/slot_verify.py`는 **수정하지 않음** — SHA256 `a262cee0cd25307a74f3a87995624e2999b47daed9294000f036d27ea1869d03` (검토자 기록과 일치).
- D-083 strict selection은 **미수정**.

## 1. Audit 결과 — val 161

| system | v1 grounded | 084a grounded | new pass | new fail | unresolved |
|---|---:|---:|---|---|---|
| pilot300 | **161/161** | **161/161** | — | — | `01518` |
| 647 | 155/161 | **156/161** | `02742` | 없음 | `01518` |
| **1,293** | 159/161 | **160/161** | `02742` | 없음 | `01518` |
| **1,940** | 158/161 | **158/161** | 없음 | 없음 | `01518` |
| **2,586** | 159/161 | **160/161** | `02742` | 없음 | `01518` |

### 1.1 예상표와 일치

rev3 §3.4의 expected table과 **정확히 일치**했다.

- 647 `155 → 156`
- 1,293 `159 → 160`
- 1,940 `158 → 158`
- 2,586 `159 → 160`
- **new fail 0** across all five systems.
- URL repair `02742`만 new pass를 만들었다.

### 1.2 1,940은 158

- `03978` — time-type; 084a에는 qualifier rule이 없으므로 남는다.
- `04709` — bare `18`; unit/alias는 084b.
- `04951` — `2.3%`, `2.2%` genuine negative control.
- 따라서 1,940은 URL-only에서 158/161이며 **gate-ineligible**이다.

### 1.3 2,586의 160은 한 문서 의존

- 2,586의 new pass는 `02742` 하나뿐이다.
- `04951`은 남는다.
- audit에서 02742 repair가 무너지면 2,586은 159/161로 돌아가고, **eligible full-train candidate가 없어진다.**

## 2. Unresolved — `01518`

`REPORT-news_r-01518-00001`:

- source URL이 `http://topis.`로 passage 끝에서 잘려 있다.
- 084a는 source-side URL을 **unresolved(terminal_punctuation)**로 기록했다.
- summary는 URL을 포함하지 않는다.
- source-side unresolved는 **new slot을 만들지 않으므로 `grounded`를 실패시키지 않는다.**
  - missing/measurement caveat로 별도 보고.
- 이 처리는 rev3의 “source-side unresolved no credit” 원칙과 일치한다.
  - **summary-side unresolved**였다면 grounded를 막는다.

`03992`도 `terminal_punctuation` unresolved로 기록됐다. audit 결과에는 영향이 없다.

## 3. Bidirectional audit

### 3.1 Clean train/val targets

| subset | n | v1 grounded | 084a grounded | changes |
|---|---:|---:|---:|---:|
| train + val clean targets | **1,454** | **1,454** | **1,454** | **0** |

- strictness-induced **new failure 0**.
- `clean` target은 v1 grounded by construction이지만, 084a URL strictness가 실제로 new fail을 만들지 않았다는 **bidirectional 확인**이다.

### 3.2 Excluded 383

| subset | n | v1 grounded | 084a grounded | changes |
|---|---:|---:|---:|---:|
| excluded | **383** | 0 | 0 | **0** |

- 5 old generic flips (2020, 2021, 404, 20, 5000/200)는 **084a에서 재현되지 않았다.**
- 그 5건은 **084b unit-clause evidence**다.
- 084a expected flips = 0; **실측 0**.

## 4. URL census

| 항목 | 값 |
|---|---:|
| URL repair 문서 | **3** (`02742`, `03992`, `04909`) |
| unresolved 문서 | **2** (`01518`, `03992`) |
| unresolved reason | `terminal_punctuation` |

- repair 3건은 source/summary의 URL wrap 후보.
- `fine.fss.`는 unresolved host 후보.
- 04909 trailing slash는 별도 정책으로 unresolved/보존.
- 01518은 source URL이 passage 끝에서 잘린 경우.

## 5. Provisional selection

`reports/provenance/C5_a1/full_2ep/selection_084a_provisional.json`

| system | grounded | new-slot micro | EOS | rep4 | screen | evidence |
|---|---:|---:|---:|---:|---|---|
| pilot300 | 161/161 | 0.00000 | 1.0 | 0.05535 | PASS | INCONCLUSIVE |
| 647 | 156/161 | 0.00570 | 0.9938 | 0.06840 | FAIL (rep4) | INCONCLUSIVE |
| **1,293** | **160/161** | **0.00117** | 1.0 | 0.05866 | **PASS** | INCONCLUSIVE |
| **1,940** | 158/161 | 0.00465 | 1.0 | 0.05138 | FAIL (grounded) | INCONCLUSIVE |
| **2,586** | **160/161** | **0.00262** | 1.0 | 0.04450 | **PASS** | INCONCLUSIVE |

- eligible full train: **2,586, 1,293**
- **provisional nominee: 2,586** (F1 .668982 > 1,293 .665946)
- `strict_d083_selected_step: null`
- `strict_d083_fallback: pilot300`
- `approval_status: NOT_APPROVED`
- `human_50: NOT_RUN`
- `test_163: SEALED`

### 5.1 2,586에 대한 경고

- 2,586은 02742 한 문서로 160/161이 된다.
- F1 차이 vs 1,293는 **.003**; noise 수준.
- 2,586 − pilot300 F1 CI는 0 포함.
- preservation .4188 < pilot .4558; slot-free 11 > 6.
- **eligibility ≠ superiority**; 2,586은 human-review nominee이며 제품 승격이 아니다.
- audit/human에서 실패하면 **no approved candidate**다.

## 6. Gate/CP

- D-083 point screens는 unchanged:
  - grounded ≥ .99
  - new-slot micro ≤ .01
  - EOS ≥ .95
  - repeated4 ≤ .06
- doc-level CP95 lower:
  - 160/161 ≈ .9659
  - 161/161 ≈ .9773
  - 모두 .99 미만.
- slot-level CP95 upper:
  - pilot 0/837 ≈ .44%
  - 1,940 4/860 ≈ 1.19%
  - 2,586 3/762 ≈ 1.15%
- **evidence_status = INCONCLUSIVE** for all systems.
- INCONCLUSIVE는 point-screen eligibility를 자동 제거하지 않는다. selection rule을 vacuous하게 만들지 않기 위해서다.
- “PASS”는 99% population certificate가 아니다.

## 7. 결론

1. **084a implementation은 rev3 expected table과 일치**했다.
2. **new fail 0**, clean train/val changes 0, excluded flips 0.
3. **1,940은 158/161로 gate-ineligible**; 1,940 quality evidence는 human exploratory로만 남긴다.
4. **2,586/1,293은 160/161로 screen PASS**; 2,586 provisional nominee.
5. **2,586은 02742 한 문서 의존**; no-candidate branch가 필요하다.
6. **084b unit/alias는 audit selection에 사용하지 않았다.**
7. **test 163은 봉인**, human 50은 미실행.
8. **D-083 strict 결과는 변경되지 않았다.**

## 8. 다음

1. **human 50 protocol** — 4 arms, 400 ratings, 2,586 vs pilot300 primary.
2. **no-candidate branch** — human/audit 실패 시 pilot300 fallback.
3. **084b diagnostics** — report-only; 5 old flips adjudication.
4. **test 163** — 별도 승인 전까지 봉인.

## 산출물

- `eval/slot_verify_084a.py`
- `eval/tests/test_slot_verify_084a.py`
- `runner/c5_a1_verifier_084a_audit.py`
- `runner/c5_a1_select_084a.py`
- `reports/provenance/C5_a1/full_2ep/verifier_084a_audit.json`
- `reports/provenance/C5_a1/full_2ep/selection_084a_provisional.json`
- `reports/provenance/C5_a1/full_2ep/verifier_084a_audit_stdout.txt`
- `reports/provenance/C5_a1/full_2ep/selection_084a_stdout.txt`
