# C5 B0-A Correctness Repair Plan v0.1

- 작성일: 2026-11-09
- 상태: **계획 승인 대기. 코드 수정 전.**
- 대상: `runner/c5_mt5_lora_b0.py` 및 B0-A 진단 경로
- 근거: 3-AI NARROW 3/3 + confirmed CE alignment defect
- test 163: **sealed**
- P1 데이터: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- B0-B / B1 / B2 / Stage C: **미승인**

---

## 1. Scope

### 1.1 포함

1. **Primary metric CE 정렬 수정**
   - `token_losses()`의 `logits[:, :-1]` vs `labels[:, 1:]`를 same-position `logits` vs `labels`로 수정
   - `shifted_copy_mask()`와 `copy_ce()`의 mask 정렬도 함께 수정
   - 기존 B0-A JSON은 **수정하지 않음**. as-run historical result로 보존
   - alignment 회귀 테스트 추가

2. **F/L 학습 모드·dropout 대칭**
   - F와 L 모두 base decoder를 eval 모드로 고정
   - adapter와 LoRA branch만 train 모드
   - `model.training`, LoRA module mode, trainable parameter identity를 assert
   - step-0 eval-mode zero-LoRA equality 재확인

3. **Generation telemetry**
   - raw token IDs
   - `gen_len`, `eos`, `cap_hit`
   - repeated-4gram rate
   - special/pad/EOS counts
   - surface empty와 semantic empty를 분리
   - fixed decoding config 기록

4. **Copyable mask audit**
   - 현재 mask의 coverage 분포와 sample precision 보고
   - 공백 제거·1음절 substring 규칙의 과대 계수 확인
   - 새 mask는 **사전등록 후** 적용. 결과를 보고 즉석에서 threshold를 바꾸지 않음
   - as-run mask는 secondary로 보존

5. **No-training P0 native sanity**
   - native mT5 encoder memory + frozen decoder
   - source memory vs shuffled source memory
   - aligned `Δcopy` / `Δfull`만 계산, 학습 0
   - 이 단계는 metric sensitivity 확인이며 B0-B가 아님

6. **Bounded P/M diagnostic**
   - P: native mT5 encoder + decoder LoRA
   - M: training-only mean memory
   - 20 train / 20 val, original seeds 20261108/09/10
   - final checkpoint only
   - 새 사전등록 후 실행

### 1.2 제외

- B0-B 300/95 4-arm
- B1 layer sweep
- B2 decoder 비교
- Stage C
- test 163 사용
- P1 데이터
- T5Gemma2 재개
- 제품 `eval/slot_verify.py` 수정
- B0-A 결과를 본 뒤 threshold·seed·donor·step 변경
- 동일 B0-A config 재실행
- A1 native fallback의 제품 승격

---

## 2. Public API / Interface

### 2.1 유지

기존 CLI:

```text
--mode smoke
--mode metric-smoke
--mode train
--arm frozen|lora|both
```

기존 output field는 삭제하지 않는다. 새 field만 추가한다.

### 2.2 추가

```text
--mode p0-sanity
```

- 학습 없이 native P0만 수행
- output: `reports/provenance/C5_b0a/p0_native_sanity.json`
- exit code:
  - 0: 계산 완료
  - 2: shape/finite/schema 실패
  - 3: 입력 누락

### 2.3 Output schema

기존 필드 유지 + 추가:

```json
{
  "metric_alignment": {
    "same_position_ce": 0.0,
    "builtin_loss": 0.0,
    "delta": 0.0
  },
  "train_mode_policy": {
    "base_decoder_training": false,
    "adapter_training": true,
    "lora_training": true
  },
  "generation": {
    "token_ids": [],
    "gen_len": 0,
    "eos": false,
    "cap_hit": true,
    "rep4": 0.0
  }
}
```

P/M output은 별도 `reports/provenance/C5_b0a/p_m_diagnostic.json`에 기록한다.

---

## 3. DoD

### D1. Metric alignment

- same-position CE mean == `out.loss` (atol 1e-5) on 3 documents
- first token, EOS, ignored label, copy-mask position test
- `Δshuffled_copy`가 same-position loss로 계산됨
- old B0-A aggregate와 report는 **변경되지 않음**
- `python -m unittest discover -s eval/tests -q` 전체 통과

### D2. F/L mode parity

- 두 arm 모두 `model.training is False`
- adapter trainable, LoRA branch trainable
- base decoder parameters `requires_grad=False`
- step-0 eval zero-LoRA loss/logits delta ≈ 0
- training mode assertions가 결과 JSON에 기록됨

