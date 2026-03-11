# Auto Resume Restart Validation Report

Date: 2026-03-11
Scope: OpenClaw 主任务在 gateway 重启后的自动续跑 MVP 验证

## Goal
验证在非人为中断（gateway restart）后，系统是否能基于持久化状态自动恢复并继续推进主任务，而无需用户再次发送“继续”。

## Test Method
使用独立的 systemd transient service 运行一个 3 分钟 demo：

1. 预先写入 durable workflow / run-state
2. 在第 1 分钟调度 `systemctl --user restart openclaw-gateway`
3. 观察 gateway 重启后，`auto-resume-orchestrator` 是否自动触发
4. 检查是否自动调用 `subtask-orchestrate resume` 并推进后续步骤

相关文件：
- `tools/demo-auto-resume-restart-test`
- `artifacts/auto_resume_demo/trace.jsonl`
- `artifacts/auto_resume/recovery_log.jsonl`
- `state/durable_execution/AUTO_RESUME_RUNTIME.json`

## Key Evidence

### 1. Demo started and scheduled restart
From `artifacts/auto_resume_demo/trace.jsonl`:
- `test_start`
- `restart_scheduled` with `delay_s=60`

### 2. Gateway actually restarted
From `systemctl --user status openclaw-gateway`:
- gateway active since `2026-03-11 14:19:30 CDT`

This aligns with the planned mid-run restart window.

### 3. Auto-resume triggered after restart
From `journalctl --user -u auto-resume-orchestrator.service`:
- time: `2026-03-11T14:19:30`
- `run_state_action: resume_running`
- `target_kind: workflow_step`
- `target_id: phase3`
- `action: resumed`

### 4. Formal resume entrypoint was used
Same log shows:
- `entrypoint: subtask-orchestrate.resume`
- downstream advance result: `action: spawn_next`
- resumed task: `demo phase3 final`

### 5. Test continued to completion window without user intervention
From `artifacts/auto_resume_demo/trace.jsonl`:
- tick events continued after restart
- final event: `test_end`

## Result

### Passed
- gateway restart occurred during active test window
- restart did not require user to send “继续”
- startup recovery automatically scanned durable state
- system automatically re-entered the formal main-task continuation path
- anti-duplicate runtime ledger updated:
  - `last_attempt_at`
  - `last_target`
  - `last_checkpoint_ts`
  - `recovery_counts`

## What This Proves
This validates the intended MVP behavior:

> checkpoint-based continuation works after gateway restart.

More concretely:
- unfinished main work can be persisted durably
- startup recovery can discover it
- auto-resume can trigger continuation automatically
- continuation uses the formal orchestrator entrypoint instead of ad-hoc chat memory

## Boundary / Non-Claim
This test does **not** prove byte-for-byte continuation of the exact same in-flight child process.

It proves the MVP design target instead:
- recover from durable checkpoint
- continue from next durable action
- avoid dependence on transient session context

That is the correct target for restart resilience.

## Known Follow-up Improvements
1. Add stronger recovery markers:
   - `resume_reason`
   - `recovered_from_checkpoint`
   - `resume_attempt`
   - `orphan_reclaimed`
2. Distinguish:
   - running-but-child-still-alive
   - running-but-child-orphaned
3. Add a formal repeatable regression wrapper around this restart scenario
4. Add richer failure classification for recovery failure states

## Verdict
MVP closed-loop validation: **PASS**

OpenClaw can now automatically continue main task progression after gateway restart, provided the task has a durable checkpoint / recoverable next action.
