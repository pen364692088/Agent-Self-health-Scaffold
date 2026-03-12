# Soak Validation Template

## Purpose
Standardized soak validation for new instance integration.

## Soak Configuration

### Quick Soak (Minimum)
- Duration: 1-2 hours
- Quick runs: 10+
- Full runs: 2+
- Gate runs: 2+

### Extended Soak (Recommended)
- Duration: 24 hours
- Quick runs: 100+
- Full runs: 24+
- Gate runs: 24+

## Soak Checklist

### Pre-Soak
- [ ] Scheduler modes tested individually
- [ ] Telemetry sources verified
- [ ] Capability check working
- [ ] Gate A/B/C tested
- [ ] Lock mechanisms tested
- [ ] Execution budgets validated

### During Soak
- [ ] Monitor scheduler runs
- [ ] Monitor capability states
- [ ] Monitor incident generation
- [ ] Monitor proposal generation
- [ ] Monitor main loop timing
- [ ] Monitor for storms

### Post-Soak
- [ ] Collect metrics
- [ ] Analyze results
- [ ] Identify issues
- [ ] Document findings

## Metrics to Collect

### Scheduler Metrics
```json
{
  "scheduler_runs_total": 0,
  "quick_runs": 0,
  "full_runs": 0,
  "gate_runs": 0,
  "skipped_runs": 0,
  "lock_contention_count": 0,
  "budget_hit_count": 0
}
```

### Capability Metrics
```json
{
  "capability_healthy": 0,
  "capability_degraded": 0,
  "capability_missing": 0,
  "capability_telemetry_missing": 0,
  "capability_unknown": 0
}
```

### Storm Metrics
```json
{
  "incident_total": 0,
  "incident_deduped": 0,
  "proposal_total": 0,
  "proposal_deduped": 0,
  "proposal_cooldown_blocked": 0,
  "repeated_same_alert_count": 0
}
```

### Impact Metrics
```json
{
  "main_loop_delay_avg_ms": 0,
  "main_loop_delay_max_ms": 0,
  "worker_lag_change_ms": 0
}
```

## Success Criteria

### Minimum (for STABLE_WITH_CAVEATS)
- No incident storm (>10 same-type in 1h)
- No proposal storm (>5 same-type in 6h)
- Main loop delay < 500ms average
- At least 1 telemetry source working
- At least 1 scheduler mode working

### Recommended (for INSTANCE_PROVEN)
- All of the above, plus:
- At least 50% capabilities healthy
- Gate A/B/C all PASS
- At least 1 user_promised_feature healthy
- Clear understanding of any missing capabilities

## Soak Report Template

```markdown
# <INSTANCE_NAME> Soak Report

## Soak Window
- Start: YYYY-MM-DD HH:MM UTC
- End: YYYY-MM-DD HH:MM UTC
- Duration: X hours

## Configuration
- Quick runs: X
- Full runs: X
- Gate runs: X

## Results

### Scheduler
- Total runs: X
- Skipped: X
- Lock contention: X
- Budget hits: X

### Capability
- Healthy: X
- Degraded: X
- Missing: X
- Telemetry missing: X

### Storms
- Incident storm: NO
- Proposal storm: NO
- Max same-type incidents/hour: X
- Max same-type proposals/6hours: X

### Impact
- Main loop avg delay: X ms
- Main loop max delay: X ms
- Worker lag change: X ms

## Issues Found
- [List issues]

## Recommendations
- [Next steps]
```
