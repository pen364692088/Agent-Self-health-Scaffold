# Context Compression Test Data - Part B

This document continues the controlled validation test data series.

## Section 11: Compression Event Examples

### 11.1 Successful Compression Event

```json
{
  "event_id": "cmp_20260308_020000",
  "session_id": "controlled_validation_session",
  "trigger": "threshold_85",
  "pressure_level": "standard",
  "before": {
    "estimated_tokens": 170000,
    "turn_count": 100,
    "ratio": 0.85
  },
  "after": {
    "estimated_tokens": 102000,
    "turn_count": 60,
    "ratio": 0.51
  },
  "resident_kept": [61, 62, 63, 64, 65, 66, 67, 68, 69, 70],
  "capsules_created": ["cap_20260308_controlled_1_60"],
  "evicted_turn_ranges": [{"start": 1, "end": 60}],
  "vector_indexed": false,
  "mode": "enforced",
  "duration_ms": 180
}
```

### 11.2 Failed Compression Event

```json
{
  "event_id": "cmp_20260308_020100",
  "session_id": "failed_compression_session",
  "trigger": "threshold_85",
  "pressure_level": "standard",
  "before": {
    "estimated_tokens": 180000,
    "turn_count": 120,
    "ratio": 0.90
  },
  "after": null,
  "resident_kept": [],
  "capsules_created": [],
  "evicted_turn_ranges": [],
  "error": {
    "type": "capsule_generation_failed",
    "message": "Unable to extract key points from turns"
  },
  "mode": "enforced",
  "duration_ms": 50,
  "rollback_initiated": true
}
```

### 11.3 Shadow Mode Event

```json
{
  "event_id": "cmp_20260308_020200",
  "session_id": "shadow_mode_session",
  "trigger": "threshold_85",
  "pressure_level": "standard",
  "before": {
    "estimated_tokens": 175000,
    "turn_count": 110,
    "ratio": 0.875
  },
  "after": {
    "estimated_tokens": 105000,
    "turn_count": 66,
    "ratio": 0.525
  },
  "resident_kept": [67, 68, 69, 70, 71],
  "capsules_created": ["cap_shadow_20260308_1_66"],
  "evicted_turn_ranges": [{"start": 1, "end": 66}],
  "mode": "shadow",
  "duration_ms": 120,
  "message": "Shadow mode: compression planned but not executed"
}
```

## Section 12: Capsule Content Examples

### 12.1 Decision Capsule

```json
{
  "capsule_id": "cap_decision_example",
  "session_id": "session_001",
  "source_turn_range": {"start": 1, "end": 30},
  "created_at": "2026-03-08T02:00:00-06:00",
  "topic": "Technical architecture decisions",
  "summary": "The user made several key architectural decisions for the new system. PostgreSQL was chosen for the database due to JSON support and performance characteristics. React was selected for the frontend based on team familiarity. Node.js was chosen for the backend to maintain JavaScript consistency across the stack.",
  "key_points": [
    "Decision: Use PostgreSQL for database",
    "Decision: Use React for frontend",
    "Decision: Use Node.js for backend",
    "Rationale: JavaScript full stack consistency",
    "Rationale: Team familiarity with React",
    "Rationale: PostgreSQL JSON support"
  ],
  "entities": ["PostgreSQL", "React", "Node.js", "JavaScript"],
  "decisions": [
    {
      "id": "dec_arch_001",
      "description": "Database selection",
      "choice": "PostgreSQL",
      "rationale": "Better JSON support and proven performance",
      "turn": 5,
      "confidence": 0.95
    },
    {
      "id": "dec_arch_002",
      "description": "Frontend framework",
      "choice": "React",
      "rationale": "Team familiarity and large ecosystem",
      "turn": 8,
      "confidence": 0.90
    },
    {
      "id": "dec_arch_003",
      "description": "Backend runtime",
      "choice": "Node.js",
      "rationale": "JavaScript full stack consistency",
      "turn": 10,
      "confidence": 0.85
    }
  ],
  "commitments": [],
  "errors_encountered": [],
  "tools_used": ["write", "exec", "read"],
  "token_count": 1500
}
```

