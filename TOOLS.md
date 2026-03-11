# TOOLS.md

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
