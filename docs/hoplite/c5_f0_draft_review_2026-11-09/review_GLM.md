# C5 F0 Draft Prereg — Independent Review (GLM 5.3 Flash)

- 작성일: 2026-11-09
- 모델: `z-ai/glm-5.3-flash`. **새 독립 검토 스레드**이며 기존 Phase 6/Results 스레드의 후속이 아니고, 어떤 선결론도 상속하지 않았다. 지정 7개 파일을 직접 읽었고, 인용 조항은 `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`와 `runner/c5_pm_phase6.py`에서 직접 대조했다. 서브에이전트/추가 LLM 미사용.
- **reviewed HEAD: `68957bdc711acb8462cb9959e2c85b5299e65fd8`** ("docs: add C5 F0 draft review request", 2026-11-09T23:42:06+09:00). 동기화: `git fetch origin` → `git pull --ff-only origin main` → **"Already up to date"** (작업트리 clean). 요청서가 기재한 초안 작성 기준 `244b25c`는 이 HEAD 이전 커밋이다.
- **필수 verbatim 인용: adapter-associated signal loss** — cause report §5가 "bottleneck"을 한정한 표현이며, 본 검토의 중심 질문(F0가 이 관찰을 native 경로에서 EG2 경로로 확장할 수 있는가)의 기준선이다.
- 범위 준수: 순수 desk review. 학습·평가 실행 없음(모델 forward 없음, 수치 재계산 없음 — 인용 수치는 전부 지정 보고서/plan 원문), test 163 미개봉, P1 미사용. 파일 수정은 지정 report 1개뿐.
- 검토 대상 상태: **F0 DRAFT — 미승인, 미실행** (plan 헤더). 본 보고서는 승인이 아니라 초안에 대한 자문이며, F0 실행을 승인하지 않는다.

---

## Q1. 2×2 정합성

- 판정: **conditional agree** — 1차 대비(E01 vs E11)는 유효하고 prereg의 질문("LoRA를 고정한 상태에서 adapter 유무가 EG2 donor-specific signal을 바꾸는가", plan §0)에 정확히 대응한다. 그러나 "2×2"라는 명칭이 설계 성격을 과장하고, adapter 인자 내부 confound가 남는다.
- 근거:
  - **1차 대비의 유효성** (plan §2, §2.1): E01/E11은 (i) 동일 memory(EG2 raw 753×512), (ii) 동일 decoder LoRA(64 modules, r8 alpha16 dropout .05, `lora_lr=1e-4`), (iii) 동일 100 updates/optimizer(AdamW, wd .01, clip 1.0, batch 1, `train20_ids[step % 20]`)를 공유하고 adapter 유무만 다르다. v1.0.11 §2.5.4의 `lora_B` zeros 초기화 때문에 step-0 LoRA 출력은 0 — 초기 decoder 입력은 E01=raw h, E11=Adapter(h) — 즉 초기점의 유일한 차이가 adapter transform이고, LoRA 부분의 초기 함수는 동일하다.
  - **donor pairing 강점**: F0 4 cell은 모두 EG2 h_len 기준 donor 규칙(v1.0.11 §2.5.6)을 공유하고 plan §3도 "E01/E11 use the same donor lists as Phase 6 F/L"로 명시하므로, cell 간 대비가 문서·donor 쌍에서 완전히 paired다. Phase 6의 F/L(753) vs P/PA(512)가 가졌던 donor/길이 불일치가 F0 내부에는 없다.
  - **한계 1 — incomplete factorial**: (adapter=none, LoRA=none) corner의 학습 cell은 구조적으로 만들 수 없다 — adapter와 LoRA가 유일한 학습 대상이고 base decoder는 frozen이므로(v1.0.11 §2.5.4), 이 corner는 0-update일 수밖에 없다(E00). 따라서 이것은 "구성요소 추가" 설계이지 학습된 2×2 factorial이 아니며, LoRA 주효과는 E11−E10(둘 다 학습, adapter 공유)으로만, adapter 주효과는 E10−E00인데 여기엔 0 vs 100 updates confound가 있다(plan §2가 스스로 경고). 명칭과 해석을 이 성격에 맞춰야 한다.
  - **한계 2 — adapter 인자 내부 confound**: E11−E01은 adapter "존재"와 함께 +526,336 params(2×(512×512+512)+1,024 affine), `adapter_lr=1e-3`(lora_lr의 10×), 출력단 LayerNorm(v1.0.11 §2.5.4: Linear→GELU→Linear→LayerNorm), joint 최적화 간섭을 묶는다. 이는 plan §0이 P vs PA에 대해 인정한 confound 2번과 동일 유형이며, F0 1차 대비도 이를 제거하지 못한다 — 제거는 H3/capacity·LR-matched 변형의 몫이다.
  - **한계 3 — E10≡F, E11≡L**: E10(EG2+adapter, no LoRA, 100 updates)과 E11(EG2+adapter+LoRA, 100 updates)은 v1.0.11 §2.1/§2.2 하의 Phase 6 F/L과 config가 동일하다. plan은 이 identity를 명시하지 않는다. Stage R 12 units 중 6 units는 사실상 replication이고 새 정보는 E01(+E00 probe)에 집중된다. 재실행이면 F0 driver 검증 축(F M Δ 0.576 대비, L copy mean −0.1135 대비)이 되고, 재사용이면 Stage R 학습이 9→3 units로 준다. 어느 쪽인지 prereg가 정해야 한다.
  - **RNG 미세점**: RNG 순서가 seed→adapter→LoRA(v1.0.11 §2.7, runner `build_arm`)라서 E01과 E11의 LoRA `lora_A` 초기값은 서로 다르다(B=0이라 초기 함수는 동일, 궤적만 다름). "LoRA fixed"의 의미를 문서로 고정하라.
