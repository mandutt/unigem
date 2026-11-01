# A2b — 오디오 타워 FP32 연구용 그래프 export (원인 규명 및 재현 절차)

- 작성: 2026-11-02
- 대상: G-A1(오디오 연구용 FP32), G-A3S(Notesoop 특징 재현)의 입력 조건
- 호스트: `local` (Windows 11, Ryzen 5 7600, 15.6 GiB, CPU-only)
- 산출물: `onnx/eg2_audio_research_fp32_t500.onnx` (+`.onnx.data`)
- 상태: **export 성공 · PyTorch FP32 대비 cos 1.0 (실측)**

## 1. 결론

오디오 타워 export 실패는 모델 하나의 문제가 아니라 **서로 다른 4개의 원인이 순차적으로 겹친 것**이었다.
원인을 하나씩 제거한 뒤 **dynamo exporter + 정적 shape** 조합으로 FP32 다층 그래프를 얻었다.

```
.venv/Scripts/python.exe onnx/export_audio.py \
    --mel 500 --exporter dynamo --static \
    --out onnx/eg2_audio_research_fp32_t500.onnx
```

- 소요: 약 2~3분 (기존 무출력 14~17분과 대조)
- 출력: `audio_soft_tokens [1,125,512]`, `audio_mask [1,125]`,
  `aud_h_l00/04/08/11 [1,125,1024]`, `aud_out_proj [1,125,1536]`
- PyTorch FP32 대비 cosine: soft **1.0**, out_proj **1.0**, 층별(token 0) **1.0**, NaN 0

## 2. 원인 분석 (시도 순서대로)

