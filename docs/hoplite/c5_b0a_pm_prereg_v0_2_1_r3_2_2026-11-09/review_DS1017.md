Review complete. Wrote `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r3_2_2026-11-09/review_DS1017.md` (295 lines, untracked, the only change; HEAD unchanged at `6aac52f`).

**Sync:** `git fetch origin` succeeded; `git pull --ff-only origin main` → `Already up to date.` HEAD = `6aac52f0c486f4137a47cf4e173be77e81975a80` ("docs: add C5 P/M v0.2.1-r3.2 review request"); the request's `44bbef6` is its parent, so the plan under review matches HEAD. Work done read-only — no training, no eval, no test 163, no P1, no subagents.

**Independently re-verified (not taken on trust):** preflight `sha256 = 3ee3f1ca…69837af` matches; `k_m_l=753 / 16 contributors / 15 targets / common_ok=true / full-K 11`, `zero_margin=true` (K=754 → 14); P0 recomputed from JSON — train 3.7617 (median 4.0680, 14/20), val 5.2375 (median 2.9739, 18/20), val `top3_share=.4862`, `leave_top3_mean=3.1659`; `ln(250100)=12.4296 < 12.7022/13.2352`; cap arithmetic 1,200+4+0=1,204 and 120+15+20=155; 54 tests total but **7** in `test_c5_b0_metric.py` and **0** PM contract tests; `runner/c5_pm_stats.py` absent; runner still `--arm {frozen,lora}` only.

## Q1–Q12

| Q | 주제 | 판정 | 핵심 근거 |
|---|---|---|---|
| Q1 | Total factored contract | **conditional** | validity/dispatch는 total이고 §5.2 label 19개 전부 도달 가능. 그러나 §6.3의 “M pass L false + control PASS”는 §4.3(`m_pass_l=false → M_CONTROL_FAIL`)과 모순 → §6.4 “every named cell” 불만족 |
| Q2 | L predicate / fixtures | **conditional** | `.05` copy / `>0` full 회귀는 **완전히 닫힘**(v0.2 §6.2 = errata §4.3 = r3.2 §9.2). fixture 16–18은 §2.3/§4.3/§5.3과 손검산 일치하나 파생값(`m_pass_l`,`m_valid`)을 주입 |
| Q3 | M preflight / cohort | **conditional** | 수치 전부 정합. 다만 zero-margin(K=754→14) knife-edge, M cohort가 길이 선택, real CE > ln\|V\|라 절대 CE 보고 필요 |
| Q4 | M builder / M_NORM / endpoint / replay | **conditional** | 공식·per-target Frobenius는 상속과 일치. 그러나 `M_POS_MEAN` 구성식과 **M primary reference 규칙 탈락** → 현행 runner(donor-crop)로 구현하면 상속 위반. `endpoint_ok` 이중 정의 |
| Q5 | PA | **conditional** | 명명·금지 label·`PA_RETENTION` 비gate는 적절. **scale/geometry caveat 0건**, PA step0 문장 충돌 |
| Q6 | Cap / D0 / D1 | **conditional** | 1,204 updates / 155 min / 96=0.8×120 **산술 정확**, D1 ledger 완결. 단 **F/L/P/PA arm 표 부재** |
| Q7 | Statistics | **conditional** | 상수·partial endpoint 규칙 충분. `tail_driven` 기준 소실, seed 집합 미기재, 금지 P0 helper 생존 |
| Q8 | 남은 Must-fix | **agree** | 9개 blocker 중 4개 완전/4개 부분/1개 신규, r3.2가 새 문제 4건 유발 |
| Q9 | 동결·구현 승인 | **disagree** | MF-1~4가 코드로 고정될 결함. §16 자체 규칙대로 text-only r3.3 |
| Q10 | D1 / 3-seed 경계 | **conditional** | 경계는 강함. checklist 7항목 누락(seed 집합, 7-phase 완전성, builder artifact 등) |
| Q11 | B0-B | **agree** | hard false 유지. predicate 재진술 제공(단 `tail_driven` 정의 선행) |
| Q12 | 최종 판정 | **NARROW** | — |

## Must-fix (ranked)

1. **MF-1 (blocker)** — §6.3 unreachable cell 미정정(468행 vs §4.3). DoD를 원리적으로 불만족.
2. **MF-2 (blocker)** — `tail_driven` 기준 삭제: r3/r3.1 `leave_top3_mean<=0 or top3_share>.50` → r3.2 “known positive criterion”. B0-B가 **정의되지 않은 predicate**에 hard gate. P0 val `.4862`는 `.50`에서 0.014 → outcome-relevant.
3. **MF-3 (blocker)** — `M_POS_MEAN[j]=mean_i A(h_i)[:K_M][j]`(shape `K_M×512`) 및 “M primary reference = target prefix at K_M, donor-crop 금지” 탈락. runner가 이미 반대 동작.
4. **MF-4 (blocker, 구현)** — F/L/P/PA arm 표 부재(12 units·1,200 updates의 전제).
5. MF-5 (high) fixture 파생값 주입 · MF-6 (mod) §15 → `§1.4` dangling · MF-7 (mod) registered seed 집합 · MF-8 (mod) hash 길이 prefix/golden 상수 · MF-9 (mod) `bootstrap_paired` seed 20261108 + `seeds_positive` mislabel 생존 · MF-10/11/12 (low) caveat·`endpoint_ok` 이중정의·cell 소실.

## Final verdict: **NARROW**

r3.2 동결 / 구현+unit tests / D0 / D1 / 3-seed / B0-B·B1·B2·Stage C — **모두 미승인**. 금지: 학습·평가, test 163, P1·external API, T5Gemma2(D-108 STOP), 결과 후 threshold/seed/donor/step/LR 변경, Phase 6 자동 진행. Compute this round: **0 updates / 0 min** (r3.3도 text-only 상한 권고). 승인된 유일한 다음 단계는 **MF-1~MF-12만 고친 text-only r3.3 → 재검토**입니다.