- 다음 단계: (1) §2에 E10≡F/E11≡L 명기 및 재실행 vs 재사용 결정(재실행 시 학습 재현성 manifest 부재(MF-6)로 bit-level 일치는 기대 불가임을 명시). (2) "LoRA fixed"의 정의 문장 추가(config 동일, A-init draw는 상이). (3) H3의 frozen random adapter(학습 없는 전체 구조 null)를 후보로 기록 — E01-LN은 LayerNorm 연산만 대체한다.

## Q2. Stage D decision/selection bias

- 판정: **conditional agree** — 1-seed screen의 방향은 맞고, 등록 seed를 쓰지 않은 것(20261111, debug seed; Stage R은 20261108/09/10)은 seed-shopping을 원천 차단한다. 다만 크기 하한이 없어 과하게 관대하며, Stage R 판독 규칙이 미정의라 조건부 진입의 후속 절차가 비어 있다.
- 근거:
  - **규칙**(§8): `E01 copy mean delta > 0 AND E01−E11 paired copy mean > 0 AND both endpoints finite on 15 common` — 통과 시에만 Stage R. 실패 시 STOP F0, no 3-seed, no threshold change.
  - **관대한 점**: mean > 0에 크기 하한이 없다. E01 copy mean +0.005도 통과하며, 그런 결과는 Stage R에서 동결 술어(plan §3.1: mean ≥ .05, CI lower >0, 2/3 seeds)를 절대 만족 못 하므로 150 min을 소모할 확정된 실패에 불과하다. Stage D가 descriptive라 해도 "진입 판정"인 이상 descriptive 크기 하한(예: E01 mean ≥ .02~.05)을 신규 prereg 설계 권한 안에서 넣는 것이 바람직하다 — 이는 v1.0.11 threshold 변경이 아니라 새 screen 조건이다.
  - **엄격성/위음성**: 15-doc 단일 seed 평균의 요동은 작지 않다. 같은 L arm에서 15-doc 평균 −0.1135 vs 20-doc 평균 −0.0222(synthesis §4 DS) — cohort/seed 요동이 threshold .05와 같은 크기다. 진 효과가 .05 미만인 E01은 Stage D에서 noise로 탈락할 수 있다. diagnostic screen으로 specificity 우선이면 수용 가능하나, Stage D 실패가 최종이며 재시도/seed 추가가 없음을 §8 Stage D 항목에도 명문화해 사후 재량을 차단해야 한다.
  - **selection bias의 성격**: Stage R은 조건부 진입이므로 winner's curse가 있다(통과한 방향만 3-seed를 얻음). 그러나 최종 증거는 Stage R의 사전 동결 술어이고, B0-B/후속 자동 진행은 non-goals(plan §9)라 하류 오염이 없다. 남는 것은 compute 배분과 서사 forking뿐이며, 이는 screen의 존재 이유(Stage D ≤45 min vs Stage R ≤150 min, §5)에 비춰 수용 가능하다.
  - **"Stage R을 항상 3-seed로 해야 하는가"**: 아니오 — Stage D의 목적이 compute 절약인 이상 조건부가 맞다. 다만 대안(무조건 3-seed, +105 min)도 합리적이므로, 현재 안을 유지하려면 아래 1번(판독 규칙 사전 등록)이 필수다.
