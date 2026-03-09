# SECOND_ROOT_CAUSE_SINGLE_POINT

## Selected bucket
**`hung_inflight_owner`** (now resolved)

## Specific condition
An embedded agent run (runId `c98af15b-000a-437e-96dd-c3248bd6b7d0`) was processing a prompt on session `agent:main:telegram:direct:8420019401`. This run held the session lane while waiting for LLM response. The run eventually failed with `FailoverError: API rate limit reached` after ~8937ms.

## Why this fits the evidence

1. **`queueAhead=0` with large `waitedMs`**: The lane was held by a single in-flight task, not queue congestion

2. **Multiple `lane wait exceeded` events over ~23 minutes**: A long-running task (or series of tasks on the same session) was holding the lane

3. **Lane released after task error**: At 21:56:50, the embedded run ended with error, and lane was released normally

4. **No stale lock or missing release**: The `completeTask` function was called, `activeTaskIds.delete` executed

## Current status
- **Lane is now FREE**: No `lane wait exceeded` events after 21:56:50
- **No manual intervention needed**: The task completed (with error) and released the lane

## Root cause chain

```
Embedded run processing prompt
         ↓
Holds session lane during LLM call
         ↓
API rate limit hit
         ↓
Task fails with FailoverError
         ↓
completeTask called, lane released
         ↓
Lane is now free
```

## What blocked the post-adoption revalidation
The post-adoption manual trigger was attempted while the embedded run was still holding the lane. The `sessions_send` mechanism timed out waiting for the busy session.

## Is there a bug?
- **In lane management**: No. Lane was acquired and released correctly.
- **In the test methodology**: Yes. The post-adoption test should have:
  1. Waited for the session to be idle
  2. OR used the correct `/compact` command path instead of `sessions_send`
