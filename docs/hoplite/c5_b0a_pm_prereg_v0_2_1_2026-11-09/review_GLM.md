# C5 B0-A Phase 6 P/M Prereg v0.2.1 — 독립 외부 검토보고서

- 검토자: **GLM 5.3 Flash (reasoning effort: max)** — v0.2.1 errata 라운드의 독립 외부 검토자. 본 라운드는 v0.1·v0.2 라운드(각 3/3 NARROW)와 별개의 **신규 독립 라운드**이며, 다른 모델의 답변을 재사용하지 않았다. 요청서 전문과 지정 원문·코드를 직접 판독했다.
- 검토일: 2026-11-09
- 검토 기준 HEAD: `075621596fbe4e169c02f0c4c75ad65b3d42853f` (`docs: add C5 P/M v0.2.1 review request`)
  - 동기화: `git fetch origin` 성공, `git pull --ff-only origin main` → **"Already up to date"**, HEAD == origin/main == `0756215`.
  - 요청서 기재 작성 기준 `672db63`(`docs: add C5 Phase 6 v0.2.1 errata`)은 HEAD의 직전 커밋이고, `0756215`는 그 위에 본 검토요청서를 추가한 커밋이다. 두 커밋 모두 v0.2.1 errata 문서 이후이므로 검토 기준으로 문제없다.
- 대상: `docs/plan_c5_b0a_pm_prereg_v0_2_1_errata.md` (434줄)
- 제약 준수: 학습·평가 미실행. test 163 미개봉(sealed 유지). P1 미사용. 외부 API 미사용. 저장소 수정 없음(이 보고서 파일 1개만 작성). subagent·추가 LLM 미호출(직접 검토). T5Gemma2 D-108 STOP 유지. Phase 6/B0-B/B1/B2/Stage C 미승인. 결과 전 단계이므로 threshold·seed·donor·step 변경 제안 없음(필요 시 새 사전등록으로만).

---

## 0. 검증 기반

### 0.1 직접 판독한 문서·코드

