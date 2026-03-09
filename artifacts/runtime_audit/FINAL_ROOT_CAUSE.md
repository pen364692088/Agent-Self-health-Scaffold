# Final Root Cause Analysis

## The Answer

**OpenClaw native compaction is REACTIVE, not PROACTIVE.**

### What This Means

OpenClaw only triggers compaction when:
1. **API returns context overflow error**
2. Then it catches the error
3. Then it calls `contextEngine.compact()`

### Evidence

From `reply-C5LKjXcC.js`:
```javascript
if (contextOverflowError) {
    log$7.warn(`context overflow detected...`);
    const compactResult = await contextEngine.compact({...});
}
```

### Why No Compaction at 111%

Current situation:
- Context: 221k/200k (111%)
- **But no API error returned**
- Model still accepts the request
- No overflow error → No compaction trigger

OpenClaw does NOT check:
- ❌ ratio >= 0.85
- ❌ proactive budget checking
- ❌ pre-assemble compression

OpenClaw DOES check:
- ✅ API error response
- ✅ "context_length_exceeded" or similar
- ✅ Only then triggers compaction

### Why `session_status` Shows Compactions: 0

Because:
1. No overflow error occurred
2. Model (qianfan-code-latest) has 200k context
3. We're at 221k which is 111% of 200k
4. But the model might accept it anyway (or silently truncate)
5. No error → No compaction

### Two Different Designs

**Our `runtime_compression_policy.json`** (never integrated):
```
ratio >= 0.85 → trigger compression (proactive)
```

**OpenClaw native compaction**:
```
API error → trigger compression (reactive)
```

### The Integration Gap

We designed a **proactive** system with thresholds:
- 0.75 → observe
- 0.85 → enforced compression
- 0.92 → strong compression

But OpenClaw's native system is **reactive**:
- Wait for error
- Then compress
- Retry

These are **fundamentally different approaches**.

### F Questions - Final Answers

1. **Has current live session loaded new runtime compression policy?**
   - NO. The policy file exists but is not used by OpenClaw.
   - OpenClaw uses its own `compaction` config, which is `null`.

2. **Has current live session executed pre-assemble budget-check?**
   - NO. OpenClaw doesn't have pre-assemble budget checking.
   - It only reacts to overflow errors.

3. **Has current live session executed guardrail 2A judgment?**
   - NO. "guardrail 2A" is from our custom policy, not OpenClaw.
   - OpenClaw doesn't have this concept.

4. **What is the root cause of no automatic compression?**
   - **OpenClaw compaction is reactive, not proactive**
   - It only triggers on API overflow errors
   - No error occurred → No compaction
   - Our proactive policy was never integrated

5. **What fix is needed?**
   
   **Option A**: Use OpenClaw's native reactive compaction
   - Configure `compaction` in `openclaw.json`
   - Wait for API overflow errors
   - Let OpenClaw handle it reactively

   **Option B**: Integrate our proactive tools
   - Requires modifying OpenClaw core
   - Add pre-assemble hook
   - Check ratio before API call
   - Call our tools when ratio >= 0.85

   **Option C**: Hybrid approach
   - Use OpenClaw's reactive for safety
   - Add external monitoring for proactive
   - Not a clean solution

### Recommendation

The cleanest fix is **Option A**:
1. Add `compaction` config to `openclaw.json`:
   ```json
   {
     "compaction": {
       "mode": "safeguard",
       "reserveTokens": 10000,
       "keepRecentTokens": 8000,
       "maxHistoryShare": 0.7
     }
   }
   ```
2. This activates OpenClaw's native compaction
3. It will trigger when API returns overflow errors
4. No code changes needed

### Why This Happened

The Config Alignment Gate created a policy file and documented it as "integrated", but:
1. No one actually modified OpenClaw core to read it
2. OpenClaw's compaction works differently (reactive)
3. The integration was assumed, not verified

---

**Generated**: 2026-03-08T19:15:00-05:00
