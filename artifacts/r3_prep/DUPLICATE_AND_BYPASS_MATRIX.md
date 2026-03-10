# Duplicate and Bypass Matrix

**Generated**: 2026-03-10 06:25 CST
**Version**: 1.0
**Purpose**: Identify redundant entry points, conflicting rules, and bypass paths

---

## 1. Memory Retrieval Duplication

### Current State

```
┌─────────────────────────────────────────────────────────────────┐
│                    MEMORY RETRIEVAL CHAOS                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Agent ──┬── session-query ──────→ SQLite FTS                 │
│           │                                                      │
│           ├── memory-retrieve ────→ ? (unclear backend)         │
│           │                                                      │
│           ├── memory-search ──────→ ? (unclear backend)         │
│           │                                                      │
│           └── context-retrieve ───→ OpenViking + Capsule        │
│                                                                 │
│   session-start-recovery ────────→ (uses session-query?)       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Problem Analysis

| Tool | Purpose | Backend | Overlap |
|------|---------|---------|---------|
| session-query | Unified search | SQLite + OpenViking | Baseline |
| memory-retrieve | Memory fetch | Unknown | 80% overlap |
| memory-search | Memory search | Unknown | 70% overlap |
| context-retrieve | Two-tier retrieval | OpenViking + Capsule | 50% overlap |

### Rule Conflicts

- `session-query` documented as main entry in TOOLS.md
- `context-retrieve` is S1-specific, but called for general retrieval
- `memory-retrieve/search` have unclear scope

### Definition Drift

```
session-query: "Unified retrieval across three layers"
context-retrieve: "Two-tier retrieval with explicit source labels"
memory-retrieve: "Memory retrieval" (vague)
memory-search: "Memory search" (vague)
```

### Recommendation

**Merge to session-query with --mode parameter:**

```bash
session-query --mode recent    # Recent events (Layer B)
session-query --mode semantic  # Vector search (Layer C)
session-query --mode keyword   # FTS search (Layer B)
session-query --mode capsule   # Capsule retrieval (S1)
```

**Post-freeze action:**
1. Add `--mode` to session-query
2. Deprecate memory-retrieve, memory-search
3. Keep context-retrieve as S1-specific wrapper

---

## 2. Task Completion Duplication

### Current State

```
┌─────────────────────────────────────────────────────────────────┐
│                    TASK COMPLETION CONFUSION                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Agent ──┬── verify-and-close ────→ Gate A/B/C → receipts     │
│           │                                                      │
│           ├── finalize-response ──→ done-guard check            │
│           │                                                      │
│           ├── enforce-task-completion → Gate enforcement        │
│           │                                                      │
│           └── (direct "完成" output) → BYPASSES ALL            │
│                                                                 │
│   safe-message ──→ output-interceptor ──→ policy check         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Problem Analysis

| Tool | Purpose | When to Use | Overlap |
|------|---------|-------------|---------|
| verify-and-close | Task close | End of task | Baseline |
| finalize-response | Output wrap | Before sending summary | 70% overlap |
| enforce-task-completion | Gate enforcement | Explicit check | 40% overlap |
| safe-message | Safe send | Sending completion msg | 30% overlap |

### Fake Green Light Paths

```
❌ Agent outputs "任务已完成" without verify-and-close
❌ Agent calls finalize-response without receipts
❌ Agent uses safe-message --force to bypass policy
❌ Agent sends directly via message tool
```

### Bypass Detection

**done-guard patterns:**
```
已完成, 全部完成, 可以交付, 已可合并, 
已准备好关闭, 所有阶段通过, 基本完成,
大体完成, 核心已完成, 主要功能完成
```

### Recommendation

**Enforce single flow:**

```
Task complete → verify-and-close → finalize-response → safe-message → user
```

**Post-freeze action:**
1. verify-and-close creates receipt
2. finalize-response requires receipt
3. safe-message requires finalize-response pass
4. Block direct message tool for completion content

---

## 3. State Writing Duplication

### Current State

```
┌─────────────────────────────────────────────────────────────────┐
│                      STATE WRITE CONFUSION                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Agent ──┬── safe-write ────────→ policy check → write        │
│           │                                                      │
│           ├── state-write-atomic ─→ atomic write (no check?)   │
│           │                                                      │
│           ├── state-journal-append → WAL append                 │
│           │                                                      │
│           └── edit tool ──────────→ ❌ BLOCKED by policy       │
│                                                                 │
│   Internal calls:                                                │
│   - session-start-recovery → state-write-atomic?               │
│   - continuity-event-log → state-journal-append                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Problem Analysis

| Tool | Purpose | Policy Check | Overlap |
|------|---------|--------------|---------|
| safe-write | General write | ✅ Yes | Baseline |
| safe-replace | Content replace | ✅ Yes | Variant |
| state-write-atomic | Atomic write | ❓ Unclear | 90% overlap |
| state-journal-append | WAL append | ❌ No | Complementary |

### Rule Conflict

```
SOUL.md: "禁止 edit/write 直接操作 ~/.openclaw/"
TOOLS.md: "safe-write 是主入口"
```

But `state-write-atomic` is used for SESSION-STATE.md without clear policy check.

### Recommendation

**Unify to safe-write:**

```python
# state-write-atomic should call safe-write internally
def state_write_atomic(path, content):
    return safe_write(path, content)  # Policy check inside
