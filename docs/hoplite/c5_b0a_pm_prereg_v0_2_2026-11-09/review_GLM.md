# C5 B0-A Phase 6 P/M Prereg v0.2 — 독립 외부 검토보고서

- 검토자: **GLM 5.3 Flash (reasoning effort: max)** — v0.2 라운드의 독립 외부 검토자. 본 라운드는 v0.1 라운드(3/3 NARROW)와 별개의 **신규 독립 라운드**이며, 다른 모델의 답변을 재사용하지 않았다.
- 검토일: 2026-11-09
- 검토 기준 HEAD: `918cfa5bc9129016b91d506bb412a1938f119bcf` (`docs: add C5 P/M prereg v0.2 review request`)
  - 동기화: `git fetch origin` 성공, `git pull --ff-only origin main` → **"Already up to date"**, HEAD == origin/main == `918cfa5`.
  - 요청서 기재 작성 기준 `8c4f197`은 HEAD의 직전 커밋이고, `918cfa5`는 그 위에 본 검토요청서를 추가한 커밋이다. 두 커밋 모두 v0.2 계획(`docs/plan_c5_b0a_pm_prereg_v0_2.md`) 이후이므로 검토 기준으로 문제없다.
- 대상: `docs/plan_c5_b0a_pm_prereg_v0_2.md` (405줄)
- 제약 준수: 학습·평가 미실행. test 163 미개봉(sealed 유지). P1 미사용. 외부 API 미사용. 저장소 수정 없음(이 보고서 파일 1개만 작성). subagent·추가 LLM 미호출(직접 검토). T5Gemma2 D-108 STOP 유지. Phase 6/B0-B/B1/B2/Stage C 미승인. 결과 전 단계이므로 threshold·seed·donor·step 변경 제안 없음(필요 시 새 사전등록으로만).

---

## 0. 검증 기반

### 0.1 직접 판독한 문서·코드

