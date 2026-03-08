# Field-Level Conflict Resolution v1.1.1

## Overview

本文档定义了字段级冲突解决的规则和实现。

## Tracked Fields

| Field | Description | Priority if Missing |
|-------|-------------|---------------------|
| objective | 当前总目标 | High |
| phase | 当前阶段 | Medium |
| branch | 当前分支 | Medium |
| blocker | 当前阻塞项 | Low |
| next_step / next_actions | 下一步行动 | High |

## Source Priority

| Priority | Source | Use When |
|----------|--------|----------|
| 100 | repo_evidence | Branch, workspace state |
| 90 | wal_entry | Latest atomic write |
| 80 | handoff_md | Session handoff |
| 70 | session_state_md | Main state file |
| 60 | working_buffer_md | Working memory |

## Resolution Algorithm

```
1. 收集所有源中该字段的值
2. 过滤掉无效值（空、placeholder、missing）
3. 按 source priority 排序
4. 选择最高优先级的有效值
5. 检查是否存在冲突（其他源有不同值）
6. 输出 resolution 结果
```

## Resolution Output

```json
{
  "field": "objective",
  "status": "valid",
  "value": "实现 Session Continuity v1.1.1",
  "chosen_source": "session_state_md",
  "reason": "Highest priority source with valid value",
  "conflicts": [
    {
      "source": "handoff_md",
      "value": "实现 v1.1",
      "priority": 80
    }
  ]
}
```

## Placeholder Detection

以下值被视为 placeholder (空值):
- 空字符串
- "TBD", "tbd"
- "N/A", "n/a"
- "无", "none"
- "-", "..."

## Uncertainty Flag

以下情况设置 `uncertainty_flag = true`:
1. 关键字段 (objective, next_step) 完全缺失
2. 多个高优先级源冲突且无法自动裁决
3. 所有源都是 placeholder

## Examples

### Example 1: Clear Winner

```
Sources:
- session_state_md: objective = "实现 v1.1.1" (priority 70)
- handoff_md: objective = "实现 v1.1" (priority 80)
- working_buffer_md: objective = "" (empty)

Resolution:
- chosen_value: "实现 v1.1.1"
- chosen_source: session_state_md
- reason: "Only valid value found"
- conflicts: null
```

### Example 2: Conflict with Different Values

```
Sources:
- session_state_md: objective = "实现 v1.1.1" (priority 70)
- handoff_md: objective = "修复 bug" (priority 80)

Resolution:
- chosen_value: "修复 bug"
- chosen_source: handoff_md
- reason: "Highest priority source (handoff_md, priority=80)"
- conflicts: [{"source": "session_state_md", "value": "实现 v1.1.1", "priority": 70}]
```

### Example 3: All Empty

```
Sources:
- session_state_md: objective = "TBD"
- handoff_md: objective = ""
- working_buffer_md: objective = "N/A"

Resolution:
- status: "missing"
- value: null
- chosen_source: null
- reason: "No valid values found"
```

---
Version: 1.1.1
Created: 2026-03-07