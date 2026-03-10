# v1.1 Candidate Rules Evaluation Framework

## Evaluation Criteria

A rule is worth adding to runtime if:

| Criterion | Weight | Check |
|-----------|--------|-------|
| Recurrence | High | Has this error repeated ≥2 times? |
| Impact | High | Is the consequence clear and significant? |
| Detectability | Medium | Can this be objectively identified? |
| Fallback | Medium | Is there a clear alternative action? |
| Noise Risk | Medium | Will this create excessive false positives? |

## Phase 1: High Priority (v1.1 First Batch)

### Rule v1.1-01: PERSIST_BEFORE_REPLY_ON_STATEFUL_TASKS

| Criterion | Assessment |
|-----------|------------|
| Recurrence | ⚠️ Medium - State drift occurs occasionally |
| Impact | High - Causes handoff failures, recovery issues |
| Detectability | Medium - Requires state change detection |
| Fallback | Clear - "persist then reply" |
| Noise Risk | Medium - May warn on simple tasks |

**Recommendation**: ✅ Add to v1.1 as WARN, upgrade to DENY for critical paths

### Rule v1.1-02: FRAGILE_REPLACE_BLOCK_ON_MANAGED_FILES

| Criterion | Assessment |
|-----------|------------|
| Recurrence | High - Repeated edit failures on managed files |
| Impact | High - Breaks config, policy, critical scripts |
| Detectability | High - Path pattern + edit method |
| Fallback | Clear - safe-write/safe-replace/exec+heredoc |
| Noise Risk | Low - Clear scope |

**Recommendation**: ✅ Add to v1.1 as DENY (already partially implemented)

### Rule v1.1-03: CHECKPOINT_REQUIRED_BEFORE_CLOSE

| Criterion | Assessment |
|-----------|------------|
| Recurrence | Medium - Missing handoff context |
| Impact | High - New session can't recover |
| Detectability | High - Close without checkpoint |
| Fallback | Clear - Generate summary before close |
| Noise Risk | Low - Formal delivery only |

**Recommendation**: ✅ Add to v1.1 as DENY for formal deliveries

## Phase 2: Governance Layer (v1.1 Second Batch)

### Rule v1.1-04: HIGH_RISK_CHANGE_REQUIRES_PREFLIGHT

| Criterion | Assessment |
|-----------|------------|
| Recurrence | Low - Rare but high impact |
| Impact | Critical - Can break core systems |
| Detectability | High - Path pattern for hooks/policies |
| Fallback | Clear - Run doctor/preflight first |
| Noise Risk | Low - Narrow scope |

**Recommendation**: ⚠️ Add as WARN initially

### Rule v1.1-05: AUDIT_REQUIRED_FOR_SUBAGENT_CRITICAL_DELIVERY

| Criterion | Assessment |
|-----------|------------|
| Recurrence | Low - Rare scenario |
| Impact | High - Critical patches go unchecked |
| Detectability | Medium - Task type + critical flag |
| Fallback | Clear - Audit step required |
| Noise Risk | Medium - May slow delivery |

**Recommendation**: ⚠️ Evaluate after multi-agent usage increases

### Rule v1.1-06: POLICY_PROMOTION_REQUIRED_AFTER_REPEAT_OFFENSE

| Criterion | Assessment |
|-----------|------------|
| Recurrence | Meta-rule - applies to all rules |
| Impact | High - Automates governance |
| Detectability | High - Violation count tracking |
| Fallback | Clear - Create promotion candidate |
| Noise Risk | Low - Background process |

**Recommendation**: ✅ Add as background automation

## Phase 3: Signal Quality (v1.1 Third Batch)

### Rule v1.1-07: NONSTANDARD_TOOL_BYPASS_ALERT

| Criterion | Assessment |
|-----------|------------|
| Recurrence | Unknown - Need observation data |
| Impact | High - Policy circumvention |
| Detectability | Medium - Pattern recognition needed |
| Fallback | N/A - Detection only |
| Noise Risk | Medium - May have false alerts |

**Recommendation**: ⏳ Defer until v1 observation complete

### Rule v1.1-09: REPEATED_WARN_SUPPRESSION_OR_ESCALATION

| Criterion | Assessment |
|-----------|------------|
| Recurrence | Medium - WARN fatigue occurs |
| Impact | Medium - Signal quality degradation |
| Detectability | High - Same rule, same context count |
| Fallback | Clear - Suppress or escalate |
| Noise Risk | Low - Improves signal quality |

**Recommendation**: ✅ Add to v1.1 as auto-suppression

## Implementation Priority

### Immediate (v1.1 First Batch)
1. FRAGILE_REPLACE_BLOCK_ON_MANAGED_FILES (DENY)
2. PERSIST_BEFORE_REPLY_ON_STATEFUL_TASKS (WARN → DENY)
3. CHECKPOINT_REQUIRED_BEFORE_CLOSE (DENY for formal)

### Near-term (v1.1 Second Batch)
4. HIGH_RISK_CHANGE_REQUIRES_PREFLIGHT (WARN)
5. POLICY_PROMOTION_REQUIRED_AFTER_REPEAT_OFFENSE (Auto)
6. REPEATED_WARN_SUPPRESSION_OR_ESCALATION (Auto)

### Observation-dependent
7. NONSTANDARD_TOOL_BYPASS_ALERT
8. AUDIT_REQUIRED_FOR_SUBAGENT_CRITICAL_DELIVERY

## Decision Template

For each candidate rule, fill:

```yaml
id: RULE_ID
status: candidate | approved | deferred | rejected
priority: P0 | P1 | P2
phase: 1 | 2 | 3
rationale: "Why this matters"
evidence: "Supporting data from v1 observation"
action: deny | warn | reroute | auto
scope: "Where this applies"
fallback: "Alternative action"
implementation_notes: "Technical details"
```

---
Last Updated: 2026-03-09 18:35 UTC