### 12.2 Commitment Capsule

```json
{
  "capsule_id": "cap_commitment_example",
  "session_id": "session_002",
  "source_turn_range": {"start": 31, "end": 60},
  "created_at": "2026-03-08T02:05:00-06:00",
  "topic": "Project commitments and deadlines",
  "summary": "The user committed to several deliverables during this conversation phase. The API implementation must be completed by Friday, March 12th. Unit tests for the authentication module are due by March 10th. Documentation is expected by March 15th.",
  "key_points": [
    "Commitment: Complete API by Friday (2026-03-12)",
    "Commitment: Write unit tests for auth module (2026-03-10)",
    "Commitment: Complete documentation (2026-03-15)",
    "Priority: API implementation is highest priority",
    "Blocker: Waiting on database schema approval"
  ],
  "entities": ["API", "Authentication", "Unit Tests", "Documentation"],
  "decisions": [],
  "commitments": [
    {
      "id": "com_proj_001",
      "description": "Complete API implementation",
      "deadline": "2026-03-12",
      "turn": 35,
      "priority": "high",
      "status": "in_progress"
    },
    {
      "id": "com_proj_002",
      "description": "Write unit tests for auth module",
      "deadline": "2026-03-10",
      "turn": 42,
      "priority": "medium",
      "status": "pending"
    },
    {
      "id": "com_proj_003",
      "description": "Complete API documentation",
      "deadline": "2026-03-15",
      "turn": 55,
      "priority": "low",
      "status": "pending"
    }
  ],
  "errors_encountered": [],
  "tools_used": ["write", "edit"],
  "token_count": 1200
}
```

### 12.3 Error Resolution Capsule

```json
{
  "capsule_id": "cap_error_example",
  "session_id": "session_003",
  "source_turn_range": {"start": 61, "end": 90},
  "created_at": "2026-03-08T02:10:00-06:00",
  "topic": "Error resolution and debugging",
  "summary": "Several errors were encountered and resolved during this phase. A CORS error was fixed by adding cors middleware. A database connection error was resolved by updating the connection string. An authentication issue was fixed by correcting the JWT secret configuration.",
  "key_points": [
    "Error: CORS error during API testing",
    "Resolution: Added cors middleware to Express",
    "Error: Database connection timeout",
    "Resolution: Updated connection string with correct host",
    "Error: JWT authentication failing",
    "Resolution: Fixed JWT secret in environment variables"
  ],
  "entities": ["CORS", "Express", "Database", "JWT", "Authentication"],
  "decisions": [],
  "commitments": [],
  "errors_encountered": [
    {
      "id": "err_001",
      "description": "CORS error during API testing",
      "error_type": "cors_policy_error",
      "resolution": "Added cors middleware to Express app",
      "turn": 65,
      "resolved": true,
      "resolution_turn": 67
    },
    {
      "id": "err_002",
      "description": "Database connection timeout",
      "error_type": "connection_error",
      "resolution": "Updated connection string with correct host and port",
      "turn": 72,
      "resolved": true,
      "resolution_turn": 74
    },
    {
      "id": "err_003",
      "description": "JWT authentication failing",
      "error_type": "authentication_error",
      "resolution": "Fixed JWT secret in environment variables",
      "turn": 80,
      "resolved": true,
      "resolution_turn": 82
    }
  ],
  "tools_used": ["exec", "read", "edit"],
  "token_count": 1800
}
```

## Section 13: Budget Trace Examples

### 13.1 Full Budget Trace

