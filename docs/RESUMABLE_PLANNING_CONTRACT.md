# Resumable Planning Contract

**Version**: 1.0.0-draft
**Status**: Draft
**Date**: 2026-03-16

---

## Purpose

定义长任务如何自动规划、checkpoint、中断恢复、动态重规划。

---

## Planning Rules

### Task Decomposition

**粒度规则**:
- 每个 step 必须 ≤ 30 分钟
- 每个 step 必须 atomic
- 每个 step 必须有明确的成功标准

**Decomposition Tree**:
```
Task
├── Step 1
│   ├── Sub-step 1.1
│   └── Sub-step 1.2
├── Step 2
│   ├── Sub-step 2.1
│   └── Sub-step 2.2
└── Step 3
```

---

## Checkpoint Rules

### Checkpoint Frequency

| Event | Checkpoint |
|-------|------------|
| Step start | Required |
| Step complete | Required |
| Step fail | Required |
| Replan trigger | Required |
| Max interval | Every 5 minutes |

### Checkpoint Content

```json
{
  "task_id": "...",
  "step_id": "...",
  "state": "running|completed|failed",
  "progress": 0.5,
  "evidence": ["path/to/evidence"],
  "timestamp": "2026-03-16T00:00:00Z",
  "checksum": "..."
}
```

---

## Recovery Rules

### Recovery Triggers

| Trigger | Action |
|---------|--------|
| Process restart | Resume from last checkpoint |
| Step timeout | Retry or skip |
| Step failure | Retry or rollback |
| Resource unavailable | Wait and retry |

### Recovery Process

```
1. Load last checkpoint
2. Verify state integrity
3. Resume from current step
4. Continue execution
```

---

## Replan Rules

### Replan Triggers

| Trigger | Condition |
|---------|-----------|
| Step fail ≥ N times | N = max_retry |
| Dependency change | New dependency detected |
| Goal change | User modifies goal |
| Resource change | Resource unavailable |
| Time exceeded | Task > max_duration |

### Replan Constraints

1. 已完成的 step 不能丢失
2. 重规划不能回滚已完成的工作
3. 重规划次数 ≤ 3 次
4. 重规划必须有明确理由

### Replan Process

```
1. Detect replan trigger
2. Preserve completed steps
3. Generate new plan
4. Validate new plan
5. Continue execution
```

---

## Progress Tracking

### Progress Metrics

| Metric | Description |
|--------|-------------|
| steps_total | Total steps |
| steps_completed | Completed steps |
| steps_failed | Failed steps |
| progress_percent | Completion percentage |
| elapsed_time | Time elapsed |
| estimated_remaining | Estimated time remaining |

### Progress Persistence

- Progress 存储在 task_state.json
- 每次状态变化时更新
- 支持 crash recovery

---

## Blocking Conditions

以下情况暂停规划：

1. 重规划次数 ≥ 3
2. 关键依赖缺失
3. 资源不足
4. 外部 blocker

---

## Evidence Requirements

### Planning Evidence

- [ ] Decomposition tree
- [ ] Checkpoint log
- [ ] Recovery log (if any)
- [ ] Replan log (if any)

### Success Criteria

- All steps completed
- Evidence complete
- No orphan checkpoints

---

## Appendix

### Related Documents

- task_state.json spec
- step_packet spec
- GATE_RULES.md

### Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0-draft | 2026-03-16 | Initial draft |
