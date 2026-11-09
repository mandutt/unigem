# C5 Phase 6 v1.0.10 — Option A Final Confirmation

- 작성일: 2026-11-09
- 작성 기준 HEAD: `a88c714`
- 대상: `docs/plan_c5_b0a_pm_prereg_v1_0_10.md` (1,769줄)
- freeze template: `docs/plan_c5_b0a_pm_prereg_v1_0_10_FREEZE.template.json`
- golden: `docs/hoplite/c5_b0a_pm_prereg_v1_0_10_2026-11-09/golden_vectors.json`
- 이전 라운드: v1.0.9 (2 CONTINUE / 1 NARROW)
- 상태: **Option A final confirmation. 실행 미승인.**
- test 163: **sealed**
- P1: **미사용**
- T5Gemma2: **D-108 STOP**
- Phase 6/B0-B/B1/B2/Stage C: **미승인**

**Mandatory verification:**
- reviewed HEAD `a88c714`
- verbatim quote: `own eval loop                       # no evaluate_arm`

---

## 0. Instructions

1. **같은 스레드의 최종 확인.** v1.0.9에서 닫힌 심볼/hash/custody는 재검토 금지.
2. 새 요청서와 v1.0.10 문서를 직접 읽어라.
3. 학습·평가/test 163/P1/subagent 금지.
4. Q1~Q5 + final block.

---

## 1. v1.0.10 변경

### Option A

```text
runner/c5_pm_phase6.py
  -> c5_mt5_lora_b0.train_arm            # training only
  -> c5_pm_stats.bootstrap_paired_v2     # stats
  -> own eval loop                       # no evaluate_arm
```

- `evaluate_arm` import/call 금지.
- legacy `bootstrap_paired` import/call 금지.
- pre-freeze helper edit 없음.
- §13.5 test에 Phase 6 path `evaluate_arm` 미사용 추가.

### 유지

- `bootstrap_paired_v2` 단일 심볼.
- `_FREEZE.json` `manifest_commit:null` + external txt.
- `freeze_manifest_sha256` 정의/custody.

---

## 2. 검토 질문

### Q1. Lifecycle

Option A가 §16.1 no-code-before-freeze와 §17.3 helper reuse를 동시에 만족하는가?

### Q2. evaluate_arm exclusion

Phase 6가 `evaluate_arm`을 import/call하지 않는다는 규정과 test가 충분한가?

### Q3. train_arm reuse

`train_arm` training-only 재사용이 `evaluate_arm` 경유 legacy bootstrap을 다시 끌어오지 않는가?

### Q4. Residual

v1.0.10이 새 문제를 만들었는가? ranked list.

### Q5. Final

**STOP / NARROW / CONTINUE**와 승인 범위.

- v1.0.10 freeze
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
v1.0.10 freeze:
구현+unit tests:
D0:
D1:
3-seed:
금지 범위:
최대 compute:
Must-fix (ranked):
v1.0.10 self-contained:
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
