# Context Compression Technical Specification v2.0

## 1. Architecture Overview

The context compression system implements a four-layer memory architecture designed to preserve critical information while reducing token usage for long-running sessions.

### 1.1 Memory Layers

#### Layer 1: Stable Memory
Stable memory contains persistent configuration and rules that rarely change:
- User preferences
- System configuration
- Agent personality and boundaries
- Long-term project context

#### Layer 2: Working Memory
Working memory contains session-specific state:
- Current objective
- Current phase
- Active branches
- Open loops
- Recent commitments
- Blockers

#### Layer 3: Capsule Memory
Capsule memory contains compressed summaries of evicted conversation turns:
- Topic identification
- Key decisions
- Action items
- Commitments made
- Errors encountered

#### Layer 4: Retrieval Memory
Retrieval memory provides on-demand access to historical information:
- Vector search over capsules
- Semantic similarity matching
- Anchor-based retrieval
- Context-aware recall

### 1.2 Compression Pipeline

The compression pipeline executes in the following order:

1. **Budget Check**: Estimate current token usage and calculate ratio
2. **Pressure Assessment**: Determine if compression is needed based on thresholds
3. **Eviction Planning**: Determine which turns can be safely evicted
4. **Capsule Generation**: Create compressed summaries of evicted content
5. **Context Trimming**: Remove evicted turns from active context
6. **State Update**: Update working memory with compression metadata

## 2. Threshold Configuration

### 2.1 Pressure Levels

| Level | Ratio Range | Action |
|-------|-------------|--------|
| Normal | < 0.75 | Observe only |
| Light | 0.75 - 0.85 | Candidate for compression |
| Standard | 0.85 - 0.92 | Pre-assemble compression required |
| Strong | >= 0.92 | Immediate strong compression |

### 2.2 Critical Rules

1. **No Delay After 0.85**: Once budget ratio reaches 0.85, compression MUST execute before the next prompt assembly
2. **Minimum Preservation**: At least 5 recent turns must be preserved
3. **Maximum Eviction**: No more than 60% of turns can be evicted in a single compression cycle
4. **Protected Fields**: The following fields cannot be overwritten by low-confidence recalls:
   - task_goal
   - open_loops
   - hard_constraints
   - response_contract
   - recent_commitments
   - tool_execution_state
   - user_corrected_constraints

## 3. Hook Integration

### 3.1 Hook Timing

The compression hook executes on `message.preprocessed` events:

```
Message Received
    ↓
Hook: message.preprocessed
    ↓
Budget Check
    ↓
Compression Decision (if ratio >= 0.85)
    ↓
Prompt Assembly
    ↓
LLM Call
```

### 3.2 Hook Configuration

```json
{
  "name": "context-compression-shadow",
  "events": ["message:preprocessed"],
  "mode": "light_enforced",
  "scope": "low_risk"
}
```

## 4. Tool Chain

### 4.1 context-budget-check

Estimates token usage from session history and state files.

**Parameters**:
- `--history`: Path to session JSONL file
- `--state`: Path to active_state.json (optional)
- `--max-tokens`: Maximum token budget (default: 200000)
- `--snapshot`: Generate budget snapshot file

**Output**:
```json
{
  "estimated_tokens": 85000,
  "max_tokens": 200000,
  "ratio": 0.425,
  "pressure_level": "normal",
  "threshold_hit": null,
  "snapshot_id": "snap_20260308_014900"
}
```

### 4.2 context-compress

Executes compression based on pressure level.

**Parameters**:
- `--session-id`: Session identifier
- `--state`: Path to active_state.json
- `--history`: Path to session JSONL file
- `--max-tokens`: Maximum token budget
- `--mode`: Compression mode (shadow|enforced)
- `--dry-run`: Plan only, don't write files

**Output**:
```json
{
  "compression_triggered": true,
  "mode": "enforced",
  "pressure_level": "standard",
  "plan": {
    "evict_turns": [1, 2, 3, ...],
    "evicted_ranges": [{"start": 1, "end": 50}],
    "create_capsules": ["cap_001"],
    "preserve_resident": ["task_goal", "open_loops"]
  },
  "before": {"tokens": 170000, "turns": 100, "ratio": 0.85},
  "after": {"tokens": 100000, "turns": 50, "ratio": 0.50}
}
```

