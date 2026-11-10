# C5 Checkpoint Policy

- 작성일: 2026-11-10
- 적용: C5 F0 및 이후 모든 장시간 학습/평가 runner

## 규칙

1. **1분 이상 걸리는 학습/평가 또는 unit이 2개 이상인 실행은 checkpoint 없이 시작하지 않는다.**
2. **unit 완료 즉시 final checkpoint**를 저장한다.
3. 100 updates 이상이면 **100-step 간격** 중간 checkpoint를 저장한다.
4. 저장 대상은 **adapter + LoRA + seed/step/RNG/config**만. base model 전체는 저장하지 않는다.
5. atomic write(`.tmp` → rename), SHA256/manifest, resume state를 기록한다.
6. checkpoint가 없는 runner는 **실행 전에 수정**한다.
7. final checkpoint는 보존하고, 중간 checkpoint는 마지막 1~2개만 유지한다.
8. 대용량 checkpoint archive는 D:로 이동할 수 있지만 raw per-unit JSON은 repo에 둔다.

## 실측 용량

| cell | checkpoint 1개 |
|---|---:|
| E00 | 1.3 KB |
| E01 | 1.8 MB |
| E10 | 2.1 MB |
| E11 | 3.8 MB |
| 12 units 합계 | 23 MB |

400-update 6-unit 실험은 final 약 17MB, 100-step 간격 포함 약 68MB 수준이다. **용량은 제약이 아니다.**

## 적용 예외

- eval-only baseline(E00)은 학습 파라미터가 없으면 state가 작다.
- D1 mechanics는 signal seal 때문에 checkpoint digest-only일 수 있다. 이 경우 정책보다 D1 stage 규칙이 우선한다.
- F0.2/F0.3/F0.4는 이미 checkpoint 없이 완료됐다. 재실행 시 이 정책을 적용한다.
