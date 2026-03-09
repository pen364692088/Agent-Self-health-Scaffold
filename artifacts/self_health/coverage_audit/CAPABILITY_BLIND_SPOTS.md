# Capability Blind Spots Analysis

**Audit Date**: 2026-03-09
**Audit Scope**: OpenClaw Self-Health Mechanism v1.0.0 SCAFFOLD

---

## Overview

This document identifies blind spots in the current self-health coverage. Blind spots represent functional gaps where:
- Features exist but aren't monitored
- Monitoring exists but doesn't check effectiveness
- Dependencies exist but aren't tracked
- User expectations exist but aren't validated

---

## Blind Spot Categories

### 1. Hidden Dependency Blind Spots

Features that depend on unstated/unmonitored prerequisites.

| Feature | Hidden Dependency | Risk Level | Evidence |
|---------|-------------------|------------|----------|
| Subagent Retry | Parent session memory | High | No check if parent session has context to retry |
| Context Compression | Session WAL integrity | Critical | WAL corruption not detected before compression |
| Callback Worker | systemd service state | Medium | Only checks file existence, not actual service health |
| Mailbox Worker | Flow definition existence | Medium | Checks prose file, not actual execution |
| Health Summary | All subcomponents | Medium | Summary assumes component data is valid |
| Gate Checks | Tool executability | Low | Assumes tools are executable, doesn't test |

**Root Cause**: Dependency graph not formalized in capability registry.

**Impact**: Cascading failures may propagate undetected.

---

### 2. Liveness-Only Coverage Blind Spots

Features that are checked for "is it running?" but not "is it working correctly?"

| Feature | Liveness Check | Effectiveness Check | Gap |
|---------|----------------|---------------------|-----|
| agent-health-check | ✅ Executed | ❌ Not validated | Tool runs, but output quality not verified |
| agent-self-heal | ✅ Executed | ❌ Not validated | Heal action completed, but impact not measured |
| callback_worker_status | ✅ File exists | ❌ Callback delivered | Worker writes status, but doesn't confirm delivery |
| mailbox_worker_status | ✅ File exists | ❌ Messages processed | Backlog tracked, but processing success not verified |
| heartbeat_status | ✅ Timestamp fresh | ❌ Heartbeat meaningful | Timestamp updated, but actual work not confirmed |
| Gate A | ✅ Files exist | ❌ Schemas valid | Policy files exist, but schema compliance not checked |

**Root Cause**: Telemetry design prioritizes "is it alive" over "is it effective".

**Impact**: Silent degradation - system appears healthy while failing.

---

### 3. Execution-Only Coverage Blind Spots

Features where execution is monitored but outcome is not.

| Feature | Execution Tracked | Outcome Tracked | Gap |
|---------|-------------------|-----------------|-----|
| Subagent spawn | ✅ Spawn initiated | ❌ Task completed successfully | Subagent created, but success/failure not linked |
| Heal action | ✅ Action executed | ❌ Problem resolved | clear_cache runs, but memory issue may persist |
| Incident report | ✅ Report created | ❌ Incident resolved | Incident logged, but no resolution tracking |
| Proposal created | ✅ Proposal written | ❌ Proposal reviewed | Proposal created, but no review workflow |
| Health check | ✅ Check completed | ❌ Health improved | Check runs, but doesn't trigger improvement |

**Root Cause**: Workflow doesn't close the loop on outcomes.

**Impact**: False sense of completion - actions taken but problems persist.

---

### 4. No Effectiveness Check Blind Spots

Features that lack validation of whether they actually work as intended.

| Feature | Expected Behavior | Effectiveness Check | Missing Validation |
|---------|-------------------|---------------------|-------------------|
| Session Recovery | State restored correctly | ❌ | No verification that recovered state matches pre-loss state |
| Context Compression | Context preserved | ❌ | No verification that compressed context is functionally equivalent |
| Subagent Retry | Task succeeds on retry | ❌ | No tracking of retry success rate |
| Heal Whitelist | Problem resolved | ❌ | No post-heal health comparison |
| Gate Pass | System actually healthy | ❌ | Gate passes don't guarantee no issues |
| Incident Detection | Real problems detected | ❌ | No ground truth validation of incident accuracy |

**Root Cause**: No end-to-end validation framework.

**Impact**: Security theater - checks pass but problems remain.

---

### 5. User-Promised but Unregistered Blind Spots

Features that are promised to users but not tracked in capability system.

| Promise | Source | Tracking | Risk |
|---------|--------|----------|------|
| Session continuity | AGENTS.md | ❌ Not in capability registry | User expects state persistence, no formal tracking |
| Proactive behavior | proactive-agent skill | ❌ Not monitored | Skill may degrade silently |
| Memory retrieval | memory dashboard | ❌ Only availability checked | Retrieval quality not validated |
| Skill availability | Skill loading system | ❌ Not monitored | Skills may fail to load without alert |
| Telegram delivery | message tool | ❌ Not tracked | Messages may fail silently |
| Subagent completion | callback worker | ❌ Only file-based check | Completion may not reach user |