- 다음 단계: (1) **Stage R 판독 규칙 사전 등록**(최대 빈틈 — §3.1은 E01 술어만 있고 E11 술어, E01−E11 대비 CI 술어, 결과→결론 분기표가 없다. §8의 분기 문안은 Stage D 점 추정 기준이다). (2) Stage D 진입에 descriptive 크기 하한 추가. (3) Stage D 실패의 최종성(no retry, no seed addition) 명시.

## Q3. H3 LN/projection/residual

- 판정: **conditional agree** — primary 분리(plan §1 "이 arms는 H3이며 primary 2×2와 분리한다")는 정확하다. 그러나 (a) E01-R은 지금 문안으로는 identity-preserving이 아니고, (b) H3는 LN 원인 분리를 절반만 달성하며, (c) 세 arm의 생성 규칙이 미지정이다.
- 근거:
  - **E01-LN** (raw EG2 + fixed LayerNorm, no learned adapter): adapter의 마지막 연산이 LayerNorm이라는 점에서 "출력 정규화가 donor-specific 성분을 죽인다" 가설(cause §5, DS 지적)을 가장 직접 시험한다. 학습 불필요(eval-only, 비용 수 분). 단, E11의 LN은 학습된 transform 뒤에 적용되므로 "raw h에 대한 LN"과 "adapter 출력에 대한 LN"은 다른 대상 — E01-LN 생존 → LN-on-raw는 원인이 아님(용의자는 학습된 transform), E01-LN 소실 → 정규화가 강력 용의자. **partial isolation**이며 완전 분리는 E11-side ablation(final LayerNorm 제거/교체, 동일 budget)이 필요 — 별도 prereg 후보.
  - **E01-P** (fixed orthogonal projection, no training): 기하 보존 변형 시험. 생존 시 원인은 학습-특이적, 소실 시 decoder가 입력 basis 자체에 민감(off-manifold/alignment 방증). 단 "orthogonal projection"의 생성 규칙(난수 orthogonal, QR, seed)과 512→512 full-rank 여부를 지정해야 재현 가능하다. eval-only.
  - **E01-R** (residual adapter): **지금 문안 `x + Adapter(x)`는 초기점에서 identity를 보존하지 않는다.** Adapter 출력은 final LayerNorm을 통과하므로 per-dim RMS ≈ 1(affine 포함) 수준이고, raw EG2 h의 scale과 무관하게 초기부터 입력을 유의미하게 바꾼다. cause §6의 원형은 `x + α·Adapter(x)`로 identity 보존이었는데 F0 §1 H3가 α를 떨어뜨리며 spec이 후퇴했다. 수정: `x + α·Adapter(x)`, α init 0(학습 가능) 또는 fixed α 명시. 이 arm은 학습이 필요한 유일한 H3 arm이며 LoRA 포함 여부·updates·LR도 미지정 — E11과 비교하려면 LoRA를 포함해야 하고, 그러면 이름도 E01-R(=no adapter 계열)이 아니라 E11-R 계열이어야 한다. LoRA 없이 두면 L−F≈0(−0.0026, 8/15; cause §2)에 근거한 LoRA 무관성 가정에 기대게 된다.
  - **primary 포함 여부**: 포함하지 말 것 — primary는 "adapter 유무", H3는 메커니즘 질문이고 섞으면 multiplicity와 해석이 오염된다. 대신 eval-only인 E01-LN/E01-P는 Stage D에 descriptive로 태울 수 있다(§5 Stage D 산출물에 추가, 비용 극소). E01-R(수정 후)은 별도 소형 prereg 또는 Stage R 통과 후 조건부.
  - **H3 술어 부재**: H3 arm의 판정 규칙이 없다. descriptive readout(mean delta, E01 대비 paired mean)만 사전 등록하고 gate를 만들지 말 것. H3 arm이 plan §3/§4의 cohort/donor/M/signal 정의를 그대로 상속한다는 문장도 필요하다.
