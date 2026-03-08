# Context Compression Test Data - Part C

Continuing controlled validation test data series with additional examples and configurations.

## Section 16: Tool Output Examples

### 16.1 context-budget-check Output

When running budget check on a session with high token usage:

```json
{
  "estimated_tokens": 175000,
  "max_tokens": 200000,
  "ratio": 0.875,
  "pressure_level": "light",
  "threshold_hit": "light",
  "snapshot_id": "snap_20260308_030000"
}
```

When running budget check on a session that has crossed the enforced threshold:

```json
{
  "estimated_tokens": 185000,
  "max_tokens": 200000,
  "ratio": 0.925,
  "pressure_level": "strong",
  "threshold_hit": "strong",
  "snapshot_id": "snap_20260308_030100"
}
```

When running budget check after compression:

```json
{
  "estimated_tokens": 95000,
  "max_tokens": 200000,
  "ratio": 0.475,
  "pressure_level": "normal",
  "threshold_hit": null,
  "snapshot_id": "snap_20260308_030200"
}
```

### 16.2 context-compress Output

Successful compression output:

```json
{
  "compression_triggered": true,
  "mode": "enforced",
  "pressure_level": "standard",
  "plan": {
    "evict_turns": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50],
    "evicted_ranges": [{"start": 1, "end": 50}],
    "create_capsules": ["cap_20260308_session_1_50"],
    "preserve_resident": ["task_goal", "open_loops", "hard_constraints", "response_contract"]
  },
  "capsules": [
    {
      "capsule_id": "cap_20260308_session_1_50",
      "topic": "Initial discussion and setup",
      "token_count": 2500
    }
  ],
  "event_id": "cmp_20260308_030000",
  "event_path": "/path/to/event.json",
  "before": {
    "tokens": 170000,
    "turns": 100,
    "ratio": 0.85
  },
  "after": {
    "tokens": 110000,
    "turns": 50,
    "ratio": 0.55
  },
  "duration_ms": 200
}
```

Compression not triggered (low pressure):

```json
{
  "compression_triggered": false,
  "mode": "enforced",
  "pressure_level": "normal",
  "reason": "Context pressure is normal, no compression needed",
  "budget": {
    "estimated_tokens": 50000,
    "max_tokens": 200000,
    "ratio": 0.25,
    "pressure_level": "normal",
    "threshold_hit": null
  }
}
```

Compression failed:

```json
{
  "compression_triggered": true,
  "mode": "enforced",
  "pressure_level": "standard",
  "plan": {
    "evict_turns": [1, 2, 3, 4, 5],
    "evicted_ranges": [{"start": 1, "end": 5}],
    "create_capsules": [],
    "preserve_resident": ["task_goal"]
  },
  "error": {
    "type": "capsule_generation_failed",
    "message": "Insufficient context to generate capsule summary",
    "turn_range": {"start": 1, "end": 5}
  },
  "event_id": "cmp_20260308_030100",
  "before": {
    "tokens": 175000,
    "turns": 120,
    "ratio": 0.875
  },
  "after": null,
  "duration_ms": 50,
  "rollback_initiated": true
}
```

### 16.3 prompt-assemble Output

Normal assembly output:

```json
{
  "session_id": "session_001",
  "prompt_tokens": 45000,
  "max_tokens": 200000,
  "ratio": 0.225,
  "layers": {
    "resident": {
      "tokens": 5000,
      "components": ["task_goal", "open_loops", "hard_constraints"]
    },
    "active": {
      "tokens": 35000,
      "turns": [10, 11, 12, 13, 14, 15]
    },
    "recall": {
      "tokens": 2000,
      "snippets": ["cap_001", "cap_002"]
    }
  },
  "pressure_level": "normal",
  "light_enforced_mode": false,
  "compression_applied": false,
  "compression_event": null
}
```

Light enforced mode assembly:

```json
{
  "session_id": "session_001",
  "prompt_tokens": 110000,
  "max_tokens": 200000,
  "ratio": 0.55,
  "layers": {
    "resident": {
      "tokens": 8000,
      "components": ["task_goal", "open_loops", "hard_constraints", "response_contract"]
    },
    "active": {
      "tokens": 90000,
      "turns": [51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62]
    },
    "recall": {
      "tokens": 5000,
      "snippets": ["cap_20260308_session_1_50"]
    }
  },
  "pressure_level": "normal",
  "light_enforced_mode": true,
  "compression_applied": true,
  "compression_event": "cmp_20260308_030000",
  "budget_snapshot": {
    "estimated_tokens": 170000,
    "ratio": 0.85,
    "pressure_level": "standard"
  }
}
```

