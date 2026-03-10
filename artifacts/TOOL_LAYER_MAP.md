# Tool Layer Map

Date: 2026-03-10
Version: 1.0
Purpose: 非行为改变型标记 - 记录工具层级

---

## 层级定义

| 层级 | 标签 | 定义 | 使用场景 |
|------|------|------|----------|
| MAIN | `# LAYER: main` | 主入口，稳定 API，文档推荐 | 日常使用 |
| SPECIALIZED | `# LAYER: specialized` | 专用场景，有限使用 | 特定功能 |
| LOW-LEVEL | `# LAYER: low-level` | 内部实现，不推荐直接使用 | 底层调用 |
| DEBUG | `# LAYER: debug` | 维护/调试专用 | 故障排查 |
| DEPRECATED | `# LAYER: deprecated` | 即将移除 | 迁移中 |
| INTERNAL | `# LAYER: internal` | 自动化/内部调用 | 非用户入口 |

---

## 子代理编排

| 工具 | 层级 | 说明 |
|------|------|------|
| `subtask-orchestrate` | MAIN | 正式编排入口 |
| `spawn-with-callback` | DEBUG | 底层 spawn + 回调 |
| `subagent-inbox` | SPECIALIZED | 回执管理 |
| `subagent-completion-handler` | INTERNAL | 回执处理 |
| `handle-subagent-complete` | INTERNAL | 自动触发 |
| `callback-handler` | INTERNAL | 回调处理 |
| `callback-handler-auto` | INTERNAL | 自动回调 |
| `callback-worker` | INTERNAL | Systemd worker |
| `check-subagent-mailbox` | DEPRECATED | 已废弃 |
| `cc-spawn` | LOW-LEVEL | 底层 spawn |
| `multi-spawn` | LOW-LEVEL | 批量 spawn |
| `serial-subagents` | LOW-LEVEL | 串行 spawn |
| `trigger-spawn` | LOW-LEVEL | 触发 spawn |

---

## 记忆检索

| 工具 | 层级 | 说明 |
|------|------|------|
| `session-query` | MAIN | 统一检索入口 |
| `memory-search` | SPECIALIZED | 记忆搜索 |
| `memory-retrieve` | SPECIALIZED | 记忆检索 |
| `context-retrieve` | SPECIALIZED | S1 两级检索 |
| `session-start-recovery` | INTERNAL | 会话恢复自动调用 |
| `session-bootstrap-retrieve` | INTERNAL | Bootstrap 检索 |
| `openviking-l2-smoke-test` | DEBUG | L2 测试 |
| `probe-memory-retrieval` | DEBUG | 检索探针 |
| `probe-openviking-retrieval` | DEBUG | OpenViking 探针 |

---

## 状态写入

| 工具 | 层级 | 说明 |
|------|------|------|
| `safe-write` | MAIN | 安全写入主入口 |
| `safe-replace` | MAIN | 安全替换主入口 |
| `write-policy-check` | SPECIALIZED | 策略检查 |
| `state-write-atomic` | SPECIALIZED | SESSION-STATE 原子写入 |
| `state-journal-append` | INTERNAL | WAL 追加 |
| `state-lock` | LOW-LEVEL | 状态锁 |

---

## 任务完成

| 工具 | 层级 | 说明 |
|------|------|------|
| `verify-and-close` | MAIN | 任务收尾入口 |
| `enforce-task-completion` | MAIN | 强制执行 |
| `finalize-response` | SPECIALIZED | 输出检查 |
| `done-guard` | SPECIALIZED | 完成拦截 |
| `safe-message` | MAIN | 安全消息发送 |
| `output-interceptor` | INTERNAL | 输出拦截 |
| `receipt-signer` | INTERNAL | Receipt 签名 |
| `receipt-validator` | INTERNAL | Receipt 验证 |
| `auto-receipt` | INTERNAL | 自动 receipt |

---

## Context Compression

| 工具 | 层级 | 说明 |
|------|------|------|
| `context-budget-check` | SPECIALIZED | Token 预算检查 |
| `context-compress` | SPECIALIZED | 压缩执行器 |
| `capsule-builder` | SPECIALIZED | 胶囊构建 |
| `prompt-assemble` | INTERNAL | Prompt 组装 |
| `s1-dashboard` | SPECIALIZED | S1 监控 |
| `s1-sampler` | INTERNAL | S1 采样 |
| `s1-validator` | INTERNAL | S1 验证 |
| `auto-context-compact` | INTERNAL | 自动压缩 |
| `shadow_watcher` | DEBUG | Shadow 监控 |

---

## Execution Policy

