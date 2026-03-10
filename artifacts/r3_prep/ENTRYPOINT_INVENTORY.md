# Entrypoint Inventory

**Generated**: 2026-03-10 06:15 CST
**Version**: 1.0
**Status**: FROZEN PERIOD - Documentation only

---

## 1. Task Completion / Verify-and-Close Entrypoints

| Name | Location | Trigger | Caller | Purpose | Layer | Main? | Bypass? | Keep? |
|------|----------|---------|--------|---------|-------|-------|---------|-------|
| `verify-and-close` | tools/verify-and-close | Explicit call | Agent | Unified task close | MAIN | ✅ | ❌ | ✅ |
| `verify-and-close-v2` | tools/verify-and-close-v2 | Explicit call | Legacy | Old version | DEPRECATED | ❌ | ❌ | ❌ Delete |
| `enforce-task-completion` | tools/enforce-task-completion | Explicit call | Agent | Gate enforcement | MAIN | ✅ | ❌ | ✅ |
| `finalize-response` | tools/finalize-response | Pre-output | Agent | Output wrap | SPECIALIZED | ⚠️ | ❌ | ✅ Merge |
| `done-guard` | tools/done-guard | Called by finalize | Internal | Fake completion detect | SPECIALIZED | ❌ | ❌ | ✅ |
| `auto-receipt` | tools/auto-receipt | Auto | Internal | Auto receipt gen | INTERNAL | ❌ | ❌ | ✅ |
| `receipt-signer` | tools/receipt-signer | Called | Internal | Receipt signing | INTERNAL | ❌ | ❌ | ✅ |
| `receipt-validator` | tools/receipt-validator | Called | Internal | Receipt validation | INTERNAL | ❌ | ❌ | ✅ |
| `output-interceptor` | tools/output-interceptor | Called | safe-message | Output check | INTERNAL | ❌ | ❌ | ✅ |
| `gate-eval` | tools/gate-eval | Explicit | Agent | Gate evaluation | MAIN | ✅ | ❌ | ✅ |
| `gate-a-signer` | tools/gate-a-signer | Called | Internal | Gate A sign | INTERNAL | ❌ | ❌ | ✅ |
| `gate-b-signer` | tools/gate-b-signer | Called | Internal | Gate B sign | INTERNAL | ❌ | ❌ | ✅ |
| `gate-c-signer` | tools/gate-c-signer | Called | Internal | Gate C sign | INTERNAL | ❌ | ❌ | ✅ |

**Duplicates**: `verify-and-close-v2` (delete after freeze)

**Conflicts**: `finalize-response` overlaps with `verify-and-close` flow - should be integrated

---

## 2. Message Sending / Reply Completion Entrypoints

| Name | Location | Trigger | Caller | Purpose | Layer | Main? | Bypass? | Keep? |
|------|----------|---------|--------|---------|-------|-------|---------|-------|
| `safe-message` | tools/safe-message | Explicit | Agent | Safe msg send | MAIN | ✅ | ⚠️ --force | ✅ |
| `message` tool | OpenClaw core | Direct | Agent, callback | Native send | CORE | ✅ | ❌ | ✅ |
| `callback-worker` | tools/callback-worker | Systemd | Auto | Notify dispatch | INTERNAL | ❌ | ❌ | ✅ |
| `output-interceptor` | tools/output-interceptor | Pre-send | safe-message | Policy check | INTERNAL | ❌ | ❌ | ✅ |
| `testbot-chat` | tools/testbot-chat | Debug | Manual | Test chat | DEBUG | ❌ | ✅ | ⚠️ Debug |

**Critical Path**: `safe-message` → `output-interceptor` → `message` tool

**Bypass Risk**: `safe-message --force` can skip policy check

---

## 3. Memory Capture / Recall / Injection Entrypoints