### D3. Generation telemetry

- 20 val 문서 각각 raw token IDs 저장
- `cap_hit`, `eos`, `rep4`, `gen_len`, special count 기록
- `nonempty`와 `usable`를 분리
- generation 결과가 gate가 아님을 report에 명시

### D4. Mask audit

- coverage distribution(mean/median/p05/p95)
- sample 100 token precision audit
- upper-coverage warning 추가
- 새 mask rule은 별도 사전등록 문서에 고정

### D5. P0

- native P0가 20/20에서 실행됨
- aligned Δcopy/full, CI, donor count 기록
- **P0 실패 시 B0-B/B1/B2/C 금지**
- P0 결과는 B0-A의 재평가가 아니라 metric sensitivity 진단

### D6. P/M

- P/M 정의, donor, K, seed, checkpoint가 사전등록에 고정됨
- P와 M 결과가 F/L과 별도로 보고됨
- P가 양수 selectivity를 만들지 못하면 **metric/assay 재설계 또는 STOP 상향**
- P/M 결과만으로 B0-B 자동 승인 없음

---

## 4. Implementation order

| 단계 | 작업 | 산출물 | 승인 |
|---:|---|---|---|
| G0 | 이 계획 승인 | 이 문서 | **필요** |
| 1 | alignment test + fix | test, runner patch | G0 후 |
| 2 | mode parity + assert | test, runner patch | G0 후 |
| 3 | generation telemetry | runner patch | G0 후 |
| 4 | mask audit | audit report | G0 후 |
| 5 | P0 native sanity | `p0_native_sanity.json` | **결과 후 보고** |
| 6 | P/M bounded diagnostic | `p_m_diagnostic.json` | **별도 사전등록 승인** |
| 7 | B0-B prereg | `docs/plan_c5_b0b_prereg_v0_1.md` | **별도 승인, 실행 금지** |

### 4.1 Commit policy

- 단계 1~4는 각각 별도 commit
- 각 commit에 test 결과와 변경 파일 기록
- 단계 5 이전에 `git diff --check` + 47 tests + new tests
- 단계 5 결과는 commit하되 B0-B를 시작하지 않음

---

## 5. Resource cap

| 항목 | 상한 |
|---|---:|
| test-only 단계 1~4 | ≤ 30 CPU-min |
| P0 20/20 × 5 donors, no training | ≤ 15 CPU-min |
| P/M bounded diagnostic | ≤ 2 CPU-hours, ≤ 1,200 optimizer updates |
| GPU | 사용 안 함 |
| test 163 | 사용 안 함 |

P/M cap은 Sol 검토의 권고를 따른다. 초과 시 자동 연장하지 않고 중단·보고한다.

---

## 6. Risks and controls

| Risk | Control |
|---|---|
| B0-A 수치를 소급 수정하는 오해 | historical JSON/report 불변, addendum만 추가 |
| alignment fix가 결과를 유리하게 바꾸는 선택으로 보임 | 수정 전 test로 실패 재현, 수정 후 built-in loss와 일치 확인 |
| F/L mode 변경이 treatment를 바꿈 | 새 diagnostic으로만 실행, B0-A와 비교 금지 |
| mask 재정의가 post-hoc tuning | train-only rule, 새 사전등록, as-run mask secondary |
| P0/P 실패를 bridge STOP으로 오해 | P0/P 실패는 assay 실패로 기록, bridge STOP은 별도 결정 |
| generation metric이 품질 gate로 오용 | telemetry only, B0-B gate 아님 |
| test/P1 재사용 | runner에 `test_split_used=false` assert 유지 |

---

## 7. Stop conditions

즉시 중단·보고:

- alignment test가 built-in loss와 맞지 않음
- F/L mode parity가 assert를 통과하지 못함
- P0에서 non-finite 또는 shape mismatch
- donor/K/mask provenance 누락
- P0/P 결과가 metric insensitivity를 보임
- CPU cap 초과
- test 163 또는 P1 접근 발생

중단 시 B0-B/B1/B2/C를 자동 진행하지 않는다.

---

## 8. Approval question

> **이 Scope·DoD·순서·cap으로 단계 1~4(코드 수리 및 테스트)를 진행해도 되는가?**

승인 후에도 단계 5(P0)와 단계 6(P/M)은 각각 결과 보고 후 진행한다.
