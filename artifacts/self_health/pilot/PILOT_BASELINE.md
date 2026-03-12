# PILOT_BASELINE

## Pilot Instance
- **Instance**: moonlight-VMware-Virtual-Platform (current OpenClaw main instance)
- **Selection Date**: 2026-03-08
- **Selection Reason**: Primary development instance with full heartbeat/callback/mailbox workers

## Pre-Integration Baseline

### System State
- OS: Linux 6.17.0-14-generic (x64)
- Node: v22.22.0
- OpenClaw Version: 2026.3.7
- Model: baiduqianfancodingplan/qianfan-code-latest

### Workers Status
- heartbeat: Configured (directPolicy: allow)
- callback-worker: Configured via systemd
- mailbox-worker: Configured via systemd
- gateway: Active on port 18789

### Current Artifacts
- artifacts/self_health/state/: Contains worker status files
- artifacts/self_health/recovery_logs/: 1 recovery record
- artifacts/self_health/capabilities/: 1 capability state
- artifacts/self_health/proposals/: 4 proposals

### Known Issues
- Worker progress signals need verification
- Some capabilities show missing due to no status files
- Recovery summary shows maintenance action only

### Baseline Metrics
- recovery_actions_total: 0
- evidence_actions_total: 0
- maintenance_actions_total: 1
- capability_healthy: 1
- capability_missing: 5
- capability_degraded: 0

### Integration Scope
1. Wire capability checks into heartbeat
2. Enable forgetting guard periodic runs
3. Auto-generate summaries every hour
4. Run gate checks before recovery actions
