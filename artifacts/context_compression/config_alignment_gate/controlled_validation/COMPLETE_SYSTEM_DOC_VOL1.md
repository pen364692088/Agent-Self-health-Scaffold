# Context Compression - Complete System Documentation Volume 1

## Comprehensive System Reference

### System Overview and Purpose

The context compression system is a critical component of OpenClaw that manages token usage in long-running conversations. Its primary purpose is to prevent context overflow while preserving essential information through structured capsule summaries.

The system operates through a pipeline of tools coordinated by a TypeScript hook handler. When the budget ratio reaches critical thresholds, the system automatically compresses the context, removing older turns and creating capsules that preserve important information.

### Core System Components

The system consists of five main components:

1. **Hook Handler** - The TypeScript-based event handler that coordinates all compression operations
2. **Budget Monitor** - The Python tool that estimates token usage and calculates budget ratios
3. **Compression Engine** - The Python tool that executes compression and generates capsules
4. **State Manager** - The system that maintains session state across compression cycles
5. **Evidence Collector** - The system that captures and validates evidence packages

Each component has specific responsibilities and communicates through well-defined interfaces.

### Hook Handler Responsibilities

The hook handler serves as the central coordinator for compression operations. It:

- Listens for message.preprocessed events from OpenClaw
- Coordinates the execution of the compression pipeline
- Manages tool invocations and result processing
- Maintains counter state and metrics
- Handles errors and recovery scenarios

### Budget Monitor Responsibilities

The budget monitor provides token estimation and threshold detection:

- Estimates token count from session history files
- Calculates budget ratio against configured limits
- Determines pressure level based on thresholds
- Identifies threshold crossings for trigger events

### Compression Engine Responsibilities

The compression engine executes context reduction:

- Plans eviction strategy based on pressure level
- Generates structured capsules for evicted content
- Updates session state atomically
- Creates evidence packages for audit

### State Manager Responsibilities

The state manager maintains session persistence:

- Manages session state file (active_state.json)
- Handles backup and recovery operations
- Ensures atomic state updates
- Maintains state consistency across compression

### Evidence Collector Responsibilities

The evidence collector provides audit trail:

- Captures pre-compression state
- Captures post-compression state
- Validates evidence package completeness
- Maintains evidence chain integrity

### System Configuration

The system is configured through multiple files:

**runtime_compression_policy.json**:
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

### Threshold Definitions

The system uses four threshold levels:

**Observe Threshold (0.75)**:
- Entry point for monitoring zone
- System begins increased observation
- State transitions to candidate

**Candidate Threshold (0.75)**:
- Marks session as compression candidate
- Trace granularity increases
- Evidence preparation begins

**Enforced Threshold (0.85)**:
- Compression becomes mandatory
- Must execute before prompt assembly
- Guardrail 2A activates

**Strong Threshold (0.92)**:
- Emergency compression trigger
- Aggressive eviction applied
- Higher compression ratio

### Critical Rule Enforcement

The critical rule states: "不允许跨过 0.85 后继续拖延"

This means that once the budget ratio reaches 0.85, compression must execute immediately, before the next prompt assembly. This prevents:
- Context overflow
- Delayed compression
- User-visible errors
- Response quality degradation

### State Machine Behavior

The state machine manages the compression lifecycle:

**State: idle**
- Normal operation
- Budget ratio < 0.75
- No compression activity

**State: candidate**
- Monitoring active
- 0.75 <= ratio < 0.85
- Preparing for potential compression

**State: pending**
- Compression required
- ratio >= 0.85
- Must compress before assemble

**State: executing**
- Compression in progress
- Eviction planning active
- Capsule generation underway

**State: completed**
- Compression successful
- Ratio reduced
- Evidence captured

**State: failed**
- Compression failed
- Error logged
- Rollback initiated

**State: rollback**
- Recovery in progress
- State being restored
- Investigation required

### Safety Mechanisms

The system implements multiple safety mechanisms:

**Kill Switch**:
- Emergency shutdown capability
- Immediately stops all compression
- Preserves current state
- Requires manual deactivation

**Safety Counters**:
- Track potential violations
- Must remain at zero
- Alert on any non-zero value
- Trigger investigation

**Scope Filter**:
- Only processes low-risk sessions
- Excludes critical sessions
- Prevents accidental compression
- Configurable exclusion list

### Evidence Package Structure

Every compression event generates a complete evidence package:

1. counter_before.json - Counter state before compression
2. counter_after.json - Counter state after compression
3. budget_before.json - Budget snapshot before compression
4. budget_after.json - Budget snapshot after compression
5. guardrail_event.json - Guardrail activation record
6. capsule_metadata.json - Capsule content summary

Each file follows a strict schema and is validated for integrity.

### Performance Characteristics

The system exhibits the following performance characteristics:

**Budget Check**:
- Duration: 30-85ms
- Memory: Minimal
- CPU: Low

**Compression Execution**:
- Duration: 140-400ms
- Memory: 10-50MB additional
- CPU: Moderate

**Total Pipeline**:
- Minimum: 170ms
- Typical: 250ms
- Maximum: 485ms

### Error Handling

The system handles errors through multiple strategies:

**Transient Errors**:
- Automatic retry with exponential backoff
- Up to 3 attempts
- Delays: 100ms, 200ms, 400ms

**Permanent Errors**:
- Fallback to safe state
- Log error details
- Restore from backup

**Catastrophic Errors**:
- Kill switch activation
- Alert operators
- Full diagnostic mode

### Monitoring and Observability

The system provides comprehensive monitoring:

**Real-Time Metrics**:
- Active session count
- Budget ratio distribution
- Compression state breakdown
- Safety counter status

**Alerting**:
- Critical: Safety violations, kill switch
- Warning: Error rate, latency
- Info: Compression events, state transitions

**Logging**:
- Structured JSON logs
- Multiple log levels
- Comprehensive audit trail

### Operational Guidelines

For daily operations:

**Monitoring**:
- Check safety counters every hour
- Review error logs daily
- Verify evidence storage weekly

**Maintenance**:
- Clean old evidence files weekly
- Update documentation monthly
- Full audit quarterly

**Troubleshooting**:
- Check logs for errors
- Verify configuration
- Test tools manually
- Contact support if needed

---

**Document Version**: 1.0
**Last Updated**: 2026-03-08T04:18:00-06:00
