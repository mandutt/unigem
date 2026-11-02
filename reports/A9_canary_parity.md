# A-9.1 — 카나리 정합 검증 (eg2-1)

- 작성: 2026-11-02
- 대상: Addendum A §A-9.1 (F-8)
- 호스트: 로컬(Windows, Ryzen 7600) vs `eg2-1`(Debian 13, EPYC 4 vCPU)
- 입력: `logs/canary_ids.json` 20개 (텍스트 길이 16~64토큰, ko/en 혼합)
- 산출물: `logs/A9_local.json`, `logs/A9_local_q8.json`, `logs/A9_canary.json`

## 1. 방법

- VPS에서 동일 체크포인트(`f9972ac2`)로 텍스트 그래프를 **직접 export** (전송 없이 재현)
- 같은 20개 입력에 대해 pooled 임베딩을 계산해 로컬 결과와 cosine 비교
- Q8은 VPS에서 동일 스크립트(`quantize_q8.py`, bits=8/block=128/accuracy_level=4)로 양자화 후 재측정

## 2. 결과

| 경로 | n | cosine 최소 | 평균 | <0.999 |
|---|---|---|---|---|
| FP32 (로컬 export vs VPS export) | 20 | **1.00000** | 1.00000 | 0 |
| **Q8** (로컬 Q8 vs VPS Q8) | 20 | **0.99917** | 0.99979 | 0 |

- Q8도 Addendum 기대치(≥0.999)를 충족한다. 커널 경로 차이로 인한 미세 오차만 있다.
- CPU 플래그는 V0에서 5대 모두 동일(avx2/avx512f/bw/vnni) 확인됨.

## 3. 미검증

- **오디오 Q8 그래프**는 VPS에 원본 q8 파일이 없어 전송 없이는 재현할 수 없다.
  다음 중 하나로 확대 검증한다(후속):
  1. 340MB q8 그래프를 Notion/청크 업로드로 전송
  2. VPS에서 FP32 오디오 그래프를 export 후 동일 스크립트로 Q8 양자화(시간 소요)
- 나머지 4대는 모델 SHA256·lock·CPU 플래그 동일성으로 대체 확인했고, 개별 추론 검증은 하지 않았다.

## 4. 판정

**A-9.1(텍스트) 통과** — FP32 1.0, Q8 최소 0.99917. 오디오는 미검증으로 남긴다.
