# OpenViking L2 Bugfix Branch

**Branch**: openviking-l2-bugfix
**Created**: 2026-03-07 07:40 CST
**Purpose**: Fix L2 retrieval issues without affecting mainline shadow

## Problem Diagnosis

### Issue 1: Missing URI Parameter
- `context-retrieve` calls `openviking find query --limit`
- Should call `openviking find query -u viking://resources/user/memory/`
- Without `-u`, search scope is undefined

### Issue 2: OpenViking Health = false
```
openviking health → {"ok": true, "result": {"healthy": false}}
```
- Service responds but reports unhealthy
- Need to check: index status, embedding model, storage

### Issue 3: No Timeout/Retry
- L2 call has 15s timeout but no retry
- Should have exponential backoff for transient failures

## Fix Scope

**Allowed**:
- Fix `-u` parameter in `search_openviking_l2()`
- Add health check before L2 calls
- Add timeout + retry with backoff
- Add smoke test for L2 path

**Not Allowed**:
- Changes to L1 logic
- Changes to capsule builder
- Changes to shadow integration
- Merging into mainline shadow branch

## Files to Modify

1. `tools/context-retrieve` - Fix L2 parameters
2. `tools/openviking-l2-smoke-test` - New test script

## Testing

After fix:
1. Run `openviking-l2-smoke-test`
2. Verify L2 returns results with correct URI
3. Verify health check works
4. Verify timeout/retry behavior

## Merge Policy

- This branch stays independent
- Merge to main only after:
  - L2 smoke test passes
  - Shadow observation window complete
  - Explicit approval
