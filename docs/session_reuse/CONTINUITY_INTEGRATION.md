# Continuity Integration

## Principle
Reuse is preferred. Recovery is mandatory fallback.

## Flow
1. Inbound router calls `session-route decide ...`
2. If `reused = true`, continue writing to the selected session.
3. If `reused = false`, create/select a new session and run continuity recovery.

## Local implementation
`tools/session-route decide --run-recovery` will invoke:

```bash
tools/session-start-recovery --recover --json
```

when `recovery_needed = true` and continuity is enabled.

## Contract
Decision layer never replaces:
- `SESSION-STATE.md`
- `working-buffer.md`
- `handoff.md`
- WAL-based recovery

It only decides whether reuse is allowed before that recovery path is needed.
