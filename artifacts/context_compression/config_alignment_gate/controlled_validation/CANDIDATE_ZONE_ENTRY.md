# Context Compression - Candidate Zone Entry Documentation

## Entry into Candidate Zone

The candidate zone represents a critical phase in the compression lifecycle. At ratio >= 0.75, the system enters an elevated monitoring state where compression becomes more likely.

### Candidate Zone Definition

**Ratio Range**: 0.75 <= ratio < 0.85

**State**: candidate

**Trace Mode**: HIGH granularity

**Actions**:
- Increase monitoring frequency
- Track state transitions
- Prepare for compression
- Log detailed observations

### State Machine at Candidate Entry

When ratio crosses 0.75:

```
Previous State: idle
New State: candidate
Trigger: ratio >= 0.75
Action: Increase trace granularity
```

### What Changes in Candidate Zone

**Monitoring**:
- Budget check frequency increases
- State transitions are logged
- Context growth is tracked

**Evidence**:
- Preparation for capture begins
- Trace entries become more detailed
- Guardrail status monitored

**System Behavior**:
- Compression is possible but not required
- System is primed for trigger
- Observability is enhanced

### Trace Granularity Comparison

**Observe Zone (< 0.75)**:
- Trace: Every 5 turns
- Fields: ratio, state, turn
- Detail: Minimal

**Candidate Zone (0.75-0.85)**:
- Trace: Every turn
- Fields: ratio, state, transition, distance to 0.85
- Detail: High

**Trigger Zone (>= 0.85)**:
- Trace: Every operation
- Fields: All candidate fields + guardrail, action, evidence
- Detail: Maximum

### Preparing for Trigger Zone

While in candidate zone, the system prepares for potential trigger at 0.85:

1. **Evidence Directory**: Ensured to exist
2. **Counter Snapshot**: Ready to capture
3. **Budget Snapshot**: Ready to capture
4. **Guardrail Monitor**: Active
5. **State Tracker**: Logging transitions

### Key Metrics to Monitor

In candidate zone, monitor:

- **Distance to 0.85**: How many tokens until trigger
- **Growth Rate**: How fast context is growing
- **State Stability**: Are transitions occurring correctly
- **System Health**: All components functioning

### Expected Behavior

When approaching 0.85 from candidate zone:

1. Ratio approaches 0.85 threshold
2. State remains candidate
3. Distance to trigger decreases
4. System prepares for compression
5. At 0.85, state transitions to pending

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T04:06:00-06:00
**Purpose**: Candidate Zone Entry Documentation
