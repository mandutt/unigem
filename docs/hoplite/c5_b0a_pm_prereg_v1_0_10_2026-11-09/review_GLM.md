# C5 Phase 6 v1.0.10 — Option A Final Confirmation (GLM 5.3 Flash, reasoning max)

- 작성일: 2026-11-09
- 모델: `z-ai/glm-5.3-flash` (reasoning max), 동일 스레드(`thr_a757d209deae4493985cc2731c5af382`) 연속, 타 모델 답변 미재사용
- **검토 기준 HEAD SHA: `a88c714`** (full: `a88c71416764949d496e40b23255a242c8bb50f6`, "docs: add Phase 6 v1.0.10 Option A repair")
- 동기화: `git fetch origin` + `git pull --ff-only origin main` → HEAD `206117b` ("docs: add C5 P/M v1.0.10 same-thread final review"). `a88c714..206117b` diff는 리뷰 인프라 7개 파일뿐 — 검토 대상 5개 문서 바이트는 `a88c714`와 동일.
- **필수 verbatim 인용 (plan line 1758, 공백 포함 그대로, 부분일치 기계 확인 완료):**
  ```
  -> own eval loop                       # no evaluate_arm
  ```
- 범위 준수: v1.0.9에서 closed된 심볼(`c5_pm_stats.bootstrap_paired_v2`)/hash/custody 재검토 없음(v1.0.9→v1.0.10 diff 전수 확인 — 해당 조항 무변경). 학습/평가 실행 없음, test 163 미개봉, P1 미사용, 서브에이전트 없음. 실행은 fixture 재해시와 읽기 전용 grep/line 확인뿐.
- 상태: v1.0.10 Option A final confirmation. **Phase 6/B0-B/B1/B2/Stage C 실행 미승인. test 163 sealed. P1 미사용. T5Gemma2 D-108 STOP.**

---

## 0. 독립 검증 결과 (hash/읽기 전용)

| 항목 | 재계산 | 결과 |
|---|---|---|
| v1_0_10 golden 4 digests (state `43ecb58e…`, replay_base `c43ea35c…`, key_coverage `8277a713…`, control `6b50c226…`) | 재해시; v1_0_9와 `spec` 문자열만 다름(`C5 Phase 6 P/M v1.0.10`)을 diff로 확인 | **전부 일치** |
| preflight SHA `3ee3f1ca…69837af` | file bytes SHA256 | **일치**, template 선기입 일치 |
| plan line 수 | 1,769 | 요청서와 일치 |
| verbatim quote 공백 | python substring 비교 `'own eval loop                       # no evaluate_arm' in line` | **True** |
| v1.0.9→v1.0.10 diff | 전수 검토 | §13.5 1줄 추가, §17.3 call graph/금지/test 교체, 버전 표기 외 없음. §10.2/§16.2 hash·custody 무변경 |

v1.0.9 계승 확인: §16.1 "No code before freeze." 무변경; §17.3 "no pre-freeze helper edit is required for this path" 신설 — v1.0.9 ERRATA-1/MTF-1 lifecycle 충돌의 원인(pre-freeze 교체 의무)이 제거됨. template `note`도 "Phase 6 owns eval; evaluate_arm is not used."로 갱신.

---

## 1. Q1–Q5

### Q1. Lifecycle 일관성

- 판정: **agree (§16.1 충돌은 해소) — 단, 해소된 구조 위에 Q3의 신규 불일치가 있음**
- 근거: Option A는 pre-freeze helper edit를 요구하지 않는다(§17.3 "no pre-freeze helper edit is required for this path"). 구현(`c5_pm_phase6.py`, `c5_pm_stats.py` 생성)은 freeze 이후 승인 단계이므로 §16.1 "No code before freeze."와 문자적·취지 모두 정합. v1.0.9 MF-1의 프로세스 모순은 실제로 제거됨. helper 4종은 freeze commit에서 `helper_commits`로 고정되어 이후 무편집 — §16.2 정합.
- 다음 단계: (1) Q3의 ERRATA를 final plan commit에 포함하여 이 구조를 완성.

### Q2. evaluate_arm 배제

- 판정: **conditional — 규정·test 존재하나 검사 범위가 이번 라운드부터 실질화됨**
- 근거: 규정은 이중으로 명확 — §17.3 "it must not import or call `runner.c5_mt5_lora_b0.evaluate_arm`" + §13.5 신설 "Phase 6 path does not import `evaluate_arm`" + §17.3 test "neither `evaluate_arm` nor legacy `bootstrap_paired(` appears in the Phase 6 path". 그러나 **helper `train_arm` 소스가 `evaluate_arm(`를 포함**하기 때문에(v1.0.10 요구의 전제 아래 후술 Q3), "Phase 6 path"가 entrypoint 소스 한정인지 import-도달 전이 소스인지에 따라 test가 유의 검사가 되거나 허위 통과가 된다. 전이 소스 해석이 옳으며(그래야 MF-2 목적 달성), 이를 문언화해야 함.
- 다음 단계: (1) §13.5/§17.3 test를 "entrypoint에서 import-도달 가능한 전이 소스 소스+콜그래프"로 명문화(ERRATA-B), (2) `c5_mt5_lora_b0.evaluate_arm` 심볼 미import 단언 추가.

