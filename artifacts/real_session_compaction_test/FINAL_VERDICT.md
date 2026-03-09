# Native Compaction - Final Verdict (CLOSED)

## Executive Summary

**VERDICT: NATIVE COMPACTION RESTORED ✅**

---

## Final Status

| Check | Status |
|-------|--------|
| Native compaction | ✅ **RESTORED** |
| Bundle adoption | ✅ **COMPLETE** |
| Trigger authenticity | ✅ **CONFIRMED** |
| Lane ownership issue | ✅ **CLOSED** |
| `invalid_cut_point_empty_preparation` | Patch present, not hit in valid restored run |
| Previous failed revalidations | ❌ Invalid due to wrong entrypoint and/or invalid session type |

---

## Verification Evidence

### Test Session: testbot

```
Session: agent:testbot:telegram:direct:8420019401
Session ID: c692a18f-8724-4d60-97c9-f42f0103d49a
Context Usage: 93% (186,986/200,000 tokens)
Messages: 62 (7 user + 32 assistant + 23 toolResult)
Model: openrouter/z-ai/glm-4.5-air:free

Result:
{
  "ok": true,
  "compacted": true,
  "result": {
    "summary": "## Goal\n- Check connectivity to OpenAI models...",
    "firstKeptEntryId": "4dd3fc15"
  }
}
```

### Session File Changes

| Metric | Before | After |
|--------|--------|-------|
| Lines | 65 | 68 (+3) |
| Compaction entries | 0 | 1 |
| Compaction entry ID | N/A | `82cf101a` |

---

## Root Cause of Previous Failures

### Failure Mode 1: Wrong Entrypoint

| Wrong Entry | Correct Entry |
|-------------|---------------|
| `sessions.compact` RPC | `/compact` command |
| Line truncation (threshold: 400) | Native compaction logic |
| Never calls `compactEmbeddedPiSessionDirect` | Full compaction pipeline |

**Code Evidence**:

```javascript
// gateway-cli-B7fBU7gD.js:9768-9774
// sessions.compact RPC = simple line truncation
if (lines.length <= maxLines) {  // maxLines = 400
    respond(true, { ok: true, compacted: false, kept: lines.length }, void 0);
    return;
}
```

### Failure Mode 2: Wrong Sample (Event Log Session)

| Wrong Sample | Correct Sample |
|--------------|----------------|
| Event log session | Real conversation session |
| No user/assistant/toolResult messages | Has user/assistant/toolResult messages |
| `compacted: false` is semantic skip | `compacted: true` is real compaction |

---

## Correct Entrypoint Path

```
/compact (Telegram command)
  → handleCompactCommand
  → compactEmbeddedPiSession
  → contextEngine.compact
  → LegacyContextEngine.compact
  → compactEmbeddedPiSessionDirect
    → resolveModel()
    → session.compact()
      → prepareCompaction()
      → findCutPoint()
      → generateSummary()
    → sessionManager.appendCompaction()
  → Return { ok: true, compacted: true }
```

---

## Runbook Rules (Permanent)

### Rule 1: Entrypoint Identification

> **`sessions.compact` RPC is a line truncation tool only.**
> 
> It must NOT be used as the verification entrypoint for native compaction success.
> 
> Correct entrypoint: `/compact` command → `compactEmbeddedPiSessionDirect`

### Rule 2: Sample Validation

> **Compaction verification samples must be validated before use.**
> 
> Before using a session for compaction verification, check that it contains at least one of:
> - `user` role messages
> - `assistant` role messages
> - `toolResult` role messages
> 
> Event log sessions (system events only) are INVALID samples.

---

## Case Closure

### Timeline

| Date | Event |
|------|-------|
| 2026-03-08 | Bundle adoption completed |
| 2026-03-08 | Initial verification failed (wrong entrypoint) |
| 2026-03-08 | Secondary verification failed (wrong sample) |
| 2026-03-08 | Correct verification passed |
| 2026-03-08 | **CASE CLOSED** |

### Lessons Learned

1. **Entrypoint confusion** - RPC method name vs actual functionality
2. **Sample validation** - Must check message types before verification
3. **Code reading** - Always verify code path, not just API surface

---

## Remaining Recommendation

For production sign-off, add one passive observation:

> This proves native compaction mechanism is restored.
> 
> For "main production sign-off", add one passive success observation on main agent natural traffic.

---

**Status**: CLOSED
**Verdict**: NATIVE COMPACTION RESTORED
**Date**: 2026-03-08 22:55 CST
