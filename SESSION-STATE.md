# SESSION-STATE.md

## Current Objective
OpenClaw 无人监管续跑闭环补齐（最小闭环 + 主链收口）

## Phase
CLOSEOUT

## Branch
main

## Blocker
None

---

## 本轮新增收口
- `callback-worker` 已降级为 trigger-only
- 唯一正式推进入口收敛为 `subtask-orchestrate resume`
- `subtask-orchestrate resume` 现在统一负责：处理 inbox → 推进 main flow → 决定 spawn / wait / notify
- 新增 `tests/test_single_entrypoint_flow.py` 验证单入口形态

## 统一后的正式主链
`callback-worker -> subtask-orchestrate resume -> handle-subagent-complete -> subagent-completion-handler -> run-state`

## 结果
主流程不再保留 callback-worker 自行决策推进的第二入口。
现在它只负责触发和必要的最终通知转发。

## Remaining
1. 更彻底清理历史文档/脚本中的旧入口表述
2. daemon 级真实重启 E2E

## Updated
2026-03-11 08:49 CDT
