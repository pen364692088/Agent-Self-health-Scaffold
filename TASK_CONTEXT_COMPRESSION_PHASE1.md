# Task: Context Compression Phase 1 - Core Tools

## Objective
实现预算检查器和胶囊构建器。

## Deliverables

### 1. tools/context-budget-check
**职责**：估算 prompt token 预算，输出压力等级

**输入**：active_state.json, history (recent turns)

**输出**：
```json
{
  "estimated_tokens": 45000,
  "max_tokens": 100000,
  "ratio": 0.45,
  "pressure_level": "normal|light|standard|strong",
  "threshold_hit": null,
  "snapshot_id": "snap_xxx"
}
```

**阈值**：
- ratio >= 0.70 → "light"
- ratio >= 0.85 → "standard"
- ratio >= 0.92 → "strong"

**选项**：
- `--snapshot` 生成 budget snapshot 到 artifacts/
- `--json` JSON 输出

### 2. tools/capsule-builder
**职责**：从对话段中抽取结构化 capsule

**输入**：turn_range (start, end), raw.jsonl 路径

**输出**：
```json
{
  "capsule_id": "cap_xxx",
  "source_turn_range": [12, 31],
  "topic": "xxx",
  "summary": "xxx",
  "decisions": [...],
  "open_loops": [...],
  "hard_constraints": [...],
  "entities": [...],
  "retrieval_keys": [...]
}
```

**关键能力**：
- 抽取 decisions（决策）
- 抽取 open_loops（未完成事项）
- 抽取 hard_constraints（硬约束）
- 生成 retrieval_keys（检索关键词）

**选项**：
- `--output-dir` 指定输出目录
- `--format json|markdown`

## Constraints
- 使用 Python 3
- 遵循 Tool Delivery Gates (Gate A/B/C)
- 包含 --help 和 --health
- 错误使用标准格式 {"error": {"type": "...", "message": "..."}}

## Verification
```bash
# Gate A: Schema
jq empty schemas/*.schema.json

# Gate B: E2E
tools/context-budget-check --test
tools/capsule-builder --test

# Gate C: Health
tools/context-budget-check --health
tools/capsule-builder --health
```

## Output
完成后列出创建的工具路径和测试结果。
