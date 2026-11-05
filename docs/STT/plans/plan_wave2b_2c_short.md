# Wave 2B + 2C-short 설계안 (v1 — 검토 이력)

- **v2가 현행 설계다: `docs/STT/plans/plan_wave2b_2c_short_v2.md`.** 이 문서는 3-AI 검토 전 v1으로만 보존한다.

- 작성: 2026-11-04
- 상태: **설계 검토용. 사용자 승인 전 코드·데이터 다운로드·학습 실행 금지.**
- 선행 결과: `docs/STT/reports/W2A_lite_results.md`, `docs/STT/reports/W2A_lite_cp_d2_lite.md`
- 목적: CP-D2-lite에서 확인된 **짧은 발화 분포 불일치**를 고치면서, EG2 상위 conformer 층 적응(2B)과 short-clip 데이터(2C-short)의 효과를 분리 측정한다.

---

## 0. 한눈에 보는 결론

- 2A-lite의 best arm은 **F-C-concat seed42 0.20913**(FLEURS dev), Kspon eval_other **0.35143**.
- Kspon 오류의 주축은 **길이 분포 불일치**다.
  - train ≤4초 **4.1%** vs Kspon eval_other ≤4초 **57.2%**
  - Kspon CER: 0–2초 **46.4%** → 12–16초 **28.6%**
  - 잡음 마커는 주원인 아님(noisy 34.7% vs clean 35.4%)
- 따라서 **2B 상위층 LoRA만으로는 부족**할 가능성이 높다.
- 제안: **2B-pilot(B0/B1/B2/B3)** → 효과 확인 후 full 2B.
  - B0: 동결 F-C-concat baseline
  - B1: 상위 2층 LoRA, 기존 6h
  - B2: 상위 2층 LoRA, 기존 6h + short 4h
  - B3: 동결 타워, 기존 6h + short 4h (data-only control)
- 최종 test는 **Kspon eval_clean의 미사용 2,900발화**를 새 봉인 test로 쓴다. 이미 D-β에서 쓴 100발화는 dev로만 쓰고 test에서 제외한다.

---

## 1. Scope

### 포함

1. **2C-short 데이터 4.0h 확보·선별**
   - KsponSpeech **train** (AI Hub datasetkey 123)에서 4.0h 선별
   - 0–2초 25%, 2–4초 35%, 4–6초 20%, 6–8초 20%
   - P0 공개 데이터만 사용
2. **2B-pilot 4-arm**
   - B0: 기존 F-C-concat seed42 (동결 타워, 6h) — 재학습 없음
   - B1: EG2 audio tower **10–11층 LoRA**, 기존 6h
   - B2: EG2 audio tower **10–11층 LoRA**, 기존 6h + short 4h
   - B3: EG2 audio tower **동결**, 기존 6h + short 4h (reader-only, data-only control)
3. **dev 평가**
   - Kspon eval_clean **100발화** (기존 D-β 사용분; dev 전용)
   - FLEURS ko dev 192발화 (보조 일반화)
   - 길이 bin별 CER 필수
4. **최종 test 1회**
   - Kspon eval_clean **2,900발화** (100발화 제외; 새 봉인 test)
   - 동결 checkpoint 1개만 평가
5. **재현성**
   - 데이터 manifest·sha256·선별 규칙
   - LoRA target·rank·alpha·trainable params
   - checkpoint에 optimizer/scheduler/epoch/RNG 포함(`--resume`)
   - dev/test overlap 0 검증

### 제외

- wordpiece head / Gemma text embedding 초기화 (후속 2C/2D)
- 13-state softmax mix (2A-lite에서 concat이 우세)
- EG2 text tower, F1 언어판정, F4/F5/F6
- 40h/100h 전체 확장
- Q4/QAT, LoRA 이외의 adapter 종류
- VPS 장기 학습 (host steal 재발; 긴 작업은 로컬)
- FLEURS test 재사용 (2A-lite에서 이미 1회 사용)

---

## 2. 현재 근거와 가정

### 2.1 2A-lite 결과

