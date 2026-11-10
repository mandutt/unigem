# C5 F0 v1.0 — Round 10 Final Review (GLM)

- 작성일: 2026-11-10
- 검토 대상: `docs/plan_c5_f0_v1_0_2026-11-09.md` (DRAFT v1.0)
- **reviewed HEAD: `80a723f83b2e559ebc1f64bc7bff12d7ed582d48`** ("docs: add C5 F0 v1.0 final review request")
- 동기화: `git fetch origin` + `git pull --ff-only origin main` → "Already up to date", HEAD = `80a723f…`
- 모델: `z-ai/glm-5.3-flash` (독립 스레드, v0.9 결론 미상속)
- 방법: 문서 8종 + `runner/c5_pm_phase6.py` + `runner/c5_mt5_lora_b0.py`/`c5_pm_stats.py` 대조 열람. **학습/평가 실행 없음, test 163/P1 미사용, subagent 없음, repository 수정 없음 (이 파일 1개만 작성).**

---

## 0. Verbatim paired E01−E11 (대상 문서에서 그대로 인용)

v1.0 §2 Cells 표, E01/E11 행:

```text
| E01 (F0) | EG2 raw | none | 64 modules | 100 | adapter-free + LoRA |
| E11 (L) | EG2 raw | trained | 64 modules | 100 | adapter + LoRA |
```

v1.0 §6.3 Primary contrast (전문):

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
```

v1.0 §6.3 (전문):

```text
- Primary positive: `mean_D > 0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0`.
- `D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary.
- Copy primary; full secondary.
- **CI_D is doc-level only.** Seed-level `D_s` is a gate/descriptor, not a doc-level interval.
- `PASS_POSITIVE` requires the paired contrast, E01 absolute copy signal, and seed replication; this is not a per-cell significance conjunction.
```

---

## Q1. Initialization audit — **conditional agree**

근거:

- §4 pseudocode (L83–94): `torch.manual_seed(seed)` → adapter → `torch.manual_seed(seed ^ 0x5EED10A5)` → LoRA attach. 어댑터 생성 후 LoRA 시드를 항상 재설정하므로 E01/E11의 LoRA init은 구조적으로 동일하다. committed Phase 6 `build_arm`(`runner/c5_pm_phase6.py:142`, "RNG order: seed, adapter, then LoRA")와 의도적으로 다르며, §4 L111 "F0 E11 ≠ Phase 6 L at init"으로 명시 — 정합.
- §4 assertions 1–8 (L101–109): `lora_names` 길이 64 동일, LoRA A/B sha256 동일, adapter sha256 E10==E11, post-init/post-step0 RNG state 동일, `lora_B` zero를 별도 assert(6), 셀별 부재 assert(7), base/cache/label freeze hash(8). `attach_decoder_lora_mt5`(`c5_mt5_lora_b0.py:52–75`)는 64 modules 강제 → assertion 1과 정합.
- Per-step reseed (§4 L92–100): 모든 셀이 동일 `step_seed(seed, step)`을 forward 전에 사용 → dropout RNG 구조적 동일. RNG 동일성이 "assumed"가 아닌 "structural"이라는 표현은 정확하다.

남는 문제 (must-fix 2·3·6):

1. **§0 변경요약 5가 약속한 "step_seed golden table"이 §4 본문에 없다.** grep 결과 `step_seed golden table`은 L33(변경요약)에만 존재. 또한 `step_seed = seed ^ (0x9E3779B9 * (step+1)) & 0xffffffff`(L92)는 Python 연산자 우선순위상 `seed ^ ((MUL*(step+1)) & 0xffffffff)`로 해석되지만 문면은 모호하다. golden vector table + golden test가 없으면 구현 시 precedence 해석이 갈릴 수 있다.
2. **§0 변경요약 5의 "post-step0 weight non-equality"도 §4 assertions에 없다.** init 동일성만 assert하고 학습 후 가중치 비동일성(학습이 실제로 진행됐다는 sanity)은 본문에 부재.
3. "before each forward"(L93)의 범위 미정의: train forward인지, eval(step0/final, donor-crop) forward까지인지. eval 모드에서는 LoRA dropout이 비활성이므로 결과는 같지만 규격으로는 pin되어야 한다.

