# LIVE_FALSE_POSITIVE_CALLPATH

## Real live path

`index.js`
-> `reply-C5LKjXcC.js`
-> outer compaction callsite (sanitize / validate / limit / repair)
-> `session.compact(...)`
-> internal preparation builder (currently unresolved internal function boundary)
-> `compactionSafeguardExtension/session_before_compact`

## Confirmed anchor
- File: `reply-C5LKjXcC.js`
- Hook function: `compactionSafeguardExtension/session_before_compact`

## Boundary result for the real Telegram live session
- Session key: `agent:main:telegram:direct:8420019401`

### Last non-empty stage
- Stage: `safeguard_handoff`
- File: `reply-C5LKjXcC.js`
- Function: `session.compact`
- Count: `285`

### First empty stage
- Stage: `session_before_compact_probe`
- File: `reply-C5LKjXcC.js`
- Function: `compactionSafeguardExtension/session_before_compact`
- `messageCount = 0`
- `turnPrefixCount = 0`
- `reasonCode = upstream_empty_candidate_set`

## Hard conclusion
The non-empty -> empty transition occurs **after the outer handoff and before the safeguard hook**.

So the current problem is no longer safeguard field interpretation.
It is an upstream internal preparation-builder issue where both:
- `messagesToSummarize`
- `turnPrefixMessages`

arrive empty by the time the hook fires.

## Implication
The minimal real repair point is closer to the internal preparation builder than to the safeguard predicate.
