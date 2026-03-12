# Telemetry Contract Template

## Purpose
Standard contract for telemetry output that capability checks can consume.

## Required Telemetry Sources

### 1. Heartbeat Telemetry
**File**: `artifacts/self_health/runtime/heartbeat_status.json`

**Schema**:
```json
{
  "last_heartbeat_at": "2026-03-08T18:00:00Z",
  "heartbeat_lag_seconds": 2.5,
  "heartbeat_cycle_ok": true,
  "last_cycle_duration_ms": 150,
  "last_quick_check_at": "2026-03-08T18:00:00Z",
  "last_full_check_at": "2026-03-08T18:00:00Z",
  "heartbeat_status": "ok"
}
```

**Field Definitions**:
- `last_heartbeat_at`: ISO 8601 timestamp of last heartbeat
- `heartbeat_lag_seconds`: Time since last heartbeat
- `heartbeat_cycle_ok`: Whether last cycle completed successfully
- `last_cycle_duration_ms`: Duration of last cycle in milliseconds
- `heartbeat_status`: "ok" | "warning" | "error" | "unknown"

### 2. Worker Telemetry
**File**: `artifacts/self_health/runtime/{worker_name}_status.json`

**Schema**:
```json
{
  "worker_name": "callback-worker",
  "alive": true,
  "last_progress_at": "2026-03-08T18:00:00Z",
  "last_output_at": "2026-03-08T18:00:00Z",
  "pending_count": 3,
  "stuck_suspected": false,
  "last_error_at": null,
  "last_error_type": null,
  "worker_status": "ok"
}
```

**Field Definitions**:
- `worker_name`: Identifier for the worker
- `alive`: Whether worker process is running
- `last_progress_at`: Last time worker made progress
- `pending_count`: Number of pending items
- `stuck_suspected`: Whether worker appears stuck
- `worker_status`: "ok" | "warning" | "error" | "unknown"

### 3. Summary Telemetry
**File**: `artifacts/self_health/runtime/summary_status.json`

**Schema**:
```json
{
  "last_health_summary_at": "2026-03-08T18:00:00Z",
  "last_recovery_summary_at": "2026-03-08T18:00:00Z",
  "last_capability_summary_at": "2026-03-08T18:00:00Z",
  "last_proposal_summary_at": "2026-03-08T18:00:00Z",
  "last_incident_recorded_at": "2026-03-08T18:00:00Z",
  "summary_pipeline_status": "ok"
}
```

## Status Semantics

| Status | Meaning |
|--------|---------|
| ok | Working normally |
| warning | Degraded but functional |
| error | Not working correctly |
| unknown | Cannot determine |

## Adaptation Guide

### If Instance Has Different Structure
1. Create adapter to normalize to this contract
2. Place adapter output in expected file location
3. Document any data transformations

### If Instance Cannot Provide Field
1. Set field to `null`
2. Mark as `telemetry_missing` in capability check
3. Document why field cannot be provided

## Validation
Run `tools/agent-telemetry-normalize --component all --json` to verify contract compliance.
