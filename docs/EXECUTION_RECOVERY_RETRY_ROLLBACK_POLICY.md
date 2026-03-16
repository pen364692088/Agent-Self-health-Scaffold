# Execution Recovery Retry Rollback Policy

**Version**: 1.0.0-draft
**Status**: Draft
**Date**: 2026-03-16

---

## Purpose

统一管理执行、恢复、重试、回滚逻辑。

---

## Execution State Machine

```
pending → running → completed
              │
              ├─► failed → retry → running
              │               │
              │               └─► exhausted → rollback
              │
              ├─► blocked → manual_review
              │
              └─► timeout → retry → running
```

---

## Retry Policy

### Retry Rules

| Error Type | Max Retry | Backoff |
|------------|-----------|---------|
| Transient | 3 | Exponential (1s, 2s, 4s) |
| Resource | 2 | Linear (5s) |
| External | 2 | Linear (10s) |
| Permanent | 0 | N/A |

### Retry Backoff

```python
def backoff(attempt, base=1, max_delay=60):
    delay = min(base * (2 ** attempt), max_delay)
    return delay
```

### Retry Exhaustion

当 retry 次数用尽：
1. 标记 step 为 exhausted
2. 触发 rollback 或 compensation
3. 更新 task 状态

---

## Recovery Policy

### Recovery Triggers

| Trigger | Detection | Action |
|---------|-----------|--------|
| Process crash | Missing heartbeat | Resume from checkpoint |
| Step timeout | Time exceeded | Retry or fail |
| Resource failure | Health check fail | Wait and retry |
| External failure | API error | Retry with backoff |

### Recovery Process

```
1. Detect failure
2. Classify error type
3. Determine recovery action
4. Execute recovery
5. Update state
6. Continue or escalate
```

---

## Rollback Policy

### Rollback Triggers

| Trigger | Condition |
|---------|-----------|
| Retry exhausted | max_retry reached |
| Critical failure | Unrecoverable error |
| User request | Explicit rollback request |
| Gate failure | Gate A/B/C failed |

### Rollback Process

```
1. Identify completed steps
2. Execute compensation in reverse order
3. Restore previous state
4. Mark task as rolled_back
5. Generate rollback evidence
```

### Compensation Actions

| Step Type | Compensation |
|-----------|--------------|
| File create | Delete file |
| File modify | Restore from backup |
| Config change | Revert config |
| External API | Call undo API |
| Database write | Rollback transaction |

---

## Idempotency Protection

### Idempotency Rules

1. 每个操作必须有唯一 ID
2. 重复执行返回相同结果
3. Side effect 必须幂等

### Implementation

```python
def execute_step(step_id, operation):
    if is_completed(step_id):
        return get_cached_result(step_id)
    
    result = operation()
    mark_completed(step_id, result)
    return result
```

---

## Blocking Conditions

以下情况暂停执行：

1. Rollback 失败
2. Compensation 失败
3. State inconsistent
4. External blocker

---

## Evidence Requirements

### Execution Evidence

- [ ] Step start/complete log
- [ ] Retry log (if any)
- [ ] Recovery log (if any)
- [ ] Rollback log (if any)

### Success Criteria

- All steps completed
- No pending retries
- No rollback needed
- Evidence complete

---

## Appendix

### Related Documents

- failure_taxonomy.yaml
- GATE_RULES.md
- task_state.json spec

### Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0-draft | 2026-03-16 | Initial draft |
