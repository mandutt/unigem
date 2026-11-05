# Wave 2A-lite 준비 기록 (2026-11-04)

- 상태: 준비 완료, 4-arm 학습 전.
- 승인: D-064. 실행 정본 `docs/STT/plans/plan_wave2a_lite.md`.
- Hoplite 3-AI 검토: `docs/STT/hoplite/v4/2026-11-04_hoplite-review_v4_SYNTHESIS.md`

## 1. FLEURS ko dev

| 항목 | 값 |
|---|---:|
| 원천 | `google/fleurs` `ko_kr` validation parquet |
| 전체 행 | 226 |
| 고유 발화 ID | **226** (`path` basename 사용) |
| 고유 문장 ID | 129 (같은 문장을 여러 화자가 낭독) |
| 전체 길이 | 0.7722 h |
| ≤16초 (추출 대상) | **192** |
| >16초 (제외) | 34 |
| 최소/최대 | 3.72 s / 29.76 s |
| 샘플레이트 | 16 kHz mono |

- `data/wave2a_lite/fleurs_dev.jsonl` — 226행. 추출기는 0.5~16초만 사용하므로 **192클립(0.65h)**이 특징으로 변환됐다.
- **함정:** FLEURS parquet의 `id`는 발화 ID가 아니라 **문장 ID**다(226행 중 129개만 고유). 발화 고유 키는 `path` basename이다. 초기 빌드에서 `id`를 파일명으로 썼다가 97개가 덮어써졌고, `path` 기반으로 수정했다.
- 34개 장문은 16초 초과로 제외했다. 이는 dev가 완전 무작위가 아니라는 한계다. 결과 보고서에 명시한다.
- FLEURS test 382와 dev 발화 ID가 겹치지 않음(0/226)을 `path` basename으로 확인했다.

## 2. Vocab

| 항목 | 값 |
|---|---:|
| train 고유 한글 | 1,064 |
| 상한 | 2,350 (실제 1,064 모두 포함) |
| 숫자/라틴/공백 추가 | 26 + 1 |
| **vocab chars** | **1,101** |
| blank 포함 | 1,102 |
| dev coverage | **99.42%** (60/10,419 missing) |
| missing types | 27 (희귀 한글) |

- `data/wave2a_lite/vocab.json`, `vocab_coverage.json`
- 2,350은 상한이며, 6h 코퍼스에는 1,064자만 있어 확장 여지가 없다.
- 남은 0.58%는 train에 없는 희귀 한글이다. dev/test 문자를 vocab에 넣지 않는다.

## 3. 파라미터 실측 (vocab 1,102)

| Arm | 입력 | params |
|---|---:|---:|
| F-A′ | 1,536 | 8,113,102 |
| F-B | 1,024 | 7,916,494 |
| F-C-softmax | 4×1,024 → 1,024 | 7,924,690 |
| F-C-concat | 4,096 | 9,096,142 |

- `FCSoftmaxReader`: 4개 LayerNorm + softmax weight 4개 + `CTCReader(1024)`. softmax 초기값은 균등 0.25.
- `train/d5_reader.py --arch softmax`로 학습·디코드 경로 확인. smoke test 통과.
- F-C-concat은 기존 `CTCReader(4096)` comparator.

## 4. FLEURS dev 특징

| Arm | 파일 | 크기 |
|---|---|---:|
| F-A′ | `data/wave2a_lite/feats_dev/fa.npz` | 150.2 MB |
| F-B | `data/wave2a_lite/feats_dev/fb.npz` | 101.7 MB |
| F-C | `data/wave2a_lite/feats_dev/fc.npz` | 403.5 MB |

- 192클립, 52,451 프레임, 7,812 참조 문자.
- `train/w1_extract.py` 실행 로그: `logs/W2A_lite_extract_dev.log`.

## 5. 1시간 positive-control subset

- `data/wave2a_lite/feats_1h/{fa,fb,fc}.npz`
- 396클립 / **1.0007h**, Wave 1 manifest 순서.
- **★대상 라벨 재인코딩 필요:** Wave 1 `feats/*.npz`의 `targets`는 구 vocab(1,069자)로 만들어져 새 vocab(1,101자)와 ID가 다르다. `train/d5_reader.py --retarget`으로 `texts`를 새 vocab으로 다시 인코딩해야 한다. 이 플래그 없이 학습하면 라벨이 뒤섞여 CER가 1.0에 붙는다(실측).
- **Positive-control 이력(실패 보존):**

