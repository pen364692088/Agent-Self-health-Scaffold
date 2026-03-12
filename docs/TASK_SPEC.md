# TASK_SPEC.md

## Mission
Upgrade Agent-Self-health-Scaffold from a health-check scaffold into a constrained self-healing execution kernel.

## Primary user outcome
After restart, crash, transcript corruption, or step failure, the system should keep moving the task toward completion without requiring the user to say "continue".

## Desired state
- Task truth is durable and independent of transcript/chat history.
- Recovery resumes unfinished runs automatically.
- Restart is handled out-of-band.
- Repairs are allowlisted and validated.
- Parent/child runs are idempotent and resumable.

## Required P0 capabilities
- append-only task ledger
- run state materialization
- boot-time recovery scan
- automatic resume / retry / abandon classification
- out-of-band restart executor
- transcript rebuild path
- durable subtask orchestration

## Success criteria
- gateway restart does not require manual resume for eligible runs
- already-completed steps are not re-executed after recovery
- transcript corruption does not destroy run truth
- missing child jobs are detectable and recoverable
- unsafe repair proposals are blocked or rolled back

## Constraints
- do not solve this with prompts alone
- do not allow restart in the current exec chain
- do not let dashboards or reports replace the durable execution core
