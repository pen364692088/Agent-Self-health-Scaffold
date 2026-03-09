# Coverage Closure Plan

**Generated**: 2026-03-09
**Scope**: OpenClaw Capability Coverage Audit - Phase 3

---

## Executive Summary

本计划将 34 个未纳管功能分 4 批实施，优先覆盖 P0 Critical 功能，确保系统核心可靠性。

| Batch | Priority | Count | Timeline | Goal |
|-------|----------|-------|----------|------|
| Batch 1 | P0 | 9 | Week 1 | Core Critical Coverage |
| Batch 2 | P1 | 12 | Week 2-3 | Safety / Governance Coverage |
| Batch 3 | P2 | 8 | Week 4 | User-Promised Feature Coverage |
| Batch 4 | P3 | 5 | Deferred | Long-Tail Feature Coverage |

---

## Batch 1: Core Critical Coverage (P0)

**Timeline**: Week 1
**Goal**: 覆盖所有 P0 Critical 功能，确保核心系统可靠性

### 1.1 Native Compaction Verification

**Implementation Plan**:
```
工具: tools/probe-native-compaction
模式: chain_integrity_check + synthetic_input_check
频率: 每次 heartbeat (quick mode)
输出: artifacts/self_health/runtime/native_compaction_status.json
```

**Verification Steps**:
1. 创建合成 session 文件（包含真实对话消息）
2. 通过 `/compact` 命令触发压缩
3. 验证 session 文件格式正确
4. 验证可恢复性

**Acceptance Criteria**:
- [ ] 合成 session 压缩成功率 100%
- [ ] 压缩后 session 可正常加载
- [ ] 无数据丢失
- [ ] 日志写入 `compaction_events.jsonl`

### 1.2 Context Overflow / Compression Fallback

**Implementation Plan**:
```
工具: tools/probe-context-overflow
模式: synthetic_input_check + probe_check
频率: 每次 heartbeat (quick mode)
输出: artifacts/self_health/runtime/context_overflow_status.json
```

**Verification Steps**:
1. 创建大 token 输入模拟 overflow 场景
2. 验证 `context-budget-check` 正确检测
3. 验证 `context-compress` 正确执行
4. 验证 fallback 行为符合预期

**Acceptance Criteria**:
- [ ] overflow 检测准确率 100%
- [ ] fallback 不丢失关键信息
- [ ] 压缩决策符合 POLICIES/CONTEXT_COMPRESSION.md
- [ ] 日志写入 `compression_events.jsonl`

### 1.3 Subagent Callback Delivery

**Implementation Plan**:
```
工具: tools/probe-callback-delivery
模式: chain_integrity_check + recent_success_check
频率: 每次 heartbeat (quick mode)
输出: artifacts/self_health/runtime/callback_delivery_status.json
```

**Verification Steps**:
1. 检查 `callback-worker` 服务状态
2. 检查最近 callback 成功记录
3. 创建测试 subagent，验证 callback 路径
4. 验证 message 发送成功

**Acceptance Criteria**:
- [ ] callback-worker 服务 healthy
- [ ] 最近 1h 有成功 callback 记录
- [ ] 端到端 callback 路径可验证
- [ ] 无 stuck callback

### 1.4 Subagent Mailbox Mechanism

**Implementation Plan**:
```
工具: tools/probe-mailbox-integrity
模式: artifact_output_check + chain_integrity_check
频率: 每次 heartbeat (quick mode)
输出: artifacts/self_health/runtime/mailbox_integrity_status.json
```

**Verification Steps**:
1. 检查 `reports/subtasks/` 目录状态
2. 验证 receipt 文件格式正确
3. 验证无 orphan receipt
4. 验证 process-backed 状态

**Acceptance Criteria**:
- [ ] 无 stuck claimed receipt (> 5min)
- [ ] receipt 格式符合 schema
- [ ] inbox metrics 与实际一致
- [ ] 无数据竞争

### 1.5 Session Continuity State Persistence

