# 데이터셋·모델 확보 기록

- 작성: 2026-11-02
- 목적: 용량이 큰 자산을 삭제해도 **재획득 경로·해시**로 복원할 수 있게 한다.

## 1. Zeroth-Korean (C2 음성)

| 항목 | 값 |
|---|---|
| 출처 | OpenSLR 40 — https://www.openslr.org/resources/40/zeroth_korean.tar.gz |
| 라이선스 | **CC BY 4.0** |
| 규모 | 51.6h train + 1.2h test(457발화), 약 9.6GB |
| 로컬 경로 | `data/raw/zeroth/zeroth_korean.tar.gz`(다운로드 중), `data/raw/zeroth/zeroth_test.parquet` |
| SHA256 | test parquet `10c10f7f36d85c27c89b5fe2b7b560a04f5c1fd453f8005e95a397be86b4d97e` (59,817,445 B) / tar은 완료 후 기록 |
| 용도 | Notesoop/komixv2 CER 기준선(C2-A1) |

재획득:
```bash
curl -L -C - -o zeroth_korean.tar.gz https://www.openslr.org/resources/40/zeroth_korean.tar.gz
```

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

