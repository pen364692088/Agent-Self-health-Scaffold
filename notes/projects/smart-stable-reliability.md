# Project: Smart+Stable Reliability

## Status
Active

## Progress
- Smart+Stable v2 protocol 已落地（Decision Gate / Confidence Routing / Dual-Path / Evidence-First / Context Stability）。
- 指标工具已上线：`tools/smart-stable-metrics`（baseline/snapshot/compare）。
- 每日自动 compare cron 已启用（21:05 America/Winnipeg）。

## Current baseline (24h)
- first_pass_success_rate: 93.39%
- retry_recovery_rate: 100%
- avg_turn_latency_ms: 414.59
- avoidable_failure_count: 20
- tool_error_rate: 6.61%

## Next milestone
- 连续 7 天趋势稳定：
  - 首轮成功率保持 ≥94%
  - 可避免错误降低到 <10
  - 错误率进一步下降
