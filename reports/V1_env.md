# V1 — VPS 공통 환경 구성 · 정합 · 캘리브레이션

- 작성: 2026-11-02
- 대상 게이트: G-V0 (a) venv·정합, (c) 캘리브레이션
- 호스트: `eg2-1` ~ `eg2-5` (Debian 13, Python 3.13.5, 4 vCPU, 7.9GB)
- 원시 로그: `logs/V1_setup.json`, `logs/V1_locks.json`, `logs/V1_probe.json`, `logs/v1_local.json`

## 1. 환경 구성

- 방식: 네이티브 venv(`/data/home/unigem/venv`), Docker 미사용 (문서 §8.2-7)
- 설치: numpy, onnx, onnxruntime, onnxscript, transformers, tokenizers, safetensors,
  huggingface-hub, psutil, torch(cpu wheel)
- **lock 일치:** 5대 전부 `lock_linux.txt` SHA256 `6cccf5e9…0470`, 43줄 (1종)
  - 최초 구성 시 eg2-1만 기존 venv가 남아 43줄 vs 41줄(filelock 버전·onnxscript 유무)로 갈렸다.
    전 머신 `FORCE_REBUILD=1`로 재구성해 단일 lock으로 통일했다.
- 버전: Python 3.13.5 / numpy 2.5.4 / onnx 1.23.2 / onnxruntime 1.31.1 /
  transformers 5.22.1 / torch 2.15.0+cpu

## 2. 정합 검증 (동일 ONNX 출력 cosine)

- 방법: 고정 시드로 생성한 소형 ONNX(MatMul 128→4096→4096→128 + LayerNorm + Softmax)를
  로컬과 각 VPS에서 실행, 출력 128차원 벡터의 cosine을 로컬 기준으로 비교.
- 결과: **5대 전부, 스레드 1/2/4 전 조합에서 cosine = 1.0** (부동소수 오차 없음)
- 해석: Windows(로컬)와 Linux VPS의 ORT FP32 결과가 사실상 동일하다. Phase A의 로컬 측정을
  VPS 재현 실험의 기준으로 쓸 수 있다.

## 3. 캘리브레이션 (참고(VPS))

동일 그래프, 30회 × 20반복, p50(ms). **판정에는 쓰지 않는다.**

| 호스트 | 1스레드 | 2스레드 | 4스레드 |
|---|---|---|---|
| local (Ryzen 7600) | 1.708 | 1.366 | 1.322 |
| eg2-1 | 1.453 | 0.999 | 0.370 |
| eg2-2 | 1.359 | 0.612 | 0.316 |
| eg2-3 | 1.348 | 0.615 | 0.577 |
| eg2-4 | 1.392 | 1.036 | 0.311 |
| eg2-5 | 1.423 | 1.079 | 0.606 |

- 상대 계수(로컬 p50 ÷ VPS p50, 4스레드): **약 3.6×** (범위 2.3~4.3)
- 4스레드에서 호스트 간 편차가 크다(0.31~0.61ms). 공유 vCPU의 순간 경합으로 보이며,
  **동시 실행 비교는 같은 시점·같은 설정에서만** 해야 한다(문서 §8.2-3).
- 이 벤치는 메모리 대역폭 위주라 EG2 추론의 절대 지연을 대표하지 않는다. 실제 계수는
  Phase B/C에서 작업별로 다시 측정한다.

## 4. steal time

유휴 상태 0.0~0.1%. 부하 시 steal은 V2 러너로 장시간 작업을 돌릴 때 재측정한다.

## 5. 판정

**G-V0 (a) 통과** — 5대 venv 구성 완료, lock 단일, 정합 cosine 1.0.
**G-V0 (c) 통과** — 캘리브레이션 표 기록.

## 6. 미해결

- 제공사 약관의 장시간 CPU·트래픽 조항은 미확인(문서로 확인 필요).
- 네트워크 대역(HF 다운로드 속도)은 아직 측정하지 않았다.
