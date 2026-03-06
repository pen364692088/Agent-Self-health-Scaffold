# Subagent Inbox Default

## 触发条件

当涉及以下操作时自动应用：
- 启动子代理任务
- 检查子代理状态
- 恢复进行中的工作
- 编排多个子代理

## 核心规则

### 1. 唯一入口

所有子代理操作必须通过 `subtask-orchestrate` 进行。

**禁止**：
- 直接调用 `spawn-with-callback`
- 直接调用 `subagent-inbox`
- 直接调用 `subagent-completion-handler`

**允许**：
- `subtask-orchestrate run "<task>" -m <model>`
- `subtask-orchestrate status`
- `subtask-orchestrate resume`

### 2. 强制流程

`subtask-orchestrate` 内部自动执行：

```
1. subagent-inbox check --once     # 检查邮箱（不可跳过）
2. process any pending receipts    # 处理回执
3. check existing work             # 检查现有工作
4. spawn if needed                 # 如需要则 spawn
5. return next step                # 返回下一步
```

### 3. 不需要记忆

主 agent 不需要：
- ❌ 记得"先查邮箱"
- ❌ 手动调用 completion handler
- ❌ 判断是否有待处理回执

系统强制执行。

## 操作指南

### 启动新任务

```bash
subtask-orchestrate run "修复 XYZ bug" -m qianfan-code-latest
```

输出会告诉你下一步该做什么。

### 查看状态

```bash
subtask-orchestrate status
```

自动检查邮箱并返回状态。

### 恢复工作

```bash
subtask-orchestrate resume
```

自动处理待处理回执。

## 检查清单

在执行任何子代理操作前，问自己：

- [ ] 是否使用了 `subtask-orchestrate` 作为入口？
- [ ] 是否避免了直接调用底层工具？

如果答案是"是"，则符合规范。

## 异常处理

如果 `subtask-orchestrate` 失败：

1. 检查 worker 状态：`systemctl --user status subagent-inbox-worker`
2. 检查指标：`subagent-inbox-metrics`
3. 手动恢复：`subagent-inbox recover-claimed`

## 监控指标

```bash
subagent-inbox-metrics
```

关注：
- `pending_count`: 待处理回执数
- `receipt_age_p95`: 回执等待时间
- `stuck_claimed_count`: 卡住的回执数

## 后台服务

- **Worker**: 每 5 秒自动检查邮箱
- **Cleanup**: 每天凌晨清理过期文件

主 agent 只负责业务决策，系统负责发现和处理。
