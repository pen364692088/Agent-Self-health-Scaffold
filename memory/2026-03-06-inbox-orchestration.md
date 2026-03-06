# Session: 2026-03-06 11:54:42 UTC

- **Session Key**: agent:main:telegram:direct:8420019401
- **Session ID**: b11ddc6f-aa83-4ea1-8709-d7d1a5c27f33
- **Source**: telegram

## Conversation Summary

assistant: ## 验证完整功能
assistant: 修复文件名问题：
assistant: ## 最终总结
assistant: **Subagent Inbox v1.1 已达到 production-beta 标准。**

### 新增硬化点

| 项目 | 实现 |
|------|------|
| Claimed 超时回收 | TTL 5分钟，retry<3 重新入队，retry>=3 标记 stale |
| 单 Worker 语义 | 文件锁保证全局互斥，不支持多实例 |
| 24h Soak 计划 | `soak-monitor` 工具，每小时记录指标 |
| Retention 策略 | completed 7天，failed/timeout 30天 |
| sessions_send 定位 | 文档明确：仅非关键通知，关键回执走 inbox |

### 升正式标准

```
⏳ 24h soak 通过
⏳ 真实场景验证 (≥10 个子代理任务)
⏳ 无 P0/P1 问题
```

**下一步**：运行 24h soak，观察指标曲线。
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "6840",
  "sender_id": "8420019401",
  "sender": "Moonlight",
  "timestamp": "Fri 2026-03-06 05:46 CST"
}
```

Sender (untrusted metadata):
```json
{
  "label": "Moonlight (8420019401)",
  "id": "8420019401",
  "name": "Moonlight"
}
```

我建议你按下面这个优先级做。

最优解：把“检查邮箱”从提示词动作，变成编排层默认动作
1）只暴露高层工具，不暴露原始分散动作

不要让主 agent 自己决定要不要先调：

subagent-inbox check

subagent-completion-handler

spawn-with-callback

而是给它一个唯一正式入口，例如：

subtask-orchestrate

或 project-check-run

这个高层工具内部固定执行：

先 subagent-inbox check --once

若发现 receipt，自动跑 subagent-completion-handler

若没有 receipt，再决定是否 spawn 新子代理

最后返回“下一步该干什么”

这样 agent 不需要“记得先查邮箱”，因为它根本没有分散选择题。
工具设计替代记忆。

这才是全局最优解。

2）在 tool policy 里收口：允许包装器，弱化原始路径

OpenClaw 支持全局、per-agent、per-subagent 的 tools.allow / tools.deny 策略，也支持 tools.subagents.tools.allow/deny。

所以你应该做的是：

主 agent：允许 subtask-orchestrate、spawn-with-callback、subagent-inbox

子 agent：只保留完成任务需要的最小工具

旧工具 check-subagent-mailbox：deny 或至少 deprecated 后不再给 main agent

更进一步：

不要让主 agent 直接拿到太多“原子级”工具。
把它能走的路收窄到一两条“正确路径”，忘不忘就不重要了。

3）把规则写进 workspace bootstrap，而不是只写在聊天里

OpenClaw 会把工作区 bootstrap 文件注入上下文，默认包括 AGENTS.md、TOOLS.md、HEARTBEAT.md 等；如果你还需要额外规则文件，也可以用 bootstrap-extra-files hook 注入。

所以你应该至少写 3 处：

AGENTS.md

写“总策略”，例如：

所有子任务完成回执只认 subagent-inbox

每次准备 spawn 新子任务前，先检查 inbox

禁止把 sessions_send 当关键完成通道

TOOLS.md

写“工具用法约束”，例如：

subtask-orchestrate 是默认入口

spawn-with-callback 只能由 orchestrator 间接调用

subagent-completion-handler 不直接面向用户使用

HEARTBEAT.md

写“后台恢复策略”，例如：

若检测到 pending / claimed 过久，优先调用 subagent-inbox check --once

若发现 stuck_claimed_count > 0，走恢复流程

这样就算开新会话、重启服务、上下文压缩，规则也会随着 bootstrap 一起回来。

4）给它一个专门的 Skill

OpenClaw 支持本地和 workspace 级 Skills，且优先级是：

<workspace>/skills > ~/.openclaw/skills > bundled skills。

你可以直接做一个 skill，比如：

<workspace>/skills/subagent-inbox-default/SKILL.md

内容不是讲原理，而是讲操作顺序：

何时必须先查 inbox

何时允许 spawn

何时必须调用 completion handler

何时通知用户

这比单写在 AGENTS.md 更有效，因为 skill 是专门教工具使用顺序的。

真正防忘记的关键：加“前置闸门”

上面是“教它”，下面是“卡住它”。

5）在执行新任务前，先跑 preflight

你现在已经有 worker 在跑，那就再加一层：

任何会新建子任务、推进 workflow、回复“任务已完成”的动作前，都必须经过一个 preflight。

这个 preflight 做两件事：

subagent-inbox check --once

若有未处理 receipt，优先处理，不允许直接继续 spawn/回复

也就是说：

不是“建议先查邮箱”

而是“不查邮箱就不给继续”

这才是真正的“不会忘”。

6）让 worker 和 agent 各司其职

你现在已经有 5 秒 systemd worker，这很好。
我的建议是明确分工：

worker：保证 receipt 最终一定会被捡起来

agent：负责理解 receipt 后的业务推进和用户回复

不要让 agent 自己承担“发现 receipt”的全部责任。
因为这类工作更适合系统层轮询，不适合靠模型注意力。cron 和 heartbeat 本来就是 OpenClaw 用来定时唤醒和后台推进的机制。

我最推荐的落地方式

如果你只做一件事，我建议做这个：

把 subtask-orchestrate 变成唯一入口

主 agent 以后只调用它。
而 subtask-orchestrate 内部固定顺序：

1. subagent-inbox check --once
2. process any receipts
3. decide next state
4. if needed, spawn-with-callback
5. return concise next-step/result

然后在 tool policy 里：

allow: subtask-orchestrate, subagent-inbox-metrics

deny 或不暴露：直接 spawn-with-callback、旧版 check-subagent-mailbox

这样 agent 根本不需要自己记住流程。

你现在不要再做的事
不要继续强化“记得调用 inbox”的提示词

这只能提高概率，不能保证执行。
因为工具可用 ≠ 工具必调用；OpenClaw 的 plugin tools 可以是 required/always available，但这只是“暴露给模型”，不是“强制每轮先调用”。

不要把 MEMORY.md 当唯一保障

Memory 很重要，但文档也说得很清楚：记忆的源头是工作区文件；它能帮助“记住规则”，不能替代“系统强制执行规则”。
assistant: 完全同意。把"检查邮箱"从提示词动作变成系统强制行为。

## 1. 更新 subtask-orchestrate 为唯一入口
assistant: ## 2. 更新 AGENTS.md 和 TOOLS.md
assistant: ## 3. 创建 Subagent Inbox Default Skill
assistant: ## 4. 更新 HEARTBEAT.md
assistant: ## 5. 测试新入口
assistant: ## 6. 更新 AGENTS.md 的回调处理部分
assistant: ## 最终总结
assistant: ## 关键改进

| 改进 | 描述 |
|------|------|
| **唯一入口** | `subtask-orchestrate` 是主 agent 唯一可用的入口 |
| **强制流程** | 内部固定执行 check → process → spawn，不可跳过 |
| **工具层级** | 禁止直接调用底层工具，避免绕过强制流程 |
| **规则固化** | 写入 bootstrap 文件，新会话自动加载 |
| **Skill 教育** | 专门的 Skill 指导操作顺序 |

### 设计原则

```
❌ 不要依赖 agent 记忆
✅ 工具设计替代记忆
✅ 系统强制执行规则
✅ 唯一入口保证一致性
```

### 文件更新

| 文件 | 内容 |
|------|------|
| `tools/subtask-orchestrate` | v3.0 - 强制先检查邮箱 |
| `AGENTS.md` | 添加优先级 0 规则 |
| `TOOLS.md` | 添加工具层级约束 |
| `HEARTBEAT.md` | 添加后台恢复策略 |
| `skills/subagent-inbox-default/SKILL.md` | 操作指南 |
user: Conversation info (untrusted metadata):
```json
{
  "message_id": "6849",
  "sender_id": "8420019401",
  "sender": "Moonlight",
  "timestamp": "Fri 2026-03-06 05:52 CST"
}
```

Sender (untrusted metadata):
```json
{
  "label": "Moonlight (8420019401)",
  "id": "8420019401",
  "name": "Moonlight"
}
```

会话归档
assistant: ✅ 归档完成

| 步骤 | 状态 |
|------|------|
| Daily log | ✅ 2026-03-06.md |
| memory.md | ✅ 已更新 |
| Session 索引 | ✅ SQLite |
| 向量库归档 | ✅ 9 resources |
| Git commit | ✅ archive: session 2026-03-06 |

---

**本次会话完成**：

1. **Subagent Inbox v1.1** - 硬化的邮箱模式
2. **subtask-orchestrate v3.0** - 唯一入口，强制先检查邮箱
3. **Worker + Cron** - 5秒轮询 + 兜底
4. **规则固化** - AGENTS.md / TOOLS.md / HEARTBEAT.md / Skill
5. **E2E 验证通过** - 邮箱模式替代 sessions_send