```jsonl
{"timestamp":"2026-03-08T02:00:00-06:00","turn":1,"estimated_tokens":5000,"max_tokens":200000,"ratio":0.025,"pressure_level":"normal","compression_state":"idle"}
{"timestamp":"2026-03-08T02:01:00-06:00","turn":10,"estimated_tokens":25000,"max_tokens":200000,"ratio":0.125,"pressure_level":"normal","compression_state":"idle"}
{"timestamp":"2026-03-08T02:02:00-06:00","turn":20,"estimated_tokens":50000,"max_tokens":200000,"ratio":0.25,"pressure_level":"normal","compression_state":"idle"}
{"timestamp":"2026-03-08T02:03:00-06:00","turn":30,"estimated_tokens":75000,"max_tokens":200000,"ratio":0.375,"pressure_level":"normal","compression_state":"idle"}
{"timestamp":"2026-03-08T02:04:00-06:00","turn":40,"estimated_tokens":100000,"max_tokens":200000,"ratio":0.50,"pressure_level":"normal","compression_state":"idle"}
{"timestamp":"2026-03-08T02:05:00-06:00","turn":50,"estimated_tokens":125000,"max_tokens":200000,"ratio":0.625,"pressure_level":"normal","compression_state":"idle"}
{"timestamp":"2026-03-08T02:06:00-06:00","turn":60,"estimated_tokens":140000,"max_tokens":200000,"ratio":0.70,"pressure_level":"light","compression_state":"candidate"}
{"timestamp":"2026-03-08T02:07:00-06:00","turn":70,"estimated_tokens":155000,"max_tokens":200000,"ratio":0.775,"pressure_level":"light","compression_state":"candidate"}
{"timestamp":"2026-03-08T02:08:00-06:00","turn":80,"estimated_tokens":165000,"max_tokens":200000,"ratio":0.825,"pressure_level":"light","compression_state":"candidate"}
{"timestamp":"2026-03-08T02:09:00-06:00","turn":85,"estimated_tokens":170000,"max_tokens":200000,"ratio":0.85,"pressure_level":"standard","compression_state":"pending"}
{"timestamp":"2026-03-08T02:09:30-06:00","turn":85,"estimated_tokens":170000,"max_tokens":200000,"ratio":0.85,"pressure_level":"standard","compression_state":"executing"}
{"timestamp":"2026-03-08T02:09:31-06:00","turn":85,"estimated_tokens":102000,"max_tokens":200000,"ratio":0.51,"pressure_level":"normal","compression_state":"completed"}
```

### 13.2 Budget Trace with Compression Failure

```jsonl
{"timestamp":"2026-03-08T02:10:00-06:00","turn":1,"estimated_tokens":10000,"max_tokens":200000,"ratio":0.05,"pressure_level":"normal","compression_state":"idle"}
{"timestamp":"2026-03-08T02:15:00-06:00","turn":50,"estimated_tokens":100000,"max_tokens":200000,"ratio":0.50,"pressure_level":"normal","compression_state":"idle"}
{"timestamp":"2026-03-08T02:20:00-06:00","turn":80,"estimated_tokens":160000,"max_tokens":200000,"ratio":0.80,"pressure_level":"light","compression_state":"candidate"}
{"timestamp":"2026-03-08T02:25:00-06:00","turn":90,"estimated_tokens":180000,"max_tokens":200000,"ratio":0.90,"pressure_level":"standard","compression_state":"pending"}
{"timestamp":"2026-03-08T02:25:30-06:00","turn":90,"estimated_tokens":180000,"max_tokens":200000,"ratio":0.90,"pressure_level":"standard","compression_state":"executing"}
{"timestamp":"2026-03-08T02:25:31-06:00","turn":90,"estimated_tokens":180000,"max_tokens":200000,"ratio":0.90,"pressure_level":"standard","compression_state":"failed","error":"capsule_generation_failed"}
{"timestamp":"2026-03-08T02:25:32-06:00","turn":90,"estimated_tokens":180000,"max_tokens":200000,"ratio":0.90,"pressure_level":"standard","compression_state":"rollback"}
```

## Section 14: Guardrail Event Examples

### 14.1 Guardrail 2A: Threshold Enforcement

