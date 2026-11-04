# Wave 2A-lite — 중간 결과 (seed 42, 2026-11-04)

- 상태: **부분 결과**. F-C-softmax/F-C-concat 미완료, seed 43/44 미완료.
- dev: FLEURS ko dev 192클립(≤16초), 참조 7,861자.
- 정규화: `normalize_nospace`.

## 1. Seed 42 dev CER

| Arm | CER | errors/ref | pred/ref | 비고 |
|---|---:|---:|---:|---|
| F-A′ | **0.22236** | 1,748 / 7,861 | 0.9875 | best epoch 16 부근 |
| F-B | **0.21931** | 1,724 / 7,861 | 0.9875 | best epoch 15 |
| F-C-softmax | 미완료 | — | — | clean VPS에서 재실행 중 |
| F-C-concat | 미완료 | — | — | F-C-softmax 후 |

## 2. Pairwise bootstrap (문장 단위, 10,000회, seed 42)

F-A′ 대비 개선량(양수 = F-A′보다 좋음):

| 비교 | 개선 | 95% CI | 판정 |
|---|---:|---|---|
| F-B − F-A′ | **+0.305%p** | **[-0.351, +0.954]%p** | CI가 0 포함 — 유의하지 않음 |

- F-A′/F-B 차이는 현재 **0.3%p 수준**으로, seed 42에서는 층 선택 우열을 말할 수 없습니다.
- seed 43/44가 이 차이를 재현하는지 확인해야 합니다.

## 3. 오류 구성

| Arm | substitution | deletion | insertion |
|---|---:|---:|---:|
| F-A′ | 1,485 | 226 | 139 |
| F-B | 1,533 | 192 | 94 |

## 4. Vocab coverage

- dev 참조 7,861자 중 미포함 **49자(0.62%)**, 192문장 중 154문장은 전부 포함.
- `vocab_oracle`(미포함 문자를 양쪽에서 제거한 진단): F-A′ 0.21947, F-B 0.21656 — **모델 결과 아님**.

## 5. 다음

- F-C-softmax/concat clean VPS 결과
- seed 43 F-A′/F-B, seed 44 F-A′
- 4-arm 동일 조건 분석 후 Go/No-Go
- 체크포인트 동결 후 Kspon eval_other/FLEURS test 1회
