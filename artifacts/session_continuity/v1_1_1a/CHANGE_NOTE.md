# Session Continuity v1.1.1a Change Note

**Release Date**: 2026-03-07
**Baseline**: v1.1.1 STABLE
**Type**: Metrics Fix (非功能变更)

---

## 变更摘要

v1.1.1a 修正了观察期事件统计口径，解决去重键过粗、重复计数、低估等问题。

---

## 修复的问题

### P0-1: handoff_created 去重过粗
- **原问题**: `dedupe_key = session_id + date`，同一天同一 session 多个 handoff 被压成 1 次
- **修复**: 改为 `dedupe_key = handoff_id`，按 handoff 文件实体去重
- **影响**: handoff 事件数不再被低估

### P0-2: recovery_success 去重过粗
- **原问题**: `dedupe_key = session_id + date`，同一天同一 session 多次恢复被压成 1 次
- **修复**: 改为 `dedupe_key = recovery_id`，其中 `recovery_id = session_id + recovery_ts`
- **影响**: 可以区分"恢复次数"和"覆盖 session 数"

### P0-3: conflict_resolution_applied 去重键脆弱
- **原问题**: `dedupe_key = timestamp`，重试/时间精度/重复写入场景不稳
- **修复**: 改为 `dedupe_key = conflict_id`，deterministic 生成
- **影响**: conflict 重试不会重复计数

### P1-1: daily-check 只输出单一数字
- **原问题**: 只有 count，无法区分 raw event 和 unique coverage
- **修复**: 同时输出 Raw Metrics 和 Unique/Coverage Metrics 两层视图
- **影响**: 观察期判断更准确

---

## 新增文件

| 文件 | 用途 |
|------|------|
| `docs/session_continuity/EVENT_IDENTITY_RULES.md` | 事件唯一性标识规则 |
| `docs/session_continuity/METRIC_SEMANTICS.md` | 指标语义定义 |
| `docs/session_continuity/ROLLOUT_METRIC_INTERPRETATION.md` | 观察期指标解释 |
| `tools/parse-continuity-events` | 事件日志解析脚本 |
| `artifacts/session_continuity/v1_1_1a/CHANGE_NOTE.md` | 本文件 |

---

## 修改文件

| 文件 | 修改内容 |
|------|----------|
| `tools/continuity-event-log` | 支持 recovery_id, handoff_id, conflict_id 等身份字段 |
| `tools/session-start-recovery` | 添加 generate_conflict_id，传递 recovery_ts |
| `tools/handoff-create` | 生成 handoff_id，传递给事件日志 |
| `tools/session-continuity-daily-check` | 双层指标输出 (raw + unique) |

---

## 新旧 dedupe_key 对比

| 事件类型 | v1.1.1 | v1.1.1a |
|----------|--------|---------|
| recovery_success | `session:date` | `recovery_id` |
| interruption_recovery | `session:date` | `interruption_recovery_id` |
| handoff_created | `session:date` | `handoff_id` |
| high_context_trigger | `session` | `session:threshold_band` |
| conflict_resolution_applied | `timestamp` | `conflict_id` |
| recovery_uncertainty | `session:date` | `recovery_id` |
| recovery_failure | `session:date` | `failure_id` |

---

## 指标分层

### Raw Event Metrics (事件次数)
- `raw_recovery_success_count`
- `raw_handoff_created_count`
- `raw_high_context_trigger_count`
- `raw_interruption_recovery_count`
- `raw_recovery_uncertainty_count`
- `raw_conflict_resolution_count`
- `raw_recovery_failure_count`

### Unique / Coverage Metrics (覆盖面)
- `unique_sessions_recovered_count`
- `unique_sessions_with_handoff_count`
- `unique_sessions_high_context_count`
- `unique_sessions_interruption_recovered_count`
- `unique_handoff_ids`
- `unique_conflict_cases`

---

## 回归验证结果

| 测试 | 结果 |
|------|------|
| Test A: 多 handoff 不低估 | ✅ PASS |
| Test B: 多 recovery 正确区分 raw/unique | ✅ PASS |
| Test C: conflict 重试不重复计数 | ✅ PASS |
| Test D: high_context 不无限累计 | ✅ PASS |
| Test E: 日报双视图正确 | ✅ PASS |

---

## 对观察期的影响

- **建议立即切换到 v1.1.1a 口径**
- 已有 Day 0 数据可以保留，新事件按新口径写入
- 观察期结束时需要说明新旧口径差异

---

## 兼容性

- ✅ 不修改核心恢复逻辑
- ✅ 不影响稳定 rollout
- ✅ 不需要迁移旧数据
- ✅ 向后兼容

---

*End of Change Note*
