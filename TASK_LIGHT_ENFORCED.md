# Task: prompt-assemble + Light Enforced Mode

## Objective
实现 prompt 组装器，并集成 light enforced 压缩模式。

## Location
`tools/prompt-assemble`

## Dependencies
- tools/context-budget-check
- tools/context-compress
- tools/context-retrieve
- schemas/active_state.v1.schema.json

## Requirements

### Input
- `--session-id <id>` - Session ID
- `--state <file>` - active_state.json
- `--history <file>` - raw.jsonl
- `--max-tokens <n>` - 最大 token 额度

### Output (JSON)
```json
{
  "prompt_tokens": 45000,
  "layers": {
    "resident": {
      "tokens": 5000,
      "components": ["identity", "task_goal", "open_loops", "hard_constraints"]
    },
    "active": {
      "tokens": 30000,
      "turns": [50, 51, 52, 53, 54, 55]
    },
    "recall": {
      "tokens": 2000,
      "snippets": ["cap_001", "cap_002"]
    }
  },
  "compression_applied": true,
  "compression_event": "cmp_001"
}
```

### Assembly Order
1. System prompt / identity
2. Resident state (task_goal, open_loops, hard_constraints, response_contract)
3. Current user message
4. Active window (recent 6-12 turns)
5. Retrieval snippets (if triggered)
6. Recent tool results

### Light Enforced Mode
- 当 pressure >= 0.85 时触发
- 只压缩最旧普通对话块
- 保留较大 active window (12 turns)
- capsule 写入并参与少量回填

### Options
- `--dry-run` - 只输出计划
- `--json` - JSON 输出
- `--health` - 健康检查
- `--test` - 自检测试

## Verification
```bash
# Assembly test
tools/prompt-assemble --test

# Health check
tools/prompt-assemble --health | jq '.status'
```

## Output
完成后输出工具路径和测试结果。
