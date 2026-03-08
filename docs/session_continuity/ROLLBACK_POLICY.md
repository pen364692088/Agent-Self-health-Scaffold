# Session Continuity Rollback Policy

**Version**: v1.1.1

---

## Rollback Triggers

### Critical (Immediate Rollback)

| Trigger | Severity | Action |
|---------|----------|--------|
| Recovery wrong state >= 1 time | CRITICAL | Immediate rollback |
| WAL corruption detected | CRITICAL | Immediate rollback |
| Data loss from write conflict | CRITICAL | Immediate rollback |
| System crash from continuity | CRITICAL | Immediate rollback |

### Warning (Monitor then Rollback)

| Trigger | Severity | Action |
|---------|----------|--------|
| Recovery success < 90% | WARNING | Monitor, rollback if persists |
| Uncertainty rate > 20% | WARNING | Monitor, rollback if persists |
| Performance degradation | WARNING | Investigate, rollback if needed |

### Info (Log only)

| Trigger | Severity | Action |
|---------|----------|--------|
| Fallback mode used | INFO | Log, no action |
| Minor conflict resolved | INFO | Log, no action |

---

## Rollback Decision Tree

```
Issue Detected
    │
    ├── Recovery wrong state?
    │   └── YES → IMMEDIATE ROLLBACK
    │
    ├── WAL corruption?
    │   └── YES → IMMEDIATE ROLLBACK
    │
    ├── Success rate < 90% for > 3 sessions?
    │   └── YES → ROLLBACK TO GUARDED
    │
    ├── Performance issue?
    │   └── YES → INVESTIGATE → ROLLBACK IF SEVERE
    │
    └── Minor issue?
        └── YES → LOG AND MONITOR
```

---

## Rollback Levels

### Level 1: STABLE → GUARDED STABLE
- Reduce automation
- Increase logging
- Continue operation

### Level 2: GUARDED → RECOVERY-ONLY
- Disable WAL
- Disable auto-handoff
- Keep recovery only

### Level 3: RECOVERY-ONLY → MANUAL
- All automatic features off
- Manual invocation only

---

## Rollback Procedure

1. **Identify trigger** - Determine rollback level
2. **Set mode** - Export SESSION_CONTINUITY_MODE
3. **Verify** - Check mode is applied
4. **Monitor** - Watch for improvement
5. **Report** - Document incident

---

## Post-Rollback

1. Investigate root cause
2. Fix issue in development
3. Validate fix
4. Plan re-deployment