| Name | Location | Trigger | Caller | Purpose | Layer | Main? | Bypass? | Keep? |
|------|----------|---------|--------|---------|-------|-------|---------|-------|
| `memory_recall` tool | OpenClaw tool | Agent call | Agent | Vector recall | CORE | ✅ | ❌ | ✅ |
| `memory_store` tool | OpenClaw tool | Agent call | Agent | Vector store | CORE | ✅ | ❌ | ✅ |
| `autoCapture` | OpenClaw core | agent_end hook | Auto | Auto capture | INTERNAL | ❌ | ⚠️ disable | ✅ FROZEN |
| `memory-lancedb-seed` | tools/memory-lancedb-seed.mjs | Manual | Admin | Seed data | DEBUG | ❌ | ✅ | ⚠️ Debug |
| `session-query` | tools/session-query | Explicit | Agent | Unified search | MAIN | ✅ | ❌ | ✅ |
| `context-retrieve` | tools/context-retrieve | Called | S1 | Two-tier retrieve | SPECIALIZED | ⚠️ | ❌ | ✅ Merge |
| `memory-retrieve` | tools/memory-retrieve | Explicit | Agent | Memory fetch | SPECIALIZED | ⚠️ | ❌ | ⚠️ Merge |
| `memory-search` | tools/memory-search | Explicit | Agent | Search | SPECIALIZED | ⚠️ | ❌ | ⚠️ Merge |
| `openviking find` | External | Called | context-retrieve | Vector search | LOW-LEVEL | ❌ | ❌ | ✅ |
| `session-indexer` | tools/session-indexer | Cron | Auto | Index sessions | INTERNAL | ❌ | ❌ | ✅ |
| `session-start-recovery` | tools/session-start-recovery | Session start | Auto | State recovery | INTERNAL | ❌ | ❌ | ✅ |

**FROZEN**: `autoCapture` logic - no changes during observation

**Duplicates**: `memory-retrieve`, `memory-search`, `context-retrieve` → consolidate to `session-query`

---

## 4. Execution Policy / Policy-Eval / Heartbeat Entrypoints

| Name | Location | Trigger | Caller | Purpose | Layer | Main? | Bypass? | Keep? |
|------|----------|---------|--------|---------|-------|-------|---------|-------|
| `policy-eval` | tools/policy-eval | Explicit | Agent | Rule evaluation | MAIN | ✅ | ❌ | ✅ |
| `policy-doctor` | tools/policy-doctor | Explicit | Agent | Health check | MAIN | ✅ | ❌ | ✅ |
| `policy-violations-report` | tools/policy-violations-report | Explicit | Agent | Violation report | MAIN | ✅ | ❌ | ✅ |
| `probe-execution-policy` | tools/probe-execution-policy | Heartbeat | Auto | Policy probe | DEBUG | ❌ | ❌ | ✅ |
| `probe-execution-policy-v2` | tools/probe-execution-policy-v2 | Heartbeat | Auto | Policy probe v2 | DEBUG | ❌ | ❌ | ✅ |
| `trigger-policy` | tools/trigger-policy | Manual | Admin | Policy trigger | INTERNAL | ❌ | ✅ | ⚠️ Debug |
| `write-policy-check` | tools/write-policy-check | Pre-write | Hook | Path check | SPECIALIZED | ❌ | ❌ | ✅ |
| `route-rebind-guard-heartbeat` | tools/route-rebind-guard-heartbeat | Heartbeat | Auto | Route guard | INTERNAL | ❌ | ❌ | ✅ |
| `agent-self-health-scheduler` | tools/agent-self-health-scheduler | Heartbeat | Auto | Health scheduler | INTERNAL | ❌ | ❌ | ✅ |

**Duplicates**: `probe-execution-policy` and `probe-execution-policy-v2` - merge to v2

---

## 5. Hooks / Loaders / Lifecycle Entrypoints

