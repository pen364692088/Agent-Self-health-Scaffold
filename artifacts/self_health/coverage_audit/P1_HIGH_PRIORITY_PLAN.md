# P1 High-Priority Coverage Expansion

**Status**: IN PROGRESS
**Started**: 2026-03-09
**Previous Phase**: P0 CLOSED ✅

---

## P1 Overview

| Metric | Value |
|--------|-------|
| Total P1 Probes | 12 |
| P1-A (Core First) | 6 |
| P1-B (Remaining) | 6 |
| Verification Modes | probe_check, chain_integrity_check, synthetic_input_check, artifact_output_check |

---

## P1-A: Core System Chain Probes (优先实现)

这些 probes 直接关联主系统核心链路：

| # | Probe | 功能 | Verification Mode |
|---|-------|------|-------------------|
| 1 | probe-openviking-retrieval | 检索健康检测 | probe_check + recent_success_check |
| 2 | probe-longrunkit-state-machine | 长任务状态机完整性 | chain_integrity_check + synthetic_input_check |
| 3 | probe-longrunkit-deadlock | 死锁检测 | probe_check |
| 4 | probe-longrunkit-timeout-retry | 超时/重试验证 | synthetic_input_check |
| 5 | probe-subagent-orchestration | 编排流完整性 | chain_integrity_check |
| 6 | probe-receipt-pipeline | 回执处理管道 | chain_integrity_check |

---

## P1-B: High-Value Flow Probes (后续实现)

| # | Probe | 功能 | Verification Mode |
|---|-------|------|-------------------|
| 7 | probe-task-completion-protocol | 任务完成协议验证 | synthetic_input_check |
| 8 | probe-context-shadow | Context shadow 一致性 | probe_check |
| 9 | probe-summary-generation | Summary 生成正确性 | artifact_output_check |
| 10 | probe-execution-degradation | 执行退化监控 | probe_check |
| 11 | probe-callback-worker-doctor | Doctor 边界验证 | probe_check |
| 12 | probe-continuity-event-log | 事件日志完整性 | artifact_output_check |

---

## Implementation Plan

### Phase 1: P1-A Implementation (6 probes)
1. Create probe files
2. Integrate into scheduler P1_PROBES list
3. Run initial validation

### Phase 2: P1-A Soak
1. Run 3+ rounds
2. Assess stability and accuracy
3. Fix any issues

### Phase 3: P1-B Implementation (6 probes)
1. Create remaining probe files
2. Integrate into scheduler
3. Run validation

### Phase 4: P1 Full Soak
1. Run extended soak
2. Generate P1_CLOSURE_VERDICT

---

## P1 Probes Directory

```
tools/
├── probe-openviking-retrieval
├── probe-longrunkit-state-machine
├── probe-longrunkit-deadlock
├── probe-longrunkit-timeout-retry
├── probe-subagent-orchestration
├── probe-receipt-pipeline
├── probe-task-completion-protocol
├── probe-context-shadow
├── probe-summary-generation
├── probe-execution-degradation
├── probe-callback-worker-doctor
└── probe-continuity-event-log
```

---

## Current Status

```
P0 Critical Coverage: CLOSED ✅
P1 High-Priority: IN PROGRESS
P1-A Progress: 0/6
P1-B Progress: 0/6
```
