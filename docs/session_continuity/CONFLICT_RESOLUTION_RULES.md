# Conflict Resolution Rules v1.1

## Overview

本文档定义了状态源冲突时的裁决规则。

## Conflict Types

### Type 1: Branch Mismatch

**场景**: SESSION-STATE.md 记录的分支与实际 repo 分支不一致

**示例**:
```
SESSION-STATE.md: branch = "feature-a"
Repo Evidence: branch = "main"
```

**裁决规则**:
| 条件 | 裁决 | 原因 |
|------|------|------|
| Repo 分支存在 | Repo 分支 | Repo 是真相来源 |
| SESSION-STATE 分支存在但 repo 不存在 | 需确认 | 可能分支已删除或合并 |
| 两者都不存在 | unknown | 需要用户确认 |

**输出**:
```json
{
  "conflict_type": "branch_mismatch",
  "session_state_branch": "feature-a",
  "repo_branch": "main",
  "resolution": "repo_evidence",
  "chosen_value": "main",
  "reason": "Repo is source of truth for branch"
}
```

---

### Type 2: Objective Mismatch

**场景**: handoff.md 与 SESSION-STATE.md 的目标不一致

**示例**:
```
handoff.md: objective = "实现用户认证"
SESSION-STATE.md: objective = "优化性能"
```

**裁决规则**:
| 条件 | 裁决 | 原因 |
|------|------|------|
| handoff 更新时间 > SESSION-STATE | handoff | handoff 是更新的 |
| SESSION-STATE 更新时间 > handoff | SESSION-STATE | SESSION-STATE 是更新的 |
| 时间相近 | 需确认 | 可能是并行更新 |

**输出**:
```json
{
  "conflict_type": "objective_mismatch",
  "handoff_objective": "实现用户认证",
  "session_state_objective": "优化性能",
  "resolution": "newer_timestamp",
  "chosen_source": "handoff_md",
  "reason": "handoff.md is newer (2h vs 5h)"
}
```

---

### Type 3: Stale State File

**场景**: 状态文件时间戳明显过旧

**示例**:
```
SESSION-STATE.md: modified 48 hours ago
working-buffer.md: modified 1 hour ago
```

**裁决规则**:
| 年龄 | 状态 | 处理 |
|------|------|------|
| < 24h | Fresh | 直接使用 |
| 24-72h | Stale | 标记警告，交叉验证 |
| > 72h | Expired | 需重新确认 |

**输出**:
```json
{
  "conflict_type": "stale_file",
  "source": "session_state_md",
  "age_hours": 48,
  "resolution": "warn",
  "reason": "SESSION-STATE.md is 48 hours old",
  "cross_validation": {
    "working_buffer_age": 1,
    "handoff_age": 2
  }
}
```

---

### Type 4: Missing Critical Field

**场景**: 关键字段缺失

**示例**:
```
SESSION-STATE.md: objective = ""
working-buffer.md: objective = "实现 v1.1"
```

**裁决规则**:
| 缺失字段 | 处理 |
|----------|------|
| objective | 从其他来源恢复或提示用户 |
| next_actions | 从 working-buffer 恢复 |
| blockers | 默认为空 |

**输出**:
```json
{
  "conflict_type": "missing_field",
  "field": "objective",
  "session_state_value": null,
  "working_buffer_value": "实现 v1.1",
  "resolution": "fallback",
  "chosen_source": "working_buffer_md",
  "reason": "SESSION-STATE.md missing objective"
}
```

---

### Type 5: WAL vs State File

**场景**: WAL 记录与状态文件不一致

**示例**:
```
WAL (latest): objective = "修复 bug #123"
SESSION-STATE.md: objective = "实现 v1.1"
```

**裁决规则**:
| 条件 | 裁决 | 原因 |
|------|------|------|
| WAL 更新时间 > SESSION-STATE | WAL | WAL 是最新的原子写入 |
| SESSION-STATE 更新时间 > WAL | SESSION-STATE | 可能在 WAL 之后手动更新 |
| 时间相近但值不同 | 需确认 | 可能是并发写入 |

**输出**:
```json
{
  "conflict_type": "wal_state_mismatch",
  "wal_value": "修复 bug #123",
  "state_file_value": "实现 v1.1",
  "resolution": "wal_entry",
  "reason": "WAL is most recent atomic write"
}
```

---

## Resolution Algorithm

```python
def resolve_all_conflicts(conflicts: List[Dict], sources: Dict) -> Dict:
    """Resolve all detected conflicts."""
    resolution = {
        "resolved": True,
        "uncertainty_flag": False,
        "chosen_values": {},
        "applied_resolutions": []
    }
    
    for conflict in conflicts:
        result = resolve_single_conflict(conflict, sources)
        resolution["applied_resolutions"].append(result)
        
        if result.get("uncertainty"):
            resolution["uncertainty_flag"] = True
        
        # Update chosen values
        if result.get("field") and result.get("chosen_value"):
            resolution["chosen_values"][result["field"]] = result["chosen_value"]
    
    return resolution
```

## Output Format

所有冲突裁决后，生成统一输出：

```json
{
  "conflicts_found": 2,
  "all_resolved": true,
  "uncertainty_flag": false,
  "resolutions": [
    {
      "conflict_type": "branch_mismatch",
      "resolution": "repo_evidence",
      "chosen_value": "main"
    },
    {
      "conflict_type": "stale_file",
      "resolution": "warn",
      "source": "session_state_md"
    }
  ]
}
```

## Uncertainty Flag

当以下情况发生时，设置 `uncertainty_flag = true`:

1. 无法自动裁决的冲突
2. 多个来源同时 Stale
3. 关键字段缺失且无法从其他来源恢复
4. WAL 与所有状态文件都不一致

**处理方式**:
- 不假装已恢复
- 显式报告不确定
- 建议用户确认

---
Version: 1.1
Created: 2026-03-07