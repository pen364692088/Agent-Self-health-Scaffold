# PHASE_D_BLOCKED_STATUS.md

## 标题
Phase D / Natural Validation — BLOCKED Status

## 当前正式状态

| 项目 | 状态 |
|---|---|
| Config Alignment Gate | PASS |
| Phase C / Controlled Validation | PASS |
| Phase D / Natural Validation | BLOCKED |

## Blocked 原因

当前尚未获得**真实、可审计的 natural 0.85 trigger 样本**。

本次 blocked 的含义是：

- 不是压缩机制失效
- 不是 runtime policy 对齐失败
- 不是验证口径被破坏
- 而是当前自然 low-risk 长会话中，尚未自然出现满足条件的 budget_ratio >= 0.85 触发事件

## 关键区分

### FAIL
表示：
- 已经拿到真实 natural 样本
- 但验证点不成立

例如：
- 未命中 guardrail 2A
- 未执行 forced_standard_compression
- 触发不发生在 assemble 前
- post_compression_ratio 未回到安全区
- 安全计数器异常

### BLOCKED
表示：
- 机制没有坏
- 验证口径没有坏
- 只是自然样本条件尚未出现

本次状态属于：

> BLOCKED，而不是 FAIL。

## 已确认成立的内容

### Config Alignment Gate
已通过，说明当前 aligned runtime policy 已正式接入运行时主链路。

### Phase C / Controlled Validation
已通过，且为**可审计通过**，已确认：

- 0.85 是真实标准压缩触发点
- guardrail 2A 在运行时真实命中
- action_taken = forced_standard_compression 在运行时真实成立
- 触发发生在 assemble 前
- 压缩后 ratio 回落到安全区，且 < 0.75
- 安全计数器正常

因此，当前已经可以确认：

> aligned runtime policy 在 controlled 条件下成立。

## 尚未成立的内容

当前尚未证明：

- aligned runtime policy 在 natural low-risk 长会话 中
- 也会在合理时机自然跨过 0.85
- 并触发一次真实、可审计的 pre-assemble standard compression

因此，当前不能将 Phase D 判为 PASS。

## 当前最优策略

### 1. 冻结当前结论
- 不再硬推 Phase D 过关
- 不把 blocked 误写成 fail
- 不把 Phase C 结果外推成 Phase D 完成

### 2. 保持 aligned runtime policy 不动
禁止：

- 修改 threshold
- 修改 scoring
- 混入 OpenViking / L2
- 引入新的验证变量

### 3. 转入纯观察模式
- 等待真实 natural long-session 流量自然跨到 0.85
- 不人为制造 natural trigger
- 不用 controlled 样本替代 natural 样本

### 4. 一旦命中，立即抓取自然证据包
必须现场验证：

- natural_enforced_trigger >= 1
- guardrail 2A hit
- action_taken = forced_standard_compression
- pre_assemble_compliant = yes
- post_compression_ratio 回到安全区
- 安全计数器保持 0

## Phase D 重新启动条件

仅当出现真实 natural 0.85 trigger 事件时，Phase D 才从 BLOCKED 重新进入 ACTIVE。

重启后必须立即落以下证据：

- guardrail_event.json
- budget_before_at_085.json
- counter_before_at_085.json
- budget_after.json
- counter_after.json
- capsule_metadata.json
- natural_budget_trace.jsonl
- FIRST_NATURAL_TRIGGER_REPORT.md
- PHASE_D_FINAL_VALIDATION_REPORT.md

## 状态结论

> Phase C 已证明对齐后的 runtime policy 在 controlled 条件下成立；Phase D 目前因缺少真实 natural trigger 样本而 blocked，不应误判为 fail。

> 当前最优策略不是继续施压交付，而是维持配置冻结，等待真实 natural evidence。

## 一句话摘要

当前系统机制正常、对齐完成、受控验证通过；自然验证尚未取得真实样本，因此 Phase D 合理状态为 BLOCKED。
