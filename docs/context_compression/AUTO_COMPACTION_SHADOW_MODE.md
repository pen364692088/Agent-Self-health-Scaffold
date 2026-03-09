# Auto-Compaction Shadow Mode v1.0

## Overview

Shadow mode allows running the auto-compaction system in a "dry-run" fashion: it executes all decision logic and records what WOULD happen, but does not perform actual compression. This enables safe validation in production-like conditions without risk.

---

## Definition

**Shadow Mode** = Run `auto-context-compact` with `--dry-run` flag, plus structured logging for metrics collection.

```
┌─────────────────────────────────────────────────────────────┐
│                    SHADOW MODE FLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Budget Watcher    → Get current ratio                  │
│  2. Trigger Policy    → Determine action (no execution)    │
│  3. Blocker Detection → Check all blockers                 │
│  4. Metrics Recording → Log what WOULD happen              │
│  5. No Compression    → Skip actual context reduction      │
│                                                             │
│  Output: SHADOW_TRACE.jsonl (one entry per run)            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## How to Enable

### Option 1: Environment Variable

```bash
export AUTO_COMPACTION_SHADOW_MODE=true
```

### Option 2: Configuration File

Create `artifacts/context_compression/shadow_config.json`:

```json
{
  "enabled": true,
  "log_trace": true,
  "metrics_interval_seconds": 300,
  "collect_baseline": true
}
```

### Option 3: Direct Tool Invocation

```bash
shadow_watcher --run-once
```

---

## Monitoring Metrics

### Primary Metrics

| Metric | Description | Target Range |
|--------|-------------|--------------|
| `trigger_count` | Times compaction would trigger | Monitor trend |
| `would_compact_count` | Times actual compression would execute | Compare to baseline |
| `blockers_hit` | Blockers encountered | < 10% of triggers |
| `ratio_distribution` | Distribution of observed ratios | Centered below 0.80 |

### Secondary Metrics

| Metric | Description | Purpose |
|--------|-------------|---------|
| `normal_trigger_count` | Normal mode triggers | Understand workload |
| `emergency_trigger_count` | Emergency mode triggers | Risk assessment |
| `cooldown_hits` | Cooldown prevented triggers | Validate cooldown logic |
| `hysteresis_transitions` | Zone transitions | State machine validation |

### Calculated Metrics

```python
def calculate_derived_metrics(trace_entries):
    """Calculate derived metrics from shadow trace."""
    total = len(trace_entries)
    
    # Trigger rate: percentage of checks that would trigger
    would_trigger = sum(1 for e in trace_entries 
                       if e["action"] in ("normal", "emergency"))
    trigger_rate = would_trigger / total if total > 0 else 0
    
    # Blocker rate: percentage of triggers blocked
    blocked = sum(1 for e in trace_entries if e["action"] == "blocked")
    blocker_rate = blocked / would_trigger if would_trigger > 0 else 0
    
    # Emergency ratio: emergency vs normal triggers
    emergency = sum(1 for e in trace_entries if e["action"] == "emergency")
    emergency_ratio = emergency / would_trigger if would_trigger > 0 else 0
    
    # Ratio distribution
    ratios = [e["ratio"] for e in trace_entries]
    ratio_p50 = sorted(ratios)[len(ratios) // 2] if ratios else 0
    ratio_p95 = sorted(ratios)[int(len(ratios) * 0.95)] if ratios else 0
    
    return {
        "trigger_rate": trigger_rate,
        "blocker_rate": blocker_rate,
        "emergency_ratio": emergency_ratio,
        "ratio_p50": ratio_p50,
        "ratio_p95": ratio_p95
    }
```

---

## Rollback Plan

### Scenario 1: Shadow Mode Causing Issues

If shadow mode causes any system instability:

```bash
# Step 1: Disable shadow mode
export AUTO_COMPACTION_SHADOW_MODE=false

# OR remove config
rm artifacts/context_compression/shadow_config.json

# Step 2: Verify disabled
shadow_watcher --status

# Step 3: Review logs
cat artifacts/context_compression/SHADOW_TRACE.jsonl | tail -20
```

### Scenario 2: Incorrect Metrics

If shadow metrics appear incorrect:

```bash
# Step 1: Validate baseline
cat artifacts/context_compression/AUTO_COMPACTION_BASELINE.json

# Step 2: Run single shadow check
shadow_watcher --run-once --verbose

# Step 3: Compare with manual run
auto-context-compact --dry-run --json
```

### Scenario 3: Trace File Corruption

If SHADOW_TRACE.jsonl becomes corrupted:

```bash
# Step 1: Backup existing trace
cp artifacts/context_compression/SHADOW_TRACE.jsonl \
   artifacts/context_compression/SHADOW_TRACE.jsonl.backup

# Step 2: Start fresh
rm artifacts/context_compression/SHADOW_TRACE.jsonl

# Step 3: Re-run shadow watcher
shadow_watcher --run-once
```

---

## Integration Points

### Heartbeat Integration

Shadow watcher runs during heartbeat cycles (see HEARTBEAT.md for details):

```bash
# In HEARTBEAT.md
# Shadow Mode Check (every 5 minutes when enabled)
if [ "$AUTO_COMPACTION_SHADOW_MODE" = "true" ]; then
    shadow_watcher --run-once --quiet
fi
```

### Manual Invocation

```bash
# Single run
shadow_watcher --run-once

# With verbose output
shadow_watcher --run-once --verbose

# Check current status
shadow_watcher --status

# Generate metrics summary
shadow_watcher --metrics
```

---

## Success Criteria for Shadow Mode

A shadow mode run is considered successful if:

1. ✅ Trace entry logged to SHADOW_TRACE.jsonl
2. ✅ No system errors during execution
3. ✅ Metrics within expected ranges:
   - `duration_ms < 5000`
   - `trigger_rate < 0.20` (20% of checks trigger)
   - `blocker_rate < 0.10` (10% or less blocked)

---

## Comparison: Shadow vs Production

| Aspect | Shadow Mode | Production Mode |
|--------|-------------|-----------------|
| Trigger Detection | ✅ Active | ✅ Active |
| Blocker Checks | ✅ Active | ✅ Active |
| Metrics Logging | ✅ Active | ✅ Active |
| Trace Logging | ✅ Active | ⚠️ Events only |
| Actual Compression | ❌ Skipped | ✅ Executed |
| State Persistence | ❌ Skipped | ✅ Executed |
| Risk Level | None | Normal |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-09 | Initial shadow mode specification |