- 다음 단계: (1) E01-R을 `x + α·Adapter(x)`, α init 0으로 수정하고 이름(E11-R 계열)/LoRA/updates/LR 명시. (2) E01-LN affine 처리(affine=false vs frozen random affine)와 E01-P 생성 규칙 지정; H3의 §3/§4 정의 상속 명문화. (3) E01-LN/E01-P를 Stage D descriptive로 포함, E11-side LN ablation은 별도 prereg 후보로 기록.

## Q4. M/signal and E00 baseline

- 판정: **agree** — M과 signal의 역할 분리, M_PASS 비-gate, E00 eval-only 배치 모두 적절하다. 보완은 경미하다.
- 근거:
  - **분리의 적절성**: M은 `control(M_POS_MEAN/M_NORM) − real`, 즉 global-mean 대비 calibration이고 donor specificity를 요구하지 않는다(v1.0.11 §9.2–§9.6, cause §1/§5). Phase 6이 실증했다: F/L/PA는 M_PASS true(Δ 0.576/0.365/0.576)이지만 signal-cohort wrong−real은 −0.017(실제로 real이 더 나쁨), L_COPY_SIGNAL −0.1135 false; P만 wrong−real +2.531, signal 3.076. 따라서 F0의 증거 하중은 signal endpoint가 지고 M은 validity/calibration 보조로 남는 위계가 올바르다. F0 §3.2는 M_PASS를 secondary로만 두고 §8 진입 규칙은 E01/E11 signal endpoint만 본다 — gate 아님, 적절. B0-B 자동 진행도 non-goals(§9).
  - **산수**: 120/cell/seed = 15 common × 2 variants × 2 endpoints × 2 memory kinds(v1.0.11 §9.5의 F/L 패턴과 동일) — Stage D 480, Stage R 1,440(§6) 정확. phase7 600/cell/seed(§9.6.1) → Stage D 2,400, Stage R 7,200 정확. M K=753 전 cell 공통(§3 "no 512 substitution")이라 Phase 6 F/L과 완전 동질, 비교 가능성 유지.
  - **E00 공정성**: E00은 trainable params가 없어 0-update가 구조적으로 강제되며(plan §2 "not a trained control", "Do not interpret E01 vs E10 as clean" 표명), Phase 6 결과 검토에서 요청된 0-update EG2-raw usability probe(synthesis §4 GLM 항목)의 구현이다. 해석 가치: E00 signal > 0이면 raw EG2 h가 학습 없이 donor discrimination을 지원, E00≈0 & E01>0이면 LoRA가 unlock, 둘 다 ≈0이면 H2 영역(alignment/off-manifold 대안은 Q6). §8 해석 트리에 E00 descriptive 참고행 추가 권장.
  - **E00 결정론/중복**: 학습 파라미터가 없어 eval이 결정론적이고 3 seeds는 동일 값 — §7이 "E00 same eval baseline may share hash"를 이미 인지. 1회 평가 + 재사용을 허용하거나 3회 실행 근거를 명시. E00의 M_PASS flag도 이미 수집되는 120 records에서 공짜로 계산되므로 descriptive 출력 권장(raw memory가 global-mean control을 이기는지의 0-update 참고치).