| 대상 | 방법 |
|---|---|
| `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_2026-11-09.md` | 전문(352줄) 직접 판독 |
| `docs/plan_c5_b0a_pm_prereg_v0_2.md` | 전문(405줄) 직접 판독 |
| `docs/plan_c5_b0a_pm_prereg_v0_1.md` | 전문(314줄) 직접 판독 |
| `reports/C5_B0A_PM_PREREG_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 전문(211줄) — "v0.1 Must-fix가 무엇이었는지"의 사실 확인 목적 |
| `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md` | 전문(116줄) |
| `reports/C5_B0A_REPAIR_2026-11-09.md` | 전문(178줄) |
| `runner/c5_mt5_lora_b0.py` | 전부(802줄) 판독 |
| `eval/tests/test_c5_b0_metric.py` | 전부(128줄) 판독 |

독립성: v0.1 라운드의 개별 리뷰 원문(`docs/hoplite/c5_b0a_pm_prereg_2026-11-09/review_*.md`)은 읽지 않았다. 3-AI 종합은 요청서가 지정한 artifact로서 Must-fix 사실 확인에만 사용했고, 아래 모든 판정은 내가 직접 읽은 v0.2 계획·러너 코드·테스트·P0 보고서에서 도출했다.

### 0.2 코드 상태 사실 (구현 전 확인)

- `runner/c5_mt5_lora_b0.py`의 `main()`은 `--mode {smoke, metric-smoke, train, p0-sanity}`만 지원한다. **`pm-diagnostic` 미구현.**
- `set_training_mode()`은 `{"frozen", "lora"}`만 허용한다. P(adapter 없음)/PA arm 불가 — P arm은 adapter를 아예 두지 않으므로 이 함수의 "adapter not train → RuntimeError" 단정과 충돌한다.
- `bootstrap_paired()`는 `"seeds_positive": int((arr > 0).sum())`로 **문서 수**를 집계한다. v0.1에서 지적된 mislabel이 코드에 그대로 남아 있다.
- `evaluate_arm()`(및 `p0_eval_split()`)의 real CE는 donor-crop(`k = min(len_real, len_donor)`) 기반이다. v0.2가 M의 real reference로 채택한 **full real K와 다른 프로토콜**이다(분리가 필요한 이유).
- 재사용 가능한 원시물: `native_source_ids()`, `native_memory()`, `p0_eval_split()`(donor-crop Δshuffled 프로토콜), `token_losses()`(same-position CE), `attach_decoder_lora_mt5()`(64-module invariant), `make_adapter(seed)`, `generation_record()`.
- `Adapter(512, 512)`: mt5-small d_model=512이고 EG2 layer19 cache가 512d이므로 PA의 native-memory 입력 차원 호환이 성립한다.
- 테스트: alignment(same-position CE == built-in), mask no-shift, copy CE same-position, generation telemetry, F/L mode symmetry, donor unique/non-self, P0 decision. P/PA/M 테스트 없음. "54 tests"는 역사적 근거이며 본 라운드에서 재실행하지 않았다(실행 금지).

### 0.3 수치 재확인

| 항목 | 값 | 출처 |
|---|---|---|
| P0 train Δcopy | +3.7617, CI [1.8917, 5.6050], Δfull +3.5027, positive 14/20 | P0 보고서 §2 |
| P0 val Δcopy | +5.2375, CI [2.5013, 8.0753], Δfull +5.2936, positive 18/20 | P0 보고서 §2 |
| P0 val median / top-3 share | 2.9739 / .4862 (train .4222) | v0.2 §7, 요청서 §4 |
| untrained real CE | 12.7022 / 13.2352 > ln(250112)=12.43 | 요청서 §4 |
| as-run copy coverage | train .8351 / val .8246; strict(piece_len≥2) .2161/.2427 | repair §5, v0.2 §5.3 |
| 정렬 결함 크기 | built-in 31.98719596862793 == aligned CE; old shifted +1.9643 | repair §2 |
| 1-step mode parity | frozen == lora CE 27.43998146057129 | repair §3 |

---

## 1. Q1~Q12 판정

### Q1. P gate — **conditional**

- 판정: conditional (구조는 agree, 잔여 약점의 명시가 조건).
- 근거:
  - v0.1 `P_POSITIVE = mean Δcopy > 0 AND CI lower > 0`(v0.1 §6.2)는 P0가 이미 +3.76/+5.24인 상태에서 near-vacuous였다(종합 §3.1).
  - v0.2 `P_VALID = mean Δcopy >= .05 AND copy CI lower > 0 AND mean Δfull > 0 AND full CI lower > 0`(v0.2 §6.1)은 (a) .05 하한, (b) full CE 동시 요구, (c) step0(P0) vs step100 비교, (d) `P_RETENTION` 기술 보고로 구성된다. binary validity gate로서의 vacuousness는 닫혔다.
  - 잔여 약점: .05 하한은 P0 효과(≈3.76/5.24) 대비 매우 작다. step100에서 Δcopy=0.3에 CI [0.05, 0.6]이면 P_VALID는 통과하고 `REGIME_ERASES_SELECTIVITY`는 발화하지 않는다(P_RETENTION≈0.08). 즉 **이 gate는 "완전 파괴"는 잡지만 "부분 침식"은 잡지 않는다.** 부분 침식은 P_RETENTION descriptive로만 노출된다(v0.2 §6.1 "reported, not a hidden gate").
  - 이것이 허용 가능한 이유: P의 역할은 효과크기 측정이 아니라 경로 파괴 실패 검출이고, plan이 gate 역할을 그렇게 규정했기 때문이다. 다만 이 한계를 결과 전에 문서화해야 결과 후 "P_VALID=true인데 selectivity가 완화됐다"는 해석 다툼이 생기지 않는다.
- 다음 단계:
  1. v0.2에 "P_VALID는 완전 파괴 검출 gate이며 부분 침식은 P_RETENTION descriptive로만 판독한다"는 문장을 결과 전에 추가·동결.
  2. step100 P/PA artifact에 P_RETENTION과 per-doc scatter를 의무 필드로 확정(D2 방향 완성).
  3. .05·CI 조건은 결과 후 변경 금지. 변경 필요 시 새 사전등록.

### Q2. PA arm — **conditional**

- 판정: conditional (설계는 agree, gate 편입과 비교 연산화가 조건).
- 근거:
  - v0.1의 regime confound: P는 adapter bypass라 F/L(adapter+LoRA)과 다른 regime(종합 §3.3). v0.2 §2.4 PA = native memory + `make_adapter(seed)` adapter + 64 LoRA는 이 confound를 직접 분리한다. `Adapter(512,512)` 차원 호환은 §0.2에서 확인.
  - 미완료: (a) `PA_VALID = same criteria on PA`(§6.1)만 있고 **P 대비 비교가 연산화되지 않았다**("PA가 P보다 selectivity를 크게 잃으면" — '크게' 미정의). (b) M_VALID(§6.3)가 P/PA M 결과에 기반하는데, P step100 또는 PA가 validity gate를 통과하지 못한 regime에서 M validation을 신뢰할 수 있는지에 대한 규칙이 없다.
  - gate 편입 제안(구조 정의이지 수치 threshold 추가가 아님): M_VALID는 **P_VALID AND PA_VALID AND P의 M pass AND PA의 M pass**를 요구한다. 이는 v0.2 §6.3의 취지("P/PA M control이 실패하면 M_NOT_VALID")를 완성한다.
- 다음 단계:
  1. `PA_RETENTION = Δ_step100/Δ_step0`(P_RETENTION과 동일 식)를 descriptive로 정의·보고.
  2. `PA_VALID=false && P_VALID=true` → `ADAPTER_SOFT_PROMPT_RISK` descriptive field 정의(결과 전 동결, label 아님).
  3. M_VALID의 전제(P/PA validity)를 §6.3에 명시.

### Q3. M real reference — **agree**

- 판정: agree.
- 근거:
  - v0.2 §2.5/§3: real reference = full real memory `K_real`, donor-crop을 M primary real reference로 사용 금지(§2.5 금지 목록). 타당하다.
  - 기존 `evaluate_arm()`의 real CE는 donor-crop 기반(§0.2). 이는 "길이-matched wrong memory 대비 우위"라는 Δshuffled 질문에는 필수적이지만, mean-memory contrast에 그대로 쓰면 crop 효과와 mean 효과가 섞인다. M은 양쪽 모두 길이 K_real이므로 crop이 없는 clean contrast다.
  - 비교 규칙: donor-cropped real CE는 Δshuffled 문맥에만 유지하고, M 문맥의 real CE(full K_real)와 **한 delta 안에서 혼합하지 않는다.** 두 real CE를 per-doc diagnostic으로 병기하면 cross-check가 가능하다.
- 다음 단계:
  1. per-doc artifact에 `real_ce_full_K`(M용)와 `real_ce_donor_crop`(Δshuffled용)을 별도 필드로 기록.
  2. M 경로에 "mean memory length == K_real" assert 추가, K_real 기록(D2) 유지.
  3. Δshuffled의 donor-crop 프로토콜은 변경 없음.

### Q4. Mean-memory 정의 — **conditional**

- 판정: conditional (구조 agree, 불변식 3가지 추가가 조건).
- 근거:
  - 동결된 규칙(v0.2 §3): train-only, `len(h_i) >= K_real`, eligible<10 → `m_eligible=false` 제외, M_POS_MEAN primary / M_GLOBAL·M_NORM secondary, source ID·eligible count·K_real·norm 기록, P/PA validation. leakage 금지(val/target/donor 혼입, real과 혼합, 타 arm 소급) 명시. negative control로서 screening 수준에서는 충분하다.
  - 빠진 invariant:
    1. **M_NORM 영(零)노름 가드**: `M_NORM = M_POS_MEAN * (||real||/||M_POS_MEAN||)`에서 `||M_POS_MEAN||≈0`이면 정의되지 않거나 폭발한다.
    2. **제외율 보고**: `len>=K` 규칙은 survivorship bias(긴 target 배제)를 만든다. arm/seed별 m_eligible=false 개수를 정량 보고해야 M 적용 범위를 알 수 있다.
    3. **불변성 테스트 실행**: row-permutation(문서 순서 교환 → mean 불변)과 target-perturbation(target summary/passage 변형 → mean 불변). v0.2 D3에 이미 항목이 있으므로 이것은 구현 시 누락 금지 확인 사항이다.
  - 공개가 필요한 미묘점: M_NORM은 target real memory의 **norm**(스케일 통계)을 사용한다. content는 아니지만 target 유도 값이다. "scale-matching 조작"으로 고지하지 않으면 "M이 완전 target-independent"라는 서술이 부정확해진다.
  - position-wise 의미 약점(T5 cross-attention에 position bias 없음)은 v0.2가 인정했고 M_GLOBAL/M_NORM secondary로 완화됐다(종합 §3.4).
- 다음 단계:
  1. M_NORM 영노름 가드 + `real_norm`/`mean_norm` artifact 기록.
  2. arm/seed별 m_eligible=false 개수 보고 필드.
  3. permutation/perturbation/leakage 테스트를 구현 전 unittest로 동결(구체 목록은 Q9).

### Q5. Decision label — **conditional**

- 판정: conditional (방향 agree, precedence·빠진 cell 존재).
- 근거:
  - 개선 확인: `NO_CONTENT_USE_EVIDENCE` → `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE`(absence 오독 차단), `L_SIGNAL true + M fail` cell 추가(`L_SIGNAL_M_CONTROL_FAIL`), P 실패 라벨을 `ASSAY_INVALID` → `REGIME_ERASES_SELECTIVITY`로 정밀화. v0.1 라벨 표(v0.1 §6.3) 대비 overclaim이 유의미하게 줄었다.
  - 잔여 문제:
    1. **precedence 부재**: "P step100 invalid AND M_VALID false"이면 REGIME_ERASES_SELECTIVITY와 M_CONTROL_NOT_VALID가 동시 적용된다. 제안 우선순위: `ASSAY_INVALID > REGIME_ERASES_SELECTIVITY > M_CONTROL_NOT_VALID > (L signal cells) > otherwise`. 근거: control이 invalid하면 M_CONTROL_PASS 해석 자체가 불가하므로 M_CONTROL_NOT_VALID가 signal cell에 선행해야 한다.
    2. **PA-only 실패 cell 없음**: P valid + PA 무효인 경우 — `ADAPTER_SOFT_PROMPT_RISK` descriptive field(Q2)로 처리하고 label은 부여하지 않는 방식을 결과 전에 확정.
    3. **M_CONTROL_PASS true + no L_SIGNAL cell**: 현재 "otherwise → INCONCLUSIVE_SMALL_N"으로 떨어진다. M pass는 "real > train-mean"이라는 affirmative 방향 증거인데 라벨이 이를 반영하지 않는다(다만 v0.1 §11의 "단독 증거 아님" 제한과 함께 과소 주장 방향이므로 안전). 전용 cell(예: MEAN_CONTRAST_ONLY, 명칭은 결과 전 정의)로 둘지 결과 전에 결정.
    4. **XOR rows(COPY_ONLY_WEAK/FULL_ONLY_WEAK) 조건 미명시**: 살아남은 쪽에 2/3 seeds 기준이 적용되는지, M 상태를 함께 기록하는지 미정의. M 상태는 label과 분리된 field로 기록하는 것이 깔끔하다.
- 다음 단계:
  1. §6.4에 precedence 의사코드 추가(결과 전 동결).
  2. 빠진 cell(PA-only, M-pass-only, XOR×M) 처리를 §6.4에 명시.
  3. label 엔진을 synthetic 결과로 unit test(D3).

### Q6. Copy vs full — **agree**

- 판정: agree.
- 근거:
  - P0에서 Δcopy≈Δfull(3.7617 vs 3.5027; 5.2375 vs 5.2936)이고 as-run coverage가 .82~.85로 높아 as-run copy CE는 사실상 full CE와 같은 신호다(종합 §3.6). "copy-specific" 주장은 이 조건에서 성립하지 않았고 v0.1의 overclaim 지적이 정확했다.
  - v0.2 §5.1: aligned full CE co-primary, §5.3: "copy라는 이름은 as-run mask에만 사용", full과 다르면 copy-specific 주장 금지, strict mask(piece_len≥2, coverage .22~.24)는 exploratory secondary. 구성이 적절하다.
  - `L_SIGNAL`이 copy+full 둘 다를 요구하는 것(§6.2)은 과도하지 않다: 두 metric의 상관이 높다는 것이 P0로 확인된 이상 conjunction의 비용은 거의 없고, 갈라짐 자체가 mask-specific artifact의 정보가 된다. XOR case에 `COPY_ONLY_WEAK`/`FULL_ONLY_WEAK`를 둔 것도 균형적이다.
- 다음 단계:
  1. arm별 Δcopy–Δfull 일치/갈라짐을 diagnostic 필드로 기록.
  2. strict mask는 exploratory 표기 유지 — 채택은 새 사전등록에서만.

### Q7. Heavy-tail / power — **agree**

- 판정: agree (범위 선언 포함).
- 근거:
  - 검출 가능한 결론(20 docs, 3 seeds, 12 units, 100 updates):
    - 방향 수준의 validity: trained P/PA의 민감도 유지(P_VALID/PA_VALID + 2/3 seeds), L>F(L_SIGNAL + 2/3 seeds), real > train-mean(M_CONTROL_PASS).
    - heavy-tail 강건성: median, top-3 share(.4862 val / .4222 train), leave-top-3-out mean으로 상위 3문서 의존 진단.
  - 금지해야 할 결론:
    - 효과크기의 cross-regime 비교(P0↔B0-A 직접 비교 금지는 P0 보고서 §3 명시; arm 간 절대 CE 직접 비교 금지는 v0.1 §11 계승).
    - "graded content use" 주장 — untrained real CE 12.70/13.24 > ln|V| 12.43은 uniform 근처/이상 operating point에서 catastrophic wrong-memory 민감도를 보는 것이다.
    - 20-doc bootstrap CI를 확정적 증거로 사용(v0.2 §7 스스로 anti-conservative 가능 인정).
    - top-3가 평균의 약 49%(val)를 만드는 상황에서 평균 단독 대표값 주장.
    - 이 결과의 B0-B 300/95 외삺.
- 다음 단계:
  1. leave-top-3-out mean과 top-3 share를 artifact에 고정(gate 판독 아닌 diagnostic).
  2. 결과 보고서에 "screening only" 문구 필수화.
  3. 외삽은 B0-B 새 사전등록에서만.

### Q8. Compute·implementation — **conditional**

- 판정: conditional.
- 근거:
  - 12 units × 100 updates + per-unit eval(20 docs × 5 donors × 2 memories = 200 CE forward) + M probes + P/PA native memory 사전계산(40 docs encoder forward, frozen encoder이라 seed 간 공유 가능)은 mt5-small CPU 6 threads에서 2 CPU-hours 내 **가능성이 높지만 여유가 적다.** 학습 없이 400 memory+CE pair를 소화한 P0 실적(`p0_eval_split`)이 유일한 실행 근거이고, 학습 unit당 forward+backward가 지배적이다.
  - `--mode pm-diagnostic`, `--pm-arm {f,l,p,pa,mean}`, P/PA `set_training_mode` 확장, M builder, label 엔진, artifact 스키마 모두 미구현(§0.2). "pm-diagnostic 코드가 아직 없다"는 전제가 정확하다.
  - cap 서술 모호: v0.2 §9 "wall time <=2 CPU-hours" — wall time과 CPU-hours는 다른 값이다. 결과 전에 측정 정의를 확정해야 cap 판정이 분쟁 없다.
- 구현 착수 전 Must-fix (ranked):
  1. mode/arm plumbing + artifact 스키마(D2 필드 전부).
  2. `set_training_mode` P/PA 확장(P: adapter 없음/0 adapter params assert, PA: adapter+LoRA) + 기존 F/L invariant 유지.
  3. seeding 순서 고정: `make_adapter(seed)` 후 LoRA init 직전 `torch.manual_seed(seed)`(P/PA 공통) + 동일 seed 재초기화 일치 테스트.
  4. M builder: full-K, eligible, M_GLOBAL/M_NORM(+영노름 가드), leakage assert, source-ID 기록.
  5. metric 계약: co-primary 산출, `seeds_positive`→`documents_positive` 분리 기록, per-seed 표, heavy-tail 필드(median/top-3/leave-top-3-out).
  6. label precedence 엔진 + synthetic unit test.
  7. per-phase timing 기록 + cap 측정 정의.
- 다음 단계:
  1. 위 7개를 구현 착수 전 체크리스트로 동결.
  2. 1-seed debug에서 unit당 시간 측정 → 3-seed 예상 시간 산출. 초과 예상 시 자동 연장 금지, 중단·보고.
  3. P/PA 학습 루프는 frozen encoder의 native train memory를 1회 사전계산해 재사용(계산 절감, 결과 불변).

### Q9. P/PA/M tests — **agree**

- 판정: agree (필수 목록 제시).
- 구현 전 반드시 필요한 test:
  1. **P/PA 구조**: native 경로 64 LoRA modules; P의 trainable = LoRA only(adapter params 0); PA의 trainable = adapter+LoRA; base decoder eval; frozen base requires_grad False.
  2. **seed 재현성**: 동일 seed에서 P LoRA 초기화 재실행 시 동일; PA는 `make_adapter(seed)`→`manual_seed(seed)`→LoRA init 순서 포함 재현.
  3. **mode parity 확장**: base eval + (P: LoRA만 train / PA: adapter+LoRA train) — 기존 `test_training_mode_is_symmetric`의 P/PA 확장.
  4. **M leakage**: mean source IDs ⊆ train IDs; target summary/label/donor/val row 변형 → mean 불변; val ID 혼입 시 fail.
  5. **M 불변성**: row-permutation 불변; eligible<10 → `m_eligible=false` 제외 경로; M_NORM 영노름 가드; M_GLOBAL 길이/형상.
  6. **metric**: native memory 경로에서 same-position CE == built-in loss(기존 test 확장); `documents_positive` vs `seeds_positive` 분리; per-seed mean 계산.
  7. **donor**: 5 unique non-self + duplicate 제외 + duplicate-check 기록(v0.2 §4 신규).
  8. **label 엔진**: synthetic 결과표로 precedence와 전체 cell 커버.
- 다음 단계:
  1. 위 8종을 unittest로 먼저 작성(구현 전 동결).
  2. 전체 suite(54 + 신규)가 debug 전 통과.
  3. 기존 `skipUnless(MODEL.exists())` 조건 유지 — 로컬 모델 의존 명시.

### Q10. 1-seed debug — **conditional**

- 판정: conditional.
- 허용 범위(제안):
  - 구현 + 전체 테스트 + seed 20261108로 F/L/P/PA 1회씩 + M 기계 점검(mean builder, leakage/invariance 테스트, L M probe 1회, P/PA M validation 1회) + per-phase timing.
  - non-gating: debug 결과로 decision label·B0-B·3-seed 판단 금지. v0.2 §10 "1-seed debug는 3-seed 결과가 아니며 gate가 아니다" 준수.
  - hyperparameter(adapter_lr=1e-3, lora_lr=1e-4 등 runner 기본값) 변경 금지 — 변경은 새 사전등록.
- 3-seed gate로 넘어가는 조건:
  1. 전체 테스트 통과(54 + 신규).
  2. artifact 완전성(D2: donor ID/K, mean source IDs, m_eligible, checkpoint hash, timing, `test_split_used=false`).
  3. P/PA path assert 통과(64 modules, mode, finite).
  4. stop conditions(§11) 미발동.
  5. timing이 cap 내 예상을 뒷받침.
  6. 별도 명시적 승인(§10 step 4).
- 다음 단계:
  1. debug artifact 체크리스트를 구현 계약에 포함.
  2. debug 결과 보고서에 "non-gating" 명시.
  3. debug에서 M eval 런타임 측정 → 3-seed cap 예산표(임계값 변경 아님, 측정만).

### Q11. B0-B 경계 — **agree**

- 판정: agree.
- 근거:
  - v0.2 §1 "Phase 6는 B0-B 300/95가 아니다", §6.4 "어떤 label도 B0-B/B1/B2/C를 자동 승인하지 않는다", §12의 검토 조건은 필요조건이며 충분조건이 아님.
  - L_SIGNAL + M pass는 20 docs/100 updates screening 결과다. B0-B 300/95는 다른 n·설계이므로 별도 사전등록(power 근거, threshold, data, seeds, compute)이 필요하다. §12의 금지 조건(ASSAY_INVALID/REGIME_ERASES_SELECTIVITY/M_CONTROL_NOT_VALID/L_SIGNAL_M_CONTROL_FAIL, INCONCLUSIVE_SMALL_N에서 "scale하면 해결" 정당화 금지)이 적절하다.
  - "heavy-tail robustness(top-3 제거 후 방향 유지)"를 B0-B 검토 조건에 넣은 것도 Q7 분석과 일치한다.
- 다음 단계:
  1. B0-B 사전등록은 Phase 6 결과와 독립한 별도 문서로 작성.
  2. §12의 "artifact 완전성" 조건 유지.
  3. test 163/P1/T5Gemma2 상태 불변 명시 유지.

### Q12. 최종 판정 — **NARROW**

- 판정: NARROW.
- 근거(요약):
  - v0.2는 v0.1 3-AI Must-fix 6개(종합 §4)를 **prereg 수준에서** 닫았다: P gate 강화+PA(1), M 정의 동결(2), leakage·seed·mode 테스트 항목(3), label 재작성(4), co-primary(5), artifact/cap contract(6).
  - 그러나 (a) 구현·테스트는 존재하지 않고(§0.2), (b) label precedence·PA 비교 연산화·M_NORM 가드·cap 측정 정의 등 **결과 전에 동결해야 할 계약 항목이 남아 있으며**(Q1/Q2/Q4/Q5/Q8), (c) trained P/PA/M 결과는 아직 하나도 없다.
  - 잔여 항목들은 과학적 재설계가 아니라 계약 tighten이고 threshold/seed/donor/step 변경을 수반하지 않는다. 따라서 STOP(재설계 필요)도 CONTINUE(그대로 착수)도 아니고 NARROW가 정확하다.

---

## 2. Must-fix (ranked)

| 순위 | Must-fix | 근거(Q) | 완료 조건 |
|---:|---|---|---|
| 1 | **Label precedence + 빠진 cell 동결** | Q5 | §6.4에 우선순위 의사코드, PA-only/M-pass-only/XOR×M cell 정의, synthetic unit test 설계까지 결과 전 commit |
| 2 | **PA gate 편입·비교 연산화** | Q2 | PA_VALID를 M_VALID 전제에 포함, PA_RETENTION 정의, ADAPTER_SOFT_PROMPT_RISK descriptive field 정의 |
| 3 | **M_NORM 가드 + exclusion/norm artifact** | Q4 | 영노름 가드, m_eligible=false 개수, real/mean norm 기록, M_NORM의 target-norm 사용 고지 |
| 4 | **cap 측정 정의 + per-phase timing** | Q8 | wall vs CPU-hours 정의, 단계별 timing artifact, 초과 시 중단·보고(자동 연장 금지) |
| 5 | **코드 계약 테스트 동결** | Q8/Q9 | documents_positive 분리, set_training_mode P/PA, seeding 순서 테스트, donor duplicate 제외, leakage/invariance 테스트를 구현 전 unittest로 확정 |

주의: 이 목록은 threshold·seed·donor·step 변경을 포함하지 않는다. 전부 결과 전 정의·문서화·테스트 동결 항목이다.

---

## 3. 잘못된 전제 (본 검토가 발견한 것)

1. "v0.2가 Must-fix를 닫았다" — **prereg 수준에서만** 닫았다. 구현(`--mode pm-diagnostic`), P/PA `set_training_mode`, P/PA/M 테스트, label 엔진은 코드에 없다(§0.2).
2. "P0 val 20이 confirmatory holdout" — 아니다. v0.2 §4 "P0 기존 val 20을 재사용; confirmatory holdout으로 부르지 않음"이 정확하다. 이 reused val의 유의성은 screening 근거다.
3. "M이 완전히 target-independent" — M_NORM은 target real memory norm을 사용한다(scale-matching). 고지 필요(Q4).
4. "P gate가 selectivity 보존을 검증한다" — 완전 파괴만 검출하고 부분 침식은 P_RETENTION descriptive다(Q1).
5. "L_SIGNAL + M pass면 B0-B로 간다" — 아니다. 별도 사전등록·승인(v0.2 §12, Q11).
6. "2 CPU-hours가 객관적 cap이다" — 측정 정의(wall/CPU)가 없어 판정 근거가 없다. 정의 확정이 MF-4다(Q8).

---

## 4. 최종 판정 (요청 형식)

```text
최종 판정: NARROW
v0.2: 조건부 승인 — MF-1~MF-5를 결과 전에 반영(threshold/seed/donor/step 무변경)하면 승인
구현·1-seed debug: 승인 (MF 반영 + 전체 테스트 통과 후, non-gating, Q10 범위)
3-seed: 미승인 — 별도 gate (Q10 조건 충족 + 명시적 승인)
금지 범위: test 163/P1/T5Gemma2, B0-B·B1·B2·Stage C 자동 진행, 결과 후 threshold·seed·donor·step 변경,
          P0↔B0-A 및 arm 간 절대 CE 직접 비교, trained M arm 신설
최대 compute: 12 arm-seeds, ≤1,200 updates, ≤2 CPU-hours(측정 정의는 MF-4로 확정), 6 threads, GPU 없음, retry 없음
다음 decision gate: 1-seed debug artifact 검토 → 3-seed 승인 여부(별도 gate); M probe/report는 3-seed 후
test 163: sealed 유지
Must-fix (ranked): MF-1 label precedence/cells, MF-2 PA gate 편입·PA 비교 연산화, MF-3 M_NORM 가드·exclusion/norm
                   artifact, MF-4 cap 측정 정의·timing, MF-5 코드 계약 테스트 동결
잘못된 전제: 위 §3의 6가지 (구현 미존재, val 재사용, M_NORM target-norm, gate=완전파괴 검출, B0-B 비자동, cap 정의 미확정)
```

---

*본 보고서는 consultation-only 검토 산출물이며 Phase 6/B0-B/B1/B2/Stage C의 승인을 구성하지 않는다. test 163은 개봉하지 않았고 P1은 사용하지 않았다. 학습·평가는 실행하지 않았다. 이 파일 외 저장소 변경은 없다.*