### 4.3 prompt-assemble

Assembles prompt from multiple layers with compression integration.

**Parameters**:
- `--session-id`: Session identifier
- `--state`: Path to active_state.json
- `--history`: Path to session JSONL file
- `--max-tokens`: Maximum token budget
- `--dry-run`: Output plan only

**Light Enforced Mode**:
- Triggers when `ratio >= 0.85`
- Calls `context-compress` before assembly
- Returns compression event ID

### 4.4 context-retrieve

Performs anchor-aware retrieval from capsule memory.

**Parameters**:
- `--query`: Search query
- `--session-id`: Session identifier
- `--max-snippets`: Maximum snippets to return

**Output**:
```json
{
  "snippets": [
    {
      "capsule_id": "cap_001",
      "relevance": 0.95,
      "content": {...}
    }
  ]
}
```

## 5. Capsule Schema

### 5.1 Capsule Structure

```json
{
  "capsule_id": "cap_20260308_session_turns_1_50",
  "session_id": "session_001",
  "source_turn_range": {"start": 1, "end": 50},
  "created_at": "2026-03-08T01:50:00-06:00",
  "topic": "Configuration and setup discussion",
  "summary": "User configured the system with the following parameters...",
  "key_points": [
    "Decision: Use PostgreSQL for database",
    "Commitment: Complete API by Friday"
  ],
  "entities": ["PostgreSQL", "API", "Friday"],
  "decisions": [
    {
      "id": "dec_001",
      "description": "Database selection",
      "choice": "PostgreSQL",
      "rationale": "Better JSON support"
    }
  ],
  "commitments": [
    {
      "id": "com_001",
      "description": "Complete API",
      "deadline": "2026-03-12"
    }
  ],
  "errors_encountered": [],
  "tools_used": ["write", "exec"],
  "token_count": 500
}
```

### 5.2 Capsule Generation

Capsules are generated using the `capsule-builder` tool:

**Parameters**:
- `--input`: Session JSONL file
- `--session-id`: Session identifier
- `--start`: Start turn number
- `--end`: End turn number
- `--output`: Output directory
- `--no-llm`: Use simple extraction (faster)

## 6. Safety Mechanisms

### 6.1 Kill Switch

The kill switch immediately disables compression:

```markdown
# KILL_SWITCH.md
KILL_SWITCH_TRIGGERED: true
Reason: Compression corrupting context
Timestamp: 2026-03-08T01:00:00-06:00
```

**Location**: `artifacts/context_compression/mainline_shadow/KILL_SWITCH.md`

### 6.2 Replay Guardrail

The replay guardrail prevents corruption of real replies:
- Shadow mode: Compression planned but not executed
- Enforced mode: Compression executed with audit trail
- Rollback capability: Previous state can be restored

### 6.3 Scope Filtering

Only low-risk sessions are processed:

**Allowed**:
- single_topic_daily_chat
- non_critical_task
- simple_tool_context

**Excluded**:
- multi_file_debug
- high_commitment_task
- critical_execution
- multi_agent_collaboration
- high_risk_scenario

## 7. Counter Metrics

### 7.1 Scope Metrics

| Counter | Description |
|---------|-------------|
| `enforced_sessions_total` | Total sessions processed in enforced mode |
| `enforced_low_risk_sessions` | Low-risk sessions processed |
| `bypass_sessions_total` | Sessions bypassed due to feature flags |
| `sessions_skipped_by_scope_filter` | Sessions excluded by scope |

### 7.2 Trigger Chain Metrics

| Counter | Description |
|---------|-------------|
| `budget_check_call_count` | Number of budget checks performed |
| `sessions_evaluated_by_budget_check` | Sessions evaluated |
| `sessions_over_threshold` | Sessions exceeding threshold |
| `compression_opportunity_count` | Compression opportunities detected |
| `enforced_trigger_count` | Actual enforced compressions |
| `retrieve_call_count` | Retrieval operations |

### 7.3 Safety Metrics

| Counter | Description |
|---------|-------------|
| `real_reply_corruption_count` | Times real replies were corrupted |
| `active_session_pollution_count` | Times active sessions were polluted |
| `rollback_event_count` | Rollback events |
| `hook_error_count` | Hook execution errors |
| `kill_switch_triggers` | Kill switch activations |

