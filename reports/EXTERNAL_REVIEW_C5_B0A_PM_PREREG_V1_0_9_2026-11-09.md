# C5 Phase 6 v1.0.9 — Final same-thread Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `e680c8f`
- 대상: `docs/plan_c5_b0a_pm_prereg_v1_0_9.md` (1,765줄)
- freeze template: `docs/plan_c5_b0a_pm_prereg_v1_0_9_FREEZE.template.json`
- golden: `docs/hoplite/c5_b0a_pm_prereg_v1_0_9_2026-11-09/golden_vectors.json`
- 이전 라운드: v1.0.8 (2 CONTINUE / 1 NARROW)
- 상태: **v1.0.9 final confirmation. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

**Mandatory verification:**
- reviewed HEAD SHA `e680c8f`
- verbatim quote: `c5_pm_stats.bootstrap_paired_v2`

---

## 0. Instructions

1. **같은 스레드의 최종 확인이다.** v1.0.8에서 이미 닫힌 항목은 재검토하지 말고, DeepSeek이 지적한 3개만 확인하라.
2. 새 요청서와 v1.0.9 문서를 직접 읽어라.
3. 학습·평가 실행 금지. test 163/P1 사용 금지.
4. 서브에이전트/추가 LLM 금지.
5. 각 Q1~Q5에 **판정 + 근거 + 다음 단계 1~3개**.
6. 최종 판정은 **STOP / NARROW / CONTINUE**.
7. 보고서:
   `docs/hoplite/c5_b0a_pm_prereg_v1_0_9_2026-11-09/review_{MODEL}.md`

---

## 1. v1.0.9 변경

### 1.1 Symbol

- §10.2: `c5_pm_stats.bootstrap_paired_v2(seed=20261109)`.
- §17.3 entrypoint: same symbol.
- legacy `bootstrap_paired` forbidden.

### 1.2 freeze_manifest_sha256

- `freeze_manifest_sha256 = SHA256(committed _FREEZE.json bytes)`.
- `freeze_manifest_commit.txt` is committed.
- D0 records both `freeze_manifest_sha256` and `manifest_commit`.
- `_FREEZE.json` stores `manifest_commit:null`.

### 1.3 evaluate_arm

- bootstrap replacement lands **before the freeze commit**.
- source/call-graph assertion.

---

## 2. 검토 질문

### Q1. Symbol closure

`bootstrap_paired_v2`가 §10.2/§17.3/§13.5에서 일관된가? legacy `bootstrap_paired`가 Phase 6 path에서 배제되는가?

### Q2. Freeze hash/custody

`freeze_manifest_sha256` 정의, external txt commit, D0 기록이 자기참조 없이 닫히는가?

### Q3. evaluate_arm

교체 시점이 freeze 전으로 명확한가? call-graph/source assertion이 충분한가?

### Q4. Residual

v1.0.9가 새 문제를 만들었는가? ranked list.

### Q5. Final

**STOP / NARROW / CONTINUE**와 승인 범위.

- v1.0.9 freeze
- 구현+unit tests
- D0
- D1
- 3-seed
- 금지 범위
- 최대 compute
- test 163 지위

---

## 3. 답변 형식

```text
Qn.
- 판정: agree / disagree / conditional / defer
- 근거
- 다음 단계: 1~3개
```

마지막:

```text
최종 판정: STOP / NARROW / CONTINUE
v1.0.9 freeze:
구현+unit tests:
D0:
D1:
3-seed:
금지 범위:
최대 compute:
Must-fix (ranked):
v1.0.9 self-contained:
잘못된 전제:
```

---

## 4. 금지

- 학습·평가 실행 금지
- test 163 열람 금지
- P1 사용 금지
- repository 수정 금지 (지정 report 파일만)
- subagent/추가 LLM 금지
- 결과 후 threshold/seed/donor/step/LR 변경 금지
- Phase 6/B0-B/B1/B2/Stage C 자동 진행 금지
