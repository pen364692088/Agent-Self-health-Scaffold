# FAILURE_TAXONOMY.md

## Initial fault codes
- `TASK_STALLED`
- `PROCESS_RESTARTED`
- `STEP_POINTER_LOST`
- `TRANSCRIPT_CORRUPTED`
- `CHILD_JOB_MISSING`
- `DUPLICATE_EXECUTION_RISK`
- `REPAIR_FAILED`
- `ORDER_CONFLICT_DETECTED`
- `OUT_OF_BAND_RESTART_REQUIRED`
- `RUN_HEARTBEAT_EXPIRED`

## Mapping guidelines
- transcript/order issues must not be treated as task truth failure by default
- process restart should route to recovery scan, not direct failure
- repeated repair failure should escalate to blocked/abandoned state
