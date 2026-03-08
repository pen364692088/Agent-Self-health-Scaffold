# Session Reuse TTL Policy

## v1.0 defaults
- `engineering`: 24h
- `project`: 24h
- `chat`: 4h

## Hard no-reuse conditions
Even inside TTL, do not reuse when:
- `session_status = closed`
- `context_state = hard_blocked`
- binding/session reference is invalid
- explicit new session requested
- agent restart policy forces fresh session

## Why conservative defaults
This version optimizes for predictable behavior and auditability rather than aggressive reuse.
TTL can be widened later once metrics show safe reuse patterns.
