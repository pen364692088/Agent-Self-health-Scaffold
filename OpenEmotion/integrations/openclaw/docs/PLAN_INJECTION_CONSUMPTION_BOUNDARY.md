# Plan Injection Consumption Boundary

## Overview

This document defines how plan fields are consumed by the agent and the strict boundaries preventing side effects.

## Plan Fields and Their Usage

| Field | Type | Usage in Reply | Side Effect Risk |
|-------|------|----------------|------------------|
| `tone` | string | Guides response style (soft/warm/guarded/cold) | None (read-only) |
| `intent` | string | Guides response intent (repair/distance/seek/set_boundary/retaliate) | None (read-only) |
| `key_points` | string[] | Topics to address in reply | None (read-only) |
| `constraints` | string[] | Topics/behaviors to avoid | None (read-only) |
| `focus_target` | string | Who/what to focus on in reply | None (read-only) |
| `emotion` | object | Emotional state for response flavor | None (read-only) |
| `relationship` | object | Bond/trust values for response calibration | None (read-only) |
| `mood` | object | Global mood baseline | None (read-only) |
| `body_state` | object | Virtual body state (energy/stress/etc.) | None (read-only) |

## Consumption Contract

### Agent Must

1. **Read plan fields from context.json only**
   - Location: `~/.openclaw/workspace/emotiond/context.json`
   - Format: JSON with `plan` key

2. **Apply plan to reply text generation only**
   - Adjust tone and style
   - Include relevant key_points naturally
   - Respect constraints (avoid certain topics)

3. **Treat plan as advisory, not mandatory**
   - Plan provides guidance, not commands
   - Agent retains final decision on response content

### Agent Must NOT

1. **Use plan fields to modify:**
   - Tool selection (which tools to call)
   - Tool execution (how tools behave)
   - Task state (pending/running/done)
   - Control flow (waiting/resume/continue)
   - Checkpoint data

2. **Write back to plan fields:**
   - Plan is read-only from agent perspective
   - Only hooks write to context.json

3. **Propagate plan to downstream systems:**
   - Plan does not affect subagents
   - Plan does not affect external APIs
   - Plan does not affect logging/storage

## Verification Boundaries

### What We Verify

| Verification | Method |
|--------------|--------|
| Plan only affects reply text | Integration test: compare replies with/without plan |
| Plan does not affect tool calls | Integration test: tool call count unchanged |
| Plan does not affect task state | Unit test: state machine unchanged |
| Plan does not affect checkpoints | Integration test: checkpoint hash unchanged |
| Plan does not affect control commands | E2E test: /approve, /deny work unchanged |

### What We Do NOT Verify

- Response quality improvement (subjective)
- User satisfaction (requires user study)
- Emotional appropriateness (subjective)

## Context Schema

```json
{
  "target_id": "telegram:8420019401",
  "plan": {
    "tone": "warm",
    "intent": "repair",
    "key_points": ["acknowledge concern", "offer support"],
    "constraints": ["don't be defensive"],
    "focus_target": "user",
    "emotion": {
      "valence": 0.3,
      "arousal": 0.2,
      "anxiety": 0.1
    },
    "relationship": {
      "bond": 0.75,
      "trust": 0.60,
      "repair_bank": 0.40
    }
  },
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
    "gate_result": "allowed",
    "latency_ms": 45,
    "fallback_triggered": false,
    "timestamp": "2026-03-13T20:45:00Z"
  }
}
```

## Skill Integration

The `openemotion-emotiond` skill is updated to:

1. Read `plan` field from context.json
2. Apply plan fields to reply generation
3. Document the read-only nature in skill instructions

### Skill Instructions Addition

```markdown
## Plan Injection (Read-only)

Before generating your reply:

1. Read the `plan` field from context.json
2. Use `tone` to match your response style
3. Use `key_points` to guide topics to address
4. Respect `constraints` by avoiding certain topics
5. Calibrate emotional expression based on `emotion` and `relationship`

**IMPORTANT**: Plan fields are advisory only. They affect reply text, not:
- Which tools you call
- How tasks are scheduled
- Task state or checkpoints
- Control commands

If plan is missing or invalid, proceed normally without it.
```

## Failure Isolation

If plan consumption fails:

| Failure Mode | Agent Behavior |
|--------------|----------------|
| Plan missing from context | Proceed normally, no guidance |
| Plan has invalid schema | Log warning, proceed normally |
| Plan has unexpected values | Use defaults, log warning |
| Context file unreadable | Proceed normally, log error |

## Version

- **Version**: 1.0.0
- **Created**: 2026-03-13
