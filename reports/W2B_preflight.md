# W2B Preflight — eval_clean split·duration·OOV·CTC

- 입력: `data/raw/kspon_eval/10.한국어음성/KsponSpeech_eval.zip`, `extracted/eval_clean.trn`
- **오디오 추출·다운로드·학습 없음.** zip metadata와 전사만 읽었다.

## 1. eval_clean 기본

- PCM: 3000, TRN: 3000, 교집합: **3000**
- 16초 초과 제외: **10** → 평가 적격 **2990**
- 기존 D-β dev 100: 100; eval_clean에 없는 ID: 0
- duration: min 0.286s / mean 3.126s / max 15.738s

| duration | all | dev 500 | test 2,400 | spare 90 |
|---|---:|---:|---:|---:|
| 0-2 | 1440 | 246 | 1151 | 43 |
| 2-4 | 783 | 126 | 633 | 24 |
| 4-8 | 537 | 90 | 431 | 16 |
| 8-12 | 187 | 32 | 149 | 6 |
| 12-16 | 43 | 6 | 36 | 1 |
| 16-999 | 0 | 0 | 0 | 0 |

## 2. split

- dev: **500** (기존 100 + 신규 400)
- test: **2400**
- spare: **90** (평가에 쓰지 않음)
- dev/test 교집합: **0**
- dev∩used: 100 / test∩used: **0**

## 3. OOV·CTC

- OOV rows: **226/2990 (7.56%)**, OOV types 106, chars 261
- OOV by split: dev **38/500 (7.6%)**, test **185/2400 (7.71%)**, spare **3/90 (3.33%)**
- top OOV: `[('밌', 26), ('낫', 14), ('컬', 8), ('껄', 7), ('쫌', 7), ('걍', 6), ('쎄', 6), ('탔', 6), ('쉴', 5), ('맘', 5), ('놈', 5), ('캡', 5), ('쉐', 4), ('썸', 4), ('숏', 4)]`
- chars > frames: **0**
- chars+repeats > frames: **0**

## 4. 화자·데이터 가용성

- eval_clean.trn과 zip 파일명에는 **화자 ID가 없다**. 따라서 dev/test는 **duration 층화**로만 나눴다.
- Kspon train shard는 로컬에 없다. AI Hub filekey 50211~50215(각 14~15GB) 중 하나를 streaming으로 받아 short 4h를 선별해야 한다.
- 현재 C: 여유는 약 18GB다. zip 전체 해제 없이 `zipfile` streaming + 선택 파일만 저장하는 전제로 진행해야 한다.

## 5. Blocker

- eval_clean **3,000**은 확인됐고, 16초 초과 10건을 제외한 **2,990**에서 dev 500/test 2,400/spare 90 split 후보를 만들었다.
- `test`는 아직 **봉인 평가 전**이며, checkpoint freeze 전에는 어떤 모델도 평가하지 않는다.
- Kspon train shard·화자 메타데이터·short 4h 선별은 아직 수행하지 않았다.
