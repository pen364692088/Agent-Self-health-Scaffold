# Upstream Attachment Notes

## What we verified
Using the installed OpenClaw package under:

- `/home/moonlight/.npm-global/lib/node_modules/openclaw/dist/`

we verified these authoritative routing anchors exist:

- `resolveInboundLastRouteSessionKey(params)`
- `buildAgentSessionKey(params)`
- `resolveAgentRoute(input)`
- `recordInboundSession(params)`

## Critical finding
`recordInboundSession()` does **not** decide reuse vs new session.
It records metadata using an already-selected `sessionKey` and optionally updates last-route pointers.

That means transport-level reuse/new-session behavior is decided earlier by:

1. `resolveAgentRoute(input)`
2. `buildAgentSessionKey(params)`

## Why this matters
If `buildAgentSessionKey()` returns the same value for the same chat/thread/account tuple,
OpenClaw's channel/session store layer should naturally reuse the same session slot.

So when the user observes a “new session” after waking up, there are two possibilities:

### Case A — sessionKey actually changed
Possible reasons:
- dmScope/config changed
- account changed
- thread/topic changed
- peer identity changed
- upstream route policy changed

### Case B — sessionKey stayed stable, but another higher layer surfaced a fresh session object/thread
Possible reasons:
- UI/control-plane session list behavior
- agent runtime thread/session abstraction above the channel store
- recovery path opening a new runtime session while preserving continuity state

## Practical implication for Session Reuse v1.0
The cleanest upstream hook is **before** `recordInboundSession()`.

Best attachment points:
- `resolveAgentRoute(input)` — preferred, because it owns route selection and session key derivation.
- `buildAgentSessionKey(params)` — lower-level and riskier; good only if reuse policy must be encoded directly into key generation.

## Recommended upstream integration shape
Pseudo-flow:

```text
inbound message
  -> resolve route inputs (channel, account, peer, thread/topic)
  -> call session reuse decision layer
  -> if reuse allowed, return reused session key / selected session identity
  -> else derive/create new session target
  -> recordInboundSession(...)
  -> continue continuity/reply pipeline
```

## Current limitation
This workspace repo does not contain the authoritative OpenClaw source tree for those runtime functions.
We can inspect the installed dist build, but should avoid patching minified dist as the primary delivery path.

## Useful locator
Run:

```bash
tools/inspect-openclaw-session-route
```

to print the current anchor file/line locations in the installed OpenClaw package.