| 工具 | 层级 | 说明 |
|------|------|------|
| `policy-eval` | MAIN | 策略评估入口 |
| `policy-doctor` | MAIN | 策略健康检查 |
| `policy-violations-report` | MAIN | 违规报告 |
| `probe-execution-policy` | DEBUG | 策略探针 |
| `probe-execution-policy-v2` | DEBUG | 策略探针 v2 |
| `trigger-policy` | INTERNAL | 策略触发 |
| `policy-daily-check` | INTERNAL | 每日检查 |
| `policy-shadow-tracker` | INTERNAL | Shadow 跟踪 |

---

## Health & Audit

| 工具 | 层级 | 说明 |
|------|------|------|
| `session-state-doctor` | MAIN | 状态诊断入口 |
| `agent-self-health-scheduler` | INTERNAL | 自健康调度 |
| `agent-health-check` | SPECIALIZED | 健康检查 |
| `agent-health-summary` | SPECIALIZED | 健康摘要 |
| `session-continuity-daily-check` | INTERNAL | 连续性检查 |
| `session-daily-audit` | INTERNAL | 每日审计 |
| `session-deep-audit` | DEBUG | 深度审计 |

---

## Gate & Verification

| 工具 | 层级 | 说明 |
|------|------|------|
| `gate-eval` | MAIN | Gate 评估入口 |
| `gate1-check` | SPECIALIZED | Gate 1 检查 |
| `gate-a-signer` | INTERNAL | Gate A 签名 |
| `gate-b-signer` | INTERNAL | Gate B 签名 |
| `gate-c-signer` | INTERNAL | Gate C 签名 |
| `gate-self-health-check` | INTERNAL | Gate 自检 |

---

## Memory-LanceDB (FROZEN)

| 工具 | 层级 | 说明 |
|------|------|------|
| `memory-lancedb-seed` | DEBUG | 数据种子 |
| `memory-dashboard` | SPECIALIZED | 记忆仪表盘 |
| `memory-emit` | INTERNAL | 记忆发射 |
| `memory-daily-obs` | INTERNAL | 每日观察 |
| `memory-sweeper` | INTERNAL | 记忆清理 |
| `memory-governance-test` | DEBUG | 治理测试 |

---

## Probe 类工具 (DEBUG)

| 工具 | 说明 |
|------|------|
| `probe-callback-delivery` | 回调投递探针 |
| `probe-context-overflow` | 上下文溢出探针 |
| `probe-continuity-event-log` | 连续性事件探针 |
| `probe-embedding-policy` | Embedding 策略探针 |
| `probe-gate-consistency` | Gate 一致性探针 |
| `probe-handoff-integrity` | Handoff 完整性探针 |
| `probe-mailbox-integrity` | Mailbox 完整性探针 |
| `probe-receipt-pipeline` | Receipt 管道探针 |
| `probe-session-persistence` | 会话持久化探针 |
| `probe-subagent-inbox-metrics` | Inbox 指标探针 |
| `probe-subagent-orchestration` | 子代理编排探针 |
| `probe-task-completion-protocol` | 任务完成协议探针 |
| `probe-truth-alignment` | 真相对齐探针 |

---

## 其他工具分类

### Cron/Automation (INTERNAL)
- `workflow-auto-advance`
- `retrieval-regression-runner`
- `srap-start-shadow`

### Archive/History (SPECIALIZED)
- `session-archive`
- `archive-with-distill`
- `distill-content`

### Route/Guard (SPECIALIZED)
- `route-rebind-guard`
- `route-write-guard`
- `inspect-openclaw-session-route`
- `session-route`

### Utility (LOW-LEVEL)
- `web-search`
- `searx-search.sh`
- `project-check-*`

### Test (DEBUG)
- `testbot-*`
- `test-callback-*`
- `test-path-*`
- `hook_smoke_test`

---

## 统计

| 层级 | 数量 | 占比 |
|------|------|------|
| MAIN | 12 | ~6% |
| SPECIALIZED | 35 | ~18% |
| LOW-LEVEL | 15 | ~8% |
| DEBUG | 60 | ~31% |
| INTERNAL | 70 | ~36% |
| DEPRECATED | 1 | ~1% |

---

## 标记规范

在工具文件头部添加注释：

```bash
#!/usr/bin/env python3
# LAYER: main
# PURPOSE: 统一检索入口
# DOCS: TOOLS.md, memory.md
```

---

## 注意事项

1. **MAIN 层级工具**：必须有稳定 API 和文档
2. **DEBUG 层级工具**：输出应包含 warning banner
3. **DEPRECATED 层级工具**：应指向替代入口
4. **INTERNAL 层级工具**：不应在用户文档中推荐