### Q3. train_arm training-only 재사용

- 판정: **disagree (as-written 불가능) — text-only ERRATA 필요. 본 라운드의 유일한 실질 항목.**
- 근거: 현재 helper `runner/c5_mt5_lora_b0.py` (HEAD에서 직접 확인):
  1. `train_arm`(line 665)은 훈련 루프 **뒤에 무조건** `evaluation = evaluate_arm(...)`(line 723)과 `generation = generate_arm(...)`(line 724)를 실행한다. `evaluate_arm`은 내부에서 legacy `bootstrap_paired`(line 460, seed 20261108)를 호출한다(220 p0 경로와 별개). 즉 entrypoint가 `train_arm`을 호출하는 순간, 소스 import가 아니더라도 **런타임 호출 그래프가 evaluate_arm→legacy bootstrap에 도달**한다 — Option A가 닫으려던 MF-2 도달성이 "training only" 표기를 문자대로 실행하면 재개된다.
  2. §17.3의 자체 test("neither `evaluate_arm` nor legacy `bootstrap_paired(` appears in the Phase 6 path")를 전이 소스로 읽으면 `train_arm` 소스가 `evaluate_arm(`를 포함하므로 재사용이 즉시 위반; entrypoint-소스 한정으로 읽으면 test는 유의미하지 않게 되고 런타임 도달은 잔존 — **어느 해석에서도 "train_arm may be reused for training"과 배제 규정이 동시에 참일 수 없다.** 이는 v1.0.8 DS MF-1(심볼 충돌)과 동일 등급의 문서 내부 불일치다.
  3. `train_arm`은 arm 어휘가 `{"lora","frozen"}`뿐(line 690 `raise ValueError(arm)`; `set_training_mode`도 335)이라 **P/PA 훈련이 불가능**하다 — P/PA는 어차피 신규 코드가 필요하고, 균일한 "재사용"은 처음부터 성립하지 않는다.
  4. 참고로 §17.1 권위 표는 `Adapter`/`make_labels`/`load_layer_cache`/`LoRALinear`/`attach_decoder_lora_mt5`/`native_memory`/`repeated_4gram_rate` 7종이며 `train_arm`/`evaluate_arm`은 **애초에 권위 helper가 아니다.** 훈련 계약은 §2.2(hyperparams)+§2.5.2(loss)+§2.7(RNG 순서)로 문서 내 완전 지정되어 있다.
- 결론: 유일하게 자기일관적인 Option A 완성은 **훈련 루프도 `c5_pm_phase6.py` 소유**(§17.1 pinned primitives + §2.2/§2.7 계약)로 읽는 것이고, call graph의 `-> c5_mt5_lora_b0.train_arm # training only`와 "`train_arm` may be reused for training"은 그렇지 않은 지시이므로 수정 대상. 과학적 내용 변경 없음.
- 다음 단계: (1) ERRATA-A(아래 Must-fix 1위)를 final plan commit에 포함, (2) 구현 시 훈련 루프를 c5_pm_phase6.py에 §2.7 RNG 순서 그대로 구현, (3) P/PA 훈련 경로를 별도 구현하는 점을 DoD에 반영.

### Q4. Residual

- 판정: **conditional — 과학적 결함 0, text 항목 3 (ranked)**
- 근거:
  1. **(medium/text, freeze-blocking)** §17.3 call graph + "`train_arm` may be reused" ↔ 배제 규정/test 불일치 — Q3. ERRATA-A로 봉합.
  2. **(medium/text)** §13.5/§17.3 test의 "Phase 6 path" 범위 미문언화 — Q2. helper가 `evaluate_arm`을 포함하는 이상 전이 소스 명문화가 필요(ERRATA-B).
  3. **(cosmetic)** helper `train_arm`이 P/PA를 훈련할 수 없음(arm 어휘 frozen/lora)을 문서가 암시조차 하지 않음 — call graph 수정 시 자연 해소.
- 긍정적 확인: Option A 도입으로 §16.1 lifecycle 모순 해소, template note 갱신, §13.5 배제 라인 추가, golden/preflight 불변 재현, 3 thread ID 동일 유지.

