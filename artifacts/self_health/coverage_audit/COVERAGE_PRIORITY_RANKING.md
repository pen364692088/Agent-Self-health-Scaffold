# Coverage Priority Ranking

**Generated**: 2026-03-09
**Scope**: OpenClaw Capability Coverage Audit - Phase 3

---

## Priority Classification Summary

| Priority | Count | Risk Level |
|----------|-------|------------|
| P0 Critical | 9 | System-critical, immediate attention |
| P1 High | 12 | Core flow, strongly recommended |
| P2 Medium | 8 | Worth covering, can defer |
| P3 Low/Deferred | 5 | Experimental/temporary |

---

## P0 — Critical (Must Cover Immediately)

### 1. Native Compaction Verification

| Field | Value |
|-------|-------|
| 功能名 | Native Compaction |
| 风险等级 | CRITICAL |
| 对主系统影响 | 一坏导致 session 损坏或上下文丢失 |
| 建议 verification mode | `chain_integrity_check` + `synthetic_input_check` |
| 纳管优先级 | P0 |
| 分级理由 | 核心记忆管理能力，已发生回归，需要持续验证 |
| 当前状态 | 工具存在 (compact 命令)，但无 self-health probe |
| Coverage Gap | 无自动探测，依赖手动触发 |

### 2. Context Overflow / Compression Fallback

| Field | Value |
|-------|-------|
| 功能名 | Context Overflow Handling |
| 风险等级 | CRITICAL |
| 对主系统影响 | 一坏导致 agent 能力退化或 silent break |
| 建议 verification mode | `synthetic_input_check` + `probe_check` |
| 纳管优先级 | P0 |
| 分级理由 | 超过阈值时的 fallback 行为决定系统稳定性 |
| 当前状态 | `context-budget-check` 存在，`context-compress` 存在 |
| Coverage Gap | 无 overflow 场景的主动探测 |

### 3. Subagent Callback Delivery

| Field | Value |
|-------|-------|
| 功能名 | Subagent Callback Delivery |
| 风险等级 | CRITICAL |
| 对主系统影响 | 一坏导致任务卡住，主流程中断 |
| 建议 verification mode | `chain_integrity_check` + `recent_success_check` |
| 纳管优先级 | P0 |
| 分级理由 | v8.0 架构核心路径，已有多轮修复 |
| 当前状态 | `callback-worker` 存在，有 telemetry |
| Coverage Gap | 无端到端验证，mailbox 为 file heuristic |

### 4. Subagent Mailbox Mechanism

| Field | Value |
|-------|-------|
| 功能名 | Subagent Mailbox |
| 风险等级 | CRITICAL |
| 对主系统影响 | 回执丢失导致任务推进失败 |
| 建议 verification mode | `artifact_output_check` + `chain_integrity_check` |
| 纳管优先级 | P0 |
| 分级理由 | 回执持久化的最后保障，当前为 file heuristic |
| 当前状态 | `subagent-inbox` 存在，有 metrics |
| Coverage Gap | 无 process-backed verification |

### 5. Session Continuity State Persistence

| Field | Value |
|-------|-------|
| 功能名 | Session Continuity State Persistence |
| 风险等级 | CRITICAL |
| 对主系统影响 | 上下文丢失，工作状态无法恢复 |
| 建议 verification mode | `probe_check` + `artifact_output_check` |
| 纳管优先级 | P0 |
| 分级理由 | AGENTS.md 要求的强制落盘，核心可靠性保障 |
| 当前状态 | `session-start-recovery`, `state-write-atomic` 存在 |
| Coverage Gap | 无自动验证落盘正确性 |

### 6. Gate A/B/C Consistency

| Field | Value |
|-------|-------|
| 功能名 | Gate A/B/C Consistency |
| 风险等级 | CRITICAL |
| 对主系统影响 | 一坏导致 always-on 判定失效 |
| 建议 verification mode | `probe_check` + `chain_integrity_check` |
| 纳管优先级 | P0 |
| 分级理由 | SOAK_FREEZE_STATE 的核心判定依据 |
| 当前状态 | `gate-self-health-check` 存在 |
| Coverage Gap | 无 Gate A/B/C 口径一致性自动验证 |

### 7. Proposal-Only Boundary Enforcement

| Field | Value |
|-------|-------|
| 功能名 | Proposal-Only Boundary |
| 风险等级 | CRITICAL |
| 对主系统影响 | 一坏导致安全/治理边界失效 |
| 建议 verification mode | `synthetic_input_check` + `probe_check` |
| 纳管优先级 | P0 |
| 分级理由 | Level B/C 修改必须走 proposal，防止 runaway |
| 当前状态 | `agent-self-heal --proposal-only` 存在 |
| Coverage Gap | 无边界违反检测 |