```json
{
  "guardrail_id": "2A",
  "guardrail_name": "budget_threshold_enforcement",
  "trigger_condition": "budget_ratio >= 0.85",
  "observed_values": {
    "budget_ratio": 0.85,
    "estimated_tokens": 170000,
    "max_tokens": 200000,
    "compression_state": "pending",
    "session_type": "single_topic_daily_chat"
  },
  "action_taken": "forced_standard_compression",
  "result": {
    "success": true,
    "post_compression_ratio": 0.51,
    "capsules_created": 1,
    "turns_evicted": 60,
    "duration_ms": 180
  },
  "session_id": "controlled_validation_session",
  "turn_number": 85,
  "timestamp": "2026-03-08T02:09:00-06:00",
  "pre_assemble_compliant": true
}
```

### 14.2 Guardrail 2B: Kill Switch Activation

```json
{
  "guardrail_id": "2B",
  "guardrail_name": "kill_switch_protection",
  "trigger_condition": "manual_activation",
  "observed_values": {
    "safety_counter_exceeded": false,
    "manual_trigger": true,
    "triggered_by": "user",
    "reason": "Testing kill switch functionality"
  },
  "action_taken": "disable_compression",
  "result": {
    "compression_disabled": true,
    "active_sessions_preserved": true,
    "pending_compressions_cancelled": 0
  },
  "timestamp": "2026-03-08T02:30:00-06:00"
}
```

### 14.3 Guardrail 2C: Safety Counter Protection

```json
{
  "guardrail_id": "2C",
  "guardrail_name": "safety_counter_protection",
  "trigger_condition": "safety_counter > 0",
  "observed_values": {
    "real_reply_corruption_count": 0,
    "active_session_pollution_count": 0,
    "rollback_event_count": 1,
    "threshold_exceeded": false
  },
  "action_taken": "continue_monitoring",
  "result": {
    "safety_status": "ok",
    "compression_allowed": true
  },
  "timestamp": "2026-03-08T02:35:00-06:00"
}
```

## Section 15: Counter State Transitions

### 15.1 Before Compression

```json
{
  "enforced_sessions_total": 0,
  "enforced_low_risk_sessions": 5,
  "bypass_sessions_total": 0,
  "sessions_skipped_by_scope_filter": 0,
  "budget_check_call_count": 100,
  "sessions_evaluated_by_budget_check": 100,
  "sessions_over_threshold": 5,
  "compression_opportunity_count": 5,
  "enforced_trigger_count": 0,
  "retrieve_call_count": 0,
  "real_reply_corruption_count": 0,
  "active_session_pollution_count": 0,
  "rollback_event_count": 0,
  "hook_error_count": 0,
  "kill_switch_triggers": 0
}
```

### 15.2 After Compression

```json
{
  "enforced_sessions_total": 1,
  "enforced_low_risk_sessions": 5,
  "bypass_sessions_total": 0,
  "sessions_skipped_by_scope_filter": 0,
  "budget_check_call_count": 101,
  "sessions_evaluated_by_budget_check": 101,
  "sessions_over_threshold": 6,
  "compression_opportunity_count": 6,
  "enforced_trigger_count": 1,
  "retrieve_call_count": 1,
  "real_reply_corruption_count": 0,
  "active_session_pollution_count": 0,
  "rollback_event_count": 0,
  "hook_error_count": 0,
  "kill_switch_triggers": 0
}
```

### 15.3 Counter Delta Analysis

| Counter | Before | After | Delta | Status |
|---------|--------|-------|-------|--------|
| enforced_sessions_total | 0 | 1 | +1 | ✅ |
| enforced_trigger_count | 0 | 1 | +1 | ✅ |
| real_reply_corruption_count | 0 | 0 | 0 | ✅ |
| active_session_pollution_count | 0 | 0 | 0 | ✅ |
| rollback_event_count | 0 | 0 | 0 | ✅ |

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T03:00:00-06:00
**Purpose**: Controlled Validation Test Data Part B
