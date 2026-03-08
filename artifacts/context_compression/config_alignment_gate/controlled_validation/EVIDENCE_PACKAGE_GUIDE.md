# Context Compression - Evidence Package Complete Guide

## Evidence Package Overview

The evidence package provides complete audit trail for every compression operation. Each package consists of multiple files that together prove correct compression behavior.

### Required Evidence Files

| File | Purpose | When Captured |
|------|---------|---------------|
| counter_before.json | Counter state before compression | At ratio >= 0.85 |
| counter_after.json | Counter state after compression | After compression |
| budget_before.json | Budget snapshot before | At ratio >= 0.85 |
| budget_after.json | Budget snapshot after | After compression |
| guardrail_event.json | Guardrail activation record | When triggered |
| capsule_metadata.json | Capsule content summary | After capsule creation |

---

## Evidence File Specifications

### counter_before.json

Captures all counter values before compression:

```json
{
  "timestamp": "2026-03-08T04:00:00-06:00",
  "session_id": "session_001",
  "enforced_counters": {
    "enforced_sessions_total": 5,
    "enforced_low_risk_sessions": 5,
    "budget_check_call_count": 100,
    "sessions_evaluated_by_budget_check": 100,
    "sessions_over_threshold": 5,
    "compression_opportunity_count": 5,
    "enforced_trigger_count": 0,
    "real_reply_corruption_count": 0,
    "active_session_pollution_count": 0,
    "rollback_event_count": 0
  }
}
```

### counter_after.json

Captures all counter values after compression:

```json
{
  "timestamp": "2026-03-08T04:00:05-06:00",
  "session_id": "session_001",
  "enforced_counters": {
    "enforced_sessions_total": 5,
    "enforced_low_risk_sessions": 5,
    "budget_check_call_count": 101,
    "sessions_evaluated_by_budget_check": 101,
    "sessions_over_threshold": 6,
    "compression_opportunity_count": 6,
    "enforced_trigger_count": 1,
    "real_reply_corruption_count": 0,
    "active_session_pollution_count": 0,
    "rollback_event_count": 0
  }
}
```

**Counter Deltas**:
- budget_check_call_count: +1
- sessions_over_threshold: +1
- compression_opportunity_count: +1
- enforced_trigger_count: +1
- Safety counters: 0 (no change)

### budget_before.json

Budget snapshot before compression:

```json
{
  "timestamp": "2026-03-08T04:00:00-06:00",
  "session_id": "session_001",
  "estimated_tokens": 170000,
  "max_tokens": 200000,
  "ratio": 0.85,
  "pressure_level": "standard",
  "threshold_hit": "standard",
  "snapshot_id": "snap_20260308_040000"
}
```

### budget_after.json

Budget snapshot after compression:

```json
{
  "timestamp": "2026-03-08T04:00:05-06:00",
  "session_id": "session_001",
  "estimated_tokens": 102000,
  "max_tokens": 200000,
  "ratio": 0.51,
  "pressure_level": "normal",
  "threshold_hit": null,
  "snapshot_id": "snap_20260308_040005"
}
```

**Budget Changes**:
- Tokens reduced: 170k → 102k
- Ratio reduced: 0.85 → 0.51
- Pressure level: standard → normal

### guardrail_event.json

Complete guardrail activation record:

```json
{
  "guardrail_id": "2A",
  "guardrail_name": "budget_threshold_enforcement",
  "trigger_condition": "budget_ratio >= 0.85",
  "observed_values": {
    "budget_ratio": 0.85,
    "estimated_tokens": 170000,
    "max_tokens": 200000,
    "compression_state": "pending"
  },
  "action_taken": "forced_standard_compression",
  "execution_result": {
    "success": true,
    "duration_ms": 200,
    "post_compression_ratio": 0.51,
    "capsules_created": 1,
    "turns_evicted": 50
  },
  "pre_assemble_compliant": true,
  "session_id": "session_001",
  "timestamp": "2026-03-08T04:00:00-06:00"
}
```

### capsule_metadata.json

