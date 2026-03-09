# SECOND_ROOT_CAUSE_NARROWING

## Selected bucket
`trigger_rejected_before_compact`

## Why this is the tightest current bucket
For the **specific post-adoption minimal revalidation window**, the only fresh trigger evidence is a manual attempt that ended as `sessions_send_timeout`. That means the freshest window does **not** prove the runtime ever accepted and executed the native compaction path.

## Stronger-than-before clarification
This does **not** mean native compaction is globally unreachable.
Historical live traces on the same session prove a real native compaction path can reach `session_before_compact` and then abort with `upstream_empty_candidate_set`.

So the current narrowing is split:
1. **Specific post-adoption minimal window**
   - best bucket: `trigger_rejected_before_compact`
   - because the attempted manual trigger never gained execution proof
2. **Historical proven native path**
   - reached at least as far as `safeguard_entered`
   - therefore a blanket claim like `compact_entered_but_prepareCompaction_not_reached` is not supported by existing live evidence

## Minimal locating point
- **user/manual trigger path bottleneck**: delivery/wait path ending in `sessions_send_timeout`
- **true native manual handler entrypoint**: `handleCompactCommand(...)` in `compact-B247y5Qt.js:33647+`
- **queueing chokepoint once accepted**: `compactEmbeddedPiSession(...)` in `93502-93506`, which enqueues on the session lane first
- **runtime blockage clue**: prior gateway evidence `lane wait exceeded: lane=session:agent:main:telegram:direct:8420019401 waitedMs=129806 queueAhead=0`

## What is ruled out
- "bundle adoption failed" → ruled out
- "the post-adoption manual attempt definitely exercised native compaction" → not proven
- "native compaction never reaches the target session" → ruled out by historical live traces
- "prepareCompaction was definitely not reached on live" → not supported by historical live traces