**Implementation Plan**:
```
工具: tools/probe-session-persistence
模式: probe_check + artifact_output_check
频率: 每次 heartbeat (quick mode)
输出: artifacts/self_health/runtime/session_persistence_status.json
```

**Verification Steps**:
1. 验证 `SESSION-STATE.md` 存在且格式正确
2. 验证 `working-buffer.md` 存在
3. 验证 `state-write-atomic` 功能正常
4. 验证 WAL 写入正确

**Acceptance Criteria**:
- [ ] SESSION-STATE.md 格式正确
- [ ] 原子写入功能正常
- [ ] WAL 事件完整
- [ ] 无状态不一致

### 1.6 Gate A/B/C Consistency

**Implementation Plan**:
```
工具: tools/probe-gate-consistency
模式: probe_check + chain_integrity_check
频率: 每次 heartbeat (quick mode)
输出: artifacts/self_health/runtime/gate_consistency_status.json
```

**Verification Steps**:
1. 运行 Gate A (registry/policy/tool presence)
2. 运行 Gate B (telemetry freshness)
3. 运行 Gate C (consistency)
4. 验证三者结果一致

**Acceptance Criteria**:
- [ ] Gate A/B/C 全部 PASS
- [ ] 结果一致性 100%
- [ ] 无矛盾判定
- [ ] 日志写入 `gate_events.jsonl`

### 1.7 Proposal-Only Boundary Enforcement

**Implementation Plan**:
```
工具: tools/probe-proposal-boundary
模式: synthetic_input_check + probe_check
频率: 每次 full mode
输出: artifacts/self_health/runtime/proposal_boundary_status.json
```

**Verification Steps**:
1. 测试 Level B 自动修复 proposal-only 路径
2. 验证 Level C 同样需要 proposal
3. 尝试绕过 proposal，验证被拒绝
4. 验证 audit trail 完整

**Acceptance Criteria**:
- [ ] Level B/C 修改必须走 proposal
- [ ] 绕过尝试被拒绝
- [ ] audit trail 完整
- [ ] 无未授权修改

### 1.8 Truth Alignment (Capability Contract)

**Implementation Plan**:
```
工具: tools/probe-truth-alignment
模式: chain_integrity_check
频率: 每次 heartbeat (quick mode)
输出: artifacts/self_health/runtime/truth_alignment_status.json
```

**Verification Steps**:
1. 读取 capability 定义
2. 读取 summary 输出
3. 读取 Gate 结果
4. 验证三者一致

**Acceptance Criteria**:
- [ ] capability/summary/gate 口径一致
- [ ] 无矛盾判定
- [ ] 日志写入 `alignment_events.jsonl`

### 1.9 Handoff Integrity

**Implementation Plan**:
```
工具: tools/probe-handoff-integrity
模式: artifact_output_check + chain_integrity_check
频率: 每次 full mode
输出: artifacts/self_health/runtime/handoff_integrity_status.json
```

**Verification Steps**:
1. 验证 `handoff.md` 存在且格式正确
2. 验证关键信息完整
3. 验证可恢复性
4. 验证 WAL 同步

**Acceptance Criteria**:
- [ ] handoff.md 格式正确
- [ ] 包含 objective, phase, blocker, next
- [ ] 可恢复到上次状态
- [ ] 无信息丢失

---

## Batch 2: Safety / Governance Coverage (P1)

**Timeline**: Week 2-3
**Goal**: 覆盖 P1 High 功能，确保安全和治理能力

### 2.1 OpenViking Retrieval (Week 2)

**Implementation Plan**:
```
工具: tools/probe-openviking-retrieval
模式: probe_check + recent_success_check
频率: 每次 heartbeat (quick mode)
输出: artifacts/self_health/runtime/openviking_status.json
```

**Verification Steps**:
1. 检查 OpenViking 服务状态
2. 执行检索测试
3. 验证最近成功记录
4. 验证索引健康

**Acceptance Criteria**:
- [ ] 服务 healthy
- [ ] 检索功能正常
- [ ] 索引无损坏
- [ ] 最近 24h 有成功检索

### 2.2 LongRunKit State Machine (Week 2)

