# Capability Coverage Matrix

**Audit Date**: 2026-03-09
**Audit Scope**: OpenClaw Self-Health Mechanism v1.0.0 SCAFFOLD

---

## Summary

| Category | Covered | Partially Covered | Not Covered | N/A |
|----------|---------|-------------------|-------------|-----|
| Core Agent Functions | 2 | 4 | 2 | 0 |
| Subagent Orchestration | 1 | 2 | 1 | 0 |
| Session Management | 1 | 3 | 2 | 0 |
| External Integrations | 0 | 2 | 3 | 1 |
| Governance & Policy | 2 | 2 | 1 | 0 |

---

## Coverage Matrix

### Core Agent Functions

| 功能名 | in_capability_registry | in_capability_check | in_forgetting_guard | in_incident_flow | in_proposal_flow | coverage_status |
|--------|------------------------|---------------------|---------------------|------------------|------------------|-----------------|
| Liveness Check | ❌ | ✅ | ❌ | ✅ | ❌ | `partially_covered` |
| Memory Monitor | ❌ | ✅ | ❌ | ✅ | ❌ | `partially_covered` |
| Context Budget | ❌ | ✅ | ❌ | ✅ | ❌ | `partially_covered` |
| Storage Health | ❌ | ✅ | ❌ | ✅ | ❌ | `partially_covered` |
| Network Connectivity | ❌ | ✅ | ❌ | ❌ | ❌ | `partially_covered` |
| Agent Identity/Persona | ❌ | ❌ | ❌ | ❌ | ❌ | `not_covered` |
| Skill Registry | ❌ | ❌ | ❌ | ❌ | ❌ | `not_covered` |
| Tool Invocation | ❌ | ✅ (via tool_doctor) | ❌ | ❌ | ❌ | `partially_covered` |

### Subagent Orchestration

| 功能名 | in_capability_registry | in_capability_check | in_forgetting_guard | in_incident_flow | in_proposal_flow | coverage_status |
|--------|------------------------|---------------------|---------------------|------------------|------------------|-----------------|
| Subagent Spawn | ❌ | ❌ | ❌ | ❌ | ✅ | `partially_covered` |
| Subagent Failure Detection | ❌ | ✅ | ❌ | ✅ | ✅ | `covered` |
| Subagent Timeout | ❌ | ❌ | ❌ | ❌ | ❌ | `not_covered` |
| Callback Worker | ❌ | ✅ (via Gate B) | ❌ | ❌ | ❌ | `partially_covered` |
| Mailbox Worker | ❌ | ✅ (via Gate B) | ❌ | ❌ | ❌ | `partially_covered` |

### Session Management

| 功能名 | in_capability_registry | in_capability_check | in_forgetting_guard | in_incident_flow | in_proposal_flow | coverage_status |
|--------|------------------------|---------------------|---------------------|------------------|------------------|-----------------|
| Session State Persistence | ❌ | ✅ (via Gate A) | ❌ | ❌ | ✅ | `partially_covered` |
| Handoff Protocol | ❌ | ❌ | ❌ | ❌ | ❌ | `not_covered` |
| WAL Journal | ❌ | ❌ | ❌ | ❌ | ❌ | `not_covered` |
| Recovery Flow | ❌ | ✅ (via Gate B) | ❌ | ❌ | ❌ | `partially_covered` |
| Context Compression | ❌ | ❌ | ❌ | ❌ | ✅ | `partially_covered` |
| Session Continuity Events | ❌ | ✅ (via health_history) | ❌ | ❌ | ❌ | `partially_covered` |

### External Integrations

| 功能名 | in_capability_registry | in_capability_check | in_forgetting_guard | in_incident_flow | in_proposal_flow | coverage_status |
|--------|------------------------|---------------------|---------------------|------------------|------------------|-----------------|
| Telegram Channel | ❌ | ❌ | ❌ | ❌ | ❌ | `not_covered` |
| MCP Servers | ❌ | ✅ (partial) | ❌ | ❌ | ❌ | `partially_covered` |
| GitHub API | ❌ | ❌ | ❌ | ❌ | ❌ | `not_covered` |
| External LLM Router | ❌ | ❌ | ❌ | ❌ | ❌ | `not_covered` |
| ClawRouter | ❌ | ❌ | ❌ | ❌ | ❌ | `not_covered` |
| Local Tools | ❌ | ✅ (via tool_doctor) | ❌ | ❌ | ❌ | `partially_covered` |

### Governance & Policy

