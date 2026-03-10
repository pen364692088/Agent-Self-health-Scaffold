# Legacy and Fallback Classification

**Generated**: 2026-03-10 06:30 CST
**Version**: 1.0
**Purpose**: Classify tools as legacy/fallback/active and determine disposition

---

## Classification Criteria

| Class | Definition | Disposition |
|-------|------------|-------------|
| ACTIVE | Current mainline, maintained | Keep and improve |
| FALLBACK | Backup path, degrade gracefully | Keep as fallback |
| LEGACY | Old but still used, migration path | Deprecate, schedule removal |
| DEPRECATED | Marked for removal | Delete post-freeze |
| DEBUG | Development/debug only | Keep, document as debug |

---

## 1. Task Completion Tools

| Tool | Class | Reason | Disposition |
|------|-------|--------|-------------|
| verify-and-close | ACTIVE | Mainline task close | Keep |
| verify-and-close-v2 | DEPRECATED | Superseded by v1.2 | **Delete** |
| enforce-task-completion | ACTIVE | Gate enforcement | Keep |
| finalize-response | ACTIVE | Output wrap | Keep, merge with verify |
| done-guard | ACTIVE | Fake completion detect | Keep |
| auto-receipt | INTERNAL | Auto receipt gen | Keep |
| receipt-signer | INTERNAL | Receipt signing | Keep |
| receipt-validator | INTERNAL | Receipt validation | Keep |
| output-interceptor | INTERNAL | Output check | Keep |
| gate-eval | ACTIVE | Gate evaluation | Keep |
| gate-a/b/c-signer | INTERNAL | Gate signing | Keep |

### Migration Path

```
verify-and-close-v2 → verify-and-close (done)
```

---

## 2. Message Sending Tools

| Tool | Class | Reason | Disposition |
|------|-------|--------|-------------|
| safe-message | ACTIVE | Safe send wrapper | Keep |
| message tool | ACTIVE | OpenClaw core | Keep, restrict for completion |
| callback-worker | INTERNAL | Auto notify | Keep |
| output-interceptor | INTERNAL | Policy check | Keep |
| testbot-chat | DEBUG | Test utility | Keep as debug |

### Fallback Chain

```
safe-message (primary)
  ↓ (if --force)
message tool (fallback, bypasses policy - DANGEROUS)
```

### Recommendation

Remove `--force` from safe-message. If emergency send needed, use message tool directly with audit log.

---

## 3. Memory Tools

| Tool | Class | Reason | Disposition |
|------|-------|--------|-------------|
| memory_store | ACTIVE | OpenClaw core capture | Keep |
| memory_recall | ACTIVE | OpenClaw core recall | Keep |
| autoCapture | ACTIVE | Auto capture hook | Keep, FROZEN |
| memory-lancedb-seed | DEBUG | Seed/debug only | Keep as debug |
| session-query | ACTIVE | Unified search | Keep, extend |
| context-retrieve | FALLBACK | S1 two-tier | Keep, integrate with session-query |
| memory-retrieve | LEGACY | Old retrieval | **Deprecate** |
| memory-search | LEGACY | Old search | **Deprecate** |
| openviking | ACTIVE | Vector backend | Keep |
| session-indexer | INTERNAL | Index builder | Keep |
| session-start-recovery | ACTIVE | State recovery | Keep |

### Migration Path

```
memory-retrieve → session-query --mode semantic
memory-search → session-query --mode keyword
context-retrieve → session-query --mode capsule (internal)
```

### Fallback Chain

```
session-query (primary)
  ↓ (if OpenViking unavailable)
SQLite FTS (fallback)
  ↓ (if DB unavailable)
Capsule retrieval (fallback)
```

---

## 4. Execution Policy Tools

| Tool | Class | Reason | Disposition |
|------|-------|--------|-------------|
| policy-eval | ACTIVE | Rule evaluation | Keep |
| policy-doctor | ACTIVE | Health check | Keep |
| policy-violations-report | ACTIVE | Violation report | Keep |
| probe-execution-policy | DEBUG | Old probe | Keep as debug |
| probe-execution-policy-v2 | DEBUG | Current probe | Keep, merge v1 |
| trigger-policy | DEBUG | Manual trigger | Keep as debug |
| write-policy-check | SPECIALIZED | Path check | Keep |
| route-rebind-guard-heartbeat | INTERNAL | Route guard | Keep |

### Migration Path

```
probe-execution-policy → probe-execution-policy-v2 (merge)
```

---

## 5. Hooks and Lifecycle

| Tool | Class | Reason | Disposition |
|------|-------|--------|-------------|
| execution-policy-enforcer | ACTIVE | Policy hook | Keep |
| emotiond-bridge | FALLBACK | Emotion bridge | Optional, keep |
| emotiond-enforcer | FALLBACK | Emotion enforce | Optional, keep |
| session-start-recovery | ACTIVE | Recovery | Keep |
| session-archive | ACTIVE | Archive | Keep |
| handoff-create | ACTIVE | Handoff gen | Keep |
| post-compaction-handoff | INTERNAL | Compaction handoff | Keep |
| continuity-event-log | INTERNAL | WAL append | Keep |

