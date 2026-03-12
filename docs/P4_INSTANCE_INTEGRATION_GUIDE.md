# P4 Instance Integration Guide

## Purpose
Guide for integrating Agent Self-Health Scaffold into a real OpenClaw instance.

## Prerequisites
- OpenClaw instance running
- Heartbeat configured
- Workers (callback-worker, mailbox-worker) operational
- Artifacts directory structure established

## Integration Steps

### Step 1: Copy Core Files
Copy these directories to your OpenClaw instance:
- `tools/agent-*` (all self-health tools)
- `POLICIES/AGENT_*.md` (all self-health policies)
- `schemas/AGENT_*.schema.json` (all schemas)
- `config/action_policy.json`

### Step 2: Initialize Artifacts Structure
```bash
mkdir -p artifacts/self_health/{state,recovery_logs,incidents,proposals,capabilities,capability_incidents,gate_reports}
```

### Step 3: Register Instance Capabilities
Edit `POLICIES/AGENT_CAPABILITY_REGISTRY.md`:
- Review each CAP-* entry
- Customize for your instance
- Add user_promised_feature entries for your specific features

### Step 4: Wire into Heartbeat
Add to your heartbeat configuration:
```bash
# Quick check every cycle
./tools/agent-self-health-scheduler --mode quick

# Full check every 6 cycles
./tools/agent-self-health-scheduler --mode full
```

### Step 5: Wire Workers
Ensure workers expose status files:
- `artifacts/self_health/state/heartbeat.status.json`
- `artifacts/self_health/state/callback-worker.status.json`
- `artifacts/self_health/state/mailbox-worker.status.json`

### Step 6: Verify Integration
```bash
# Run capability check
./tools/agent-capability-check --all --json

# Run gate check
./tools/gate-self-health-check --json

# Check summaries
cat artifacts/self_health/CAPABILITY_SUMMARY.md
cat artifacts/self_health/VERIFIED_RECOVERY_SUMMARY.md
```

## Key Integration Points

### Heartbeat Integration
- Quick capability check: every heartbeat cycle
- Forgetting guard: every 6 cycles
- Summary refresh: every hour

### Worker Integration
Workers must output:
- `process_alive`: boolean
- `last_progress_time`: timestamp
- `backlog`: integer
- `stuck`: boolean
- `failure_indicators`: array

### Gate Integration
Gate A/B/C should call:
- `tools/gate-self-health-check --write`
- Include in preflight/doctor checks

## Customization

### Instance-Specific Capabilities
Add to `POLICIES/AGENT_CAPABILITY_REGISTRY.md`:
```markdown
### CAP-USER_PROMISED_FEATURE_<YOUR_FEATURE>
- **Name**: Your Feature Name
- **Component**: your-component
- **Category**: user_promised_feature
- **Expected Behavior**: Clear description
- **Verification Mode**: probe_check/artifact_output_check
- **Verification Frequency**: 1h/24h
- **Severity if Missing**: high/critical
```

### Instance-Specific Actions
Edit `config/action_policy.json`:
- Add components to whitelist
- Adjust cooldown/max_retry
- Customize verification windows

## Monitoring

### Health Indicators
- `CAPABILITY_SUMMARY.md`: Overall capability health
- `VERIFIED_RECOVERY_SUMMARY.md`: Recovery effectiveness
- `PROPOSAL_SUMMARY.md`: Proposal flow health
- `gate_reports/`: Gate validation status

### Alert Conditions
- Capability status: missing/degraded
- Gate status: FAIL
- Recovery rate: < 50%
- Proposal backlog: growing

## Troubleshooting

### "No status files found"
Workers are not outputting status. Check worker configuration.

### "Gate A fails"
- Check capability registry exists
- Check schemas are valid
- Check proposal_only is not violated

### "Capability always missing"
- Verify verification mode matches component type
- Check artifact paths are correct
- Verify component is actually running

## Safety Notes

1. Level B/C actions remain proposal-only
2. Gate must pass before any recovery action
3. All proposals require human approval
4. No automatic modification of core governance files