| # | 증상 | 실제 원인 | 조치 | 결과 |
|---|---|---|---|---|
| 1 | legacy: `IndexError: invalid unordered_map<K, T> key` | `autograd.Function` inlining이 커스텀 연산의 노드 키를 잃음 (PyTorch #104067 계열) | `torch.onnx.export(..., autograd_inlining=False)` | 다음 단계로 진행 |
| 2 | legacy: ONNX `Pad`의 pad 상수가 `NoneType` | `Gemma4AudioAttention._convert_to_block` / `_extract_block_context`가 `F.pad(..., value 생략)` → tracer가 `value=None`을 상수로 굳힘 | export 동안 `F.pad` 기본값을 `0.0`으로 monkeypatch | 다음 단계로 진행 |
| 3 | legacy: `Unfold ... input size not accessible` | legacy exporter가 `Tensor.unfold`의 입력 크기를 추적하지 못함. **정적 shape으로도 해결되지 않음** | legacy 경로 포기 (모델 코드 재작성 없이는 불가) | **legacy = dead end** |
| 4 | dynamo: `Obtain model graph ... torch.export.export(..., strict=False)`에서 14~17분+ 무출력 | `dynamic_axes`가 dynamo에서 symbolic 제약으로 변환되고, 블록-슬라이딩 5D mask(`gather`/`repeat_interleave`, `num_blocks`가 T에 의존)와 결합해 제약 해소가 정체 | **`dynamic_axes` 제거 + 정적 shape(`--static`)** | export 완료 |
| 5 | `masked_select` 미지원オペレーター | 래퍼가 유효 토큰만 평탄화(`[N,512]`)하려고 사용 | 래퍼에서 제거, `audio_soft_tokens [B,T,512]` + `audio_mask`로 출력 | export 완료 |
| 6 | ORT 로드 실패: `mul_10_min_1 is not a graph input...` | ONNX optimizer가 `Clip`의 min 상수 노드를 지우고 참조만 남김 (정적 그래프 최적화 버그) | `torch.onnx.export(..., optimize=False)` | **로드·추론 정상** |

### 왜 dynamo + dynamic_axes가 멈추는가

- `dynamic_axes`는 dynamo 경로에서 권장되지 않으며(경고 출력), 내부적으로 `Dim` 제약으로 변환된다.
- 오디오 타워는 `input_features [B, T_mel, 128]`에서 `T_mel`이 `num_blocks`, `chunk_size`, `context`를 거쳐
  5D mask(`[B,1,num_blocks,chunk,context]`)의 `gather` 인덱스로 전파된다.
- 이 연쇄가 symbolic shape solver에 부담을 주어 `torch.export` 단계에서 진행이 멈춘다.
  (같은 모델이 정적 shape에서는 2~3분 내 통과한다.)

### 왜 legacy는 정적 shape으로도 안 되는가

- `unfold`는 legacy exporter의 `shape inference`가 입력 텐서의 크기를 알아야 하는데,
  `F.pad`를 거친 텐서의 shape이 tracer 상에서 `*`로 남아 `input size not accessible`가 된다.
- `autograd_inlining=False`와 `F.pad` 기본값 수정으로 앞단은 통과하지만, 이 지점은 모델 코드를
  `unfold` 대신 슬라이스+`stack`으로 재작성하지 않는 한 해결되지 않는다. **원본 모델 수정은 하지 않는다.**

## 3. 재현 절차 (코드 변경분)

`onnx/export_audio.py`에 반영된 4가지:

1. `F.pad` 기본값 패치 (legacy 전용이지만 무해하므로 공통 적용)
2. legacy일 때 `autograd_inlining=False`
3. `--static` 플래그: `dynamic_axes`를 전달하지 않음
4. dynamo일 때 `optimize=False`

추가로 래퍼는 `masked_select`를 쓰지 않고 `audio_soft_tokens`와 `audio_mask`를 그대로 출력한다.

## 4. 입출력 계약 (연구용 FP32)

| 구분 | 이름 | dtype | shape | 비고 |
|---|---|---|---|---|
| 입력 | `input_features` | float32 | `[1, 500, 128]` | **정적** (mel 500 = 5초) |
| 입력 | `input_features_mask` | bool | `[1, 500]` | 유효 mel 프레임 |
| 출력 | `audio_soft_tokens` | float32 | `[1, 125, 512]` | 패딩 포함, 소비자가 mask 적용 |
| 출력 | `audio_mask` | bool | `[1, 125]` | 유효 오디오 토큰 |
| 출력 | `aud_h_l00/04/08/11` | float32 | `[1, 125, 1024]` | 타워 층 hidden |
| 출력 | `aud_out_proj` | float32 | `[1, 125, 1536]` | output_proj 이후 |

- **정적 그래프이므로 입력 길이를 그래프별로 맞춰야 한다.** 짧은 오디오는 0으로 패딩하고 mask를 False로 준다.
- 16초(Notesoop 청크) 용 그래프는 `--mel 1600`으로 별도 export한다 (산출물 `eg2_audio_research_fp32_t1600.onnx`).
- 기존 운영 호환용 평탄화(`[N,512]`)는 q8 그래프(`eg2_audio_q8_layers.onnx`)가 담당한다.

## 5. 검증 로그

- 입력: FLEURS en_us 5초 클립 → `log_mel` 500 프레임 (전부 유효)
- 비교: PyTorch `Gemma4AudioModel` + `EmbeddingGemma2MultimodalEmbedder` (FP32, CPU)
- 결과: `soft_full 1.0`, `outproj_full 1.0`, `l00/l04/l08/l11 token0 1.0`, `nan 0`
- 스크래치: `%LOCALAPPDATA%\hermes\cache\scratch\eg2probe\audio_fp32_t500_ref.npz`

## 5.1 산출물 파일

| 파일 | 그래프 B | 가중치 B | SHA256 (graph) |
|---|---|---|---|
| `eg2_audio_research_fp32_t500.onnx` | 9,483,265 | 1,222,446,080 | `ccde2d3b…192bd` |
| `eg2_audio_research_fp32_t1600.onnx` | 9,485,098 | 1,222,446,080 | `13bc96d7…4a1` |
| `eg2_audio_research_fp32_t1600_l12.onnx` | 9,487,250 | 1,222,446,080 | `5a4e8313…b502` |
| `eg2_audio_research_fp32_t3000.onnx` | 9,485,098 | 1,222,446,080 | `a00b7616…c5d8` |

- t1600(16초, Notesoop 청크 길이)도 동일 절차로 export 성공. 스모크 실행 결과 출력 `[1,400,512]`,
  유효 토큰 125(입력 5초분), 전 출력 finite.
- `t1600_l12`는 12층 전체(`aud_h_l00..l11`, 총 15출력). 스모크: `[1,400,1024]`×12, finite.
- `t3000`(30초)은 `[1,750,512]`, 유효 토큰 125(입력 5초분), finite.
- 두 그래프 모두 가중치는 `.onnx.data` 외부 파일이며 git 미추적(.gitignore).

## 6. 게이트 판정

- **G-A1(오디오): PASS** — 기존 q8 파생(12층)에 더해 **FP32 연구용 다층 그래프**를 확보.
- **G-A3(오디오 수치 일치): PASS** — PyTorch FP32 대비 cos 1.0 (t500, 5초 클립 1건).
- G-A3S(Notesoop 특징 재현)는 t1600 그래프와 원 추출기 비교로 별도 판정한다.

## 7. 한계·미해결

- 정적 shape만 가능하다. 가변 길이 실시간 스트림에는 그래프 세트(예: 500/1600/3000) 또는 패딩 정책이 필요하다.
- 층 집합은 현재 `{0,4,8,11}`이다. C2-B의 층 조합 스윕에는 12층 전체 export가 필요할 수 있다(`--layers` 확장).
- batch는 1로 고정했다. 다중 배치는 그래프 재export 또는 루프 실행으로 처리한다.
- `optimize=False`로 그래프가 최적화되지 않아 추론 지연은 별도 측정이 필요하다(A4는 q8 기준).

## 8. 다음 단계

1. ~~t1600 export 결과 확인~~ → **완료** (16초 그래프 확보, 스모크 통과).
2. 필요 시 12층 전체 연구용 그래프 export (`--layers 0..11`).
3. CP1 안건에 "오디오 연구용 FP32 확보" 완료 보고.
