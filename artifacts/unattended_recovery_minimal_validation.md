# Unattended Recovery Minimal Validation

Date: 2026-03-11 08:42 CDT

## Scope
Validate minimal unattended execution loop closure for:
1. durable truth persisted outside chat session
2. startup recovery derives actionable resume state
3. hard-block-only escalation policy
4. old ledger noise does not force false resume
5. ordinary failure retries/degrades before escalation
6. restart / compact-like new session recovery behavior

## Changes Under Test
- `tools/run-state`
- `tools/hard-block-policy`
- `tools/retry-policy`
- `tools/session-start-recovery`
- `tools/subagent-completion-handler`
- `tools/handle-subagent-complete`
- `tools/spawn-with-callback`

## Validation Cases

### Case 1: phase complete -> next step can auto-continue
Method:
- synthetic workflow with `s1=done`, `s2=pending`
- run `tools/run-state recover`

Expected:
- `resume_action = spawn_pending`
- `recovery_hint.should_auto_continue = true`

Result:
- PASS (`tests/test_run_state_minimal.py`)

### Case 2: ordinary failure should not hard-block
Method:
- patch `RUN_STATE.last_error_type = subagent_failed`
- run `tools/run-state derive`

Expected:
- `hard_block = false`

Result:
- PASS (`tests/test_hard_block_policy_minimal.py`)

### Case 3: hard-block classification only for allowed categories
Method:
- run `tools/hard-block-policy classify --error-type missing_permission`

Expected:
- `hard_block = true`
- reason preserved

Result:
- PASS (`tests/test_hard_block_policy_minimal.py`)

### Case 4: startup recovery consumes durable truth layer
Method:
- run `tools/session-start-recovery --recover --json`

Expected:
- output includes `run_state`
- output includes `durable_resume_action`
- output includes `durable_should_auto_continue`

Result:
- PASS

### Case 5: historical ledger noise must not trigger false recovery
Method:
- keep old historical `TASK_LEDGER.jsonl` entries
- clear hard block fields
- run `tools/run-state recover`

Expected:
- no historical test/pending entries included in `unfinished_tasks.ledger`
- `resume_action = idle` when no live workflow/orchestrator work exists

Result:
- PASS

### Case 6: retryable failure schedules retry instead of asking user
Method:
- active workflow contains running step with `retry_count=0`, `max_retries=2`
- send failed payload with `error.type = tool_failed`

Expected:
- handler returns `action = spawn_next`
- step moves back to `pending`
- `retry_count` increments

Result:
- PASS (`tests/test_retry_policy_minimal.py`)

### Case 7: second retry can degrade model
Method:
- run `tools/retry-policy decide --error-type tool_failed --retry-count 1 --max-retries 3 --model gpt --degraded-model haiku`

Expected:
- action = retry
- mode = retry_degraded
- next_model = haiku

Result:
- PASS (`tests/test_retry_policy_minimal.py`)

### Case 8: restart-like new session auto-surfaces pending work
Method:
- persist active workflow with one pending step
- force `.last_session_id` mismatch
- run `tools/session-start-recovery --recover --json`

Expected:
- `is_new_session = true`
- `durable_resume_action = spawn_pending`
- `durable_should_auto_continue = true`

Result:
- PASS (`tests/test_live_recovery_minimal.py`)

### Case 9: compact-like new session stays idle when no live work exists
Method:
- remove active workflow
- clear hard block fields
- force `.last_session_id` mismatch
- run `tools/session-start-recovery --recover --json`

Expected:
- `is_new_session = true`
- `durable_resume_action = idle`
- `durable_should_auto_continue = false`

Result:
- PASS (`tests/test_live_recovery_minimal.py`)

## Test Commands
```bash
python3 -m pytest -q \
  tests/test_live_recovery_minimal.py \
  tests/test_retry_policy_minimal.py \
  tests/test_run_state_minimal.py \
  tests/test_hard_block_policy_minimal.py

./tools/run-state recover
./tools/session-start-recovery --recover --json
```

## Current Gaps
- retry/degrade is currently implemented in `subagent-completion-handler`; not yet fully centralized for all failure sources
- callback-worker still retains legacy direct notification behavior and should be aligned to the same durable recovery contract
- no full daemon-level end-to-end restart simulation with real background workers yet

## Verdict
The minimum unattended loop is now closed enough to be meaningful:
- task truth is durable
- startup recovery can decide whether to continue automatically
- ordinary failures retry/degrade first
- only hard-block classes require user involvement
- stale ledger noise no longer creates false continuation

This is a real shift from “wait for user to say continue” toward unattended continuation.