| 대상 | 방법 |
|---|---|
| `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_1_2026-11-09.md` | 전문 직접 판독 |
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_errata.md` | 전문(434줄) 직접 판독(도구 절단분 §3.5–§4.3 별도 재판독) |
| `docs/plan_c5_b0a_pm_prereg_v0_2.md` | 전문 직접 판독(절단분 §6.1–§7 별도 재판독) |
| `reports/C5_B0A_PM_PREREG_V0_2_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 전문 판독 — v0.2 MF-1~6 정의 확인 |
| `reports/C5_B0A_PM_PREREG_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 전문 판독 — v0.1 계보 확인 |
| `reports/C5_B0A_REPAIR_2026-11-09.md` | 전문 판독 — mode/mode-policy/telemetry/테스트 상태 확인 |
| `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md` | 전문 판독 |
| `reports/provenance/C5_b0a/p0_native_sanity.json` | 수치 재확인: train mean Δcopy 3.7617 / CI [1.8917, 5.6050] / Δfull 3.5027, val 5.2375 / CI [2.5013, 8.0753] / Δfull 5.2936, docs_positive(copy) 14/20·18/20, real CE 12.7022/13.2352, SENSITIVE_POSITIVE — 요청서·보고서와 일치 |
| `runner/c5_mt5_lora_b0.py` | 전부(802줄) 판독 |
| `eval/tests/test_c5_b0_metric.py` | 전문 판독(7 test method) |

### 0.2 구현 상태(사실 확인)

- runner `--mode`는 `smoke|metric-smoke|train|p0-sanity`뿐이며 `pm-diagnostic`/`--pm-arm`은 미구현, `train_arm`은 `frozen|lora`만 지원. errata §0("코드는 이 errata 승인 후에만 작성")과 정합.
- runner의 `bootstrap_paired`는 여전히 `seeds_positive` 필드에 **문서 수**를 담는다(요청서가 지적한 이름 오용의 잔존 지점).
- `train_arm`에서 `make_adapter(seed)` 이후 LoRA attach 전에 `torch.manual_seed(seed)` 재호출이 없다. errata §2.1의 시딩 순서는 구현 시 충족해야 할 신규 코드다.
- `torch.set_num_threads(6)` 이미 존재(cap §6.1 threads=6과 정합).
- PM 관련 테스트(decision truth table, M leakage, cohort, seed 재현)는 존재하지 않는다. "54 tests"는 historical evidence이며, 현재 `test_c5_b0_metric.py`는 7 method다.

---

## 1. 핵심 요약

> v0.2.1은 v0.2 MF-2~6(P/PA step0·retention, M AND-norm·quantifier·cohort·checkpoint, 통계, debug seed/cap, artifact/manifest)을 **실제로 닫았다**. 그러나 §1.2 precedence는 여전히 **결정적 total function이 아니다**: (i) rule 3의 이중 라벨, (ii) PA path-fail cell 누락, (iii) NOT_ASSESSABLE headline 부재, (iv) copy_only/full_only 미정의. 이 4개는 **문서 수정**(새 사전등록이 아니라 contract tighten, threshold·seed·donor·step 변경 아님)으로 동결 전에 닫아야 한다. 이후 동결 → 구현·unit tests → unregistered-seed mechanics debug까지는 조건부 승인 가능. 3-seed는 별도 gate, B0-B는 무조건 별도 승인. **최종 판정: NARROW.**

---

## 2. Q1–Q12

### Q1. Total decision function

- 판정: **conditional** (설계 구조는 agree, 현 문장은 total 아님)
- 근거:
  - **닫은 부분.** 독립 flag vector 19개(errata L36–55), headline을 "위→아래 첫 일치"의 결정 함수로 규정(L63–100), L_SIGNAL 비억제 명시(§1.3 L108–112: headline이 validity failure여도 flag 유지 + artifact·report 양쪽 명시), P/PA interaction 표(L116–121), `REGIME_ERASES_SELECTIVITY` 삭제·descriptive화(L123–124). v0.2 MF-1의 요구("independent flag vector + deterministic headline + 모든 cell")의 뼈대는 갖췄다. `l_signal, m_control_pass_l, copy_only, full_only` 조합은 rule 7–12가 전부 덮으며(3·4 조합 검증 결과 누수 없음), `tail_driven`은 label 비변경 별도 flag로 일관적이다(§4.5).
  - **남은 결함 4건.**
    1. **rule 3 이중 라벨**(L74): `P_STEP100_NOT_VALID / REGIME_SENSITIVITY_LOST` — 어느 쪽을 표제로 할지 선택 규칙이 없고, `REGIME_SENSITIVITY_LOST`는 문서 어디에도 정의돼 있지 않다. §1.4(L120–121)와 L123–124는 `P_STEP100_NOT_VALID` 단일 사용을 가리키므로 문서 내부 모순. 같은 flag 조합에 후보 라벨이 둘이면 함수가 아니다. **이것은 v0.2.1이 새로 만든 결함이다**(v0.2 표는 cell당 단일 라벨이었다).
    2. **PA path-fail hole**: rule 2는 `not p_step100_path_ok`만 검사(L71–72), rule 4는 `pa_step100_path_ok`를 전제(L77–78). 따라서 (p_step100_path_ok ∧ p_valid ∧ ¬pa_step100_path_ok) 조합은 rule 5/6/13으로 낙하한다 — PA 학습 자체의 path 실패가 `M_CONTROL_NOT_VALID`(m_valid_pa 미계산) 또는 `INCONCLUSIVE_SMALL_N`로 오분류되는 cell. §1.4 표는 validity-only여서 path cell을 덮지 못한다.
    3. **NOT_ASSESSABLE headline 부재**: §1.5는 CI 불가·seed 누락 시 `NOT_ASSESSABLE` 기록과 "pass/fail로 바꾸지 않음"을 명령(L129–131)하고 §4.4도 common subset <15/20 → `NOT_ASSESSABLE`(L325)인데, precedence 어디에도 이 상태를 표제로 내는 규칙이 없다. 결과적으로 §1.5가 요구하는 상태가 rule 3(stat fail) 또는 rule 13으로 흡수되어 모순.
    4. **copy_only/full_only 미정의**(L49–50): flag vector에는 있으나 어디에도 정의가 없고, rule 9/10의 `copy_only and not full_only` 중복 논리가 이 정의에 의존한다(자연 정의는 `l_copy_signal ∧ ¬l_full_signal` / `l_full_signal ∧ ¬l_copy_signal`이나 문서가 고정해야 한다).
- 다음 단계:
  1. rule 3을 단일 라벨로 확정한다(§1.4 정합성상 `P_STEP100_NOT_VALID`). `REGIME_SENSITIVITY_LOST`를 쓰려면 정의·위치·표를 문서에 추가한다.
  2. rule 2를 P/PA 양쪽 path 실패로 확장하거나 rule 4 앞에 PA path 전용 rule(예: `PA_STEP100_NOT_VALID` path cell)을 추가한다.
  3. precedence에 NOT_ASSESSABLE rule(CI 불가/seed 누락/common-subset<15 → rule 11–13보다 앞)을 추가하고, copy_only/full_only 정의를 §1.1에 명시한다.
  4. 수정 후 §7 체크리스트의 "total decision function / precedence [x]"를 재확인한다. 현 시점의 [x]는 이르다.

### Q2. P/PA contract

- 판정: **conditional**
- 근거:
  - **step0**: P step0 = P0-regime(native + zero-LoRA, 동일 docs/donors), PA step0 = random adapter **별도 실행**, "P0를 PA step0으로 대체하지 않는다"(§2.2) — v0.2 MF-2의 "PA는 step0 reference가 없다"를 닫았다. P0는 historical reference로 보존해 PA step0의 대용 오용을 차단했다.
  - **movement/retention**: §2.3의 필드 세트(step0/step100 real/wrong CE copy·full, train CE first/last/last10, LoRA B norm, adapter delta norm, LR)와 `P_RETENTION`/`PA_RETENTION` descriptive + denominator null guard — "hidden gate 금지" 요구와 정합.
  - **ADAPTER_REGIME_LOSS**: §1.4에서 descriptive 라벨로 재정의하고 인과적 이름 `REGIME_ERASES_SELECTIVITY` 삭제 — v0.2 MF-1/2의 명명 문제 닫음.
  - **PA_VALID 연결**: §2.5 `M_VALID` = P_VALID AND PA_VALID 전제 + precedence rule 4/6 — "PA_VALID가 M_VALID/decision에 일관되게 연결 안 됨"을 닫았다. 단 PA path-fail cell은 Q1-2 결함으로 남는다.
  - **잔존**: 현 runner는 `make_adapter(seed)` 후 LoRA init 전 재시드가 없다(§0.2). §2.1의 "make_adapter(seed) 후 LoRA init 직전 `torch.manual_seed(seed)`" + "seed별 LoRA init 재현 test 필수"는 구현 단계 필수 사항이며, 구현·테스트 전에는 이 contract가 executable하지 않다.
- 다음 단계:
  1. §2.1 시딩 순서를 코드 + 재현 단위 테스트로 강제한다.
  2. interaction 표를 path/validity 4×4로 확장 검토해 Q1-2의 PA path cell을 포함한다.
  3. §2.3 movement 필드가 §6.3 artifact schema에 1:1 매핑되는지 구현 전 확인한다.

### Q3. P gate

- 판정: **conditional** (gate 자체는 약하나, 현 제약에서 유지가 정답)
- 근거:
  - `.05`는 P0 val mean 5.2375의 약 1%, train 3.7617의 약 1.3% — v0.2 리뷰의 "학습이 99%를 지웠는가만 검출" 지적은 유효하며, v0.2.1도 이를 부정하지 않는다.
  - 그러나 P0 수치는 v0.2 이전에 이미 판독됐고, 요청서 §8은 결과 후 threshold 변경을 금지한다. v0.2.1의 처방 — threshold 유지 + 의미 재라벨링("**post-training native-path sensitivity screen**", §2.4, "LoRA가 selectivity를 학습했다는 증거로 부르지 않는다") + step0/retention/movement 진단 필드 — 는 제약 내에서 유일하게 정직한 선택이다.
  - P_VALID는 copy·full **양쪽** CI lower > 0을 요구(§2.4)해 v0.1의 단일-endpoint 대비 강화됐다. P_VALID의 역할이 M_VALID 전제(§2.5)와 headline path로 제한되고 B0-B 경계(v0.2 §12)가 유지되므로, 약한 gate가 통과해도 B0-B로 직결되지 않는다.
- 다음 단계:
  1. `.05` 유지. 보고서 문구에서 P_VALID를 sensitivity screen으로만 부르는 것을 강제한다.
  2. gate 재설계가 필요해지면 결과 후 수정이 아니라 **새 사전등록**으로 분리한다.

### Q4. M contract

- 판정: **agree** (구현·테스트 조건부)
- 근거:
  - `M_CONTROL_PASS_L = M_PASS_POS_L AND M_PASS_NORM_L`(§3.4), "M_POS_MEAN-only pass는 pass가 아니다", M_GLOBAL은 rescue 불가(§3.4), POS-only는 `M_PASS_NORM_CONFOUNDED` descriptive(§3.6) — v0.2 MF-3의 "가장 약한 variant가 통과" 문제를 닫았다.
  - `M_VALID = M_PASS_POS(P) AND M_PASS_NORM(P) AND M_PASS_POS(PA) AND M_PASS_NORM(PA)`(§3.4) — quantifier가 명시됐다(MF-3 닫음). P/PA 하나라도 missing/CI 불가면 `M_NOT_EVALUABLE`.
  - **cohort 분리**: contributor eligible ≥10(§3.2 item 3)과 target common M cohort(L/P/PA 교집합) ≥15/20(§3.3)이 분리됐다 — "eligible ≥10은 train contributor 수"라는 MF-3 혼동 지적을 구조적으로 해소. <15면 `M_NOT_EVALUABLE`, pass/fail 금지, excluded doc·사유 기록.
  - **M_NORM**: whole K×512 Frobenius scale, per-row norm은 secondary 진단(§3.5), "strictly target-independent가 아니다; **magnitude-matched negative control**"로 정직 표기. norm 0/non-finite → `M_NOT_EVALUABLE`(§3.2 item 7). 결측 처리 규칙도 §1.5와 일관.
  - **reference/persistence**: full real K_real 고정, donor-cropped real CE는 M primary 배제(§3.1), final checkpoint hash가 manifest에 포함(§6.2) — MF-3의 real reference·checkpoint 닫음.
  - **잔존(구현 세부)**: `M_POS_MEAN[j] = mean_i A(h_i)[j]`, `len(h_i) >= K_real`(§3.2)은 **target별** K_real에 따라 contributor 집합과 길이가 달라지는 per-target 평균이다. §3.2가 "target doc별로 재계산"을 명시하지 않아 전역 mean 1개로 오구현할 여지가 있다. §6.3의 "M source IDs/eligible"이 per-target 기록인지도 확정이 필요하다.
- 다음 단계:
  1. §3.2에 "mean은 target doc별로 재계산된다"를 명시하고 per-target contributor IDs를 artifact schema에 고정한다.
  2. M leakage assert(val/target/donor 미사용)와 row-permutation/perturbation invariance test를 구현 DoD에 고정한다.
  3. M_NORM이 per-row scale로 오구현되지 않게 whole-matrix Frobenius 비율 단위 테스트를 추가한다.

### Q5. Statistics

- 판정: **conditional**
- 근거:
  - **unit**: seed 평균 선행 후 document bootstrap, "3 seeds × 20 docs를 60 independent units로 취급하지 않는다"(§4.1), 1,000 resamples, pooled + per-seed 표(§4.2) — MF-4 첫 항목 닫음.
  - **L>F**: paired per-doc difference(`L_doc_delta − F_doc_delta`), 양쪽 endpoint 각각(§4.3); L_COPY/L_FULL_SIGNAL에 paired mean > 0과 2/3 seeds(**seed-level mean** >0) 포함 — v0.2 §6.2 정의와 정합, MF-4 닫음.
  - **documents_positive/seeds_positive 분리** + "seeds_positive라는 이름을 문서 수에 쓰지 않는다"(§4.2) — MF-4 닫음. 단 runner `bootstrap_paired`는 여전히 문서 수를 `seeds_positive`에 담으므로(§0.2), 신규 PM 코드가 이 필드를 재사용하지 않게 하는 구현 규칙+테스트가 필요하다.
  - **missingness**: copy/full eligible 불일치 시 common-document subset primary + full-only/copy-only counts 별도(§4.4), common subset <15/20 → `NOT_ASSESSABLE` — MF-4 닫음. 단 NOT_ASSESSABLE의 headline mapping은 Q1-3 결함으로 남는다.
  - **heavy-tail**: mean/median/p05/p95/top-3 share/leave-top-3-out, `tail_driven` 별도 flag(§4.5) — MF-4 닫음. bootstrap RNG seed 기록(v0.2 §7 유지)과 "20-doc bootstrap은 anti-conservative 가능; CI를 확정적 증거로 사용하지 않음"도 유지된다.
- 다음 단계:
  1. documents_positive/seeds_positive를 별도 필드로 구현하고 기존 `bootstrap_paired` 재사용 금지를 테스트로 강제한다.
  2. seed-averaged per-doc bootstrap이 20 unit으로 도는지 단위 테스트한다(60-unit 회귀 방지).
  3. NOT_ASSESSABLE headline rule을 Q1 수정에 포함한다.

### Q6. Debug

- 판정: **agree**
- 근거:
  - unregistered seed **20261111**, max **5 updates/arm**, F/L/P/PA mechanics-only, **no M outcome labels**, M은 synthetic fixture + 1회 mechanics probe(§5.1) — v0.2 MF-5("registered seed 100-step 결과 노출")를 구조적으로 차단했다.
  - v0.2.1 commit hash + code/test commit hash freeze, debug의 cap 포함(§5.1, §6.1), per-phase timing(§5.2).
  - 금지 목록이 명시적: registered seed 100-step 사용, debug label의 headline 사용, debug로 3-seed 자동 승인, seed/donor/step/LR 탐색(§5.3). debug 허용 검사 범위(path/shape/finite/64 modules/mode/seed 재현/same-position CE atol 1e-5/metric alignment/provenance/M synthetic tests/label function/timing)도 합리적이다(§5.2).
- 다음 단계:
  1. debug runner에 seed ∈ {20261108, 20261109, 20261110} 배타 assert를 기계적으로 추가한다.
  2. debug artifact에 "MECHANICS_ONLY / NOT_A_RESULT" 마커와 label·pass-fail 필드 부재 assert를 넣는다.
  3. debug per-phase timing으로 3-seed 시간 외삽을 산출해 Q7의 cap 리스크를 사전 검증한다.

### Q7. Cap/artifact

- 판정: **conditional**
- 근거:
  - cap은 검증 가능한 구조다: 12 trained units, ≤1,200 updates, wall-clock **≤2h from process start**, 6 threads, GPU 없음, **debug 포함**, 자동 연장 없음, wall-clock과 process CPU time 동시 기록, 초과 시 중단·보고(§6.1). runner의 `torch.set_num_threads(6)`와 일치.
  - manifests(§6.2): prereg/code commit hash, data/split hash, tokenizer/model hash, seeds, donor policy, LR, max lengths, **final adapter/LoRA checkpoint hash(M replay용)** — MF-6 닫음. artifacts(§6.3): flags vector, headline, per-doc deltas·eligible counts, donor IDs/K/crop, metric_alignment, train_mode_policy, movement fields, M source IDs/eligible/m_eligible/norm, generation telemetry, timings, `test_split_used:false`.
  - **리스크**: generation telemetry(v0.2 DoD D2: 12 units × 20 docs greedy, CPU)와 M replay 평가 비용이 cap 항목화에 명시적으로 없다. mT5-small CPU에서 2h wall-clock 안에 전부 들어오는지는 미검증이며, 요청서 Q7이 정확히 이 지점을 묻는다. debug의 per-phase timing이 이를 검증할 유일한 사전 데이터다. 초과 시 자동 연장 없이 중단·보고가 원칙이므로 데이터 손실 위험은 통제된다.
- 다음 단계:
  1. debug per-phase timing으로 3-seed 총 시간을 외삽하고, generation이 병목이면 3-seed gate에서 명시적으로 다룬다.
  2. wall-clock 측정 기준(process start)과 CPU time 측정 위치를 manifest에 명시한다.

### Q8. 남은 Must-fix

- 판정: **conditional** — v0.2 MF-2~6은 닫혔고, MF-1(total function)은 부분 닫힘. 신규 결함 1건(rule 3 이중 라벨).
- 근거: 아래 ranked list. v0.2 항목과의 대응: MF-2 → §2.1–2.5(step0/retention/movement/descriptive cell)로 닫음(단 PA path cell은 Q1-2로 잔존), MF-3 → §3.2–3.6·§6.2로 닫음, MF-4 → §4.1–4.5로 닫음, MF-5 → §5로 닫음, MF-6 → §6으로 닫음. P gate 약함(MF-2의 `.05`)은 threshold 유지 + 재라벨링으로 "닫은 것"이 아니라 "제약 내 최선 처치"다(Q3).

**Must-fix (ranked)**

| 순위 | 항목 | 위치 | 성격 |
|---:|---|---|---|
| 1 | rule 3 이중 라벨 `P_STEP100_NOT_VALID / REGIME_SENSITIVITY_LOST` — 단일 라벨로 확정 | errata L74 | **신규 결함, 동결 전 필수** |
| 2 | PA path-fail cell 누락(p_valid ∧ ¬pa_step100_path_ok가 M_CONTROL_NOT_VALID/INCONCLUSIVE로 낙하) | L71–78, §1.4 | 잔존, 동결 전 필수 |
| 3 | NOT_ASSESSABLE headline rule 부재(§1.5·§4.4와 §1.2 모순) | L129–131, L325 | 잔존, 동결 전 필수 |
| 4 | copy_only/full_only 정의 부재(rule 9/10 실행 가능성) | L49–50, L93–96 | 잔존, 동결 전 필수 |
| 5 | runner `bootstrap_paired.seeds_positive`(문서 수)의 신규 코드 재사용 금지 + 별도 필드/테스트 | runner, §4.2 | 구현 규칙 |
| 6 | M_POS_MEAN per-target 재계산 명시 + per-target contributor IDs artifact | §3.2, §6.3 | 구현 세부 |
| 7 | debug seed 배타 assert + MECHANICS_ONLY 마커 + label 필드 부재 assert | §5 | debug 안전 |

- 다음 단계:
  1. 1–4를 반영한 errata 수정(문서 변경이며 threshold·seed·donor·step 변경 아님)을 commit한다.
  2. 5–7을 구현 DoD와 debug DoD에 명시한다.
  3. 수정 후 §7 체크리스트를 재점검한다.

### Q9. 구현 승인

- 판정: **conditional**
- 근거:
  - 구현은 v0.2.1 동결(Must-fix 1–4 반영 후 commit hash 고정)을 선행해야 한다(errata §0 "코드는 이 errata 승인 후에만 작성"). 현 runner에는 `pm-diagnostic`이 전혀 없으므로 구현 자체는 적법한 승인 대상이며, 구현 전 코드 작성 금지 규칙도 지금까지 지켜졌다.
  - 구현 전 반드시 있어야 할 test/contract:
    1. **precedence/truth-table 전수 단위 테스트** — flag 조합 전체(특히 PA path fail, NOT_ASSESSABLE, rule 3 해소 후 셀)와 **L flag 비억제**(headline이 validity failure여도 `l_*` flag 유지) 검증.
    2. P/PA LoRA-init **seed 재현 테스트**(§2.1) — 동일 seed 재실행 시 LoRA init 동일.
    3. 64 modules / mode policy(P/PA 포함: base eval, trainable base = 0) 테스트 — `set_training_mode` 확장.
    4. P step0 == P0 path 동등성, zero-LoRA equivalence(atol 1e-5), PA random-adapter step0 결정성 테스트.
    5. M leakage assert + row-permutation/perturbation invariance + `M_NOT_EVALUABLE` 트리거(cohort<15, eligible<10, non-finite) + M_NORM whole-Frobenius scale 테스트.
    6. documents_positive vs seeds_positive 분리, seed-averaged bootstrap(20 unit), common-subset <15/20 → NOT_ASSESSABLE 테스트.
    7. P_RETENTION/PA_RETENTION null guard, §6.3 artifact schema 완전성, `test_split_used:false` assert.
- 다음 단계:
  1. Must-fix 1–4 반영 → v0.2.1 동결 commit → 해시를 구현 계약에 고정한다.
  2. 위 1–7을 구현 DoD로 명시하고 전부 녹색이어야 다음 단계로 간다.
  3. 구현 diff는 threshold/seed/donor/step을 일절 변경하지 않아야 한다.

### Q10. 1-seed mechanics debug

- 판정: **conditional**
- 근거:
  - 승인 가능하다: 구현+unit tests 통과 후의 unregistered-seed mechanics debug는 §5가 3-seed 결과 노출 경로를 차단한다(5 updates, no labels, commit freeze, 등록 시드 금지, 3-seed 자동 승인 금지).
  - debug를 3-seed gate로 오인하지 않게 하려는 artifact가 핵심이다:
    1. debug manifest(v0.2.1 commit + code/test commit + `seed=20261111` 기록),
    2. `MECHANICS_ONLY / NOT_A_RESULT` 마커 + label/pass-fail 필드 부재 assert,
    3. synthetic M fixture 결과 + 1회 mechanics probe 결과(pass/fail label 없음),
    4. per-phase timing + 3-seed 시간 외삽,
    5. seed 배타 assert의 실행 기록.
- 다음 단계:
  1. 위 1–5를 debug DoD로 명시한다.
  2. debug 실행 경로가 headline/label 함수를 호출하지 않음을 테스트로 확인한다.
  3. debug 결과 보고서에 "3-seed 결과가 아니다"를 명기한 상태로만 저장한다.

### Q11. 3-seed / B0-B 경계

- 판정: **agree**
- 근거:
  - **3-seed 조건**(본 라운드 기준): (1) Must-fix 1–4 반영 v0.2.1 동결, (2) 구현+unit tests 전부 녹색, (3) mechanics debug artifact가 §5.2 허용 검사 전부 통과 + cap 외삽 합리적, (4) 별도 명시적 승인. 이 넷은 모두 필요조건이다.
  - **B0-B 조건**은 v0.2 §12 그대로다(필요조건, 충분조건 아님): P/PA valid, M valid + L M pass, L_SIGNAL(copy+full), heavy-tail robustness, leakage/mode/metric 실패 없음, artifact 완전성 — 그리고 별도 사전등록·승인.
  - **경계 유지**: 유지된다. v0.2.1은 threshold/seed/donor/step을 바꾸지 않고(§0), 자동 진행 조항을 추가하지 않았으며, v0.2 §12의 금지 조건(ASSAY_INVALID, M_CONTROL_NOT_VALID, L_SIGNAL_M_CONTROL_FAIL, INCONCLUSIVE_SMALL_N의 "scale하면 해결" 정당화 등)을 폐기하지 않았다. 3-seed가 `EXPLORATORY_L_SIGNAL`로 끝나도 B0-B는 자동 승인되지 않는다.
- 다음 단계:
  1. 3-seed gate 요청 시 debug artifact 목록 + unit-test 결과를 첨부하도록 절차화한다.
  2. B0-B는 반드시 새 사전등록 문서로 분리한다(결과 후 threshold 변경 금지 원칙 유지).

### Q12. 최종 판정

- 판정: **NARROW**
- 근거: v0.2.1은 v0.2 MF-2~6을 닫아 동결·구현·debug 단계 진입이 가능한 수준에 도달했으나, 검토 대상인 total decision function 자체에 결정성 결함 4건(신규 1건 포함)이 남아 있다. 구조적 방향이 옳고 잔여 결함이 문서 수정으로 닫히는 범위이므로 STOP이 아니며, 3-seed·B0-B가 열려 있지 않으므로 CONTINUE도 아니다.

```text
최종 판정: NARROW
v0.2.1 동결: 조건부 승인 — Must-fix 1–4(rule 3 단일화, PA path cell,
  NOT_ASSESSABLE headline rule, copy_only/full_only 정의) 반영 문서 수정 후
  commit/freeze. contract tighten이며 threshold/seed/donor/step 변경 아님.
