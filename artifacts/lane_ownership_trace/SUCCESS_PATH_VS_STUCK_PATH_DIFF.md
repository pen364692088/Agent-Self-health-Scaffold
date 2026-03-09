# SUCCESS_PATH_VS_STUCK_PATH_DIFF

## Historical success path (session_before_compact reached)

**Evidence**: `artifacts/compaction_safeguard_bugfix/runtime_instrumentation_trace.jsonl`

**Pattern**:
1. Agent session auto-compaction triggered (`_checkCompaction` / `_runAutoCompaction`)
2. Preparation builder ran inside `session.compact(...)`
3. `session_before_compact` hook emitted
4. Safeguard received and inspected the preparation
5. Safeguard cancelled with `upstream_empty_candidate_set`

**Lane acquisition**: Automatic (internal to session), not via `/compact` command

**Release pattern**: Normal completion (error path at safeguard, but task finished)

## Stuck path (post-adoption manual trigger)

**Evidence**: `artifacts/compaction_safeguard_bundle_adoption/live_revalidation_after_bundle_adoption_trace.jsonl`

**Pattern**:
1. External attempt to trigger via `sessions_send`
2. `sessions_send_timeout` before any handler ran
3. No evidence of `handleCompactCommand` invocation

**Lane status at time of attempt**: Busy with embedded run (runId c98af15b-...)

**Release pattern**: Never acquired, never released

## Minimal difference

| Aspect | Success Path | Stuck Path |
|--------|--------------|------------|
| Trigger source | Internal auto-compaction | External sessions_send |
| Entry point | `_runAutoCompaction` | N/A (never entered) |
| Lane acquisition | Internal session mechanism | Never acquired |
| Session busy? | No | Yes (embedded run holding) |
| Reached session_before_compact? | Yes | No |
| Reached prepareCompaction? | Yes (inferred) | No |

## Root difference
The success path used **internal auto-compaction** which runs within the session's own context.
The stuck path used **external sessions_send** which could not even enter the handler because the session was busy.

## Implication
The compaction mechanism itself is reachable; the post-adoption test just used the wrong trigger method at the wrong time (when session was busy).
