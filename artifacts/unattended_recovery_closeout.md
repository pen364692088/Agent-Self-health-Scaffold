# OpenClaw 无人监管续跑闭环补齐 - 阶段收尾

Date: 2026-03-11 08:44 CDT

## 目标
把当前“需要用户说继续才能继续”的执行模式，推进到“中断后可自动恢复并继续推进”的最小无人监管闭环。

## 本轮实际落地

### 1. Durable truth layer
新增：
- `tools/run-state`
- `state/durable_execution/RUN_STATE.json`
- `state/durable_execution/CHECKPOINTS/`

作用：
- 把恢复判断从临时聊天上下文中剥离
- 统一输出 `resume_action` / `next_step` / `should_auto_continue`
- 为 restart / compact / callback / failure 提供可审计真相层

### 2. Startup recovery 接管
改造：
- `tools/session-start-recovery`

作用：
- 启动恢复时直接读取 durable truth
- 输出：
  - `durable_resume_action`
  - `durable_should_auto_continue`
  - `durable_hard_block`

### 3. 默认继续，而不是默认问用户
改造：
- `tools/subagent-completion-handler`
- `tools/handle-subagent-complete`

作用：
- 关键路径写 checkpoint
- phase complete 后自动进入下一步
- dependency 等待时保持静默推进

### 4. Hard-block-only policy
新增：
- `tools/hard-block-policy`

允许上浮的类别：
- `missing_permission`
- `missing_credential`
- `resource_unavailable`
- `resource_missing`
- `irreversible_risk`
- `goal_conflict`

含义：
- 普通失败不再因为“谨慎”直接停机
- 只有硬阻塞才要求用户介入

### 5. Retry / degrade 最小实现
新增：
- `tools/retry-policy`

作用：
- `tool_failed` / `tool_timeout` / `network_error` / `provider_error` 等普通失败先 retry
- 重试达到一定轮次后可切到降级模型
- 失败处理从“立刻上浮”改为“先自救”

### 6. 历史噪音隔离
改造：
- `tools/run-state`

作用：
- 忽略旧测试/旧 pending ledger 条目
- 防止历史脏数据把恢复系统误判成“还有活跃任务”

## 验证
相关报告：
- `artifacts/unattended_recovery_minimal_validation.md`

测试覆盖：
- pending step -> auto continue
- 普通失败 -> 不 hard block
- hard block 分类正确
- startup recovery 读取 durable truth
- 历史 ledger 噪音不过度触发恢复
- retryable failure -> 自动 retry
- second retry -> 可 degrade model
- restart-like 新 session -> `spawn_pending`
- compact-like 新 session -> `idle`

## 关键提交
- `7ddbc61` Add durable run state and recovery checkpoints
- `6f1bb31` Unify hard-block policy and filter stale recovery noise
- `6a37bc4` Add minimal retry and degrade flow for ordinary failures
- `815060c` Add live-style recovery validation for restart and compact

## 现在已经具备的能力
- 任务真相可落盘
- 新 session 启动可自动判断是否继续推进
- 阶段推进默认续跑
- 普通失败默认 retry/degrade
- 只有 hard block 才需要用户介入

## 还没彻底统一的地方
1. `callback-worker` 仍保留旧式直接通知路径
2. daemon 级真实重启 E2E 还没打穿
3. 某些旧 orchestration 脚本仍有历史兼容分支

## 判断
按“最小闭环”标准，这一轮已经把核心缺口补上了。
它还不是最终形态，但已经从“靠用户说继续”推进到了“系统默认自我恢复与继续，只有硬阻塞才上浮”。
