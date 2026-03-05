# HEARTBEAT.md

## Strict output contract (highest priority)
- Healthy: output exactly `HEARTBEAT_OK`
- Unhealthy: output exactly one line `ALERT: <reason>`
- No extra words, no JSON, no markdown, no second line

## Decision scope
- Treat `Cron: HEARTBEAT_OK` and heartbeat poll reminders as heartbeat checks (not chat reminders).
- If gateway/nodes look unhealthy: output ALERT
- Otherwise: output HEARTBEAT_OK
- Never do deep reasoning on heartbeat
- Never start big coding tasks on heartbeat; only queue a note/system-event for manager
