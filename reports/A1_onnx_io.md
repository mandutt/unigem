# A1 — 현재 ONNX 점검 (입출력 계약)

- 작성: 2026-11-02
- 대상 게이트: **G-A1** (시퀀스 다층 출력 + pooled를 한 세션에서 확보)
- 호스트: `local`
- 입력: `C:\code\eg2-langidentifier\scripts\mmal4\` (운영 중 q8-al4, 읽기 전용)

## 1. 목적

현재 운영 중인 EG2 ONNX가 어떤 출력을 내는지 확인한다. pooled만 나오면 A2 재수출이 필수다(문서 §9 A1).

## 2. 환경 스냅샷

`reports/A0_env.md`와 동일. 검사 도구: `onnx 1.23.2`(그래프), `onnxruntime 1.31.1` + `tokenizers 0.23.3`(실행).

## 3. 결과 — 그래프

### 3.1 텍스트 백본 `model_quantized_al4.onnx`

| 항목 | 값 |
|---|---|
| IR / opset | 10 / `""` 21, `com.microsoft` 1 |
| producer | huggingface |
| nodes / initializers | 1,068 / 655 |
| 양자화 | `MatMulNBits` 146개, **bits=8** (int8 블록, accuracy_level=4 = q8-al4) |

입력

| 이름 | dtype | shape |
|---|---|---|
| `input_ids` | int64 | `[batch_size, sequence_length]` |
| `attention_mask` | int64 | `[batch_size, sequence_length]` |
| `image_features` | float32 | `[num_image_tokens, 512]` |
| `video_features` | float32 | `[num_video_tokens, 512]` |
| `audio_features` | float32 | `[num_audio_tokens, 512]` |

출력

| 이름 | dtype | shape |
|---|---|---|
| `last_hidden_state` | float32 | `[batch_size, sequence_length, 768]` |
| `sentence_embedding` | float32 | `[batch_size, 768]` |

### 3.2 오디오 타워 `audio_encoder_quantized_al4.onnx`

| 항목 | 값 |
|---|---|
| IR / opset | 10 / `""` 20, `com.microsoft` 1 |
| producer | pytorch 2.10.0 |
| nodes / initializers | 1,148 / 859 |
| 양자화 | `MatMulNBits` 123개, **bits=8** |

입력: `input_features` float32 `[s4, s37, 128]` = `[B, T_mel, 128]`, `input_features_mask` **bool** `[s4, s37]`
출력: `audio_features` float32 `[u0, 512]` (= 오디오 soft token, 25 Hz)

## 4. 결과 — 실행 확인

토크나이저: `run-20261024-embedgemma2ko\model-src\tokenizer.json` (SHA256 `4d777ef5…828be4`).
세션: `intra_op_num_threads=6`, `ORT_ENABLE_ALL`, `CPUExecutionProvider`.

| 입력 | `last_hidden_state` | `sentence_embedding` | 관측 |
|---|---|---|---|
| `task: search result \| query: hello world` (11 tok) | `[1,11,768]`, row norm 335.4 ~ 4,734.0 | `[1,768]`, norm 1.0000001 | `cos(se, mean_pool(lh)) = 1.0000000` |
| 같은 입력 반복 | — | — | `cos = 1.0000004` (결정적) |
| `task: search result \| query: ` + `word`×200 (210 tok) | `[1,210,768]`, row norm 76.4 ~ 7,358.6 | norm 1.0000004 | `cos(se, mean_pool(lh)) = 0.9999999` |

해석(측정으로 확인된 것만):

1. `sentence_embedding`은 **시퀀스 평균 pooling 후 L2 정규화**된 768차원이다 (cos = 1.0).
2. `last_hidden_state`는 **768차원이며 정규화되지 않았다** — row norm이 335~7,358로 크게 변한다.
   text_config의 hidden_size는 512이므로 이 텐서는 **768차원 projection 이후** 지점이다.
   즉 문서가 요구하는 "백본 층 hidden `[B,S,512]`"은 **현재 그래프에 없다**.
3. `attention_mask`는 그래프 안에서 pooling에 쓰이지만, 패딩이 섞인 batch에서의 불변성은 이번에 시험하지 않았다(A3에서 수행).

## 5. 게이트 판정

**G-A1: FAIL** — 근거:

- 확보된 시퀀스 출력은 `last_hidden_state` **1개 층(projection 이후 768차원)**뿐이다.
- 요구사항은 "선택 가능한 여러 층의 hidden + pooled를 한 세션에서" 확보하는 것이다.
- 오디오 타워도 `audio_features` 단일 출력이며 층별 hidden이 없다.

FAIL은 예상된 결과다(문서 §15 "현재 ONNX가 pooled만 출력 → A2 재수출"). A2에서 재수출한다.

## 6. 이상 징후

- `last_hidden_state`가 768차원이라, 이름만 보고 "백본 hidden"으로 오인하면 F4 edit 태깅의 입력 차원을
  잘못 설계하게 된다. 계약에 `tok_h_*`(512, projection 이전)와 `tok_emb_768`(768, 이후)을 분리해 표기했다.
- 오디오 `input_features_mask`는 int64가 아니라 **bool**이다. A2에서 동일 dtype을 유지해야 기존 소비자와 호환된다.

## 7. 미해결

- 패딩 불변성, batch 1/N 일치, 원본 PyTorch 대비 수치 일치 → A3.
- `last_hidden_state`가 정확히 어느 모듈 출력인지(projection layer 이름) → A2 export 시 그래프에서 확인.

## 8. 다음 단계

A2 재수출 (사용자 승인 OA-4 후). 계약 초안: `onnx/contracts/eg2_io_v1_draft.json`.
