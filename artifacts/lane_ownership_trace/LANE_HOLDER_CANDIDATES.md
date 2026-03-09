# LANE_HOLDER_CANDIDATES

## Verdict
The lane `session:agent:main:telegram:direct:8420019401` was held by an **embedded agent run**.

## Candidate ranking

| Rank | Owner Type | Probability | Evidence |
|------|------------|-------------|----------|
| 1 | embedded_run | **CONFIRMED** | Journal shows `embedded run agent end: runId=c98af15b-000a-437e-96dd-c3248bd6b7d0 isError=true` at 21:56:50, immediately followed by `lane task error` for the same session lane |
| 2 | N/A | ruled out | No other candidates match the evidence pattern |

## Key evidence

1. **Multiple `lane wait exceeded` events** with `queueAhead=0` from ~21:33 to ~21:42
   - This indicates a single long-running task, not queue congestion

2. **Lane task error at 21:56:50** for both `main` and `session:agent:main:telegram:direct:8420019401`
   - Same timestamp as `embedded run agent end`
   - Error: `FailoverError: API rate limit reached`
   - Duration: 8937ms for that specific task

3. **No more lane events after 21:56:50**
   - Lane is now free
   - The embedded run that held it has completed (with error)

## Holder details

- **runId**: `c98af15b-000a-437e-96dd-c3248bd6b7d0`
- **sessionKey**: `agent:main:telegram:direct:8420019401`
- **error**: `FailoverError: API rate limit reached`
- **durationMs**: 8937 (for the final task that released)
