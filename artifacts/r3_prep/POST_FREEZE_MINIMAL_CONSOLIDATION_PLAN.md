# Post-Freeze Minimal Consolidation Plan

**Generated**: 2026-03-10 06:35 CST
**Version**: 1.0
**Observation Window End**: ~2026-03-13 to 2026-03-17
**Status**: PLANNING ONLY - No execution during freeze

---

## Execution Timeline

```
┌─────────────────────────────────────────────────────────────────┐
│                     CONSOLIDATION TIMELINE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  NOW         │ Freeze continues, observation metrics collected │
│  ~Mar 13-17  │ Observation window ends, freeze lifted          │
│  Day 1-2     │ Phase 1: Delete deprecated tools                │
│  Day 3-5     │ Phase 2: Merge duplicates                       │
│  Day 6-7     │ Phase 3: Close bypass paths                     │
│  Day 8-10    │ Phase 4: Integration and testing                │
│  Day 11+     │ Monitoring and rollback watch                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Delete Deprecated Tools (Day 1-2)

### Tools to Delete

| Tool | Location | Reason | Risk |
|------|----------|--------|------|
| verify-and-close-v2 | tools/verify-and-close-v2 | Superseded by v1.2 | None |
| check-subagent-mailbox | tools/legacy/check-subagent-mailbox | Deprecated | None |
| callback-handler | tools/callback-handler | Replaced by subagent-completion-handler | Low |
| session-archive.original | tools/session-archive.original | Backup file | None |
| session-start-recovery.bak | tools/session-start-recovery.bak | Backup file | None |

### Pre-Delete Verification

```bash
# Check for any remaining references
grep -r "verify-and-close-v2" tools/ 2>/dev/null
grep -r "check-subagent-mailbox" tools/ 2>/dev/null
grep -r "callback-handler" tools/ --exclude="callback-handler-auto" 2>/dev/null
```

### Rollback Point

```bash
# Tag before deletion
git tag pre-consolidation-phase1
git commit -am "Pre-Phase 1: Document deprecated tools to delete"
```

---

## Phase 2: Merge Duplicates (Day 3-5)

### P1: Memory Retrieval Consolidation

**Target**: Merge memory-retrieve, memory-search into session-query

**Changes**:

```python
# session-query: Add --mode parameter

def session_query(query, mode="recent", limit=10):
    if mode == "recent":
        return query_recent_events(query, limit)
    elif mode == "semantic":
        return query_vector_search(query, limit)  # OpenViking
    elif mode == "keyword":
        return query_fts_search(query, limit)     # SQLite FTS
    elif mode == "capsule":
        return query_capsules(query, limit)       # S1 capsules
```

**Migration**:

```
memory-retrieve → session-query --mode semantic
memory-search → session-query --mode keyword
```

**Deprecation Notice**:

```python
# memory-retrieve: Add deprecation warning
def memory_retrieve(query):
    warnings.warn(
        "memory-retrieve is deprecated. Use session-query --mode semantic",
        DeprecationWarning
    )
    return session_query(query, mode="semantic")
```

**Testing**:

```bash
# Verify session-query covers all modes
python tests/test_session_query_modes.py

# Verify memory-retrieve still works (deprecation)
python tools/memory-retrieve --test
```

---

### P2: State Writing Unification

**Target**: state-write-atomic internally calls safe-write

**Changes**:

```python
# state-write-atomic: Delegate to safe-write

def state_write_atomic(path, content):
    """
    Atomic state write with policy check.
    Internally uses safe-write for policy enforcement.
    """
    # Use safe-write for policy check
    return safe_write(path, content, atomic=True)
```

**Files to Update**:

- `tools/state-write-atomic`
- Documentation: TOOLS.md, SOUL.md

**Testing**:

```bash
# Verify policy check is performed
python tools/state-write-atomic ~/.openclaw/workspace/test.md "test" --dry-run
# Should show policy evaluation
```

---

### P3: Probe Consolidation

**Target**: Merge probe-execution-policy into probe-execution-policy-v2

**Changes**:

```
probe-execution-policy → probe-execution-policy-v2 (rename)
probe-execution-policy-v2 → probe-execution-policy (final name)
```

**Migration**:

```bash
# Add alias for backward compatibility
ln -s probe-execution-policy probe-execution-policy-v2
```

---

## Phase 3: Close Bypass Paths (Day 6-7)

### B1: Remove safe-message --force

**Current**:

```python
if args.force:
    print("[FORCED] Would send...")
    return 0
```

**Change**:

```python
if args.force:
    # Log to audit instead of bypassing
    audit_log("safe-message --force attempted", task_id, message)
    return error("Force mode removed. Use message tool directly for emergencies.")
```

**Alternative for Emergencies**:

```bash
# Direct message tool with audit log
audit-log "Emergency message send" && message --action send --to user --message "..."
```

---

### B2: Block Direct message Tool for Completion Content

**Approach**: Runtime-level check (requires OpenClaw core change)

**Detection**:

```python
COMPLETION_PATTERNS = [
    r"已完成", r"全部完成", r"可以交付", r"任务完成",
    r"task.*complete", r"finished", r"done"
]

def check_message_content(message):
    for pattern in COMPLETION_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return BLOCK("Use safe-message for completion messages")
    return ALLOW