### Q5. Final

- 판정: **NARROW (text-only; ERRATA-A/B를 final plan commit에 포함 후 재확인)**
- 근거: v1.0.9의 프로세스 모순은 실제로 닫혔으나, 그 닫는 수단(Option A)의 문서 표현이 자체 배제 규정과 충돌한다 — "train_arm 재사용"을 문자대로 실행하면 MF-2가 재개되고 plan 자신의 §13.5/§17.3 test를 전이 해석에서 위반한다. 이는 이전 라운드에서 material로 처리된 등급(DS v1.0.8 MF-1, Sol v1.0.9 MF-1)이며, 합성 규칙(3/3 CONTINUE 전까지 동결 보류)상 동결은 보류된다. 수정은 한 줄 ERRATA이고 과학적 내용·golden·코호트·임계값 불변이므로 STOP 사유는 없다.

---

## 2. Must-fix (ranked)

1. **ERRATA-A (freeze-blocking, text)** §17.3 수정: call graph의 `-> c5_mt5_lora_b0.train_arm            # training only` 행과 "`train_arm` may be reused for training; evaluation is owned by `c5_pm_phase6.py`."를 삭제·교체 — 권장 문구: "`c5_pm_phase6.py` implements its own training loop per §2.2/§2.5.2/§2.7 using the §17.1 pinned primitives; helper `train_arm` and `evaluate_arm` are not called by Phase 6 (helper `train_arm` internally invokes `evaluate_arm`, line-level fact at freeze commit)." call graph는 `own train loop (§2.2/§2.7)` / `own eval loop` / `c5_pm_stats.bootstrap_paired_v2`로 표기.
2. **ERRATA-B (text)** §13.5+§17.3 test 범위 문언화: "Phase 6 path" = `runner/c5_pm_phase6.py`에서 import-도달 가능한 전이 소스의 소스+콜그래프. helper 소스 내 `evaluate_arm(` 존재가 곧 위반 판정 근거가 됨을 명시.
3. **(cosmetic)** P/PA는 helper `train_arm`으로 훈련 불가(arm 어휘 frozen/lora) — P/PA 훈련 경로가 신규 구현임을 §17.3에 한 줄 명시.

과학적 must-fix 없음. threshold/seed/donor/step/LR 변경 제안 없음.

## 3. 최종 판정 블록

```text
최종 판정: NARROW (text-only — ERRATA-A/B를 final plan commit에 포함하고 동일 스레드에서 재확인)
v1.0.10 freeze: 보류 (ERRATA-A/B 반영 시 승인 가능; 현재 §17.3 call graph가 자체 배제 규정과 충돌)
구현+unit tests: 보류 (freeze 이후; §13 매트릭스 + §17.1 pinned primitives 기반 own train/eval 구현 + 전이 소스 단언 + paired-L>F/NA + golden 5종)
D0: 보류 (freeze 승인 후; 0 update, ≤4 config, ≤15 min, seed 20261111, labels_computed:false, freeze_manifest_sha256+manifest_commit+txt SHA256 기록)
D1: 미승인 (별도 승인 필요)
3-seed: 미승인 (D1 이후 별도 등록 실행)
금지 범위: D1/3-seed/B0-B/B1/B2/Stage C 자동 진행, test 163 개봉, P1 사용, T5Gemma2(D-108 STOP), 결과 후 threshold/seed/donor/step/LR 변경, Phase 6 path에서 evaluate_arm·legacy bootstrap_paired 사용, pre-freeze helper 편집, freeze 이후 helper 재편집(ERRATA 제외)
최대 compute: freeze 승인분 = ERRATA 커밋(문서) + 구현+unit tests(CPU, 학습 없음) + D0(0 update, ≤15 min). 등록 Phase 6는 12 units/1,200 updates/120 min wall/6 threads/no GPU/no retry, T_proj ≤96 min, 120-min hard abort; 155 min은 D0 15+D1 20+등록 120 총 envelope로 단일 cap 아님 — 별도 승인 전까지 미실행
Must-fix (ranked): ERRATA-A train_arm 재사용 조항/행 교체(own train loop) / ERRATA-B test 전이 소스 범위 문언화 / P·PA 신규 훈련 경로 명시
v1.0.10 self-contained: 예 — 단, §17.3의 train_arm 재사용 표현은 실행 불가 지시이므로 ERRATA-A 없이는 구현자가 문서만 따라가면 배제 규정 위반에 도달
잘못된 전제: "train_arm을 training-only로 재사용할 수 있다" — helper 사실(line 723 evaluate_arm 호출, line 460 legacy bootstrap, line 690 frozen/lora 전용)와 상충. 이 전제만 교정하면 Option A는 자기완결적
```