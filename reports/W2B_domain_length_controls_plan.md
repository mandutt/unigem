# Wave 2B V2 — domain/length control 계획 (D-074 사전등록)

- 작성: 2026-11-05 (KST)
- 목적: B3의 +10%p가 **Kspon domain** 때문인지 **short-length 분포** 때문인지 분리한다.
- 범위: **dev 500 전용**. sealed test 2,400은 사용하지 않는다. 새 gate가 아니다.
- 선행 결과: `reports/W2B_b0_matched_controls.md` — compute/exposure는 B3 이점을 설명하지 못했다.
- 설계: **natural sampler를 고정**해 B3-natural(기존 Kspon short)과 직접 비교한다.

## 1. 비교 구조

| Arm | Wave1 6h | 추가 4h | sampler | 역할 |
|---|---|---|---|---|
| B0′-12 | Zeroth/Kconf | 없음 | natural | baseline |
| **B3-nat** (기존) | Zeroth/Kconf | Kspon short 0.5–8s | natural | Kspon + short reference |
| **B3-long** (신규) | Zeroth/Kconf | **Kspon long 8–16s** | natural | **length control** |
| **B3-zeroth-short** (신규) | Zeroth/Kconf | **Zeroth short 0.5–8s** | natural | **domain control** |

- `B3-nat − B3-long`: 같은 Kspon domain, **길이만** 다름.
- `B3-nat − B3-zeroth-short`: 같은 short length, **도메인만** 다름.
- 두 신규 arm 모두 **10h, 12 epoch, seed 42, V2 vocab, same remapped init**.
- B3-nat는 기존 결과 `0.2633` (best epoch 11) / `0.2634` (final)을 참조한다.

## 2. 데이터

### 2.1 Kspon long 4h

- 원본: `D:/unigem/kspon_train/10.한국어음성/KsponSpeech_05.zip` (재다운로드 없음)
- transcript: `D:/unigem/w2b/train.trn`
- duration: **8.0–16.0초**
- target: **4.0h**
- V2 vocab 밖 문자 clip은 제외; OOV 비율 기록
- folder proxy cap: 1,440초/folder (short와 동일)
- 출력: `data/wave2b/long_4h.jsonl`, `data/wave2b/audio/long_4h/`

### 2.2 Zeroth short 4h

- 원본: `data/raw/zeroth/data/train-*.parquet` (기존 로컬)
- **Wave1에서 이미 쓴 Zeroth 1,534개를 건너뛴 뒤** 추가 4h를 선택한다.
- duration: 0.5–8.0초
- target bin: 0–2 25% / 2–4 35% / 4–6 20% / 6–8 20%
- V2 vocab 밖 문자 clip은 제외; OOV 비율 기록
- 출력: `data/wave2b/short_4h_zeroth.jsonl`, `data/wave2b/audio/short_4h_zeroth/`

## 3. Feature·cache

- 각 4h subset을 `w1_extract.py --arms fc --fc-memmap --threads 6 --min-dur 0.5`로 추출.
- `w2b_combine_feats.py`로 Wave1 6h + control 4h = **10h cache** 생성.
- V2 vocab 고정, `--retarget`.

## 4. 학습

- Reader: `arch=base`, 9,183,922 params
- Init: `data/wave2b/ckpt_v2/w2a_fc_concat_s42_v2head.pt`
- 12 epochs, patience 4, batch 2, grad accumulation 4, seed 42, CPU 6 threads
- sampler: **natural**
- dev: `data/wave2b/dev_500.jsonl` / `feats_dev`
- final 및 best dev CER를 모두 보고

## 5. 판정 규칙

이 실험은 **exploratory control**이며 gate가 아니다.

1. **H-length**: `B3-nat`가 `B3-long`보다 유의하게 좋으면 short-length 분포가 기여.
2. **H-domain**: `B3-nat`가 `B3-zeroth-short`보다 유의하게 좋으면 Kspon domain이 기여.
3. 둘 다 유의하지 않으면 domain/length 분리 실패로 기록하고, 추가 control을 논의.
4. `B0′` 대비 효과와 함께 보고한다.
5. **dev 500 paired utterance bootstrap 95% CI**를 붙인다.
6. **test 2,400 사용 금지.** 새 gate PASS/FAIL을 만들지 않는다.

## 6. DoD

- [ ] Kspon long 4h 선택 (OOV audit 포함)
- [ ] Zeroth short 4h 선택 (Wave1 1,534 제외, OOV audit 포함)
- [ ] 각 feature 4h + 10h cache
- [ ] `b3long_v2_s42` 12 epoch 완료
- [ ] `b3zeroth_v2_s42` 12 epoch 완료
- [ ] dev 500 prediction·bootstrap
- [ ] `reports/W2B_domain_length_controls.md`
- [ ] D-075 결과 기록
- [ ] test 2,400 미사용 확인

## 7. 예상 소요

- Kspon long 선택: 20–30분
- Zeroth short 선택: 30–60분
- feature/cache 2회: 20–30분
- 학습 2-arm: 4.0–4.4시간
- 분석·보고: 20–30분

**총 5~6.5시간**, CPU 6 threads, GPU/VPS 미사용, 비용 $0.

## 8. 산출물 경로

- `runner/w2b_select_kspon_long.py`
- `runner/w2b_select_zeroth_short.py`
- `runner/w2b_run_domain_controls.py`
- `runner/w2b_watch_domain_controls.py`
- `data/wave2b/long_4h.jsonl`
- `data/wave2b/short_4h_zeroth.jsonl`
- `data/wave2b/feats_10h_kspon_long/`
- `data/wave2b/feats_10h_zeroth_short/`
- `data/wave2b/ckpt_controls/`
- `data/wave2b/DOMAIN_CONTROLS_DONE.json`