다음 단계: (1) §4에 step_seed golden table(등록 seed 4종 × step 0/1 기대값)과 precedence 명시, (2) §4에 post-step0 weight non-equality assert 추가, (3) reseed 적용 forward 범위 한 문장 고정 — 모두 구현 commit에서 해결 가능.

## Q2. D1 seal — **conditional agree (1개 내부 모순은 must-fix)**

근거:

- §5 D1 (L155–165): signal delta/per_doc/phase7/final 미산출, `d1_mechanics.json` exact-key allowlist, `d1_report.json` 금지 경로, `d1_sealed/` 부재, negative test("any `d1_report.json`/`per_doc`/`delta_*` input exits non-zero"), "D1 values must not be read for Stage R or STOP"(L165). v0.9 must-fix 2를 v1.0이 digest-only로 강화 — 방향 correct.
- Checkpoint oracle: L160–163 "digest-only: SHA-256 recorded, checkpoint file discarded; loading forbidden" + "process non-computation is not artifact non-access" 자체 인정 + state_dict-only/no signal arrays. Phase 6 `save_d1_checkpoint`(`c5_pm_phase6.py:765–776`)가 파일을 남기는 것과 대비되는 강화.
- D1 assertion 6: `phase7 records == 0` (L148) — D1이 phase7을 쓰지 않음을 count로 검증.

남는 문제:

1. **내부 모순 (must-fix 1, blocker-class):** §5 D1 assertion 9 (L151) = "3 trained checkpoints exist; E00 checkpoint optional"인데 L160은 "checkpoint file discarded". 두 절을 문자대로 이행하면 서로 배타적이다. assertion 9는 "3 checkpoint digest 기록 + D1 종료 시 checkpoint 파일 0개"로 교체되어야 하고, §13 artifacts의 `checkpoints/{cell}/{seed}.pt`(L374)는 Stage R 전용임을 명기해야 한다.
2. 남는 우회 경로: (a) D1 arm process는 counts를 위해 step0/final eval을 메모리에서 계산한다(L146 `n_docs_step0/n_docs_final == 20`) — artifact allowlist는 파일 누출은 막지만 stdout/log 누출 규정이 없다. (b) Phase 6 `run_d1`이 쓰는 `d1_partial.json`(`c5_pm_phase6.py:857–871`) 전례가 있으므로 F0 D1의 partial file 정책(허용 경로 1개 명시 또는 금지)이 필요하다. (c) external review 요구의 "phase7 filesystem assert"는 §0.3에만 있고 §5에는 count assert만 있다 — 디렉터리 부재 assert를 §5에 명시 권장.

다음 단계: (1) assertion 9 재작성 + §13 범위 명기, (2) D1 stdout/partial-file 정책 1줄 추가, (3) phase7 디렉터리 부재 filesystem assert 명시.

## Q3. STOP / MDE — **agree**

근거:

