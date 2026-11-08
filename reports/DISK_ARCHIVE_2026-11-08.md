# Disk archive — 2026-11-08

## 목적

C: 드라이브 여유 부족(검토요청서 §5)에 대응해, **현재 F5/Stage B에 쓰지 않는 대용량 데이터·모델 형식 사본**을 외장 D: 드라이브로 이동했다. **삭제는 하지 않았다.**

## 결과

| 항목 | 이동 전 | 이동 후 |
|---|---:|---:|
| C: 여유 | 41 GB | **123 GB** |
| D: 여유 | 332 GB | **250 GB** |
| 이동량 | — | **약 82 GB** |

목적지: `D:\unigem\archive_2026-11-08\`

## 이동 목록

| 원래 경로 (C:) | 보관 경로 (D:) | 크기 | 사유 |
|---|---|---:|---|
| `data/wave2b` | `data/wave2b` | 45 GB | STT 동결(D-079) |
| `data/wave1` | `data/wave1` | 12 GB | STT 동결 |
| `data/wave2a_lite` | `data/wave2a_lite` | 5.9 GB | STT 동결 |
| `data/raw` | `data/raw` | 6.6 GB | 원본 데이터, F3/F4 재개 시 복원 |
| `data/wave2c/b1d` | `data/wave2c/b1d` | 3.3 GB | 과거 T5Gemma2 bridge teacher cache |
| `data/wave2c/a2null` | `data/wave2c/a2null` | 2.4 GB | A2-null exploratory |
| `data/wave2c/a2null_pilot` | `data/wave2c/a2null_pilot` | 454 MB | A2-null pilot |
| `data/wave2c/eg2_concat` | `data/wave2c/eg2_concat` | 717 MB | concat 기각(D-103) |
| `data/wave2c/eg2_layer24` | `data/wave2c/eg2_layer24` | 601 MB | projection layer, 현재 계획 제외 |
| `data/models/mt5-small/onnx` | `models/mt5-small/onnx` | 3.7 GB | ONNX 미사용, 향후 ONNX 전환 시 복원 |
| `data/models/mt5-small/tf_model.h5` | `models/mt5-small/tf_model.h5` | 1.2 GB | TensorFlow 미사용 |
| `data/models/mt5-small/flax_model.msgpack` | `models/mt5-small/flax_model.msgpack` | 1.2 GB | Flax 미사용 |

## C:에 유지한 것

| 경로 | 이유 |
|---|---|
| `data/wave2c/eg2_layer0`~`eg2_layer23` | Stage B1/B2 feature cache (24개, 약 9.6 GB) |
| `data/models/mt5-small/pytorch_model.bin`, tokenizer | Stage B0/B1 PyTorch 경로 |
| `data/models/umt5-small` | Stage B2 |
| `data/models/embeddinggemma-2-f9972ac2` | EG2 feature·layer role probing |
| `data/models/t5gemma-2-270m-270m` | A1 native fallback |
| `data/models/f5_t5gemma2_lora` | A1 native `full_2ep` 포함, 과거 bridge 산출물 |
| `data/external/f5_pairs_v3_clean.jsonl`, `splits.json` | 현재 F5 데이터 |
| `docs/`, `reports/`, `eval/`, `runner/` | 코드·문서·원장 |

## 검증

- `robocopy /MOVE` 전 항목 **RC=1**(정상: 파일 복사 완료), 최종 exit 0
- 이동 대상 source 디렉터리 **잔여 없음**
- `data/wave2b`의 git 추적 메타데이터 5개는 C로 복원:
  - `V2_READY.json`
  - `short_4h_v2_summary.json`
  - `vocab_v2.json`
  - `vocab_v2_alltrain.json`
  - `preflight/split_candidate.json`
- `git status` 기준 **tracked deletion 없음**
- 단위 테스트: **47 tests OK**
- mT5 smoke after move (`layer19`, 2 train / 2 val, 2 step):
  - `val_real_ce 12.2921`
  - `val_zero_ce 30.1188`
  - `delta_shuffled -0.0152`
  - 목적: 모델 로딩·feature 경로 정상 확인. 성능 판정 아님.

## 복원 방법

```cmd
robocopy "D:\unigem\archive_2026-11-08\data\wave2b" "C:\code\unigem\data\wave2b" /E
robocopy "D:\unigem\archive_2026-11-08\data\wave1" "C:\code\unigem\data\wave1" /E
robocopy "D:\unigem\archive_2026-11-08\data\wave2a_lite" "C:\code\unigem\data\wave2a_lite" /E
robocopy "D:\unigem\archive_2026-11-08\data\raw" "C:\code\unigem\data\raw" /E
```

ONNX를 사용할 경우:

```cmd
robocopy "D:\unigem\archive_2026-11-08\models\mt5-small\onnx" "C:\code\unigem\data\models\mt5-small\onnx" /E
```

또는 C 경로를 유지해야 하는 코드에는 junction을 사용한다.

```cmd
mklink /J "C:\code\unigem\data\models\mt5-small\onnx" "D:\unigem\archive_2026-11-08\models\mt5-small\onnx"
```

## 주의

- D:는 외장 드라이브이므로 **분리 시 복원·학습 스크립트가 실패**할 수 있다.
- `data/raw`를 참조하는 과거 스크립트는 복원 전까지 실행하지 않는다.
- `data/wave2b`는 메타데이터만 C에 남아 있으므로, 전체 재현 시 D에서 복원한다.
- 이 문서는 **삭제가 아니라 이동**을 기록한다.
