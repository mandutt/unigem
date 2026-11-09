# C5 F0 v0.2 — Independent Re-Review (GLM)

- 검토일: 2026-11-09
- **Reviewed HEAD: `185d2ff7b2c29aaa10093838335cb15901981657`** (origin/main, commit "docs: revise C5 F0 draft to v0.2")
- 동기화: `git fetch origin` → `git pull --ff-only origin main` = "Already up to date", 작업 트리 clean
- 대상: `docs/plan_c5_f0_v0_2_2026-11-09.md` (DRAFT v0.2 — 미승인·미실행)
- 성격: **새 독립 재검토 스레드.** v0.1 스레드의 후속이 아니며 결론을 상속하지 않음.
- test 163: sealed / P1: unused / T5Gemma2: D-108 STOP
- 실행: 없음 (학습·평가 없음, runner 실행 없음, test 163/P1 미사용, subagent 없음)
- 파일 수정: 본 보고서뿐 (다른 파일 무변경)

---

## 0. 검토 방법

직접 읽은 파일:

- `docs/plan_c5_f0_v0_2_2026-11-09.md` (검토 대상), `docs/plan_c5_f0_2026-11-09.md` (v0.1, superseded)
- `reports/EXTERNAL_REVIEW_C5_F0_V0_2_2026-11-09.md` (검토 요청)
- `reports/C5_F0_DRAFT_3AI_REVIEW_SYNTHESIS_2026-11-09.md` (v0.1 3/3 NARROW, MF-1~MF-6)
- `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
- `docs/plan_c5_b0a_pm_prereg_v1_0_11.md` (frozen Phase 6 spec — 상속 정의의 출처)
- `runner/c5_pm_phase6.py` @ HEAD (코드 대조: `ARMS` L59, `arm_spec` L125, `build_arm` L142, `run_d0` L280, `optimizer_for` L367, `memory_for` L391, `eval_arm_d1` L429, `train_registered` L518, `run_registered_unit` L890)

판정 축: v0.1 must-fix 6개(draft synthesis §3)가 v0.2에 반영됐는지 + v0.2 자체의 신규 결함.

---

## Q1. Stage D/R selection bias 제거

- 판정: **agree (conditional)**
- 근거:
  - v0.2 §0.1–2/§4: Stage D = D0(0 update) + D1(1 update), "no decision labels; telemetry only", Stage R은 "only after D0/D1 mechanics pass (not signal-based)", "**No 1-seed signal gate**", R은 항상 3 seeds(20261108/09/10). v0.1 §8이 갖고 있던 selection channel 2개 — (a) 1-seed 결과로 R 진입/STOP 결정("E01 copy mean delta > 0 AND E01−E11 paired copy mean > 0 …" 아니면 "STOP F0"), (b) 1-seed 결과로 트랙 STOP("stop EG2 resident track") — 이 모두 제거됐다. 남는 D→R gate는 순수 기계 검사(shape 753×512, LoRA 0/0/64/64, finiteness)뿐이며, 이는 draft synthesis MF-2의 수정안 3개 중 두 가지(mechanics-only + 항상 3-seed)를 동시에 채택한 것이라 이중으로 안전하다.
  - **D1은 필요하다, D0만으로는 부족하다.** `run_d0`(runner L280)은 build + memory_probe + assert만 수행하고 optimizer step, checkpoint 저장, eval battery를 전혀 실행하지 않는다. D1은 1-update 학습 경로, step0/final 20×5 donors, M 120/cell, phase7 600/cell, generation 20/cell, checkpoint 저장을 검증하고 R wall-time 산출에 필요한 per-phase timing을 남긴다. 25분짜리 D1으로 120분짜리 R 진입 전 training-path 기계 결함을 잡는 것은 정당하다.
  - 결함 2개: (1) §4 D1 "4 cells, 1 update"과 §9 표 "D1 | 4 | 4"는 §2 표(E00 updates=0)·§6("E00 is a baseline")과 모순이고, 코드상 E00형 셀은 `optimizer_for`가 `no trainable parameters` RuntimeError를 낸다(L367–375, 아래 MF-2). (2) "mechanics pass"의 판정 술어가 열거되어 있지 않아 gate가 재량으로 남을 수 있다.
- 다음 단계:
  1. D1을 "E10/E01/E11 ×1 update + E00 0-update eval-only battery"로 수정, §9 표를 3 updates로 정정.
  2. D0/D1 pass 술어를 assert 목록으로 명시 + "D1 실패 시 코드 수리·D1 재실행만 허용, threshold/scope 변경 금지" 명문화.
  3. D1 signal telemetry(`step0`/`final` eval 산출물)가 어떤 결정에도 사용되지 않음을 artifact 필드로 명기.

## Q2. E01 vs E11 2×2 validity

- 판정: **agree (conditional)**
- 근거:
  - E01 vs E11은 v0.2 §2 기준 LoRA 고정(64 modules, r8/α16/dropout .05), adapter absent/present, 동일 100 updates·cohort·donor·threshold — v0.1 review MF-4가 요구한 "F0 vs L (LoRA 고정, adapter만 차이)"의 정확한 구현이다. §2가 E01 vs E10을 "not clean causal", E10 vs E00을 confounded, E00을 "not a trained unit"로 표기한 것(MF-3 반영)도 정확하다. Primary contrast로서 타당하다.
  - 단, 해석 범위 조건 2개가 문서에 명시돼야 한다.
    (a) **adapter-as-configured**: E11은 E01 대비 학습 파라미터 +526,336(Linear 512→512 ×2 + LayerNorm 512; results synthesis MF-4의 P/PA 수치와 동일)과 adapter_lr 1e-3(LoRA 1e-4의 10×)을 추가로 가진다. 또한 prereg v1.0.11 §2.7 RNG 순서(seed → adapter → LoRA, no reseed)상 E01(LoRA만)과 E11(adapter 후 LoRA)의 LoRA 초기화 draw가 달라진다. 따라서 E11−E01은 "adapter 유무(as configured)"이지 LayerNorm vs input-insensitive mapping vs optimization interference를 분리하지 못한다 — §5 "No positive result uniquely proves adapter architecture"와 방향은 일치하지만 §2 본문에 한 문장 필요.
    (b) **decision algebra 부재**: §5 분기(E01 positive / E11 negative / E01−E11 >0)의 술어가 정식화돼 있지 않다. v0.2 §5는 "Signal predicates use frozen Phase 6 definitions: copy mean ≥ .05, CI lower >0, 2/3 seeds >0 / full mean >0 …"로 요약하지만, (i) 그 술어가 E01/E11 각각의 arm-level signal에 붙는 것인지, (ii) paired contrast E01−E11에도 CI lower >0를 요구하는지, (iii) "E01 ≈ E11"의 연산적 정의, (iv) missing registered seed → NA·no 2-of-available 상속(prereg §3.5)이 빠져 있다.
- 다음 단계:
  1. E01_SIGNAL / E11_SIGNAL / PAIRED_CONTRAST 술어를 prereg §3.5 스타일로 재기술(CI 조건 포함)하고 missing-seed → NA 상속 명시.
  2. §2에 adapter-as-configured 조건(+526,336 params, adapter_lr 10×, LoRA-init RNG stream 차이) 한 문장 추가.
  3. "E01 ≈ E11"을 연산적으로 정의(예: paired contrast CI가 0을 포함하고 양 arm 술어 모두 false).

## Q3. route STOP vs track STOP interpretation

- 판정: **agree**
- 근거:
  - v0.1의 blocker 모순(§1 H2 "F0 negative는 트랙 STOP의 충분조건이 아니다" vs §8 "E01 negative and E11 negative → stop EG2 resident track")이 해소됐다. v0.2 §5 분기 2: "this configured EG2-raw→mT5-decoder route does not show donor-specific signal; **not** proof that EG2 features lack information. Track decision separate." §0.3도 "최대 'EG2-raw→mT5-decoder route as configured'만 STOP"으로 한정, §11 non-goals에 "EG2 전체 track STOP/keep 결정" 금지. 이는 draft synthesis MF-1 수정 문구("stop the EG2-raw→mT5-decoder route as configured")를 그대로 반영한다.
  - positive/negative 분기가 4개 모두 존재한다(E01+/E11− → adapter-associated signal loss supported, 다음 진단 H3 / E01+/E11+ → adapter 불필요, 구조적 주장 금지 / E01≈E11 → adapter 효과 미지지 / E01−/E11− → route 한정 STOP).
  - 보강점 3개: (a) "route as configured"가 연산적으로 정의돼 있지 않다 — EG2 layer19 raw 753×512 prefix → mT5-small decoder(base eval) + decoder LoRA r8/α16, frozen Phase 6 hyperparams/cohorts/thresholds, 20-doc 학습, donor-crop signal 조합에 한정된 STOP임을 명시해야 한다. (b) E01+/E11+ 분기에 다음 단계가 없다 — v0.1 §8의 "investigate replication/anomaly, not H3" 절이 삭제됐다. (c) F0 결과가 Phase 6 negative 종료와 B0-B 미승인 상태를 소급 변경하지 않음을 한 줄 명시(§14 금지와 정합).
- 다음 단계:
  1. §5에 "route as configured" 정의 문장 추가.
  2. E01+/E11+ 분기에 "replication/anomaly 조사(별도 prereg)" 복원.
  3. non-retroactivity 문장 추가.

## Q4. M/signal and E00 baseline

- 판정: **agree (conditional)**
- 근거:
  - M 120/cell/seed = 15 common × 2 variants × 2 endpoints × 2 memory kinds로 prereg v1.0.11 §11.3 phase-5 산술(F/L 120/arm-seed)과 정확히 일치하고, E10/E11/E00 모두 F/L형 K=753/15 common이므로 cell당 120이 맞다. Stage R 총계 M 1,440 = 4 cells × 3 seeds × 120, phase7 7,200 = 4×3×600, generation 240 = 4×3×20도 자기일치한다.
  - §6 "M_PASS is not donor-specific content-use evidence", "M is reported separately; not a gate"는 cause report §1/§5의 실측(M 표: P control-real 6.118·wrong-real 2.531·ratio 0.414 vs F 0.576/0.001, L 0.365/−0.017 — 모두 M_PASS true인데 L_SIGNAL=false, L mean Δ copy −0.1135, CI [−0.2341, −0.0012], 6/15 positive, 0/3 seeds)과 results synthesis MF-5를 정확히 반영한다.
  - E00 처리(§2/§6): eval-only baseline, "not a clean training control; interpret only as descriptive" — MF-3 반영이 정확하다. E00의 M 120/cell/seed도 descriptive로만 읽어야 한다(untrained decoder 기준 CE이므로 trained cells와 직접 비교 불가).
  - 조건: **primary endpoint의 record source가 지정돼 있지 않다.** §4 Stage R 예산에는 M 1,440/phase7 7,200/generation 240만 있고 step0/final donor-crop signal eval(§3 정의: 20 val docs ×5 donors) 행이 없다. 그런데 Phase 6에서 unit-final donor-crop signal과 phase7 재계산이 다른 값으로 문서화돼 있다(results synthesis §4 GLM: unit-final −0.1135 vs phase7 −0.0407; DS: 15-doc −0.1135 vs 20-doc −0.0222). F0 primary delta(E01−E11)를 phase7 raw ce에서 계산할 것인지 별도 unit-final eval로 둘 것인지 미확정이면 값이 소스에 따라 달라진다. Tail(signal tail only, E01/E11)이 어떤 F0 결정에도 쓰이지 않음도 명시 필요.
- 다음 단계:
  1. primary delta record source 명시(unit-final donor-crop eval vs phase7 records) + Stage R 예산에 signal eval 행 추가.
  2. missing registered seed → NA, no 2-of-available, no 15→14 상속 명시.
  3. tail 포함 모든 F0 진단을 descriptive-only로 표기.

## Q5. Compute realism

- 판정: **agree**
- 근거:
  - 기준선: prereg v1.0.11 §11.1 registered = 12 units / 1,200 updates / wall 120 min / threads 6 / GPU none, 그리고 results synthesis MF-6의 DS 실측 **82 min**. F0 Stage R은 12 units(그중 3개 eval-only), 900 updates — 학습 step은 Phase 6 대비 −25%, unit당 eval battery(M 120 + phase7 600 + generation 20)는 동등하다. v0.2가 v0.1의 R cap 150 min을 120 min으로 오히려 줄였지만, 1,200 updates 실측 82 min 대비 900 updates + 3 eval-only units은 120 min 내에 충분히 들어온다.
  - D0 ≤15 min: Phase 6 D0 cap(v1.0.11 §11.2 ≤15 min)과 동일한 build×4 + probe + assert workload — 현실적. D1 ≤25 min: Phase 6 D1 ≤20 min(§11.3)보다 5분 여유이고 battery는 동일(E00을 eval-only로 고치면 1 update만큼 더 여유) — 현실적. CPU 6 threads는 v1.0.11 §11.1과 동일한 선언이다.
  - 남는 점: F0에는 T_proj(v1.0.11 §11.5, ≤96 min projection + 120 min hard abort) 대응물이 없다. D1 per-phase timing에서 R wall projection 규칙을 만들 것을 권한다. primary source를 unit-final로 정하면 step0/final 20×5 eval이 R 예산에 추가되며, E00은 step0=final이므로 1회만 실행하면 된다.
- 다음 단계:
  1. D1 timing → R wall projection(T_proj 아날로그) 규칙 추가.
  2. primary source 확정 후 Stage R 예산 표에 signal eval 행 추가(E00 1회).
  3. cap 초과 시 no-retry/no-extension 유지 명시.

## Q6. H3 separation

- 판정: **agree**
- 근거:
  - cause report §5가 남긴 미분리 원인(LayerNorm/input-insensitive mapping vs optimization interference vs decoder off-manifold; "Adapter는 512→512이며 width bottleneck이 아님")을 겨냥한 arms(E01-LN fixed LayerNorm / E01-P fixed orthogonal projection / E01-R residual `x + Adapter(x)`)를 v0.2 §7이 primary 2×2 밖 별도 prereg로 분리하고 "No H3 execution in this plan"으로 잠근 것은 정확하다. 이 arms를 primary에 넣으면 (a) 유일한 clean contrast(E01 vs E11)가 무너지고, (b) units/compute가 배증하며, (c) "adapter 유무" 질문과 "원인 메커니즘" 질문이 섞인다. primary에 LN/projection을 넣을 근거는 없다.
  - §5 분기 1이 E01+/E11−일 때 H3를 다음 진단으로 지정해 H3 prereg의 트리거가 사실상 사전 등록돼 있다.
  - H3 prereg 작성 시 요구: E01-R identity 보존 assert(draft synthesis MF-5 잔여), E01-P 직교성/초기화 검증, "H3 양성이 adapter 구조를 유일하게 확정하지 않음" 해석 상한.
- 다음 단계:
  1. H3 prereg에 E01-R identity 보존 검증과 E01-P 직교성 검증 포함.
  2. H3 트리거(E01+/E11−) 명시 + 본 plan 내 H3 실행 없음 유지.

---

## 최종 판정 블록

```text
Q1. 판정: agree (conditional) — mechanics-only D gate + 무조건 3-seed R로 MF-2 selection bias 제거 확인.
    D1 유지(필요), 단 E00-in-D1 모순 수정 + mechanics-pass 술어 열거 필요.
