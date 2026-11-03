# Wave 2A 설계안 — D-β 측정 타당성 보강 + F-C softmax mix

- 작성: 2026-11-04
- 상태: **설계안. 사용자 승인 전 구현·실행 금지**
- 선행: D-062 (D-β Wave 1 완료, 40h 확장 보류)
- 범위: D 트랙 연구. F2 제품 경로(D-057, komixv2/whisper) 변경 없음

## 1. 목적

D-β Wave 1의 결론을 해석 가능하게 만드는 **측정 타당성 보강**과, Addendum D-5.4가 원래 요구한 **F-C softmax 혼합**을 구현하는 단계다.

Wave 1에서 확인된 문제:

- dev 어휘 포함율 **85.6%** (1,808참조 문자 중 260개가 학습 vocab에 없음)
- dev가 FLEURS ko dev가 아니라 **Kspon eval 100**
- F-C가 요구사항(softmax 학습 혼합)과 달리 **concat + linear**
- F-A′/F-B/F-C가 0.44%p 이내 동률 → 현재 조건으로는 층 선택을 판별할 수 없음

Wave 2A는 이 네 가지를 고친 뒤, **reader 출력 단위와 특징 혼합 방식이 CER에 영향을 주는지**를 다시 측정한다.

## 2. Scope

### 포함

1. FLEURS ko **dev** 확보·manifest·특징 추출
2. dev 어휘 포함율 ≥95%를 목표로 하는 **고정 출력 vocab** 재구성
3. F-C를 **4개 층(6/8/10/11) softmax 학습 혼합**으로 구현
4. F-A′/F-B/F-C-softmax를 **같은 6시간 오디오·같은 seed**로 재학습
5. dev CER, 어휘 포함율, arm별 파라미터·시간, 대응 부트스트랩 보고

### 제외

- FLEURS **test** 사용 — G-C2에서 이미 사용, 재사용 금지
- 40시간 확장·R-D2 — Wave 2C
- 오디오 타워 LoRA/fine-tune — Wave 2B
- word piece head — 10M 파라미터 상한과 충돌하므로 Wave 2B 이후 별도 검토
- Q4/QAT, Jev head, MaxSim — 별도 승인 사항

## 3. DoD (완료 정의)

| # | DoD | 검증 |
|---|---|---|
| 1 | FLEURS ko dev manifest가 test와 분리됨 | split·ID 대조, test 미포함 확인 |
| 2 | 새 vocab의 dev 포함율 **≥95%** | 문자 단위 coverage 계산 |
| 3 | F-C softmax mix 구현, 파라미터 **≤10M** | 모델 parameter count |
| 4 | F-A′/F-B/F-C-softmax 3-arm 학습 완료 | 체크포인트·로그 |
| 5 | dev CER(공백 무시)와 문장별 예측 저장 | `decode_*.json` |
| 6 | arm별 95% 대응 부트스트랩 | 10,000회, seed 고정 |
| 7 | AM-6 이행 표 포함 보고서 | `reports/W2A_results.md` |
| 8 | FLEURS test 미사용 확인 | 사용 로그·manifest |

## 4. Public API / 산출물 계약

### 4.1 데이터·vocab

- `data/wave2a/fleurs_dev.jsonl`
  - fields: `id`, `source=fleurs_ko`, `split=dev`, `audio`, `ref`, `dur`
- `data/wave2a/vocab.json`
  - `blank: 0`, `unk: 1`
  - `chars`: 고정 목록
  - `char2id`
- `data/wave2a/coverage.json`
  - `train_chars`, `dev_chars`, `missing`, `coverage`

### 4.2 특징

- 기존 `data/wave1/feats_{fd,fa,fb,fc}` 재사용
- F-C는 기존 `fc.npz`의 4,096d concat을 **4×1,024로 slice**해 softmax mix에 사용
- FLEURS dev 특징: `data/wave2a/feats_dev/{fa,fb,fc}.npz`
- 특징 추출은 기존 `train/w1_extract.py`의 Gemma4 feature extractor + Q8 ONNX 경로를 그대로 사용

### 4.3 모델

- F-A′: 기존 `CTCReader(in_dim=1536)`
- F-B: 기존 `CTCReader(in_dim=1024)`
- F-C-softmax: 신규 `FCSoftmaxReader`
  - 입력: 4개 층 각 1,024d (LayerNorm 후)
  - 학습 파라미터 `w[4]` → softmax → 가중 합 1,024d
  - 이후 기존 reader와 동일: Linear 1024→384 → 4층 Transformer(6 head, FF1536) → CTC
  - 출력 vocab: 새 vocab
- 체크포인트:
  - `train/w2a_ckpt/{fa,fb,fc_softmax}.best.pt`

### 4.4 CLI 계약

- `runner/w2a_build_dev.py --out data/wave2a/fleurs_dev.jsonl`
- `runner/w2a_build_vocab.py --text-corpus <P0> --top-syllables 2350 --out data/wave2a/vocab.json`
- `train/w2a_extract_dev.py --manifest ... --vocab ... --out-dir ...`
- `train/w2a_train.py --arm {fa,fb,fc_softmax} --features ... --dev-features ... --vocab ... --seed 42 --epochs 20 --batch 8 --threads 4`

## 5. Vocab 설계

- 구성:
  - P0 텍스트 코퍼스에서 빈도 상위 **한글 음절 2,350개**
  - 숫자 0~9
  - 라틴 소문자 a~z
  - 공백 1
  - `<unk>` 1