- 다음 단계: (1) E00 M flag를 descriptive 산출물에 추가. (2) §8 트리에 E00 참고 행 추가(비-gating). (3) E00 1회 vs 3회 평가 결정 기록.

## Q5. Compute realism

- 판정: **conditional agree** — 9 trained units 산수는 정확하지만 cap은 Phase 6 blended 단위 시간 기준으로 낙관적이다. 특히 Stage D ≤45 min은 여유가 사실상 없다.
- 근거:
  - **산수 확인**: Stage D = E10/E01/E11 ×100 = 300 updates(§5), Stage R = 4 cells ×3 seeds에서 E00 0 updates + 9 trained ×100 = 900 updates(§5) — "12 units가 아니라 9 trained units + E00 eval-only" 계산은 맞다. checkpoint hash 12 keys(§7)와도 정합. generation/phase7 포함 여부: §5 Stage D 산출물에 "unit JSON, M records, phase7 diagnostic, generation, checkpoints"가 명시되어 cap 포함으로 읽힌다.
  - **기준선과의 격차**: Phase 6 registered는 12 units/1,200 updates/120 min/6 threads(v1.0.11 §11.1) — blended 약 10 min/unit. 그러나 이 평균에는 F/L보다 가벼운 512-class P/PA(M prefix 512 vs 753, phase7 K_d 512 vs ≤753)가 절반 포함되어 있고, F0은 전부 EG2/753-class다. EG2-class를 native-class의 1.3–1.5배로 두면(6e+6n=120 → e≈11.7~13 min/unit) Stage D ≈ 3×e + E00 eval(≈0.6e) + D0-like check + stats ≈ **42–50 min** — 45 min cap은 0~마이너스 여유. Stage R ≈ 9×e + E00 evals + stats ≈ 110–135 min — 150 min 가능하되 여유 작음. (주의: per-arm timing artifact 미커밋(MF-6 — wall/threads는 telemetry)으로 이 추정은 §11.1 aggregate로부터의 보간이며 확증이 아니다.)
  - **재사용 효과**: E10≡F/E11≡L을 재사용하면(Q1) Stage R 학습은 E01 3 units로 줄어 ≈40–55 min — cap이 여유로워진다. 재실행이면 위 추정 그대로.
  - **체계 결손**: Phase 6에는 T_proj ≤96 min(§11.5)과 120-min hard abort(§11.6)가 있었지만 F0 plan에는 T_proj 상당의 사전 타이밍 projection도 cap 초과 시 동작(hard abort, 결과 무효)도 없다 — Stage R의 "no retry; no extension"만 있다.
  - **threads 불일치**: plan §5는 "4–8 threads"인데 요청서 Q5/v1.0.11 §11.1/runner(`torch.set_num_threads(6)`, runner/c5_pm_phase6.py L779)는 6이다. Phase 6 비교 가능성을 위해 6으로 고정 권장 — 4 threads로 돌면 위 추정은 cap을 초과한다.
- 다음 단계: (1) threads 6 고정 + cap 초과 동작(hard abort) 명문화. (2) D1 상당 타이밍으로 T_proj-equivalent를 사전 등록하고 Stage D/R cap 재확인 — draft 단계에서의 cap 조정(예: Stage D ≤60 min)은 허용되지만 승인 후 조정은 금지다. (3) E10/E11 재실행 vs 재사용 결정에 따라 Stage R 산수·cap 갱신.

## Q6. Interpretation boundaries

