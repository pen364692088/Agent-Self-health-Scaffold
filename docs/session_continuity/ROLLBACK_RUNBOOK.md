# Session Continuity Rollback Runbook

**Version**: v1.1.1

---

## Quick Rollback Commands

### Rollback to GUARDED STABLE
```bash
export SESSION_CONTINUITY_MODE=GUARDED
# Verify
session-state-doctor --json | grep mode
```

### Rollback to RECOVERY-ONLY
```bash
export SESSION_CONTINUITY_MODE=RECOVERY_ONLY
# Disable WAL writes
# Disable auto-handoff
```

### Rollback to MANUAL
```bash
export SESSION_CONTINUITY_MODE=MANUAL
# All features require manual call
```

---

## Rollback Scenarios

### Scenario 1: Recovery Wrong State

**Symptoms**:
- Recovery returns incorrect objective
- User reports context loss
- Phase/branch mismatch

**Action**:
```bash
# 1. Immediate rollback
export SESSION_CONTINUITY_MODE=RECOVERY_ONLY

# 2. Check state files
session-state-doctor --json

# 3. Manual recovery
session-start-recovery --recover --debug

# 4. Report incident
echo "Rollback: Wrong recovery state" >> artifacts/session_continuity/incidents.log
```

---

### Scenario 2: WAL Corruption

**Symptoms**:
- WAL read errors
- Invalid JSON in WAL
- Write failures

**Action**:
```bash
# 1. Immediate rollback
export SESSION_CONTINUITY_MODE=MANUAL

# 2. Backup WAL
cp state/wal/session_state_wal.jsonl state/wal/session_state_wal.jsonl.bak

# 3. Inspect WAL
head -20 state/wal/session_state_wal.jsonl

# 4. Reset if needed
rm state/wal/session_state_wal.jsonl
touch state/wal/session_state_wal.jsonl

# 5. Report incident
```

---

### Scenario 3: Performance Degradation

**Symptoms**:
- Slow recovery
- High latency on state writes
- System sluggish

**Action**:
```bash
# 1. Check WAL size
ls -la state/wal/

# 2. If large, truncate
tail -100 state/wal/session_state_wal.jsonl > state/wal/tmp.jsonl
mv state/wal/tmp.jsonl state/wal/session_state_wal.jsonl

# 3. If persists, rollback
export SESSION_CONTINUITY_MODE=RECOVERY_ONLY

# 4. Report incident
```

---

## Post-Rollback Checklist

- [ ] Mode set correctly
- [ ] Functionality verified
- [ ] Incident logged
- [ ] Root cause investigation started
- [ ] Fix plan created
- [ ] Re-deployment plan ready

---

## Recovery from Rollback

When ready to re-enable:

```bash
# 1. Verify fix is deployed
session-state-doctor

# 2. Run tests
python scripts/run_session_continuity_checks.py --gate all

# 3. Re-enable
unset SESSION_CONTINUITY_MODE  # Return to default

# 4. Monitor
session-start-recovery --recover --summary
```