# Sample Admission Rules Effectiveness Report

**Date**: 2026-03-07 03:45 CST
**Purpose**: Document the impact of sample admission rules on benchmark quality

---

## Problem Identified

**v2 Benchmark** had 5 `real_main_agent` samples that were **heartbeat-only**:
- `text_hash: null` - no actual text content
- `sent_events: [{type: "time_passed"}]` - only time passing events
- No user messages, no assistant responses, no tool calls

**Result**:
- Baseline score: 0.000
- Anchor score: 0.230 (only time anchors)
- No meaningful anchors extracted

---

## Admission Rules Implemented

```yaml
admission_rules:
  min_user_messages: 2
  min_assistant_messages: 2
  min_text_length: 500
  min_anchor_types: 2
  exclude_heartbeat_only: true
```

### Sample Check Logic

```python
# Heartbeat detection
if user_message_count == 0:
    reject("heartbeat_only")

# Content quality
if total_text_length < 500:
    reject("insufficient_content")

# Anchor potential
anchor_types = sum([
    has_decision_anchor,
    has_entity_anchor,
    has_open_loop_anchor,
    has_constraint_anchor,
    has_tool_state_anchor
])
if anchor_types < 2:
    reject("no_anchor_potential")
```

---

## Results Comparison

### v2 (Heartbeat-Only Samples)

| Metric | Value |
|--------|-------|
| Total samples | 5 |
| Avg baseline | 0.000 |
| Avg anchor | 0.230 |
| Delta | +0.230 |
| >=0.75 | 0/5 |

**Anchor counts** (typical):
```json
{
  "decision": 0,
  "entity": 0,
  "time": 10,
  "open_loop": 0,
  "constraint": 0,
  "tool_state": 0
}
```

### v3 (Real Samples with Admission Rules)

| Metric | Value |
|--------|-------|
| Total samples | 5 |
| Avg baseline | 0.299 |
| Avg anchor | 1.000 |
| Delta | +0.701 |
| >=0.75 | 5/5 |

**Anchor counts** (typical):
```json
{
  "decision": 10,
  "entity": 15,
  "time": 10,
  "open_loop": 10,
  "constraint": 10,
  "tool_state": 15
}
```

---

## Key Findings

1. **Heartbeat-only samples cannot be used for anchor evaluation**
   - They only have timestamps, no actual content
   - Baseline score is 0.000 (no topic keywords)
   - Anchor extraction returns only time anchors

2. **Real samples with admission rules show strong anchor potential**
   - Multiple anchor types extracted (decision, entity, constraint, etc.)
   - Baseline score reflects actual topic coverage
   - Anchor-aware retrieve shows significant improvement (+0.701)

3. **Admission rules are critical for benchmark validity**
   - Without filtering, benchmark results are misleading
   - v2 showed "improvement" (+0.230) but on meaningless data
   - v3 shows true performance on real conversations

---

## Recommendation

**Proceed to prompt assemble anchor injection experiment**

- Admission rules now ensure sample quality
- Real samples demonstrate anchor extraction works
- Next step: inject anchors explicitly into prompt assembly

---

## Files Created

- `sample_admission_rules.py` - Admission rules implementation
- `real_session_candidates.json` - Scanned real sessions
- `old_topic_micro_benchmark_v3.json` - Benchmark with real samples
- `run_benchmark_v3.py` - Benchmark runner with admission checks
- `ab_benchmark_v3_results.json` - Results

---

**Next Phase**: Prompt Assemble Anchor Injection (only if v3 delta < 0.3, but we got +0.701, so anchor-aware retrieve alone is sufficient for real samples)