- 판정: **conditional agree** — §1 H2의 경계 문안은 정확하다("feature 부족과 alignment 부족은 구분되지 않는다", "F0 negative는 트랙 STOP의 충분조건이 아니다"). 그러나 §8이 이와 모순되는 track-level STOP 문구를 갖고 있고, positive 쪽 상한 문안도 보강이 필요하다.
- 근거:
  - **negative 경계의 내부 모순**: §1 H2는 "F0 negative는 트랙 STOP의 충분조건이 아니다"라 명시하는데 §8은 "If E01 negative and E11 negative → EG2 raw feature/alignment insufficient; **stop EG2 resident track**"이라 쓴다. cause §5가 기록했듯 LayerNorm/input-insensitive mapping, optimization interference, decoder off-manifold는 아직 미분리 — F0 negative가 말해 주는 것은 "raw h가 decoder에서 donor-specific하게 안 쓰인다"까지이지 "feature에 정보가 없다"가 아니다. §8 문구를 "stop the EG2-raw→mT5-decoder route as configured" 수준으로 하향하고 track 판단은 별도 결정으로 남겨라.
  - **positive 경계**: F0 positive(E01 signal, E11≈0)는 Phase 6 native 관찰(P copy 3.076 → PA 0.011, paired +3.065, 14/15)을 LoRA 고정 하 EG2로 확장하는 것으로, **adapter-associated signal loss**가 memory source를 넘어 재현된다는 연관 증거를 강화한다. 그러나 adapter 인과 "확정"까지는 아니다 — E01 vs E11은 capacity(+526,336)/LR(10×)/LayerNorm/joint 최적화를 함께 바꾼다(Q1 한계 2). 올바른 상한: "adding the trained adapter changes EG2 donor-specific signal". 메커니즘(구조) 주장은 H3/후속의 몫이다. 참고로 §8의 "E01 positive and E11 positive" 분기(Phase 6 L이 −0.1135였으므로 E11 양성 자체가 이상 신호)와 "E01≈E11" 분기의 route(replication/anomaly 조사, adapter hypothesis 중단)는 합리적이다.
  - **구조적 원인 주장에 필요한 것**(현재 F0에 없음): (a) adapter-side ablation(final LayerNorm 제거/교체, 동일 budget), (b) α-residual(`x + α·Adapter(x)`, α init 0) 대비, (c) capacity/LR-matched adapter 변형, (d) donor-discrimination probe(MF-4 목록), (e) ≥2 memory source 반복, (f) 학습 재현성 manifest(MF-6)로 trajectory noise 배제. F0는 이 중 어느 것도 제공하지 않으며, plan이 H3을 분리해 둔 것은 올바르다 — 다만 해석 절에 "F0 positive가 확정하는 것/하지 않는 것" 요약을 명문화하면 오독이 차단된다.
  - **기타 경계**: n=15 docs, 5 donors, F5-clean val subset — 이 cohort 밖 일반화 없음. generation은 telemetry(gate 아님, v1.0.11 §2.5.7). test 163 sealed, P1 unused. signal population(uncapped donor crop)과 phase7 K_d≤K_M diagnostic population의 이중성은 Phase 6에서 이미 오독 사례(−0.1135 vs −0.0407, synthesis §4 GLM)가 있었으므로 F0 report 템플릿에 population 명시를 의무화할 것.
- 다음 단계: (1) §8 "stop EG2 resident track"을 route-level로 수정(H2 정렬). (2) §1에 F0 positive가 확정하는 것(연관 확장)/하지 않는 것(메커니즘·capacity/LR/LN 분리) 요약 추가. (3) F0 report 템플릿에 signal population 명시 의무화.

---

## 최종 판정