```

**Post-freeze action:**
1. state-write-atomic internally calls safe-write
2. Document that state-write-atomic is SESSION-STATE.md specific
3. All other writes use safe-write

---

## 4. Callback Handling Duplication

### Current State

```
┌─────────────────────────────────────────────────────────────────┐
│                    CALLBACK HANDLING CHAOS                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Subagent done ──┬── subagent-inbox ──────→ receipt stored    │
│                   │                                              │
│                   ├── callback-worker ──────→ process + notify │
│                   │                                              │
│                   ├── subagent-completion-handler → update state│
│                   │                                              │
│                   ├── handle-subagent-complete → unified check │
│                   │                                              │
│                   └── callback-handler ──────→ ❌ DEPRECATED   │
│                                                                 │
│   Heartbeat ────────→ handle-subagent-complete → spawn_next?   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Problem Analysis

| Tool | Purpose | Status | Overlap |
|------|---------|--------|---------|
| subagent-inbox | Receipt storage | Active | Baseline |
| callback-worker | Process + notify | Active v8.0 | 80% overlap |
| subagent-completion-handler | Update state | Active | 60% overlap |
| handle-subagent-complete | Unified check | Active | 70% overlap |
| callback-handler | Old callback | DEPRECATED | Delete |

### Flow Confusion

```
Current: Multiple tools call each other in unclear ways

Desired:
  Subagent done → subagent-inbox → callback-worker (systemd)
                                    ↓
                              subagent-completion-handler
                                    ↓
                              handle-subagent-complete (heartbeat)
```

### Recommendation

**Clarify single path:**

```
1. Subagent writes to subagent-inbox
2. callback-worker (systemd) processes inbox
3. subagent-completion-handler updates WORKFLOW_STATE
4. handle-subagent-complete (heartbeat) spawns next

Remove: callback-handler (deprecated)
```

---

## 5. Execution Policy Bypass Paths

### Identified Bypasses

| Path | Risk Level | Mitigation |
|------|------------|------------|
| `safe-message --force` | HIGH | Remove --force or require audit log |
| `message` tool direct | HIGH | Block for completion content |
| `trigger-policy` | MEDIUM | Admin only, audit log |
| `memory-lancedb-seed` | MEDIUM | Debug only, requires confirmation |
| `execution-policy-enforcer` disable | HIGH | Runtime config, not user accessible |

### False Safety Paths

```
❌ "I used finalize-response, task is complete"
   → finalize-response only checks text, not receipts

❌ "I called policy-doctor, everything is fine"
   → policy-doctor is diagnostic, not enforcement

❌ "safe-message succeeded, policy passed"
   → safe-message --force bypasses policy
```

### Recommendation

**Close bypasses:**

1. Remove `--force` from safe-message
2. Add receipt check to finalize-response
3. Block message tool for completion patterns
4. Audit log for trigger-policy usage

---

## 6. Heartbeat Check Duplication

### Current State

```
HEARTBEAT.md calls:
  1. session-start-recovery --recover
  2. route-rebind-guard-heartbeat
  3. probe-execution-policy-v2 --quick
  4. agent-self-health-scheduler --mode quick
  5. handle-subagent-complete
  6. shadow_watcher (conditional)
```

### Overlap Analysis

| Check | Purpose | Overlap |
|-------|---------|---------|
| session-start-recovery | State recovery | None |
| route-rebind-guard-heartbeat | Route guard | None |
| probe-execution-policy-v2 | Policy health | 20% with agent-self-health |
| agent-self-health-scheduler | General health | 20% with probe |
| handle-subagent-complete | Subagent check | None |
| shadow_watcher | Compaction preview | None |

### Potential Consolidation

```
probe-execution-policy-v2 could be merged into agent-self-health-scheduler
  → agent-self-health-scheduler --mode quick --include-policy
```

---

## Summary Matrix

| Area | Duplicate Count | Bypass Risk | Consolidation Priority |
|------|-----------------|-------------|------------------------|
| Memory retrieval | 4 tools | Low | P1 |
| Task completion | 3 tools | High | P0 |
| State writing | 2 tools | Medium | P1 |
| Callback handling | 5 tools | Low | P2 |
| Execution policy | 2 tools | High | P0 |
| Heartbeat checks | 2 probes | Low | P3 |

---

## Post-Freeze Priority Order

1. **P0**: Close task completion bypasses
2. **P0**: Remove safe-message --force
3. **P1**: Merge memory retrieval tools
4. **P1**: Unify state writing
5. **P2**: Clean up callback handlers
6. **P3**: Consolidate heartbeat probes