### 7.4 Continuity Metrics

| Counter | Description |
|---------|-------------|
| `old_topic_continuity_signal` | Signal for topic continuity |
| `open_loop_preservation_signal` | Signal for loop preservation |
| `user_correction_stability_signal` | Signal for user corrections |

## 8. Event Logging

### 8.1 Compression Event Schema

```json
{
  "event_id": "cmp_20260308_015000",
  "session_id": "session_001",
  "trigger": "threshold_85",
  "pressure_level": "standard",
  "before": {
    "estimated_tokens": 170000,
    "turn_count": 100,
    "ratio": 0.85
  },
  "after": {
    "estimated_tokens": 100000,
    "turn_count": 50,
    "ratio": 0.50
  },
  "resident_kept": [51, 52, 53, 54, 55],
  "capsules_created": ["cap_001"],
  "evicted_turn_ranges": [{"start": 1, "end": 50}],
  "vector_indexed": false,
  "mode": "enforced",
  "duration_ms": 250
}
```

### 8.2 Event Storage

- **File**: `artifacts/compression_events/events.jsonl`
- **Format**: JSONL (one event per line)
- **Retention**: 7 days default

## 9. Rollback Procedure

### 9.1 Automatic Rollback

Rollback is triggered when:
- Compression fails
- Safety counter exceeds threshold
- Kill switch is activated

### 9.2 Manual Rollback

```bash
# Restore previous handler
cp handler.ts.backup handler.ts

# Reset counters
echo '{"enforced_counters": {...}}' > light_enforced_counters.json

# Clear recent events
rm artifacts/compression_events/events_*.json
```

## 10. Validation Checklist

### 10.1 Pre-Deployment

- [ ] All tools self-test pass
- [ ] Kill switch verified
- [ ] Scope filter configured
- [ ] Thresholds validated
- [ ] Counter baseline established

### 10.2 Post-Compression

- [ ] Compression ratio reduced
- [ ] Safety counters zero
- [ ] Capsules created successfully
- [ ] Evidence preserved
- [ ] Session continuity maintained

### 10.3 Natural Validation

- [ ] Natural triggers observed
- [ ] Timing appropriate
- [ ] No user-visible disruption
- [ ] Evidence chain complete

## 11. Configuration Reference

### 11.1 runtime_compression_policy.json

```json
{
  "policy_version": "1.0",
  "context_window": 200000,
  "thresholds": {
    "observe": 0.75,
    "candidate": 0.75,
    "enforced": 0.85,
    "strong": 0.92
  },
  "critical_rule": "不允许跨过 0.85 后继续拖延",
  "execution_point": "prompt_assemble",
  "layers": {
    "resident_budget_ratio": 0.10,
    "active_budget_ratio": 0.70,
    "recall_budget_ratio": 0.10
  },
  "safety": {
    "min_preserve_turns": 5,
    "max_evict_ratio": 0.60,
    "protected_fields": [
      "task_goal",
      "open_loops",
      "hard_constraints",
      "response_contract"
    ]
  }
}
```

### 11.2 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CONTEXT_COMPRESSION_ENABLED` | Enable/disable compression | `1` |
| `CONTEXT_COMPRESSION_MODE` | Compression mode | `shadow` |
| `OPENCLAW_WORKSPACE` | Workspace path | `~/.openclaw/workspace` |

## 12. Troubleshooting

### 12.1 Common Issues

**Issue**: Compression not triggering
- Check threshold configuration
- Verify mode is `light_enforced`
- Check kill switch status

**Issue**: Compression failing
- Verify tool parameters
- Check file paths
- Review error logs

**Issue**: Context corruption
- Activate kill switch
- Review rollback events
- Check safety counters

### 12.2 Debug Commands

```bash
# Check current budget
context-budget-check --history <session> --max-tokens 200000

# Test compression
context-compress --session-id test --state <state> --history <history> --dry-run

# View counters
cat light_enforced_counters.json | jq '.enforced_counters'

# Check events
tail -10 artifacts/compression_events/events.jsonl
```

---

**Document Version**: 2.0
**Last Updated**: 2026-03-08T01:50:00-06:00
**Status**: CONTROLLED VALIDATION SPEC