**Implementation Plan**:
```
工具: tools/probe-longrunkit-state-machine
模式: chain_integrity_check + synthetic_input_check
频率: 每次 full mode
输出: artifacts/self_health/runtime/longrunkit_state_status.json
```

**Verification Steps**:
1. 创建测试长任务
2. 验证状态机转换正确
3. 验证状态持久化
4. 验证状态恢复

**Acceptance Criteria**:
- [ ] 状态机转换正确
- [ ] 状态持久化可靠
- [ ] 状态恢复正确
- [ ] 无状态泄漏

### 2.3 LongRunKit Deadlock Detection (Week 2)

**Implementation Plan**:
```
工具: tools/probe-longrunkit-deadlock
模式: probe_check
频率: 每次 heartbeat (quick mode)
输出: artifacts/self_health/runtime/longrunkit_deadlock_status.json
```

**Verification Steps**:
1. 检查并发子代理状态
2. 验证无死锁
3. 验证超时处理
4. 验证恢复机制

**Acceptance Criteria**:
- [ ] 无死锁
- [ ] 超时机制正常
- [ ] 恢复机制正常
- [ ] 日志记录完整

### 2.4 LongRunKit Timeout/Retry (Week 2)

**Implementation Plan**:
```
工具: tools/probe-longrunkit-timeout
模式: synthetic_input_check
频率: 每次 full mode
输出: artifacts/self_health/runtime/longrunkit_timeout_status.json
```

**Verification Steps**:
1. 创建超时场景
2. 验证超时检测
3. 验证重试逻辑
4. 验证降级处理

**Acceptance Criteria**:
- [ ] 超时检测正确
- [ ] 重试逻辑正确
- [ ] 降级处理正确
- [ ] 无资源泄漏

### 2.5 Subagent Orchestration Flow (Week 3)

**Implementation Plan**:
```
工具: tools/probe-subagent-orchestration
模式: chain_integrity_check
频率: 每次 full mode
输出: artifacts/self_health/runtime/orchestration_status.json
```

**Verification Steps**:
1. 创建测试子代理
2. 验证 spawn -> pending -> join -> collect -> continue 流程
3. 验证状态同步
4. 验证错误处理

**Acceptance Criteria**:
- [ ] 流程完整
- [ ] 状态同步正确
- [ ] 错误处理正确
- [ ] 日志完整

### 2.6 Receipt Processing Pipeline (Week 3)

**Implementation Plan**:
```
工具: tools/probe-receipt-pipeline
模式: chain_integrity_check
频率: 每次 heartbeat (quick mode)
输出: artifacts/self_health/runtime/receipt_pipeline_status.json
```

**Verification Steps**:
1. 验证 receipt 生成正确
2. 验证 receipt 处理正确
3. 验证 receipt 归档正确
4. 验证无丢失 receipt

**Acceptance Criteria**:
- [ ] receipt 生成正确
- [ ] receipt 处理正确
- [ ] receipt 归档正确
- [ ] 无丢失

### 2.7 Task Completion Protocol (Week 3)

**Implementation Plan**:
```
工具: tools/probe-task-completion-protocol
模式: synthetic_input_check
频率: 每次 full mode
输出: artifacts/self_health/runtime/completion_protocol_status.json
```

**Verification Steps**:
1. 创建测试任务
2. 验证 verify-and-close 执行
3. 验证 done-guard 拦截
4. 验证 safe-message 检查

**Acceptance Criteria**:
- [ ] protocol 执行完整
- [ ] 拦截功能正常
- [ ] 无伪完成
- [ ] audit trail 完整

### 2.8 Context Shadow Report (Week 3)

**Implementation Plan**:
```
工具: tools/probe-context-shadow
模式: probe_check
频率: 每次 full mode
输出: artifacts/self_health/runtime/context_shadow_status.json
```

**Verification Steps**:
1. 运行 context-shadow-report
2. 验证 shadow 与实际一致
3. 验证差异检测正确
4. 验证报告完整

