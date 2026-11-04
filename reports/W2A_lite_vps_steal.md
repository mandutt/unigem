# Wave 2A-lite — VPS CPU steal 실측과 대응

- 작성: 2026-11-04
- 목적: F-C 학습 지연(epoch 260s → 1,035s)의 원인 판별
- 결론: **guest-level CPU affinity(`taskset`)로 해결할 수 없다.** 원인은 eg2-1의 host contention이며, **clean VPS로 워크로드를 옮기는 것**이 실제 대응이다.

## 1. /proc/stat 실측

각 머신의 `/proc/stat` aggregate (부팅 이후 누적 jiffies).

| 머신 | user | idle | steal | steal 비율(대략) | 판정 |
|---|---:|---:|---:|---:|---|
| eg2-1 | 1,474,763 | 775,326 | **1,384,143** | **~38%** | noisy neighbor |
| eg2-2 | 1,004,492 | 950,889 | 466 | ~0.02% | clean |
| eg2-3 | 1,010,966 | 943,475 | 377 | ~0.02% | clean |
| eg2-4 | 959,555 | 992,862 | 396 | ~0.02% | clean |
| eg2-5 | 1,287 | 1,867,451 | 57 | ~0.003% | clean(새 부팅) |

eg2-1의 **vCPU별 steal도 균일**했다.

| vCPU | steal |
|---|---:|
| cpu0 | 344,502 |
| cpu1 | 345,272 |
| cpu2 | 345,326 |
| cpu3 | 344,788 |

즉 특정 vCPU만 나쁜 것이 아니라 **host 전체가 과점유**된 상태다. guest 안에서 어느 vCPU를 고르든 피할 수 없다.

## 2. Exa 검색 결과

- **SSD Nodes, “CPU steal time and noisy neighbours on a VPS”**: steal은 hypervisor가 물리 코어를 다른 guest에 넘긴 시간이며, “**Nothing inside your server can clear that state**”라고 명시한다.
- **Linux kernel “Preferred CPUs” / steal governor**: guest가 steal을 줄이는 유일한 커널 기능은 **preferred CPU 집합을 줄여 vCPU 수를 접는 것**이다. 그러나 `CONFIG_PREFERRED_CPU`와 드라이버가 필요하고, 모든 guest가 협조해야 하며, **affinity/taskset과는 다른 메커니즘**이다. 우리 VPS에는 `/sys/devices/system/cpu/preferred`가 없었다.
- **LWN “Using steal time to moderate CPU demands”**: guest가 steal을 보고 스스로 vCPU 사용을 줄이는 접근. 단일 프로세스 affinity와 무관.
- **Red Hat KVM tuning / Rocky KVM tuning**: vCPU pinning은 **host의 `virsh vcpupin`** 영역이다. guest의 `taskset`은 guest vCPU 안에서의 배치만 바꾼다.
- **SSD Nodes / Worldstream**: 실질 대응은 **덜 붐비는 노드로 migration**, **dedicated vCPU**, 또는 **threads를 vCPU 수보다 줄이는 것**이다.

## 3. 대응

- eg2-1의 F-C 학습을 중단하고, **clean host인 eg2-5**로 F-C를 이동했다.
- eg2-5에서 `--fc-memmap`으로 F-C 특징을 재추출한 뒤 F-C-softmax/F-C-concat을 순차 학습한다.
- eg2-1의 `fc_softmax_s42.best.pt`(best CER 0.2346, epoch 8)는 보존한다. 단, host steal 상태의 결과이므로 최종 판정에는 쓰지 않고 참고로만 남긴다.
- `taskset`은 적용하지 않는다. per-vCPU steal이 균일해 이득이 없고, 오히려 스케줄러의 이동 자유를 뺏을 수 있다.
- VPS 2~4의 seed43/fbank는 clean host에서 계속한다.

## 4. 교훈

- **VPS epoch 시간이 갑자기 4배 느려지면 먼저 `/proc/stat`의 steal을 본다.**
- **guest affinity는 host contention의 해결책이 아니다.**
- **같은 계정의 VPS라도 host마다 상태가 다르다.** eg2-1만 steal 38%, eg2-2~5는 거의 0이었다.
- **긴 학습은 host별 steal을 모니터링하고, 나쁜 host의 job은 clean host로 옮긴다.**

## 5. 1시간 구간 steal probe (2026-11-04 03:53~04:57 UTC)

누적값이 아니라 **1분 구간 delta**로 다시 측정했다. `runner/w2a_steal_probe.py`가 5대를 동시에 샘플링했다.