## Section 17: Compression State Machine Examples

### 17.1 State: idle

The idle state is the default state when budget ratio is below 0.75:

```json
{
  "compression_state": "idle",
  "budget_ratio": 0.50,
  "estimated_tokens": 100000,
  "max_tokens": 200000,
  "turn_count": 60,
  "recommended_action": "observe",
  "next_threshold": 0.75,
  "tokens_to_next_threshold": 50000
}
```

### 17.2 State: candidate

The candidate state is entered when budget ratio is between 0.75 and 0.85:

```json
{
  "compression_state": "candidate",
  "budget_ratio": 0.80,
  "estimated_tokens": 160000,
  "max_tokens": 200000,
  "turn_count": 90,
  "recommended_action": "mark_for_potential_compression",
  "next_threshold": 0.85,
  "tokens_to_next_threshold": 10000,
  "candidate_since": "2026-03-08T03:00:00-06:00",
  "candidate_duration_turns": 5
}
```

### 17.3 State: pending

The pending state is entered when budget ratio reaches or exceeds 0.85:

```json
{
  "compression_state": "pending",
  "budget_ratio": 0.85,
  "estimated_tokens": 170000,
  "max_tokens": 200000,
  "turn_count": 100,
  "recommended_action": "execute_compression_before_assemble",
  "trigger_threshold": 0.85,
  "pending_since": "2026-03-08T03:05:00-06:00",
  "max_delay_turns": 1,
  "eviction_preview": {
    "estimated_evict_count": 50,
    "estimated_preserve_count": 50,
    "estimated_post_ratio": 0.55
  }
}
```

### 17.4 State: executing

The executing state represents an active compression operation:

```json
{
  "compression_state": "executing",
  "budget_ratio": 0.85,
  "estimated_tokens": 170000,
  "max_tokens": 200000,
  "turn_count": 100,
  "recommended_action": "in_progress",
  "started_at": "2026-03-08T03:05:30-06:00",
  "current_operation": "capsule_generation",
  "progress": {
    "eviction_plan_complete": true,
    "capsules_generated": 0,
    "capsules_total": 1,
    "state_update_complete": false
  }
}
```

### 17.5 State: completed

The completed state indicates successful compression:

```json
{
  "compression_state": "completed",
  "budget_ratio": 0.55,
  "estimated_tokens": 110000,
  "max_tokens": 200000,
  "turn_count": 50,
  "recommended_action": "observe",
  "completed_at": "2026-03-08T03:05:31-06:00",
  "compression_summary": {
    "tokens_before": 170000,
    "tokens_after": 110000,
    "tokens_evicted": 60000,
    "gain_percent": 35,
    "turns_evicted": 50,
    "capsules_created": 1,
    "duration_ms": 200
  },
  "next_threshold": 0.75
}
```

### 17.6 State: failed

The failed state indicates compression could not complete:

```json
{
  "compression_state": "failed",
  "budget_ratio": 0.85,
  "estimated_tokens": 170000,
  "max_tokens": 200000,
  "turn_count": 100,
  "recommended_action": "retry_or_rollback",
  "failed_at": "2026-03-08T03:06:00-06:00",
  "error": {
    "type": "capsule_generation_failed",
    "message": "Unable to generate capsule for turn range",
    "details": {
      "turn_range": {"start": 1, "end": 50},
      "attempt": 1,
      "max_attempts": 3
    }
  },
  "retry_available": true,
  "rollback_available": true
}
```

### 17.7 State: rollback

The rollback state indicates compression was reverted:

```json
{
  "compression_state": "rollback",
  "budget_ratio": 0.85,
  "estimated_tokens": 170000,
  "max_tokens": 200000,
  "turn_count": 100,
  "recommended_action": "restore_previous_state",
  "rollback_reason": "compression_failed",
  "rollback_initiated_at": "2026-03-08T03:06:30-06:00",
  "rollback_status": "in_progress",
  "previous_state": {
    "compression_state": "pending",
    "budget_ratio": 0.85
  }
}
```

## Section 18: Configuration Validation

### 18.1 Runtime Config Check

Valid runtime configuration:

