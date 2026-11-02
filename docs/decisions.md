# 결정 로그 (append-only)

기준 문서: `docs/plan_v0_5.md` (v0.5, 2026-11-01). 문서의 `eg2-lab/`은 이 저장소 루트를 뜻한다.

| ID | 날짜 | 결정 | 근거·비고 |
|---|---|---|---|
| D-001 | 2026-11-02 | 프로젝트 루트 = `C:\code\unigem`, git 저장소로 관리 | 사용자 지시(경로 정정: unige → unigem). 문서 §14의 `eg2-lab/` 경로를 이 루트로 매핑 |
| D-002 | 2026-11-02 | 기존 운영 자산(`C:\code\eg2-langidentifier`, `%LOCALAPPDATA%\jev-mem`)은 **읽기 전용 참조**만. 프로젝트 venv는 `.venv`(Python 3.12)로 분리 | 문서 §0-3, §9 A0 |
| D-003 | 2026-11-02 | Phase A0·A1을 read-only로 선행 수행 (코드 산출 없음, 측정·기록만) | 문서 §9 A0·A1. A1 결과 G-A1 FAIL 확인 → A2 필요 |
| D-004 | 2026-11-02 | VPS는 **계정 B**를 사용하며, **4대를 추가 생성해 5대 구성** (eq-2 ~ eq-5) | 사용자 승인(2026-11-02). 계정 B 기존 `eg2-1` + 신규 4대 = 5대, 전부 4 vCPU / 8 GiB / 20 GiB 목표 |
| D-005 | 2026-11-02 | A2 export의 1차 실행 호스트는 **로컬 PC** (VPS 전송 비용 회피, RAM 부족/OOM 시에만 vps-1로 이관) | 문서 §9 A2는 vps-1 우선이나 "RAM 부족 시 로컬" 허용. 로컬에 체크포인트 사본이 있어 역방향이 더 저렴 |
| D-006 | 2026-11-02 | A2의 원본 체크포인트는 **HF `google/embeddinggemma-2` revision `f9972ac2…5a1e`를 새로 다운로드**해 쓴다. 로컬 사본은 파생본(바이트 불일치)이므로 export 원본으로 쓰지 않는다 | provenance 실측: tokenizer 해시 일치, config는 `transformers_version`만 다름, `model.safetensors`는 같은 크기·다른 SHA256(재저장본 추정) |
| D-007 | 2026-11-02 | 다운로드한 체크포인트의 `model.safetensors` SHA256이 HF blob `197a3296…53d79`와 **일치**함을 확인. 이후 이 사본을 export 원본으로 고정 | `data/models/embeddinggemma-2-f9972ac2/` (git 미추적) |
| D-008 | 2026-11-02 | ~~오디오 타워 export는 dynamo exporter만 동작한다~~ → **D-010에서 정정**: dynamo도 dynamic_axes로는 실패하며, 정적 shape에서만 동작 | 오디오 forward가 커스텀 autograd 연산을 사용. 텍스트는 dynamo로 성공 |
| D-009 | 2026-11-02 | 오디오 다층 hidden은 **재수출 대신 기존 q8 그래프에 중간 텐서를 출력으로 추가**해 확보한다 (`eg2_audio_q8_layers.onnx`). 원본 불변, 파생 사본만 수정 | dynamo export가 로컬·VPS(8GiB) 모두 14~17분+ 무출력. 그래프 수술 결과 PyTorch 대비 cos 0.99945~0.999998, 패딩 불변 1.0. FP32 오디오 그래프는 미확보 |
| D-010 | 2026-11-02 | 오디오 **FP32 연구용 그래프**는 `dynamo + 정적 shape(--static) + optimize=False`로 export한다. legacy는 `unfold` 미지원으로 사용하지 않는다 | 원인 4중 규명: ① legacy `autograd_inlining=False` 필요 ② `F.pad(value=None)`이 None 상수로 굳음 ③ legacy `Tensor.unfold` input size 미추적 ④ dynamo+`dynamic_axes` symbolic 제약 정체. 해결 후 cos 1.0, NaN 0 (`reports/A2_export_audio_research.md`) |
| D-011 | 2026-11-02 | **CP1 D1=A 승인**: G-A3L FAIL은 그대로 기록하고, id↔ms 1건만 "비확신 모호 구간" 예외로 승인. 게이트 임계값 불변 | 사용자 승인. 불일치 margin 0.0094/0.0068, 확신 오판 0. Q8에서는 44/44 |
| D-012 | 2026-11-02 | **CP1 D3 승인**: 상주 EG2는 **텍스트+오디오 한 세션**, Q8(q8-al4), 스레드 6, 연구용 전체 층 노출(운영 층 축소는 B2 이후) | 사용자 승인. 비전 타워는 C1에서 추가, RAM 상한은 G-D에 따라 측정만 |
| D-013 | 2026-11-02 | **CP1 D5=A 승인**: 오디오 연구용 FP32 그래프는 500/1600/3000 mel 3종. 런타임은 가장 가까운 긴 그래프에 zero-pad + mask | 사용자 승인. 그래프당 1.22GB, 디스크 여유 109GB |
| D-014 | 2026-11-02 | **CP1 D6=A 승인**: t1600에 대해 **12층 전체** export (`--layers 0..11`) | 사용자 승인. C2-B 층 조합 스윕 즉시 수행 가능 |
| D-015 | 2026-11-02 | **CP1 D7 승인**: G-A3S(Notesoop 특징 재현), G-C2a(Q8 특징 CER 상대 증가 ≤10%)를 **게이트로 승인** | 사용자 승인. 사전등록 원칙 유지 — 결과 확인 전 임계값 고정 |
| D-016 | 2026-11-02 | **Phase V 실행 완료 (G-V0 PASS)**: 5대 네이티브 venv, lock 단일(`6cccf5e9…`), 정합 cos 1.0, 가드 4종(메모리·타임아웃·디스크·P1) 실측 | `reports/V0_hosts.md`, `V1_env.md`, `V2_runner.md`. 러너 `runner/run_job.py` |
| D-017 | 2026-11-02 | **B1 실행**: P0 코퍼스 1,050문장(FLEURS 600·합성 300·오타 150), 8개 층 선형 프로브. l00 99.57%/숫자 100%, l04 94.51%/92.42%, last 69.86%/84.13% | 토큰 층화 분할 기준. H1 지지, H2 부분 지지. 식별자 토큰은 토크나이저 분해로 0개 → 지표 재정의 필요 (`reports/B1_probing.md`) |
| D-018 | 2026-11-02 | **식별자 span 지표 도입·측정**(CP2 옵션 4): 전용 합성 300문장/177 span. l00 **95.5%**, l04 85.3%, l08 52.0%, last 78.0%, l00+l04 94.9% | 약점은 무작위 hex(sha 66.7%, token 87.1%). version/path/date/host/model은 l00에서 100%. `train/b1_span_eval2.py`, `logs/B1_span.jsonl` |
| D-019 | 2026-11-02 | **Addendum A 수신·승인**: `docs/addendum_A.md` (400줄, SHA256 `df46077763ab29568fffd31b64bf9598efe9f36766aadd1dd807e293ec09d920`). AM-1~AM-4를 사용자 전달로 승인된 개정으로 기록. 충돌 시 v0.5보다 본 애더넘 §A-2~A-9 우선 | 사용자 직접 전달. 임계값 불변, 대상·지표·표본 정의만 명확화 |
| D-020 | 2026-11-02 | **AM-1 (G-A3L-R) 사전 등록**: 판정 대상 = **Q8 운영 경로**(텍스트·오디오 q8 pooled), 평가 세트 = 운영 220클립(`data/raw/fleurs_test`, 22언어×10), 일치율 ≥99% + 확신 오판 증가 0 유지. PASS-R은 신규만 오답 0 + 확신 오판 0 + 건별 보고 + **사용자 확인** 시에만 인정 | 측정 **전** 기록 완료. 44클립 FP32 결과는 이력으로만 |
| D-021 | 2026-11-02 | **AM-2**: G-B1 식별자 지표를 토큰 단위 → **문자 오프셋 span exact**(임계값 95% 불변)로 정식 개정. 기존 177 span은 탐색적 결과, 판정은 B1.5-1 신규 홀드아웃만 사용 | n=0 지표 결함 수정. 결과 확인 후 개정임을 이력에 명시 |
| D-022 | 2026-11-02 | **AM-3**: 모든 게이트에 최소 표본·신뢰구간 규칙 적용. 표본 부족 시 PASS 대신 **INCONCLUSIVE**. G-A3L-R 220(CP), G-C1 ≥100(권장 150), G-C2 ≥300문장, G-C4 ≥600문장, G-C5 ≥300슬롯 | rule of three(3/n) 병기. `gates.md`에 표 추가 |
| D-023 | 2026-11-02 | **AM-4**: F4/F5 지표 정의 고정 — 슬롯 strict/canonical 모드, 신규 슬롯=환각, 정상 문장 보존률·과교정률 정의, coverage-정밀도 곡선 보고 | `eval/slot_norm.py` + 단위 테스트 ≥50건 통과 후 측정 |
| D-024 | 2026-11-02 | **G-A3L-R 판정: FAIL** — 220클립, Q8 일치 216/220(98.18%, CP 95.41~99.50%), 확신 오판 21→23(+2), 신규만 오답 3. FP32도 98.18%(오판 21/21) | Addendum A §A-2.3에 따라 **Q8 운영 그래프 교체 보류**. CP2' 사용자 결정 대기 (`reports/G-A3L-R.md`) |
| D-025 | 2026-11-02 | **B1.5-0 완료**: `tok_h_l00`은 임베딩이 아니라 **decoder layer 0 출력**(HF hidden_states[1], cos 0.99998; 임베딩과는 0.39). 모델은 24층/512dim/2048hidden | B1의 l00 결과는 실제 표면 보존 결과. 단 24층 중 1층(`reports/B1_5_0_layer_definition.md`) |
| D-026 | 2026-11-02 | **A-7.2/A-7.3 측정**: 오디오 q8 RTF 0.030~0.032(5/16/30초, p50 149/513/962ms), 텍스트 Q8 679MB 중 임베딩 테이블 536.9MB(79%) | F-11·F-10 확인. 임베딩 양자화 실험은 후속(`reports/A7_audio_q8_latency.md`, `A7_embedding_table.md`) |
| D-027 | 2026-11-02 | **C0 최종**: T5Gemma2 접근 승인 후 확인 — vocab 동일(262,144), 공유 문자열 262,124이나 **id 불일치 6,186개** + `<eos>` 차이 → **H4 기각**. 디코더 hidden 640/18층/bf16 0.52GB | id 정렬 없이 C3 설계. `reports/C0_feasibility.md` |
| D-028 | 2026-11-02 | **C2-A0 완료**: Notesoop 라이선스 Apache-2.0(데이터 약관 미확인), 특징은 `audio_tower→lm.norm→projection[:256]→L2`(256d bf16), reader Conformer 10층/384/25k CTC, 청크 16s+1s | 우리 ONNX `aud_out_proj` + projection 슬라이스로 **특징 재현 가능**(G-A3S). `reports/C2_A0_notesoop.md` |
| D-029 | 2026-11-02 | **A-9.1 카나리(텍스트) 통과**: VPS에서 동일 체크포인트로 export → 20입력 cosine FP32 **1.0**, Q8 **최소 0.99917/평균 0.99979** | 오디오 q8은 원본 그래프 부재로 미검증. `reports/A9_canary_parity.md` |
| D-030 | 2026-11-02 | **C-D0 1차 조사**: Zeroth CC BY 4.0(즉시), FLEURS/Common Voice 공개, AI Hub·NIKL은 신청·약관 확인 필요. C4는 규칙 합성 우선, C5는 합성 격차 | LLM API 합성 필수 항목 없음 → G-DATA 제안서 보류. `reports/C-D0_public_data_survey.md` |
| D-031 | 2026-11-02 | **B1.5-2 코퍼스 v2 보강 완료**: 4,695문장, 토큰 198,317, 8층 캐시 1.62GB. 자연문장 각 300/60 충족, 식별자 문장 800(고유 731), 오타 600쌍, 길이 398 | 구어체 267·길이 2건 부족은 근소. B1.5-1 착수 가능 (`reports/B1_5_2_corpus.md`) |
| D-032 | 2026-11-02 | **B1.5-1 프로브 v2(잠정)**: 임베딩 테이블 공유, 129,407 토큰/14,789 어휘. l00 0.8856, l04 0.8175, last 0.4438 (test) — **단조 감소** | 시드 3·전체어휘 4,096표본. G-B1.5-a 잠정 PASS (`reports/B1_5_1_probe_v2.md`) |
| D-033 | 2026-11-02 | **B1.5-3 완료: G-B1.5-b FAIL(1/3)**. T1 l04 +10.6%p(CI +3.4~+17.3) 통과, T2 +1.87%p(CI +1.28~+2.48) 미달, T3 −0.67%p(천장) | F4에는 l04 근거, 게이트는 미충족. `reports/B1_5_3_context_value.md` |
| D-034 | 2026-11-02 | **G-B1.5-a FAIL** — l00 0.8856, l04 0.8175 (<0.98). B1.5-4 디코더는 상위 게이트 FAIL로 미수행 | 표면 보존 기준 미달. `reports/B1_5_4_copy_fidelity.md` |
| D-035 | 2026-11-02 | **B1.5-5 완료: G-B1.5-c PASS** — FP32→Q8 하락 l00 0.043%p, l04 −0.059%p (기준 ≤2%p) | Q8 특징이 FP32와 사실상 동등. `reports/B1_5_5_q8.md` |
| D-036 | 2026-11-02 | **B1.5-6(부분)**: 길이 구간별 정확도 하락 없음(l00 0.886~0.911). 접두사 3종은 모델 카드 문자열 미확인으로 보류 | `reports/B1_5_6_length_prefix.md` |
| D-037 | 2026-11-02 | **Addendum B 수신·CP2 결정**: SHA256 `7a5201d22566fd2db256cab62a6ce87203151ecd0dc9f505bcef4600109ee03f`. CP2 질문1은 **A′+파일럿**(R1/R2/R3/P1 수행, B1.5-4 보류, 폐기는 B-12 판정표), 질문2는 **C2-A1·F4 파일럿 병렬 → C1 PyTorch → C3**. CP2는 R1/R2/P1 후 CP2′로 재개 | `docs/addendum_B.md` |
| D-038 | 2026-11-02 | **AM-5/AM-6 채택**: 게이트 정정은 (i) 프로토콜 준수 재측정, (ii) VR-1 무효 과제 1회 교체만 허용, (iii) 임계값 완화 불허. 모든 보고서에 사전 요구 대비 이행 표 + `INCONCLUSIVE(프로토콜 미준수)`/`INVALID-MEASUREMENT` 라벨 | B1.5 기존 보고서에 소급 적용 |
| D-039 | 2026-11-02 | **사전 선언 등록(측정 전)**: T3′(자연문장 5유형, 테스트 ≥600), T1 확장(오타 ≥1,500쌍, 양성 ≥300, BL-2 추가), P1 F4 파일럿(H1/H1b vs H2~H5, AUPRC +3%p/10% 데이터 +5%p/오탐률), H4′(문장 단위 분절 일치 ≥99.5%) | `docs/gates.md` |
| D-040 | 2026-11-02 | **R1 완료: G-B1.5-a = PASS(l00) / FAIL(l04)**. 폐쇄형 릿지+전체어휘: l00 0.9992(CI 0.9989~0.9995), span 98.7~100%; l04 0.8504, span 44~88%. 이전 0.8856은 최적화 부족(≈95스텝) | 후보 층 l00 확정. `reports/R1_B1_5_1_rerun.md` |
| D-041 | 2026-11-02 | **R2 완료: G-B1.5-b FAIL(1/3)**. T1-exp +5.60%p(CI +2.41~+8.97) PASS, T2 +1.87%p FAIL, T3′ +0.89%p(CI +0.07~+1.64) FAIL | B-12 유효 FAIL → 텍스트 hidden 폐기 권고 트리거. P1 결과는 CP2′에서 병행 보고 (`reports/R2_B1_5_3_rerun.md`) |
| D-042 | 2026-11-02 | **P1 F4 파일럿 FAIL**: H1 AUPRC 0.8056 vs H3 0.7786 = +2.83%p(CI +2.13~+3.67, 기준 +3), 10% 데이터 +7.50%p(기준 +5 충족), 오탐률 0.368 vs 0.527(개선), 문장 P@R80 +8.9%p | B-12 1행 확정: **EG2 텍스트 hidden F4/F5 사용 폐기**. H4′는 PASS(100%) (`reports/P1_f4_pilot.md`) |
| D-043 | 2026-11-02 | **C2-A1 기준선 완료**: Notesoop greedy(KenLM 없음) CER 18.15%(Zeroth 17.32%, Kspon eval_clean 27.81%), WER 47.15%, RTF 0.178, 557클립/1.27h. **G-C2 FAIL**: FLEURS ko 382클립 CER **17.41%** > 15% | G-C2a는 ONNX 256d MRL 특징 재현 선행 필요. KenLM Windows 빌드 제약 (`reports/C2_A1_cer.md`) |

