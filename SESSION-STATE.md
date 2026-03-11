# SESSION-STATE.md

## Current Objective
OpenClaw 无人监管续跑闭环补齐（最小闭环）

## Phase
IMPLEMENTING

## Branch
main

## Blocker
None

---

## 本轮目标
把当前“需要用户说继续才能继续”的执行模式，升级为“中断后可自动恢复并继续推进”的无人监管模式。

## 已完成
- 新增 `tools/run-state`，作为 durable truth layer
- 新增 `state/durable_execution/RUN_STATE.json`
- 新增 `state/durable_execution/CHECKPOINTS/`
- `session-start-recovery` 已接入 `run-state recover`
- `subagent-completion-handler` 已在 step complete / failed / duplicate / wait-deps / workflow done 时写 checkpoint
- `handle-subagent-complete` 已在 spawn / wait / done / error 路径写 checkpoint
- `spawn-with-callback` 补齐 `-p` 短参数兼容，并满足既有测试期望
- 新增最小测试 `tests/test_run_state_minimal.py`

## 当前判断
最小闭环已覆盖两段核心链路：
1. 状态真相落盘（RUN_STATE + CHECKPOINT）
2. 启动恢复读取 durable state，并给出 resume_action / should_auto_continue

## 剩余收口
1. 把 hard-block-only 策略显式收敛成统一判定函数/表
2. 处理旧 TASK_LEDGER 历史脏数据对恢复判断的干扰
3. 补一份中断恢复验证报告（restart / phase complete / normal tool fail）
4. 提交本轮改动

## Next Actions
1. 清洗/隔离旧 pending ledger 噪音
2. 补 hard-block policy 最小实现
3. 产出最小验证报告
4. git commit

## Updated
2026-03-11 08:34 CDT
