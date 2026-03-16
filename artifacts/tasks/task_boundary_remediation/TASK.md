# Task: task_boundary_remediation

## Objective
边界整改与仓库迁移 - 把主体本体从 EgoCore 迁回 OpenEmotion

## Repository
- Path: `/home/moonlight/Project/Github/MyProject/EgoCore`
- Branch: `main`

## Acceptance Criteria
1. OpenEmotion 成为 identity/self-model/summary 的唯一正式权威源
2. EgoCore 不再拥有主体本体逻辑的最终解释权
3. 所有过渡实现已登记并带删除计划
4. Self Restore 仍可稳定运行
5. replay/audit/trace 完整不丢

## Steps
- [S1] 盘点与归类
- [S2] 建立 OpenEmotion 正式本体模块
- [S3] EgoCore 改为读取 OpenEmotion 产物
- [S4] Shim 登记与限期
- [S5] 删除或降级违规实现
- [S6] 回归验证
- [S7] Gate A/B/C 验证

## Status
- Created: 2026-03-16T03:49:51.654056Z
- Status: created

## Files
- State: `task_state.json`
- Ledger: `ledger.jsonl`
- Steps: `steps/`
- Evidence: `evidence/`
- Handoff: `handoff/`
