# Cron Jobs Audit Report (Updated)

## Changes Made

### 2026-03-09 19:38 UTC

1. **Retrieval Regression Runner**: 频率降低
   - Before: `0 */6 * * *` (每 6 小时)
   - After: `0 2 * * *` (每天凌晨 2 点)

2. **healthcheck.sh**: 已删除
   - 原因: 只是占位符 (exit 0)
   - 替代: Heartbeat 已有 agent-self-health-scheduler

---

## Current Cron Jobs

| Job | Schedule | Purpose | Status |
|-----|----------|---------|--------|
| antfarm @reboot | 启动时 | Dashboard 启动 | ✅ 必要 |
| proactive-check (yuno) | */30 min | Yuno agent 主动聊天 | ✅ 保留 |
| retrieval-regression | 每天 02:00 | Retrieval 测试 | ✅ 已降频 |
| subagent-inbox cleanup | 每天 00:00 | Inbox 清理 | ✅ 必要 |

## Systemd Timers

| Timer | Interval | Purpose | Status |
|-------|----------|---------|--------|
| agent-self-health-gate | 5 min | Gate 检查 | ✅ 必要 |
| agent-self-health-full | 1 hour | 完整检查 + probes | ✅ 必要 |
| longrunkit-job-watchdog | 5 min | 长任务监控 | ✅ 必要 |
| session-index-daily | 每天 03:00 | Session 索引 | ✅ 必要 |
| s1-validator-scan | 1 hour | S1 样本扫描 | ⚠️ 无输出 |
| s1-validator-hourly | 4 hours | S1 运行 | ⚠️ 无输出 |
| s1-validator-daily-report | 每天 23:30 | S1 日报 | ⚠️ 无输出 |

---

## Summary

| Category | Before | After |
|----------|--------|-------|
| Cron jobs | 4 | 4 (1 个降频) |
| Systemd timers | 9 | 9 |
| Removed | 0 | 1 (healthcheck.sh) |
| Duplicates | 0 | 0 |

---

## Notes

- **S1 Validators**: 暂时保留，等 Gate 1 通过后决定是否禁用
- **cc-godmode skill**: 保留 (是手动触发的 skill，不是 cron)
- **longrunkit**: 已覆盖长任务监控，无需额外 cc-godmode-continue

---

Last Updated: 2026-03-10 00:40 UTC
