# Task: task_egocore_p1b_selfmodel

## Objective
P1-B: Self-Model v1 - 建立结构化自我模型，定义能力/限制/目标/承诺/置信度

## Repository
- Path: `/home/moonlight/Project/Github/MyProject/EgoCore`
- Branch: `main`

## Acceptance Criteria
1. self_model.schema.json 完整
2. 字段职责明确：capabilities/limitations/active_goals/standing_commitments
3. self-model 可被稳定加载与校验
4. 允许字段可按规则更新
5. identity invariants 不会被 self-model 越权改写
6. 变更可追踪、可审计、可回滚定位
7. 不破坏现有主链稳定性

## Steps
- [S1] 创建 Self-Model Schema
- [S2] 创建 Self-Model Contract 文档
- [S3] 实现 Self-Model Manager
- [S4] 创建 Snapshot 和 Change Audit
- [S5] Gate A/B/C 验证

## Status
- Created: 2026-03-16T02:53:13.798329Z
- Status: created

## Files
- State: `task_state.json`
- Ledger: `ledger.jsonl`
- Steps: `steps/`
- Evidence: `evidence/`
- Handoff: `handoff/`
