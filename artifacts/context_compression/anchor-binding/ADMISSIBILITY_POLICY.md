# Real Old-Topic Sample Admissibility Policy

**Version**: 1.0
**Effective**: 2026-03-07 03:55 CST
**Status**: FROZEN

---

## Purpose

Define the admissibility criteria for `real_main_agent` samples entering the old-topic benchmark. This policy ensures only samples with meaningful content and anchor potential are evaluated.

---

## Frozen Admission Rules

```yaml
admission_rules:
  min_user_messages: 2
  min_assistant_messages: 2
  min_text_length: 500
  min_anchor_types: 2
  exclude_heartbeat_only: true
```

---

## Exclusion Criteria

### Automatic Exclusion (not_admissible)

1. **Heartbeat-only samples**
   - `text_hash: null` with no actual text content
   - `sent_events: [{type: "time_passed"}]` only
   - No user messages, no assistant responses

2. **Insufficient content**
   - Less than 2 user messages
   - Less than 2 assistant messages
   - Total text length < 500 characters

3. **No anchor potential**
   - Fewer than 2 anchor types extractable:
     - decision_anchor
     - entity_anchor
     - open_loop_anchor
     - constraint_anchor
     - tool_state_anchor

---

## Anchor Type Definitions

| Type | Patterns |
|------|----------|
| decision | 决定, 确认, 选择, 采用, decide, confirmed, ✅, completed |
| entity | files (*.py, *.js, etc), tools, commands |
| open_loop | TODO, TBD, 待定, pending, need to |
| constraint | 必须, 不能, 禁止, must, cannot, forbidden |
| tool_state | 执行, 运行, 调用, executed, ran, called |

---

## Sample Audit Requirements

For each candidate sample, record:

```json
{
  "sample_id": "...",
  "admissible": true/false,
  "reason": "...",
  "metrics": {
    "user_message_count": N,
    "assistant_message_count": N,
    "tool_call_count": N,
    "total_text_length": N,
    "anchor_types": N,
    "anchor_breakdown": {...}
  }
}
```

---

## Benchmark Construction Rules

1. **Separate reporting required**
   - `historical_replay` subset
   - `real_main_agent(admissible)` subset
   - Never mix or report only total average

2. **Minimum sample counts**
   - `historical_replay`: 10+
   - `real_main_agent(admissible)`: 15+

3. **Isolation of not_admissible**
   - Keep for data quality records
   - Do not include in evaluation set

---

## Version Control

This policy is FROZEN and must not be modified during the candidate patch validation phase.

Any changes require:
1. Explicit approval
2. Version bump to 1.1
3. Re-validation of all samples

---

**Keywords**: `admissibility` `frozen-policy` `sample-quality` `anchor-validation`
