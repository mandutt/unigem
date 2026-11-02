# ONNX 산출물 Provenance

- 체크포인트: `google/embeddinggemma-2` rev `f9972ac2e696a105c482202646979e33e4b5a1e`
- `model.safetensors` SHA256 `197a32965d4b1105faf060417baa899e193fb73cd401f42ec9295234d5553d79`
- 런타임: onnxruntime 1.31.1 CPU EP, Python 3.12

| 파일 | 크기 | SHA256 | 재생성 |
|---|---|---|---|
| eg2_text_research_fp32.onnx | 5,285,487 | `d55432f9af8aadb2…` | `.venv/Scripts/python.exe onnx/export_text.py --out onnx/eg2_text_research_fp32.onnx --seq 16` |
| eg2_text_research_fp32.onnx.data | 1,083,993,600 | `62d80161d4115dd3…` | `same as eg2_text_research_fp32.onnx` |
| eg2_text_research_q8.onnx | 4,929,716 | `34e210a68ffae642…` | `.venv/Scripts/python.exe onnx/quantize_q8.py --input onnx/eg2_text_research_fp32.onnx --output onnx/eg2_text_research_q8.onnx` |
| eg2_text_research_q8.onnx.data | 679,208,960 | `b5b0ca0821cb86d7…` | `same as eg2_text_research_q8.onnx` |
| eg2_audio_research_fp32_t500.onnx | 9,483,265 | `ccde2d3b62babda9…` | `.venv/Scripts/python.exe onnx/export_audio.py --mel 500 --static --out onnx/eg2_audio_research_fp32_t500.onnx` |
| eg2_audio_research_fp32_t500.onnx.data | 1,222,446,080 | `8ca5dfd5abcb5010…` | `same as eg2_audio_research_fp32_t500.onnx` |

## 전체 SHA256

- `eg2_text_research_fp32.onnx`: `d55432f9af8aadb271db61b730d2fe46a31ca858dd4af6eb82a95bb6f65edf8e`
- `eg2_text_research_fp32.onnx.data`: `62d80161d4115dd3046f3f11ef342720c797305f8005a35725fe9f01ac3105e5`
- `eg2_text_research_q8.onnx`: `34e210a68ffae64252f7c910fee362adca29772c0be9c33cb399faa376579b65`
- `eg2_text_research_q8.onnx.data`: `b5b0ca0821cb86d7838bc1d95a0cff5bcac3d47812c8b004e2dfd2495c85d717`
- `eg2_audio_research_fp32_t500.onnx`: `ccde2d3b62babda91bf767b6b930b8fd532f6d20a76ce0ba83c347a6bf0192bd`
- `eg2_audio_research_fp32_t500.onnx.data`: `8ca5dfd5abcb501035928869c4dacd51cde67c79be8bfb91cabe80564eb4cf75`