- 상호배타·전체포괄: §7 L280–288 priority 1–4. `NOT_EVALUABLE`(1) → `PASS_POSITIVE`(2) → `ROUTE_STOP`(3, `ALL_FAIL`) → `INDETERMINATE`(4, catch-all). PASS는 `SIGNAL(E01,copy)`를 요구하고 ALL_FAIL은 `FAIL(E01,copy)`를 포함하므로 2와 3은 논리적으로 배타 — 순서는 belt-and-braces.
- PASS vs EQUIVALENT 비겹침: PASS는 `CI_D.lower > +.05`(L285), EQUIVALENT는 CI 전체가 `[-.05,+.05]`(L269) → lower가 +.05 초과면 EQUIVALENT 불가. §6.5 L238 "practical-equivalence label; not a population equality claim" — v0.8 MF-1 해소 유지 확인.
- reason enum: precedence `EQUIVALENT > harm > benefit`(L277), `ALL_FAIL`+각 라벨→`no_signal_equivalent`/`adapter_harm`/`adapter_benefit`, 그 외 default `no_signal_uncertain`(L291–294). default는 도달 가능: delta≈0이면 CI≈±.117 → EQUIVALENT/harm/benefit 모두 비해당 → `no_signal_uncertain`. Phase 6 L처럼 broad negative(CI upper <0)이면 `adapter_benefit` — cause report §1(L CI [-0.2341,-0.0012])과 방향 정합.
- MDE: §12 L359 ".166/.216 are approximations from Phase 6 L single-arm half-width ≈.117; report realized `CI_D` half-width and implied MDE". .117은 Phase 6 L 15-doc CI 폭 0.2329의 절반과 일치(P6 synthesis DS 지적 인용 수치). "`.05` is a lower-bound gate, not power at .05; results bounded/exploratory" — 과소검력 정직 표기. paired contrast는 single-arm보다 분산이 작을 수 있어 .166/.216은 보수적 상한 추정이라는 점도 "approximation" 표기로 커버됨.

다음 단계: 없음(설계 변경 불요). 결과 보고 시 realized half-width + implied MDE 필수 기입만 상기.

## Q4. Cohort / CI — **agree**

근거:

- §6.1 (L181–191): 15 common = frozen preflight `common_ids`, 전 셀×seed 존재 검사, doc당 정확히 5 donors, donor sets 셀 간 동일, doc-level 3/3.
- 셀 간 donor 동일성은 구조적으로 보장된다: 4개 셀 모두 EG2 raw memory이므로 `donors_for(val_ids, cache)`(`c5_mt5_lora_b0.py:318–326`, EG2 h_len 기반 deterministic length-nearest)가 셀 무관 동일 list를 반환; §4 assertion 8/§7 PROTOCOL_VALID가 이중 검증.
- Silent-drop 차단: committed `eval_arm_d1`(`c5_pm_phase6.py:471–473`)은 copyable token 부재 doc을 `continue`로 누락한다. v1.0 §6.1 L189 "a missing doc means `NOT_EVALUABLE`, never a smaller cohort"로 명시적 차단 — P6 review의 cohort 축소 우려 해소.
- n_boot=10000 override는 committed `bootstrap_paired_v2(values, n_boot=N_BOOT, seed=BOOTSTRAP_SEED)`(`c5_pm_stats.py:29–33`)가 인자로 허용 → 구현 가능. override가 F0 prereg 자체에 등록되어 있고 "argument + record"(§0.4) 요구 존재 — frozen §10.1(n_boot=1000) 위반이 아니라 사전 등록된 변경.
- donor dependence: wrong-donor CE = 5 donor 평균, donor pool이 doc 간 겹침(length-nearest) → doc-level bootstrap의 교환성 가정에 경미한 의존 존재. Phase 6 §2.5.6과 동일 컨벤션이므로 신규 리스크 아님; CI는 "doc-level resampling interval"로 해석 한정 권고.

다음 단계: (1) f0_report에 override 기록 필드 명칭 고정(예: `n_boot_override:10000`), (2) CI 해석 문구 1줄.

## Q5. Compute — **agree (conditional: D1 nproc 게이트)**

근거:

