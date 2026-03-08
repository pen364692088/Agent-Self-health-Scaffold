# Additional Test Data for Context Ramp - Section 27-35

## Section 27: Extended Configuration Parameters

### 27.1 Hook Timing Configuration

The hook timing configuration determines when the compression check is executed in relation to prompt assembly:

```json
{
  "hook_timing": {
    "event": "message.preprocessed",
    "execution_order": 1,
    "must_complete_before": "prompt_assembly",
    "timeout_ms": 5000
  }
}
```

### 27.2 Compression Mode Configuration

Different compression modes provide different levels of intervention:

```json
{
  "modes": {
    "shadow": {
      "description": "Observe only, no real compression",
      "modify_context": false,
      "create_evidence": true
    },
    "light_enforced": {
      "description": "Execute compression on low-risk sessions",
      "modify_context": true,
      "create_evidence": true,
      "scope": "low_risk"
    },
    "full_enforced": {
      "description": "Execute compression on all sessions",
      "modify_context": true,
      "create_evidence": true,
      "scope": "all"
    }
  }
}
```

### 27.3 Eviction Strategy Configuration

The eviction strategy determines how turns are selected for removal:

```json
{
  "eviction_strategy": {
    "method": "chronological",
    "preserve_recent_turns": 5,
    "max_evict_ratio": 0.6,
    "consider_turn_importance": false
  }
}
```

## Section 28: Advanced Error Scenarios

### 28.1 Cascading Failure

A cascading failure occurs when one error triggers additional errors:

```json
{
  "cascading_failure": {
    "initial_error": {
      "type": "budget_check_timeout",
      "message": "Budget check exceeded 5 second timeout"
    },
    "secondary_errors": [
      {
        "type": "compression_skipped",
        "reason": "budget_check_failed"
      },
      {
        "type": "context_overflow",
        "reason": "compression_not_executed"
      }
    ],
    "recovery": {
      "action": "force_compression",
      "params": {
        "mode": "strong",
        "force": true
      }
    }
  }
}
```

### 28.2 State Corruption Detection

State corruption can be detected through checksum validation:

```json
{
  "state_validation": {
    "checksum": "sha256:abc123...",
    "validated_at": "2026-03-08T03:10:00-06:00",
    "validation_result": "corrupted",
    "corruption_details": {
      "field": "open_loops",
      "expected_type": "array",
      "actual_type": "object"
    },
    "recovery_action": "restore_from_backup"
  }
}
```

### 28.3 Concurrent Compression Conflict

When multiple compression requests occur simultaneously:

```json
{
  "concurrent_compression": {
    "request_1": {
      "session_id": "session_001",
      "timestamp": "2026-03-08T03:10:00.000-06:00"
    },
    "request_2": {
      "session_id": "session_001",
      "timestamp": "2026-03-08T03:10:00.050-06:00"
    },
    "conflict_resolution": {
      "strategy": "first_wins",
      "winner": "request_1",
      "loser_action": "skip"
    }
  }
}
```

## Section 29: Performance Optimization

### 29.1 Lazy Capsule Generation

Capsule generation can be deferred until needed:

```json
{
  "lazy_capsule": {
    "enabled": true,
    "trigger": "first_retrieval",
    "cache_duration_hours": 24,
    "max_cached_capsules": 100
  }
}
```

### 29.2 Parallel Processing

Multiple operations can be parallelized:

```json
{
  "parallel_processing": {
    "enabled": true,
    "max_workers": 4,
    "operations": [
      "budget_estimation",
      "eviction_planning",
      "capsule_generation"
    ]
  }
}
```

### 29.3 Incremental Budget Estimation

Budget estimation can be updated incrementally:

```json
{
  "incremental_estimation": {
    "enabled": true,
    "cache_key": "session_budget_cache",
    "update_frequency_turns": 5
  }
}
```

## Section 30: Monitoring Dashboards

### 30.1 Real-Time Dashboard Metrics

