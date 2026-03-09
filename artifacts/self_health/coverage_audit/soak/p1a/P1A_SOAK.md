# P1-A Core Chains Soak

**Started**: 2026-03-09
**Status**: IN PROGRESS
**Objective**: 验证 6 个 P1-A probes 在 always-on 下稳定、准确、无噪音

---

## P1-A Probes (6)

| # | Probe | 功能 | Verification Mode |
|---|-------|------|-------------------|
| 1 | probe-openviking-retrieval | 检索健康检测 | probe_check + recent_success_check |
| 2 | probe-longrunkit-state-machine | 状态机完整性 | chain_integrity_check |
| 3 | probe-longrunkit-deadlock | 死锁检测 | probe_check |
| 4 | probe-longrunkit-timeout-retry | 超时/重试验证 | synthetic_input_check |
| 5 | probe-subagent-orchestration | 编排流完整性 | chain_integrity_check |
| 6 | probe-receipt-pipeline | 回执管道验证 | chain_integrity_check |

---

## Soak Focus Areas

### 1. 稳定性
- 6 个 P1-A probes 是否持续稳定
- 是否出现 flaky pass/fail

### 2. 准确性
- 有没有假阳 (probe fail 但系统正常)
- 有没有假阴 (probe pass 但系统有问题)
- 能不能抓到真实链路异常

### 3. 噪音
- 是否引入 incident/proposal 风暴
- 是否增加重复告警

### 4. 语义一致性
- probe 结果是否和 capability / gate / truth alignment 一致
- 是否出现"probe 说坏，Gate 说好"之类冲突

### 5. 运行成本
- scheduler 跑这些 probe 后的开销
- execution budget / lock contention / latency 是否仍健康

### 6. 深链路真实性 (重点)
- **retrieval**: 是否真能代表"能找回"
- **LongRunKit**: 是否真能反映"任务推进"
- **subagent orchestration**: 是否真能代表"编排成功"
- **receipt pipeline**: 是否真能代表"闭环收据存在"

---

## Current Status

```
P0 Critical Coverage: CLOSED ✅
P1-A Core Chains: COMPLETE (6/6 PASS)
P1-A Soak: IN PROGRESS
P1-B Remaining: PENDING
```