| Arm | FLEURS dev CER | 비고 |
|---|---:|---|
| F-A′ | 0.22236 | baseline |
| F-B | 0.21931 | |
| F-C-softmax | 0.22211 | |
| **F-C-concat** | **0.20913** | best; seed43 0.208116 |
| fbank | 0.9812 | 실패(진단 필요) |

### 2.2 CP-D2-lite 결과

| 항목 | 값 |
|---|---:|
| Kspon eval_other CER | 0.35143 |
| 0–2초 CER | 0.4644 |
| 2–4초 CER | 0.3778 |
| 12–16초 CER | 0.2862 |
| train ≤4초 비중 | 4.1% |
| Kspon eval_other ≤4초 비중 | 57.2% |
| noisy vs clean CER | 34.7% vs 35.4% |
| 상위 1% 발화 오류 비중 | 4.2% |

### 2.3 가정

- EG2 audio tower의 10–11층 LoRA가 Kspon 도메인 적응에 가장 비용 효율적이다(하위층은 범용 acoustic feature 유지).
- F-C-concat 입력을 유지하면 2A-lite와 직접 비교할 수 있다.
- Kspon eval_clean 100은 dev, 나머지 2,900은 test로 분리하면 test 재사용 편향을 피할 수 있다.
- CPU 15.6GB에서 batch 2 + gradient accumulation 4 + LoRA만 학습하면 10h 데이터 1 epoch를 감당할 수 있다. **이는 가정이며 pilot에서 실측한다.**

---

## 3. 데이터 설계

### 3.1 2C-short: Kspon train 4h

- 원천: AI Hub KsponSpeech **train** (datasetkey 123, filekey 50211~50215 중 선별)
- 라이선스/등급: P0 공개; AI Hub 약관 준수
- 오디오: 16kHz mono PCM(headerless), 홀수 바이트 1바이트 절단 후 wav 변환
- 전사: Kspon train 전사 파일을 사용하고, eval_other와 동일한 정리 규칙 적용
  - `[A-Za-z]{1,2}/` 잡음 마커 제거
  - `(A)/(B)` 첫 대안
  - `+`·잔여 괄호 제거
  - `ref_raw` 보존
- 선별 목표:

| duration | 목표 비중 | 목표 시간(4h 기준) |
|---|---:|---:|
| 0–2초 | 25% | 1.0h |
| 2–4초 | 35% | 1.4h |
| 4–6초 | 20% | 0.8h |
| 6–8초 | 20% | 0.8h |

- 선별 규칙:
  - 빈 전사·1자 이하 제외
  - 0.5초 미만 제외
  - 화자 단위로 train/2C-short에만 사용; eval 발화와 ID·화자 중복 0
  - 같은 화자가 과도하게 몰리지 않도록 화자당 상한(예: 4h의 10%)을 둔다.
- 산출물:
  - `data/wave2b/short/manifest.jsonl`
  - `data/wave2b/short/audio/*.wav`
  - `data/wave2b/short/summary.json`
  - `reports/provenance/W2B/short_data.json`

### 3.2 train mix

- 기존: `data/wave1/manifest.jsonl` 6.0008h / 2,384클립
- 추가: short 4.0h
- 총 **10.0h**
- natural 분포는 ≤4초 24% 정도이므로, **LengthBalancedSampler**로 epoch당 effective 분포를 다음으로 맞춘다.

| effective duration | 목표 |
|---|---:|
| ≤4초 | 40% |
| 4–8초 | 30% |
| 8–16초 | 30% |

- 같은 short 클립을 단순 복제하지 않는다. sampler weight만 올리고, unique data는 4h를 유지한다.
- 2B-pilot에서 short를 **2h만** 쓰는 옵션도 두되, 기본은 4h.

### 3.3 dev

| 세트 | 용도 | 크기 |
|---|---|---:|
| Kspon eval_clean 100 | primary dev, early stop | 100발화 |
| FLEURS ko dev | secondary generalization | 192클립 |

- Kspon eval_clean 100은 D-β에서 이미 사용된 dev다. **test가 아니므로 2B dev로 재사용 가능**하다.
- dev 길이 bin: 0–2, 2–4, 4–8, 8–12, 12–16초.

### 3.4 최종 test (새 봉인)