### 8. Truth Alignment (Capability Contract)

| Field | Value |
|-------|-------|
| 功能名 | Truth Alignment |
| 风险等级 | CRITICAL |
| 对主系统影响 | capability/summary/gate 口径不一致导致误判 |
| 建议 verification mode | `chain_integrity_check` |
| 纳管优先级 | P0 |
| 分级理由 | 24h verdict 核心条件之一 |
| 当前状态 | 多文件但无统一验证 |
| Coverage Gap | 无 cross-source consistency check |

### 9. Handoff Integrity

| Field | Value |
|-------|-------|
| 功能名 | Handoff Integrity |
| 风险等级 | CRITICAL |
| 对主系统影响 | 长会话交接失败导致工作丢失 |
| 建议 verification mode | `artifact_output_check` + `chain_integrity_check` |
| 纳管优先级 | P0 |
| 分级理由 | SESSION-STATE.md 的核心承诺 |
| 当前状态 | `handoff.md` 手动维护 |
| Coverage Gap | 无自动 handoff 生成与验证 |

---

## P1 — High (Strongly Recommended Soon)

### 10. OpenViking Retrieval

| Field | Value |
|-------|-------|
| 功能名 | OpenViking Retrieval |
| 风险等级 | HIGH |
| 对主系统影响 | 检索失败导致历史上下文不可用 |
| 建议 verification mode | `probe_check` + `recent_success_check` |
| 纳管优先级 | P1 |
| 分级理由 | 语义检索核心能力，已被 session archive 依赖 |
| 当前状态 | 服务运行，有 enablement verdict |
| Coverage Gap | 无持续健康探测 |

### 11. LongRunKit State Machine

| Field | Value |
|-------|-------|
| 功能名 | LongRunKit State Machine |
| 风险等级 | HIGH |
| 对主系统影响 | 长任务状态机错误导致任务卡住 |
| 建议 verification mode | `chain_integrity_check` + `synthetic_input_check` |
| 纳管优先级 | P1 |
| 分级理由 | 长任务编排核心 |
| 当前状态 | `tools/orchestrator/` 存在 |
| Coverage Gap | 无状态机完整性验证 |

### 12. LongRunKit Deadlock Detection

| Field | Value |
|-------|-------|
| 功能名 | LongRunKit Deadlock Detection |
| 风险等级 | HIGH |
| 对主系统影响 | 死锁导致系统完全卡死 |
| 建议 verification mode | `probe_check` |
| 纳管优先级 | P1 |
| 分级理由 | 并发子代理场景关键保障 |
| 当前状态 | 有 `test_deadlock_regression.py` |
| Coverage Gap | 无生产环境主动探测 |

### 13. LongRunKit Timeout/Retry

| Field | Value |
|-------|-------|
| 功能名 | LongRunKit Timeout/Retry |
| 风险等级 | HIGH |
| 对主系统影响 | 超时处理不当导致资源泄漏 |
| 建议 verification mode | `synthetic_input_check` |
| 纳管优先级 | P1 |
| 分级理由 | 容错机制核心 |
| 当前状态 | orchestrator 有超时逻辑 |
| Coverage Gap | 无 timeout 场景验证 |

### 14. Subagent Orchestration Flow

| Field | Value |
|-------|-------|
| 功能名 | Subagent Orchestration Flow |
| 风险等级 | HIGH |
| 对主系统影响 | 编排失败导致任务无法推进 |
| 建议 verification mode | `chain_integrity_check` |
| 纳管优先级 | P1 |
| 分级理由 | subtask-orchestrate 是正式入口 |
| 当前状态 | `subtask-orchestrate` 存在，有测试 |
| Coverage Gap | 无全链路自动验证 |

### 15. Receipt Processing Pipeline

| Field | Value |
|-------|-------|
| 功能名 | Receipt Processing Pipeline |
| 风险等级 | HIGH |
| 对主系统影响 | 回执处理失败导致任务状态不一致 |
| 建议 verification mode | `chain_integrity_check` |
| 纳管优先级 | P1 |
| 分级理由 | verify-and-close 依赖 receipt |
| 当前状态 | `auto-receipt`, `finalize-response` 存在 |
| Coverage Gap | 无 receipt 完整性验证 |

### 16. Task Completion Protocol

| Field | Value |
|-------|-------|
| 功能名 | Task Completion Protocol |
| 风险等级 | HIGH |
| 对主系统影响 | 跳过验证导致伪完成 |
| 建议 verification mode | `synthetic_input_check` |
| 纳管优先级 | P1 |
| 分级理由 | SOUL.md 强制要求五工具链 |
| 当前状态 | `verify-and-close`, `done-guard`, `safe-message` 存在 |
| Coverage Gap | 无 protocol 执行完整性验证 |

