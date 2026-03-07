# Task: context-shadow-report + Metrics Gate

## Objective
实现压缩观测报告器和治理门禁。

## Location
`tools/context-shadow-report`

## Dependencies
- artifacts/context_compression/shadow_log.jsonl
- schemas/compression_event.v1.schema.json

## Requirements

### Input
- `--days <n>` - 分析最近 N 天
- `--session-id <id>` - 特定 session
- `--format json|markdown` - 输出格式

### Output (JSON)
```json
{
  "period": {
    "start": "2026-03-01",
    "end": "2026-03-06"
  },
  "metrics": {
    "compression_events": 45,
    "avg_compression_ratio": 0.52,
    "capsules_created": 120,
    "retrieval_triggers": 23,
    "old_topic_recovery_rate": 0.87,
    "commitment_preservation_rate": 0.95,
    "open_loop_recall_rate": 0.82
  },
  "risks": {
    "false_compression_rate": 0.03,
    "over_retrieval_rate": 0.08,
    "hallucinated_commitment_rate": 0.01
  },
  "readiness": {
    "ready_for_enforced": true,
    "blockers": []
  }
}
```

### Quality Metrics
1. **预算类**: avg_prompt_tokens, compression_trigger_rate, compression_gain_ratio
2. **连续性类**: old_topic_recovery_rate, commitment_preservation_rate
3. **风险类**: false_compression_rate, over_retrieval_rate
4. **用户体验类**: long_chat_success_rate, user_correction_rate

### Readiness Gate
```yaml
ready_for_enforced:
  conditions:
    - old_topic_recovery_rate >= 0.85
    - commitment_preservation_rate >= 0.90
    - false_compression_rate < 0.05
    - hallucinated_commitment_rate < 0.02
```

### Options
- `--health` - 健康检查
- `--test` - 自检测试
- `--watch` - 持续监控模式

## Verification
```bash
# Report test
tools/context-shadow-report --test

# Health check
tools/context-shadow-report --health | jq '.status'
```

## Output
完成后输出工具路径和测试结果。