- Kspon eval_clean **3,000 − 100 = 2,900발화**
- `data/c2a1/manifest.json`의 `source=kspon_eval_clean` 100개 ID를 제외
- 나머지 2,900개 ID만 `data/wave2b/test/kspon_eval_clean_2900.jsonl`로 봉인
- 검증:
  - 2,900 고유 ID
  - dev 100과 교집합 0
  - 2A-lite eval_other와 교집합 0
  - 학습·2C-short와 교집합 0
- **FLEURS test는 2A-lite에서 이미 사용했으므로 2B에서 재사용하지 않는다.**
- 최종 test는 checkpoint freeze 후 1회만 평가한다.

---

## 4. 모델 설계

### 4.1 입력·reader

- F-C-concat 유지: `aud_h_l06/08/10/11` 각각 LayerNorm → concat 4096 → `CTCReader(4096)`
- reader는 기존 `train/d5_reader.py`의 `CTCReader`를 재사용한다.
- vocab: `data/wave2a_lite/vocab.json` 1,101자 고정(2A-lite와 동일)
- CTC loss, `normalize_nospace` 평가

### 4.2 LoRA 대상

- 대상 층: **10, 11층만**
- 대상 모듈(실제 state dict 기준):
  - `self_attn.q_proj.linear`
  - `self_attn.k_proj.linear`
  - `self_attn.v_proj.linear`
  - `self_attn.post.linear`
  - `feed_forward1.ffw_layer_1.linear`
  - `feed_forward1.ffw_layer_2.linear`
  - `feed_forward2.ffw_layer_1.linear`
  - `feed_forward2.ffw_layer_2.linear`
- `lconv1d`, norm, `relative_k_proj`, embedding, output_proj는 **동결**
- LoRA:
  - rank **8**, alpha **16**, dropout 0.0
  - `B`를 0으로 초기화 → 학습 시작 시 identity
  - base weight는 freeze; A/B만 optimizer에 포함
- 0–9층, embedding, `embed_audio` 동결.

### 4.3 학습 그래프

```
wav → Gemma4AudioFeatureExtractor (mel, 16kHz)
    → Gemma4AudioModel (layers 0–9 frozen, 10–11 LoRA)
    → hooks: l06/l08/l10/l11
    → per-frame LayerNorm → concat 4096
    → CTCReader(4096)
    → CTC loss
```

- `tower.eval()`로 고정 층 dropout 비활성; LoRA/reader만 train.
- variable-length batch: mel을 batch 내 max length로 pad; `input_features_mask` 전달.
- short clip도 16초 상한; 0.5초 미만 제외.
- `torch.utils.checkpoint`는 pilot에서 메모리 부족 시에만 10–11층에 적용.

### 4.4 학습 hyperparameter (초안)

| 항목 | 값 |
|---|---:|
| batch size | 2 (16s), short-only batch는 4 |
| grad accumulation | 4 |
| epochs | pilot 3 / full 12 |
| early stop | patience 3 on Kspon dev 100 |
| LoRA LR | 1e-4 |
| reader LR | 1e-3 |
| weight decay | 0.01 |
| scheduler | cosine, warmup 10% |
| grad clip | 5.0 |
| seed | 42 |
| threads | 6 |
| AMP | 없음 (CPU) |

- **B1/B2**: LoRA + reader 학습.
- **B3**: tower 완전 동결; short feature를 `w1_extract.py --arms fc`로 미리 추출하고 `d5_reader.py`로 reader만 학습.
- **B0**: 기존 frozen F-C-concat seed42.

---

## 5. Public API

새 파일은 `train/` 아래에 두고, 기존 `d5_reader.py`는 수정하지 않는다(회귀 방지).

### 5.1 `train/w2b_lora.py`

```python
class LoRALinear(nn.Module):
    def __init__(self, base: nn.Linear, rank: int = 8, alpha: float = 16.0): ...
    def forward(self, x: torch.Tensor) -> torch.Tensor: ...

def attach_lora(
    tower: nn.Module,
    layers: tuple[int, ...] = (10, 11),
    targets: tuple[str, ...] = (...),
    rank: int = 8,
    alpha: float = 16.0,
) -> list[str]:
    """Wrap target Linear modules; return wrapped parameter names."""

def lora_parameters(tower: nn.Module) -> list[nn.Parameter]: ...
```

