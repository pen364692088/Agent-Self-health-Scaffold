# Context Compression - Final Push Documentation Part 2

## Complete System Documentation - Part 2

### Implementation Details

The implementation follows a layered architecture:

**Layer 1: Hook Handler (TypeScript)**
- Listens for message.preprocessed events
- Coordinates compression pipeline
- Manages tool execution
- Handles errors and recovery

**Layer 2: Python Tools**
- context-budget-check: Token estimation
- context-compress: Compression execution
- prompt-assemble: Prompt building
- context-retrieve: Capsule retrieval

**Layer 3: State Management**
- Session state persistence
- Counter management
- Evidence storage
- Configuration management

### Tool Chain Details

**context-budget-check**
```bash
--history <file>    # Session JSONL file
--max-tokens <n>    # Maximum token budget
--json              # JSON output
```

**context-compress**
```bash
--session-id <id>   # Session identifier
--state <file>      # State file path
--history <file>    # History file path
--max-tokens <n>    # Maximum token budget
--mode <mode>       # shadow|enforced
--json              # JSON output
```

**prompt-assemble**
```bash
--session-id <id>   # Session identifier
--state <file>      # State file path
--history <file>    # History file path
--max-tokens <n>    # Maximum token budget
--dry-run           # Plan only
--json              # JSON output
```

**context-retrieve**
```bash
--query <text>      # Search query
--session-id <id>   # Session identifier
--max-snippets <n>  # Maximum results
--json              # JSON output
```

### Counter Schema

Complete counter schema:

```json
{
  "enforced_counters": {
    "enforced_sessions_total": 0,
    "enforced_low_risk_sessions": 0,
    "bypass_sessions_total": 0,
    "sessions_skipped_by_scope_filter": 0,
    "budget_check_call_count": 0,
    "sessions_evaluated_by_budget_check": 0,
    "sessions_over_threshold": 0,
    "compression_opportunity_count": 0,
    "enforced_trigger_count": 0,
    "retrieve_call_count": 0,
    "real_reply_corruption_count": 0,
    "active_session_pollution_count": 0,
    "rollback_event_count": 0,
    "hook_error_count": 0,
    "kill_switch_triggers": 0
  }
}
```

### Event Schema

Complete event schema:

```json
{
  "event_id": "string",
  "session_id": "string",
  "trigger": "threshold_85|threshold_92|manual",
  "pressure_level": "normal|light|standard|strong",
  "before": {
    "estimated_tokens": 0,
    "turn_count": 0,
    "ratio": 0.0
  },
  "after": {
    "estimated_tokens": 0,
    "turn_count": 0,
    "ratio": 0.0
  },
  "resident_kept": [],
  "capsules_created": [],
  "evicted_turn_ranges": [],
  "mode": "shadow|enforced",
  "duration_ms": 0
}
```

### Capsule Schema

Complete capsule schema:

```json
{
  "capsule_id": "string",
  "session_id": "string",
  "source_turn_range": {
    "start": 0,
    "end": 0
  },
  "created_at": "ISO timestamp",
  "topic": "string",
  "summary": "string",
  "key_points": [],
  "entities": [],
  "decisions": [],
  "commitments": [],
  "errors_encountered": [],
  "tools_used": [],
  "token_count": 0
}
```

### Guardrail Event Schema

Complete guardrail event schema:

```json
{
  "guardrail_id": "2A",
  "guardrail_name": "budget_threshold_enforcement",
  "trigger_condition": "budget_ratio >= 0.85",
  "observed_values": {
    "budget_ratio": 0.0,
    "estimated_tokens": 0,
    "max_tokens": 0,
    "compression_state": "string"
  },
  "action_taken": "forced_standard_compression",
  "result": {
    "success": true,
    "post_compression_ratio": 0.0
  },
  "session_id": "string",
  "timestamp": "ISO timestamp"
}
```

### State File Schema

Complete state file schema:

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

### Evidence Package Validation

Validation rules for evidence package:

**File Existence**:
- All 6 required files must exist
- No missing or corrupted files

**Timestamp Consistency**:
- before timestamps < after timestamps
- All within same session
- Reasonable duration between

**Counter Validation**:
- enforced_trigger_count delta = +1
- Safety counters remain 0
- No unexpected changes

**Budget Validation**:
- before ratio >= 0.85
- after ratio < 0.75
- Gain percentage reasonable

### Error Handling Matrix

Complete error handling matrix:

| Error | Severity | Action | Recovery |
|-------|----------|--------|----------|
| state_not_found | Critical | Halt | Restore backup |
| history_corrupted | Critical | Halt | Regenerate |
| timeout | High | Retry | Backoff retry |
| memory_exceeded | High | Reduce load | Free memory |
| evidence_missing | Medium | Regenerate | Re-capture |
| config_invalid | Medium | Use default | Fix config |

### Rollback Procedures

Complete rollback procedures:

**Automatic Rollback Triggers**:
1. Compression execution failure
2. State corruption detected
3. Safety counter violation
4. Kill switch activation

**Rollback Steps**:
1. Stop current operation
2. Create backup of corrupted state
3. Restore from last good backup
4. Verify restoration integrity
5. Update rollback counter
6. Log rollback event
7. Notify monitoring

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T03:56:00-06:00
**Purpose**: Final Push Documentation Part 2
