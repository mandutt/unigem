# C5 F0 — Post-mortem (2026-11-10)

- 대상: `reports/provenance/C5_f0/r/units/*.json` 12개, `r/f0_r_labels.json`
- 재학습 없음, threshold 변경 없음, label 재계산 없음
- 재현 artifact: `reports/provenance/C5_f0/postmortem.json`

## 결론

**F0의 계약상 label은 `ROUTE_STOP`이지만, 과학적 해석은 “adapter 무효”가 아니라 “E01 underfit으로 인한 불완전한 test”다.**

핵심 증거:

1. **E01(LoRA-only)가 수렴하지 않았다.**
   - E01 final train loss: 약 **19.7**
   - E10/E11 final train loss: 약 **6.2–7.3**
   - E01 loss reduction: first→last **0.736** (약 26% 감소)
   - E11 loss reduction: **0.236** (약 76% 감소)
   - 3 seeds 모두 동일한 패턴

2. **E01의 per-doc 분산이 E11보다 약 13배 크다.**
   - E01 copy doc-mean SD: **0.7228**
   - E11 copy doc-mean SD: **0.0555**
   - E10 copy doc-mean SD: **0.0390**
   - E01 seed mean: `+0.0224 / -0.0100 / -0.0037` → 불안정
   - E11 seed mean: `+0.0378 / +0.0012 / +0.0356` → 상대적으로 안정

3. **Primary D의 negative는 E01의 불안정성에 크게 의존한다.**
   - `mean_D = -0.02196`
   - seed별 D: `-0.0154 / -0.0112 / -0.0393`
   - positive docs: 8/15
   - E01이 수렴하지 않은 상태에서 E01−E11을 adapter causal contrast로 해석할 수 없다.

4. **Copy coverage는 E01/E11 동일하다.**
   - E01 mean coverage: **0.8267**
   - E11 mean coverage: **0.8267**
   - 따라서 signal 차이는 copy mask/coverage 차이가 아니다.

5. **E10은 descriptive하게 full-endpoint signal이 있다.**
   - E10 copy: mean `0.0368`, 12/15 positive, SD `0.0390` → copy SIGNAL false (mean < .05)
   - E10 full: mean `0.0324`, 14/15 positive, SD `0.0295` → full SIGNAL true
   - E10은 primary/ALL_FAIL 대상이 아니므로 causal 결론에 사용할 수 없다. 다만 “adapter-only가 full endpoint에서 약한 donor discrimination을 만들 수 있다”는 **가설**은 남는다.

## F0 계약 결과

```text
status = ROUTE_STOP
reason = no_signal_uncertain
ALL_FAIL = true   # E01/E11 x copy/full
mean_D = -0.0219615
95% CI = [-0.374112, +0.334945]
positive seeds = 0/3
```

계약상 label은 변경하지 않는다. `ROUTE_STOP`은 frozen rule에 따른 기계적 판정이다.

## 해석상 금지

- “adapter is useless”라고 단정하지 않는다.
- “EG2 has no content use”라고 단정하지 않는다.
- “LoRA-only is worse than adapter”라고 단정하지 않는다.
- F0 negative를 H3나 B0-B의 자동 승인 근거로 쓰지 않는다.

## 다음 선택지

### A. F0.1 optimization diagnostic — 별도 prereg

E01 underfit이 F0의 교란이라는 가설을 검증하는 별도 실험.

- E01 LoRA-only의 학습 예산/LR을 별도 prereg로 고정
- E01이 E10/E11과 비교 가능한 수준으로 fit하는지 **사전 정의한 training-fit gate**로 확인
- fit 후에도 copy signal이 없으면 그때 “adapter effect 부재”에 가까운 증거가 됨
- F0 결과를 사후적으로 rescue하는 것이 아니라 **새 실험**으로 등록해야 함

### B. F5 abstract summary track — 제품 목적 우선

F0와 독립적으로 메모리 요약 라인을 진행.

- mT5/UMT5-small decoder
- 다국어 abstract summary
- F5 pilot/eval 설계

F0가 inconclusive이므로 F5를 막을 이유는 없다.

### C. H3 — 보류

H3는 별도 prereg/승인 없이는 시작하지 않는다. 현재 F0 post-mortem은 H3를 지지하는 증거가 아니라 **E01 optimization 문제**를 지지한다.

### D. B0-B — 비권장

Phase 6 negative, F0 inconclusive. 지금 재개할 근거가 약하다.

## 권고

**F0는 계약상 종료하되, scientific status는 `INCONCLUSIVE_UNDERFIT`로 기록한다.** 다음은 F0.1 optimization diagnostic 또는 F5 중 하나를 선택하는 것이 맞다. H3/B0-B는 지금 열지 않는다.