### 5.2 `train/w2b_data.py`

```python
def select_kspon_short(
    archive: Path,
    out_dir: Path,
    target_hours: float = 4.0,
    bins: dict[tuple[float, float], float] = ...,
    seed: int = 42,
) -> dict:
    """Stream archive, select P0 train clips by duration; write manifest/audio."""

def build_eval_clean_2900(
    raw_eval_dir: Path,
    exclude_ids: set[str],
    out_manifest: Path,
) -> dict:
    """Build the new sealed eval_clean 2,900 manifest; verify exclusions."""

def length_balanced_sampler(
    manifest: list[dict],
    effective_probs: dict[str, float],
    seed: int = 42,
) -> torch.utils.data.WeightedRandomSampler: ...
```

### 5.3 `train/w2b_train.py`

```bash
python train/w2b_train.py \
  --arm b2 \
  --train-manifest data/wave2b/train_mix.jsonl \
  --dev-manifest data/wave2b/dev/kspon_eval_clean_100.jsonl \
  --fleurs-dev data/wave2a_lite/fleurs_dev.jsonl \
  --vocab data/wave2a_lite/vocab.json \
  --lora-layers 10,11 --rank 8 --alpha 16 \
  --epochs 3 --batch-size 2 --grad-accum 4 \
  --lr-lora 1e-4 --lr-reader 1e-3 \
  --seed 42 --threads 6 \
  --ckpt-dir data/wave2b/ckpt --resume
```

- `--arm {b1,b2}`: end-to-end LoRA.
- `--frozen-tower` + `--features`: B3 reader-only 경로(또는 기존 `d5_reader.py` 사용).
- checkpoint: model, LoRA, reader, optimizer, scheduler, epoch, best, RNG, args.
- `--resume`로 host/세션 중단 시 이어서 학습.

### 5.4 `train/w2b_eval.py`

```bash
python train/w2b_eval.py \
  --ckpt data/wave2b/frozen/b2.best.pt \
  --manifest data/wave2b/test/kspon_eval_clean_2900.jsonl \
  --out docs/STT/reports/W2B_test.json \
  --bins 0,2,4,8,12,16
```

- 출력: corpus CER, sentence bootstrap CI, 길이 bin별 CER, blank, taxonomy, coverage.
- test는 freeze 후 1회만.

---

## 6. DoD

### 6.1 데이터 DoD

- [ ] 2C-short 4.0h, duration bin 목표 ±5%p
- [ ] Kspon train 전사 정리 규칙 적용, `ref_raw` 보존
- [ ] train/dev/test ID 교집합 0
- [ ] eval_clean 100 dev와 2,900 test 분리
- [ ] sha256·행 수·시간·화자 수 provenance
- [ ] **FLEURS test 미사용**

### 6.2 모델 DoD

- [ ] LoRA target 8개×2층, trainable params 보고
- [ ] base weight `requires_grad=False`, LoRA A/B만 학습
- [ ] B0/B1/B2/B3 동일 vocab·reader·seed·eval
- [ ] B2는 B1과 데이터만 다름(단일 변수)
- [ ] B3는 B2와 adaptation만 다름(단일 변수)
- [ ] checkpoint `--resume` round-trip

### 6.3 평가 DoD

- [ ] dev: Kspon eval_clean 100 + FLEURS dev 192, 길이 bin별 CER
- [ ] test: Kspon eval_clean 2,900 1회, bin별 CER
- [ ] paired bootstrap 95% CI (문장 단위)
- [ ] error taxonomy·blank·vocab coverage
- [ ] test 결과는 gate와 benchmark comparison 분리 표기

### 6.4 판정 DoD

- [ ] pilot Go/No-Go
- [ ] full Go/No-Go
- [ ] No-Go 시 CP-D2 원인 진단(구현/데이터/타워)
- [ ] 2B 자동 착수 금지, CP 경계 승인

---

## 7. Test plan

### 7.1 Unit tests

