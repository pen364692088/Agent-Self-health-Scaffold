# Task: demo_checkpointed_step_loop_v1

## Objective
Demo: Checkpointed Step Loop v1 恢复能力演示

## Repository
- Path: `/tmp/demo_repo`
- Branch: `main`

## Acceptance Criteria
1. 步骤可以在中断后恢复
2. 不会重复执行已完成的步骤
3. 完成前必须通过 Gate A/B/C 验证

## Steps
- [S01] 初始化
- [S02] 处理
- [S03] 收尾

## Status
- Created: 2026-03-15T12:13:44.692012Z
- Status: created

## Files
- State: `task_state.json`
- Ledger: `ledger.jsonl`
- Steps: `steps/`
- Evidence: `evidence/`
- Handoff: `handoff/`
