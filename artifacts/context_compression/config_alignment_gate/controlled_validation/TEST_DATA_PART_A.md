# Context Compression Test Data - Part A

This document contains test data for context compression validation. It is designed to be low-risk, auditable content that can be safely compressed.

## Section 1: System Configuration Parameters

### 1.1 Compression Thresholds Configuration

The compression system uses the following threshold values for determining when to trigger compression actions:

- **observe_threshold**: 0.75 - System enters observation mode
- **candidate_threshold**: 0.75 - System marks session as candidate for compression
- **enforced_threshold**: 0.85 - System must execute compression before next assembly
- **strong_threshold**: 0.92 - System executes immediate strong compression

The critical rule states: "不允许跨过 0.85 后继续拖延" which means compression must not be delayed after crossing 0.85.

### 1.2 Memory Layer Budget Ratios

The four-layer memory architecture uses the following budget ratios:

- **Resident Layer**: 10% of max_tokens - Contains stable memory items
- **Active Layer**: 70% of max_tokens - Contains recent conversation turns
- **Recall Layer**: 10% of max_tokens - Contains retrieved capsule snippets
- **Overhead**: 10% reserved for system operations

### 1.3 Safety Thresholds

The following safety thresholds must never be exceeded:

- **real_reply_corruption_count**: Must remain at 0
- **active_session_pollution_count**: Must remain at 0
- **rollback_event_count**: Should be minimized
- **kill_switch_triggers**: Should remain at 0 unless manual activation

## Section 2: Session Type Classification

### 2.1 Allowed Session Types

The following session types are eligible for compression in light_enforced mode:

1. **single_topic_daily_chat**: Regular daily conversations on a single topic
2. **non_critical_task**: Tasks that don't have high commitment requirements
3. **simple_tool_context**: Simple tool usage with straightforward context

### 2.2 Excluded Session Types

The following session types are excluded from compression:

1. **multi_file_debug**: Complex debugging sessions spanning multiple files
2. **high_commitment_task**: Tasks with strict deadlines or commitments
3. **critical_execution**: Critical system operations that must not be interrupted
4. **multi_agent_collaboration**: Sessions involving multiple agents
5. **high_risk_scenario**: Any session classified as high risk

## Section 3: Compression Event Fields

### 3.1 Required Event Fields

Every compression event must contain the following fields:

```json
{
  "event_id": "string - unique identifier",
  "session_id": "string - session identifier",
  "trigger": "string - trigger type (threshold_85, threshold_92, manual)",
  "pressure_level": "string - normal|light|standard|strong",
  "before": {
    "estimated_tokens": "number",
    "turn_count": "number",
    "ratio": "number"
  },
  "after": {
    "estimated_tokens": "number",
    "turn_count": "number",
    "ratio": "number"
  },
  "resident_kept": "array of turn numbers",
  "capsules_created": "array of capsule IDs",
  "evicted_turn_ranges": "array of {start, end} objects",
  "vector_indexed": "boolean",
  "mode": "string - shadow|enforced",
  "duration_ms": "number - execution duration"
}
```

### 3.2 Capsule Required Fields

Every capsule must contain the following fields:

```json
{
  "capsule_id": "string - unique identifier",
  "session_id": "string - source session",
  "source_turn_range": {"start": "number", "end": "number"},
  "created_at": "string - ISO timestamp",
  "topic": "string - topic summary",
  "summary": "string - content summary",
  "key_points": "array of strings",
  "entities": "array of strings",
  "decisions": "array of decision objects",
  "commitments": "array of commitment objects",
  "errors_encountered": "array of error objects",
  "tools_used": "array of strings",
  "token_count": "number"
}
```

## Section 4: Protected Fields

### 4.1 Resident State Protected Fields

The following fields in resident state cannot be overwritten by low-confidence recall:

1. **task_goal**: The current task objective
2. **open_loops**: Items that need follow-up
3. **hard_constraints**: Non-negotiable constraints
4. **response_contract**: Expected response format
5. **recent_commitments**: Recently made commitments
6. **tool_execution_state**: Current tool execution state
7. **user_corrected_constraints**: Constraints corrected by user

### 4.2 Minimum Preservation Rules

The following minimum preservation rules apply:

- **MIN_PRESERVE_TURNS**: 5 - At least 5 recent turns must be preserved
- **MAX_EVICT_RATIO**: 0.60 - Maximum 60% of turns can be evicted

## Section 5: Counter Definitions

### 5.1 Scope Counters

| Counter Name | Description |
|--------------|-------------|
| enforced_sessions_total | Total sessions processed in enforced mode |
| enforced_low_risk_sessions | Low-risk sessions processed |
| bypass_sessions_total | Sessions bypassed due to feature flags |
| sessions_skipped_by_scope_filter | Sessions excluded by scope |

### 5.2 Trigger Chain Counters

