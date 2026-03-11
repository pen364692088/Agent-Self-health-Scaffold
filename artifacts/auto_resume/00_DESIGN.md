# Auto Resume MVP Design

## State Machine
- idle -> recoverable -> leased -> resumed -> cooldown
- hard_block / stopped / completed / failed_waiting_human are excluded

## Recovery Conditions
- `run-state recover` says `recovery_hint.should_auto_continue=true`
- global switch `state/durable_execution/AUTO_RESUME_CONFIG.json.enabled=true`
- target is not disabled by per-task override
- not in cooldown
- attempts for `(target, checkpoint)` below limit

## Exclusion Conditions
- global disabled
- hard block
- user/manual stop states
- completed / failed_waiting_human
- per-task or per-step `auto_resume=false`

## Idempotency / Anti-loop
- global lock: one orchestrator process at a time
- target lease: one claimant per target
- cooldown: suppress immediate duplicate retries after restart storms
- attempt cap per `(target, checkpoint)`
- checkpoint-based dedupe: new checkpoint permits a fresh resume

## Trigger Path
1. system startup runs `tools/auto-resume-orchestrator --once --json`
2. tool derives durable truth via `tools/run-state recover`
3. on eligible target, it invokes the single formal advance entrypoint: `tools/subtask-orchestrate resume`
4. writes logs to `artifacts/auto_resume/recovery_log.jsonl` and runtime to `state/durable_execution/AUTO_RESUME_RUNTIME.json`

## Switches
- Global: `AUTO_RESUME_CONFIG.json.enabled`
- Per task: `AUTO_RESUME_CONFIG.json.task_overrides[<target_id>].enabled=false`
- Per workflow step: add `"auto_resume": false` in `WORKFLOW_STATE.json` step
