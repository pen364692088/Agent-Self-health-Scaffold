# Metric Semantics v1.1.1a

**Version**: v1.1.1a
**Purpose**: 定义双层指标模型，区分原始事件计数与覆盖面统计。

---

## 核心模型

```
┌─────────────────────────────────────────────────────────┐
│                 Event Log (Source of Truth)             │
│             session_continuity_events.jsonl             │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────┴─────────────────┐
         │                                   │
         ▼                                   ▼
┌─────────────────┐                 ┌─────────────────┐
│  Raw Metrics    │                 │ Unique Metrics  │
│  (Event Count)  │                 │ (Coverage)      │
└─────────────────┘                 └─────────────────┘
```

---

## Layer A: Raw Event Metrics

**用途**: 统计事件发生次数，反映系统活动量

| 指标名 | 含义 | 事件类型 |
|--------|------|----------|
| raw_recovery_success_count | 成功恢复事件数 | recovery_success |
| raw_handoff_created_count | Handoff 创建事件数 | handoff_created |
| raw_high_context_trigger_count | 高 context 触发数 | high_context_trigger |
| raw_interruption_recovery_count | 中断恢复事件数 | interruption_recovery |
| raw_recovery_uncertainty_count | 不确定恢复事件数 | recovery_uncertainty |
| raw_conflict_resolution_count | 冲突裁决事件数 | conflict_resolution_applied |
| raw_recovery_failure_count | 恢复失败事件数 | recovery_failure |

**计算方式**:
```bash
raw_recovery_success_count = count(events where event_type == "recovery_success")
```

---

## Layer B: Unique / Coverage Metrics

**用途**: 统计影响的唯一实体数，反映覆盖面

| 指标名 | 含义 | 去重维度 |
|--------|------|----------|
| unique_sessions_recovered_count | 被恢复的唯一 session 数 | session_id |
| unique_sessions_with_handoff_count | 有 handoff 的唯一 session 数 | session_id |
| unique_sessions_high_context_count | 触发高 context 的唯一 session 数 | session_id |
| unique_sessions_interruption_recovered_count | 中断恢复的唯一 session 数 | session_id |
| unique_uncertain_recoveries_count | 不确定恢复的唯一次数 | recovery_id |
| unique_conflict_cases_count | 唯一冲突案例数 | conflict_id |
| unique_failed_sessions_count | 恢复失败的唯一 session 数 | session_id |

**计算方式**:
```bash
unique_sessions_recovered_count = count(distinct session_id where event_type == "recovery_success")
unique_conflict_cases_count = count(distinct conflict_id where event_type == "conflict_resolution_applied")
```

---

## Derived Rates

基于 raw 指标计算：

### Recovery Success Rate
```
recovery_success_rate = raw_recovery_success_count / 
                        (raw_recovery_success_count + raw_recovery_failure_count)
```

### Uncertainty Rate
```
uncertainty_rate = raw_recovery_uncertainty_count / raw_recovery_success_count
```

### Failure Rate
```
failure_rate = raw_recovery_failure_count / 
               (raw_recovery_success_count + raw_recovery_failure_count)
```

---

## Rollout Coverage Targets

观察期 (2026-03-07 ~ 2026-03-14) 目标：

| 目标 | 推荐指标 | 理由 |
|------|----------|------|
| 10+ 新 session 恢复 | unique_sessions_recovered_count | 看覆盖面 |
| 5+ handoff | raw_handoff_created_count + unique_sessions_with_handoff_count | 同时看次数和覆盖 |
| 3+ 高 context 触发 | unique_sessions_high_context_count | 看影响范围 |
| 2+ 中断恢复 | raw_interruption_recovery_count | 看实际发生次数 |

---

## 输出格式要求

### HEALTH_SUMMARY.md

必须包含以下两个表格：

```markdown
## Raw Event Metrics

| Metric | Count |
|--------|-------|
| recovery_success | X |
| handoff_created | X |
| ... | ... |

## Unique / Coverage Metrics

| Metric | Count |
|--------|-------|
| unique_sessions_recovered | X |
| unique_sessions_with_handoff | X |
| ... | ... |
```

### ROLLOUT_OBSERVATION.md

每日日志必须区分 raw 和 unique：

```markdown
### Day N (YYYY-MM-DD)

**Raw Events**:
- recovery_success: X
- handoff_created: X

**Coverage**:
- unique_sessions_recovered: X
- unique_sessions_with_handoff: X
```

---

## 与 v1.1.1 的差异

| 方面 | v1.1.1 | v1.1.1a |
|------|--------|---------|
| recovery_success 去重 | session + date | recovery_id |
| handoff_created 去重 | session + date | handoff_id |
| conflict 去重 | timestamp | conflict_id |
| 日报指标 | 单一计数 | raw + unique 双视图 |
| 目标达成判断 | 模糊 | 明确区分次数 vs 覆盖 |

---

## 数据迁移说明

v1.1.1a 不需要迁移旧数据：

1. 旧事件日志保留原样
2. 新事件按新口径写入
3. 聚合时按版本标签区分计算

---

*This document defines the authoritative metric semantics.*
