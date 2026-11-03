# D0-d — 비용 probe (완료)

- 작성: 2026-11-03
- 대상: Addendum D §D0-d
- 상태: **완료 — 특징 추출 RTF + reader 1-step/epoch 비용 실측**
- 호스트: 로컬(Ryzen 5 7600, 6 threads), eg2-1(4 vCPU, 4 threads)

## 1. 오디오 Q8 특징 추출 RTF

입력: 고정 random mel `[1,1600,128]`, mask all-true (16초 상당). 그래프만 측정(전처리 제외).

| 호스트 | threads | 16초 1회 | RTF | 6시간 추출(그래프만) |
|---|---|---|---|---|
| 로컬 | 6 | 0.468s | **0.0292** | 약 10.5분 |
| eg2-1 | 4 | 0.364s | **0.0227** | 약 8.2분 |

- VPS가 로컬보다 1.29배 빠르다(같은 Q8 그래프, 4 threads).
- 전처리(mel)와 I/O를 포함하면 RTF는 더 높아진다. C-8의 Notesoop 전체 RTF 0.093은 디코더·LM 포함 값이므로 직접 비교하지 않는다.
- 6시간 파일럿의 특징 추출은 **그래프만 8~11분**, 전처리 포함 20~30분 수준으로 추정된다.

## 2. reader 비용 probe

`train/d5_reader.py` 구현: 입력 투영(1024→384) → 4층 Transformer(6 head, FF 1536, GELU, pre-norm) → CTC head. blank=0, 프레임률 25Hz.

- 학습 파라미터 **8,647,224 (8.65M)** — D-5.5 상한 10M 이내.
- 합성 특징 `[B=8, T=400, 1024]`, 라벨 길이 40~100, vocab 3,000. warmup 5 + 측정 20 step.
- **수렴 품질이 아니라 비용 측정**이다(랜덤 특징/라벨).

| 호스트 | threads | sec/step | 6h 1 epoch | 20 epoch |
|---|---|---|---|---|
| 로컬 | 6 | **1.452s** | **4.09분** (169 step) | 약 82분 |
| eg2-1 | 4 | **1.180s** | **3.32분** (169 step) | 약 66분 |
| — | — | peak RSS | 로컬 1,452MB | eg2-1 1,655MB |

- 6시간 = 1,350개 16초 창, batch 8 → 169 step/epoch.
- 20 epoch 기준 로컬 82분, VPS 66분. **호스트당 48시간 한도에 충분히 들어온다.**
- 피크 RSS 1.5~1.7GB — VPS 7.9GB에서 여유.

## 3. 판정

**D0-d 완료.** 추출 RTF와 reader epoch 비용 모두 측정했고, 6시간 파일럿은 호스트당 48시간 한도 안에 들어온다. D-β Wave 1의 비용 전제가 확보됐다.

## 4. 산출물

- `train/d5_reader.py`
- `logs/D5_reader_probe.json`
- `reports/provenance/D5_reader_probe.json`
- `logs/D0d_extract_rtf.json`
- `reports/provenance/D0d_extract_rtf.json`

## 5. AM-6 이행 표

| 요구 (D0-d) | 이행 |
|---|---|
| 추출 RTF (VPS/로컬) | 이행 |
| reader 1 epoch 시간 | 이행(합성 비용 probe) |
| 피크 RAM | 이행 |
| 48시간 한도 판정 | 이행 — 충분 |
| 실제 데이터 수렴 | **미이행** — D-β Wave 1에서 측정 |