Q2. 판정: agree (conditional) — E01 vs E11 유효, 단 adapter-as-configured 명시 + decision algebra 정의 필요.
Q3. 판정: agree — route-scoped STOP로 MF-1 모순 해소. "route as configured" 정의 + E01+/E11+ 다음 단계 보강.
Q4. 판정: agree (conditional) — M 120/cell 비게이트 설계 타당. primary record source 지정 + NA 규칙 상속 필요.
Q5. 판정: agree — 900 updates ≤120 min은 실측(Phase 6 1,200 updates = 82 min) 대비 현실적. T_proj 아날로그 권장.
Q6. 판정: agree — H3 별도 prereg 정답. primary에 LN/projection 불필요.

최종 판정: NARROW
Stage D/R: agree — Stage D는 mechanics-only로 재정의됐고 R은 signal-free 진입. D1 유지, E00 수정, pass 술어 열거.
2×2: conditional — E01 vs E11 primary 유효(adapter-as-configured 해석). 술어/CI/NA 정의가 전제.
Interpretation: agree — track STOP 삭제·route 한정 확인. scope 정의와 E01+/E11+ 분기 보강.
M/signal: conditional — M 비게이트 유지. primary record source가 미지정이면 값이 달라질 수 있음(Phase 6 −0.1135 vs −0.0407 전례).
Compute: agree — D0 15 + D1 25 + R 120 min, 900 updates, 6 threads 현실적. projection 규칙 권장.
H3: agree — 별도 prereg. E01-R identity 검증을 H3 prereg로.
```

## Must-fix (ranked)

1. **MF-A — primary endpoint 술어/소스 미지정 (Stage R 승인의 전제)**
   v0.2 §5가 분기 라벨(E01 positive / E11 negative / E01−E11 >0)만 두고 술어를 정식화하지 않았다. 요구: (i) E01_SIGNAL/E11_SIGNAL을 prereg §3.5 형식으로 재기술(copy mean ≥ .05, CI lower >0, 2/3 seeds >0; full mean >0, CI lower >0, 2/3 seeds >0), (ii) paired contrast E01−E11에 대한 CI 규칙(최소한 CI lower >0 권장 — mean >0만으로는 분기 1이 발동된다), (iii) "E01 ≈ E11" 연산적 정의, (iv) missing seed → NA / no 2-of-available / no 15→14 상속. 아울러 §4 Stage R에 step0/final donor-crop signal eval 행이 없는데 §3은 signal을 "20 val docs, 5 donors"로 정의한다. primary delta가 phase7 records에서 오는지 unit-final eval에서 오는지 명시하라 — Phase 6에서 두 소스가 −0.1135 vs −0.0407로 갈렸던 전례(results synthesis §4 GLM)가 있다.
2. **MF-B — Stage D1 E00 모순 (코드로 검증된 결함)**
   §4 "4 cells, 1 update" + §9 표 "D1 | 4 | 4"는 §2(E00 updates=0)·§6("E00 is a baseline")과 모순이고, 코드상 E00형 셀(.adapter 없음, .lora_ 없음)은 `optimizer_for`(runner L367–375)가 `no trainable parameters` RuntimeError를 발생시켜 1 update가 기계적으로 불가능하다. 수정: D1 = E10/E01/E11 ×1 update(합계 3) + E00 0-update eval-only, §9 표 정정.
3. **MF-C — D0 assert 오탈자 + mechanics-pass 술어 열거**
   §4 D0 "assert LoRA modules 0/0/64/64; adapter absent/present/present" — adapter 값이 3개뿐이다(E00/E10/E01/E11 4셀 기준 absent/present/absent/present여야 함). 또한 D0/D1 pass 술어를 assert 목록으로 열거해 D→R gate를 재량 없는 기계 판정으로 고정하고, D1 실패 시 허용되는 것은 코드 수리 + D1 재실행뿐임을 명문화하라.
4. **MF-D — compute projection 규칙 + signal eval 예산**
   F0용 T_proj 아날로그(D1 per-phase timing → R wall projection, hard abort 유지)와, primary source 확정 시의 step0/final 20×5 eval 예산(E00은 step0=final이므로 1회)을 Stage R 표에 반영하라.
5. **MF-E — interpretation wording**
   (a) "route as configured" 연산적 정의, (b) E01+/E11+ 분기의 다음 단계(replication/anomaly, 별도 prereg) 복원, (c) F0 결과의 non-retroactivity(Phase 6 negative 종료·B0-B 미승인 상태 불변) 명시.

## 잘못된 전제

- D1이 E00에 optimizer step을 수행할 수 있다는 전제 — 코드상 불가능(`optimizer_for` RuntimeError, runner L367–375).
- phase7 records와 unit-final donor-crop signal eval이 교환 가능한 소스라는 암묵적 전제 — Phase 6에서 −0.0407 vs −0.1135로 문서화된 불일치가 있다.
- "adapter 유무만이 다르다"는 전제 — E01 vs E11은 +526,336 params, adapter_lr 10×(1e-3 vs 1e-4), LoRA-init RNG stream(prereg §2.7 seed→adapter→LoRA no-reseed)까지 함께 다르다. 결론은 adapter-as-configured에 한정된다.
- "mechanics pass"가 자명하다는 전제 — 술어가 열거되지 않으면 그것은 기계 판정이 아니라 재량이다.

---

## 상태

```text
Reviewed HEAD: 185d2ff7b2c29aaa10093838335cb15901981657
판정: NARROW (must-fix MF-A~MF-E; 신규 과학적 선택 금지)
F0 v0.2 = 미승인·미실행 유지
test 163 sealed / P1 unused / T5Gemma2 D-108 STOP
```