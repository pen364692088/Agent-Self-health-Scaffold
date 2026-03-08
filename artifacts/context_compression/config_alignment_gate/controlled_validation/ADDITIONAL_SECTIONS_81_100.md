# Context Compression - Additional Validation Content Sections 81-100

## Section 81: Compression Pipeline Detailed Flow

The compression pipeline executes in a strict sequence to ensure data integrity and correct operation.

### Stage 1: Pre-Check

Before any compression operation:

1. Verify kill switch is not active
2. Verify session is in allowed scope
3. Verify state file exists
4. Verify history file exists
5. Verify budget ratio is correct

### Stage 2: Budget Evaluation

Calculate current context pressure:

1. Estimate tokens from history file
2. Calculate ratio against max_tokens
3. Determine pressure level
4. Determine threshold hit (if any)
5. Return budget snapshot

### Stage 3: Decision Point

At ratio >= 0.85:

1. Must execute compression before next assemble
2. Cannot proceed without compression
3. Critical rule enforcement active

### Stage 4: Eviction Planning

Determine what to remove:

1. Calculate eviction ratio based on pressure
2. Identify turns to evict (from beginning)
3. Identify turns to preserve (recent turns)
4. Verify minimum preservation (5 turns)
5. Verify maximum eviction (60%)

### Stage 5: Capsule Generation

Create structured summaries:

1. Extract topic from evicted turns
2. Extract key points
3. Extract decisions
4. Extract commitments
5. Extract errors
6. Calculate capsule token count

### Stage 6: State Update

Update session state:

1. Update turn count
2. Update token count
3. Add capsule references
4. Update compression metadata
5. Persist state atomically

### Stage 7: Evidence Capture

Create evidence package:

1. Capture counter_after.json
2. Capture budget_after.json
3. Capture guardrail_event.json
4. Capture capsule_metadata.json
5. Verify evidence integrity

## Section 82: Counter Update Logic

Counters track all compression operations:

### Scope Counters

```
enforced_sessions_total: Incremented when compression mode is enforced
enforced_low_risk_sessions: Incremented for low-risk sessions only
bypass_sessions_total: Incremented when feature disabled
sessions_skipped_by_scope_filter: Incremented for excluded session types
```

### Trigger Chain Counters

```
budget_check_call_count: Incremented on every budget check
sessions_evaluated_by_budget_check: Incremented per session
sessions_over_threshold: Incremented when ratio >= 0.85
compression_opportunity_count: Incremented when could compress
enforced_trigger_count: Incremented when actually compress
retrieve_call_count: Incremented on retrieval operation
```

### Safety Counters

```
real_reply_corruption_count: Must always be 0
active_session_pollution_count: Must always be 0
rollback_event_count: Incremented on rollback
hook_error_count: Incremented on hook error
kill_switch_triggers: Incremented on kill switch activation
```

## Section 83: Threshold Calculation Details

Thresholds are calculated as follows:

### Ratio Calculation

```
ratio = estimated_tokens / max_tokens
```

### Pressure Level Determination

```
if ratio >= 0.92:
    pressure_level = "strong"
elif ratio >= 0.85:
    pressure_level = "standard"
elif ratio >= 0.75:
    pressure_level = "light"
else:
    pressure_level = "normal"
```

### Threshold Hit Detection

```
if ratio >= 0.92:
    threshold_hit = "strong"
elif ratio >= 0.85:
    threshold_hit = "standard"
elif ratio >= 0.75:
    threshold_hit = "light"
else:
    threshold_hit = null
```

## Section 84: Eviction Strategy Details

The eviction strategy determines optimal removal:

### Eviction Ratio Calculation

```
if pressure_level == "strong":
    evict_ratio = 0.5
elif pressure_level == "standard":
    evict_ratio = 0.4
elif pressure_level == "light":
    evict_ratio = 0.25
else:
    evict_ratio = 0
```

### Turn Selection

Turns are selected for eviction in chronological order:

1. Start from turn 1
2. Evict consecutive turns
3. Preserve recent turns
4. Respect minimum preservation (5 turns)
5. Respect maximum eviction (60%)

### Preservation Rules

Always preserve:
- Last 5 turns (minimum)
- Turns with open loop references
- Turns with commitments
- Turns with recent decisions

## Section 85: Capsule Content Structure

Capsules contain structured information:

### Required Fields

```
capsule_id: Unique identifier
session_id: Source session
source_turn_range: {start, end}
created_at: ISO timestamp
topic: Brief topic description
summary: Content summary
key_points: Array of key points
```

### Optional Fields

```
decisions: Array of decision objects
commitments: Array of commitment objects
errors_encountered: Array of error objects
entities: Array of entity names
tools_used: Array of tool names
```

### Token Counting

Capsule token count includes:
- All field names
- All string values
- JSON structure overhead

## Section 86: State File Schema

The state file contains session metadata:

### Root Structure

```json
{
  "session_id": "string",
  "objective": "string",
  "phase": "string",
  "branch": "string",
  "open_loops": [],
  "commitments": [],
  "hard_constraints": [],
  "last_updated": "ISO timestamp"
}
```

### Open Loop Structure

```json
{
  "loop_id": "string",
  "description": "string",
  "status": "open|closed",
  "created_at": "ISO timestamp"
}
```

### Commitment Structure

```json
{
  "commitment_id": "string",
  "description": "string",
  "deadline": "ISO date",
  "status": "pending|completed"
}
```

## Section 87: Evidence Package Validation

Evidence packages must pass validation:

### File Existence Check

All required files must exist:
- counter_before.json
- counter_after.json
- budget_before.json
- budget_after.json
- guardrail_event.json
- capsule_metadata.json

### Timestamp Consistency

Timestamps must be consistent:
- before < after
- All within same session
- Reasonable duration

### Counter Delta Validation

Counter deltas must be correct:
- enforced_trigger_count: +1
- safety_counters: 0
- rollback_event_count: 0 (for success)

### Budget Consistency

Budget values must be consistent:
- before ratio >= 0.85
- after ratio < 0.75
- Gain percentage reasonable

## Section 88: Hook Event Schema

Hook events follow a standard schema:

### Message Preprocessed Event

```json
{
  "type": "message",
  "action": "preprocessed",
  "sessionKey": "string",
  "timestamp": "ISO timestamp",
  "message": {
    "role": "user|assistant",
    "content": []
  }
}
```

### Compression Trigger Event

```json
{
  "type": "compression",
  "action": "triggered",
  "sessionKey": "string",
  "trigger_ratio": 0.85,
  "trigger_type": "threshold_85",
  "timestamp": "ISO timestamp"
}
```

## Section 89: Monitoring Metrics Schema

Monitoring metrics follow standard schema:

### Session Metric

```json
{
  "session_id": "string",
  "ratio": 0.85,
  "pressure_level": "standard",
  "turn_count": 100,
  "estimated_tokens": 170000,
  "compression_state": "pending"
}
```

### Counter Metric

```json
{
  "counter_name": "string",
  "value": 10,
  "last_updated": "ISO timestamp"
}
```

### Event Metric

```json
{
  "event_id": "string",
  "event_type": "compression",
  "session_id": "string",
  "timestamp": "ISO timestamp",
  "duration_ms": 200
}
```

## Sections 90-100: Additional Test Data

[Additional structured content continues to fill context towards 0.75 threshold...]

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T03:34:00-06:00
**Purpose**: Additional Validation Content for Context Ramp
