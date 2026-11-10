# C5 F0 v1.5 — 독립 검토 (DS1017)

- 검토일: 2026-11-10
- 검토자: DeepSeek V4.1 Flash 1017 (`deepseek-v4.1-flash-1017`)
- **reviewed HEAD: `79b5dc772817d68026b7548507d0d6e87927b30e`** (`docs: add C5 F0 v1.5 review request`, 2026-11-10 10:41 +0900)
- 동기화: `git fetch origin` → `git pull --ff-only origin main` = **Already up to date**; `git status --porcelain` = **clean** (수정 전)
- 범위: 문서·코드·아티팩트 읽기와 산술 재계산만. 학습/평가 실행 없음, test 163/P1 미사용, subagent/추가 LLM 미사용, 지정 파일 외 수정 없음.
- 독립성: v1.4 스레드 결론을 상속하지 않고 아래 파일만으로 재검토. v1.4 문서는 **변경 이력 확인용**으로만 사용.

검토 대상: `docs/plan_c5_f0_v1_5_2026-11-09.md`(§ 이하 모든 인용의 출처), `docs/plan_c5_f0_v1_4_2026-11-09.md`, `reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py`, `runner/c5_pm_stats.py`, `runner/c5_pm_labels.py`, `runner/c5_pm_gate.py`.

---

## 0. HEAD에서 직접 확인한 사실 (판정의 전제)

v1.5의 서술을 코드·산술로 재확인했다. 아래는 인용이 아니라 HEAD에서 재계산/재확인한 결과다.

| 항목 | 재확인 결과 | 근거 |
|---|---|---|
| `step_seed` golden 12개 (seed 08/09/10/11 × step 0/1/2) | **전부 일치** (`0x9f02514d` … `0xdb9345dc`) | 식 `(seed ^ ((0x9E3779B9*(step+1)) & 0xffffffff)) & 0xffffffff` 로 재계산 |
| SE / 50% MDE / 80% MDE | `0.037573/1.96 = .019171` → `.0376` / `.0537` **일치** | 산술 |
| gate mean `.104` / 50% boundary `.0876` | `.05+.0537=.1037`, `.05+.03757=.08757` → **일치** | 산술 |
| Phase 6 registered wall anchor `4,939.884s` | **82.33 min** (96 min cap 대비 13.7 min 여유) | `phase6_artifact_registry.json` |
| Phase 6 D1 parallel `1,180.6s` | **19.68 min** (25 min cap) | `reports/C5_B0A_PM_PHASE6_D1_2026-11-09.md` |
| `N_BOOT = 1000` (`runner/c5_pm_stats.py:15`) | 확인. F0는 `n_boot=10000` 명시 override 필요 | 코드 |
| `bootstrap_paired_v2(values, n_boot, seed)` 반환 키 | `mean/ci_lower/ci_upper/n/n_boot/seed/rng/ci_method` — `realized.n_boot`/`realized.seed` assert **구현 가능** | `c5_pm_stats.py:29-66` |
| Phase 6 `build_arm` RNG 순서 | `manual_seed(seed)` → adapter → LoRA, **재시드 없음** (`c5_pm_phase6.py:142-155`) | 코드 |
| `eval_arm_d1` 산출물 | `per_doc` + `delta_shuffled_copy/full` 를 **materialize** (`c5_pm_phase6.py:466-487`); `not real_copy` 이면 `continue` 로 **문서 조용히 탈락**, `n_donors=len(real_copy)` 는 5 강제 아님 | 코드 |
| `--mode registered` | 현재 **지원됨** (`c5_pm_phase6.py:946-964`). v1.0 synthesis MF-1의 “거부” 상태는 HEAD에서 해소 |

**§0의 핵심 결론 두 가지.**

1. `build_arm`이 adapter 생성 후 **재시드하지 않고** LoRA를 붙이므로, Phase 6의 F(no adapter + LoRA)와 L(adapter + LoRA)는 **LoRA 초기값이 애초에 다르다.** v1.5 §4의 `LORA_SEED_XOR` 재시드는 이 실제 confound를 제거한다. 즉 Q1의 출발 전제는 코드로 확인되며, **v1.5의 개선은 실질적**이다.
2. 반대로 §4의 주장 “F0 must not modify Phase 6 `build_arm`”은 코드상 필수다. `build_arm`을 고치면 Phase 6 재현이 깨진다. 별도 `build_arm_f0`는 옳은 선택이다.

---

## Q1. Stage P / init / step_seed

**판정: conditional**

### 근거 (충분한 부분)

