# A2 — ONNX 재수출 (텍스트 백본)

- 작성: 2026-11-02
- 대상 게이트: **G-A1** (시퀀스 다층 출력 + pooled를 한 세션에서 확보)
- 호스트: `local`

## 1. 목적

현재 운영 ONNX(G-A1 FAIL)를 대체할 연구용 그래프를 원본 체크포인트에서 재수출한다.
텍스트 백본은 `sentence_embedding`과 선택 층 hidden을 한 세션에서 출력해야 한다.

## 2. 환경 스냅샷

`reports/A0_env.md`와 동일. export 스크립트: `onnx/export_text.py`, torch 2.15.0+cpu, transformers 5.22.1,
onnxscript 0.7.2 (dynamo exporter).

## 3. 입력

| 항목 | 값 |
|---|---|
| 체크포인트 | `google/embeddinggemma-2` revision `f9972ac22e696a105c482202646979e33e4b5a1e` |
| 로컬 경로 | `data/models/embeddinggemma-2-f9972ac2/` |
| `model.safetensors` | 1,488,915,288 B, SHA256 `197a32965d4b1105faf060417baa899e193fb73cd401f42ec9295234d5553d79` (**HF blob과 일치**) |
| `tokenizer.json` | SHA256 `4d777ef5bdc1aa36227abdfb77c3e49e7b9c892d16e1b6bda41c393504828be4` (HF와 일치) |
| 실행 명령 | `.venv/Scripts/python.exe onnx/export_text.py --seq 16` |
| 시드 | 해당 없음 (학습 없음) |

> 로컬에 있던 기존 사본은 transformers 5.19.0 재저장본(바이트 불일치)이라 쓰지 않았다 (`reports/A0_env.md` §4.1).

## 4. 결과

### 4.1 그래프

| 항목 | 값 |
|---|---|
| 파일 | `onnx/eg2_text_research_fp32.onnx` + `.onnx.data` |
| 크기 | 5,285,487 B (graph) + 1,083,993,600 B (weights) |
| opset | 21 (단일 도메인, `com.microsoft` 없음) |
| nodes | 2,711 |
| dtype | float32 |
| 입력 | `input_ids` int64 `[B,S]`, `attention_mask` int64 `[B,S]`, `image_features` f32 `[N_i,512]`, `video_features` f32 `[N_v,512]`, `audio_features` f32 `[N_a,512]` |
| 출력 | `sentence_embedding` f32 `[B,768]`, `tok_h_l00/04/08/12/16/20` f32 `[B,S,512]`, `tok_h_last` f32 `[B,S,512]`, `tok_emb_768` f32 `[B,S,768]` |

층 정의(계약):
- `tok_h_l{NN}` = encoder layer NN(0-based) 출력, **final RMSNorm 이전**, 512차원.
- `tok_h_last` = final RMSNorm 이후, projection 이전, 512차원.
- `tok_emb_768` = `embedding_projection(tok_h_last)`, 768차원 (기존 `last_hidden_state`와 동일 지점).
- `sentence_embedding` = `normalize(mean(tok_emb_768, attention_mask))`.

### 4.2 export 중 관측

| 항목 | 값 |
|---|---|
| 모델 로드 | 2.5 s, RSS 1.32 GiB, peak 1.83 GiB |
| dry-run 출력 shape | `sentence_embedding (1,768)`, `tok_h_* (1,S,512)`, `tok_emb_768 (1,S,768)` |
| PyTorch 대조 | `tok_emb_768` vs `tm.last_hidden_state` — cos 1.0000001, **max abs diff 0.0** |
| `cos(se, normalize(mean(proj)))` | 1.0000001 |

## 5. 게이트 판정

**G-A1: PASS** — 한 세션에서 pooled(768) + 6개 층 hidden(512) + final-norm hidden + projected sequence를 모두 출력한다.
수치 일치(G-A3)는 `reports/A3_parity.md`.

## 6. 이상 징후

- 없음. 단, export는 dynamo 경로라 `onnxscript`가 필요했다(환경에 추가, lock 갱신).
- PyTorch 모델은 마지막에 norm+projection을 수행하는데, 본 그래프는 `tok_h_last`/`tok_emb_768`을 위해
  같은 연산을 한 번 더 계산한다(값은 동일, 그래프상 dead code는 exporter가 제거).

## 7. 미해결

- 오디오 타워 export — 별도 진행(`onnx/export_audio.py`), `reports/A2_export_audio.md`.
- Q8 양자화·성능 측정 — A4.

## 8. 다음 단계

A3 패딩 불변/batch 일치(완료) → 오디오 export·parity → A4 Q8.