**Root Cause**: User-facing commitments not formalized as capabilities.

**Impact**: Trust erosion - promises not backed by monitoring.

---

### 6. Governance Critical but Unmonitored Blind Spots

Critical governance functions that lack monitoring.

| Function | Criticality | Monitoring | Gap |
|----------|-------------|------------|-----|
| SOUL.md integrity | Critical | ❌ Only hard boundary | No checksum/validation of core principles |
| Policy drift detection | Critical | ❌ Not implemented | Policies may silently diverge from intent |
| Gate bypass audit | High | ❌ Only flag exists | Bypass events not tracked/alerted |
| Level escalation | High | ❌ Only in code | Level B/C actions may execute without proper review |
| Audit trail integrity | High | ❌ Assumed | Audit logs may be tampered with or lost |
| Self-heal whitelist integrity | Critical | ❌ Static check only | Whitelist may be modified without detection |

**Root Cause**: Governance mechanisms lack self-monitoring.

**Impact**: Governance bypass - rules may be violated without detection.

---

## Blind Spot Severity Matrix

| Blind Spot | Likelihood of Silent Failure | Impact if Failure | Severity |
|------------|------------------------------|-------------------|----------|
| Session WAL corruption | Low | Critical | High |
| Capability degradation | Medium | High | High |
| Hidden dependency failure | Medium | Medium | Medium |
| False health positive | Medium | Medium | Medium |
| Outcome not tracked | High | Medium | Medium |
| User promise untracked | Medium | Medium | Medium |
| Governance bypass | Low | Critical | High |

---

## Root Cause Analysis

### Why These Blind Spots Exist

1. **No Capability Registry**
   - Capabilities are implicit in tools/skills
   - No formal definition of what the agent can do
   - No tracking of capability health

2. **Telemetry Gap**
   - Telemetry designed for debugging, not capability monitoring
   - Component-level, not capability-level
   - Focus on availability, not effectiveness

3. **No Forgetting Guard**
   - Agent doesn't track what it has learned
   - No protection against knowledge degradation
   - No detection of capability regression

4. **Incomplete Gate Integration**
   - Gates check existence, not capability
   - Gates are tool-centric, not user-centric
   - Gate results not linked to capability status

5. **Proposal Workflow Not Closed**
   - Proposals created but not tracked to resolution
   - No feedback loop on proposal effectiveness
   - No escalation for stale proposals

---

## Recommendations by Priority

### Critical (Address Immediately)

1. **Implement Forgetting Guard**
   - Create capability registry
   - Track capability usage patterns
   - Alert on capability degradation
   - Protect critical capabilities

2. **Add Outcome Tracking**
   - Track heal action outcomes
   - Verify incident resolution
   - Close the loop on proposals
   - Validate session recovery

### High (Address in Near-Term)

3. **Expand Gate Coverage**
   - Add capability schema to Gate A
   - Add effectiveness metrics to Gate B
   - Add capability doctor to Gate C

4. **Implement Dependency Tracking**
   - Formalize dependency graph
   - Add dependency health checks
   - Alert on dependency degradation

### Medium (Address When Possible)

5. **Add User Promise Tracking**
   - Map user promises to capabilities
   - Track promise fulfillment
   - Alert on promise degradation

6. **Strengthen Governance Monitoring**
   - Add SOUL.md checksum
   - Implement policy drift detection
   - Audit gate bypass events

---

## Testing Recommendations

### Gap-Specific Tests

```bash
# Hidden dependency test
test_hidden_dependency() {
  # Verify WAL before compression
  # Verify parent session before retry
  # Verify service before callback
}

# Effectiveness test
test_heal_effectiveness() {
  # Clear cache, verify memory improved
  # Retry subagent, verify task completed
}

# Forgetting guard test
test_capability_degradation() {
  # Simulate skill not used for 30 days
  # Verify alert generated
  # Verify capability remains functional
}

# Governance integrity test
test_governance_integrity() {
  # Verify SOUL.md checksum
  # Verify policy files not modified
  # Verify audit trail intact
}
```

---

## Appendix: Blind Spot Detection Checklist

Use this checklist to detect blind spots when adding new features:

- [ ] Is the capability registered?
- [ ] Are dependencies tracked?
- [ ] Is effectiveness checked, not just liveness?
- [ ] Is outcome tracked, not just execution?
- [ ] Is there a user promise? Is it tracked?
- [ ] Is governance impacted? Is it monitored?
- [ ] Could this fail silently?
- [ ] What would indicate success?
- [ ] How would we know if it degraded?

---

*Generated by: OpenClaw Capability Coverage Audit v2.0*
*Audit Session: subagent:a4c4ebbe-6de6-4481-a51e-6b9a9a9e8806*
