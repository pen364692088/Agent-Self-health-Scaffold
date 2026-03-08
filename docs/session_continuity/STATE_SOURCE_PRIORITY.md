# State Source Priority v1.1

## Overview

本文档定义了状态源的优先级顺序，用于冲突裁决。

## Priority Order

| 优先级 | 来源 | 信任度 | 说明 |
|--------|------|--------|------|
| 1 | Repo Evidence | 100 | Git repo 的当前状态 |
| 2 | WAL Entry | 90 | 最新的原子写入记录 |
| 3 | handoff.md | 80 | 交接摘要 |
| 4 | SESSION-STATE.md | 70 | 会话主状态 |
| 5 | working-buffer.md | 60 | 工作记忆缓冲 |

## Source Descriptions

### 1. Repo Evidence (Priority: 100)
**最可信来源**

Repo 是项目状态的最终真相来源。

**包含**:
- 当前分支 (git branch --show-current)
- 最近提交 (git log -1)
- 工作区状态 (git status)
- 远程同步状态 (git fetch && git status)

**何时使用**:
- 验证 SESSION-STATE.md 中的分支信息
- 确认任务是否已提交
- 检查工作区是否有未保存变更

### 2. WAL Entry (Priority: 90)
**最新原子写入**

WAL (Write-Ahead Log) 记录了所有状态变更。

**包含**:
- timestamp
- session_id
- agent_id
- action_type
- summary
- state_hash

**何时使用**:
- 状态文件损坏时恢复
- 确认最近一次状态写入
- 崩溃恢复

### 3. handoff.md (Priority: 80)
**交接摘要**

Handoff 文件记录了会话交接时的完整状态。

**包含**:
- 会话进度
- 已确认结论
- 待验证项
- 下一步建议

**何时使用**:
- 新 session 启动时
- 长时间中断后恢复
- 上下文即将丢失前

### 4. SESSION-STATE.md (Priority: 70)
**会话主状态**

主状态文件，记录当前工作的骨架信息。

**包含**:
- Current Objective
- Current Phase
- Current Branch / Workspace
- Latest Verified Status
- Next Actions
- Blockers

**何时使用**:
- 每次恢复的主数据源
- 确认当前目标
- 检查下一步行动

### 5. working-buffer.md (Priority: 60)
**工作记忆缓冲**

短期工作记忆，记录当前焦点和假设。

**包含**:
- Active Focus
- Hypotheses
- Candidates
- Pending Verification

**何时使用**:
- 恢复工作上下文
- 理解当前思考过程
- 恢复临时假设

## Conflict Resolution

当多个来源提供不一致信息时，按优先级裁决：

```
Higher Priority Source Wins
```

**示例**:
- SESSION-STATE.md 说 branch = "feature-a"
- Repo Evidence 显示 branch = "main"
- **裁决**: 使用 "main" (Repo 优先级更高)

## Freshness Consideration

除了优先级，还需要考虑新鲜度：

| 新鲜度 | 时间范围 | 状态 |
|--------|----------|------|
| Fresh | < 24h | ✅ 可信 |
| Stale | 24-72h | ⚠️ 需验证 |
| Expired | > 72h | ❌ 需重新确认 |

**规则**:
- Fresh 文件可直接使用
- Stale 文件需与其他来源交叉验证
- Expired 文件不作为主要依据

## Implementation

```python
# Priority in code
SOURCE_PRIORITY = {
    "repo_evidence": 100,
    "wal_entry": 90,
    "handoff_md": 80,
    "session_state_md": 70,
    "working_buffer_md": 60,
}

def resolve_conflict(sources: Dict[str, Any]) -> Tuple[str, Any]:
    """Resolve conflict by choosing highest priority source."""
    best_source = None
    best_priority = -1
    
    for source_name, value in sources.items():
        priority = SOURCE_PRIORITY.get(source_name, 0)
        if priority > best_priority and value is not None:
            best_priority = priority
            best_source = source_name
    
    return best_source, sources[best_source]
```

---
Version: 1.1
Created: 2026-03-07