# RULE_INDEX.md

## Canonical locations
- Agent operating rules: `AGENTS.md`
- Core operating principles: `SOUL.md`
- Tool order and boundaries: `TOOLS.md`
- Heartbeat behavior: `HEARTBEAT.md`
- User preferences: `USER.md`
- Minimal bootstrap memory: `memory.md`
- cc-godmode governance boundary: `POLICIES/CC_GODMODE_BOUNDARY.md`

## Current single source of truth for subagent workflow
Use inbox/orchestrator architecture:
- `subtask-orchestrate`
- `subagent-inbox`
- `subagent-completion-handler`

Do not treat legacy callback-text patterns as the formal completion path.
