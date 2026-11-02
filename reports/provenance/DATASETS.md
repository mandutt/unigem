# 데이터셋·모델 확보 기록

- 작성: 2026-11-02
- 목적: 용량이 큰 자산을 삭제해도 **재획득 경로·해시**로 복원할 수 있게 한다.

## 1. Zeroth-Korean (C2 음성)

| 항목 | 값 |
|---|---|
| 출처 | HF 미러 `Bingsu/zeroth-korean` (원본 OpenSLR 40의 재배포), rev `bd173fe2c8ed0ddc47acb4eda77542593651622` |
| 라이선스 | **CC BY 4.0** |
| 규모 | 51.6h train + 1.2h test(457발화), parquet 7개 **2,874,794,995 B (2.7GB)** |
| 로컬 경로 | `data/raw/zeroth/data/*.parquet` |
| SHA256 | 파일별 목록 `reports/provenance/zeroth_sha256.json` (test `10c10f7f…`) |
| 용도 | Notesoop/komixv2 CER 기준선(C2-A1) |

재획득:
```python
from huggingface_hub import snapshot_download
snapshot_download("Bingsu/zeroth-korean", repo_type="dataset",
                  allow_patterns=["data/*.parquet"], local_dir="data/raw/zeroth")
```

- 검증: test 457 + train 22,263 = **22,720행**(공식 발화 수와 일치), test 1.191h(공식 1.2h), 전부 **16kHz mono**, 오디오는 **FLAC**(`fLaC` 매직) — OpenSLR tar의 무압축 WAV를 무손실 압축한 것이라 용량 차이(9.6GB→2.7GB)는 정상이다. 디코드 후 PCM 동일성이 보장되는 포맷이나, 원본 tar와 바이트 단위 대조는 수행하지 않았다.
- 판정: **동일 코퍼스로 사용 가능**. 발화 수·길이·샘플레이트가 원본 사양과 일치한다.

## 2. FLEURS (자연 문장·다국어)

| 항목 | 값 |
|---|---|
| 출처 | HF `google/fleurs` (dataset), rev `70bb2e84b976b7e960aa89f1c648e09c59f894dd` |
| 라이선스 | CC BY 4.0 |
| 로컬 | `~/.cache/huggingface/hub/datasets--google--fleurs/.../data/{lang}/{split}.tsv` (8개 언어 train/dev/test) |
| 용도 | 코퍼스 v2 자연 문장, LID 평가 |

재획득:
```python
from huggingface_hub import hf_hub_download
hf_hub_download("google/fleurs", "data/ja_jp/train.tsv", repo_type="dataset")
```

## 3. T5Gemma 2 270M (C0/C3 디코더)

| 항목 | 값 |
|---|---|
| 출처 | HF `google/t5gemma-2-270m-270m`, rev `7c38f16641f455ef0685b18431faf1b17722d5a1` |
| 접근 | gated — 사용자 계정 승인 완료 |
| 로컬 | `data/models/t5gemma-2-270m-270m/` |
| model.safetensors | 1,572,182,264 B, SHA256 `623a67dd770cefacce6bd77e63b5c127d843fb7749fbf67e919d7a5c3f866deb` |
| 용도 | C0 토크나이저 비교, C3 arm A1 |

재획득:
```python
from huggingface_hub import snapshot_download
snapshot_download("google/t5gemma-2-270m-270m", local_dir="data/models/t5gemma-2-270m-270m")
```

## 4. EG2 체크포인트

| 항목 | 값 |
|---|---|
| 출처 | HF `google/embeddinggemma-2`, rev `f9972ac22e696a105c482202646979e33e4b5a1e` |
| model.safetensors | 1,488,915,288 B, SHA256 `197a32965d4b1105faf060417baa899e193fb73cd401f42ec9295234d5553d79` |
| 로컬 | `data/models/embeddinggemma-2-f9972ac2/` |

## 5. 미확보 (신청·약관 필요)

| 데이터 | 사유 |
|---|---|
| AI Hub 한국어 음성 | 신청·약관 확인 필요 |
| NIKL 맞춤법 교정 말뭉치 | 신청 필요, 비상업 제한 가능 |
| Common Voice ko | CC0, 필요 시 즉시 다운로드 가능(미착수) |
| RICO(UI 화면) | 연구용 라이선스 확인 필요 |

## 6. COCO val2017 (C1 후보)

| 항목 | 값 |
|---|---|
| 출처 | https://cocodataset.org — `val2017.zip`(778MB), `annotations_trainval2017.zip`(242MB) |
| 라이선스 | 이미지별 Flickr 라이선스, 주석 CC BY 4.0 |
| 로컬 | `data/raw/coco/` |
| 용도 | 비전 태깅 후보 이미지(사진 30장 선별) |

## 7. 이모지 데이터 (C1 후보표)

| 항목 | 값 |
|---|---|
| 출처 | Unicode `emoji-test.txt`(656KB), CLDR `annotations_ko.xml`(350KB)/`en.xml`(290KB) |
| 라이선스 | Unicode License |
| 로컬 | `data/raw/emoji/` |
| 용도 | 이모지 후보표·한국어 명칭 |

## 8. C2 평가 자산 (Notesoop 비교)

| 자산 | 크기 | 위치·출처 |
|---|---|---|
| Notesoop 리더 가중치 | 137,379,319 B | HF `Phsoft-ai/Notesoop-STT-Ko-v1` → `checkpoints/best_reader_inference.pt` |
| KenLM 3-gram | 86,738,030 B | 동일 repo → `data/vocab/korean_lm.bin` |
| vector bank | 12,801,093 B | 동일 repo → `data/vocab/vector_bank_25k.pt` |
| vocab 25k | 1,152,753 B | 동일 repo → `data/vocab/vocab_25k.json` |
| sample_audio | 96,044 B | 동일 repo → `sample_audio.wav` |
| komixv2 (ct2) | 740MB | `%LOCALAPPDATA%/jev-mem/bench/run-20261024-embedgemma2ko/komixv2-ct2` |
| faster-whisper large-v3-turbo | HF 캐시 | `deepdml/faster-whisper-large-v3-turbo-ct2` |
| FLEURS ko test 오디오 | 205MB | `C:\code\eg2-langidentifier\data\raw\fleurs_cache\ko_kr_test.tar.gz` |
| Zeroth test | 457발화/1.19h | `data/raw/zeroth/data/test-*.parquet` |

