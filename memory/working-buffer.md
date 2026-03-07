# Working Buffer

**Purpose**: 恢复工作记忆 - 短期工作焦点

**Updated**: 2026-03-07T17:32:00-06:00

---

## Active Focus
实现会话连续性最小保障机制

## Current Problem
新 session 导致工作上下文丢失，因为没有：
1. 强制状态落盘
2. 新 session 恢复流程
3. context 阈值行为

## Hypotheses
- 问题根源：agent 先回复，没写状态
- 解决方案：WAL 思路 - 先写，再说
- 需要三层：文档层 + 状态层 + 执行层

## Candidates
| 方案 | 优点 | 缺点 |
|------|------|------|
| 只改 AGENTS.md | 简单 | 约束力弱 |
| 只改 HEARTBEAT.md | 执行检查 | 缺少上位约束 |
| 三层全改 | 最稳 | 工作量大 |

## Pending Verification
- [ ] hook/wrapper 机制是否存在
- [ ] pre-reply guard 如何实现
- [ ] session-start recovery 如何触发

## This Turn
- 更新 AGENTS.md ✅
- 更新 HEARTBEAT.md ✅
- 创建 SESSION-STATE.md ✅
- 检查 hook 机制 ⏳

---

## 职责说明

**本文件 (working-buffer.md)**:
- 放短期工作焦点
- 当前正在处理的问题
- 候选方案和假设
- 本轮待验证点
- 它是"恢复工作记忆"

**NOT for**:
- 长期稳定信息 (→ SESSION-STATE.md)
- 交接摘要 (→ handoff.md)