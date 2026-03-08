# Session Continuity Rollout Modes

**Version**: v1.1.1

---

## Mode Definitions

### STABLE (Full Automation)
All features enabled, fully automatic.

| Feature | Status |
|---------|--------|
| Auto-recovery | ON |
| WAL journal | ON |
| Auto-handoff | ON |
| Conflict resolution | ON |
| Context monitoring | ON |

**Use when**: Production stable, high confidence.

---

### GUARDED STABLE (Default)
Full features with extra logging and monitoring.

| Feature | Status |
|---------|--------|
| Auto-recovery | ON |
| WAL journal | ON |
| Auto-handoff | ON + LOG |
| Conflict resolution | ON + LOG |
| Context monitoring | ON |

**Use when**: New deployment, monitoring phase.

---

### RECOVERY-ONLY
Minimal mode, recovery only.

| Feature | Status |
|---------|--------|
| Auto-recovery | ON |
| WAL journal | OFF |
| Auto-handoff | OFF |
| Conflict resolution | BASIC |
| Context monitoring | OFF |

**Use when**: Issues with WAL or handoff, need stability.

---

### MANUAL
All automatic features disabled.

| Feature | Status |
|---------|--------|
| Auto-recovery | OFF |
| WAL journal | OFF |
| Auto-handoff | OFF |
| Conflict resolution | OFF |
| Context monitoring | OFF |

**Use when**: Debugging, or severe issues.

---

## Mode Switching

### Switch to GUARDED STABLE
```bash
# Default mode, no action needed
# Or explicitly set
export SESSION_CONTINUITY_MODE=GUARDED
```

### Switch to RECOVERY-ONLY
```bash
export SESSION_CONTINUITY_MODE=RECOVERY_ONLY

# Disable WAL writes
# Disable auto-handoff
```

### Switch to MANUAL
```bash
export SESSION_CONTINUITY_MODE=MANUAL

# All features require manual invocation
session-start-recovery --recover  # Manual call
```

---

## Mode Selection Guide

| Situation | Recommended Mode |
|-----------|------------------|
| Normal operation | GUARDED STABLE |
| After stable observation | STABLE |
| WAL issues detected | RECOVERY-ONLY |
| Debugging problems | MANUAL |
| High error rate | RECOVERY-ONLY → MANUAL |

---

## Current Mode

**Active Mode**: GUARDED STABLE

**Reason**: New rollout, monitoring for stability.