### 17. Context Shadow Report

| Field | Value |
|-------|-------|
| 功能名 | Context Shadow Report |
| 风险等级 | HIGH |
| 对主系统影响 | shadow 不一致导致压缩决策错误 |
| 建议 verification mode | `probe_check` |
| 纳管优先级 | P1 |
| 分级理由 | 上下文一致性保障 |
| 当前状态 | `context-shadow-report` 存在 |
| Coverage Gap | 无持续验证 |

### 18. Summary Generation

| Field | Value |
|-------|-------|
| 功能名 | Summary Generation |
| 风险等级 | HIGH |
| 对主系统影响 | summary 错误导致状态不一致 |
| 建议 verification mode | `artifact_output_check` |
| 纳管优先级 | P1 |
| 分级理由 | 状态持久化核心 |
| 当前状态 | `agent-health-summary` 存在 |
| Coverage Gap | 无 summary 正确性验证 |

### 19. Execution Degradation Monitor

| Field | Value |
|-------|-------|
| 功能名 | Execution Degradation Monitor |
| 风险等级 | HIGH |
| 对主系统影响 | 退化检测失效导致问题蔓延 |
| 建议 verification mode | `probe_check` |
| 纳管优先级 | P1 |
| 分级理由 | 早期预警关键 |
| 当前状态 | `execution-degradation-monitor` 存在 |
| Coverage Gap | 无主动退化场景测试 |

### 20. Callback Worker Doctor

| Field | Value |
|-------|-------|
| 功能名 | Callback Worker Doctor |
| 风险等级 | HIGH |
| 对主系统影响 | 误判导致错误处理 |
| 建议 verification mode | `probe_check` |
| 纳管优先级 | P1 |
| 分级理由 | 语义修正后的验证保障 |
| 当前状态 | `callback-worker-doctor` 存在 |
| Coverage Gap | 无边界情况验证 |

### 21. Continuity Event Log

| Field | Value |
|-------|-------|
| 功能名 | Continuity Event Log |
| 风险等级 | HIGH |
| 对主系统影响 | 事件丢失导致审计不完整 |
| 建议 verification mode | `artifact_output_check` |
| 纳管优先级 | P1 |
| 分级理由 | WAL 协议核心 |
| 当前状态 | `continuity-event-log` 存在 |
| Coverage Gap | 无事件完整性验证 |

---

## P2 — Medium (Worth Covering, Can Defer)

### 22. Telegram Notification Delivery

| Field | Value |
|-------|-------|
| 功能名 | Telegram Notification |
| 风险等级 | MEDIUM |
| 对主系统影响 | 通知失败不影响核心流程 |
| 建议 verification mode | `recent_success_check` |
| 纳管优先级 | P2 |
| 分级理由 | user_promised_feature，低频关键 |
| 当前状态 | `openclaw message send` 存在 |
| Coverage Gap | 无 delivery 确认 |

### 23. Session Archive with Distillation

| Field | Value |
|-------|-------|
| 功能名 | Session Archive with Distillation |
| 风险等级 | MEDIUM |
| 对主系统影响 | 归档失败导致历史丢失，不影响当前 |
| 建议 verification mode | `artifact_output_check` |
| 纳管优先级 | P2 |
| 分级理由 | 辅助能力，压缩率验证已存在 |
| 当前状态 | `archive-with-distill`, `distill-content` 存在 |
| Coverage Gap | 无持续验证 |

### 24. Subagent Inbox Metrics

| Field | Value |
|-------|-------|
| 功能名 | Subagent Inbox Metrics |
| 风险等级 | MEDIUM |
| 对主系统影响 | 指标不准确影响监控但不影响执行 |
| 建议 verification mode | `probe_check` |
| 纳管优先级 | P2 |
| 分级理由 | 监控辅助 |
| 当前状态 | `subagent-inbox-metrics` 存在 |
| Coverage Gap | 无 metrics 准确性验证 |

### 25. Embedding Policy Gate

| Field | Value |
|-------|-------|
| 功能名 | Embedding Policy Gate |
| 风险等级 | MEDIUM |
| 对主系统影响 | embedding 失败影响检索 |
| 建议 verification mode | `probe_check` |
| 纳管优先级 | P2 |
| 分级理由 | 检索辅助能力 |
| 当前状态 | 有测试 `test_embedding_policy_gate.py` |
| Coverage Gap | 无生产探测 |

### 26. Memory Retrieval Hardening

