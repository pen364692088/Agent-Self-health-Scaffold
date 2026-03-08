# Objective Parser Rules v1.1.1

## Overview

本文档定义了 Objective 字段的解析规则，确保能正确提取各种格式的目标信息。

## Supported Formats

### Format 1: Markdown Header Section
```markdown
## Current Objective
实现 Session Continuity v1.1.1
```

### Format 2: Single Line with Colon
```markdown
Objective: 实现用户认证功能
```

### Format 3: Multi-line Block
```markdown
Objective:
这是一个多行的目标描述
可以跨越多行
```

### Format 4: List Item
```markdown
- Objective: 实现性能优化
```

### Format 5: Bold Key
```markdown
**Current Objective**: 实现数据同步
```

### Format 6: Chinese/English Mixed
```markdown
## Current Objective 当前目标
Implement the session continuity protocol
实现会话连续性协议
```

## Parsing Algorithm

```
1. 尝试匹配 Markdown 标题格式 (## Current Objective)
2. 如果匹配，提取标题后的内容直到下一个 ## 或文件结束
3. 如果不匹配，尝试单行格式 (Objective: xxx)
4. 如果不匹配，尝试列表项格式 (- Objective: xxx)
5. 如果不匹配，尝试粗体格式 (**Current Objective**:)
6. 清理提取的内容：
   - 移除前后空白
   - 移除 markdown 格式符号
   - 合并多行为单行
7. 判断状态：
   - 内容存在且有实质文字 → valid
   - 内容为空或只有空白 → empty
   - 未找到任何匹配 → missing
```

## Normalization Rules

1. 移除前后空白
2. 将多个空白符合并为单个空格
3. 移除 markdown 格式符号（*, _, # 等）
4. 截断超过 200 字符的内容（保留前 200 字符）
5. 空字符串、纯空白、"TBD"、"N/A"、"无" 视为空值

## Status Determination

| 状态 | 条件 |
|------|------|
| valid | 找到匹配且内容非空 |
| empty | 找到匹配但内容为空/占位符 |
| missing | 未找到任何匹配 |

## Debug Output

每次解析应输出：
```json
{
  "source_file": "SESSION-STATE.md",
  "matched_pattern": "## Current Objective",
  "extracted_raw": "实现 Session Continuity v1.1.1\n",
  "normalized_value": "实现 Session Continuity v1.1.1",
  "status": "valid"
}
```

## Test Cases

| Case | Input | Expected Status | Expected Value |
|------|-------|-----------------|----------------|
| 1 | `## Current Objective\n实现目标` | valid | 实现目标 |
| 2 | `Objective: 实现目标` | valid | 实现目标 |
| 3 | `- Objective: 实现目标` | valid | 实现目标 |
| 4 | `**Current Objective**: 实现目标` | valid | 实现目标 |
| 5 | `## Current Objective\n\n` | empty | "" |
| 6 | `## Current Objective\nTBD` | empty | "" |
| 7 | `## Other Section\n内容` | missing | null |
| 8 | `## Current Objective 目标\n实现目标` | valid | 实现目标 |
| 9 | `## Current Objective\n实现目标\n继续` | valid | 实现目标 继续 |
| 10 | `## Current Objective\n实现目标\n\n## Next\n下一步` | valid | 实现目标 |

---
Version: 1.1.1
Created: 2026-03-07