| 功能名 | in_capability_registry | in_capability_check | in_forgetting_guard | in_incident_flow | in_proposal_flow | coverage_status |
|--------|------------------------|---------------------|---------------------|------------------|------------------|-----------------|
| SOUL.md Protection | ❌ | ✅ (hard boundary) | ❌ | ✅ | ✅ | `covered` |
| Policy Mutation Detection | ❌ | ✅ (hard boundary) | ❌ | ✅ | ✅ | `covered` |
| Tool Delivery Gates | ❌ | ✅ (Gate A/B/C) | ❌ | ❌ | ❌ | `covered` |
| Execution Policy | ❌ | ✅ (Gate C) | ❌ | ❌ | ❌ | `partially_covered` |
| Audit Trail | ❌ | ✅ | ❌ | ✅ | ✅ | `covered` |
| Self-Heal Whitelist | ❌ | ✅ | ❌ | ✅ | ✅ | `covered` |

---

## Gate Coverage Analysis

### Gate A: Contract Validation
**Scope**: File/policy/tool presence check

| Covered | Not Covered |
|---------|-------------|
| AGENT_SELF_HEALTH_POLICY.md | Capability Registry Schema |
| OPENCLAW_ALWAYS_ON_POLICY.md | Tool Input/Output Schemas |
| tools/agent-health-check | Integration Schemas |
| tools/agent-self-heal | Subagent Capability Schemas |
| tools/agent-self-health-scheduler | Session State Schemas |

**Gap**: No explicit capability registry to validate against.

### Gate B: Runtime Telemetry
**Scope**: Runtime state freshness check

| Covered | Not Covered |
|---------|-------------|
| heartbeat_status.json | Capability Execution Metrics |
| callback_worker_status.json | Feature Usage Telemetry |
| mailbox_worker_status.json | Integration Health Metrics |
| summary_status.json | Session Quality Metrics |

**Gap**: No capability-level telemetry, only component-level.

### Gate C: Preflight Check
**Scope**: Doctor and guard execution

| Covered | Not Covered |
|---------|-------------|
| tool_doctor(agent-health-check) | Skill Capability Doctor |
| pre-reply-guard health | MCP Server Doctor |
| | External Integration Doctor |
| | Capability Effectiveness Check |

**Gap**: No capability-level doctor checks.

---

## Incident/Proposal Flow Coverage

### Incident Triggers
| Trigger | Covered |
|---------|---------|
| Memory threshold exceeded | ✅ |
| Context budget exceeded | ✅ |
| Subagent failures | ✅ |
| Disk usage threshold | ✅ |
| Health level change (YELLOW/ORANGE/RED) | ✅ |

### Missing Incident Triggers
| Trigger | Status |
|---------|--------|
| Capability degradation | ❌ |
| Skill load failure | ❌ |
| Integration timeout | ❌ |
| Policy drift | ❌ |
| Feature effectiveness drop | ❌ |

### Proposal Flow
| Action Type | Level | Coverage |
|-------------|-------|----------|
| clear_cache | A (auto) | ✅ |
| rotate_logs | A (auto) | ✅ |
| retry_subagent | A (auto) | ✅ |
| compact_context | A (auto) | ✅ |
| refresh_session_index | A (auto) | ✅ |
| restart_subsystem | B (proposal) | ✅ |
| reset_session_state | B (proposal) | ✅ |
| promote_hotfix | B (proposal) | ✅ |
| core_config_mutation | C (human) | ✅ |
| router_modification | C (human) | ✅ |
| data_deletion | C (human) | ✅ |

---

## Forgetting Guard Analysis

### Current Status
**Tool**: `agent-forgetting-guard` - **NOT IMPLEMENTED**

### Evidence
- Referenced in memory/2026-03-08.md as planned feature
- No implementation found in tools/ directory
- No schema in schemas/ directory

### Missing Protections
| Capability | Forgetting Risk | Guard Status |
|------------|-----------------|--------------|
| Skill invocation patterns | High | ❌ Not guarded |
| Tool usage patterns | Medium | ❌ Not guarded |
| Session recovery patterns | High | ❌ Not guarded |
| Integration patterns | Medium | ❌ Not guarded |
| Workflow patterns | High | ❌ Not guarded |

---

## Recommendations

### Critical Gaps (Immediate Action Required)
1. **Create Capability Registry**: Define explicit capability schema and registry
2. **Implement Forgetting Guard**: Protect learned patterns from degradation
3. **Add Integration Health Checks**: Monitor external service connectivity

### Important Gaps (Near-term)
1. **Expand Gate A**: Include capability schema validation
2. **Add Capability Telemetry**: Track feature-level usage in Gate B
3. **Create Capability Doctor**: Add capability-level checks to Gate C

### Enhancement Opportunities
1. **Session Quality Metrics**: Track session continuity success rates
2. **Skill Effectiveness Tracking**: Monitor skill invocation success/failure
3. **Integration Circuit Breakers**: Auto-disable failing integrations

---

*Generated by: OpenClaw Capability Coverage Audit v2.0*
*Audit Session: subagent:a4c4ebbe-6de6-4481-a51e-6b9a9a9e8806*
