# C2-A0 — Notesoop-STT-Ko-v1 코드·라이선스 점검

- 작성: 2026-11-02
- 대상: Addendum A §A-8.1, plan v0.5 §9 C2-A0
- 소스: HF `Phsoft-ai/Notesoop-STT-Ko-v1` snapshot `030e4720…` (코드·문서만, 가중치 제외)
- 호스트: `local` (정적 분석)

## 1. 라이선스

| 항목 | 내용 |
|---|---|
| 저장소 LICENSE | **Apache License 2.0** |
| 학습 데이터 | 모델 카드: AI Hub 한국어 강의 음성 약 300GB |
| AI Hub 약관의 파생 모델 제약 | **미확인** — 데이터 이용약관은 별도 문서이며, 재배포·상업적 활용·미세조정 조건이 Apache-2.0과 다를 수 있다 |
| 결론 | 코드·가중치 사용은 Apache-2.0으로 보이나, **AI Hub 약관 확인 전 상업적 채택·재배포는 보류** |

## 2. 구조 (코드 확인)

| 구성 | 값 |
|---|---|
| 입력 특징 | **256차원** (오디오 토큰을 MRL로 256d 절단 후 L2 정규화, bfloat16) |
| Reader | Conformer **10층**, d_model **384**, nhead 6, FFN 1536, conv kernel 15 |
| 출력 | CTC, 어휘 **25,000** (형태소·음절), `CosineCTCHead` (blank + vocab bias) |
| 디코딩 | greedy CTC / KenLM 빔(선택, kenlm 별도 설치) |
| 청크 | **16초 + 1초 겹침**, 16kHz, 마지막 청크는 16초로 zero-pad, 겹침은 최대 문자열/단어 overlap 병합 |
| 런타임 의존 | `google/embeddinggemma-2` 전체(740M)를 로드해 audio_tower + embed_audio + language_model 사용. torch≥2.2, transformers≥4.40 |

## 3. 특징 추출 경로 (핵심)

코드(`src/step2_extract_features.py`)에서 확인한 순서:

1. `audio_tower(input_features)` → `[T, 1536]`
2. `language_model.norm(h)` → `[T, 1536]`
3. `embedding_projection.weight[:256, :]` 로 **MRL 256d 절단** → `[T, 256]`
4. L2 normalize → bfloat16

이는 우리 ONNX 산출물로 재현 가능하다:
- `aud_out_proj`(1536) → 체크포인트의 `embedding_projection.weight[:256,:]` 적용 → L2 normalize
- 즉 **G-A3S(특징 재현)는 별도 모델 없이 우리 그래프 + 가중치 슬라이스로 검증 가능**하다.

## 4. 주의

- Notesoop은 추론 시 **HF에서 EG2 전체 모델을 다시 로드**한다(우리 체크포인트와 동일 revision인지 확인 필요).
- `kenlm`은 requirements에 없고 주석으로 별도 설치 안내 — Linux/Windows 빌드 이슈는 C2-A4에서 확인.
- 모델 카드의 CER/WER/RTF는 **Apple M1 Pro(MPS, bf16)** 기준이며, Linux/Windows CPU 수치는 없다.

## 5. 다음 (C2-A1)

1. 위 3단계 특징을 우리 ONNX(FP32/Q8)로 만들어 Notesoop reader에 넣고 CER 비교(G-A3S·G-C2a).
2. Zeroth-Korean/FLEURS ko test에서 komixv2·whisper-turbo와 동일 정규화로 비교.
3. kenlm 설치 가능성 확인(Linux 우선).
