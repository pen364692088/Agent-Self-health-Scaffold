# Manager Callback Policy Snapshot

Timestamp: 2026-02-21 20:00 America/Winnipeg

## User-confirmed preference
- Do not rely only on auto subagent completion messages.
- On every key completion (subagent done / audit verdict), Manager must send a proactive Telegram message.

## Required callback format
Use one concise message with:
- prefix: `[Manager callback]`
- `runId=<id>`
- `status=done|blocked|approved`
- short payload summary (1-3 lines)

Example:
`[Manager callback] runId=<id> status=done\npayload: <summary>`

## Delivery rule
1. Receive subagent completion event.
2. Immediately send proactive message via `message(action=send)` to user chat.
3. Include decision + key evidence path when applicable.

## Verification history
- Auto callback visibility: inconsistent in this chat.
- Proactive `message` send: confirmed working by user replies (`收到2/3/4`).

## Default behavior from now on
- Keep normal in-thread replies.
- Additionally push Manager callback for key milestones so user never misses progress.