```json
{
  "dashboard": {
    "metrics": [
      {
        "name": "compression_rate",
        "type": "gauge",
        "unit": "per_minute"
      },
      {
        "name": "average_compression_ratio",
        "type": "gauge",
        "unit": "ratio"
      },
      {
        "name": "compression_latency",
        "type": "histogram",
        "unit": "milliseconds"
      },
      {
        "name": "safety_violations",
        "type": "counter",
        "unit": "count"
      }
    ]
  }
}
```

### 30.2 Alert Configuration

```json
{
  "alerts": [
    {
      "name": "high_rollback_rate",
      "condition": "rollback_event_count > 5",
      "severity": "warning",
      "action": "notify_admin"
    },
    {
      "name": "safety_violation",
      "condition": "real_reply_corruption_count > 0",
      "severity": "critical",
      "action": "kill_switch"
    }
  ]
}
```

## Section 31: Recovery Procedures

### 31.1 State Recovery

```json
{
  "state_recovery": {
    "backup_location": "artifacts/backups/",
    "backup_frequency": "every_compression",
    "max_backups": 10,
    "recovery_steps": [
      "stop_compression",
      "restore_state",
      "verify_integrity",
      "resume_compression"
    ]
  }
}
```

### 31.2 Counter Reset

```json
{
  "counter_reset": {
    "trigger": "manual",
    "authorization": "admin",
    "reset_target": "all",
    "backup_before_reset": true
  }
}
```

## Section 32: Security Considerations

### 32.1 Access Control

```json
{
  "access_control": {
    "compression_trigger": {
      "required_role": "system",
      "rate_limit": "100_per_minute"
    },
    "kill_switch": {
      "required_role": "admin",
      "audit": true
    },
    "counter_reset": {
      "required_role": "admin",
      "audit": true
    }
  }
}
```

### 32.2 Data Sanitization

```json
{
  "data_sanitization": {
    "capsule_content": {
      "remove_pii": true,
      "hash_user_ids": true,
      "max_content_length": 10000
    }
  }
}
```

## Section 33: Integration Points

### 33.1 LLM Provider Integration

```json
{
  "llm_integration": {
    "token_counting": {
      "provider": "openai",
      "method": "tiktoken",
      "model": "gpt-4"
    },
    "context_window": {
      "openai_gpt4": 128000,
      "anthropic_claude": 200000,
      "openai_gpt4_turbo": 128000
    }
  }
}
```

### 33.2 Vector Store Integration

```json
{
  "vector_store": {
    "provider": "chromadb",
    "collection": "compression_capsules",
    "embedding_model": "text-embedding-3-small",
    "similarity_metric": "cosine"
  }
}
```

## Section 34: Compliance and Audit

### 34.1 Audit Log Format

```json
{
  "audit_log": {
    "schema_version": "1.0",
    "required_fields": [
      "timestamp",
      "event_type",
      "session_id",
      "user_id",
      "action",
      "result"
    ],
    "retention_days": 90
  }
}
```

### 34.2 Compliance Checks

```json
{
  "compliance": {
    "checks": [
      {
        "name": "evidence_preservation",
        "requirement": "All compression events must have complete evidence",
        "validation": "evidence_package_complete"
      },
      {
        "name": "safety_counter_audit",
        "requirement": "Safety counters must be audited daily",
        "validation": "counter_audit_performed"
      }
    ]
  }
}
```

## Section 35: Final Validation Checklist

### 35.1 Pre-Trigger Checklist

- [ ] Configuration verified
- [ ] Trace collection active
- [ ] Budget monitor running
- [ ] Safety counters at zero
- [ ] Kill switch available

### 35.2 Post-Trigger Checklist

- [ ] Trigger captured at 0.85
- [ ] Pre-assemble timing verified
- [ ] Compression succeeded
- [ ] Capsules created
- [ ] Evidence preserved
- [ ] Safety counters still zero

### 35.3 Evidence Package Checklist

- [ ] counter_before.json
- [ ] counter_after.json
- [ ] budget_before.json
- [ ] budget_after.json
- [ ] guardrail_event.json
- [ ] capsule_metadata.json
- [ ] compression_event.json
- [ ] CONTROLLED_TRIGGER_AT_085_REPORT.md

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T03:08:00-06:00
**Purpose**: Additional Test Data Sections 27-35
