# Working Buffer

## Focus
不要继续横向铺 Web/WhatsApp。先把 Telegram 原事故链收口。

## Confirmed Findings
- durable outbound queue 主入口已经在 `src/infra/outbound/deliver.ts`
- Signal / iMessage 已经切过去
- Telegram bot inbound reply 主路径仍直接调用 `deliverReplies()`
- `deliverReplies()` 内部直接 `sendTelegramText/sendTelegramWithThreadFallback`，没有 write-ahead queue
- 因此 Telegram 仍可能处于“有 lifecycle / safe-point 感知，但 durable queue / recovery / dedupe 观测不统一”的状态

## Immediate Plan
1. 锁定 14:40/14:45 对应路径与代码入口
2. 设计最小改动：让 Telegram final/special/direct send 复用 outbound adapter/queue，而不是另造一套
3. 补原事故导向 E2E
4. 再做 telemetry 导出

## Remaining Uncertainty
- lane preview/edit 路径是否也必须全量并入 durable queue，还是先只收敛 final direct send 即可
- 原事故是否发生在 final answer、fallback send、还是 native command direct reply 分支
