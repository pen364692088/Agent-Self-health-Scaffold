---
name: plan-injection
description: "Inject OpenEmotion /plan into reply generation context (read-only)"
homepage: https://docs.openclaw.ai/automation/hooks
metadata:
  {
    "openclaw":
      {
        "emoji": "💉",
        "events": ["message:received"],
        "requires": { "env": ["EMOTIOND_BASE_URL", "EMOTIOND_OPENCLAW_TOKEN"] }
      }
  }
---

# Plan Injection Hook

Injects OpenEmotion `/plan` API response into agent context for reply generation.

## What It Does

1. **Gate Check**: Determines if injection is appropriate for this message type
2. **Plan Fetch**: Calls `/plan` API with user context
3. **Context Write**: Writes plan fields to `emotiond/context.json`
4. **Fallback**: Gracefully handles all failure modes

## Configuration

Environment variables (set in `~/.openclaw/openclaw.json`):

| Variable | Default | Description |
|----------|---------|-------------|
| `inject_plan_into_reply` | `true` | Master switch |
| `plan_injection_for_chat_only` | `true` | Only inject for chat |
| `skip_plan_for_commands` | `true` | Skip slash commands |
| `skip_plan_for_task_control` | `true` | Skip task control |
| `skip_plan_for_tool_paths` | `true` | Skip tool paths |
| `plan_injection_soft_fail` | `true` | Don't block on failure |
| `plan_injection_timeout_ms` | `5000` | API timeout |

## Injection Gate

The gate determines if plan injection should proceed:

| Path Type | Gate Result | Reason |
|-----------|-------------|--------|
| Normal chat | ALLOW | User conversation |
| Slash command | SKIP | Command processing |
| Task control | SKIP | Task state management |
| Tool path | SKIP | Tool execution |
| High-risk confirm | SKIP | Security-sensitive |

## Fallback Behavior

See `docs/PLAN_INJECTION_FALLBACK_RULES.md` for complete fallback matrix.

## Installation

Hook is installed at: `<workspace>/hooks/plan-injection/`

Enable via config:
```json
{
  "hooks": {
    "internal": {
      "enabled": true,
      "entries": {
        "plan-injection": { "enabled": true }
      }
    }
  }
}
```

## Version

- **Version**: 1.0.0
- **Created**: 2026-03-13
