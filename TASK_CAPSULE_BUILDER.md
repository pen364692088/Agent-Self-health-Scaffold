# Task: capsule-builder Tool

## Objective
从对话段中抽取结构化 capsule。

## Location
`tools/capsule-builder`

## Requirements

### Input
- `--input <file>` - raw.jsonl 路径
- `--start <n>` - 起始 turn
- `--end <n>` - 结束 turn
- `--session-id <id>` - Session ID

### Output (JSON)
```json
{
  "capsule_id": "cap_20260306_001",
  "session_id": "sess_abc",
  "source_turn_range": [12, 31],
  "topic": "OpenClaw 会话压缩设计",
  "summary": "讨论了 resident layer、open loops、向量回填边界。",
  "decisions": [
    "压缩发生在编排层",
    "只靠 embedding 不够"
  ],
  "open_loops": [
    {"id": "loop_1", "text": "xxx", "priority": "high", "status": "open"}
  ],
  "hard_constraints": [
    "response plan 必须常驻"
  ],
  "entities": ["OpenClaw", "session capsule"],
  "retrieval_keys": ["context compression", "session capsule"],
  "reconstructable": true,
  "created_at": "2026-03-06T10:00:00-06:00"
}
```

### Extraction Logic
1. **decisions**: 识别"决定"、"确认"、"选择"等决策语句
2. **open_loops**: 识别"待定"、"需要"、"尚未"等未完成事项
3. **hard_constraints**: 识别"必须"、"不能"、"禁止"等约束
4. **entities**: 提取名词实体
5. **retrieval_keys**: 生成检索关键词

### Options
- `--output <dir>` - 输出目录
- `--format json|markdown` - 输出格式
- `--health` - 健康检查
- `--test` - 自检测试

### Constraints
- 使用 LLM 提取结构化信息
- 遵循 schema/session_capsule.v1.schema.json
- 错误格式：`{"error": {"type": "...", "message": "..."}}`

## Verification
```bash
# Gate B: E2E test
tools/capsule-builder --test
# Gate C: Health
tools/capsule-builder --health | jq '.status'
```

## Output
完成后输出工具路径和测试结果。
