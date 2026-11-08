# C5 EG2 layer12 feature pretest (v0.1)

## 1. 목적

EG2 final hidden 768이 retrieval/embedding objective에 최적화되어 있어
token-level syntax/order 정보가 약할 수 있다.

- final 768 (현재 B1d/B2 입력)
- layer12 512 (중간 layer, syntax 보존 가능)

을 **동일 teacher hidden cosine objective**로 비교한다.

## 2. 데이터

- train 300 / val 100
- `summarize: ` prefix 포함
- **T5 tokenizer ID**로 EG2 model에 전달
  - B1d cache와 동일한 token alignment
  - 이전 시도에서 prompt를 빠뜨려 2 token 길이 차이가 발생 → 수정
- test 163 미사용

## 3. 모델

- adapter만 학습, decoder 없음
- linear 512→640
- MLP768 512→768→640
- MLP1536 512→1536→640
- loss: `1 - cosine(adapter(h12), teacher_hidden)`
- 2 epoch, lr 1e-3, scratch, same seed

## 4. 비교 기준

- final 768 MLP768: **0.6998** (기존 capacity pretest)
- layer12 512 MLP768: 이번 실험
- layer12가 유의하게 높으면 B2 입력 feature로 채택

## 5. 해석

- layer12 > final: final layer 정보 손실 시사; layer12로 B2 재학습
- layer12 ≈ final: layer 선택 무효; decoder/objective로 이동
- layer12 < final: final layer가 더 유용; 현 구조 유지

## 6. 비용

- layer12 cache 400문서: 약 7분
- pretest 3 arm: 약 1분
- test 163 미사용

## 7. 산출물

- `data/wave2c/eg2_layer12/`
- `runner/c5_eg2_layer12_cache.py`
- `runner/c5_layer12_pretest.py`
- `reports/provenance/C5_b1d/layer12_pretest.json`
- `reports/C5_LAYER12_PRETEST_2026-11-08.md`
