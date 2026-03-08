# Rollout Metric Interpretation v1.1.1a

**Version**: v1.1.1a
**Purpose**: 解释观察期目标与指标的对应关系，明确什么场景看 raw，什么场景看 unique。

---

## 观察期目标与推荐指标

### 目标 1: "10+ 新 session 恢复"

**推荐指标**: `unique_sessions_recovered`

**理由**:
- 目标关注的是"覆盖面"——有多少不同的 session 被成功恢复
- `raw_recovery_success` 反映的是恢复事件次数，同一 session 多次恢复会重复计数
- `unique_sessions_recovered` 按 session_id 去重，更准确反映覆盖范围

**计算方式**:
```python
unique_sessions_recovered = count(distinct session_id where event_type == "recovery_success")
```

---

### 目标 2: "5+ handoff"

**推荐同时查看**:
- `raw_handoff_created` - 实际发生了多少次 handoff
- `unique_handoff_ids` - 有多少不同的 handoff 文件被创建

**理由**:
- v1.1.1a 按 handoff_id 去重，同一 session 多次 handoff 分别计数
- `raw_handoff_created` 反映 handoff 活动量
- `unique_handoff_ids` 反映实际 handoff 实体数

**计算方式**:
```python
raw_handoff_created = count(events where event_type == "handoff_created")
unique_handoff_ids = count(distinct handoff_id where event_type == "handoff_created")
```

---

### 目标 3: "3+ 高 context 触发"

**推荐指标**: `unique_sessions_high_context`

**理由**:
- 目标关注的是"影响范围"——有多少 session 遇到了高 context 情况
- `raw_high_context_trigger` 在 v1.1.1a 中每个 session 只触发一次
- 实际上 raw 和 unique 数值相同

**计算方式**:
```python
unique_sessions_high_context = count(distinct session_id where event_type == "high_context_trigger")
```

---

### 目标 4: "2+ 中断恢复"

**推荐同时查看**:
- `raw_interruption_recovery` - 中断恢复事件数
- `unique_sessions_interruption_recovered` - 被中断恢复的唯一 session 数

**理由**:
- 中断恢复是关键场景，需要了解次数和覆盖面
- 如果同一个 session 多次中断恢复，次数 > 覆盖面

**计算方式**:
```python
raw_interruption_recovery = count(events where event_type == "interruption_recovery")
unique_sessions_interruption_recovered = count(distinct session_id where event_type == "interruption_recovery")
```

---

## Rate 计算说明

### Recovery Success Rate

```
recovery_success_rate = raw_recovery_success / (raw_recovery_success + raw_recovery_failure)
```

**使用 raw 而非 unique 的原因**:
- Rate 反映的是"每次恢复尝试的成功概率"
- 应该基于事件次数，而非 session 数

### Uncertainty Rate

```
uncertainty_rate = raw_recovery_uncertainty / raw_recovery_success
```

**含义**: 在成功恢复的事件中，有多少比例存在不确定性

### Failure Rate

```
failure_rate = raw_recovery_failure / (raw_recovery_success + raw_recovery_failure)
```

---

## v1.1.1 vs v1.1.1a 差异

| 方面 | v1.1.1 | v1.1.1a |
|------|--------|---------|
| recovery_success 去重 | session + date | recovery_id (session + recovery_ts) |
| handoff_created 去重 | session + date | handoff_id (content hash + ts) |
| conflict 去重 | timestamp | conflict_id (deterministic hash) |
| 日报指标 | 单一计数 | raw + unique 双视图 |
| 多 handoff 场景 | 被压成 1 次 | 正确计数多次 |
| 多 recovery 场景 | 被压成 1 次 | 正确计数多次 |
| conflict 重试 | 可能重复计数 | deterministic 去重 |

---

## 数据迁移说明

**不需要迁移旧数据**:

1. v1.1.1a 不修改已有事件
2. 新事件按 v1.1.1a 口径写入
3. 聚合时统一处理

**Day 0 数据重解释**:

如果 Day 0 使用 v1.1.1 口径记录了事件：
- raw 指标可能被低估（多次事件被压成 1 次）
- unique 指标是准确的
- 建议在观察期结束后统一说明

---

## 判断目标达成

| 目标 | 达成标准 | 查看指标 |
|------|----------|----------|
| 10+ session 恢复 | ≥ 10 | unique_sessions_recovered |
| 5+ handoff | ≥ 5 | raw_handoff_created |
| 3+ 高 context | ≥ 3 | unique_sessions_high_context |
| 2+ 中断恢复 | ≥ 2 | raw_interruption_recovery |
| Success Rate | > 95% | recovery_success_rate |
| Uncertainty Rate | < 10% | uncertainty_rate |

---

*This document provides authoritative interpretation of rollout metrics.*
