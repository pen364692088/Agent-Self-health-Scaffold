# Task: context-budget-check Tool

## Objective
实现 prompt token 预算检查器，输出压力等级。

## Location
`tools/context-budget-check`

## Requirements

### Input
- `--state <file>` - active_state.json 路径
- `--history <file>` - 原始对话历史 (JSONL)
- `--max-tokens <n>` - 最大 token 额度 (默认 100000)

### Output (JSON)
```json
{
  "estimated_tokens": 45000,
  "max_tokens": 100000,
  "ratio": 0.45,
  "pressure_level": "normal",
  "threshold_hit": null,
  "snapshot_id": "snap_20260306_001"
}
```

### Pressure Levels
- ratio < 0.70 → "normal"
- ratio >= 0.70 → "light"
- ratio >= 0.85 → "standard"
- ratio >= 0.92 → "strong"

### Options
- `--snapshot` - 生成 budget snapshot 文件
- `--json` - JSON 输出
- `--health` - 健康检查
- `--test` - 自检测试

### Constraints
- 使用 tiktoken 或简单估算（4 chars ≈ 1 token）
- 错误格式：`{"error": {"type": "...", "message": "..."}}`
- 必须符合 Tool Delivery Gates

## Verification
```bash
# Gate A: Schema exists (already done)
# Gate B: E2E test
tools/context-budget-check --test
# Gate C: Health
tools/context-budget-check --health | jq '.status'
```

## Output
完成后输出工具路径和测试结果。