| 테스트 | 기대 |
|---|---|
| `test_lora_identity` | 초기 LoRA 출력 == base 출력 |
| `test_lora_trainable` | trainable params = LoRA A/B만 |
| `test_lora_targets` | 10/11층 8개 target만 wrap |
| `test_sampler_bins` | epoch당 duration 분포 목표 ±5%p |
| `test_no_test_overlap` | train/dev/test ID 교집합 0 |
| `test_eval_bins_sum` | bin별 n 합 == 전체 n |
| `test_resume_roundtrip` | optimizer/epoch/RNG 복원 |
| `test_frozen_forward` | 동결 파라미터 변화 0 |

### 7.2 Pilot

- B1 100 step, B2 100 step
- 측정: sec/step, peak RSS, loss, NaN, LoRA grad norm
- 중단 조건:
  - peak RSS > 13GB
  - step > 5s (예상의 3배)
  - loss NaN/발산
- B3 1 epoch (reader-only) — short feature 추출 포함
- pilot 결과로 batch/rank/checkpointing 조정; **결과를 본 뒤 gate threshold는 변경하지 않음**

### 7.3 Full run

- B1, B2, B3 각각 seed42, 12 epoch(early stop)
- B0 재학습 없음(기존 checkpoint)
- dev 평가는 epoch마다; test는 freeze 후 1회

---

## 8. 판정 기준 (사전등록 초안)

### Pilot Go

- B2 Kspon dev 100 CER가 B0 대비 **상대 5% 이상** 개선
- B2 ≤4초 bin CER가 B0 대비 **상대 8% 이상** 개선
- paired bootstrap 95% CI 하한 > 0 (가능한 경우; n=100)
- 위 조건 미충족 → full run 중단, CP-D2

### Full Go

- B2 Kspon dev 100 CER가 B0 대비 **상대 10% 이상** 개선
- B2 ≤4초 bin CER가 B0 대비 **상대 10% 이상** 개선
- CI 하한 > 0
- B2 > B1 (short data 이득) AND B2 > B3 (adaptation 이득) — 둘 중 하나라도 역전이면 원인 분석
- 최종 test 2,900에서 **상대 10% 이상** 개선, CI 하한 > 0
- 위 미충족 → No-Go/CP-D2

### 해석 규칙

- B2가 B1보다 좋지 않으면 **short data 효과 없음**.
- B2가 B3보다 좋지 않으면 **LoRA adaptation 효과 없음**.
- B3가 B0보다 좋으면 **데이터만으로 개선**; 2B 불필요.
- 전체 CER만 보지 말고 **≤4초 bin**을 반드시 본다.

---

## 9. 구현 순서

| 단계 | 작업 | 산출물 | 예상 |
|---:|---|---|---:|
| 0 | Preflight: 디스크·AI Hub·전사·ID overlap 확인 | `docs/STT/reports/W2B_preflight.md` | 0.5일 |
| 1 | Kspon train 1 shard에서 short 4h 선별 | `data/wave2b/short/*` | 0.5~1일 |
| 2 | eval_clean 2,900 test manifest 구축·봉인 | `data/wave2b/test/*` | 0.5일 |
| 3 | dev 100·FLEURS dev manifest 정리 | `data/wave2b/dev/*` | 0.5일 |
| 4 | LoRA·Dataset·Sampler 구현 + unit tests | `train/w2b_lora.py`, `w2b_data.py` | 1일 |
| 5 | B3 short feature 추출 + reader-only 학습 | `data/wave2b/feats_short`, ckpt | 0.5일 |
| 6 | B1/B2 100-step pilot, RSS/step 측정 | `logs/W2B/pilot.json` | 0.5일 |
| 7 | B1/B2 full 12 epoch | checkpoints | 3~5일 |
| 8 | dev bin 평가·B2 vs B0/B1/B3 | `docs/STT/reports/W2B_dev.md` | 1일 |
| 9 | freeze → test 2,900 1회 | `docs/STT/reports/W2B_test.md` | 0.5일 |
| 10 | D-066·최종 보고 | `docs/decisions.md` | 0.5일 |

**총 예상: 7~10일** (pilot 결과에 따라 3~5일로 단축 가능)

---

## 10. 예산·자원