- §4의 init 계약은 코드 현실과 정합한다. `manual_seed(seed)` → adapter → `manual_seed(seed ^ 0x5EED10A5)` → LoRA 순서는, E01(adapter 없음)과 E11(adapter 있음)에서 **LoRA 초기 RNG 상태를 동일**하게 만든다. adapter 생성이 LoRA RNG를 소비하는 Phase 6 결함을 정확히 차단한다.
- §4의 step_seed golden 12개는 **내가 독립 재계산해 전부 일치**했다. 괄호 우선순위 모호성도 없다. 이 항목은 종결.
- E10/E11 adapter 해시 동일(§4-3)은 adapter가 `manual_seed(seed)` 직후, 재시드 **이전**에 생성되므로 성립한다. E01/E11 LoRA 해시 동일(§4-2)도 재시드 이후 생성이므로 성립한다.
- assertion 6(`lora_B` zero-init을 동등성 증거로 쓰지 않음)은 정확한 지적이다. r8 LoRA의 B=0이면 `sha256(lora_B)` 동일은 **자동으로 참**이라 정보량이 0이다. A만 증거로 쓰는 구조가 맞다.
- P를 init-only로 축소한 것(§13A.1: assertion 1–4, 6–8만; 5/9/13A.3은 D1 seed 20261111)은 **일관**하다. 5/9는 1스텝 학습이 필요하고, P는 0-update이므로 원리상 불가능하다. 축소가 옳다.

### 근거 (부족한 부분 — must-fix)

**P-1. Stage P는 `§12 Compute` 표에 행이 없고, 승인 단위도 없다.**

- §12 표는 `D0 / D1 / R` 3행뿐이다. P는 표에 없고 “P ≤10 min inside D0 budget”(§0-1, §13A.1)로만 등장한다.
- 그런데 D0 cap은 “≤15 min **provisional**”(§5 D0)이고 P는 “≤10 min”이다. **10분이 15분에 포함되는지, 별도인지 문서가 정하지 않는다.** 포함이면 D0 실사용 여유는 5분뿐이고, 별도면 D0 총 25분이며 §12 표가 틀린다.
- §5 D1/R은 “each require explicit stage approval”(§11 말미)인데, **P에 대한 승인 문장이 없다.** P는 신규 stage이므로 `pre_r_init_audit_pass`를 만드는 산출물을 생성하는 단계이고, 승인 없이 실행되면 안 된다.

**P-2. `d0/init_hashes.json`의 stage별 내용과 덮어쓰기 규칙이 미정.**

- §13은 `d0/init_hashes.json`(P/D0)과 `r/init_hashes.json`(R-only)를 나눈다. 그러나 P는 seed 20261108/09/10, D0는 seed 20261111을 쓴다.
- §4는 “capture point = immediately after builder returns, before D0 forward”라고만 쓴다. P가 D0보다 **먼저** 도는데, 같은 파일에 4개 seed를 **append**하는지 D0가 **덮어쓰는지** 정해지지 않았다. 덮어쓰면 P의 3-seed init 감사 기록이 소실되고 `pre_r_init_audit_pass`의 근거가 사라진다.
- §6.1은 donor map sha256을 `init_hashes.json`에 기록하라고 하는데, 이 파일이 P/D0/R 중 어느 단계에서 donor map을 아는지도 미정이다(§13A.8에 따라 D1은 donor를 로드하지 않는다).

**P-3. P는 `phase6_io_zero`를 기록하지 않는다.**

- §13A.1은 P가 assertion 1–4, 6–8만 기록한다고 못박는다. 그런데 §13A.6의 Phase 6 protected-path I/O 감사(“count of protected-path opens must be 0”)는 **어느 stage 산출물에 들어가는지 불명**이고, D1 schema(§13A.4)에만 `phase6_io_zero` 불리언이 있다.
- R은 Phase 6 checkpoint를 재사용하지 않는다는 것이 F0의 핵심 주장인데(§4 “Phase 6 I/O assert”, §13A.6), 그 감사가 **R 직전 gate인 `pre_r_init_audit_pass`에 포함되지 않는다.** R 진입 gate가 실제로 검사하지 않는 항목을 “pre-R audit”이라 부르는 것은 명칭과 내용의 불일치다.

### 다음 단계

1. §12 표에 `P` 행(4 cells × 3 seeds, 0 updates, 1 thread/arm, cap ≤10 min)을 추가하고, D0 15분과의 포함/별도 관계를 한 문장으로 확정.
2. §5 또는 §11에 “P도 explicit stage approval 대상”을 명시.
3. `d0/init_hashes.json`을 `{stage, seed -> hashes, donor_map_sha256, code_commit}` 구조로 정의하고, P는 append-only, D0는 별도 `stage` 키로 기록하도록 확정.
4. `pre_r_init_audit_pass`의 정의에 `phase6_io_zero==true`와 `clean_tree_sha`를 포함시키고, 그 감사를 P가 수행하도록 이동.

---

## Q2. D1 full schema / signal path / seal

