# Task: task_egocore_p1c1_summary

## Objective
P1-C1: Long-Term Self Summary v1 - 定义长期自我摘要，用于跨天恢复

## Repository
- Path: `/home/moonlight/Project/Github/MyProject/EgoCore`
- Branch: `main`

## Acceptance Criteria
1. long_term_self_summary.schema.json 完整
2. summary 与 identity invariants 不冲突
3. summary 是主体压缩表示，不是历史流水账
4. summary 可用于跨天恢复
5. summary 不包含 memory/appraisal/reflection 本体
6. 变更可追踪、可审计
7. 不破坏现有主链稳定性

## Steps
- [S1] 创建 Long-Term Self Summary Schema
- [S2] 创建 Summary Contract 文档
- [S3] 实现 Summary Generator
- [S4] 创建 Snapshot 和 Audit
- [S5] Gate A/B/C 验证

## Status
- Created: 2026-03-16T03:07:25.963223Z
- Status: created

## Files
- State: `task_state.json`
- Ledger: `ledger.jsonl`
- Steps: `steps/`
- Evidence: `evidence/`
- Handoff: `handoff/`
