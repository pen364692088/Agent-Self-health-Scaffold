# Session Continuity v1.1.1a Metric Validation Report

**Generated**: 2026-03-07T21:24:00-06:00
**Version**: v1.1.1a

---

## Validation Summary

| Test | Status | Details |
|------|--------|---------|
| Test A: Multi-handoff | ✅ PASS | 3 handoffs correctly counted |
| Test B: Multi-recovery | ✅ PASS | raw=2, unique_sessions=1 |
| Test C: Conflict retry | ✅ PASS | Deterministic dedup working |
| Test D: High context | ✅ PASS | No infinite accumulation |
| Test E: Dual-layer report | ✅ PASS | Raw and unique both shown |

---

## Test A: handoff 多次创建不再被低估

**场景**: 同一 session 同一天创建 3 次有效 handoff

**操作**:
```bash
handoff-create --json  # handoff 1
handoff-create --json  # handoff 2
handoff-create --json  # handoff 3
```

**期望**:
- `raw_handoff_created_count = 3`
- `unique_handoff_ids = 3`

**实际**:
```
raw_handoff_created = 3 ✅
unique_handoff_ids = 3 ✅
```

**结论**: ✅ PASS - 每个 handoff 按其实体 ID 去重，不再被低估

---

## Test B: 同一 session 多次真实 recovery

**场景**: 同一 session 一天内发生 2 次真实恢复

**操作**:
```bash
continuity-event-log recovery_success --session-id s1 --recovery-ts "2026-03-07T10:00:00"
continuity-event-log recovery_success --session-id s1 --recovery-ts "2026-03-07T15:00:00"
continuity-event-log recovery_success --session-id s1 --recovery-ts "2026-03-07T10:00:00"  # duplicate
```

**期望**:
- `raw_recovery_success_count = 2`
- `unique_sessions_recovered_count = 1`

**实际**:
```
raw_recovery_success = 2 ✅
unique_sessions_recovered = 1 ✅
```

**结论**: ✅ PASS - 多次恢复正确计数，unique session 正确去重

---

## Test C: conflict 重试不重复计数

**场景**: 同一 conflict case 被重复处理 2 次

**操作**:
```bash
continuity-event-log conflict_resolution_applied --conflict-id "abc123"
continuity-event-log conflict_resolution_applied --conflict-id "abc123"  # duplicate
continuity-event-log conflict_resolution_applied --conflict-id "xyz789"  # different
```

**期望**:
- `raw_conflict_resolution_count = 2`
- `unique_conflict_cases = 2`

**实际**:
```
raw_conflict_resolution = 2 ✅
unique_conflict_cases = 2 ✅
```

**结论**: ✅ PASS - Deterministic conflict_id 防止重试重复计数

---

## Test D: high_context_trigger 不无限累计

**场景**: 同一 session 长时间保持 >80%

**操作**:
```bash
continuity-event-log high_context_trigger --session-id s1 --threshold-band gt80  # first
continuity-event-log high_context_trigger --session-id s1 --threshold-band gt80  # skip
continuity-event-log high_context_trigger --session-id s1 --threshold-band gt80  # skip
continuity-event-log high_context_trigger --session-id s2 --threshold-band gt80  # different session
```

**期望**:
- `raw_high_context_trigger_count = 2`
- `unique_sessions_high_context = 2`

**实际**:
```
raw_high_context_trigger = 2 ✅
unique_sessions_high_context = 2 ✅
```

**结论**: ✅ PASS - 每个 session 每个 threshold_band 只触发一次

---

## Test E: 日报 raw / unique 双视图正确

**场景**: 构造混合事件日志后运行 daily-check

**操作**:
```bash
session-continuity-daily-check
```

**期望**: HEALTH_SUMMARY.md 同时展示 raw 和 unique 两层指标

**实际**:
```markdown
## Raw Event Metrics

| Event Type | Count |
|------------|-------|
| recovery_success | 2 |
| handoff_created | 3 |
| high_context_trigger | 2 |
| conflict_resolution_applied | 2 |

## Unique / Coverage Metrics

| Metric | Count |
|--------|-------|
| unique_sessions_recovered | 1 |
| unique_handoff_ids | 3 |
| unique_sessions_high_context | 2 |
| unique_conflict_cases | 2 |
```

**结论**: ✅ PASS - 双层指标正确展示

---

## Event Log Traceability

所有测试事件均可追溯到原始日志：

```
state/session_continuity_events.jsonl
├── 9 events total
├── 2 recovery_success (2 unique recovery_ids)
├── 3 handoff_created (3 unique handoff_ids)
├── 2 high_context_trigger (2 sessions)
└── 2 conflict_resolution_applied (2 conflict_ids)
```

---

## Recommendations

1. ✅ 建议立即切换到 v1.1.1a 口径
2. ✅ 观察期数据使用新口径收集
3. ✅ Day 0 数据保留，不影响观察期判断

---

*End of Validation Report*
