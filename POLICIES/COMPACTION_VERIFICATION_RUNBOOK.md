# Compaction Verification Runbook

## Entrypoint Identification

### Rule 1: `sessions.compact` RPC is NOT Native Compaction

**Definition**: `sessions.compact` RPC is a **line truncation tool** only.

- **Threshold**: 400 lines
- **Behavior**: If session file has ≤400 lines, return `{ compacted: false, kept: <lines> }`
- **Never calls**: `compactEmbeddedPiSessionDirect`, `prepareCompaction()`, `generateSummary()`

**Correct Native Compaction Entrypoint**:
```
/compact command → handleCompactCommand → compactEmbeddedPiSession → compactEmbeddedPiSessionDirect
```

**Verification**: When testing native compaction success:
- ✅ Use `/compact` command (via Telegram or direct function call)
- ❌ Do NOT use `sessions.compact` RPC

---

## Sample Validation

### Rule 2: Verify Session Contains Real Conversations

**Definition**: Compaction verification requires sessions with real conversation messages.

**Valid Message Types**:
- `user` role
- `assistant` role
- `toolResult` role

**Invalid Sample Types**:
- Event log sessions (only `session`, `custom`, `model_change` types)
- Empty sessions
- System-only sessions

**Verification Check**:
```bash
# Before using a session for compaction test, verify:
cat <session_file>.jsonl | jq -r 'select(.type == "message") | .message.role' | sort | uniq -c

# Expected output should include at least one of:
#   user
#   assistant
#   toolResult
```

---

## Quick Reference

| Scenario | Entrypoint | Sample Requirement |
|----------|------------|-------------------|
| Test native compaction | `/compact` command | Real conversation session |
| Test line truncation | `sessions.compact` RPC | Any session file |
| Debug compaction failure | `compactEmbeddedPiSessionDirect` | Real conversation session |

---

**Added**: 2026-03-08
**Reason**: Prevent future verification failures due to entrypoint/sample confusion
**Reference**: artifacts/real_session_compaction_test/FINAL_VERDICT.md
