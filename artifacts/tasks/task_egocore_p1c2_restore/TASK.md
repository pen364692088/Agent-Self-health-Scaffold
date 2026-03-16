# Task: task_egocore_p1c2_restore

## Objective
P1-C2: Self Restore - 实现新会话启动时的主体恢复流程

## Repository
- Path: `/home/moonlight/Project/Github/MyProject/EgoCore`
- Branch: `main`

## Acceptance Criteria
1. 新会话可恢复为同一主体
2. 恢复过程可审计、可追踪
3. 冲突与缺失有明确错误出口
4. 不破坏现有主链稳定性
5. identity invariants、self-model、summary 三层可加载
6. 一致性校验与冲突处理完整
7. 恢复结果可注入 runtime/session context

## Steps
- [S1] 创建 Self Restore Schema 和 Contract
- [S2] 实现 Self Restorer
- [S3] 实现 Restore Context Injector
- [S4] 创建 Restore Audit Artifacts
- [S5] Gate A/B/C 验证

## Status
- Created: 2026-03-16T03:18:18.042622Z
- Status: created

## Files
- State: `task_state.json`
- Ledger: `ledger.jsonl`
- Steps: `steps/`
- Evidence: `evidence/`
- Handoff: `handoff/`
