# Final Root Cause Analysis (CORRECTED)

## The Real Answer

**OpenClaw IS trying to compact, but `compaction-safeguard` is BLOCKING it.**

### Evidence from Logs

```
[compaction-safeguard] Compaction safeguard: cancelling compaction with no real conversation messages to summarize.
```

This error appears **every few minutes** (18:31, 18:35, 18:40, 18:45, 18:50, 18:55, 19:00, 19:05, 19:10...)

### What's Happening

1. OpenClaw's `compaction-safeguard` mode IS active
2. OpenClaw IS attempting to compact
3. **But safeguard cancels it** because:
   - "no real conversation messages to summarize"
   - Safeguard thinks there's nothing meaningful to compress

### The Safeguard Mode

From OpenClaw code:
```javascript
defaults: {
    compaction: {
        mode: "safeguard"  // Default mode
    }
}
```

**Safeguard mode** means:
- Only compact when it's safe
- Cancel if there's "no real conversation messages"
- This prevents data loss

### Why It Thinks There's No Messages

Possible reasons:
1. Session file format issue
2. Messages not recognized as "real"
3. Safeguard's "real message" detection is too strict
4. Session state vs message history mismatch

### Why We See 111% Context

- Compaction is attempted
- Safeguard cancels it
- Context keeps growing
- No actual compression happens

### The Fix

**Option A**: Check why safeguard thinks there's no messages
- Investigate "real conversation messages" detection
- Maybe session has tool calls / system messages but not "real" messages

**Option B**: Switch to `"default"` mode (riskier)
```json
{
  "compaction": {
    "mode": "default"
  }
}
```
- This disables safeguard
- More aggressive compaction
- Risk of losing important context

**Option C**: Investigate session message format
- Check if messages are being recognized
- May need to fix session state

### Updated F Answers

1. **Has current live session loaded new runtime compression policy?**
   - NO, but it's using OpenClaw's native `compaction-safeguard` mode.

2. **Has current live session executed pre-assemble budget-check?**
   - NO proactive check, but it IS attempting reactive compaction.

3. **Has current live session executed guardrail 2A judgment?**
   - NO, but it has compaction-safeguard active which is blocking.

4. **What is the root cause of no automatic compression?**
   - **Compaction-safeguard is cancelling all compactions**
   - It thinks there are "no real conversation messages to summarize"
   - This happens on every attempt

5. **What fix is needed?**
   - **Diagnose why safeguard sees no messages** (preferred)
   - OR switch to `"default"` mode (riskier)
   - OR manually compact the session

### Immediate Action

1. Check session message format:
   ```bash
   head -20 ../agents/main/sessions/ee931bff-6fce-4682-930e-44f23cb8382a.jsonl
   ```

2. See if messages are "real" or just tool calls

3. If needed, switch compaction mode

---

**Generated**: 2026-03-08T19:16:00-05:00

---

## Quick Fix

The session has 733 messages but safeguard doesn't see them as "real conversation messages".

This might be because:
- Messages are mostly tool calls/results
- Safeguard has a strict definition of "real"
- System messages / tool messages don't count

**Try this**:
```bash
# Manually compact the session
openclaw sessions compact <session-id>

# Or restart with different compaction mode
```

Or add to `openclaw.json`:
```json
{
  "compaction": {
    "mode": "default",
    "reserveTokens": 20000,
    "keepRecentTokens": 10000
  }
}
```

Then restart gateway.