- 수치 정합: R 900 updates = 3 trained cells × 3 seeds × 100(§5 L171); D1 updates_total=3(§5 L140); M 1,440 = 120×4×3, phase7 7,200 = 600×12, generation 240 = 20×4×3(§5 L172) — prereg §11.5/§2.3 레코드 수 산식과 모두 일치. 12 logical = 4 arms × 3 threads(§5 L141,173).
- D1 25 min: D-156 실측 1,180.6s / 1,200s cap(`docs/decisions.md:216`)과 정합, F0 D1은 Phase 6 D1보다 phase7(2,400→0)·controls가 가벼우므로 25 min cap은 근거 있는 여유. 단, prereg §11.3 D1 cap은 ≤20 min이므로 F0이 cap을 완화한 것임을 문서에 명시 권장(사소).
- R 96 min: prereg §11.5 "T_proj finite/nonnegative/≤96 min" 그대로 인출 — 출처 정확. T_proj_R 공식(§12 L353)은 §11.5의 8-phase term set을 유지하되 집계가 "all-arm 합"(Phase 6)에서 "slowest arm ×3 waves"(F0 병렬)로 바뀐다 — 병렬 orchestration에 correct한 적응이지만 "Phase 6 §11.5 term set"이라는 표현은 term set만 공유함을 밝혀야 한다(잘못된 전제 참조).
- "no 1.316 multiplier"(§5 L174) — v0.x의 계수 문제 제거 확인. Hard abort `nproc<12`/`T_proj_R>96`(§12 L358), no retry/extension(L362).
- Orchestration commit 선행조건: §11 L333–342 신규 `c5_pm_f0.py`/`c5_pm_f0_parallel.py`/`c5_pm_f0_gate.py`, "Implementation + D0/D1 requires approval". P6 MF-1 provenance gap 상태도 개선됨 — `c5_pm_registered.py`/`c5_pm_labels.py`/`c5_pm_gate.py`/`c5_pm_replay.py`/`c5_pm_stats.py`가 현재 HEAD의 `runner/`에 커밋되어 있고 `main()`이 `--mode registered`를 처리한다(`c5_pm_phase6.py:946–963`). F0도 동일 컨벤션 준수가 게이트.

남는 문제 (must-fix 5): `nproc<12` hard abort는 §12에서 R에만 명시되어 있다. D1도 12 logical threads를 요구하므로 D1 실행 전 nproc 검사 + 기록이 필요하다(D0에서 `nproc` 기록으로 충분).

다음 단계: (1) D1 nproc 전제조건 1줄 추가, (2) T_proj_R 집계가 all-arm 합이 아님을 §12에 명기.

## Q6. Scope — **agree (해석 한정 조건부)**

근거:

- Title/claim: §0.1 "Factorial → Single-Contrast Diagnostic", registered contrast는 E01 vs E11 하나, 나머지 셀쌍은 descriptive + confounded 명시(§2 L65–69). architecture-only bottleneck 금지(§0.1, §14 L395) — P6 MF-3/MF-4의 과대일반화·confound 지적을 정면으로 수용.
- H3: §10 (L327–331) 완전 제외 + "H3 requires a separate prereg ... F0 results do not automatically launch H3". §17 "B0-B/B1/B2/Stage C 자동 진행 금지", "Phase 6 결과 재해석으로 B0-B 구제 금지" — 자동 승급 차단 충분.
- Lost controls: §14 L396 "the earlier MF-4 zero/permuted null and 1-seed signal gate are intentionally out of scope; F0 cannot claim they were replaced". §7 PROTOCOL_VALID/§6로 1-seed 게이트 대신 3-seed full 등록 — 폐기가 "교체"가 아님을 명시한 것은 정직하다.

해석 한정 (조건): null control 부재 하에서 `PASS_POSITIVE`는 donor-crop eval 기계 자체의 artifact 가능성을 배제하지 못한다. paired E01−E11은 init을 통제하지만 endpoint에 대한 placebo가 없다. 따라서 F0 출력은 §14 대로 association-only로 보고되어야 하고, PASS 시에도 "adapter가 원인"이 아니라 "이 고정 route에서 adapter-as-configured와 signal이 연관"으로만 기술되어야 한다. 이는 계획이 이미 규정한 바이며 위반 시 review 재개 사유.

다음 단계: (1) f0_report.json 결과 서식에 association-only 문구 포함, (2) H3 개시 조건 "별도 prereg + 승인" 유지 확인.

---

## 최종 판정

