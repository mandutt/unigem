# C5 Phase 6 v1.0.11 — Own-Loop Final Confirmation

- 작성일: 2026-11-09
- 작성 기준 HEAD: `6fad89e`
- 대상: `docs/plan_c5_b0a_pm_prereg_v1_0_11.md` (1,773줄)
- freeze template: `docs/plan_c5_b0a_pm_prereg_v1_0_11_FREEZE.template.json`
- golden: `docs/hoplite/c5_b0a_pm_prereg_v1_0_11_2026-11-09/golden_vectors.json`
- 이전 라운드: v1.0.10 (3/3 NARROW)
- 상태: **own-loop final confirmation. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

**Mandatory verification:**
- reviewed HEAD `6fad89e`
- verbatim quote: `-> own training loop`

---

## 0. Instructions

1. 같은 스레드의 최종 확인. v1.0.10에서 닫힌 심볼/hash/lifecycle은 재검토 금지.
2. 새 요청서와 v1.0.11 문서를 직접 읽어라.
3. 학습·평가/test 163/P1/subagent 금지.
4. Q1~Q5 + final block.

---

## 1. v1.0.11 변경

```text
runner/c5_pm_phase6.py
  -> own training loop
  -> own eval loop
  -> c5_pm_stats.bootstrap_paired_v2
```

- `train_arm` import/call 금지.
- `evaluate_arm` import/call 금지.
- legacy `bootstrap_paired` 금지.
- Phase 6 path = transitive call graph rooted at entrypoint.
- P0 uses `p0_eval_split`; unaffected.

---

## 2. 검토 질문

### Q1. Own-loop lifecycle

Phase 6가 training/eval loop를 직접 소유하는 것이 §16.1 no-code-before-freeze와 §17.3를 동시에 만족하는가?

### Q2. train_arm/evaluate_arm exclusion

`train_arm`과 `evaluate_arm`을 모두 배제한 규정/test가 충분한가? transitive path 정의가 명확한가?

### Q3. Training correctness

Phase 6 own training loop가 §2.7 mode/RNG, §2.5 measurement semantics, adapter/LoRA 구성을 그대로 구현할 수 있는가?

### Q4. Residual

v1.0.11이 새 문제를 만들었는가? ranked list.

### Q5. Final

**STOP / NARROW / CONTINUE**와 승인 범위.

- v1.0.11 freeze
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
v1.0.11 freeze:
구현+unit tests:
D0:
D1:
3-seed:
금지 범위:
최대 compute:
Must-fix (ranked):
v1.0.11 self-contained:
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
