# Unattended Recovery Minimal Validation

Date: 2026-03-11 08:39 CDT

## Scope
Validate minimal unattended execution loop closure for:
1. durable truth persisted outside chat session
2. startup recovery derives actionable resume state
3. hard-block-only escalation policy
4. old ledger noise does not force false resume

## Changes Under Test
- `tools/run-state`
- `tools/hard-block-policy`
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
- PASS (covered by `tests/test_run_state_minimal.py`)

### Case 2: ordinary failure should not hard-block
Method:
- patch `RUN_STATE.last_error_type = subagent_failed`
- run `tools/run-state derive`

Expected:
- `hard_block = false`

Result:
- PASS (covered by `tests/test_hard_block_policy_minimal.py`)

### Case 3: hard-block classification only for allowed categories
Method:
- run `tools/hard-block-policy classify --error-type missing_permission`

Expected:
- `hard_block = true`
- reason preserved

Result:
- PASS (covered by `tests/test_hard_block_policy_minimal.py`)

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

## Test Commands
```bash
python3 -m pytest -q tests/test_run_state_minimal.py tests/test_hard_block_policy_minimal.py
./tools/run-state recover
./tools/session-start-recovery --recover --json
```

## Current Gaps
- tool-fail auto retry/degrade path is partially represented via `repairing` status but not yet unified into a dedicated retry policy module
- restart/compact live E2E was not simulated end-to-end; current validation is minimal and deterministic
- callback-worker still writes direct notifications; policy is improved but not fully centralized

## Verdict
Minimal loop closure is now materially better:
- durable state exists
- startup recovery can auto-decide resume vs hard-block
- normal failures do not automatically escalate to user
- stale ledger noise no longer forces false continuation

Not fully complete yet, but the smallest viable unattended recovery loop is now present.