- 로컬 CPU만 사용: Ryzen 5 7600 6C/12T, 15.6GiB, GPU 없음
- 디스크: 현재 C: 여유 약 **19GB**. Kspon train zip 14~15GB + short 0.5GB + test 0.3GB → **여유 25GB 이상 확보 후 시작**.
  - 부족 시 `cache/wave1.tar.gz`(502MB), 오래된 scratch, 중복 cache 정리 후 진행. 사용자 데이터 삭제 금지.
- VPS: 사용하지 않음. 짧은 데이터 전처리만 필요하면 P0에 한해 검토하되, 긴 학습은 로컬.
- 외부 LLM API: 사용하지 않음.

---

## 11. 리스크와 대응

| 리스크 | 영향 | 대응 |
|---|---|---|
| 디스크 19GB 부족 | 데이터 다운로드 실패 | preflight에서 25GB 확보; zip streaming; 선택 후 zip 삭제 |
| Kspon train 전사 형식 미확인 | 선별 불가 | 0단계에서 zip 내부 `.pcm`/`.txt`/`.trn` 확인; 없으면 scripts/전사 파일 확보 |
| CPU 학습 Too slow | full run 지연 | 100-step pilot; batch 2, grad accum 4; 필요 시 short 2h로 축소 |
| LoRA target 모듈이 custom Linear | wrap 실패 | `safetensors` key와 module type 확인; `.linear`만 wrap; unit test |
| test 재사용 편향 | 결과 신뢰도 하락 | eval_clean 2,900 새 봉인; 100 dev/test 분리; FLEURS test 미사용 |
| B2가 B1/B3보다 나쁨 | 가설 기각 | CP-D2로 원인 분석; gate threshold 변경 금지 |
| 4h short가 부족 | short bin 개선 미미 | 2h→4h→6h 단계 확장; 2B-pilot에서 먼저 확인 |
| 화자/도메인 누출 | test 오염 | ID·화자 교집합 0; eval_clean 100 제외; provenance |

---

## 12. 승인 요청 사항

아래 4개를 승인해 주시면 0단계(preflight)부터 시작하겠습니다. **승인 전에는 코드·데이터 다운로드·학습을 실행하지 않습니다.**

1. **2C-short 4h**: Kspon train에서 0–2초 25%, 2–4초 35%, 4–6초 20%, 6–8초 20%로 선별.
2. **2B-pilot 4-arm**: B0/B1/B2/B3, LoRA 10–11층 rank8 alpha16, 기존 F-C-concat reader.
3. **새 test**: Kspon eval_clean 2,900(100 dev 제외)을 2B 봉인 test로 사용. FLEURS test 재사용 금지.
4. **Gate**: pilot 상대 5%/short bin 8%, full 상대 10%/short bin 10%, CI 하한>0. 결과 후 threshold 변경 금지.

### 검토가 필요한 대안

- **A. 4h short + 10h train** (권장): 균형과 비용의 절충.
- **B. 2h short + 8h train**: 빠르지만 short bin 개선이 작을 수 있음.
- **C. 6h short + 12h train**: 데이터 효과는 크지만 CPU 시간·디스크 부담.

권장은 **A**입니다.

---

## 13. 재현·산출물 계약

- `data/wave2b/short/manifest.jsonl`
- `data/wave2b/train_mix.jsonl`
- `data/wave2b/dev/kspon_eval_clean_100.jsonl`
- `data/wave2b/test/kspon_eval_clean_2900.jsonl`
- `data/wave2b/ckpt/{b1,b2}.best.pt`, `data/wave2b/feats_short/fc.npz`
- `logs/W2B/{pilot,b1,b2,b3}.log`
- `docs/STT/reports/W2B_dev.md`, `docs/STT/reports/W2B_test.md`
- `reports/provenance/W2B/{short_data,test_seal,pilot}.json`
- `docs/decisions.md` D-066

---

## 14. 하지 말아야 할 것

- Kspon eval_other 재사용 (2A-lite에서 이미 사용)
- FLEURS test 재사용 (2A-lite에서 이미 사용)
- test 결과를 보고 LoRA 층·LR·threshold 변경
- B1/B2/B3를 서로 다른 vocab·reader·seed로 비교
- VPS에서 장기 학습 (steal 재발)
- short 클립을 같은 4개로 단순 복제 (과적합)