구현+unit tests: 동결 후 승인(Q9 테스트 목록 1–7을 DoD로).
mechanics debug: unit tests 녹색 후 승인(Q10 artifact 1–5 포함, seed 20261111).
3-seed: 미승인 — 별도 gate(debug artifact + tests + 명시적 승인).
금지 범위: B0-B/B1/B2/Stage C 자동 진행, test 163 개봉, P1 사용,
  T5Gemma2 재개(D-108 STOP 유지), threshold/seed/donor/step 변경,
  debug label의 headline 사용, 등록 시드(20261108/09/10)의 debug 사용,
  P0의 graded content use 해석.
최대 compute: v0.2.1 §6.1 그대로 — 12 trained units, ≤1,200 updates,
  wall-clock ≤2h(debug 포함), 6 threads, GPU 없음, 자동 연장 없음,
  wall+CPU time 기록.
test 163 지위: sealed, 변경 없음.
```

**잘못된 전제**

1. 요청서 §3 요약과 errata §7 체크리스트의 "total decision function 완료 [x]" — 결정성 결함 4건으로 현 문서는 아직 total이 아니다. 동결 전에 닫아야 한다.
2. "v0.2.1이 Must-fix를 닫았는가"는 이분법이 아니다: MF-2~6은 닫았고, MF-1은 구조는 갖췄으나 결정성 결함으로 부분 닫힘이다.
3. "54 tests"는 historical evidence이며 PM 행위(decision table, M, cohort, seed 재현)를 커버하지 않는다. 현재 `test_c5_b0_metric.py`는 7 method고 PM 테스트는 없다. 이는 요청서의 오류는 아니지만 승인 판단에서 "테스트가 준비됐다"로 읽으면 안 된다.

---

## 3. 제한

- 이 보고서는 승인이 아니라 독립 검토 의견이다. 최종 결정은 요청자 몫이다.
- 본 라운드에서 Phase 6/B0-B/B1/B2/Stage C는 승인되지 않았다. 3-seed도 승인되지 않았다.
- 학습·평가를 실행하지 않았고, test 163을 열지 않았으며, P1·외부 API를 사용하지 않았다. 저장소 수정은 이 보고서 파일 1개뿐이다.
- P0 수치는 `reports/provenance/C5_b0a/p0_native_sanity.json`에서 재확인했으나, 이는 P0 산출물의 내부 정합성 확인일 뿐 재실행 검증이 아니다.
- 수치 예측(예: 2h cap 내 완료 가능성)은 실행 없이는 확정할 수 없으며, debug per-phase timing이 유일한 사전 검증 수단이다.