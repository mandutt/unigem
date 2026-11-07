# C5 B1d adapter-only teacher-fidelity pilot (v0.1)

## 1. 목적

B1d/B2 계열의 실패가 **bridge(adapter)가 teacher behavior를 운반하지 못한 것**인지,
**frozen decoder가 그 hidden을 사용하지 못한 것**인지 분리한다.

- Teacher: A1 native T5Gemma2 pilot300
  - val161: char F1 **0.657580**, grounded **161/161**, EOS **161/161**
  - train100 (이번 생성): char F1 **0.669685**, grounded **99/100**, EOS **100/100**
- Student: EG2 → adapter(768→640) → **frozen** T5Gemma2 decoder
- Trainable: **adapter only** (decoder LoRA 없음)

## 2. 왜 adapter-only teacher output인가

기존 실험:

| target | decoder | 결과 |
|---|---|---|
| teacher hidden (B1d) | frozen | hidden cosine 0.727, 생성 붕괴 |
| gold CE (B1d-CE) | frozen | F1 0.206, grounded 5% |
| gold CE (B2) | LoRA | F1 0.335, grounded 18% |

**teacher output sequence KD는 아직 하지 않았다.** hidden cosine이 높아도 behavior가
무너질 수 있으므로, teacher가 생성한 문장을 teacher-forced CE로 직접 맞춘다.

Exa 근거:
- projector/adapter는 coarse alignment만 하며 10~20% 데이터로 대부분 회복
  (`Rethinking Projector Training in Multimodal LLMs`, 2026 preprint)
- sequence KD는 capacity gap이 있어 큰 teacher가 항상 좋지 않음
  (`Don't Throw Away Data`, 2024)
- frozen decoder에서는 projector-attention deadlock이 발생할 수 있어
  hidden auxiliary가 필요 (`Audio-Native ... Frozen Discrete-Diffusion LM`, 2026 preprint)

## 3. 데이터

- train: clean split 1,293 중 teacher output이 있는 100건
  - teacher output `verify_summary`에서 new slot이 있으면 제외
- val: clean split 161 중 100건
- test 163: **로드하지 않음**
- teacher hidden/student hidden: 기존 B1d cache 사용

## 4. 손실

```text
L = CE(teacher output)
  + 0.05 * (1 - cosine(adapter_hidden, teacher_hidden))
```

- decoder frozen
- adapter init: B1d-CE adapter
- AdamW lr 3e-4, 2 epoch, batch 1

## 5. 평가

Primary (teacher-forced):
- teacher CE
- teacher token accuracy
- hidden cosine

Secondary:
- free-running val 20
- teacher char F1
- gold char F1
- EOS rate
- grounded rate

## 6. 해석 규칙

- teacher-forced token accuracy가 의미 있게 상승하고 free-running도 개선
  → bridge가 behavior를 운반; B2 teacher KD 또는 full로 확장
- teacher-forced는 상승하나 free-running이 붕괴
  → decoder/exposure bias/stop token 문제; B2 attention-only 필요
- teacher-forced 자체가 상승하지 않음
  → adapter capacity 또는 frozen decoder deadlock; B2/attention-only 필요

## 7. 비용

- teacher train100 생성: 약 5분 (완료)
- adapter-only 2 epoch: 약 10~20분
- teacher-forced eval 200건: 약 10분
- free-running 20건: 약 5분
- 총 약 30~40분 (CPU)

## 8. 산출물

- `runner/c5_b1d_teacher_fidelity.py`
- `data/models/f5_t5gemma2_lora/b1d_teacher100/adapter_final.pt`
- `reports/provenance/C5_b1d/teacher_train100.jsonl`
- `reports/provenance/C5_b1d/b1d_teacher100_metrics.json`
- `reports/C5_B1D_TEACHER_FIDELITY_2026-11-07.md`