| Name | Location | Trigger | Caller | Purpose | Layer | Main? | Bypass? | Keep? |
|------|----------|---------|--------|---------|-------|-------|---------|-------|
| `execution-policy-enforcer` | hooks/execution-policy-enforcer | Pre-tool | Runtime | Policy enforce | INTERNAL | ❌ | ⚠️ disable | ✅ |
| `emotiond-bridge` | hooks/emotiond-bridge | Agent call | Runtime | Emotion bridge | INTERNAL | ❌ | ✅ | ⚠️ Optional |
| `emotiond-enforcer` | hooks/emotiond-enforcer | Pre-response | Runtime | Emotion enforce | INTERNAL | ❌ | ✅ | ⚠️ Optional |
| `session-start-recovery` | tools/session-start-recovery | Session start | Auto | Recovery | INTERNAL | ❌ | ❌ | ✅ |
| `session-archive` | tools/session-archive | Explicit/trigger | Agent | Archive session | SPECIALIZED | ✅ | ❌ | ✅ |
| `handoff-create` | tools/handoff-create | Explicit | Agent | Create handoff | SPECIALIZED | ✅ | ❌ | ✅ |
| `post-compaction-handoff` | tools/post-compaction-handoff | Post-compact | Auto | Compaction handoff | INTERNAL | ❌ | ❌ | ✅ |
| `continuity-event-log` | tools/continuity-event-log | State change | Auto | Event log | INTERNAL | ❌ | ❌ | ✅ |

---

## 6. Callback / Mailbox / Scheduler / Heartbeat Entrypoints

| Name | Location | Trigger | Caller | Purpose | Layer | Main? | Bypass? | Keep? |
|------|----------|---------|--------|---------|-------|-------|---------|-------|
| `subtask-orchestrate` | tools/subtask-orchestrate | Explicit | Agent | Orchestration | MAIN | ✅ | ❌ | ✅ |
| `subagent-inbox` | tools/subagent-inbox | Explicit/Auto | Agent, worker | Receipt inbox | SPECIALIZED | ✅ | ❌ | ✅ |
| `subagent-completion-handler` | tools/subagent-completion-handler | Auto | callback-worker | Process receipt | INTERNAL | ❌ | ❌ | ✅ |
| `handle-subagent-complete` | tools/handle-subagent-complete | Heartbeat | Auto | Unified check | INTERNAL | ❌ | ❌ | ✅ |
| `callback-worker` | tools/callback-worker | Systemd path | Auto | Dispatch notify | INTERNAL | ❌ | ❌ | ✅ |
| `callback-handler` | tools/callback-handler | Explicit | Legacy | Old callback | DEPRECATED | ❌ | ❌ | ❌ Delete |
| `callback-handler-auto` | tools/callback-handler-auto | Auto | Internal | Auto callback | INTERNAL | ❌ | ❌ | ⚠️ Review |
| `spawn-with-callback` | tools/spawn-with-callback | Explicit | subtask-orchestrate | Spawn + callback | DEBUG | ❌ | ❌ | ✅ |
| `check-subagent-mailbox` | tools/legacy/check-subagent-mailbox | Explicit | Legacy | Old mailbox | DEPRECATED | ❌ | ❌ | ❌ Delete |
| `subagent-inbox-metrics` | tools/subagent-inbox-metrics | Explicit | Agent | Inbox metrics | SPECIALIZED | ✅ | ❌ | ✅ |
| `probe-subagent-inbox-metrics` | tools/probe-subagent-inbox-metrics | Heartbeat | Auto | Inbox probe | DEBUG | ❌ | ❌ | ✅ |
| `probe-callback-delivery` | tools/probe-callback-delivery | Heartbeat | Auto | Delivery probe | DEBUG | ❌ | ❌ | ✅ |

**Duplicates**: `callback-handler` (deprecated), `check-subagent-mailbox` (deprecated)

---

## 7. Handoff / Continuity / Recovery / Compaction Entrypoints

