# Session Reuse / Thread Affinity v1.0 Validation Report

## Scope
Validated a reusable decision layer without modifying continuity state semantics, WAL semantics, or handoff meaning.

## Implemented
- binding registry
- append-only decision log
- fixed reason enums
- TTL profiles
- deterministic decision engine
- continuity handoff flag (`recovery_needed`)
- CLI wrapper (`tools/session-route`)
- local recovery invocation path (`--run-recovery`)
- 9 regression tests

## Test result
```bash
$ pytest -q tests/session_reuse/test_session_reuse_v1.py
9 passed in 0.04s
```

## Validation matrix
- ✅ Test 1 reuse within TTL
- ✅ Test 2 TTL timeout
- ✅ Test 3 different thread => no reuse
- ✅ Test 4 hard blocked context
- ✅ Test 5 closed session
- ✅ Test 6 missing session file
- ✅ Test 7 binding update after new session
- ✅ Test 8 decision log + metrics integrity
- ✅ Test 9 account change => no reuse

## Continuity integration check
`tools/session-route decide --run-recovery ...` successfully marks `recovery_needed=true` on new-session paths and invokes `tools/session-start-recovery --recover --json`.

## Expected limitation
Direct OpenClaw core inbound router attachment is not implemented in this repo because no authoritative router source is present here.
The decision layer is ready to be called from that router.
