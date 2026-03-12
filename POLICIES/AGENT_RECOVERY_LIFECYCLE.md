# AGENT_RECOVERY_LIFECYCLE

## Purpose
Define a deterministic lifecycle for verified recovery attempts.

## State Flow
`detected -> snapshot_before -> action -> snapshot_after -> verdict -> escalate/archive`

## Required Fields
Each recovery attempt must record at least:
- `recovery_id`
- `incident_id` (nullable)
- `component`
- `action`
- `status`
- `started_at`
- `snapshot_before_path`
- `snapshot_after_path`
- `verdict`
- `rollback_needed`
- `escalation_state`
- `attempt_number`
- `cooldown_applied`

## Verdicts
Allowed verdicts:
- `recovered`
- `unchanged`
- `degraded`
- `insufficient_evidence`

## Rules
1. No Level A recovery may claim success without a snapshot-based verdict.
2. Missing evidence must yield `insufficient_evidence`, not success.
3. `unchanged` and `degraded` must be escalation-eligible outcomes.
4. Audit trail must be sufficient to reconstruct one full recovery attempt end-to-end.
