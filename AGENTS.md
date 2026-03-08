# AGENTS.md

## Session Continuity v1.1.1 (STABLE) ⭐⭐⭐⭐⭐

**Baseline Version**: v1.1.1 STABLE  
**Frozen Date**: 2026-03-07  
**Mode**: DEFAULT-ON

---

## ⚠️ FIRST ACTION (MANDATORY) ⚠️

**Before ANY other action in a new session, you MUST:**

```bash
session-start-recovery --recover --summary
```

This command:
1. Detects if this is a new session
2. Recovers state from SESSION-STATE.md, working-buffer.md, handoff.md
3. Logs recovery events to session_continuity_events.jsonl
4. Generates recovery summary

**You MUST execute this command now if this is a new session.**

---

## 最高优先级：会话连续性协议 (MANDATORY)

### Purpose
防止新 session/thread 导致工作上下文丢失。

### Core Rules

1. **Chat context is temporary cache only, not source of truth.**
   - 聊天上下文只是临时缓存，不是真相来源
   - 真相必须持久化到状态文件

2. **Source of truth for ongoing work must be persisted in:**
   - `SESSION-STATE.md` - 当前总目标、阶段、分支、blocker、下一步
   - `working-buffer.md` - 当前工作焦点、假设、待验证点
   - `handoff.md` - 交接摘要（长会话或任务交接时）

3. **Before sending a reply that changes anything important:**
   - 任务状态变化 → 更新 SESSION-STATE.md
   - 工作焦点变化 → 更新 working-buffer.md
   - 会话可能结束 → 写 handoff.md
   - **Rule: Persist first, reply second.**

4. **On every new session start, read before doing substantive work:**
   - SESSION-STATE.md
   - working-buffer.md
   - latest handoff.md (if present)

5. **If these files are missing, stale, or contradictory:**
   - 明确报告状态不确定
   - 从 repo/logs 重建状态后再继续

6. **Never rely on prior chat history alone for continuity.**

7. **Context threshold behavior:**
   | Context | Behavior |
   |---------|----------|
   | < 60% | 按事件写状态 |
   | 60-80% | 每条实质性回复前检查并必要时写 |
   | > 80% | 强制 handoff + 压缩前强制落盘 |

---

## 自动恢复流程 (DEFAULT-ON)

### 新 Session 启动时自动执行

**Execute immediately at session start:**
```bash
session-start-recovery --recover --summary
```

**如果恢复成功**:
- 从 SESSION-STATE.md 提取 objective, phase, branch, blocker
- 从 handoff.md 获取交接信息
- 从 WAL 获取最新状态
- 事件记录到 session_continuity_events.jsonl

**如果恢复失败**:
- 设置 uncertainty_flag
- 报告状态不确定
- 记录 recovery_uncertainty 事件

---

## 子代理编排唯一正式规则

### 唯一正式入口
所有子代理相关操作默认只通过以下入口进行：

- `subtask-orchestrate run "<task>" -m <model>`
- `subtask-orchestrate status`
- `subtask-orchestrate resume`

### 禁止直接走的底层路径
除非明确处于调试/修复场景，否则主 agent 不应直接调用：

- `spawn-with-callback`
- `subagent-inbox`
- `subagent-completion-handler`
- `sessions_spawn` 作为普通子任务主链路
- `sessions_send` 作为关键完成回执主链路
- `check-subagent-mailbox`（已废弃）

---

## cc-godmode 长任务流接入

### 长任务入口前执行
1. `session-start-recovery --preflight`
2. 如果 needs_recovery，执行恢复
3. 从恢复状态获取当前 objective, phase, next actions

### 关键状态变化后执行
1. 更新 SESSION-STATE.md
2. 追加 WAL entry
3. 必要时更新 working-buffer.md

### 任务结束/切换/暂停时
1. 生成或更新 handoff.md
2. 确保状态已落盘
3. 汇报包含: recovered state, uncertainty, last persisted step

---

## 会话归档规则

当用户明确说"归档 / 会话归档 / wrap up / session wrap up"时，必须运行：

```bash
~/.openclaw/workspace/tools/session-archive
```

---

## 回复前状态落盘 (强制)

**Before any substantive reply, verify whether state persistence is required.**

### 触发落盘的变化类型
- 任务状态变化
- 当前目标变化
- 分支/仓库状态变化
- 架构决策变化
- 执行策略变化
- 下一步/blocker 变化
- 交接准备

### 落盘动作
```bash
# 使用原子写入
state-write-atomic SESSION-STATE.md "<content>"

# 追加 WAL
state-journal-append --action state_update --summary "..."
```

---

## 健康检查

```bash
# 快速健康检查
session-state-doctor

# 完整 Gate 验证
python scripts/run_session_continuity_checks.py --gate all
```

---

## 故障处理

### 如果恢复失败
1. 检查状态文件是否存在
2. 运行 `session-state-doctor --json`
3. 从 git log / session index 重建状态
4. 报告 uncertainty

### 如果需要回退
参见: `docs/session_continuity/ROLLBACK_RUNBOOK.md`
