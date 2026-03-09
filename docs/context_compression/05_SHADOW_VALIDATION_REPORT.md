# Phase 5: Shadow Validation Report

## Overview

This document outlines the shadow validation plan for the auto-compaction system, defining success criteria for Phase 6 production rollout.

---

## Shadow Mode Summary

**What is Shadow Mode?**

Shadow mode runs the complete auto-compaction decision pipeline but skips actual execution. This allows:

1. **Risk-free validation** - Test in production-like conditions
2. **Metrics collection** - Gather real workload data
3. **Threshold tuning** - Validate trigger thresholds
4. **Blocker detection** - Identify common blockers

**Key Principle**: Shadow mode observes and records, never modifies.

---

## Infrastructure Components

### 1. AUTO_COMPACTION_SHADOW_MODE.md

Defines:
- Shadow mode operation
- Enable/disable methods
- Monitoring metrics
- Rollback procedures

### 2. shadow_watcher Tool

Executes:
- Dry-run compaction checks
- Metrics collection
- Trace logging
- Baseline comparison

### 3. AUTO_COMPACTION_BASELINE.json

Contains:
- Expected trigger rate: 15%
- Expected blocker rate: <10%
- Target ratio range: 0.45-0.75

### 4. SHADOW_TRACE.jsonl

Records:
- One entry per shadow check
- Timestamp, ratio, action, blockers
- Used for metrics calculation

---

## Success Criteria for Phase 6

### Mandatory Criteria

| # | Criterion | Target | How to Measure |
|---|-----------|--------|----------------|
| 1 | Shadow mode runs without errors | 100% success | `shadow_watcher --metrics` |
| 2 | Trace entries logged correctly | All entries | Check SHADOW_TRACE.jsonl |
| 3 | Trigger rate within range | 5-30% | Metrics: trigger_rate |
| 4 | Blocker rate acceptable | <20% | Metrics: blocker_rate |
| 5 | Emergency triggers rare | <5% of triggers | Metrics: emergency_ratio |

### Validation Metrics

```bash
# After collecting shadow data, run:
shadow_watcher --metrics --json
```

Expected output structure:
```json
{
  "total_checks": 100,
  "trigger_rate": 0.15,
  "blocker_rate": 0.08,
  "ratio_distribution": {
    "p50": 0.62,
    "p95": 0.78
  }
}
```

### Baseline Comparison

```bash
# Compare with baseline:
shadow_watcher --compare --json
```

Expected:
- `trigger_rate.status`: "ok"
- `blocker_rate.status`: "ok"
- `ratio_p95.status`: "ok"

---

## Validation Procedure

### Step 1: Enable Shadow Mode

```bash
# Option A: Environment variable
export AUTO_COMPACTION_SHADOW_MODE=true

# Option B: Config file
cat > artifacts/context_compression/shadow_config.json << 'CONF'
{
  "enabled": true,
  "log_trace": true,
  "metrics_interval_seconds": 300
}
CONF
```

### Step 2: Verify Shadow Mode Active

```bash
shadow_watcher --status
# Should show: Enabled: true
```

### Step 3: Run Initial Shadow Check

```bash
shadow_watcher --run-once --verbose
```

Expected output:
```
[timestamp] Running shadow check...
  Ratio: 0.XX
  Zone: normal/warning
  Action: none/normal
  Would Compact: true/false
```

### Step 4: Collect Data Over Time

- Minimum: 24 hours of shadow checks
- Recommended: 1 week for workload patterns
- Expected checks: 288+ (every 5 min for 24h)

### Step 5: Analyze Metrics

```bash
shadow_watcher --metrics
shadow_watcher --compare
```

### Step 6: Validate Against Criteria

Check each criterion from the table above.

---

## Metrics to Track

### Primary Metrics

| Metric | Definition | Collection Method |
|--------|------------|-------------------|
| `trigger_count` | Times compaction would trigger | Count entries with action=normal/emergency |
| `would_compact_count` | Times actual compression would run | Count would_compact=true |
| `blockers_hit` | Blockers encountered | Sum of blocker counts |
| `ratio_distribution` | Observed context ratios | Statistics from ratio field |

### Calculated Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| `trigger_rate` | trigger_count / total_checks | 0.05 - 0.30 |
| `blocker_rate` | blocked_count / trigger_count | < 0.20 |
| `emergency_ratio` | emergency_count / trigger_count | < 0.05 |

### Trend Metrics

| Metric | Purpose | Alert Threshold |
|--------|---------|-----------------|
| `ratio_trend` | Context growth pattern | Increasing > 0.01/hour |
| `trigger_frequency` | Compaction frequency | > 1/hour |
| `error_rate` | System stability | > 0.01 |

---

## Phase 6 Readiness Checklist

Before proceeding to Phase 6 (Production Rollout):

- [ ] Shadow mode enabled and stable
- [ ] Minimum 24 hours of shadow data collected
- [ ] All mandatory criteria met
- [ ] No critical errors in shadow runs
- [ ] Baseline comparison shows "ok" status
- [ ] Ratio P95 below emergency threshold (0.85)
- [ ] Blocker rate within acceptable range (<20%)

---

## Rollback Scenarios

### If Shadow Mode Causes Issues

1. Disable immediately:
   ```bash
   export AUTO_COMPACTION_SHADOW_MODE=false
   # or
   rm artifacts/context_compression/shadow_config.json
   ```

2. Verify disabled:
   ```bash
   shadow_watcher --status
   ```

3. Review logs for root cause

### If Metrics Indicate Problems

1. Document issues in validation report
2. Adjust thresholds if needed
3. Re-run shadow validation
4. Do NOT proceed to Phase 6 until resolved

---

## Next Steps After Validation

### If All Criteria Met

1. Generate validation report with metrics
2. Update AUTO_COMPACTION_BASELINE.json with actual observed values
3. Proceed to Phase 6: Production Rollout

### If Criteria Not Met

1. Analyze root cause
2. Adjust configuration:
   - Thresholds in AUTO_COMPACTION_POLICY.md
   - Blocker rules in COMPACTION_BLOCKERS.md
3. Re-run shadow validation
4. Iterate until criteria met

---

## Appendix: Shadow Trace Schema

Each entry in SHADOW_TRACE.jsonl:

```json
{
  "timestamp": "2026-03-09T14:45:00Z",
  "version": "v1.0",
  "ratio": 0.82,
  "zone": "warning",
  "trend": "increasing",
  "action": "normal",
  "reason": "ratio_threshold_exceeded",
  "blockers": [],
  "target_ratio": 0.60,
  "duration_ms": 150,
  "would_compact": true,
  "dry_run": true
}
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-09 | Initial shadow validation plan |
