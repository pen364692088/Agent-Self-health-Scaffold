# OpenClaw Function Inventory

**Audit Date**: 2026-03-09
**Version**: v1.0
**Scope**: Historical key functions audit - Phase 1

---

## Overview

This document provides a structured inventory of OpenClaw's key functions, organized by category. It includes both currently managed capabilities and those implemented but not yet formally managed.

---

## 1. Main Loop / Infrastructure

| function_id | function_name | component | category | description | source_file |
|-------------|---------------|-----------|----------|-------------|-------------|
| INFRA-001 | heartbeat_mechanism | agent-self-health-scheduler | infrastructure | Periodic health monitoring with quick/full/gate modes; cooldown enforcement; component snapshots | tools/agent-self-health-scheduler |
| INFRA-002 | scheduler_cron | systemd-timers | infrastructure | Timer-based scheduling for self-health checks (quick/full/gate intervals) | templates/systemd/agent-self-health-*.timer |
| INFRA-003 | callback-worker | callback-worker | infrastructure | Processes subagent receipts, sends Telegram notifications, wakes main session | tools/callback-worker |
| INFRA-004 | mailbox-worker | subagent-inbox | infrastructure | Persistent mailbox for subagent completion receipts with atomic writes | tools/subagent-inbox |
| INFRA-005 | preflight_doctor | tool_doctor | infrastructure | Preflight checks for tools before delivery (config, health, sample calls) | tools/tool_doctor |
| INFRA-006 | execution_guard | verify-and-close | infrastructure | Unified task completion entry point with Gate A/B/C enforcement | tools/verify-and-close |
| INFRA-007 | session_continuity | session-start-recovery | infrastructure | Session state recovery with WAL, conflict resolution, uncertainty flags | tools/session-start-recovery |
| INFRA-008 | always_on_policy | agent-self-health-scheduler | infrastructure | Continuous health monitoring with dedup/cooldown/lock/budget guards | templates/systemd/, POLICIES/OPENCLAW_ALWAYS_ON_POLICY.md |

---

## 2. Core Runtime Chain

| function_id | function_name | component | category | description | source_file |
|-------------|---------------|-----------|----------|-------------|-------------|
| RUNTIME-001 | compaction_executor | context-compress | runtime | Context compression executor with shadow/enforced modes; capsule building | tools/context-compress |
| RUNTIME-002 | context_overflow_handling | context-budget-check | runtime | Context budget monitoring with pressure thresholds (light/standard/strong) | tools/context-budget-check |
| RUNTIME-003 | retrieval_system | context-retrieve | runtime | Two-tier retrieval (L1: capsule/keyword, L2: OpenViking vector enhancement) | tools/context-retrieve |
| RUNTIME-004 | openviking_retrieval | OpenViking | runtime | Vector-based semantic search for context retrieval | artifacts/openviking/ |
| RUNTIME-005 | summary_generation | capsule-builder | runtime | Capsule generation for context compression with retrieval keys | tools/capsule-builder |
| RUNTIME-006 | incident_recording | agent-incident-report | runtime | Health incident capture with severity levels (YELLOW/ORANGE/RED) | tools/agent-incident-report |
| RUNTIME-007 | recovery_summary | session-start-recovery | runtime | Recovery summary generation with conflict detection and resolution | tools/session-start-recovery |
| RUNTIME-008 | handoff_continuity | handoff-create | runtime | Handoff creation for session continuity across sessions | tools/handoff-create |
| RUNTIME-009 | continuity_event_logging | continuity-event-log | runtime | Event logging for session continuity with identity fields | tools/continuity-event-log |
| RUNTIME-010 | session_state_doctor | session-state-doctor | runtime | Session state health verification and repair | tools/session-state-doctor |
| RUNTIME-011 | memory_retrieval | memory-retrieve | runtime | Two-stage memory retrieval (pinned first, semantic fallback) | tools/memory-retrieve |

---

## 3. Long-Running Task / Background Systems

