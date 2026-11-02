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

## 9. C1 UI 데이터 (2026-11-02 확보)

| 자산 | 크기 | 라이선스 | 위치 |
|---|---|---|---|
| ShowUI_Web 어노테이션 | `samples.json` 304MB (22,000 화면/576,000 요소 bbox) | **Apache-2.0** | `data/raw/showui_web/samples.json` |
| ShowUI_Web 이미지 부분집합 | **540장**, 전체 711MB | Apache-2.0 | `data/raw/showui_web/data/` |

- 출처: HF `ZhuOnR/ShowUI_Web` (Show Lab NUS + Microsoft)
- **전체 이미지 22,000장(약 16GB)은 받지 않았다.** 파일당 전송이 느려(≈1.5s/파일) 대표 540장 + 전체 어노테이션만 확보.
- 전체가 필요할 때:
```python
from huggingface_hub import snapshot_download
snapshot_download("ZhuOnR/ShowUI_Web", repo_type="dataset",
                  allow_patterns=["data/**"], local_dir="data/raw/showui_web")
```
- 용도: C1 이모지 태깅 평가 이미지(웹 UI). 어노테이션의 bbox를 이모지 후보표와 매칭.

## 10. C3 디코더 학습 데이터 (2026-11-02 확보)

| 자산 | 크기 | 라이선스 | 위치 |
|---|---|---|---|
| open-korean-instructions | 745MB (375K행) | 소스별 혼재(NC 포함) | `data/raw/ko_instruct/` |
| kullm-v2 | 252MB (152K) | Apache-2.0 | `data/raw/kullm_v2/` |
| KITE | 270KB (527 지시) | Apache-2.0 | `data/raw/kite/` |

## 11. C5 요약 데이터 (2026-11-02 확보)

| 자산 | 크기 | 라이선스 | 위치 |
|---|---|---|---|
| XL-Sum Korean | tar 5.7MB → **5,507건**(train 4,407 / val 550 / test 550) | **CC BY-NC-SA 4.0** | `data/raw/xlsum/korean/*.jsonl` |

- 비상업 라이선스이므로 연구 평가에만 사용한다.
- AI Hub 문서요약(원문 40만/요약 80만)은 사용자가 신청 예정.

## 12. AI Hub 데이터 (2026-11-02 사용자 다운로드)

경로: `C:\code\dataset\ai_hub\` (프로젝트 외부, 원본 zip 유지)

### 12.1 문서요약 텍스트 (dataSetSn=97)

| 항목 | 값 |
|---|---|
| 규모 | zip 6개, **402MB** |
| 구성 | Training 3 + Validation 3 (법률/사설/신문기사) |
| 문서 수 | **365,206** (train 325,072 / valid 40,134) |
| 필드 | `title`, `text[]`(문장·highlight_indices), `extractive[]`(문장 인덱스), `abstractive[]`(요약문), `document_quality_scores` |
| 비고 | 공식 40만 건 중 **잡지 카테고리 없음**(신문 30만/기고 6만/법률 3만 중 일부) |

### 12.2 요약·기계독해 말뭉치 (dataPckageSn=3)

| 항목 | 값 |
|---|---|
| 규모 | **36GB**, 하위 19개 데이터 |
| 주요 | 022 요약문·레포트 **146,771 train + 18,300 valid** passage, `summary1~3` |
| 기타 | 018 논문자료 요약 1.7GB, 029 구매도서 말뭉치 17GB, 전문분야 14GB, 153 기술과학 요약 307MB, 157 사실성 검증 314MB |
| 비고 | 022는 **passage 단위 JSON 146,771개**(zip 내 개별 파일) |

### 12.3 인터페이스(자판/음성)별 고빈도 오류 교정 (dataSetSn=71560)

| 항목 | 값 |
|---|---|
| 규모 | zip 24개(원천 12 + 라벨 12), **45MB** |
| 레코드 | **205,550** (train 180,700 / valid 24,850) |
| 범주 | 오탈자 88,000 / 띄어쓰기·문장부호 36,000 / 음성인식 24,000 / 자동생성 18,000 / 맞춤법 14,400 / 자주 틀리는 맞춤법 300 (train 기준) |
| 필드 | `annotation.err_sentence`, `cor_sentence`, `err_sentence_spell`, `errors[]`(`err_location`, `err_text`, `cor_text`, `err_details`) |
| 비고 | 공식 290,500문장 중 일부(6범주). 원천·라벨 zip 분리 |

- 라이선스: **AI Hub 이용약관**(내국인 신청·승인). 상업적 활용은 별도 조건 확인 필요.
- 가공 없이 zip을 스트리밍으로 읽는다(`zipfile` + `ijson`).

### 12.4 Notion 백업 (2026-11-02)

- 페이지: `AI Hub Datasets` (`40c1f1de-06e4-818f-8921-f3e4e5a7d636`), 상위 `Datasets`
- 감사: 기대 5 / 보유 5, 누락 0

| 업로드 파일 | 원본 | 압축 크기 | SHA256 |
|---|---|---|---|
| `aihub_error_correction.zip` | 71560 오류 교정 | 46.6MB | `logs/aihub_backup.json` |
| `aihub_docsum_text.zip` | 097 문서요약 | 420.7MB | 〃 |
| `aihub_022_summary_report.zip` | 022 요약문·레포트 | 495.6MB | 〃 |
| `aihub_018_paper_summary.zip` | 018 논문자료 요약 | 1,755.7MB | 〃 |
| `AIHUB_BACKUP_MANIFEST.md` | 인벤토리·재획득 절차 | — | — |

- **제외**: 029 구매도서(17GB), 전문분야(14GB), 기타 소형 — 매니페스트에 경로·파일 수·바이트 기록.
- 재획득: AI Hub 로그인 후 동일 데이터셋 재다운로드(승인 유지). 매니페스트의 크기·구성과 대조.

