# Context Compression - Final Push Documentation

## Complete System Documentation - Part 1

### Overview of Compression System

The context compression system is a critical component of OpenClaw that manages token usage across long-running sessions. This document provides comprehensive coverage of all system aspects.

### System Components

**Component 1: Budget Monitor**
- Continuously estimates token usage
- Calculates budget ratio in real-time
- Triggers compression when thresholds exceeded
- Provides early warning system

**Component 2: Compression Engine**
- Plans eviction strategy
- Generates structured capsules
- Updates session state atomically
- Maintains audit trail

**Component 3: State Manager**
- Persists session state
- Handles backup and recovery
- Manages state transitions
- Ensures consistency

**Component 4: Evidence Collector**
- Captures pre-compression state
- Captures post-compression state
- Validates evidence integrity
- Maintains evidence chain

### Compression Workflow

The complete compression workflow follows these steps:

1. **Trigger Detection**
   - Budget ratio crosses threshold
   - State transitions to pending
   - Guardrail activated

2. **Pre-Compression**
   - Capture counter state
   - Capture budget snapshot
   - Log guardrail event
   - Prepare evidence directory

3. **Eviction Planning**
   - Calculate eviction ratio
   - Identify turns to remove
   - Identify turns to preserve
   - Verify constraints

4. **Capsule Generation**
   - Extract content from evicted turns
   - Generate structured summary
   - Calculate token count
   - Persist capsule file

5. **State Update**
   - Update turn count
   - Update token count
   - Add capsule references
   - Persist new state

6. **Post-Compression**
   - Capture new counter state
   - Capture new budget snapshot
   - Verify safety counters
   - Complete evidence package

### Threshold Behavior Details

**Observe Threshold (0.75)**
- Entry into candidate zone
- State: candidate
- Action: Increase monitoring
- Trace: HIGH granularity

**Enforced Threshold (0.85)**
- Entry into trigger zone
- State: pending
- Action: Execute compression
- Trace: MAXIMUM granularity

**Strong Threshold (0.92)**
- Entry into emergency zone
- State: pending (strong)
- Action: Aggressive compression
- Higher eviction ratio

### State Machine Details

The state machine manages the compression lifecycle:

```
States:
- idle: Normal operation, ratio < 0.75
- candidate: Monitoring, 0.75 <= ratio < 0.85
- pending: Compression required, ratio >= 0.85
- executing: Compression in progress
- completed: Compression successful
- failed: Compression failed
- rollback: Restoring previous state

Transitions:
- idle → candidate: ratio >= 0.75
- candidate → pending: ratio >= 0.85
- pending → executing: compression started
- executing → completed: success
- executing → failed: error
- failed → rollback: recovery initiated
- rollback → idle: restoration complete
- completed → idle: ratio < 0.75
```

### Safety Mechanism Details

**Kill Switch**
- Provides emergency shutdown
- Immediately stops all compression
- Preserves current state
- Requires manual deactivation

**Safety Counters**
- Track potential violations
- Must remain at zero
- Alert on any non-zero value
- Trigger investigation

**Scope Filter**
- Only processes low-risk sessions
- Excludes critical sessions
- Prevents accidental compression
- Configurable exclusion list

### Evidence Chain Requirements

Complete evidence chain for each compression:

**Required Files**:
1. counter_before.json
2. counter_after.json
3. budget_before.json
4. budget_after.json
5. guardrail_event.json
6. capsule_metadata.json

**Validation Requirements**:
- All files present
- Timestamps consistent
- Counter deltas correct
- Budget changes valid
- JSON schema valid

### Performance Characteristics

Expected performance under various conditions:

**Light Load (< 10 sessions)**:
- Budget check: < 50ms
- Compression: < 150ms
- Evidence capture: < 50ms

**Medium Load (10-50 sessions)**:
- Budget check: < 100ms
- Compression: < 250ms
- Evidence capture: < 100ms

**Heavy Load (50+ sessions)**:
- Budget check: < 200ms
- Compression: < 500ms
- Evidence capture: < 200ms

### Configuration Details

Complete configuration specification:

```json
{
  "policy_version": "1.0",
  "context_window": 200000,
  "thresholds": {
    "observe": 0.75,
    "candidate": 0.75,
    "enforced": 0.85,
    "strong": 0.92
  },
  "critical_rule": "不允许跨过 0.85 后继续拖延",
  "execution_point": "prompt_assemble",
  "safety": {
    "min_preserve_turns": 5,
    "max_evict_ratio": 0.60
  }
}
```

### Monitoring Metrics

Key metrics for system health:

**Session Metrics**:
- Active session count
- Average ratio
- Compression state distribution

**Compression Metrics**:
- Trigger count
- Success rate
- Average duration
- Compression gain

**Safety Metrics**:
- Safety counter values
- Kill switch status
- Rollback frequency

### Alert Configuration

Alert thresholds for monitoring:

**Critical Alerts**:
- Safety counter > 0
- Kill switch activated
- Configuration error

**Warning Alerts**:
- Error rate > 5%
- Latency > 500ms
- Rollback rate > 5%

**Info Alerts**:
- Compression triggered
- State transition
- Evidence captured

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T03:55:00-06:00
**Purpose**: Final Push Documentation for Candidate Zone Entry
