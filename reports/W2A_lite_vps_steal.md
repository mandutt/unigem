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
