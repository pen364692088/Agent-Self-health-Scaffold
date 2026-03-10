# Canonical Mainline Map

**Generated**: 2026-03-10 06:20 CST
**Version**: 1.0
**Purpose**: Define the single recommended primary entry for each capability

---

## Core Capabilities Mainline

### 1. Task Close

```
CANONICAL ENTRY: verify-and-close

Flow:
  verify-and-close → Gate A/B/C → receipts → READY_TO_CLOSE

Alternatives (SPECIALIZED):
  - enforce-task-completion (Gate enforcement only)
  - finalize-response (Output wrapping, not close)

Bypass paths to BLOCK:
  - Direct "task complete" output without verify-and-close
  - finalize-response without prior verify-and-close

Integration points:
  - Called by: Agent (explicit)
  - Calls: gate-eval, receipt-signer, state-write-atomic
  - Emits: READY_TO_CLOSE | BLOCKED
```

---

### 2. Reply Finish / Message Send

```
CANONICAL ENTRY: safe-message

Flow:
  safe-message → output-interceptor → policy check → message tool → SEND

Alternatives:
  - message tool (direct, BYPASSES POLICY) - DO NOT USE for completion messages
  - callback-worker (internal, auto-notify only)

Bypass paths to BLOCK:
  - Direct message tool call for "完成" content
  - safe-message --force (only for emergencies)

Integration points:
  - Called by: Agent, callback-worker
  - Calls: output-interceptor, message tool
  - Emits: ALLOW | BLOCK
```

---

### 3. Memory Capture

```
CANONICAL ENTRY: memory_store (OpenClaw tool)

Flow:
  memory_store → LanceDB → vector index → STORED

Auto path (FROZEN):
  autoCapture (agent_end hook) → shouldCapture → memory_store

Alternatives:
  - memory-lancedb-seed (debug/seed only, NOT production)

Bypass paths to BLOCK:
  - Direct LanceDB writes bypassing memory_store
  - Disabling autoCapture for normal operations

Integration points:
  - Called by: Agent (explicit), autoCapture (auto)
  - Calls: LanceDB, embedding model
  - Emits: memory_id

FROZEN STATUS: autoCapture logic frozen during observation window
```

---

### 4. Memory Recall

```
CANONICAL ENTRY: session-query

Flow:
  session-query --mode <mode> → Layer B (SQLite) / Layer C (OpenViking) → RESULTS

Modes (proposed post-freeze):
  --mode recent    → Recent session events
  --mode semantic  → Vector search (OpenViking)
  --mode keyword   → FTS search (SQLite)
  --mode capsule   → Capsule retrieval

Current alternatives (to merge):
  - memory-retrieve → session-query --mode semantic
  - memory-search → session-query --mode keyword
  - context-retrieve → session-query --mode capsule (S1)

Integration points:
  - Called by: Agent, session-start-recovery
  - Calls: SQLite DB, OpenViking (optional)
  - Emits: JSON results

Proposed change: Add --mode parameter to session-query
```

---

### 5. Policy Enforcement

```
CANONICAL ENTRY: policy-eval

Flow:
  policy-eval --path <path> --tool <tool> → rule evaluation → ALLOW | DENY | WARN

Alternatives:
  - write-policy-check (specialized for write ops)
  - probe-execution-policy-v2 (heartbeat probe)

Integration points:
  - Called by: execution-policy-enforcer hook, Agent (explicit)
  - Calls: EXECUTION_POLICY_RULES.yaml
  - Emits: {decision, rule_id, message}

Hook integration:
  execution-policy-enforcer → policy-eval → BLOCK if DENY
```

---

### 6. Heartbeat Health Check

```
CANONICAL ENTRY: agent-self-health-scheduler --mode quick

Flow:
  Heartbeat prompt → HEARTBEAT.md → multiple probes → HEARTBEAT_OK | ALERT

Components (in order):
  1. Session Recovery Check → session-start-recovery --recover
  2. State Flush Check → context check
  3. Route Rebind Guard → route-rebind-guard-heartbeat
  4. Execution Policy Check → probe-execution-policy-v2 --quick
  5. Self-Health Quick Mode → agent-self-health-scheduler --mode quick
  6. Subagent Completion Check → handle-subagent-complete
  7. Shadow Mode Check (conditional) → shadow_watcher

Integration points:
  - Triggered by: OpenClaw heartbeat prompt
  - Calls: Multiple probes
  - Emits: HEARTBEAT_OK | ALERT: <reason>
```

