# Task: task_egocore_p0_hosting

## Objective
EgoCore P0: 宿主化收口 - 让 EgoCore 成为 OpenEmotion 的唯一正式宿主，完成最小主体链路的标准化接线

## Repository
- Path: `/home/moonlight/Project/Github/MyProject/EgoCore`
- Branch: `main`

## Acceptance Criteria
1. EgoCore 可稳定生成合法事件 payload (event_input.schema.json)
2. OpenEmotion 输出可被 EgoCore 结构化消费 (openemotion_output.schema.json)
3. adapter 成为唯一正式接线入口
4. 最小闭环具备 replay / audit / artifact
5. 不破坏现有 EgoCore 主链稳定

## Steps
- [S1] 创建 Event Input Contract v1
- [S2] 创建 OpenEmotion Output Contract v1
- [S3] 创建 OpenEmotion Adapter
- [S4] 实现最小 E2E Replay Chain
- [S5] 验证与 Gate 检查

## Status
- Created: 2026-03-16T01:52:16.144439Z
- Status: created

## Files
- State: `task_state.json`
- Ledger: `ledger.jsonl`
- Steps: `steps/`
- Evidence: `evidence/`
- Handoff: `handoff/`
