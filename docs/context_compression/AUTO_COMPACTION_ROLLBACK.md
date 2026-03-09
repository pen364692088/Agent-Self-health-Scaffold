# Auto-Compaction Rollback Procedure

**Version**: 1.0
**Date**: 2026-03-09

---

## Overview

This document provides procedures for disabling, rolling back, and recovering from auto-compaction issues.

---

## Quick Rollback

### Immediate Disable

```bash
# Method 1: Environment variable
export AUTO_COMPACTION_ENABLED=false

# Method 2: Remove config file
rm -f ~/.openclaw/workspace/artifacts/context_compression/auto_compaction_config.json

# Verify disabled
auto-context-compact --health
# Should show: auto_compaction: disabled
```

### Emergency Stop

```bash
# Create stop flag
touch ~/.openclaw/workspace/artifacts/context_compression/EMERGENCY_STOP

# This will prevent all auto-compaction attempts
# Remove the file to re-enable
```

---

## Full Rollback Procedure

### Step 1: Disable Auto-Trigger

```bash
# Disable environment variable
unset AUTO_COMPACTION_ENABLED
export AUTO_COMPACTION_ENABLED=false

# Or update config
cat > ~/.openclaw/workspace/artifacts/context_compression/auto_compaction_config.json << 'EOF'
{
  "enabled": false,
  "reason": "rollback",
  "timestamp": "2026-03-09T19:45:00Z"
}
EOF
```

### Step 2: Clear Cooldown State

```bash
# Remove cooldown file to reset state
rm -f ~/.openclaw/workspace/artifacts/context_compression/cooldown_state.json

# Verify removed
ls -la ~/.openclaw/workspace/artifacts/context_compression/cooldown_state.json
# Should show: No such file or directory
```

### Step 3: Archive Shadow Traces

```bash
# Archive existing traces
mkdir -p ~/.openclaw/workspace/artifacts/context_compression/archive
mv ~/.openclaw/workspace/artifacts/context_compression/SHADOW_TRACE.jsonl \
   ~/.openclaw/workspace/artifacts/context_compression/archive/SHADOW_TRACE_$(date +%Y%m%d).jsonl

# Start fresh trace file
touch ~/.openclaw/workspace/artifacts/context_compression/SHADOW_TRACE.jsonl
```

### Step 4: Reset Baseline (Optional)

```bash
# If baseline needs reset
rm -f ~/.openclaw/workspace/artifacts/context_compression/AUTO_COMPACTION_BASELINE.json

# Re-initialize
shadow_watcher --init-baseline
```

### Step 5: Verify Rollback

```bash
# Check all components
echo "=== Rollback Verification ==="
echo ""
echo "Auto-compaction enabled:"
grep -q "enabled.*false" ~/.openclaw/workspace/artifacts/context_compression/auto_compaction_config.json 2>/dev/null && echo "  ✅ Disabled" || echo "  ⚠️ Check config"

echo ""
echo "Cooldown state:"
[ ! -f ~/.openclaw/workspace/artifacts/context_compression/cooldown_state.json ] && echo "  ✅ Cleared" || echo "  ⚠️ Still exists"

echo ""
echo "Shadow trace archived:"
[ -f ~/.openclaw/workspace/artifacts/context_compression/archive/SHADOW_TRACE_*.jsonl ] && echo "  ✅ Archived" || echo "  ℹ️ No archive needed"

echo ""
echo "Tool health:"
auto-context-compact --health
```

---

## Revert to Manual-Only Mode

### Configuration

```bash
# Disable all auto features
export AUTO_COMPACTION_ENABLED=false
export AUTO_COMPACTION_SHADOW_MODE=false

# Clear any auto-trigger configs
rm -f ~/.openclaw/workspace/artifacts/context_compression/auto_compaction_config.json
rm -f ~/.openclaw/workspace/artifacts/context_compression/shadow_config.json
```

### Manual Compaction

```bash
# Manual trigger (user-initiated)
auto-context-compact --force

# Or use individual tools
context-budget-watcher          # Check current ratio
trigger-policy --ratio 0.85     # Decide action
# Then manually decide whether to proceed
```

---

## Emergency Rollback Scenarios

### Scenario 1: High Error Rate

