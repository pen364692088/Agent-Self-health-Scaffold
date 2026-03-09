# MANUAL_TRIGGER_AUTHENTICITY_FINAL

## Final verdict
The post-adoption manual trigger **did NOT enter the true native compaction path**.

## Evidence

1. **Artifact record shows `sessions_send_timeout`**
   - This means the trigger was sent via `sessions_send` mechanism
   - NOT via the actual `/compact` command handler

2. **True native `/compact` path is**:
   ```
   handleCompactCommand (33647+)
   → compactEmbeddedPiSession (93502)
   → enqueueCommandInLane (session lane)
   → enqueueCommandInLane (global lane)
   → compactEmbeddedPiSessionDirect (93030)
   → contextEngine.compact
   ```

3. **What actually happened**:
   - `sessions_send` was used to send a message to the session
   - The session was busy (lane held by embedded run)
   - The send timed out waiting for response
   - No evidence of `handleCompactCommand` being invoked

## last_hit_stage / first_miss_stage

| Stage | Status |
|-------|--------|
| trigger_requested | HIT |
| trigger_accepted | MISS (sessions_send_timeout) |
| session_selected | MISS (never reached) |
| compaction_job_started | MISS |
| compact_wrapper_entered | MISS |
| compact_direct_entered | MISS |
| prepareCompaction_entered | MISS |

## Was the miss caused by lane busy?
- **Partially**: The target session was busy with an embedded run
- **But more fundamentally**: The trigger mechanism (`sessions_send`) was not the correct path to invoke native compaction

## Correct trigger path
To actually test native compaction, the trigger should be:
1. A real `/compact` command sent via Telegram to the bot
2. OR direct invocation via `compactEmbeddedPiSessionDirect` from within the same process
