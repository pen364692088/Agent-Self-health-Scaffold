# Prompt Pilot Operations Runbook

## Quick Reference

### Status Check
```bash
tools/prompt-pilot-control --status
```

### Enable Pilot
```bash
# Pre-flight check first
tools/prompt-pilot-preflight

# Enable in shadow mode (recommended first step)
tools/prompt-pilot-control --enable --mode shadow

# After observation period, switch to pilot mode
tools/prompt-pilot-control --set-mode pilot
```

### Disable Pilot
```bash
# Immediate disable
tools/prompt-pilot-control --disable

# With reason
tools/prompt-pilot-control --disable --reason "conflict rate exceeded"
```

### Reset Metrics
```bash
tools/prompt-pilot-control --reset-metrics
```

---

## Daily Operations

### Morning Check (Daily)
```bash
# 1. Check status
tools/prompt-pilot-control --status

# 2. Check for violations
# (shown in status output)

# 3. Review metrics
cat artifacts/prompt_pilot/metrics.jsonl | tail -20 | jq .
```

### Weekly Review
```bash
# 1. Aggregate metrics
cat artifacts/prompt_pilot/metrics.jsonl | jq -s '
{
  total: length,
  successful: map(select(.success)) | length,
  fallbacks: map(select(.fallback)) | length,
  avg_match: (map(.match_rate) | add / length)
}
'

# 2. Check for patterns
cat artifacts/prompt_pilot/metrics.jsonl | jq -r .error | sort | uniq -c

# 3. Review conflict patterns
cat artifacts/prompt_pilot/metrics.jsonl | jq 'select(.conflict_count > 0)'
```

---

## Incident Response

### Conflict Rate Spike

**Symptoms**: Conflict rate > 5%

**Response**:
1. Check recent changes to state files
2. Review conflict details
3. If persistent, disable pilot:
   ```bash
   tools/prompt-pilot-control --disable --reason "conflict rate spike"
   ```
4. Investigate root cause

### Match Rate Drop

**Symptoms**: Match rate < 80%

**Response**:
1. Check if state files are being updated correctly
2. Review shadow vs main comparison
3. If persistent, disable pilot
4. Check for data quality issues

### Error Spike

**Symptoms**: Multiple errors in short time

**Response**:
1. Check error logs:
   ```bash
   cat artifacts/prompt_pilot/metrics.jsonl | jq 'select(.error != null)'
   ```
2. If systematic error, disable pilot
3. Fix error source before re-enabling

### Fallback Loop

**Symptoms**: Frequent fallbacks to main chain

**Response**:
1. Check fallback reasons
2. If fallback rate > 5%, investigate
3. Consider staying in shadow mode longer

---

## Rollback Procedure

### Manual Rollback
```bash
# 1. Disable pilot
tools/prompt-pilot-control --disable --reason "manual rollback"

# 2. Verify main chain is working
# (Run a test task)

# 3. Document reason in session notes
echo "$(date): Rollback - <reason>" >> artifacts/prompt_pilot/rollback_log.txt
```

### Auto Rollback
- Triggered automatically when stop condition violated
- Logs to metrics.jsonl with `error` field
- Pilot disabled in config

---

## Monitoring Dashboard

### Key Metrics to Watch

| Metric | Healthy Range | Warning | Critical |
|--------|---------------|---------|----------|
| Match Rate | 85-100% | 80-85% | < 80% |
| Conflict Rate | 0-3% | 3-5% | > 5% |
| Missing Rate | 0-2% | 2-5% | > 5% |
| Fallback Rate | 0-5% | 5-10% | > 10% |
| Error Rate | 0% | 0-1% | > 1% |

### Sample Dashboard Query
```bash
# Last hour summary
cat artifacts/prompt_pilot/metrics.jsonl | \
  jq -s 'map(select(.timestamp > "2026-03-14T09:00")) |
  {
    calls: length,
    success_rate: (map(select(.success)) | length / length * 100),
    avg_match: (map(.match_rate) | add / length * 100),
    conflicts: map(.conflict_count) | add,
    fallbacks: map(select(.fallback)) | length
  }'
```

---

## Escalation Path

1. **Level 1**: Operator can disable/enable pilot
2. **Level 2**: Investigate root cause (check state files, shadow systems)
3. **Level 3**: Engage development team if systematic issue
4. **Level 4**: Consider reverting to Phase 2.8 (pre-pilot)

---

## Post-Pilot Checklist

### Before Expanding Pilot

- [ ] Match rate ≥ 85% for 7 days
- [ ] Conflict rate ≤ 3% for 7 days
- [ ] Fallback rate ≤ 5% for 7 days
- [ ] Zero unhandled errors
- [ ] All stop conditions passing
- [ ] Operator confidence high

### Before Ending Pilot

- [ ] Document final metrics
- [ ] Document lessons learned
- [ ] Make post-pilot decision
- [ ] Update design documents
- [ ] Archive pilot data

---

## Configuration Reference

### config/prompt_pilot.json

| Key | Type | Description |
|-----|------|-------------|
| pilot_enabled | bool | Master switch |
| pilot_mode | string | "shadow" or "pilot" |
| allowed_events | array | Task types allowed |
| blocked_events | array | Task types blocked |
| authority_chain | object | Which chain is authority |
| fallback_on_error | bool | Auto-fallback on error |
| stop_conditions | object | Thresholds for auto-stop |
| rollback_trigger | object | What triggers rollback |

### Stop Conditions

| Condition | Default | Description |
|-----------|---------|-------------|
| max_conflict_rate | 0.05 | Max 5% conflicts |
| max_missing_rate | 0.05 | Max 5% missing fields |
| min_match_rate | 0.80 | Min 80% match |
| max_token_overhead | 0.30 | Max 30% token increase |

---

## Support

- **Logs**: `artifacts/prompt_pilot/metrics.jsonl`
- **Config**: `config/prompt_pilot.json`
- **Design**: `PHASE_2_9_DESIGN.md`
- **Tools**: `tools/prompt-pilot-*`
