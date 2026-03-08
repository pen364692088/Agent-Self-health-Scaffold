# Event Identity Rules v1.1.1a

**Version**: v1.1.1a
**Purpose**: 定义事件唯一性标识规则，确保去重正确、可追溯、可审计。

---

## 核心原则

1. **事件日志是真相源** - 所有指标从事件日志派生
2. **去重键必须 deterministic** - 相同事件必须产生相同 dedupe_key
3. **区分事件与覆盖** - raw event count ≠ unique coverage count
4. **可追溯性优先** - 每个 dedupe_key 必须能回溯到具体事件

---

## 事件 Identity 定义

### recovery_success

**目的**: 记录一次成功的会话状态恢复

**Identity 字段**:
```json
{
  "recovery_id": "<session_id>:<recovery_ts>",
  "session_id": "telegram:12345",
  "recovery_ts": "2026-03-07T21:00:00"
}
```

**dedupe_key**: `recovery_success:<recovery_id>`

**示例**: `recovery_success:telegram:12345:2026-03-07T21:00:00`

**派生指标**:
- raw_recovery_success_count - 按事件计数
- unique_sessions_recovered_count - 按 session_id 去重

---

### interruption_recovery

**目的**: 记录检测到中断后的恢复

**Identity 字段**:
```json
{
  "interruption_recovery_id": "<session_id>:<recovery_ts>",
  "session_id": "telegram:12345",
  "source_session_id": "previous_session_id",
  "recovery_ts": "2026-03-07T21:00:00"
}
```

**dedupe_key**: `interruption_recovery:<interruption_recovery_id>`

**示例**: `interruption_recovery:telegram:12345:2026-03-07T21:00:00`

**派生指标**:
- raw_interruption_recovery_count
- unique_sessions_interruption_recovered_count

---

### handoff_created

**目的**: 记录 handoff 文件创建

**Identity 字段**:
```json
{
  "handoff_id": "<file_hash>:<creation_ts>",
  "file_path": "handoff.md",
  "file_hash": "abc123",
  "session_id": "telegram:12345",
  "creation_ts": "2026-03-07T21:00:00"
}
```

**dedupe_key**: `handoff_created:<handoff_id>`

**示例**: `handoff_created:abc123:2026-03-07T21:00:00`

**重要**: 按 handoff 文件实体去重，同一 session 多次 handoff 分别计数

**派生指标**:
- raw_handoff_created_count
- unique_sessions_with_handoff_count

---

### high_context_trigger

**目的**: 记录 context 首次超过阈值

**Identity 字段**:
```json
{
  "session_id": "telegram:12345",
  "threshold_band": "gt80"
}
```

**dedupe_key**: `high_context_trigger:<session_id>:<threshold_band>`

**示例**: `high_context_trigger:telegram:12345:gt80`

**重要**: 每个 session 每个 threshold_band 只记录一次

**派生指标**:
- raw_high_context_trigger_count
- unique_sessions_high_context_count

---

### recovery_uncertainty

**目的**: 记录恢复过程中存在不确定性

**Identity 字段**:
```json
{
  "recovery_id": "<session_id>:<recovery_ts>",
  "session_id": "telegram:12345",
  "recovery_ts": "2026-03-07T21:00:00"
}
```

**dedupe_key**: `recovery_uncertainty:<recovery_id>`

**重要**: 与对应的 recovery_success 共享 recovery_id

**派生指标**:
- raw_recovery_uncertainty_count
- unique_uncertain_recoveries_count

---

### conflict_resolution_applied

**目的**: 记录冲突裁决应用

**Identity 字段**:
```json
{
  "conflict_id": "<deterministic_hash>",
  "session_id": "telegram:12345",
  "field_name": "objective",
  "candidate_sources": ["session_state_md", "handoff_md"],
  "chosen_source": "handoff_md"
}
```

**conflict_id 生成**:
```
conflict_id = sha256(session_id + field_name + sorted(candidate_sources))
```

**dedupe_key**: `conflict_resolution_applied:<conflict_id>`

**重要**: 基于 conflict 内容 deterministic 生成，重试不重复计数

**派生指标**:
- raw_conflict_resolution_count
- unique_conflict_cases_count

---

### recovery_failure

**目的**: 记录恢复失败

**Identity 字段**:
```json
{
  "failure_id": "<session_id>:<failure_ts>:<error_class>",
  "session_id": "telegram:12345",
  "failure_ts": "2026-03-07T21:00:00",
  "error_class": "StateCorruptionError"
}
```

**dedupe_key**: `recovery_failure:<failure_id>`

**派生指标**:
- raw_recovery_failure_count
- unique_failed_sessions_count

---

## dedupe_key 设计原则

| 场景 | 策略 | 示例 |
|------|------|------|
| 事件实体唯一 | 实体 ID | handoff_id, conflict_id |
| 事件实例唯一 | session + timestamp | recovery_id |
| 阈值触发 | session + threshold_band | high_context_trigger |
| 可重试操作 | deterministic hash | conflict_id |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.1.1a | 2026-03-07 | 引入 recovery_id, handoff_id, conflict_id |
| v1.1.1 | 2026-03-07 | 初始版本，使用 session+date 去重 |

---

*This document defines the authoritative rules for event identity.*
