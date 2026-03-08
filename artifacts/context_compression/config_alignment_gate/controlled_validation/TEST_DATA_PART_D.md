# Context Compression Test Data - Part D

Additional test data for controlled validation with extended examples.

## Section 20: Performance Benchmarks

### 20.1 Token Estimation Benchmarks

| Content Size | Estimated Tokens | Actual Tokens | Accuracy |
|--------------|------------------|---------------|----------|
| 1000 chars | 250 | 267 | 94% |
| 10000 chars | 2500 | 2589 | 97% |
| 100000 chars | 25000 | 24156 | 97% |
| 500000 chars | 125000 | 128432 | 97% |
| 1000000 chars | 250000 | 256789 | 97% |

### 20.2 Compression Duration Benchmarks

| Turn Count | Token Count Before | Token Count After | Duration (ms) |
|------------|--------------------|-------------------|---------------|
| 50 | 50000 | 30000 | 120 |
| 100 | 100000 | 60000 | 180 |
| 200 | 200000 | 120000 | 250 |
| 500 | 500000 | 300000 | 450 |
| 1000 | 1000000 | 600000 | 800 |

### 20.3 Memory Usage Benchmarks

| Operation | Memory Before (MB) | Memory After (MB) | Delta |
|-----------|--------------------|-------------------|-------|
| Budget Check | 50 | 52 | +2 |
| Compression | 52 | 55 | +3 |
| Capsule Generation | 55 | 60 | +5 |
| Retrieval | 60 | 62 | +2 |

## Section 21: Error Handling Examples

### 21.1 Error: State File Not Found

```json
{
  "error": {
    "type": "file_not_found",
    "message": "State file not found: /path/to/active_state.json",
    "resolution": "Create state file or verify path"
  }
}
```

### 21.2 Error: History File Corrupted

```json
{
  "error": {
    "type": "parse_error",
    "message": "Failed to parse history file: Invalid JSON at line 42",
    "resolution": "Repair or regenerate history file"
  }
}
```

### 21.3 Error: Tool Execution Timeout

```json
{
  "error": {
    "type": "timeout",
    "message": "Tool execution exceeded 30 second timeout",
    "tool": "context-compress",
    "resolution": "Reduce session size or increase timeout"
  }
}
```

### 21.4 Error: Capsule Generation Failed

```json
{
  "error": {
    "type": "capsule_generation_failed",
    "message": "Unable to extract meaningful content from turns 1-50",
    "resolution": "Manually create capsule or skip turn range"
  }
}
```

## Section 22: Edge Cases

### 22.1 Empty Session

```json
{
  "session_id": "empty_session",
  "turn_count": 0,
  "estimated_tokens": 0,
  "ratio": 0,
  "pressure_level": "normal",
  "compression_state": "idle",
  "action": "observe"
}
```

### 22.2 Single Turn Session

```json
{
  "session_id": "single_turn_session",
  "turn_count": 1,
  "estimated_tokens": 500,
  "ratio": 0.0025,
  "pressure_level": "normal",
  "compression_state": "idle",
  "action": "observe"
}
```

### 22.3 Maximum Context Session

```json
{
  "session_id": "max_context_session",
  "turn_count": 500,
  "estimated_tokens": 199000,
  "ratio": 0.995,
  "pressure_level": "strong",
  "compression_state": "pending",
  "action": "forced_strong_compression"
}
```

### 22.4 Exactly At Threshold

```json
{
  "session_id": "exact_threshold_session",
  "turn_count": 200,
  "estimated_tokens": 170000,
  "ratio": 0.85,
  "pressure_level": "standard",
  "compression_state": "pending",
  "action": "forced_standard_compression"
}
```

### 22.5 Just Below Threshold

```json
{
  "session_id": "below_threshold_session",
  "turn_count": 199,
  "estimated_tokens": 169000,
  "ratio": 0.845,
  "pressure_level": "light",
  "compression_state": "candidate",
  "action": "observe"
}
```

## Section 23: Multi-Agent Scenarios

### 23.1 Agent Coordination for Compression

```json
{
  "agents": [
    {
      "agent_id": "agent_001",
      "role": "compression_manager",
      "responsibilities": ["budget_monitoring", "trigger_decision"]
    },
    {
      "agent_id": "agent_002",
      "role": "capsule_generator",
      "responsibilities": ["content_extraction", "summary_generation"]
    },
    {
      "agent_id": "agent_003",
      "role": "state_manager",
      "responsibilities": ["state_persistence", "recovery"]
    }
  ],
  "coordination_protocol": {
    "trigger_flow": [
      "agent_001 detects threshold breach",
      "agent_001 signals agent_002",
      "agent_002 generates capsules",
      "agent_002 signals agent_003",
      "agent_003 persists state"
    ]
  }
}
```

### 23.2 Compression Delegation

