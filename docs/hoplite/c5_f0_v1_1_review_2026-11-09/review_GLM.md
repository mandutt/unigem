# C5 F0 v1.1 — New Block Round 1/10 Review (GLM)

- 작성일: 2026-11-10
- 검토 대상: `docs/plan_c5_f0_v1_1_2026-11-09.md` (DRAFT v1.1)
- **reviewed HEAD: `af0fa3ec374ab5cb20c9823485c78f2bd47c45d2`** ("docs: add C5 F0 v1.1 review request")
- 동기화: `git fetch origin` + `git pull --ff-only origin main` → "Already up to date.", HEAD = `af0fa3e…` (커밋 시점 이후 변경 없음)
- 모델: `z-ai/glm-5.3-flash` (신규 독립 스레드, 새 10라운드 블록 round 1, v1.0 결론 미상속)
- 방법: 지정 문서 8종 + `runner/c5_pm_phase6.py` + `runner/c5_pm_stats.py` + `runner/c5_pm_gate.py` + `docs/decisions.md`(D-156) + `reports/provenance/C5_b0a/labels/labels.json` 대조 열람. **학습/평가 실행 없음, test 163/P1 미사용, subagent 없음, repository 수정 없음 (이 파일 1개만 작성).**

---

## 0. Verbatim paired E01−E11 (대상 문서에서 그대로 인용)

v1.1 §2 Cells 표 (L60-65), E01/E11 행:

```text
| E01 (F0) | EG2 raw | none | 64 modules | 100 | adapter-free + LoRA |
| E11 (L) | EG2 raw | trained | 64 modules | 100 | adapter + LoRA |
```

v1.1 §6.3 Primary contrast (L211-215, 전문):

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
```

v1.1 §6.3 불릿 (L217-221, 전문):

```text
- Primary positive: `mean_D > 0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0`.
- `D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary.
- Copy primary; full secondary.
- **CI_D is doc-level only.** Seed-level `D_s` is a gate/descriptor, not a doc-level interval.
- `PASS_POSITIVE` requires the paired contrast, E01 absolute copy signal, and seed replication; this is not a per-cell significance conjunction.
```

---

## Q1. Init — **conditional agree**

근거 (긍정):

- §4 L88-97 pseudocode: `torch.manual_seed(seed)` → adapter → `torch.manual_seed(seed ^ 0x5EED10A5)` ("always, adapter-independent") → LoRA attach. 커밋된 Phase 6 `build_arm`(`runner/c5_pm_phase6.py:142-155`, "RNG order: seed, adapter, then LoRA" — 재시드 없음)과 의도적으로 다르며, 어댑터가 RNG를 소비해도 LoRA init이 E01/E11에서 구조적으로 동일해진다. §4 L114 "F0 E11 ≠ Phase 6 L at init" 선언과 정합.
- §4 assertions 1-8 (L105-112): `lora_names` 64 동일, LoRA A/B sha256 동일, adapter sha256 E10==E11, post-init/post-step0 RNG hash 동일, `lora_B` zero 별도 assert(6), 셀별 부재 assert(7), base/cache/label freeze hash(8). L104 "per registered seed" → 3 registered seed 전부 적용 (v1.0 DS MF-5의 "all three seeds" 해소).
- Per-step reseed (L94-96, L103): 모든 셀 동일 `step_seed(seed, step)` → dropout RNG structural 동일. "not merely assumed" 표현 정확.

남는 문제:

