# EG2 텍스트 hidden 연구 자산 (보존)

Addendum C §C-2.3에 따라 삭제·덮어쓰기 금지. 재현 방법과 함께 보존한다.

## 그래프

| 파일 | 용도 |
|---|---|
| `onnx/eg2_text_research_fp32.onnx`(+`.data`) | 텍스트 9출력 연구용(FP32) |
| `onnx/eg2_text_research_q8.onnx`(+`_data`) | 텍스트 Q8 연구용 |
| `onnx/eg2_text_prod_q8.onnx`(+`_data`) | 운영 후보 Q8 |
| `onnx/eg2_audio_research_fp32_t500/t1600/t1600_l12/t3000.onnx` | 오디오 연구용(정적 길이) |
| `onnx/eg2_audio_q8_layers.onnx` | 오디오 다층 Q8(운영) |

재현: `python onnx/export_text.py`, `python onnx/export_audio.py --static`, `python onnx/quantize_q8.py`.

## 데이터·캐시

| 경로 | 내용 |
|---|---|
| `data/b1_5/corpus_v2/` | 코퍼스 v2 4,695문장/198,317토큰 |
| `cache/b1_5/` | l00~last fp16 특징 19샤드 |
| `cache/b1_5_q8/` | Q8 특징 샤드 |
| `data/p1/p1_corpus.jsonl` | P1 F4 파일럿 5,700행 |
| `cache/p1/` | P1 특징 샤드 |
| `data/r2/` | T1 확장·T3′ 코퍼스 |
| `data/r3/`, `cache/r3_*` | 접두사 3조건(선행 완료) |

## 코드·결과

- 프로브/헤드: `train/b15_*.py`, `train/r1_*.py`, `train/r2_*.py`, `train/p1_*.py`
- 결과: `reports/R1_B1_5_1_rerun.md`, `R2_B1_5_3_rerun.md`, `P1_f4_pilot.md`, `G_C2a.md`, `R3_prefix.md`, `C3_records_fix.md`
- 원시 JSON: `reports/provenance/`, `logs/*.json`(git 미추적)

## H4′ 자산

- 분절 정렬 결과: `reports/D1_h4prime.md` (4,695/4,695 = 100%)
- EG2 ↔ T5Gemma 2 **문자열 기반 토큰 id 변환표**: 필요 시 `tokenizer.json` 두 개로 재생성(코드 `eval/c0_tokenizer.py` 참조)

## 재개 조건

Addendum C §C-2.4 참조. 재개는 새 사전 선언 실험으로만 한다(AM-8).