```json
{
  "delegation": {
    "from_agent": "main_agent",
    "to_agent": "compression_worker",
    "task": "execute_compression",
    "params": {
      "session_id": "session_001",
      "mode": "enforced",
      "max_tokens": 200000
    },
    "callback": {
      "on_success": "compression_complete",
      "on_failure": "compression_failed"
    }
  }
}
```

## Section 24: Audit Trail Examples

### 24.1 Complete Audit Trail

```json
{
  "audit_id": "audit_20260308_030000",
  "session_id": "session_001",
  "events": [
    {
      "timestamp": "2026-03-08T03:00:00-06:00",
      "event": "session_started",
      "details": {"session_type": "single_topic_daily_chat"}
    },
    {
      "timestamp": "2026-03-08T03:05:00-06:00",
      "event": "budget_check",
      "details": {"ratio": 0.50, "pressure_level": "normal"}
    },
    {
      "timestamp": "2026-03-08T03:10:00-06:00",
      "event": "threshold_crossed",
      "details": {"ratio": 0.85, "threshold": "enforced"}
    },
    {
      "timestamp": "2026-03-08T03:10:01-06:00",
      "event": "compression_started",
      "details": {"mode": "enforced", "turns_to_evict": 50}
    },
    {
      "timestamp": "2026-03-08T03:10:02-06:00",
      "event": "capsule_created",
      "details": {"capsule_id": "cap_001", "turns": "1-50"}
    },
    {
      "timestamp": "2026-03-08T03:10:03-06:00",
      "event": "compression_completed",
      "details": {"duration_ms": 200, "gain_percent": 35}
    }
  ]
}
```

### 24.2 Audit Trail with Failure

```json
{
  "audit_id": "audit_20260308_030100",
  "session_id": "session_002",
  "events": [
    {
      "timestamp": "2026-03-08T03:15:00-06:00",
      "event": "session_started",
      "details": {"session_type": "single_topic_daily_chat"}
    },
    {
      "timestamp": "2026-03-08T03:20:00-06:00",
      "event": "threshold_crossed",
      "details": {"ratio": 0.90, "threshold": "enforced"}
    },
    {
      "timestamp": "2026-03-08T03:20:01-06:00",
      "event": "compression_started",
      "details": {"mode": "enforced", "turns_to_evict": 70}
    },
    {
      "timestamp": "2026-03-08T03:20:02-06:00",
      "event": "compression_failed",
      "details": {"error": "capsule_generation_failed"}
    },
    {
      "timestamp": "2026-03-08T03:20:03-06:00",
      "event": "rollback_initiated",
      "details": {"reason": "compression_failed"}
    },
    {
      "timestamp": "2026-03-08T03:20:04-06:00",
      "event": "rollback_completed",
      "details": {"state_restored": true}
    }
  ]
}
```

## Section 25: Metrics Collection

### 25.1 Real-Time Metrics

```json
{
  "timestamp": "2026-03-08T03:25:00-06:00",
  "metrics": {
    "active_sessions": 5,
    "total_compressions": 10,
    "successful_compressions": 9,
    "failed_compressions": 1,
    "average_compression_ratio": 0.45,
    "average_duration_ms": 220,
    "safety_violations": 0,
    "kill_switch_activations": 0
  }
}
```

### 25.2 Aggregated Metrics

```json
{
  "period": "2026-03-08T00:00:00-06:00/PT6H",
  "aggregated_metrics": {
    "total_sessions_processed": 100,
    "total_compressions": 25,
    "compression_success_rate": 0.96,
    "average_pre_compression_ratio": 0.88,
    "average_post_compression_ratio": 0.52,
    "average_gain_percent": 41,
    "p50_duration_ms": 180,
    "p95_duration_ms": 350,
    "p99_duration_ms": 500,
    "safety_violation_count": 0
  }
}
```

## Section 26: Validation Report Template

### 26.1 Controlled Validation Report

```markdown
# Controlled Validation Report

## Summary
- **Validation ID**: controlled_20260308_030000
- **Status**: PASS
- **Duration**: 5 minutes

## Configuration
- Context Window: 200000 tokens
- Threshold Enforced: 0.85
- Threshold Strong: 0.92
- Mode: light_enforced

## Results
- Trigger Ratio: 0.85
- Pre-Assemble Compliant: yes
- Post-Compression Ratio: 0.52
- Safety Counters Zero: yes

## Evidence
- counter_before.json: ✅
- counter_after.json: ✅
- budget_before.json: ✅
- budget_after.json: ✅
- guardrail_event.json: ✅
- capsule_metadata.json: ✅

## Conclusion
Phase C validation passed. Runtime policy is correctly aligned.
Ready for Phase D Natural Validation.
```

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T03:04:00-06:00
**Purpose**: Controlled Validation Test Data Part D