**판정: conditional (seal 설계는 승인 가능, `mechanics_pass` 정의는 불완전)**

### 근거 (충분한 부분)

- **D1은 signal 값을 materialize하지 않는다**는 구조가 코드 수준에서 성립한다. §11이 `c5_pm_f0_mechanics.py`가 `eval_arm_d1`을 **재사용하지 않는다**고 못박은 것이 결정적이다. HEAD의 `eval_arm_d1`은 `per_doc`과 `delta_shuffled_copy/full`을 실제로 계산해 반환한다(`c5_pm_phase6.py:466-487`). 따라서 재사용 금지 + 신규 evaluator는 v1.0 synthesis DS-1(oracle)을 **정면으로** 해소한다. v1.5에서 가장 잘 고친 부분이다.
- `d1_report.json` 절대경로 금지, `d1_sealed/` 부재, gate negative test(§5 D1), `checkpoint_absent`, digest-then-delete(§13A.4 `checkpoint_digests`+`checkpoint_absent`)는 서로 모순되지 않는다. “checkpoint가 signal oracle이 될 수 있다”는 §5의 자기 지적과 digest-only 처리는 정합한다.
- `f0_labels.json` alias 금지, canonical `f0_r_labels.json`(§6.3)은 이전 라운드의 혼동을 제거한다.
- §13A.4의 keys/types가 리터럴로 닫혀 있고 “Only these keys”를 선언한 점, writer/consumer allowlist를 분리한 점은 재량 게이트를 실질적으로 막는다.

### 근거 (부족한 부분 — must-fix)

**D1-1. `mechanics_pass` predicate가 seal의 핵심 플래그를 검사하지 않는다.**

§13A.4의 정의는 다음과 같다(그대로):

```text
mechanics_pass = partial==false AND error==null AND checkpoint_absent==true
                 AND all assertions==true AND phase7_records==0
                 AND wrong_donor_ce_calls==0 AND donor_map_loads==0
```

그런데 같은 스키마가 동시에 요구하는 다음 5개는 predicate에 **없다**:

- `labels_computed` (must false)
- `not_a_result` (must true)
- `test_split_used` (must false)
- `p1_used` (must false)
- `d1_signal_read` (must false)

즉 `labels_computed:true`인 D1 산출물도 `mechanics_pass:true`가 될 수 있다. v1.5 변경 #3이 “exact `mechanics_pass` predicate”를 표방했지만, 실제로는 seal 선언과 predicate가 어긋난다. 이 5개는 “must false/true”로 산문에만 존재하고 기계 판정에는 없다.

**D1-2. `assertions` 객체가 §5 D1 assertion 1–3을 담지 않는다.**

§13A.4는 “`assertions` covers all §5 assertions (10)”라고 주장하지만, 15개 불리언 목록에는 다음이 **없다**:

- §5 D1-1 `cells == 4`
- §5 D1-2 `updates_total == 3` (스키마에 `updates_total` 필드 자체가 없다)
- §5 D1-3 E00 `optimizer_steps == 0` (top-level에 `optimizer_steps` 없음, `cells.E00.updates`로만 추정 가능)

`cells.{cell}.updates`가 있으므로 소비자가 합산할 수는 있지만, “all assertions==true”로 닫힌 predicate 안에서는 검사되지 않는다. **D1이 1 update를 실제로 수행했는지**를 기계적으로 보증하는 항목이 predicate 밖에 있는 것은, D1의 존재 이유(1-update mechanics 증명)를 약화시킨다.

**D1-3. §0-4와 §13A.8이 정면으로 모순된다 (절차 미확정).**

- §0 변경 요약 4항: “D1 wrong-donor CE finiteness **dry run** (per-doc values not persisted), or R-first-risk accepted; **choose dry run**.”
- §13A.8: “D1 does **not** call wrong-donor CE; `wrong_donor_ce_calls:0` remains **absolute**. Primary wrong-donor CE path is **first exercised at R**; explicitly accepted.”
- §13A.4: `wrong_donor_ce_calls: int (must 0)`.

요약은 “dry run을 선택했다”고 하고, 본문은 “D1은 wrong-donor CE를 절대 호출하지 않는다”고 한다. 두 문장은 같은 실행을 서로 다르게 규정한다. 이대로면 구현자가 어느 쪽을 따라야 하는지 결정할 수 없고, dry run을 택하면 `wrong_donor_ce_calls:0`이 깨진다.

**해소 방향(내 판단): §13A.8을 유지하고 §0-4를 고친다.** 근거는 이 경로가 신규가 아니라는 점이다. HEAD의 `eval_arm_d1`은 이미 `memory_for(donor)` + `k=min(len(real),len(donor))` crop + `token_losses` 경로를 구현하고 있고, Phase 6는 이 경로로 **12/12 replay_ok**를 기록했다. 따라서 “R에서 처음 실행”이라는 위험은 **미검증 코드 리스크가 아니라 F0 배선 리스크**이며, §13A.8의 `donors_for`/crop 단위 테스트로 충분히 통제된다. dry run을 D1에 넣는 것은 seal을 깨는 대가가 더 크다.