**Acceptance Criteria**:
- [ ] shadow 一致
- [ ] 差异检测正确
- [ ] 报告完整
- [ ] 日志记录

### 2.9 Summary Generation (Week 3)

**Implementation Plan**:
```
工具: tools/probe-summary-generation
模式: artifact_output_check
频率: 每次 heartbeat (quick mode)
输出: artifacts/self_health/runtime/summary_status.json (增强)
```

**Verification Steps**:
1. 验证 summary 生成正确
2. 验证 summary 格式正确
3. 验证 summary 与实际一致
4. 验证 summary 更新及时

**Acceptance Criteria**:
- [ ] summary 格式正确
- [ ] summary 内容准确
- [ ] 更新及时
- [ ] 无信息丢失

### 2.10 Execution Degradation Monitor (Week 3)

**Implementation Plan**:
```
工具: tools/probe-degradation-monitor
模式: probe_check
频率: 每次 full mode
输出: artifacts/self_health/runtime/degradation_status.json
```

**Verification Steps**:
1. 检查 degradation monitor 运行状态
2. 验证退化检测逻辑
3. 验证告警触发正确
4. 验证恢复检测

**Acceptance Criteria**:
- [ ] monitor 运行正常
- [ ] 检测逻辑正确
- [ ] 告警正确
- [ ] 恢复检测正确

### 2.11 Callback Worker Doctor (Week 3)

**Implementation Plan**:
```
工具: tools/probe-callback-doctor
模式: probe_check
频率: 每次 heartbeat (quick mode)
输出: artifacts/self_health/runtime/callback_doctor_status.json
```

**Verification Steps**:
1. 运行 callback-worker-doctor
2. 验证 active/idle_expected/degraded 判定正确
3. 验证边界情况
4. 验证报告完整

**Acceptance Criteria**:
- [ ] 判定正确
- [ ] 边界情况处理正确
- [ ] 报告完整
- [ ] 无误报

### 2.12 Continuity Event Log (Week 3)

**Implementation Plan**:
```
工具: tools/probe-continuity-event-log
模式: artifact_output_check
频率: 每次 heartbeat (quick mode)
输出: artifacts/self_health/runtime/continuity_log_status.json
```

**Verification Steps**:
1. 验证 WAL 文件存在
2. 验证事件格式正确
3. 验证事件完整
4. 验证可查询

**Acceptance Criteria**:
- [ ] WAL 存在
- [ ] 格式正确
- [ ] 事件完整
- [ ] 可查询

---

## Batch 3: User-Promised Feature Coverage (P2)

**Timeline**: Week 4
**Goal**: 覆盖 P2 Medium 功能，确保用户承诺功能可靠

### 3.1 Telegram Notification Delivery

**Implementation Plan**:
```
工具: tools/probe-telegram-notification
模式: recent_success_check
频率: 每次 full mode
输出: artifacts/self_health/runtime/telegram_status.json
```

### 3.2 Session Archive with Distillation

**Implementation Plan**:
```
工具: tools/probe-session-archive
模式: artifact_output_check
频率: 每天
输出: artifacts/self_health/runtime/archive_status.json
```

### 3.3 Subagent Inbox Metrics

**Implementation Plan**:
```
工具: tools/probe-inbox-metrics
模式: probe_check
频率: 每次 heartbeat (quick mode)
输出: artifacts/self_health/runtime/inbox_metrics_status.json
```

### 3.4 Embedding Policy Gate

**Implementation Plan**:
```
工具: tools/probe-embedding-gate
模式: probe_check
频率: 每次 full mode
输出: artifacts/self_health/runtime/embedding_gate_status.json
```

### 3.5 Memory Retrieval Hardening

**Implementation Plan**:
```
工具: tools/probe-memory-retrieval
模式: probe_check
频率: 每次 full mode
输出: artifacts/self_health/runtime/memory_retrieval_status.json
```

### 3.6 Daily Rollup Aggregation

**Implementation Plan**:
```
工具: tools/probe-daily-rollup
模式: artifact_output_check
频率: 每天
输出: artifacts/self_health/runtime/rollup_status.json
```

