# Verdict Templates

## Instance Verdicts

### INSTANCE_PROVEN
Use when:
- [ ] All critical telemetry sources working
- [ ] Gate A/B/C all PASS
- [ ] At least 1 user_promised_feature verified
- [ ] Soak test completed
- [ ] No structural issues
- [ ] Capability states reflect reality

Template:
```markdown
## Verdict: INSTANCE_PROVEN

### Evidence
- Telemetry: X sources working
- Capabilities: X healthy, X missing
- Gate: A=PASS, B=PASS, C=PASS
- User-promised features: X verified
- Soak: X hours completed
- Issues: None structural

### Conclusion
This instance has demonstrated stable, reliable self-health monitoring
with accurate capability detection and no harmful side effects.
```

### STABLE_WITH_CAVEATS
Use when:
- [ ] Basic functionality working
- [ ] Some issues but not structural
- [ ] Soak test completed
- [ ] Main loop impact acceptable

Template:
```markdown
## Verdict: STABLE_WITH_CAVEATS

### Evidence
- Telemetry: X sources working, X missing
- Capabilities: X healthy, X missing
- Gate: A=?, B=?, C=?
- User-promised features: X registered
- Soak: X hours completed
- Issues: [List]

### Caveats
- [List specific issues]

### Recommendations
- [What to fix before INSTANCE_PROVEN]
```

### READY_BUT_NEEDS_HARDENING
Use when:
- [ ] Integration possible but incomplete
- [ ] Structural issues identified
- [ ] More work needed before stable

Template:
```markdown
## Verdict: READY_BUT_NEEDS_HARDENING

### Evidence
- Telemetry: X sources working, X missing
- Capabilities: X healthy, X missing
- Gate: A=?, B=?, C=?
- Issues: [List structural issues]

### Hardening Needed
- [Specific work required]

### Timeline
- Estimated effort: X hours
```

### NOT_READY_FOR_WIDER_ROLLOUT
Use when:
- [ ] Fundamental blockers exist
- [ ] Cannot achieve basic functionality
- [ ] Structural problems prevent integration

Template:
```markdown
## Verdict: NOT_READY_FOR_WIDER_ROLLOUT

### Blockers
- [List fundamental blockers]

### Root Causes
- [Why this instance is not ready]

### Resolution Path
- [What would be needed to make it ready]
```

## Transferability Verdicts

### TRANSFERABLE_WITH_LOW_FRICTION
Use when:
- [ ] Second instance integrated in < 16 hours
- [ ] < 20% components needed instance-specific adaptation
- [ ] No major architectural surprises
- [ ] Telemetry contract mostly reusable

### TRANSFERABLE_WITH_MODERATE_FRICTION
Use when:
- [ ] Second instance integrated in 16-40 hours
- [ ] 20-50% components needed adaptation
- [ ] Some architectural differences
- [ ] Telemetry needed significant adaptation

### TRANSFERABLE_BUT_NEEDS_HARDENING
Use when:
- [ ] Integration possible but costly
- [ ] > 50% components needed adaptation
- [ ] Major architectural differences
- [ ] Telemetry contract not directly reusable

### NOT_YET_TRANSFERABLE
Use when:
- [ ] Integration failed or impractical
- [ ] Fundamental architectural mismatches
- [ ] Scaffold design does not generalize
```

cat > docs/p5_prep/ROLLOUT_RECOMMENDATION_TEMPLATE.md <<'EOF'
# Rollout Recommendation Template

## Purpose
Standardized rollout recommendations after instance validation.

## Recommendation Types

### PROCEED_TO_FLEET_PILOT
Use when:
- INSTANCE_PROVEN on 2+ instances
- Low or moderate friction
- Clear integration pattern

Template:
```markdown
## Recommendation: PROCEED_TO_FLEET_PILOT

### Basis
- Instance 1: INSTANCE_PROVEN
- Instance 2: INSTANCE_PROVEN (or STABLE_WITH_CAVEATS)
- Transferability: LOW/MODERATE friction
- Integration pattern: Clear

### Next Steps
1. Document integration pattern
2. Create fleet onboarding guide
3. Select 3-5 additional instances
4. Apply pattern with adaptations
5. Collect fleet-wide metrics

### Timeline
- Fleet pilot: X weeks
- Full rollout: X months
```

### PROCEED_WITH_HARDENING
Use when:
- STABLE_WITH_CAVEATS on second instance
- Specific issues identified
- Clear path to improvement

Template:
```markdown
## Recommendation: PROCEED_WITH_HARDENING

### Issues to Address
1. [Issue 1]
2. [Issue 2]

### Hardening Plan
- [Specific work]
- Timeline: X hours/days

### Validation
- Re-run soak after hardening
- Target: INSTANCE_PROVEN

### Cost
- Estimated: X hours
```

### PAUSE_FOR_ARCHITECTURE_REVIEW
Use when:
- Fundamental architectural issues found
- Scaffold design may need revision
- Pattern does not generalize

Template:
```markdown
## Recommendation: PAUSE_FOR_ARCHITECTURE_REVIEW

### Architectural Issues
- [List issues]

### Impact on Scaffold
- [How this affects scaffold design]

### Review Scope
- [What needs review]

### Timeline
- Review: X days
- Potential redesign: X weeks
```

### DO_NOT_PROCEED
Use when:
- Fundamental incompatibility
- Scaffold cannot work on this instance type
- Better to create separate solution

Template:
```markdown
## Recommendation: DO_NOT_PROCEED

### Incompatibility
- [Why scaffold cannot work]

### Alternatives
- [Suggested alternatives]

### Lesson Learned
- [What this teaches us about scaffold boundaries]
```

## Decision Matrix

| Instance 1 | Instance 2 | Transferability | Recommendation |
|------------|------------|-----------------|----------------|
| INSTANCE_PROVEN | INSTANCE_PROVEN | LOW | FLEET_PILOT |
| INSTANCE_PROVEN | INSTANCE_PROVEN | MODERATE | FLEET_PILOT |
| INSTANCE_PROVEN | STABLE_WITH_CAVEATS | LOW/MODERATE | HARDENING |
| INSTANCE_PROVEN | STABLE_WITH_CAVEATS | HIGH | ARCHITECTURE_REVIEW |
| INSTANCE_PROVEN | NOT_READY | ANY | PAUSE |
| ANY | FAILED | ANY | DO_NOT_PROCEED |