### 다음 단계

1. `mechanics_pass`에 5개 플래그를 **모두** AND로 추가(또는 `assertions`에 불리언으로 승격).
2. `assertions`에 `cells_ok`, `updates_total_ok`, `e00_steps_zero` 3개를 추가하고, `updates_total:int` 필드를 top-level에 추가.
3. §0-4를 “unit-test only, R-first accepted; dry run **not** used”로 수정. §13A.8과 §13A.4를 유일한 규정으로 삼고, §0에 그 결정 이유(Phase 6 12/12 replay)를 한 줄로 남긴다.
4. `d1_signal_read`의 **의미**를 정의(누가/언제 어떤 키를 읽으면 true가 되는지). 현재는 “must false”만 있고 판정 주체가 없다.

---

## Q3. STOP / MDE label 정합성

**판정: agree (라벨 산술 정합; 단, near-threshold 보고 의무 추가 권고)**

### 근거

- **4-state는 상호배타·전체포괄이다.** priority 1 `NOT_EVALUABLE`(not PROTOCOL_VALID), 2 `PASS_POSITIVE`, 3 `ROUTE_STOP`(ALL_FAIL), 4 `INDETERMINATE`(나머지). 모든 입력이 정확히 한 상태에 떨어진다.
- **PASS와 EQUIVALENT는 겹치지 않는다.** PASS는 `CI_D.lower > +.05`, EQUIVALENT는 `CI_D.upper <= +.05`. `lower <= upper`이므로 두 조건은 동시에 참일 수 없다. 논리적으로 닫혀 있다.
- **PASS와 ALL_FAIL도 겹치지 않는다.** PASS는 `SIGNAL(E01,copy)`를 요구하고 ALL_FAIL은 `FAIL(E01,copy)=NOT SIGNAL(E01,copy)`를 요구한다. 따라서 `ROUTE_STOP`과 `PASS_POSITIVE`는 배타적이다는 §7의 서술이 성립한다.
- **MDE 라벨 산술은 정합하다(직접 재계산).** `.037573/1.96=.019171`(=SE), 50% MDE `1.96×SE=.03757→.0376`, 80% MDE `2.8016×SE=.05371→.0537`, gate mean `.05+.0537=.1037→.104`, 50% boundary `.05+.03757=.08757→.0876`. **5개 숫자가 모두 같은 SE에서 유도되며 서로 모순이 없다.** 이전 라운드에서 지적된 “단일 arm SE 0.0594 사용” 오류는 완전히 제거됐다.
- 라벨 의미도 정확하다. `.0376`은 50% power MDE이자 **95% CI 반폭과 같은 값**이고, `.0876`은 “관측 평균이 .05 위에 있으려면 50% power로 필요한 경계”, `.104`는 80% power 경계다. “none is an observed F0 mean”(§12)이라는 단서도 맞다.
- `EQUIVALENT > harm > benefit` 우선순위는 실질적으로 **공허(vacuous)**하다. harm/benefit 정의가 각각 `NOT EQUIVALENT`를 포함하고 `lower>0`과 `upper<0`은 동시에 불가능하므로 세 라벨은 이미 배타적이다. 따라서 우선순위 문장은 해가 없으나 규칙을 추가로 제약하지 않는다. 이것은 결함이 아니라 잉여 문장이다.

### 남는 문제 (must-fix는 아니나 결정 품질)

**Q3-1. near-threshold positive가 `ROUTE_STOP`으로 떨어진다.**

`SIGNAL(copy)`는 `mean(delta_c) >= .05`를 요구한다. 따라서 E01이 평균 `.049`, `CI.lower=.02`, 3/3 seed>0 인 **명백한 양의 신호**여도 `FAIL`이고, E11도 same이면 `ALL_FAIL` → `ROUTE_STOP`(reason `no_signal_uncertain`)이 된다. 이때 상태는 `INDETERMINATE`가 아니다. reason enum이 `no_signal_uncertain`을 따로 둔 것은 이 경우를 의식한 것이지만, **상태 이름이 “STOP”이므로 독자·후속 결정자에게 “신호 없음”으로 오독될 수 있다.**

### 다음 단계

1. §7에 “`ROUTE_STOP` 산출 시 4개 cell의 `mean(delta)`, `CI.lower/upper`, seed별 부호를 **반드시 함께 보고**”를 추가. `.05` 미달 positive와 0 근처를 구분할 수 있게.
2. (선택) `no_signal_uncertain`인 경우 `ROUTE_STOP` 대신 별도 `NEAR_THRESHOLD` 사유를 두거나, 최소한 reason에 관측 평균을 각인.

