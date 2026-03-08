# WAL Protocol v1.1

## Overview

WAL (Write-Ahead Log) 协议确保状态变更的原子性和可恢复性。

## Core Principle

> **Journal Before State**
> 先写日志，再更新状态文件。

## WAL File Location

```
state/wal/session_state_wal.jsonl
```

## Entry Schema

```json
{
  "timestamp": "2026-03-07T18:00:00-06:00",
  "session_id": "telegram:8420019401",
  "agent_id": "main",
  "task_id": "task_20260307_001",
  "branch": "feature-a",
  "action_type": "objective_change",
  "summary": "Changed objective from 'v1.0' to 'v1.1'",
  "objective": "实现 Session Continuity v1.1",
  "phase": "Phase 1: 强制恢复链路",
  "hash": "abc123def456"
}
```

## Action Types

| Action Type | Description | Required Fields |
|-------------|-------------|-----------------|
| `objective_change` | 目标变更 | objective |
| `phase_change` | 阶段变更 | phase |
| `branch_change` | 分支变更 | branch |
| `task_start` | 任务开始 | task_id |
| `task_complete` | 任务完成 | task_id |
| `state_update` | 状态更新 | summary |
| `handoff_create` | 创建交接 | summary |
| `recovery` | 恢复操作 | summary |

## Write Flow

```
1. 准备状态变更
2. 构建 WAL entry
3. Append 到 WAL 文件
4. Fsync 确保 WAL 落盘
5. 更新状态文件 (使用 atomic write)
6. Fsync 确保状态文件落盘
```

## Recovery Flow

```
1. 检测状态文件是否损坏或不一致
2. 读取 WAL 文件
3. 从最新有效 entry 开始回放
4. 重建状态
5. 验证重建状态
```

## Tools

### state-journal-append

```bash
# 追加日志条目
state-journal-append --action objective_change --summary "Changed to v1.1"

# 列出最近条目
state-journal-append --list --limit 20

# 获取最新条目
state-journal-append --latest

# 回放日志重建状态
state-journal-append --replay
```

### state-write-atomic

```bash
# 原子写入文件
state-write-atomic --file SESSION-STATE.md --content "<content>"

# 自动追加 WAL
state-write-atomic --file SESSION-STATE.md --content "<content>" --session-id "telegram:123"
```

## Integrity Checks

### Entry Validation

每条 WAL entry 必须包含：
- ✅ timestamp (ISO 8601)
- ✅ session_id
- ✅ action_type
- ✅ summary

### Corruption Detection

```bash
# 检查 WAL 完整性
state-journal-append --validate
```

## Retention Policy

| 条目类型 | 保留时间 |
|----------|----------|
| 所有条目 | 最近 7 天 |
| 重要条目 | 最近 30 天 |

**自动清理**: 每周清理超过保留期的条目

## Example Session

```bash
# 开始新任务
state-journal-append --action task_start --task-id "task_001" --summary "开始实现 WAL"

# 更新目标
state-journal-append --action objective_change --objective "实现 WAL 协议"

# 更新阶段
state-journal-append --action phase_change --phase "实现阶段"

# 完成任务
state-journal-append --action task_complete --task-id "task_001" --summary "WAL 协议实现完成"
```

---
Version: 1.1
Created: 2026-03-07