1. **§0 L36이 약속한 항목 3개가 §4 본문에 없다.** (a) "step_seed golden table" — 본문에는 L95 수식만 있고 golden vector/golden test 없음. 또한 L95 `seed ^ (0x9E3779B9 * (step+1)) & 0xffffffff`는 Python 우선순위(`&` > `^`)상 `seed ^ ((MUL*(step+1)) & 0xffffffff)`로 해석되지만 문면 모호 — golden 값으로 고정 필요. (b) "post-step0 weight non-equality" — assertions 1-8에 부재 (init 동일성만 검증, 학습 진행 sanity 없음). (c) "tensor/RNG serialization" — L113은 `init_hashes.json` 문자열 digest 규격일 뿐, `sha256(lora_A/lora_B)`/`sha256(adapter)`의 텐서 직렬화 규격이 없다. prereg v1.0.11 §12.1 프레임 포맷(name_len|dtype|shape|nbytes|bytes, SHA-256)을 인용해 pin해야 한다. 이 3개는 v1.0 round 10 GLM must-fix 2·3과 동일 항목으로 **v1.1에서도 해소되지 않았다.**
2. L96 "before each forward" 범위 미정의: train forward만인지 step0/final/donor-crop eval forward까지인지.
3. assertion 5의 "post_step0" 시점 미정의: step0 diagnostic eval 이후인지 첫 optimizer step 이후인지.
4. L114 "F0 E11 ≠ Phase 6 L at init"은 서술이지 assert가 아니다 (v1.0 DS MF-5가 I-O provenance assert로 교체 요구). F0 init hash와 Phase 6 L init hash lineage를 비교하는 recorded assert가 필요.

다음 단계: (1) 구현 commit에서 §4에 golden table(등록 seed 3종 × step 0/1 기대값)+precedence 명시, (2) post-step0 weight non-equality assert 추가, (3) 텐서 hash에 prereg §12.1 프레임 포맷 인용 + reseed forward 범위/post_step0 시점 한 문장 고정 + Phase6-L 대비 I-O assert — 전부 D0 전 구현 commit 게이트(§11 L347)에서 강제 가능.

## Q2. D1 — **conditional agree (계약은 올바르나 봉쇄 경로 3개 남음)**

근거 (긍정):

- v1.0 blocker(DS-1)의 핵심 모순 해소: v1.0 L153 "3 trained checkpoints exist" → v1.1 L154 "checkpoint digest recorded then checkpoint deleted; `checkpoint_absent == true`; no loading". L166 "stronger than a seal: the values are never materialized in D1" 방향 전환.
- `eval_arm_d1` 재사용 금지(§11 L343)는 실제 코드로 정당화된다: 커밋된 `runner/c5_pm_phase6.py:429-489`는 per-doc `delta_shuffled_copy/full`(L470-476)과 `per_doc` dict(L466-476)를 materialize하고, 비복사 문서를 무음 drop한다(L459-465 `if not real_copy: continue`). 별도 mechanics evaluator가 맞다.
- phase7 차단: assertion 6 (L151, "phase7 records == 0") + 커밋된 `run_d1`(`c5_pm_phase6.py:813-821`)이 실제로 D1에서 phase7을 썼다는 사실과 대비되는 정확한 차단.
- exact-key allowlist(L160) + `d1_report.json` 금지 경로/`d1_sealed/` 부재(L161) + gate negative test(L162) + §13 L392 재확인.

남는 문제:

1. **"does not compute"(L159)은 자기모순적이다.** assertion 4(`n_docs_step0==20`, `n_docs_final==20`)·5(M 480 counts)·7(generation 80)를 산출하려면 mechanics evaluator는 per-doc CE를 필연적으로 계산해야 하고, delta는 메모리에 이미 있는 두 값의 차감일 뿐이다. 강제 가능한 계약은 "영구 저장 없음 + digest-only checkpoint"이며 L166의 framing이 정확하다. L159를 "does not compute"→"does not persist"로 재작성 필요.
2. **D1 파일셋 allowlist 미흡.** allowlist가 `d1_mechanics.json` 내용만 규정한다. 커밋된 Phase 6 `run_d1`은 `d1_partial.json`(L851)을 추가로 쓴다. F0도 부분 상태 파일을 쓸 가능성이 있으므로 "D1이 `reports/provenance/C5_f0/d1/` 아래 생성 가능한 파일은 `f0_d1_mechanics.json` 정확히 1개"라는 경로 수준 allowlist + filesystem negative test를 §5/§11에 명시해야 한다 (v1.0 DS-1이 요구한 "full denylist including `d1_partial.json`"의 잔여).
3. **부수 유출 경로 2개.** (a) assertion 8 NaN 검사 등 실패 메시지에 endpoint 값이 포함될 수 있다 → 오류 메시지/stdout에 CE·delta 값 포함 금지 규정 필요. (b) checkpoint 저장(L154 digest 기록)과 삭제 사이 crash 시 oracle이 디스크에 남는다 → 실패 경로에서도 delete+absent assert가 실행됨을 명시 (rerun D1이 이미 규정되므로 정리 규정만 추가).