### Fallback Chain

```
execution-policy-enforcer (primary)
  ↓ (if disabled)
No enforcement (dangerous, audit log required)
```

---

## 6. Callback and Mailbox Tools

| Tool | Class | Reason | Disposition |
|------|-------|--------|-------------|
| subtask-orchestrate | ACTIVE | Main orchestration | Keep |
| subagent-inbox | ACTIVE | Receipt inbox | Keep |
| subagent-completion-handler | ACTIVE | Process receipt | Keep |
| handle-subagent-complete | ACTIVE | Unified check | Keep |
| callback-worker | ACTIVE | Dispatch notify | Keep |
| callback-handler | DEPRECATED | Old callback | **Delete** |
| callback-handler-auto | INTERNAL | Auto callback | Review, may deprecate |
| spawn-with-callback | DEBUG | Low-level spawn | Keep as debug |
| check-subagent-mailbox | DEPRECATED | Old mailbox | **Delete** |
| subagent-inbox-metrics | ACTIVE | Metrics | Keep |
| probe-subagent-inbox-metrics | DEBUG | Metrics probe | Keep |
| probe-callback-delivery | DEBUG | Delivery probe | Keep |

### Migration Path

```
callback-handler → subagent-completion-handler (done)
check-subagent-mailbox → subagent-inbox check (done)
```

---

## 7. Handoff and Continuity Tools

| Tool | Class | Reason | Disposition |
|------|-------|--------|-------------|
| session-start-recovery | ACTIVE | Recovery | Keep |
| session-state-doctor | ACTIVE | State diagnose | Keep |
| handoff-create | ACTIVE | Handoff gen | Keep |
| session-archive | ACTIVE | Archive | Keep |
| continuity-event-log | INTERNAL | WAL append | Keep |
| state-write-atomic | ACTIVE | Atomic write | Keep, integrate with safe-write |
| state-journal-append | INTERNAL | WAL | Keep |
| pre-reply-guard | INTERNAL | Context guard | Keep |
| auto-context-compact | ACTIVE | Auto compress | Keep |
| context-compress | ACTIVE | Manual compress | Keep |
| capsule-builder | ACTIVE | Capsule gen | Keep |
| context-budget-check | ACTIVE | Budget check | Keep |
| session-continuity-daily-check | INTERNAL | Daily check | Keep |
| probe-session-persistence | DEBUG | Persistence probe | Keep |
| probe-handoff-integrity | DEBUG | Handoff probe | Keep |

### Fallback Chain

```
session-start-recovery (primary)
  ↓ (if state files missing)
Reconstruct from git log / session index
```

---

## Summary Classification

| Category | ACTIVE | FALLBACK | LEGACY | DEPRECATED | DEBUG |
|----------|--------|----------|--------|------------|-------|
| Task Completion | 6 | 0 | 0 | 1 | 0 |
| Message Sending | 2 | 0 | 0 | 0 | 1 |
| Memory | 5 | 1 | 2 | 0 | 1 |
| Execution Policy | 3 | 0 | 0 | 0 | 4 |
| Hooks/Lifecycle | 5 | 2 | 0 | 0 | 0 |
| Callback/Mailbox | 5 | 0 | 0 | 2 | 3 |
| Handoff/Continuity | 8 | 0 | 0 | 0 | 2 |
| **TOTAL** | **34** | **3** | **2** | **3** | **11** |

---

## Delete List (Post-Freeze)

```
tools/verify-and-close-v2          # Superseded
tools/legacy/check-subagent-mailbox # Deprecated
tools/callback-handler             # Deprecated
tools/session-archive.original     # Backup file
tools/session-start-recovery.bak   # Backup file
```

---

## Deprecate List (Post-Freeze)

```
tools/memory-retrieve    # Use session-query --mode semantic
tools/memory-search      # Use session-query --mode keyword
tools/probe-execution-policy  # Use probe-execution-policy-v2
```

---

## Fallback Retention Rules

### Keep as Fallback If:

1. **Degrades gracefully** when primary fails
2. **No data loss** risk
3. **Well-documented** fallback path
4. **Auditable** usage

### Examples:

- `context-retrieve`: Falls back to capsule if OpenViking unavailable
- `emotiond-bridge`: Optional feature, not critical path
- `SQLite FTS`: Fallback for vector search

---

## Integration Notes

### safe-write Integration

```python
# state-write-atomic should internally call safe-write
# to ensure policy check for all state writes

def state_write_atomic(path, content):
    # Delegate to safe-write for policy check
    return safe_write(path, content)
```

### session-query Integration

```python
# session-query should integrate context-retrieve logic
# for --mode capsule

def session_query(query, mode="recent"):
    if mode == "capsule":
        return context_retrieve(query)
    # ... other modes
```

### verify-and-close Integration

```python
# finalize-response should require verify-and-close receipt
# before allowing completion output

def finalize_response(task_id, summary):
    # Check for receipt from verify-and-close
    if not receipt_exists(task_id):
        return BLOCK("Run verify-and-close first")
    # ... continue
```
