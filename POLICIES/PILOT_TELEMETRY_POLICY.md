# PILOT_TELEMETRY_POLICY

## Purpose
Define telemetry output contracts for instance-level capability verification.

## Telemetry Sources

### Heartbeat Telemetry
- File: `artifacts/self_health/runtime/heartbeat_status.json`
- Required fields:
  - `last_heartbeat_at`: ISO timestamp
  - `heartbeat_lag_seconds`: number
  - `heartbeat_cycle_ok`: boolean
  - `last_cycle_duration_ms`: number
  - `last_quick_check_at`: ISO timestamp
  - `last_full_check_at`: ISO timestamp
  - `heartbeat_status`: "ok"|"warning"|"error"|"unknown"

### Callback Worker Telemetry
- File: `artifacts/self_health/runtime/callback_worker_status.json`
- Required fields:
  - `worker_name`: string
  - `alive`: boolean
  - `last_progress_at`: ISO timestamp
  - `last_output_at`: ISO timestamp
  - `pending_count`: number
  - `stuck_suspected`: boolean
  - `last_error_at`: ISO timestamp|null
  - `last_error_type`: string|null
  - `worker_status`: "ok"|"warning"|"error"|"unknown"

### Mailbox Worker Telemetry
- File: `artifacts/self_health/runtime/mailbox_worker_status.json`
- Required fields:
  - `worker_name`: string
  - `alive`: boolean
  - `last_poll_at`: ISO timestamp
  - `last_progress_at`: ISO timestamp
  - `backlog_count`: number
  - `stuck_suspected`: boolean
  - `mailbox_status`: "ok"|"warning"|"error"|"unknown"

### Summary Telemetry
- File: `artifacts/self_health/runtime/summary_status.json`
- Required fields:
  - `last_health_summary_at`: ISO timestamp
  - `last_recovery_summary_at`: ISO timestamp
  - `last_capability_summary_at`: ISO timestamp
  - `last_proposal_summary_at`: ISO timestamp
  - `last_incident_recorded_at`: ISO timestamp|null
  - `summary_pipeline_status`: "ok"|"warning"|"error"

## Status Semantics
- `ok`: Working normally
- `warning`: Degraded but functional
- `error`: Not working correctly
- `unknown`: Cannot determine

## Telemetry Missing vs Capability Missing
- `telemetry_missing`: No telemetry output available
- `capability_missing`: Telemetry shows capability not working

These must be distinguished in capability checks and Gate B.