| function_id | function_name | component | category | description | source_file |
|-------------|---------------|-----------|----------|-------------|-------------|
| LONG-001 | self_health_scheduler | agent-self-health-scheduler | background | Continuous health scheduling with quick/full/gate modes | tools/agent-self-health-scheduler |
| LONG-002 | watchdog_monitor | execution-degradation-monitor | background | Execution degradation detection and alerting | tools/execution-degradation-monitor |
| LONG-003 | task_queue | task-ledger | background | Task state persistence for parent-child agent coordination | tools/task-ledger |
| LONG-004 | stuck_task_handling | subagent-inbox | background | Claimed timeout recovery (TTL 5min), stale detection | tools/subagent-inbox |
| LONG-005 | soak_monitoring | soak-monitor | background | Long-running test monitoring and verdict checking | tools/soak-monitor |
| LONG-006 | daily_health_check | session-continuity-daily-check | background | Daily session continuity verification | tools/session-continuity-daily-check |
| LONG-007 | retention_gc | subagent-inbox cleanup | background | Automatic cleanup of processed receipts (7-30 days retention) | tools/subagent-inbox |
| LONG-008 | budget_monitoring | context-budget-check | background | Context budget snapshots and monitoring | artifacts/budget_snapshots/ |

---

## 4. Multi-Agent / Orchestration

| function_id | function_name | component | category | description | source_file |
|-------------|---------------|-----------|----------|-------------|-------------|
| ORCH-001 | subagent_orchestrate | subtask-orchestrate | orchestration | Unified entry point for subagent task management | tools/subtask-orchestrate |
| ORCH-002 | callback_routing | callback-worker | orchestration | Routes subagent completion callbacks to appropriate handlers | tools/callback-worker |
| ORCH-003 | task_dispatch | spawn-with-callback | orchestration | Creates subagent tasks with callback instructions | tools/spawn-with-callback |
| ORCH-004 | agent_coordination | subagent-completion-handler | orchestration | Handles subagent completion and workflow progression | tools/subagent-completion-handler |
| ORCH-005 | orchestrator_cli | orchestrator-cli | orchestration | CLI for orchestrator operations | tools/orchestrator/orchestrator-cli |
| ORCH-006 | multi_spawn | multi-spawn | orchestration | Parallel subagent spawning support | tools/multi-spawn |
| ORCH-007 | subagent_conflict | subagent-conflict | orchestration | Conflict detection and resolution for concurrent subagents | tools/subagent-conflict |
| ORCH-008 | workflow_auto_advance | callback-handler-auto-advance | orchestration | Automatic workflow progression after subagent completion | tools/callback-handler-auto-advance |

---

## 5. User-Committed Features

| function_id | function_name | component | category | description | source_file |
|-------------|---------------|-----------|----------|-------------|-------------|
| USER-001 | telegram_notification | callback-worker | user_feature | Direct Telegram notification via openclaw message send | tools/callback-worker |
| USER-002 | daily_summary_report | callback-daily-summary | user_feature | Daily summary generation and delivery | tools/callback-daily-summary |
| USER-003 | emotion_detection | OpenEmotion | user_feature | Real-time emotion detection from user messages | OpenEmotion/ |
| USER-004 | session_archive | session-archive | user_feature | Session archiving with content distillation | tools/session-archive |
| USER-005 | project_check | project-check | user_feature | Project health checking and status reporting | tools/project-check |
| USER-006 | s1_dashboard | s1-dashboard | user_feature | S1 metrics dashboard | tools/s1-dashboard |

---

## 6. Security / Governance

| function_id | function_name | component | category | description | source_file |
|-------------|---------------|-----------|----------|-------------|-------------|
| SEC-001 | gate_a_check | gate1-check | governance | Contract/Spec/Scope validation for task completion | tools/gate1-check |
| SEC-002 | gate_b_check | verify-and-close | governance | Receipt verification (contract/e2e/preflight/final) | tools/verify-and-close |
| SEC-003 | gate_c_check | verify-and-close | governance | State machine validation and human_failed rollback | tools/verify-and-close |
| SEC-004 | proposal_boundary | POLICIES/AGENT_SELF_HEALTH_POLICY.md | governance | Level A/B/C actions boundary enforcement | POLICIES/AGENT_SELF_HEALTH_POLICY.md |
| SEC-005 | dedup_cooldown | agent-self-health-scheduler | governance | Incident and proposal deduplication with cooldown | tools/agent-self-health-scheduler |
| SEC-006 | lock_mechanism | state-lock | governance | File-based locking for state files | tools/state-lock |
| SEC-007 | budget_guard | context-budget-check | governance | Context budget enforcement with thresholds | tools/context-budget-check |
| SEC-008 | rollback_path | verify-and-close | governance | Human_failed → repairing → reverify path enforcement | tools/verify-and-close |
| SEC-009 | capability_truth | verify-and-close | governance | Receipt validation against actual capabilities | tools/verify-and-close |
| SEC-010 | gate_eval | gate-eval | governance | Independent Gate 1 evaluation with sample thresholds | tools/gate-eval |
| SEC-011 | done_guard | done-guard | governance | Completion interception with fake-done detection | tools/done-guard |
| SEC-012 | finalize_response | finalize-response | governance | Output layer enforcement before user messages | tools/finalize-response |
| SEC-013 | safe_message | safe-message | governance | Safe message sending with execution policy checks | tools/safe-message |
| SEC-014 | output_interceptor | output-interceptor | governance | Output channel interception for completion validation | tools/output-interceptor |
| SEC-015 | write_policy | safe-write, safe-replace | governance | Controlled write policies for ~/.openclaw paths | tools/safe-write, tools/safe-replace |

