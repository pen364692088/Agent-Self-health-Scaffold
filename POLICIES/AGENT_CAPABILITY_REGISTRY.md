# Agent Capability Registry

**Generated**: 2026-03-17T21:28:23.450352+00:00
**Source**: artifacts/self_health/capabilities/
**Schema**: schemas/AGENT_CAPABILITY.schema.json

## Purpose

This registry is the authoritative index of all tracked agent capabilities.
It is auto-generated from individual capability files in `artifacts/self_health/capabilities/`.

## Capabilities (12 total)

| ID | Name | Component | Category | Status | Severity |
|----|------|-----------|----------|--------|----------|
| CAP-CALLBACK_DELIVERY | Callback Delivery | callback-worker | delivery_capability | telemetry_missing | high |
| CAP-COMPACTION_EFFECTIVENESS | Compaction Effectiveness | compaction | core_feature | healthy | high |
| CAP-COMPACTION_EXECUTION | Native Compaction Execution | compaction | core_feature | healthy | critical |
| CAP-CONTEXT_OVERFLOW_HANDLING | Context Overflow Handling | context_manager | safety | degraded | critical |
| CAP-HEALTH_SUMMARY_GENERATION | Health Summary Generation | agent-health-summary | workflow_capability | telemetry_missing | medium |
| CAP-HEARTBEAT_CYCLE_EXECUTION | Heartbeat Cycle Execution | heartbeat | liveness_capability | telemetry_missing | critical |
| CAP-INCIDENT_RECORDING | Incident Recording | agent-incident-report | safety_capability | telemetry_missing | high |
| CAP-LONGRUNKIT_HEALTH | LongRunKit Job Processing | longrunkit | core_feature | healthy | high |
| CAP-MAILBOX_CONSUMPTION | Mailbox Consumption | mailbox-worker | processing_capability | telemetry_missing | high |
| CAP-RECOVERY_SUMMARY_GENERATION | Recovery Summary Generation | agent-recovery-summary | workflow_capability | telemetry_missing | medium |
| CAP-USER_PROMISED_FEATURE_SUBAGENT_ORCHESTRATION | Subagent Orchestration | subtask-orchestrate | user_promised_feature | telemetry_missing | medium |
| CAP-USER_PROMISED_FEATURE_TELEGRAM_NOTIFICATION | Telegram Notification Delivery | telegram-channel | user_promised_feature | telemetry_missing | high |


## Status Definitions

| Status | Meaning |
|--------|---------|
| healthy | Capability is functioning normally |
| degraded | Capability is partially working or under stress |
| missing | Capability is expected but not found |
| telemetry_missing | No telemetry data available to verify |
| unknown | Status could not be determined |

## Maintenance

### How to Update

1. Add/modify individual capability files in `artifacts/self_health/capabilities/`
2. Run `tools/gate-self-health-check --write` to regenerate this registry

### How to Verify

```bash
./tools/gate-self-health-check --json
```

### Anti-Regression

Gate A checks for this file's existence. If deleted, the gate will FAIL with `capability_registry_missing`.

## Related

- Schema: `schemas/AGENT_CAPABILITY.schema.json`
- Gate Check: `tools/gate-self-health-check`
- Capabilities Directory: `artifacts/self_health/capabilities/`
