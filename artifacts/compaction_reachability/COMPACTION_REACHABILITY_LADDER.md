# COMPACTION_REACHABILITY_LADDER

## Verdict
- **Target session**: `agent:main:telegram:direct:8420019401`
- **post-adoption minimal window**: manual trigger authenticity **not proven**
- **historical live native path**: proven to reach `session_before_compact` on the target session
- **last_hit_stage (best proven for real native path)**: `safeguard_entered`
- **first_miss_stage (post-adoption minimal window)**: `trigger_accepted` for the attempted manual trigger, because the only recorded result is `sessions_send_timeout`

## Stage ladder

| stageName | hit/miss | file | function | approxLine | sessionKey | triggerId/requestId | timestamp | abortReason | note |
|---|---|---|---|---:|---|---|---|---|---|
| trigger_requested | HIT | `artifacts/compaction_safeguard_bundle_adoption/live_revalidation_after_bundle_adoption_trace.jsonl` | `manual_compact_trigger_attempt` | n/a | `agent:main:telegram:direct:8420019401` | n/a | `2026-03-09T03:33:00Z` |  | attempted post-adoption manual trigger |
| trigger_accepted | MISS (post-adoption window) | `same` | `manual_compact_trigger_attempt` | n/a | `agent:main:telegram:direct:8420019401` | n/a | `2026-03-09T03:33:00Z` | `sessions_send_timeout` | no proof that runtime accepted/executed `/compact` |
| session_selected | HIT (source path) | `~/.npm-global/lib/node_modules/openclaw/dist/compact-B247y5Qt.js` | `handleCompactCommand` | `33669-33671` | `params.sessionKey` | n/a | source |  | `/compact` uses the current session key/session id |
| compaction_job_started | HIT (historical live native path) | `artifacts/compaction_safeguard_bugfix/runtime_instrumentation_trace.jsonl` | `AgentSession._runAutoCompaction` callstack | `runtime trace` | `agent:main:telegram:direct:8420019401` | n/a | `2026-03-09T02:28:48.774Z` |  | real live compaction reached post-builder hook |
| compact_wrapper_entered | HIT (source path) | `~/.npm-global/lib/node_modules/openclaw/dist/compact-B247y5Qt.js` | `compactEmbeddedPiSession` | `93502-93506` | `params.sessionKey` | n/a | source |  | queued via session lane then global lane |
| compact_direct_entered | HIT (source path + historical live inference) | `~/.npm-global/lib/node_modules/openclaw/dist/compact-B247y5Qt.js` | `compactEmbeddedPiSessionDirect` | `93030` | `params.sessionKey` | `diagId` | source / inferred from downstream hook |  | downstream safeguard hook implies direct path executed |
| prepareCompaction_entered | HIT (inferred from downstream live hook) | `@mariozechner/pi-coding-agent/src/core/agent-session.ts` -> internal preparation builder | `prepareCompaction(...)` | prior analysis | `agent:main:telegram:direct:8420019401` | n/a | before `2026-03-09T02:28:48.774Z` |  | `session_before_compact` occurs after preparation object exists |
| safeguard_entered | HIT | `reply-C5LKjXcC.js` | `compactionSafeguardExtension/session_before_compact` | `72879-72890` | `agent:main:telegram:direct:8420019401` | callstack fingerprint present | `2026-03-09T02:28:48.774Z` |  | strongest live proof |
| compaction_finished / aborted | ABORTED | `artifacts/compaction_safeguard_bugfix/runtime_instrumentation_trace.jsonl` | `session_before_compact_cancel` | `runtime trace` | `agent:main:telegram:direct:8420019401` | n/a | `2026-03-09T02:28:48.774Z` | `upstream_empty_candidate_set` | aborted at safeguard due upstream-empty-candidate-set |

## Callstack fingerprint
```text
Error: session_before_compact_probe
    at file:///home/moonlight/.npm-global/lib/node_modules/openclaw/dist/reply-C5LKjXcC.js:72879:16
    at ExtensionRunner.emit (file:///home/moonlight/.npm-global/lib/node_modules/openclaw/node_modules/@mariozechner/pi-coding-agent/src/core/extensions/runner.ts:554:34)
    at AgentSession._runAutoCompaction (file:///home/moonlight/.npm-global/lib/node_modules/openclaw/node_modules/@mariozechner/pi-coding-agent/src/core/agent-session.ts:1645:58)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at AgentSession._checkCompaction (file:///home/moonlight/.npm-global/lib/node_modules/openclaw/node_modules/@mariozechner/pi-coding-agent/src/core/agent-session.ts:1608:4)
    at _handleAgentEvent (file:///home/moonlight/.npm-global/lib/node_modules/openclaw/node_modules/@mariozechner/pi-coding-agent/src/core/agent-session.ts:394:4)
```