---

## 7. Data Persistence & Recovery

| function_id | function_name | component | category | description | source_file |
|-------------|---------------|-----------|----------|-------------|-------------|
| DATA-001 | wal_protocol | state-journal-append | persistence | Write-ahead logging for state changes | tools/state-journal-append |
| DATA-002 | atomic_write | state-write-atomic | persistence | Atomic file writing for state persistence | tools/state-write-atomic |
| DATA-003 | session_index | session-indexer | persistence | Session log indexing for retrieval | tools/session-indexer |
| DATA-004 | session_query | session-query | persistence | Unified session retrieval interface | tools/session-query |

---

## 8. Testing & Validation

| function_id | function_name | component | category | description | source_file |
|-------------|---------------|-----------|----------|-------------|-------------|
| TEST-001 | hook_smoke_test | hook_smoke_test | testing | Smoke tests for hooks and tools | tools/hook_smoke_test |
| TEST-002 | openviking_l2_smoke | openviking-l2-smoke-test | testing | L2 retrieval smoke tests | tools/openviking-l2-smoke-test |
| TEST-003 | trigger_validation | trigger-validation-test | testing | Trigger mechanism validation | tools/trigger-validation-test |
| TEST-004 | callback_acceptance | test-callback-acceptance | testing | Callback acceptance tests | tools/test-callback-acceptance |
| TEST-005 | path_b_acceptance | test-path-b-acceptance | testing | Path B acceptance tests | tools/test-path-b-acceptance |
| TEST-006 | verify_callback_guards | verify-callback-guards | testing | Callback guard verification | tools/verify-callback-guards |

---

## Summary Statistics

| Category | Count | Notes |
|----------|-------|-------|
| Infrastructure | 8 | Core platform functions |
| Runtime Chain | 11 | Context and retrieval |
| Background Systems | 8 | Long-running tasks |
| Orchestration | 8 | Multi-agent coordination |
| User Features | 6 | Committed deliverables |
| Security/Governance | 15 | Gates and enforcement |
| Data Persistence | 4 | State management |
| Testing | 6 | Validation tools |
| **Total** | **66** | Unique functions identified |

---

## Implementation Status

| Status | Count | Description |
|--------|-------|-------------|
| Implemented & Managed | 45 | Fully integrated with governance |
| Implemented, Not Managed | 18 | Functional but lacking formal tracking |
| Scaffold/Partial | 3 | Architecture defined, incomplete implementation |

---

## Key Dependencies

### Critical Path Dependencies

```
heartbeat_mechanism → callback-worker → subagent-inbox → verify-and-close
                     ↓
              session-start-recovery → continuity-event-log
```

### Retrieval Dependencies

```
context-retrieve → capsule-builder → context-compress
                ↓
          memory-retrieve → OpenViking (optional L2)
```

### Orchestration Dependencies

```
subtask-orchestrate → spawn-with-callback → subagent-inbox
                    ↓
            subagent-completion-handler → callback-worker
```

---

## Notes on "Implemented but Not Managed"

The following functions are implemented but lack formal governance tracking:

1. **memory-retrieve** - Two-stage retrieval works but lacks Gate integration
2. **task-ledger** - Task persistence exists but not linked to workflow state
3. **orchestrator-cli** - CLI exists but not formally documented in TOOLS.md
4. **multi-spawn** - Parallel spawn capability exists but no formal coordination
5. **s1-dashboard** - Dashboard exists but no health monitoring integration

---

## Recommendations

### Phase 2: Gap Analysis

1. Identify functions missing from governance policies
2. Map implicit dependencies not captured in receipts
3. Audit capability truth alignment for unmanaged functions

### Phase 3: Integration Priority

1. **High Priority**: memory-retrieve, task-ledger integration
2. **Medium Priority**: orchestrator-cli formalization, multi-spawn coordination
3. **Low Priority**: Dashboard health integration, legacy tool cleanup

---

*Generated by OpenClaw Capability Coverage Audit*
*Audit Session: 2026-03-09*