다음 단계: (1) L159 표현 수정, (2) D1 경로 allowlist + 실패 메시지/stdout 규칙 + crash-path cleanup assert 추가 — 구현 commit에서 D1 승인 전 해소.

## Q3. STOP/MDE — **conditional agree (산술 검증됨, §6.5 잔존 오류)**

근거 (긍정):

- 4-state table(§7 L287-292) 상호배타·전체 포괄 확인: 평가 순서 고정, INDETERMINATE가 여집합. PASS(`lower > +.05`)와 EQUIVALENT(`lower ≥ −.05 AND upper ≤ +.05`)는 disjoint — `lower > .05`면 `upper ≥ lower > .05`이므로 EQUIVALENT 불가. harm/benefit도 동시 성립 불가(`lower>0` ⇒ `upper>0`; `upper<0` ⇒ `lower<0`). ALL_FAIL+CI 위치 4분할(EQUIVALENT/harm/benefit/기타)은 전체 포괄이고 reason enum(L296-299)이 정합.
- **MDE 산술 검증.** 유일한 커밋된 paired 근거는 `reports/provenance/C5_b0a/labels/labels.json` L_COPY_SIGNAL.paired: mean −0.002639355, CI [−0.040844837, +0.034302208], n=15, n_boot=1000, seed 20261109. half-width = (0.034302208+0.040844837)/2 = **0.037573** ✓, SE = 0.037573/1.96 = **0.019170** ✓. PASS 역치: 0.05 + 1.96×0.019170 = **0.087573 ≈ 0.0876** ✓ (§0 L30, §12 L367). 80% MDE: (z_.975+z_.8)×SE = 2.8016×0.019170 = **0.0537 ≈ 0.054** ✓. v1.0의 .166/.216(단일군 SE 0.059419 = 0.116462/1.96 기반) 제거 확인 — DS-3 해소.
- v1.0 → v1.1 비교: §0 L21-23(§6.5 rewrite 약속)과 §12 L367 "report realized CI_D half-width" 존재.

남는 문제:

1. **§6.5 L245이 여전히 단일군 근거에 기생한다.** "Phase 6 L half-width ≈0.117 ... EQUIVALENT and ROUTE_STOP may be rare; plain INDETERMINATE is the expected dominant null outcome". (a) paired half-width .037573 기준으로는 EQUIVALENT 도달역이 mean ∈ (−.0124, +.0124)로 충분히 도달 가능하다 — §0/§12의 paired 수치와 §6.5의 0.117 서술이 문서 내부에서 충돌 (v1.0 DS의 "cannot have it both ways"가 v1.1에서도 미해소). (b) 기대결과의 base rate 오류: 15-common cohort에서 Phase 6 F −0.11087 / L −0.11351이므로 E11 FAIL은 사실상 기정사실이고 ALL_FAIL→ROUTE_STOP이 INDETERMINATE보다 우세한 분기다. DS가 v1.0에서 지적하고 v1.1이 미수정한 문장.
2. **MDE proxy의 정체 미선언.** 0.019170은 F−L(=adapter 하에서 LoRA 효과) paired SE이며, D=E01−E11(=LoRA matched 하에서 adapter 효과)은 다른 대비다. 가장 가까운 adapter-효과 paired 유사체는 P−PA(native, +3.065, 14/15 positive — cause report §2)로 per-doc 산포가 F−L보다 훨씬 클 가능성이 높다. 즉 proxy가 D의 SE를 과소추정(과다 power 표시)할 수 있다. §12의 realized half-width 보고(L367)가 부분 완충이지만, proxy 전이 가정과 방향 편의를 §12에 한 문장 선언해야 한다. 이는 STOP 로직 자체는 바꾸지 않는다 — ROUTE_STOP은 cell-level FAIL 기반이고 PASS는 realized CI로 판정되므로.