## 미결 안건 (사용자 승인 필요)

| ID | 안건 | 선택지 | 필요 시점 |
|---|---|---|---|
| OA-1 | VPS 규모·계정 | **확정: 계정 B에 머신 4대 추가 생성 (5대 구성)** | 2026-11-02 승인 완료 |
| OA-2 | git 원격 | **확정: GitHub 비공개 `mandutt/unigem`** (2026-11-02) | 사용자 지시 |
| OA-3 | G-A3S(Notesoop 특징 재현), G-C2a(호환성) 게이트 승인 | **확정: 게이트로 승인 (2026-11-02, D-015)** | C2-A 착수 전 |
| OA-4 | A2 export 실행 승인 | **확정: 승인 (2026-11-02)** — 로컬 텍스트 export + 오디오 그래프 수술 | 완료 |

## 참고: 로컬 자산 실측 메모

- `run-20261024-embedgemma2ko/model-src/`에 HF 체크포인트 사본 존재: `model.safetensors` 1,488,915,288 B (bf16), `config.json`, `tokenizer.json`(32,170,510 B).
- 이 사본의 **HF revision/provenance는 아직 미확인** — A2에서 `google/embeddinggemma-2` config·tokenizer 해시와 대조해 고정한다.
- `config.json`의 `text_config.max_position_embeddings = 262144`는 문서 §5.1의 "컨텍스트 8192"와 불일치. 실제 유효 컨텍스트는 A2에서 확인·기록한다(문서 수치를 사실로 가정하지 않는다).
