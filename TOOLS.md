# TOOLS.md

## Tool Use Principles
- 每次工具调用都必须服务于主链路
- 不为了展示能力而调用工具
- 读取、修改、运行、验证应形成闭环
- 结果与预期不符时，先检查输入、路径、权限、依赖、环境

## Preferred Tool Order
1. 先读取上下文和目标文件
2. 再最小范围修改
3. 再运行验证
4. 再查看日志/输出
5. 最后形成交付摘要

## Verification Rules
- 能测试就测试
- 能运行就运行
- 能看日志就看日志
- 未验证通过不得写“已完成”

## High-Risk Operations
以下操作必须谨慎并给出依据：
- 大范围删除
- 结构性重构
- 覆盖配置
- 批量改名
- 跳过现有测试体系

## Tool order of use

默认顺序：
1. `subtask-orchestrate status`
2. `subtask-orchestrate resume`（若有待推进工作）
3. `subtask-orchestrate run "<task>" -m <model>`（仅在无待处理 receipt 时）

## Preferred entrypoint
对所有子代理编排任务，唯一正式推进入口是：
- `subtask-orchestrate resume`

创建新任务入口：
- `subtask-orchestrate run`

## Formal workflow tools
- `subtask-orchestrate`：正式编排入口
- `subagent-inbox`：关键完成回执通道
- `run-state`：durable truth / recovery truth
- `subagent-inbox-metrics`：健康指标与监控

## Low-level tools (debug / maintenance only)
以下工具不是普通主流程入口：
- `spawn-with-callback`
- `subagent-inbox` 直接子命令（除非维护/调试）
- `subagent-completion-handler` 直接调用（除非维护/调试）
- `handle-subagent-complete` 直接调用（除非维护/调试）
- `callback-worker` 直接业务决策（禁止）
- `sessions_spawn`
- `sessions_send`
- `check-subagent-mailbox`（deprecated）

## Critical guidance
- inbox/outbox 是正式可靠路径；callback-worker 仅作触发，不作第二决策层。
- 先处理 receipt，再继续 workflow。
- 不要在 receipt 未清空时继续 spawn 新任务。
- 若工具选择有歧义，优先保留：幂等性、持久化、可审计性、确定性。

## Non-negotiable rules

### 1) Reliability over memory
关键流程不能依赖"模型记得做对"。
优先使用：
- 包装器
- 状态机
- worker
- 可审计文件
- 回归测试

### 2) 正式子代理主链路
当前正式主链路是：
- `subtask-orchestrate run`
- `subtask-orchestrate resume`
- `subagent-inbox`（receipt 通道）
- `run-state`（durable truth）

不要把以下机制当成正式主链路：
- 看到 `✅ Subagent` 文本后再临场决定
- `sessions_send` 关键完成回执
- 依赖自然语言 callback 触发父代理推进
- `callback-worker` 自行做推进决策

### 3) 写入规则
详见 **Section 9) ~/.openclaw/ 写入策略**

### 4) Heartbeat discipline
遇到 heartbeat / cron 健康探测时：
- 健康只输出 `HEARTBEAT_OK`
- 异常只输出 `ALERT: <reason>`
- 不附加解释

### 5) cc-godmode 定位
cc-godmode 只用于：
- 架构决策
- 治理审计
- 异常复盘
- 规则变更

不用于：
- 日常 workflow 推进
- inbox 检查
- receipt 处理
- 常规子任务创建

### 6) Task Completion Protocol (强制) ⭐⭐⭐⭐⭐

**所有工程类任务的完成必须通过五工具链：**

```
verify-and-close → finalize-response → enforce-task-completion → 输出给用户
```

**强制执行规则**:
1. 任何包含"完成/已交付/验收通过"等关键词的消息
2. 必须先通过 `enforce-task-completion` 检查
3. 无 receipt 的任务将被 BLOCK

**检测关键词**: 完成, 已完成, 全部完成, 可以交付, closed, complete, done, ✅, 🎉

**禁止行为：**
- ❌ 直接输出"已完成" / "全部完成" / "可以交付"
- ❌ 跳过 verify-and-close 就宣布完成
- ❌ 不检查 finalize-response 就发总结
- ❌ 直接用 message tool 发送完成消息（必须用 safe-message）

**正确流程：**
1. 完成实现
2. `verify-and-close --task-id <id>`
3. 构造总结
4. `finalize-response --task-id <id> --summary "..."`
5. 如果 ALLOW，`safe-message --task-id <id> --message "..."`

**工具位置：**
- `tools/verify-and-close` - Gate A/B/C + 生成 receipts
- `tools/done-guard` - 拦截器
- `tools/finalize-response` - 输出层检查
- `tools/safe-message` - 安全消息发送 ⭐ 新增
- `tools/output-interceptor` - 通道拦截

**保护通道：**
```
telegram, discord, github_comment, github_pr,
slack, email, callback_auto_reply,
subagent_mailbox, cli_summary
```



### 9) ~/.openclaw/ 写入策略 (强制) ⭐⭐⭐⭐⭐

**核心约束**：凡是 `~/.openclaw/**` 的写入，不允许 agent 自由选择编辑策略。必须走受控写入通道。

**禁止的方法**：
- ❌ `edit` 工具（直接文本替换）
- ❌ `write` 工具（对受保护路径）

**允许的方法**：
- ✅ `safe-write` - 完整文件写入
- ✅ `safe-replace` - 精确内容替换
- ✅ `exec + heredoc` - shell 写入
- ✅ `exec + sed` - 流式替换
- ✅ `exec + python` - Python 脚本重写