### 3.7 Token Counter CJK

**Implementation Plan**:
```
工具: tools/probe-token-counter-cjk
模式: synthetic_input_check
频率: 每次 full mode
输出: artifacts/self_health/runtime/token_counter_status.json
```

### 3.8 Webhook Sender Fallback

**Implementation Plan**:
```
工具: tools/probe-webhook-fallback
模式: chain_integrity_check
频率: 每次 full mode
输出: artifacts/self_health/runtime/webhook_status.json
```

---

## Batch 4: Long-Tail Feature Coverage (P3)

**Timeline**: Deferred
**Goal**: 按需覆盖 P3 Low 功能

### Deferred Items

1. Testbot Monitor - 仅测试环境使用
2. External Spawn - 非主流程
3. CI Memory Hardening - CI 专用
4. Use Link Audit - 审计辅助
5. Event Queue - 事件缓冲

**Implementation Trigger**:
- 功能升级为主流程
- 用户明确需求
- 发现问题需要探测

---

## Implementation Schedule

```
Week 1: Batch 1 - Core Critical Coverage
├── Day 1-2: Native Compaction + Context Overflow
├── Day 3-4: Callback + Mailbox
└── Day 5: Gate + Proposal + Truth + Handoff

Week 2: Batch 2 (Part 1) - Safety Coverage
├── Day 1-2: OpenViking + LongRunKit State Machine
├── Day 3: LongRunKit Deadlock + Timeout
└── Day 4-5: Subagent Orchestration

Week 3: Batch 2 (Part 2) - Governance Coverage
├── Day 1: Receipt Pipeline + Task Protocol
├── Day 2: Context Shadow + Summary
├── Day 3: Degradation Monitor
└── Day 4-5: Callback Doctor + Continuity Log

Week 4: Batch 3 - User-Promised Feature Coverage
├── Day 1-2: Telegram + Session Archive
├── Day 3: Inbox Metrics + Embedding Gate
└── Day 4-5: Memory Retrieval + Daily Rollup + Token Counter + Webhook

Deferred: Batch 4 - Long-Tail Feature Coverage
```

---

## Success Metrics

### Batch 1 Completion Criteria

| Metric | Target |
|--------|--------|
| P0 功能覆盖率 | 100% (9/9) |
| Probe 可用性 | 100% |
| Gate 集成 | 100% |
| Telemetry 输出 | 持续写入 |

### Batch 2 Completion Criteria

| Metric | Target |
|--------|--------|
| P1 功能覆盖率 | 100% (12/12) |
| Safety 覆盖 | 100% |
| Governance 覆盖 | 100% |

### Batch 3 Completion Criteria

| Metric | Target |
|--------|--------|
| P2 功能覆盖率 | 100% (8/8) |
| User-Promised 覆盖 | 100% |

---

## Risk Mitigation

### Implementation Risks

| Risk | Mitigation |
|------|------------|
| Probe 实现复杂 | 优先实现 `probe_check` 模式，逐步增强 |
| Telemetry 爆炸 | 控制输出频率，聚合指标 |
| 误报/漏报 | 边界情况测试，渐进式阈值调整 |
| 影响主循环 | 异步执行，预算控制 |

### Rollback Strategy

1. 每个 probe 独立可禁用
2. 通过 `--skip-probe` 参数临时禁用
3. 回滚不影响主流程
4. 日志完整保留审计

---

## Appendix: Tool Template

```bash
#!/usr/bin/env python3
"""
Probe: <功能名>
Mode: <verification_mode>
Frequency: <frequency>
Output: <output_path>
"""

import json
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE = Path('/home/moonlight/.openclaw/workspace')
RUNTIME = WORKSPACE / 'artifacts' / 'self_health' / 'runtime'

def probe():
    """执行探测"""
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",  # PASS / FAIL / PARTIAL
        "details": {},
        "errors": []
    }
    
    # TODO: 实现探测逻辑
    
    return result

def main():
    result = probe()
    output = RUNTIME / '<output_file>.json'
    output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
```
