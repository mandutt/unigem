# A0 — 환경 고정 (환경 스냅샷)

- 작성: 2026-11-02
- 대상 게이트: 없음 (A0는 환경 고정 단계)
- 호스트: `local` (목표 하드웨어, 최종 판정 환경)

## 1. 목적

프로젝트 venv를 운영 venv와 분리해 고정하고, 이후 모든 보고서에 붙일 환경 스냅샷을 만든다.
기존 운영 자산은 읽기 전용으로만 참조한다(문서 §0-3).

## 2. 하드웨어·OS

| 항목 | 값 |
|---|---|
| OS | Windows 11 Pro, 10.0.26300 |
| CPU | AMD Ryzen 5 7600 6-Core (6C/12T, base 3.8 GHz, Zen 4 — AVX-512 계열 지원) |
| RAM | 16,735,182,848 B = 15.59 GiB |
| GPU | 없음 (ORT `CPUExecutionProvider`만 노출) |
| 디스크 C: | 858 GiB total / 103 GiB free (88% 사용) |
| 셸 | git-bash(MSYS) 3.6.6 |

## 3. 소프트웨어

### 3.1 프로젝트 venv (신규, `C:\code\unige\.venv`)

| 패키지 | 버전 |
|---|---|
| Python | 3.12.13 (uv 관리) |
| numpy | 2.5.4 |
| onnx | 1.23.2 |
| onnxruntime | 1.31.1 |
| torch | 2.15.0+cpu |
| transformers | 5.22.1 |
| tokenizers | 0.23.3 |
| safetensors | 0.8.0 |
| huggingface-hub | 2.4.0 |
| psutil | 7.2.2 |

- lock: `env/lock_local_2026-11-02.txt` (41줄, SHA256 `c5321c4e0a1d709c995d476e23996a4dc34a09b7dfd3def8e0ef0d1f2a40f03f`)
- ORT 세션 옵션(A2에서 확정): `intra_op_num_threads` 명시, `ORT_ENABLE_ALL`, `CPUExecutionProvider`.

### 3.2 기존 운영 환경 (읽기 전용, 수정 금지)

| 항목 | 값 |
|---|---|
| venv | `%LOCALAPPDATA%\jev-mem\venv` (Python 3.14.7) |
| onnxruntime | 1.30.0 |
| onnx | 1.23.1 |
| torch | 2.14.1 |
| transformers | 5.20.1 |
| tokenizers | 0.23.2 |
| numpy | 2.5.3 |
| ORT providers | `AzureExecutionProvider`, `CPUExecutionProvider` |

> **주의(기존 프로젝트 기록):** transformers 5.20은 whisper 계열 파인튠(komixv2) 전사가 깨지는 것이
> eg2-langidentifier에서 실측되었다. Phase C2/D1의 ASR 평가는 transformers 4.57.x 고정이 필요하다.
> 이 프로젝트 venv의 5.22.1은 EG2 export 전용으로 쓰고, ASR용은 별도 env로 분리한다.

## 4. 입력 자산 (읽기 전용)

현재 운영 ONNX — `C:\code\eg2-langidentifier\scripts\mmal4\`

| 파일 | 크기 (B) | SHA256 |
|---|---|---|
| `model_quantized_al4.onnx` | 500,889 | `39c1ce1fcd7b0c31b10dd9be698f2296c206a8321b49cefeda5e0c212427ef73` |
| `model_quantized_al4.onnx_data` | 313,724,928 | `278a7ff1248c3618e4bd11a607fc54f7bdc7778854230f3956d3f86bd9db4f3b` |
| `audio_encoder_quantized_al4.onnx` | 254,189 | `837a2eff88dccbb7f221686bf0cd3070701927483fd3d4c1fa7c579388ae5823` |
| `audio_encoder_quantized_al4.onnx_data` | 340,058,624 | `aa6361d898e1f1d6303f8dd2b5fabf4fd3629e15fd709e9cb06ac5cb9416a030` |

HF 체크포인트 사본 — `%LOCALAPPDATA%\jev-mem\bench\run-20261024-embedgemma2ko\model-src\`

| 파일 | 크기 (B) | SHA256 / 비고 |
|---|---|---|
| `model.safetensors` | 1,488,915,288 | (미계산 — A2에서 기록) bf16 |
| `tokenizer.json` | 32,170,510 | `4d777ef5bdc1aa36227abdfb77c3e49e7b9c892d16e1b6bda41c393504828be4` |
| `config.json` | 4,450 | text 24층/hidden 512/embedding 768, audio 12층/hidden 1024 |

> 이 사본의 HF revision은 **미확인**이다. A2.1에서 `google/embeddinggemma-2`의 config·tokenizer 해시와
> 대조해 revision을 고정한다.

## 5. 게이트 판정

해당 없음 (A0는 판정 게이트 없음). 환경 분리 확인: 프로젝트 venv와 운영 venv가 서로 다른 Python(3.12 vs 3.14)이며
site-packages를 공유하지 않는다.

## 6. 이상 징후

- `config.json`의 `text_config.max_position_embeddings = 262144` — 문서 §5.1의 "컨텍스트 8192"와 불일치.
  문서 수치를 사실로 가정하지 않고 A2에서 유효 컨텍스트를 확인한다.
- 시스템 Python 기본이 3.14.6이라 일부 wheel 호환이 나쁘다. 프로젝트는 3.12로 고정했다.

## 7. 미해결

- 프로젝트 venv의 transformers 5.22.1이 EG2 ONNX export에 호환되는지 미검증 (A2에서 확인, 실패 시 5.19.x로 내림).
- A2 export용 체크포인트 provenance 미확인.

## 8. 다음 단계

A2.1(체크포인트 provenance 고정) → A2.2(텍스트 연구용 export). 사용자 승인(OA-4) 필요.
