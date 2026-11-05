# W2B Preflight Addendum — 0.5초·중복·디스크·해시

- 작성: 2026-11-04
- 목적: v2 preflight 이후 3-AI 검토에서 지적된 항목을 **원자료로 재확인**
- 입력: `data/raw/kspon_eval/10.한국어음성/KsponSpeech_eval.zip`, `extracted/eval_clean.trn`, `data/wave2b/preflight/split_candidate.json`, `data/wave1/manifest.jsonl`, `data/wave2a_lite/kspon_eval_other.jsonl`
- **오디오 추출·학습·test 평가 없음.**

## 1. 0.5초 미만 클립

`w1_extract.py`는 0.5초 미만을 제외한다. 현재 split 후보에는 다음이 포함되어 있다.

| 세트 | 0.5초 미만 | 최소 duration |
|---|---:|---:|
| dev 500 | 2 | 0.347s |
| **test 2,400** | **28** | **0.286s** |
| spare 90 | 0 | 0.589s |

- 그대로 추출하면 test는 **2,372**가 된다.
- v3 정책: **평가 추출만 최소 0.28초**로 낮추고, 실제 feature frame에서 CTC 적격성을 재검사한다. CTC 불가 건은 오류로 계산한다.
- **실측(2026-11-04)**: `w1_extract.py --min-dur 0.0`로 28건을 별도 probe 추출 → **kept 28/28, elapsed 2.6s**, CTC skip 0. 따라서 2,400을 유지할 수 있다.
- `preflight.json`의 CTC 0건은 **TRN/metadata 기반**이었으므로 실제 feature frame 검사로 대체한다.

## 2. test 길이 대표성

| 세트 | ≤4초 | 0–2초 | 12–16초 |
|---|---:|---:|---:|
| test 2,400(eval_clean) | **74.33%** | 47.96% | 36 |
| eval_other 2,962 | 57.2% | 27.6% | 3.9% |

- eval_clean test는 eval_other보다 **훨씬 짧은 발화 중심**이다.
- Kspon eval_other CER 0.35143을 test 기준선으로 직접 이전하지 않는다.
- test 12–16초 bin(n=36)은 탐색적으로만 보고한다.

## 3. ID 중복

| 비교 | 교집합 |
|---|---:|
| test ∩ eval_other | **0** |
| test ∩ Wave 1 train(2,384) | **0** |
| test ∩ 기존 D-β 100 | **0** |
| test ∩ short 4h | **미생성** |
| test ∩ B3-nat | **미생성** |

- short/B3-nat 선별 후 ID 중복을 다시 검사한다.
- eval_clean에 화자 ID가 없으므로 **화자 중복 0은 주장하지 않는다.**
- **ID 블록 감사 결과: filename shuffle로 화자/세션 대응이 확인되지 않아 블록 split을 적용하지 않는다.** 현재 duration 층화 split을 유지한다. 상세 `docs/STT/reports/W2B_split_audit.md`.

## 4. 디스크·feature

- 2026-11-04 현재 `df -h /c`: **79GB 여유** (기존 “18GB” 표기는 낡음).
- `preflight.json`의 `disk_free_gb`는 **null** — provenance 미기록.
- 특징 크기:
  - `data/wave1/feats`: **11GB** (`fc.npz` 3.9GB)
  - `data/wave2a_lite/feats_dev`: 630MB
  - `data/wave2a_lite/feats_kspon_eval_other`: 2.6GB
- 로컬은 이전보다 여유가 있지만, VPS eg2-2 20GB에서 15GB zip + 10h feature + test feature를 동시에 두는 것은 불가능하다.
- VPS는 **audio 선별만**, feature는 로컬에서 만드는 분리를 우선한다.

## 5. sha256 — Git blob vs 작업 트리

| 대상 | sha256 |
|---|---|
| 작업 트리(CRLF) | `25eb37f6314072aa9a113b8d6f822ebedb8d6b3a638c42b52de8b7954d680deb` |
| **Git blob** (`5170404`~) | **`6805a8de071067502e421c0da96257eaea6ee7b5f2ec6607f51360b885b515f0`** |

- 요청서의 `25eb...`는 작업 트리 CRLF 해시다.
- 데이터 내용(seed 42, dev 500/test 2,400/spare 90)은 동일하다.
- v3 정본은 **Git blob 해시**를 쓴다.

## 6. 6h train 출처

- `data/wave1/manifest.jsonl`: 2,384클립
- **Zeroth 1,534 + Kconf 850**
- **Kspon 0** — short 4h가 최초의 Kspon 도메인 데이터다.
- 따라서 `B3−B3-nat`을 “Kspon natural length distribution” 실험으로 부르지 않는다.

## 7. 결론

- v3는 test 2,400을 유지하되 **0.5초 28건 처리 규칙**을 추가한다.
- short/B3-nat 선별 후 ID 중복·OOV율을 재측정한다.
- split은 **ID 블록 감사 후** 확정한다.
- 디스크는 로컬 79GB 기준으로 계획하되, VPS는 audio 선별 전용으로 제한한다.