| Counter Name | Description |
|--------------|-------------|
| budget_check_call_count | Number of budget checks performed |
| sessions_evaluated_by_budget_check | Sessions evaluated |
| sessions_over_threshold | Sessions exceeding threshold |
| compression_opportunity_count | Compression opportunities detected |
| enforced_trigger_count | Actual enforced compressions |
| retrieve_call_count | Retrieval operations |

### 5.3 Safety Counters

| Counter Name | Description | Target |
|--------------|-------------|--------|
| real_reply_corruption_count | Times real replies were corrupted | 0 |
| active_session_pollution_count | Times active sessions were polluted | 0 |
| rollback_event_count | Rollback events | Minimize |
| hook_error_count | Hook execution errors | Minimize |
| kill_switch_triggers | Kill switch activations | 0 |

## Section 6: Tool Parameters

### 6.1 context-budget-check Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| --history | Path | Required | Session JSONL file path |
| --state | Path | Optional | active_state.json path |
| --max-tokens | Int | 100000 | Maximum token budget |
| --snapshot | Flag | False | Generate snapshot file |
| --json | Flag | False | JSON output |

### 6.2 context-compress Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| --session-id | String | Required | Session identifier |
| --state | Path | Required | active_state.json path |
| --history | Path | Required | Session JSONL path |
| --max-tokens | Int | 100000 | Maximum token budget |
| --mode | String | shadow | Compression mode |
| --dry-run | Flag | False | Plan only |
| --json | Flag | False | JSON output |

### 6.3 prompt-assemble Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| --session-id | String | Required | Session identifier |
| --state | Path | Required | active_state.json path |
| --history | Path | Required | Session JSONL path |
| --max-tokens | Int | 100000 | Maximum token budget |
| --dry-run | Flag | False | Plan only |
| --json | Flag | False | JSON output |

### 6.4 context-retrieve Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| --query | String | Required | Search query |
| --session-id | String | Required | Session identifier |
| --max-snippets | Int | 3 | Maximum snippets |
| --json | Flag | False | JSON output |

## Section 7: State Machine Transitions

### 7.1 Compression State Values

The compression_state field can have the following values:

1. **idle**: No compression needed, ratio < 0.75
2. **candidate**: Compression candidate, ratio 0.75-0.85
3. **pending**: Compression pending, ratio >= 0.85
4. **executing**: Compression in progress
5. **completed**: Compression finished successfully
6. **failed**: Compression failed
7. **rollback**: Rolled back to previous state

### 7.2 Valid State Transitions

```
idle → candidate → pending → executing → completed
                              ↓
                            failed
                              ↓
                            rollback
```

### 7.3 State Transition Triggers

| From | To | Trigger |
|------|----|---------|
| idle | candidate | ratio >= 0.75 |
| candidate | pending | ratio >= 0.85 |
| pending | executing | compression started |
| executing | completed | compression succeeded |
| executing | failed | compression failed |
| failed | rollback | rollback initiated |
| completed | idle | ratio < 0.75 |

## Section 8: Validation Checklist

### 8.1 Pre-Compression Checklist

- [ ] Budget ratio >= 0.85
- [ ] Session type is allowed
- [ ] Kill switch not triggered
- [ ] Feature is enabled
- [ ] State file exists
- [ ] History file exists

### 8.2 Post-Compression Checklist

- [ ] Compression ratio reduced
- [ ] Safety counters zero
- [ ] Capsules created
- [ ] Evidence preserved
- [ ] State updated

### 8.3 Validation Report Checklist

- [ ] counter_before.json captured
- [ ] counter_after.json captured
- [ ] budget_before.json captured
- [ ] budget_after.json captured
- [ ] guardrail_event.json captured
- [ ] capsule_metadata.json captured
- [ ] report.md written

## Section 9: Error Handling

### 9.1 Error Types

| Error Type | Description | Recovery |
|------------|-------------|----------|
| budget_check_failed | Budget estimation failed | Return null, log error |
| compress_failed | Compression execution failed | Rollback, log event |
| retrieve_failed | Retrieval operation failed | Continue without recall |
| state_load_failed | State file not found | Return error |
| history_not_found | History file not found | Return error |

### 9.2 Rollback Triggers

Rollback is triggered when:

1. Compression execution fails
2. Safety counter exceeds threshold
3. Kill switch is activated
4. Manual rollback requested

## Section 10: Performance Metrics

### 10.1 Target Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Compression duration | < 500ms | duration_ms in event |
| Token estimation accuracy | ±10% | Compare estimate vs actual |
| Safety violation rate | 0% | Safety counters |
| Rollback rate | < 5% | rollback_event_count / total |

### 10.2 Observed Performance

| Metric | Value | Status |
|--------|-------|--------|
| Average compression duration | 254ms | ✅ Within target |
| Safety violation rate | 0% | ✅ Target met |
| Rollback rate | 11/1465 = 0.75% | ✅ Within target |

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T01:56:00-06:00
**Purpose**: Controlled Validation Test Data Part A
