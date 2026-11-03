# D-β Wave 1 — 데이터·특징·학습 셋업

- 작성: 2026-11-03
- 상태: **학습 실행 중(1차 결과 전)**
- 목적: Addendum D §D-5.1 — EG2 오디오 특징 위 4층 CTC reader의 arm 비교

## 1. 데이터 선정

| 소스 | 용도 | 시간 | 클립 | 화자 |
|---|---|---|---|---|
| Zeroth train (Bingsu/zeroth-korean) | 낭독체 | **3.9001h** | 1,534 | 화자 ID 없음 |
| KconfSpeech sample | 회의·대화체 | **2.1007h** | 850 | 3명(S000012/13/17) |
| **합계** | 학습 | **6.0008h** | **2,384** | — |
| Kspon eval_clean 100 | dev(중간 판단) | 0.079h | 100 | 학습과 분리 |

- D-5.3 목표(낭독 65% + 대화 35%)를 **65.0/35.0**으로 충족.
- 모든 클립은 **0.5~16초**로 제한해 16초 창 하나에 정렬. 16초 초과 클립은 학습에서 제외하고 목표 시간을 다시 채웠다.
- 참조 텍스트는 Kconf 주석·문장부호·슬래시를 제거하고 공백을 정리했다. 학습 목표는 **공백 제거 문자 단위**.
- **화자 분리 한계**: Zeroth에는 화자 ID가 없어 낭독 구간의 speaker-disjoint holdout을 보장할 수 없다. Kconf는 화자 ID가 있으나 3명뿐이다. dev는 Kspon eval_clean 100으로 분리했다.
- **FLEURS dev 미사용**: FLEURS test는 G-C2에서 이미 사용했고 D-5.3에서 학습 금지 대상이므로, 이번 Wave 1의 dev는 Kspon eval_clean 100으로 대체했다. FLEURS test는 최종 판정 전까지 사용하지 않는다.

## 2. 특징

`train/w1_extract.py`로 16kHz WAV를 Gemma4AudioFeatureExtractor에 넣고 Q8 다층 그래프(`eg2_audio_q8_layers.onnx`)를 실행했다.

| Arm | 입력 | 차원 | 전처리 | 파일 |
|---|---|---|---|---|
| F-D | `audio_features` 앞 256d | 256 | 프레임별 L2 | 245MB |
| F-A′ | `aud_out_proj` | 1,536 | 프레임별 LayerNorm | 1.5GB |
| F-B | `aud_h_l11` | 1,024 | 프레임별 LayerNorm | 1.0GB |
| F-C | `aud_h_l06/08/10/11` concat | 4,096 | 층별 LayerNorm 후 concat | 3.9GB |

- F-A′는 errata E-2에 따라 `audio_features`(512, LM 이후)가 아니라 `aud_out_proj`(1,536, LM 이전)를 사용했다.
- F-C는 4개 층을 concat하고 reader 입력 투영이 학습 가능한 혼합을 담당한다. Addendum의 "softmax 가중 합"을 별도 층으로 구현하지는 않았고, **선형 투영이 그 역할을 대체**한다. 이 차이는 결과 해석에 명시한다.
- 모든 특징은 클립별로 패딩/플랫 저장했고, 유효 프레임 수를 `lens`에 기록했다.

## 3. Reader·학습

- 구조: 입력 투영 → 4층 Transformer(d=384, 6 head, FF=1536, pre-norm) → CTC head, blank=0.
- 파라미터: F-D 7.61M, F-A′ 8.10M, F-B 7.90M, F-C 9.08M — 전부 **≤10M**.
- AdamW, lr 1e-3, cosine, grad clip 5.0, batch 8, seed 42, threads 4.
- 최대 20 epoch, **Kspon dev CER(공백 무시) 기준 best checkpoint**, patience 5.
- 호스트: eg2-1 F-D, eg2-2 F-A′, eg2-3 F-B, eg2-4 F-C. eg2-5는 D-6용으로 비참여.
- 모든 호스트는 같은 코드·vocab·시드·하이퍼파라미터를 사용한다.

## 4. 비용

D0-d 실측 기준 6h 1 epoch ≈ 3.3~4.1분. 실제 2,384클립·batch 8에서 **1 epoch 252~279초**로 측정됐다(1차 2 epoch). 20 epoch는 약 85~95분으로 호스트당 48시간 한도 내다.

## 5. 아직 남은 것

- 4개 arm의 dev CER 곡선·최종 CER.
- FLEURS test는 최종 판정 1회만 사용.
- R-D1 대응 부트스트랩, R-D2 학습곡선 외삽.
- cross-host 재현(D-5.7)은 Wave 2로 보류.

## 6. 산출물

- `data/wave1/manifest.jsonl`, `data/wave1/summary.json`
- `data/wave1/vocab.json` (1,069자)
- `data/wave1/dev_kspon.jsonl`
- `train/w1_extract.py`, `train/d5_reader.py`
- `logs/W1_build_manifest.log`, `logs/W1_extract.log`