| 머신 | 구간 steal 평균 | 최대 | 마지막 10분 | 부하 상태 |
|---|---:|---:|---:|---|
| eg2-1 | 0.007% | 0.040% | 0.003% | 유휴 |
| eg2-2 | 0.025% | 0.116% | 0.002% | 학습 종료 후 유휴 |
| eg2-3 | 0.021% | 0.052% | 0.002% | 학습 종료 후 유휴 |
| eg2-4 | 0.015% | 0.048% | 0.002% | fbank 종료 후 유휴 |
| eg2-5 | **0.097%** | **0.296%** | **0.153%** | F-C 학습 지속 |

- eg2-5는 부하가 계속되면서 **0.055% → 0.153%**로 완만히 상승했다. 다만 절대값은 **0.15%**로, eg2-1의 38%와 비교하면 **약 250배 낮다**.
- eg2-2/3/4는 학습이 끝난 뒤 유휴가 되면서 steal이 0에 가까워졌다.
- **1시간 안에 provider-wide time-based throttle이 온다는 증거는 없었다.**
- eg2-5의 완만한 상승은 host noisy neighbor 또는 지속 부하에 따른 미세한 경합으로 보이며, **현재 학습 속도(epoch 280초)에는 실질 영향이 없다.**
- 결론: **steal이 보일 때마다 기계적으로 migration하지 않는다.** 구간 steal이 5% 이상으로 지속될 때만 이동하고, 그렇지 않으면 해당 host에서 계속한다. 긴 critical job은 로컬 폴백을 우선한다.

## 6. 지연 발현 — 1시간 probe 이후 eg2-5 급증

- 05:31경까지 eg2-5 F-C-softmax epoch는 **280초**였고, 06:12에는 **1,062~1,083초**로 4배 가까이 느려졌다.
- 같은 시점 `/proc/stat` aggregate: **steal 1,033,321 / total 약 5.9M = 약 17.5%**.
- 1시간 probe 마지막(04:57)의 0.153%에서 약 2시간 만에 **17.5%**로 상승했다. 즉 **clean host도 시간이 지나면 noisy neighbor가 될 수 있다.**
- 따라서 **migration은 일시적 회피일 뿐**이며, 긴 critical 학습의 해법이 아니다.
- 조치: eg2-5 F-C-softmax를 epoch 17에서 중단하고 **로컬로 이전**했다. `fc_softmax_s42.best.pt`(best 0.2210, epoch 15)는 참고용으로 보존한다.
- 원칙 변경: **VPS는 1시간 이내의 짧은/병렬 작업에만 사용하고, 긴 critical job은 로컬에서 실행한다.** 단, steal이 커져도 **남은 시간이 재시작보다 짧으면 중단하지 않는다**(§7). VPS 결과를 쓰더라도 host가 checkpoint 저장조차 불가능할 정도로 불안정할 때만 로컬로 폴백한다.

## 7. 중단 판단 — “steal = 즉시 로컬”은 틀렸다

- eg2-5 F-C-softmax를 epoch 17/20에서 중단한 것은 **잘못된 판단**이었다. 남은 3 epoch는 당시 1,080초/epoch 기준 **약 54분**이면 끝났고, 로컬에서 20 epoch를 처음부터 다시 도는 데는 **약 1시간 50분**이 걸린다. 즉 **중단이 더 오래 걸렸다.**
- 올바른 규칙은 “steal이 보이면 중단”이 아니라 **남은 시간과 재시작 비용을 비교**하는 것이다.

```
remaining_on_current = 남은 epoch × 현재 epoch 시간
restart_local       = 전체 epoch × 로컬 epoch 시간 + 특징 전송·로드 시간
if remaining_on_current < restart_local: 계속 실행
else: 다음 checkpoint에서 중단·이전 (가능하면 --resume)
```

- steal이 5%를 넘어도 **아직 완주가 더 빠르면 그대로 둔다.** 중단은 (a) 남은 시간이 재시작보다 길거나, (b) host가 checkpoint 저장조차 못 할 정도로 불안정할 때만 한다.
- 장기적으로는 `d5_reader.py --resume`(optimizer/scheduler/epoch/RNG 포함)을 구현해, 중단 시 손실을 “현재 epoch”로 제한한다.
- 2026-11-04 현재 복구: eg2-5의 `fc_softmax_s42.best.pt`(0.2210)는 보존하고, 완전한 4-arm 비교를 위해 로컬에서 F-C-softmax를 다시 실행 중이다. 이 재실행은 **steal 회피가 아니라 중단 손실 복구**다.