---

## Q4. Cohort / cell CI / donor conditional

**판정: conditional**

### 근거 (충분한 부분)

- 15 common = frozen preflight `common_ids`(prereg v1.0.11 §“L M targets … 15”), length-eligible임을 **명시**하고, 20-doc 모집단 일반화를 금지하며 20-doc F/L을 **descriptive로 보고**하도록 고정했다(§6.1). DS-2의 “length-selected를 숨긴 채 15-doc으로 결정” 문제를 정면으로 다룬다.
- donor 조건부 estimand를 명시했다: “primary estimand is **15 length-eligible docs + fixed donor graph**”, “conditional on the fixed donor graph; no population inference”(§12). donor 재사용을 **선언**하고 leave-one-donor-out 민감도를 요구한다(§6.1). 통계적 정직성 측면에서 적절하다.
- donor 수 강제가 코드 결함을 정확히 겨냥한다. HEAD의 `eval_arm_d1`은 `n_donors=len(real_copy)`로 5 미만을 조용히 허용하고, `not real_copy`면 문서를 **말없이 탈락**시킨다(`c5_pm_phase6.py:479`). §13A.5의 “`evaluated_donors==5` and `expected_donors==5`, abort otherwise”와 §6.1의 “silently drops … `NOT_EVALUABLE`, never a smaller cohort”는 이 결함을 **직접** 봉인한다.
- cell CI 파라미터가 동결 prereg와 정합한다: seed-average **후** bootstrap(prereg “seed-average the contrast before bootstrap”), `n_boot=10000`, `seed=20261109`, linear percentile. HEAD의 `bootstrap_paired_v2`가 `np.random.default_rng(seed)`로 **호출마다 fresh PCG64**를 만들고 `method="linear"`를 쓰므로(§29-66), 요구사항이 코드로 실현 가능하다.
- `n_boot=10000`은 `N_BOOT=1000`(stats.py:15)의 명시적 override이며, `assert realized.n_boot == 10000`이 반환 키 `n_boot`과 맞는다. silent revert 경로(DS-6)가 닫혔다.

### 근거 (부족한 부분)

**Q4-1. 20-doc descriptive가 F/L에만 요구된다.**

§6.1은 “report 20-doc F/L descriptively”라고만 한다. 그런데 이번 primary는 E01/E11이고, length selection이 결과 부호를 뒤집은 전례가 정확히 F/L에서 관측됐다(v1.0 synthesis DS-2: F `15-doc −0.11087` vs `20-doc +0.000195`; L `−0.11351` vs `−0.02218`). E01/E11에서도 같은 부호 반전이 가능하므로, **E01/E11의 20-doc descriptive를 의무화**하지 않으면 length-selection 민감도를 점검할 수 없다.

**Q4-2. CI가 seed 변동을 포함하지 않는다(fixed-effect 처리).**

cell CI는 “seed mean over 20261108/09/10” 후 doc-level bootstrap이다. 즉 CI는 **3개 seed를 조건으로 한** doc-level 구간이고, seed 간 변동은 구간에 들어가지 않는다. §6.4의 `2/3 seeds>0` 게이트가 부분 보완이지만, seed를 확률효과로 다루지 않는다는 점은 §6.3 “CI_D is doc-level only”로 **선언**되어 있으므로 은폐는 아니다. 다만 3-seed 평균의 불확실성이 CI에 없다는 사실을 결과 보고에 명시해야 한다.

**Q4-3. donor cluster 구조가 CI에 반영되지 않는다.**

doc 내 5 donor는 독립이 아니지만 bootstrap은 doc만 재표집한다. LODO range(§6.1)가 유일한 완화책이다. 이는 Phase 6와 동일한 동결 설계이므로 **변경 금지 원칙상 수용**해야 하지만, “donor-conditional, cluster-robust 아님”을 §6.5에 한 줄 명시하는 것이 정직하다.

### 다음 단계

1. §6.1의 descriptive 대상을 **E00/E10/E01/E11 전 cell**의 20-doc으로 확대(최소 E01/E11 필수).
2. §6.5에 “CI는 3 seed를 조건으로 하며 seed 변동·donor cluster를 포함하지 않는다”를 명시.
3. (선택) seed별 cell delta와 seed별 CI를 부록 표로 보고.

---

## Q5. Compute — nproc / setup / T_proj

**판정: conditional**

### 근거 (충분한 부분)

