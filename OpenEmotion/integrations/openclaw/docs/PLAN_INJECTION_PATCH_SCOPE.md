# Plan Injection Patch Scope

## Overview

This document defines the scope of the Plan Injection Patch (Read-only Reply Injection) for OpenEmotion × OpenClaw integration.

## Goal

Safely integrate `/plan` API into the reply generation pipeline, **only affecting reply text**, with strict boundaries preventing influence on task runtime, tool execution, checkpoints, task state, or control commands.

## Scope: ALLOWED

| Component | Description | Implementation Location |
|-----------|-------------|------------------------|
| `/plan` API call | Call `/plan` before reply generation | `plan-injection-hook/handler.js` |
| Read-only consumption | Consume plan fields: tone, key_points, constraints, focus_target, emotion, relationship | Skill guidance |
| Configuration switches | Enable/disable injection per path type | `openclaw.json` env vars |
| Fallback mechanisms | Graceful degradation on failure | Fallback rules document |
| Logging & observability | Request/response/fallback logging | Hook implementation |
| Unit/Integration/E2E tests | Comprehensive test coverage | `artifacts/verification/` |

## Scope: FORBIDDEN

The following are explicitly **out of scope** and must NOT be affected by plan injection:

| Forbidden Area | Reason | Verification |
|----------------|--------|--------------|
| Task scheduling | Plan must not change which tasks run | Unit test: task creation unchanged |
| Tool selection | Plan must not change which tools are called | Unit test: tool calls unchanged |
| Tool execution | Plan must not change tool execution results | Integration test: tool output unchanged |
| Checkpoint writes | Plan must not affect checkpoint data | Integration test: checkpoint unchanged |
| Task state | Plan must not modify task state machine | Unit test: state transitions unchanged |
| Waiting/resume | Plan must not affect waiting or resume logic | Integration test: resume unchanged |
| Control commands | Plan must not affect /approve, /deny, etc. | E2E test: commands work unchanged |

## Scope: NOT IMPLEMENTING

The following are explicitly excluded from this patch:

| Excluded | Reason |
|----------|--------|
| Memory bridge | Separate feature, requires security review |
| Deep planner coupling | Keep integration minimal and testable |
| Unified personality bus | Architecture decision pending |
| Multi-agent emotional core | Out of MVP scope |
| Grayscale console | Infrastructure feature, separate track |

## Implementation Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    OpenClaw Agent Runtime                       │
├─────────────────────────────────────────────────────────────────┤
│  Skill: openemotion-emotiond                                    │
│  ↓ Reads context.json                                           │
│  ↓ Applies tone/key_points/constraints to reply                 │
├─────────────────────────────────────────────────────────────────┤
│  Context: emotiond/context.json                                 │
│  ↓ Contains plan fields + decision                              │
├─────────────────────────────────────────────────────────────────┤
│  Hook: plan-injection-hook                                      │
│  ↓ Calls /plan API                                              │
│  ↓ Writes plan to context                                       │
│  ↓ Gate: skip for command/tool/control paths                    │
├─────────────────────────────────────────────────────────────────┤
│  OpenEmotion emotiond                                           │
│  /plan API → PlanResponse (tone, key_points, etc.)              │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
User message received
    │
    ├─► emotiond-bridge hook
    │   ├─► Extract context (target_id, etc.)
    │   └─► Send time_passed event
    │
    ├─► plan-injection hook (NEW)
    │   ├─► Gate: Is this a chat path?
    │   │   ├─► YES: Continue
    │   │   └─► NO (command/tool/control): Skip injection
    │   ├─► Call /plan API
    │   ├─► Fallback on failure
    │   └─► Write plan to context.json
    │
    └─► Agent processes message
        ├─► Skill guides: read context.json
        ├─► Apply plan fields to reply
        └─► Generate response
```

## Success Criteria

1. ✅ Plan fields visible in context.json for chat paths
2. ✅ Plan fields absent for command/tool/control paths
3. ✅ Fallback triggers on all defined failure modes
4. ✅ No change to task runtime, tool execution, or control commands
5. ✅ All tests pass (unit/integration/E2E)

## Version

- **Patch Version**: 1.0.0
- **Created**: 2026-03-13
- **OpenEmotion Version**: v0.1.0
- **OpenClaw Version**: 2026.3.x
