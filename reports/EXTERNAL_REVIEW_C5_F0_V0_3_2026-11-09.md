# C5 F0 v0.3 — Independent Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `c5daaa7`
- 대상: `docs/plan_c5_f0_v0_3_2026-11-09.md` (DRAFT v0.3)
- 이전: v0.1 3/3 NARROW, v0.2 3/3 NARROW
- 이전 F0 검토 스레드 6개는 **archive 완료**
- 상태: **미승인·미실행**
- test 163: sealed
- P1: unused
- T5Gemma2: D-108 STOP
- **새 독립 검토 라운드**. archive된 스레드의 후속이 아니며 중복 요청이 아님.

---

## 0. Reviewer Instructions

1. 새 스레드에서 독립 검토하라. 이전 v0.1/v0.2 결론을 상속하지 말라.
2. 아래 파일을 직접 읽어라.
   - `docs/plan_c5_f0_v0_3_2026-11-09.md`
   - `docs/plan_c5_f0_v0_2_2026-11-09.md` (superseded)
   - `reports/C5_F0_DRAFT_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_F0_V0_2_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`
   - `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`
   - `runner/c5_pm_phase6.py`
3. 학습·평가 실행 금지. test 163/P1 사용 금지. 서브에이전트/추가 LLM 금지.
4. repository 수정 금지. 지정 report 파일만 작성.
5. Q1~Q6에 판정 + 근거 + 다음 단계 1~3개.
6. 최종 판정은 STOP / NARROW / CONTINUE.
7. 보고서 경로:
   `docs/hoplite/c5_f0_v0_3_review_2026-11-09/review_{MODEL}.md`
8. reviewed HEAD와 verbatim quote `paired E01−E11`를 포함하라.

---

## 1. v0.3 변경

v0.2 must-fix 반영:

1. **LoRA 초기화 고정**
   - F0 전용 builder에서 adapter 생성 후 `torch.manual_seed(seed ^ 0x5EED10A5)`로 LoRA 초기화.
   - E01/E11 LoRA init hash 동일성 assert.
   - E10/E11 adapter init hash 동일성 assert.
   - Phase 6 `build_arm` 불변.
2. **D1 E00 모순 수정**
   - D1 = E10/E01/E11 각 1 update, 총 3; E00 0-update eval-only.
3. **mechanics predicate 열거**
   - D0 10개, D1 10개 닫힌 목록.
   - D1 signal read 금지.
4. **Primary = paired contrast**
   - final-checkpoint donor-crop `E01−E11` CI lower>0.
   - per-cell significance는 secondary descriptor.
5. **Primary source 고정**
   - `unit.final.per_doc`; phase7 diagnostic.
6. **STOP protocol gate**
   - `PROTOCOL_VALID` 실패 시 `NOT_EVALUABLE`.
7. **Compute**
   - D1 25min parallel/55min sequential; R 900 updates ≤120min.
8. **Interpretation**
   - `adapter-as-configured`, `route as configured` 정의.
   - E01+/E11+ = replication/anomaly, H3 아님.

## 2. 설계

| cell | memory | adapter | decoder LoRA | updates |
|---|---|---|---|---|
| E00 | EG2 raw 753×512 | none | none | 0 |
| E10 | EG2 raw | trained | none | 100 |
| E01 (F0) | EG2 raw | none | 64 modules | 100 |
| E11 (L) | EG2 raw | trained | 64 modules | 100 |

- Primary: E01 vs E11 (LoRA fixed after v0.3 RNG fix).
- E00 eval-only baseline.
- E01 vs E10 not clean causal.
- Stage R always 3 seeds after D0/D1 mechanics; no 1-seed signal gate.
- Primary: 15 common docs, paired bootstrap, `CI_D.lower >0`.
- `E01≈E11`: CI contains 0 AND |mean_D|<.05.
- 15→14 substitution forbidden.
- STOP only if `PROTOCOL_VALID` + both fail + CI not >0.

## 3. 검토 질문

### Q1. RNG

F0-only LoRA seed reset + init hash assert가 E01/E11 “LoRA fixed”를 충분히 보장하는가? Phase 6 builder를 건드리지 않는 분리가 적절한가?

### Q2. D0/D1

D1 3 updates + E00 eval-only, mechanics predicate 10/10이 충분한가? D1 signal read 금지를 실제로 강제할 수 있는가?

### Q3. Primary

paired `E01−E11` CI lower>0, final-checkpoint source, 15 common/no substitution이 적절한가?

### Q4. STOP

`PROTOCOL_VALID` + both fail + CI not >0일 때만 route STOP, 아니면 NOT_EVALUABLE이 충분한가?

### Q5. Compute

D1 25min parallel / 55min sequential, R 120min, 900 updates가 현실적인가?

### Q6. H3

H3 별도 prereg, residual identity 별도 검증이 충분한가?

## 4. 답변 형식

```text
Qn.
- 판정: agree / disagree / conditional / defer
- 근거
- 다음 단계: 1~3개

최종 판정: STOP / NARROW / CONTINUE
RNG:
D0/D1:
Primary:
STOP:
Compute:
H3:
Must-fix (ranked):
잘못된 전제:
```

## 5. 금지

- 승인 전 F0 실행 금지
- 학습·평가 실행 금지 (review 단계)
- test 163/P1 사용 금지
- repository 수정 금지 (지정 report만)
- subagent/추가 LLM 금지
- threshold/seed/donor/step/LR 변경 금지
- B0-B/B1/B2/Stage C 자동 진행 금지
- Phase 6 결과 재해석으로 B0-B 구제 금지
