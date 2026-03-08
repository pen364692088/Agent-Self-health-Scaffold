# TOOLS.md

## Tool order of use

默认顺序：
1. `subtask-orchestrate status`
2. `subtask-orchestrate resume`（若有待推进工作）
3. `subtask-orchestrate run "<task>" -m <model>`（仅在无待处理 receipt 时）

## Preferred entrypoint
对所有子代理编排任务，优先入口是：
- `subtask-orchestrate`

## Formal workflow tools
- `subtask-orchestrate`：正式编排入口
- `subagent-inbox`：关键完成回执的正式通道
- `subagent-completion-handler`：处理回执并推进 workflow
- `subagent-inbox-metrics`：健康指标与监控

## Low-level tools (debug / maintenance only)
以下工具不是普通主流程入口：
- `spawn-with-callback`
- `subagent-inbox` 直接子命令（除非维护/调试）
- `subagent-completion-handler` 直接调用（除非维护/调试）
- `sessions_spawn`
- `sessions_send`
- `check-subagent-mailbox`（deprecated）

## Critical guidance
- inbox/outbox 是正式可靠路径；实时 callback 只作辅助通知或调试。
- 先处理 receipt，再继续 workflow。
- 不要在 receipt 未清空时继续 spawn 新任务。
- 若工具选择有歧义，优先保留：幂等性、持久化、可审计性、确定性。

## External path write caveat
对于 workspace 之外的路径：
- 不要依赖 `write` 直接写外部仓库
- 优先 `exec` + heredoc
- 写前确认绝对路径与父目录存在

## Session memory tools
- `session-indexer`：原始日志 → 结构化索引
- `session-query`：统一检索入口
- `openviking find`：语义检索兜底

规则：
- 先最小检索，再最小读取
- 不整库灌入 prompt

<!-- EMOTIOND_RUNTIME_BEGIN -->
```json
{
  "target_id": "telegram:8420019401",
  "channel": "telegram",
  "from": "telegram:8420019401",
  "conversation_id": "telegram:8420019401",
  "message_id": "7834",
  "ts": 1772955417000,
  "dt_seconds": 300,
  "request_id_base": "telegram:7834",
  "pre_decision": {
    "action": "boundary",
    "decision_id": 335
  },
  "allowed_subtypes_infer": [
    "care",
    "apology",
    "ignored",
    "rejection",
    "betrayal",
    "neutral",
    "uncertain"
  ]
}
```
<!-- EMOTIOND_RUNTIME_END -->

---

## Task Completion Protocol (OPENCLAW_EXECUTION_POLICY) - 2026-03-06

### 核心规则

1. **唯一收尾入口**: 所有任务必须通过 `verify-and-close` 完成
2. **四类 receipt 必需**: contract/e2e/preflight/final
3. **状态机驱动**: 不能靠文本判断完成
4. **human_failed 必回退**: 不能忽视用户失败反馈

### 工具

**verify-and-close** - 统一收尾入口
```bash
# 完整验证
verify-and-close --task-id <id> --artifacts path1,path2

# 跳过 E2E (非代码任务)
verify-and-close --task-id <id> --skip-e2e

# JSON 输出
verify-and-close --task-id <id> --json
```

输出:
- `READY_TO_CLOSE` - 所有 Gate 通过
- `BLOCKED` - 存在阻断条件

**done-guard** - 完成拦截器
```bash
# 完整检查 (receipts + state + human_failed)
done-guard --task-id <id> --all

# 文本伪完成检测
done-guard --check-text <file>

# 状态迁移校验
done-guard --validate-state current:target

# doctor report 验证
done-guard --validate-doctor <report.json>
```

### Receipt 文件位置

```
artifacts/receipts/
├── <task_id>_contract_receipt.json
├── <task_id>_e2e_receipt.json
├── <task_id>_preflight_receipt.json
└── <task_id>_final_receipt.json
```

### Schema

- `schemas/task_receipt.v1.schema.json` - Receipt schema

### 状态机

```
planned -> implementing -> self_verify -> await_human_test
                                    ↓              ↓
                              human_failed <- repairing
                                    ↓
                              reverify -> ready_to_close -> closed
```

---
Added: 2026-03-06 09:05 CST

---

## Completion Bypass Audit (2026-03-06)

### 审计结果

**扫描范围**: 4319 个文件

**问题分布**:
| 风险级别 | 数量 | 说明 |
|---------|------|------|
| High | 0 | 无高风险 |
| Medium | 933 | 主要是历史文档记录 |
| Low | 703 | 测试文件、注释等 |

**工具集成状态**:
| 工具 | 状态 | 原因 |
|------|------|------|
| callback-worker | ✅ | v8.0 直接发送通知（openclaw message send --account manager） |
| callback-handler-auto | ❌ | 不直接发送消息，返回 action |
| spawn-with-callback | ❌ | Spawn 子代理，非输出点 |

### 架构分析

**真正出口点**: `message` tool (OpenClaw 核心)

**拦截策略**: 
1. ✅ 创建 `safe-message` wrapper
2. ✅ SOUL.md 强制要求使用 safe-message
3. ⏳ 需要在 OpenClaw 核心集成检查

### 工具

**safe-message** - 安全消息发送
```bash
# 自动检查 execution policy
safe-message --task-id <id> --channel telegram --message "..."

# 强制发送（危险）
safe-message --task-id <id> --message "..." --force
```

**completion-bypass-audit** - 旁路审计
```bash
# 扫描仓库
completion-bypass-audit

# JSON 输出
completion-bypass-audit --json

# 显示修复建议
completion-bypass-audit --fix-hints
```

### 剩余风险

| 风险 | 状态 | 缓解措施 |
|------|------|----------|
| 直接调用 message tool | 中 | SOUL.md 强制 + 审计 |
| 历史文档误报 | 低 | 已知问题，不影响实时输出 |
| OpenClaw 核心未集成 | 中 | safe-message wrapper |

---
Added: 2026-03-06 09:22 CST
