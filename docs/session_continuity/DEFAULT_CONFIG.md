# Session Continuity Default Configuration

**Version**: v1.1.1  
**Last Updated**: 2026-03-07

---

## Default Behavior

All features below are **DEFAULT-ON** for new sessions:

### Recovery
- ✅ `session-start-recovery` - Auto-recovery on new session
- ✅ Field-level state extraction
- ✅ Conflict resolution with priority rules

### Persistence
- ✅ `state-write-atomic` - Atomic writes for state files
- ✅ WAL journal enabled
- ✅ `state-lock` - Concurrency protection

### Monitoring
- ✅ `pre-reply-guard` - Check before substantive replies
- ✅ `session-state-doctor` - Health diagnostics
- ✅ Context ratio monitoring (with fallback)

### Threshold Behavior
| Context | Default Action |
|---------|----------------|
| < 60% | Event-triggered writes |
| 60-80% | Check before each reply |
| > 80% | Force handoff + flush |

---

## Guarded Switches

Features that can be toggled:

| Switch | Default | Config Path |
|--------|---------|-------------|
| recovery_auto | ON | AGENTS.md |
| wal_enabled | ON | tools/state-write-atomic |
| lock_enabled | ON | tools/state-lock |
| handoff_auto | ON | HEARTBEAT.md |
| conflict_strict | ON | session-start-recovery |

---

## State Files

| File | Purpose | Auto-created |
|------|---------|--------------|
| SESSION-STATE.md | Main state | YES |
| working-buffer.md | Working memory | YES |
| handoff.md | Handoff summary | YES |
| state/wal/session_state_wal.jsonl | WAL journal | YES |

---

## Rollout Mode Configuration

### STABLE (Default)
All features enabled, full automation.

### GUARDED
- Recovery: ON
- WAL: ON
- Auto-handoff: WARNING mode (log only)

### RECOVERY-ONLY
- Recovery: ON
- WAL: OFF
- Auto-handoff: OFF

### MANUAL
All automatic features disabled. Manual invocation only.

---

## How to Change Mode

```bash
# Edit AGENTS.md to change mode
# Or set environment variable
export SESSION_CONTINUITY_MODE=GUARDED
```

---

*Configuration applies to v1.1.1 STABLE baseline.*