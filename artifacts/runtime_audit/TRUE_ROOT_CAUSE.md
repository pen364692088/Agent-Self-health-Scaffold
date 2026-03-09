# True Root Cause: Session Format Mismatch

## The Real Problem

**OpenClaw's compaction-safeguard can't find messages because of session format mismatch.**

### Evidence

1. **Session has 786 "message" type events**
   ```bash
   cat session.jsonl | jq -r '.type' | sort | uniq -c
   # 786 message
   ```

2. **Messages are nested inside `.message` field**
   ```json
   {
     "type": "message",
     "message": {
       "role": "user",
       "content": [{"type": "text", "text": "..."}]
     }
   }
   ```

3. **Top-level `role` and `content` are `null`**
   ```bash
   cat session.jsonl | jq '{role, content}' | head -10
   # All null
   ```

4. **Safeguard looks at wrong level**
   - Safeguard checks top-level `role`
   - Finds `null`
   - Concludes "no real conversation messages"
   - Cancels compaction

### Why This Happens

OpenClaw stores messages in an **event-based** format:
- Each line is an event with `type: "message"`
- The actual message content is nested in `.message`
- But safeguard's detection logic checks the wrong level

This is likely a **bug in safeguard's message detection**.

### The Flow

```
1. Context reaches high ratio
2. OpenClaw attempts compaction
3. Safeguard checks for "real messages"
4. Checks top-level role → finds null
5. Concludes "no messages to summarize"
6. Cancels compaction
7. Context keeps growing
```

### Log Evidence

```
[compaction-safeguard] Compaction safeguard: cancelling compaction with no real conversation messages to summarize.
```

This happens **every few minutes** (18:31, 18:35, 18:40, 18:45, 18:50, 18:55, 19:00, 19:05, 19:10...)

### The Fix

**Option A**: Fix OpenClaw's safeguard detection (upstream)
- Safeguard should check `.message.role` not `.role`
- This is a bug in OpenClaw

**Option B**: Workaround - use `"default"` mode
```json
{
  "compaction": {
    "mode": "default"
  }
}
```
- Disables safeguard
- Compaction will proceed
- But higher risk of losing context

**Option C**: Manual compaction
```bash
# Force compact the session
openclaw sessions compact ee931bff-6fce-4682-930e-44f23cb8382a
```

### Why Config Alignment Gate Missed This

The Gate:
1. Created `runtime_compression_policy.json` ✅
2. Documented "OpenClaw reads and applies policy" ✅
3. But never tested actual compaction ❌

The safeguard bug would only show when:
- Context is high
- Compaction is attempted
- Safeguard runs its check

### Final F Answers

1. **Has session loaded new runtime compression policy?**
   - OpenClaw uses its native `compaction-safeguard` mode, which is active.

2. **Has session executed pre-assemble budget-check?**
   - No proactive check. But reactive compaction IS being attempted.

3. **Has session executed guardrail 2A judgment?**
   - Compaction-safeguard IS running, but canceling due to bug.

4. **Root cause of no automatic compression?**
   - **Safeguard can't find messages due to format mismatch**
   - Messages are in `.message.role`, safeguard checks `.role`
   - All checks return null → "no messages" → cancel

5. **What fix is needed?**
   - **Immediate**: Switch to `"default"` mode or manual compact
   - **Proper**: Fix OpenClaw's safeguard message detection

---

**Generated**: 2026-03-08T19:18:00-05:00
