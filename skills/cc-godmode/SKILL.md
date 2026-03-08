---
name: cc-godmode
description: "Self-orchestrating multi-agent development workflows. You say WHAT, the AI decides HOW."
metadata:
  clawdbot:
    emoji: "🚀"
version: 5.12.0
---

# CC-Godmode - Self-Orchestrating Multi-Agent Workflows

**You say WHAT, the AI decides HOW.**

CC-Godmode is an advanced multi-agent orchestration system that enables self-organizing development workflows. Instead of micromanaging each step, you define the goal and the system determines the optimal execution strategy.

## ⚠️ Session Continuity Integration (MANDATORY) ⭐⭐⭐⭐⭐

**Before ANY long task execution, you MUST recover session state.**

### Pre-Flight Recovery

```bash
# Step 1: Check if recovery needed
session-start-recovery --preflight

# Step 2: If needs_recovery, execute recovery
session-start-recovery --recover --summary

# Step 3: Extract recovered state
# - objective
# - phase  
# - branch
# - next_actions
# - blockers
```

### State Persistence During Task

**On ANY significant state change:**

```bash
# Update SESSION-STATE.md
cat > ~/.openclaw/workspace/SESSION-STATE.md << 'STATE'
## Current Objective
[Updated objective]

## Current Phase
[Current phase]

## Next Actions
[Next steps]

## Blockers
[Current blockers]
STATE

# Append to WAL
state-journal-append --action state_update --summary "Phase X completed"

# Update working-buffer if focus changed
cat > ~/.openclaw/workspace/memory/working-buffer.md << 'BUFFER'
## Active Focus
[Current focus]

## Hypotheses
[Current hypotheses]

## Pending Verification
[Items to verify]
BUFFER
```

### Task Completion / Pause

```bash
# Generate handoff
handoff-create --summary "Task paused/completed: ..."

# Log completion event
continuity-event-log task_completed --session-id $SESSION_ID --meta task_name="..."
```

### Events Logged

| Event | When | Tool |
|-------|------|------|
| recovery_success | Task start, new session | session-start-recovery |
| handoff_created | Task pause/complete | handoff-create |
| state_update | State changes | state-journal-append |
| high_context_trigger | Context > 80% | pre-reply-guard |

### Persistence Principle

**Persist first, reply second.**

Before sending any substantial update:
1. Write SESSION-STATE.md
2. Append to WAL
3. Update working-buffer if needed
4. Then send the reply

---

## Core Philosophy

Traditional development: You specify every step, tool, and approach.
CC-Godmode: You specify the outcome, the system figures out the path.

## Key Features

### 🎯 Goal-Oriented Execution
- Define high-level objectives
- System determines optimal strategy
- Dynamic plan adaptation based on progress

### 🤝 Multi-Agent Coordination
- Automatic agent role assignment
- Inter-agent communication protocols
- Conflict resolution and handoff management

### 🔄 Self-Orchestration
- Real-time plan adjustment
- Resource optimization
- Failure recovery and rerouting

### 📊 Intelligent Planning
- Context-aware strategy selection
- Risk assessment and mitigation
- Progress tracking and reporting

## Usage Examples

### Simple Goal
```bash
cc-godmode "build a REST API for user management"
```

### Complex Project
```bash
cc-godmode "create a full-stack e-commerce platform with payment processing"
```

### Technical Specification
```bash
cc-godmode "migrate the database from PostgreSQL to MongoDB while maintaining zero downtime"
```

## Workflow Stages

1. **Session Recovery**: Restore state from previous session (MANDATORY)
2. **Goal Analysis**: Parse and understand objectives
3. **Strategy Planning**: Determine optimal approach
4. **Agent Allocation**: Assign specialized agents
5. **Execution**: Coordinate multi-agent work
6. **Monitoring**: Track progress and handle issues
7. **Completion**: Validate, persist state, deliver results

## Agent Types

- **Planner Agent**: Strategy and roadmap creation
- **Coder Agent**: Implementation and development
- **Tester Agent**: Quality assurance and validation
- **Reviewer Agent**: Code review and optimization
- **Orchestrator Agent**: Overall coordination

## Configuration

```yaml
cc_godmode:
  max_agents: 5
  timeout: "2h"
  approval_required_for: ["deployment", "database_changes"]
  session_continuity:
    recovery_on_start: true
    persist_on_change: true
    handoff_on_pause: true
```

## Safety Features

- Session recovery before task start
- Goal validation before execution
- Progress checkpoints and approval gates
- Automatic rollback on critical failures
- Full audit trail of all actions
- State persistence on changes

## Integration

CC-Godmode integrates with:
- Session Continuity (MANDATORY)
- Development environments
- CI/CD pipelines
- Project management tools
- Code repositories

## Best Practices

1. **Recover First**: Always recover session state before starting
2. **Clear Goals**: Be specific about desired outcomes
3. **Reasonable Scope**: Break large projects into manageable goals
4. **Regular Checkpoints**: Monitor progress and provide feedback
5. **Safety First**: Use approval gates for critical operations
6. **Persist Changes**: Update state files on significant changes

## ⚠️ Tool Delivery Gates (MANDATORY for Tool Tasks)

**When task involves creating/modifying tools, wrappers, integrations, or handlers, the following gates are MANDATORY:**

### Gate A: Contract Validation
- Input/output schemas MUST be defined
- Drift detection MUST pass
- Errors MUST follow standard format

### Gate B: E2E Testing
- Happy path test MUST pass
- Bad args handling MUST be verified
- Real transport (no mocks for external services)

### Gate C: Preflight Check
- `tool_doctor` MUST run successfully
- `doctor_report.json` MUST be generated

### Required Output Format
```markdown
## EVIDENCE_GATE_A
- Schema validated: [files]
- Drift detection: PASS/FAIL
- Error format: standard

## EVIDENCE_GATE_B
- E2E happy: [test result]
- E2E bad args: [test result]

## EVIDENCE_GATE_C
- tool_doctor: [summary]
- Health checks: [passed list]
```

### Bypass (Emergency Only)
```bash
export GATES_DISABLE=1  # Must document why
```

See `POLICIES/TOOL_DELIVERY.md` for full protocol.

---

## Standard Task Types

CC-Godmode supports pre-defined task types with standardized workflows:

### 1. project-check

**Description**: Standardized project health check with artifact-first, phase-based execution.

**Principles**:
- Main session only orchestrates
- One phase per session
- Artifacts only (status.json + summary.md + raw.log)
- Progress queries read status files only

**Usage**:
```bash
# Initialize
project-check init /path/to/repo

# Auto-advance all phases
project-check-advance <check_id> --auto-spawn

# Query progress
project-check status <check_id>
```

**Phases**:
| Phase | Name | Timeout |
|-------|------|---------|
| A | Repo Snapshot | 60s |
| B | Fast Tests | 300s |
| C | Testbot E2E | 600s |
| D | Hard Gate | 300s |
| E | Aggregation | 60s |

**Output**:
- `artifacts/project_check/<check_id>/final/FINAL_CHECK_REPORT.md`
- `artifacts/project_check/<check_id>/final/one_liner.txt`

**See**: `templates/cc-godmode/project_check_task.md` for full specification.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 5.12.0 | 2026-03-07 | Added Session Continuity integration (MANDATORY) |
| 5.11.3 | 2026-03-06 | Previous stable version |

---

## Warnings

This is a powerful autonomous system. Start with simple goals and gradually increase complexity as you gain confidence in the system's capabilities.