| Field | Value |
|-------|-------|
| 功能名 | Memory Retrieval Hardening |
| 风险等级 | MEDIUM |
| 对主系统影响 | 检索失败有 fallback |
| 建议 verification mode | `probe_check` |
| 纳管优先级 | P2 |
| 分级理由 | 有测试但无持续验证 |
| 当前状态 | 有测试 `test_memory_retrieval_hardening.py` |
| Coverage Gap | 无生产探测 |

### 27. Daily Rollup Aggregation

| Field | Value |
|-------|-------|
| 功能名 | Daily Rollup Aggregation |
| 风险等级 | MEDIUM |
| 对主系统影响 | 汇总错误影响报告准确性 |
| 建议 verification mode | `artifact_output_check` |
| 纳管优先级 | P2 |
| 分级理由 | 报告辅助 |
| 当前状态 | 有测试 `test_daily_rollup_aggregates_metrics_correctly.py` |
| Coverage Gap | 无生产验证 |

### 28. Token Counter CJK

| Field | Value |
|-------|-------|
| 功能名 | Token Counter CJK |
| 风险等级 | MEDIUM |
| 对主系统影响 | 计数不准影响预算估算 |
| 建议 verification mode | `synthetic_input_check` |
| 纳管优先级 | P2 |
| 分级理由 | 边缘情况处理 |
| 当前状态 | 有测试 `test_token_counter_cjk_no_whitespace.py` |
| Coverage Gap | 无持续验证 |

### 29. Webhook Sender Fallback

| Field | Value |
|-------|-------|
| 功能名 | Webhook Sender Fallback |
| 风险等级 | MEDIUM |
| 对主系统影响 | webhook 失败有 fallback queue |
| 建议 verification mode | `chain_integrity_check` |
| 纳管优先级 | P2 |
| 分级理由 | 降级机制 |
| 当前状态 | 有测试 `test_webhook_sender_downgrade_to_failed_queue.py` |
| Coverage Gap | 无生产验证 |

---

## P3 — Low / Deferred

### 30. Testbot Monitor

| Field | Value |
|-------|-------|
| 功能名 | Testbot Monitor |
| 风险等级 | LOW |
| 对主系统影响 | 仅影响测试环境 |
| 建议 verification mode | `probe_check` |
| 纳管优先级 | P3 |
| 分级理由 | 实验功能 |
| 当前状态 | `testbot-*` 系列工具存在 |
| Coverage Gap | 非核心 |

### 31. External Spawn

| Field | Value |
|-------|-------|
| 功能名 | External Spawn |
| 风险等级 | LOW |
| 对主系统影响 | 非主流程 |
| 建议 verification mode | `probe_check` |
| 纳管优先级 | P3 |
| 分级理由 | 临时机制 |
| 当前状态 | `external-spawn` 存在 |
| Coverage Gap | 非核心 |

### 32. CI Memory Hardening

| Field | Value |
|-------|-------|
| 功能名 | CI Memory Hardening |
| 风险等级 | LOW |
| 对主系统影响 | 仅 CI 环境 |
| 建议 verification mode | `probe_check` |
| 纳管优先级 | P3 |
| 分级理由 | CI 专用 |
| 当前状态 | `ci-memory-hardening` 存在 |
| Coverage Gap | 非核心 |

### 33. Use Link Audit

| Field | Value |
|-------|-------|
| 功能名 | Use Link Audit |
| 风险等级 | LOW |
| 对主系统影响 | 审计辅助 |
| 建议 verification mode | `probe_check` |
| 纳管优先级 | P3 |
| 分级理由 | 辅助功能 |
| 当前状态 | `use-link-audit` 存在 |
| Coverage Gap | 非核心 |

### 34. Event Queue

| Field | Value |
|-------|-------|
| 功能名 | Event Queue |
| 风险等级 | LOW |
| 对主系统影响 | 事件缓冲，非关键路径 |
| 建议 verification mode | `probe_check` |
| 纳管优先级 | P3 |
| 分级理由 | 辅助机制 |
| 当前状态 | `event-queue` 存在 |
| Coverage Gap | 非核心 |

---

## Notes

1. **Verification Mode Mapping**:
   - `probe_check`: 主动探测功能是否正常
   - `recent_success_check`: 检查近期成功记录
   - `artifact_output_check`: 验证输出文件存在且正确
   - `synthetic_input_check`: 合成输入测试边界情况
   - `chain_integrity_check`: 验证完整链路端到端

2. **Coverage Gap Definition**:
   - 工具存在但无 self-health probe
   - 有测试但无生产验证
   - 有 telemetry 但无主动探测

3. **Priority Factors**:
   - 对主系统核心行为影响
   - 安全/治理边界
   - silent break 风险
   - 主流程依赖程度