| 실행 | 조건 | 결과 | 판정 |
|---|---|---|---|
| `pc_fa` | 20 epoch, retarget 없음 | epoch 8 CER 0.978, 조기 종료 | **무효(라벨 불일치)** |
| `pc_fa80` | 80 epoch, retarget 없음 | epoch 3 CER 0.976에서 중단 | **무효(라벨 불일치)** |
| `pc_fa80r` | 80 epoch, retarget, 공백 포함 | epoch 3 CER 0.741, 공백 제거 일관성 위해 중단 | **참고(중단)** |
| `pc_fa80n` | 80 epoch, retarget, 공백 제외 | epoch 5 CER 0.2087에서 중단(로그아웃) | 참고(중단) |
| **`pc_fa20n`** | **20 epoch, retarget, 공백 제외** | **epoch 7 CER 0.1161** | **PASS(positive control)** |

- `--retarget`은 `texts`를 새 vocab으로 인코딩하며 **공백은 제외**한다(평가의 `normalize_nospace`와 일치, D-β와 동일).
- Positive control은 train=dev 1h subset에서 **epoch 7 CER 0.1161**까지 내려가 overfit 가능성을 확인했다. 20 epoch 중 epoch 7에서 중단했으며 best checkpoint `pc_fa20n.best.pt`를 보존한다.
- F-C flat npz는 4.1GB라 `fc.feats.npy`를 한 번 추출해 memmap으로 subset을 만들었다.

## 6. Kspon eval_other (봉인 test)

| 항목 | 값 |
|---|---:|
| 원천 | AI Hub KsponSpeech eval_other (`filekey 50216`), scripts `50217` |
| 전체 발화 | 3,000 |
| 전체 길이 | **3.8027 h** |
| ≤16초 (평가 대상) | 2,963 |
| >16초 (제외) | 32 |
| <0.5초 (제외) | 5 |
| 빈 전사 | 0 |
| 상태 | **sealed** — 학습·dev·arm 선택에 미사용 |

- `data/wave2a_lite/kspon_eval_other.jsonl` — 3,000행, `sealed=true`, `test_role=primary_gate`.
- 전사 정리(사전등록): `[A-Za-z]{1,2}/` 잡음 마커 제거, `(A)/(B)`는 첫 대안, `+`·잔여 괄호 제거. `ref_raw` 보존.
- PCM은 1바이트 홀수 패딩을 잘라 16 kHz mono WAV로 변환했다.
- 특징 추출은 **체크포인트 동결 후**에만 한다. 지금은 manifest/audio만 준비했다.
- eval_clean 100은 D 평가에서 은퇴한다.

## 7. 아직 필요한 것

1. ~~Kspon eval_other 확보·봉인 manifest~~ — 완료.
2. 4-arm 학습(seed 42) + best arm seed 43/44.
3. dev decode·CER·pairwise bootstrap·per-domain·error taxonomy·blank.
4. vocab oracle·fbank baseline.
5. 체크포인트 동결 후 Kspon eval_other 1회, FLEURS test 1회.
6. `docs/STT/reports/W2A_lite_results.md`.

## 7.1 실행 현황 (2026-11-04)

- 로컬: F-A′ `fa_s42` epoch 7 CER **0.2380**, F-B `fb_s42` epoch 7 CER **0.2283** — 학습 계속.
- VPS eg2-1: F-C full feature를 **`--fc-memmap`**으로 재추출 성공(4.2GB `fc.feats.npy` + 329KB metadata). 8GB 호스트에서 기존 방식은 저장 단계 OOM이었음.
- VPS eg2-1: F-C-softmax `fc_softmax_s42` 학습 중, epoch 4 CER **0.2537**. 완료 후 같은 머신에서 F-C-concat을 순차 실행.
- `runner/w2a_monitor.py`가 5분 간격으로 로컬 FA/FB와 VPS F-C의 checkpoint/로그를 확인하고 완료 시 알림.
- eg2-2~eg2-5: 유휴·auto-suspend. best arm seed 반복/fbank에 배정 예정.
- Kspon eval_other와 FLEURS test는 아직 특징 추출·평가하지 않음(봉인 유지).

## 8. 무결성

`reports/provenance/W2A_lite/prep.json`에 파일 크기·sha256을 기록했다.
