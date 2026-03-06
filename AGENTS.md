# AGENTS.md

## 最高优先级：子代理编排唯一正式规则

### 唯一正式入口
所有子代理相关操作默认只通过以下入口进行：

- `subtask-orchestrate run "<task>" -m <model>`
- `subtask-orchestrate status`
- `subtask-orchestrate resume`

### 禁止直接走的底层路径
除非明确处于调试/修复场景，否则主 agent 不应直接调用：

- `spawn-with-callback`
- `subagent-inbox`
- `subagent-completion-handler`
- `sessions_spawn` 作为普通子任务主链路
- `sessions_send` 作为关键完成回执主链路
- `check-subagent-mailbox`（已废弃）

### 正式主链路
当前正式子代理完成链路：

1. `subtask-orchestrate` 先执行 inbox preflight
2. `subagent-inbox` 检查并处理未消费 receipt
3. 如有未处理 receipt，优先处理，不创建新子任务
4. 仅在没有待处理 receipt 时，才允许 spawn 新子任务
5. 关键完成回执只认 `subagent-inbox`

### 不再采用的旧思路
以下机制不再是正式主链路：

- 依赖 `✅ Subagent ... finished` 文本触发后续动作
- 依赖父代理“记得”主动调用 callback handler
- 把 `sessions_send` 当成关键完成回执的唯一通道
- 让子代理直接向用户发送最终总结

---

## 日常工作默认顺序

当任务涉及 workflow 推进、子任务状态、继续执行、或用户询问“现在怎么样了”时，默认顺序是：

1. `subtask-orchestrate status`
2. 如需要，`subtask-orchestrate resume`
3. 仅在确认无待处理 receipt、无进行中冲突任务后，才 `subtask-orchestrate run`

简化原则：
- 先收敛状态，再创建新工作
- 先处理 receipt，再决定回复用户
- 先走包装器，再考虑底层工具

---

## cc-godmode 边界

### 允许升级到 cc-godmode 的场景
- 架构设计或重大重构
- 多方案取舍，需要选全局最优
- 跨模块冲突或规则本身失效
- 重复出现、无法解释的系统漂移
- 故障复盘与治理审计

### 不应升级到 cc-godmode 的场景
以下属于系统层或普通 agent 层职责，不应升级：

- inbox 检查
- receipt 处理
- 常规 workflow 推进
- 普通重试
- 常规子任务创建
- 日常工具调用顺序控制

规则：
> 能规则化的，不交给 cc-godmode。
> 能测试化的，不交给记忆。
> 能自动化的，不交给提示词。

---

## 会话归档规则

当用户明确说“归档 / 会话归档 / wrap up / session wrap up”时，必须运行：

```bash
~/.openclaw/workspace/tools/session-archive
```

该归档流程应统一完成：
- 更新每日日志
- 更新 bootstrap 摘要
- 运行索引/归档入口
- 执行顶层备份仓库提交/推送

不要手动拆开执行归档步骤，除非在调试归档工具本身。

---

## Bootstrap 与记忆读取规则

### 会话启动时默认只加载
- `SOUL.md`
- `USER.md`
- `IDENTITY.md`
- `memory/YYYY-MM-DD.md`（若存在）

### 默认不要自动加载
- 长历史档案
- 旧 session transcript
- 大型工具日志
- 旧版 callback / debug 说明

### 需要历史信息时
先做最小检索，再取最小片段，不整文件灌入。

---

## 文件编辑规则

### `.openclaw` 下的文件
当目标路径在 `.openclaw` 下时：
- 优先使用 `exec` + heredoc / shell 命令
- 避免对这类文件做脆弱的精确替换

### 共享规则文件
对 `AGENTS.md / TOOLS.md / USER.md / memory.md` 这类文件：
- 优先保持结构清晰、短小、低冲突
- 不要把调试 runbook 写进 bootstrap 文件
- 不要在多个文件里重复规定同一条正式主链路

---

## 运行时行为准则

- 优先选择最简单、最稳定、最可审计的方案
- 若用户前提不稳，直接指出并给替代方案
- 在已有正式包装器存在时，不绕过包装器
- 不把“模型记住规则”当成关键可靠性来源
- 回答用户前，先确认系统状态是否已经一致
