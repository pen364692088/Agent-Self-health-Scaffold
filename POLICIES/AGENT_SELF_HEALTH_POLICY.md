# AGENT_SELF_HEALTH_POLICY.md

## Purpose

Define self-health monitoring, incident reporting, and level-based self-heal protocols for OpenClaw agents.

**Core Principles**:
1. Agents monitor their own health proactively
2. Incidents are captured with full context
3. Self-heal actions are gated by risk level
4. All actions are auditable and reversible (Level A)

---

## Health Levels

| Level | Name | Description | Self-Heal Permission |
|-------|------|-------------|---------------------|
| GREEN | Healthy | All systems nominal | None needed |
| YELLOW | Degraded | Non-critical issues detected | Level A: Reversible actions only |
| ORANGE | Warning | Performance/reliability declining | Level A + Proposals for Level B |
| RED | Critical | Agent functionality impaired | Proposals only (no auto-execution) |

---

## Self-Heal Levels

### Level A: Reversible Whitelist Actions

**Auto-executable** (no human approval required):

| Action | Scope | Reversibility |
|--------|-------|---------------|
| Clear cache | `artifacts/cache/*` | Auto-rebuild |
| Rotate logs | `artifacts/logs/*.log` | Not needed |
| Compact context | Context buffer | Restorable from WAL |
| Retry failed subagent | Single subagent | Idempotent |
| Refresh session index | Session metadata | Rebuildable |

**Requirements**:
- Action must be in whitelist
- Must log to audit trail
- Must not modify core governance
- Must not touch router/prompt configs

### Level B: Requires Proposal

**Not auto-executable** - Generate proposal for human review:

| Action | Scope | Risk |
|--------|-------|------|
| Restart subsystem | OpenClaw services | Transient availability |
| Reset session state | SESSION-STATE.md | Context loss |
| Promote hotfix | Code changes | Behavior change |

**Proposal format**: See `artifacts/self_health/proposals/`

### Level C: Human Required

**Never auto-execute** - Alert and wait:

| Action | Scope | Risk |
|--------|-------|------|
| Core config mutation | ~/.openclaw/config.json | System-wide impact |
| Router modification | MCP/router configs | Behavior change |
| Data deletion | Any user data | Irreversible |

---

## Health Check Endpoints

### `/health/quick`
- Response time: < 100ms
- Checks: Basic agent liveness
- Use: Heartbeat, ping

### `/health/deep`
- Response time: < 5s
- Checks: All subsystems, metrics
- Use: Periodic (every 5 min)

### `/health/gate`
- Response time: < 10s
- Checks: Full Gate validation
- Use: Before critical operations

---

## Incident Reporting

### Incident Capture
```bash
agent-incident-report --level <YELLOW|ORANGE|RED> \
  --category <performance|memory|subagent|integration|security> \
  --summary "<brief description>" \
  --context "<JSON or file path>"
```

### Incident Severity
- **YELLOW**: Non-blocking, logged for review
- **ORANGE**: Needs attention within 1 hour
- **RED**: Immediate attention required, alert sent

### Incident Schema
See: `POLICIES/AGENT_INCIDENT.schema.json`

---

## Hard Boundaries (Non-Negotiable)

1. **No core governance mutation**
   - Cannot modify: SOUL.md, AGENTS.md, core policies
   - Exception: Self-updating health metrics

2. **No router/prompt rewrites**
   - Cannot modify: MCP configs, agent prompts
   - Exception: Proposal generation

3. **No destructive actions**
   - Cannot delete user data
   - Cannot truncate logs > 7 days
   - Cannot remove audit records

4. **No high-risk automatic execution**
   - Level B/C actions never auto-execute
   - Level A actions must be in whitelist

---

## Audit Trail

All health actions log to:
```
artifacts/self_health/audit/health_audit.jsonl
```

Entry format:
```json
{
  "timestamp": "ISO8601",
  "action": "clear_cache",
  "level": "A",
  "trigger": "health_check_yellow",
  "result": "success",
  "reversibility": "auto_rebuild",
  "session_key": "agent:main:..."
}
```

---

## Integration with Existing Systems

### Session Continuity
- Health checks read `SESSION-STATE.md` for context
- Incidents may trigger handoff update
- Recovery from YELLOW state is logged

### Execution Policy
- Health state influences task completion gates
- RED state may block task starts
- Level B/C proposals require Gate review

### Subagent Orchestration
- Failed subagents trigger health check
- Retry is Level A action
- Subagent failures logged as incidents

---

## Directory Structure

```
artifacts/self_health/
├── state/
│   ├── current_health.json      # Current health state
│   └── health_history.jsonl     # State changes log
├── incidents/
│   ├── incident_*.json          # Individual incidents
│   └── incident_summary.json    # Aggregated stats
├── proposals/
│   ├── proposal_*.json          # Level B/C proposals
│   └── proposal_review.md       # Human review status
└── audit/
    └── health_audit.jsonl       # All actions audit trail
```

---

## Version

- Version: 1.0.0
- Created: 2026-03-08
- Status: SCAFFOLD