```text
최종 판정: NARROW

F0 2×2: primary contrast(E01 vs E11) 유효 — LoRA 고정 하 adapter 유무의 문서-paired 대비로
  prereg 질문에 정확히 대응. 단 "2×2"는 (none,none) corner가 frozen 규정상 0-update일 수밖에
  없는 component-addition 설계임을 명기할 것. adapter 인자 내부에 capacity(+526,336)/LR(10×)/
  LayerNorm이 묶여 있음을 해석에서 항시 명시. E10≡F/E11≡L identity 문서화 필요.
Stage D: 1-seed screen 유지 가능. 등록 seed 미사용(20261111) 적절. 크기 하한 부재는 관대 —
  descriptive 하한 추가 권장. 실패의 최종성 명문화. Stage R 판독 규칙 사전 등록 필수(현재 미정의).
H3: primary 분리 동의. E01-LN/E01-P(eval-only)는 Stage D descriptive 포함 가능. E01-R은 지금
  문안으로 identity-preserving이 아님 — `x + α·Adapter(x)`, α init 0 필요(cause §6 원형 복원).
  LN 완전 분리는 E11-side ablation(별도 prereg).
M/signal: 120/cell/seed·480/1,440·600/2,400/7,200 산수 정확. M_PASS 비-gate 적절. E00 eval-only
  probe는 이전 리뷰 요청사항의 올바른 구현. E00 M flag descriptive 추가 권장.
Compute: 9 trained units 산수 정확. Stage D 45 min은 Phase 6 blended 10 min/unit 기준으로 여유
  없음(F0은 전부 753-class). threads 6 고정, T_proj-equivalent 사전 등록, cap 초과 동작 필요.
  E10/E11 재사용 시 Stage R 여유.
금지 범위: 승인 전 실행 금지, test 163/P1 금지, threshold/seed/donor/step/LR 변경 금지,
  B0-B/B1/B2/Stage C 자동 진행 금지, native P/PA 재해석을 통한 B0-B 구제 금지 — plan §9/§12 유지.
  본 검토는 F0 실행을 승인하지 않는다.
Must-fix (ranked):
  1. (blocker) Stage R 판독 규칙 미정의 — §3.1 E01 술어는 4 conjunct 중 3개(paired conjunct 누락),
     E11 술어·E01−E11 대비 CI 술어·결과→결론 분기표 부재. §4 "reuse frozen v1.0.11 definitions
     exactly"와의 정합 관계 명문화.
  2. (blocker) §8 "stop EG2 resident track" ↔ §1 H2 "F0 negative는 트랙 STOP의 충분조건이 아니다"
     모순 해소(route-level stop으로 하향).
  3. E01-R spec: `x + α·Adapter(x)`, α init 0; 이름(E11-R 계열)/LoRA/updates/LR 지정; E01-LN affine
     처리, E01-P 생성 규칙(seed/QR); H3의 §3/§4 정의 상속 명시; H3 술어는 descriptive만.
  4. E10≡F/E11≡L 명기 및 재실행/재사용 결정(재실행 시 일치 기대 범위 명시 — 학습 재현성 manifest
     부재로 bit 일치 불가, 재사용 시 Stage R 9→3 units).
  5. Compute: threads 6 고정, T_proj-equivalent 사전 등록, cap 초과 hard abort, Stage D cap 재검토
     (draft 단계에서만 허용).
  6. draft 잔여물 제거: §6 "M 480? Wait", "1,680? EG2 only", §2.1 "source max 512?" — freeze 전 정리;
     §2.1의 prefix/source-max 문장은 memory-direct EG2 arm에서 오해 소지.
  7. (low) "LoRA fixed"의 RNG 정의, E00 M flag, E00 1회/3회 평가, §3 tail arm 표기("E01/E11") 명확화.
잘못된 전제:
  - "2×2"가 완결 factorial이라는 암시 — (none,none) 학습 corner는 존재 불가(adapter/LoRA가 유일한
    학습 대상), E10−E00은 update confound를 안는다(스스로 경고하긴 함).
  - Stage D 통과 후 해석 규칙이 이미 존재한다는 암시 — Stage R 술어 체계는 실제로 미완성.
  - F0 unit 비용 ≈ Phase 6 blended 단위 비용이라는 암시 — 512-class unit이 없어 과소추정 경향.
  - §8의 track-STOP 문구 — H2 자체 경계와 모순.
```

---

*본 보고서는 자문(review)이며 새 실험의 승인이 아니다. F0는 수정·재검토 후 별도 승인 절차를 거쳐야 한다. 인용 수치의 출처: `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_B0A_PM_PHASE6_LABELS_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_f0_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py` (reviewed HEAD `68957bd`).*