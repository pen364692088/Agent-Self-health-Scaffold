# Native Compaction Safeguard Bug Root Cause Analysis

## Executive Summary

**Bug**: OpenClaw's compaction safeguard incorrectly reports "no real conversation messages" and cancels all native compaction, even when messages exist.

**Impact**: Sessions with high context never get compacted, leading to context overflow and degraded performance.

**Root Cause**: Message format mismatch - safeguard checks wrong field level.

---

## Technical Root Cause

### The Bug Location

**File**: `~/.npm-global/lib/node_modules/openclaw/dist/compact-B247y5Qt.js`

**Function 1** (line 13666):
```javascript
function isRealConversationMessage(message) {
    return message.role === "user" || message.role === "assistant" || message.role === "toolResult";
}
```

**Function 2** (line 92957):
```javascript
function hasRealConversationContent(msg) {
    return msg.role === "user" || msg.role === "assistant" || msg.role === "toolResult";
}
```

### The Session Format

OpenClaw stores session messages in an **event-based** format:

```json
{
  "type": "message",
  "message": {
    "role": "user",
    "content": [{"type": "text", "text": "..."}]
  }
}
```

### The Mismatch

| Layer | Field | Value |
|-------|-------|-------|
| Top-level | `.role` | `null` / `undefined` |
| Top-level | `.content` | `null` / `undefined` |
| Nested | `.message.role` | `"user"` / `"assistant"` |
| Nested | `.message.content` | `[{type: "text", text: "..."}]` |

**Safeguard checks**: `message.role` → finds `null`
**Actual data location**: `message.message.role` → contains `"user"`

---

## Evidence Chain

### 1. Log Evidence

```
[compaction-safeguard] Compaction safeguard: cancelling compaction with no real conversation messages to summarize.
```

This appears **every 5-10 minutes** when context is high.

### 2. Session Format Analysis

```bash
# Session has 786 message events
cat session.jsonl | jq -r '.type' | sort | uniq -c
# 786 message

# Top-level role is null
cat session.jsonl | jq '{role, content}' | head -10
# {"role": null, "content": null}

# Nested message has data
cat session.jsonl | jq '.message | {role, content: .content[0].text[0:50]}' | head -3
# {"role": "user", "content": "..."}
```

### 3. Code Execution Flow

```
1. Context reaches high ratio (>80%)
2. OpenClaw attempts compaction
3. Safeguard hook fires: session_before_compact
4. Checks: messagesToSummarize.some(isRealConversationMessage)
5. isRealConversationMessage checks: message.role === "user"
6. message.role is undefined (at top level)
7. .some() returns false
8. Safeguard returns { cancel: true }
9. Compaction cancelled
10. Context keeps growing
```

---

## Why This Happens

### Design vs Implementation Gap

1. **Session store** uses event-based format with nested messages
2. **Safeguard** was written assuming flat message format
3. **Integration gap** - the compaction system passes event entries, but safeguard expects message objects

### Historical Context

- OpenClaw uses a session entry format with `type: "message"` and nested `message` field
- This is used for replay, persistence, and debugging
- Compaction code passes these entries directly to safeguard
- Safeguard's detection functions never account for nesting

---

## The Fix

### Corrected Functions

```javascript
function isRealConversationMessage(entry) {
    // Support both nested (event) and flat message formats
    const msg = entry.message || entry;
    const role = msg.role;
    return role === "user" || role === "assistant" || role === "toolResult";
}

function hasRealConversationContent(entry) {
    // Support both nested (event) and flat message formats
    const msg = entry.message || entry;
    const role = msg.role;
    return role === "user" || role === "assistant" || role === "toolResult";
}
```

### Key Change

- Check `entry.message` first (nested format)
- Fall back to `entry` directly (flat format)
- This makes both formats work correctly

---

## Verification

### Before Fix

```bash
# Session with 786 messages
# Safeguard cancels compaction
# Context never reduces
```

### After Fix

```bash
# Same session with 786 messages
# Safeguard detects messages correctly
# Compaction proceeds
# Context reduces to target
```

---

## Files Affected

| File | Function | Line | Change |
|------|----------|------|--------|
| `compact-B247y5Qt.js` | `isRealConversationMessage` | 13666 | Add nested format support |
| `compact-B247y5Qt.js` | `hasRealConversationContent` | 92957 | Add nested format support |
| `pi-embedded-*.js` | (duplicate copies) | various | Same fix needed |

---

## Upstream Report

**Repository**: https://github.com/openclaw/openclaw
**Version Affected**: 2026.3.7
**Issue**: Compaction safeguard fails to detect messages in nested event format

---

## Metadata

- **Analyzed**: 2026-03-08T19:30:00-05:00
- **Analyzer**: Manager Agent
- **Session**: telegram:8420019401