Capsule content summary:

```json
{
  "capsule_id": "cap_20260308_session_001_turns_1_50",
  "session_id": "session_001",
  "source_turn_range": {
    "start": 1,
    "end": 50
  },
  "created_at": "2026-03-08T04:00:03-06:00",
  "topic": "Initial configuration and setup",
  "summary": "User configured the system with PostgreSQL database, React frontend, and Node.js backend.",
  "key_points": [
    "Decision: Use PostgreSQL for database",
    "Decision: Use React for frontend",
    "Decision: Use Node.js for backend",
    "Commitment: Complete API by Friday"
  ],
  "entities": ["PostgreSQL", "React", "Node.js", "API"],
  "decisions": [
    {
      "id": "dec_001",
      "description": "Database selection",
      "choice": "PostgreSQL"
    }
  ],
  "commitments": [
    {
      "id": "com_001",
      "description": "Complete API",
      "deadline": "2026-03-12"
    }
  ],
  "token_count": 2500
}
```

---

## Evidence Validation Rules

### File Existence Validation

All six required files must exist:

```python
def validate_file_existence(evidence_dir: Path) -> bool:
    required = [
        'counter_before.json',
        'counter_after.json',
        'budget_before.json',
        'budget_after.json',
        'guardrail_event.json',
        'capsule_metadata.json'
    ]
    
    for filename in required:
        if not (evidence_dir / filename).exists():
            return False
    
    return True
```

### Timestamp Consistency Validation

Timestamps must be in correct order:

```python
def validate_timestamps(evidence: dict) -> bool:
    before_time = parse_timestamp(evidence['counter_before']['timestamp'])
    after_time = parse_timestamp(evidence['counter_after']['timestamp'])
    
    # Before must be earlier than after
    if before_time >= after_time:
        return False
    
    # Duration must be reasonable (< 60 seconds)
    duration = (after_time - before_time).total_seconds()
    if duration > 60:
        return False
    
    return True
```

### Counter Delta Validation

Counter deltas must be correct:

```python
def validate_counter_deltas(before: dict, after: dict) -> bool:
    # enforced_trigger_count should increase by 1
    trigger_delta = after['enforced_trigger_count'] - before['enforced_trigger_count']
    if trigger_delta != 1:
        return False
    
    # Safety counters must remain 0
    if after['real_reply_corruption_count'] != 0:
        return False
    if after['active_session_pollution_count'] != 0:
        return False
    
    return True
```

### Budget Change Validation

Budget changes must be valid:

```python
def validate_budget_changes(before: dict, after: dict) -> bool:
    # Before ratio must be >= 0.85
    if before['ratio'] < 0.85:
        return False
    
    # After ratio must be < 0.75
    if after['ratio'] >= 0.75:
        return False
    
    # Tokens must decrease
    if after['estimated_tokens'] >= before['estimated_tokens']:
        return False
    
    # Gain must be reasonable (10-60%)
    gain = (before['estimated_tokens'] - after['estimated_tokens']) / before['estimated_tokens']
    if not (0.1 <= gain <= 0.6):
        return False
    
    return True
```

---

## Evidence Package Generation

### Generation Process

```python
def generate_evidence_package(
    session_id: str,
    compression_event: dict
) -> dict:
    evidence_dir = create_evidence_directory(session_id)
    
    # Capture pre-compression evidence
    capture_counter_before(evidence_dir)
    capture_budget_before(evidence_dir)
    
    # Execute compression
    result = execute_compression(compression_event)
    
    # Capture post-compression evidence
    capture_counter_after(evidence_dir)
    capture_budget_after(evidence_dir)
    capture_guardrail_event(evidence_dir, result)
    capture_capsule_metadata(evidence_dir, result.capsule)
    
    # Validate evidence
    validation = validate_evidence_package(evidence_dir)
    
    return {
        'evidence_dir': evidence_dir,
        'validation': validation,
        'files': list_evidence_files(evidence_dir)
    }
```

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T04:16:00-06:00
**Purpose**: Evidence Package Complete Guide
