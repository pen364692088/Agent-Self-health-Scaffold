# Plan Injection Fallback Rules

## Overview

This document defines all fallback scenarios and behaviors for the Plan Injection system.

## Fallback Scenarios

### Scenario Matrix

| Scenario | Detection | Fallback Behavior | User Impact |
|----------|-----------|-------------------|-------------|
| Feature disabled | `inject_plan_into_reply=false` | Skip injection entirely | Normal response |
| Degraded mode | Emotiond returns 503 | Skip plan, log warning | Normal response |
| Timeout | API call > 5000ms | Abort, skip plan | Normal response |
| Connection refused | ECONNREFUSED | Skip plan, log error | Normal response |
| 5xx error | HTTP 500-599 | Skip plan, log error | Normal response |
| 4xx error | HTTP 400-499 (except 401) | Skip plan, log warning | Normal response |
| Auth failure | HTTP 401 | Skip plan, log error | Normal response |
| Schema invalid | Response doesn't match PlanResponse | Skip plan, log warning | Normal response |
| Empty plan | Response has empty key_points | Use decision fallback | Slightly less guided |
| Plan parsing error | JSON.parse fails | Skip plan, log error | Normal response |

## Fallback Priority

When multiple fallback conditions exist:

1. **Feature disabled** → Immediate skip, no API call
2. **Connection failure** → Skip, log error
3. **Timeout** → Abort, skip, log warning
4. **HTTP error** → Based on status code
5. **Schema invalid** → Skip, log warning
6. **Empty plan** → Use decision guidance

## Fallback Behaviors

### 1. Skip Injection (Primary Fallback)

```javascript
{
  "injection_metadata": {
    "gate_result": "skipped",
    "reason": "feature_disabled|timeout|error|...",
    "fallback_triggered": true,
    "timestamp": "2026-03-13T20:45:00Z"
  }
}
```

**Agent behavior**: Proceed with normal response generation, optionally using decision guidance from emotiond.

### 2. Use Decision Fallback

When plan fails but decision is available:

```javascript
{
  "plan": null,
  "decision": {
    "action": "approach",
    "explanation": { ... }
  },
  "guidance": {
    "tone": "warm, open, friendly",
    "intent": "engage warmly",
    "phrases": ["glad to hear", "I appreciate"]
  },
  "injection_metadata": {
    "gate_result": "plan_failed_decision_fallback",
    "reason": "timeout",
    "fallback_triggered": true
  }
}
```

**Agent behavior**: Use decision-based guidance instead of plan.

### 3. Complete Fallback

When both plan and decision fail:

```javascript
{
  "plan": null,
  "decision": null,
  "guidance": {
    "tone": "neutral, helpful",
    "intent": "assist normally",
    "phrases": []
  },
  "injection_metadata": {
    "gate_result": "complete_fallback",
    "reason": "emotiond_unavailable",
    "fallback_triggered": true
  }
}
```

**Agent behavior**: Proceed with default neutral response.

## Configuration

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `inject_plan_into_reply` | boolean | `true` | Master switch for plan injection |
| `plan_injection_for_chat_only` | boolean | `true` | Only inject for chat paths |
| `skip_plan_for_commands` | boolean | `true` | Skip for slash commands |
| `skip_plan_for_task_control` | boolean | `true` | Skip for task control messages |
| `skip_plan_for_tool_paths` | boolean | `true` | Skip when tools are being called |
| `plan_injection_soft_fail` | boolean | `true` | Don't block on plan failures |
| `plan_injection_timeout_ms` | number | `5000` | API timeout in milliseconds |
| `plan_injection_max_retries` | number | `1` | Max retry attempts |

### Configuration Example

```json
{
  "env": {
    "inject_plan_into_reply": "true",
    "plan_injection_for_chat_only": "true",
    "skip_plan_for_commands": "true",
    "skip_plan_for_task_control": "true",
    "skip_plan_for_tool_paths": "true",
    "plan_injection_soft_fail": "true",
    "plan_injection_timeout_ms": "5000"
  }
}
```

## Logging

### Log Levels

| Scenario | Log Level | Message |
|----------|-----------|---------|
| Successful injection | INFO | "Plan injection success: {target_id}" |
| Feature disabled | DEBUG | "Plan injection disabled by config" |
| Gate blocked | INFO | "Plan injection skipped: {reason}" |
| Timeout | WARN | "Plan injection timeout after {ms}ms" |
| Connection error | ERROR | "Plan injection failed: {error}" |
| Schema invalid | WARN | "Plan response schema invalid: {error}" |
| Fallback used | INFO | "Plan injection fallback: {fallback_type}" |

### Log Format

```json
{
  "timestamp": "2026-03-13T20:45:00Z",
  "level": "INFO",
  "component": "plan-injection-hook",
  "event": "plan_injection_success",
  "target_id": "telegram:8420019401",
  "latency_ms": 45,
  "fallback_triggered": false
}
```

## Metrics

### Tracked Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `plan_injection_requests_total` | counter | Total injection attempts |
| `plan_injection_success_total` | counter | Successful injections |
| `plan_injection_fallback_total` | counter | Fallback triggered count |
| `plan_injection_latency_ms` | histogram | API call latency |
| `plan_injection_gate_skip_total` | counter | Gate skipped count by reason |

## Health Check

The hook exposes a health endpoint for monitoring:

```
GET /health/plan-injection
```

Response:
```json
{
  "status": "healthy|degraded|unhealthy",
  "last_success": "2026-03-13T20:45:00Z",
  "last_failure": null,
  "consecutive_failures": 0,
  "fallback_rate": 0.02
}
```

## Version

- **Version**: 1.0.0
- **Created**: 2026-03-13