---

## Secondary Capabilities Mainline

### 7. Subagent Orchestration

```
CANONICAL ENTRY: subtask-orchestrate

Flow:
  subtask-orchestrate run → check inbox → spawn → track

Sub-commands:
  run "<task>" -m <model>  → Create and spawn task
  status                   → Show workflow state
  resume                   → Resume pending work

Alternatives (DO NOT USE directly):
  - spawn-with-callback (low-level)
  - sessions_spawn (OpenClaw core, bypasses orchestration)
  - cc-spawn (legacy)

Integration points:
  - Called by: Agent (explicit)
  - Calls: subagent-inbox, spawn-with-callback
  - Emits: task_id, run_id
```

---

### 8. State Persistence

```
CANONICAL ENTRY: safe-write

Flow:
  safe-write <path> <content> → policy check → atomic write → SUCCESS

For SESSION-STATE.md specifically:
  state-write-atomic SESSION-STATE.md "<content>"

Alternatives:
  - state-write-atomic (wrapper for safe-write, specialized)
  - exec + heredoc (shell path, allowed)

BLOCKED:
  - edit tool for ~/.openclaw/**
  - write tool for managed paths

Integration points:
  - Called by: Agent, state machine
  - Calls: policy-eval internally
  - Emits: SUCCESS | DENY
```

---

### 9. Session Recovery

```
CANONICAL ENTRY: session-start-recovery

Flow:
  session-start-recovery --recover → read state files → validate → recover

State files:
  1. SESSION-STATE.md (objective, phase, branch)
  2. working-buffer.md (current focus)
  3. handoff.md (if present)
  4. WAL (session_continuity_events.jsonl)

Integration points:
  - Called by: HEARTBEAT.md (auto), Agent (explicit)
  - Calls: session-query (proposed post-freeze)
  - Emits: {recovered, is_new_session, uncertainty_flag}

Event log:
  → state/session_continuity_events.jsonl
```

---

### 10. Context Compression

```
CANONICAL ENTRY: auto-context-compact (auto) / context-compress (manual)

Flow:
  context > 80% → auto-context-compact → capsule-builder → compressed

Components:
  - context-budget-check: Token estimation
  - capsule-builder: Extract high-signal content
  - context-compress: Execute compression
  - prompt-assemble: Reassemble prompt

Integration points:
  - Triggered by: pre-reply-guard (auto), Agent (manual)
  - Calls: capsule-builder, context-retrieve
  - Emits: compression_ratio
```

---

## Mainline Decision Matrix

| Capability | Canonical Entry | Alternatives | Bypass Risk |
|------------|-----------------|--------------|-------------|
| Task Close | verify-and-close | finalize-response | Low (gate enforced) |
| Message Send | safe-message | message tool | Medium (--force) |
| Memory Capture | memory_store | memory-lancedb-seed | Low (frozen) |
| Memory Recall | session-query | memory-retrieve, memory-search | Low (consolidation) |
| Policy Enforcement | policy-eval | write-policy-check | Low (hook enforced) |
| Heartbeat | HEARTBEAT.md probes | None | None |
| Subagent Orchestrate | subtask-orchestrate | spawn-with-callback | Medium (direct spawn) |
| State Persistence | safe-write | exec + heredoc | Low (policy enforced) |
| Session Recovery | session-start-recovery | None | None |
| Context Compression | auto-context-compact | context-compress | None |

---

## Enforcement Mechanisms

### Gate A: Policy Verification
- Hook: `execution-policy-enforcer`
- Checks: Path patterns, tool usage
- Block: DENY decisions

### Gate B: Tool Availability
- Check: Tool exists and executable
- Block: Missing tools

### Gate C: Test Coverage
- Check: Tests pass
- Block: Failing tests

---

## Post-Freeze Consolidation Targets

| Target | Current State | Desired State |
|--------|---------------|---------------|
| Memory recall | 4 separate tools | session-query with --mode |
| Task completion | verify-and-close + finalize-response | Integrated flow |
| State writing | safe-write + state-write-atomic | state-write-atomic calls safe-write |
| Callback handling | 3 handlers | subagent-completion-handler only |
