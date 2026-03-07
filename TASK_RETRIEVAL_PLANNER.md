# Task: context-retrieve

## Objective
实现检索规划器，在旧主题回归时从 capsule/vector 中回填片段。

## Location
`tools/context-retrieve`

## Dependencies
- tools/capsule-builder
- schemas/session_capsule.v1.schema.json
- OpenViking 或本地向量索引

## Requirements

### Input
- `--query <text>` - 检索查询
- `--session-id <id>` - Session ID
- `--capsules <file>` - capsules.jsonl
- `--max-snippets <n>` - 最大回填片段数 (默认 4)

### Output (JSON)
```json
{
  "query": "context compression",
  "snippets": [
    {
      "source": "capsule",
      "capsule_id": "cap_001",
      "relevance": 0.85,
      "content": {
        "topic": "...",
        "decisions": [...],
        "hard_constraints": [...]
      }
    }
  ],
  "total_found": 5,
  "returned": 2
}
```

### Retrieval Priority
1. 当前 session 的 capsules
2. 当前 session 的历史 raw chunk 索引
3. 跨 session 的相关 capsule
4. 外部业务知识库（如有）

### Constraints
- 每次最多回填 2-4 个片段
- 每个片段控制在短块（<500 chars）
- 优先回填结构化决策而非长原文

### Options
- `--format json|markdown` - 输出格式
- `--health` - 健康检查
- `--test` - 自检测试

## Verification
```bash
# Retrieval test
tools/context-retrieve --query "context compression" --test

# Health check
tools/context-retrieve --health | jq '.status'
```

## Output
完成后输出工具路径和测试结果。
