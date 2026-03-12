# PILOT_ROLLOUT_RECOMMENDATION

## Recommendation: PROCEED_WITH_HARDENING

## Context
Based on P4.5 pilot integration, the scaffold is functional and stable, but requires instance-specific hardening before wider rollout.

## Required Actions Before Wider Rollout

### 1. Worker Status Integration
**Priority: Critical**
- Ensure callback-worker outputs status to `artifacts/self_health/state/callback-worker.status.json`
- Ensure mailbox-worker outputs status to `artifacts/self_health/state/mailbox-worker.status.json`
- Ensure heartbeat outputs status to `artifacts/self_health/state/heartbeat.status.json`

Required fields:
```json
{
  "status": "ok|warning|error|failed",
  "metrics": {
    "process_alive": true,
    "last_progress_time": "2026-03-08T18:00:00Z",
    "backlog": 0,
    "stuck": false
  },
  "failure_indicators": []
}
```

### 2. User-Promised Feature Registration
**Priority: High**
- Register instance-specific user_promised_feature capabilities
- Define verification methods
- Set degradation rules
- Examples:
  - Telegram notification delivery
  - Subagent orchestration
  - Memory persistence

### 3. Scheduler Integration
**Priority: High**
- Wire `agent-self-health-scheduler --mode quick` into heartbeat cycle
- Wire `agent-self-health-scheduler --mode full` into hourly schedule
- Wire `agent-self-health-scheduler --mode gate` into preflight checks

### 4. Threshold Tuning
**Priority: Medium**
- Adjust capability check frequencies based on instance rhythm
- Tune forgetting guard thresholds
- Set appropriate incident/proposal cooldown values

### 5. Artifacts Rotation
**Priority: Medium**
- Implement log rotation for:
  - scheduler_runs.jsonl
  - soak_metrics.jsonl
  - health_audit.jsonl
- Prevent artifacts explosion

## Rollout Phases

### Phase 1: Single Instance Hardening (Current)
- Complete worker status integration
- Register user_promised_features
- Run full 24h soak

### Phase 2: Second Instance Pilot
- Select second OpenClaw instance
- Apply lessons from first pilot
- Verify portability

### Phase 3: Gradual Expansion
- Document integration patterns
- Create instance onboarding checklist
- Enable opt-in for interested instances

## Non-Recommendations
- DO NOT enable Level B auto-execution
- DO NOT open restart_service
- DO NOT skip worker status integration
- DO NOT ignore Gate B PARTIAL status

## Success Metrics for Phase 2
- All capabilities healthy or explained
- Gate B: PASS
- 24h soak with no storms
- Main loop impact < 100ms

## Timeline Estimate
- Worker integration: 2-4 hours
- Full soak observation: 24 hours
- Second instance pilot: 1-2 days

## Go/No-Go Decision
**GO** - Proceed with hardening after worker status integration.