다음 단계: (1) §6.5를 paired half-width 기준으로 재작성 + 기대분기 수정(ROUTE_STOP 우세), (2) §12에 proxy 출처(labels.json paired, F−L, n_boot=1000)와 전이 가정 명시 — prereg 문서 수정으로 D0 승인 전 해소.

## Q4. Cohort — **conditional agree**

근거 (긍정):

- DS-2 해소: §6.1 L187 "primary estimand is 15 length-eligible docs + fixed donor graph", L188 length-selection(5/20 제외) 자기선언, L189 "Generalization to the 20-doc val population is forbidden; report 20-doc F/L descriptively", L190 donor 재사용 선언 + donor-cluster sensitivity.
- 결측 규율: L191 presence check, L192 정확히 5 donors·전 셀 donor set 동일, L193 3/3 seed, L194 `eval_arm_d1` 무음 drop을 전제로 "a missing doc means `NOT_EVALUABLE`, never a smaller cohort", L251-252 15→14 대체 금지. 커밋 코드의 drop 동작(`c5_pm_phase6.py:459-465`)과 정확히 대응.
- DS-6 해소: L195 n_boot=10000 + L214 explicit override (`N_BOOT=1000`은 `runner/c5_pm_stats.py:15` 실재, labels.json의 과거 paired n_boot=1000 기록과 부합) + assert.

남는 문제:

1. **donor-cluster sensitivity 방법 미정의 (L190).** donor-cluster bootstrap인지 leave-one-donor-out 재계산인지, 어떤 수치를 보고하는지 한 문장이라도 pin 필요. 없으면 사후 재량이 남는다.
2. **fixed donor graph의 출처 미 pin.** 커밋 코드는 `donors_for(val_ids, cache)`로 **val 20 전체**에서 donor를 만든다(`c5_pm_phase6.py:801, 905-907`) — 15 문서의 donor에 K=753 제외 5문서가 포함될 수 있다. estimand의 "fixed donor graph"가 이 그래프(val20 기반, preflight frozen)임을 §6.1에 명시해야 해석 분쟁이 없다.
3. **`l_predicate` 금지가 본문에서 미작동.** §0 L38이 약속하지만 §6/§11 본문에 금지·negative test 규정이 없다. 실재로 `runner/c5_pm_gate.py:37-38`과 `runner/c5_pm_labels.py:54`가 `l_predicate`를 사용하므로, F0 gate가 import/call하지 않음을 assert하는 negative test를 §11 gate 규격에 추가해야 한다.

다음 단계: (1) §6.1에 sensitivity 방법 1문장 + donor graph = donors_for(val20, cache) 명시, (2) §11에 l_predicate 금지 negative test 추가 — 구현 commit에서 해소.

## Q5. Compute — **conditional agree**

근거 (긍정):

- 900 updates = 3 trained cells × 100 × 3 seeds (L174) 정합. M 1,440 = 120×12, phase7 7,200 = 600×12, generation 240 = 20×12 (L175) — F0 전 셀 EG2이므로 전부 15-common 기준 120/cell로 Phase 6 D1의 560(F/L 120, P/PA 160, docs/decisions.md D-216/D-156)과 다르고 정합.
- D1 cap 25 min의 근거 존재: D-156 실측 parallel 1,180.6s(19.7 min)은 F0 D1보다 무거운 작업(phase7 600/arm, checkpoint 보존)을 포함 — F0 D1(mechanics only)은 더 빠를 것이므로 여유 타당. L360에 측정 근거 명시됨.
- DS-7 해소: `t_proj_f0` 별도(L345), term set(L361-363), `contention_ratio` 정의(L365), nproc<12 / T_proj>96 hard abort(L366), 1.316 multiplier 제거(L177).
- Q5 부질문: F0 전용 orchestration commit이 선행 조건인가 — **예.** §11 L347 "committed at a recorded SHA with clean tree before D0" + artifacts에 code_commit/command/input SHA. v1.0 DS-4 해소.

남는 문제:

