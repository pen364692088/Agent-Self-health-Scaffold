# Session State

**Purpose**: 恢复主骨架 - 稳定且关键的信息

**Updated**: 2026-03-07T17:35:00-06:00

---

## Current Objective
建立 OpenClaw 会话连续性最小保障机制

## Current Phase
✅ 实现阶段完成 - 等待验证

## Current Branch / Workspace
- Branch: main
- Workspace: ~/.openclaw/workspace

## Latest Verified Status
- ✅ AGENTS.md 已更新，加入 Session Continuity Protocol
- ✅ HEARTBEAT.md 已更新，加入 Session Recovery Check + State Flush Check
- ✅ SESSION-STATE.md 已创建并明确职责
- ✅ working-buffer.md 已创建并明确职责
- ✅ handoff.md 已创建并明确职责
- ✅ session-start-recovery 工具已创建
- ✅ pre-reply-guard 工具已创建
- ⏳ 需要验证 session-start recovery 流程
- ⏳ 需要测试新 session 恢复

## Next Actions
1. 提交变更到 git
2. 新 session 启动时验证恢复流程
3. 监控 context 阈值行为
4. 根据实际使用调整规则

## Blockers
无

---

## 验证说明

### 新 Session 启动时如何恢复

**方法 1: 手动恢复**
```bash
~/.openclaw/workspace/tools/session-start-recovery --recover
```

**方法 2: HEARTBEAT 自动检查**
- 每个 heartbeat 会执行 Session Recovery Check
- 检测到新 session 时自动恢复

**方法 3: AGENTS.md 强制规则**
- 新 session 启动时必须读取状态文件
- 在发送任何实质性回复前完成恢复

### 重要回复前如何确保状态已落盘

**方法 1: 手动检查**
```bash
~/.openclaw/workspace/tools/pre-reply-guard --check "<你的消息>"
```

**方法 2: Context 阈值自动触发**
- < 60%: 按事件触发
- 60-80%: 每条实质性回复前检查
- > 80%: 强制落盘

**方法 3: HEARTBEAT 自动检查**
- 每个 heartbeat 会执行 State Flush Check

---

## 职责定义

**SESSION-STATE.md** (本文件) - 恢复主骨架
- 当前总目标
- 当前阶段
- 当前分支/仓库
- 已确认完成项
- 当前 blocker
- 下一步

**working-buffer.md** - 恢复工作记忆
- 当前正在处理的问题
- 为什么这么做
- 候选方案
- 当前假设
- 本轮待验证点

**handoff.md** - 防中断保险丝
- 会话做到哪里
- 哪些结论已经确定
- 哪些还没验证
- 下一位 agent / 下个 session 该从哪开始