# C5 Phase 6 v1.0.8 — External Review Request (same-thread continuation)

- 작성일: 2026-11-09
- 작성 기준 HEAD: `38a2a81`
- 대상: `docs/plan_c5_b0a_pm_prereg_v1_0_8.md` (1,763줄)
- freeze template: `docs/plan_c5_b0a_pm_prereg_v1_0_8_FREEZE.template.json`
- golden: `docs/hoplite/c5_b0a_pm_prereg_v1_0_8_2026-11-09/golden_vectors.json`
- 이전 라운드: v1.0.7 (`1 CONTINUE / 2 NARROW`)
- 상태: **v1.0.8 review. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

**Mandatory verification:**
- reviewed HEAD SHA `38a2a81`
- verbatim quote: `manifest_commit` is always `null` inside `_FREEZE.json`

---

## 0. Reviewer instructions

1. **같은 스레드의 연속 검토다.** v1.0.7에서 이미 닫힌 항목은 재검토하지 말고, v1.0.8에서 새로 바뀐 부분과 아래 Must-fix 폐쇄만 확인하라.
2. 새 요청서와 v1.0.8 문서를 직접 읽어라. 다른 모델 답을 재사용하지 말라.
3. **학습·평가를 실행하지 말라.** test 163을 열지 말라. P1을 사용하지 말라.
4. 서브에이전트/추가 LLM을 호출하지 말라.
5. 각 Q1~Q9에 **판정 + 근거 + 다음 단계 1~3개**.
6. 최종 판정은 **STOP / NARROW / CONTINUE**.
7. 결과를 본 뒤 threshold·seed·donor·step·LR 변경 제안 금지.
8. 보고서 파일:
   `docs/hoplite/c5_b0a_pm_prereg_v1_0_8_2026-11-09/review_{MODEL}.md`
   같은 스레드지만 **새 라운드 디렉터리**에 작성하라.

---

## 1. TL;DR

> **v1.0.7은 1 CONTINUE / 2 NARROW였다. v1.0.8은 `manifest_commit` 자기참조, legacy `bootstrap_paired` 도달, paired `L>F`, template `note`, cap 120/155, P0 tail provenance, §4.6 표기를 닫았다. 이 문서는 v1.0.8이 freeze 가능한지, 구현·unit tests·D0를 승인할 수 있는지를 묻는다.**

---

## 2. v1.0.8 변경

### 2.1 manifest_commit

- `_FREEZE.json`의 `manifest_commit`은 **항상 `null`**.
- 실제 SHA는 `reports/provenance/C5_b0a/freeze_manifest_commit.txt`.
- D0 report에 `freeze_manifest_sha256` + `manifest_commit` 기록.

### 2.2 Phase 6 entrypoint

```text
runner/c5_pm_phase6.py
  -> c5_pm_stats.bootstrap_paired_v2
  -> c5_mt5_lora_b0.train_arm/evaluate_arm
```

- legacy `bootstrap_paired` import 금지.
- `evaluate_arm` 재사용 시 bootstrap call 교체.
- source/call-graph assertion.

### 2.3 paired L>F

- 15 common IDs.
- same variant/endpoint/memory_kind/seed.
- per-doc `delta_L - delta_F`.
- seed-average before bootstrap.
- missing pair → NA.

### 2.4 기타

- frozen schema `note` 허용.
- registered 120분 vs aggregate 155분.
- P0 tail `.4862/.43355/.455`는 derived, not stored.
- §4.6 `p_step NA + p_valid=NA`.

### 2.5 Golden

| vector | digest |
|---|---|
| state | `43ecb58e…d65712` |
| base replay | `c43ea35c…f7851667` |
| key coverage | `8277a713…af7a20` |
| control | `6b50c226…c1938` |

---

## 3. 검토 질문

### Q1. 7 residual closure

v1.0.7 잔여 7개가 실제로 닫혔는가?

1. `manifest_commit` self-reference
2. legacy `bootstrap_paired` reachability
3. paired `L>F`
4. template `note`
5. cap 120/155
6. P0 tail provenance
7. §4.6 `p_valid=false`

### Q2. Freeze chain

`manifest_commit:null` + external `freeze_manifest_commit.txt` + D0 report가 자기참조 없이 닫히는가? `freeze_commit`은 final plan commit으로 명확한가?

### Q3. Legacy bootstrap

`runner/c5_pm_phase6.py` call graph와 source assertion이 `evaluate_arm` 경유 legacy 호출을 실제로 차단하는가?

### Q4. Paired L>F

cohort 15, endpoint/variant/memory/seed 정렬, seed-average, missing NA가 실행 가능한가?

### Q5. Cap/labels

registered 120 vs aggregate 155가 혼동 없이 정의됐는가?

### Q6. P0 tail

`.4862/.43355/.455`가 derived-not-stored로 명시된 것이 충분한가?

### Q7. §4.6

`p_step NA + p_valid=NA`가 F9와 정합적인가? 다른 unreachable 표기가 남았는가?

### Q8. Self-containedness

v1.0.8만 읽고 구현 가능한가? 남은 외부 참조는 무엇인가?

### Q9. 최종 판정 및 freeze

**STOP / NARROW / CONTINUE**와 승인 범위를 제시하라.

- v1.0.8 freeze
- 구현+unit tests
- D0
- D1
- 3-seed
- 금지 범위
- 최대 compute
- test 163 지위

---

## 4. 답변 형식

각 Q1~Q9:

```text
Qn.
- 판정: agree / disagree / conditional / defer
- 근거: 구체 수치·조항
- 다음 단계: 1~3개
```

마지막:

```text
최종 판정: STOP / NARROW / CONTINUE
v1.0.8 freeze:
구현+unit tests:
D0:
D1:
3-seed:
금지 범위:
최대 compute:
Must-fix (ranked):
v1.0.8 self-contained:
잘못된 전제:
```

---

## 5. 금지

- 학습·평가 실행 금지
- test 163 열람 금지
- P1 사용 금지
- repository 수정 금지 (지정 report 파일만)
- subagent/추가 LLM 호출 금지
- 결과 후 threshold/seed/donor/step/LR 변경 금지
- Phase 6/B0-B/B1/B2/Stage C 자동 진행 금지