| Name | Location | Trigger | Caller | Purpose | Layer | Main? | Bypass? | Keep? |
|------|----------|---------|--------|---------|-------|-------|---------|-------|
| `session-start-recovery` | tools/session-start-recovery | Session start | Auto | Recovery | MAIN | ✅ | ❌ | ✅ |
| `session-state-doctor` | tools/session-state-doctor | Explicit | Agent | State diagnose | MAIN | ✅ | ❌ | ✅ |
| `handoff-create` | tools/handoff-create | Explicit | Agent | Handoff gen | SPECIALIZED | ✅ | ❌ | ✅ |
| `session-archive` | tools/session-archive | Explicit | Agent | Archive | SPECIALIZED | ✅ | ❌ | ✅ |
| `continuity-event-log` | tools/continuity-event-log | State change | Auto | WAL append | INTERNAL | ❌ | ❌ | ✅ |
| `state-write-atomic` | tools/state-write-atomic | Explicit | Agent | Atomic write | SPECIALIZED | ⚠️ | ❌ | ✅ Merge |
| `state-journal-append` | tools/state-journal-append | Called | Internal | WAL | INTERNAL | ❌ | ❌ | ✅ |
| `pre-reply-guard` | tools/pre-reply-guard | Pre-reply | Auto | Context guard | INTERNAL | ❌ | ❌ | ✅ |
| `auto-context-compact` | tools/auto-context-compact | Context > 80% | Auto | Auto compress | INTERNAL | ❌ | ❌ | ✅ |
| `context-compress` | tools/context-compress | Explicit | Agent | Compress | SPECIALIZED | ✅ | ❌ | ✅ |
| `capsule-builder` | tools/capsule-builder | Called | compress | Capsule gen | SPECIALIZED | ✅ | ❌ | ✅ |
| `context-budget-check` | tools/context-budget-check | Explicit | Agent | Budget check | SPECIALIZED | ✅ | ❌ | ✅ |
| `session-continuity-daily-check` | tools/session-continuity-daily-check | Daily | Heartbeat | Daily check | INTERNAL | ❌ | ❌ | ✅ |
| `probe-session-persistence` | tools/probe-session-persistence | Heartbeat | Auto | Persistence probe | DEBUG | ❌ | ❌ | ✅ |
| `probe-handoff-integrity` | tools/probe-handoff-integrity | Heartbeat | Auto | Handoff probe | DEBUG | ❌ | ❌ | ✅ |

**Duplicates**: `state-write-atomic` should internally call `safe-write`

---

## Summary Statistics

| Category | Total | Main | Specialized | Internal | Debug | Deprecated |
|----------|-------|------|-------------|----------|-------|------------|
| Task Completion | 13 | 3 | 2 | 6 | 0 | 2 |
| Message Sending | 5 | 2 | 0 | 2 | 1 | 0 |
| Memory | 11 | 2 | 4 | 3 | 1 | 0 |
| Execution Policy | 9 | 3 | 1 | 2 | 3 | 0 |
| Hooks/Lifecycle | 8 | 0 | 2 | 5 | 0 | 0 |
| Callback/Mailbox | 12 | 2 | 2 | 5 | 2 | 3 |
| Handoff/Continuity | 15 | 3 | 5 | 5 | 2 | 0 |
| **TOTAL** | **73** | **15** | **16** | **28** | **9** | **5** |

---

## Files to Delete (Post-Freeze)

1. `tools/verify-and-close-v2` - Superseded by v1.2
2. `tools/legacy/check-subagent-mailbox` - Deprecated
3. `tools/callback-handler` - Deprecated (use subagent-completion-handler)
4. `tools/session-archive.original` - Backup file
5. `tools/session-start-recovery.bak` - Backup file

---

## Observations

### High-Risk Bypass Paths

1. `safe-message --force` - Can skip policy check
2. `trigger-policy` - Manual policy trigger
3. `memory-lancedb-seed` - Can inject arbitrary data
4. `execution-policy-enforcer` - Can be disabled

### Multiple Entrypoints for Same Purpose

1. **Memory retrieval**: `session-query`, `memory-retrieve`, `memory-search`, `context-retrieve`
2. **Task completion**: `verify-and-close`, `finalize-response`, `done-guard`
3. **State writing**: `safe-write`, `state-write-atomic`, `write-policy-check`
4. **Callback handling**: `subagent-completion-handler`, `callback-handler`, `handle-subagent-complete`

### Missing Canonical Path

Some capabilities have no clear single entry:
- Memory recall: Multiple tools, no unified `--mode` param
- State persistence: `state-write-atomic` vs `safe-write` confusion