**Symptoms**: > 5% of compactions failing

**Actions**:
```bash
# 1. Immediate stop
touch ~/.openclaw/workspace/artifacts/context_compression/EMERGENCY_STOP

# 2. Check error logs
tail -50 ~/.openclaw/workspace/artifacts/context_compression/auto_compaction/events.jsonl | jq 'select(.event == "failed")'

# 3. Analyze root cause
auto-context-compact --health

# 4. Document issue
echo "$(date): Emergency stop due to high error rate" >> ~/.openclaw/workspace/artifacts/context_compression/ROLLBACK_LOG.md
```

### Scenario 2: Recovery Quality Degradation

**Symptoms**: Post-compaction sessions unable to resume properly

**Actions**:
```bash
# 1. Disable immediately
export AUTO_COMPACTION_ENABLED=false

# 2. Review compaction history
cat ~/.openclaw/workspace/artifacts/context_compression/COMPACTION_HISTORY.jsonl

# 3. Check recovery quality
# Review recent handoff files and session recovery

# 4. Adjust capsule_builder settings if needed
# Edit ~/.openclaw/workspace/docs/context_compression/ANCHOR_SELECTION_RULES.md
```

### Scenario 3: Threshold Too Aggressive

**Symptoms**: Triggering too frequently, disrupting work

**Actions**:
```bash
# 1. Increase threshold
# Edit AUTO_COMPACTION_POLICY.md:
# - Change normal trigger from 0.80 to 0.85
# - Change emergency trigger from 0.90 to 0.95

# 2. Re-run threshold tests
python scripts/run_threshold_replay_tests.py

# 3. Update baseline
shadow_watcher --init-baseline
```

### Scenario 4: Blocker Detection Issues

**Symptoms**: Blocking on false positives or missing real blockers

**Actions**:
```bash
# 1. Review blocker rules
cat ~/.openclaw/workspace/docs/context_compression/COMPACTION_BLOCKERS.md

# 2. Temporarily disable specific blocker
# Add bypass_allowed: true to the blocker definition

# 3. Or disable all blockers temporarily (emergency only)
trigger-policy --ratio 0.85 --force
```

---

## Recovery After Rollback

### Step 1: Fix Root Cause

- Analyze error logs
- Identify failure pattern
- Implement fix
- Test in isolation

### Step 2: Shadow Mode First

```bash
# Re-enable shadow mode only
export AUTO_COMPACTION_SHADOW_MODE=true
export AUTO_COMPACTION_ENABLED=false

# Monitor for stability
shadow_watcher --metrics
```

### Step 3: Gradual Re-enablement

```bash
# After shadow mode stable (24-48 hours)
export AUTO_COMPACTION_ENABLED=true

# Monitor closely
tail -f ~/.openclaw/workspace/artifacts/context_compression/auto_compaction/events.jsonl
```

---

## Rollback Checklist

| # | Step | Command | Status |
|---|------|---------|--------|
| 1 | Disable auto-compaction | `export AUTO_COMPACTION_ENABLED=false` | ⬜ |
| 2 | Clear cooldown state | `rm -f artifacts/.../cooldown_state.json` | ⬜ |
| 3 | Archive traces | `mv SHADOW_TRACE.jsonl archive/` | ⬜ |
| 4 | Verify disabled | `auto-context-compact --health` | ⬜ |
| 5 | Document reason | Add entry to ROLLBACK_LOG.md | ⬜ |

---

## Rollback Log Template

```markdown
## Rollback Entry: YYYY-MM-DD HH:MM

**Reason**: [Why rollback was needed]
**Symptoms**: [What was observed]
**Action Taken**: [What was done]
**Resolution**: [How issue was fixed]
**Time to Recovery**: [Duration]

**Events**:
- [Timestamp] Issue detected
- [Timestamp] Rollback initiated
- [Timestamp] Rollback complete
- [Timestamp] Root cause identified
- [Timestamp] Fix implemented
```

---

## Contact Information

For rollback assistance:
1. Check `99_HANDOFF.md` for system overview
2. Review `00_SCOPE_AND_GOALS.md` for design decisions
3. Consult phase reports for implementation details

---

**Document Version**: 1.0
**Last Updated**: 2026-03-09
