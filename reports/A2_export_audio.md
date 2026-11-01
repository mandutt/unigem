# A2 — 오디오 타워 다층 출력 (그래프 수술 방식)

- 작성: 2026-11-02
- 대상 게이트: G-A1 (오디오 측 다층 hidden)
- 호스트: `local`
- 산출물: `onnx/eg2_audio_q8_layers.onnx` (+`.onnx_data`)

## 1. 결론

**재수출(export) 대신 기존 운영 q8 오디오 그래프에 중간 텐서를 출력으로 추가하는 방식으로 해결했다.**
원본 그래프·가중치는 불변(복사본만 수정, §0-8 허용 범위). 12개 층 hidden과 `aud_out_proj`를 확보했고,
PyTorch 대비 cosine **0.99945~0.999998**, 패딩 불변 cosine **1.0**이다.

## 2. export가 막힌 이유 (기록)

| 시도 | 환경 | 결과 |
|---|---|---|
| legacy exporter (`dynamo=False`) | 로컬 | `IndexError: invalid unordered_map<K, T> key` (커스텀 autograd 연산) |
| dynamo exporter, mel 3000 | 로컬 | 420초 타임아웃 |
| dynamo exporter, mel 750 | 로컬 | 831초+ 무출력 → 중단 |
| dynamo exporter, mel 500 | 로컬 | 790초+ 무출력 → 중단 |
| dynamo exporter, mel 500 | VPS `eg2-1` (8 GiB) | 17분+ 무출력 → 중단 |

원인 후보: Gemma4 audio의 블록-슬라이딩 attention(5D mask) + conv subsampling이 dynamo 변환에서
과도한 그래프/심볼릭 제약을 만든다. (Exa 검색: Gemma-4 계열 dynamo export의 알려진 난제 — PyTorch issue #182266,
optimum-onnx의 gemma4 미지원.)

## 3. 그래프 수술 절차

1. 운영 q8 그래프(`audio_encoder_quantized_al4.onnx`)에 `onnx.shape_inference` 적용.
2. `[B,T,1024]` 후보 533개를 임시 출력으로 추가한 probe 그래프를 만들어 1회 실행.
3. PyTorch 타워(12층, hook) 출력과 cosine 매칭 → 층별 정확 텐서 식별:
   **`type_as_8`, `type_as_17`, …, `type_as_107`** (9 간격, cos 0.99997~0.999998).
4. `[B,T,1536]` 후보 3개 중 `linear_133`이 `out_proj`와 cos 0.99945로 일치.
5. 최종 그래프: 위 12개 + `aud_out_proj`를 Identity 출력으로 추가해 저장.

## 4. 입출력 계약 (실측)

| 구분 | 이름 | dtype | shape |
|---|---|---|---|
| 입력 | `input_features` | float32 | `[B, T_mel, 128]` |
| 입력 | `input_features_mask` | bool | `[B, T_mel]` |
| 출력 | `audio_features` | float32 | `[N, 512]` (유효 토큰 평탄화, 기존 호환) |
| 출력 | `aud_h_l00` … `aud_h_l11` | float32 | `[B, T_audio, 1024]` (타워 layer 출력) |
| 출력 | `aud_out_proj` | float32 | `[B, T_audio, 1536]` (output_proj 이후) |

- `T_audio` = stride-2 conv 2회 적용 후 길이. 소비자는 출력 마스크를 `input_features_mask[:, ::2][:, ::2]`로 만든다.
- `audio_features`는 `aud_out_proj`를 `embed_audio`(1536→512)로 투영한 뒤 유효 토큰만 평탄화한 값이다.

## 5. 파일

| 파일 | 크기 (B) | SHA256 |
|---|---|---|
| `eg2_audio_q8_layers.onnx` | 251,021 | `03e0ad8608cdbc810ddee3e8ab78b46675e5ef1615929d0b63476aa171c52d59` |
| `eg2_audio_q8_layers.onnx_data` | 340,058,624 | `aa6361d898e1f1d6303f8dd2b5fabf4fd3629e15fd709e9cb06ac5cb9416a030` (원본과 동일) |

## 6. 게이트 판정

**G-A1(오디오): PASS (q8 파생)** — 다층 hidden 12개 + soft token을 한 세션에서 확보.
이후 **FP32 연구용 그래프도 export에 성공**했다 → `reports/A2_export_audio_research.md` 참조.
원인은 4중(autograd inlining, `F.pad` None 상수, legacy `unfold` 미지원, dynamo의 symbolic shape 정체)이었고,
`dynamo + 정적 shape + optimize=False` 조합으로 해결했다.

## 7. 한계·주의

- 이 그래프는 **q8 가중치**다. FP32 참조가 필요하면 (a) PyTorch 타워를 오프라인으로 돌리거나,
  (b) 향후 export가 성공할 때 다시 만들어야 한다.
- 원본 파일은 건드리지 않았다(복사본에 출력만 추가).
- `audio_mask`는 그래프 출력이 아니다 — 소비자가 입력 마스크에서 계산한다(위 규칙).

## 8. 다음 단계

C2-A3(Notesoop 호환성)에서 이 q8 다층 특징을 사용할 수 있다. FP32 조건이 필요하면 CP1에서 결정.