```text
최종 판정: CONTINUE
Initialization:   conditional agree — golden table/weight non-equality/reseed scope 보강 필요
D1:               conditional agree — assertion 9 vs digest-only 모순 해소 필수
STOP/MDE:         agree
Cohort/CI:        agree
Compute:          agree — D1 nproc 게이트 1줄 보강
H3/Scope:         agree — association-only 해석 한정 유지
```

**CONTINUE = F0 구현 commit + D0 stage approval 진행을 승인한다.** 단, 아래 must-fix가 구현 commit 이전에 계획 문서/구현에 반영되고 D0 stage-approval 게이트에서 확인되어야 한다. threshold/seed/donor/step/LR 변경은 여전히 금지이며, 본 must-fix는 어느 것도 해당 frozen 값을 건드리지 않는다. 신규 review round는 불요 — D0 승인 시점 확인으로 충분.

## Must-fix (ranked)

1. **D1 assertion 9 ↔ digest-only seal 모순 제거** (§5 L151 vs L160; §13 L374): assertion 9를 "3 checkpoint digest 기록, D1 종료 시 checkpoint 파일 0개"로 교체; §13 `checkpoints/`를 Stage R 전용으로 명기.
2. **step_seed golden table 추가** (§0.5 약속 vs §4 부재): precedence 고정 + seed 20261108/09/10/11 × step 0,1 기대값 table + golden test 명세.
3. **post-step0 weight non-equality assert를 §4에 추가** (§0.5 약속 vs 본문 부재).
4. **artifact 파일명 통일**: §5 L177 `f0_r_labels.json` vs §13 L377 `f0_labels.json` — 하나로 고정.
5. **D1 nproc≥12 전제조건 명시** (§12 L358은 R에만 존재) + D0에서 nproc 기록.
6. **D1 partial/stdout 정책**: D1이 쓸 수 있는 파일 경로를 allowlist로 1개로 한정(Phase 6 `d1_partial.json` 전례 차단), arm process stdout 보존 정책 명시.
7. **per-step reseed 적용 범위 pin** (train forward vs 모든 forward) — §4에 1문장.

## 잘못된 전제

1. "T_proj Phase6 §11.5 term set" — term 집합은 동일하지만 Phase 6 §11.5는 **4-arm 합**이고 F0은 **slowest arm ×3 waves**이다. 동일 항 세트의 재집계이지 동일 공식이 아님; 문서 표현이 이를 단순화하고 있다.
2. "R 96 min" 출처는 prereg §11.5로 정확하나, 같은 절에 "120-min hard abort"(§11.5)와 §11.1 registered wall 120 min이 병존한다. F0이 더 엄격한 96을 채택한 것은 문제없지만 출처 내 이중 기준을 인지하고 있어야 한다.
3. Phase 6 D1 cap은 prereg §11.3 기준 ≤20 min이다. F0의 25 min은 Phase 6 값 인용이 아니라 완화이며(F0 D1이 더 가벼워 정당), §3 "frozen Phase 6 values" 문구가 cap까지 포괄하는 것으로 오독되지 않게 cap은 frozen 항목이 아님을 밝힐 것.
4. "LoRA initialization matched"는 초기화 일치이지 학습 후 가중치 일치가 아니며(§4 L112 명시) — 이 전제는 본문에 정확히 기재되어 있으므로 결과 해석 단계에서만 반복 상기하면 된다.

## 검증 범위

- 확인된 것: HEAD 동기화(80a723f, up-to-date), 문서 8종 전량 열람, `runner/c5_pm_phase6.py`(970 lines)·`c5_mt5_lora_b0.py`·`c5_pm_stats.py`의 대응 함수 대조, D-156 수치의 decisions.md 원출처 확인, `bootstrap_paired_v2` n_boot/seed 인자 확인, §13/§5/§0 간 수치·파일명 교차검증.
- 실행하지 않은 것: 학습/평가 전무, test 163/P1 미접촉, subagent 미사용 — external review §0 규정 준수.
- 미확인(실행 전제): 실제 호스트 nproc≥12 여부 — D0 기록으로 확인될 사항이며 설계상 abort 게이트가 존재.