- `nproc>=16` 또는 `threads_per_arm<=1`(§13A.7), 그리고 “현재 4-vCPU workspace는 qualifying host 아님, no F0 run there”는 **명확한 하드 게이트**다. 12 logical thread를 16 물리 코어에 얹어 headroom을 확보하려는 의도가 일관된다.
- `contention_ratio = parallel_wall_s / sum(per_arm_phase_s)`를 기록하고 cap을 **측정값**에서 정하는 구조(§12)는 이전의 “1.316 multiplier”식 추정을 제거했다.
- 900 updates 산술이 정확하다: E10/E01/E11 × 100 × 3 seeds = **900** (§5 R). D1은 3 trained cells × 1 = **3**.
- cap 여유가 실측 anchor로 정당화된다: Phase 6 registered **4,939.884s=82.33min** < 96min(13.7min 여유), Phase 6 D1 **1,180.6s=19.68min** < 25min. F0는 per-step `manual_seed` 외에 Phase 6 대비 추가 연산이 없으므로 두 cap은 **현실적**이다.
- `T_proj_R = setup_s_effective + 3 × sum(9 terms …)`의 9개 항은 prereg §11.5의 9개 항과 **정확히 일치**한다(코드 대조). `t_primary_replay`에 per-seed 120/160을 넣고 outer `3×`를 적용하라는 prereg 주의도 위반하지 않는다.

### 근거 (부족한 부분 — must-fix)

**Q5-1. `nproc>=12`가 문서에 남아 있다 (모순).**

- §15 Q5 본문: “12 logical threads, D1 25min, R 96min, **T_proj/nproc≥12**”
- §13A.7: “**nproc>=16** (or `threads_per_arm<=1`) required”
- §12 마지막 hard abort: “if **`nproc < 16`** and `threads_per_arm > 1`”

리뷰 질문이 검토자에게 **폐기된 기준(12)**을 평가하도록 제시한다. §12·§13A.7은 16이고 §15만 12다. 어느 것이 규범인지 확정해야 하며, 이 상태로 승인하면 구현자가 12코어 host에서 실행할 수 있다.

**Q5-2. `setup_s_effective`의 이중계산 여부가 불명.**

§12는 `T_proj_R = setup_s_effective + 3 × sum(9 terms)`로 **setup을 더한다.** 그런데 “Wall anchor: Phase 6 registered 4,939.884s”를 상한 sanity로 쓰면서, **이 anchor에 setup이 포함됐는지 명시하지 않는다.**

- 포함이면: anchor(82.33min)에 setup을 또 더하는 것은 **이중계산**이고 T_proj가 과대평가된다.
- 미포함이면: 3 waves × 4 processes = 12회 model load가 anchor에 없으므로, 82.33min + setup이 96min을 넘을 수 있다.

96min cap의 타당성이 이 한 문장에 달려 있다. 또한 `setup_s_effective = total setup for 3 waves × 4 processes`라고 정의하면서 “no amortization claim without committed orchestrator measurement”라고 했으므로, **어느 artifact의 어느 필드가 그 측정인지** 지목해야 한다.

**Q5-3. P가 T_proj/D0 회계에서 빠져 있다.** (Q1의 P-1과 동일 사안, compute 관점)

`T_proj_R`은 D1/R만 다룬다. P는 D0 budget이라고만 되어 있고 §12 표에 없다. 3 seeds × 4 cells = 12회 init/load가 D0 15분 안에 들어가는지 **검증 가능한 산술이 없다.** Phase 6 D1이 4 arms 1,180.6s였던 것을 감안하면 12회 load는 무시할 수 없다.

**Q5-4. `parallel_arms:true` 요구와 D1의 실행 형태가 서로 다른 stage에 적용된다.**

§12 “F0 D1/R require `parallel_arms:true`; sequential diagnostic only”와 §5 D1 “4 parallel arm processes × 3 threads/arm”은 정합한다. 다만 §13A.7의 “F0 runner/orchestrator must be committed before D0”와 §11의 신규 3개 runner 파일이 **아직 존재하지 않는다**(문서 §11 “No F0 code is implemented by this draft”). 이는 결함이 아니라 **선행 조건**이며, D0 승인 전에 commit SHA가 있어야 한다는 요구는 옳다. 다만 승인 문서에 “선행 조건 미충족 시 D0 실행 불가”를 §18 상태 블록에도 반영해야 한다.

### 다음 단계

1. §15 Q5의 `nproc≥12`를 `nproc≥16 (or threads_per_arm≤1)`로 수정.
2. `4,939.884s` anchor의 **setup 포함 여부**를 명시하고, 포함이면 `setup_s_effective`를 T_proj에서 제거하거나 anchor를 setup-exclusive 값으로 교체.
3. §12에 P 행 추가 + 12회 load의 실측 근거(또는 D0에서 측정 후 cap 확정 절차) 명시.
4. §18 상태 블록에 “F0 runner 3종 commit + clean-tree SHA 없이는 D0 승인 불가”를 추가.

---

## Q6. Scope / route-only

**판정: agree**

### 근거