1. **T_proj term 매핑 불명확.** v1.1 L361의 term 목록에는 `setup_s`가 있는데 Phase 6 prereg §11.5(L1332-1341)에는 setup 항이 없고(100*t_train + step0 + step100 + M_build + M_ce + generate + primary_replay + replay_15x5x2x2x2 + overhead), replay 항 2개(`phase7_replay_s`/`primary_replay_s`)와 §11.5의 2개 replay 항의 대응이 선언되지 않았다. "mirrors §11.5"(L362) 주장과 달라지는 부분을, `c5_pm_f0_parallel.py` per-phase timer 이름(L344)과 1:1로 고정하고 setup_s를 정의해야 hard-abort 오판을 막는다.
2. **L177 "final cap from D1 T_proj" 모호.** §12 L364는 cap을 고정(25/96 min, "no cap increase without re-review")으로 규정하는데 L177은 D1 T_proj에서 cap을 "설정"하는 것처럼 읽힌다. "R cap은 96 min 고정, D1 측정 기반 T_proj_R이 사전 조건으로 ≤96 요구, 초과 시 abort"로 한 문장 재작성 필요.
3. R 96 min은 직접 측정 없는 신규 projection이다(Phase 6 registered는 arm당 프로세스 sequential, cap 120 min). prereg cap + hard abort 구조라 허용되지만, 측정 근거가 D-156(D1)뿐임을 §12에 명시하는 것이 정직하다.

다음 단계: (1) t_proj_f0 timer 이름↔§11.5 항 매핑표 + setup_s 정의, (2) L177 문구 수정, (3) §12에 R cap 근거 상태 명시 — 구현 commit에서 해소.

## Q6. Scope — **agree**

근거:

- ROUTE_STOP route-only: §14 L404 "stops only the route as configured ... does not stop the EG2 track, does not rescue B0-B, and does not launch H3" + §8 route 정의(L307-319). v1.0 §14(L388-399)에 없던 항목으로 v1.1 신규 추가 — 외부 요청 1.8 반영 확인.
- descriptive no-inference: §14 L405 "E00/E10/E01 vs E00 are descriptive; no causal inference" + §2 L69-71 confounded 명시. E01 vs E11만 registered contrast.
- dropped controls 기록: §14 L406 "the earlier MF-4 zero/permuted null and 1-seed signal gate are intentionally out of scope; F0 cannot claim they were replaced" — 외부 요청 1.8 "dropped 1-seed/null recorded" 충족. null 부재 하에서 PASS_POSITIVE는 donor-crop 기계 artifact를 배제하지 못하므로, 출력은 association-only(L403)로만 보고되어야 한다는 §14 규정과 짝이 맞다.
- 승인 구조: §11 L350 "D0/D1/R each require explicit stage approval" + L349 "No F0 code is implemented by this draft" — v1.1 L11 "어떤 실행도 승인하지 않는다"와 일관.
- M 격리(§9 L321-325): M evaluability는 PROTOCOL_VALID 조건, M_PASS는 ROUTE_STOP 조건 아님 — Phase 6 결과("M_PASS ≠ donor-specific content-use", cause report §5)와 정합.
- H3 완전 제거(§10 L330-336): 별도 prereg + 승인, F0 결과의 자동 개시 금지 — 과잉 요구 없음, 적정.

다음 단계: 추가 수정 불요. PASS 시에도 "adapter가 원인"이 아닌 "이 고정 route에서 adapter-as-configured와 signal이 연관" 문구가 f0_report.json 결과 서식에 포함되도록 구현 시 확인.

---

## 최종 판정