- 총 크기 약 **2,388** (blank 포함 2,389)
- 파라미터 영향:
  - 기존 head 1,069 → 2,388: +1,319 × 384 ≈ +0.51M
  - F-A′ 8.10M → **8.61M**
  - F-B 7.90M → **8.41M**
  - F-C 9.08M → **9.59M**
  - 전부 10M 이내
- dev 포함율이 95% 미만이면:
  - 상위 음절 수를 3,000까지 확장하되 10M 상한을 재계산
  - 그래도 미달이면 **중단·보고** (임의로 dev 문자를 vocab에 추가하지 않음)

## 6. F-C softmax mix 사양

- 층: `aud_h_l06`, `aud_h_l08`, `aud_h_l10`, `aud_h_l11`
- 각 층에 프레임별 LayerNorm
- `logits[4]` 학습 → `softmax(logits / τ)` (초기 τ=1)
- 가중 합 `sum_i w_i * h_i` → 1,024d
- 이후 reader 입력 투영
- 초기화: 균등 가중치(0.25)로 시작해 기존 concat+linear와 비교 가능하게 함
- 기울기 폭주 방지: softmax temperature는 학습 파라미터로 두지 않고 고정, `w`만 학습

## 7. 실험 조건

| 항목 | 값 |
|---|---|
| 학습 오디오 | Wave 1과 동일 6.0008h/2,384클립 |
| dev | FLEURS ko dev 전체 |
| seed | 42 |
| batch | 8 |
| threads | 4 |
| optimizer | AdamW, lr 1e-3, cosine |
| grad clip | 5.0 |
| epochs | 최대 20, patience 5 |
| checkpoint 선택 | dev CER 최저 |
| 호스트 | 로컬 우선(F-C 3.9GB 특징, 15.6GB RAM) |
| test | FLEURS test 사용 금지 |

## 8. 분석·판정

### 주지표

- dev CER(공백 무시), corpus 누적
- arm별 오류/참조 문자
- 어휘 포함율
- 파라미터 수, epoch 시간, 총 학습 시간

### 비교

- F-A′ vs F-B vs F-C-softmax:
  - 점추정 CER
  - 문장 단위 대응 부트스트랩 95% CI (10,000회, seed 고정)
- 참고: Wave 1의 F-A′ 0.4707, F-B 0.4679, F-C(concat) 0.4663

### 사전 선언 go/no-go

- **Go (Wave 2B로):** 3-arm 중 best가 **현재 F-A′ 0.4707 대비 상대 5% 이상 개선**이고, 대응 부트스트랩 95% CI 하한 > 0
- **No-Go (reader/output unit 아님):** 상대 개선 < 5% 또는 CI 하한 ≤ 0
  - 이 경우 Wave 2B(상위층 LoRA)로 바로 이동하되, Wave 2A 결과를 “reader/output unit 한계”로 기록

> 이 기준은 **탐색적 의사결정**이며, G-C2/R-D1 같은 게이트 임계값을 변경하지 않는다.

## 9. 구현 순서 (승인 후)

1. FLEURS ko dev 다운로드·manifest 생성·test 미포함 검증
2. P0 텍스트에서 상위 2,350 음절 추출, vocab 생성
3. dev 특징 추출 (F-A′/F-B/F-C 4층)
4. `FCSoftmaxReader` 구현 + 단위 테스트(shape, softmax 합=1, param count)
5. 10클립 smoke test (loss 감소, vocab 크기, 체크포인트 저장)
6. F-A′/F-B/F-C-softmax 3-arm 학습
7. dev decode + 문장별 CER + 부트스트랩
8. `reports/W2A_results.md`, `docs/decisions.md` 기록
9. 2B 진행 여부 보고

## 10. 리스크·완화

| 리스크 | 완화 |
|---|---|
| FLEURS dev 다운로드 실패 | HF `google/fleurs` ko_kr dev 수동 확인, P0만 |
| dev 포함율 <95% | 상위 3,000까지 확장, 10M 재계산 |
| F-C 메모리 | 기존 3.9GB flat features, batch 8, local 15.6GB |
| softmax mix 학습 불안정 | 균등 초기화, grad clip, LR 1e-3 |
| FLEURS test 재사용 | manifest에 test ID 부재 검증, 사용 로그 확인 |
| 로컬 CPU 시간 | 3-arm 순차, 1 epoch 약 6~8분 목표 |

## 11. 예상 비용

- 구현: 0.5~1일
- 학습: 3 arm × 약 1~2시간 = **3~6시간** (로컬)
- 평가·보고: 1~2시간
- **총 1~2일**

## 12. AM-6 이행 표

| 요구 | 이행 계획 |
|---|---|
| dev를 FLEURS ko dev로 | 이행 |
| 어휘 포함율 보고 | 이행, ≥95% 목표 |
| F-C softmax mix | 이행 |
| 3-arm 동일 조건 | 이행(같은 오디오·seed·코드) |
| FLEURS test 미사용 | 이행 |
| CER(공백 무시) | 이행 |
| CER(공백 포함)·WER | **미이행** — 예측이 공백을 출력하지 않음. 별도 과제 |
| R-D2 | **미이행** — Wave 2C |

## 13. 승인 요청

이 설계안대로 **Wave 2A를 구현·실행해도 되는지** 승인해 주세요.

승인 시 다음 순서로 진행합니다:

1. FLEURS dev·vocab 확보
2. F-C softmax mix 구현
3. 3-arm 학습
4. 결과 보고 및 Wave 2B/2C 결정
