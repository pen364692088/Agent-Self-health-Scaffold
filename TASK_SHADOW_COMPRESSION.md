# Task: context-compress (Shadow Mode)

## Objective
实现压缩执行器，先以 shadow 模式运行（只观测，不替换 prompt）。

## Location
`tools/context-compress`

## Dependencies
- tools/context-budget-check
- tools/capsule-builder
- schemas/session_capsule.v1.schema.json
- schemas/compression_event.v1.schema.json

## Requirements

### Input
- `--session-id <id>` - Session ID
- `--state <file>` - active_state.json
- `--history <file>` - raw.jsonl
- `--capsules <file>` - capsules.jsonl (append)
- `--events <file>` - compression_events.jsonl (append)
- `--mode shadow|enforced` - 运行模式

### Output (JSON)
```json
{
  "compression_triggered": true,
  "mode": "shadow",
  "pressure_level": "standard",
  "plan": {
    "evict_turns": [12, 31],
    "create_capsules": ["cap_001"],
    "preserve_resident": ["task_goal", "open_loops"]
  },
  "capsules": [...],
  "event_id": "cmp_001"
}
```

### Shadow Mode Behavior
- 生成压缩计划但不执行
- 记录 compression_event (mode=shadow)
- 输出 "如果执行会压缩什么"

### Enforced Mode Behavior
- 实际执行压缩
- 更新 active_state.json
- 创建 capsules
- 移除原始对话段

### Options
- `--dry-run` - 只输出计划
- `--json` - JSON 输出
- `--health` - 健康检查
- `--test` - 自检测试

## Verification
```bash
# Shadow mode test
tools/context-compress --mode shadow --test

# Health check
tools/context-compress --health | jq '.status'
```

## Output
完成后输出工具路径和测试结果。
