# Session Recovery Flow v1.1

## Overview

本文档定义了 Session 状态恢复的完整流程。恢复必须在任何实质性回复之前执行。

## Core Principle

> **Recovery BEFORE Reply**
> 状态恢复必须在任何实质性回复之前完成。

## Trigger Points

恢复在以下位置触发：

| 优先级 | 触发点 | 说明 |
|--------|--------|------|
| P1 | Message 入口 | 收到用户消息时立即检查 |
| P2 | HEARTBEAT | 周期性检查（兜底） |
| P3 | 手动调用 | `session-start-recovery --recover` |

## Recovery Flow

```
┌─────────────────────────────────────────────────────┐
│               Message Received                       │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│           Preflight: Is this a new session?          │
│           session-start-recovery --preflight         │
└─────────────────────────────────────────────────────┘
                        │
           ┌────────────┴────────────┐
           │                         │
      New Session              Same Session
           │                         │
           ▼                         ▼
┌─────────────────────┐    ┌─────────────────────┐
│   Perform Recovery  │    │   Continue Normal   │
│   --recover         │    │   Processing        │
└─────────────────────┘    └─────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│              Read State Sources                      │
│  1. SESSION-STATE.md (primary)                       │
│  2. working-buffer.md (working memory)              │
│  3. handoff.md (if exists)                          │
│  4. WAL journal (if exists)                         │
└─────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│           Detect & Resolve Conflicts                 │
│  See CONFLICT_RESOLUTION_RULES.md                   │
└─────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│              Generate Recovery Summary               │
│  artifacts/session_recovery/latest_recovery_summary │
└─────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│           Continue to Process Message                │
└─────────────────────────────────────────────────────┘
```

## State Sources Read Order

恢复时按以下顺序读取状态源：

1. **WAL Journal** (`state/wal/session_state_wal.jsonl`)
   - 最新的原子写入记录
   - 最高优先级

2. **SESSION-STATE.md**
   - 当前总目标、阶段、分支、blocker、下一步
   - 主骨架

3. **working-buffer.md**
   - 当前工作焦点、假设、待验证点
   - 工作记忆

4. **handoff.md**
   - 交接摘要（如存在）
   - 防中断保险丝

## Recovery Output

每次恢复生成以下输出：

### JSON Summary
`artifacts/session_recovery/latest_recovery_summary.json`

```json
{
  "session_id": "telegram:8420019401",
  "timestamp": "2026-03-07T17:50:00-06:00",
  "is_new_session": true,
  "recovered": true,
  "uncertainty_flag": false,
  "objective": "实现 Session Continuity v1.1",
  "phase": "Phase 1: 强制恢复链路",
  "next_actions": "Task 1: Recovery 前移",
  "sources": {
    "session_state": {"exists": true, "fresh": true, "age_hours": 0.5},
    "working_buffer": {"exists": true, "fresh": true, "age_hours": 0.5},
    "handoff": {"exists": true, "fresh": true, "age_hours": 1.0}
  },
  "conflicts": [],
  "resolution": null
}
```

### Markdown Summary
`artifacts/session_recovery/latest_recovery_summary.md`

## Failure Handling

### Recovery Failure
如果恢复失败：
1. 设置 `uncertainty_flag = true`
2. 记录失败原因
3. **不得假装已恢复**
4. 显式报告状态不确定

### No State Files Found
如果没有状态文件：
1. 这是一个全新开始
2. 不需要恢复
3. 继续正常处理

### Conflicts Detected
如果检测到冲突：
1. 按 CONFLICT_RESOLUTION_RULES.md 裁决
2. 记录冲突和裁决结果
3. 如果仍有不确定，设置 `uncertainty_flag = true`

## Integration Points

### AGENTS.md Integration
```markdown
## 新 Session 启动时必须执行 (强制) ⭐⭐⭐⭐⭐
1. 读取 SESSION-STATE.md
2. 读取 working-buffer.md
3. 如存在 handoff.md，读取最新版本
4. 比较恢复状态与当前 repo/task 状态
5. 如有冲突，以文件/repo 为准，报告不确定
```

### HEARTBEAT.md Integration
```markdown
## Session Recovery Check (每次 heartbeat) ⭐⭐⭐⭐⭐
session-start-recovery --check
```

### pre-reply-guard Integration
```bash
# Before any substantive reply
session-start-recovery --preflight
# If needs_recovery, perform recovery first
```

## Verification

### Test Cases
1. 新 session 第一条消息前恢复完成
2. 无状态文件时正常处理
3. 有冲突时正确裁决
4. 恢复失败时设置 uncertainty_flag
5. 恢复摘要正确生成

### Health Check
```bash
session-start-recovery --health
```

---
Version: 1.1
Created: 2026-03-07