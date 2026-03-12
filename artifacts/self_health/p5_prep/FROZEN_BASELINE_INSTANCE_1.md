# FROZEN BASELINE - Instance 1

## Instance
- **Name**: moonlight-VMware-Virtual-Platform
- **Status**: INSTANCE_PROVEN
- **Frozen Date**: 2026-03-08

## Achieved State

### P1 Complete
- Unified health state output
- Structured incident recording
- Basic health checks

### P2 Complete
- Verified recovery with before/after snapshots
- Deterministic verdict engine
- Clean effectiveness metrics
- Action governance (whitelist, cooldown, max retry)

### P3 Complete
- 8 capabilities registered
- Forgetting guard operational
- Proposal engine with dedup
- Level B proposal-only enforced

### P4 Complete
- Scheduler (quick/full/gate modes)
- Gate A/B/C wiring
- Fault injection tests
- Instance integration guide

### P4.5 Complete
- Pilot instance integration
- Short soak validation
- Verdict: STABLE_WITH_CAVEATS → INSTANCE_PROVEN

### P4.6 Complete
- 4 telemetry sources integrated
- Capability truth aligned
- Gate B improved from PARTIAL to PASS
- 2 user_promised_features registered

## Final Metrics

### Capability Summary
- Total: 8
- Healthy: 5
- Missing: 0
- Telemetry Missing: 2
- Unknown: 1

### Gate Status
- Gate A: PASS
- Gate B: PASS
- Gate C: PASS

### User-Promised Features
1. CAP-USER_PROMISED_FEATURE_TELEGRAM_NOTIFICATION - healthy
2. CAP-USER_PROMISED_FEATURE_SUBAGENT_ORCHESTRATION - healthy

### Test Coverage
- 40 tests passing

### Telemetry Sources
1. heartbeat_status.json
2. callback_worker_status.json
3. mailbox_worker_status.json
4. summary_status.json

## What This Baseline Proves

- Scaffold works on one real OpenClaw instance
- Telemetry integration is achievable
- Capability contract is enforceable
- Gate validation is meaningful

## What This Baseline Does NOT Prove

- Does NOT prove transferability
- Does NOT prove low-friction migration
- Does NOT prove scaffold works on different instance types

## Preservation

This baseline should be preserved as reference for P5 validation. Any changes to this instance should be tracked.
