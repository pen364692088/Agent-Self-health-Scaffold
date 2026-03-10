# Open Loops

## Active

- [ ] Execution Policy v1 观察窗 (3-7 天)
  - 等待样本成熟: deny≥5, warn≥10
  - 检查: `policy-daily-report --save`
  - 评估后决定是否 A-confirmed

- [ ] Context Compression Gate 1
  - 样本数不足 (需要 ≥80)
  - Shadow Mode 运行中
  - 不急着上 runtime

- [ ] v1.1 候选规则 Shadow Tracking
  - PERSIST_BEFORE_REPLY: 0 hits
  - FRAGILE_REPLACE_BLOCK: 0 hits
  - CHECKPOINT_REQUIRED_BEFORE_CLOSE: 0 hits

## Completed This Session ✅

- [x] Execution Policy Framework v1 实现
- [x] Gate A/B/C 验证
- [x] 监控接入 heartbeat
- [x] Cron jobs 优化
- [x] Session 清理机制固化
- [x] context = unknown 诊断 (A-confirmed)

## Notes

- Qianfan provider usage 不可观测 (归档为观测缺口)
- S1 validator timers 暂未禁用 (无输出，可后续处理)
