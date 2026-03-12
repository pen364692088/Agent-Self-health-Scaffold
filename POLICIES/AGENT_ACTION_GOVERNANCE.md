# AGENT_ACTION_GOVERNANCE

## Purpose
Constrain verified recovery actions so the agent does not turn “recoverable” into “unsafe automation”.

## Required Guards
Every action must pass:
- whitelist
- component allowlist
- precondition check
- cooldown check
- retry ceiling check
- postcondition verification window

## Execution Model
`probe -> candidate_action -> guarded_execution -> verification_window -> verdict`

## Action Contracts
Each action must define:
- precondition
- execution
- postcondition
- verification_window_seconds
- failure_handling

## Notes
- `restart_worker` should precede `restart_service` in rollout.
- `rerun_health_check` is an evidence-refresh action, not a strong repair.
- `clear_stale_lock` must protect against deleting active locks.


## Restart Service Open Gate
Open `restart_service` only when all conditions hold:
- systemd probe is stable
- service/component whitelist is complete
- precondition is machine-checkable
- post-check includes both service-layer and function-layer evidence
- cooldown / retry / escalation coverage exists
- at least one worker-class recovery action has already demonstrated credible recovery

## Clear Stale Lock Guardrails
`clear_stale_lock` may execute only when all of the following hold:
- owner is not alive
- lock age exceeds stale threshold
- lease/heartbeat is not fresh
- lock is not currently active
- expected holder identity matches actual holder identity when available

Removing the lock alone does not equal recovery. If downstream progress does not resume, verdict must remain `unchanged` or worse.