```json
{
  "config_valid": true,
  "checks": [
    {
      "name": "context_window",
      "expected": 200000,
      "actual": 200000,
      "status": "pass"
    },
    {
      "name": "threshold_enforced",
      "expected": 0.85,
      "actual": 0.85,
      "status": "pass"
    },
    {
      "name": "threshold_strong",
      "expected": 0.92,
      "actual": 0.92,
      "status": "pass"
    },
    {
      "name": "critical_rule",
      "expected": "不允许跨过 0.85 后继续拖延",
      "actual": "不允许跨过 0.85 后继续拖延",
      "status": "pass"
    }
  ]
}
```

Invalid runtime configuration (threshold mismatch):

```json
{
  "config_valid": false,
  "checks": [
    {
      "name": "context_window",
      "expected": 200000,
      "actual": 200000,
      "status": "pass"
    },
    {
      "name": "threshold_enforced",
      "expected": 0.85,
      "actual": 0.92,
      "status": "fail",
      "error": "Threshold enforced is 0.92, expected 0.85"
    }
  ],
  "recommendation": "Update threshold_enforced to 0.85 in runtime config"
}
```

### 18.2 Hook Health Check

Healthy hook status:

```json
{
  "hook_status": "healthy",
  "hook_name": "context-compression-shadow",
  "mode": "light_enforced",
  "checks": [
    {
      "name": "feature_enabled",
      "status": "pass",
      "value": true
    },
    {
      "name": "kill_switch",
      "status": "pass",
      "value": false
    },
    {
      "name": "tools_available",
      "status": "pass",
      "tools": ["context-budget-check", "context-compress", "prompt-assemble", "context-retrieve"]
    },
    {
      "name": "counters_accessible",
      "status": "pass",
      "path": "artifacts/context_compression/light_enforced/light_enforced_counters.json"
    }
  ]
}
```

Unhealthy hook status:

```json
{
  "hook_status": "degraded",
  "hook_name": "context-compression-shadow",
  "mode": "light_enforced",
  "checks": [
    {
      "name": "feature_enabled",
      "status": "pass",
      "value": true
    },
    {
      "name": "kill_switch",
      "status": "fail",
      "value": true,
      "error": "Kill switch is triggered"
    },
    {
      "name": "tools_available",
      "status": "pass",
      "tools": ["context-budget-check", "context-compress"]
    },
    {
      "name": "counters_accessible",
      "status": "fail",
      "error": "Counter file not found"
    }
  ],
  "recommendation": "Disable kill switch and verify counter file path"
}
```

## Section 19: Integration Test Scenarios

### 19.1 End-to-End Compression Flow

Test scenario: Complete compression cycle from idle to completed

```json
{
  "test_id": "test_e2e_001",
  "test_name": "Complete compression cycle",
  "steps": [
    {
      "step": 1,
      "action": "budget_check",
      "expected_result": {
        "compression_state": "idle",
        "pressure_level": "normal"
      }
    },
    {
      "step": 2,
      "action": "add_turns",
      "params": {"count": 50},
      "expected_result": {
        "compression_state": "candidate",
        "pressure_level": "light"
      }
    },
    {
      "step": 3,
      "action": "add_turns",
      "params": {"count": 30},
      "expected_result": {
        "compression_state": "pending",
        "pressure_level": "standard"
      }
    },
    {
      "step": 4,
      "action": "trigger_compression",
      "expected_result": {
        "compression_state": "executing",
        "mode": "enforced"
      }
    },
    {
      "step": 5,
      "action": "wait_for_completion",
      "expected_result": {
        "compression_state": "completed",
        "pressure_level": "normal"
      }
    }
  ]
}
```

### 19.2 Kill Switch Test

Test scenario: Kill switch activation during compression

```json
{
  "test_id": "test_kill_switch_001",
  "test_name": "Kill switch activation",
  "steps": [
    {
      "step": 1,
      "action": "activate_kill_switch",
      "params": {"reason": "Test kill switch"}
    },
    {
      "step": 2,
      "action": "add_turns",
      "params": {"count": 100}
    },
    {
      "step": 3,
      "action": "trigger_compression",
      "expected_result": {
        "compression_triggered": false,
        "kill_switch_active": true
      }
    },
    {
      "step": 4,
      "action": "deactivate_kill_switch"
    },
    {
      "step": 5,
      "action": "trigger_compression",
      "expected_result": {
        "compression_triggered": true,
        "kill_switch_active": false
      }
    }
  ]
}
```

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T03:02:00-06:00
**Purpose**: Controlled Validation Test Data Part C