- H3 완전 제거(§10)는 타당하다. “no H3 arm, trigger, rank, identity, null, or donor-discrimination endpoint is registered here”로 **등록 대상 자체를 없앴고**, “F0 results do not automatically launch H3”로 자동 개시 경계를 닫았다. H3 세부가 F0 승인을 막지 않고, negative F0가 H3로 구제되지 않는다는 §10의 이유 서술도 정확하다.
- `ROUTE_STOP`의 의미를 “route as configured”로 한정하고(§8), “does not stop the EG2 track, does not rescue B0-B, and does not launch H3”(§14)로 3중 경계를 걸었다. 이는 Phase 6 synthesis MF-3의 과대 일반화 지적에 정확히 대응한다.
- association-only 한정(§1, §14)과 “descriptive contrasts” 명시(E00/E10/E01 vs E00)는 인과 주장 범위를 올바르게 좁힌다. `E01 vs E10`을 “not clean causal”로 스스로 표기한 것도 정직하다.
- M과 signal의 분리(§9): “M_PASS is not donor-specific content-use evidence”, “M is not a gate for F0 primary”, “M evaluability required for PROTOCOL_VALID; M_PASS not required for ROUTE_STOP”는 cause report §5와 일치한다.
- lost controls(MF-4 zero/permuted null, 1-seed gate)를 “intentionally out of scope; F0 cannot claim they were replaced”(§14)로 **명시적으로 포기**했다. 조용한 누락이 아니라 선언된 한계다.

### 남는 지적(비차단)

H3의 완전 제거는 옳지만, F0 negative 시 “EG2 content 부족”과 “decoder-space alignment 부재”를 구분하지 못한다는 근본 한계(cause report §5, DS 지적)는 남는다. §14가 이를 “association-only”로 덮고 있으므로 **차단 사유는 아니나**, F0 결과 보고서에 이 구분 불가를 한 번 더 명시해야 한다. 또한 §11 “The causal factor is `adapter-as-configured` (adapter params + adapter LR + adapter-conditioned forward graph)”는 capacity·LR·graph를 하나로 묶은 **복합 처치**임을 정확히 인정한 표현이며, 그대로 유지해야 한다.

### 다음 단계

1. F0 결과 보고 템플릿에 “EG2 content 부족 vs alignment 부재 구분 불가”를 고정 문구로 삽입.
2. §18 상태 블록에 “F0 = v1.5 review 대기 → NARROW, D0 미승인”을 반영.

---

## 7. Verbatim — paired `E01−E11` (primary contrast, §6.3 그대로)

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

§6.3의 판정 규칙도 그대로 옮긴다:

> Primary positive: `mean_D > 0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0`.

그리고 §6.2의 cell delta 정의(인용):

```text
delta_c(s,d) = mean_donor( CE_wrong_donor - CE_real )
```

이 세 조각이 F0 primary estimand의 **전부**이며, §0 D1-3의 모순(§0-4 vs §13A.8)이 바로 이 `CE_wrong_donor` 경로의 사전 실행 여부에 관한 것이다.

---

## 8. 최종 판정

**NARROW** — v1.5는 설계·seal·산술에서 v1.4보다 **명확히 개선**됐고, 남은 문제는 **문서 내부 모순과 기계 판정 정의의 불완전성**이지 새 실험이나 재설계가 아니다. 다만 아래 4건은 **D0 승인 전에 반드시** 닫아야 한다. 특히 MF-1과 MF-2는 “D1이 무엇을 통과했다고 말하는가”를 정의하므로, 구현 착수 전에 확정되지 않으면 runner가 잘못된 계약을 구현한다.

```text
최종 판정: NARROW
Initialization: conditional — step_seed golden 12/12 재계산 일치, LORA_SEED_XOR는 build_arm의 실제 결함을 제거.
                P의 compute 행·승인·init_hashes 경로·phase6_io_zero 소속 미정.
D1 seal:       conditional — eval_arm_d1 미재사용 결정은 정확. mechanics_pass가 5개 must-flag와
                D1 assertion 1–3을 검사하지 않음. §0-4 ↔ §13A.8 정면 모순.
STOP/MDE:      agree — 4-state 배타·포괄, PASS/EQUIVALENT 비중첩, 5개 MDE 숫자 동일 SE에서 유도되어 정합.
                near-threshold ROUTE_STOP의 관측 평균 보고 의무 추가 권고.
Cohort:        conditional — 조건부 estimand·n=5 abort·LODO·n_boot=10000 확정. 20-doc descriptive가 F/L에만
                한정되고, seed/donor 변동이 CI에 없음을 명시해야 함.
Compute:       conditional — anchor 여유(82.33→96, 19.68→25)는 현실적. nproc≥12 잔존, setup 이중계산 여부,
                P 회계 누락.
Scope:         agree — H3 완전 제거, route-only 3중 경계, association-only, lost controls 명시.
```