```

**Note**: This requires coordination with OpenClaw core. For now, document in SOUL.md.

---

### B3: Add Receipt Check to finalize-response

**Current**: finalize-response checks text patterns only

**Change**:

```python
def finalize_response(task_id, summary):
    # Check for receipt from verify-and-close
    receipt_path = f"artifacts/receipts/{task_id}_final_receipt.json"
    if not Path(receipt_path).exists():
        return BLOCK("No receipt found. Run verify-and-close first.")
    
    # Continue with done-guard check
    ...
```

---

## Phase 4: Integration and Testing (Day 8-10)

### Test Suite Updates

```
tests/
├── test_session_query_modes.py      # New: session-query --mode tests
├── test_state_write_integration.py  # New: safe-write integration
├── test_bypass_prevention.py        # New: bypass path tests
├── test_consolidation.py            # New: overall consolidation tests
└── test_regression.py               # Updated: regression tests
```

### Integration Tests

```python
# test_consolidation.py

def test_memory_retrieval_consolidation():
    """Verify session-query covers all modes"""
    result = subprocess.run(
        ["session-query", "test", "--mode", "semantic"],
        capture_output=True
    )
    assert result.returncode == 0

def test_state_write_policy_check():
    """Verify state-write-atomic checks policy"""
    result = subprocess.run(
        ["state-write-atomic", "~/.openclaw/test.md", "test"],
        capture_output=True
    )
    # Should show policy evaluation in output

def test_bypass_prevention():
    """Verify bypasses are blocked"""
    result = subprocess.run(
        ["safe-message", "--task-id", "test", "--force", "--message", "test"],
        capture_output=True
    )
    assert "Force mode removed" in result.stdout
```

---

## Rollback Strategy

### Rollback Points

```bash
# Create tags at each phase
git tag pre-consolidation-phase1
git tag post-consolidation-phase1
git tag pre-consolidation-phase2
git tag post-consolidation-phase2
git tag pre-consolidation-phase3
git tag post-consolidation-phase3
git tag pre-consolidation-phase4
git tag post-consolidation-phase4  # Final
```

### Rollback Procedure

```bash
# If Phase 2 issues
git checkout post-consolidation-phase1

# If Phase 3 issues
git checkout post-consolidation-phase2

# Full rollback
git checkout pre-consolidation-phase1
```

### Monitoring Signals

| Signal | Threshold | Action |
|--------|-----------|--------|
| Test failures | > 5% | Pause, investigate |
| Heartbeat alerts | > 2/hour | Pause, investigate |
| Policy violations | > 10/hour | Pause, investigate |
| User complaints | Any | Pause, investigate |

---

## Risk Assessment

| Change | Risk Level | Mitigation |
|--------|------------|------------|
| Delete deprecated tools | Low | No active references |
| Merge memory retrieval | Medium | Keep aliases, deprecation warnings |
| Unify state writing | Low | Internal change only |
| Remove --force | Medium | Provide alternative for emergencies |
| Add receipt check | Low | Enforces existing policy |

---

## Minimal Patch Queue (Post-Freeze)

### Batch 1: Safe Deletes (No Testing Required)

```
- tools/verify-and-close-v2
- tools/legacy/check-subagent-mailbox
- tools/session-archive.original
- tools/session-start-recovery.bak
```

### Batch 2: Deprecation Warnings (No Behavior Change)

```
- tools/memory-retrieve: Add deprecation warning
- tools/memory-search: Add deprecation warning
- tools/probe-execution-policy: Add deprecation warning
```

### Batch 3: Integration Changes (Requires Testing)

```
- tools/session-query: Add --mode parameter
- tools/state-write-atomic: Delegate to safe-write
- tools/finalize-response: Add receipt check
- tools/safe-message: Remove --force
```

### Batch 4: Core Changes (Requires Coordination)

```
- OpenClaw core: Block message tool for completion content
- OpenClaw core: Integration with execution-policy-enforcer
```

---

## Success Criteria

### Phase 1 Success

- [ ] All deprecated tools deleted
- [ ] No references to deleted tools
- [ ] All tests pass

### Phase 2 Success

- [ ] session-query supports all modes
- [ ] state-write-atomic uses safe-write
- [ ] Deprecation warnings appear
- [ ] All tests pass

### Phase 3 Success

- [ ] safe-message --force removed
- [ ] finalize-response requires receipt
- [ ] Bypass attempts blocked
- [ ] All tests pass

### Phase 4 Success

- [ ] All integration tests pass
- [ ] No regression in existing tests
- [ ] Documentation updated
- [ ] Monitoring shows no issues for 7 days

---

## Documentation Updates

### Files to Update

| File | Changes |
|------|---------|
| TOOLS.md | Update mainline entries, remove deprecated |
| SOUL.md | Update rules, add consolidation notes |
| memory.md | Update retrieval section |
| HEARTBEAT.md | Update probe list |
| POLICIES/EXECUTION_POLICY.md | Update bypass prevention |

### Commit Message Template

```
R3 Consolidation Phase X: <description>

Changes:
- <change 1>
- <change 2>

Testing:
- <test coverage>
- <verification steps>

Rollback: git checkout <tag>
```
