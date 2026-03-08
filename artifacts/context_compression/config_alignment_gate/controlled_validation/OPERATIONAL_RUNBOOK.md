# Context Compression - Complete Operational Runbook

## Operations Manual

### Daily Operations

#### Morning Checklist (9:00 AM)

1. **Check Safety Counters**
```bash
cat ~/.openclaw/workspace/artifacts/context_compression/light_enforced/light_enforced_counters.json | jq '.enforced_counters | {real_reply_corruption_count, active_session_pollution_count}'
```

Expected output:
```json
{
  "real_reply_corruption_count": 0,
  "active_session_pollution_count": 0
}
```

If non-zero: **IMMEDIATE INVESTIGATION REQUIRED**

2. **Review Overnight Logs**
```bash
grep "compression" ~/.openclaw/logs/overnight.log | tail -50
```

Look for:
- Error patterns
- Rollback events
- Unusual behavior

3. **Verify Evidence Storage**
```bash
df -h ~/.openclaw/workspace/artifacts/context_compression/
```

Ensure:
- Sufficient disk space
- No storage errors

4. **Check Alert Queue**
```bash
cat ~/.openclaw/workspace/alerts/queue.json | jq '.pending'
```

Process any pending alerts.

#### Midday Check (12:00 PM)

1. **Monitor Active Sessions**
```bash
cat ~/.openclaw/workspace/state/active_state.json | jq '.'
```

2. **Check Compression Rate**
```bash
tail -100 ~/.openclaw/workspace/artifacts/compression_events/events.jsonl | jq -s 'length'
```

3. **Review Performance**
```bash
tail -100 ~/.openclaw/workspace/artifacts/compression_events/events.jsonl | jq -s '[.[].duration_ms] | add / length'
```

Expected: < 300ms average

#### Evening Checklist (5:00 PM)

1. **Review Daily Metrics**
```bash
# Compression count
cat light_enforced_counters.json | jq '.enforced_counters.enforced_trigger_count'

# Success rate
# (total - rollbacks) / total
cat light_enforced_counters.json | jq '.enforced_counters'
```

2. **Check Evidence Completeness**
```bash
find artifacts/context_compression -name "counter_after.json" -mtime -1 | wc -l
```

Should match compression count.

3. **Verify System Health**
```bash
# All tools responding
context-budget-check --health
context-compress --health
```

### Weekly Operations

#### Monday: Trend Analysis

1. **Compression Trend**
```bash
# Last 7 days
cat events.jsonl | jq 'select(.timestamp >= "2026-03-01")' | jq -s 'length'
```

2. **Error Rate Trend**
```bash
# Calculate daily error rate
for day in Mon Tue Wed Thu Fri Sat Sun; do
  echo "$day: $(grep $day errors.log | wc -l) errors"
done
```

3. **Performance Trend**
```bash
# Average duration per day
for day in Mon Tue Wed Thu Fri Sat Sun; do
  avg=$(grep $day events.jsonl | jq '.duration_ms' | awk '{sum+=$1} END {print sum/NR}')
  echo "$day: ${avg}ms average"
done
```

#### Friday: Maintenance

1. **Clean Old Evidence**
```bash
# Remove evidence older than 30 days
find artifacts/context_compression -name "*.json" -mtime +30 -delete
```

2. **Archive Old Events**
```bash
# Archive events older than 90 days
find artifacts/compression_events -name "events.jsonl" -mtime +90 -exec gzip {} \;
```

3. **Update Documentation**
- Review runbook accuracy
- Update procedures as needed
- Note any changes

### Monthly Operations

#### First Week: Full Audit

1. **Configuration Audit**
```bash
# Verify configuration
cat runtime_compression_policy.json | jq '.'
```

Check:
- Thresholds correct
- Context window matches model
- Safety settings appropriate

