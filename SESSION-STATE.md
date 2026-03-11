# SESSION-STATE.md

## Current Objective
收口 OpenClaw reply → durable queue → compaction safe-point 闭环。

## Phase
INPROGRESS

## Branch
main

## Blocker
None

---

## 最新推进

### 已完成补丁

#### 第一轮：compaction safe-point guard (8e8bcb6)
- 给 compaction 加了 `reply_in_flight` 检查
- compaction 触发前先检查全局 pending replies
- 如果有 reply in flight，跳过 compaction

#### 第二轮：bounded defer + automatic recheck (dd71b00)
- 统一 reply lifecycle snapshot/state machine
- `reply_in_flight` 判断基于统一 snapshot
- compaction defer 后 bounded wait (5s)
- 自动 recheck compaction
- telemetry 入口：deferCount, deferDurationMs, recoveryCount, retryCount, dedupeCount

#### 第三轮：Signal / iMessage 统一到 durable outbound delivery (43e0573)
- `src/signal/monitor.ts`: deliverReplies 改为调用 deliverOutboundPayloads
- `src/imessage/monitor/deliver.ts`: deliverReplies 改为调用 deliverOutboundPayloads
- 两者现在都走统一的 outbound adapter + write-ahead queue

---

## 当前状态
- compaction ↔ reply lifecycle 闭环已打通
- Signal / iMessage 已统一到公共 durable delivery
- telemetry 骨架已在主链

---

## 下一步
1. Web/WhatsApp direct-send path 统一
2. 降级策略完整自动化（短消息/结论优先）
3. telemetry 落地到可观测出口

---

## 关键文件
- `src/agents/pi-embedded-runner/compaction-bridge.ts`
- `src/agents/pi-embedded-runner/run/attempt.ts`
- `src/auto-reply/reply/dispatcher-registry.ts`
- `src/auto-reply/reply/reply-dispatcher.ts`
- `src/infra/outbound/deliver.ts`
- `src/signal/monitor.ts`
- `src/imessage/monitor/deliver.ts`
