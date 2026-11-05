# W2B Split Audit — eval_clean ID 블록

- 작성: 2026-11-04
- 목적: v3 결정 4번 — **연속 ID 블록이 화자/세션과 대응하는가**
- 입력: `KsponSpeech_eval.zip` eval_clean PCM metadata, `eval_clean.trn`, KsponSpeech 원논문
- **오디오 추출·학습·test 평가 없음.**

## 1. 확인된 사실

KsponSpeech 원논문(Applied Sciences 10(19):6936)과 AI Hub 설명:

- eval_clean: **3,000발화 / 60명 화자(남 30·여 30)**
- 평가 데이터는 화자당 100발화를 뽑은 뒤, 발화별 perplexity 순위로 **대략 50개씩** eval_clean/eval_other로 분할
- **개인정보 보호를 위해 filename을 변경·shuffle했다** — 즉 파일번호가 화자 순서와 대응하지 않는다.

로컬 확인:

- `eval_clean.trn`과 zip 파일명에는 **speaker ID가 없다.**
- ID는 `KsponSpeech_E00001`~`E03000`로 연속이지만, 이는 **파일 정렬용 번호**이지 화자 그룹 번호가 아니다.
- 50-ID 블록의 duration 평균은 3.77s / 3.34s / 3.07s로 달랐지만, 이는 화자 대응의 증거가 아니다.

## 2. 판정

**블록 split을 적용하지 않는다.**

이유:

1. filename shuffle로 화자 정보가 제거되어 **연속 ID = 화자/세션**이라는 가정이 성립하지 않는다.
2. 근거 없이 블록을 나누면 길이 분포만 왜곡되고, 화자 누출을 줄인다는 보장도 없다.
3. 따라서 v3의 조건부 결정 중 **“대응이 확인되지 않으면 현 split 유지”**에 해당한다.

## 3. 확정 split

| 세트 | 크기 | 방식 |
|---|---:|---|
| dev | **500** | duration 층화, 기존 D-β 100 포함 |
| test | **2,400** | duration 층화, 봉인 |
| spare | **90** | 평가 미사용 |

- 16초 초과 10건 제외 후 적격 2,990.
- dev∩test = 0, test∩기존 D-β 100 = 0.
- test∩eval_other = 0, test∩Wave 1 train = 0 (preflight addendum).
- **화자 독립 test가 아니다.**
- bootstrap은 **utterance-level paired bootstrap**만 사용한다.
- test는 **“Kspon in-domain sealed holdout(절차적)”**으로 표기한다.

## 4. 한계

- eval_clean과 eval_other는 같은 60명 화자 풀을 공유한다.
- short 4h(Kspon train)와 eval_clean 화자의 중복 여부는 **확인 불가**하다.
- 화자 단위 일반화 주장은 하지 않는다.
- 가능하면 후속 라운드에서 별도 P0 화자-disjoint holdout을 확보한다.