2. **Evidence Audit**
```bash
# Verify evidence packages
for dir in artifacts/context_compression/*/; do
  echo "Checking $dir"
  test -f "$dir/counter_before.json" && echo "  counter_before: OK"
  test -f "$dir/counter_after.json" && echo "  counter_after: OK"
  test -f "$dir/budget_before.json" && echo "  budget_before: OK"
  test -f "$dir/budget_after.json" && echo "  budget_after: OK"
  test -f "$dir/guardrail_event.json" && echo "  guardrail_event: OK"
  test -f "$dir/capsule_metadata.json" && echo "  capsule_metadata: OK"
done
```

3. **Security Audit**
```bash
# Check kill switch
test -f KILL_SWITCH.md && echo "Kill switch file exists" || echo "Kill switch file not found"

# Check safety counters
cat light_enforced_counters.json | jq '.enforced_counters | to_entries | .[] | select(.value > 0)'
```

Should return nothing.

#### Last Week: Reporting

1. **Monthly Report Generation**
```bash
# Generate report
echo "# Monthly Compression Report"
echo "Generated: $(date)"
echo ""
echo "## Summary"
echo "- Total compressions: $(cat events.jsonl | jq -s 'length')"
echo "- Success rate: $(calculate_success_rate)"
echo "- Average latency: $(calculate_avg_latency)ms"
echo "- Safety violations: $(cat counters.json | jq '.real_reply_corruption_count')"
```

2. **Capacity Planning**
- Estimate growth rate
- Project resource needs
- Plan upgrades if needed

### Troubleshooting Procedures

#### Issue: Compression Not Triggering

Symptoms:
- Ratio exceeds 0.85
- No compression event
- Context growing unbounded

Diagnosis:
```bash
# Check configuration
cat runtime_compression_policy.json | jq '.thresholds'

# Check kill switch
test -f KILL_SWITCH.md && cat KILL_SWITCH.md || echo "Kill switch not active"

# Check scope filter
cat LIGHT_ENFORCED_MANIFEST.json | jq '.scope'

# Check logs
grep "compression" hooks.log | tail -20
```

Resolution:
1. Verify configuration correct
2. Deactivate kill switch if active
3. Check session is in allowed scope
4. Restart hook if needed

#### Issue: Compression Failing

Symptoms:
- High rollback count
- Error events in logs
- Context not reducing

Diagnosis:
```bash
# Check rollback events
cat rollback_events.jsonl | tail -20

# Check error logs
grep ERROR compression.log | tail -20

# Test tools manually
context-budget-check --test
context-compress --test
```

Resolution:
1. Identify error type
2. Fix root cause
3. Test manually
4. Resume operations

#### Issue: Evidence Missing

Symptoms:
- Incomplete evidence packages
- Validation failures
- Audit gaps

Diagnosis:
```bash
# Check evidence directory
ls -la artifacts/context_compression/

# Check file permissions
stat artifacts/context_compression/

# Check disk space
df -h artifacts/
```

Resolution:
1. Fix permissions if needed
2. Free disk space if needed
3. Regenerate evidence if possible
4. Document gap if not recoverable

### Emergency Procedures

#### Kill Switch Activation

When to activate:
- Safety counter > 0
- Suspected data corruption
- System behaving incorrectly
- Manual intervention required

How to activate:
```bash
cat > KILL_SWITCH.md << 'EOF'
KILL_SWITCH_TRIGGERED: true
Reason: [Your reason here]
Timestamp: $(date -Iseconds)
ActivatedBy: [Your name]
EOF
```

How to deactivate:
```bash
rm KILL_SWITCH.md
```

#### Rollback Procedure

When to rollback:
- Compression caused data loss
- State corruption detected
- User-reported issues

How to rollback:
```bash
# Find backup
ls -lt state/*.backup | head -1

# Restore backup
cp state/active_state.json.backup state/active_state.json

# Verify restoration
cat state/active_state.json | jq '.'
```

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T04:21:00-06:00