```text
최종 판정: CONTINUE

Init: conditional agree — §0 L36 약속 3개(golden table/post-step0 weight
  non-equality/tensor serialization)가 §4 본문에 여전히 부재. v1.0 GLM
  must-fix 2·3 미해소 잔여. 구현 commit(§11 L347 clean-tree 게이트)에서 강제.
D1: conditional agree — DS-1 계약(digest-delete, mechanics evaluator 분리,
  allowlist)은 올바르게 재설계됨. 잔여: "does not compute" 표현 모순,
  d1/ 경로 수준 파일 allowlist, 실패 메시지/stdout 값 금지, crash-path cleanup.
STOP/MDE: conditional agree — 4-state 상호배타·전체포괄 확인, MDE 산술 전부
  검증 통과(0.037573/0.019170/0.054/0.0876, labels.json paired에서 재계산).
  잔여: §6.5 L245이 단일군 0.117과 INDETERMINATE-우세 전제를 유지(내부 충돌),
  F−L proxy 전이 가정 미선언.
Cohort: conditional agree — DS-2 estimand 고정 완료. 잔여: sensitivity 방법,
  donor graph 출처(val20 기반) pin, l_predicate 금지 negative test.
Compute: conditional agree — D-156 기반 cap 정합, DS-7 해소. 잔여: t_proj_f0
  항 매핑(setup_s/replay 2항), L177 "final cap" 문구, R cap 측정근거 명시.
Scope: agree — ROUTE_STOP route-only, descriptive no-inference, lost controls,
  D0/D1/R stage approvals 모두 §14/§11에 반영됨.

Must-fix (ranked):
1. §6.5 재작성: paired half-width .037573 기준으로 EQUIVALENT 도달역/기대분기
   수정(0.117 제거, ALL_FAIL→ROUTE_STOP 우세 명시) — D0 승인 전 prereg 수정.
2. §4 보강: step_seed golden table+precedence, post-step0 weight non-equality
   assert, 텐서 hash 직렬화(prereg §12.1 인용), reseed forward 범위,
   post_step0 시점, F0-E11 vs Phase6-L I-O provenance assert — 구현 commit.
3. MDE 출처 선언: 0.019170 = labels.json L_COPY_SIGNAL.paired(F−L, n_boot=1000)
   명시 + "F−L은 LoRA-효과 대비, D는 adapter-효과 대비" 전이 가정과 편의 방향
   선언 — prereg 수정.
4. D1 봉쇄 보강: d1/ 경로 수준 파일 allowlist(d1_partial류 금지), 오류 메시지/
   stdout에 endpoint 값 포함 금지, crash-path delete+absent assert — D1 승인 전.
5. Cohort pin: donor-cluster sensitivity 방법 1문장, donor graph=donors_for(
   val20, cache) 명시, l_predicate 금지 negative test — 구현 commit.
6. Compute pin: t_proj_f0 timer↔§11.5 매핑+setup_s 정의, L177 문구 수정,
   R cap 근거 상태 명시 — R 승인 전.

잘못된 전제:
1. §6.5의 "INDETERMINATE가 지배적 기대 결과" — 15-common 기준 Phase 6 F/L가
   −0.111/−0.1135이므로 ALL_FAIL→ROUTE_STOP이 더 우세한 분기.
2. §6.5의 "Phase 6 L half-width ≈0.117로 EQUIVALENT/ROUTE_STOP 드묾" — paired
   half-width 기준으로는 EQUIVALENT 도달역 mean ∈ (−.0124, +.0124)로 도달 가능.
3. paired SE .019170이 D(E01−E11)에 전이된다는 암묵 전제 — 실제 출처는 F−L
   (LoRA 효과)이며 adapter 효과의 산포는 P−PA(+3.065) 근거상 더 클 수 있음.
4. §0 L36이 §4 본문 내용을 설명한다는 전제 — 해당 3항목은 본문에 없음.
```

판정 근거 요약: v1.0의 4개 blocker(DS-1 D1 seal 모순, DS-2 cohort estimand, DS-3 MDE 산술, DS-4 provenance)는 v1.1에서 **계약 수준으로 모두 해소**되었고, 잔여 must-fix 6개는 설계 변경이 아닌 규격 고정(golden table, 문구 수정, allowlist 확장, 매핑 선언)이다. v1.0 round 10에서 내가 제시한 CONTINUE 조건(F0 구현 commit + D0 stage 승인 시점 확인, threshold/seed/donor/step/LR 동결)은 v1.1 §11 L347/L350과 §3 L82가 그대로 유지하고 있다. 이 조건 하에서 CONTINUE이며, must-fix 1·3은 prereg 문서 수정, 2·4·5는 D0/D1 승인 전 구현 commit에서, 6은 R 승인 전에 확인한다. 신규 review round는 불요 — v1.0 합의와 동일하게 D0 승인 시점 커밋에서 확인한다.