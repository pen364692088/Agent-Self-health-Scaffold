# SESSION-STATE.md

## Current Objective
先闭环 Telegram 真实故障链：确认原事故发送路径 → 将 Telegram special/direct send 统一进 durable outbound queue → 补 compaction defer/recheck E2E → 暴露 channel 级 telemetry。

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
- 公共 durable outbound queue 已存在：`src/infra/outbound/deliver.ts`
- Telegram bot 回复主路径仍有直接发送入口：`src/telegram/bot-message-dispatch.ts` -> `src/telegram/bot/delivery.replies.ts`
- 该 Telegram 路径会发 `message:sent` hook，但未统一经过 write-ahead queue / queue recovery ledger
- 本轮额外硬要求已确认：保持 Telegram 现有用户可见语义不变；补真正 dedupe identity；E2E 覆盖两个最危险中断断点；telemetry 必须支持单条 reply 生命周期串联
- 用户明确要求暂停 Web/WhatsApp 横向扩展，优先修复 Telegram 原事故链

---

## 下一步
1. P0：用代码路径 + trace/log + 复现实验确认 14:40/14:45 事故实际命中的 Telegram 分支（final answer / fallback reply / native command direct reply）
2. P1：把 Telegram bot special/direct reply path 统一进 durable outbound queue，且保持 reply_to / thread fallback / chunking / media fallback / native command 即时性语义不变
3. P1.5：同时补幂等与 dedupe identity，覆盖“send 成功但 ack 未落盘”恢复后重复发送风险
4. P2：补 3 条事故导向 E2E：正常 defer+recheck；queue write 成功但 send 前中断；send 成功但 ack 前中断，断言不丢、不重、可恢复
5. P3：把 telemetry 落到可观测出口，支持单条 reply 级关联追踪（turn_id / logical_reply_id / outbound_delivery_id / channel / lifecycle / defer reason / recheck / recovery / retry / dedupe）

---

## 关键文件
- `src/telegram/bot-message-dispatch.ts`
- `src/telegram/bot/delivery.replies.ts`
- `src/channels/plugins/outbound/telegram.ts`
- `src/infra/outbound/deliver.ts`
- `src/auto-reply/reply/dispatcher-registry.ts`
- `src/agents/pi-embedded-runner/compaction-bridge.ts`
- `src/agents/pi-embedded-runner/run/attempt.ts`