### Must-fix (ranked)

1. **[blocker] §0-4 ↔ §13A.8 정면 모순 해소.** “choose dry run”과 “D1 does not call wrong-donor CE / `wrong_donor_ce_calls:0` absolute”가 동일 실행을 다르게 규정. §13A.8을 유지하고 §0-4를 “unit-test only, R-first accepted”로 수정. 근거: Phase 6 `eval_arm_d1` 경로가 12/12 replay_ok로 이미 실행됨.
2. **[blocker] `mechanics_pass` predicate에 `labels_computed==false`, `not_a_result==true`, `test_split_used==false`, `p1_used==false`, `d1_signal_read==false`를 AND로 추가.** 현재 predicate는 seal의 핵심 플래그를 검사하지 않아 `labels_computed:true`도 통과 가능.
3. **[blocker] `assertions`에 `cells_ok`, `updates_total_ok`, `e00_steps_zero` 추가 + top-level `updates_total:int` 추가.** §13A.4의 “covers all §5 assertions (10)” 주장이 실제로는 3개를 누락.
4. **[blocker] Stage P를 §12 compute 표에 행으로 추가하고 승인 단위로 명시.** 10분이 D0 15분에 포함인지 별도인지 확정. 12회 load의 산술 근거 제시.
5. **[high] `d0/init_hashes.json`의 stage·seed별 구조와 append/overwrite 규칙 확정.** P의 3-seed 감사 기록이 D0에 덮이지 않도록.
6. **[high] `pre_r_init_audit_pass` 정의에 `phase6_io_zero==true`와 clean-tree SHA 포함.** P가 그 감사를 수행하도록 이동.
7. **[high] §15 Q5의 `nproc≥12`를 `nproc≥16 (or threads_per_arm≤1)`로 수정.**
8. **[high] `4,939.884s` anchor의 setup 포함 여부 명시.** 포함이면 `setup_s_effective` 이중계산 제거.
9. **[medium] 20-doc descriptive를 E00/E10/E01/E11 전 cell(E01/E11 필수)로 확대.** length-selection 부호 반전(F −0.11087→+0.000195) 재발 감시.
10. **[medium] §6.5에 “CI는 3 seed 조건부, seed 변동·donor cluster 미포함” 명시.**
11. **[low] `ROUTE_STOP` 산출 시 4 cell의 mean/CI/seed 부호를 의무 보고.** near-threshold positive 오독 방지.
12. **[low] CI 키 이름 정합.** `bootstrap_paired_v2` 반환은 `ci_lower/ci_upper`, 문서는 `CI_D.lower/upper` — 매핑 문장 추가.
13. **[low] §18 상태 블록에 “F0 runner 3종 commit + clean-tree SHA 없이는 D0 불가”와 “F0 = NARROW, 미승인” 반영.**

### 잘못된 전제

1. **§0-4 “choose dry run”** — D1에 wrong-donor CE를 넣으면 `wrong_donor_ce_calls:0`(§13A.4)과 seal이 동시에 성립할 수 없다. 두 요구는 양립 불가.
2. **§13A.4 “`assertions` covers all §5 assertions (10)”** — 실제 15개 불리언에 `cells`/`updates_total`/`E00 optimizer_steps` 3개가 없다. “10개 전부” 주장은 거짓.
3. **§15 Q5 “T_proj/nproc≥12”** — §12·§13A.7의 `nproc>=16`과 모순. 12는 폐기된 기준인데 리뷰 질문에 남아 검토자를 오도한다.
4. **§13A.1 “P ≤10 min inside D0 budget”** — D0 cap은 “provisional ≤15 min”(§5 D0)이므로 P 포함 시 실사용 여유가 5분뿐이다. “inside”라는 전제가 §12 표( P 행 부재)와 충돌.
5. **§0-5 “D1 wrong-donor CE finiteness dry run”** — §13A.8의 “first exercised at R”과 정반대. 요약이 본문 결정을 반영하지 못한 잔재.
6. **P가 init 감사 전체를 커버한다는 전제** — P는 assertion 1–4, 6–8만 기록하며 `phase6_io_zero`는 기록하지 않는다. R 진입 gate의 이름(“pre-r init audit”)이 실제 검사 범위보다 넓다.

### 승인 경계

이 문서는 어떤 실행도 승인하지 않는다. D0/D1/R은 각각 별도 승인이 필요하고, F0 runner 3종(`runner/c5_pm_f0.py`, `runner/c5_pm_f0_parallel.py`, `runner/c5_pm_f0_mechanics.py`)의 commit + clean-tree SHA가 D0의 선행 조건이다. Phase 6 = negative 종료, B0-B = 미승인, test 163 = sealed, P1 = unused, T5Gemma2 = D-108 STOP을 변경하지 않는다.